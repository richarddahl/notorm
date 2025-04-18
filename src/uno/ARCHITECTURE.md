# Uno Framework Architecture

This document provides an overview of the Uno framework's architecture, including its directory structure, key components, and class hierarchies.

## Directory Structure

The Uno framework follows a layered architecture based on Clean Architecture principles:

```
/uno/
  ├── core/            # Core layer: framework fundamentals, no external dependencies
  │   ├── base/        # Base classes and protocols used throughout the framework
  │   ├── errors/      # Error handling system
  │   ├── async/       # Asynchronous utilities
  │   ├── di/          # Dependency injection tools
  │   └── ...
  │
  ├── domain/          # Domain layer: business logic and domain models
  │   ├── base/        # Base domain models and entities
  │   ├── protocols/   # Domain-related protocols
  │   └── ...
  │
  ├── application/     # Application layer: application services and use cases
  │   ├── dto/         # Data Transfer Objects
  │   ├── workflows/   # Business workflows
  │   ├── queries/     # Query handling
  │   └── ...
  │
  ├── infrastructure/  # Infrastructure layer: external dependencies implementations
  │   ├── repositories/# Data storage implementations
  │   ├── services/    # External service implementations
  │   └── ...
  │
  └── api/             # API layer: endpoints and controllers
      ├── endpoints/   # API endpoints
      ├── schemas/     # API request/response schemas
      └── ...
```

## Core Components

### Base Classes

The core/base directory contains fundamental interfaces and base classes that are used throughout the framework:

```
/uno/core/base/
  ├── dto.py          # BaseDTO and related classes
  ├── repository.py   # BaseRepository and repository protocols
  └── ...
```

These base classes provide consistent abstractions that the rest of the framework builds upon.

## Class Hierarchies

### Repository Pattern

The repository pattern is implemented with a clear hierarchy of abstractions:

```
BaseRepository[T, ID]
  ├── SpecificationRepository[T, ID]
  ├── BatchRepository[T, ID]
  ├── StreamingRepository[T, ID]
  ├── EventCollectingRepository[T, ID]
  │   └── AggregateRepository[A, ID]
  └── CompleteRepository[T, ID]
```

Concrete implementations include:

```
SQLAlchemyRepository[T, ID, M]
  ├── SQLAlchemySpecificationRepository[T, ID, M]
  ├── SQLAlchemyBatchRepository[T, ID, M]
  ├── SQLAlchemyStreamingRepository[T, ID, M]
  ├── SQLAlchemyEventCollectingRepository[T, ID, M]
  │   └── SQLAlchemyAggregateRepository[A, ID, M]
  └── SQLAlchemyCompleteRepository[T, ID, M]

InMemoryRepository[T, ID]
  ├── InMemorySpecificationRepository[T, ID]
  ├── InMemoryBatchRepository[T, ID]
  ├── InMemoryStreamingRepository[T, ID]
  ├── InMemoryEventCollectingRepository[T, ID]
  │   └── InMemoryAggregateRepository[A, ID]
  └── InMemoryCompleteRepository[T, ID]
```

### Data Transfer Objects (DTOs)

```
BaseDTO
  ├── PaginatedListDTO[T]
  ├── WithMetadataDTO[T]
  └── [Domain-specific DTOs]
```

### Domain Models

```
BaseModel
  ├── [Domain-specific models]
  ├── Entity
  │   └── AggregateRoot
  └── ValueObject
```

## Repository System

The repository system provides a flexible way to interact with data storage:

1. **Protocols**: Core interfaces that define expected behavior
2. **Base Classes**: Abstract implementations that provide common functionality
3. **Concrete Implementations**: SQL, In-Memory, or other storage-specific implementations
4. **Factory**: Creates appropriate repository instances based on context
5. **Unit of Work**: Manages transactions across multiple repositories

### Repository Features

Different repository implementations provide various features:

