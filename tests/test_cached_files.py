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

def test_files_cache_is_none_on_init(cc_client):
    assert cc_client._files_cache == None
    assert cc_client._files_cache_time == None

def test_cached_files_same_to_actual(cc_client, files):
    pd.testing.assert_frame_equal(cc_client.list_files(), files)

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
