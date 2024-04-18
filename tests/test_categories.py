"""
Unit tests for listing and mirroring categories with CashCtrlClient.
"""

import pandas as pd, pytest
from cashctrl_api import CashCtrlClient

categories = [
    '/hello',
    '/world',
    '/how',
    '/are',
    '/you?'
]

more_categories = [
    '/hello/world/how/are/you/?',
    '/feeling/kind/of/warm',
]

def test_initial_category_creation():
    """Test that categories are correctly created initially."""
    cc_client = CashCtrlClient()
    cc_client.update_categories('file', target=categories)
    remote_categories = cc_client.list_categories('file')
    assert set(categories).issubset(remote_categories['path']), (
        "Remote categories do not match initial categories")

def test_category_addition():
    """Test that new categories are added correctly (delete=False)."""
    cc_client = CashCtrlClient()
    cc_client.update_categories('file', target=more_categories, delete=False)
    remote_categories = cc_client.list_categories('file')
    assert set(more_categories).issubset(remote_categories['path']), (
        "Not all initial categories appear in remote categories")

@pytest.mark.skip(reason="One category on test account can not be deleted.")
def test_category_deletion():
    """Test that categories are deleted when specified."""
    cc_client = CashCtrlClient()
    cc_client.update_categories('file', target=more_categories, delete=True)
    remote_categories = cc_client.list_categories('file')
    target = pd.Series(more_categories)
    assert all([target.str.startswith(node).any()
                for node in remote_categories['path']]), (
        "Remote categories do not match `more_categories'")

@pytest.mark.skip(reason="One category on test account can not be deleted.")
def test_category_removal():
    """Test that all categories are deleted when specified."""
    cc_client = CashCtrlClient()
    cc_client.update_categories('file', target=[], delete=True)
    remote_categories = cc_client.list_categories('file')
    assert len(remote_categories) == 0, "Some remote categories remain."

def test_invalid_path():
    """Test the system's response to invalid category paths."""
    invalid_categories = ['not/a/valid/path', '']
    cc_client = CashCtrlClient()
    with pytest.raises(Exception):
        cc_client.update_categories('file', target=invalid_categories[[0]])
    with pytest.raises(Exception):
        cc_client.update_categories('file', target=invalid_categories[[1]])