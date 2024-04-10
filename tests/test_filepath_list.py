import pathlib
import pytest
from pathlib import Path
from cashctrl_api import CashCtrlAPIClient
from cashctrl_api.errors import CashCtrlAPIClientError

def test_filepaths():

    # IMPORTANT: this test is very provisional:
    # - it depends on the 'res/FileMockup/Init/0All' structure
    # - UI language is supposed to be german ('All files')
    # - id values for check are hard-coded. This will change if we recreate the structure

    # FIXME: without iloc[0] there is a 'truth value of a Series is ambiguous' error
    # (don't know pandas well, is iloc the best solution here?)

    cc = CashCtrlAPIClient()
    df = cc.filepath_list()

    r72 = df[df['id'] == 72].iloc[0]
    assert(r72['catId'] == 5)
    assert(r72['path'] == '/All files/2Hallo/2welt.txt')

    r75 = df[df['id'] == 75].iloc[0]
    assert(r75['catId'] == 7)
    assert(r75['filename'] == '21welt2.txt')
