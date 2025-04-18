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
  - [Testing](#testing)
  - [Performance Benchmarks](#performance-benchmarks)
  - [Documentation](#documentation)
- [License](#license)

## Introduction

uno is a comprehensive application framework for building data-driven applications with PostgreSQL and FastAPI. Despite its name, uno is NOT an ORM - it's a complete framework that goes well beyond traditional ORMs to provide a unified approach to database operations, API definition, and business logic.

The name "uno" (Spanish for "one") represents the unified nature of the framework, bringing together database, API, and business logic in a cohesive but loosely coupled system.

The name "uno" is also, of course, a cheeky homage to gnu.

## Features

- **Domain-Driven Design**: Support for building applications using DDD principles with entities, value objects, aggregates, and repositories
- **Event-Driven Architecture**: Built-in event system for loosely coupled components that communicate through domain events
- **Modern Dependency Injection**: Protocol-based DI system with proper scoping and lifecycle management, following modern Python design patterns
- **CQRS Pattern**: Separation of command (write) and query (read) operations for better performance and scalability
- **Async-First Architecture**: Enhanced async utilities for robust concurrent operations with proper cancellation handling
- **Resource Management**: Comprehensive resource lifecycle management with connection pooling and health monitoring
- **Unified Database Management**: Centralized approach to database connection management with support for both synchronous and asynchronous operations
- **SQL Generation**: Powerful SQL emitters for creating and managing database objects
- **API Integration**: FastAPI endpoint factory with automatic dependency injection
- **Schema Management**: Advanced schema generation and validation
- **Business Logic Layer**: Clean separation of business logic from database operations
- **Authorization System**: Built-in user and permission management
- **Advanced Filtering**: Dynamic query building with support for complex filters
- **High-Performance Batch Operations**: Optimized batch processing for efficient database operations
- **Workflow Management**: Support for complex business workflows and state transitions
- **Metadata Management**: Track relationships between entities
- **PostgreSQL Integration**: Leverages PostgreSQL-specific features like JSONB, ULID, and row-level security
- **Vector Search**: Built-in vector similarity search using pgvector with automatic embedding generation
- **Graph Database**: Integrated graph database capabilities with the AGE extension
- **Hybrid Search**: Combine vector similarity with graph relationships for powerful contextual search
- **Functional Error Handling**: Result pattern for handling errors without exceptions
- **Advanced Security**: Comprehensive security framework with encryption, MFA, audit logging, and security testing
- **Field-Level Encryption**: Automatic encryption of sensitive data fields with key management
- **Multi-Factor Authentication**: Built-in TOTP-based MFA and password policy enforcement
- **Audit Logging**: Immutable, tamper-evident logging of all security-relevant events

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

### Using the Async-First Architecture

```python
# Import the new async utilities
from uno.core.async import TaskGroup, timeout, AsyncLock
from uno.core.async_integration import cancellable, retry, timeout_handler
from uno.core.async_manager import get_async_manager, as_task
from uno.database.enhanced_session import enhanced_async_session, SessionOperationGroup

# Properly handled async task with cancellation, retries, and timeouts
@cancellable
@retry(max_attempts=3)
@timeout_handler(timeout_seconds=5.0)
async def fetch_data(data_id: str):
    # The operation is automatically:
    # - Cancellable (with cleanup)
    # - Retryable (up to 3 times)
    # - Time-limited (5 second timeout)
    
    # Use enhanced async session
    async with enhanced_async_session() as session:
        # Perform database query with proper cancellation handling
        result = await session.execute(f"SELECT * FROM data WHERE id = '{data_id}'")
        return result.fetchone()

# Run concurrent tasks with proper structured concurrency
async def process_multiple_items(items):
    results = []
    
    # Use a task group for structured concurrency
    async with TaskGroup(name="process_items") as group:
        # Create tasks for each item
        tasks = [
            group.create_task(fetch_data(item["id"]), name=f"fetch_{i}")
            for i, item in enumerate(items)
        ]
        
        # Process results as they complete
        for task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing item: {e}")
    
    # All tasks are guaranteed to be completed or cancelled here
    return results

# Register with the application lifecycle
async def startup():
    # Register application startup
    manager = get_async_manager()
    
    # Start background tasks
    manager.create_task(background_monitoring(), name="monitoring")

# Use the async manager to run the application
if __name__ == "__main__":
    import asyncio
    from uno.core.async_manager import run_application
    
    # Run the application with proper lifecycle management
    asyncio.run(run_application(startup_func=startup))
```

### Using Resource Management

```python
# Import the resource management utilities
from uno.core.resources import CircuitBreaker, get_resource_registry
from uno.core.resource_management import (
    get_resource_manager, 
    managed_connection_pool,
    managed_background_task,
)
from uno.core.resource_monitor import get_resource_monitor
from uno.database.pooled_session import pooled_async_session
from uno.core.fastapi_integration import (
    setup_resource_management,
    create_health_endpoint,
)

# Create a FastAPI application with resource management
from fastapi import FastAPI, Depends

# Create the app
app = FastAPI()

# Set up resource management
setup_resource_management(app)

# Add health check endpoint
create_health_endpoint(app)

# Use pooled sessions for database access
@app.get("/example")
async def example_endpoint():
    async with pooled_async_session() as session:
        # Connection is from pool and managed with circuit breaker
        result = await session.execute("SELECT 1")
        return {"result": result.scalar()}

# Use a circuit breaker for external services
async def call_external_api():
    # Create a circuit breaker
    circuit = CircuitBreaker(
        name="api_circuit",
        failure_threshold=5,
        recovery_timeout=30.0,
    )
    
    # Register with resource registry
    registry = get_resource_registry()
    await registry.register("api_circuit", circuit)
    
    # Use the circuit breaker
    async def api_call():
        # Make the actual API call
        return {"status": "success"}
    
    # Call through the circuit breaker
    return await circuit(api_call)

# Create a managed background task
async def setup_background_tasks():
    async def monitoring_task():
        while True:
            # Monitor system health
            await asyncio.sleep(60)
    
    # Create and register the task
    async with managed_background_task(
        "monitoring",
        monitoring_task,
        restart_on_failure=True,
    ) as task:
        # Task is running and will be properly managed
        pass

# Use the resource manager to create pooled database connections
async def initialize_database():
    # Get the resource manager
    manager = get_resource_manager()
    
    # Create database connection pools
    pools = await manager.create_database_pools()
    
    # Create pooled session factory
    session_factory = await manager.create_session_factory()
    
    return session_factory

# Register startup and shutdown with FastAPI
@app.on_event("startup")
async def startup():
    # Initialize resources
    await get_resource_manager().initialize()
    
    # Set up background tasks
    await setup_background_tasks()
    
    # Initialize database
    await initialize_database()

# Monitor resource health
@app.get("/health")
async def health_check():
    # Get the resource monitor
    monitor = get_resource_monitor()
    
    # Get health summary
    return await monitor.get_health_summary()
```

### Using Batch Operations for High-Performance Database Access

```python
# Import batch operations components
from uno.queries import BatchOperations, BatchConfig, BatchExecutionStrategy, BatchSize
from uno.domain.repository import UnoDBRepository

# Create repository with batch operations enabled
repo = UnoDBRepository(
    entity_type=Product,
    use_batch_operations=True,
    batch_size=500,
)

# Batch get products
product_ids = ["prod-001", "prod-002", "prod-003", ..., "prod-999"]
products = await repo.batch_get(
    ids=product_ids,
    load_relations=["category", "reviews"],
    parallel=True,
)

# Update multiple products in batch
for product in products:
    if product.stock_level < 10:
        product.status = "low_stock"
        product.updated_at = datetime.utcnow()

# Batch update with a single database operation
updated_count = await repo.batch_update(
    entities=products,
    fields=["status", "updated_at"],
)
print(f"Updated {updated_count} products")

# Direct use of batch operations for advanced scenarios
batch_ops = BatchOperations(
    model_class=Order,
    batch_config=BatchConfig(
        batch_size=BatchSize.LARGE.value,
        execution_strategy=BatchExecutionStrategy.PARALLEL,
        max_workers=4,
        collect_metrics=True,
    ),
)

# Import orders with validation and duplicate handling
orders_data = load_orders_from_csv("orders.csv")
import_result = await batch_ops.batch_import(
    records=orders_data,
    unique_fields=["order_number"],
    update_on_conflict=True,
    return_stats=True,
)

print(f"Imported {import_result['inserted']} orders, updated {import_result['updated']}")
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

### Using the Security Framework

```python
# Import the security components
from uno.security import SecurityManager
from uno.security.config import SecurityConfig
from uno.security.audit import SecurityEvent
from uno.security.encryption import FieldEncryption

# Create security configuration
config = SecurityConfig(
    encryption={
        "algorithm": "AES_GCM",
        "key_management": "LOCAL",  # For development
        "field_level_encryption": True,
        "encrypted_fields": ["password", "credit_card", "ssn"]
    },
    authentication={
        "enable_mfa": True,
        "mfa_type": "TOTP",
        "session_timeout_minutes": 60,
        "password_policy": {
            "level": "STRICT",
            "min_length": 16
        }
    },
    audit={
        "enabled": True,
        "storage": {
            "type": "database",
            "connection": "postgresql://user:pass@localhost/db",
        },
        "retention_days": 365
    }
)

# Create security manager
security = SecurityManager(config)

# Field-level encryption in model
class User(AggregateEntity[str]):
    def __init__(self, id: str, email: str, ssn: str):
        super().__init__(id=id)
        self.email = email
        self._ssn = security.encrypt_field("ssn", ssn)  # Encrypted field
    
    @property
    def ssn(self) -> str:
        # Decrypt when accessed
        return security.decrypt_field("ssn", self._ssn)

# MFA implementation in API
@router.post("/mfa/setup")
@inject_params()
async def setup_mfa(
    user_id: str,
    security_manager: SecurityManager
):
    # Set up MFA for user
    setup_info = await security_manager.setup_mfa(user_id)
    
    # Return setup information including QR code
    return {
        "secret": setup_info.secret,
        "qr_code": setup_info.qr_code_uri,
        "instructions": setup_info.instructions
    }

@router.post("/mfa/verify")
@inject_params()
async def verify_mfa(
    user_id: str,
    code: str,
    security_manager: SecurityManager
):
    # Verify MFA code
    is_valid = await security_manager.verify_mfa(user_id, code)
    
    if is_valid:
        # Log successful verification
        security_manager.audit.log(
            event_type=SecurityEvent.MFA_VERIFICATION,
            user_id=user_id,
            metadata={"success": True}
        )
        return {"verified": True}
    else:
        # Log failed verification
        security_manager.audit.log(
            event_type=SecurityEvent.MFA_VERIFICATION,
            user_id=user_id,
            metadata={"success": False}
        )
        return {"verified": False}

# Security testing in CI/CD pipeline
@task(name="security-scan")
async def run_security_scan():
    from uno.security.testing import SecurityScanner
    
    # Create scanner
    scanner = SecurityScanner()
    
    # Run dependency scan
    vulnerabilities = await scanner.scan_dependencies()
    
    # Run static analysis
    security_issues = await scanner.run_static_analysis()
    
    # Generate report
    report = scanner.generate_report(
        vulnerabilities=vulnerabilities,
        security_issues=security_issues
    )
    
    # Check if any critical issues
    if report.has_critical_issues():
        print("Critical security issues found!")
        print(report.critical_issues_summary())
        return False
    
    return True
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

3. **Async Layer**: Implements robust async patterns
   - `TaskManager`: Manages async tasks with proper cancellation
   - `AsyncLock/Semaphore/Event`: Enhanced concurrency primitives
   - `TaskGroup`: Structured concurrency for related tasks
   - `AsyncBatcher`: Batches async operations for efficiency
   - `AsyncCache`: Provides async-aware caching with TTL

4. **Resource Management Layer**: Manages application resources
   - `ResourceRegistry`: Centralized registry for tracked resources
   - `ConnectionPool`: Pooled connections with health checking
   - `CircuitBreaker`: Circuit breaker for external service reliability
   - `ResourceMonitor`: Monitoring and health checking for resources
   - `ResourceManager`: Application lifecycle integration

5. **Data Layer**: Manages database connections, schema definition, and data operations
   - `UnoModel`: SQLAlchemy-based model for defining database tables
   - `DatabaseFactory`: Centralized factory for creating database connections
   - `SQL Emitters`: Components that generate SQL for various database objects
   - `EnhancedAsyncSession`: Improved async session with robust error handling
   - `PooledAsyncSession`: Connection pooling with circuit breakers

6. **API Layer**: Exposes functionality through REST endpoints
   - `DIAPIRouter`: FastAPI-based router with dependency injection
   - `EndpointFactory`: Automatically generates endpoints from objects
   - `Filter Manager`: Handles query parameters and filtering

7. **Infrastructure Layer**: Provides cross-cutting concerns
   - `Dependency Injection`: Protocol-based DI with proper scoping
   - `Event Bus`: Publishes and subscribes to domain events
   - `Configuration`: Environment-aware configuration system
   - `AsyncManager`: Coordinates async resources throughout the application

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
│   ├── async/            # Async utilities
│   │   ├── task_manager.py  # Task management
│   │   ├── concurrency.py   # Enhanced concurrency primitives
│   │   └── context.py       # Context management
│   ├── async_integration.py  # Async integration utilities
│   ├── async_manager.py  # Central async resource manager
│   ├── resources.py      # Resource management components
│   ├── resource_monitor.py  # Resource monitoring
│   ├── resource_management.py  # Resource lifecycle management
│   ├── fastapi_integration.py  # FastAPI integration for resources
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
│   ├── enhanced_db.py    # Enhanced database operations
│   ├── enhanced_session.py  # Enhanced session management
│   ├── pooled_session.py  # Pooled session management
│   └── engine/           # Database engine management
│       ├── async.py      # Async engine
│       ├── enhanced_async.py  # Enhanced async engine
│       ├── pooled_async.py  # Pooled async engine
│       ├── base.py       # Base engine factory
│       └── sync.py       # Synchronous engine
├── model.py              # SQL Alchemy model base
├── queries/              # Query components
│   ├── filter.py         # Filter definitions
│   ├── filter_manager.py # Query filtering
│   ├── optimized_queries.py # Optimized query building and execution
│   ├── common_patterns.py   # Common query patterns with optimizations
│   ├── batch_operations.py  # High-performance batch operations
│   └── executor.py      # Query execution engine
├── schema/               # Schema components
│   ├── schema.py         # Schema definitions
│   └── schema_manager.py # Schema management
├── sql/                  # SQL generation
│   ├── emitter.py        # Base SQL emitter
│   └── emitters/         # Specialized emitters
├── domain/               # Domain-specific components
│   ├── service_example.py  # Example domain service
│   └── api_example.py    # Example API endpoints
├── security/             # Security framework
│   ├── config.py         # Security configuration
│   ├── manager.py        # Security manager
│   ├── encryption/       # Encryption components
│   │   ├── aes.py        # AES encryption
│   │   ├── rsa.py        # RSA encryption
│   │   └── field.py      # Field-level encryption
│   ├── auth/             # Authentication components
│   │   ├── totp.py       # TOTP-based MFA
│   │   ├── password.py   # Password management
│   │   └── sso.py        # Single sign-on
│   ├── audit/            # Audit logging
│   │   ├── event.py      # Security event definitions
│   │   └── logger.py     # Audit logger
│   └── testing/          # Security testing tools
│       ├── scanner.py    # Vulnerability scanner
│       ├── dependency.py # Dependency security 
│       └── static.py     # Static analysis
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

### Documentation

Comprehensive documentation is available in the `/docs` directory and can be built using MkDocs:

```console
# Build documentation
python src/scripts/generate_docs.py --mkdocs

# Serve documentation locally
python src/scripts/generate_docs.py --mkdocs --serve
```

For more information on the documentation, see:
- [Documentation Guide](docs/developer_docs_guide.md)
- [Documentation Generation](docs/documentation_generation/overview.md)

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

# Run integration tests
hatch run test:integration

# Run integration tests with vector search components
hatch run test:integration-vector

# Run performance benchmarks for integration tests
hatch run test:benchmarks

# Type checking
hatch run types:check
```

The test suite includes comprehensive integration tests that verify component interactions in a real-world environment. These tests cover:

- Core infrastructure components (migrations, connection pooling, transactions)
- Authentication and authorization (JWT, RBAC, permissions)
- Data processing features (vector search, batch operations, query optimization)
- Distributed systems features (caching, error handling)

Each test verifies that components work together correctly with real infrastructure (PostgreSQL, Redis) through Docker.

### Performance Benchmarks

```console
# Run all benchmarks
hatch run test:benchmark

# Run specific module benchmarks
hatch run test:benchmark tests/benchmarks/test_database_performance.py

# Run integration test benchmarks
cd tests/integration
./run_benchmarks.py --output benchmark_results.json --csv

# Compare benchmark results with previous run
./run_benchmarks.py --compare previous_results.json

# View dashboard for all benchmark results
cd benchmarks/dashboard
./run_dashboard.sh
```

The benchmark infrastructure includes:

1. **Comprehensive Benchmarks**: Performance tests for all critical components
2. **Integration Test Benchmarks**: Performance tests for component interactions
3. **Benchmark Runner**: Tools for running benchmarks and comparing results
4. **Dashboard**: Visualization and analysis of benchmark results

The dashboard provides performance comparison, trend analysis, and scaling visualization. It integrates results from both unit-level and integration-level benchmarks. See [docs/benchmarks/dashboard.md](docs/benchmarks/dashboard.md) for more details.

### Documentation

```console
# Build documentation
hatch run docs:build

# Serve documentation locally
hatch run docs:serve
```

## License

`uno` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.