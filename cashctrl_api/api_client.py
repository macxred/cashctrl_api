"""cashctrl_api_client

This module implements the CashCtrlAPIClient class, which facilitates interactions
with the CashCtrl REST API.

Example usage:
    from cashctrl_api import CashCtrlAPIClient

    client = CashCtrlAPIClient(organisation='myorg', api_key='secret')
    persons = client.get("person/list.json")
"""
import os, requests

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
        url = f"{self._base_url}/{endpoint}"
        response = requests.request(method, url, auth=(self._api_key, None), data=data, params=params)
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
