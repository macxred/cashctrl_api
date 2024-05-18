"""
Module to extend the CashCtrlClient class with caching capabilities.
"""

import time
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional

class CachedCashCtrlClient(CashCtrlClient):
    """
    A subclass of CashCtrlClient that caches the results of list_accounts and
    list_tax_codes methods to avoid repeated API calls within a specified timeout.

    Users are responsible for invalidating the cache if the data is changed.
    Note: Changes on the server are not reflected until the cache is updated.
    """
    def __init__(self, *args, cache_timeout: int = 300, **kwargs):
        """
        Initializes the cached client with an optional cache timeout.

        Args:
            cache_timeout (int, optional): Timeout for cache in seconds. Defaults to 300 seconds.
            *args: Variable length argument list for the parent class.
            **kwargs: Arbitrary keyword arguments for the parent class.
        """
        super().__init__(*args, **kwargs)
        self._cache_timeout = cache_timeout
        self._accounts_cache: Optional[pd.DataFrame] = None
        self._accounts_cache_time: Optional[datetime] = None
        self._tax_codes_cache: Optional[pd.DataFrame] = None
        self._tax_codes_cache_time: Optional[datetime] = None

    @property
    def cache_timeout(self) -> int:
        """
        Gets the current cache timeout.

        Returns:
            int: The cache timeout in seconds.
        """
        return self._cache_timeout

    @cache_timeout.setter
    def cache_timeout(self, timeout: int) -> None:
        """
        Sets a new cache timeout.

        Args:
            timeout (int): The new cache timeout in seconds.
        """
        self._cache_timeout = timeout

    def list_accounts(self) -> pd.DataFrame:
        """
        Lists remote accounts with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.ACCOUNT_COLUMNS schema.
        """
        if self._accounts_cache is None or self._is_expired(self._accounts_cache_time):
            self._accounts_cache = super().list_accounts()
            self._accounts_cache_time = datetime.now()
        return self._accounts_cache

    def list_tax_codes(self) -> pd.DataFrame:
        """
        Lists remote tax codes with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.TAX_COLUMNS schema.
        """
        if self._tax_codes_cache is None or self._is_expired(self._tax_codes_cache_time):
            self._tax_codes_cache = super().list_tax_rates()
            self._tax_codes_cache_time = datetime.now()
        return self._tax_codes_cache

    def invalidate_accounts_cache(self) -> None:
        """
        Invalidates the cached accounts data.
        """
        self._accounts_cache = None
        self._accounts_cache_time = None

    def invalidate_tax_codes_cache(self) -> None:
        """
        Invalidates the cached tax codes data.
        """
        self._tax_codes_cache = None
        self._tax_codes_cache_time = None

    def account_from_id(self, id: int) -> float:
        """
        Retrieve the account number corresponding to a given id.

        Args:
            id (int): The id of the account.

        Returns:
            float: The account number associated with the provided id.

        Raises:
            ValueError: If no account is found for the given id or if multiple accounts are found.
        """
        df = self.list_accounts()
        result = df.loc[df['id'] == id, 'account']
        if result.empty:
            raise ValueError(f"No account found for id {id}")
        elif len(result) > 1:
            raise ValueError(f"Multiple accounts found for id {id}")
        else:
            return result.item()

    def account_to_id(self, account: float) -> int:
        """
        Retrieve the id corresponding to a given account number.

        Args:
            account (float): The account number.

        Returns:
            int: The id associated with the provided account number.

        Raises:
            ValueError: If no id is found for the given account number or if multiple ids are found.
        """
        df = self.list_accounts()
        result = df.loc[df['account'] == account, 'id']
        if result.empty:
            raise ValueError(f"No id found for account {account}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for account {account}")
        else:
            return result.item()

    def tax_code_from_id(self, id: int) -> str:
        """
        Retrieve the tax code name corresponding to a given id.

        Args:
            id (int): The id of the tax code.

        Returns:
            str: The tax code name associated with the provided id.

        Raises:
            ValueError: If no tax code is found for the given id or if multiple tax codes are found.
        """
        df = self.list_tax_codes()
        result = df.loc[df['id'] == id, 'name']
        if result.empty:
            raise ValueError(f"No tax code found for id {id}")
        elif len(result) > 1:
            raise ValueError(f"Multiple tax codes found for id {id}")
        else:
            return result.item()

    def tax_code_to_id(self, name: str) -> int:
        """
        Retrieve the id corresponding to a given tax code name.

        Args:
            name (str): The tax code name.

        Returns:
            int: The id associated with the provided tax code name.

        Raises:
            ValueError: If no id is found for the given tax code name or if multiple ids are found.
        """
        df = self.list_tax_codes()
        result = df.loc[df['name'] == name, 'id']
        if result.empty:
            raise ValueError(f"No id found for tax code {name}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for tax code {name}")
        else:
            return result.item()

    def _is_expired(self, cache_time: Optional[datetime]) -> bool:
        """
        Checks if the cache has expired based on the cache timeout.

        Args:
            cache_time (Optional[datetime]): The timestamp when the cache was last updated.

        Returns:
            bool: True if the cache is expired or cache_time is None, False otherwise.
        """
        if cache_time is None:
            return True
        return (datetime.now() - cache_time) > timedelta(seconds=self._cache_timeout)
