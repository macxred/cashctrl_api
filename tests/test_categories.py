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

asterisk_path = '/Anlagevermögen/bla * blaaaa'
account_categories = {
    '/Anlagevermögen/hello': 1000,
    '/Anlagevermögen/world/how/are/you/?': 1010,
    '/Anlagevermögen/feeling/kind/of/warm': 1020,
    '/Anlagevermögen/are': 1020,
    '/Anlagevermögen/you?': 1020,
    '/Anlagevermögen/Finanzanlagen': 6000,
    asterisk_path: 6000,
}

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

def test_update_account_categories_with_list():
    """Test that should get error while updating account categories with target as a list type"""
    cc_client = CashCtrlClient()
    with pytest.raises(ValueError):
        cc_client.update_categories('account', target=categories)

def test_update_file_categories_with_dict():
    """Test that should get error while updating file categories with target as a dict type"""
    cc_client = CashCtrlClient()
    with pytest.raises(ValueError):
        cc_client.update_categories('file', target=account_categories)

def test_account_category_update():
    """Test that new updates categories for accounts and then restores initial state"""
    cc_client = CashCtrlClient()
    initial_categories = cc_client.list_categories('account')

    cc_client.update_categories('account', target=account_categories)
    remote = cc_client.list_categories('account')
    asterisk_node = remote[remote['path'] == asterisk_path]
    assert asterisk_node['text'].iat[0] == 'bla / blaaaa', (
        'Asterisk should be represented as slash symbol in cashCtrl')

    remote = remote.set_index('path')['number'].to_dict()
    assert all(category in remote.items() for category in account_categories.items()), (
        "Not all categories were updated")

    initial_paths = initial_categories.set_index('path')['number'].to_dict()
    cc_client.update_categories('account', target=initial_paths, delete=True)
    updated = cc_client.list_categories('account')
    updated = updated.set_index('path')['number'].to_dict()
    assert updated == initial_paths, "Initial categories were not restored"