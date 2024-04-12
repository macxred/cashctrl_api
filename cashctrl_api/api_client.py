import json, os, pandas as pd, requests
from mimetypes import guess_type
from pathlib import Path

class CashCtrlAPIClient:
    """
    A lightweight wrapper to facilitate interactions with the CashCtrl REST API.

    See package README for an overview and for usage examples: https://github.com/macxred/cashctrl_api
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

    def _request(self, method, endpoint, data=None, params={}):

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
        result = response.json()

        # Enforce 'success' (if field is present)
        if ('success' in result) and (not result['success']):
            msg = result.get('message', None)
            if msg is None:
                errors = result.get('errors', [])
                msg = " / ".join(error.get('message', '')
                                 for error in errors if 'message' in error)
            if msg == '':
                msg = '(no message)'
            raise requests.RequestException(f"API call failed with message: {msg}")

        return result

    def get(self, endpoint, data=None, params={}):
        return self._request("GET", endpoint, data=data, params=params)

    def post(self, endpoint, data=None, params={}):
        return self._request("POST", endpoint, data=data, params=params)

    def put(self, endpoint, data=None, params={}):
        return self._request("PUT", endpoint, data=data, params=params)

    def delete(self, endpoint, data=None, params={}):
        return self._request("DELETE", endpoint=None, data=data, params=params)


    def file_upload(self, local_path, remote_name=None, remote_category=None, mime_type=None):
        """
        Uploads a file to the server and marks it for persistent storage.

        Parameters:
            local_path (str|Path): Path to a local file to upload.
            remote_name (str): The filename on the remote server; defaults to the name of the local file.
            remote_category (id, optional): The category under which the file should be stored.
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

        # step (1/3: prepare)
        if remote_category is None:
            myfilelist = [{"mimeType": mime_type, "name": remote_name}]
        else:
            myfilelist = [{"mimeType": mime_type, "name": remote_name, 'categoryId': remote_category}]
        response = self.post("file/prepare.json", params={'files': myfilelist})
        myid = response['data'][0]['fileId']
        write_url = response['data'][0]['writeUrl']

        # step (2/3): upload
        with open(mypath, 'rb') as f:
            response = requests.put(write_url, files={str(mypath): f})
        if response.status_code != 200:
            raise requests.RequestException(f"File upload failed (status {response.status_code}): {response.reason}.")

        # step (3/3): persist
        self.post("file/persist.json", params={'ids': myid})
        return myid


    def list_categories(self, object: str, system: bool=False) -> pd.DataFrame:
        """
        Retrieves a category tree and converts the nested categories into a flat pd.DataFrame.
        Each node's hierarchical position is described as a 'path' in Unix-like filepath format.
        The function works for all CashCtrl object types with associated category trees, such as 'account', 'file', etc.

        Parameters:
            object (str): Specifies the CashCtrl object type with an associated category tree.
                        Examples include 'account', 'file', etc.
            system (bool, optional): Determines whether system-generated nodes should be included in the result.
                                    If True, system nodes are included. If False (default), system nodes are excluded.

        Returns:
            pd.DataFrame: A DataFrame containing the flattened category tree. Each row represents a category,
                        with a 'path' column indicating the category's hierarchical position in Unix-like filepath format.
                        The path's root name depends on the object type and the current UI language setting.
                        Additional columns correspond to properties of each category node.
        """
        def flatten_data(nodes, parent_path=''):
            if not isinstance(nodes, list):
                raise ValueError(f"Expecting `nodes' to be a list, not {type(nodes)}.")
            rows = []
            for node in nodes:
                path = f"{parent_path}/{node['text']}"
                if ('data' in node) and (not node['data'] is None):
                    data = node.pop('data')
                    rows.extend(flatten_data(data, path))
                rows.append({'path': path} | node)
            return rows

        data = self.get(f"{object}/category/tree.json")['data']
        df = pd.DataFrame(flatten_data(data.copy()))
        df['level'] = df['path'].apply(lambda x: x.count(('/') - 1))
        if not system:
            df = df.loc[~df['isSystem'], :]
        return df.sort_values('path')
