# API Endpoint Integration Implementation Plan

## Overview

This document outlines the implementation plan for integrating API endpoints with domain entities across the Uno framework. The goal is to ensure a consistent approach to exposing domain entities through RESTful API endpoints following domain-driven design principles.

## Current Status

We have successfully implemented domain-driven design across all modules in the codebase as documented in `DOMAIN_DRIVEN_DESIGN_IMPLEMENTATION.md`. The next step is to ensure these domain entities are properly exposed through API endpoints.

The Uno framework already includes a sophisticated API endpoint integration system, including:
- `UnoEndpoint` - Base class for API endpoints
- `UnoEndpointFactory` - Factory for creating standardized endpoints
- `RepositoryAdapter` - Bridge between repositories and API endpoints
- Domain-specific routers for various entity types

## Implementation Plan

### Phase 1: Core Components Verification (Completed)

1. ✅ Verify that the core API components are properly implemented:
   - `UnoEndpoint` - Base endpoint class
   - `UnoEndpointFactory` - Endpoint factory
   - `RepositoryAdapter` - Repository adapter
   - `SchemaManager` - Schema management system

2. ✅ Ensure all components follow domain-driven design principles:
   - Proper domain entity usage
   - Repository pattern integration
   - Clean separation of concerns
   - Data Transfer Object (DTO) pattern

### Phase 2: Domain Module Integration (In Progress)

For each domain module, implement API endpoint integration:

1. ✅ **Attributes Module** - COMPLETED
   - ✅ Create DTOs (data transfer objects) for API requests/responses
   - ✅ Implement Schema Manager for entity-DTO conversion
   - ✅ Create endpoint registration function
   - ✅ Add comprehensive API documentation
   - ✅ Implement proper validation rules

2. ✅ **Values Module** - COMPLETED
   - ✅ Create DTOs for various value types (Boolean, Text, Decimal, etc.)
   - ✅ Implement Schema Manager for entity-DTO conversion
   - ✅ Create endpoint registration function
   - ✅ Add comprehensive API documentation
   - ✅ Implement specialized field validation

3. ✅ **Queries Module** - COMPLETED
   - ✅ Create DTOs for Query, QueryPath, and QueryValue entities
   - ✅ Implement Schema Manager with appropriate conversions
   - ✅ Create endpoint registration with specialized filter handling
   - ✅ Add comprehensive API documentation
   - ✅ Implement query execution endpoint

4. ✅ **Reports Module** - COMPLETED
   - ✅ Create DTOs for report templates, fields, and executions
   - ✅ Implement Schema Manager with appropriate conversions
   - ✅ Create endpoint registration including specialized operations (execute, export)
   - ✅ Add comprehensive API documentation
   - ✅ Implement file download capabilities for reports

5. **Workflows Module** - CURRENT FOCUS
   - Create DTOs for workflow definitions, triggers, and executions
   - Implement Schema Manager with appropriate conversions
   - Create endpoint registration including specialized operations
   - Add comprehensive API documentation
   - Implement workflow execution and monitoring endpoints

6. **Authorization Module**
   - Create DTOs for users, roles, permissions, and tenants
   - Implement Schema Manager with secure field handling
   - Create endpoint registration with proper authorization controls
   - Add comprehensive API documentation
   - Implement secure credential handling

7. **Meta Module**
   - Create DTOs for meta types and records
   - Implement Schema Manager with appropriate conversions
   - Create endpoint registration function
   - Add comprehensive API documentation
   - Implement specialized field validation

### Phase 3: API Consistency Layer

1. **Central Registration**
   - Create a central API registry for all endpoints
   - Implement consistent URL structure
   - Add versioning support
   - Implement API documentation aggregation

2. **Global Middleware**
   - Implement authorization middleware
   - Add logging and monitoring
   - Implement rate limiting
   - Add compression and caching

3. **Error Handling**
   - Implement standardized error responses
   - Create error mapping from domain errors to HTTP status codes
   - Add detailed error documentation
   - Implement validation error formatting

4. **Testing Framework**
   - Create API testing utilities
   - Implement comprehensive test coverage
   - Add performance testing
   - Create documentation for API testing

### Phase 4: Advanced Features

1. **Field Selection**
   - Implement field selection for all endpoints
   - Add nested field selection
   - Create documentation for field selection
   - Add performance optimizations

2. **Pagination**
   - Implement consistent pagination for list endpoints
   - Add cursor-based pagination option
   - Create documentation for pagination
   - Implement pagination metadata

3. **Filtering**
   - Implement consistent filtering for list endpoints
   - Add complex query support
   - Create documentation for filtering
   - Implement query optimization

4. **Sorting**
   - Implement consistent sorting for list endpoints
   - Add multi-field sort support
   - Create documentation for sorting
   - Implement sort optimization

5. **Streaming**
   - Implement streaming for large datasets
   - Add event stream support
   - Create documentation for streaming
   - Implement performance optimizations

