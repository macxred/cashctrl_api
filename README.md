# Python Client for Proffix REST API

proffix_api is a lightweight Python package to manage connections to the REST API of [Proffix](https://www.proffix.ch/), an ERP software popular in Switzerland. This package simplifies the interaction with Proffix's API by automatically handling authentication. It is designed as a thin wrapper that routes requests via universal methods and does not implement individual endpoints.

Most GET, POST, PATCH, PUT and DELETE requests are transmitted via generic `get()`, `post()`, `patch()`, `put()` and `delete()` methods. These methods take an API `endpoint`, request parameters and json payload as arguments and return the server's response as a `requests.Response` object.

The package further provides specific methods for endpoints that can not be handled by the generic requests:
- `login()` and `logout()` manage the `session_id` authentication token.
- `info()` and `database()` _class_ methods access PRO/INFO and PRO/DATABASE endpoints. These endpoints require an API key as an authentication token and do not depend on the standard login mechanism.\
_(Note that the api_key is solely needed for these endpoints. All other endpoints can be used without the api_key)._
- `file_upload()` and `file_download()`

The Proffix API manages authentication through a `PxSessionId` token transmitted in the HTML header. The token is initially acquired by a html POST request to the PRO/LOGIN endpoint. The proffix_api package embeds the current session ID in the HTML header and obtains a new session ID if none is available or if the current one has expired. A new session ID is acquired through the `login()` method that forwards username, password, database name and necessary modules to the 'PRO/LOGIN' endpoint.

## Installation

```bash
pip install https://github.com/lasuk/proffix_api/tarball/main
```

## Usage

Below example connects to the API [test environment](https://www.proffix.ch/Portals/0/content/REST%20API/zugriff_auf_testumgebung.html) provided by Proffix. Changes can be viewed in the online demo GUI.


```python
import re, pandas as pd
from pkg_resources import resource_filename
from proffix_api import ProffixAPIClient


# Login ------------------------------------------------------------------------

# Query available databases
ProffixAPIClient.database(
    base_url = "https://remote.proffix.net:11011/pxapi/v4",
    api_key = "Demo_2016_PWREST!,Wangs")

# Connect to test environment
proffix = ProffixAPIClient(
    base_url = "https://remote.proffix.net:11011/pxapi/v4",
    username = "Gast",
    password = "gast123",
    database = "DEMODB",
    modules = ["VOL"])


# Contacts ---------------------------------------------------------------------

# Create new contact
contact = {
    "Vorname": "Tina",
    "Name": "Test",
    "Strasse": "Teststreet 15",
    "PLZ": "0000",
    "Ort": "Testtown",
    "Land": {"LandNr": "CH"},
    "Anrede": "Mrs.",
    "EMail": "tina.test@example.org"}
response = proffix.post("ADR/ADRESSE", json=contact)
adress_no = re.sub("^.*/", "", response.headers['Location'])

# Look up contact created above
response = proffix.get(f"ADR/ADRESSE/{adress_no}",
                       params={'fields': "Vorname,Name,Ort"})
response.json()

# Display contacts matching a search string
response = proffix.get("ADR/ADRESSE", params={'Suche': 'Tina'})
address_list = response.json()
pd.DataFrame(address_list)

# Delete contact created above
response = proffix.delete(f"ADR/ADRESSE/{adress_no}")


# File handling ----------------------------------------------------------------

# File upload
path = resource_filename('proffix_api', 'resources/test_image.jpg')
file_id = proffix.file_upload(path, params={'filename': "test_image.jpg"})
# Uploaded files are stored in a temporary directory for further use. They will
# be automatically deleted if not attached to an object within 20 minutes.

# File info
proffix.get(f"PRO/Datei/{file_id}/Info").json()

# File download
proffix.file_download(file_id, "~/Downloads/temp_test_image.jpg")


# Use file as product picture --------------------------------------------------

# Create a new product (Artikel in Lagerverwaltung)
product = {
    "ArtikelNr": "TESTARTIKEL",
    "Bezeichnung1": "Ein klitzekleiner Testartikel.",
    "Steuercode": {'SteuercodeNr': 1},
    "SteuercodeEinkauf": {'SteuercodeNr': 1}}
proffix.post("LAG/Artikel", json=product)

# Link picture to product
product_picture = {
    "DateiNr": file_id,
    "Artikel": {"ArtikelNr": "TESTARTIKEL"},
    "Hauptbild": True,
    "Bezeichnung": "Testbild"}
# Below request is not authorized on Proffix' official REST API test environment
# Raises ProffixAPIError: "Sie haben keine Berechtigung für diese Funktion!"
proffix.post("LAG/Artikelbild", json=product_picture)


# Logout -----------------------------------------------------------------------

# Terminate session to free license
proffix.logout()
```

## Run in Docker Container

```bash
docker pull python:latest
docker run -it --rm python:latest bash

pip install pandas
pip install https://github.com/lasuk/proffix_api/tarball/main
```


## Test Strategy

Unit tests in the python_api package are executed by gitlab after each commit,
when pull requests are created or modified, and once every day. Tests connect to
the public Proffix test environment.

## Package Development

We recommend to work within a virtual environment for package development.
You can create and activate an environment with:

```bash
python3 -m venv ~/.virtualenvs/env_name
source ~/.virtualenvs/env_name/bin/activate
```

To locally modify and test the package, clone the repository and
execute `python setup.py develop` in the repository root folder. This approach
adds a symbolic link to your development directory in Python's search path,
ensuring immediate access to the latest code version upon (re-)loading the
package.
