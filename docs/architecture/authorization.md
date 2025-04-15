# Advanced Authorization

The uno framework provides a comprehensive authorization system that integrates with the service context to provide fine-grained access control. This system includes support for policy-based authorization, role-based access control (RBAC), and multi-tenant authorization.

## Overview

The advanced authorization system in uno consists of several components that work together to provide secure, flexible, and powerful access control:

1. **Authorization Policies**: Define rules for who can access what resources and actions
2. **Role-Based Access Control (RBAC)**: Manages users, roles, and permissions
3. **Multi-Tenant Authorization**: Isolates access control between tenants in a multi-tenant system
4. **Service Context Integration**: Connects authorization to the application service layer

These components provide a layered approach to authorization, allowing you to implement simple or sophisticated access control as needed.

## Authorization Policies

Authorization policies determine whether a user is allowed to perform an action on a resource based on the service context and the target object.

### Policy Types

The framework includes several built-in policy types:

- **SimplePolicy**: Checks only if the user has the required permission
- **OwnershipPolicy**: Checks if the user is the owner of the target entity
- **TenantPolicy**: Checks if the entity belongs to the user's tenant
- **FunctionPolicy**: Delegates to a custom function for authorization logic
- **CompositePolicy**: Combines multiple policies with AND/OR logic

### Implementing Policies

Policies are implemented as classes that inherit from `AuthorizationPolicy`:

```python
class CustomPolicy(AuthorizationPolicy[Product]):```

async def _authorize_internal(self, context: ServiceContext, target: Optional[Product] = None) -> bool:```

# Custom authorization logic
if not target:```

return False
```
``````

```
```

# Check if the product is active
if not target.active:```

return False
```
``````

```
```

# Only allow access to products with price < 1000
return target.price < 1000
```
```
```

### Using Policies

Policies are registered with an `AuthorizationService` and then applied to authorize requests:

```python
# Create and register policies
auth_service = get_authorization_service()
auth_service.register_policy(SimplePolicy("products", "read"))
auth_service.register_policy(OwnershipPolicy("products", "write", "owner_id"))

# Create a service context
context = ServiceContext(```

user_id="user1",
is_authenticated=True,
permissions=["products:read", "products:write"]
```
)

# Create a product
product = Product(```

id="prod-1",
name="Sample Product",
price=99.99,
owner_id="user1"
```
)

# Check authorization
can_read = await auth_service.authorize(context, "products", "read")
can_write = await auth_service.authorize(context, "products", "write", product)
```

## Role-Based Access Control (RBAC)

RBAC manages users, roles, and permissions, making it easier to assign and revoke permissions for groups of users.

### Core Components

- **Permission**: Represents a single permission in the format `resource:action`
- **Role**: A collection of permissions that can be assigned to users
- **User**: An identity with assigned roles and direct permissions
- **RbacService**: Service for managing users, roles, and permissions

### Permission Format

Permissions follow a `resource:action` format with support for wildcards:

- `products:read`: Permission to read products
- `products:*`: Permission for all product actions
- `*:read`: Permission to read any resource
- `*:*`: Permission for all resources and actions

### Implementing RBAC

```python
# Create RBAC service
rbac_service = get_rbac_service()

# Create roles
admin_role = rbac_service.create_role("admin", [```

"products:read", "products:write", "products:delete",
"orders:read", "orders:write", "orders:delete"
```
])

user_role = rbac_service.create_role("user", [```

"products:read",
"orders:read"
```
])

# Create users
admin_user = rbac_service.create_user("admin", ["admin"])
user1 = rbac_service.create_user("user1", ["user"])
user2 = rbac_service.create_user("user2", ["user"], ["orders:write"])  # User with extra permission

# Check permissions
has_permission = rbac_service.has_permission("user1", "products:read")  # True
can_write_orders = rbac_service.has_permission("user2", "orders:write")  # True

# Create service context
context = rbac_service.create_service_context("admin")
```

## Multi-Tenant Authorization

Multi-tenant authorization extends RBAC to support isolated tenants, each with their own users, roles, and permissions.

### Core Components

