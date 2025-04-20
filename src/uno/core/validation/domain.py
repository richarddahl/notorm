"""
Domain validation utilities.

This module provides utilities for validating domain objects, including
entities, aggregates, and value objects.
"""

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    Type,
    TypeVar,
)

from uno.core.errors.result import ValidationResult, ValidationError, ErrorSeverity
from uno.core.validation.validator import Validator, ValidationContext, FieldRule

T = TypeVar("T")  # Type of domain object
E = TypeVar("E")  # Type of entity
V = TypeVar("V")  # Type of value object


class DomainValidator(Validator[T]):
    """
    Base class for domain validators.

    This class provides a foundation for implementing validators that
    validate domain objects according to domain invariants and business rules.
    """

    def __init__(self, field_validators: Optional[Dict[str, list[FieldRule]]] = None):
        """
        Initialize a domain validator.

        Args:
            field_validators: A dictionary mapping field names to validator functions
        """
        self.field_validators = field_validators or {}

    def _validate(self, obj: T, context: ValidationContext) -> None:
        """
        Validate an object against domain rules.

        Args:
            obj: The object to validate
            context: The validation context to update
        """
        # Validate fields
        self._validate_fields(obj, context)

        # Validate invariants
        self._validate_invariants(obj, context)

    def _validate_fields(self, obj: T, context: ValidationContext) -> None:
        """
        Validate fields using field validators.

        Args:
            obj: The object to validate
            context: The validation context to update
        """
        for field_name, validators in self.field_validators.items():
            if hasattr(obj, field_name):
                value = getattr(obj, field_name)
                for validator in validators:
                    error_message = validator(value)
                    if error_message:
                        context.add_error(
                            message=error_message,
                            path=field_name,
                            severity=ErrorSeverity.ERROR,
                        )

    def _validate_invariants(self, obj: T, context: ValidationContext) -> None:
        """
        Validate domain invariants.

        This method should be overridden by derived classes to provide
        specific invariant validation logic.

        Args:
            obj: The object to validate
            context: The validation context to update
        """
        pass


class EntityValidator(DomainValidator[E]):
    """
    Validator for domain entities.

    This validator checks that entities have a valid identifier and
    satisfy their domain invariants.
    """

    def _validate_invariants(self, obj: E, context: ValidationContext) -> None:
        """
        Validate entity invariants.

        Args:
            obj: The entity to validate
            context: The validation context to update
        """
        # Check if entity has an ID
        if hasattr(obj, "id"):
            if getattr(obj, "id") is None:
                context.add_error(
                    message="Entity must have an ID",
                    path="id",
                    severity=ErrorSeverity.ERROR,
                )

        # Run specific entity validation logic
        self._validate_entity_invariants(obj, context)

    def _validate_entity_invariants(self, obj: E, context: ValidationContext) -> None:
        """
        Validate entity-specific invariants.

        This method should be overridden by derived classes to provide
        specific entity validation logic.

        Args:
            obj: The entity to validate
            context: The validation context to update
        """
        pass


class ValueObjectValidator(DomainValidator[V]):
    """
    Validator for value objects.

    This validator checks that value objects satisfy their domain invariants
    and have valid field values.
    """

    def _validate_invariants(self, obj: V, context: ValidationContext) -> None:
        """
        Validate value object invariants.

        Args:
            obj: The value object to validate
            context: The validation context to update
        """
        # Run specific value object validation logic
        self._validate_value_object_invariants(obj, context)

    def _validate_value_object_invariants(
        self, obj: V, context: ValidationContext
    ) -> None:
        """
        Validate value object-specific invariants.

        This method should be overridden by derived classes to provide
        specific value object validation logic.

        Args:
            obj: The value object to validate
            context: The validation context to update
        """
        pass


def domain_validator(
    cls: Type[T],
    field_validators: Optional[Dict[str, list[FieldRule]]] = None,
    invariant_validator: Optional[Callable[[T, ValidationContext], None]] = None,
) -> DomainValidator[T]:
    """
    Create a domain validator for a class.

    Args:
        cls: The class to validate
        field_validators: A dictionary mapping field names to validator functions
        invariant_validator: A function that validates domain invariants

    Returns:
        A DomainValidator for the given class
    """
    # Create base validator
    validator = DomainValidator[T](field_validators=field_validators)

    # Override invariants validation if provided
    if invariant_validator:
        original_validate_invariants = validator._validate_invariants

        def validate_invariants(obj: T, context: ValidationContext) -> None:
            original_validate_invariants(obj, context)
            invariant_validator(obj, context)

        validator._validate_invariants = validate_invariants

    return validator
