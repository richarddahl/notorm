"""
Schema validation utilities.

This module provides utilities for validating data against Pydantic schemas,
integrating Pydantic validation with the Uno validation framework.
"""

from collections.abc import Callable
from typing import TypeVar, cast

from pydantic import BaseModel, ValidationError as PydanticValidationError

from uno.core.errors.result import ErrorSeverity, ValidationError, ValidationResult
from uno.core.validation.validator import ValidationContext, Validator

T = TypeVar('T', bound=BaseModel)
D = TypeVar('D')  # Data type


class SchemaValidator(Validator[dict[str, object] | BaseModel]):
    """
    Validator for Pydantic schemas.
    
    This validator validates data against Pydantic schemas and converts
    Pydantic validation errors to Uno ValidationErrors.
    """
    
    def __init__(self, schema_type: type[BaseModel], strict: bool = False):
        """
        Initialize a schema validator.
        
        Args:
            schema_type: The Pydantic schema type to validate against
            strict: Whether to use strict validation
        """
        self.schema_type = schema_type
        self.strict = strict
    
    def _validate(
        self,
        obj: dict[str, object] | BaseModel,
        context: ValidationContext
    ) -> None:
        """
        Validate an object against a Pydantic schema.
        
        Args:
            obj: The object to validate
            context: The validation context to update
        """
        try:
            if isinstance(obj, dict):
                self.schema_type.model_validate(obj, strict=self.strict)
            elif isinstance(obj, BaseModel):
                # Skip validation if the object is already the right type
                if not isinstance(obj, self.schema_type):
                    # Convert to dict and validate
                    data = obj.model_dump()
                    self.schema_type.model_validate(data, strict=self.strict)
        except PydanticValidationError as e:
            self._convert_errors(e, context)
    
    def _convert_errors(
        self,
        error: PydanticValidationError,
        context: ValidationContext
    ) -> None:
        """
        Convert Pydantic validation errors to Uno ValidationErrors.
        
        Args:
            error: The Pydantic validation error
            context: The validation context to update
        """
        for err in error.errors():
            # Extract field path, message, and type
            loc: tuple[str, ...] = err.get("loc", [])
            field_path = ".".join(str(loc_item) for loc_item in loc)
            msg = err.get("msg", "Validation error")
            error_type = err.get("type", "")
            
            # Add error to context
            context.add_error(
                message=msg,
                path=field_path,
                code=error_type,
                severity=ErrorSeverity.ERROR,
                context={"schema": self.schema_type.__name__}
            )


def schema_validator(schema_type: type[T], strict: bool = False) -> SchemaValidator:
    """
    Create a schema validator for a Pydantic schema.
    
    Args:
        schema_type: The Pydantic schema type to validate against
        strict: Whether to use strict validation
        
    Returns:
        A SchemaValidator for the given schema type
    """
    return SchemaValidator(schema_type, strict=strict)


def validate_schema(schema_type: type[T], strict: bool = False) -> Callable[[dict[str, object]], ValidationResult[T]]:
    """
    Create a function that validates data against a Pydantic schema.
    
    Args:
        schema_type: The Pydantic schema type to validate against
        strict: Whether to use strict validation
        
    Returns:
        A function that validates data against the schema and returns a ValidationResult
    """
    validator = schema_validator(schema_type, strict=strict)
    
    def validate(data: dict[str, object]) -> ValidationResult[T]:
        """
        Validate data against a Pydantic schema.
        
        Args:
            data: The data to validate
            
        Returns:
            A ValidationResult containing the validated model or errors
        """
        # Validate the data
        result = validator.validate(data)
        if result.is_failure:
            return cast(ValidationResult[T], result)
        
        # Create the model
        try:
            model = schema_type.model_validate(data, strict=strict)
            return ValidationResult.success(model)
        except PydanticValidationError as e:
            # This should not happen because we already validated above,
            # but just in case
            errors = []
            for err in e.errors():
                loc = err.get("loc", [])
                field_path = ".".join(str(l) for l in loc)
                msg = err.get("msg", "Validation error")
                error_type = err.get("type", "")
                
                errors.append(ValidationError(
                    message=msg,
                    path=field_path,
                    code=error_type,
                    severity=ErrorSeverity.ERROR,
                    context={"schema": schema_type.__name__}
                ))
            
            return ValidationResult.failures(errors)
    
    return validate