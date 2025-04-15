# Comprehensive Developer Documentation Guide

This guide provides instructions for creating comprehensive documentation for uno. Following these guidelines ensures consistency and high quality across all documentation.

## Table of Contents

- [Documentation Structure](#documentation-structure)
- [Code Documentation](#code-documentation)
- [API Documentation](#api-documentation)
- [Component Documentation](#component-documentation)
- [Documentation Tools](#documentation-tools)
- [Documentation Generation](#documentation-generation)
- [Documentation Standards](#documentation-standards)
- [Examples](#examples)

## Documentation Structure

uno documentation is organized into the following structure:

- **API Reference**: Automatically generated from code docstrings
- **Guides**: Step-by-step tutorials for common tasks
- **Concepts**: Explanations of core concepts and architecture
- **Examples**: Code examples demonstrating usage patterns
- **Development**: Information for framework contributors

All documentation is written in Markdown and can be rendered to various formats including HTML, PDF, and AsciiDoc.

## Code Documentation

All code should be documented using Python docstrings following the Google style:

```python
def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:```

"""Example function with PEP 484 type annotations.

Args:```

param1: The first parameter.
param2: The second parameter.
```

Returns:```

The return value. True for success, False otherwise.
```

Raises:```

ValueError: If param1 is negative.
TypeError: If param2 is not a string.
```
"""
if param1 < 0:```

raise ValueError("param1 must be positive.")
```
if not isinstance(param2, str):```

raise TypeError("param2 must be a string.")
```
return param1 > len(param2)
```
```

### Docstring Guidelines

1. **Classes** should have docstrings that explain the purpose of the class, its attributes, and any special behaviors.
2. **Methods and Functions** should have docstrings that explain what they do, their parameters, return values, and any exceptions they might raise.
3. **Modules** should have docstrings that explain the purpose of the module and provide an overview of its contents.
4. **Type Annotations** should be used whenever possible to help with code understanding and static analysis.

## API Documentation

API documentation is generated automatically from code docstrings using our documentation generation tools. To ensure your API is well-documented:

1. Use consistent, descriptive names for functions, classes, and parameters.
2. Provide comprehensive docstrings for all public APIs.
3. Use type annotations for parameters and return values.
4. Document all parameters, return values, and exceptions.
5. Include examples where appropriate.

## Component Documentation

Component documentation explains how major subsystems work and how to use them. Each component documentation should include:

1. **Overview**: What the component does and why it exists
2. **Architecture**: How the component is designed
3. **Configuration**: How to configure the component
4. **Usage**: How to use the component with examples
5. **Integration**: How the component integrates with other components
6. **Examples**: Complete examples showing the component in use

## Documentation Tools

We use the following tools for documentation:

1. **MkDocs**: Documentation site generator
2. **Material for MkDocs**: Theme for MkDocs
3. **mkdocstrings**: Plugin for automatic API documentation
4. **generate_docs.py**: Custom script for generating documentation from code
5. **standardize_docs.py**: Script for checking and fixing documentation issues

## Documentation Generation

To generate documentation, use the following command:

```bash
python src/scripts/generate_docs.py --output docs/api --formats markdown openapi html --mkdocs
```

This will:

1. Extract documentation from code docstrings
2. Generate Markdown, OpenAPI, and HTML documentation
3. Set up an MkDocs site with the documentation

To check documentation consistency:

```bash
python src/scripts/standardize_docs.py --check-links --check-images --standardize-headings
```

To fix documentation issues:

```bash
python src/scripts/standardize_docs.py --fix --standardize-headings --standardize-code-blocks --add-frontmatter
```

## Documentation Standards

1. **Headings** should use ATX style (`#`, `##`, etc.) rather than Setext style (`===` or `---` underlines).
2. **Code blocks** should be fenced with backticks and include a language identifier.
3. **Links** should be checked to ensure they point to valid targets.
4. **Images** should have descriptive alt text.
5. **Frontmatter** should be included at the top of markdown files.
6. **Lists** should be consistent in their formatting.
7. **Tables** should be well-formatted with headers.

## Examples

### Class Documentation Example

```python
class DatabaseSession:```

"""Session for database operations.
``````

```
```

This class provides a session for performing database operations
with transaction support and connection pooling.
``````

```
```

Attributes:```

engine: The database engine used by this session
autocommit: Whether to automatically commit transactions
isolation_level: The transaction isolation level
```
    
Examples:```

```
```python
    # Create a new session
    session = DatabaseSession(engine)```

```
```

# Use the session for querying
result = session.query(User).filter(User.name == "example").all()
```
    
    # Use the session for transactions
    with session.begin():
        user = User(name="new_user")
        session.add(user)```

```
```
"""
``````

```
```

def __init__(self, engine: Engine, autocommit: bool = False, ```

         isolation_level: Optional[str] = None):
"""Initialize a database session.
``````

```
```

Args:
    engine: The database engine to use
    autocommit: Whether to automatically commit transactions
    isolation_level: The transaction isolation level
    
Raises:
    TypeError: If engine is not a valid Engine instance
"""
# Implementation
```
```
```

### Module Documentation Example

```python
"""
Database engine for uno framework.

This module provides a database engine implementation that supports
both synchronous and asynchronous operations, connection pooling,
and transaction management.

Classes:```

Engine: Base class for database engines
SyncEngine: Synchronous database engine implementation
AsyncEngine: Asynchronous database engine implementation
```
    
Functions:```

create_engine: Factory function for creating engines
```
    
Examples:```

```python
# Create a synchronous engine
engine = create_engine('postgresql://user:pass@localhost/dbname')
``````

```
```

# Create an asynchronous engine
async_engine = create_engine('postgresql://user:pass@localhost/dbname', ```

                        async_=True)
```
```
```
"""

# Implementation
```

### Component Documentation Example (Markdown)

```markdown
# Database Engine

The database engine is the core component for database interactions in uno. It provides connection management, pooling, and query execution capabilities.

## Overview

The database engine abstracts database operations and provides a consistent interface for both synchronous and asynchronous operations. It supports multiple database backends through SQLAlchemy, with additional optimizations for PostgreSQL.

## Architecture

The engine system consists of several key components:

- **Engine**: Base class that defines the interface
- **SyncEngine**: Implementation for synchronous operations
- **AsyncEngine**: Implementation for asynchronous operations
- **ConnectionPool**: Manages database connections
- **Transaction**: Manages database transactions

## Configuration

Configure the engine using a database URL and additional options:

```python
from uno.database.engine import create_engine

# Synchronous engine
sync_engine = create_engine(```

'postgresql://user:pass@localhost/dbname',
pool_size=10,
max_overflow=20,
echo=False
```
)

# Asynchronous engine
async_engine = create_engine(```

'postgresql://user:pass@localhost/dbname',
async_=True,
pool_size=10,
max_overflow=20,
echo=False
```
)
```

## Usage

### Synchronous Usage

```python
from uno.database.engine import create_engine
from uno.database.session import Session

# Create engine
engine = create_engine('postgresql://user:pass@localhost/dbname')

# Create session
session = Session(engine)

# Query
users = session.query(User).filter(User.name == 'example').all()

# Transaction
with session.begin():```

user = User(name='new_user')
session.add(user)
```
```

### Asynchronous Usage

```python
from uno.database.engine import create_engine
from uno.database.session import AsyncSession

# Create engine
engine = create_engine('postgresql://user:pass@localhost/dbname', async_=True)

# Create session
session = AsyncSession(engine)

# Query
users = await session.query(User).filter(User.name == 'example').all()

# Transaction
async with session.begin():```

user = User(name='new_user')
await session.add(user)
```
```

## Integration

The database engine integrates with other components:

- **Models**: ORM models use the engine for queries
- **Repositories**: Database repositories use the engine for data access
- **Migrations**: Migration tools use the engine for schema changes
- **Connection Pool**: The engine manages connection pooling

## Performance

For optimal performance:

1. Use connection pooling with appropriate pool size
2. Use asynchronous operations for IO-bound workloads
3. Use batch operations for multiple inserts/updates
4. Use the query optimizer for complex queries
```