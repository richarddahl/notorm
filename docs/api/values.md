# Values API

This document provides an overview of the Values API, which allows you to manage different types of values used throughout the system, particularly as attribute values.

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

Request body:
```json
{
  "value_type": "text",
  "value": "Example value",
  "name": "Example Text"
}
```

Example variations for different types:

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

```http
POST /values/get-or-create
```

Request body:
```json
{
  "value_type": "text",
  "value": "Example value",
  "name": "Example Text"
}
```

### Get Value by ID

```http
GET /values/{value_type}/{value_id}
```

For example:
```http
GET /values/text/01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

### Upload Attachment

```http
POST /values/attachments
```

Use a multipart form with:
- `file`: The file to upload
- `name`: Name of the attachment

### Download Attachment

```http
GET /values/attachments/{attachment_id}/download
```

### Delete Value

```http
DELETE /values/{value_type}/{value_id}
```

For example:
```http
DELETE /values/text/01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

### Search Values

```http
GET /values/{value_type}/search?term={search_term}&limit={limit}
```

Parameters:
- `term`: The search term
- `limit`: Maximum number of results (default: 20)

For example:
```http
GET /values/text/search?term=example&limit=10
```

## Integration

To integrate the Values API into your FastAPI application:

```python
from fastapi import FastAPI, APIRouter
from uno.database.db_manager import DBManager
from uno.values import (```

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
```
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
value_service = ValueService(```

boolean_repository=boolean_repository,
text_repository=text_repository,
integer_repository=integer_repository,
decimal_repository=decimal_repository,
date_repository=date_repository,
datetime_repository=datetime_repository,
time_repository=time_repository,
attachment_repository=attachment_repository,
db_manager=db_manager
```
)

# Register endpoints
register_value_endpoints(```

router=router,
value_service=value_service,
prefix="/values",
tags=["Values"]
```
)

# Include router in app
app.include_router(router)
```