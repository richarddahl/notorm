# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Validation utilities for error handling in the Uno framework.

This module provides tools for structured validation with error
collection and contextual information.
"""

from typing import Any, Dict, List, Optional, Set, Callable
from uno.core.errors.base import UnoError, ErrorCode, ValidationError


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
    
    def add_error(self, field: str, message: str, value: Any = None) -> None:
        """
        Add an error to the context.
        
        Args:
            field: The field with the error
            message: The error message
            value: The problematic value (optional)
        """
        # Build the full path to the field
        full_path = ".".join(self.current_path + [field]) if field else ".".join(self.current_path)
        
        self.errors.append({
            "field": full_path,
            "message": message,
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
            raise ValidationError(
                f"Validation failed for {self.entity_name}",
                validation_errors=self.errors
            )


def validate_fields(
    data: Dict[str, Any],
    required_fields: Set[str] = None,
    validators: Dict[str, List[Callable[[Any], Optional[str]]]] = None,
    entity_name: str = "entity"
) -> None:
    """
    Validate fields in a dictionary.
    
    Args:
        data: The data to validate
        required_fields: Set of required field names
        validators: Dictionary mapping field names to lists of validator functions
        entity_name: Name of the entity being validated
        
    Raises:
        ValidationError: If validation fails
    """
    required_fields = required_fields or set()
    validators = validators or {}
    
    context = ValidationContext(entity_name)
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field]):
            context.add_error(
                field=field,
                message=f"Field '{field}' is required",
                value=data.get(field)
            )
    
    # Run validators
    for field, field_validators in validators.items():
        if field in data and data[field] is not None:
            value = data[field]
            for validator in field_validators:
                error_message = validator(value)
                if error_message:
                    context.add_error(
                        field=field,
                        message=error_message,
                        value=value
                    )
    
    # Raise exception if there are any errors
    context.raise_if_errors()