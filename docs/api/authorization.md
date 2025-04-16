# Authorization API Reference

This document provides a comprehensive reference for the Authorization API endpoints, following the domain-driven design approach. It includes detailed information about request and response formats, authentication requirements, and integration examples.

## Overview

The Authorization module provides a robust system for user management, role-based access control, and multi-tenant isolation. It follows domain-driven design principles with a clean separation of:

- **Domain Entities**: Core business objects like User, Group, Role, and Permission
- **DTOs**: Data Transfer Objects for API requests and responses
- **Schema Managers**: Convert between domain entities and DTOs
- **API Integration**: Register standardized API endpoints

## Base URL

All API endpoints are prefixed with `/api/v1/`.

## Authentication

All API endpoints require authentication using a valid JWT token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## User Management

### List Users

Retrieves a paginated list of users with optional filtering.

**Endpoint:** `GET /api/v1/users`  
**Query Parameters:**
- `email`: Filter by email (exact match)
- `email_contains`: Filter by email (contains)
- `handle`: Filter by handle (exact match)
- `handle_contains`: Filter by handle (contains)
- `full_name_contains`: Filter by full name (contains)
- `is_superuser`: Filter by superuser status (true/false)
- `tenant_id`: Filter by tenant ID
- `group_id`: Filter by group membership
- `role_id`: Filter by role assignment
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of users
```json
{
  "items": [
    {
      "id": "user_12345abcde",
      "email": "john.doe@example.com",
      "handle": "johndoe",
      "full_name": "John Doe",
      "is_superuser": false,
      "tenant_id": "tenant_12345abcde",
      "default_group_id": "group_12345abcde",
      "created_at": "2025-04-01T12:00:00.000Z",
      "updated_at": "2025-04-16T14:30:22.123Z",
      "group_ids": ["group_12345abcde", "group_67890fghij"],
      "role_ids": ["role_12345abcde", "role_67890fghij"]
    },
    // More users...
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### Get User

Retrieves a specific user by ID.

**Endpoint:** `GET /api/v1/users/{user_id}`  
**Path Parameters:**
- `user_id`: The ID of the user to retrieve

**Response:** User details
```json
{
  "id": "user_12345abcde",
  "email": "john.doe@example.com",
  "handle": "johndoe",
  "full_name": "John Doe",
  "is_superuser": false,
  "tenant_id": "tenant_12345abcde",
  "default_group_id": "group_12345abcde",
  "created_at": "2025-04-01T12:00:00.000Z",
  "updated_at": "2025-04-16T14:30:22.123Z",
  "group_ids": ["group_12345abcde", "group_67890fghij"],
  "role_ids": ["role_12345abcde", "role_67890fghij"]
}
```

### Create User

Creates a new user.

**Endpoint:** `POST /api/v1/users`  
**Request Body:** User creation data
```json
{
  "email": "jane.smith@example.com",
  "handle": "janesmith",
  "full_name": "Jane Smith",
  "is_superuser": false,
  "tenant_id": "tenant_12345abcde",
  "default_group_id": "group_12345abcde",
  "password": "securepassword"
}
```

**Response:** Created user
```json
{
  "id": "user_67890fghij",
  "email": "jane.smith@example.com",
  "handle": "janesmith",
  "full_name": "Jane Smith",
  "is_superuser": false,
  "tenant_id": "tenant_12345abcde",
  "default_group_id": "group_12345abcde",
  "created_at": "2025-04-16T15:45:30.789Z",
  "updated_at": "2025-04-16T15:45:30.789Z",
  "group_ids": ["group_12345abcde"],
  "role_ids": []
}
```

### Update User

Updates an existing user.

**Endpoint:** `PATCH /api/v1/users/{user_id}`  
**Path Parameters:**
- `user_id`: The ID of the user to update

**Request Body:** User update data (all fields optional)
```json
{
  "email": "jane.updated@example.com",
  "full_name": "Jane Updated Smith"
}
```

**Response:** Updated user (same structure as Get User)

### Delete User

Deletes an existing user.

**Endpoint:** `DELETE /api/v1/users/{user_id}`  
**Path Parameters:**
- `user_id`: The ID of the user to delete

**Response:** No content (204)

## Group Management

### List Groups

Retrieves a paginated list of groups with optional filtering.

**Endpoint:** `GET /api/v1/groups`  
**Query Parameters:**
- `name`: Filter by name (exact match)
- `name_contains`: Filter by name (contains)
- `tenant_id`: Filter by tenant ID
- `user_id`: Filter by user membership
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of groups
```json
{
  "items": [
    {
      "id": "group_12345abcde",
      "name": "Administrators",
      "tenant_id": "tenant_12345abcde",
      "created_at": "2025-04-01T12:00:00.000Z",
      "updated_at": "2025-04-16T14:30:22.123Z",
      "user_ids": ["user_12345abcde", "user_67890fghij"]
    },
    // More groups...
  ],
  "total": 8,
  "limit": 50,
  "offset": 0
}
```

### Get Group

Retrieves a specific group by ID.

**Endpoint:** `GET /api/v1/groups/{group_id}`  
**Path Parameters:**
- `group_id`: The ID of the group to retrieve

**Response:** Group details
```json
{
  "id": "group_12345abcde",
  "name": "Administrators",
  "tenant_id": "tenant_12345abcde",
  "created_at": "2025-04-01T12:00:00.000Z",
  "updated_at": "2025-04-16T14:30:22.123Z",
  "user_ids": ["user_12345abcde", "user_67890fghij"]
}
```

### Create Group

Creates a new group.

**Endpoint:** `POST /api/v1/groups`  
**Request Body:** Group creation data
```json
{
  "name": "Marketing Team",
  "tenant_id": "tenant_12345abcde",
  "user_ids": ["user_12345abcde", "user_67890fghij"]
}
```

**Response:** Created group
```json
{
  "id": "group_abcde12345",
  "name": "Marketing Team",
  "tenant_id": "tenant_12345abcde",
  "created_at": "2025-04-16T15:45:30.789Z",
  "updated_at": "2025-04-16T15:45:30.789Z",
  "user_ids": ["user_12345abcde", "user_67890fghij"]
}
```

### Update Group

Updates an existing group.

**Endpoint:** `PATCH /api/v1/groups/{group_id}`  
**Path Parameters:**
- `group_id`: The ID of the group to update

**Request Body:** Group update data
```json
{
  "name": "Marketing Department"
}
```

**Response:** Updated group (same structure as Get Group)

### Delete Group

Deletes an existing group.

**Endpoint:** `DELETE /api/v1/groups/{group_id}`  
**Path Parameters:**
- `group_id`: The ID of the group to delete

**Response:** No content (204)

## Role Management

### List Roles

Retrieves a paginated list of roles with optional filtering.

**Endpoint:** `GET /api/v1/roles`  
**Query Parameters:**
- `name`: Filter by name (exact match)
- `name_contains`: Filter by name (contains)
- `description_contains`: Filter by description (contains)
- `tenant_id`: Filter by tenant ID
- `responsibility_role_id`: Filter by responsibility role ID
- `user_id`: Filter by user assignment
- `permission_id`: Filter by permission ID
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of roles
```json
{
  "items": [
    {
      "id": "role_12345abcde",
      "name": "Product Manager",
      "description": "Manages product catalog and inventory",
      "tenant_id": "tenant_12345abcde",
      "responsibility_role_id": "resp_12345abcde",
      "created_at": "2025-04-01T12:00:00.000Z",
      "updated_at": "2025-04-16T14:30:22.123Z",
      "permission_ids": [1, 2, 3, 4],
      "user_ids": ["user_12345abcde", "user_67890fghij"]
    },
    // More roles...
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

### Get Role

Retrieves a specific role by ID.

**Endpoint:** `GET /api/v1/roles/{role_id}`  
**Path Parameters:**
- `role_id`: The ID of the role to retrieve

**Response:** Role details
```json
{
  "id": "role_12345abcde",
  "name": "Product Manager",
  "description": "Manages product catalog and inventory",
  "tenant_id": "tenant_12345abcde",
  "responsibility_role_id": "resp_12345abcde",
  "created_at": "2025-04-01T12:00:00.000Z",
  "updated_at": "2025-04-16T14:30:22.123Z",
  "permission_ids": [1, 2, 3, 4],
  "user_ids": ["user_12345abcde", "user_67890fghij"]
}
```

### Create Role

Creates a new role.

**Endpoint:** `POST /api/v1/roles`  
**Request Body:** Role creation data
```json
{
  "name": "Marketing Manager",
  "description": "Manages marketing campaigns and content",
  "tenant_id": "tenant_12345abcde",
  "responsibility_role_id": "resp_67890fghij",
  "permission_ids": [5, 6, 7],
  "user_ids": ["user_abcde12345"]
}
```

**Response:** Created role
```json
{
  "id": "role_fghij67890",
  "name": "Marketing Manager",
  "description": "Manages marketing campaigns and content",
  "tenant_id": "tenant_12345abcde",
  "responsibility_role_id": "resp_67890fghij",
  "created_at": "2025-04-16T15:45:30.789Z",
  "updated_at": "2025-04-16T15:45:30.789Z",
  "permission_ids": [5, 6, 7],
  "user_ids": ["user_abcde12345"]
}
```

### Update Role

Updates an existing role.

**Endpoint:** `PATCH /api/v1/roles/{role_id}`  
**Path Parameters:**
- `role_id`: The ID of the role to update

**Request Body:** Role update data (all fields optional)
```json
{
  "description": "Manages marketing campaigns, content, and social media"
}
```

**Response:** Updated role (same structure as Get Role)

### Delete Role

Deletes an existing role.

**Endpoint:** `DELETE /api/v1/roles/{role_id}`  
**Path Parameters:**
- `role_id`: The ID of the role to delete

**Response:** No content (204)

## Responsibility Role Management

### List Responsibility Roles

Retrieves a paginated list of responsibility roles with optional filtering.

**Endpoint:** `GET /api/v1/responsibility-roles`  
**Query Parameters:**
- `name`: Filter by name (exact match)
- `name_contains`: Filter by name (contains)
- `description_contains`: Filter by description (contains)
- `tenant_id`: Filter by tenant ID
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of responsibility roles
```json
{
  "items": [
    {
      "id": "resp_12345abcde",
      "name": "Product Management",
      "description": "Responsible for product catalog and inventory",
      "tenant_id": "tenant_12345abcde",
      "created_at": "2025-04-01T12:00:00.000Z",
      "updated_at": "2025-04-16T14:30:22.123Z"
    },
    // More responsibility roles...
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

### Get Responsibility Role

Retrieves a specific responsibility role by ID.

**Endpoint:** `GET /api/v1/responsibility-roles/{role_id}`  
**Path Parameters:**
- `role_id`: The ID of the responsibility role to retrieve

**Response:** Responsibility role details
```json
{
  "id": "resp_12345abcde",
  "name": "Product Management",
  "description": "Responsible for product catalog and inventory",
  "tenant_id": "tenant_12345abcde",
  "created_at": "2025-04-01T12:00:00.000Z",
  "updated_at": "2025-04-16T14:30:22.123Z"
}
```

### Create Responsibility Role

Creates a new responsibility role.

**Endpoint:** `POST /api/v1/responsibility-roles`  
**Request Body:** Responsibility role creation data
```json
{
  "name": "Customer Support",
  "description": "Handles customer inquiries and issue resolution",
  "tenant_id": "tenant_12345abcde"
}
```

**Response:** Created responsibility role
```json
{
  "id": "resp_fghij67890",
  "name": "Customer Support",
  "description": "Handles customer inquiries and issue resolution",
  "tenant_id": "tenant_12345abcde",
  "created_at": "2025-04-16T15:45:30.789Z",
  "updated_at": "2025-04-16T15:45:30.789Z"
}
```

### Update Responsibility Role

Updates an existing responsibility role.

**Endpoint:** `PATCH /api/v1/responsibility-roles/{role_id}`  
**Path Parameters:**
- `role_id`: The ID of the responsibility role to update

**Request Body:** Responsibility role update data (all fields optional)
```json
{
  "description": "Handles customer inquiries, issue resolution, and feedback"
}
```

**Response:** Updated responsibility role (same structure as Get Responsibility Role)

### Delete Responsibility Role

Deletes an existing responsibility role.

**Endpoint:** `DELETE /api/v1/responsibility-roles/{role_id}`  
**Path Parameters:**
- `role_id`: The ID of the responsibility role to delete

**Response:** No content (204)

## Permission Management

### List Permissions

Retrieves a paginated list of permissions with optional filtering.

**Endpoint:** `GET /api/v1/permissions`  
**Query Parameters:**
- `meta_type_id`: Filter by meta type ID
- `operation`: Filter by operation (SELECT, INSERT, UPDATE, DELETE)
- `role_id`: Filter by role assignment
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of permissions
```json
{
  "items": [
    {
      "id": 1,
      "meta_type_id": "product",
      "operation": "SELECT",
      "role_ids": ["role_12345abcde", "role_67890fghij"]
    },
    // More permissions...
  ],
  "total": 32,
  "limit": 50,
  "offset": 0
}
```

### Get Permission

Retrieves a specific permission by ID.

**Endpoint:** `GET /api/v1/permissions/{permission_id}`  
**Path Parameters:**
- `permission_id`: The ID of the permission to retrieve

**Response:** Permission details
```json
{
  "id": 1,
  "meta_type_id": "product",
  "operation": "SELECT",
  "role_ids": ["role_12345abcde", "role_67890fghij"]
}
```

### Create Permission

Creates a new permission.

**Endpoint:** `POST /api/v1/permissions`  
**Request Body:** Permission creation data
```json
{
  "meta_type_id": "order",
  "operation": "INSERT"
}
```

**Response:** Created permission
```json
{
  "id": 33,
  "meta_type_id": "order",
  "operation": "INSERT",
  "role_ids": []
}
```

### Delete Permission

Deletes an existing permission.

**Endpoint:** `DELETE /api/v1/permissions/{permission_id}`  
**Path Parameters:**
- `permission_id`: The ID of the permission to delete

**Response:** No content (204)

## Tenant Management

### List Tenants

Retrieves a paginated list of tenants with optional filtering.

**Endpoint:** `GET /api/v1/tenants`  
**Query Parameters:**
- `name`: Filter by name (exact match)
- `name_contains`: Filter by name (contains)
- `tenant_type`: Filter by tenant type (INDIVIDUAL, ORGANIZATION)
- `limit` (default=50): Maximum number of results to return
- `offset` (default=0): Number of results to skip

**Response:** Paginated list of tenants
```json
{
  "items": [
    {
      "id": "tenant_12345abcde",
      "name": "Acme Corporation",
      "tenant_type": "ORGANIZATION",
      "created_at": "2025-04-01T12:00:00.000Z",
      "updated_at": "2025-04-16T14:30:22.123Z",
      "user_count": 42,
      "group_count": 8,
      "role_count": 15
    },
    // More tenants...
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

### Get Tenant

Retrieves a specific tenant by ID.

**Endpoint:** `GET /api/v1/tenants/{tenant_id}`  
**Path Parameters:**
- `tenant_id`: The ID of the tenant to retrieve

**Response:** Tenant details
```json
{
  "id": "tenant_12345abcde",
  "name": "Acme Corporation",
  "tenant_type": "ORGANIZATION",
  "created_at": "2025-04-01T12:00:00.000Z",
  "updated_at": "2025-04-16T14:30:22.123Z",
  "user_count": 42,
  "group_count": 8,
  "role_count": 15
}
```

### Create Tenant

Creates a new tenant.

**Endpoint:** `POST /api/v1/tenants`  
**Request Body:** Tenant creation data
```json
{
  "name": "Globex Corporation",
  "tenant_type": "ORGANIZATION"
}
```

**Response:** Created tenant
```json
{
  "id": "tenant_fghij67890",
  "name": "Globex Corporation",
  "tenant_type": "ORGANIZATION",
  "created_at": "2025-04-16T15:45:30.789Z",
  "updated_at": "2025-04-16T15:45:30.789Z",
  "user_count": 0,
  "group_count": 0,
  "role_count": 0
}
```

### Update Tenant

Updates an existing tenant.

**Endpoint:** `PATCH /api/v1/tenants/{tenant_id}`  
**Path Parameters:**
- `tenant_id`: The ID of the tenant to update

**Request Body:** Tenant update data (all fields optional)
```json
{
  "name": "Globex International Corporation"
}
```

**Response:** Updated tenant (same structure as Get Tenant)

### Delete Tenant

Deletes an existing tenant.

**Endpoint:** `DELETE /api/v1/tenants/{tenant_id}`  
**Path Parameters:**
- `tenant_id`: The ID of the tenant to delete

**Response:** No content (204)

## Error Handling

The API follows standard HTTP status codes for errors with a consistent response format:

```json
{
  "status_code": 404,
  "error": "NOT_FOUND",
  "message": "User with ID user_12345abcde not found",
  "details": {
    "resource_type": "user",
    "resource_id": "user_12345abcde"
  },
  "timestamp": "2025-04-16T15:45:30.789Z"
}
```

Common status codes:

- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate email)
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

## Integration Examples

### Register All Authorization Endpoints

The authorization module provides a convenience function to register all endpoints:

```python
from fastapi import FastAPI
from uno.authorization import register_authorization_endpoints

app = FastAPI()

# Register all authorization endpoints
endpoints = register_authorization_endpoints(
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
from uno.authorization import (
    register_user_endpoints, 
    register_role_endpoints
)

app = FastAPI()

# Create a router
auth_router = APIRouter(prefix="/api/v1")

# Register only user and role endpoints
user_endpoints = register_user_endpoints(
    app_or_router=auth_router,
    path_prefix="",
    dependencies=[Depends(authenticate_user)]
)

role_endpoints = register_role_endpoints(
    app_or_router=auth_router,
    path_prefix="",
    dependencies=[Depends(authenticate_user)]
)

# Include the router in the app
app.include_router(auth_router)
```

### Using Schema Managers Directly

You can use schema managers to convert between domain entities and DTOs:

```python
from uno.authorization import (
    User, UserViewDto, UserSchemaManager
)

# Create a schema manager
schema_manager = UserSchemaManager()

# Get a user entity from the repository
user = await user_repository.get_by_id("user_12345abcde")

# Convert the entity to a DTO
user_dto = schema_manager.entity_to_dto(user)

# Return the DTO in an API response
return user_dto
```

## Related Resources

- [API Overview](overview.md): Overview of the API system
- [Endpoint Factory](endpoint-factory.md): Automatic endpoint generation
- [Domain Integration](domain-integration.md): Using domain repositories with endpoints