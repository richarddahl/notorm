# API Overview

The Uno framework provides a comprehensive API system that follows domain-driven design principles. It allows you to expose your domain entities via RESTful endpoints with minimal boilerplate code while maintaining clean separation of concerns.

## Domain-Driven Design Approach

Uno has fully adopted the domain-driven design pattern for all API endpoints. This modern approach:

1. Separates domain entities from API representation (DTOs)
2. Uses repositories for data access and persistence
3. Encapsulates business logic in domain services
4. Leverages dependency injection for loose coupling
5. Provides standardized endpoint creation with consistent patterns

### Key Components

- **Domain Entities**: Core business objects defined in `entities.py`
- **Domain Repositories**: Data access interfaces in `domain_repositories.py`
- **Domain Services**: Business logic in `domain_services.py`
- **DTOs**: Data Transfer Objects for API contracts
- **Domain Endpoints**: API endpoints in `domain_endpoints.py`
- **Domain Provider**: DI configuration in `domain_provider.py`

### Basic Example

```python
# Register domain-driven endpoints
from fastapi import FastAPI
from uno.attributes import register_attribute_routers

app = FastAPI()

# Register standardized attribute endpoints
register_attribute_routers(app)
```

### Custom Domain Endpoints

You can create custom endpoints using the domain_endpoint decorator:

```python
from fastapi import APIRouter, Depends, Path
from uno.domain.api_integration import domain_endpoint
from uno.dependencies.scoped_container import get_service
from uno.attributes.domain_services import AttributeService
from uno.attributes.entities import Attribute

# Create router
router = APIRouter(prefix="/api/attributes", tags=["Attributes"])

@router.get("/{id}/with-related")
@domain_endpoint(entity_type=Attribute, service_type=AttributeService)
async def get_attribute_with_related(
    id: str = Path(..., description="The ID of the attribute"),
    service: AttributeService = Depends(lambda: get_service(AttributeService))
):
    """Get an attribute with its related data."""
    result = await service.get_with_related_data(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()
```

### Domain Router Creation

Use the create_domain_router factory to generate standardized endpoints:

```python
from uno.domain.api_integration import create_domain_router
from uno.attributes.entities import Attribute
from uno.attributes.domain_services import AttributeService

# Create router with standardized endpoints
attribute_router = create_domain_router(
    entity_type=Attribute,
    service_type=AttributeService,
    prefix="/api/attributes",
    tags=["Attributes"],
)

# Include the router in your FastAPI app
app.include_router(attribute_router)
```

## Feature Overview

The API module provides:

1. **Standardized Endpoints**: Create, read, update, delete operations
2. **Pagination**: Support for paginated results with metadata
3. **Filtering**: Powerful filtering capabilities for list endpoints
4. **Field Selection**: Choose specific fields to return
5. **OpenAPI Documentation**: Automatic documentation generation
6. **Validation**: Input validation using Pydantic models
7. **Authorization**: Integrate with authentication and authorization systems
8. **Error Handling**: Standardized error responses

## Module-Specific API Endpoints

The Uno framework provides domain-driven API endpoints for each module:

| Module         | Base Endpoints                          | Key Functionality                            |
|----------------|----------------------------------------|---------------------------------------------|
| Attributes     | `/attributes`, `/attribute-types`      | Attribute definition and management          |
| Authorization  | `/users`, `/roles`, `/permissions`     | Role-based access control                    |
| Meta           | `/meta-types`, `/meta-records`         | Meta type management and metadata storage    |
| Values         | `/values`                              | Value storage and validation                 |
| Reports        | `/report-templates`, `/report-executions` | Report definition and execution            |
| Workflows      | `/workflows`, `/workflow-executions`   | Workflow definition and orchestration        |
| Queries        | `/queries`, `/query-results`           | Query execution and result handling          |
| Vector Search  | `/vector-indexes`, `/vectors`, `/search` | Vector storage and semantic search           |
| AI             | `/embeddings`, `/completions`          | AI-powered content generation                |

Each module follows the same consistent pattern for endpoint organization, making the API intuitive and easy to learn. For detailed documentation on each module's API endpoints, see the module-specific pages in this documentation.

## API Best Practices

1. **Use Domain-Driven Design**: Follow the DDD approach for clean architecture
2. **Proper Validation**: Validate inputs with proper DTOs
3. **Result Pattern**: Use the Result pattern for error handling
4. **Documentation**: Add detailed documentation with examples
5. **Versioning**: Use versioning for non-backward compatible changes
6. **Pagination**: Always paginate list endpoints
7. **Testing**: Write comprehensive tests for your API endpoints

## Related Documentation

- [Domain Endpoints](domain-endpoints.md): Comprehensive guide to domain-driven endpoints
- [Domain Integration](domain-integration.md): Detailed guide on domain-driven integration
- [Endpoint Factory](endpoint-factory.md): Guide to creating endpoints
- [Repository Adapter](repository-adapter.md): Guide to repository adapters

## Example App

Here's a complete example application using domain-driven design for API endpoints:

```python
from fastapi import FastAPI, APIRouter, HTTPException
from uno.domain.api_integration import create_domain_router
from uno.api.domain_repositories import ApiResourceRepository
from uno.api.domain_services import ApiResourceService
from uno.api.entities import ApiResource

# Create FastAPI app
app = FastAPI(title="Uno API Example")

# Create domain router for API resources
api_resource_router = create_domain_router(
    entity_type=ApiResource,
    service_type=ApiResourceService,
    prefix="/api/resources",
    tags=["API Resources"],
)

# Include the router in the app
app.include_router(api_resource_router)

# Add a custom endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```