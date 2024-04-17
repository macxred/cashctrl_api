import json, os, pandas as pd, requests
from mimetypes import guess_type
from pathlib import Path
from typing import List
from .list_directory import list_directory

class CashCtrlAPIClient:
    """
    A lightweight wrapper to facilitate interactions with the CashCtrl REST API.

    For an overview and for usage examples, see README on https://github.com/macxred/cashctrl_api.
    """
    def __init__(self,
                 organisation=os.getenv("CC_API_ORGANISATION"),
                 api_key=os.getenv("CC_API_KEY")):
        """
        Parameters:
            organisation (str): The sub-domain of the organization as configured in CashCtrl.
                                Defaults to the value of the `CC_API_ORGANISATION`
                                environment variable if not explicitly provided.
            api_key (str): The API key used for authenticating with the CashCtrl API.
                        Defaults to the value of the `CC_API_KEY` environment variable
                        if not explicitly provided.
        """
        self._api_key = api_key
        self._base_url = f"https://{organisation}.cashctrl.com/api/v1"

    def _raw_request(self, method, endpoint, data=None, params={}):

        # The CashCtrl API does not accept nested json data structures,
        # we need to convert nested lists and dicts to string representation.
        # See https://forum.cashctrl.com/d/644-adresse-anlegen-ueber-api
        def flatten(d):
            if d is None:
                return None
            else:
                return {k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in d.items()}

        url = f"{self._base_url}/{endpoint}"
        response = requests.request(method, url, auth=(self._api_key, ''), data=flatten(data), params=flatten(params))
        if response.status_code != 200:
            raise requests.HTTPError(f"API request failed with status {response.status_code}: {response.text}")
        return response

    def _request(self, method, endpoint, data=None, params={}):
        response = self._raw_request(method=method, endpoint=endpoint, data=data, params=params)
        result = response.json()
        # Enforce 'success' (if field is present)
        if ('success' in result) and (not result['success']):
            msg = result.get('message', None)
            if msg is None:
                errors = result.get('errors', [])
                msg = [(f"{error.get('field', '')}: " if error.get('field', '') is not None else '') +
                       error.get('message', '') for error in errors if 'message' in error]
                msg = " / ".join(msg)
            raise requests.RequestException(f"API call failed. {msg}")

        return result

    def get(self, endpoint, data=None, params={}):
        return self._request("GET", endpoint, data=data, params=params)

    def post(self, endpoint, data=None, params={}):
        return self._request("POST", endpoint, data=data, params=params)

    def put(self, endpoint, data=None, params={}):
        return self._request("PUT", endpoint, data=data, params=params)

    def delete(self, endpoint, data=None, params={}):
        return self._request("DELETE", endpoint=None, data=data, params=params)


    def file_upload(self, local_path, id=None, remote_name=None, remote_category=None, mime_type=None):
        """
        Uploads a file to the server and marks it for persistent storage.

        Parameters:
            local_path (str|Path): Path to a local file to upload.
            id (int | str | None): Remote file id. If other than None, the remote file with given `id`
                is replaced with the newly uploaded file.
            remote_name (str): The filename on the remote server; defaults to the name of the local file.
            remote_category (int | str | None): The remote category id under which the file should be stored.
            mime_type (str, optional): The MIME type of the file. If None, the MIME type will be guessed from the file extension.

        Returns:
            The Id of the newly created object.
        """
        # init and checks
        mypath = Path(local_path).resolve()
        if not mypath.is_file():
            raise FileNotFoundError(f"File not found: '{mypath}'.")
        if remote_name is None: remote_name = mypath.name
        if mime_type is None:
            mime_type = guess_type(mypath)[0]
            if mime_type is None:
                # If MIME type can not be guessed, we use 'text' as default
                mime_type = 'text/plain'

        # step (1/3): prepare
        files = [{"mimeType": mime_type, "name": remote_name, 'categoryId': remote_category}]
        response = self.post("file/prepare.json", params={'files': files})
        if len(response['data']) != 1:
            raise ValueError("Expected response['data'] with length 1, got length {len(response['data'])}.")
        myid = response['data'][0]['fileId']
        write_url = response['data'][0]['writeUrl']

        # step (2/3): upload
        with open(mypath, 'rb') as f:
            response = requests.put(write_url, f,
                headers = {'Content-Type': 'application/octet-stream'})
        if response.status_code != 200:
            raise requests.RequestException(f"File upload failed (status {response.status_code}): {response.reason}.")

        # step (3/3): persist
        if id is None:
            self.post("file/persist.json", params={'ids': myid})
            return myid
        else:
            # Replace file with given remote file id
            params = {"id": id, "name": remote_name, "replaceWith": myid, "categoryId": remote_category}
            response = self.post("file/update.json", params=params)
            return id

    def file_download(self, id: int | str, file: str | Path):
        """
        Download a file identified by a remote id and save it to a local path.

        Parameters:
            id (int | str): The filename on the remote server; defaults to the name of the local file.
            path (str|Path): Path where to store the file.
        """
        response = self._raw_request('GET', endpoint='file/get', params={'id': id})
        with open(Path(file).resolve(), 'wb') as f:
            f.write(response.content)

    def list_categories(self, resource: str, include_system: bool = False) -> pd.DataFrame:
        """
        Retrieves a category tree from the specified resource type ('account', 'file', etc.) and flattens it into a
        DataFrame. The resulting DataFrame includes a 'path' column that represents each category's hierarchical
        position, formatted as a Unix-like filepath.

        Parameters:
            resource (str): Type of resource with an associated category tree (e.g., 'account', 'file').
            include_system (bool, optional): If True, includes system-generated nodes in the result if True.
                    Default is False, excluding system nodes and omitting the system root node in path names.

        Returns:
            pd.DataFrame: A DataFrame where each row represents a category. The 'path' column indicates the category's
                        hierarchical position. Additional columns correspond to properties of each category node.
        """
        def flatten_data(nodes, parent_path=''):
            if not isinstance(nodes, list):
                raise ValueError(f"Expected 'nodes' to be a list, got {type(nodes)}.")
            rows = []
            for node in nodes:
                path = f"{parent_path}/{node['text']}"
                if ('data' in node) and (not node['data'] is None):
                    data = node.pop('data')
                    rows.extend(flatten_data(data, path))
                rows.append({'path': path} | node)
            return rows

        data = self.get(f"{resource}/category/tree.json")['data']
        df = pd.DataFrame(flatten_data(data.copy()))
        df['id'] = df['id'].astype(int)
        df['path'] = df['path'].astype(pd.StringDtype())
        if not include_system:
            df = df.loc[~df['isSystem'], :]
            # Remove first node (the system root) from paths
            df['path'] = df['path'].str.replace('^/+[^/]+', '', regex=True)

        return df.sort_values('path')


    def update_categories(self, resource: str, categories: List[str], delete: bool = False) -> None:
        """
        Aligns the server's category tree for a given resource type ('account', 'file', etc.) with specified
        set of category paths. Categories that do not exist on the server will be created, and optionally,
        categories that do not appear in the list can be deleted.

        Parameters:
            resource (str): Type of resource (e.g., 'account', 'file') for which categories are managed.
            categories (List[str]): List of target category paths in Unix-like filepath format.
            delete (bool, optional): If True, deletes server categories that do not have corresponding local categories.
                                    Default is False.

        """
        remote_categories_df = self.list_categories(resource=resource)
        remote_categories = dict(zip(remote_categories_df['path'], remote_categories_df['id']))

        if delete:
            target_categories_df = pd.Series(categories)
            to_delete = [node for node in remote_categories_df['path']
                        if not target_categories_df.str.startswith(node).any()]
            if to_delete:
                # start deletion from leafs, progress towards root:
                to_delete.sort(reverse=True)
                delete_ids = [str(remote_categories.pop(node)) for node in to_delete]
                self.post(f"{resource}/category/delete.json", params={'ids': ','.join(delete_ids)})

        # Create missing categories
        missing_leaves = set(categories).difference(remote_categories).difference('/')
        for category in missing_leaves:
            nodes = category.split('/')
            for i in range(1, len(nodes)):
                node_path = '/'.join(nodes[:i+1])
                parent_path = '/'.join(nodes[:i])
                if node_path not in remote_categories:
                    params={'name': nodes[i]}
                    if parent_path != '':
                        params['parentId'] = remote_categories[parent_path]
                    response = self.post(f"{resource}/category/create.json", params=params)
                    remote_categories[node_path] = response['insertId']

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
        local_files = list_directory(directory, recursive=True, exclude_dirs=True)
        local_files['remote_path'] = '/' + local_files['path']
        local_files['remote_category'] = [str(Path(p).parent)
                                        for p in local_files['remote_path']]
        local_files['remote_category'] = local_files['remote_category'].astype(
            pd.StringDtype())
        remote_files = self.list_files()

        if delete_files:
            to_delete = (
                remote_files['path'].duplicated(keep='first') |
                ~remote_files['path'].isin(local_files['remote_path'])
            )
            if to_delete.any():
                ids = ','.join(remote_files.loc[to_delete, 'id'].astype(str))
                self.post("file/delete.json", params={'ids': ids, 'force': True})
                remote_files = remote_files.loc[~to_delete,:]
            # Empty recycle bin to release references before category deletion
            self.post("file/empty_archive.json")

        self.update_categories('file', categories=local_files['remote_category'],
                            delete=delete_categories)
        remote_categories = self.list_categories('file')
        category_map = dict(zip(remote_categories['path'], remote_categories['id']))
        category_map['/'] = None

        if remote_files['path'].duplicated().any():
            raise ValueError("Some remote files are duplicated. Either use "
                            "mirror_files(..., delete_files=True) or manually "
                            "remove duplicates.")
        df = local_files.merge(
            remote_files[['path', 'lastUpdated', 'id']].rename(
                columns={'path': 'remote_path', 'lastUpdated': 'remote_modified_time'}),
            on='remote_path', how='left')
        local_file_is_newer = (df['mtime'] > df['remote_modified_time']).fillna(False)
        to_update = df.loc[local_file_is_newer, :]
        for local_file, remote_category, id in zip(to_update['path'],
                                                to_update['remote_category'],
                                                to_update['id']):
            self.file_upload(Path(directory) / local_file,
                            remote_category=category_map[remote_category], id=id)

        to_upload = local_files.loc[~local_files['remote_path'].isin(remote_files['path']), :]
        for local_file, remote_category in zip(to_upload['path'],
                                            to_upload['remote_category']):
            self.file_upload(Path(directory) / local_file,
                            remote_category=category_map[remote_category])


    def list_files(self):
        """
        List remote files with their attributes. Add the files' hierarchical
        position in the category tree in Unix-like filepath format.

        Returns:
            pd.DataFrame: A DataFrame with columns 'name', 'path', 'categoryId',
                'created', 'lastUpdated', and 'id'. Timestamps are localized to
                'Europe/Berlin'.
        """
        files = pd.DataFrame(self.get("file/list.json")['data'])
        if len(files) > 0:
            files['categoryId'] = files['categoryId'].astype(pd.Int64Dtype())
            categories = self.list_categories('file')[['path', 'id']].rename(
                columns={'id': 'categoryId'})
            df = files.merge(categories, on='categoryId', how='left')
            df['path'] = df['path'].fillna('') + '/' + df['name']
            # The CashCtrl API returns CET, rather than UTC time
            df['created'] = pd.to_datetime(df['created']).dt.tz_localize(
                'Europe/Berlin')
            df['lastUpdated'] = pd.to_datetime(df['lastUpdated']).dt.tz_localize(
                'Europe/Berlin')
        else:
            df = pd.DataFrame({
                'name': pd.Series(dtype='string'),
                'path': pd.Series(dtype='string'),
                'categoryId': pd.Series(dtype='Int64'),
                'created': pd.Series(dtype='datetime64[ns, Europe/Berlin]'),
                'lastUpdated': pd.Series(dtype='datetime64[ns, Europe/Berlin]'),
                'id': pd.Series(dtype='int')
            })
        return df.sort_values('path')
