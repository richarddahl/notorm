# Values API

This document provides an overview of the Values API, which allows you to manage different types of values used throughout the system, particularly as attribute values.

## API Architecture

The Values API implements two approaches:

1. **Legacy Service-Based Approach**: Uses the original service pattern with value services and endpoints
2. **Domain-Driven Design (DDD) Approach**: Uses domain entities, repositories, and schema managers

Both approaches provide the same functionality but follow different architectural patterns.

## Overview

The Values API provides endpoints for:
- Creating values of different types (boolean, text, integer, decimal, date, datetime, time)
- Getting or creating values (to avoid duplicates)
- Retrieving values by ID
- Uploading and downloading file attachments
- Deleting values
- Searching for values

## Value Types

The system supports the following value types:
- `boolean`: True/False values
- `integer`: Whole number values
- `text`: String text values
- `decimal`: Decimal/floating point values
- `date`: Date values (YYYY-MM-DD)
- `datetime`: Date and time values (ISO format)
- `time`: Time values (HH:MM:SS)
- `attachment`: File attachments

## Value Operations

### Create Value

```http
POST /values
```

Legacy approach request body:
```json
{
  "value_type": "text",
  "value": "Example value",
  "name": "Example Text"
}
```

DDD approach request body (for text values):
```json
{
  "value": "Example value",
  "name": "Example Text"
}
```

Example variations for different types in the legacy approach:

```json
{
  "value_type": "boolean",
  "value": true,
  "name": "Boolean Example"
}
```

```json
{
  "value_type": "integer",
  "value": 42,
  "name": "Integer Example"
}
```

```json
{
  "value_type": "decimal",
  "value": 3.14159,
  "name": "Decimal Example"
}
```

```json
{
  "value_type": "date",
  "value": "2023-01-15",
  "name": "Date Example"
}
```

```json
{
  "value_type": "datetime",
  "value": "2023-01-15T14:30:15",
  "name": "DateTime Example"
}
```

```json
{
  "value_type": "time",
  "value": "14:30:15",
  "name": "Time Example"
}
```

### Get or Create Value

Legacy approach:
```http
POST /values/get-or-create
```

DDD approach:
```http
POST /api/v1/values/get-or-create
```

Request body (legacy approach):
```json
{
  "value_type": "text",
  "value": "Example value",
  "name": "Example Text"
}
```

### Get Value by ID

Legacy approach:
```http
GET /values/{value_type}/{value_id}
```

DDD approach:
```http
GET /api/v1/values/{value_type}/{value_id}
```

For example:
```http
GET /values/text/01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

### Upload Attachment

Legacy approach:
```http
POST /values/attachments
```

DDD approach:
```http
POST /api/v1/values/attachments/upload
```

Use a multipart form with:
- `file`: The file to upload
- `name`: Name of the attachment

### Download Attachment

Legacy approach:
```http
GET /values/attachments/{attachment_id}/download
```

DDD approach:
```http
GET /api/v1/values/attachments/{attachment_id}/download
```

### Delete Value

Legacy approach:
```http
DELETE /values/{value_type}/{value_id}
```

DDD approach:
```http
DELETE /api/v1/values/{value_type}/{value_id}
```

For example:
```http
DELETE /values/text/01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

### Search Values

Legacy approach:
```http
GET /values/{value_type}/search?term={search_term}&limit={limit}
```

DDD approach:
```http
GET /api/v1/values/{value_type}/search?term={search_term}&limit={limit}
```

Parameters:
- `term`: The search term
- `limit`: Maximum number of results (default: 20)

For example:
```http
GET /values/text/search?term=example&limit=10
```

## Integration

### Legacy Service-Based Approach

To integrate the legacy Values API into your FastAPI application:

```python
from fastapi import FastAPI, APIRouter
from uno.database.db_manager import DBManager
from uno.values import (
    AttachmentRepository,
    BooleanValueRepository,
    DateTimeValueRepository,
    DateValueRepository,
    DecimalValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    TimeValueRepository,
    ValueService,
    register_value_endpoints,
)

# Create FastAPI app
app = FastAPI()

# Create router
router = APIRouter()

# Create repositories
db_manager = DBManager()
boolean_repository = BooleanValueRepository(db_manager)
text_repository = TextValueRepository(db_manager)
integer_repository = IntegerValueRepository(db_manager)
decimal_repository = DecimalValueRepository(db_manager)
date_repository = DateValueRepository(db_manager)
datetime_repository = DateTimeValueRepository(db_manager)
time_repository = TimeValueRepository(db_manager)
attachment_repository = AttachmentRepository(db_manager)

# Create service
value_service = ValueService(
    boolean_repository=boolean_repository,
    text_repository=text_repository,
    integer_repository=integer_repository,
    decimal_repository=decimal_repository,
    date_repository=date_repository,
    datetime_repository=datetime_repository,
    time_repository=time_repository,
    attachment_repository=attachment_repository,
    db_manager=db_manager
)

# Register endpoints
register_value_endpoints(
    router=router,
    value_service=value_service,
    prefix="/values",
    tags=["Values"]
)

# Include router in app
app.include_router(router)
```

### Domain-Driven Design Approach

To integrate the DDD Values API into your FastAPI application:

```python
from fastapi import FastAPI
from uno.values import (
    # Repositories
    AttachmentRepository,
    BooleanValueRepository,
    DateTimeValueRepository,
    DateValueRepository,
    DecimalValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    TimeValueRepository,
    
    # Domain-driven API integration
    register_domain_value_endpoints_api,
)

# Create FastAPI app
app = FastAPI()

# Register domain-driven endpoints
endpoints = register_domain_value_endpoints_api(
    app_or_router=app,
    path_prefix="/api/v1",
    dependencies=None,
    include_auth=True,
    # Optionally provide custom repositories
    # boolean_repository=custom_boolean_repository,
    # text_repository=custom_text_repository,
    # etc.
)
```

## Domain-Driven Design Components

The DDD approach uses the following components:

### Domain Entities

The module provides the following domain entities:

- `BaseValue`: Abstract base class for all value types
- `BooleanValue`: Entity for boolean values
- `IntegerValue`: Entity for integer values
- `TextValue`: Entity for text values
- `DecimalValue`: Entity for decimal values
- `DateValue`: Entity for date values
- `DateTimeValue`: Entity for datetime values
- `TimeValue`: Entity for time values
- `Attachment`: Entity for file attachments

### Data Transfer Objects (DTOs)

The module provides DTOs for serialization/deserialization:

- `ValueBaseDto`: Base DTO for all value types
- `ValueResponseDto`: Base response DTO for all value types
- `CreateValueDto`: DTO for creating a value with any type
- `UpdateValueDto`: DTO for updating a value of any type
- Type-specific DTOs (e.g., `BooleanValueViewDto`, `TextValueCreateDto`, etc.)

### Schema Managers

The module provides schema managers for entity-DTO conversion:

- `BaseValueSchemaManager`: Base schema manager for all value types
- Type-specific schema managers (e.g., `BooleanValueSchemaManager`, `TextValueSchemaManager`, etc.)
- `ValueSchemaManagerFactory`: Factory for creating the appropriate schema manager based on value type

### Repositories

The module provides repositories for persistence:

- Type-specific repositories (e.g., `BooleanValueRepository`, `TextValueRepository`, etc.)

### API Integration

Two approaches for API integration:

- `register_value_endpoints`: Legacy service-based approach
- `register_domain_value_endpoints_api`: Domain-driven design approach