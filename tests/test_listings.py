"""Unit tests for listing methods to have expected columns with CashCtrlClient."""

from cashctrl_api import CashCtrlClient, constants
import pandas as pd


def test_list_tax_rates_to_have_expected_columns() -> None:
    """Test that the DataFrame returned by CashCtrlClient contains all expected columns
    with the correct data types as specified in TAX_COLUMNS.
    """
    # Given: CashCtrlClient returns a DataFrame of tax rates
    cc_client = CashCtrlClient()
    tax_rates = cc_client.list_tax_rates()

    assert isinstance(tax_rates, pd.DataFrame), "`tax_rates` is not a DataFrame."
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


def test_list_accounts_to_have_expected_columns() -> None:
    """Test that the DataFrame returned by CashCtrlClient's list_accounts contains all expected
    columns with the correct data types as specified in ACCOUNT_COLUMNS.
    """
    # Create the CashCtrlClient object and fetch the DataFrame
    cc_client = CashCtrlClient()
    accounts = cc_client.list_accounts()

    assert isinstance(accounts, pd.DataFrame), "`accounts` is not a DataFrame."
    assert set(constants.ACCOUNT_COLUMNS.keys()) == set(accounts.columns), (
        "Some expected columns are missing or unexpected columns found"
    )

    # Check that the data types of the columns are as expected
    for column, expected_dtype in constants.ACCOUNT_COLUMNS.items():
        actual_dtype = accounts[column].dtype
        assert actual_dtype == expected_dtype, (
            f"Column '{column}' has incorrect dtype. Expected '{expected_dtype}', "
            f"but got '{actual_dtype}'."
        )


def test_list_journal_entries_to_have_columns() -> None:
    """Test that the DataFrame returned by CashCtrlClient's list_journal_entries contains
    all expected columns with the correct data types as specified in JOURNAL_ENTRIES.
    """
    # Create the CashCtrlClient object and fetch the DataFrame
    cc_client = CashCtrlClient()
    journal_entries = cc_client.list_journal_entries()

    assert isinstance(journal_entries, pd.DataFrame), "`journal_entries` is not a DataFrame."
    assert set(constants.JOURNAL_ENTRIES.keys()) == set(journal_entries.columns), (
        "Some expected columns are missing or unexpected columns found"
    )

    # Check that the data types of the columns are as expected
    for column, expected_dtype in constants.JOURNAL_ENTRIES.items():
        actual_dtype = journal_entries[column].dtype
        assert actual_dtype == expected_dtype, (
            f"Column '{column}' has incorrect dtype. Expected '{expected_dtype}', "
            f"but got '{actual_dtype}'."
        )
