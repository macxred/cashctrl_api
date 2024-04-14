from pathlib import Path
import pandas as pd

def list_directory(directory: str | Path, recursive: bool = False, exclude_dirs: bool = False,
                   include_hidden: bool = False) -> pd.DataFrame:
    """
    Lists files and directories in a specified folder, with their attributes such as size,
    modification time, etc.

    Parameters:
        directory (str | Path): The directory to list.
        recursive (bool): If True, list items recursively. If False, only list items in the specified directory. Default is False.
        exclude_dirs (bool): If True, the listing only contains files, not directories. Default is False.
        include_hidden (bool): If True, include hidden files and directories (those starting with a dot). Default is False.

    Returns:
        pd.DataFrame: A DataFrame where each row represents a file or directory, including attributes.
                      Columns include 'path', the relative path from the given base directory,
                      'ctime' (creation time) and 'mtime' (modification time), both in UTC, 'size', etc.
    """
    directory_path = Path(directory).expanduser()
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}.")
    if not directory_path.is_dir():
        raise FileNotFoundError(f"`directory` is not a directory: {directory}.")

    def is_hidden(path):
        return any(part.startswith('.') for part in path.parts)
    glob_pattern = "**/*" if recursive else "*"
    paths = [entry for entry in directory_path.glob(glob_pattern)
                if ((not exclude_dirs) or entry.is_file())
                and (include_hidden or not is_hidden(entry))]
    if len(paths) > 0:
        path_dicts = [
            {**{'path': str(path.relative_to(directory_path))}, **_file_attributes_as_dict(path)}
            for path in paths]
        df = pd.DataFrame(path_dicts)
        df['ctime'] = pd.to_datetime(df['ctime_ns'], unit='ns').dt.tz_localize('UTC')
        df['mtime'] = pd.to_datetime(df['mtime_ns'], unit='ns').dt.tz_localize('UTC')
    else:
        # Return an empty DataFrame with specified columns
        df = pd.DataFrame({
            'path': pd.StringDtype(),
            'size': pd.Int64Dtype(),
            'ctime': pd.Series(dtype='datetime64[ns, UTC]'),
            'mtime': pd.Series(dtype='datetime64[ns, UTC]')})

    return df

def _file_attributes_as_dict(path: Path) -> dict:
    """Extract file attributes from a given path and return as a dictionary."""
    stat = path.stat()
    return {k[3:]: getattr(stat, k) for k in dir(stat) if k.startswith('st_')}
