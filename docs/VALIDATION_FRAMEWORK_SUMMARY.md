# Validation Framework Implementation

As part of the Phase 1 core infrastructure implementation, we have completed the Validation Framework task. This framework provides a comprehensive approach to validation across the UNO framework.

## Key Components

### Enhanced Result Pattern

- Extended `Result[T, E]` class to support validation scenarios with metadata
- Added `ValidationError` class to provide detailed error information with path, code, severity, and context
- Added new utility methods like `value_or`, `value_or_raise`, `map_error`, `combine`, and `tap`
- Added class methods like `from_exception`, `try_catch`, and `all` for better error handling
- Added `ValidationResult` type alias for ease of use

### Core Validation Components

1. **ValidationContext**
   - Tracks validation state with path information for nested validation
   - Provides hierarchical error path tracking
   - Supports severities for differentiating errors, warnings, and info

2. **Validator Framework**
   - Base `Validator` class for implementing custom validators
   - `ValidationProtocol` interface for static typing of validators
   - Field-level validation rules like `required`, `min_length`, `max_length`, etc.

3. **Schema Validation**
   - `SchemaValidator` for validating against Pydantic schemas
   - Integration with Pydantic v2 validation system
   - Conversion between Pydantic errors and UNO validation errors

4. **Domain Validation**
   - `DomainValidator` for validating domain objects
   - Specialized validators for entities and value objects
   - Support for field-level validation and invariant validation

5. **Rule-Based Validation**
   - Composable business rules with `Rule` class hierarchy
   - Support for logical operations (`AND`, `OR`, `NOT`) using operator overloading
   - Rule sets for organizing related rules

## Usage Examples

### Using Result Pattern for Error Handling

```python
def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Result.failure("Division by zero")
    return Result.success(a / b)

# Chain operations with bind
result = divide(10, 2).bind(lambda x: divide(x, 2))

# Handle results
if result.is_success:
    print(f"Result: {result.value}")
else:
    print(f"Error: {result.error}")
```

### Validating Schema Data

```python
from pydantic import BaseModel, Field
from uno.core.validation import validate_schema

class UserSchema(BaseModel):
    name: str = Field(..., min_length=3)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    age: int = Field(..., ge=18)

# Validate data against schema
validate = validate_schema(UserSchema)
result = validate({
    "name": "John",
    "email": "john@example.com",
    "age": 25
})

if result.is_success:
    user = result.value
    print(f"Valid user: {user.name}, {user.email}, {user.age}")
else:
    for error in result.errors:
        print(f"Error at {error.path}: {error.message}")
```

### Domain Object Validation

```python
from uno.core.validation import domain_validator, required, min_length, email, range_rule

@dataclass
class User:
    name: str
    email: str
    age: int

# Create domain validator
validator = domain_validator(
    User,
    field_validators={
        "name": [required, min_length(3)],
        "email": [required, email],
        "age": [required, range_rule(18, 120)]
    }
)

# Validate a domain object
result = validator.validate(User("John", "john@example.com", 25))
```

### Business Rule Validation

```python
from uno.core.validation import RuleValidator, Rule

class AgeRule(Rule[User]):
    def evaluate(self, obj: User, context: ValidationContext) -> bool:
        if obj.age < 18:
            context.add_error("User must be at least 18 years old", path="age")
            return False
        return True

class EmailRule(Rule[User]):
    def evaluate(self, obj: User, context: ValidationContext) -> bool:
        if not obj.email or "@" not in obj.email:
            context.add_error("User must have a valid email", path="email")
            return False
        return True

# Combine rules using operators
rule = AgeRule() & EmailRule()  # AND rule
rule = AgeRule() | EmailRule()  # OR rule
rule = ~AgeRule()               # NOT rule

# Create validator with rule
validator = RuleValidator[User]()
validator.add_rule(rule)
```

## Integration with Other Components

- Repository pattern will use validation for input validation
- Service layer will use validation for business rule enforcement
- API layer will use schema validation for request/response validation
- Domain model will use validation for invariant enforcement

## Next Steps

The validation framework is now complete and ready for use in other components. The next steps in Phase 1 are:

1. Complete the protocol testing framework
2. Implement the database provider with connection pooling
3. Create the event bus implementation
4. Implement the Unit of Work pattern