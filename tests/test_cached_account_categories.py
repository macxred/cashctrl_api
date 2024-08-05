"""Unit tests for cached account categories."""

import time
from cashctrl_api import CachedCashCtrlClient, CashCtrlClient
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def cc_client():
    return CachedCashCtrlClient()


@pytest.fixture(scope="module")
def account_categories(cc_client):
    # Explicitly call the base class method to circumvent the cache.
    return CashCtrlClient.list_categories(cc_client, "account", include_system=True)


def test_account_categories_cache_is_none_on_init(cc_client):
    assert cc_client._account_categories_cache is None
    assert cc_client._account_categories_cache_time is None


def test_cached_account_categories_same_to_actual(cc_client, account_categories):
    pd.testing.assert_frame_equal(cc_client.list_account_categories(), account_categories)


def test_account_category_from_id(cc_client, account_categories):
    assert (
        cc_client.account_category_from_id(account_categories["id"].iat[0])
        == account_categories["path"].iat[0]
    ), "Cached account category doesn't correspond actual"


def test_account_category_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No path found for account category id"):
        cc_client.account_category_from_id(99999999)


def test_account_category_to_id(cc_client, account_categories):
    assert (
        cc_client.account_category_to_id(account_categories["path"].iat[1])
        == account_categories["id"].iat[1]
    ), "Cached account category id doesn't correspond actual id"


def test_account_category_to_id_with_invalid_account_category_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for account category path"):
        cc_client.account_category_to_id(99999999)


def test_account_categories_cache_timeout():
    cc_client = CachedCashCtrlClient(cache_timeout=1)
    cc_client.list_account_categories()
    assert not cc_client._is_expired(cc_client._account_categories_cache_time)
    time.sleep(1)
    assert cc_client._is_expired(cc_client._account_categories_cache_time)


def test_account_categories_cache_invalidation():
    cc_client = CachedCashCtrlClient()
    cc_client.list_account_categories()
    assert not cc_client._is_expired(cc_client._account_categories_cache_time)
    cc_client.invalidate_account_categories_cache()
    assert cc_client._is_expired(cc_client._account_categories_cache_time)
