# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the errors.py module.

These tests verify the functionality of custom error classes defined in the Uno framework.
"""

import pytest
from fastapi import status, HTTPException

from uno.errors import (
    UnoError,
    UnoRegistryError,
    DataExistsError,
    UnauthorizedError,
    ForbiddenError,
)


class TestUnoError:
    """Tests for the UnoError base class."""

    def test_init(self):
        """Test initialization of UnoError."""
        error = UnoError("Test error message", "TEST_ERROR")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"

    def test_as_exception(self):
        """Test UnoError can be raised and caught as an exception."""
        with pytest.raises(UnoError) as excinfo:
            raise UnoError("Test exception", "TEST_EXCEPTION")
        
        assert str(excinfo.value) == "Test exception"
        assert excinfo.value.message == "Test exception"
        assert excinfo.value.error_code == "TEST_EXCEPTION"


class TestUnoRegistryError:
    """Tests for the UnoRegistryError class."""

    def test_init(self):
        """Test initialization of UnoRegistryError."""
        error = UnoRegistryError("Registry error", "REGISTRY_ERROR")
        
        assert isinstance(error, UnoError)
        assert str(error) == "Registry error"
        assert error.message == "Registry error"
        assert error.error_code == "REGISTRY_ERROR"

    def test_as_exception(self):
        """Test UnoRegistryError can be raised and caught appropriately."""
        # Can be caught as UnoRegistryError
        with pytest.raises(UnoRegistryError) as excinfo:
            raise UnoRegistryError("Registry exception", "REG_EXCEPTION")
        
        assert excinfo.value.message == "Registry exception"
        assert excinfo.value.error_code == "REG_EXCEPTION"
        
        # Can also be caught as UnoError
        with pytest.raises(UnoError):
            raise UnoRegistryError("Registry exception", "REG_EXCEPTION")


class TestHTTPExceptions:
    """Tests for HTTP exception classes."""

    def test_data_exists_error(self):
        """Test DataExistsError initialization."""
        # Create the error by specifying the detail directly
        expected_detail = "Record matching data already exists in database."
        error = DataExistsError(status_code=400, detail=expected_detail)
        
        assert error.status_code == 400
        assert error.detail == expected_detail
        assert isinstance(error, HTTPException)

    def test_unauthorized_error(self):
        """Test UnauthorizedError initialization."""
        # Create the error by specifying the detail directly
        expected_detail = "Invalid user credentials"
        expected_headers = {"WWW-enticate": "Bearer"}
        error = UnauthorizedError(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=expected_detail,
            headers=expected_headers
        )
        
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.detail == expected_detail
        assert error.headers == expected_headers
        assert isinstance(error, HTTPException)

    def test_forbidden_error(self):
        """Test ForbiddenError initialization."""
        # Create the error by specifying the detail directly
        expected_detail = "You do not have permission to access this resource."
        error = ForbiddenError(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=expected_detail
        )
        
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.detail == expected_detail
        assert isinstance(error, HTTPException)