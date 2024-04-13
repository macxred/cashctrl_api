# Python Client for CashCtrl REST API

`cashctrl_api` is a lightweight Python package that streamlines interaction with the [CashCtrl REST API](https://app.cashctrl.com/static/help/en/api/index.html). This API serves [CashCtrl](https://cashctrl.com), a straightforward and effective online accounting software with a beautifully clear data model. Our package acts as a thin wrapper, efficiently routing requests through universal methods to the API without implementing individual endpoints.

In `cashctrl_api`, requests are typically transmitted through generic methods:

- `get()`, `post()`, `patch()`, `put()`, and `delete()` take an API `endpoint`, request parameters, and JSON payload as parameters and return the server's response as a JSON dictionary.

Specialized methods manage more complex tasks:
- `file_upload()` uploads a file and marks it for persistent storage.
- `file_download()` downloads a file and saves it to the local file system.
- `list_categories()` retrieves a category tree and flattens it to a pandas DataFrame.
- `update_categories()` synchronizes a remote category tree with a given list of category paths,
   adding new categories and optionally removing those that are no longer needed.
- `mirror_files()` (TODO) mirrors a local set of nested categories with the category tree on the server.
    to the server, mapping local sub-folders to categories on the remote server.

To use this Python client, you'll need a valid API key, which can be acquired from your CashCtrl account settings.

## Installation

Easily install the package using pip:

```bash
pip install https://github.com/macxred/cashctrl_api/tarball/main
```

## Basic Usage

Get started with the CashCtrl API client by following these steps:

```python
from cashctrl_api import CashCtrlAPIClient

# Initialize the client with your organization's name and API key
cc = CashCtrlAPIClient("<my_organisation>", api_key="<my_api_key>")

# Example: Create a new contact
contact = {
    "firstName": "Tina",
    "lastName": "Test",
    "addresses": [{
            "type": "MAIN",
            "address": "Teststreet 15",
            "zip": "1234",
            "city": "Testtown"
        }],
    "titleId": 2
}
response = cc.post("person/create.json", data=contact)
id = response["insertId"]

# Retrieve the newly created contact
response = cc.get("person/read.json", params={'id': id})
print(response)

# Delete the contact
response = cc.post("person/delete.json", params={'ids': id})
print(response)
```

For simplicity, API Key and organization can also be set as environment
variables `CC_API_KEY` and `CC_API_ORGANISATION`. For example, by setting both
variables in the shell when starting python:

```bash
CC_API_ORGANISATION=<myorg> CC_API_KEY=<mykey> python
```

This allows for an even simpler code snippet:
```python
from cashctrl_api import CashCtrlAPIClient
cc = CashCtrlAPIClient()
response = cc.get("person/list.json")
```

## Testing Strategy

We prefer pytest for its straightforward and readable syntax over the unittest
package. Tests are housed in the [cashctrl_api/tests](tests) directory.

Tests are automated through GitHub Actions after each commit, during pull
requests, and daily. When executed as GitHub Actions, tests utilize an API key
stored as a GitHub secret, connecting to a non-public CashCtrl Test
organization covered by MaCX ReD's subscription.


## Package Development and Contribution

We recommend using a virtual environment for package development:

```bash
python3 -m venv ~/.virtualenvs/env_name
source ~/.virtualenvs/env_name/bin/activate
```

To locally modify and test the package, clone the repository and run
`python setup.py develop` in the root folder. This method adds a symbolic link
to your development directory to Python's search path, ensuring any changes are
immediately available when (re-)loading the package.
