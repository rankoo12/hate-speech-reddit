from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from .config import get_config
from .models import UserPost, UserRisk
from .scoring.user_scoring import score_users


def _load_users_history(path: Path) -> Dict[str, List[UserPost]]:
    """
    Load users_enriched.json into a mapping:
        username -> List[UserPost]
    """
    if not path.exists():
        print(f"[user_score] users_enriched file not found: {path}")
        return {}

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    users_history: Dict[str, List[UserPost]] = {}

    # Expecting structure: { "username": [ {UserPost fields...}, ... ], ... }
    for username, items in raw.items():
        posts: List[UserPost] = []
        for item in items:
            # Be defensive: ignore malformed entries
            try:
                posts.append(
                    UserPost(
                        id=item["id"],
                        url=item["url"],
                        subreddit=item["subreddit"],
                        author=item["author"],
                        kind=item["kind"],
                        text=item["text"],
                        created_utc=item["created_utc"],
                    )
                )
            except KeyError:
                continue
        users_history[username] = posts

    return users_history


def _load_posts_fallback_scores(path: Path) -> Dict[str, List[float]]:
    """
    Load post-level scores from posts_scored.csv so that we can derive
    a user score even when we have no user history for that user.

    We only need two columns:
        author, score
    """
    if not path.exists():
        print(f"[user_score] posts_scored file not found, skipping fallback: {path}")
        return {}

    fallback: Dict[str, List[float]] = defaultdict(list)

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            author = row.get("author")
            score_str = row.get("score")
            if not author or score_str is None:
                continue
            try:
                score = float(score_str)
            except ValueError:
                continue
            fallback[author].append(score)

    return dict(fallback)


def _write_users_scored_csv(path: Path, users: Dict[str, UserRisk]) -> None:
    fieldnames = [
        "username",
        "score",
        "label",
        "max_post_score",
        "average_score",
        "count_high_posts",
        "total_posts",
        "explanation",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for u in users.values():
            writer.writerow(
                {
                    "username": u.username,
                    "score": f"{u.score:.4f}",
                    "label": u.label,
                    "max_post_score": f"{u.max_post_score:.4f}",
                    "average_score": f"{u.average_score:.4f}",
                    "count_high_posts": u.count_high_posts,
                    "total_posts": u.total_posts,
                    "explanation": u.explanation,
                }
            )


def _write_users_scored_jsonl(path: Path, users: Dict[str, UserRisk]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for u in users.values():
            obj = {
                "username": u.username,
                "score": u.score,
                "label": u.label,
                "max_post_score": u.max_post_score,
                "average_score": u.average_score,
                "count_high_posts": u.count_high_posts,
                "total_posts": u.total_posts,
                "explanation": u.explanation,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main() -> None:
    cfg = get_config()

    # 1. Load inputs
    users_history = _load_users_history(cfg.paths.users_enriched_path)
    posts_fallback_scores = _load_posts_fallback_scores(cfg.paths.posts_scored_path)

    # 2. Run user-level scoring
    users_scored = score_users(
        users_history,
        high_risk_threshold=cfg.scoring.high_risk_threshold,
        medium_risk_threshold=cfg.scoring.medium_risk_threshold,
        min_user_posts_for_confident_score=cfg.scoring.min_user_posts_for_confident_score,
        posts_fallback_scores=posts_fallback_scores,
    )

    # 3. Write outputs
    _write_users_scored_csv(cfg.paths.users_scored_path, users_scored)

    # JSONL is optional but configured in PathsConfig
    users_scored_jsonl_path = getattr(cfg.paths, "users_scored_jsonl_path", None)
    if users_scored_jsonl_path is not None:
        _write_users_scored_jsonl(users_scored_jsonl_path, users_scored)

    print(
        f"[user_score] wrote {len(users_scored)} users to "
        f"{cfg.paths.users_scored_path}"
    )
    if users_scored_jsonl_path is not None:
        print(f"[user_score] JSONL written to {users_scored_jsonl_path}")


if __name__ == "__main__":
    main()
