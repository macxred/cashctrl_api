"""Unit tests for currencies."""

from cashctrl_api import CashCtrlClient
import pytest


def test_exchange_rate():
    cc_client = CashCtrlClient()

    exchange_rate = cc_client.get_exchange_rate("USD", "CHF")
    assert isinstance(exchange_rate, float), "`exchange_rate` is not a Float."

    # Exchange rate for invalid currency should raise an error
    with pytest.raises(Exception):
        cc_client.get_exchange_rate("USD", "INVALID")

    exchange_rate = cc_client.get_exchange_rate("USD", "USD")
    assert exchange_rate == 1, "Exchange rate for the same currency should be 1."

    exchange_rate = cc_client.get_exchange_rate("USD", "CHF", '2020-01-15')
    assert exchange_rate == 0.967145, "Exchange rate for USD-CHF on 2020-01-15 should be 0.967145."
