import json
import pytest
from cashctrl_api import CashCtrlAPIClient

def test_person_list():
    cc = CashCtrlAPIClient()
    response = cc.get("person/list.json")

def test_person_flatten_dict():
    # create
    contact = {
        "firstName": "Tina",
        "lastName": "Test",
        "addresses": 
            [{"type": "MAIN",
                "address": "Teststreet 15",
                "zip": "1234",
                "city": "Testtown"
            }],
        "titleId": 2
    }
    cc = CashCtrlAPIClient()
    response = cc.post("person/create.json", data=contact)
    id = response["insertId"]
    # read
    response = cc.get("person/read.json", params={'id': id})
    # delete
    response = cc.post("person/delete.json", params={'ids': id})

def test_non_success_and_msg():
    cc = CashCtrlAPIClient()
    with pytest.raises(Exception) as e:
        assert(cc.post("person/create.json"))
    assert str(e.value) == 'API call failed with message: Either first name, last name or company must be set.'
  