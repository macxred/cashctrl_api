# Python Client for CashCtrl REST API

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
- `upload_file()` uploads a file from the local file system to the server,
  and optionally replaces an existing remote file.
- `download_file()` downloads a file from the server and saves it to the local
  file system.
- `mirror_files()` mirrors a local set of nested categories with the category
  tree on the server, mapping local sub-folders to categories on the remote
  server.

To use this Python client, you'll need a valid API key, which can be acquired
from your CashCtrl account settings -> Users & roles -> Add [API User].
API Usage requires a pro subscription, which can be tested free of charge for
30 days.

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

## Testing Strategy

Tests are housed in the [tests](tests) directory and are automatically executed
via GitHub Actions after each commit, during pull requests, and on a daily
schedule. When executed as GitHub Actions, tests utilize an API key stored as a
GitHub secret, connecting to a non-public CashCtrl Test organization covered by
MaCX ReD's subscription.

We prefer pytest for its straightforward and readable syntax over the unittest
package from the standard library.


## Package Development and Contribution

### Virtual environment

We recommend using a virtual environment for package development:

```bash
python3 -m venv ~/.virtualenvs/env_name
source ~/.virtualenvs/env_name/bin/activate
```

To locally modify and test the package, clone the repository and run
`python setup.py develop` in the root folder. This method adds a symbolic link
to your development directory to Python's search path, ensuring any changes are
immediately available when (re-)loading the package.

### DataFrames and Type Consistency

Accounting data is typically organized into interconnected tables, making
DataFrames exceptionally useful for data extraction, manipulation, and
in-memory storage. For example, ledger entries can be efficiently retrieved
and converted to a DataFrame, then further queried as follows:

```python
df = pd.DataFrame(cc_client.get('journal/list.json'))
df.loc[df['account'] == '1020', 'amount'].sum()
```

A DataFrame is essentially a named collection of vectors of the same length,
where each vector has its own data type, and the names are treated as column
headers. While R's tibbles provide a straightforward implementation of this
concept, pandas DataFrames introduce complexities with their multi-dimensional
indexing. In our experience, the cost of the added complexity does not justify
the limited additional features. Therefore, in this package, we minimize the
use of row indexing and consistently use strings for column indices to maintain
simplicity and clarity.

DataFrames are dynamic, allowing for the addition and removal of columns and
the modification of column types. While this flexibility is powerful for
explorations in an interpreted environment (as shown in the ledger example
above), it can pose challenges in production code. For instance, if the API
returns an empty list, the DataFrame `df` in the above example will be empty
with no columns, causing an exception when attempting to access the
non-existent `df['account']` column.

To ensure robustness in such cases, we provide the `enforce_column_types()`
(UNDER DEVELOPMENT)
function to maintain consistency of expected columns and their data types. This
function ensures that your code functions correctly, regardless of the data
returned by the API:

```python
df = pd.DataFrame(cc_client.get('journal/list.json'))
columns = {'date': 'datetime64', 'amount': 'float', 'account': 'str'}
df = enforce_column_types(df, mandatory_columns=columns)
df.loc[df['account'] == '1020', 'amount'].sum()
```

### Leveraging AI Tools

ChatGPT has been extremely helpful in the development of this package,
particularly for developers less seasoned in Python package development. It
assists with various tasks, from generating quick code snippets to implementing
pseudocode, and conducting full code reviews. Python's nature as an interpreted
language integrates well with ChatGPT’s capabilities, allowing it to infer data
structures from console output and suggest actionable code snippets, favoring
immediate testing and iterative refinement. ChatGPT also performs more complex
tasks, such as writing docstrings, crafting unit tests, conducting code
reviews, and ensuring compliance with Python standards and best practices.

The modular structure of Python packages aligns well with ChatGPT's abilities:
ChatGPT is well suited for clearly structured projects with pre-defined file
layout, clear conventions, and concise code segments. Trained with numerous
open-source Python projects, it adeptly adjusts to different coding styles and
bridges community preferences (e.g., unittest vs. pytest). Python's approach to
in-code documentation also enables ChatGPT to understand and contribute both to
the scope and the implementation details of code segments.

While ChatGPT is highly effective and knowledgeable, it has its limitations; it
lacks creativity and design experience, and its output can be bloated. It does
not provide perfect outcomes right out of the box but requires precise
instructions. Much like a conductor leading an orchestra, you must guide
ChatGPT by gradually steering it towards the desired results.

Here are a few suggestions for useful prompts:

```
Review this Python unit and the corresponding test suite. [upload files]
Provide review as downloadable markdown file with 79 char line width.
Implement the first and third suggestions from your review.
Suggest alternative wordings for foo().
Provide a docstring for foo, keep it concise.
Align code with the style of popular open-source Python packages.
Extract ... from this API response [paste console output].
```

For those who find ChatGPT beneficial, we recommend considering a paid license
to access its richer language model and advanced features.

_At MaCX ReD, we have primarily used ChatGPT, and are not familiar with other
AI tools like GitHub Copilot. We are eager to learn from the community about
these tools to better understand what works best and would appreciate any
feedback. We encourage users to share their experiences, helping us all to
learn and benefit from collective knowledge. We remain committed to open-source
principles, not only to share our work but also to foster a community of shared
learning and improvement._
