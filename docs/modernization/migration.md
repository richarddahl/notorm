# Migrating to the Modern Uno Framework

This guide provides step-by-step instructions for migrating existing applications to the modern Uno framework. The migration process is designed to be gradual, allowing you to adopt the new features at your own pace.

## Migration Strategy

The migration strategy focuses on:

1. **Incremental Adoption**: Migrate one component at a time
2. **Backward Compatibility**: Old and new approaches work side by side
3. **Clear Benefits**: Each step provides tangible benefits
4. **Low Risk**: Minimize disruption to existing applications

## Migration Steps

### Step 1: Update Dependencies

First, update to the latest version of the Uno framework:

```bash
pip install --upgrade uno
```

### Step 2: Configure Modern Dependency Injection

Update your application startup code to use the modern dependency injection system:

```python
# Before
from uno.dependencies.container import configure_di
import inject

def configure_dependencies():
    def config(binder):
        binder.bind(ConfigService, ConfigService())
        binder.bind(DatabaseService, DatabaseService())
        binder.bind(UserService, UserService())
    
    inject.configure(config)
    
# After
from uno.dependencies.modern_provider import get_service_provider
from uno.dependencies.scoped_container import ServiceCollection

async def configure_dependencies():
    # Create a service collection
    services = ServiceCollection()
    
    # Register services
    services.add_singleton(ConfigService)
    services.add_singleton(DatabaseService)
    services.add_singleton(UserService)
    
    # Configure the service provider
    provider = get_service_provider()
    provider.configure_services(services)
    
    # Initialize the service provider
    await provider.initialize()
```

Update your application shutdown code:

```python
# Before
# No explicit shutdown code

# After
from uno.dependencies.modern_provider import get_service_provider, shutdown_services

async def shutdown_application():
    await shutdown_services()
```

### Step 3: Use Dependency Injection Decorators

Replace manual dependency resolution with decorators:

```python
# Before
class UserService:
    def __init__(self):
        self.config = inject.instance(ConfigService)
        self.database = inject.instance(DatabaseService)
    
    def get_user(self, user_id):
        # Implementation...

# After
from uno.dependencies.decorators import singleton, inject_params

@singleton
class UserService:
    def __init__(self, config: ConfigService, database: DatabaseService):
        self.config = config
        self.database = database
    
    def get_user(self, user_id):
        # Implementation...
```

### Step 4: Update FastAPI Integration

Update your FastAPI endpoints to use the modern dependency injection:

```python
# Before
from fastapi import Depends
from uno.dependencies.fastapi import get_config, get_database

@app.get("/users/{user_id}")
async def get_user(user_id: str, config = Depends(get_config), db = Depends(get_database)):
    # Implementation...

# After
from uno.dependencies.decorators import inject_params
from uno.dependencies.fastapi_integration import DIAPIRouter

router = DIAPIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
@inject_params()
async def get_user(user_id: str, config: ConfigService, database: DatabaseService):
    # Implementation...

app.include_router(router)
```

### Step 5: Implement the Result Pattern

Replace exception-based error handling with the Result pattern:

```python
# Before
class UserService:
    def get_user(self, user_id):
        try:
            user = self.database.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User not found: {user_id}")
            return user
        except Exception as e:
            raise ApplicationError(f"Error getting user: {e}")

# After
from uno.core import Success, Failure, Result

class UserService:
    def get_user(self, user_id) -> Result[User]:
        try:
            user = self.database.query(User).filter(User.id == user_id).first()
            if not user:
                return Failure(ValueError(f"User not found: {user_id}"))
            return Success(user)
        except Exception as e:
            return Failure(ApplicationError(f"Error getting user: {e}"))
```

Update your API endpoints to handle Result objects:

```python
# Before
@router.get("/{user_id}")
async def get_user(user_id: str, user_service: UserService):
    try:
        user = user_service.get_user(user_id)
        return user.to_dict()
    except ValueError as e:
        return {"error": str(e)}, 404
    except ApplicationError as e:
        return {"error": str(e)}, 500

# After
@router.get("/{user_id}")
async def get_user(user_id: str, user_service: UserService):
    result = user_service.get_user(user_id)
    
    if result.is_success:
        return result.value.to_dict()
    elif isinstance(result.error, ValueError):
        return {"error": str(result.error)}, 404
    else:
        return {"error": str(result.error)}, 500
```

