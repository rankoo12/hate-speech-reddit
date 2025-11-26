from __future__ import annotations

import pytest

from src import run_score


@pytest.mark.skip(
    reason="Smoke test depends on having raw_posts.json; enable in an environment with data."
)
def test_run_score_smoke_does_not_crash():
    """
    Smoke test: ensure the post scoring script runs without raising.
    Skipped by default; can be enabled when raw_posts.json is available.
    """
    run_score.main()
