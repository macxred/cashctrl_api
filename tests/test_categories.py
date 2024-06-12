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

account_categories = {
    '/Assets/Anlagevermögen/hello': 1000,
    '/Assets/Anlagevermögen/world/how/are/you/?': 1010,
    '/Assets/Anlagevermögen/feeling/kind/of/warm': 1020,
    '/Assets/Anlagevermögen/are': 1020,
    '/Assets/Anlagevermögen/you?': 1020,
    '/Assets/Anlagevermögen/Finanzanlagen': 6000,
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

def test_update_file_categories_raises_error_when_creating_account_root_node():
    """Test that attempting to create a new root node in account categories raises an error"""
    cc_client = CashCtrlClient()
    with pytest.raises(ValueError, match="Cannot create new root node"):
        cc_client.update_categories('account', target={"/new_root_node": 42})

def test_account_category_update():
    """Test update_categories for accounts and then restores initial state"""
    cc_client = CashCtrlClient()
    initial_categories = cc_client.list_categories('account')

    # Check categories that do not already exist on remote are created
    assert not all([category in list(initial_categories['path']) for category in account_categories]), (
        "All account catetegories are already present on the server.")
    cc_client.update_categories('account', target=account_categories)
    remote = cc_client.list_categories('account')
    remote_dict = remote.set_index('path')['number'].to_dict()
    assert all(category in remote_dict.items() for category in account_categories.items()), (
        "Not all categories were updated")

    # Check that backslash in node names is converted to forward slash
    slash_path = '/Assets/Anlagevermögen/bla \\ blaaaa'
    assert slash_path not in list(remote['path']), 'Slash_path already exists on remote.'
    cc_client.update_categories('account', target={slash_path: 6000})
    remote = cc_client.list_categories('account')
    assert slash_path in list(remote['path']), 'Slash_path was not created.'
    slash_node = remote[remote['path'] == slash_path]
    assert slash_node['text'].iat[0] == 'bla / blaaaa', (
        'Backslash should be represented as slash symbol in cashCtrl')
    assert slash_node['number'].iat[0] == 6000, 'Incorrect sequence number.'

    # Check sequence number is updated for existing paths
    cc_client.update_categories('account', target={slash_path: 42})
    remote = cc_client.list_categories('account')
    assert slash_path in list(remote['path']), 'Slash_path has vanished.'
    slash_node = remote[remote['path'] == slash_path]
    assert slash_node['number'].iat[0] == 42, 'Sequence number not updated.'

    # Restore initial state
    initial_paths = initial_categories.set_index('path')['number'].to_dict()
    cc_client.update_categories('account', target=initial_paths, delete=True)
    updated = cc_client.list_categories('account')
    updated = updated.set_index('path')['number'].to_dict()
    assert updated == initial_paths, "Initial categories were not restored"