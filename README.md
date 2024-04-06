# Python Client for CashCtrl REST API

cashctrl_api is a lightweight Python package designed to facilitate connections
to the [CashCtrl](https://cashctrl.com) REST API, a concise online accounting
software. It is designed as a thin wrapper that routes requests via
universal methods and does not implement individual endpoints.

Most GET, POST, PATCH, PUT and DELETE requests are transmitted via generic
`get()`, `post()`, `patch()`, `put()` and `delete()` methods. These methods take
an API `endpoint`, request parameters and json payload as arguments and return
the server's response as a `requests.Response` object.

To use this Python client, you'll need a valid API key which can be obtained
from your CashCtrl account settings.

## Installation

```bash
pip install git+ssh://git@github.com/macxred/cashctrl_api.git
```

To update an existing installation to the latest version, use:
```bash
pip install --upgrade --force-reinstall git+ssh://git@github.com/macxred/cashctrl_api.git
```

Installation requires SSH access to the GitHub repository.
If you encounter any installation issues, confirm your SSH access by attempting
to clone the repository with `git clone git@github.com:macxred/cashctrl_api.git`.

## Usage

```python
from cashctrl_api import CashCtrlAPIClient

# Insert your oganisation's name and api_key
cc = CashCtrlAPIClient("<my_organisation>", api_key="<my_api_key>")

# Create a new contact
# (https://app.cashctrl.com/static/help/en/api/index.html#/person/create.json)
contact = {
    "firstName": "Tina",
    "lastName": "Test",
    "titleId": 2
}
response = cc.post("person/create.json", data=contact)
id = response["insertId"]

# Look up the contact created above
response = cc.get("person/read.json", params={'id': id})
print(response)
```

Alternatively, you can provide API Key and organisation as environment variables
`CC_API_KEY` and `CC_API_ORGANISATION`. For example, by setting both variables
in the shell when starting python:

```bash
CC_API_ORGANISATION=<myorg> CC_API_KEY=<mykey> python
```

Usage in python is now even simpler:
```python
from cashctrl_api import CashCtrlAPIClient
cc = CashCtrlAPIClient()
response = cc.get("person/list.json")
```

## Test Strategy

We use pytest for it's clean and concise test syntax, rather than the unittest
from the standard library.

Tests in the [cashctrl_api/tests](tests) folder are executed as github action
after each commit, when pull requests are created or modified, and once every
day. When executed as github action, the tests use an API key stored as github
secret and connect to an organisation covered by Macxred's CashCtrl
subscription (which is not publicly accessible).

## Package Development

We recommend to work within a virtual environment for package development.
You can create and activate an environment with:

```bash
python3 -m venv ~/.virtualenvs/env_name
source ~/.virtualenvs/env_name/bin/activate
```

To locally modify and test the package, clone the repository and execute `python
setup.py develop` in the repository root folder. This approach adds a symbolic
link to your development directory in Python's search path, ensuring the latest
code version is sourced when (re-)loading the package.