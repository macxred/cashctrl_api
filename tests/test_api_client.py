import json
from cashctrl_api import CashCtrlAPIClient

def test_person_list():
    cc = CashCtrlAPIClient()
    response = cc.get("person/list.json")

def test_person_flatten_dict():
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
    response = cc.get("person/read.json", params={'id': id})
    response = cc.post("person/delete.json", params={'ids': id})