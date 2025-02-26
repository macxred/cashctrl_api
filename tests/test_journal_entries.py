"""Unit tests for journal entries."""

from cashctrl_api import CashCtrlClient
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def cc_client() -> CashCtrlClient:
    return CashCtrlClient()


@pytest.fixture(scope="module")
def journal_entries(cc_client):
    # Explicitly call the base class method to circumvent the cache.
    return CashCtrlClient.list_journal_entries(cc_client)


def test_cached_journal_entries_same_to_actual(cc_client, journal_entries):
    pd.testing.assert_frame_equal(cc_client.list_journal_entries(), journal_entries)
