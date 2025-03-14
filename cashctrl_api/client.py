"""Module to interact with the REST API of the CashCtrl accounting service."""

from datetime import datetime
import json
from mimetypes import guess_type
import os
from pathlib import Path
import re
import time
from typing import Dict, List
import pandas as pd
from requests import HTTPError, request, RequestException, Response
import requests.exceptions
import urllib3.exceptions
from .decorators import timed_cache
from .constants import (
    ACCOUNT_COLUMNS,
    CACHE_TIMEOUT,
    CATEGORY_COLUMNS,
    CURRENCY_COLUMNS,
    FILE_COLUMNS,
    FISCAL_PERIOD_COLUMNS,
    JOURNAL_ENTRIES,
    PROFIT_CENTER_COLUMNS,
    TAX_COLUMNS
)
from consistent_df import enforce_dtypes
from .list_directory import list_directory


class CashCtrlClient:
    """A lightweight wrapper to interact with the CashCtrl REST API.

    See README on https://github.com/macxred/cashctrl_api for overview and usage examples.
    """

    # ----------------------------------------------------------------------
    # Constructor

    def __init__(self, organisation: str = None, api_key: str = None):
        """Initializes the API client with the organization's domain and API key.

        Args:
            organisation (str, optional): The sub-domain of the organization. Defaults to
                                          the `CC_API_ORGANISATION` environment variable.
            api_key (str, optional): API key for authenticating with the CashCtrl API.
                                     Defaults to the `CC_API_KEY` environment variable.
        """
        self._api_key = api_key if api_key is not None else os.getenv("CC_API_KEY")
        organisation = (
            organisation if organisation is not None else os.getenv("CC_API_ORGANISATION")
        )
        self._base_url = f"https://{organisation}.cashctrl.com/api/v1"

    # ----------------------------------------------------------------------
    # API Requests

    def request_with_retry(
            self, method: str, url: str, wait_time: float = 1, **kwargs
    ) -> Response:
        """Send an API request to CashCtrl with retry logic.

        Args:
            method (str): HTTP method to use for the request (e.g., 'GET', 'POST').
            url (str): The full URL for the API endpoint.
            wait_time (float): Time to wait between retries in seconds. Default is 1 second.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            requests.Response: The API response.

        Raises:
            HTTPError: If the API request fails with a non-200 status code.

        This method will retry the request up to three times in case of
        connection-related exceptions or a 429 status code (Too Many Requests).
        """
        retries = 3
        for attempt in range(retries):
            try:
                response = request(method, url, **kwargs)
                if response.status_code == 429 and attempt < retries - 1:
                    # Too Many Requests hit the API too quickly. See
                    # https://app.cashctrl.com/static/help/en/api/index.html#errors
                    time.sleep(wait_time)
                else:
                    break
            except (urllib3.exceptions.MaxRetryError,
                    requests.exceptions.ConnectionError) as e:
                attempt += 1
                if attempt < retries:
                    time.sleep(wait_time)
                else:
                    raise e

        if response.status_code != 200:
            raise HTTPError(
                f"API request failed with status {response.status_code}: {response.text}"
            )
        return response

    def request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> Response:
        """Send an API request with authentication token to CashCtrl.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.).
            endpoint (str): API endpoint to call (e.g. 'journal/read.json')
            data (dict, optional): The payload to send in the request.
            params (dict, optional): The parameters to append in the request URL.

        Returns:
            requests.Response: The API response.

        Raises:
            HTTPError: If the API request fails with non-200 status code.
        """
        data = data or {}
        params = params or {}

        def flatten(data):
            return {
                k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                for k, v in data.items()
            }

        url = f"{self._base_url}/{endpoint}"
        response = self.request_with_retry(method, url, auth=(self._api_key, ''),
                                           data=flatten(data), params=flatten(params))
        return response

    def json_request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> dict:
        """Send an API request to CashCtrl and process the response as json.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.).
            endpoint (str): API endpoint to call (e.g. 'journal/read.json')
            data (dict, optional): The payload to send in the request.
            params (dict, optional): The parameters to append in the request URL.

        Returns:
            dict: The parsed JSON response.

        Raises:
            RequestException: If the API call fails.
        """
        response = self.request(method, endpoint, data=data, params=params)
        result = response.json()
        if "success" in result and not result["success"]:
            msg = result.get("message", None)
            if msg is None:
                errors = result.get("errors", [])
                msg = [
                    (
                        f"{error['field']}: "
                        if "field" in error and error["field"] is not None
                        else ""
                    ) + error.get("message", "")
                    for error in errors
                    if "message" in error
                ]
                msg = " / ".join(msg)
            raise RequestException(f"API call failed. {msg}")
        return result

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
    # Categories

    def list_categories(
        self, resource: str, include_system: bool = False
    ) -> pd.DataFrame:
        r"""Retrieves and flattens the category tree for the specified resource
        into a DataFrame. Includes a 'path' column representing each category's
        hierarchical position in Unix-like file path format.

        Slashes ('/') in category names are replaced with backslashes ('\\')
        to ensure the slash character is reserved for separating hierarchy levels
        in path notation.

        Args:
            resource (str): Resource type ('account', 'file', etc.), for which
                            to fetch the category tree.
            include_system (bool, optional): If True, includes system-generated categories.

        Returns:
            pd.DataFrame: DataFrame with CashCtrlClient.CATEGORY_COLUMNS schema.
                Column 'path' indicates the category's hierarchical position.
        """

        def flatten_nodes(nodes, parent_path=""):
            """Recursive function to flatten category hierarchy."""
            if not isinstance(nodes, list):
                raise ValueError(f"Expected 'nodes' to be a list, got {type(nodes).__name__}.")
            rows = []
            for node in nodes:
                path = f"{parent_path}/{node['text'].replace('/', '\\')}"
                if "data" in node and node["data"] is not None:
                    data = node.pop("data")
                    rows.extend(flatten_nodes(data, path))
                rows.append({"path": path} | node)
            return rows

        data = self.get(f"{resource}/category/tree.json")["data"]
        df = pd.DataFrame(flatten_nodes(data.copy()))

        if resource == "account":
            columns = CATEGORY_COLUMNS | {"number": "Int64"}
        else:
            columns = CATEGORY_COLUMNS
        df = enforce_dtypes(df, columns)
        if not include_system:
            df = df.loc[~df["isSystem"], :]
            if resource == "file":
                # Remove first node (the system root) from paths
                df["path"] = df["path"].str.replace("^/+[^/]+", "", regex=True)

        return df.sort_values("path")

    def update_categories(
        self,
        resource: str,
        target: Dict[str, int] | List[str],
        delete: bool = False,
        ignore_account_root_nodes: bool = False,
    ):
        r"""Updates the server's category tree for a specified resource,
        synchronizing it with the provided category list.

        Backslashes ('\\') in category names are converted to slashes ('/').
        This allows slashes in category names while reserving the slash character
        as separator for hierarchy levels in path notation.

        Args:
            resource (str): Resource type ('account', 'file', etc.).
            target (Dict[str, int] | List[str]): Target category paths in Unix-like format.
                                                 Type of [str, int] is suitable only for 'account'
                                                 resource and represent key-value
                pairs of path and associated account number. Type of List[str] is suitable for the
                rest of the resources and should contain just a list of paths in string format.
            delete (bool, optional): If True, deletes categories not present in the provided list.
                                     Defaults to False.
            ignore_account_root_nodes (bool, optional): If True, silently ignores account root
                                                        categories. Account root nodes are
                                                        immutable in CashCtrl.

        Raises:
            ValueError: If the target type does not match the resource type.
        """
        if resource == "account" and not isinstance(target, dict):
            raise ValueError("Target should be a dict if resource == 'account'.")
        elif resource != "account" and isinstance(target, dict):
            raise ValueError("Target should be a list for resources other than 'account'.")

        category_list = self.list_categories(resource, include_system=(resource.lower() != "file"))
        categories = dict(zip(category_list["path"], category_list["id"]))

        if delete:
            if resource == "account":
                target_series = pd.Series(target.keys())
            else:
                target_series = pd.Series(target).unique()
            to_delete = [
                node
                for node in category_list["path"]
                if not target_series.str.startswith(node).any()
            ]
            # Silently ignore account category root nodes, they are immutable in CashCtrl
            if ignore_account_root_nodes and resource == "account":
                to_delete = [
                    path for path in to_delete if not re.fullmatch("/[^/]*", path)
                ]

            if to_delete:
                to_delete.sort(reverse=True)  # Delete from leaf to root
                delete_ids = [str(categories.pop(path)) for path in to_delete]
                self.post(
                    f"{resource}/category/delete.json", params={"ids": ",".join(delete_ids)}
                )

        # Update account category number if target differs from remote
        if resource == "account":
            for row in category_list.to_dict("records"):
                if row["path"] in target and row["number"] != target[row["path"]]:
                    if re.fullmatch("/[^/]*", row["path"]):
                        if not ignore_account_root_nodes:
                            raise ValueError(
                                f"Failed to update sequence number for '{row['path']}'. "
                                "Account root categories are immutable."
                            )
                    else:
                        params = {
                            "id": row["id"],
                            "name": row["text"],
                            "number": target[row["path"]],
                            "parentId": row["parentId"],
                        }
                        self.post("account/category/update.json", params=params)

        # Create missing categories
        missing_leaves = set(target).difference(categories).difference("/")
        for category in missing_leaves:
            nodes = category.split("/")
            for i in range(1, len(nodes)):
                node_path = "/".join(nodes[: i + 1])
                parent_path = "/".join(nodes[:i])
                if node_path not in categories:
                    params = {"name": nodes[i].replace("\\", "/")}
                    if parent_path:
                        params["parentId"] = categories[parent_path]
                    elif resource == "account":
                        raise ValueError(
                            f"Cannot create new root nodes for account categories: '{node_path}'."
                        )
                    if resource == "account":
                        params["number"] = target[category]
                    response = self.post(f"{resource}/category/create.json", params=params)
                    categories[node_path] = response["insertId"]

        if resource == "file":
            self.list_files.cache_clear()
        elif resource == "account":
            self.list_account_categories.cache_clear()

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_account_categories(self) -> pd.DataFrame:
        """Lists remote account categories with their attributes, and caches the result.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.CATEGORY_COLUMNS
                          | {'number': 'Int64'} schema.
        """
        return self.list_categories("account", include_system=True)

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
            ValueError: If the account category id does not exist.
        """
        df = self.list_account_categories()
        result = df.loc[df["id"] == id, "path"]
        if result.empty:
            raise ValueError(f"No path found for account category id: {id}")
        else:
            return result.item()

    # ----------------------------------------------------------------------
    # File Operations

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_files(self) -> pd.DataFrame:
        """List remote files with their attributes. Add the files' hierarchical
        position in the category tree in Unix-like filepath format.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.FILE_COLUMNS schema.
        """
        # get("file/list.json") returns by default the first 100 elements.
        # We override the size limit to download all values
        # https://app.cashctrl.com/static/help/en/api/index.html#/file/list.json
        response = self.get("file/list.json", params={"limit": 999999999999999999})
        files = pd.DataFrame(response["data"])
        date_columns = ["created", "lastUpdated", "dateArchived"]
        if not files.empty:
            for column in date_columns:
                files[column] = files[column].astype("datetime64[ns, Europe/Berlin]")
        columns_except_path = {
            key: value for key, value in FILE_COLUMNS.items() if key != "path"
        }
        df = enforce_dtypes(files, columns_except_path)
        if len(df) > 0:
            categories = self.list_categories("file")[["path", "id"]]
            categories = categories.rename(columns={"id": "categoryId"})
            df = df.merge(categories, on="categoryId", how="left")
            df["path"] = df["path"].fillna("") + "/" + df["name"]
        df = enforce_dtypes(df, FILE_COLUMNS)
        return df.sort_values("path")

    def file_id_to_path(self, id: int, allow_missing: bool = False) -> str | None:
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

    def file_path_to_id(self, path: str, allow_missing: bool = False) -> int | None:
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

    def upload_file(
        self,
        file: str | Path,
        id: int | str | None = None,
        name: str | None = None,
        category: int | str | None = None,
        mime_type: str | None = None,
    ) -> int:
        """Uploads a file to the server, marks it for persistent storage and,
        if a remote file `id` is provided, replaces an existing file.

        Args:
            file (str | Path): Path to the local file to upload.
            id (int | str | None, optional): ID of remote file to replace with new file.
            name (str | None, optional): The filename on the remote server;
                                         defaults to the local file's base name.
            category (int | str | None, optional): ID of category the file is stored in.
            mime_type (str | None, optional): The file's MIME type; guessed if not provided.

        Returns:
            int: The ID of the newly created or replaced file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the response does not contain exactly one file ID.
            HTTPError: If the file upload fails.
        """
        path = Path(file).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: '{file}'")
        files = [
            {
                "mimeType": (mime_type if mime_type is not None
                             else guess_type(path)[0] or "text/plain"),
                "name": name if name is not None else path.name,
                "categoryId": category,
            }
        ]
        response = self.post("file/prepare.json", params={"files": files})
        if len(response["data"]) != 1:
            raise ValueError("Expected response['data'] with length 1.")
        new_file_id = response["data"][0]["fileId"]
        write_url = response["data"][0]["writeUrl"]

        with open(path, "rb") as file:
            headers = {"Content-Type": "application/octet-stream"}
            response = self.request_with_retry("PUT", write_url, data=file, headers=headers,
                                               timeout=60)
        if response.status_code != 200:
            raise HTTPError(f"File upload failed: {response.reason}.")

        if id is None:
            self.post("file/persist.json", params={"ids": new_file_id})
            file_id = new_file_id
        else:
            params = {
                "id": id,
                "name": name if name is not None else path.name,
                "replaceWith": new_file_id,
                "categoryId": category,
            }
            self.post("file/update.json", params=params)
            file_id = int(id)

        self.list_files.cache_clear()
        return file_id

    def download_file(self, id: int | str, path: str | Path):
        """Downloads a file identified by a remote ID and saves it locally.

        Args:
            id (int | str): The remote file ID to download.
            path (str | Path): Local path to save the downloaded file.
        """
        response = self.request("GET", endpoint="file/get", params={"id": id})
        with open(Path(path).expanduser(), "wb") as file:
            file.write(response.content)

    def mirror_directory(
        self,
        directory: str | Path,
        delete_files: bool = False,
        delete_categories: bool = False,
    ):
        """Recursively mirrors a local directory on the CashCtrl server.

        Ensures that the remote file system reflects the state of the local
        directory, and that local sub-folders are mapped to remote categories.
        The method creates, updates, and optionally deletes files and
        categories (folders) on the server to match the local structure.

        Args:
            directory (str | Path): Path of the local directory to mirror.
            delete_files (bool, optional): If True, deletes remote files without
                                           a corresponding local file. Also empties
                                           the recycle bin to release references
                                           and allow for category deletion.
            delete_categories (bool, optional): If True, deletes unused categories
                                                (folders) on the server.
        """
        local_files = list_directory(directory, recursive=True, exclude_dirs=True)
        local_files["remote_path"] = "/" + local_files["path"]
        local_files["remote_category"] = [
            Path(p).parent.as_posix() for p in local_files["remote_path"]
        ]
        local_files["remote_category"] = local_files["remote_category"].astype(pd.StringDtype())
        remote_files = self.list_files()

        if delete_files:
            to_delete = remote_files["path"].duplicated(keep="first") | ~remote_files[
                "path"
            ].isin(local_files["remote_path"])
            if to_delete.any():
                ids = ",".join(remote_files.loc[to_delete, "id"].astype(str))
                params = {"ids": ids, "force": True}
                self.post("file/delete.json", params=params)
                remote_files = remote_files.loc[~to_delete, :]
            # Empty recycle bin to release references before category deletion
            self.post("file/empty_archive.json")

        self.update_categories(
            "file", target=local_files["remote_category"], delete=delete_categories
        )
        categories = self.list_categories("file")
        category_map = dict(zip(categories["path"], categories["id"]))
        category_map["/"] = None

        if remote_files["path"].duplicated().any():
            raise ValueError(
                "Some remote files are duplicated. Either use mirror_files(..., delete_files=True) "
                "or manually remove duplicates."
            )
        cols = {"path": "remote_path", "lastUpdated": "remote_modified_time"}
        df = local_files.merge(
            remote_files[["path", "lastUpdated", "id"]].rename(columns=cols),
            on="remote_path",
            how="left",
        )
        local_file_is_newer = (df["mtime"] > df["remote_modified_time"]).fillna(False)
        to_update = df.loc[local_file_is_newer, :]
        for local_file, remote_category, file_id in zip(
            to_update["path"], to_update["remote_category"], to_update["id"]
        ):
            self.upload_file(
                Path(directory) / local_file,
                category=category_map[remote_category], id=int(file_id)
            )

        to_upload = local_files.loc[
            ~local_files["remote_path"].isin(remote_files["path"]), :
        ]
        for local_file, remote_category in zip(
            to_upload["path"], to_upload["remote_category"]
        ):
            self.upload_file(
                Path(directory) / local_file, category=category_map[remote_category]
            )
        self.list_files.cache_clear()

    # ----------------------------------------------------------------------
    # Tax Rates

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_tax_rates(self) -> pd.DataFrame:
        """List remote tax rates with their attributes.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.TAX_COLUMNS schema.
        """
        tax_rates = pd.DataFrame(self.get("tax/list.json")["data"])
        df = enforce_dtypes(tax_rates, TAX_COLUMNS)
        return df.sort_values("name")

    def tax_code_from_id(self, id: int, allow_missing: bool = False) -> str | None:
        """Retrieve the tax code name corresponding to a given id.

        Args:
            id (int): The id of the tax code.
            allow_missing (boolean): If True, return None if the tax id does not exist.
                                     Otherwise raise a ValueError.

        Returns:
            str | None: The tax code name associated with the provided id.
                        or None if allow_missing is True and there is no such tax code.

        Raises:
            ValueError: If the tax id does not exist and allow_missing=False.
        """
        df = self.list_tax_rates()
        result = df.loc[df["id"] == id, "name"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No tax code found for id: {id}")
        else:
            return result.item()

    def tax_code_to_id(self, name: str, allow_missing: bool = False) -> int | None:
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

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_accounts(self) -> pd.DataFrame:
        """List remote accounts with their attributes, and Unix-style path
        representation of their hierarchical position in the category tree.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.ACCOUNT_COLUMNS schema.
        """
        accounts = pd.DataFrame(self.get("account/list.json")["data"])
        columns_except_path = {
            key: value for key, value in ACCOUNT_COLUMNS.items() if key != "path"
        }
        df = enforce_dtypes(accounts, columns_except_path)
        if len(df) > 0:
            categories = self.list_categories("account", include_system=True)[["path", "id"]]
            categories = categories.rename(columns={"id": "categoryId"})
            df = df.merge(categories, on="categoryId", how="left")
            df["path"] = df["path"].fillna("")
        df = enforce_dtypes(df, ACCOUNT_COLUMNS)
        return df.sort_values("number")

    def account_from_id(self, id: int, allow_missing: bool = False) -> int | None:
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

    def account_to_id(self, account: int, allow_missing: bool = False) -> int | None:
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

    def account_to_currency(self, account: int, allow_missing: bool = False) -> str | None:
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

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_currencies(self) -> pd.DataFrame:
        """Lists remote currencies with their attributes.

        Returns:
            pd.DataFrame: A DataFrame with currencies.
        """
        currencies = pd.DataFrame(self.get("currency/list.json")["data"])
        df = enforce_dtypes(currencies, CURRENCY_COLUMNS)
        return df.sort_values("code")

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

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_journal_entries(self, fiscal_period_id: int | None = None) -> pd.DataFrame:
        """List remote journal entries with their attributes.

        Args:
            fiscal_period_id (int | None, optional):
                - If None (default), retrieves entries for the current fiscal period.
                - If provided, retrieves entries for the specified fiscal period.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.JOURNAL_ENTRIES schema.
        """
        # get("journal/list.json") returns by default the first 100 elements.
        # We override the size limit to download all values
        # https://app.cashctrl.com/static/help/en/api/index.html#/journal/list.json
        params = {"limit": 999999999999999999, "fiscalPeriodId": fiscal_period_id}
        response = self.get("journal/list.json", params=params)
        journal_entries = pd.DataFrame(response["data"])
        df = enforce_dtypes(journal_entries, JOURNAL_ENTRIES)
        return df.sort_values("dateAdded")

    # ----------------------------------------------------------------------
    # Price

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: datetime.date = None
    ) -> float:
        """
        Retrieves the exchange rate for a given currency pair on a specific date.

        Args:
            from_currency (str): The currency code to convert from.
            to_currency (str): The currency code to convert to.
            date (datetime.date, optional): The date for which the exchange rate
                is requested. Defaults to None, which retrieves the latest rate.

        Returns:
            float: The exchange rate for the given currency pair.
        """
        params = {"from": from_currency, "to": to_currency, "date": date}
        response = self.request("GET", "currency/exchangerate", params=params)
        return response.json()

    # ----------------------------------------------------------------------
    # Profit Centers

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_profit_centers(self) -> pd.DataFrame:
        """List remote profit centers with their attributes.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.PROFIT_CENTER_COLUMNS schema.
        """
        profit_centers = pd.DataFrame(self.get("account/costcenter/list.json")["data"])
        df = enforce_dtypes(profit_centers, PROFIT_CENTER_COLUMNS)
        return df.sort_values("name")

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

    # ----------------------------------------------------------------------
    # Fiscal Periods

    @timed_cache(seconds=CACHE_TIMEOUT)
    def list_fiscal_periods(self) -> pd.DataFrame:
        """List remote fiscal periods with their attributes.

        Returns:
            pd.DataFrame: A DataFrame with FISCAL_PERIOD_SCHEMA applied.
        """
        fiscal_periods = pd.DataFrame(self.get("fiscalperiod/list.json")["data"])
        fiscal_periods = enforce_dtypes(fiscal_periods, FISCAL_PERIOD_COLUMNS)
        fp = fiscal_periods.sort_values("start").reset_index(drop=True)

        # Normalize start and end dates, dropping timezone information
        fp["start"] = fp["start"].dt.tz_localize(None).dt.floor("D")
        fp["end"] = fp["end"].dt.tz_localize(None).dt.floor("D")

        return fp

    def fiscal_period_from_id(self, id: int, allow_missing: bool = False) -> str | None:
        """Retrieve the fiscal period name corresponding to a given id.

        Args:
            id (int): The id of the fiscal period.
            allow_missing (bool): If True, return None if the fiscal period id does not exist.
                                Otherwise, raise a ValueError.

        Returns:
            str | None: The fiscal period name associated with the provided id,
                        or None if allow_missing is True and there is no such fiscal period.

        Raises:
            ValueError: If the fiscal period id does not exist and allow_missing=False.
        """
        df = self.list_fiscal_periods()
        result = df.query("id == @id")["name"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No fiscal period found for id: {id}")
        return result.item()

    def fiscal_period_to_id(self, name: str, allow_missing: bool = False) -> int | None:
        """Retrieve the id corresponding to a given fiscal period name.

        Args:
            name (str): The fiscal period name.
            allow_missing (bool): If True, return None if the fiscal period does not exist.
                                Otherwise, raise a ValueError.

        Returns:
            int | None: The id associated with the provided fiscal period name,
                        or None if allow_missing is True and there is no such fiscal period.

        Raises:
            ValueError: If the fiscal period does not exist and allow_missing=False,
                        or if the fiscal period is duplicated.
        """
        df = self.list_fiscal_periods()
        result = df.query("name == @name")["id"]
        if result.empty:
            if allow_missing:
                return None
            else:
                raise ValueError(f"No id found for fiscal period {name}")
        elif len(result) > 1:
            raise ValueError(f"Multiple ids found for fiscal period {name}")
        return result.item()
