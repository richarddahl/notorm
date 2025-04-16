# Attributes API

This document provides an overview of the Attributes API, which allows you to manage attribute types and attribute instances.

## Overview

The Attributes API provides endpoints for:
- Managing attribute types (creating, updating, retrieving, deleting)
- Managing attributes (creating, updating, retrieving, deleting)
- Adding and removing values to/from attributes
- Finding attributes applicable to specific object types

## API Architecture

The Attributes API implements two approaches:

1. **Legacy Service-Based Approach**: Uses the original UnoObj pattern with services and endpoints
2. **Domain-Driven Design (DDD) Approach**: Uses domain entities, repositories, and schema managers

This documentation covers both approaches with a focus on the recommended DDD approach.

## Domain-Driven Design Approach

### Base URL

All DDD API endpoints are prefixed with `/api/v1`.

### Attribute Types Endpoints

#### Create Attribute Type

`POST /api/v1/attribute-types`

Creates a new attribute type with the specified properties.

**Request Body:**

```json
{
  "name": "color",
  "text": "Product Color",
  "required": true,
  "multiple_allowed": false,
  "comment_required": false,
  "display_with_objects": true
}
```

**Response:**

```json
{
  "id": "4f82-8c9d-a2b3",
  "name": "color",
  "text": "Product Color",
  "required": true,
  "multiple_allowed": false,
  "comment_required": false,
  "display_with_objects": true,
  "parent_id": null,
  "initial_comment": null,
  "description_limiting_query_id": null,
  "value_type_limiting_query_id": null,
  "group_id": null,
  "tenant_id": null
}
```

#### Get Attribute Type

`GET /api/v1/attribute-types/{id}`

Retrieves an attribute type by its ID.

**Response:**

```json
{
  "id": "4f82-8c9d-a2b3",
  "name": "color",
  "text": "Product Color",
  "required": true,
  "multiple_allowed": false,
  "comment_required": false,
  "display_with_objects": true,
  "parent_id": null,
  "initial_comment": null,
  "description_limiting_query_id": null,
  "value_type_limiting_query_id": null,
  "group_id": null,
  "tenant_id": null,
  "children": [],
  "describes": [
    {
      "id": "product",
      "name": "Product"
    }
  ],
  "value_types": [
    {
      "id": "text_value",
      "name": "Text Value"
    }
  ]
}
```

#### List Attribute Types

`GET /api/v1/attribute-types`

Lists all attribute types with optional filtering.

**Query Parameters:**

- `name` - Filter by name
- `required` - Filter by required flag (true/false)
- `multiple_allowed` - Filter by multiple_allowed flag (true/false)
- `page` - Page number (default: 1)
- `page_size` - Page size (default: 50)
- `fields` - Comma-separated list of fields to include

**Response:**

```json
[
  {
    "id": "4f82-8c9d-a2b3",
    "name": "color",
    "text": "Product Color",
    "required": true,
    "multiple_allowed": false,
    "comment_required": false,
    "display_with_objects": true
  },
  {
    "id": "7e21-5f4a-9c3b",
    "name": "size",
    "text": "Product Size",
    "required": true,
    "multiple_allowed": false,
    "comment_required": false,
    "display_with_objects": true
  }
]
```

#### Update Attribute Type

`PATCH /api/v1/attribute-types/{id}`

Updates an attribute type with the specified properties.

**Request Body:**

```json
{
  "text": "Updated Product Color",
  "required": false,
  "multiple_allowed": true
}
```

**Response:**

```json
{
  "id": "4f82-8c9d-a2b3",
  "name": "color",
  "text": "Updated Product Color",
  "required": false,
  "multiple_allowed": true,
  "comment_required": false,
  "display_with_objects": true,
  "parent_id": null,
  "initial_comment": null,
  "description_limiting_query_id": null,
  "value_type_limiting_query_id": null,
  "group_id": null,
  "tenant_id": null
}
```

#### Delete Attribute Type

`DELETE /api/v1/attribute-types/{id}`

Deletes an attribute type by its ID.

**Response:**

```json
{
  "status": "success",
  "message": "Attribute type deleted"
}
```

### Attributes Endpoints

#### Create Attribute

`POST /api/v1/attributes`

Creates a new attribute with the specified properties.

**Request Body:**

```json
{
  "attribute_type_id": "4f82-8c9d-a2b3",
  "comment": "This is a blue color variant",
  "follow_up_required": false
}
```

**Response:**

```json
{
  "id": "9a7b-6c5d-8e3f",
  "attribute_type_id": "4f82-8c9d-a2b3",
  "comment": "This is a blue color variant",
  "follow_up_required": false,
  "group_id": null,
  "tenant_id": null,
  "value_ids": [],
  "meta_record_ids": []
}
```

#### Get Attribute

`GET /api/v1/attributes/{id}`

Retrieves an attribute by its ID.

**Response:**

```json
{
  "id": "9a7b-6c5d-8e3f",
  "attribute_type_id": "4f82-8c9d-a2b3",
  "comment": "This is a blue color variant",
  "follow_up_required": false,
  "group_id": null,
  "tenant_id": null,
  "value_ids": ["val1", "val2"],
  "meta_record_ids": [],
  "attribute_type": {
    "id": "4f82-8c9d-a2b3",
    "name": "color",
    "text": "Product Color",
    "required": true,
    "multiple_allowed": false,
    "comment_required": false,
    "display_with_objects": true
  }
}
```

