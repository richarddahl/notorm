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

- **Unified Database Management**: Centralized approach to database connection management with support for both synchronous and asynchronous operations
- **SQL Generation**: Powerful SQL emitters for creating and managing database objects
- **API Integration**: FastAPI endpoint factory for quickly building REST APIs
- **Schema Management**: Advanced schema generation and validation
- **Business Logic Layer**: Clean separation of business logic from database operations
- **Authorization System**: Built-in user and permission management
- **Advanced Filtering**: Dynamic query building with support for complex filters
- **Workflow Management**: Support for complex business workflows and state transitions
- **Metadata Management**: Track relationships between entities
- **PostgreSQL Integration**: Leverages PostgreSQL-specific features like JSONB, ULID, and row-level security

## Installation

```console
pip install uno
```

## Usage

### Quick Start

```python
from uno.database.engine import DatabaseFactory
from uno.model import UnoModel
from uno.obj import UnoObj

# Initialize the database factory
db_factory = DatabaseFactory()

# Define a model
class User(UnoModel):
    __tablename__ = "user"
    
    id: str
    email: str
    handle: str
    full_name: str
    
# Define business logic
class UserObj(UnoObj):
    id: str
    email: str
    handle: str
    full_name: str
    
    def validate_email(self):
        if "@" not in self.email:
            raise ValueError("Invalid email format")
```

### Starting the Database with Docker

```console
cd uno/docker
docker build -t pg16_uno .
docker-compose up
```

## Architecture

uno is built on a modular architecture with three primary components:

1. **Data Layer**: Manages database connections, schema definition, and data operations
   - `UnoModel`: SQLAlchemy-based model for defining database tables
   - `DatabaseFactory`: Centralized factory for creating database connections
   - `SQL Emitters`: Components that generate SQL for various database objects

2. **Business Logic Layer**: Handles validation, processing, and business rules
   - `UnoObj`: Pydantic-based models that encapsulate business logic
   - `Registry`: Central registry for managing object relationships
   - `Schema Manager`: Manages schema definitions and transformations

3. **API Layer**: Exposes functionality through REST endpoints
   - `UnoEndpoint`: FastAPI-based endpoints for CRUD operations
   - `EndpointFactory`: Automatically generates endpoints from objects
   - `Filter Manager`: Handles query parameters and filtering

## Project Structure

```
src/uno/
├── __init__.py
├── api/                  # API components
│   ├── endpoint.py       # Base endpoint definition
│   └── endpoint_factory.py  # Factory for creating API endpoints
├── attributes/           # User-defined attributes 
├── authorization/        # Authentication and authorization
├── database/             # Database components
│   ├── config.py         # Connection configuration
│   ├── db.py             # Database operations
│   └── engine/           # Database engine management
│       ├── async.py      # Async engine
│       ├── base.py       # Base engine factory
│       └── sync.py       # Synchronous engine
├── messaging/            # Inter-user messaging
├── meta/                 # Entity relationships
├── mixins.py             # Shared functionality
├── model.py              # SQL Alchemy model base
├── obj.py                # Business logic base
├── queries/              # Query components
│   ├── filter.py         # Filter definitions
│   └── filter_manager.py # Query filtering
├── registry.py           # Object registry
├── reports/              # Reporting functionality
├── schema/               # Schema components
│   ├── schema.py         # Schema definitions
│   └── schema_manager.py # Schema management
├── sql/                  # SQL generation
│   ├── emitter.py        # Base SQL emitter
│   └── emitters/         # Specialized emitters
│       ├── database.py   # Database-level SQL
│       ├── grants.py     # Permission SQL
│       ├── security.py   # Security SQL
│       └── table.py      # Table SQL
└── workflows/            # Business workflows
```

## Development

### Requirements

- Python 3.12+
- PostgreSQL 16+
- Docker (for local development)

### Testing

```console
# Run all tests
ENV=test pytest

# Run with details
ENV=test pytest -vv --capture=tee-sys --show-capture=all

# Type checking
mypy --install-types --non-interactive src/uno tests
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
