"""Unit tests for account categories."""

from cashctrl_api import CashCtrlClient
import pytest


@pytest.fixture(scope="module")
def cc_client():
    return CashCtrlClient()


def test_account_category_from_id(cc_client):
    account_categories = cc_client.list_account_categories()
    assert (
        cc_client.account_category_from_id(account_categories["id"].iat[0])
        == account_categories["path"].iat[0]
    ), "Mapped account category doesn't correspond actual"


def test_account_category_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No path found for account category id"):
        cc_client.account_category_from_id(99999999)


def test_account_category_to_id(cc_client):
    account_categories = cc_client.list_account_categories()
    assert (
        cc_client.account_category_to_id(account_categories["path"].iat[1])
        == account_categories["id"].iat[1]
    ), "Mapped account category id doesn't correspond actual id"


def test_account_category_to_id_with_invalid_account_category_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for account category path"):
        cc_client.account_category_to_id(99999999)
