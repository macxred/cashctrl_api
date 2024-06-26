"""Unit tests for up- and downloading files with CashCtrlClient."""

import random
import string
from cashctrl_api import CashCtrlClient


def random_word(length: int) -> str:
    """Generate a random word using lowercase letters."""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def test_upload_file_and_download(tmp_path) -> None:
    """Test uploading and downloading files."""
    cc_client = CashCtrlClient()

    # Create a temporary file with random content to upload
    temp_file = tmp_path / "upload_test.txt"
    original_content = [f"{random_word(20)}\n" for _ in range(20)]
    with open(temp_file, "w") as f:
        f.writelines(original_content)

    # Upload the file
    file_id = cc_client.upload_file(temp_file, name=f"{random_word(30)}.txt")

    # Download from CashCtrl and verify that content matches the original file
    download_path = tmp_path / "download_test.txt"
    cc_client.download_file(id=file_id, path=download_path)
    with open(download_path, "r") as f:
        downloaded_content = f.readlines()
    assert downloaded_content == original_content, (
        "Downloaded content does not match the original."
    )

    # Replace remote file by a file with differing random content
    updated_content = [f"{random_word(20)}\n" for _ in range(20)]
    with open(temp_file, "w") as f:
        f.writelines(updated_content)

    # Re-upload using the same file ID
    cc_client.upload_file(temp_file, name=f"{random_word(30)}.txt", file_id=file_id)

    # Re-download and verify updated content
    cc_client.download_file(id=file_id, path=download_path)
    with open(download_path, "r") as f:
        downloaded_content = f.readlines()
    assert downloaded_content == updated_content, "Content does not match."
