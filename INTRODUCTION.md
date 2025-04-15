# An Introduction to Uno

## What is Uno?

**Uno** ("Uno is Not an ORM") is a comprehensive application framework that goes beyond traditional ORMs to provide a unified approach to building modern, data-driven applications with PostgreSQL and FastAPI. Despite its playful name, Uno is much more than what it claims not to be—it's an integrated framework that bridges the gap between your database, application logic, and API layer.

The name "uno" (Spanish for "one") represents the unified nature of the framework, bringing together database, API, and business logic in a cohesive but loosely coupled system. It allows you to express complex relationships and operations in a way that plays to PostgreSQL's strengths while maintaining clean, maintainable Python code.

## Core Philosophy

Uno is built on several key philosophical principles:

1. **Database-First Approach**: Unlike ORMs that try to abstract away the database, Uno embraces PostgreSQL's powerful features and encourages leveraging them for optimal performance.

2. **Domain-Driven Design**: The framework supports building applications based on DDD principles with entities, value objects, aggregates, and repositories.

3. **Clean Architecture**: Uno promotes separation of concerns with clear boundaries between infrastructure, domain, and application layers.

4. **Async-First**: Built from the ground up with asynchronous operations in mind, with proper handling of cancellation, concurrency, and resource management.

5. **Protocol-Based Interfaces**: Using Python's Protocol system to define clear interfaces between components, improving testability and maintainability.

6. **Flexible Development Models**: Supporting both traditional UnoObj-based development and modern dependency injection patterns to fit different team preferences and project requirements.

## Key Components

Uno consists of several core components that work together to provide a complete application development experience:

### 1. Domain Layer

The domain layer implements domain-driven design principles and includes:

- **AggregateEntity**: Base class for aggregate roots that encapsulate domain logic and ensure consistency
- **ValueObject**: Immutable objects that represent domain concepts without identity
- **DomainEvent**: Events that capture changes in the domain model
- **Repository**: Abstractions for data persistence that enforce aggregate boundaries

The domain layer focuses on expressing your business rules and processes in clean, maintainable code.

### 2. Database Layer

The database layer provides modern, type-safe interaction with PostgreSQL:

- **UnoDB**: Enhanced database manager for both sync and async operations
- **EnhancedAsyncSession**: Improved async sessions with robust error handling and cancellation support
- **SQLEmitters**: Code that generates optimized SQL for various database operations
- **Migrations**: Tools for managing database schema changes
- **Vector Search**: Integration with pgvector for similarity search and embeddings

This layer maximizes performance by leveraging PostgreSQL-specific features while maintaining clean, type-safe abstractions.

### 3. API Layer

The API layer facilitates seamless exposure of your domain functionality:

- **Endpoint Factory**: Generates API endpoints from domain objects with proper validation
- **Schema Management**: Handles validation, serialization, and documentation
- **Filter Manager**: Provides flexible query parameter handling for filtering and sorting
- **FastAPI Integration**: Integrates with FastAPI for modern, high-performance APIs

This layer ensures that your API is consistent, well-documented, and aligned with your domain model.

### 4. Infrastructure Layer

The infrastructure layer provides cross-cutting concerns:

- **Dependency Injection**: Modern DI system with proper scoping and lifecycle management
- **Resource Management**: Centralized management of application resources with health monitoring
- **Async Task Management**: Enhanced async utilities with proper cancellation and lifecycle
- **Event Bus**: Publishes and subscribes to domain events for loose coupling
- **Caching**: Multi-level caching system with various invalidation strategies

This layer ensures that your application is robust, maintainable, and well-structured.

## How It All Works Together

Let's walk through a high-level example of how Uno's components work together in a typical application flow:

1. **Domain Definition**: You define your domain entities, value objects, and business rules.

2. **Data Access**: Uno's repository pattern connects your domain model to the database, automating common CRUD operations while allowing you to write custom queries when needed.

3. **Business Logic**: Your application services implement business processes by orchestrating domain objects and repositories.

4. **API Exposure**: The endpoint factory creates API endpoints with proper validation, documentation, and error handling.

5. **Resource Management**: The framework manages database connections, background tasks, and other resources with proper lifecycle handling.

6. **Event Processing**: Domain events trigger follow-up actions, ensuring loose coupling between components.

Uno handles much of the boilerplate, allowing you to focus on your domain-specific code while ensuring that all components work together harmoniously.

## Distinctive Features

What makes Uno stand out from other frameworks?

### 1. PostgreSQL Integration

Uno is built specifically for PostgreSQL, leveraging its advanced features:

