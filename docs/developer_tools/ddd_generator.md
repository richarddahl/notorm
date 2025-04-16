# Domain-Driven Design Generator

The Domain-Driven Design (DDD) Generator is a powerful CLI tool that helps create consistent DDD components for your Uno applications. It generates domain entities, repositories, services, endpoints, and provider classes that follow DDD principles.

## Overview

The DDD Generator helps you:

- Create properly structured domain entities with fields and relationships
- Generate repository interfaces with custom query methods
- Create service classes that implement business logic
- Set up dependency injection with a domain provider
- Create FastAPI endpoints for domain entities
- Bootstrap entire DDD modules with multiple entities

## Installation

The DDD Generator is included in the Uno framework and available as a script in the `src/scripts` directory:

```bash
python src/scripts/ddd_generator.py [command] [options]
```

## Basic Usage

### Generate a Domain Entity

```bash
python src/scripts/ddd_generator.py entity \
  /path/to/module \
  module_name \
  EntityName \
  --fields "id:str,name:str,email:str,is_active:bool" \
  --aggregate \
  --description "Entity representing a user account"
```

This creates a domain entity in the `entities.py` file and updates `__init__.py` to expose it.

### Generate a Repository

```bash
python src/scripts/ddd_generator.py repository \
  /path/to/module \
  module_name \
  EntityName
```

This creates a repository class in the `domain_repositories.py` file that implements the Repository pattern for your entity.

### Generate a Service

```bash
python src/scripts/ddd_generator.py service \
  /path/to/module \
  module_name \
  EntityName
```

This creates a service class in the `domain_services.py` file that provides business logic methods for your entity.

### Generate a Provider

```bash
python src/scripts/ddd_generator.py provider \
  /path/to/module \
  module_name \
  EntityName1 EntityName2 EntityName3
```

This creates or updates the `domain_provider.py` file to register repositories and services for dependency injection.

### Generate Endpoints

```bash
python src/scripts/ddd_generator.py endpoints \
  /path/to/module \
  module_name \
  EntityName1 EntityName2 EntityName3
```

This creates or updates the `domain_endpoints.py` file with FastAPI endpoints for the entities.

## Generating Complete Modules

The most powerful feature is the ability to generate a complete DDD module with all components:

```bash
python src/scripts/ddd_generator.py module \
  /path/to/module \
  module_name \
  "User:id:str,name:str,email:str,is_active:bool" \
  "Product:id:str,name:str,description:str,price:float,inventory:int"
```

This creates:

1. Domain entities for User and Product
2. Repositories for both entities
3. Services for both entities
4. A provider that registers all components
5. Endpoints for both entities
6. Updates `__init__.py` to expose all components

## Advanced Features

### Custom Query Methods

You can define custom query methods for repositories in your entity specifications. This is particularly useful when generating a complete module.

### Custom Service Methods

You can define custom business logic methods for your services.

### Custom Endpoints

You can define custom API endpoints beyond the standard CRUD operations.

## Generated Code Structure

The DDD Generator creates files with the following structure:

### entities.py

```python
"""
Domain entities for the module_name module.

This module contains domain entities for the module_name module that represent
the core business objects in the domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List, Dict, Optional, Any, Set, Union

from uno.domain.core import Entity, AggregateRoot, ValueObject

@dataclass
class EntityName(AggregateRoot[str]):
    """
    Entity description.
    """
    id: str
    name: str
    email: str
    is_active: bool = True
```

### domain_repositories.py

```python
"""
Domain repositories for the module_name module.

This module contains repositories for accessing and manipulating module_name
entities in the underlying data store.
"""

from typing import List, Dict, Optional, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.repository import Repository
from uno.core.result import Result, Success, Failure

from .entities import *

class EntityNameRepository(Repository[EntityName, str]):
    """Repository for managing EntityName entities."""
    
    entity_class = EntityName
```

### domain_services.py

