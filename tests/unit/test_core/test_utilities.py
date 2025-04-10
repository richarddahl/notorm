# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the utilities.py module.

These tests verify the functionality of various utility functions in the Uno framework.
"""

import pytest
import decimal
import os
import sys
import tempfile
from datetime import datetime, date, timedelta
from unittest import mock

from uno.utilities import (
    import_from_path,
    snake_to_title,
    snake_to_camel,
    snake_to_caps_snake,
    boolean_to_string,
    date_to_string,
    decimal_to_string,
    obj_to_string,
    timedelta_to_string,
    boolean_to_okui,
    date_to_okui,
    datetime_to_okui,
    decimal_to_okui,
    obj_to_okui,
    timedelta_to_okui,
)


class TestStringConversions:
    """Tests for string conversion utility functions."""

    def test_snake_to_title(self):
        """Test converting snake_case to Title Case."""
        assert snake_to_title("hello_world") == "Hello World"
        assert snake_to_title("user_profile") == "User Profile"
        assert snake_to_title("this_is_a_test") == "This Is A Test"
        assert snake_to_title("single") == "Single"
        assert snake_to_title("") == ""

    def test_snake_to_camel(self):
        """Test converting snake_case to CamelCase."""
        assert snake_to_camel("hello_world") == "HelloWorld"
        assert snake_to_camel("user_profile") == "UserProfile"
        assert snake_to_camel("this_is_a_test") == "ThisIsATest"
        assert snake_to_camel("single") == "Single"
        assert snake_to_camel("") == ""

    def test_snake_to_caps_snake(self):
        """Test converting snake_case to CAPS_SNAKE."""
        assert snake_to_caps_snake("hello_world") == "HELLO_WORLD"
        assert snake_to_caps_snake("user_profile") == "USER_PROFILE"
        assert snake_to_caps_snake("this_is_a_test") == "THIS_IS_A_TEST"
        assert snake_to_caps_snake("single") == "SINGLE"
        assert snake_to_caps_snake("") == ""


class TestBooleanConversions:
    """Tests for boolean conversion utility functions."""

    def test_boolean_to_string(self):
        """Test converting boolean values to strings."""
        assert boolean_to_string(True) == "Yes"
        assert boolean_to_string(False) == "No"

    def test_boolean_to_okui(self):
        """Test converting boolean values to OKUI format."""
        result = boolean_to_okui(True)
        assert result["value"] is True
        assert result["type"] == "boolean"
        assert result["element"] == "checkbox"
        
        result = boolean_to_okui(False)
        assert result["value"] is False
        
        assert boolean_to_okui(None) is None


class TestDateTimeConversions:
    """Tests for date and time conversion utility functions."""

    def test_date_to_string(self):
        """Test converting date objects to strings."""
        test_date = date(2023, 4, 15)
        assert date_to_string(test_date) == "Apr 15, 2023"
        assert date_to_string(None) is None

    def test_date_to_okui(self):
        """Test converting date objects to OKUI format."""
        test_date = date(2023, 4, 15)
        assert date_to_okui(test_date) == "Apr 15, 2023"
        assert date_to_okui(None) is None

    def test_datetime_to_okui(self):
        """Test converting datetime objects to OKUI format."""
        # Mock the config since it's imported in the function
        with mock.patch('uno.utilities.uno_settings') as mock_settings:
            mock_settings.LOCALE = "en_US"
            test_datetime = datetime(2023, 4, 15, 14, 30, 0)
            result = datetime_to_okui(test_datetime)
            assert result is not None
            assert datetime_to_okui(None) is None


class TestDecimalConversions:
    """Tests for decimal conversion utility functions."""

    def test_decimal_to_string(self):
        """Test converting decimal values to strings."""
        test_decimal = decimal.Decimal("1234.56")
        assert decimal_to_string(test_decimal) == "1,234.56"
        assert decimal_to_string(None) is None

    def test_decimal_to_okui(self):
        """Test converting decimal values to OKUI format."""
        test_decimal = decimal.Decimal("1234.56")
        result = decimal_to_okui(test_decimal)
        assert result["value"] == test_decimal
        assert result["type"] == "decimal"
        assert result["element"] == "imput"
        
        assert decimal_to_okui(None) is None


class TestObjectConversions:
    """Tests for object conversion utility functions."""

    def test_obj_to_string(self):
        """Test converting objects to strings using __str__."""
        class TestObject:
            def __str__(self):
                return "Test Object"
        
        test_obj = TestObject()
        assert obj_to_string(test_obj) == "Test Object"
        assert obj_to_string(None) is None

    def test_obj_to_okui(self):
        """Test converting objects to OKUI format using __str__."""
        class TestObject:
            def __str__(self):
                return "Test Object"
        
        test_obj = TestObject()
        assert obj_to_okui(test_obj) == "Test Object"
        assert obj_to_okui(None) is None


class TestTimedeltaConversions:
    """Tests for timedelta conversion utility functions."""

    def test_timedelta_to_string(self):
        """Test converting timedelta objects to strings."""
        test_delta = timedelta(days=2, hours=3, minutes=30)
        assert timedelta_to_string(test_delta) is not None
        assert timedelta_to_string(None) is None


class TestModuleImport:
    """Tests for module import utility function."""

    def test_import_from_path(self):
        """Test importing a module from a file path."""
        # Create a temporary Python module file
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"test_var = 'Hello World'\n")
            f.write(b"def test_func():\n")
            f.write(b"    return 'Test Function'\n")
            module_path = f.name
        
        try:
            # Import the module using a patched version of the function
            module_name = "temp_test_module"
            
            # Mock the importlib functions
            with mock.patch("uno.utilities.importlib") as mock_importlib:
                # Configure the mocks to return a suitable module
                mock_spec = mock.MagicMock()
                mock_module = mock.MagicMock()
                mock_module.__name__ = module_name
                mock_module.test_var = "Hello World"
                mock_module.test_func.return_value = "Test Function"
                
                mock_importlib.util.spec_from_file_location.return_value = mock_spec
                mock_importlib.util.module_from_spec.return_value = mock_module
                
                module = import_from_path(module_name, module_path)
                
                # Check function calls
                mock_importlib.util.spec_from_file_location.assert_called_once_with(module_name, module_path)
                mock_importlib.util.module_from_spec.assert_called_once_with(mock_spec)
                mock_spec.loader.exec_module.assert_called_once_with(mock_module)
                
                # Check the returned module
                assert module.__name__ == module_name
                assert module.test_var == "Hello World"
                assert module.test_func() == "Test Function"
        finally:
            # Clean up temporary file
            os.unlink(module_path)