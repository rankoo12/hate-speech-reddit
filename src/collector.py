from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from .config import get_config
from .models import Post
from .reddit_html_client import RedditHtmlClient


class Collector:
    """
    Orchestrates collection of recent posts from configured subreddits
    using the RedditHtmlClient.
    """

    def __init__(self) -> None:
        self.cfg = get_config()
        self.client = RedditHtmlClient()

        # Use data_dir from config, filename is local convention here
        self.output_path: Path = self.cfg.paths.data_dir / "raw_posts.json"

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
            posts = self.client.fetch_subreddit_new(subreddit, fetch_limit)
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
