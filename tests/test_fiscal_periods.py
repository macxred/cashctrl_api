"""Unit tests for fiscal periods."""

from cashctrl_api import CashCtrlClient
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def cc_client() -> CashCtrlClient:
    return CashCtrlClient()


@pytest.fixture(scope="module")
def fiscal_periods(cc_client):
    # Explicitly call the base class method to circumvent the cache.
    return CashCtrlClient.list_fiscal_periods(cc_client)


def test_cached_fiscal_periods_same_to_actual(cc_client, fiscal_periods):
    pd.testing.assert_frame_equal(cc_client.list_fiscal_periods(), fiscal_periods)


def test_fiscal_period_from_id(cc_client, fiscal_periods):
    assert (
        cc_client.fiscal_period_from_id(fiscal_periods["id"].iat[0])
        == fiscal_periods["name"].iat[0]
    ), "Cached fiscal period name doesn't correspond to actual name"


def test_fiscal_period_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No fiscal period found for id"):
        cc_client.fiscal_period_from_id(99999999)


def test_fiscal_period_from_id_invalid_id_returns_none_with_allowed_missing(cc_client):
    assert cc_client.fiscal_period_from_id(99999999, allow_missing=True) is None


def test_fiscal_period_to_id(cc_client, fiscal_periods):
    assert (
        cc_client.fiscal_period_to_id(fiscal_periods["name"].iat[0])
        == fiscal_periods["id"].iat[0]
    ), "Cached fiscal period id doesn't correspond to actual id"


def test_fiscal_period_to_id_with_invalid_fiscal_period_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for fiscal period"):
        cc_client.fiscal_period_to_id("Nonexistent Period")


def test_fiscal_period_to_id_with_invalid_fiscal_period_returns_none_with_allowed_missing(
    cc_client
):
    assert cc_client.fiscal_period_to_id("Nonexistent Period", allow_missing=True) is None