- **Tenant**: Represents a tenant in the system
- **TenantRbacService**: Extends RbacService to support tenant-specific users and roles
- **MultiTenantAuthorizationService**: Extends AuthorizationService to support tenant-specific policies

### Implementing Multi-Tenant Authorization

```python
# Get the multi-tenant authorization service
mt_auth_service = get_multi_tenant_auth_service()
tenant_rbac = mt_auth_service.rbac_service

# Create tenants
tenant1 = tenant_rbac.create_tenant("tenant1", "Tenant 1")
tenant2 = tenant_rbac.create_tenant("tenant2", "Tenant 2")

# Create global roles
tenant_rbac.create_role("global_admin", [```

"products:read", "products:write", "products:delete",
"tenants:read", "tenants:write", "users:*"
```
])

# Create tenant-specific roles
tenant_rbac.create_role("tenant_admin", [```

"products:read", "products:write", "products:delete"
```
], "tenant1")

tenant_rbac.create_role("tenant_user", [```

"products:read"
```
], "tenant1")

# Create global user (system admin)
tenant_rbac.create_user("global_admin", ["global_admin"])

# Create tenant-specific users
tenant_rbac.create_user("tenant1_admin", ["tenant_admin"], tenant_id="tenant1")
tenant_rbac.create_user("tenant1_user", ["tenant_user"], tenant_id="tenant1")

# Create multi-tenant user (user in both tenants)
tenant_rbac.create_user("multi_tenant_user", ["tenant_user"], tenant_id="tenant1")
tenant_rbac.add_user_to_tenant("multi_tenant_user", "tenant2", ["tenant_user"])

# Register tenant-specific policies
mt_auth_service.register_tenant_isolation_policy("products", "read", "tenant1")
mt_auth_service.register_tenant_isolation_policy("products", "write", "tenant1")

# Create service context for a tenant
context = tenant_rbac.create_service_context("tenant1_user", "tenant1")
```

## Integration with Service Context

The authorization system integrates with the service context to provide authorization for application services.

### Service Context Integration

```python
class ProductService(EntityService[Product]):```

def authorize_command(self, command: Command, context: ServiceContext) -> None:```

"""Authorize commands."""
# Require authentication
context.require_authentication()
``````

```
```

# Require permission
if isinstance(command, CreateEntityCommand):
    context.require_permission("products:write")
elif isinstance(command, UpdateEntityCommand):
    context.require_permission("products:write")
elif isinstance(command, DeleteEntityCommand):
    context.require_permission("products:delete")
```
``````

```
```

def authorize_query(self, query: Query, context: ServiceContext) -> None:```

"""Authorize queries."""
# Require authentication for all queries
context.require_authentication()
``````

```
```

# Require permission
if isinstance(query, EntityByIdQuery) or isinstance(query, EntityListQuery):
    context.require_permission("products:read")
```
``````

```
```

async def get_by_id(self, id: str, context: ServiceContext) -> QueryResult:```

"""Get a product by ID with authorization."""
# Execute the query
result = await super().get_by_id(id, context)
``````

```
```

# Check object-level permissions if result is successful
if result.is_success and result.output is not None:
    product = result.output
    
    # Get the authorization service
    auth_service = get_authorization_service()
    
    # Check if user can read this specific product
    authorized = await auth_service.authorize(
        context, "products", "read", product
    )
    
    if not authorized:
        return QueryResult.failure(
            query_id=str(uuid4()),
            query_type="EntityByIdQuery",
            error="Not authorized to read this product",
            error_code="AUTHORIZATION_ERROR"
        )
``````

```
```

return result
```
```
```

### Custom Context Provider

The service context can be populated with authorization information from RBAC:

```python
class RbacContextProvider(ContextProvider):```

def __init__(self, rbac_service: RbacService):```

self.rbac_service = rbac_service
```
``````

```
```

def _get_user_id(self, request: Request) -> Optional[str]:```

# Extract user ID from request (e.g., from token)
token = request.headers.get("Authorization", "").replace("Bearer ", "")
if token:
    return decode_jwt(token).get("sub")
return None
```
``````

```
```

def _get_permissions(self, request: Request) -> List[str]:```

# Get user ID
user_id = self._get_user_id(request)
if not user_id:
    return []
``````

```
```

# Get permissions from RBAC
return self.rbac_service.get_user_permissions(user_id)
```
```
```

