import pytest
from cashctrl_api import CashCtrlAPIClient

def test_mirror_files():

    if False:
        # NOTE: this is my local test script. It must be decided how often and how far
        #       we want to test. It might be a bit overwhelming if we fully delete and
        #       recreate categories and files on each single commit...

        # NOTE 2: until mtime / file update is finished it is likely easier to work with
        #         simple functions instead of a class (my Python knowledge is limited alas)

        with open('cctest_mirror.py', 'r') as file:
            mirror_content = file.read()
        exec(mirror_content)

        cc = CashCtrlAPIClient()

        # Rev1:
        # - DELETED: 22welt.txt, 21welt2.txt
        # - CREATED: 2Hallo/21Hallo/21welt3.txt, 3Hallo/31Hallo/311Hallo/311welt.txt
        root = "~/dev/prj/le24/dev/cashctrl_api/res/FileMockup/Rev1/0All"

        # Init:
        # root = "~/dev/prj/le24/dev/cashctrl_api/res/FileMockup/Init/0All"

        mirror_files(cc, root)

    pass
