"""
Unit tests for cached files.
"""

import time
import pytest
import pandas as pd
from cashctrl_api import CachedCashCtrlClient, CashCtrlClient

@pytest.fixture(scope="module")
def cc_client():
    return CachedCashCtrlClient()

@pytest.fixture(scope="module")
def files():
    cc_client = CachedCashCtrlClient()
    return CashCtrlClient.list_files(cc_client)

@pytest.fixture
def mock_directory(tmp_path):
    """Create a temporary directory, populate with files and folders."""
    (tmp_path / 'file1.txt').write_text("This is a text file.")
    (tmp_path / 'file2.log').write_text("Log content here.")
    subdir = tmp_path / 'subdir'
    subdir.mkdir(exist_ok=True)
    (subdir / 'file3.txt').write_text("A Text file in a subdirectory.")
    nested_subdir = tmp_path / 'nested' / 'subdir'
    nested_subdir.mkdir(parents=True, exist_ok=True)
    (nested_subdir / 'file4.txt').write_text("File in the nested directory.")
    (nested_subdir / 'file5.log').write_text("Another nested directory file.")
    return tmp_path

def test_files_cache_is_none_on_init(cc_client):
    assert cc_client._files_cache == None
    assert cc_client._files_cache_time == None

def test_cached_files_same_to_actual(cc_client, files):
    pd.testing.assert_frame_equal(cc_client.list_files(), files)

def test_file_id_to_path(cc_client, mock_directory):
    cc_client.mirror_directory(mock_directory, delete_files=True)
    cc_client.invalidate_files_cache()
    files = CashCtrlClient.list_files(cc_client)
    assert cc_client.file_id_to_path(files['id'].iat[0]) == files['path'].iat[0], (
        'Cached file doesn`t correspond actual'
    )

def test_file_id_to_path_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match='No path found for id'):
        cc_client.file_id_to_path(99999999)

def test_file_id_to_path_invalid_id_returns_none_when_allowed_missing(cc_client):
    cc_client.file_id_to_path(99999999, allow_missing=True) == None

def test_file_path_to_id(cc_client, mock_directory):
    cc_client.mirror_directory(mock_directory, delete_files=True)
    cc_client.invalidate_files_cache()
    files = CashCtrlClient.list_files(cc_client)
    assert cc_client.file_path_to_id(files['path'].iat[0]) == files['id'].iat[0], (
        'Cached file id doesn`t correspond actual id'
    )

def test_file_path_to_id_with_invalid_path_raises_error(cc_client):
    with pytest.raises(ValueError, match='No id found for path'):
        cc_client.file_path_to_id(99999999)

def test_file_path_to_id_with_invalid_returns_none_when_allowed_missing(cc_client):
    cc_client.file_path_to_id(99999999, allow_missing=True) == None

def test_files_cache_timeout(cc_client):
    cc_client = CachedCashCtrlClient(cache_timeout=1)
    cc_client.list_files()
    assert not cc_client._is_expired(cc_client._files_cache_time)
    time.sleep(1)
    assert cc_client._is_expired(cc_client._files_cache_time)

def test_files_cache_invalidation(cc_client):
    cc_client = CachedCashCtrlClient()
    cc_client.list_files()
    assert not cc_client._is_expired(cc_client._files_cache_time)
    cc_client.invalidate_files_cache()
    assert cc_client._is_expired(cc_client._files_cache_time)
