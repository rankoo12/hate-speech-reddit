from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # Typed only to avoid import cycles at runtime
    from ..models import Post, UserPost


@runtime_checkable
class RedditClient(Protocol):
    """
    Minimal client abstraction for fetching Reddit data.

    Implementations are responsible for *how* data is collected
    (HTML scraping, official API, etc.), but they must return
    the core domain models used by the rest of the pipeline.
    """

    def fetch_new_posts(self, subreddit: str, limit: int = 100) -> List["Post"]:
        """
        Fetch recent posts for a subreddit, ordered newest-first.

        Implementations should:
        - respect the `limit` parameter (best-effort is acceptable),
        - return `Post` instances ready for scoring/enrichment.
        """
        raise NotImplementedError

    def fetch_user_history(self, username: str, since: datetime) -> List["UserPost"]:
        """
        Fetch user activity (posts/comments) since a given datetime.

        Implementations may:
        - cap the total number of items,
        - perform paging/scrolling as needed.

        The caller is responsible for any additional filtering or
        truncation based on business rules.
        """
        raise NotImplementedError


@dataclass
class RedditApiCredentials:
    """
    Simple container for Reddit API credentials.

    This is intentionally minimal and only models what we need
    for a PoC / fallback client. It is *not* a full OAuth model.
    """

    client_id: str
    client_secret: str
    user_agent: str

    @classmethod
    def from_env(cls) -> Optional["RedditApiCredentials"]:
        """
        Load credentials from environment variables.

        Expected variables:
        - REDDIT_CLIENT_ID
        - REDDIT_CLIENT_SECRET
        - REDDIT_USER_AGENT

        Returns None if any required variable is missing.
        """
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT")

        if not (client_id and client_secret and user_agent):
            return None

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )


class RedditApiClient(RedditClient):
    """
    PoC / untested Reddit API client.

    This client is *not* used by default. It is intended as a
    design-only example of how an official API client would plug
    into the existing pipeline:

    - It implements the same `RedditClient` interface used by the
      HTML scraper.
    - It is expected to be created only when:
        * a feature flag (e.g. USE_REDDIT_API) is enabled, AND
        * valid `RedditApiCredentials` are available.
    - Methods currently return empty lists and contain pseudo-code
      comments to outline the intended behavior.

    This keeps the PoC safe to import and instantiate even without
    real credentials or network access.
    """

    def __init__(self, credentials: RedditApiCredentials) -> None:
        self._credentials = credentials
        # Pseudo-code placeholders for a future real implementation:
        # - create a requests.Session()
        # - configure auth headers / token retrieval
        # - set a base URL and reasonable timeouts
        # These are intentionally omitted here to keep the PoC minimal.

    def fetch_new_posts(self, subreddit: str, limit: int = 100) -> List["Post"]:
        """
        PoC implementation: returns an empty list.

        In a real implementation, this would:
        - call the Reddit API (e.g. /r/{subreddit}/new),
        - normalize the JSON payload into `Post` objects,
        - respect the `limit` parameter best-effort.
        """
        # Pseudo-code outline for a real implementation:
        #
        # response = self._session.get(
        #     f"https://oauth.reddit.com/r/{subreddit}/new",
        #     params={"limit": limit},
        #     headers={"User-Agent": self._credentials.user_agent},
        #     timeout=10,
        # )
        # response.raise_for_status()
        # data = response.json()
        # return [self._convert_listing_item_to_post(item) for item in data["data"]["children"]]
        #
        # For the assignment, we keep this as a no-op that compiles.
        return []

    def fetch_user_history(self, username: str, since: datetime) -> List["UserPost"]:
        """
        PoC implementation: returns an empty list.

        In a real implementation, this would:
        - call the Reddit API for the user's posts/comments,
        - page through results until `since` is reached or a cap is hit,
        - normalize into `UserPost` objects used by enrichment.
        """
        # Pseudo-code outline for a real implementation:
        #
        # items: List[UserPost] = []
        # after: Optional[str] = None
        #
        # while True:
        #     response = self._session.get(
        #         f"https://oauth.reddit.com/user/{username}/submitted",
        #         params={"after": after, "limit": 100},
        #         headers={"User-Agent": self._credentials.user_agent},
        #         timeout=10,
        #     )
        #     response.raise_for_status()
        #     data = response.json()
        #
        #     batch = self._convert_listing_to_user_posts(data)
        #     if not batch:
        #         break
        #
        #     for item in batch:
        #         if item.created_utc < since:
        #             return items
        #         items.append(item)
        #
        #     after = data["data"].get("after")
        #     if not after:
        #         break
        #
        # return items
        #
        # For the assignment, we keep this as a no-op that compiles.
        return []
