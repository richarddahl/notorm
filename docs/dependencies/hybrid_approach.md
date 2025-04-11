# Hybrid Architecture: Combining UnoObj with Dependency Injection

Uno supports a hybrid architecture that combines the simplicity of UnoObj with the flexibility of dependency injection. This guide explains how to effectively use both patterns together.

The latest enhancements to Uno's architecture include a unified database layer that works seamlessly with both patterns, making it easier than ever to adopt a hybrid approach.

## When to Use Each Pattern

### Use UnoObj When:

- Building standard CRUD operations
- Dealing with simple business logic
- Rapid development is a priority
- Schema generation is needed
- Auto-endpoint generation is sufficient

### Use Dependency Injection When:

- Implementing complex business logic
- Creating custom queries beyond basic CRUD
- Writing unit tests with mock dependencies
- Building performance-critical components
- Working with multiple interrelated services

## Integration Patterns

### Pattern 1: UnoObj as Data Transfer Object

UnoObj can serve as a rich data transfer object with built-in validation:

```python
# Repository
class UserRepository(UnoRepository[UserModel]):
    async def create_with_validation(self, data: dict) -> UserModel:
        # Use UnoObj for validation
        user_obj = User(**data)
        # Save using the repository pattern
        return await self.create(user_obj.model_dump())

# Service
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
        
    async def register_user(self, data: dict) -> UserModel:
        return await self.repository.create_with_validation(data)
```

### Pattern 2: Service Delegation

Services can delegate to UnoObj for certain operations:

```python
class ComplexService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def perform_complex_operation(self, user_id: str) -> Result:
        # Get user via repository
        user_model = await self.repository.get(user_id)
        
        # Use UnoObj for a specific operation
        user_obj = User(**user_model.dict())
        result = await user_obj.some_specialized_operation()
        
        # Continue with repository
        await self.repository.update(user_id, {"result": result})
        return result
```

### Pattern 3: Repository Composition

Repositories can use UnoObj internally:

```python
class EnhancedUserRepository(UnoRepository[UserModel]):
    async def find_with_specialized_logic(self, criteria: dict) -> List[UserModel]:
        # Use UnoObj's filter capabilities which might be complex
        user_obj = User()
        filtered_models = await user_obj.filter(criteria)
        
        # Apply additional repository logic
        return [model for model in filtered_models if self._additional_filter(model)]
```

### Pattern 4: Schema Reuse

Reuse UnoObj's schema capabilities:

```python
# Get schema from UnoObj
user_schema = User.schema_manager.get_schema("view_schema")

# Use in FastAPI endpoint with DI
@router.post("/users", response_model=user_schema)
async def create_user(
    data: user_schema,
    repository: UserRepository = Depends(get_repository(UserRepository))
):
    service = UserService(repository)
    return await service.create_user(data.model_dump())
```

## Best Practices

### 1. Clear Boundaries

Establish clear boundaries between code using each pattern:

```python
# Module using UnoObj pattern
from uno.obj import UnoObj

class SimpleEntity(UnoObj[SimpleModel]):
    # Standard UnoObj implementation
    pass

# Module using DI pattern
from uno.dependencies.repository import UnoRepository

class ComplexRepository(UnoRepository[ComplexModel]):
    # Repository implementation
    pass
```

### 2. Consistent Naming

Use consistent naming to distinguish between patterns:

- `EntityObj` - Classes using UnoObj pattern
- `EntityRepository` - Repository classes
- `EntityService` - Service classes

### 3. Documentation

Document which pattern is used for each component:

```python
"""
User management module.

This module uses:
- UnoObj for validation and simple operations
- Dependency Injection for complex business logic
"""
```

### 4. Testing Strategy

Adopt different testing strategies for each pattern:

```python
# Testing UnoObj
async def test_user_obj():
    user = User(name="Test", email="test@example.com")
    await user.save()
    assert user.id is not None

# Testing DI components
async def test_user_service():
    mock_repo = MockRepository.create()
    service = UserService(repository=mock_repo)
    await service.create_user({"name": "Test"})
    mock_repo.create.assert_called_once()
```

## Unified Database Architecture

The new database architecture in Uno is designed to work seamlessly with both UnoObj and dependency injection patterns, providing a consistent interface regardless of which pattern you choose.

