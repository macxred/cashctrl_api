"""Unit tests for basic requests with CashCtrlClient."""

from cashctrl_api import CashCtrlClient
import pytest


def test_person_list():
    cc_client = CashCtrlClient()
    cc_client.get("person/list.json")


def test_person_flatten_dict():
    """Test creating, reading, and deleting a person."""
    # create
    contact = {
        "firstName": "Tina",
        "lastName": "Test",
        "addresses": [
            {
                "type": "MAIN",
                "address": "Teststreet 15",
                "zip": "1234",
                "city": "Testtown",
            }
        ],
        "titleId": 2,
    }
    cc_client = CashCtrlClient()
    response = cc_client.post("person/create.json", data=contact)
    id = response["insertId"]
    # read
    response = cc_client.get("person/read.json", params={"id": id})
    # delete
    response = cc_client.post("person/delete.json", params={"ids": id})


def test_exception_when_not_successful():
    """Test exception handling for unsuccessful API calls."""
    cc_client = CashCtrlClient()

    # Error message with filed name (error['field'] is set)
    with pytest.raises(Exception) as e:
        cc_client.post("file/category/create.json")
    assert str(e.value) == "API call failed. name: This field cannot be empty."

    # Error message without filed name (error['field']=None)
    with pytest.raises(Exception) as e:
        cc_client.post("person/create.json")
    assert str(e.value) == (
        "API call failed. Either first name, last name or company must be set."
    )
