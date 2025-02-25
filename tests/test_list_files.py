"""Unit tests for cached files."""

from cashctrl_api import CashCtrlClient
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def mock_directory(tmp_path_factory):
    """Create a temporary directory, populate with files and folders."""
    tmp_path = tmp_path_factory.mktemp("temp")
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


@pytest.fixture(scope="module")
def cc_client(mock_directory):
    """Create a CachedCashCtrlClient, populate with files and folders."""
    cc_client = CashCtrlClient()
    initial_files = cc_client.list_files()
    cc_client.mirror_directory(mock_directory, delete_files=False)

    # We create a fresh instance with empty cache, because the cache is
    # populated when mirroring a directory
    cc_client = CashCtrlClient()

    yield cc_client

    # Delete files added in the test
    files = cc_client.list_files()
    to_delete = set(files["id"]).difference(initial_files["id"])
    params = {"ids": ",".join(str(i) for i in to_delete), "force": True}
    cc_client.post("file/delete.json", params=params)


@pytest.fixture(scope="module")
def files(cc_client):
    # Explicitly call the base class method to circumvent the cache.
    return CashCtrlClient.list_files(cc_client)


def test_cached_files_same_to_actual(cc_client, files):
    pd.testing.assert_frame_equal(cc_client.list_files(), files)


def test_file_id_to_path(cc_client, files):
    assert (
        cc_client.file_id_to_path(files["id"].iat[0]) == files["path"].iat[0]
    ), "Cached file path doesn't correspond actual"


def test_file_id_to_nested_path(cc_client, files):
    path = "/nested/subdir/file4.txt"
    id = files.loc[files["path"] == path, "id"].item()
    assert cc_client.file_id_to_path(id) == path, (
        "Cached nested file path doesn't correspond actual."
    )


def test_file_id_to_path_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No path found for id"):
        cc_client.file_id_to_path(99999999)


def test_file_id_to_path_invalid_id_returns_none_when_allowed_missing(cc_client):
    assert cc_client.file_id_to_path(99999999, allow_missing=True) is None


def test_file_path_to_id(cc_client, files):
    path = "/nested/subdir/file4.txt"
    id = files.loc[files["path"] == path, "id"].item()
    assert cc_client.file_path_to_id(path) == id, (
        "Cached nested file id doesn't correspond actual id."
    )


def test_nested_file_path_to_id(cc_client, files):
    assert (
        cc_client.file_path_to_id(files["path"].iat[0]) == files["id"].iat[0]
    ), "Cached file id doesn't correspond actual id"


def test_file_path_to_id_with_invalid_path_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for path"):
        cc_client.file_path_to_id(99999999)


def test_file_path_to_id_with_invalid_returns_none_when_allowed_missing(cc_client):
    assert cc_client.file_path_to_id(99999999, allow_missing=True) is None
