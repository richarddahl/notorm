# UnoEndpoint

The `UnoEndpoint` class is the base class for all API endpoints in the Uno framework. It provides a standardized way to expose business objects through a RESTful API.

## Overview

The UnoEndpoint class integrates with FastAPI to provide:

- RESTful API endpoints for business objects
- Request validation
- Response serialization
- Error handling
- Documentation

## Endpoint Types

The Uno framework provides several specialized endpoint types:

- **CreateEndpoint**: Creates new objects (POST method)
- **ViewEndpoint**: Retrieves a single object by ID (GET method)
- **ListEndpoint**: Lists objects with filtering, sorting, and pagination (GET method)
- **UpdateEndpoint**: Updates an existing object (PATCH method)
- **DeleteEndpoint**: Deletes an object (DELETE method)
- **ImportEndpoint**: Imports/bulk creates objects (PUT method)

## Basic Usage

Endpoints are typically created using the `UnoEndpointFactory`, but you can also create them manually:

```python
from uno.api.endpoint import ViewEndpoint, ListEndpoint
from fastapi import FastAPI

# Create a FastAPI app
app = FastAPI()

# Create a view endpoint for a Customer model
view_endpoint = ViewEndpoint(```

model=Customer,
app=app
```
)

# Create a list endpoint for a Customer model
list_endpoint = ListEndpoint(```

model=Customer,
app=app
```
)
```

## Configuration

Endpoints can be configured with various options:

```python
from uno.api.endpoint import CreateEndpoint
from fastapi import FastAPI, Depends

# Function for authorization
def get_current_user():```

# Implementation...
return {"id": "user123"}
```

# Create a FastAPI app
app = FastAPI()

# Create an endpoint with custom configuration
create_endpoint = CreateEndpoint(```

model=Customer,
app=app
```,```

path="/api/customers",  # Custom path
tags=["customers"],     # OpenAPI tags
dependencies=[Depends(get_current_user)],  # FastAPI dependencies
response_model_exclude={"password"},  # Fields to exclude from response
status_code=201  # Custom status code
```
)
```

## Customization

You can create custom endpoint classes by inheriting from `UnoEndpoint`:

```python
from uno.api.endpoint import UnoEndpoint
from fastapi import FastAPI, Request, Response

class ExportEndpoint(UnoEndpoint):```

"""Custom endpoint for exporting data."""
``````

```
```

def __init__(self, model, app, **kwargs):```

super().__init__(model, app, **kwargs)
``````

```
```

# Register the endpoint
@app.get(f"/api/v1/{self.model_name}/export", tags=self.tags)
async def export():
    """Export all data as CSV."""
    # Implementation...
    data = await self.model.filter(limit=1000)
    
    # Convert to CSV
    csv_data = self.to_csv(data)
    
    # Return as file download
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={self.model_name}.csv"}
    )
```
``````

```
```

def to_csv(self, data):```

"""Convert data to CSV format."""
# Implementation...
return "id,name,email\n" + "\n".join(
    [f"{item.id},{item.name},{item.email}" for item in data]
)
```
```
```

## Error Handling

Endpoints include standardized error handling:

```python
from uno.api.endpoint import UnoEndpoint
from fastapi import HTTPException, Request

class CustomEndpoint(UnoEndpoint):```

"""Custom endpoint with error handling."""
``````

```
```

def __init__(self, model, app, **kwargs):```

super().__init__(model, app, **kwargs)
``````

```
```

@app.get(f"/api/v1/{self.model_name}/custom")
async def custom_endpoint(request: Request):
    try:
        # Implementation...
        result = await self.perform_operation()
        return result
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle other errors
        self.logger.error(f"Error in custom endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```
``````

```
```

async def perform_operation(self):```

"""Perform the custom operation."""
# Implementation...
return {"status": "success"}
```
```
```

## Best Practices

1. **Use EndpointFactory**: Use the `UnoEndpointFactory` to create endpoints whenever possible, as it ensures consistency across your API.

2. **Document Endpoints**: Add proper documentation to your endpoints to make them easier to use.

3. **Handle Errors**: Implement proper error handling to provide meaningful error messages.

4. **Validate Input**: Use Pydantic models to validate input data before processing.

5. **Secure Endpoints**: Add authentication and authorization to protect your endpoints.

6. **Use Pagination**: Always paginate list endpoints to avoid performance issues.

7. **Use Consistent Paths**: Follow RESTful conventions for endpoint paths.

8. **Add Tags**: Use tags to organize endpoints in the documentation.

9. **Test Thoroughly**: Test endpoints with various inputs, including edge cases.

10. **Monitor Performance**: Track endpoint performance to identify bottlenecks.