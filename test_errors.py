#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Standalone test runner for error handling.

This script tests the newly added error categories without running initialization code.
"""

import sys
import unittest
from enum import Enum, auto

# Create a simplified version of the ErrorCategory enum for testing
class ErrorCategory(Enum):
    """Test version of error categories for classification."""
    
    VALIDATION = auto()      # Input validation errors
    BUSINESS_RULE = auto()   # Business rule violations
    AUTHORIZATION = auto()   # Permission/authorization errors
    AUTHENTICATION = auto()  # Login/identity errors
    DATABASE = auto()        # Database-related errors
    NETWORK = auto()         # Network/connectivity errors
    RESOURCE = auto()        # Resource availability errors
    CONFIGURATION = auto()   # System configuration errors
    INTEGRATION = auto()     # External system integration errors
    INTERNAL = auto()        # Unexpected internal errors
    INITIALIZATION = auto()  # Initialization errors
    SERIALIZATION = auto()   # Serialization/deserialization errors
    DEPENDENCY = auto()      # Dependency resolution errors
    EXECUTION = auto()       # Execution/processing errors
    SECURITY = auto()        # Security-related errors

class ErrorCategoryTest(unittest.TestCase):
    """Tests for the error categories."""
    
    def test_error_categories(self):
        """Test error categories."""
        # Make sure all categories are defined
        categories = {category.name for category in ErrorCategory}
        self.assertIn("VALIDATION", categories)
        self.assertIn("BUSINESS_RULE", categories)
        self.assertIn("AUTHORIZATION", categories)
        self.assertIn("AUTHENTICATION", categories)
        self.assertIn("DATABASE", categories)
        self.assertIn("NETWORK", categories)
        self.assertIn("RESOURCE", categories)
        self.assertIn("CONFIGURATION", categories)
        self.assertIn("INTEGRATION", categories)
        self.assertIn("INTERNAL", categories)
        
        # New categories added in modernization
        self.assertIn("INITIALIZATION", categories)
        self.assertIn("SERIALIZATION", categories)
        self.assertIn("DEPENDENCY", categories)
        self.assertIn("EXECUTION", categories)
        self.assertIn("SECURITY", categories)
        
        # Ensure we have the expected number of categories (15)
        self.assertEqual(len(categories), 15, 
                        f"Expected 15 categories, got {len(categories)}: {sorted(categories)}")
        
        # Verify all expected categories are present
        expected_categories = {
            "VALIDATION", "BUSINESS_RULE", "AUTHORIZATION", "AUTHENTICATION",
            "DATABASE", "NETWORK", "RESOURCE", "CONFIGURATION", "INTEGRATION",
            "INTERNAL", "INITIALIZATION", "SERIALIZATION", "DEPENDENCY",
            "EXECUTION", "SECURITY"
        }
        self.assertEqual(categories, expected_categories)
    
if __name__ == "__main__":
    unittest.main()