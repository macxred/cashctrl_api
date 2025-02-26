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
        self._profit_centers_cache: Optional[pd.DataFrame] = None
        self._profit_centers_cache_time: Optional[datetime] = None

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

    def invalidate_profit_centers_cache(self) -> None:
        """Invalidates the cached profit centers data."""
        self._profit_centers_cache = None
        self._profit_centers_cache_time = None

    # ----------------------------------------------------------------------
    # Profit Centers

    def list_profit_centers(self) -> pd.DataFrame:
        """Lists remote profit centers with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.PROFIT_CENTER_COLUMNS schema.
        """
        if self._profit_centers_cache is None or self._is_expired(self._profit_centers_cache_time):
            self._profit_centers_cache = super().list_profit_centers()
            self._profit_centers_cache_time = datetime.now()
        return self._profit_centers_cache

    def profit_center_from_id(self, id: int, allow_missing: bool = False) -> str | None:
        """Retrieve the profit center name corresponding to a given id.

        Args:
            id (int): The id of the profit center.
            allow_missing (boolean): If True, return None if the profit center id does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            str | None: The profit center name associated with the provided id.
                        or None if allow_missing is True and there is no such profit center.

        Raises:
            ValueError: If the profit center id does not exist and allow_missing=False.
        """
        df = self.list_profit_centers()
        result = df.query("id == @id")["name"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No profit center found for id: {id}")
        else:
            return result.item()

    def profit_center_to_id(self, name: str, allow_missing: bool = False) -> int | None:
        """Retrieve the id corresponding to a given profit center name.

        Args:
            name (str): The profit center name.
            allow_missing (boolean): If True, return None if the profit center does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            int | None: The id associated with the provided profit center name.
                        or None if allow_missing is True and there is no such profit center.

        Raises:
            ValueError: If the profit center does not exist and allow_missing=False,
                        or if the profit center is duplicated.
        """
        df = self.list_profit_centers()
        result = df.query("name == @name")["id"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No id found for profit center {name}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for profit center {name}")
        else:
            return result.item()
