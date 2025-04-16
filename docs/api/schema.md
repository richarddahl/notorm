# Schema Module API

The Schema module in Uno provides a domain-driven approach to schema management, including validation and transformation of data structures. This documentation covers the domain entities, repositories, and services for working with schema definitions.

## Key Features

- Create, update, and manage schema definitions for domain entities, DTOs, and API contracts
- Validate data against schemas with detailed error reporting
- Transform between different schema representations (entity ⟷ DTO)
- Generate API schemas for CRUD operations
- Manage schema configurations for different use cases (data storage, API responses, forms, etc.)

## Getting Started

### Basic Usage

```python
from uno.schema import (
    SchemaDefinition, SchemaType, FieldDefinition, SchemaId, 
    SchemaProvider, SchemaConfiguration
)
from typing import Optional

# Initialize and configure the Schema module
provider = SchemaProvider()
provider.configure()

# Register standard configurations
provider.register_standard_configurations()

# Get the schema manager service
schema_manager = SchemaProvider.get_schema_manager()

# Create a schema definition
user_schema = SchemaDefinition(
    id=SchemaId("UserSchema"),
    name="User",
    type=SchemaType.ENTITY,
    description="User entity schema"
)

# Add fields to the schema
user_schema.add_field(FieldDefinition(
    name="id",
    annotation=str,
    description="User identifier",
    required=True
))
user_schema.add_field(FieldDefinition(
    name="username",
    annotation=str,
    description="Username",
    required=True
))
user_schema.add_field(FieldDefinition(
    name="email",
    annotation=str,
    description="Email address",
    required=True
))
user_schema.add_field(FieldDefinition(
    name="password",
    annotation=str,
    description="Password (hashed)",
    required=True
))
user_schema.add_field(FieldDefinition(
    name="full_name",
    annotation=Optional[str],
    description="Full name",
    required=False
))

# Save the schema
result = schema_manager.save_schema_definition(user_schema)
if result.is_success:
    print(f"Schema saved: {user_schema.name}")
```

### Data Validation

```python
from uno.schema import SchemaProvider

# Get the schema validation service
schema_validation = SchemaProvider.get_schema_validation()

# Validate data against a schema
data = {
    "id": "user123",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "hashed_password",
    "full_name": "John Doe"
}

result = schema_validation.validate_data(SchemaId("UserSchema"), data)
if result.is_success:
    validated_data = result.value
    print("Data validation successful")
else:
    print(f"Validation error: {result.error.message}")
```

### Schema Transformation

```python
from uno.schema import SchemaProvider, SchemaType

# Get the schema transformation service
schema_transformation = SchemaProvider.get_schema_transformation()

# Create DTOs from an entity class
from myapp.domain.entities import User

# Create a DTO for API responses
dto_result = schema_transformation.create_dto_from_entity(
    entity_class=User,
    schema_type=SchemaType.DETAIL,
    exclude_fields={"password", "internal_data"}
)

if dto_result.is_success:
    UserDetailDTO = dto_result.value
    print(f"Created DTO: {UserDetailDTO.__name__}")
```

### Using the FastAPI Router

```python
from fastapi import FastAPI
from uno.schema import schema_router

app = FastAPI()

# Include the schema router
app.include_router(schema_router)
```

## API Reference

### Entities

#### Value Objects

- `SchemaId`: Unique identifier for a schema
- `FieldDefinition`: Definition of a field in a schema
- `PaginationParams`: Parameters for pagination
- `PaginationMetadata`: Metadata for paginated results
- `MetadataFields`: Common metadata fields like created_at, updated_at, etc.

#### Entities and Aggregates

- `SchemaDefinition`: Entity representing a schema definition
- `SchemaConfiguration`: Configuration for schema creation
- `PaginatedResult`: Entity representing a paginated list of items

#### Request/Response Models

- `SchemaCreationRequest`: Request model for creating a schema
- `SchemaUpdateRequest`: Request model for updating a schema
- `SchemaValidationRequest`: Request model for schema validation
- `ApiSchemaCreationRequest`: Request model for creating a set of API schemas

### Repositories

#### Protocols

- `SchemaDefinitionRepositoryProtocol`: Repository protocol for schema definitions
- `SchemaConfigurationRepositoryProtocol`: Repository protocol for schema configurations

#### Implementations

- `InMemorySchemaDefinitionRepository`: In-memory implementation of the schema definition repository
- `InMemorySchemaConfigurationRepository`: In-memory implementation of the schema configuration repository
- `FileSchemaDefinitionRepository`: File-based implementation of the schema definition repository
- `FileSchemaConfigurationRepository`: File-based implementation of the schema configuration repository

### Services

#### Protocols

