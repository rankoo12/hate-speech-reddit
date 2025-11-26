from __future__ import annotations

from datetime import datetime, timezone
from time import sleep
from typing import List, Optional, Literal, Tuple

import requests
from bs4 import BeautifulSoup

from src.config import get_config
from src.models import Post, UserPost


class RedditHtmlClient:
    """
    HTML scraper for old.reddit.com.

    Responsibilities:
    - Fetch newest posts from a subreddit (/r/{sub}?sort=new) with pagination.
    - Fetch a user's recent submissions + comments within a lookback window.
    - Parse <div class="thing"> into Post / UserPost models.
    - Hide HTTP + HTML details from the rest of the pipeline.
    """

    def __init__(
        self,
        scraper_config: Optional[object] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        app_config = get_config()
        self._cfg = scraper_config or app_config.scraper

        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": self._cfg.user_agent})

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def fetch_subreddit_new(self, subreddit: str, max_posts: int) -> List[Post]:
        """
        Scrape newest posts from /r/{subreddit}/?sort=new with pagination.

        Stops when:
        - we collected max_posts, or
        - there is no next page, or
        - HTTP/parse error.
        """
        collected: List[Post] = []
        url = f"{self._cfg.base_url}/r/{subreddit}/?sort=new"

        while url and len(collected) < max_posts:
            html = self._get(url)
            if html is None:
                break

            page_posts, next_url = self._parse_subreddit_page(html, subreddit)
            for post in page_posts:
                if len(collected) >= max_posts:
                    break
                collected.append(post)

            if len(collected) >= max_posts or not next_url:
                break

            url = next_url
            sleep(self._cfg.request_delay_seconds)

        return collected

    def get_user_history(
        self,
        username: str,
        since: datetime,
        max_items: int,
    ) -> List[UserPost]:
        """
        Scrape a user's submissions + comments since a given datetime (UTC),
        with a hard cap on the total number of UserPost items.

        Returns newest-first list of UserPost.

        max_items:
            Maximum total items to return (submissions + comments combined).
        """
        if max_items <= 0:
            return []

        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        cutoff_ts = since.timestamp()

        history: List[UserPost] = []

        # Split budget between submissions and comments in a simple way.
        # For odd max_items, submissions get the extra one.
        max_submissions = (max_items + 1) // 2
        max_comments = max_items - max_submissions

        # Submissions stream
        if max_submissions > 0:
            submissions = self._fetch_user_stream(
                username=username,
                kind="submission",
                path="submitted",
                cutoff_ts=cutoff_ts,
                max_items=max_submissions,
            )
            history.extend(submissions)

        # Comments stream
        remaining_for_comments = max_items - len(history)
        if remaining_for_comments > 0:
            comments = self._fetch_user_stream(
                username=username,
                kind="comment",
                path="comments",
                cutoff_ts=cutoff_ts,
                max_items=remaining_for_comments,
            )
            history.extend(comments)

        # Newest-first
        history.sort(key=lambda item: item.created_utc, reverse=True)
        return history

    # -------------------------------------------------------------------------
    # Internal: user history
    # -------------------------------------------------------------------------

    def _fetch_user_stream(
        self,
        username: str,
        kind: Literal["submission", "comment"],
        path: str,
        cutoff_ts: float,
        max_items: Optional[int] = None,
    ) -> List[UserPost]:
        """
        Fetch either /user/{username}/submitted/ or /comments/ with pagination.

        Stops when:
        - no next page, or
        - we hit items older than cutoff_ts (pages are newest-first), or
        - we collected max_items items (if max_items is not None).
        """
        collected: List[UserPost] = []
        url = f"{self._cfg.base_url}/user/{username}/{path}/"
        stop = False

        while url and not stop:
            # If we already hit the cap, stop early.
            if max_items is not None and len(collected) >= max_items:
                break

            html = self._get(url)
            if html is None:
                break

            page_items, next_url, stop = self._parse_user_page(
                html, username, kind, cutoff_ts
            )

            # If we have a max_items cap, trim the last page to respect it.
            if max_items is not None:
                remaining = max_items - len(collected)
                if remaining <= 0:
                    break
                if len(page_items) > remaining:
                    page_items = page_items[:remaining]
                    # After this page we are at the cap; no need to follow next_url.
                    stop = True

            collected.extend(page_items)

            if not next_url or stop:
                break

            url = next_url
            sleep(self._cfg.request_delay_seconds)

        return collected

    # -------------------------------------------------------------------------
    # Internal: HTTP
    # -------------------------------------------------------------------------

    def _get(self, url: str) -> Optional[str]:
        """
        GET with basic retry + timeout + status handling.

        Returns HTML text on success, or None on failure.
        """
        last_exc: Optional[Exception] = None

        for _ in range(self._cfg.max_retries):
            try:
                resp = self._session.get(url, timeout=self._cfg.timeout_seconds)
                if resp.status_code == 200:
                    return resp.text

                if resp.status_code in {403, 404}:
                    # Suspended/private/deleted/etc.
                    return None

                last_exc = RuntimeError(
                    f"Unexpected status {resp.status_code} for {url}"
                )
            except (requests.RequestException, OSError) as exc:
                last_exc = exc

            sleep(self._cfg.request_delay_seconds)

        # Could log last_exc here with a logger if we add one later.
        return None

    # -------------------------------------------------------------------------
    # Internal: parsing subreddit pages
    # -------------------------------------------------------------------------

    def _parse_subreddit_page(
        self, html: str, subreddit_fallback: str
    ) -> Tuple[List[Post], Optional[str]]:
        soup = BeautifulSoup(html, "html.parser")
        posts: List[Post] = []

        for thing in soup.find_all("div", class_="thing"):
            if thing.get("data-promoted") == "true":
                continue

            created_utc = self._extract_created_utc(thing)
            if created_utc is None:
                continue

            fullname = thing.get("data-fullname") or thing.get("id")
            if not fullname:
                continue
            post_id = fullname.split("_")[-1]

            subreddit = thing.get("data-subreddit") or subreddit_fallback
            author = thing.get("data-author") or "[deleted]"

            permalink = (
                thing.get("data-permalink") or thing.get("data-url") or ""
            ).strip()
            url = (
                f"{self._cfg.base_url}{permalink}"
                if permalink.startswith("/")
                else permalink
            )

            title_tag = thing.find("a", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            body_text = ""
            expando = thing.find("div", class_="expando")
            if expando:
                md = expando.find("div", class_="md")
                if md:
                    body_text = md.get_text(separator="\n", strip=True)

            text = "\n\n".join(part for part in (title, body_text) if part)

            posts.append(
                Post(
                    id=post_id,
                    url=url,
                    subreddit=subreddit,
                    author=author,
                    title=title,
                    text=text,
                    created_utc=created_utc,
                    language=None,  # language detection happens later
                )
            )

        next_url = self._find_next_url(soup)
        return posts, next_url

    # -------------------------------------------------------------------------
    # Internal: parsing user pages
    # -------------------------------------------------------------------------

    def _parse_user_page(
        self,
        html: str,
        username: str,
        kind: Literal["submission", "comment"],
        cutoff_ts: float,
    ) -> Tuple[List[UserPost], Optional[str], bool]:
        """
        Parse a user history page into UserPost models.

        Returns:
            (items, next_url, stop_pagination)
        """
        soup = BeautifulSoup(html, "html.parser")
        items: List[UserPost] = []
        stop = False

        for thing in soup.find_all("div", class_="thing"):
            created_utc = self._extract_created_utc(thing)
            if created_utc is None:
                continue

            if created_utc < cutoff_ts:
                # Items are newest-first; once we see old content we can stop.
                stop = True
                break

            fullname = thing.get("data-fullname") or thing.get("id")
            if not fullname:
                continue
            item_id = fullname.split("_")[-1]

            subreddit = thing.get("data-subreddit") or ""
            author = thing.get("data-author") or username or "[deleted]"

            permalink = (
                thing.get("data-permalink") or thing.get("data-url") or ""
            ).strip()
            url = (
                f"{self._cfg.base_url}{permalink}"
                if permalink.startswith("/")
                else permalink
            )

            md = thing.find("div", class_="md")
            text = md.get_text(separator="\n", strip=True) if md else ""

            items.append(
                UserPost(
                    id=item_id,
                    url=url,
                    subreddit=subreddit,
                    author=author,
                    kind=kind,
                    text=text,
                    created_utc=created_utc,
                )
            )

        next_url = None if stop else self._find_next_url(soup)
        return items, next_url, stop

    # -------------------------------------------------------------------------
    # Internal: small helpers
    # -------------------------------------------------------------------------

    def _extract_created_utc(self, thing) -> Optional[float]:
        """
        Extract a Unix timestamp from a <div class="thing">.

        Tries:
        - data-timestamp (ms or s)
        - <time datetime="...">
        """
        ts_attr = thing.get("data-timestamp")
        if ts_attr:
            try:
                ts_int = int(ts_attr)
                if ts_int > 10_000_000_000:  # ms -> s
                    return ts_int / 1000.0
                return float(ts_int)
            except (TypeError, ValueError):
                pass

        time_tag = thing.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            try:
                dt = datetime.fromisoformat(time_tag["datetime"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except (TypeError, ValueError):
                return None

        return None

    @staticmethod
    def _find_next_url(soup: BeautifulSoup) -> Optional[str]:
        next_span = soup.find("span", class_="next-button")
        if not next_span:
            return None
        a = next_span.find("a")
        if not a or not a.has_attr("href"):
            return None
        return a["href"]
