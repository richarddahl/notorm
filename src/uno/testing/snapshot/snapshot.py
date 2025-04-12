# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Snapshot testing utilities for Uno applications.

This module provides functions for snapshot testing, allowing developers
to capture the state of complex objects and compare them against stored
snapshots in future test runs.
"""

import datetime
import json
import os
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
import hashlib
import difflib


def _get_snapshot_dir() -> Path:
    """
    Get the directory where snapshots are stored.
    
    Returns:
        Path to the snapshot directory
    """
    # Start with the current file's directory
    current_file = inspect.currentframe().f_back.f_back.f_code.co_filename
    current_dir = Path(current_file).parent
    
    # Walk up the directory tree to find tests directory
    test_dir = None
    current_path = current_dir
    while current_path.name and not test_dir:
        if current_path.name == "tests":
            test_dir = current_path
            break
        current_path = current_path.parent
    
    if not test_dir:
        # If we couldn't find a tests directory, use a conventional location
        project_root = Path(os.getcwd())
        test_dir = project_root / "tests"
    
    # Create snapshots directory if it doesn't exist
    snapshot_dir = test_dir / "snapshots"
    snapshot_dir.mkdir(exist_ok=True)
    
    return snapshot_dir


def _get_caller_info() -> Dict[str, str]:
    """
    Get information about the caller function.
    
    Returns:
        Dictionary with information about the caller
    """
    # Get info about the test function that called snapshot_test
    frame = inspect.currentframe().f_back.f_back
    caller_file = frame.f_code.co_filename
    caller_function = frame.f_code.co_name
    caller_class = None
    
    # Try to determine the class name if the caller is a method
    frame_locals = frame.f_locals
    if "self" in frame_locals:
        caller_class = frame_locals["self"].__class__.__name__
    
    # Get the module name
    module_name = inspect.getmodulename(caller_file) or "unknown_module"
    
    return {
        "file": caller_file,
        "module": module_name,
        "function": caller_function,
        "class": caller_class
    }


def _get_snapshot_path(caller_info: Dict[str, str], name: Optional[str] = None) -> Path:
    """
    Get the path to the snapshot file.
    
    Args:
        caller_info: Information about the caller
        name: Optional name to differentiate multiple snapshots in the same test
        
    Returns:
        Path to the snapshot file
    """
    snapshot_dir = _get_snapshot_dir()
    
    # Create a snapshot filename based on the caller information
    module_part = caller_info["module"]
    class_part = f"{caller_info['class']}_" if caller_info["class"] else ""
    func_part = caller_info["function"]
    name_part = f"_{name}" if name else ""
    
    filename = f"{module_part}_{class_part}{func_part}{name_part}.snapshot.json"
    
    # Create module-specific subdirectory
    module_dir = snapshot_dir / module_part
    module_dir.mkdir(exist_ok=True)
    
    return module_dir / filename


class _UnoJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles Uno objects and other complex types."""
    
    def default(self, obj):
        # Handle datetime objects
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Handle Uno models
        if hasattr(obj, "__dict__") and hasattr(obj, "__class__"):
            # Try to get a dict representation
            if hasattr(obj, "dict") and callable(obj.dict):
                try:
                    return obj.dict()
                except Exception:
                    pass
            
            # Fall back to __dict__
            result = {}
            for key, value in obj.__dict__.items():
                # Skip private attributes
                if not key.startswith("_"):
                    result[key] = value
            
            result["__type__"] = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
            return result
        
        # Handle other types
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def snapshot_test(
    obj: Any,
    name: Optional[str] = None,
    update: bool = False,
) -> bool:
    """
    Test an object against a stored snapshot.
    
    This function captures the state of an object and compares it against 
    a stored snapshot. If the snapshot doesn't exist, it creates one.
    
    Args:
        obj: The object to snapshot
        name: Optional name to differentiate multiple snapshots in the same test
        update: If True, update the snapshot even if it exists
        
    Returns:
        True if the object matches the snapshot, False if it doesn't
        
    Example:
        ```python
        def test_complex_object():
            obj = create_complex_object()
            assert snapshot_test(obj)
        ```
    """
    caller_info = _get_caller_info()
    snapshot_path = _get_snapshot_path(caller_info, name)
    
    # Convert object to JSON
    try:
        current_json = json.dumps(
            obj, 
            indent=2, 
            sort_keys=True, 
            cls=_UnoJSONEncoder
        )
    except (TypeError, ValueError) as e:
        raise ValueError(f"Could not convert object to JSON: {e}")
    
    # If snapshot doesn't exist or update is True, create it
    if not snapshot_path.exists() or update:
        with open(snapshot_path, "w") as f:
            f.write(current_json)
        return True
    
    # Otherwise, read the existing snapshot and compare
    with open(snapshot_path, "r") as f:
        expected_json = f.read()
    
    # Parse and re-serialize both to normalize formatting
    try:
        current_data = json.loads(current_json)
        expected_data = json.loads(expected_json)
        
        # Re-serialize with same parameters to normalize formatting
        current_normalized = json.dumps(
            current_data, 
            indent=2, 
            sort_keys=True
        )
        expected_normalized = json.dumps(
            expected_data, 
            indent=2, 
            sort_keys=True
        )
        
        # Compare normalized JSON strings
        return current_normalized == expected_normalized
    except json.JSONDecodeError:
        # Fall back to direct string comparison if JSON parsing fails
        return current_json == expected_json


