"""Module for listing directory contents with attributes in a pandas DataFrame."""

from pathlib import Path
import pandas as pd


def list_directory(directory: str | Path,
                   recursive: bool = False,
                   exclude_dirs: bool = False,
                   include_hidden: bool = False) -> pd.DataFrame:
    """Lists files and directories in a specified folder, with attributes such as
    size and modification time.

    Args:
        directory (str | Path): The directory to list.
        recursive (bool): If True, lists items recursively. Defaults to False.
        exclude_dirs (bool): If True, only files are listed, not directories.
                             Defaults to False.
        include_hidden (bool): If True, includes hidden files and directories
                               (those starting with a dot). Defaults to False.

    Returns:
        pd.DataFrame: A DataFrame where each row represents a file or directory,
                      with columns including 'path', 'ctime', 'mtime', and 'size'.
                      'ctime' and 'mtime' are in UTC.

    Raises:
        FileNotFoundError: If the specified directory does not exist or is not a directory.
    """
    directory_path = Path(directory).expanduser()
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}.")
    if not directory_path.is_dir():
        raise FileNotFoundError(f"`directory` is not a directory: {directory}.")

    def is_hidden(path):
        """Determines if the given path should be considered hidden."""
        return any(part.startswith(".") for part in path.parts)

    glob_pattern = "**/*" if recursive else "*"
    paths = [entry for entry in directory_path.glob(glob_pattern)
             if (not exclude_dirs or entry.is_file())
             and (include_hidden or not is_hidden(entry))]

    if paths:
        path_dicts = [
            {**{"path": path.relative_to(directory_path).as_posix()},
             **_file_attributes_as_dict(path)} for path in paths]
        df = pd.DataFrame(path_dicts)
        df["ctime"] = (pd.to_datetime(df["ctime_ns"], unit="ns")
                       .dt.tz_localize("UTC"))
        df["mtime"] = (pd.to_datetime(df["mtime_ns"], unit="ns")
                       .dt.tz_localize("UTC"))
    else:
        # Return an empty DataFrame with specified columns if no paths found
        df = pd.DataFrame({
            "path": pd.Series(dtype="string"),
            "size": pd.Series(dtype="Int64"),
            "ctime": pd.Series(dtype="datetime64[ns, UTC]"),
            "mtime": pd.Series(dtype="datetime64[ns, UTC]")})

    return df


def _file_attributes_as_dict(path: Path) -> dict:
    """Extract file attributes from a given path and return as a dictionary."""
    stat = path.stat()
    return {k[3:]: getattr(stat, k) for k in dir(stat) if k.startswith("st_")}
