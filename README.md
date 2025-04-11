# uno

[![PyPI - Version](https://img.shields.io/pypi/v/uno.svg)](https://pypi.org/project/uno)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/uno.svg)](https://pypi.org/project/uno)

-----

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Development](#development)
- [License](#license)

## Introduction

uno is a comprehensive application framework for building data-driven applications with PostgreSQL and FastAPI. Despite its name, uno is NOT an ORM - it's a complete framework that goes well beyond traditional ORMs to provide a unified approach to database operations, API definition, and business logic.

The name "uno" (Spanish for "one") represents the unified nature of the framework, bringing together database, API, and business logic in a cohesive but loosely coupled system.

## Features

- **Domain-Driven Design**: Support for building applications using DDD principles with entities, value objects, aggregates, and repositories
- **Event-Driven Architecture**: Built-in event system for loosely coupled components that communicate through domain events
- **Modern Dependency Injection**: Protocol-based DI system with proper scoping and lifecycle management
- **CQRS Pattern**: Separation of command (write) and query (read) operations for better performance and scalability
- **Unified Database Management**: Centralized approach to database connection management with support for both synchronous and asynchronous operations
- **SQL Generation**: Powerful SQL emitters for creating and managing database objects
- **API Integration**: FastAPI endpoint factory with automatic dependency injection
- **Schema Management**: Advanced schema generation and validation
- **Business Logic Layer**: Clean separation of business logic from database operations
- **Authorization System**: Built-in user and permission management
- **Advanced Filtering**: Dynamic query building with support for complex filters
- **Workflow Management**: Support for complex business workflows and state transitions
- **Metadata Management**: Track relationships between entities
- **PostgreSQL Integration**: Leverages PostgreSQL-specific features like JSONB, ULID, and row-level security
- **Vector Search**: Built-in vector similarity search using pgvector with automatic embedding generation
- **Graph Database**: Integrated graph database capabilities with the AGE extension
- **Hybrid Search**: Combine vector similarity with graph relationships for powerful contextual search
- **Functional Error Handling**: Result pattern for handling errors without exceptions

## Installation

```console
pip install uno
```

## Usage

### Quick Start

```python
# Import the new domain-driven design components
from uno.core import (
    AggregateEntity, BaseDomainEvent, 
    BaseCommand, CommandBus, command_handler,
    AbstractUnitOfWork, Success, Failure
)
from uno.dependencies import get_service_provider, singleton, inject_params

# Define a domain event
class UserCreatedEvent(BaseDomainEvent):
    user_id: str
    email: str
    
    @property
    def aggregate_id(self) -> str:
        return self.user_id

# Define a domain entity
class User(AggregateEntity[str]):
    def __init__(self, id: str, email: str, handle: str, full_name: str):
        super().__init__(id=id)
        self.email = email
        self.handle = handle
        self.full_name = full_name
    
    def validate_email(self) -> bool:
        if "@" not in self.email:
            return False
        return True
    
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

# Define a command
class CreateUserCommand(BaseCommand):
    email: str
    handle: str
    full_name: str

# Define a command handler
@singleton
@command_handler(CreateUserCommand)
class CreateUserCommandHandler:
    def __init__(self, unit_of_work: AbstractUnitOfWork):
        self.unit_of_work = unit_of_work
    
    async def handle(self, command: CreateUserCommand):
        try:
            # Create user entity
            user_id = generate_id()
            user = User.create(
                id=user_id,
                email=command.email,
                handle=command.handle,
                full_name=command.full_name
            )
            
            # Use unit of work to manage transaction
            async with self.unit_of_work:
                user_repo = self.unit_of_work.get_repository(UserRepository)
                await user_repo.save(user)
            
            return Success(user)
        except Exception as e:
            return Failure(e)

# FastAPI endpoint with dependency injection
from fastapi import APIRouter
from uno.dependencies.fastapi_integration import DIAPIRouter

# Create a router with automatic dependency injection
router = DIAPIRouter(prefix="/users", tags=["users"])

@router.post("/")
@inject_params()
async def create_user(
    command: CreateUserCommand,
    command_bus: CommandBus
):
    result = await command_bus.dispatch(command)
    
    if result.is_success:
        user = result.value
        return {"id": user.id, "email": user.email}
    else:
        return {"error": str(result.error)}, 400
```

### Using Vector Search with the New Architecture

```python
# Get the service provider
provider = get_service_provider()

# Define a query using the CQRS pattern
class DocumentSearchQuery(BaseQuery):
    query_text: str
    limit: int = 10
    threshold: float = 0.7
    metric: str = "cosine"

# Define a query handler
@singleton
@query_handler(DocumentSearchQuery)
class DocumentSearchQueryHandler:
    def __init__(self, vector_search_factory):
        self.vector_search_factory = vector_search_factory
    
    async def handle(self, query: DocumentSearchQuery):
        try:
            # Get vector search service for documents
            document_search = self.vector_search_factory.create_search_service(
                entity_type="document",
                table_name="documents"
            )
            
            # Perform a search
            results = await document_search.search(query)
            return Success(results)
        except Exception as e:
            return Failure(e)

# Use in an API endpoint
@router.get("/search")
@inject_params()
async def search_documents(
    query_text: str,
    limit: int = 10,
    threshold: float = 0.7,
    query_bus: QueryBus = None
):
    query = DocumentSearchQuery(
        query_text=query_text,
        limit=limit,
        threshold=threshold
    )
    
    result = await query_bus.dispatch(query)
    
    if result.is_success:
        return [
            {
                "id": item.id,
                "similarity": item.similarity,
                "title": item.entity.title,
                "content": item.entity.content[:100] + "..." if len(item.entity.content) > 100 else item.entity.content
            }
            for item in result.value
        ]
    else:
        return {"error": str(result.error)}, 400
```

### Starting with Docker (Recommended)

We follow a Docker-first approach for all environments. The easiest way to get started is:

```console
# Set up Docker and run the application
hatch run dev:app

# Or just set up the Docker environment
hatch run dev:docker-setup
```

This will create a PostgreSQL 16 container with all required extensions, including pgvector for vector search and AGE for graph database capabilities.

See [DOCKER_FIRST.md](DOCKER_FIRST.md) for more details on our Docker-first approach.

## Architecture

uno is built on a modular architecture with several core components:

1. **Domain Layer**: Implements domain-driven design (DDD) principles
   - `AggregateEntity`: Base class for aggregate roots
   - `BaseDomainEvent`: Base class for domain events
   - `ValueObject`: Base class for immutable value objects
   - `Repository`: Protocol for data access abstraction

2. **Application Layer**: Implements application services and CQRS
   - `CommandBus`: Dispatches commands to their handlers
   - `QueryBus`: Dispatches queries to their handlers
   - `UnitOfWork`: Manages transaction boundaries

3. **Data Layer**: Manages database connections, schema definition, and data operations
   - `UnoModel`: SQLAlchemy-based model for defining database tables
   - `DatabaseFactory`: Centralized factory for creating database connections
   - `SQL Emitters`: Components that generate SQL for various database objects

4. **API Layer**: Exposes functionality through REST endpoints
   - `DIAPIRouter`: FastAPI-based router with dependency injection
   - `EndpointFactory`: Automatically generates endpoints from objects
   - `Filter Manager`: Handles query parameters and filtering

5. **Infrastructure Layer**: Provides cross-cutting concerns
   - `Dependency Injection`: Protocol-based DI with proper scoping
   - `Event Bus`: Publishes and subscribes to domain events
   - `Configuration`: Environment-aware configuration system

## Project Structure

```
src/uno/
├── __init__.py
├── core/                 # Core domain-driven design components
│   ├── protocols.py      # Interface protocols
│   ├── domain.py         # DDD building blocks
│   ├── events.py         # Event-driven architecture
│   ├── cqrs.py           # CQRS pattern
│   ├── uow.py            # Unit of Work pattern
│   ├── result.py         # Result pattern for error handling
│   └── config.py         # Configuration management
├── api/                  # API components
│   ├── endpoint.py       # Base endpoint definition
│   └── endpoint_factory.py  # Factory for creating API endpoints
├── dependencies/         # Dependency injection
│   ├── scoped_container.py  # DI container with scoping
│   ├── decorators.py     # DI decorators
│   ├── fastapi_integration.py  # FastAPI integration
│   └── discovery.py      # Automatic service discovery
├── database/             # Database components
│   ├── config.py         # Connection configuration
│   ├── db.py             # Database operations
│   └── engine/           # Database engine management
│       ├── async.py      # Async engine
│       ├── base.py       # Base engine factory
│       └── sync.py       # Synchronous engine
├── model.py              # SQL Alchemy model base
├── queries/              # Query components
│   ├── filter.py         # Filter definitions
│   └── filter_manager.py # Query filtering
├── schema/               # Schema components
│   ├── schema.py         # Schema definitions
│   └── schema_manager.py # Schema management
├── sql/                  # SQL generation
│   ├── emitter.py        # Base SQL emitter
│   └── emitters/         # Specialized emitters
├── domain/               # Domain-specific components
│   ├── service_example.py  # Example domain service
│   └── api_example.py    # Example API endpoints
└── vector_search/        # Vector search components
    ├── services.py       # Vector search services
    ├── events.py         # Event handlers for vector updates
    └── models.py         # Vector query and result models
```

## Development

### Requirements

- Python 3.12+
- Docker and Docker Compose
  - All PostgreSQL dependencies are handled by Docker
  - No local PostgreSQL installation needed

### Testing

```console
# Setup Docker for testing and run tests
hatch run test:all

# Just set up the Docker test environment 
hatch run test:docker-setup

# Run tests (after Docker setup)
hatch run test:test

# Run tests with more details
hatch run test:testvv

# Type checking
hatch run types:check
```

### Documentation

```console
# Build documentation
hatch run docs:build

# Serve documentation locally
hatch run docs:serve
```

## License

`uno` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.