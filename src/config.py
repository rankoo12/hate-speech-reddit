from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# Base directory of the project (one level above src/)
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------- Scraper configuration ----------


@dataclass
class ScraperConfig:
    """
    Settings for HTML scraping of old.reddit.com.
    """

    base_url: str = "https://old.reddit.com"
    user_agent: str = "hate-speech-html-scraper/1.0"
    request_delay_seconds: float = 1.0  # polite delay between requests
    timeout_seconds: float = 10.0  # HTTP timeout
    max_retries: int = 3  # optional future use for retry logic


# ---------- Collection configuration ----------


@dataclass
class CollectionConfig:
    """
    What and how much we collect from Reddit.

    Design B:
    - We always scan newest posts from selected subreddits (no Reddit search).
    - We do not pre-filter by simple keywords.
    - Every collected post is scored by the risk model.
    """

    # Subreddits to target; "all" means the global 'r/all' feed
    target_subreddits: List[str] = field(
        default_factory=lambda: [
            "news",
            "worldnews",
            "politics",
            "PublicFreakout",
            "unpopularopinion",
            "Palestine",
        ]
    )

    # Maximum number of posts to collect per subreddit (upper bound)
    max_posts_per_subreddit: int = 50

    # Safety cap for entire run (assignment target ~100–150 posts overall)
    max_total_posts: int = 150

    # Lookback for user history (days)
    user_history_lookback_days: int = 60


# ---------- Scoring configuration ----------


@dataclass
class ScoringConfig:
    """
    Thresholds and scoring-related constants.
    Actual keyword weights will live in scoring/vocab.py.
    """

    # Post risk thresholds
    high_risk_threshold: float = 0.8
    medium_risk_threshold: float = 0.5

    # User scoring
    min_user_posts_for_confident_score: int = 5


# ---------- Paths configuration ----------


@dataclass
class PathsConfig:
    """
    Central place for file paths used by the pipeline.
    """

    data_dir: Path = BASE_DIR / "data"
    raw_posts_path: Path = data_dir / "raw_posts.json"
    users_enriched_path: Path = data_dir / "users_enriched.json"
    posts_scored_path: Path = data_dir / "posts_scored.csv"
    users_scored_path: Path = data_dir / "users_scored.csv"


# ---------- Top-level application configuration ----------


@dataclass
class AppConfig:
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    collection: CollectionConfig = field(default_factory=CollectionConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)


def get_config() -> AppConfig:
    """
    Main entrypoint to get the full application config.

    Usage:
        from src.config import get_config
        cfg = get_config()
        cfg.collection.target_subreddits
    """
    cfg = AppConfig()

    # Ensure data directory exists
    cfg.paths.data_dir.mkdir(parents=True, exist_ok=True)

    return cfg
