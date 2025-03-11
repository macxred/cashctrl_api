"""Unit tests for profit centers."""

from cashctrl_api import CashCtrlClient
import pytest


@pytest.fixture(scope="module")
def cc_client() -> CashCtrlClient:
    return CashCtrlClient()


@pytest.fixture(scope="module")
def profit_centers(cc_client):
    # Retrieve initial profit center ids
    initial_profit_center_ids = CashCtrlClient.list_profit_centers(cc_client)["id"].to_list()
    new_profit_center = {"name": "Test Profit Center", "number": 1000}
    cc_client.post("account/costcenter/create.json", params=new_profit_center)
    cc_client.list_profit_centers.cache_clear()

    yield CashCtrlClient.list_profit_centers(cc_client)

    # Delete any created profit center
    updated_profit_center_ids = CashCtrlClient.list_profit_centers(cc_client)["id"].to_list()
    to_delete = set(updated_profit_center_ids) - set(initial_profit_center_ids)
    if len(to_delete):
        ids = ",".join([str(id) for id in to_delete])
        cc_client.post("account/costcenter/delete.json", params={"ids": ids})


def test_profit_center_from_id(cc_client, profit_centers):
    profit_center_from_id = cc_client.profit_center_from_id(profit_centers["id"].iat[0])
    assert profit_center_from_id == profit_centers["name"].iat[0], (
        "Cached profit center name doesn't correspond actual name"
    )


def test_profit_centers_from_id_invalid_id_raises_error(cc_client):
    with pytest.raises(ValueError, match="No profit center found for id"):
        cc_client.profit_center_from_id(99999999)


def test_profit_center_from_id_invalid_id_returns_none_with_allowed_missing(cc_client):
    assert cc_client.profit_center_from_id(99999999, allow_missing=True) is None


def test_profit_center_to_id(cc_client, profit_centers):
    assert (
        cc_client.profit_center_to_id(profit_centers["name"].iat[0]) == profit_centers["id"].iat[0]
    ), "Cached profit center id doesn't correspond actual id"


def test_profit_center_to_id_with_invalid_profit_center_name_raises_error(cc_client):
    with pytest.raises(ValueError, match="No id found for profit center"):
        cc_client.profit_center_to_id(99999999)


def test_profit_center_to_id_with_invalid_profit_center_returns_none_with_allowed_missing(
    cc_client
):
    assert cc_client.profit_center_to_id(99999999, allow_missing=True) is None
