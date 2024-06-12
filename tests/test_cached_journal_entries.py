"""
Unit tests for cached journal entries.
"""

import time
import pytest
import pandas as pd
from cashctrl_api import CachedCashCtrlClient, CashCtrlClient

@pytest.fixture(scope="module")
def cc_client():
    return CachedCashCtrlClient()

@pytest.fixture(scope="module")
def journal_entries():
    cc_client = CachedCashCtrlClient()
    return CashCtrlClient.list_journal_entries(cc_client)

def test_journal_entries_cache_is_none_on_init(cc_client):
    assert cc_client._journal_entries_cache == None
    assert cc_client._journal_entries_cache_time == None

def test_cached_journal_entries_same_to_actual(cc_client, journal_entries):
    pd.testing.assert_frame_equal(cc_client.list_journal_entries(), journal_entries)

def test_journal_entries_cache_timeout(cc_client):
    cc_client = CachedCashCtrlClient(cache_timeout=1)
    cc_client.list_journal_entries()
    assert not cc_client._is_expired(cc_client._journal_entries_cache_time)
    time.sleep(1)
    assert cc_client._is_expired(cc_client._journal_entries_cache_time)

def test_journal_entries_cache_invalidation(cc_client):
    cc_client = CachedCashCtrlClient()
    cc_client.list_journal_entries()
    assert not cc_client._is_expired(cc_client._journal_entries_cache_time)
    cc_client.invalidate_journal_entries_cache()
    assert cc_client._is_expired(cc_client._journal_entries_cache_time)
