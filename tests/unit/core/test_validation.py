"""
Tests for the validation framework.

This module contains tests for the Uno validation framework, including
the Result pattern, validators, and validation rules.
"""

import pytest
from pydantic import BaseModel, Field
from dataclasses import dataclass

from uno.core.errors.result import ValidationResult, ValidationError, ErrorSeverity
from uno.core.validation import (
    Validator, ValidationContext, SchemaValidator, DomainValidator,
    RuleValidator, Rule, schema_validator, validate_schema, domain_validator,
    required, min_length, max_length, pattern, email, range_rule
)


# Test Result class enhancements
def test_result_success():
    """Test the success case for Result."""
    result = ValidationResult.success("test")
    assert result.is_success
    assert not result.is_failure
    assert result.value == "test"
    assert result.error is None
    assert len(result.errors) == 0


def test_result_failure():
    """Test the failure case for Result."""
    error = ValidationError("Invalid value")
    result = ValidationResult.failure(error)
    assert not result.is_success
    assert result.is_failure
    assert result.value is None
    assert result.error == error
    assert len(result.errors) == 1


def test_result_map():
    """Test the map method on Result."""
    result = ValidationResult.success(5)
    mapped = result.map(lambda x: x * 2)
    assert mapped.is_success
    assert mapped.value == 10


def test_result_bind():
    """Test the bind method on Result."""
    result = ValidationResult.success(5)
    
    def double(x):
        return ValidationResult.success(x * 2)
    
    bound = result.bind(double)
    assert bound.is_success
    assert bound.value == 10


def test_result_combine():
    """Test the combine method on Result."""
    result1 = ValidationResult.success(5)
    result2 = ValidationResult.success(10)
    result3 = ValidationResult.failure(ValidationError("Error"))
    
    combined1 = result1.combine(result2)
    assert combined1.is_success
    assert combined1.value == 5
    
    combined2 = result1.combine(result3)
    assert combined2.is_failure
    assert len(combined2.errors) == 1


def test_result_all():
    """Test the all static method on Result."""
    result1 = ValidationResult.success(5)
    result2 = ValidationResult.success(10)
    result3 = ValidationResult.failure(ValidationError("Error"))
    
    all_success = ValidationResult.all([result1, result2])
    assert all_success.is_success
    assert all_success.value == [5, 10]
    
    some_failure = ValidationResult.all([result1, result2, result3])
    assert some_failure.is_failure
    assert len(some_failure.errors) == 1


# Test basic validators
class SimpleValidator(Validator[str]):
    """A simple validator for testing."""
    
    def _validate(self, obj: str, context: ValidationContext) -> None:
        if not obj:
            context.add_error("Value cannot be empty")
        elif len(obj) < 3:
            context.add_error("Value must be at least 3 characters long")


def test_simple_validator():
    """Test a simple validator."""
    validator = SimpleValidator()
    
    result1 = validator.validate("")
    assert result1.is_failure
    assert "empty" in result1.error.message
    
    result2 = validator.validate("ab")
    assert result2.is_failure
    assert "3 characters" in result2.error.message
    
    result3 = validator.validate("abc")
    assert result3.is_success
    assert result3.value == "abc"


# Test schema validator
class UserSchema(BaseModel):
    """A schema for user data."""
    
    name: str = Field(..., min_length=3)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    age: int = Field(..., ge=18)


def test_schema_validator():
    """Test schema validation with Pydantic."""
    validator = schema_validator(UserSchema)
    
    # Invalid data
    result1 = validator.validate({
        "name": "Jo",
        "email": "not-an-email",
        "age": 17
    })
    assert result1.is_failure
    assert len(result1.errors) == 3
    
    # Valid data
    result2 = validator.validate({
        "name": "John",
        "email": "john@example.com",
        "age": 25
    })
    assert result2.is_success


def test_validate_schema_function():
    """Test the validate_schema function."""
    validate = validate_schema(UserSchema)
    
    # Invalid data
    result1 = validate({
        "name": "Jo",
        "email": "not-an-email",
        "age": 17
    })
    assert result1.is_failure
    assert len(result1.errors) == 3
    
    # Valid data
    result2 = validate({
        "name": "John",
        "email": "john@example.com",
        "age": 25
    })
    assert result2.is_success
    assert isinstance(result2.value, UserSchema)
    assert result2.value.name == "John"


# Test domain validator
@dataclass
class User:
    """A simple user class for testing domain validation."""
    
    name: str
    email: str
    age: int


def test_domain_validator():
    """Test domain validation for a class."""
    validator = domain_validator(
        User,
        field_validators={
            "name": [required, min_length(3)],
            "email": [required, email],
            "age": [required, range_rule(18, 120)]
        }
    )
    
    # Invalid user
    result1 = validator.validate(User("Jo", "not-an-email", 17))
    assert result1.is_failure
    assert len(result1.errors) == 3
    
    # Valid user
    result2 = validator.validate(User("John", "john@example.com", 25))
    assert result2.is_success
    assert result2.value.name == "John"


# Test rule validator
class AgeRule(Rule[User]):
    """A rule that checks if a user is an adult."""
    
    def evaluate(self, obj: User, context: ValidationContext) -> bool:
        if obj.age < 18:
            context.add_error("User must be at least 18 years old", path="age")
            return False
        return True


class EmailRule(Rule[User]):
    """A rule that checks if a user has a valid email."""
    
    def evaluate(self, obj: User, context: ValidationContext) -> bool:
        if not obj.email or "@" not in obj.email:
            context.add_error("User must have a valid email", path="email")
            return False
        return True


def test_rule_validator():
    """Test rule validation."""
    validator = RuleValidator[User]()
    validator.add_rule(AgeRule())
    validator.add_rule(EmailRule())
    
    # Invalid user
    result1 = validator.validate(User("John", "not-an-email", 17))
    assert result1.is_failure
    assert len(result1.errors) == 2
    
    # Valid user
    result2 = validator.validate(User("John", "john@example.com", 25))
    assert result2.is_success
    assert result2.value.name == "John"


def test_composite_rules():
    """Test composite rules."""
    # Create composite rule
    rule = AgeRule() & EmailRule()
    
    # Create validator with composite rule
    validator = RuleValidator[User]()
    validator.add_rule(rule)
    
    # Invalid user
    result1 = validator.validate(User("John", "not-an-email", 17))
    assert result1.is_failure
    assert len(result1.errors) == 2
    
    # Valid user
    result2 = validator.validate(User("John", "john@example.com", 25))
    assert result2.is_success
    assert result2.value.name == "John"