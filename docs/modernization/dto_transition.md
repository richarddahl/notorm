# Transitioning from Schema to DTO Naming

This guide provides information on the transition from `UnoSchema` to `UnoDTO` naming convention in the uno framework to better align with Domain-Driven Design principles.

## Background

With the full transition to domain-driven design (DDD), the terminology used in the framework needs to clearly distinguish between different architectural concepts. One such distinction is between database schemas and Data Transfer Objects (DTOs).

In the original implementation, the `UnoSchema` class was used to create Pydantic models for data validation, serialization, and API documentation. While this functionality is valuable, the term "schema" is overloaded:

1. In database contexts, "schema" refers to database structure
2. In API contexts, "schema" often refers to JSON schema for validation
3. In DDD, separate objects for data transfer are typically called DTOs

To reduce confusion and better align with DDD terminology, we're transitioning from `UnoSchema` to `UnoDTO` naming.

## Changes Overview

The following classes and concepts are being renamed:

| Old Name | New Name | Purpose |
|----------|----------|---------|
| `UnoSchema` | `UnoDTO` | Base class for data transfer objects |
| `UnoSchemaConfig` | `DTOConfig` | Configuration for DTO creation |
| `UnoSchemaManager` | `DTOManager` | Manager for creating and registering DTOs |
| `PaginatedList` | `PaginatedListDTO` | DTO for paginated lists |
| `WithMetadata` | `WithMetadataDTO` | DTO with metadata fields |

## Migration Guide

### 1. Update Import Statements

Replace imports from `uno.schema.schema` to use the new module path:

```python
# Old imports
from uno.schema.schema import UnoSchema, UnoSchemaConfig, PaginatedList, WithMetadata

# New imports
from uno.dto import UnoDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO
```

### 2. Update Class References

Update references to these classes throughout your code:

```python
# Old code
class MySchema(UnoSchema):
    name: str
    value: int

# New code
class MyDTO(UnoDTO):
    name: str
    value: int
```

### 3. Update Manager Usage

Replace schema manager with DTO manager:

```python
# Old code
from uno.schema.schema_manager import UnoSchemaManager, get_schema_manager

schema_manager = get_schema_manager()
my_schema = schema_manager.create_schema("my_schema", MyModel)

# New code
from uno.dto.manager import DTOManager, get_dto_manager

dto_manager = get_dto_manager()
my_dto = dto_manager.create_dto("my_dto", MyModel)
```

### 4. Update Configuration

Update configuration objects:

```python
# Old code
config = UnoSchemaConfig(
    schema_base=UnoSchema,
    exclude_fields={"internal_field"}
)

# New code
config = DTOConfig(
    dto_base=UnoDTO,
    exclude_fields={"internal_field"}
)
```

### 5. Update Method Calls

Update method calls using the new terminology:

```python
# Old code
list_schema = schema_manager.get_list_schema(MyModel)

# New code
list_dto = dto_manager.get_list_dto(MyModel)
```

## Implementation Roadmap

The transition will be implemented in phases to minimize disruption:

1. **Phase 1 (Current)**: Introduce new classes alongside existing ones
   - New `uno.dto` module with the new classes
   - Old classes remain but are marked as deprecated

2. **Phase 2**: Deprecation period
   - Old classes continue to work but issue deprecation warnings
   - Documentation and examples updated to use new terminology

3. **Phase 3**: Remove deprecated classes
   - Old classes removed in a future major version

## Benefits of the Change

This naming transition offers several benefits:

1. **Clearer terminology**: "DTO" explicitly communicates the purpose of these objects for data transfer
2. **Alignment with DDD**: Proper DDD terminology helps developers understand the architectural patterns
3. **Reduced confusion**: Avoids overloading the term "schema" which has different meanings in different contexts
4. **Better code organization**: Separate module for DTOs makes the code organization clearer

## Compatibility

During the transition, both naming conventions will work to maintain backward compatibility. The deprecated classes will remain functional but will issue deprecation warnings encouraging migration to the new names.

## Example

Here's a complete example showing both the old and new approach:

### Old Approach

```python
from uno.schema.schema import UnoSchema
from uno.schema.schema_manager import get_schema_manager

class UserSchema(UnoSchema):
    id: str
    name: str
    email: str

schema_manager = get_schema_manager()
list_schema = schema_manager.get_list_schema(UserSchema)
```

### New Approach

```python
from uno.dto import UnoDTO
from uno.dto.manager import get_dto_manager

class UserDTO(UnoDTO):
    id: str
    name: str
    email: str

dto_manager = get_dto_manager()
list_dto = dto_manager.get_list_dto(UserDTO)
```

## Conclusion

The transition from `UnoSchema` to `UnoDTO` naming is part of our commitment to clear, consistent, and precise terminology in the uno framework. This change better aligns the framework with domain-driven design principles and helps developers understand the purpose and responsibility of each component.

For any questions or issues related to this transition, please file an issue on GitHub.