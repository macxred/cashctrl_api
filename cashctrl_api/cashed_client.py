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
        self._accounts_cache: Optional[pd.DataFrame] = None
        self._accounts_cache_time: Optional[datetime] = None
        self._currencies_cache: Optional[pd.DataFrame] = None
        self._currencies_cache_time: Optional[datetime] = None
        self._journal_cache: Optional[pd.DataFrame] = None
        self._journal_cache_time: Optional[datetime] = None
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

    def invalidate_accounts_cache(self) -> None:
        """Invalidates the cached accounts data."""
        self._accounts_cache = None
        self._accounts_cache_time = None

    def invalidate_currencies_cache(self) -> None:
        """Invalidates the cached currencies data."""
        self._currencies_cache = None
        self._currencies_cache_time = None

    def invalidate_journal_cache(self) -> None:
        """Invalidates the cached journal entries data."""
        self._journal_cache = None
        self._journal_cache_time = None

    def invalidate_profit_centers_cache(self) -> None:
        """Invalidates the cached profit centers data."""
        self._profit_centers_cache = None
        self._profit_centers_cache_time = None

    # ----------------------------------------------------------------------
    # Accounts

    def list_accounts(self) -> pd.DataFrame:
        """Lists remote accounts with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.ACCOUNT_COLUMNS schema.
        """
        if self._accounts_cache is None or self._is_expired(self._accounts_cache_time):
            self._accounts_cache = super().list_accounts()
            self._accounts_cache_time = datetime.now()
        return self._accounts_cache

    def account_from_id(self, id: int, allow_missing: bool = False) -> Optional[int]:
        """Retrieve the account number corresponding to a given id.

        Args:
            id (int): The id of the account.
            allow_missing (boolean): If True, return None if the account id does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            int | None: The account number associated with the provided id
                        or None if allow_missing is True and there is no such account.

        Raises:
            ValueError: If the id does not exist and allow_missing=False.
        """
        df = self.list_accounts()
        result = df.loc[df["id"] == id, "number"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No account found for id {id}")
        else:
            return result.item()

    def account_to_id(self, account: int, allow_missing: bool = False) -> Optional[int]:
        """Retrieve the id corresponding to a given account number.

        Args:
            account (int): The account number.
            allow_missing (boolean): If True, return None if the account number does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            int | None: The id associated with the provided account number.
                        or None if allow_missing is True and there is no such account.

        Raises:
            ValueError: If the account number does not exist and allow_missing=False,
                        or if the number is duplicated.
        """
        df = self.list_accounts()
        result = df.loc[df["number"] == account, "id"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No id found for account: {account}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for account: {account}")
        else:
            return result.item()

    def account_to_currency(self, account: int, allow_missing: bool = False) -> Optional[str]:
        """Retrieve the account currency corresponding to a given account number.

        Args:
            account (int): The account number.
            allow_missing (boolean): If True, return None if the account number does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            str | None: The currency associated with the provided account number.
                        or None if allow_missing is True and there is no such account.

        Raises:
            ValueError: If the account number does not exist and allow_missing=False,
                        or if the number is duplicated.
        """
        df = self.list_accounts()
        result = df.loc[df["number"] == account, "currencyCode"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No currency found for account: {account}")
        elif len(result) > 1:
            raise ValueError(f"Multiple currencies found for account: {account}")
        else:
            return result.item()

    # ----------------------------------------------------------------------
    # Currencies

    def list_currencies(self) -> pd.DataFrame:
        """Lists remote currencies with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with currencies.
        """
        if self._currencies_cache is None or self._is_expired(self._currencies_cache_time):
            self._currencies_cache = pd.DataFrame(self.get("currency/list.json")["data"])
            self._currencies_cache_time = datetime.now()
        return self._currencies_cache

    def currency_from_id(self, id: int) -> str:
        """Retrieve the currency corresponding to a given id.

        Args:
            id (int): The id of the currency.

        Returns:
            str: The currency name associated with the provided id.

        Raises:
            ValueError: If the currency id does not exist.
        """
        df = self.list_currencies()
        result = df.loc[df["id"] == id, "text"]
        if result.empty:
            raise ValueError(f"No currency found for id: {id}")
        else:
            return result.item()

    def currency_to_id(self, name: str) -> int:
        """Retrieve the id corresponding to a given currency name.

        Args:
            text (srt): The currency name.

        Returns:
            int: The id associated with the provided currency name.

        Raises:
            ValueError: If the currency does not exist or is duplicated.
        """
        df = self.list_currencies()
        result = df.loc[df["text"] == name, "id"]
        if result.empty:
            raise ValueError(f"No id found for currency: {name}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for currency: {name}")
        else:
            return result.item()

    # ----------------------------------------------------------------------
    # Ledger

    def list_journal_entries(self) -> pd.DataFrame:
        """Lists remote journal entries with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.JOURNAL_ENTRIES schema.
        """
        if self._journal_cache is None or self._is_expired(self._journal_cache_time):
            self._journal_cache = super().list_journal_entries()
            self._journal_cache_time = datetime.now()
        return self._journal_cache

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
