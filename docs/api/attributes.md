# Attributes API

This document provides an overview of the Attributes API, which allows you to manage attribute types and attribute instances.

## Overview

The Attributes API provides endpoints for:
- Managing attribute types (creating, updating, retrieving, deleting)
- Managing attributes (creating, updating, retrieving, deleting)
- Adding and removing values to/from attributes
- Finding attributes applicable to specific object types

## Attribute Types

Attribute types define the structure and constraints for attributes. They specify what types of objects can have the attribute, what types of values the attribute can have, and other constraints.

### Create Attribute Type

```http
POST /attribute-types
```

Request body:
```json
{
  "name": "Priority",
  "text": "What is the priority of this item?",
  "required": true,
  "multiple_allowed": false,
  "comment_required": false,
  "display_with_objects": true,
  "meta_type_ids": ["01H3ZEVKY6ZH3F41K5GS77PJ1Z"],
  "value_type_ids": ["01H3ZEVKY9PDSF51K5HS77PJ2A"]
}
```

### Get Attribute Type

```http
GET /attribute-types/{attribute_type_id}
```

### Update Attribute Type

```http
PATCH /attribute-types/{attribute_type_id}
```

Request body:
```json
{
  "name": "Updated Priority",
  "text": "What is the priority level of this item?",
  "required": true,
  "multiple_allowed": true
}
```

### Update Applicable Meta Types

```http
POST /attribute-types/{attribute_type_id}/applicable-meta-types
```

Request body:
```json
["01H3ZEVKY6ZH3F41K5GS77PJ1Z", "01H3ZEVKY9PDSF51K5HS77PJ2A"]
```

### Update Value Meta Types

```http
POST /attribute-types/{attribute_type_id}/value-meta-types
```

Request body:
```json
["01H3ZEVKY6ZH3F41K5GS77PJ1Z", "01H3ZEVKY9PDSF51K5HS77PJ2A"]
```

### Get Applicable Attribute Types

```http
GET /attribute-types/applicable-for/{meta_type_id}
```

### Delete Attribute Type

```http
DELETE /attribute-types/{attribute_type_id}
```

## Attributes

Attributes are instances of attribute types that can be associated with objects and have values.

### Create Attribute

```http
POST /attributes
```

Request body:
```json
{
  "attribute_type_id": "01H3ZEVKXN7PQWGW5KVS77PJ0Y",
  "comment": "This is a test attribute",
  "follow_up_required": false,
  "value_ids": ["01H3ZEVKY6ZH3F41K5GS77PJ1Z", "01H3ZEVKY9PDSF51K5HS77PJ2A"]
}
```

### Get Attribute

```http
GET /attributes/{attribute_id}
```

### Update Attribute

```http
PATCH /attributes/{attribute_id}
```

Request body:
```json
{
  "comment": "Updated comment",
  "follow_up_required": true,
  "value_ids": ["01H3ZEVKY6ZH3F41K5GS77PJ1Z"]
}
```

### Add Values to Attribute

```http
POST /attributes/{attribute_id}/values
```

Request body:
```json
["01H3ZEVKY6ZH3F41K5GS77PJ1Z", "01H3ZEVKY9PDSF51K5HS77PJ2A"]
```

### Remove Values from Attribute

```http
DELETE /attributes/{attribute_id}/values
```

Request body:
```json
["01H3ZEVKY6ZH3F41K5GS77PJ1Z", "01H3ZEVKY9PDSF51K5HS77PJ2A"]
```

### Get Attributes for Record

```http
GET /attributes/by-record/{record_id}
```

Query parameters:
- `include_values`: Whether to include attribute values (default: true)

### Delete Attribute

```http
DELETE /attributes/{attribute_id}
```

## Integration

To integrate the Attributes API into your FastAPI application:

```python
from fastapi import FastAPI, APIRouter
from uno.database.db_manager import DBManager
from uno.attributes import (
    AttributeRepository,
    AttributeTypeRepository,
    AttributeService,
    AttributeTypeService,
    register_attribute_endpoints,
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