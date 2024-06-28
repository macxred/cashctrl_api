# Python Client for CashCtrl REST API

[![codecov](https://codecov.io/gh/lasuk/cashctrl_api/branch/main/graph/badge.svg)](https://codecov.io/gh/lasuk/cashctrl_api)

`cashctrl_api` is a lightweight Python package that implements the
CashCtrlClient class for interactions with the
[CashCtrl REST API](https://app.cashctrl.com/static/help/en/api/index.html).
This API serves [CashCtrl](https://cashctrl.com), a straightforward and
effective online accounting software with a clean data model and a clear
REST API. Our package acts as a thin wrapper, efficiently routing requests
through universal methods to the API without the need for implementing
individual endpoints.

`CashCtrlClient` provides generic methods to transmit typical requests:

- `get()`, `post()`, `patch()`, `put()`, and `delete()` take an API `endpoint`,
  request parameters, and a JSON payload as arguments, and return the server's
  response as a JSON dictionary.

Specialized methods manage categories and files:
- `list_categories()` retrieves a category tree and flattens it into a pandas
  DataFrame.
- `update_categories()` updates a category tree on the server with a given
   list of category paths, adding new categories and optionally removing
   those that are no longer needed.
- `list_files()` lists remote files, their attributes, and Unix-style path
  representations of their hierarchical position in the category tree.
- `list_tax_rates()` List remote tax rates with their attributes.
- `list_accounts()` List remote accounts with their attributes, and
  Unix-style path representation of their hierarchical position in the
  category tree.
- `list_journal_entries()` List remote journal entries with their attributes.
- `upload_file()` uploads a file from the local file system to the server,
  and optionally replaces an existing remote file.
- `download_file()` downloads a file from the server and saves it to the local
  file system.
- `mirror_files()` mirrors a local set of nested categories with the category
  tree on the server, mapping local sub-folders to categories on the remote
  server.


## Credentials

An active Pro subscription is required to interact with your CashCtrl account
via the API. New users can explore the Pro version with a free 30-day trial.
Software developers can create a new test account when the trial period
expires, as they generally do not mind the data loss associated with switching
accounts.

To set up a free test account, follow these steps:

1. Go to https://cashctrl.com/en.
2. 'Sign up' for an account using an email address and an organization name;
    accept the terms and conditions.
3. A confirmation email with an activation link and a password will be sent.
    The activation link brings up a 'First Steps' page.
4. On the 'First Steps' dialog, select 'Try the PRO demo' and
   confirm with 'Update to PRO'.
5. Navigate to Settings (gear icon in the top right corner) ->
   Users & roles -> Add (plus icon) -> Add [API User].
6. Assign the role of 'Administrator' and generate an API key.

The organization name and API key will be used to authenticate API requests.

## Installation

Easily install the package using pip:

```bash
pip install https://github.com/macxred/cashctrl_api/tarball/main
```


## Basic Usage

Get started with the CashCtrl API client by following these steps:

```python
from cashctrl_api import CashCtrlClient

# Initialize the client with your organization's name and API key
cc_client = CashCtrlClient("<my_organisation>", api_key="<my_api_key>")

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
response = cc_client.post("person/create.json", data=contact)
id = response["insertId"]

# Retrieve the newly created contact
response = cc_client.get("person/read.json", params={'id': id})
print(response)

# Delete the contact
response = cc_client.post("person/delete.json", params={'ids': id})
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
from cashctrl_api import CashCtrlClient
cc_client = CashCtrlClient()
response = cc_client.get("person/list.json")
```

## Package Development and Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Testing Strategy
- Setting Up Your Development Environment
- Type Consistency with DataFrames
- Standards and Best Practices
- Leveraging AI Tools
- Shared Learning thru Open Source