### Step 6: Migrate to Domain-Driven Design

Start migrating your business objects to domain entities and aggregates:

```python
# Before
from uno.obj import UnoObj

class UserObj(UnoObj):
    id: str
    email: str
    handle: str
    full_name: str
    
    def validate_email(self):
        if "@" not in self.email:
            raise ValueError("Invalid email format")

# After
from uno.core import AggregateEntity, BaseDomainEvent

class UserCreatedEvent(BaseDomainEvent):
    user_id: str
    email: str
    
    @property
    def aggregate_id(self) -> str:
        return self.user_id

class User(AggregateEntity[str]):
    def __init__(self, id: str, email: str, handle: str, full_name: str):
        super().__init__(id=id)
        self.email = email
        self.handle = handle
        self.full_name = full_name
    
    def validate_email(self) -> bool:
        return "@" in self.email
    
    @classmethod
    def create(cls, id: str, email: str, handle: str, full_name: str) -> "User":
        user = cls(id, email, handle, full_name)
        if not user.validate_email():
            raise ValueError("Invalid email format")
        
        # Register a domain event
        user.register_event(UserCreatedEvent(
            user_id=id,
            email=email
        ))
        
        return user
```

### Step 7: Implement Repositories

Create repositories for your domain entities:

```python
from uno.core import Repository, AbstractUnitOfWork

class UserRepository(Repository[User, str]):
    def __init__(self, db_session):
        self.db_session = db_session
        self._events = []
    
    async def get(self, id: str) -> Optional[User]:
        query = "SELECT id, email, handle, full_name FROM users WHERE id = $1"
        row = await self.db_session.fetchrow(query, id)
        if not row:
            return None
        
        return User(
            id=row["id"],
            email=row["email"],
            handle=row["handle"],
            full_name=row["full_name"]
        )
    
    async def save(self, user: User) -> None:
        # Collect events from the aggregate
        self._events.extend(user.clear_events())
        
        # Check if user exists
        exists = await self.exists(user.id)
        
        if exists:
            # Update
            query = """
            UPDATE users
            SET email = $1, handle = $2, full_name = $3
            WHERE id = $4
            """
            await self.db_session.execute(
                query,
                user.email,
                user.handle,
                user.full_name,
                user.id
            )
        else:
            # Insert
            query = """
            INSERT INTO users (id, email, handle, full_name)
            VALUES ($1, $2, $3, $4)
            """
            await self.db_session.execute(
                query,
                user.id,
                user.email,
                user.handle,
                user.full_name
            )
    
    async def delete(self, id: str) -> bool:
        query = "DELETE FROM users WHERE id = $1"
        result = await self.db_session.execute(query, id)
        return result == "DELETE 1"
    
    async def exists(self, id: str) -> bool:
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)"
        return await self.db_session.fetchval(query, id)
    
    def collect_events(self) -> List[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events
```

### Step 8: Implement Unit of Work

Create a unit of work for transaction management:

```python
from uno.core import DatabaseUnitOfWork

class ApplicationUnitOfWork(DatabaseUnitOfWork):
    def __init__(self, connection_factory, event_bus = None):
        super().__init__(connection_factory, event_bus)
        
        # Register repositories
        self.register_repository(UserRepository, UserRepository(self._connection))
        # Register other repositories...
```

Update your services to use the unit of work:

```python
@singleton
class UserService:
    def __init__(self, uow: ApplicationUnitOfWork):
        self.uow = uow
    
    async def create_user(self, email: str, handle: str, full_name: str) -> Result[User]:
        try:
            # Create user
            user_id = generate_id()
            user = User.create(
                id=user_id,
                email=email,
                handle=handle,
                full_name=full_name
            )
            
            # Use unit of work to manage transaction
            async with self.uow:
                user_repo = self.uow.get_repository(UserRepository)
                await user_repo.save(user)
            
            return Success(user)
        except Exception as e:
            return Failure(e)
```

### Step 9: Implement CQRS

Separate command and query responsibilities:

