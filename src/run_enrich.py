from __future__ import annotations

"""
CLI entrypoint for the Enricher step.

Usage (from repo root):

    python -m src.run_enrich

This will:
- Load data/raw_posts.json
- For each unique author, fetch recent history (submissions + comments)
- Write data/users_enriched.json
"""

from src.config import get_config
from src.enricher import run_enrichment
from src.reddit_html_client import RedditHtmlClient


def main() -> None:
    cfg = get_config()

    client = RedditHtmlClient(
        scraper_config=cfg.scraper,
    )

    run_enrichment(client=client, cfg=cfg)


if __name__ == "__main__":
    main()
