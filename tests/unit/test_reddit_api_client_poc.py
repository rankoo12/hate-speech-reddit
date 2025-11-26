from __future__ import annotations

from datetime import datetime

from src.clients import RedditClient, RedditApiClient, RedditApiCredentials


def _make_dummy_client() -> RedditApiClient:
    creds = RedditApiCredentials(
        client_id="dummy-client-id",
        client_secret="dummy-client-secret",
        user_agent="dummy-user-agent",
    )
    return RedditApiClient(credentials=creds)


def test_reddit_api_client_poc_is_reddit_client() -> None:
    """
    The PoC RedditApiClient should conform to the RedditClient protocol.

    This is a minimal safety check that we can treat the API client as a
    drop-in replacement for the HTML client in places that depend only
    on the RedditClient abstraction.
    """
    client = _make_dummy_client()
    assert isinstance(client, RedditClient)


def test_reddit_api_client_poc_methods_return_lists() -> None:
    """
    PoC methods currently return empty lists but must be present and
    return list instances to be compatible with the rest of the pipeline.
    """
    client = _make_dummy_client()

    posts = client.fetch_new_posts(subreddit="testsubreddit", limit=5)
    history = client.fetch_user_history(username="testuser", since=datetime.utcnow())

    assert isinstance(posts, list)
    assert isinstance(history, list)