- **Basic Repository**: CRUD operations (get, list, add, update, delete)
- **Specification Repository**: Query using the Specification pattern
- **Batch Repository**: Batch operations (add_many, update_many, delete_many)
- **Streaming Repository**: Stream large result sets with async iterators
- **Event Collecting Repository**: Collect domain events from entities
- **Aggregate Repository**: Specialized handling for aggregate roots with event collection and versioning

## Dependency Injection

The framework uses a dependency injection system for managing dependencies:

1. **Core DI**: Basic dependency injection tools
2. **Service Provider**: Registers and resolves dependencies
3. **Scoped Container**: Manages lifecycle of dependencies
4. **FastAPI Integration**: Integrates with FastAPI's dependency system

## Error Handling

The error handling system provides:

1. **UnoError Base Class**: Common base for all framework errors
2. **Result Pattern**: Functional approach to error handling with Success/Failure objects
3. **Error Context**: Detailed error information for debugging
4. **Error Catalog**: Structured error definitions
5. **FastAPI Integration**: Error handlers for API endpoints

## Asynchronous Support

The framework is designed for asynchronous operation:

1. **Async Context**: Context management for async operations
2. **Task Management**: Utilities for managing async tasks
3. **AsyncSession**: Asynchronous database sessions

## Naming Conventions

The framework follows consistent naming conventions:

- **Files**: snake_case (e.g., `repository.py`, `dto_manager.py`)
- **Classes**: PascalCase (e.g., `BaseRepository`, `SQLAlchemyRepository`)
- **Functions/Methods**: snake_case (e.g., `get_repository`, `create_unit_of_work`)
- **Variables**: snake_case (e.g., `entity_type`, `specification_translator`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_BATCH_SIZE`, `MAX_RETRY_COUNT`)
- **Protocols/Interfaces**: PascalCase with "Protocol" suffix (e.g., `RepositoryProtocol`, `UnitOfWorkProtocol`)

## Working with Repositories

### Creating a Repository

```python
# Using the factory
repository = create_repository(
    entity_type=User,
    session=session,
    model_class=UserModel,
    include_specification=True
)

# Using DI
repository = await get_repository(
    entity_type=User,
    include_batch=True
)
```

### Using a Repository

```python
# Basic CRUD
user = await repository.get(user_id)
users = await repository.list(filters={"status": "active"})
new_user = await repository.add(user)
updated_user = await repository.update(user)
await repository.delete(user)

# Specification pattern
active_users = await spec_repository.find(
    UserSpecifications.is_active()
)

# Batch operations
new_users = await batch_repository.add_many([user1, user2, user3])

# Streaming
async for user in streaming_repository.stream(
    filters={"department": "engineering"},
    batch_size=100
):
    process_user(user)
```

### Using Unit of Work

```python
async with get_unit_of_work() as uow:
    user = await uow.users.get(user_id)
    order = await uow.orders.get(order_id)
    
    user.add_order(order)
    
    await uow.users.update(user)
    await uow.orders.update(order)
    
    await uow.commit()
```

### Service Pattern

The service pattern is implemented with a clear hierarchy of abstractions:

```
BaseService[InputT, OutputT]
  └── TransactionalService[InputT, OutputT]
      └── ApplicationService[InputT, OutputT]

BaseQueryService[ParamsT, OutputT]
  └── RepositoryQueryService[T, ID, ParamsT]

CrudServiceProtocol[T, ID]
  └── CrudService[T, ID]
      └── AggregateCrudService[T, ID]
```

### Using Services

```python
# Basic service
service = get_service(MyService)
result = await service.execute(input_data)

# CRUD service
crud_service = get_crud_service(User)
user = await crud_service.get(user_id)
users = await crud_service.list(filters={"status": "active"})
new_user = await crud_service.create(user_data)
updated_user = await crud_service.update(user_id, update_data)
await crud_service.delete(user_id)

# Query service
query_service = get_query_service(UserQueryService)
results = await query_service.execute_query(params)
count = await query_service.count(filters)
```