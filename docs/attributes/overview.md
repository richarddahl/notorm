# Attributes Module Overview

The Attributes module provides a flexible system for attaching dynamic attributes to objects in your application. It enables you to define attribute types with specific constraints and associate attribute values with objects without modifying the database schema.

## Core Concepts

### Attribute Types

Attribute types define the structure and constraints of attributes that can be associated with objects. They specify:

- Which object types the attribute can be applied to
- What value types are allowed
- Whether multiple values are permitted
- Whether a comment is required
- Whether the attribute is required

```python
from uno.attributes import AttributeType

# Create an attribute type
attribute_type = AttributeType(
    name="Priority",
    text="Task priority level",
    required=True,
    multiple_allowed=False,
    comment_required=False,
    display_with_objects=True
)

# Specify which meta types this attribute applies to
attribute_type.describes = [task_meta_type]

# Specify which meta types can be used as values
attribute_type.value_types = [priority_meta_type]

# Save the attribute type
await attribute_type.save()
```

### Attributes

Attributes are instances of attribute types that are associated with specific objects:

```python
from uno.attributes import Attribute

# Create an attribute
attribute = Attribute(
    attribute_type_id=priority_type.id,
    comment="Set during initial planning"
)

# Associate values with the attribute
attribute.values = [high_priority]

# Save the attribute
await attribute.save()

# Associate the attribute with a record
task_record.attributes.append(attribute)
await task_record.save()
```

## Using the Attributes Service

The attributes module provides services for working with attributes and attribute types:

```python
from uno.attributes.services import AttributeService, AttributeTypeService

# Create an attribute with values
result = await attribute_service.create_attribute(
    attribute=new_attribute,
    values=[value1, value2]
)

# Add values to an existing attribute
result = await attribute_service.add_values(
    attribute_id="attr123",
    values=[value3, value4]
)

# Remove values from an attribute
result = await attribute_service.remove_values(
    attribute_id="attr123",
    value_ids=["val1", "val2"]
)

# Validate an attribute against its type constraints
result = await attribute_service.validate_attribute(
    attribute=attribute,
    values=[value1, value2]
)

# Get all attributes for a record
result = await attribute_service.get_attributes_for_record(
    record_id="record123"
)
```

## Graph Database Integration

The attributes module is fully integrated with the graph database, enabling complex queries based on attribute relationships:

```python
# Graph query to find all tasks with high priority
query = """
MATCH (t:Task)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType),
      (a)-[:HAS_VALUE]->(v:Value)
WHERE at.name = 'Priority' AND v.name = 'High'
RETURN t
"""
```

## Dependency Injection

The attributes module follows the project's dependency injection pattern:

```python
import inject
from uno.attributes.interfaces import AttributeServiceProtocol

# Get the attribute service from the DI container
attribute_service = inject.instance(AttributeServiceProtocol)

# Use the service
result = await attribute_service.get_attributes_for_record("record123")
```

## Type Safety

The attributes module ensures type safety through:

- Protocol definitions for repositories and services
- Validation of attribute values against type constraints
- Result type for error handling

## Error Handling

All operations return a `Result` type for consistent error handling:

```python
result = await attribute_service.create_attribute(attribute, values)

if result.is_ok():
    attribute = result.unwrap()
    print(f"Created attribute: {attribute.id}")
else:
    error = result.unwrap_err()
    print(f"Error: {error}")
```

## Best Practices

1. **Define Clear Attribute Types**: Create attribute types with clear names and descriptions
2. **Set Appropriate Constraints**: Use the required, multiple_allowed, and comment_required flags
3. **Validate Before Saving**: Always validate attributes against their types before saving
4. **Use Services for Business Logic**: Use the provided services instead of direct model operations
5. **Handle Errors Appropriately**: Check Result values for errors and handle them properly