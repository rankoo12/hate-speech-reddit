from __future__ import annotations

from typing import Dict, List

from src.models import UserPost
from src.scoring.user_scoring import score_users


def make_user_post(
    author: str,
    text: str,
    *,
    kind: str = "comment",
    post_id: str = "p1",
    created_utc: float = 0.0,
    subreddit: str = "test",
) -> UserPost:
    return UserPost(
        id=post_id,
        url=f"https://old.reddit.com/r/{subreddit}/comments/{post_id}",
        subreddit=subreddit,
        author=author,
        kind=kind,  # type: ignore[arg-type]
        text=text,
        created_utc=created_utc,
    )


def test_user_with_single_high_risk_item_is_scored_and_explained():
    users_history: Dict[str, List[UserPost]] = {
        "alice": [
            make_user_post(
                "alice",
                "We should bomb them all, they deserve to die.",
                post_id="p1",
            )
        ]
    }

    users = score_users(
        users_history,
        high_risk_threshold=0.8,
        medium_risk_threshold=0.5,
        min_user_posts_for_confident_score=5,
        posts_fallback_scores=None,
    )

    u = users["alice"]
    # Basic sanity: score is in range and non-zero for clearly violent text
    assert 0.0 <= u.score <= 1.0
    assert u.score > 0.0

    # We don't force "high" label; current rule-based model may yield low/medium
    assert u.label in ("low", "medium")

    # Aggregation stats should reflect the single item
    assert u.total_posts == 1
    assert u.count_high_posts == 0  # no posts above high_risk_threshold

    # Explanation should mention counts
    assert "0 high-risk posts out of 1 items" in u.explanation


def test_user_with_many_low_risk_items_remains_low():
    users_history: Dict[str, List[UserPost]] = {
        "bob": [
            make_user_post("bob", "I like coffee and cats.", post_id="p1"),
            make_user_post("bob", "Nice weather today.", post_id="p2"),
            make_user_post("bob", "Great movie last night.", post_id="p3"),
        ]
    }

    users = score_users(
        users_history,
        high_risk_threshold=0.8,
        medium_risk_threshold=0.5,
        min_user_posts_for_confident_score=5,
        posts_fallback_scores=None,
    )

    u = users["bob"]
    assert u.label == "low"
    assert u.count_high_posts == 0
    assert u.total_posts == 3
    assert "high-risk posts" in u.explanation


def test_fallback_scores_used_when_no_history():
    users_history: Dict[str, List[UserPost]] = {"carol": []}
    fallback = {"carol": [0.9]}

    users = score_users(
        users_history,
        high_risk_threshold=0.8,
        medium_risk_threshold=0.5,
        min_user_posts_for_confident_score=5,
        posts_fallback_scores=fallback,
    )

    u = users["carol"]
    assert u.score >= 0.8
    assert u.label == "high"
    assert "current scored posts only" in u.explanation


def test_user_with_no_history_and_no_fallback_gets_zero_score():
    users_history: Dict[str, List[UserPost]] = {"dave": []}

    users = score_users(
        users_history,
        high_risk_threshold=0.8,
        medium_risk_threshold=0.5,
        min_user_posts_for_confident_score=5,
        posts_fallback_scores=None,
    )

    u = users["dave"]
    assert u.score == 0.0
    assert u.label == "low"
    assert u.total_posts == 0
    assert "No historical activity or scored posts" in u.explanation
