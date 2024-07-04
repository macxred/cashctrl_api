"""Unit tests for directory mirroring with CashCtrlClient."""

from pathlib import Path
from cashctrl_api import CashCtrlClient, list_directory
import pytest


@pytest.fixture
def mock_directory(tmp_path: Path):
    """Create a temporary directory, populate with files and folders."""
    (tmp_path / "file1.txt").write_text("This is a text file.")
    (tmp_path / "file2.log").write_text("Log content here.")
    subdir = tmp_path / "subdir"
    subdir.mkdir(exist_ok=True)
    (subdir / "file3.txt").write_text("A Text file in a subdirectory.")
    nested_subdir = tmp_path / "nested" / "subdir"
    nested_subdir.mkdir(parents=True, exist_ok=True)
    (nested_subdir / "file4.txt").write_text("File in the nested directory.")
    (nested_subdir / "file5.log").write_text("Another nested directory file.")
    return tmp_path


def local_files(base_dir: str | Path) -> set:
    """List files in a local directory, returning a set of paths."""
    files = list_directory(base_dir, recursive=True, exclude_dirs=True)
    return set("/" + Path(p).as_posix() for p in files["path"])


def remote_content(cc_client: CashCtrlClient, file_id: int) -> str:
    """Fetch and return the content of a remote file identified by its ID."""
    params = {"id": file_id}
    response = cc_client.request("GET", "file/get", params=params)
    return response.content.decode("utf-8")


def test_directory_mirroring_sync_local_files_to_remote(mock_directory):
    cc_client = CashCtrlClient()

    # Mirror directory and check file presence
    cc_client.mirror_directory(mock_directory, delete_files=True)
    remote_files = cc_client.list_files().set_index("path")
    initial_sync_time = remote_files["lastUpdated"].max()
    assert local_files(mock_directory) == set(remote_files.index), (
        "Files do not match after mirroring"
    )

    # Add a local file, mirror again, check file presence and integrity.
    (mock_directory / "new_file.txt").write_text("This is a new file.")
    cc_client.mirror_directory(mock_directory, delete_files=True)
    remote_files = cc_client.list_files().set_index("path")
    assert local_files(mock_directory) == set(remote_files.index), (
        "Files do not match after mirroring new file"
    )
    file_id = remote_files.at["/new_file.txt", "id"]
    assert remote_content(cc_client, file_id) == "This is a new file.", (
        "Content differs between local and remote files"
    )

    # Verify new file is modified after other files
    addition_time = remote_files.at["/new_file.txt", "lastUpdated"]
    assert addition_time > initial_sync_time, "New file modified time not set"
    assert all(
        remote_files.drop("/new_file.txt")["lastUpdated"] <= initial_sync_time
    ), "Others files' modified time changed"

    # Modify new file and mirror again
    (mock_directory / "new_file.txt").write_text("This file was updated.")
    cc_client.mirror_directory(mock_directory, delete_files=True)
    remote_files = cc_client.list_files().set_index("path")
    assert local_files(mock_directory) == set(remote_files.index), (
        "Files do not match after mirroring updated file"
    )
    assert remote_content(cc_client, file_id) == "This file was updated.", (
        "Remote content differs from updated local content"
    )

    # Verify updated file is modified after other files
    update_time = remote_files.at["/new_file.txt", "lastUpdated"]
    assert update_time > addition_time, "Updated file modified time not set"
    assert all(
        remote_files.drop("/new_file.txt")["lastUpdated"] <= initial_sync_time
    ), "Others files' modified time changed"

    # Delete a file, mirror without deletion, verify remote file is preserved.
    initial_local_files = local_files(mock_directory)
    (mock_directory / "file2.log").unlink()
    cc_client.mirror_directory(mock_directory, delete_files=False)
    remote_files = cc_client.list_files().set_index("path")
    assert initial_local_files == set(remote_files.index), (
        "Remote files are not preserved"
    )
    assert remote_files["lastUpdated"].max() <= update_time, (
        "Unexpected remote file update"
    )

    # Mirror with deletion, ensure remote file is removed.
    cc_client.mirror_directory(mock_directory, delete_files=True)
    remote_files = cc_client.list_files().set_index("path")
    assert local_files(mock_directory) == set(remote_files.index), (
        "Files do not match after deletion"
    )
    assert remote_files["lastUpdated"].max() <= update_time, (
        "Unexpected remote file update"
    )


def test_mirror_empty_directory_removes_all_remote_files(tmp_path):
    cc_client = CashCtrlClient()
    cc_client.mirror_directory(tmp_path, delete_files=True)
    assert cc_client.list_files().empty, (
        "Expected no remote files after mirroring an empty directory"
    )
