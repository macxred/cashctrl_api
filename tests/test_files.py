from pathlib import Path
from cashctrl_api import CashCtrlAPIClient
import random, string

def random_word(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

def test_file_upload_and_download():

    cc = CashCtrlAPIClient()

    # Upload a test file with random content to CashCtrl
    original_content = [f"{random_word(20)}\n" for i in range(20)]
    file = "temp_cashctrl_upload_test.txt"
    with open(file, 'w') as f:
        f.writelines(original_content)
    id = cc.file_upload(file, remote_name=f"{random_word(30)}.txt")

    # Download from CashCtrl and verify that content matches original file
    download_path = "temp_cashctrl_download_test.txt"
    cc.file_download(id=id, file=download_path)
    with open(download_path, 'r') as f:
        downloaded_content = f.readlines()
    assert downloaded_content == original_content, (
        "The downloaded content does not match the original content.")

    # Replace remote file by a file with differing random content
    updated_content = [f"{random_word(20)}\n" for i in range(20)]
    with open(file, 'w') as f:
        f.writelines(updated_content)
    cc.file_upload(file, remote_name=f"{random_word(30)}.txt", id=id)

    # Download from CashCtrl and verify that content matches updated file
    cc.file_download(id=id, file=download_path)
    with open(download_path, 'r') as f:
        downloaded_content = f.readlines()
    assert downloaded_content == updated_content, (
        "The downloaded content does not match the updated content.")

    # Cleanup: remove temporary files
    Path(file).unlink()
    Path(download_path).unlink()
    cc.post("file/delete.json", params={'ids': id, 'force': True})

