import pytest
from pathlib import Path
from cashctrl_api import CashCtrlAPIClient
from cashctrl_api.errors import CashCtrlAPIClientError

def test_files():


    cc = CashCtrlAPIClient()

    myfile = "res/cctest_img.jpg"
    if not Path(myfile).is_file():
        raise CashCtrlAPIClientError(f"The file test requires the file '{myfile}'")

    # TODO: atm we don't ensure that this file is deleted again. Due to check failures
    #       more than one file might exists on the server. You can delete it manually
    name = "autotest_img.jpg"

    # test file_upload
    id = cc.file_upload(myfile, name)

    # test delete file
    cc.post("file/delete.json", params={'ids': id, 'force': True})

