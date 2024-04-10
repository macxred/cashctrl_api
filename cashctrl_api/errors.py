class CashCtrlAPIClientError(Exception):
    "Raised when something fails within the client and/or API call"
    pass

class CashCtrlAPINoSuccess(Exception):
    "Raised when an API call returns a 'Success' field with the 'False' value"
    pass