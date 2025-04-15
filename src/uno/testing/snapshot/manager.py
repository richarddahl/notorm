# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Snapshot testing manager for Uno applications.

This module provides a manager class for snapshot testing, allowing developers
to perform more advanced operations with snapshots, including batch updates
and cleaning up unused snapshots.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from uno.testing.snapshot.snapshot import (
    snapshot_test,
    compare_snapshot,
    _get_snapshot_dir,
    _get_snapshot_path,
    _get_caller_info,
    _UnoJSONEncoder,
)


def update_snapshot(
    obj: Any,
    name: Optional[str] = None,
) -> bool:
    """
    Update a snapshot with a new object.
    
    This is a convenience wrapper around snapshot_test with update=True.
    
    Args:
        obj: The object to update the snapshot with
        name: Optional name to differentiate multiple snapshots in the same test
        
    Returns:
        True if the snapshot was updated successfully
        
    Example:
        ```python
        def test_complex_object():
            obj = create_complex_object()
            # Update the snapshot with the new object
            update_snapshot(obj)
        ```
    """
    return snapshot_test(obj, name=name, update=True)


class SnapshotManager:
    """
    Manager for snapshot operations.
    
    This class provides methods for managing snapshot files, including
    listing, updating, and cleaning up snapshots.
    
    Example:
        ```python
        # Create a snapshot manager
        manager = SnapshotManager()
        
        # List all snapshots
        snapshots = manager.list_snapshots()
        
        # Clean up unused snapshots
        manager.clean_unused_snapshots()
        ```
    """
    
    def __init__(self, snapshot_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the snapshot manager.
        
        Args:
            snapshot_dir: Optional path to the snapshot directory
        """
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else _get_snapshot_dir()
    
    def list_snapshots(self) -> List[Path]:
        """
        List all snapshot files.
        
        Returns:
            List of paths to snapshot files
        """
        snapshots = []
        
        # Walk through the snapshot directory
        for root, _, files in os.walk(self.snapshot_dir):
            for file in files:
                if file.endswith(".snapshot.json"):
                    snapshots.append(Path(root) / file)
        
        return snapshots
    
    def update_all_snapshots(
        self, 
        snapshots: Dict[str, Any],
        backup: bool = True
    ) -> Dict[str, bool]:
        """
        Update multiple snapshots at once.
        
        Args:
            snapshots: Dictionary mapping snapshot names to objects
            backup: If True, create backup copies of the original snapshots
            
        Returns:
            Dictionary mapping snapshot names to update success status
        """
        results = {}
        
        for name, obj in snapshots.items():
            # Create a backup if requested
            snapshot_path = self.snapshot_dir / f"{name}.snapshot.json"
            if backup and snapshot_path.exists():
                backup_path = snapshot_path.with_suffix(".snapshot.json.bak")
                shutil.copy2(snapshot_path, backup_path)
            
            # Update the snapshot
            success = snapshot_test(obj, name=name, update=True)
            results[name] = success
        
        return results
    
    def clean_unused_snapshots(
        self, 
        used_snapshots: Optional[Set[str]] = None,
        dry_run: bool = False
    ) -> List[Path]:
        """
        Clean up unused snapshot files.
        
        Args:
            used_snapshots: Set of snapshot names that are still in use
            dry_run: If True, don't actually delete files, just return what would be deleted
            
        Returns:
            List of snapshots that were (or would be) deleted
        """
        all_snapshots = self.list_snapshots()
        to_delete = []
        
        # If no used_snapshots provided, assume none are used
        if used_snapshots is None:
            to_delete = all_snapshots
        else:
            # Convert used_snapshots to absolute paths
            used_paths = {
                self.snapshot_dir / f"{name}.snapshot.json" 
                for name in used_snapshots
            }
            
            # Find snapshots not in used_paths
            for snapshot in all_snapshots:
                if snapshot not in used_paths:
                    to_delete.append(snapshot)
        
        # Delete snapshots if not a dry run
        if not dry_run:
            for snapshot in to_delete:
                snapshot.unlink()
        
        return to_delete
    
    def diff_snapshot(
        self, 
        obj: Any, 
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a detailed diff between an object and its snapshot.
        
        This is a wrapper around compare_snapshot that provides a more
        detailed diff in a structured format.
        
        Args:
            obj: The object to compare
            name: Optional name to differentiate multiple snapshots in the same test
            
        Returns:
            Dictionary with detailed diff information
        """
        # Use compare_snapshot to get basic diff
        result = compare_snapshot(obj, name)
        
        # If we got a diff, enhance it with more details
        if not result["matches"] and result["diff"]:
            # Parse the diff into a more structured format
            structured_diff = []
            
            for line in result["diff"]:
                if line.startswith("+ "):
                    structured_diff.append({
                        "type": "added",
                        "line": line[2:],
                    })
                elif line.startswith("- "):
                    structured_diff.append({
                        "type": "removed",
                        "line": line[2:],
                    })
                elif line.startswith("? "):
                    # Diff markers are not included in the structured diff
                    pass
                else:
                    structured_diff.append({
                        "type": "unchanged",
                        "line": line[2:] if line.startswith("  ") else line,
                    })
            
            # Add structured diff to the result
            result["structured_diff"] = structured_diff
        
        return result
    
    def restore_snapshot(self, name: str, backup_suffix: str = ".bak") -> bool:
        """
        Restore a snapshot from its backup.
        
        Args:
            name: Name of the snapshot to restore
            backup_suffix: Suffix of the backup file
            
        Returns:
            True if the snapshot was restored, False otherwise
        """
        snapshot_path = self.snapshot_dir / f"{name}.snapshot.json"
        backup_path = snapshot_path.with_suffix(f".snapshot.json{backup_suffix}")
        
        # Check if backup exists
        if not backup_path.exists():
            return False
        
        # Restore the backup
        shutil.copy2(backup_path, snapshot_path)
        return True