
# Developer Guide

## Uno Framework Structure

This guide explains the standardized code organization and import paths for the Uno framework.

### Clean Architecture Structure

The Uno framework follows clean architecture principles with a clear separation between:

1. **Core Layer**: Base abstractions, interfaces, and fundamental building blocks
2. **Domain Layer**: Business logic, entities, and domain services  
3. **Application Layer**: Orchestration of domain logic, DTOs, use cases
4. **Infrastructure Layer**: Technical implementations, database access, external services

### Standard Import Paths

Use these import paths for the primary building blocks of the framework:

#### Core Components

```python
# Base model for database tables
from uno.domain.base.model import BaseModel

# Core domain entities
from uno.domain.entities.base_entity import Entity, AggregateRoot, ValueObject

# Repository base classes
from uno.core.base.repository import BaseRepository

# Service base classes  
from uno.core.base.service import BaseService

# DTO base classes
from uno.core.base.dto import BaseDTO, PaginatedListDTO

# Error handling
from uno.core.base.error import BaseError
```

#### Application Layer Components

```python
# DTO management
from uno.application.dto.manager import DTOManager, get_dto_manager

# CQRS Query components
from uno.application.queries.executor import QueryExecutor

# Workflow engine
from uno.application.workflows.engine import WorkflowEngine
```

#### Infrastructure Layer Components

```python
# Repository implementations  
from uno.infrastructure.repositories.sqlalchemy_repository import SQLAlchemyRepository

# Service implementations
from uno.infrastructure.services.base_service import ServiceImplementation

# Database connections
from uno.infrastructure.database.db_manager import DBManager
```

### Module Documentation

Each module should provide documentation on its purpose and usage:

```python
"""
Module name and purpose.

This module provides... [brief explanation]

Key components:
- Class1: [purpose]
- Class2: [purpose]

Usage example:
from module import Class1
"""
```

### Naming Conventions

- **Base classes**: Use the `Base` prefix (e.g., `BaseRepository`, `BaseService`)
- **Protocols/interfaces**: Use the `Protocol` suffix (e.g., `RepositoryProtocol`)
- **Implementations**: Use descriptive names without prefixes (e.g., `SQLAlchemyRepository`)
- **Factory methods**: Use `create_` prefix (e.g., `create_repository`)

### Standard File Structure

Each module should follow this general structure:

```
module_name/
  __init__.py         # Exports public API
  entities/           # Domain entities
    __init__.py
    base_entity.py    # Base entity classes  
    entity_name.py    # Specific entity implementations
  repositories/       # Repository interfaces and implementations  
    __init__.py
    repository_name.py
  services/           # Service interfaces and implementations
    __init__.py
    service_name.py
```

## Development Tools

The framework provides several development tools:

- Code generators: `uno-codegen`
- Documentation tools: `uno-docs`
- Testing utilities: `uno.testing`

### Modernization Tools

The framework includes several scripts to help modernize code to follow our standards:

#### Import Standards Tools

- **Validation**: `src/scripts/validate_import_standards.py`
  - Identifies legacy class names and non-standard imports
  - Generates detailed reports and fix guides
  
- **Auto-fixing**: `src/scripts/modernize_imports.py`
  - Automatically updates legacy imports to follow standards
  - Replaces legacy class names with their standardized versions
  - Adds required imports automatically
  
```bash
# Validate the codebase against import standards
python -m src.scripts.validate_import_standards

# Modernize imports in a specific directory (dry run first)
python -m src.scripts.modernize_imports --dry-run --path=src/uno/api

# Apply import modernization
python -m src.scripts.modernize_imports --path=src/uno/api
```

#### Additional Modernization Tools

- **Async Patterns**: `src/scripts/modernize_async.py`
  - Updates to modern Python 3.12+ async patterns
  
- **DateTime**: `src/scripts/modernize_datetime.py`
  - Replaces `datetime.utcnow()` with `datetime.now(datetime.UTC)`
  
- **Domain Models**: `src/scripts/modernize_domain.py`
  - Updates domain models to follow clean architecture
  
- **Error Handling**: `src/scripts/modernize_result.py`
  - Implements the Result pattern for error handling

For more details, see `src/scripts/README_MODERNIZATION.md`.

## Testing Guidelines

1. Use pytest for all tests
2. Write unit tests for all public APIs
3. Use factory fixtures for test data
4. Mock external dependencies
5. Use the testing container for dependency injection

## Error Handling

Use the standardized error handling approach:

```python
from uno.core.base.error import BaseError

# Raising errors
raise BaseError("Message", "ERROR_CODE")

# Custom error types
class MyDomainError(BaseError):
    """Custom domain error."""
    
    def __init__(self, message, **context):
        super().__init__(message, "DOMAIN_ERROR_CODE", **context)
```

## Documentation

Always document your code with docstrings following this format:

```python
def function_name(param1, param2):
    """
    Short description of function purpose.
    
    More detailed explanation if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ErrorType: Description of when this error is raised
    """
```