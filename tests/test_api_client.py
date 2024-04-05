from cashctrl_api import CashCtrlAPIClient

def test_person_list():
    cc = CashCtrlAPIClient()
    response = cc.get("person/list.json")
