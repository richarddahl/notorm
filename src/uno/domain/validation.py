"""
Validation utilities for the Uno framework.

This module provides validation utilities for validating commands, entities,
and other domain objects.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union, cast

from uno.core.base.error import ValidationError


class ValidationSeverity(Enum):
    """Severity level for validation results."""

    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    This class represents the result of validating an object, including
    any validation errors, warnings, or information messages.
    """

    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def add_message(
        self, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR
    ) -> None:
        """
        Add a message to the validation result.

        Args:
            message: The validation message
            severity: The severity level of the message
        """
        if severity == ValidationSeverity.ERROR:
            self.errors.append(message)
            self.valid = False
        elif severity == ValidationSeverity.WARNING:
            self.warnings.append(message)
        elif severity == ValidationSeverity.INFO:
            self.info.append(message)

    @property
    def has_errors(self) -> bool:
        """Check if the validation result has errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if the validation result has warnings."""
        return len(self.warnings) > 0

    @property
    def has_info(self) -> bool:
        """Check if the validation result has info messages."""
        return len(self.info) > 0

    def raise_if_invalid(self) -> None:
        """
        Raise a ValidationError if the validation result is invalid.

        Raises:
            ValidationError: If the validation result has errors
        """
        if self.has_errors:
            raise ValidationError("\n".join(self.errors))


class Validator:
    """Base validator for validating domain objects."""

    def validate(self, obj: Any) -> ValidationResult:
        """
        Validate an object.

        Args:
            obj: The object to validate

        Returns:
            The validation result
        """
        result = ValidationResult()
        self._validate(obj, result)
        return result

    def _validate(self, obj: Any, result: ValidationResult) -> None:
        """
        Perform validation on an object.

        This method should be overridden by derived classes to provide
        specific validation logic.

        Args:
            obj: The object to validate
            result: The validation result to update
        """
        pass


class FieldValidator(Validator):
    """Validator for validating object fields."""

    def required(self, obj: Any, field: str, result: ValidationResult) -> None:
        """
        Validate that a field is present and not None.

        Args:
            obj: The object to validate
            field: The field to check
            result: The validation result to update
        """
        if not hasattr(obj, field) or getattr(obj, field) is None:
            result.add_message(f"Required field '{field}' is missing")

    def min_length(
        self, obj: Any, field: str, min_length: int, result: ValidationResult
    ) -> None:
        """
        Validate that a string field has at least the minimum length.

        Args:
            obj: The object to validate
            field: The field to check
            min_length: The minimum allowed length
            result: The validation result to update
        """
        if hasattr(obj, field) and getattr(obj, field) is not None:
            value = getattr(obj, field)
            if isinstance(value, str) and len(value) < min_length:
                result.add_message(
                    f"Field '{field}' must be at least {min_length} characters long"
                )

    def max_length(
        self, obj: Any, field: str, max_length: int, result: ValidationResult
    ) -> None:
        """
        Validate that a string field doesn't exceed the maximum length.

        Args:
            obj: The object to validate
            field: The field to check
            max_length: The maximum allowed length
            result: The validation result to update
        """
        if hasattr(obj, field) and getattr(obj, field) is not None:
            value = getattr(obj, field)
            if isinstance(value, str) and len(value) > max_length:
                result.add_message(
                    f"Field '{field}' must be at most {max_length} characters long"
                )

    def range(
        self,
        obj: Any,
        field: str,
        min_value: Union[int, float],
        max_value: Union[int, float],
        result: ValidationResult,
    ) -> None:
        """
        Validate that a numeric field is within the specified range.

        Args:
            obj: The object to validate
            field: The field to check
            min_value: The minimum allowed value
            max_value: The maximum allowed value
            result: The validation result to update
        """
        if hasattr(obj, field) and getattr(obj, field) is not None:
            value = getattr(obj, field)
            if isinstance(value, (int, float)) and (
                value < min_value or value > max_value
            ):
                result.add_message(
                    f"Field '{field}' must be between {min_value} and {max_value}"
                )

    def pattern(
        self, obj: Any, field: str, pattern: str, result: ValidationResult
    ) -> None:
        """
        Validate that a string field matches a regular expression pattern.

        Args:
            obj: The object to validate
            field: The field to check
            pattern: The regular expression pattern
            result: The validation result to update
        """
        import re

        if hasattr(obj, field) and getattr(obj, field) is not None:
            value = getattr(obj, field)
            if isinstance(value, str) and not re.match(pattern, value):
                result.add_message(
                    f"Field '{field}' does not match the required pattern"
                )

    def email(self, obj: Any, field: str, result: ValidationResult) -> None:
        """
        Validate that a field contains a valid email address.

        Args:
            obj: The object to validate
            field: The field to check
            result: The validation result to update
        """
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if hasattr(obj, field) and getattr(obj, field) is not None:
            value = getattr(obj, field)
            if isinstance(value, str) and not re.match(email_pattern, value):
                result.add_message(f"Field '{field}' must be a valid email address")


