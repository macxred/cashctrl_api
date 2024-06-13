"""
Unit tests for cached accounts.
"""

import time
import pytest
import pandas as pd
from cashctrl_api import CachedCashCtrlClient, CashCtrlClient

@pytest.fixture(scope="module")
def cc_client():
    return CachedCashCtrlClient()

@pytest.fixture(scope="module")
def accounts():
    cc_client = CachedCashCtrlClient()
    return CashCtrlClient.list_accounts(cc_client)

def test_account_cache_is_none_on_init(cc_client):
    assert cc_client._accounts_cache == None
    assert cc_client._accounts_cache_time == None

def test_cached_accounts_same_to_actual(cc_client, accounts):
    pd.testing.assert_frame_equal(cc_client.list_accounts(), accounts)

def test_account_from_id(cc_client, accounts):
    assert cc_client.account_from_id(accounts['id'].iat[0]) == accounts['number'].iat[0], (
        'Cached account number doesn`t correspond actual number'
    )

def test_account_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match='No account found for id'):
        cc_client.account_from_id(99999999)

def test_account_from_id_invalid_id_returns_none_with_allowed_missing(cc_client):
    assert cc_client.account_from_id(99999999, allow_missing=True) == None

def test_account_to_id(cc_client, accounts):
    assert cc_client.account_to_id(accounts['number'].iat[1]) == accounts['id'].iat[1], (
        'Cached account id doesn`t correspond actual id'
    )

def test_account_to_id_with_invalid_account_number_raises_error(cc_client):
    with pytest.raises(ValueError, match='No id found for account'):
        cc_client.account_to_id(99999999)

def test_account_to_id_with_invalid_account_number_returns_none_with_allowed_missing(cc_client):
    assert cc_client.account_to_id(99999999, allow_missing=True) == None

def test_account_cache_timeout(cc_client):
    cc_client = CachedCashCtrlClient(cache_timeout=1)
    cc_client.list_accounts()
    assert not cc_client._is_expired(cc_client._accounts_cache_time)
    time.sleep(1)
    assert cc_client._is_expired(cc_client._accounts_cache_time)

def test_account_cache_invalidation(cc_client):
    cc_client = CachedCashCtrlClient()
    cc_client.list_accounts()
    assert not cc_client._is_expired(cc_client._accounts_cache_time)
    cc_client.invalidate_accounts_cache()
    assert cc_client._is_expired(cc_client._accounts_cache_time)
