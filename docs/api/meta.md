# Meta API Reference

This document provides a comprehensive reference for the Meta API endpoints, following the domain-driven design approach. It includes detailed information about request and response formats, authentication requirements, and integration examples.

## Overview

The Meta module provides a foundational system for tracking types and records in the application. It serves as a registry for meta-information about objects in the system and enables features like the knowledge graph, attributes, and values to work. It follows domain-driven design principles with a clean separation of:

- **Domain Entities**: Core business objects like MetaType and MetaRecord
- **DTOs**: Data Transfer Objects for API requests and responses
- **Schema Managers**: Convert between domain entities and DTOs
- **API Integration**: Register standardized API endpoints

## Base URL

All API endpoints are prefixed with `/api/v1/meta/`.

## Authentication

All API endpoints require authentication using a valid JWT token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## Meta Types

Meta types define the types of records in the system and are used for type-safety and tracking throughout the application.

### List Meta Types

Retrieves a paginated list of meta types with optional filtering.

**Endpoint:** `GET /api/v1/meta/types`  
**Query Parameters:**
- `id`: Filter by ID (exact match)
- `id_contains`: Filter by ID (contains)
- `name_contains`: Filter by name (contains)
- `description_contains`: Filter by description (contains)
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of meta types
```json
{
  "items": [
    {
      "id": "user_profile",
      "name": "User Profile",
      "description": "Stores user profile information",
      "display_name": "User Profile",
      "record_count": 42
    },
    {
      "id": "product",
      "name": "Product",
      "description": "Stores product catalog information",
      "display_name": "Product",
      "record_count": 567
    },
    // More meta types...
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

### Get Meta Type

Retrieves a specific meta type by ID.

**Endpoint:** `GET /api/v1/meta/types/{meta_type_id}`  
**Path Parameters:**
- `meta_type_id`: The ID of the meta type to retrieve

**Response:** Meta type details
```json
{
  "id": "user_profile",
  "name": "User Profile",
  "description": "Stores user profile information",
  "display_name": "User Profile",
  "record_count": 42
}
```

### Create Meta Type

Creates a new meta type.

**Endpoint:** `POST /api/v1/meta/types`  
**Request Body:** Meta type creation data
```json
{
  "id": "customer",
  "name": "Customer",
  "description": "Stores customer information"
}
```

**Response:** Created meta type
```json
{
  "id": "customer",
  "name": "Customer",
  "description": "Stores customer information",
  "display_name": "Customer",
  "record_count": 0
}
```

### Update Meta Type

Updates an existing meta type.

**Endpoint:** `PATCH /api/v1/meta/types/{meta_type_id}`  
**Path Parameters:**
- `meta_type_id`: The ID of the meta type to update

**Request Body:** Meta type update data (all fields optional)
```json
{
  "name": "Customer Account",
  "description": "Stores customer account information and preferences"
}
```

**Response:** Updated meta type (same structure as Get Meta Type)

### Delete Meta Type

Deletes an existing meta type.

**Endpoint:** `DELETE /api/v1/meta/types/{meta_type_id}`  
**Path Parameters:**
- `meta_type_id`: The ID of the meta type to delete

**Response:** No content (204)

## Meta Records

Meta records represent specific instances of meta types and serve as the base for all identifiable objects in the system.

### List Meta Records

Retrieves a paginated list of meta records with optional filtering.

**Endpoint:** `GET /api/v1/meta/records`  
**Query Parameters:**
- `id`: Filter by ID (exact match)
- `meta_type_id`: Filter by meta type ID
- `has_attribute`: Filter by having a specific attribute
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of meta records
```json
{
  "items": [
    {
      "id": "prof_12345abcde",
      "meta_type_id": "user_profile",
      "type_name": "User Profile",
      "attributes": ["attr_12345abcde", "attr_67890fghij"]
    },
    {
      "id": "prof_67890fghij",
      "meta_type_id": "user_profile",
      "type_name": "User Profile",
      "attributes": ["attr_abcde12345", "attr_fghij67890"]
    },
    // More meta records...
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### Get Meta Record

Retrieves a specific meta record by ID.

**Endpoint:** `GET /api/v1/meta/records/{meta_record_id}`  
**Path Parameters:**
- `meta_record_id`: The ID of the meta record to retrieve

**Response:** Meta record details
```json
{
  "id": "prof_12345abcde",
  "meta_type_id": "user_profile",
  "type_name": "User Profile",
  "attributes": ["attr_12345abcde", "attr_67890fghij"]
}
```

### Create Meta Record

Creates a new meta record.

**Endpoint:** `POST /api/v1/meta/records`  
**Request Body:** Meta record creation data
```json
{
  "id": "prof_abcde12345",
  "meta_type_id": "user_profile",
  "attributes": ["attr_12345abcde", "attr_67890fghij"]
}
```

**Response:** Created meta record
```json
{
  "id": "prof_abcde12345",
  "meta_type_id": "user_profile",
  "type_name": "User Profile",
  "attributes": ["attr_12345abcde", "attr_67890fghij"]
}
```

### Update Meta Record

Updates an existing meta record.

**Endpoint:** `PATCH /api/v1/meta/records/{meta_record_id}`  
**Path Parameters:**
- `meta_record_id`: The ID of the meta record to update

**Request Body:** Meta record update data
```json
{
  "attributes": ["attr_12345abcde", "attr_67890fghij", "attr_new12345"]
}
```

**Response:** Updated meta record (same structure as Get Meta Record)

### Delete Meta Record

Deletes an existing meta record.

**Endpoint:** `DELETE /api/v1/meta/records/{meta_record_id}`  
**Path Parameters:**
- `meta_record_id`: The ID of the meta record to delete

**Response:** No content (204)

## Error Handling

The API follows standard HTTP status codes for errors with a consistent response format:

```json
{
  "status_code": 404,
  "error": "NOT_FOUND",
  "message": "Meta type with ID user_profile_invalid not found",
  "details": {
    "resource_type": "meta_type",
    "resource_id": "user_profile_invalid"
  },
  "timestamp": "2025-04-16T15:45:30.789Z"
}
```

Common status codes:

- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate ID)
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

## Integration Examples

### Register All Meta Endpoints

The meta module provides a convenience function to register all endpoints:

```python
from fastapi import FastAPI
from uno.meta import register_meta_endpoints

app = FastAPI()

# Register all meta endpoints
endpoints = register_meta_endpoints(
    app_or_router=app,
    path_prefix="/api/v1",
    dependencies=[Depends(authenticate_user)],
    include_auth=True
)
```

### Register Only Specific Endpoint Types

You can also register specific endpoint types:

```python
from fastapi import FastAPI, APIRouter
from uno.meta import (
    register_meta_type_endpoints, 
    register_meta_record_endpoints
)

app = FastAPI()

# Create a router
meta_router = APIRouter(prefix="/api/v1/meta")

# Register only meta type endpoints
type_endpoints = register_meta_type_endpoints(
    app_or_router=meta_router,
    path_prefix="",
    dependencies=[Depends(authenticate_user)]
)

# Include the router in the app
app.include_router(meta_router)
```

### Using Schema Managers Directly

You can use schema managers to convert between domain entities and DTOs:

```python
from uno.meta import (
    MetaType, MetaTypeViewDto, MetaTypeSchemaManager
)

# Create a schema manager
schema_manager = MetaTypeSchemaManager()

# Get a meta type entity from the repository
meta_type = await meta_type_repository.get_by_id("user_profile")
record_count = await meta_record_repository.count_by_type("user_profile")

# Convert the entity to a DTO
meta_type_dto = schema_manager.entity_to_dto(meta_type, record_count)

# Return the DTO in an API response
return meta_type_dto
```

## Related Resources

- [API Overview](overview.md): Overview of the API system
- [Endpoint Factory](endpoint-factory.md): Automatic endpoint generation
- [Domain Integration](domain-integration.md): Using domain repositories with endpoints
- [Attributes API](attributes.md): API for managing attributes
- [Values API](values.md): API for managing values