- **Row-Level Security**: Automatic application of access controls at the database level
- **JSONB**: Native support for semi-structured data
- **Vector Search**: Built-in similarity search via pgvector extension
- **Graph Database**: Graph querying capabilities via Apache AGE integration
- **Functions and Triggers**: Generation and management of custom SQL functions and triggers

### 2. Modern Dependency Injection

Uno provides a state-of-the-art dependency injection system:

- **Protocol-Based Interfaces**: Definition of clear contracts between components
- **Hierarchical Scoping**: Proper management of object lifecycles (singleton, scoped, transient)
- **AsyncIO Support**: Full async support for service initialization and disposal
- **Automatic Resolution**: Smart resolution of dependencies with constructor injection

### 3. Unified Domain Model

Uno connects all layers through a consistent domain model:

- **Smart Attribute System**: Type-safe attribute management with validation
- **Graph-Based Querying**: Model relationships as a graph for complex traversals
- **Selective Updates**: Efficient database updates that only modify changed fields
- **Business Logic Integration**: Domain rules enforced throughout the stack

### 4. Enhanced AsyncIO Support

Uno includes robust async utilities:

- **Structured Concurrency**: Task groups for related operations
- **Resource Management**: Proper handling of async resource lifecycle
- **Cancellation Support**: Clean handling of task cancellation
- **Enhanced Primitives**: Improved async locks, events, and semaphores

### 5. Integrated Security Framework

Uno provides comprehensive security features:

- **Field-Level Encryption**: Automatic encryption of sensitive data
- **Audit Logging**: Immutable logging of security-relevant operations
- **Authentication Integration**: Flexible auth system with MFA support
- **Authorization Framework**: Fine-grained permission control

### 6. Comprehensive Testing Framework

Uno includes an extensive testing infrastructure:

- **Integration Tests**: Verify that components work correctly together in real environments
- **Performance Benchmarks**: Measure and monitor system performance
- **Vector Search Testing**: Specialized tests for similarity search capabilities
- **Authorization Testing**: Verify proper enforcement of access controls
- **Distributed Cache Testing**: Validate cross-process cache behavior

## Getting Started

Uno is designed to be approachable while providing advanced capabilities as your application grows. The recommended way to start is with Docker:

```bash
# Set up Docker and run the application
hatch run dev:app

# Or just set up the Docker environment
hatch run dev:docker-setup
```

This creates a PostgreSQL 16 container with all required extensions, including pgvector for vector search and Apache AGE for graph database capabilities.

### Running Tests

Uno comes with a comprehensive test suite that verifies all components work correctly:

```bash
# Run all tests
hatch run test:all

# Run integration tests only
hatch run test:integration

# Run integration tests with vector search components
hatch run test:integration-vector

# Run performance benchmarks
hatch run test:benchmarks
```

Integration tests verify that components work together correctly in a realistic environment with actual PostgreSQL and Redis instances (provided through Docker).

### Defining Your Domain Model

From there, you can start defining your domain model:

```python
from uno.core import AggregateEntity, BaseDomainEvent, ValueObject
from dataclasses import dataclass
from typing import List

# Define a value object
@dataclass(frozen=True)
class Address(ValueObject):
    street: str
    city: str
    state: str
    zip_code: str
    
    def format(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

# Define a domain event
class UserCreatedEvent(BaseDomainEvent):
    user_id: str
    email: str
    
    @property
    def aggregate_id(self) -> str:
        return self.user_id

# Define an aggregate entity
class User(AggregateEntity[str]):
    def __init__(self, id: str, email: str, name: str, address: Address):
        super().__init__(id=id)
        self.email = email
        self.name = name
        self.address = address
    
    @classmethod
    def create(cls, id: str, email: str, name: str, address: Address) -> "User":
        user = cls(id, email, name, address)
        
        # Register a domain event
        user.register_event(UserCreatedEvent(
            user_id=id,
            email=email
        ))
        
        return user
```

## Conclusion

Uno provides a comprehensive, integrated approach to building modern applications with PostgreSQL and Python. It combines the best practices of domain-driven design, clean architecture, and modern async programming while leveraging PostgreSQL's powerful features.

The framework is built on a foundation of reliability, with extensive integration tests verifying that all components work correctly together. This testing infrastructure ensures that as your application grows, you can be confident in its stability and performance.

Whether you're building a small API or a complex application with advanced querying needs, Uno provides the tools and structure to make your development process more efficient and your code more maintainable.

By unifying your database, domain logic, and API into a cohesive system, Uno enables you to build applications that are robust, performant, and a joy to develop and maintain. The comprehensive test suite and benchmarking tools help you maintain this quality as your application evolves.