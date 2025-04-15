# Values Module Overview

The Values module provides type-safe storage for different kinds of values used throughout the UNO framework, particularly as attribute values. It implements specialized storage for various data types, ensuring proper validation and efficient querying.

## Core Concepts

### Value Types

The module supports the following value types:

- **BooleanValue**: True/False values
- **TextValue**: String text values
- **IntegerValue**: Integer numeric values
- **DecimalValue**: Decimal numeric values
- **DateValue**: Date values
- **DateTimeValue**: Date and time values
- **TimeValue**: Time values
- **Attachment**: File attachments

Each value type has appropriate storage and validation logic tailored to its data type.

### Value Lookups

Each value type defines appropriate lookup operations for filtering, stored in the `lookups` field:

- **Text lookups**: equal, not_equal, contains, startswith, endswith, in, not_in
- **Numeric lookups**: equal, not_equal, greater_than, greater_than_equal, less_than, less_than_equal, in, not_in
- **Boolean lookups**: equal, not_equal
- **DateTime lookups**: equal, not_equal, greater_than, greater_than_equal, less_than, less_than_equal, in, not_in

## Using the Values Module

### Creating Values

```python
from uno.values import BooleanValue, TextValue, IntegerValue
from uno.values.services import ValueService

# Using the value service
text_result = await value_service.create_value(```

value_type=TextValue,
value="High",
name="High Priority"
```
)

bool_result = await value_service.create_value(```

value_type=BooleanValue,
value=True,
name="Yes"
```
)

int_result = await value_service.create_value(```

value_type=IntegerValue,
value=100,
name="Maximum Score"
```
)

# Creating an attachment
attachment_result = await value_service.create_attachment(```

file_path="/path/to/file.pdf",
name="Project Proposal"
```
)
```

### Getting or Creating Values

If you want to get an existing value or create it if it doesn't exist:

```python
result = await value_service.get_or_create_value(```

value_type=TextValue,
value="Medium",
name="Medium Priority"
```
)

if result.is_ok():```

text_value = result.unwrap()
print(f"Value ID: {text_value.id}")
```
```

### Value Validation and Conversion

The values module provides utilities for validating and converting values:

```python
# Validate a value
validation_result = await value_service.validate_value(```

value_type=IntegerValue,
value=42
```
)

# Convert a value to the appropriate type
conversion_result = await value_service.convert_value(```

value="42",
target_type=IntegerValue
```
)

if conversion_result.is_ok():```

converted_value = conversion_result.unwrap()  # Will be an int: 42
```
```

## Using Values with Attributes

Values are commonly used in conjunction with the Attributes module:

```python
from uno.attributes import Attribute
from uno.values import TextValue

# Create a priority value
priority_result = await value_service.create_value(```

value_type=TextValue,
value="Critical",
name="Critical Priority"
```
)

priority_value = priority_result.unwrap()

# Create an attribute with the value
attribute = Attribute(```

attribute_type_id=priority_type_id,
comment="Set by project manager"
```
)

# Associate the value with the attribute
attribute.values = [priority_value]

# Save the attribute
await attribute.save()
```

## Dependency Injection

The values module follows the project's dependency injection pattern:

```python
import inject
from uno.values.interfaces import ValueServiceProtocol

# Get the value service from the DI container
value_service = inject.instance(ValueServiceProtocol)

# Use the service
result = await value_service.get_value_by_id(TextValue, "value123")
```

## Type Safety

The values module ensures type safety through:

- Strict value type validation
- Type checking during value creation
- Conversion utilities for different value types
- Result type for error handling

## Error Handling

All operations return a `Result` type for consistent error handling:

```python
result = await value_service.create_value(TextValue, "Test")

if result.is_ok():```

value = result.unwrap()
print(f"Created value with ID: {value.id}")
```
else:```

error = result.unwrap_err()
print(f"Error: {error}")
```
```

## Best Practices

1. **Use Appropriate Value Types**: Choose the correct value type for your data
2. **Validate Input**: Always validate input values before creating value objects
3. **Handle Type Conversion**: Use the conversion utilities when dealing with user input
4. **Use Services for Business Logic**: Use the provided services instead of direct model operations
5. **Reuse Values**: Use get_or_create_value to avoid duplicate values
6. **Handle Errors Appropriately**: Check Result values for errors and handle them properly