def compare_snapshot(
    obj: Any,
    name: Optional[str] = None,
    update: bool = False,
) -> Dict[str, Any]:
    """
    Compare an object against a stored snapshot and return detailed differences.
    
    This function is similar to snapshot_test but returns detailed information
    about the differences between the object and the snapshot.
    
    Args:
        obj: The object to compare
        name: Optional name to differentiate multiple snapshots in the same test
        update: If True, update the snapshot even if it exists
        
    Returns:
        A dictionary with the following keys:
        - matches: True if the object matches the snapshot, False if it doesn't
        - diff: A list of differences between the object and the snapshot
        - snapshot_path: The path to the snapshot file
        
    Example:
        ```python
        def test_complex_object():
            obj = create_complex_object()
            result = compare_snapshot(obj)
            if not result["matches"]:
                print("Differences:", result["diff"])
            assert result["matches"]
        ```
    """
    caller_info = _get_caller_info()
    snapshot_path = _get_snapshot_path(caller_info, name)
    
    # Convert object to JSON
    try:
        current_json = json.dumps(
            obj, 
            indent=2, 
            sort_keys=True, 
            cls=_UnoJSONEncoder
        )
    except (TypeError, ValueError) as e:
        raise ValueError(f"Could not convert object to JSON: {e}")
    
    # If snapshot doesn't exist or update is True, create it
    if not snapshot_path.exists() or update:
        with open(snapshot_path, "w") as f:
            f.write(current_json)
        return {
            "matches": True,
            "diff": [],
            "snapshot_path": str(snapshot_path),
            "created": not snapshot_path.exists(),
            "updated": update and snapshot_path.exists()
        }
    
    # Otherwise, read the existing snapshot and compare
    with open(snapshot_path, "r") as f:
        expected_json = f.read()
    
    # Parse and re-serialize both to normalize formatting
    try:
        current_data = json.loads(current_json)
        expected_data = json.loads(expected_json)
        
        # Re-serialize with same parameters to normalize formatting
        current_normalized = json.dumps(
            current_data, 
            indent=2, 
            sort_keys=True
        )
        expected_normalized = json.dumps(
            expected_data, 
            indent=2, 
            sort_keys=True
        )
        
        # Check if they match
        matches = current_normalized == expected_normalized
        
        # If they don't match, generate a diff
        if not matches:
            current_lines = current_normalized.splitlines()
            expected_lines = expected_normalized.splitlines()
            
            differ = difflib.Differ()
            diff = list(differ.compare(expected_lines, current_lines))
        else:
            diff = []
        
        return {
            "matches": matches,
            "diff": diff,
            "snapshot_path": str(snapshot_path),
            "created": False,
            "updated": False
        }
    except json.JSONDecodeError:
        # Fall back to direct string comparison if JSON parsing fails
        matches = current_json == expected_json
        
        if not matches:
            current_lines = current_json.splitlines()
            expected_lines = expected_json.splitlines()
            
            differ = difflib.Differ()
            diff = list(differ.compare(expected_lines, current_lines))
        else:
            diff = []
        
        return {
            "matches": matches,
            "diff": diff,
            "snapshot_path": str(snapshot_path),
            "created": False,
            "updated": False
        }