### Phase 5: Documentation and Optimization

1. **OpenAPI Documentation**
   - Generate comprehensive OpenAPI documentation
   - Add examples for all endpoints
   - Create interactive documentation
   - Implement documentation testing

2. **Performance Optimization**
   - Implement caching strategies
   - Add database query optimization
   - Create performance monitoring
   - Implement lazy loading for related entities

3. **Security Review**
   - Conduct comprehensive security review
   - Implement security best practices
   - Add security documentation
   - Create security testing

## Implementation Details for Attributes Module

As a starting point, we'll implement the API integration for the Attributes module:

### DTOs for Attributes Module

```python
# attribute_dtos.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any

class AttributeTypeCreateDto(BaseModel):
    """DTO for creating attribute types."""
    name: str = Field(..., description="Name of the attribute type")
    text: str = Field(..., description="Display text for the attribute type")
    description: Optional[str] = Field(None, description="Description of the attribute type")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: bool = Field(False, description="Whether this attribute is required")
    multiple_allowed: bool = Field(False, description="Whether multiple values are allowed")
    comment_required: bool = Field(False, description="Whether a comment is required")
    display_with_objects: bool = Field(False, description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment text")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")

class AttributeTypeViewDto(BaseModel):
    """DTO for viewing attribute types."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the attribute type")
    text: str = Field(..., description="Display text for the attribute type")
    description: Optional[str] = Field(None, description="Description of the attribute type")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: bool = Field(..., description="Whether this attribute is required")
    multiple_allowed: bool = Field(..., description="Whether multiple values are allowed")
    comment_required: bool = Field(..., description="Whether a comment is required")
    display_with_objects: bool = Field(..., description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment text")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    # Add computed or relationship fields as needed
    
class AttributeTypeUpdateDto(BaseModel):
    """DTO for updating attribute types."""
    name: Optional[str] = Field(None, description="Name of the attribute type")
    text: Optional[str] = Field(None, description="Display text for the attribute type")
    description: Optional[str] = Field(None, description="Description of the attribute type")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: Optional[bool] = Field(None, description="Whether this attribute is required")
    multiple_allowed: Optional[bool] = Field(None, description="Whether multiple values are allowed")
    comment_required: Optional[bool] = Field(None, description="Whether a comment is required")
    display_with_objects: Optional[bool] = Field(None, description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment text")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")

# Similar DTOs for Attribute entity
class AttributeCreateDto(BaseModel):
    """DTO for creating attributes."""
    attribute_type_id: str = Field(..., description="ID of the attribute type")
    comment: Optional[str] = Field(None, description="Comment for this attribute")
    follow_up_required: bool = Field(False, description="Whether follow-up is required")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")

class AttributeViewDto(BaseModel):
    """DTO for viewing attributes."""
    id: str = Field(..., description="Unique identifier")
    attribute_type_id: str = Field(..., description="ID of the attribute type")
    comment: Optional[str] = Field(None, description="Comment for this attribute")
    follow_up_required: bool = Field(..., description="Whether follow-up is required")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    # Add related fields or computed properties as needed

class AttributeUpdateDto(BaseModel):
    """DTO for updating attributes."""
    comment: Optional[str] = Field(None, description="Comment for this attribute")
    follow_up_required: Optional[bool] = Field(None, description="Whether follow-up is required")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
```

### Schema Manager for Attributes Module

```python
# attribute_schemas.py
from typing import Dict, Type, Any, Optional
from pydantic import BaseModel

from uno.attributes.entities import Attribute, AttributeType
from uno.attributes.dtos import (
    AttributeTypeCreateDto, AttributeTypeViewDto, AttributeTypeUpdateDto,
    AttributeCreateDto, AttributeViewDto, AttributeUpdateDto
)

class AttributeTypeSchemaManager:
    """Schema manager for attribute type entities."""
    
    def __init__(self):
        self.schemas = {
            "view_schema": AttributeTypeViewDto,
            "edit_schema": AttributeTypeCreateDto,
            "update_schema": AttributeTypeUpdateDto,
        }
    
    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)
    
    def entity_to_dto(self, entity: AttributeType) -> AttributeTypeViewDto:
        """Convert an entity to a DTO."""
        # Implementation details
        return AttributeTypeViewDto(
            id=entity.id,
            name=entity.name,
            text=entity.text,
            description=entity.description,
            parent_id=entity.parent_id,
            required=entity.required,
            multiple_allowed=entity.multiple_allowed,
            comment_required=entity.comment_required,
            display_with_objects=entity.display_with_objects,
            initial_comment=entity.initial_comment,
            group_id=entity.group_id,
        )
    
    def dto_to_entity(self, dto: BaseModel) -> AttributeType:
        """Convert a DTO to an entity."""
        # Implementation details
        data = dto.model_dump()
        return AttributeType(**data)

class AttributeSchemaManager:
    """Schema manager for attribute entities."""
    
    def __init__(self):
        self.schemas = {
            "view_schema": AttributeViewDto,
            "edit_schema": AttributeCreateDto,
            "update_schema": AttributeUpdateDto,
        }
    
    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)
    
    def entity_to_dto(self, entity: Attribute) -> AttributeViewDto:
        """Convert an entity to a DTO."""
        # Implementation details
        return AttributeViewDto(
            id=entity.id,
            attribute_type_id=entity.attribute_type_id,
            comment=entity.comment,
            follow_up_required=entity.follow_up_required,
            group_id=entity.group_id,
        )
    
    def dto_to_entity(self, dto: BaseModel) -> Attribute:
        """Convert a DTO to an entity."""
        # Implementation details
        data = dto.model_dump()
        return Attribute(**data)
```

