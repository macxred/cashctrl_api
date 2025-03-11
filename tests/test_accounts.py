"""Unit tests for accounts."""

from cashctrl_api import CashCtrlClient
import pytest


@pytest.fixture(scope="module")
def cc_client():
    return CashCtrlClient()


def test_account_from_id(cc_client):
    accounts = cc_client.list_accounts()
    assert (
        cc_client.account_from_id(accounts["id"].iat[0]) == accounts["number"].iat[0]
    ), "Mapped account number doesn't correspond actual number"


def test_account_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No account found for id"):
        cc_client.account_from_id(99999999)


def test_account_from_id_invalid_id_returns_none_with_allowed_missing(cc_client):
    assert cc_client.account_from_id(99999999, allow_missing=True) is None


def test_account_to_id(cc_client):
    accounts = cc_client.list_accounts()
    assert (
        cc_client.account_to_id(accounts["number"].iat[1]) == accounts["id"].iat[1]
    ), "Mapped account id doesn't correspond actual id"


def test_account_to_id_with_invalid_account_number_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for account"):
        cc_client.account_to_id(99999999)


def test_account_to_id_with_invalid_account_number_returns_none_with_allowed_missing(cc_client):
    assert cc_client.account_to_id(99999999, allow_missing=True) is None


def test_account_to_currency(cc_client):
    accounts = cc_client.list_accounts()
    assert (
        cc_client.account_to_currency(accounts["number"].iat[1])
        == accounts["currencyCode"].iat[1]
    ), "Mapped account currency doesn't correspond actual currency"


def test_account_to_currency_with_invalid_account_number_raises_error(cc_client):
    with pytest.raises(ValueError, match="No currency found for account"):
        cc_client.account_to_currency(99999999)


def test_account_to_currency_with_invalid_account_number_returns_none_with_allowed_missing(
    cc_client
):
    assert cc_client.account_to_currency(99999999, allow_missing=True) is None
