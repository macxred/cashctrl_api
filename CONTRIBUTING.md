# Package Development and Contribution

We value contributions and look forward to seeing this package evolve.
Contributions can include code development, documentation enhancements,
or additional tests. This guide helps you get started with contributing.

## Setting Up Your Development Environment

### Virtual Environment

To isolate your development environment, we recommend setting up a virtual
Python environment:

```bash
python3 -m venv env_name

# Activate on Linux / macOS
source env_name/bin/activate

# Activate on Windows
.\env_name\Scripts\activate
```

### Local Development

To modify and test the package locally, clone the repository and run
the following in the package root folder:
```bash
python setup.py develop
```

This command links your source code to Python's search path, immediately
reflecting code changes when reloading the package. This setup facilitates
rapid iterations without the need for reinstallation.


### Step-by-Step Installation Guide

Follow these steps to set up your local development environment on Unix/Mac OS:

<details><summary> Click to expand.</summary>

<br>

1. **Navigate to the local folder designated for package development.**
    For example:
    ```bash
    cd ~/macx/
    ```

2. **Clone the repository using SSH.**
    Ensure your SSH keys are set up on GitHub:
    ```bash
    git clone git@github.com:macxred/cashctrl_api.git
    ```

3. **Create a virtual development environment.**
    We suggest naming this environment 'dev' and placing it within your
    development directory:
    ```bash
    mkdir -p ~/macx/.virtualenvs/
    python3 -m venv ~/macx/.virtualenvs/dev
    ```

4. **Activate the virtual environment.**
    Repeat this command when returning to package development or starting
    a new terminal session:
    ```bash
    source ~/macx/.virtualenvs/dev/bin/activate
    ```

5. **Set up the package in development mode:**
    ```bash
    cd ~/macx/cashctrl_api/
    python setup.py develop
    ```

6. **Install the required packages specified in `setup.py`:**
    ```bash
    pip install requests pandas
    ```
    Alternatively, if you develop several packages simultaneously, you can set
    up required packages in development mode by repeating step 5 for the other
    packages.

</details>


## Naming Patterns

# Branch name
```
(feat|fix|docs|style|refactor|test|revert)/taskId_task-short-description
Ex.: feat/1_add-commit-and-branch-name-styles-to-readme
```

# Commit name
```
(feat|fix|docs|style|refactor|test|revert): update descriptions
Ex.: bug: update readme
```

# Commit description
```
tickets: taskId, taskId
Ex.: tickets: 1, 2, 3
```

# Pull-request name
```
(Feat|Fix|Docs|Style|Refactor|Test|Revert)/taskId description
Ex.: Fix/15 unnecessary request removed
```

## Testing Strategy

We use pytest, we prefer its straightforward and readable syntax over the
standard library's unittest package.

Tests are located in the [tests](tests) directory and are automatically
executed  through GitHub Actions after each commit, during pull requests,
and daily. The tests connect to a private CashCtrl test account with the API
key stored as a GitHub secret.

Before you try to run tests, execute the following command, to install pytest
```bash
pip install pytest
```

For local testing, provide authentication details via environment variables:
```bash
CC_API_ORGANISATION=<myorg> CC_API_KEY=<mykey> pytest
```

If you have not set up credentials yet, please refer to the Credentials section
in the [README.md](README.md#credentials).


## Working with DataFrames

DataFrames are extremely useful for in-memory storage, and manipulation of
accounting data, which is typically organized into interconnected tables.
For example, ledger entries can be efficiently retrieved and processed using
DataFrames:

```python
import pandas as pd
from cashctrl_api import CashCtrlClient
cc_client = CashCtrlClient()

df = pd.DataFrame(cc_client.get('journal/list.json')['data'])
df.loc[df['account'] == '1020', 'amount'].sum()
```

### Type Consistency

The dynamic nature of DataFrames offers powerful exploration capabilities in
an interpreted environment but can introduce challenges in production.
For instance, if the API returns an empty list in above example, the DataFrame
`df` will have no columns, resulting in an exception when trying to access
the non-existent `df['account']` column.

To mitigate runtime errors, we provide the `enforce_dtypes()`
function to ensure DataFrames maintain expected columns and types,
even if the data source returns unexpected results:

```python
df = pd.DataFrame(cc_client.get('journal/list.json')['data'])
columns = {'date': 'datetime64', 'amount': 'float', 'account': 'str'}
df = enforce_dtypes(df, required=columns)
df.loc[df['account'] == '1020', 'amount'].sum()
```

### Indexing

To maintain clarity and prevent errors, our package avoids relying on pandas'
native indexing and consistently uses strings for column indices.

Our rationale: A DataFrame is essentially a named collection of vectors of
equal length, where each vector has its own data type, and the names are
treated as column headers. While R's tibble provides a straightforward
implementation of this concept, pandas DataFrames introduce additional
complexities with their multi-dimensional indexing. In our experience,
the cost of the added complexity is not justified by the limited additional
features.


## Leveraging AI Tools

We extensively use ChatGPT to assist in various development tasks, from
generating code snippets to comprehensive code reviews. Python's interpreted
nature complements ChatGPT's capabilities, enabling it to infer data
structures from console output and suggest actionable code enhancements,
favoring immediate testing and iterative refinement. ChatGPT also
performs more complex tasks, such as writing docstrings, crafting unit tests,
conducting code reviews, and ensuring compliance with Python standards and
best practices.

The modular structure of Python packages aligns well with ChatGPT's abilities:
ChatGPT is well suited for structured projects with pre-defined file
layout, clear conventions, and concise code segments. Trained with numerous
open-source Python projects, it adeptly adjusts to different coding styles and
bridges community preferences (e.g., unittest vs. pytest). Python's approach to
in-code documentation also enables ChatGPT to understand and contribute both to
the scope and the implementation details of code segments.

While ChatGPT excels in many areas, precise instructions are essential for
optimal results. For example, requiring concise output avoids bloated texts. Much
like a conductor leading an orchestra, you must guide ChatGPT by gradually
steering it towards the desired results.

Example prompts for using ChatGPT:

```
Review this unit and its test suite, provide a downloadable markdown file.
Format the unit to a 79-character line width.
Implement the first and third suggestions from your review.
Suggest alternative wordings for function names and arguments.
Provide a concise docstring for this method.
Align code with the style of popular open-source Python projects.
Extract data from this nested data structure [paste console output].
```

Consider a paid license for ChatGPT to access more advanced features and a
richer language model.

## Standards and Best Practices

We adhere to community standards and best practices to ensure our code is
readable, maintainable, and easily integrated across projects.
Here are some recommended resources on coding styles:

- [Python's Code Style Guide](https://docs.python-guide.org/writing/style/)
- [Real Python on PEP8](https://realpython.com/python-pep8/)

By aligning with these standards, we set clear expectations for contributions
and ensure the quality of our work. ChatGPT can help review and align our code
with these practices.

## Shared Learning

Our commitment to open-source principles fosters a community of shared learning
and continuous improvement. We value feedback and encourage users to share their
experiences, allowing everyone to benefit from collective knowledge.
