"""
This castctrl_api package provides a thin client for interacting with the
CashCtrl REST API. In addition to generic GET, PUT, POST, and DELETE requests,
it includes functionality to list, create, and manage categories,
as well as to upload and download files.

Modules:
- client: Contains the CashCtrlClient class that encapsulates API interactions.
- list_directory: Provides a utility function listing local directory contents.
- enforce_dtypes: Provides a method to enforce a DataFrame column schema.
"""

from .client import CashCtrlClient
from .list_directory import list_directory
from .enforce_dtypes import enforce_dtypes
import constants