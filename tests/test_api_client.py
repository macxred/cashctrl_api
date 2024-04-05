import re, filecmp
from pkg_resources import resource_filename
from proffix_api import ProffixAPIClient

# Credetials for official Proffix API test environment are
# publicly available at
# https://www.proffix.ch/Portals/0/content/REST%20API/zugriff_auf_testumgebung.html
# We're not giving away a secret by including them in plain text.

def test_database_request():
    database = ProffixAPIClient.database(
        base_url = "https://remote.proffix.net:11011/pxapi/v4",
        api_key = "Demo_2016_PWREST!,Wangs")
    assert database[0]['Name'] == "DEMODB"
    pass

def test_info_request():
    version_info = ProffixAPIClient.info(
        base_url = "https://remote.proffix.net:11011/pxapi/v4",
        api_key = "Demo_2016_PWREST!,Wangs")
    assert version_info['Version'][0] == "4"
    assert version_info['NeuesteVersion'][0] == "4"
    pass

def test_api_login():
    proffix = ProffixAPIClient(
        base_url="https://remote.proffix.net:11011/pxapi/v4",
        username="Gast",
        password="gast123",
        database="DEMODB",
        modules=["VOL"])

    response = proffix.get("PRO/LOGIN")
    assert response.json()['Benutzer'] == "GAST"

    proffix.logout()
    pass

def test_file_handling():
    proffix = ProffixAPIClient(
        base_url="https://remote.proffix.net:11011/pxapi/v4",
        username="Gast",
        password="gast123",
        database="DEMODB",
        modules=["VOL"])

    # File upload
    test_file = resource_filename('proffix_api', 'resources/test_image.jpg')
    params = {'filename': "test_image.jpg"}
    file_id = proffix.file_upload(test_file, params=params)

    # File info
    response = proffix.get(f"PRO/Datei/{file_id}/Info")
    assert re.match(r"^.*/test_image.jpg.*$", response.json()['Dateipfad'])

    # File download
    proffix.file_download(file_id, "test_image.jpg")
    # Ensure original and downloaded files are identical
    assert filecmp.cmp(test_file, "test_image.jpg")

    proffix.logout()
    pass
