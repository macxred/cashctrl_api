import json, os, pandas as pd, requests
from mimetypes import guess_type
from pathlib import Path
from typing import List

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
        if mime_type is None: mime_type = guess_type(mypath)[0]

        # step (1/3): prepare
        myfilelist = [{"mimeType": mime_type, "name": remote_name}]
        if remote_category is not None:
            myfilelist['categoryId': remote_category]
        response = self.post("file/prepare.json", params={'files': myfilelist})
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

    def file_download(self, id: (int | str), file: (str | Path)):
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