### Key Components

- **DatabaseProvider**: Central connection manager for both patterns
- **UnoBaseRepository**: Repository pattern implementation
- **SchemaManager**: DDL and schema management for both patterns

### Example: DatabaseProvider with Both Patterns

```python
# Configure the DatabaseProvider
from uno.database.provider import DatabaseProvider
from uno.database.config import ConnectionConfig
from uno.dependencies.container import get_instance, UnoDatabaseProviderProtocol

# The provider is configured once and used by both patterns
db_provider = DatabaseProvider(
    ConnectionConfig(
        host="localhost", 
        port=5432, 
        user="postgres", 
        password="password", 
        database="mydb"
    )
)

# Use with UnoObj pattern
class User(UnoObj[UserModel]):
    @classmethod
    async def get_by_id(cls, id: str) -> Optional["User"]:
        async with db_provider.async_session() as session:
            stmt = select(cls.model).where(cls.model.id == id)
            result = await session.execute(stmt)
            model = result.scalars().first()
            if not model:
                return None
            return cls.from_model(model)

# Use with DI pattern
class UserRepository(UnoBaseRepository[UserModel]):
    async def find_by_email(self, email: str) -> Optional[UserModel]:
        stmt = select(self.model_class).where(self.model_class.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
```

## Example: Complete Hybrid Implementation

Here's a complete example showing both patterns working together with the new database architecture:

```python
# UnoObj implementation
class User(UnoObj[UserModel]):
    model = UserModel
    # Standard fields and methods
    
    async def validate_email(self) -> bool:
        # Complex validation logic
        return True

# Repository implementation
class UserRepository(UnoBaseRepository[UserModel]):
    async def find_by_email(self, email: str) -> Optional[UserModel]:
        stmt = select(self.model_class).where(self.model_class.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()

# Service using both
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def register_user(self, data: dict) -> UserModel:
        # Use UnoObj for validation
        user_obj = User(**data)
        if not await user_obj.validate_email():
            raise ValueError("Invalid email")
        
        # Use repository for persistence
        return await self.repository.create(user_obj.model_dump())
    
    async def find_users(self, criteria: dict) -> List[UserModel]:
        # Complex query using repository
        if "email" in criteria:
            return [await self.repository.find_by_email(criteria["email"])]
        return await self.repository.list(filters=criteria)

# API endpoint using DI
@router.post("/users")
async def create_user(
    data: UserCreateSchema,
    service: UserService = Depends(get_user_service)
):
    return await service.register_user(data.model_dump())

# Helper function to get UserService
def get_user_service(
    repository: UserRepository = Depends(get_repository(UserRepository))
) -> UserService:
    return UserService(repository)
```

## Migration Strategy

When migrating from pure UnoObj to the hybrid approach:

1. Start by integrating the new database architecture components:
   - Add `DatabaseProvider` to your dependency injection container
   - Configure the `SchemaManager` for schema operations
   - Create base repositories for your core domain models

2. Gradually migrate in this order:
   - Start with repositories for complex domains
   - Add services for business logic
   - Leave simple CRUD operations using UnoObj initially
   - Create integration points between patterns
   - Update endpoints to use the new components

3. Use the unified database layer:
   - Replace direct UnoDB usage with `UnoBaseRepository`
   - Use the `DatabaseProvider` for database connections
   - Leverage the `SchemaManager` for schema operations

4. Apply the hybrid pattern:
   - Use UnoObj for validation and data transfer
   - Use repositories for data access
   - Use services for business logic
   - Connect all components through dependency injection

This strategy allows for incremental adoption without disrupting existing functionality, leveraging the new unified database architecture as a bridge between patterns.

## Conclusion

The hybrid approach combines the best of both worlds: the rapid development of UnoObj with the flexibility and testability of dependency injection. By using each pattern where it makes the most sense, you can build applications that are both quick to develop and easy to maintain.

With the new unified database architecture, Uno offers a seamless way to adopt modern application patterns while preserving compatibility with existing code. The `DatabaseProvider`, `UnoBaseRepository`, and `SchemaManager` components provide a clean, testable foundation for both patterns, making it easier than ever to build maintainable, high-performance applications with Uno.