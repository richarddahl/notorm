# Architecture Overview

uno is built on a modular architecture with three primary components that work together to provide a comprehensive framework for building data-driven applications.

## Three-Tier Architecture

### 1. Data Layer

The Data Layer manages database connections, schema definition, and data operations:

- **UnoModel**: SQLAlchemy-based model for defining database tables
- **DatabaseFactory**: Centralized factory for creating database connections
- **SQL Emitters**: Components that generate SQL for various database objects

### 2. Business Logic Layer

The Business Logic Layer handles validation, processing, and business rules:

- **UnoObj**: Pydantic-based models that encapsulate business logic
- **Registry**: Central registry for managing object relationships
- **Schema Manager**: Manages schema definitions and transformations

### 3. API Layer

The API Layer exposes functionality through REST endpoints:

- **UnoEndpoint**: FastAPI-based endpoints for CRUD operations
- **EndpointFactory**: Automatically generates endpoints from objects
- **Filter Manager**: Handles query parameters and filtering

## Component Relationships

These three layers are designed to work together but are loosely coupled, allowing for flexibility in how they're used:

- **UnoModel** defines the database structure and provides data access methods
- **UnoObj** wraps a model with business logic and validation
- **UnoEndpoint** exposes UnoObj functionality through a REST API

## Framework Features

### Database Features

- **Centralized Connection Management**: Unified approach to database connections with support for both synchronous and asynchronous operations
- **Advanced SQL Generation**: SQL emitters for creating tables, functions, triggers, and more
- **Transaction Management**: Support for atomic operations with proper error handling
- **Migration Support**: Tools for managing database schema migrations

### Business Logic Features

- **Data Validation**: Pydantic-based validation of data inputs and outputs
- **Business Rules**: Encapsulation of business rules within UnoObj classes
- **Object Relationships**: Management of object relationships through the Registry
- **Schema Transformation**: Dynamic schema generation and transformation

### API Features

- **Automatic Endpoint Generation**: Creation of CRUD endpoints from UnoObj classes
- **Advanced Filtering**: Support for complex query parameters and filtering
- **Authentication and Authorization**: Built-in user and permission management
- **Documentation**: Automatic OpenAPI documentation generation

## Design Principles

uno is built on several key design principles:

1. **Separation of Concerns**: Clear separation between data access, business logic, and API layers
2. **Loose Coupling**: Components can be used independently or together
3. **Composition over Inheritance**: Favor composition patterns over deep inheritance hierarchies
4. **Convention over Configuration**: Sensible defaults with the ability to override
5. **Type Safety**: Comprehensive type annotations for better IDE support and runtime validation
6. **PostgreSQL Integration**: First-class support for PostgreSQL-specific features

## Next Steps

- [Database Layer](../database/overview.md): Understand the database connection management
- [Models](../models/overview.md): Learn how to define data models
- [Business Logic](../business_logic/overview.md): Understand how to implement business logic with UnoObj
- [API Integration](../api/overview.md): Learn how to expose your business logic through API endpoints
