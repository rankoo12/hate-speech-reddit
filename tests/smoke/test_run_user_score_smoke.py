from __future__ import annotations

import pytest

from src import run_user_score


@pytest.mark.skip(
    reason="Smoke test depends on users_enriched.json and posts_scored.csv; enable in a prepared env."
)
def test_run_user_score_smoke_does_not_crash():
    """
    Smoke test: ensure the user scoring script runs without raising.
    Skipped by default; can be enabled when enrichment + post scoring have run.
    """
    run_user_score.main()