```python
from uno.core import BaseCommand, BaseCommandHandler, command_handler

# Command
class CreateUserCommand(BaseCommand):
    email: str
    handle: str
    full_name: str

# Command handler
@singleton
@command_handler(CreateUserCommand)
class CreateUserCommandHandler(BaseCommandHandler[CreateUserCommand, User]):
    def __init__(self, uow: ApplicationUnitOfWork):
        self.uow = uow
    
    async def handle(self, command: CreateUserCommand) -> Result[User]:
        try:
            # Create user
            user_id = generate_id()
            user = User.create(
                id=user_id,
                email=command.email,
                handle=command.handle,
                full_name=command.full_name
            )
            
            # Use unit of work to manage transaction
            async with self.uow:
                user_repo = self.uow.get_repository(UserRepository)
                await user_repo.save(user)
            
            return Success(user)
        except Exception as e:
            return Failure(e)

# Query
class GetUserQuery(BaseQuery):
    user_id: str

# Query handler
@singleton
@query_handler(GetUserQuery)
class GetUserQueryHandler(BaseQueryHandler[GetUserQuery, User]):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def handle(self, query: GetUserQuery) -> Result[User]:
        try:
            user = await self.user_repository.get(query.user_id)
            if not user:
                return Failure(ValueError(f"User not found: {query.user_id}"))
            return Success(user)
        except Exception as e:
            return Failure(e)
```

Update your API endpoints to use the command and query buses:

```python
@router.post("/")
@inject_params()
async def create_user(
    data: Dict[str, Any] = Body(...),
    command_bus: CommandBus = None
):
    command = CreateUserCommand(
        email=data["email"],
        handle=data["handle"],
        full_name=data["full_name"]
    )
    
    result = await command_bus.dispatch(command)
    
    if result.is_success:
        user = result.value
        return {"id": user.id, "email": user.email}
    else:
        return {"error": str(result.error)}, 400

@router.get("/{user_id}")
@inject_params()
async def get_user(
    user_id: str = Path(...),
    query_bus: QueryBus = None
):
    query = GetUserQuery(user_id=user_id)
    
    result = await query_bus.dispatch(query)
    
    if result.is_success:
        user = result.value
        return {
            "id": user.id,
            "email": user.email,
            "handle": user.handle,
            "full_name": user.full_name
        }
    elif isinstance(result.error, ValueError):
        return {"error": str(result.error)}, 404
    else:
        return {"error": str(result.error)}, 500
```

### Step 10: Implement Event Handlers

Create event handlers for your domain events:

```python
from uno.core import event_handler, DomainEventProcessor

class UserEventProcessor(DomainEventProcessor):
    def __init__(self, event_bus: EventBus, email_service: EmailService):
        super().__init__(event_bus)
        self.email_service = email_service
    
    @event_handler(UserCreatedEvent)
    async def handle_user_created(self, event: UserCreatedEvent):
        # Send welcome email
        await self.email_service.send_email(
            to=event.email,
            subject="Welcome to our platform",
            body=f"Thank you for signing up! Your account ID is {event.user_id}."
        )
```

Register the event processor:

```python
# In your dependency configuration
services.add_singleton(UserEventProcessor)
```

## Migration Checklist

Use this checklist to track your migration progress:

- [ ] Update to the latest Uno framework version
- [ ] Configure modern dependency injection
- [ ] Use dependency injection decorators
- [ ] Update FastAPI integration
- [ ] Implement the Result pattern
- [ ] Migrate to domain-driven design
- [ ] Implement repositories
- [ ] Implement unit of work
- [ ] Implement CQRS
- [ ] Implement event handlers

## Troubleshooting

### Dependency Injection Issues

If you encounter issues with dependency injection:

1. Ensure that services are registered with the correct scope
2. Check for circular dependencies
3. Use `@inject_params()` correctly on functions and methods
4. Verify that the service provider is initialized before use

### Repository Issues

If you encounter issues with repositories:

1. Ensure that repositories are registered with the unit of work
2. Check that the unit of work has access to the correct database connection
3. Verify that repositories implement the Repository protocol correctly

### Event Handling Issues

If you encounter issues with event handling:

1. Ensure that event handlers are registered with the event bus
2. Check that events are being properly registered with aggregates
3. Verify that events are being published after successful transactions

## Conclusion

By following this migration guide, you can gradually adopt the modern features of the Uno framework while maintaining compatibility with existing code. Each step provides tangible benefits, and you can adopt the steps at your own pace.

If you encounter any issues during the migration, please refer to the troubleshooting section or file an issue on GitHub.