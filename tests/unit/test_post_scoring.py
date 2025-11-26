from __future__ import annotations

from src.models import Post
from src.scoring.post_scoring import score_post


def make_post(text: str, title: str = "") -> Post:
    return Post(
        id="test-id",
        url="https://old.reddit.com/r/test/comments/test-id",
        subreddit="test",
        author="test_user",
        title=title,
        text=text,
        created_utc=0.0,
    )


def test_high_violence_post_gets_high_label():
    post = make_post(
        "We should kill them all and bomb their city, they deserve to die."
    )
    risk = score_post(post)

    assert 0.0 <= risk.score <= 1.0
    assert risk.label in ("medium", "high")
    assert "kill" in risk.explanation or "bomb" in risk.explanation


def test_benign_post_gets_low_label_and_no_harmful_keywords():
    post = make_post("I love puppies and rainbows, this is a wholesome post.")
    risk = score_post(post)

    assert risk.label == "low"
    # Explanation should mention we did not find explicit harmful keywords.
    assert "no explicit harmful keywords" in risk.explanation


def test_all_caps_contributes_to_explanation():
    post = make_post("THIS IS SO CRAZY I AM SO ANGRY BUT NOT VIOLENT")
    risk = score_post(post)

    assert 0.0 <= risk.score <= 1.0
    # We don't require a specific threshold, but all_caps feature should show up.
    assert "allcaps=" in risk.explanation
