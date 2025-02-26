"""Unit tests for currencies."""

from cashctrl_api import CashCtrlClient
import pytest
import pandas as pd


@pytest.fixture(scope="module")
def cc_client():
    return CashCtrlClient()


@pytest.fixture(scope="module")
def currencies():
    cc_client = CashCtrlClient()
    return cc_client.list_currencies()


def test_cached_currencies_same_to_actual(cc_client, currencies):
    pd.testing.assert_frame_equal(cc_client.list_currencies(), currencies)


def test_currency_from_id(cc_client, currencies):
    assert (
        cc_client.currency_from_id(currencies["id"].iat[0]) == currencies["text"].iat[0]
    ), "Cached currency doesn't correspond actual"


def test_currency_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No currency found for id"):
        cc_client.currency_from_id(99999999)


def test_currency_to_id(cc_client, currencies):
    assert (
        cc_client.currency_to_id(currencies["text"].iat[1]) == currencies["id"].iat[1]
    ), "Cached currency id doesn't correspond actual id"


def test_currency_to_id_with_invalid_currency_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for currency"):
        cc_client.currency_to_id(99999999)


def test_exchange_rate(cc_client):
    exchange_rate = cc_client.get_exchange_rate("USD", "CHF")
    assert isinstance(exchange_rate, float), "`exchange_rate` is not a Float."

    # Exchange rate for invalid currency should raise an error
    with pytest.raises(Exception):
        cc_client.get_exchange_rate("USD", "INVALID")

    exchange_rate = cc_client.get_exchange_rate("USD", "USD")
    assert exchange_rate == 1, "Exchange rate for the same currency should be 1."

    exchange_rate = cc_client.get_exchange_rate("USD", "CHF", '2020-01-15')
    assert exchange_rate == 0.967145, "Exchange rate for USD-CHF on 2020-01-15 should be 0.967145."
