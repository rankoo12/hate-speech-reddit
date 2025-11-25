from __future__ import annotations

import json
import csv
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List

from .models import Post
from .scoring.post_scoring import PostRisk, score_posts


# Default paths – you can change them later or make them configurable
RAW_POSTS_PATH = Path("./data/raw_posts.json")
SCORED_JSONL_PATH = Path("./data/posts_scored.jsonl")
SCORED_CSV_PATH = Path("./data/posts_scored.csv")


# -----------------------------------------------------------------------------
# Loading
# -----------------------------------------------------------------------------


def _post_from_dict(data: Dict) -> Post:
    """
    Convert a raw dict from raw_posts.json into a Post instance.

    This is intentionally defensive: if some fields are missing,
    it falls back to empty strings / 0.0 instead of crashing.
    """
    return Post(
        id=str(data.get("id", "")),
        url=data.get("url", "") or "",
        subreddit=data.get("subreddit", "") or "",
        author=data.get("author", "") or "",
        title=data.get("title", "") or "",
        # Prefer 'text' but fall back to 'selftext' if needed
        text=data.get("text") or data.get("selftext") or "",
        created_utc=float(data.get("created_utc", 0.0)),
        language=data.get("language"),  # may be None; scoring may re-detect
    )


def load_posts(path: Path = RAW_POSTS_PATH) -> List[Post]:
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError(f"Expected a list of posts in {path}, got {type(raw)}")

    posts: List[Post] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        posts.append(_post_from_dict(item))

    return posts


# -----------------------------------------------------------------------------
# Export helpers
# -----------------------------------------------------------------------------


def _merge_post_and_risk(post: Post, risk: PostRisk) -> Dict:
    """
    Create a single flat dict with both original post info and scoring info.

    This is what we export into JSONL/CSV as the "scored post" record.
    """
    return {
        # Original post fields
        "id": post.id,
        "url": post.url,
        "subreddit": post.subreddit,
        "author": post.author,
        "title": post.title,
        "text": post.text,
        "created_utc": post.created_utc,
        # Language (prefer the risk language; fall back to post.language)
        "language": risk.language or post.language,
        # Scoring
        "risk_score": risk.score,
        "risk_label": risk.label,
        "risk_explanation": risk.explanation,
        # feature_values is a nested dict; fine for JSONL, will be stringified in CSV
        "risk_features": risk.feature_values,
    }


def write_jsonl(records: Iterable[Dict], path: Path = SCORED_JSONL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_csv(records: Iterable[Dict], path: Path = SCORED_CSV_PATH) -> None:
    records = list(records)
    if not records:
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    # We choose a fixed, explicit column order for the CSV
    fieldnames = [
        "id",
        "url",
        "subreddit",
        "author",
        "title",
        "text",
        "created_utc",
        "language",
        "risk_score",
        "risk_label",
        "risk_explanation",
        "risk_features",  # will be JSON-like string
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            row = rec.copy()
            # risk_features is a dict; make it a compact JSON string for CSV
            row["risk_features"] = json.dumps(
                row.get("risk_features", {}), ensure_ascii=False
            )
            writer.writerow(row)


# -----------------------------------------------------------------------------
# Summary / CLI
# -----------------------------------------------------------------------------


def _summarize(risks: List[PostRisk]) -> None:
    total = len(risks)
    label_counts: Dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    for r in risks:
        label_counts[r.label] = label_counts.get(r.label, 0) + 1

    print(f"Scored {total} posts.")
    for label in ("high", "medium", "low"):
        c = label_counts.get(label, 0)
        pct = (c / total * 100.0) if total else 0.0
        print(f"  {label:6}: {c:5d} ({pct:5.1f}%)")

    # Show a few highest-risk examples
    top_examples = sorted(risks, key=lambda r: r.score, reverse=True)[:5]
    print("\nTop 5 highest-risk posts:")
    for r in top_examples:
        print(f"  - id={r.post_id}, score={r.score:.2f}, label={r.label}")


def main() -> None:
    print(f"Loading raw posts from {RAW_POSTS_PATH} ...")
    posts = load_posts(RAW_POSTS_PATH)
    print(f"Loaded {len(posts)} posts.")

    print("Scoring posts ...")
    risks: List[PostRisk] = score_posts(posts)

    # Build export records
    records = [_merge_post_and_risk(p, r) for p, r in zip(posts, risks)]

    print(f"Writing scored posts to {SCORED_JSONL_PATH} ...")
    write_jsonl(records, SCORED_JSONL_PATH)

    print(f"Writing scored posts to {SCORED_CSV_PATH} ...")
    write_csv(records, SCORED_CSV_PATH)

    _summarize(risks)
    print("Done.")


if __name__ == "__main__":
    main()
