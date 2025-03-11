"""Unit tests for tax codes."""

from cashctrl_api import CashCtrlClient
import pytest


@pytest.fixture(scope="module")
def cc_client() -> CashCtrlClient:
    return CashCtrlClient()


def test_tax_code_from_id(cc_client):
    tax_rates = cc_client.list_tax_rates()
    assert (
        cc_client.tax_code_from_id(tax_rates["id"].iat[0]) == tax_rates["name"].iat[0]
    ), "Mapped tax code name doesn't correspond actual name"


def test_tax_code_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No tax code found for id"):
        cc_client.tax_code_from_id(99999999)


def test_tax_code_from_id_invalid_id_returns_none_with_allowed_missing(cc_client):
    assert cc_client.tax_code_from_id(99999999, allow_missing=True) is None


def test_tax_code_to_id(cc_client):
    tax_rates = cc_client.list_tax_rates()
    assert (
        cc_client.tax_code_to_id(tax_rates["name"].iat[1]) == tax_rates["id"].iat[1]
    ), "Mapped tax code id doesn't correspond actual id"


def test_tax_code_to_id_with_invalid_tax_code_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for tax code"):
        cc_client.tax_code_to_id(99999999)


def test_tax_code_to_id_with_invalid_tax_code_returns_none_with_allowed_missing(cc_client):
    assert cc_client.tax_code_to_id(99999999, allow_missing=True) is None
