# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the snapshot testing module.

These tests verify the functionality of the snapshot testing utilities.
"""

import json
import os
import pytest
from datetime import datetime
from pathlib import Path

from uno.testing.snapshot import snapshot_test, compare_snapshot


class TestObject:
    """Test object class for snapshot testing."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    def __init__(self, name, value, created_at=None):
        self.name = name
        self.value = value
        self.created_at = created_at or datetime.now()


class TestSnapshotTest:
    """Tests for the snapshot_test function."""

    def test_snapshot_test_with_dict(self):
        """Test snapshot_test with a dictionary."""
        # Create a test object
        data = {
            "name": "test",
            "values": [1, 2, 3, 4, 5],
            "metadata": {"version": "1.0.0", "created": "2023-01-01"},
        }

        # Test against a snapshot
        # This will create a snapshot on the first run
        # and compare against it on subsequent runs
        assert snapshot_test(data, name="dict_example")

    def test_snapshot_test_with_object(self):
        """Test snapshot_test with a custom object."""
        # Create a test object with fixed date for reproducibility
        test_date = datetime(2023, 1, 1, 12, 0, 0)
        obj = TestObject("test_object", 42, test_date)

        # Test against a snapshot
        assert snapshot_test(obj, name="object_example")

    def test_snapshot_test_update(self):
        """Test snapshot_test with update=True."""
        # Create a test object
        data = {"name": "test", "updated_at": datetime.now().isoformat()}

        # Update the snapshot
        assert snapshot_test(data, name="update_example", update=True)

        # Should match since we just updated it
        assert snapshot_test(data, name="update_example")


class TestCompareSnapshot:
    """Tests for the compare_snapshot function."""

    def test_compare_snapshot_match(self):
        """Test compare_snapshot with matching data."""
        # Create a test object with reproducible data
        data = {
            "name": "compare_test",
            "values": [1, 2, 3],
            "created_at": "2023-01-01T12:00:00",
        }

        # First call creates the snapshot
        result = compare_snapshot(data, name="compare_example")

        # Second call should match
        result = compare_snapshot(data, name="compare_example")
        assert result["matches"] is True
        assert result["diff"] == []

    def test_compare_snapshot_mismatch(self):
        """Test compare_snapshot with mismatched data."""
        # Create initial data and snapshot
        initial_data = {
            "name": "compare_test",
            "values": [1, 2, 3],
            "created_at": "2023-01-01T12:00:00",
        }

        # Create the snapshot
        compare_snapshot(initial_data, name="mismatch_example")

        # Modified data
        modified_data = {
            "name": "compare_test",
            "values": [1, 2, 3, 4],  # Added a value
            "created_at": "2023-01-01T12:00:00",
        }

        # Compare against the snapshot
        result = compare_snapshot(modified_data, name="mismatch_example")

        # Should not match
        assert result["matches"] is False
        assert len(result["diff"]) > 0
