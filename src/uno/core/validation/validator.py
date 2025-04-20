"""
Base validator classes for the validation framework.

This module provides the foundational classes for validation, including
the ValidationContext for tracking validation state and the Validator
interface for implementing validators.
"""

from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Set, TypeVar
from dataclasses import dataclass, field

from uno.core.errors.result import ValidationResult, ValidationError, ErrorSeverity

T = TypeVar("T")  # Type of object being validated


class ValidationProtocol(Protocol[T]):
    """Protocol defining the interface for validators."""

    def validate(self, obj: T) -> ValidationResult[T]:
        """
        Validate an object.

        Args:
            obj: The object to validate

        Returns:
            A ValidationResult containing the validated object or errors
        """
        ...


class ValidationContext:
    """
    Context for tracking validation state.

    This class provides a context for tracking validation state during
    complex validation processes, allowing validators to build nested
    error paths and accumulate errors.
    """

    def __init__(self, object_name: str = ""):
        """
        Initialize a validation context.

        Args:
            object_name: The name of the object being validated
        """
        self.object_name = object_name
        self.errors: list[ValidationError] = []
        self.current_path: list[str] = []

    def add_error(
        self,
        message: str,
        path: str | None = None,
        code: str | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an error to the context.

        Args:
            message: The error message
            path: The path to the field with the error (overrides current path)
            code: An optional error code
            severity: The severity of the error
            context: Additional context information
        """
        # Build the full path to the field
        full_path = path
        if not full_path:
            if self.current_path:
                full_path = ".".join(self.current_path)

        self.errors.append(
            ValidationError(
                message=message,
                path=full_path,
                code=code,
                severity=severity,
                context=context or {},
            )
        )

    def nested(self, field: str) -> "ValidationContext":
        """
        Create a nested validation context.

        This allows for hierarchical validation with proper field path tracking.

        Args:
            field: The field name for the nested context

        Returns:
            A new validation context with the current path extended by the field name
        """
        context = ValidationContext(self.object_name)
        context.current_path = self.current_path + [field]
        context.errors = self.errors  # Share the same errors list
        return context

    def has_errors(self, include_warnings: bool = False) -> bool:
        """
        Check if the context has any errors.

        Args:
            include_warnings: Whether to count warnings as errors

        Returns:
            True if there are errors (or warnings if include_warnings=True),
            False otherwise
        """
        if not include_warnings:
            return any(
                e.severity == ErrorSeverity.ERROR
                or e.severity == ErrorSeverity.CRITICAL
                for e in self.errors
            )
        return len(self.errors) > 0

    def to_result(self, value: Optional[T] = None) -> ValidationResult[T]:
        """
        Convert the context to a ValidationResult.

        Args:
            value: The value to include in a successful result

        Returns:
            A ValidationResult containing the value if there are no errors,
            or the errors if there are errors
        """
        if self.has_errors():
            return ValidationResult(errors=self.errors)
        return ValidationResult(value=value)


class Validator(Generic[T]):
    """
    Base class for validators.

    This class provides a foundation for implementing validators that
    can validate objects and return ValidationResults.
    """

    def validate(self, obj: T) -> ValidationResult[T]:
        """
        Validate an object.

        Args:
            obj: The object to validate

        Returns:
            A ValidationResult containing the validated object or errors
        """
        context = ValidationContext(object_name=self._get_object_name(obj))
        self._validate(obj, context)
        return context.to_result(value=obj)

    def _validate(self, obj: T, context: ValidationContext) -> None:
        """
        Perform validation on an object.

        This method should be overridden by derived classes to provide
        specific validation logic.

        Args:
            obj: The object to validate
            context: The validation context to update
        """
        pass

    def _get_object_name(self, obj: Any) -> str:
        """
        Get the name of an object for error reporting.

        Args:
            obj: The object to get the name of

        Returns:
            A string representation of the object type
        """
        if hasattr(obj, "__class__"):
            return obj.__class__.__name__
        return str(type(obj).__name__)


# Field validation rules

FieldRule = Callable[[Any], Optional[str]]
ObjectRule = Callable[[Any], Optional[str]]


def required(value: Any) -> Optional[str]:
    """
    Validate that a value is not None or empty.

    Args:
        value: The value to validate

    Returns:
        An error message if the validation fails, None otherwise
    """
    if value is None:
        return "Value is required"

    if isinstance(value, str) and not value.strip():
        return "Value cannot be empty"

    return None


def min_length(min_length: int) -> FieldRule:
    """
    Create a validator that checks if a string has at least the minimum length.

    Args:
        min_length: The minimum allowed length

    Returns:
        A validator function
    """

    def validator(value: Any) -> Optional[str]:
        if value is None:
            return None

        if isinstance(value, str) and len(value) < min_length:
            return f"Value must be at least {min_length} characters long"

        return None

    return validator


def max_length(max_length: int) -> FieldRule:
    """
    Create a validator that checks if a string doesn't exceed the maximum length.

    Args:
        max_length: The maximum allowed length

    Returns:
        A validator function
    """

    def validator(value: Any) -> Optional[str]:
        if value is None:
            return None

        if isinstance(value, str) and len(value) > max_length:
            return f"Value must be at most {max_length} characters long"

        return None

    return validator


def pattern(pattern_str: str, message: str | None = None) -> FieldRule:
    """
    Create a validator that checks if a string matches a regular expression.

    Args:
        pattern_str: The regular expression pattern
        message: A custom error message

    Returns:
        A validator function
    """
    import re

    compiled_pattern = re.compile(pattern_str)

    def validator(value: Any) -> Optional[str]:
        if value is None:
            return None

        if isinstance(value, str) and not compiled_pattern.match(value):
            return message or "Value does not match the required pattern"

        return None

    return validator


def email(value: Any) -> Optional[str]:
    """
    Validate that a value is a valid email address.

    Args:
        value: The value to validate

    Returns:
        An error message if the validation fails, None otherwise
    """
    if value is None:
        return None

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return pattern(email_pattern, "Value must be a valid email address")(value)


def range_rule(min_value: float, max_value: float) -> FieldRule:
    """
    Create a validator that checks if a numeric value is within a range.

    Args:
        min_value: The minimum allowed value
        max_value: The maximum allowed value

    Returns:
        A validator function
    """

    def validator(value: Any) -> Optional[str]:
        if value is None:
            return None

        if isinstance(value, (int, float)) and (value < min_value or value > max_value):
            return f"Value must be between {min_value} and {max_value}"

        return None

    return validator