- `SchemaManagerServiceProtocol`: Protocol for schema manager service
- `SchemaValidationServiceProtocol`: Protocol for schema validation service
- `SchemaTransformationServiceProtocol`: Protocol for schema transformation service

#### Implementations

- `SchemaManagerService`: Service for managing schema definitions and configurations
- `SchemaValidationService`: Service for validating data against schemas
- `SchemaTransformationService`: Service for transforming between different schema representations

### Dependency Injection

- `SchemaProvider`: Dependency provider for the Schema module
- `TestingSchemaProvider`: Testing provider for the Schema module

### HTTP API Endpoints

The Schema module provides a FastAPI router with endpoints for schema management:

#### Schema Definition Endpoints

- `POST /api/schemas`: Create a new schema definition
- `GET /api/schemas`: List schema definitions with optional filtering
- `GET /api/schemas/{schema_id}`: Get a schema definition by ID
- `PUT /api/schemas/{schema_id}`: Update a schema definition
- `DELETE /api/schemas/{schema_id}`: Delete a schema definition

#### Schema Validation Endpoints

- `POST /api/schemas/validate`: Validate data against a schema

#### Schema Configuration Endpoints

- `POST /api/schemas/configs/{name}`: Create a schema configuration
- `GET /api/schemas/configs`: List all schema configurations
- `GET /api/schemas/configs/{name}`: Get a schema configuration by name
- `DELETE /api/schemas/configs/{name}`: Delete a schema configuration

#### API Schema Endpoints

- `POST /api/schemas/api-schemas`: Create a complete set of API schemas

## Example Uses

### Creating and Managing Schemas

```python
from uno.schema import SchemaProvider, SchemaCreationRequest
from fastapi import Depends

async def create_product_schema(
    schema_manager = Depends(SchemaProvider.get_schema_manager)
):
    request = SchemaCreationRequest(
        name="Product",
        type="ENTITY",
        description="Product entity schema",
        fields={
            "id": {
                "annotation": "str",
                "description": "Product identifier",
                "required": True
            },
            "name": {
                "annotation": "str",
                "description": "Product name",
                "required": True
            },
            "description": {
                "annotation": "Optional[str]",
                "description": "Product description",
                "required": False
            },
            "price": {
                "annotation": "Decimal",
                "description": "Product price",
                "required": True
            },
            "category_id": {
                "annotation": "str",
                "description": "Category identifier",
                "required": True
            }
        }
    )
    
    result = schema_manager.create_schema_definition(request)
    return result.value.to_dict() if result.is_success else {"error": result.error.message}
```

### Generating API Schemas for an Entity

```python
from uno.schema import SchemaProvider, ApiSchemaCreationRequest
from fastapi import Depends

async def generate_order_api_schemas(
    schema_transformation = Depends(SchemaProvider.get_schema_transformation)
):
    request = ApiSchemaCreationRequest(
        entity_name="Order",
        fields={
            "id": {
                "annotation": "str",
                "description": "Order identifier",
                "required": True
            },
            "user_id": {
                "annotation": "str",
                "description": "User identifier",
                "required": True
            },
            "items": {
                "annotation": "List[Dict[str, Any]]",
                "description": "Order items",
                "required": True
            },
            "total": {
                "annotation": "Decimal",
                "description": "Order total",
                "required": True
            },
            "status": {
                "annotation": "str",
                "description": "Order status",
                "required": True
            },
            "created_at": {
                "annotation": "datetime",
                "description": "Creation timestamp",
                "required": True
            },
            "updated_at": {
                "annotation": "datetime",
                "description": "Last update timestamp",
                "required": True
            }
        },
        create_list_schema=True,
        create_detail_schema=True,
        create_create_schema=True,
        create_update_schema=True
    )
    
    result = schema_transformation.create_api_schemas(request)
    return {
        "entity_name": request.entity_name,
        "schemas": {key: schema.to_dict() for key, schema in result.value.items()} if result.is_success else {},
        "error": result.error.message if not result.is_success else None
    }
```

## Testing

The Schema module provides a `TestingSchemaProvider` class for testing:

```python
from uno.schema import TestingSchemaProvider
import pytest

class MockSchemaDefinitionRepository:
    def get_by_id(self, schema_id):
        # Mock implementation
        pass
    
    # Other methods...

@pytest.fixture
def setup_test_schema():
    # Configure with mocks
    TestingSchemaProvider.configure_with_mocks(
        schema_def_repository=MockSchemaDefinitionRepository()
    )
    
    yield
    
    # Clean up
    TestingSchemaProvider.cleanup()

def test_schema_validation(setup_test_schema):
    # Test schema validation
    schema_validation = SchemaProvider.get_schema_validation()
    # Test code...
```