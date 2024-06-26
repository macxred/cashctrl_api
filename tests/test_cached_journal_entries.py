"""Unit tests for cached journal entries."""

import time
from cashctrl_api import CachedCashCtrlClient
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def cc_client() -> CachedCashCtrlClient:
    return CachedCashCtrlClient()


@pytest.fixture(scope="module")
def journal_entries(cc_client: CachedCashCtrlClient) -> pd.DataFrame:
    """Explicitly call the base class method to circumvent the cache."""
    return cc_client.list_journal_entries()


def test_journal_cache_is_none_on_init(cc_client: CachedCashCtrlClient) -> None:
    assert cc_client._journal_cache is None
    assert cc_client._journal_cache_time is None


def test_cached_journal_entries_same_to_actual(
    cc_client: CachedCashCtrlClient, journal_entries: pd.DataFrame
) -> None:
    pd.testing.assert_frame_equal(cc_client.list_journal_entries(), journal_entries)


def test_journal_cache_timeout() -> None:
    cc_client = CachedCashCtrlClient(cache_timeout=1)
    cc_client.list_journal_entries()
    assert not cc_client._is_expired(cc_client._journal_cache_time)
    time.sleep(1)
    assert cc_client._is_expired(cc_client._journal_cache_time)


def test_journal_cache_invalidation() -> None:
    cc_client = CachedCashCtrlClient()
    cc_client.list_journal_entries()
    assert not cc_client._is_expired(cc_client._journal_cache_time)
    cc_client.invalidate_journal_cache()
    assert cc_client._is_expired(cc_client._journal_cache_time)
