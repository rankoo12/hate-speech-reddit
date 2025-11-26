from __future__ import annotations

import pytest

from src import run_collect


@pytest.mark.skip(
    reason="Smoke test requires live Reddit HTML scraping; enable manually."
)
def test_run_collect_smoke_does_not_crash():
    """
    Smoke test: ensure the collect script can run end-to-end without raising.
    This is intentionally skipped by default because it depends on live Reddit.
    """
    run_collect.main()