class DataValidator:
    """Utilities for validating data dictionaries."""

    @staticmethod
    def required(data: Dict[str, Any], *fields: str) -> ValidationResult:
        """
        Check that all required fields are present.

        Args:
            data: The data to validate
            *fields: The required fields

        Returns:
            The validation result
        """
        result = ValidationResult()

        for field in fields:
            if field not in data or data[field] is None:
                result.add_message(f"Required field '{field}' is missing")

        return result

    @staticmethod
    def min_length(
        data: Dict[str, Any], field: str, min_length: int
    ) -> ValidationResult:
        """
        Check that a string field has at least the minimum length.

        Args:
            data: The data to validate
            field: The field to check
            min_length: The minimum allowed length

        Returns:
            The validation result
        """
        result = ValidationResult()

        if field in data and data[field] is not None:
            value = data[field]
            if isinstance(value, str) and len(value) < min_length:
                result.add_message(
                    f"Field '{field}' must be at least {min_length} characters long"
                )

        return result

    @staticmethod
    def max_length(
        data: Dict[str, Any], field: str, max_length: int
    ) -> ValidationResult:
        """
        Check that a string field doesn't exceed the maximum length.

        Args:
            data: The data to validate
            field: The field to check
            max_length: The maximum allowed length

        Returns:
            The validation result
        """
        result = ValidationResult()

        if field in data and data[field] is not None:
            value = data[field]
            if isinstance(value, str) and len(value) > max_length:
                result.add_message(
                    f"Field '{field}' must be at most {max_length} characters long"
                )

        return result

    @staticmethod
    def range(
        data: Dict[str, Any],
        field: str,
        min_value: Union[int, float],
        max_value: Union[int, float],
    ) -> ValidationResult:
        """
        Check that a numeric field is within the specified range.

        Args:
            data: The data to validate
            field: The field to check
            min_value: The minimum allowed value
            max_value: The maximum allowed value

        Returns:
            The validation result
        """
        result = ValidationResult()

        if field in data and data[field] is not None:
            value = data[field]
            if isinstance(value, (int, float)) and (
                value < min_value or value > max_value
            ):
                result.add_message(
                    f"Field '{field}' must be between {min_value} and {max_value}"
                )

        return result

    @staticmethod
    def pattern(data: Dict[str, Any], field: str, pattern: str) -> ValidationResult:
        """
        Check that a string field matches a regular expression pattern.

        Args:
            data: The data to validate
            field: The field to check
            pattern: The regular expression pattern

        Returns:
            The validation result
        """
        import re

        result = ValidationResult()

        if field in data and data[field] is not None:
            value = data[field]
            if isinstance(value, str) and not re.match(pattern, value):
                result.add_message(
                    f"Field '{field}' does not match the required pattern"
                )

        return result

    @staticmethod
    def email(data: Dict[str, Any], field: str) -> ValidationResult:
        """
        Check that a field contains a valid email address.

        Args:
            data: The data to validate
            field: The field to check

        Returns:
            The validation result
        """
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return DataValidator.pattern(data, field, email_pattern)

    @staticmethod
    def validate_all(*results: ValidationResult) -> ValidationResult:
        """
        Combine multiple validation results into one.

        Args:
            *results: The validation results to combine

        Returns:
            The combined validation result
        """
        combined = ValidationResult()

        for result in results:
            for error in result.errors:
                combined.add_message(error, ValidationSeverity.ERROR)

            for warning in result.warnings:
                combined.add_message(warning, ValidationSeverity.WARNING)

            for info in result.info:
                combined.add_message(info, ValidationSeverity.INFO)

        return combined
