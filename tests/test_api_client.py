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

def test_exception_when_not_successful():
    cc = CashCtrlAPIClient()

    # Error message wit filed name (error['field'] is set)
    with pytest.raises(Exception) as e:
        cc.post(f"file/category/create.json")
    assert str(e.value) == 'API call failed. name: This field cannot be empty.'

    # Error message without filed name (error['field']=None)
    with pytest.raises(Exception) as e:
        cc.post("person/create.json")
    assert str(e.value) == 'API call failed. Either first name, last name or company must be set.'