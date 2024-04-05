# Python Client for CashCtrl REST API

cashctrl_api is a lightweight Python package designed to facilitate connections
to the REST API of [CashCtrl](https://cashctrl.com), a comprehensive online
accounting software. It is designed as a thin wrapper that routes requests via
universal methods and does not implement individual endpoints.

Most GET, POST, PATCH, PUT and DELETE requests are transmitted via generic
`get()`, `post()`, `patch()`, `put()` and `delete()` methods. These methods take
an API `endpoint`, request parameters and json payload as arguments and return
the server's response as a `requests.Response` object.

To use this Python client, you'll need valid credentials for CashCtrl, including
an API key which can be obtained from your CashCtrl account settings.

## Installation

```bash
pip install cashctrl_api
```

## Usage

The API Key and the name of the (demo) organisation can be provided to Python
as `CC_API_KEY` and `CC_API_ORGANISATION` environment variables:

    CC_API_ORGANISATION=<myorg> CC_API_KEY=<mykey> python

Here is a simple example with contacts/people: 

```python
from cashctrl_api import CashCtrlAPIClient

cc = CashCtrlAPIClient()

# Create a new contact
# (https://app.cashctrl.com/static/help/en/api/index.html#/person/create.json)

contact = {
    "firstName": "Tina",
    "lastName": "Testfrau",
    "titleId": 2
}

response = cc.post("person/create.json", data=contact)
print(response)
insertId = response["insertId"]

# Look up the contact created above
dd = {}; dd["id"] = insertId
response = cc.get("person/read.json", params=dd)
print(response)
```

## Test Strategy

We use pytest for it's clean and concise test syntax, rather than the standard
test framework.

The tests in the cashctrl_api package are executed by github after each commit,
when pull requests are created or modified, and once every day. The tests
connect to an organisation within Macxred's CashCtrl subscription (which is not
publicly accessible).

## Package Development

We recommend to work within a virtual environment for package development.
You can create and activate an environment with:

```bash
python3 -m venv ~/.virtualenvs/env_name
source ~/.virtualenvs/env_name/bin/activate
```

To locally modify and test the package, clone the repository and execute `python
setup.py develop` in the repository root folder. This approach adds a symbolic
link to your development directory in Python's search path, ensuring immediate
access to the latest code version upon (re-)loading the package.