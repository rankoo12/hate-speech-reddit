from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import List

from .config import get_config
from .models import Post
from .reddit_html_client import RedditHtmlClient
from .clients.reddit_client import RedditClient, RedditApiClient, RedditApiCredentials


class Collector:
    """
    Orchestrates collection of recent posts from configured subreddits
    using a RedditClient implementation (HTML scraper by default, with
    an optional Reddit API PoC behind a feature flag).
    """

    def __init__(self) -> None:
        self.cfg = get_config()
        self.client: RedditClient = self._build_client()

        # Use data_dir from config, filename is local convention here
        self.output_path: Path = self.cfg.paths.data_dir / "raw_posts.json"

    def _build_client(self) -> RedditClient:
        """
        Select a Reddit client implementation based on environment.

        Behavior:
        - If USE_REDDIT_API is not "true" (case-insensitive) → HTML client.
        - If USE_REDDIT_API is "true" but credentials are missing → HTML client.
        - If USE_REDDIT_API is "true" and credentials are present → API PoC client.

        This keeps the default behavior identical to the original HTML-only
        pipeline while allowing an optional API-based PoC to be wired in.
        """
        use_api_flag = os.getenv("USE_REDDIT_API", "").lower() == "true"
        if not use_api_flag:
            print(
                "[collector] Using HTML Reddit client (USE_REDDIT_API is not 'true')."
            )
            return RedditHtmlClient()

        creds = RedditApiCredentials.from_env()
        if creds is None:
            print(
                "[collector] USE_REDDIT_API='true' but Reddit API env vars are missing; "
                "falling back to HTML client."
            )
            return RedditHtmlClient()

        print("[collector] Using Reddit API client (PoC, untested).")
        return RedditApiClient(credentials=creds)

    def collect_all(self) -> List[Post]:
        all_posts: List[Post] = []
        total_limit = self.cfg.collection.max_total_posts
        per_sub_limit = self.cfg.collection.max_posts_per_subreddit

        for subreddit in self.cfg.collection.target_subreddits:
            if len(all_posts) >= total_limit:
                break

            remaining = total_limit - len(all_posts)
            fetch_limit = min(per_sub_limit, remaining)

            print(f"[collector] Fetching from r/{subreddit} (limit={fetch_limit})...")
            # Use the protocol-style method so either HTML or API client works.
            posts = self.client.fetch_new_posts(subreddit=subreddit, limit=fetch_limit)
            print(f"[collector] Retrieved {len(posts)} posts from r/{subreddit}")

            all_posts.extend(posts)

        self._save_posts(all_posts)
        return all_posts

    def _save_posts(self, posts: List[Post]) -> None:
        data_dir: Path = self.cfg.paths.data_dir
        data_dir.mkdir(parents=True, exist_ok=True)

        serializable = [asdict(p) for p in posts]

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

        print(f"[collector] Saved {len(posts)} posts → {self.output_path}")