## Advanced Usage

### Dynamic Policies

You can create policies dynamically based on configuration:

```python
def create_policy_from_config(config: Dict[str, Any]) -> AuthorizationPolicy:```

policy_type = config["type"]
resource = config["resource"]
action = config["action"]
``````

```
```

if policy_type == "simple":```

return SimplePolicy(resource, action)
```
elif policy_type == "ownership":```

return OwnershipPolicy(resource, action, config.get("owner_field", "owner_id"))
```
elif policy_type == "tenant":```

return TenantPolicy(resource, action, config.get("tenant_field", "tenant_id"))
```
elif policy_type == "function":```

# Load function from module
module_name, func_name = config["function"].rsplit(".", 1)
module = importlib.import_module(module_name)
func = getattr(module, func_name)
return FunctionPolicy(resource, action, func)
```
elif policy_type == "composite":```

sub_policies = [create_policy_from_config(p) for p in config["policies"]]
mode = CompositePolicy.CombinationMode.ALL
if config.get("mode") == "any":
    mode = CompositePolicy.CombinationMode.ANY
return CompositePolicy(resource, action, sub_policies, mode)
```
else:```

raise ValueError(f"Unknown policy type: {policy_type}")
```
```
```

### Custom Permission Evaluators

You can create custom permission evaluators for complex permission schemes:

```python
class RegexPermissionEvaluator:```

"""Permission evaluator that supports regex patterns."""
``````

```
```

def has_permission(self, required_permission: str, user_permissions: List[str]) -> bool:```

"""Check if the user has the required permission."""
# Check for direct match
if required_permission in user_permissions:
    return True
``````

```
```

# Check for wildcard matches
for user_permission in user_permissions:
    if self._matches_pattern(user_permission, required_permission):
        return True
``````

```
```

return False
```
``````

```
```

def _matches_pattern(self, pattern: str, permission: str) -> bool:
    """Check if a permission matches a pattern."""
    # Convert wildcard pattern to regex
    if "*" in pattern:
        regex_pattern = pattern.replace(".", "\\.").replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", permission))```

return False
```
```
```

### Hierarchical RBAC

You can implement hierarchical roles where roles inherit permissions from parent roles:

```python
class HierarchicalRole(Role):```

"""Role with hierarchical inheritance."""
``````

```
```

def __init__(self, name: str, permissions: Optional[List[Permission]] = None, parent_roles: Optional[List['HierarchicalRole']] = None):```

super().__init__(name, permissions)
self._parent_roles = parent_roles or []
```
``````

```
```

def has_permission(self, permission: Permission) -> bool:```

"""Check if this role has a permission, including inherited permissions."""
# Check own permissions
if super().has_permission(permission):
    return True
```
    ```

# Check parent roles' permissions
for parent in self._parent_roles:
    if parent.has_permission(permission):
        return True
``````

```
```

return False
```
```
```

## Best Practices

1. **Layer your authorization**: Use RBAC for coarse-grained access control and policies for fine-grained control
2. **Keep policies simple**: Each policy should have a single responsibility
3. **Use composite policies**: Combine policies for complex authorization scenarios
4. **Implement tenant isolation**: Always ensure data is isolated between tenants
5. **Test your policies**: Write unit tests for authorization policies
6. **Don't repeat yourself**: Use roles to group permissions that are frequently assigned together
7. **Be explicit**: Prefer explicit permission checks over implicit ones
8. **Document your permissions**: Keep a clear list of all permissions used in your system
9. **Audit authorization decisions**: Log important authorization decisions for security audits
10. **Default to deny**: Always default to denying access when authorization fails

## Conclusion

The Advanced Authorization system in uno provides a comprehensive solution for implementing fine-grained access control. By combining policy-based authorization, role-based access control, and multi-tenant support, you can create a secure and flexible authorization system for your application.

The integration with the service context ensures that authorization is consistently applied across your application, from the API layer through to the domain model. This layered approach to authorization allows you to implement both simple and sophisticated access control as needed.

By following the best practices and leveraging the provided components, you can create a secure authorization system that meets the needs of your application and protects your users' data.