### API Endpoint Registration

```python
# attribute_endpoints.py
from fastapi import FastAPI, Depends, Security
from fastapi.security import OAuth2PasswordBearer

from uno.api.endpoint_factory import UnoEndpointFactory
from uno.attributes.domain_repositories import AttributeTypeRepository, AttributeRepository
from uno.attributes.entities import AttributeType, Attribute
from uno.attributes.schemas import AttributeTypeSchemaManager, AttributeSchemaManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def register_attribute_endpoints(
    app: FastAPI,
    path_prefix: str = "/api/v1",
    dependencies: list = None,
):
    """Register attribute endpoints with the FastAPI app."""
    # Set up endpoint factory
    endpoint_factory = UnoEndpointFactory()
    
    # Create schema managers
    attribute_type_schema_manager = AttributeTypeSchemaManager()
    attribute_schema_manager = AttributeSchemaManager()
    
    # Get repositories - these would typically be injected or created elsewhere
    attribute_type_repository = AttributeTypeRepository()
    attribute_repository = AttributeRepository()
    
    # Create default dependencies if none provided
    if dependencies is None:
        dependencies = [Depends(oauth2_scheme)]
    
    # Create attribute type endpoints
    attribute_type_endpoints = endpoint_factory.create_endpoints(
        app=app,
        repository=attribute_type_repository,
        entity_type=AttributeType,
        schema_manager=attribute_type_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{path_prefix}/attribute-types",
        endpoint_tags=["Attribute Types"],
        dependencies=dependencies,
    )
    
    # Create attribute endpoints
    attribute_endpoints = endpoint_factory.create_endpoints(
        app=app,
        repository=attribute_repository,
        entity_type=Attribute,
        schema_manager=attribute_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{path_prefix}/attributes",
        endpoint_tags=["Attributes"],
        dependencies=dependencies,
    )
    
    return {
        "attribute_type_endpoints": attribute_type_endpoints,
        "attribute_endpoints": attribute_endpoints,
    }
```

## Timeline and Milestones

### Phase 2: Domain Module Integration

1. ✅ **Attributes Module** - Week 1 - COMPLETED
2. ✅ **Values Module** - Week 2 - COMPLETED
3. ✅ **Queries Module** - Week 3 - COMPLETED
4. ✅ **Reports Module** - Week 4 - COMPLETED
5. **Workflows Module** - Week 5 - IN PROGRESS
6. **Authorization Module** - Week 6
7. **Meta Module** - Week 7

### Phase 3: API Consistency Layer - Week 8-9

### Phase 4: Advanced Features - Week 10-12

### Phase 5: Documentation and Optimization - Week 13-14

## Next Steps

1. ✅ Implement the DTOs for the Attributes module - COMPLETED
2. ✅ Create the schema manager for attribute entities - COMPLETED
3. ✅ Implement the endpoint registration function - COMPLETED
4. ✅ Update the API documentation - COMPLETED
5. ✅ Test the endpoints and validate functionality - COMPLETED
6. ✅ Move on to the Values module - COMPLETED
7. ✅ Implement the DTOs for the Values module - COMPLETED
8. ✅ Create the schema manager for value entities - COMPLETED
9. ✅ Implement the endpoint registration function - COMPLETED
10. ✅ Update the API documentation - COMPLETED
11. ✅ Move on to the Queries module - COMPLETED
12. ✅ Implement the DTOs for the Queries module - COMPLETED
13. ✅ Create the schema manager for query entities - COMPLETED
14. ✅ Implement the endpoint registration function - COMPLETED
15. ✅ Update the API documentation - COMPLETED
16. ✅ Move on to the Reports module - COMPLETED
17. ✅ Implement the DTOs for the Reports module - COMPLETED
18. ✅ Create the schema manager for report entities - COMPLETED
19. ✅ Implement the endpoint registration function - COMPLETED
20. ✅ Update the API documentation - COMPLETED
21. Move on to the Workflows module

## Conclusion

This implementation plan provides a structured approach to integrating API endpoints with domain entities across the Uno framework. By following domain-driven design principles and using the existing UnoEndpoint system, we'll create a consistent, maintainable, and well-documented API layer that exposes our domain functionality to clients.