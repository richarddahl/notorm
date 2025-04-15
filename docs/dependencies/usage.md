# Using Dependency Injection in uno

uno now supports two approaches to building API endpoints:

1. The traditional UnoObj approach
2. The new dependency injection pattern

This guide explains how to use both approaches and when to choose each one.

## UnoObj Approach

The UnoObj approach is the original pattern used in uno. It combines model representation and business logic in a single class:

```python
from uno.obj import UnoObj
from myapp.models import UserModel

class User(UnoObj[UserModel]):```

model = UserModel
endpoints = ["Create", "View", "List", "Update", "Delete"]
``````

```
```

# Fields from model
id: Optional[str] = None
name: str = None
email: str = None
``````

```
```

# Business logic methods
async def validate_email(self) -> bool:```

# Implementation...
pass
```
```
```

The UnoObj approach automatically:
- Registers with UnoRegistry
- Creates schemas
- Sets up FastAPI endpoints
- Manages database access

## Dependency Injection Approach

The dependency injection approach separates concerns into repositories, services, and API endpoints:

```python
# Repository
from uno.dependencies.repository import UnoRepository
from myapp.models import UserModel

class UserRepository(UnoRepository[UserModel]):```

async def find_by_email(self, email: str) -> Optional[UserModel]:```

stmt = select(self.model_class).where(self.model_class.email == email)
result = await self.session.execute(stmt)
return result.scalars().first()
```
```

# Service
from uno.dependencies.service import UnoService
from uno.dependencies.interfaces import UnoRepositoryProtocol

class UserService(UnoService[UserModel, List[UserModel]]):```

def __init__(self, repository: UnoRepositoryProtocol[UserModel]):```

super().__init__(repository)
```
``````

```
```

async def execute(self, email: Optional[str] = None) -> List[UserModel]:```

if email and hasattr(self.repository, 'find_by_email'):
    user = await self.repository.find_by_email(email)
    return [user] if user else []
return await self.repository.list()
```
```

# API Endpoint
from fastapi import APIRouter, Depends
from uno.dependencies.fastapi import get_db_session, get_repository

router = APIRouter()

@router.get("/users")
async def list_users(```

email: Optional[str] = None,
repository: UserRepository = Depends(get_repository(UserRepository))
```
):```

service = UserService(repository)
users = await service.execute(email=email)
return {"items": users}
```
```

The dependency injection approach offers:
- Clear separation of concerns
- Better testability
- More explicit dependencies
- More control over database queries

## Choosing Between Approaches

Consider the UnoObj approach when:
- You need rapid development with minimal boilerplate
- You want automatic endpoint generation
- Your requirements fit the standard CRUD operations

Consider the dependency injection approach when:
- You need more control over database queries
- You want better testability
- You have complex business logic
- You want clearer separation of concerns

## Integrating Both Approaches

You can use both approaches in the same application. For example:

```python
# In main.py
from myapp.users.endpoints import router as users_router
app.include_router(users_router)

# The rest of the application uses UnoObj
for obj_name, obj in registry.get_all().items():```

if hasattr(obj, "configure"):```

obj.configure(app)
```
```
```

See the `authorization/endpoints.py` module for a complete example of using the dependency injection approach alongside the UnoObj pattern.