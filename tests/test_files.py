from pathlib import Path
from cashctrl_api import CashCtrlAPIClient
import random, string

def random_word(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

def test_file_upload_and_download():

    # Generate a test file with random content
    original_content = [f"{random_word(20)}\n" for i in range(20)]
    file = "temp_cashctrl_upload_test.txt"
    with open(file, 'w') as f:
        f.writelines(original_content)

    # Upload to CashCtrl
    cc = CashCtrlAPIClient()
    id = cc.file_upload(file, remote_name=f"{random_word(30)}.txt")

    # Download from CashCtrl
    download_path = "temp_cashctrl_download_test.txt"
    cc.file_download(id=id, file=download_path)

    # Verify that contents are identical
    with open(download_path, 'r') as f:
        downloaded_content = f.readlines()
    assert downloaded_content == original_content, (
        "The downloaded content does not match the original content.")

    # Cleanup: remove temporary files
    Path(file).unlink()
    Path(download_path).unlink()
    cc.post("file/delete.json", params={'ids': id, 'force': True})

