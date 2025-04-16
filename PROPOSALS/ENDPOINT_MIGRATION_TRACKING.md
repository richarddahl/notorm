# Endpoint Migration Tracking Issue

## Issue Summary

During the migration from legacy `endpoints.py` to domain-driven `domain_endpoints.py`, we encountered an issue with Pydantic model generation from domain entities. This issue prevents us from completely removing all legacy endpoint files at once. This document tracks the steps needed to complete the migration.

## Technical Details

### Current Status

All modules have been migrated to use domain-driven design principles:
- Domain entities are defined in `entities.py` files
- Domain repositories are implemented in `domain_repositories.py`
- Domain services are implemented in `domain_services.py`
- Domain API endpoints are defined in `domain_endpoints.py`

However, some modules still have legacy `endpoints.py` files:
- `src/uno/attributes/endpoints.py`
- `src/uno/authorization/endpoints.py`
- `src/uno/meta/endpoints.py`
- `src/uno/reports/endpoints.py`
- `src/uno/values/endpoints.py`
- `src/uno/vector_search/endpoints.py`
- `src/uno/workflows/endpoints.py`

These files are no longer actively used but may still be referenced in some parts of the code.

### Issue Description

When attempting to remove these files and ensure all code uses the domain-driven approach, we discovered an issue with the automatic Pydantic model generation in the `uno.domain.api_integration.DomainRouter._generate_schemas` method:

1. Some entity classes like `MetaType` have fields with default values (e.g., `name: Optional[str] = None`)
2. When the domain router tries to create Pydantic models from these entity fields, Pydantic 2.x raises an error:
   ```
   pydantic.errors.PydanticUserError: A non-annotated attribute was detected: `name = typing.Optional[str]`.
   ```

This suggests that the automatic model generation approach needs to be updated to be compatible with Pydantic 2.x's stricter typing requirements.

## Migration Plan

1. **Fix Domain Router Schema Generation**
   - Update `uno.domain.api_integration.DomainRouter._generate_schemas` to handle entity fields with default values correctly
   - Ensure compatibility with Pydantic 2.x's type annotation requirements
   - Add specific handling for dataclass fields

2. **Create Integration Tests**
   - Develop API integration tests for each module to ensure functionality is preserved
   - Test both legacy endpoints and domain-driven endpoints to confirm equivalence

3. **Module-by-Module Migration**
   - Fix and test each module one by one
   - Remove legacy `endpoints.py` files after confirming functionality
   - Update any code that might be referencing these files

4. **Documentation Updates**
   - Update API documentation to reflect the domain-driven approach
   - Add examples of how to use the domain-driven endpoints
   - Clearly mark the legacy approach as deprecated

## Tracking

| Module        | Integration Tests Created | Router Schema Fix Applied | Legacy File Removed | Documentation Updated |
|---------------|---------------------------|---------------------------|---------------------|------------------------|
| Attributes    | ✅                        | ✅                        | ✅                  | ✅                     |
| Authorization | ✅                        | ✅                        | ✅                  | ✅                     |
| Meta          | ✅                        | ✅                        | ✅                  | ✅                     |
| Reports       | ✅                        | ✅                        | ✅                  | ✅                     |
| Values        | ✅                        | ✅                        | ✅                  | ✅                     |
| Vector Search | ✅                        | ✅                        | ✅                  | ✅                     |
| Workflows     | ✅                        | ✅                        | ✅                  | ✅                     |

## Implemented Solution for Schema Generation

The core issue was in how the domain router generates Pydantic models from dataclass fields. We needed to:

1. Extract field type annotations correctly, including default values
2. Handle Optional fields properly
3. Ensure ClassVar and other special fields are excluded

The solution has been implemented in `src.uno.domain.api_integration.DomainRouter._generate_schemas()`:

```python
def _generate_schemas(self) -> None:
    """
    Generate Pydantic schemas (DTOs) based on the entity type.
    
    This method automatically creates reasonable DTOs if they weren't provided.
    """
    from dataclasses import fields, MISSING
    
    entity_name = self.entity_type.__name__
    
    # Extract field information properly from dataclass fields
    field_info = {}
    excluded_fields = ['id', 'created_at', 'updated_at']
    
    # Get dataclass fields to handle default values correctly
    dataclass_fields = {f.name: f for f in fields(self.entity_type)}
    # Get type hints for annotation information
    type_hints = get_type_hints(self.entity_type)
    
    for name, field_type in type_hints.items():
        # Skip private fields and exclusions
        if name.startswith('_') or name in excluded_fields:
            continue
            
        # Skip ClassVar fields
        if str(field_type).startswith('typing.ClassVar'):
            continue
            
        # Handle fields with default values from dataclass fields
        if name in dataclass_fields:
            dc_field = dataclass_fields[name]
            if dc_field.default is not MISSING:
                # Field has a default value
                field_info[name] = (field_type, dc_field.default)
            elif dc_field.default_factory is not MISSING:
                # Field has a default factory
                field_info[name] = (field_type, None)
            else:
                # Required field
                field_info[name] = (field_type, ...)
        else:
            # Regular field without default
            field_info[name] = (field_type, ...)
    
    # Create response model (includes all fields)
    if not self.response_dto:
        self.response_dto = create_model(
            f"{entity_name}Response",
            id=(str, ...),
            created_at=(Optional[Any], None),
            updated_at=(Optional[Any], None),
            **field_info
        )
        
    # Create model for creation (no id required)
    if not self.create_dto:
        self.create_dto = create_model(
            f"{entity_name}Create",
            **field_info
        )
        
    # Create model for updates (all fields optional)
    if not self.update_dto:
        update_field_info = {
            k: (Optional[v[0]], None) for k, v in field_info.items()
        }
        self.update_dto = create_model(
            f"{entity_name}Update",
            **update_field_info
        )
```

This implementation has been tested and successfully generates the correct DTOs for entities with default values, including the problematic `MetaType` entity.

## Timeline

- **Week 1**: Fix the domain router schema generation
- **Week 2**: Create integration tests for all modules
- **Week 3**: Complete module-by-module migration
- **Week 4**: Update documentation and finalize transition