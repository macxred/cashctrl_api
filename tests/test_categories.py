import pandas as pd, pytest
from cashctrl_api import CashCtrlAPIClient

initial_categories = [
    '/hello',
    '/world',
    '/how',
    '/are',
    '/you?'
]

further_categories = [
    '/hello/world/how/are/you/?',
    '/feeling/kind/of/warm',
]

def test_initial_category_creation():
    """Test that categories are correctly created initially."""
    cc = CashCtrlAPIClient()
    cc.update_categories('file', categories=initial_categories)
    remote_categories = cc.list_categories('file')
    assert set(initial_categories).issubset(remote_categories['path']), (
        "Remote categories do not match initial categories")

def test_category_addition():
    """Test that new categories are added correctly (delete=False)."""
    cc = CashCtrlAPIClient()
    cc.update_categories('file', categories=further_categories, delete=False)
    remote_categories = cc.list_categories('file')
    assert set(further_categories).issubset(remote_categories['path']), (
        "Not all initial categories appear in remote categories")

@pytest.mark.skip(reason="One category on test account can not be deleted.")
def test_category_deletion():
    """Test that categories are deleted when specified."""
    cc = CashCtrlAPIClient()
    cc.update_categories('file', categories=further_categories, delete=True)
    remote_categories = cc.list_categories('file')
    target = pd.Series(further_categories)
    assert all([target.str.startswith(node).any() for node in remote_categories['path']]), (
        "Remote categories do not match `further_categories'")

@pytest.mark.skip(reason="One category on test account can not be deleted.")
def test_category_removal():
    """Test that all categories are deleted when specified."""
    cc = CashCtrlAPIClient()
    cc.update_categories('file', categories=[], delete=True)
    remote_categories = cc.list_categories('file')
    assert len(remote_categories) == 0, "Some remote categories remain."

def test_invalid_path():
    """Test the system's response to invalid category paths."""
    invalid_categories = ['not/a/valid/path', '']
    cc = CashCtrlAPIClient()
    with pytest.raises(Exception):
        cc.update_categories('file', categories=invalid_categories[[0]])
    with pytest.raises(Exception):
        cc.update_categories('file', categories=invalid_categories[[1]])