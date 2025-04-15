# Authorization Overview

The authorization system in uno provides a comprehensive approach to user permissions, access control, and row-level security.

## Key Components

### User and Role Management

The authorization system includes a complete user and role management system:

```python
from uno.authorization.models import User, Role, Permission
from uno.authorization.objs import UserObj, RoleObj, PermissionObj

# Create a role
role = RoleObj(```

name="Admin",
description="Administrator role with full access"
```
)
await role.save()

# Create a permission
permission = PermissionObj(```

name="user:create",
description="Can create users"
```
)
await permission.save()

# Assign permission to role
role.permissions.append(permission)
await role.save()

# Create a user
user = UserObj(```

username="admin",
email="admin@example.com",
password="securepassword"  # Will be hashed automatically
```
)
await user.save()

# Assign role to user
user.roles.append(role)
await user.save()
```

### Permission Checking

The authorization system provides methods for checking permissions:

```python
from uno.authorization.objs import UserObj

# Get a user
user = await UserObj.get(username="admin")

# Check permissions
if await user.has_permission("user:create"):```

# Create a user...
pass
```
else:```

raise PermissionError("User does not have permission to create users")
```
```

### Row-Level Security

uno integrates with PostgreSQL's row-level security features:

```python
from uno.authorization.rlssql import RLSPolicy
from uno.sql.emitters.security import SecurityEmitter

# Define a row-level security policy
policy = RLSPolicy(```

table="customer",
policy_name="customer_access_policy",
using_expr="(user_id = current_user_id() OR is_public = true)",
check_expr="(user_id = current_user_id())"
```
)

# Generate SQL for the policy
emitter = SecurityEmitter(policy=policy)
sql = emitter.emit()

# Execute the SQL to create the policy
# (Implementation depends on your database setup)
```

## Integration with FastAPI

The authorization system integrates with FastAPI's dependency injection system:

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from uno.authorization.objs import UserObj

# Create a FastAPI app
app = FastAPI()

# Create OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get the current user
async def get_current_user(token: str = Depends(oauth2_scheme)):```

"""Get the current user from the token."""
# Validate token and get user
# (Implementation depends on your token system)
user = await UserObj.get_by_token(token)
if not user:```

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
```
return user
```

# Dependency to check permissions
def require_permission(permission: str):```

"""Require a specific permission."""
async def check_permission(user: UserObj = Depends(get_current_user)):```

if not await user.has_permission(permission):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Permission denied: {permission}"
    )
return user
```
return check_permission
```

# Example protected endpoint
@app.get("/api/v1/users")
async def list_users(user: UserObj = Depends(require_permission("user:list"))):```

"""List all users (requires permission)."""
# Implementation...
return []
```
```

## Best Practices

1. **Use Role-Based Access Control**: Assign permissions to roles, then assign roles to users.

2. **Implement Row-Level Security**: Use PostgreSQL's row-level security for data isolation.

3. **Validate Permissions**: Always validate permissions before performing protected operations.

4. **Use Secure Authentication**: Implement secure authentication with proper password hashing and token management.

5. **Apply Least Privilege**: Give users only the permissions they need to perform their tasks.

6. **Audit Access**: Log permission checks and access attempts for auditing purposes.

7. **Centralize Authorization Logic**: Keep authorization logic in one place for consistency.

8. **Test Permissions**: Write tests to verify that permissions are properly enforced.

9. **Document Permissions**: Document the available permissions and their purposes.

10. **Keep Permissions Fine-Grained**: Create specific permissions for different operations.