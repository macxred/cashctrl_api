"""
Module to interact with the REST API of the CashCtrl accounting service.
"""

import json
import os
from requests import request, put, Response, RequestException, HTTPError
from mimetypes import guess_type
from pathlib import Path
from typing import List
import pandas as pd
from .list_directory import list_directory
from .enforce_dtypes import enforce_dtypes

class CashCtrlClient:
    """
    A lightweight wrapper to interact with the CashCtrl REST API.

    See README on https://github.com/macxred/cashctrl_api for overview and
    usage examples.
    """
    CATEGORY_COLUMNS = {
            'id': 'int',
            'name': 'string[python]',
            'path': 'string[python]',
            'text': 'string[python]',
            'parentId': 'Int64',
            'created': 'datetime64[ns, Europe/Berlin]',
            'createdBy': 'string[python]',
            'lastUpdated': 'datetime64[ns, Europe/Berlin]',
            'lastUpdatedBy': 'string[python]',
            'cls': 'string[python]',
            'leaf': 'bool',
            'disableAdd': 'bool',
            'isSystem': 'bool',
    }
    FILE_COLUMNS = {
            'id': 'int',
            'name': 'string[python]',
            'path': 'string[python]',
            'description': 'string[python]',
            'notes': 'string[python]',
            'size': 'int',
            'mimeType': 'string[python]',
            'isAttached': 'bool',
            'attachedCount': 'int',
            'categoryId': 'Int64',
            'categoryName': 'string[python]',
            'created': 'datetime64[ns, Europe/Berlin]',
            'createdBy': 'string[python]',
            'lastUpdated': 'datetime64[ns, Europe/Berlin]',
            'lastUpdatedBy': 'string[python]',
            'dateArchived': 'datetime64[ns, Europe/Berlin]',
    }

    def __init__(self,
                 organisation: str = os.getenv("CC_API_ORGANISATION"),
                 api_key: str = os.getenv("CC_API_KEY")):
        """
        Initializes the API client with the organization's domain and API key.

        Args:
            organisation (str): The sub-domain of the organization. Defaults to
                                the `CC_API_ORGANISATION` environment variable.
            api_key (str): API key for authenticating with the CashCtrl API.
                           Defaults to the `CC_API_KEY` environment variable.
        """
        self._api_key = api_key
        self._base_url = f"https://{organisation}.cashctrl.com/api/v1"

    def request(self, method: str, endpoint: str, data: dict = {},
                params: dict = {}) -> Response:
        """
        Send a an API request to CashCtrl.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.).
            endpoint (str): API endpoint to call (e.g. 'journal/read.json')
            data (dict): The payload to send in the request.
            params (dict): The parameters to append in the request URL.

        Returns:
            requests.Response: The API response.

        Raises:
            HTTPError: If the API request fails with non-200 status code.
        """
        def flatten(data):
            return {k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                    for k, v in data.items()}

        url = f"{self._base_url}/{endpoint}"
        response = request(method, url, auth=(self._api_key, ''),
                           data=flatten(data), params=flatten(params))
        if response.status_code != 200:
            raise HTTPError("API request failed with status "
                            f"{response.status_code}: {response.text}")
        return response

    def json_request(self, method: str, endpoint: str, data: dict = {},
                     params: dict = {}) -> list | dict:
        """
        Send an API request to CashCtrl and process the response as json.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.).
            endpoint (str): API endpoint to call (e.g. 'journal/read.json')
            data (dict): The payload to send in the request.
            params (dict): The parameters to append in the request URL.

        Returns:
            list | dict: The parsed JSON response.

        Raises:
            RequestException: If the API call fails.
        """
        response = self.request(method, endpoint, data=data, params=params)
        result = response.json()
        if 'success' in result and not result['success']:
            msg = result.get('message', None)
            if msg is None:
                errors = result.get('errors', [])
                msg = [(f"{error['field']}: "
                            if 'field' in error and not error['field'] is None
                            else '') + error.get('message', '')
                       for error in errors if 'message' in error]
                msg = " / ".join(msg)
            raise RequestException(f"API call failed. {msg}")
        return result

    def get(self, endpoint: str, data: dict = {}, params: dict = {}) -> dict:
        """Send GET request. See json_request for args and return value."""
        return self.json_request("GET", endpoint, data=data, params=params)

    def post(self, endpoint: str, data: dict = {}, params: dict = {}) -> dict:
        """Send POST request. See json_request for args and return value."""
        return self.json_request("POST", endpoint, data=data, params=params)

    def put(self, endpoint: str, data: dict = {}, params: dict = {}) -> dict:
        """Send PUT request. See json_request for args and return value."""
        return self.json_request("PUT", endpoint, data=data, params=params)

    def delete(self, endpoint: str, data: dict = {},
               params: dict = {}) -> dict:
        """Send DELETE request. See json_request for args and return value."""
        return self.json_request("DELETE", endpoint, data=data, params=params)

    def upload_file(self,
                    file: str | Path,
                    id: int | str | None = None,
                    name: str | None = None,
                    category: int | str | None = None,
                    mime_type: str | None = None) -> int:
        """
        Uploads a file to the server, marks it for persistent storage and,
        if a remote file `id` is provided, replaces an existing file.

        Args:
            path (str | Path): Path to the local file to upload.
            id (int | str | None): id of remote file to replace with new file.
            name (str | None): The filename on the remote server;
                               defaults to the local file's base name.
            category (int | str | None): id of category the file is stored in.
            mime_type (str | None): The file's MIME type; guessed if not
                                    provided.

        Returns:
            int: The Id of the newly created or replaced file.
        """
        path = Path(file).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: '{file}'")
        files = [{
            'mimeType': mime_type if mime_type is not None
                                  else guess_type(path)[0] or 'text/plain',
            'name': name if name is not None else path.name,
            'categoryId': category}]
        response = self.post('file/prepare.json', params={'files': files})
        if len(response['data']) != 1:
            raise ValueError("Expected response['data'] with length 1.")
        new_file_id = response['data'][0]['fileId']
        write_url = response['data'][0]['writeUrl']

        with open(path, 'rb') as file:
            headers = {'Content-Type': 'application/octet-stream'}
            response = put(write_url, file, headers=headers)
        if response.status_code != 200:
            raise HTTPError(f'File upload failed: {response.reason}.')

        if id is None:
            self.post('file/persist.json', params={'ids': new_file_id})
            return new_file_id
        else:
            params = {'id': id,
                      'name': name if name is not None else path.name,
                      'replaceWith': new_file_id,
                      'categoryId': category}
            self.post('file/update.json', params=params)
            return int(id)

    def download_file(self, id: int | str, path: str | Path):
        """
        Downloads a file identified by a remote ID and saves it locally.

        Args:
            id (int | str): The remote file ID to download.
            path (str | Path): Local path to save the downloaded file.
        """
        response = self.request('GET', endpoint='file/get', params={'id': id})
        with open(Path(path).expanduser(), 'wb') as file:
            file.write(response.content)

    def list_categories(self, resource: str,
                        include_system: bool = False) -> pd.DataFrame:
        """
        Retrieves and flattens the category tree for the specified resource
        into a DataFrame. Includes a 'path' column representing each category's
        hierarchical position in Unix-like file path format.

        Args:
            resource (str): Resource type ('account', 'file', etc.),
                            for which to fetch the category tree.
            include_system (bool, optional): If True, includes system-generated
                                             categories.

        Returns:
            pd.DataFrame: DataFrame with CashCtrlClient.CATEGORY_COLUMNS
                          schema. Column 'path' indicates the category's
                          hierarchical position.
        """
        def flatten_nodes(nodes, parent_path=''):
            """ Recursive function to flatten category hierarchy. """
            if not isinstance(nodes, list):
                raise ValueError("Expected 'nodes' to be a list, "
                                 f"got {type(nodes).__name__}.")
            rows = []
            for node in nodes:
                path = f"{parent_path}/{node['text']}"
                if ('data' in node) and (not node['data'] is None):
                    data = node.pop('data')
                    rows.extend(flatten_nodes(data, path))
                rows.append({'path': path} | node)
            return rows

        data = self.get(f"{resource}/category/tree.json")['data']
        df = pd.DataFrame(flatten_nodes(data.copy()))
        df = enforce_dtypes(df, self.CATEGORY_COLUMNS)
        if not include_system:
            df = df.loc[~df['isSystem'], :]
            # Remove first node (the system root) from paths
            df['path'] = df['path'].str.replace('^/+[^/]+', '', regex=True)

        return df.sort_values('path')

    def update_categories(self, resource: str, target: List[str],
                        delete: bool = False):
        """
        Updates the server's category tree for a specified resource,
        synchronizing it with the provided category list.

        Args:
            resource (str): Resource type ('account', 'file', etc.).
            target (List[str]): Target category paths in Unix-like format.
            delete (bool, optional): If True, deletes categories not present
                                     in the provided list. Defaults to False.
        """
        category_list = self.list_categories(resource)
        categories = dict(zip(category_list['path'], category_list['id']))

        if delete:
            target_df = pd.Series(pd.Series(target).unique())
            to_delete = [node for node in category_list['path']
                        if not target_df.str.startswith(node).any()]
            if to_delete:
                to_delete.sort(reverse=True) # Delete from leaf to root
                delete_ids = [str(categories.pop(path)) for path in to_delete]
                self.post(f"{resource}/category/delete.json",
                          params={'ids': ','.join(delete_ids)})

        # Create missing categories
        missing_leaves = set(target).difference(categories).difference('/')
        for category in missing_leaves:
            nodes = category.split('/')
            for i in range(1, len(nodes)):
                node_path = '/'.join(nodes[:i + 1])
                parent_path = '/'.join(nodes[:i])
                if node_path not in categories:
                    params = {'name': nodes[i]}
                    if parent_path:
                        params['parentId'] = categories[parent_path]
                    response = self.post(f"{resource}/category/create.json",
                                         params=params)
                    categories[node_path] = response['insertId']


    def mirror_directory(self, directory: str | Path,
                        delete_files: bool = False,
                        delete_categories: bool = False):
        """
        Recursively mirrors a local directory on the CashCtrl server.

        Ensures that the remote file system reflects the state of the local
        directory, and that local sub-folders are mapped to remote categories.
        The method creates, updates, and optionally deletes files and
        categories (folders) on the server to match the local structure.

        Parameters:
            directory (str | Path): Path of the local directory to mirror.
            delete_files (bool, optional): If True, deletes remote files
                without a corresponding local file. Also empties the recycle
                bin to release references and allow for category deletion.
            delete_categories (bool, optional): If True, deletes unused
                categories (folders) on the server.
        """
        local_files = list_directory(directory, recursive=True,
                                     exclude_dirs=True)
        local_files['remote_path'] = '/' + local_files['path']
        local_files['remote_category'] = [Path(p).parent.as_posix()
                                        for p in local_files['remote_path']]
        local_files['remote_category'] = (
            local_files['remote_category'].astype( pd.StringDtype()))
        remote_files = self.list_files()

        if delete_files:
            to_delete = (
                remote_files['path'].duplicated(keep='first') |
                ~remote_files['path'].isin(local_files['remote_path'])
            )
            if to_delete.any():
                ids = ','.join(remote_files.loc[to_delete, 'id'].astype(str))
                params = {'ids': ids, 'force': True}
                self.post("file/delete.json", params=params)
                remote_files = remote_files.loc[~to_delete,:]
            # Empty recycle bin to release references before category deletion
            self.post("file/empty_archive.json")

        self.update_categories('file',
                               target=local_files['remote_category'],
                               delete=delete_categories)
        categories = self.list_categories('file')
        category_map = dict(zip(categories['path'], categories['id']))
        category_map['/'] = None

        if remote_files['path'].duplicated().any():
            raise ValueError("Some remote files are duplicated. Either use "
                            "mirror_files(..., delete_files=True) or manually "
                            "remove duplicates.")
        cols = {'path': 'remote_path', 'lastUpdated': 'remote_modified_time'}
        df = local_files.merge(
            remote_files[['path', 'lastUpdated', 'id']].rename(columns=cols),
            on='remote_path', how='left')
        local_file_is_newer = (
            df['mtime'] > df['remote_modified_time']).fillna(False)
        to_update = df.loc[local_file_is_newer, :]
        for local_file, remote_category, id in zip(to_update['path'],
                                                to_update['remote_category'],
                                                to_update['id']):
            self.upload_file(Path(directory) / local_file,
                            category=category_map[remote_category], id=id)

        to_upload = local_files.loc[
            ~local_files['remote_path'].isin(remote_files['path']), :]
        for local_file, remote_category in zip(to_upload['path'],
                                            to_upload['remote_category']):
            self.upload_file(Path(directory) / local_file,
                            category=category_map[remote_category])

    def list_files(self) -> pd.DataFrame:
        """
        List remote files with their attributes. Add the files' hierarchical
        position in the category tree in Unix-like filepath format.

        Returns:
            pd.DataFrame: A DataFrame with CashCtrlClient.FILE_COLUMNS schema.
        """
        files = pd.DataFrame(self.get("file/list.json")['data'])
        columns_except_path = {key: value for key, value
                               in self.FILE_COLUMNS.items() if key != 'path'}
        df = enforce_dtypes(files, columns_except_path)
        if len(df) > 0:
            categories = self.list_categories('file')[['path', 'id']]
            categories = categories.rename(columns={'id': 'categoryId'})
            df = df.merge(categories, on='categoryId', how='left')
            df['path'] = df['path'].fillna('') + '/' + df['name']
        df = enforce_dtypes(df, self.FILE_COLUMNS)
        return df.sort_values('path')
