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

        def flatten_dict(d):
            if d is None:
                return d
            else:
                return {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in d.items()}

        url = f"{self._base_url}/{endpoint}"
        response = requests.request(method, url, auth=(self._api_key, ''), data=flatten_dict(data), params=params)
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"API request failed with status {response.status_code}: {response.text}")
        return response.json()


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
            CashCtrlAPIClientError: If the file does not exist or there is a processing error.

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
        res_pers = self.post("file/persist.json", params={'ids': myid})
        if not res_pers['success']:
            raise CashCtrlAPIClientError(f"API file-persist call failed with message: {res_pers['message']}")
        return myid

    def file_delete(self, id):
        """Deletes a file specified by its ID from the server."""
        res_del = self.post("file/delete.json", params={'ids': id, 'force': True})
        if not res_del['success']:
            raise CashCtrlAPIClientError(f"API file-delete call failed with message: {res_del['message']}")
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

    def file_list(self):
        """Get a table with all files from the server."""
        res_flist = self.get("file/list.json")
        return pd.DataFrame(res_flist['data'])
