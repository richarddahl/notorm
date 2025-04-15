# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error classes for the Uno framework.

This module provides standardized error classes with error codes and context
information to help with debugging and client-side error handling.
"""

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class ValidationContext:
    """
    Validation context for tracking validation errors.
    
    This class helps track validation errors during complex validation processes,
    allowing for contextual error reporting.
    """
    
    def __init__(self, entity_name: str = ""):
        """
        Initialize a validation context.
        
        Args:
            entity_name: The name of the entity being validated
        """
        self.entity_name: str = entity_name
        self.errors: List[Dict[str, Any]] = []
        self.current_path: List[str] = []
    
    def add_error(self, field: str, message: str, error_code: str, value: Any = None) -> None:
        """
        Add an error to the context.
        
        Args:
            field: The field with the error
            message: The error message
            error_code: The error code
            value: The problematic value (optional)
        """
        # Build the full path to the field
        full_path = ".".join(self.current_path + [field]) if field else ".".join(self.current_path)
        
        self.errors.append({
            "field": full_path,
            "message": message,
            "error_code": error_code,
            "value": value
        })
    
    def nested(self, field: str) -> "ValidationContext":
        """
        Create a nested validation context.
        
        This allows for hierarchical validation with proper field path tracking.
        
        Args:
            field: The field name for the nested context
            
        Returns:
            A new validation context with the current path extended by the field name
        """
        context = ValidationContext(self.entity_name)
        context.current_path = self.current_path + [field]
        context.errors = self.errors  # Share the same errors list
        return context
    
    def has_errors(self) -> bool:
        """
        Check if the context has any errors.
        
        Returns:
            True if there are errors, False otherwise
        """
        return len(self.errors) > 0
    
    def raise_if_errors(self) -> None:
        """
        Raise a validation error if there are any errors.
        
        Raises:
            ValidationError: If there are validation errors
        """
        if self.has_errors():
            # Import ValidationError and ErrorCode from core.errors.base to ensure consistency
            from uno.core.errors.base import ValidationError, ErrorCode
            
            raise ValidationError(
                f"Validation failed for {self.entity_name}",
                ErrorCode.VALIDATION_ERROR,
                validation_errors=self.errors
            )


class UnoError(Exception):
    """
    Base class for all Uno framework errors.
    
    This class provides standardized error formatting with error codes
    and context information.
    """
    
    def __init__(self, message: str, error_code: str, **context: Any):
        """
        Initialize a UnoError.
        
        Args:
            message: The error message
            error_code: A code identifying the error type
            **context: Additional context information
        """
        super().__init__(message)
        self.message: str = message
        self.error_code: str = error_code
        self.context: Dict[str, Any] = context
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            A dictionary representation of the error
        """
        return {
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class ValidationError(UnoError):
    """
    Error raised when validation fails.
    
    This error includes detailed information about validation failures.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str, 
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        **context: Any
    ):
        """
        Initialize a ValidationError.
        
        Args:
            message: The error message
            error_code: A code identifying the error type
            validation_errors: A list of validation errors
            **context: Additional context information
        """
        super().__init__(message, error_code, **context)
        self.validation_errors: List[Dict[str, Any]] = validation_errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            A dictionary representation of the error
        """
        result = super().to_dict()
        result["validation_errors"] = self.validation_errors
        return result


class UnoRegistryError(UnoError):
    """Error raised when there are issues with the registry."""
    pass


class SchemaError(UnoError):
    """Error raised when there are issues with schemas."""
    pass


class DataExistsError(HTTPException):
    """Error raised when a record already exists."""
    status_code = 400
    detail = "Record matching data already exists in database."


class UnauthorizedError(HTTPException):
    """Error raised for authentication failures."""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid user credentials"
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(HTTPException):
    """Error raised for authorization failures."""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You do not have permission to access this resource."