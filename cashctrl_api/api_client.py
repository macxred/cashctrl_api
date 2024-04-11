"""cashctrl_api_client
This module implements the CashCtrlAPIClient class, which facilitates interactions
with the CashCtrl REST API.

Requests are typically transmitted through generic methods:
  - `get()`, `post()`, `patch()`, `put()`, and `delete()` take an API
      `endpoint`, request parameters, and JSON payload as parameters and return
      the server's response as a JSON dictionary.
    
Specialized methods manage more complex tasks:
  - `file_upload()` uploads files and marks it as persistent.
  - `list_categories()` retrieves a category tree and converts the nested categories into a flat pd.DataFrame.

Last but not least there are (company) specific tasks, like e.g.:
  - mirror_files

Example usage:
    from cashctrl_api import CashCtrlAPIClient

    client = CashCtrlAPIClient(organisation='myorg', api_key='secret')
    persons = client.get("person/list.json")
"""
import json, os, pandas as pd, requests
from mimetypes import guess_type
from pathlib import Path
from .errors import CashCtrlAPIClientError
from .errors import CashCtrlAPINoSuccess

class CashCtrlAPIClient:
    """
    A client for interacting with the CashCtrl REST API.

    Attributes:
        organisation (str): The sub-domain of the organization as configured in CashCtrl.
                            Defaults to the value of the `CC_API_ORGANISATION`
                            environment variable if not explicitly provided.
        api_key (str): The API key used for authenticating with the CashCtrl API.
                       Defaults to the value of the `CC_API_KEY` environment variable
                       if not explicitly provided.
    """
    def __init__(self,
                 organisation=os.getenv("CC_API_ORGANISATION"),
                 api_key=os.getenv("CC_API_KEY")):
        self._api_key = api_key
        self._base_url = f"https://{organisation}.cashctrl.com/api/v1"

    def _request(self, method, endpoint, data=None, params={}):

        # The CashCtrl API does not accept nested json data structures,
        # we need to convert nested lists and dicts to string representation.
        # See https://forum.cashctrl.com/d/644-adresse-anlegen-ueber-api
        if data is None:
            flat_data = None
        else:
            flat_data = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in data.items()}
        if params is None:
            flat_params = None
        else:
            flat_params = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in params.items()}

        url = f"{self._base_url}/{endpoint}"
        response = requests.request(method, url, auth=(self._api_key, ''), data=flat_data, params=flat_params)
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"API request failed with status {response.status_code}: {response.text}")
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
            raise CashCtrlAPINoSuccess(f"API call failed with message: {msg}")

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
        Uploads a file to the server under a specified category and with an optional MIME type.

        Parameters:
            local_path (str|Path): A valid path to the local file.
            remote_name (str): The filename on the remote server; defaults to 'basename(local_path)'
            remote_category (id, optional): The category under which the file should be uploaded on the server.
            mime_type (str, optional): The MIME type of the file. If None, the MIME type will be guessed based on the file extension.

        Returns:
            The Id of the newly created object.
        """
        # init and checks
        mypath = Path(local_path).resolve()
        if not mypath.is_file():
            raise CashCtrlAPIClientError(f"File does not exist ('{mypath}')")
        if remote_name is None: remote_name = mypath.name
        if mime_type is None: mime_type = guess_type(mypath)[0]

        # step (1/3: prepare)
        myfilelist = [{"mimeType": mime_type, "name": remote_name}]
        response = self.post("file/prepare.json", params={'files': myfilelist})
        myid = response['data'][0]['fileId']
        write_url = response['data'][0]['writeUrl']

        # step (2/3): upload)
        with open(mypath, 'rb') as f:
            response = requests.put(write_url, files={str(mypath): f})
        if response.status_code != 200:
            raise CashCtrlAPIClientError(f"API file-put call failed ({response.reason} / {response.status_code}")

        # step (3/3): persist)
        self.post("file/persist.json", params={'ids': myid})
        return myid

    def list_categories(self, object: str, system: bool=False) -> pd.DataFrame:
        """
        Retrieves a category tree for a given CashCtrl object and converts it into a Pandas DataFrame.
        Each category's nested structure is represented as a flat 'path' in Unix-like filepath format.
        The root name in the 'path' field is dynamic and depends on the object type and the current UI language setting.

        This function is designed to work with different CashCtrl objects that have associated category trees,
        such as 'account', 'file', etc. It can optionally include or exclude system nodes based on the 'system' parameter.

        Parameters:
            object (str): Specifies the CashCtrl object type with an associated category tree.
                        Examples include 'account', 'file', etc.
            system (bool, optional): Determines whether system nodes should be included in the result.
                                    If True, system nodes are included. If False (default), system nodes are excluded.

        Returns:
            pd.DataFrame: A DataFrame containing the flattened category tree. Each row represents a category,
                        with a 'path' column indicating the category's hierarchical position in Unix-like filepath format.
                        Additional columns correspond to properties of each category node.

        Raises:
            ValueError: If 'object' is not a supported CashCtrl object type or if 'nodes' parameter
                        expected in the nested 'flatten_data' function is not a list.

        Example:
            >>> list_categories('account')
            Returns a DataFrame with the categories' paths and details for the 'account' object, excluding system nodes.
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
        if not system:
            df = df.loc[~df['isSystem'], :]
        return df.sort_values('path')
