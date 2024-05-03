"""
Unit tests for listing methods to have expected columns
with CashCtrlClient.
"""

import pandas as pd
from cashctrl_api import CashCtrlClient, constants

# Test function with assertions to check the tax rates DataFrame
def test_list_tax_rates_to_have_expected_columns():
    """
    Test that the DataFrame returned by CashCtrlClient contains all expected columns
    with the correct data types as specified in TAX_COLUMNS.
    """
    # Given: CashCtrlClient returns a DataFrame of tax rates
    cc_client = CashCtrlClient()
    tax_rates = cc_client.list_tax_rates()

    assert isinstance(tax_rates, pd.DataFrame), "`tax_rates` is not a DataFrame."
    # Check if some expected columns are missing or Unexpected columns 
    # found in the DataFrame
    assert set(constants.TAX_COLUMNS.keys()) == set(tax_rates.columns), (
        "Some expected columns are missing or unexpected columns found"
    )

    # Check that the data types of the columns are as expected
    for column, expected_dtype in constants.TAX_COLUMNS.items():
        actual_dtype = tax_rates[column].dtype
        assert actual_dtype == expected_dtype, (
            f"Column '{column}' has incorrect dtype. Expected '{expected_dtype}', "
            f"but got '{actual_dtype}'."
        )

# Test function to check list_accounts returns expected columns and data types
def test_list_accounts_to_have_expected_columns():
    """
    Test that the DataFrame returned by CashCtrlClient's list_accounts contains all expected
    columns with the correct data types as specified in ACCOUNT_COLUMNS.
    """
    # Create the CashCtrlClient object and fetch the DataFrame
    cc_client = CashCtrlClient()
    accounts = cc_client.list_accounts()

    assert isinstance(accounts, pd.DataFrame), "`accounts` is not a DataFrame."

    # Check if all expected columns are in the DataFrame
    assert set(constants.ACCOUNT_COLUMNS.keys()).issubset(
        accounts.columns
    ), "Some expected columns are missing."

    # Check for unexpected columns in the DataFrame
    unexpected_columns = set(accounts.columns) - set(constants.ACCOUNT_COLUMNS.keys())
    assert not unexpected_columns, (
        f"Unexpected columns found: {unexpected_columns}."
    )

    # Check that the data types of the columns are as expected
    for column, expected_dtype in constants.ACCOUNT_COLUMNS.items():
        actual_dtype = accounts[column].dtype
        assert actual_dtype == expected_dtype, (
            f"Column '{column}' has incorrect dtype. Expected '{expected_dtype}', "
            f"but got '{actual_dtype}'."
        )

# Test function to check list_journal_entries returns expected columns and data types
def test_list_journal_entries_to_have_columns():
    """
    Test that the DataFrame returned by CashCtrlClient's list_journal_entries contains all expected
    columns with the correct data types as specified in JOURNAL_ENTRIES.
    """
    # Create the CashCtrlClient object and fetch the DataFrame
    cc_client = CashCtrlClient()
    journal_entries = cc_client.list_journal_entries()

    assert isinstance(journal_entries, pd.DataFrame), "`journal_entries` is not a DataFrame."

    # Check if all expected columns are in the DataFrame
    assert set(constants.JOURNAL_ENTRIES.keys()).issubset(
        journal_entries.columns
    ), "Some expected columns are missing."

    # Check for unexpected columns in the DataFrame
    unexpected_columns = set(journal_entries.columns) - set(constants.JOURNAL_ENTRIES.keys())
    assert not unexpected_columns, (
        f"Unexpected columns found: {unexpected_columns}."
    )

    # Check that the data types of the columns are as expected
    for column, expected_dtype in constants.JOURNAL_ENTRIES.items():
        actual_dtype = journal_entries[column].dtype
        assert actual_dtype == expected_dtype, (
            f"Column '{column}' has incorrect dtype. Expected '{expected_dtype}', "
            f"but got '{actual_dtype}'."
        )