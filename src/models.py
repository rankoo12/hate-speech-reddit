from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Post:
    """
    A single Reddit post collected from subreddit 'new' feeds.

    This is the main unit we will:
    - detect language for
    - score for risk
    - export into the posts_scored.csv feed
    """

    id: str  # Reddit full name / unique id (e.g. t3_xxxxx)
    url: str  # Full URL to the post
    subreddit: str  # Subreddit name (without 'r/')
    author: str  # Author username or placeholder if unknown
    title: str  # Post title
    text: str  # Main text content (title + selftext or snippet)
    created_utc: float  # Unix timestamp
    language: str | None = None  # Filled later by language detection


@dataclass
class UserPost:
    """
    Any content written by a user: submission or comment.

    This is what we use to build a 2-month activity profile
    for user-level risk scoring.
    """

    id: str  # Unique id (same idea as Post.id)
    url: str  # URL to the submission or comment
    subreddit: str  # Subreddit name
    author: str  # Username
    kind: Literal["submission", "comment"]  # Type of item
    text: str  # Text body (title+body or comment)
    created_utc: float  # Unix timestamp


@dataclass
class UserRisk:
    """
    Aggregated risk profile for a single Reddit user, based on their
    recent posts and comments.

    This is what we export into users_scored.csv.
    """

    username: str
    score: float
    label: Literal["high", "medium", "low"]

    max_post_score: float
    average_score: float
    count_high_posts: int
    total_posts: int

    explanation: str
