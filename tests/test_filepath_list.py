import pathlib
import pytest
from pathlib import Path
from cashctrl_api import CashCtrlAPIClient
from cashctrl_api.errors import CashCtrlAPIClientError

def test_filepaths():

    # IMPORTANT:
    # * this test depends on the 'res/FileMockup/Init/0All' structure. Future changes likely
    #   will be defined in 'res/FileMockup/Rev1/0All' (or Rev2..) folders
    # * in addition the ID's are hard-coded (checked) atm

    cc = CashCtrlAPIClient()

    df = cc.filepath_list()

    assert(all(df['catId'] == [4,5,6,7,7,8]))
    assert(all(df[df['catId'] == 8]['path'] == '/2Hallo/21Hallo/211Hallo/211welt.txt'))