```python
"""
Domain services for the module_name module.

This module contains services that implement business logic for
working with module_name domain entities.
"""

import logging
from typing import List, Dict, Optional, Any, Union, Type

from uno.domain.service import DomainService
from uno.core.result import Result, Success, Failure

from .entities import *
from .domain_repositories import *

class EntityNameService(DomainService[EntityName, str]):
    """Service for managing EntityName entities."""
    
    def __init__(self, repository: EntityNameRepository, logger: Optional[logging.Logger] = None):
        """
        Initialize the service.
        
        Args:
            repository: Repository for EntityName entities
            logger: Optional logger instance
        """
        super().__init__(repository)
        self.logger = logger or logging.getLogger(__name__)
```

### domain_provider.py

```python
"""
Domain provider for the module_name module.

This module configures the dependency injection container for
module_name domain services and repositories.
"""

from uno.dependencies.service import register_service

from .domain_repositories import EntityNameRepository
from .domain_services import EntityNameService


def register_module_name_services():
    """Register module_name services in the dependency container."""
    register_service(EntityNameRepository)
    register_service(EntityNameService, depends=[EntityNameRepository])
```

### domain_endpoints.py

```python
"""
Domain endpoints for the module_name module.

This module provides FastAPI endpoints for module_name domain entities,
exposing them through a RESTful API.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import List, Dict, Optional, Any
from uno.dependencies.scoped_container import get_service

from uno.domain.api_integration import create_domain_router, domain_endpoint

from .entities import EntityName
from .domain_services import EntityNameService


def create_entity_name_router() -> APIRouter:
    """Create router for EntityName endpoints."""
    router = create_domain_router(
        entity_type=EntityName,
        service_type=EntityNameService,
        prefix="/entity_names",
        tags=["EntityName"]
    )
    return router


def create_module_name_router() -> APIRouter:
    """Create combined router for all module_name endpoints."""
    router = APIRouter(tags=["ModuleName"])
    
    # Add any module-level routes here
    
    return router
    
def register_module_name_routes(app):
    """Register all module_name routes with the app."""
    app.include_router(create_entity_name_router())
    app.include_router(create_module_name_router())
```

## Best Practices

When using the DDD Generator:

1. **Plan Your Domain Model**: Before generating code, sketch your domain model with entities and their relationships.

2. **Use Meaningful Names**: Use descriptive, domain-specific names for entities and their fields.

3. **Generate Early**: Generate code early in your development process to establish a consistent structure.

4. **Extend, Don't Rewrite**: Extend the generated code rather than rewriting it from scratch.

5. **Add Custom Logic**: The generated code provides the structure; add your domain-specific logic to the services.

6. **Use Type Hints**: Add proper type hints when extending the generated code.

7. **Validate Your Model**: Run validation and tests on your domain model to ensure correctness.

## Examples

### E-commerce Module

```bash
python src/scripts/ddd_generator.py module \
  /path/to/ecommerce \
  ecommerce \
  "Customer:id:str,name:str,email:str,address:str" \
  "Product:id:str,name:str,description:str,price:float,inventory:int" \
  "Order:id:str,customer_id:str,order_date:datetime,status:str,total_amount:float"
```

### Content Management Module

```bash
python src/scripts/ddd_generator.py module \
  /path/to/cms \
  cms \
  "Article:id:str,title:str,content:str,author_id:str,published_date:datetime,status:str" \
  "Author:id:str,name:str,bio:str,email:str" \
  "Category:id:str,name:str,description:str"
```

## Troubleshooting

- **Existing Files**: The generator won't overwrite existing entity, repository, or service definitions.
- **Invalid Names**: Entity names should be in PascalCase; the generator will convert them if needed.
- **Module Structure**: The module directory must exist before running the generator.
- **Field Formats**: Field specifications must be in the format `name:type`.
- **Import Errors**: Make sure all required imports are available in your project.

## Extending the Generator

The DDD Generator is designed to be extensible. You can modify the `ddd_generator.py` script to:

- Add new field types
- Change the generated code templates
- Add support for additional DDD patterns
- Customize the validation logic

## Conclusion

The Domain-Driven Design Generator is a powerful tool for bootstrapping your domain model implementation in Uno applications. It helps maintain consistency and adherence to DDD principles while accelerating your development process.