"""
Validation Framework for the Uno Framework.

This package provides a comprehensive validation framework for validating
domain objects, DTOs, and other data structures. It integrates with the
Result pattern for error handling and supports both domain validation and
schema validation.

Key components:
- Validator: Base class for creating validators
- ValidationContext: Context for hierarchical validation
- SchemaValidator: Validator for Pydantic schema validation
- DomainValidator: Validator for domain rules 
- RuleValidator: Validator for complex business rules
"""

from uno.core.validation.validator import (
    Validator, ValidationContext, FieldRule, ObjectRule, 
    required, min_length, max_length, pattern, email, range_rule,
    ValidationProtocol
)
from uno.core.validation.schema import (
    SchemaValidator, schema_validator, validate_schema
)
from uno.core.validation.domain import (
    DomainValidator, EntityValidator, ValueObjectValidator, domain_validator
)
from uno.core.validation.rules import (
    RuleValidator, Rule, CompositeRule, RuleSet
)
from uno.core.errors.result import ValidationResult, ValidationError, ErrorSeverity