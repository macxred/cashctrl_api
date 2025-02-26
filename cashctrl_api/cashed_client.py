"""Module to extend the CashCtrlClient class with caching capabilities."""

from datetime import datetime, timedelta
from typing import Optional
from cashctrl_api import CashCtrlClient
import pandas as pd


class CachedCashCtrlClient(CashCtrlClient):
    """A subclass of CashCtrlClient that caches the results of list_xy methods
    to avoid repeated API calls within a specified timeout.

    Users are responsible for invalidating the cache if the data is changed.
    Changes on the server are not reflected until the cache expires or is
    invalidated.
    """

    # ----------------------------------------------------------------------
    # Constructor

    def __init__(self, *args, cache_timeout: int = 300, **kwargs):
        """Initializes the cached client with an optional cache timeout.

        Args:
            cache_timeout (int, optional): Timeout for cache in seconds.
                                           Defaults to 300 seconds.
            *args: Variable length argument list for the parent class.
            **kwargs: Arbitrary keyword arguments for the parent class.
        """
        super().__init__(*args, **kwargs)
        self._cache_timeout = cache_timeout

    # ----------------------------------------------------------------------
    # Cache Invalidation

    @property
    def cache_timeout(self) -> int:
        """Gets the current cache timeout.

        Returns:
            int: The cache timeout in seconds.
        """
        return self._cache_timeout

    @cache_timeout.setter
    def cache_timeout(self, timeout: int) -> None:
        """Sets a new cache timeout.

        Args:
            timeout (int): The new cache timeout in seconds.
        """
        self._cache_timeout = timeout

    def _is_expired(self, cache_time: Optional[datetime]) -> bool:
        """Checks if the cache has expired based on the cache timeout.

        Args:
            cache_time (datetime | None): The timestamp when the cache was last updated.

        Returns:
            bool: True if the cache is expired or cache_time is None, False otherwise.
        """
        if cache_time is None:
            return True
        return (datetime.now() - cache_time) > timedelta(seconds=self._cache_timeout)
