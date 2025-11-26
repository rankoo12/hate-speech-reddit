from __future__ import annotations

import pytest

from src import run_pipeline


@pytest.mark.skip(
    reason="E2E test runs full pipeline (collect → enrich → score → user_score); enable manually."
)
def test_full_pipeline_e2e_runs_without_crashing():
    """
    End-to-end test: run the full pipeline once.

    This is intentionally skipped by default because it depends on:
      - Live Reddit (for scraping & user history)
      - Reasonable runtime

    It can be enabled locally by removing or editing the @skip marker.
    """
    run_pipeline.main()
