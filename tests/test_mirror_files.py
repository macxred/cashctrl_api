import pytest
from cashctrl_api import CashCtrlAPIClient

def test_mirror_files():

    if True:
        # I'm not sure if we can/should run this code on every commit.
        # It will test run one time and then be disabled again (atm)

        cc = CashCtrlAPIClient()

        root = "~/dev/prj/le24/dev/cashctrl_api/res/FileMockup/Init/0All"
        cc.mirror_files(root)

        root = "~/dev/prj/le24/dev/cashctrl_api/res/FileMockup/Rev1/0All"
        cc.mirror_files(root)

        root = "~/dev/prj/le24/dev/cashctrl_api/res/FileMockup/Rev2/0All"
        cc.mirror_files(root)
    else:
        pass
