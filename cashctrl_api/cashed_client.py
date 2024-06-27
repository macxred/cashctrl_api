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
    # Constructors

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
        self._account_categories_cache: Optional[pd.DataFrame] = None
        self._account_categories_cache_time: Optional[datetime] = None
        self._journal_cache: Optional[pd.DataFrame] = None
        self._journal_cache_time: Optional[datetime] = None
        self._tax_rates_cache: Optional[pd.DataFrame] = None
        self._tax_rates_cache_time: Optional[datetime] = None
        self._files_cache: Optional[pd.DataFrame] = None
        self._files_cache_time: Optional[datetime] = None

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

    # ----------------------------------------------------------------------
    # Helper Methods

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

    # ----------------------------------------------------------------------
    # API Requests

    def get(self, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Send GET request. See json_request for args and return value."""
        return self.json_request("GET", endpoint, data=data, params=params)

    def post(self, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Send POST request. See json_request for args and return value."""
        return self.json_request("POST", endpoint, data=data, params=params)

    def put(self, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Send PUT request. See json_request for args and return value."""
        return self.json_request("PUT", endpoint, data=data, params=params)

    def delete(self, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Send DELETE request. See json_request for args and return value."""
        return self.json_request("DELETE", endpoint, data=data, params=params)

    # ----------------------------------------------------------------------
    # File Operations

    def list_files(self) -> pd.DataFrame:
        """List remote files with their attributes. Add the files' hierarchical
        position in the category tree in Unix-like filepath format.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.FILE_COLUMNS schema.
        """
        if self._files_cache is None or self._is_expired(self._files_cache_time):
            self._files_cache = super().list_files()
            self._files_cache_time = datetime.now()
        return self._files_cache

    def file_id_to_path(self, id: int, allow_missing: bool = False) -> Optional[str]:
        """Retrieve the file path corresponding to a given id.

        Returns:
            str | None: The file path associated with the provided id
                        or None if allow_missing is True and there is no such file path.
        """
        df = self.list_files()
        result = df.loc[df["id"] == id, "path"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No path found for id: {id}")
        elif len(result) > 1:
            raise ValueError(f"Multiple paths found for id: {id}")
        else:
            return result.item()

    def file_path_to_id(self, path: str, allow_missing: bool = False) -> Optional[int]:
        """Retrieve the file id corresponding to a given file path.

        Returns:
            int | None: The id associated with the file path
                        or None if allow_missing is True and there is no such file id.
        """
        df = self.list_files()
        result = df.loc[df["path"] == path, "id"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No id found for path: {path}")
        elif len(result) > 1:
            raise ValueError(f"Multiple id found for path: {path}")
        else:
            return result.item()

    def mirror_directory(self, *args, **kwargs):
        super().mirror_directory(*args, **kwargs)
        self.invalidate_files_cache()

    def upload_file(self, *args, **kwargs) -> int:
        super().upload_file(*args, **kwargs)
        self.invalidate_files_cache()

    def update_categories(self, resource: str, *args, **kwargs):
        super().update_categories(resource, *args, **kwargs)
        if resource == "file":
            self.invalidate_files_cache()
        elif resource == "account":
            self.invalidate_account_categories_cache()

    # ----------------------------------------------------------------------
    # Tax Rates

    def list_tax_rates(self) -> pd.DataFrame:
        """Lists remote tax rates with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.TAX_COLUMNS schema.
        """
        if self._tax_rates_cache is None or self._is_expired(self._tax_rates_cache_time):
            self._tax_rates_cache = super().list_tax_rates()
            self._tax_rates_cache_time = datetime.now()
        return self._tax_rates_cache

    def tax_code_from_id(self, id: int, allow_missing: bool = False) -> Optional[str]:
        """Retrieve the tax code name corresponding to a given id.

        Args:
            id (int): The id of the tax code.
            allow_missing (boolean): If True, return None if the tax id does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            str | None: The tax code name associated with the provided id.
                        or None if allow_missing is True and there is no such tax code.

        Raises:
            ValueError: If the tax id does not exist and allow_missing=False,
                        or if the id is duplicated.
        """
        df = self.list_tax_rates()
        result = df.loc[df["id"] == id, "name"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No tax code found for id: {id}")
        elif len(result) > 1:
            raise ValueError(f"Multiple tax codes found for id: {id}")
        else:
            return result.item()

    def tax_code_to_id(self, name: str, allow_missing: bool = False) -> Optional[int]:
        """Retrieve the id corresponding to a given tax code name.

        Args:
            name (str): The tax code name.
            allow_missing (boolean): If True, return None if the tax code does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            int | None: The id associated with the provided tax code name.
                        or None if allow_missing is True and there is no such tax code.

        Raises:
            ValueError: If the tax code does not exist and allow_missing=False,
                        or if the tax code is duplicated.
        """
        df = self.list_tax_rates()
        result = df.loc[df["name"] == name, "id"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No id found for tax code {name}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for tax code {name}")
        else:
            return result.item()

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
            ValueError: If the id does not exist and allow_missing=False,
            or if the id is duplicated.
        """
        df = self.list_accounts()
        result = df.loc[df["id"] == id, "number"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No account found for id {id}")
        elif len(result) > 1:
            raise ValueError(f"Multiple accounts found for id {id}")
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
            ValueError: If the currency id does not exist or is duplicated.
        """
        df = self.list_currencies()
        result = df.loc[df["id"] == id, "text"]
        if result.empty:
            raise ValueError(f"No currency found for id: {id}")
        elif len(result) > 1:
            raise ValueError(f"Multiple currencies found for id: {id}")
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
    # Categories

    def list_account_categories(self) -> pd.DataFrame:
        """Lists remote account categories with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.CATEGORY_COLUMNS
                          | {'number': 'Int64'} schema.
        """
        if (
            self._account_categories_cache is None
            or self._is_expired(self._account_categories_cache_time)
        ):
            self._account_categories_cache = self.list_categories(
                "account", include_system=True
            )
            self._account_categories_cache_time = datetime.now()
        return self._account_categories_cache

    def account_category_to_id(self, path: str) -> int:
        """Retrieve the id corresponding to a given category path.

        Args:
            path (str): The path of category.

        Returns:
            int: The id associated with the provided category path.

        Raises:
            ValueError: If the account category path does not exist or is duplicated.
        """
        df = self.list_account_categories()
        result = df.loc[df["path"] == path, "id"]
        if result.empty:
            raise ValueError(f"No id found for account category path: {path}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for category path: {path}")
        else:
            return result.item()

    def account_category_from_id(self, id: int) -> int:
        """Retrieve the path corresponding to a given account category id.

        Args:
            id (int): The id of category path.

        Returns:
            path: The path associated with the provided account category id.

        Raises:
            ValueError: If the account category id does not exist or is duplicated.
        """
        df = self.list_account_categories()
        result = df.loc[df["id"] == id, "path"]
        if result.empty:
            raise ValueError(f"No path found for account category id: {id}")
        elif len(result) > 1:
            raise ValueError(f"Multiple paths found for account category id: {id}")
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
    # Cache Invalidation

    def invalidate_accounts_cache(self) -> None:
        """Invalidates the cached accounts data."""
        self._accounts_cache = None
        self._accounts_cache_time = None

    def invalidate_tax_rates_cache(self) -> None:
        """Invalidates the cached tax rates data."""
        self._tax_rates_cache = None
        self._tax_rates_cache_time = None

    def invalidate_currencies_cache(self) -> None:
        """Invalidates the cached currencies data."""
        self._currencies_cache = None
        self._currencies_cache_time = None

    def invalidate_account_categories_cache(self) -> None:
        """Invalidates the cached account categories data."""
        self._account_categories_cache = None
        self._account_categories_cache_time = None

    def invalidate_journal_cache(self) -> None:
        """Invalidates the cached journal entries data."""
        self._journal_cache = None
        self._journal_cache_time = None

    def invalidate_files_cache(self) -> None:
        """Invalidates the cached files data."""
        self._files_cache = None
        self._files_cache_time = None
