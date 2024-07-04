"""Unit tests for basic requests with CashCtrlClient."""

from cashctrl_api import CashCtrlClient
import pytest


def test_get_person_list():
    cc_client = CashCtrlClient()
    cc_client.get("person/list.json")


def test_create_read_delete_person():
    contact = {
        "firstName": "Tina",
        "lastName": "Test",
        "titleId": 2,
    }
    cc_client = CashCtrlClient()
    response = cc_client.post("person/create.json", data=contact)
    id = response["insertId"]
    response = cc_client.get("person/read.json", params={"id": id})
    response = cc_client.post("person/delete.json", params={"ids": id})


def test_create_category_failed_with_invalid_payload():
    cc_client = CashCtrlClient()
    with pytest.raises(Exception, match='API call failed'):
        cc_client.post("file/category/create.json")


def test_create_person_failed_with_invalid_payload():
    cc_client = CashCtrlClient()
    with pytest.raises(Exception, match='API call failed'):
        cc_client.post("person/create.json")
