"""
Snapshot testing for Uno applications.

This module provides utilities for snapshot testing of complex objects,
allowing developers to capture the state of objects and compare them
against stored snapshots in future test runs.
"""

from uno.testing.snapshot.snapshot import snapshot_test, compare_snapshot
from uno.testing.snapshot.manager import SnapshotManager, update_snapshot

__all__ = ["snapshot_test", "compare_snapshot", "update_snapshot", "SnapshotManager"]