#### List Attributes

`GET /api/v1/attributes`

Lists all attributes with optional filtering.

**Query Parameters:**

- `attribute_type_id` - Filter by attribute type ID
- `follow_up_required` - Filter by follow_up_required flag (true/false)
- `page` - Page number (default: 1)
- `page_size` - Page size (default: 50)
- `fields` - Comma-separated list of fields to include

**Response:**

```json
[
  {
    "id": "9a7b-6c5d-8e3f",
    "attribute_type_id": "4f82-8c9d-a2b3",
    "comment": "This is a blue color variant",
    "follow_up_required": false
  },
  {
    "id": "2d4e-1f3c-5b6a",
    "attribute_type_id": "7e21-5f4a-9c3b",
    "comment": "Large size",
    "follow_up_required": false
  }
]
```

#### Update Attribute

`PATCH /api/v1/attributes/{id}`

Updates an attribute with the specified properties.

**Request Body:**

```json
{
  "comment": "Updated comment for blue color variant",
  "follow_up_required": true
}
```

**Response:**

```json
{
  "id": "9a7b-6c5d-8e3f",
  "attribute_type_id": "4f82-8c9d-a2b3",
  "comment": "Updated comment for blue color variant",
  "follow_up_required": true,
  "group_id": null,
  "tenant_id": null,
  "value_ids": ["val1", "val2"],
  "meta_record_ids": []
}
```

#### Delete Attribute

`DELETE /api/v1/attributes/{id}`

Deletes an attribute by its ID.

**Response:**

```json
{
  "status": "success",
  "message": "Attribute deleted"
}
```

#### Get Attribute Values

`GET /api/v1/attributes/{attribute_id}/values`

Gets all values associated with an attribute.

**Response:**

```json
[
  "val1",
  "val2"
]
```

### Error Handling

All endpoints use standardized error responses with the following format:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field1": "Error details for field1",
    "field2": "Error details for field2"
  }
}
```

Common error codes:

- `NOT_FOUND` - The requested resource was not found
- `VALIDATION_ERROR` - The request body failed validation
- `DUPLICATE_KEY` - A resource with the same key already exists
- `UNAUTHORIZED` - Authentication is required
- `FORBIDDEN` - The authenticated user does not have permission

## Legacy Approach

The legacy approach uses the original service-based pattern with the following endpoints:

### Legacy Attribute Types

```http
POST /attribute-types
GET /attribute-types/{attribute_type_id}
PATCH /attribute-types/{attribute_type_id}
POST /attribute-types/{attribute_type_id}/applicable-meta-types
POST /attribute-types/{attribute_type_id}/value-meta-types
GET /attribute-types/applicable-for/{meta_type_id}
DELETE /attribute-types/{attribute_type_id}
```

### Legacy Attributes

```http
POST /attributes
GET /attributes/{attribute_id}
PATCH /attributes/{attribute_id}
POST /attributes/{attribute_id}/values
DELETE /attributes/{attribute_id}/values
GET /attributes/by-record/{record_id}
DELETE /attributes/{attribute_id}
```

## Domain-Driven Design Components

This API implements domain-driven design principles with the following components:

1. **Domain Entities** - `Attribute` and `AttributeType` classes in `entities.py`
2. **Repositories** - `AttributeRepository` and `AttributeTypeRepository` for data access
3. **DTOs** - Data Transfer Objects defined in `dtos.py` for API serialization
4. **Schema Managers** - Convert between entities and DTOs in `schemas.py`
5. **Domain Services** - Encapsulate business logic in `domain_services.py`

## Integration

### Domain-Driven Integration

To use the DDD API in your FastAPI application:

```python
from fastapi import FastAPI
from uno.attributes.api_integration import register_domain_attribute_endpoints

app = FastAPI()

# Register attribute endpoints
endpoints = register_domain_attribute_endpoints(
    app_or_router=app,
    path_prefix="/api/v1",
    include_auth=True
)
```

### Legacy Integration

To integrate the legacy Attributes API into your FastAPI application:

```python
from fastapi import FastAPI, APIRouter
from uno.database.db_manager import DBManager
from uno.attributes import (
    AttributeRepository,
    AttributeTypeRepository,
    AttributeService,
    AttributeTypeService,
    register_attribute_endpoints
)

# Create FastAPI app
app = FastAPI()

# Create router
router = APIRouter()

# Create services
db_manager = DBManager()
attribute_repository = AttributeRepository(db_manager)
attribute_type_repository = AttributeTypeRepository(db_manager)
attribute_service = AttributeService(attribute_repository, attribute_type_repository, db_manager)
attribute_type_service = AttributeTypeService(attribute_type_repository, db_manager)

# Register endpoints
register_attribute_endpoints(
    router=router,
    attribute_service=attribute_service,
    attribute_type_service=attribute_type_service,
    attribute_prefix="/attributes",
    attribute_type_prefix="/attribute-types",
    attribute_tags=["Attributes"],
    attribute_type_tags=["Attribute Types"]
)

# Include router in app
app.include_router(router)
```