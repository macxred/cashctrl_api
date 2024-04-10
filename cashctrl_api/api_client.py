"""cashctrl_api_client

This module implements the CashCtrlAPIClient class, which facilitates interactions
with the CashCtrl REST API.

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

        url = f"{self._base_url}/{endpoint}"
        response = requests.request(method, url, auth=(self._api_key, ''), data=flat_data, params=params)
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


    def file_upload(self, name, local_path, remote_category=None, mime_type=None):
        """
        Uploads a file to the server under a specified category and with an optional MIME type.

        This function takes a file name and its local path to upload the file to the server. It optionally allows
        specifying the category under which the file should be uploaded and the MIME type of the file. If the MIME type
        is not specified, it attempts to determine it based on the file extension.

        Parameters:
            name (str): The name of the file.
            local_path (str): The local path where the file is stored. Either a directory or a full file path (enabling a different local filename).
            remote_category (str, optional): The category under which the file should be uploaded on the server.
            mime_type (str, optional): The MIME type of the file. If None, the MIME type will be guessed based on the file extension.

        Raises:
            CashCtrlAPIClientError: General errors like file not existing, bad HTML status code etc.
            CashCtrlAPINoSuccess: If the call indicates failure (i.e. has a 'Success' field with the value 'False')

        Returns:
            The Id of the newly created object.
        """
        mypath = Path(local_path)

        # local path and MIME type
        if mypath.is_file():
            if mime_type is None: mime_type = guess_type(mypath)[0]
            fname = str(mypath.resolve())
        else:
            mypath = mypath.joinpath(name).resolve()
            if not mypath.is_file():
                raise CashCtrlAPIClientError(f"File does not exist ('{mypath}')")
            if mime_type is None: mime_type = guess_type(mypath)[0]
            fname = str(mypath)

        # step (1/3: prepare)
        myfilelist = [{"mimeType": mime_type, "name": name}]
        res_prep = self.post("file/prepare.json", params={'files': json.dumps(myfilelist)})
        if not res_prep['success']:
            raise CashCtrlAPIClientError(f"API file-prepare call failed with message: {res_prep['message']}")
        myid = res_prep['data'][0]['fileId']
        write_url = res_prep['data'][0]['writeUrl']

        # step (2/3): upload)
        with open(fname, 'rb') as f:
            res_put = requests.put(write_url, files={fname: f})
        if res_put.status_code != 200:
            raise CashCtrlAPIClientError(f"API file-put call failed ({res_put.reason} / {res_put.status_code}")

        # step (3/3): persist)
        self.post("file/persist.json", params={'ids': myid})
        return myid

    def file_delete(self, id):
        """Deletes a file specified by its ID from the server."""
        self.post("file/delete.json", params={'ids': id, 'force': True})
        return None

    def _file_get_Id(self, name, remote_category):
        """Map a filename to its id, fails if there are more than one file with the same name."""
        # FIXME: remote_category support is missing
        # FIXME: should several names be supported, e.g. give back id of first found name
        res_flist = self.get("file/list.json")
        findid = -1
        for f in res_flist['data']:
                if name == f['name']:
                        if findid > -1:
                                raise CashCtrlAPIClientError(f"There are more than one files with the same name '{name}'")
                        findid = f['id']
        return findid

    def file_remove(self, name, remote_category=None):
        """
        Removes a file specified by its name from the server.

        If there are more than one file with the same name, the function fails.
        """
        # FIXME: should remove all be supported and/or first found?
        findid = self._file_get_Id(name, remote_category)
        if findid > -1:
            return self.file_delete(findid)

    def list_categories(self, object: str, system: bool=False) -> pd.DataFrame:
        """
        Params:
        - object (str): a CashCtrl object with a category tree, e.g. 'file', etc.
        - system (bool): if True, return system nodes. Otherwise silently drop system nodes.
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

    def file_list(self):
        """Get a table with all files from the server."""
        res_flist = self.get("file/list.json")
        return pd.DataFrame(res_flist['data'])

    def filepath_list(self):
        """Get a table with all files incl. path (i.e. category) from the server."""
        xcat = self.list_categories('file')
        xcat.rename(columns={'id': 'catId'}, inplace=True)

        xfile = self.file_list()
        xfile = xfile[['id', 'categoryId', 'name', 'mimeType', 'created', 'lastUpdated']]
        xfile = xfile.sort_values(['categoryId', 'name'])

        merged_df = pd.merge(xfile, xcat[['catId', 'text', 'path']], left_on='categoryId', right_on='catId', how='left')
        merged_df['path'] = merged_df['path'] + '/' + merged_df['name']
        merged_df.drop(['text', 'catId'], axis=1, inplace=True)
        merged_df.rename(columns={'name': 'filename'}, inplace=True)
        merged_df.rename(columns={'categoryId': 'catId'}, inplace=True)
        merged_df = merged_df[['id', 'catId', 'filename', 'path', 'created', 'lastUpdated' ]]

        return merged_df
