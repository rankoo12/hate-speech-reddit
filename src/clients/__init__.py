from __future__ import annotations

"""
Client package for external data sources (e.g. Reddit).

This package currently exposes:
- RedditClient: minimal protocol for fetching posts and user history.
- RedditApiCredentials: helper for loading Reddit API credentials from env vars.
- RedditApiClient: PoC / untested Reddit API implementation behind a feature flag.

HTML scraping is implemented in `src/reddit_html_client.py` and wrapped
to conform to the RedditClient protocol, but it lives outside this package
to keep backwards compatibility with the existing codebase.
"""

from .reddit_client import RedditClient, RedditApiClient, RedditApiCredentials

__all__ = [
    "RedditClient",
    "RedditApiClient",
    "RedditApiCredentials",
]
