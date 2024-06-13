"""
Unit tests for cached currencies.
"""

import time
import pytest
import pandas as pd
from cashctrl_api import CachedCashCtrlClient

@pytest.fixture(scope="module")
def cc_client():
    return CachedCashCtrlClient()

@pytest.fixture(scope="module")
def currencies():
    cc_client = CachedCashCtrlClient()
    return pd.DataFrame(cc_client.get("currency/list.json")['data'])

def test_currencies_cache_is_none_on_init(cc_client):
    assert cc_client._currencies_cache == None
    assert cc_client._currencies_cache_time == None

def test_cached_currencies_same_to_actual(cc_client, currencies):
    pd.testing.assert_frame_equal(cc_client.list_currencies(), currencies)

def test_currency_from_id(cc_client, currencies):
    assert cc_client.currency_from_id(currencies['id'].iat[0]) == currencies['text'].iat[0], (
        'Cached currency doesn`t correspond actual'
    )

def test_currency_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match='No currency found for id'):
        cc_client.currency_from_id(99999999)

def test_currency_to_id(cc_client, currencies):
    assert cc_client.currency_to_id(currencies['text'].iat[1]) == currencies['id'].iat[1], (
        'Cached currency id doesn`t correspond actual id'
    )

def test_currency_to_id_with_invalid_currency_raises_error(cc_client):
    with pytest.raises(ValueError, match='No id found for currency'):
        cc_client.currency_to_id(99999999)

def test_currencies_cache_timeout(cc_client):
    cc_client = CachedCashCtrlClient(cache_timeout=1)
    cc_client.list_currencies()
    assert not cc_client._is_expired(cc_client._currencies_cache_time)
    time.sleep(1)
    assert cc_client._is_expired(cc_client._currencies_cache_time)

def test_currencies_cache_invalidation(cc_client):
    cc_client = CachedCashCtrlClient()
    cc_client.list_currencies()
    assert not cc_client._is_expired(cc_client._currencies_cache_time)
    cc_client.invalidate_currencies_cache()
    assert cc_client._is_expired(cc_client._currencies_cache_time)
