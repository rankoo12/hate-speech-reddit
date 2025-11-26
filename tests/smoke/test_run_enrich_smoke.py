from __future__ import annotations

import pytest

from src import run_enrich


@pytest.mark.skip(reason="Smoke test requires live Reddit user pages; enable manually.")
def test_run_enrich_smoke_does_not_crash():
    """
    Smoke test: ensure the enrich script can run end-to-end without raising.
    This is intentionally skipped by default because it depends on live Reddit.
    """
    run_enrich.main()
