import pathlib
import pytest
from pathlib import Path
from cashctrl_api import CashCtrlAPIClient
from cashctrl_api.errors import CashCtrlAPIClientError

def test_files():

    # FIXME: if this test fails then {name} files might remain at the cc server

    cc = CashCtrlAPIClient()

    myfile = "res/cctest_img.jpg"
    if not Path(myfile).is_file():
        raise CashCtrlAPIClientError(f"The file test requires the file '{myfile}'")

    # test file_list; ensure that there is no testfile already
    name = "autotest_img.jpg"
    df = cc.file_list()
    if any([x == name for x in df['name']]):
        raise CashCtrlAPIClientError(f"The testfile '{name}' is already on the cc server")

    # test file_upload: two times, retain id of the first one
    id = cc.file_upload(name, myfile)
    cc.file_upload(name, myfile)

    # test file_remove; two identically named files not supported atm
    with pytest.raises(Exception):
        assert(cc.file_remove(name))

    # test file_delete
    cc.file_delete(id)

    # test file_remove
    cc.file_remove(name)

    # test file_list; ensure no testfile remains on cc server
    df = cc.file_list()
    if any([x == name for x in df.name]):
        raise CashCtrlAPIClientError(f"The testfile '{name}' is still on the cc server")
