"""Unit tests for local directory listing with list_directory()."""

from pathlib import Path
from cashctrl_api import list_directory
import pandas as pd
import pytest


@pytest.fixture
def mock_directory(tmp_path: Path) -> Path:
    """Create a mock directory with various files and subdirectories for testing."""
    # For debugging, set: tmp_path = Path("temp_test"); tmp_path.mkdir()
    (tmp_path / "file1.txt").write_text("This is a text file.")
    (tmp_path / "file2.log").write_text("Log content here.")
    (tmp_path / ".hiddenfile").write_text("Secret content.")

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("Another text file in a subdirectory.")

    hidden_dir = tmp_path / ".hiddendir"
    hidden_dir.mkdir()
    (hidden_dir / "hidden_file.txt").write_text("Hidden file in hidden dir.")

    return tmp_path


def test_non_recursive_listing(mock_directory: Path) -> None:
    """Test non-recursive listing of directory contents."""
    result_df = list_directory(mock_directory)
    expected_files = {"file1.txt", "file2.log", "subdir"}
    assert set(result_df["path"]) == expected_files


def test_exclude_directories(mock_directory: Path) -> None:
    """Test excluding directories from the listing."""
    result_df = list_directory(mock_directory, exclude_dirs=True)
    expected_files = {"file1.txt", "file2.log"}
    assert set(result_df["path"]) == expected_files


def test_recursive_listing(mock_directory: Path) -> None:
    """Test recursive listing of directory contents."""
    result_df = list_directory(mock_directory, recursive=True)
    expected_files = {"file1.txt", "file2.log", "subdir", "subdir/file3.txt"}
    assert set(result_df["path"]) == expected_files


def test_recursive_exclude_directories(mock_directory: Path) -> None:
    """Test recursive listing excluding directories."""
    result_df = list_directory(mock_directory, recursive=True, exclude_dirs=True)
    assert all(
        not Path(mock_directory / p).is_dir() for p in result_df["path"]
    )


def test_include_hidden_files(mock_directory: Path) -> None:
    """Test including hidden files in the listing."""
    result_df = list_directory(
        mock_directory, recursive=True, include_hidden=True
    )
    assert ".hiddenfile" in set(result_df["path"])
    assert ".hiddendir/hidden_file.txt" in set(result_df["path"])


def test_exclude_hidden_files(mock_directory: Path) -> None:
    """Test excluding hidden files from the listing."""
    result_df = list_directory(
        mock_directory, recursive=True, include_hidden=False
    )
    assert ".hiddenfile" not in set(result_df["path"])
    assert ".hiddendir/hidden_file.txt" not in set(result_df["path"])


def test_non_existent_directory() -> None:
    """Test listing a non-existent directory."""
    with pytest.raises(FileNotFoundError):
        list_directory("nonexistent_directory")


def test_empty_directory(tmp_path: Path) -> None:
    """Test listing an empty directory."""
    result_df = list_directory(tmp_path)
    assert isinstance(result_df, pd.DataFrame), (
        "The result should be a pd.DataFrame."
    )
    assert result_df.empty, (
        "The DataFrame should be empty for an empty directory."
    )
