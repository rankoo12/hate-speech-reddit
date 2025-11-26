from __future__ import annotations

from math import log
from typing import Dict, Iterable, List, Mapping, Optional

from ..models import Post, UserPost, UserRisk
from .post_scoring import score_post


def _build_post_from_user_post(item: UserPost) -> Post:
    """
    Convert a UserPost into a Post-shaped object so we can reuse the
    post-level scoring logic (score_post) without duplicating features.
    """
    return Post(
        id=item.id,
        url=item.url,
        subreddit=item.subreddit,
        author=item.author,
        title="",  # user history items typically don't have a separate title
        text=item.text,
        created_utc=item.created_utc,
        language=None,
    )


def score_users(
    users_history: Mapping[str, List[UserPost]],
    *,
    high_risk_threshold: float,
    medium_risk_threshold: float,
    min_user_posts_for_confident_score: int = 5,
    posts_fallback_scores: Optional[Mapping[str, List[float]]] = None,
) -> Dict[str, UserRisk]:
    """
    Aggregate per-user risk scores from user history (and optionally
    from post-level scores when no history is available).

    Parameters
    ----------
    users_history:
        Mapping from username -> list of UserPost items (e.g. loaded from
        users_enriched.json).
    high_risk_threshold:
        Score at or above which a post/user is considered high risk.
    medium_risk_threshold:
        Score at or above which a post/user is considered medium risk
        (and below high_risk_threshold).
    min_user_posts_for_confident_score:
        Minimum number of posts/comments to consider the user score
        "confident". Used only for explanation text.
    posts_fallback_scores:
        Optional mapping from username -> list of post-level scores,
        typically derived from posts_scored.*. Used for users who have
        no history in users_history but do appear in scored posts.

    Returns
    -------
    Dict[str, UserRisk]
        Aggregated risk profile for each user.
    """
    result: Dict[str, UserRisk] = {}
    posts_fallback_scores = posts_fallback_scores or {}

    for username, history_items in users_history.items():
        # 1. Score all historical items with the existing post-level model.
        scores: List[float] = []
        for item in history_items:
            post_obj = _build_post_from_user_post(item)
            risk = score_post(post_obj)
            scores.append(risk.score)

        has_history = bool(scores)

        # 2. If no history scores, optionally fall back to post-level scores.
        used_fallback = False
        if not scores:
            fallback = posts_fallback_scores.get(username, [])
            if fallback:
                scores.extend(fallback)
                used_fallback = True

        total_posts = len(scores)

        if not scores:
            # No activity at all (neither history nor posts).
            user_score = 0.0
            label = "low"
            explanation = (
                "No historical activity or scored posts found for this user; "
                "user_score set to 0.00 (low)."
            )
            result[username] = UserRisk(
                username=username,
                score=user_score,
                label=label,
                max_post_score=0.0,
                average_score=0.0,
                count_high_posts=0,
                total_posts=0,
                explanation=explanation,
            )
            continue

        # 3. Aggregate basic stats.
        max_post_score = max(scores)
        average_score = sum(scores) / total_posts if total_posts > 0 else 0.0
        count_high_posts = sum(1 for s in scores if s >= high_risk_threshold)

        # 4. Compute user_score using the formula from plan.md:
        #    user_score = max(max_post_score,
        #                     average_score + 0.2 * log(1 + count_high_posts))
        user_score = max(
            max_post_score,
            average_score + 0.2 * log(1 + count_high_posts),
        )

        # 5. Map user_score to label using thresholds.
        if user_score >= high_risk_threshold:
            label = "high"
        elif user_score >= medium_risk_threshold:
            label = "medium"
        else:
            label = "low"

        # 6. Build explanation text.
        parts = [
            f"{count_high_posts} high-risk posts out of {total_posts} items",
            f"max_post_score={max_post_score:.2f}",
            f"user_score={user_score:.2f} ({label})",
        ]

        if has_history and not used_fallback:
            parts.append("derived from historical activity only (last window).")
        elif has_history and used_fallback:
            parts.append("derived from historical activity plus current scored posts.")
        elif not has_history and used_fallback:
            parts.append(
                "no user history found; score derived from current scored posts only."
            )

        if total_posts < min_user_posts_for_confident_score:
            parts.append(
                f"low-confidence estimate (only {total_posts} items available)."
            )

        explanation = "; ".join(parts)

        result[username] = UserRisk(
            username=username,
            score=user_score,
            label=label,
            max_post_score=max_post_score,
            average_score=average_score,
            count_high_posts=count_high_posts,
            total_posts=total_posts,
            explanation=explanation,
        )

    return result
