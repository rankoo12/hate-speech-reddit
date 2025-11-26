# src/enricher.py
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Sequence
import json

from .config import AppConfig, get_config
from .models import Post, UserPost
from .reddit_html_client import RedditHtmlClient


def load_raw_posts(path: Path) -> List[Post]:
    """
    Load collected posts from raw_posts.json and convert them to Post objects.
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # raw_posts.json is expected to be a list of dicts compatible with Post
    return [Post(**item) for item in data]


def load_existing_users_enriched(path: Path) -> Dict[str, List[UserPost]]:
    """
    Load existing users_enriched.json (if present) into UserPost objects.

    Returns an empty dict if the file does not exist.
    """
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    existing: Dict[str, List[UserPost]] = {}
    for username, items in data.items():
        existing[username] = [UserPost(**item) for item in items]

    print(
        f"[Enricher] Loaded existing users_enriched.json for {len(existing)} users "
        f"from: {path}"
    )
    return existing


def get_unique_authors(posts: Sequence[Post]) -> List[str]:
    """
    Extract unique author usernames from collected posts.
    """
    authors = {p.author for p in posts if p.author}
    # deterministic order (useful for debugging / reproducibility)
    return sorted(authors)


def _compute_since(lookback_days: int) -> datetime:
    """
    Compute the UTC 'since' datetime for the configured lookback window.
    """
    now = datetime.now(timezone.utc)
    return now - timedelta(days=lookback_days)


def enrich_user(
    username: str,
    client: RedditHtmlClient,
    since: datetime,
    max_items: int,
) -> List[UserPost]:
    """
    Enrich a single user by fetching their recent history via the HTML client.

    Delegates to:
        RedditHtmlClient.get_user_history(username, since, max_items)

    Returns newest-first list of UserPost.
    """
    if max_items <= 0:
        return []
    return client.get_user_history(
        username=username,
        since=since,
        max_items=max_items,
    )


def enrich_all_users(
    posts: Sequence[Post],
    client: RedditHtmlClient,
    cfg: AppConfig,
    existing_users: Mapping[str, List[UserPost]] | None = None,
) -> Dict[str, List[UserPost]]:
    """
    For every unique author in raw_posts, fetch and normalize their
    recent history into a mapping:

        {username: [UserPost, ...]}

    existing_users:
        Mapping of usernames that already have enriched history. These
        users will be skipped (no additional network calls).
    """
    authors = get_unique_authors(posts)
    since = _compute_since(cfg.collection.user_history_lookback_days)

    # Hard cap per user, to avoid infinite crawling for very active accounts.
    max_items_per_user = getattr(cfg.collection, "max_user_history_items", 300)

    existing_usernames = set(existing_users.keys()) if existing_users else set()
    authors_to_fetch = [a for a in authors if a not in existing_usernames]

    print(f"[Enricher] Found {len(authors)} unique authors in raw_posts.")
    print(f"[Enricher] {len(existing_usernames)} users already enriched.")
    print(f"[Enricher] Will fetch history for {len(authors_to_fetch)} users.")
    print(f"[Enricher] Fetching history since {since.isoformat()} (UTC).")
    print(
        f"[Enricher] Max user history items per user: {max_items_per_user}",
        flush=True,
    )

    users_enriched_new: Dict[str, List[UserPost]] = {}

    for idx, username in enumerate(authors_to_fetch, start=1):
        print(
            f"[Enricher] [{idx}/{len(authors_to_fetch)}] Fetching history for u/{username}...",
            flush=True,
        )
        history = enrich_user(
            username=username,
            client=client,
            since=since,
            max_items=max_items_per_user,
        )
        print(f"[Enricher] u/{username}: {len(history)} activities", flush=True)

        # Only keep users with at least one recent activity
        users_enriched_new[username] = history

    return users_enriched_new


def save_users_enriched(
    users_enriched: Mapping[str, List[UserPost]],
    path: Path,
) -> None:
    """
    Serialize users_enriched mapping into JSON.

    Shape:

    {
        "username1": [
            {...UserPost...},
            ...
        ],
        "username2": [
            ...
        ]
    }
    """
    serializable: Dict[str, List[dict]] = {
        username: [asdict(item) for item in history]
        for username, history in users_enriched.items()
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    print(
        f"[Enricher] Wrote users_enriched.json for {len(users_enriched)} users to: {path}"
    )


def run_enrichment(client: RedditHtmlClient, cfg: AppConfig | None = None) -> None:
    """
    High-level function to be called by the CLI entrypoint (run_enrich.py).

    - Loads raw_posts.json
    - Loads existing users_enriched.json if present (cache)
    - Enriches remaining authors using the provided HTML client
    - Writes merged users_enriched.json
    """
    if cfg is None:
        cfg = get_config()

    # Load existing users_enriched (cache) if available
    existing = load_existing_users_enriched(cfg.paths.users_enriched_path)

    print(f"[Enricher] Loading raw posts from: {cfg.paths.raw_posts_path}")
    posts = load_raw_posts(cfg.paths.raw_posts_path)
    print(f"[Enricher] Loaded {len(posts)} posts.")

    users_enriched_new = enrich_all_users(
        posts=posts,
        client=client,
        cfg=cfg,
        existing_users=existing,
    )

    # Merge existing + new (new wins if there is overlap)
    combined: Dict[str, List[UserPost]] = dict(existing)
    combined.update(users_enriched_new)

    save_users_enriched(combined, cfg.paths.users_enriched_path)
