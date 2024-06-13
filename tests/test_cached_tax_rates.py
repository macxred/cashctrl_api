"""
Unit tests for cached tax codes.
"""

import time
import pytest
import pandas as pd
from cashctrl_api import CachedCashCtrlClient, CashCtrlClient

@pytest.fixture(scope="module")
def cc_client():
    return CachedCashCtrlClient()

@pytest.fixture(scope="module")
def tax_rates():
    cc_client = CachedCashCtrlClient()
    return CashCtrlClient.list_tax_rates(cc_client)

def test_tax_rates_cache_is_none_on_init(cc_client):
    assert cc_client._tax_rates_cache == None
    assert cc_client._tax_rates_cache_time == None

def test_cached_tax_codes_same_to_actual(cc_client, tax_rates):
    pd.testing.assert_frame_equal(cc_client.list_tax_rates(), tax_rates)

def test_tax_code_from_id(cc_client, tax_rates):
    assert cc_client.tax_code_from_id(tax_rates['id'].iat[0]) == tax_rates['name'].iat[0], (
        'Cached tax code name doesn`t correspond actual name'
    )

def test_tax_code_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match='No tax code found for id'):
        cc_client.tax_code_from_id(99999999)

def test_tax_code_from_id_invalid_id_returns_none_with_allowed_missing(cc_client):
    assert cc_client.tax_code_from_id(99999999, allow_missing=True) == None

def test_tax_code_to_id(cc_client, tax_rates):
    assert cc_client.tax_code_to_id(tax_rates['name'].iat[1]) == tax_rates['id'].iat[1], (
        'Cached tax code id doesn`t correspond actual id'
    )

def test_tax_code_to_id_with_invalid_tax_code_raises_error(cc_client):
    with pytest.raises(ValueError, match='No id found for tax code'):
        cc_client.tax_code_to_id(99999999)

def test_tax_code_to_id_with_invalid_tax_code_returns_none_with_allowed_missing(cc_client):
    assert cc_client.tax_code_to_id(99999999,  allow_missing=True) == None

def test_tax_rates_cache_timeout(cc_client):
    cc_client = CachedCashCtrlClient(cache_timeout=1)
    cc_client.list_tax_rates()
    assert not cc_client._is_expired(cc_client._tax_rates_cache_time)
    time.sleep(1)
    assert cc_client._is_expired(cc_client._tax_rates_cache_time)

def test_tax_rates_cache_invalidation(cc_client):
    cc_client = CachedCashCtrlClient()
    cc_client.list_tax_rates()
    assert not cc_client._is_expired(cc_client._tax_rates_cache_time)
    cc_client.invalidate_tax_rates_cache()
    assert cc_client._is_expired(cc_client._tax_rates_cache_time)