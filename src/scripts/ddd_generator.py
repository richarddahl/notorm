#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain-Driven Design (DDD) component generator CLI tool.

This script provides utilities for generating domain entities, repositories,
services, endpoints, and other domain-driven design components.
"""

import argparse
import os
import re
import sys
import logging
import string
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DDDGenerator:
    """Generator for domain-driven design components."""

    def __init__(self, module_path: str, module_name: str):
        """
        Initialize the DDD generator.
        
        Args:
            module_path: Path to the module directory
            module_name: Name of the module
        """
        self.module_path = Path(module_path)
        self.module_name = module_name
        
        # Validate module path
        if not self.module_path.exists():
            logger.error(f"Module path '{module_path}' does not exist")
            sys.exit(1)
        
        if not self.module_path.is_dir():
            logger.error(f"Module path '{module_path}' is not a directory")
            sys.exit(1)
            
        # Ensure module name is valid
        if not re.match(r'^[a-z][a-z0-9_]*$', module_name):
            logger.error(f"Module name '{module_name}' is not valid. "
                        "Use lowercase letters, numbers, and underscores.")
            sys.exit(1)

    def create_entity(self, entity_name: str, fields: Dict[str, str], 
                      is_aggregate: bool = True, 
                      description: Optional[str] = None) -> Path:
        """
        Create a domain entity file.
        
        Args:
            entity_name: Name of the entity class
            fields: Dictionary of field names to their types
            is_aggregate: Whether this is an aggregate root
            description: Optional description for the entity
            
        Returns:
            Path to the created file
        """
        # Convert entity name to PascalCase if needed
        entity_class_name = self._to_pascal_case(entity_name)
        
        # Validate that entity name is valid
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', entity_class_name):
            logger.error(f"Entity name '{entity_class_name}' is not valid. "
                        "Use PascalCase format.")
            sys.exit(1)
            
        # Create entities.py if it doesn't exist
        entities_path = self.module_path / "entities.py"
        if not entities_path.exists():
            self._create_entities_file(entities_path)
            logger.info(f"Created file: {entities_path}")
            
        # Add entity class to entities.py
        entity_code = self._generate_entity_code(
            entity_class_name, fields, is_aggregate, description
        )
        
        # Check if entity already exists
        with open(entities_path, 'r') as f:
            content = f.read()
            
        if f"class {entity_class_name}" in content:
            logger.error(f"Entity '{entity_class_name}' already exists in {entities_path}")
            sys.exit(1)
            
        # Append entity to file
        with open(entities_path, 'a') as f:
            f.write("\n\n" + entity_code)
            
        logger.info(f"Added entity '{entity_class_name}' to {entities_path}")
        
        # Update __init__.py to expose the entity
        self._update_init_file_for_entity(entity_class_name)
        
        return entities_path

    def create_repository(self, entity_name: str, 
                         custom_queries: Optional[List[Dict[str, Any]]] = None) -> Path:
        """
        Create a domain repository file.
        
        Args:
            entity_name: Name of the entity class
            custom_queries: List of custom query methods to add
            
        Returns:
            Path to the created file
        """
        # Convert entity name to PascalCase
        entity_class_name = self._to_pascal_case(entity_name)
        repository_class_name = f"{entity_class_name}Repository"
        
        # Create domain_repositories.py if it doesn't exist
        repo_path = self.module_path / "domain_repositories.py"
        if not repo_path.exists():
            self._create_repository_file(repo_path)
            logger.info(f"Created file: {repo_path}")
            
        # Add repository class to domain_repositories.py
        repo_code = self._generate_repository_code(
            entity_class_name, repository_class_name, custom_queries
        )
        
        # Check if repository already exists
        with open(repo_path, 'r') as f:
            content = f.read()
            
        if f"class {repository_class_name}" in content:
            logger.error(f"Repository '{repository_class_name}' already exists in {repo_path}")
            sys.exit(1)
            
        # Append repository to file
        with open(repo_path, 'a') as f:
            f.write("\n\n" + repo_code)
            
        logger.info(f"Added repository '{repository_class_name}' to {repo_path}")
        
        # Update __init__.py to expose the repository
        self._update_init_file_for_repository(repository_class_name)
        
        return repo_path

    def create_service(self, entity_name: str, 
                      custom_methods: Optional[List[Dict[str, Any]]] = None) -> Path:
        """
        Create a domain service file.
        
        Args:
            entity_name: Name of the entity class
            custom_methods: List of custom service methods to add
            
        Returns:
            Path to the created file
        """
        # Convert entity name to PascalCase
        entity_class_name = self._to_pascal_case(entity_name)
        service_class_name = f"{entity_class_name}Service"
        repository_class_name = f"{entity_class_name}Repository"
        
        # Create domain_services.py if it doesn't exist
        service_path = self.module_path / "domain_services.py"
        if not service_path.exists():
            self._create_service_file(service_path)
            logger.info(f"Created file: {service_path}")
            
        # Add service class to domain_services.py
        service_code = self._generate_service_code(
            entity_class_name, service_class_name, repository_class_name, custom_methods
        )
        
        # Check if service already exists
        with open(service_path, 'r') as f:
            content = f.read()
            
        if f"class {service_class_name}" in content:
            logger.error(f"Service '{service_class_name}' already exists in {service_path}")
            sys.exit(1)
            
        # Append service to file
        with open(service_path, 'a') as f:
            f.write("\n\n" + service_code)
            
        logger.info(f"Added service '{service_class_name}' to {service_path}")
        
        # Update __init__.py to expose the service
        self._update_init_file_for_service(service_class_name)
        
        return service_path

    def create_provider(self, entity_names: List[str]) -> Path:
        """
        Create or update a domain provider file.
        
        Args:
            entity_names: List of entity class names
            
        Returns:
            Path to the created or updated file
        """
        # Convert entity names to PascalCase
        entity_class_names = [self._to_pascal_case(name) for name in entity_names]
        repository_class_names = [f"{name}Repository" for name in entity_class_names]
        service_class_names = [f"{name}Service" for name in entity_class_names]
        
        # Create domain_provider.py if it doesn't exist
        provider_path = self.module_path / "domain_provider.py"
        if not provider_path.exists():
            self._create_provider_file(provider_path)
            logger.info(f"Created file: {provider_path}")
            
        # Generate provider code
        provider_code = self._generate_provider_code(
            entity_class_names, repository_class_names, service_class_names
        )
        
        # Update or replace provider file
        with open(provider_path, 'w') as f:
            f.write(provider_code)
            
        logger.info(f"Updated provider file: {provider_path}")
        
        return provider_path

    def create_endpoints(self, entity_names: List[str], 
                        custom_endpoints: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Path:
        """
        Create or update domain endpoints file.
        
        Args:
            entity_names: List of entity class names
            custom_endpoints: Dictionary mapping entity names to lists of custom endpoint configs
            
        Returns:
            Path to the created or updated file
        """
        # Convert entity names to PascalCase
        entity_class_names = [self._to_pascal_case(name) for name in entity_names]
        
        # Create domain_endpoints.py if it doesn't exist
        endpoints_path = self.module_path / "domain_endpoints.py"
        if not endpoints_path.exists():
            self._create_endpoints_file(endpoints_path)
            logger.info(f"Created file: {endpoints_path}")
            
        # Generate endpoints code
        endpoints_code = self._generate_endpoints_code(
            entity_class_names, custom_endpoints
        )
        
        # Update or replace endpoints file
        with open(endpoints_path, 'w') as f:
            f.write(endpoints_code)
            
        logger.info(f"Updated endpoints file: {endpoints_path}")
        
        # Update __init__.py to expose the endpoint functions
        self._update_init_file_for_endpoints(entity_class_names)
        
        return endpoints_path

    def create_module(self, entity_specs: List[Dict[str, Any]]) -> None:
        """
        Create a complete DDD module with all components.
        
        Args:
            entity_specs: List of entity specifications with fields and options
        """
        entity_names = []
        
        # Create entities
        for spec in entity_specs:
            entity_name = spec["name"]
            entity_names.append(entity_name)
            
            # Create entity
            self.create_entity(
                entity_name=entity_name,
                fields=spec.get("fields", {}),
                is_aggregate=spec.get("is_aggregate", True),
                description=spec.get("description")
            )
            
            # Create repository
            self.create_repository(
                entity_name=entity_name,
                custom_queries=spec.get("custom_queries")
            )
            
            # Create service
            self.create_service(
                entity_name=entity_name,
                custom_methods=spec.get("custom_methods")
            )
        
        # Create provider for all entities
        self.create_provider(entity_names)
        
        # Create endpoints for all entities
        custom_endpoints = {}
        for spec in entity_specs:
            if "custom_endpoints" in spec:
                custom_endpoints[spec["name"]] = spec["custom_endpoints"]
                
        self.create_endpoints(entity_names, custom_endpoints)
        
        logger.info(f"Successfully created DDD module '{self.module_name}' with {len(entity_names)} entities")

    def _create_entities_file(self, file_path: Path) -> None:
        """Create the entities.py file with initial content."""
        content = textwrap.dedent('''\
        """
        Domain entities for the {module_name} module.
        
        This module contains domain entities for the {module_name} module that represent
        the core business objects in the domain model.
        """
        
        from dataclasses import dataclass, field
        from datetime import datetime, UTC
        from typing import List, Dict, Optional, Any, Set, Union
        
        from uno.domain.core import Entity, AggregateRoot, ValueObject
        ''').format(module_name=self.module_name)
        
        with open(file_path, 'w') as f:
            f.write(content)

    def _create_repository_file(self, file_path: Path) -> None:
        """Create the domain_repositories.py file with initial content."""
        content = textwrap.dedent('''\
        """
        Domain repositories for the {module_name} module.
        
        This module contains repositories for accessing and manipulating {module_name}
        entities in the underlying data store.
        """
        
        from typing import List, Dict, Optional, Any, Union
        from sqlalchemy.ext.asyncio import AsyncSession
        
        from uno.domain.repository import Repository
        from uno.core.result import Result, Success, Failure
        
        from .entities import *
        ''').format(module_name=self.module_name)
        
        with open(file_path, 'w') as f:
            f.write(content)

    def _create_service_file(self, file_path: Path) -> None:
        """Create the domain_services.py file with initial content."""
        content = textwrap.dedent('''\
        """
        Domain services for the {module_name} module.
        
        This module contains services that implement business logic for
        working with {module_name} domain entities.
        """
        
        import logging
        from typing import List, Dict, Optional, Any, Union, Type
        
        from uno.domain.service import DomainService
        from uno.core.result import Result, Success, Failure
        
        from .entities import *
        from .domain_repositories import *
        ''').format(module_name=self.module_name)
        
        with open(file_path, 'w') as f:
            f.write(content)

    def _create_provider_file(self, file_path: Path) -> None:
        """Create the domain_provider.py file with initial content."""
        content = textwrap.dedent('''\
        """
        Domain provider for the {module_name} module.
        
        This module configures the dependency injection container for
        {module_name} domain services and repositories.
        """
        
        from uno.dependencies.service import register_service
        
        from .domain_repositories import *
        from .domain_services import *
        
        
        def register_{module_name}_services():
            """Register {module_name} services in the dependency container."""
            # Register repositories and services here
            pass
        ''').format(module_name=self.module_name)
        
        with open(file_path, 'w') as f:
            f.write(content)

    def _create_endpoints_file(self, file_path: Path) -> None:
        """Create the domain_endpoints.py file with initial content."""
        content = textwrap.dedent('''\
        """
        Domain endpoints for the {module_name} module.
        
        This module provides FastAPI endpoints for {module_name} domain entities,
        exposing them through a RESTful API.
        """
        
        from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
        from typing import List, Dict, Optional, Any
        
        from uno.domain.api_integration import create_domain_router, domain_endpoint
        
        from .entities import *
        from .domain_services import *
        ''').format(module_name=self.module_name)
        
        with open(file_path, 'w') as f:
            f.write(content)

    def _update_init_file(self, content: str) -> None:
        """Update the __init__.py file with new content."""
        init_path = self.module_path / "__init__.py"
        
        if not init_path.exists():
            # Create a new __init__.py file
            with open(init_path, 'w') as f:
                f.write(textwrap.dedent(f'''\
                """
                {self.module_name.capitalize()} module for the Uno framework.
                
                This module provides domain-driven functionality for {self.module_name}.
                """

                '''))
        
        # Update the file with new content
        with open(init_path, 'a') as f:
            f.write(content)
            
        logger.info(f"Updated __init__.py file")

    def _update_init_file_for_entity(self, entity_class_name: str) -> None:
        """Update __init__.py to expose the entity."""
        content = f"from .entities import {entity_class_name}\n"
        
        # Check if entity is already imported
        init_path = self.module_path / "__init__.py"
        if init_path.exists():
            with open(init_path, 'r') as f:
                init_content = f.read()
                
            if f"from .entities import {entity_class_name}" in init_content:
                return
                
        self._update_init_file(content)

    def _update_init_file_for_repository(self, repository_class_name: str) -> None:
        """Update __init__.py to expose the repository."""
        content = f"from .domain_repositories import {repository_class_name}\n"
        
        # Check if repository is already imported
        init_path = self.module_path / "__init__.py"
        if init_path.exists():
            with open(init_path, 'r') as f:
                init_content = f.read()
                
            if f"from .domain_repositories import {repository_class_name}" in init_content:
                return
                
        self._update_init_file(content)

    def _update_init_file_for_service(self, service_class_name: str) -> None:
        """Update __init__.py to expose the service."""
        content = f"from .domain_services import {service_class_name}\n"
        
        # Check if service is already imported
        init_path = self.module_path / "__init__.py"
        if init_path.exists():
            with open(init_path, 'r') as f:
                init_content = f.read()
                
            if f"from .domain_services import {service_class_name}" in init_content:
                return
                
        self._update_init_file(content)

    def _update_init_file_for_endpoints(self, entity_class_names: List[str]) -> None:
        """Update __init__.py to expose the endpoint functions."""
        router_funcs = [f"create_{self._to_snake_case(name)}_router" for name in entity_class_names]
        main_router_func = f"create_{self.module_name}_router"
        
        content = f"from .domain_endpoints import {', '.join(router_funcs)}, {main_router_func}\n"
        
        # Check if endpoint functions are already imported
        init_path = self.module_path / "__init__.py"
        if init_path.exists():
            with open(init_path, 'r') as f:
                init_content = f.read()
                
            if f"from .domain_endpoints import {main_router_func}" in init_content:
                return
                
        self._update_init_file(content)

    def _generate_entity_code(self, entity_class_name: str, 
                             fields: Dict[str, str],
                             is_aggregate: bool = True,
                             description: Optional[str] = None) -> str:
        """Generate code for an entity class."""
        # Prepare class docstring
        if description is None:
            description = f"Domain entity for {entity_class_name} in the {self.module_name} module."
            
        # Determine the base class
        base_class = "AggregateRoot[str]" if is_aggregate else "Entity"
        
        # Generate field definitions
        field_defs = []
        for name, field_type in fields.items():
            if name == "id" and is_aggregate:
                field_defs.append("    id: str")
            else:
                field_defs.append(f"    {name}: {field_type}")
                
        if not fields.get("id") and is_aggregate:
            # Add ID field if not present for aggregate roots
            field_defs.insert(0, "    id: str")
            
        field_str = "\n".join(field_defs)
        
        # Generate the entity class code
        code = textwrap.dedent(f'''\
        @dataclass
        class {entity_class_name}({base_class}):
            """
            {description}
            """
        {field_str}
        ''')
        
        return code

    def _generate_repository_code(self, entity_class_name: str, 
                                 repository_class_name: str,
                                 custom_queries: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate code for a repository class."""
        # Generate custom query methods
        custom_methods = ""
        if custom_queries:
            for query in custom_queries:
                method_name = query.get("name", "find_by_field")
                params = query.get("params", [{"name": "field_value", "type": "Any"}])
                return_type = query.get("return_type", f"Optional[{entity_class_name}]")
                
                # Generate parameter list
                param_list = ["self"]
                for param in params:
                    param_list.append(f"{param['name']}: {param['type']}")
                param_list.append("session: Optional[AsyncSession] = None")
                params_str = ", ".join(param_list)
                
                # Generate method docstring
                param_docs = "\n        ".join([f"{p['name']}: {p.get('description', 'Field value')}" 
                                             for p in params])
                
                method_code = textwrap.dedent(f'''
                async def {method_name}({params_str}) -> Result[{return_type}]:
                    """
                    Find {entity_class_name} by specific field value.
                    
                    Args:
                        {param_docs}
                        session: Database session to use
                        
                    Returns:
                        Result containing the entity or error
                    """
                    # Implementation to be added
                    pass
                ''')
                
                custom_methods += method_code
        
        # Generate the repository class code
        code = textwrap.dedent(f'''\
        class {repository_class_name}(Repository[{entity_class_name}, str]):
            """Repository for managing {entity_class_name} entities."""
            
            entity_class = {entity_class_name}
        {custom_methods}
        ''')
        
        return code

    def _generate_service_code(self, entity_class_name: str, 
                              service_class_name: str,
                              repository_class_name: str,
                              custom_methods: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate code for a service class."""
        # Generate custom service methods
        custom_method_code = ""
        if custom_methods:
            for method in custom_methods:
                method_name = method.get("name", "process_entity")
                params = method.get("params", [{"name": "entity_id", "type": "str"}])
                return_type = method.get("return_type", f"Result[{entity_class_name}]")
                
                # Generate parameter list
                param_list = ["self"]
                for param in params:
                    param_list.append(f"{param['name']}: {param['type']}")
                params_str = ", ".join(param_list)
                
                # Generate method docstring
                param_docs = "\n        ".join([f"{p['name']}: {p.get('description', 'Parameter description')}" 
                                             for p in params])
                
                method_code = textwrap.dedent(f'''
                async def {method_name}({params_str}) -> {return_type}:
                    """
                    Custom service method for {entity_class_name}.
                    
                    Args:
                        {param_docs}
                        
                    Returns:
                        Result containing the entity or error
                    """
                    # Implementation to be added
                    pass
                ''')
                
                custom_method_code += method_code
        
        # Generate the service class code
        code = textwrap.dedent(f'''\
        class {service_class_name}(DomainService[{entity_class_name}, str]):
            """Service for managing {entity_class_name} entities."""
            
            def __init__(self, repository: {repository_class_name}, logger: Optional[logging.Logger] = None):
                """
                Initialize the service.
                
                Args:
                    repository: Repository for {entity_class_name} entities
                    logger: Optional logger instance
                """
                super().__init__(repository)
                self.logger = logger or logging.getLogger(__name__)
        {custom_method_code}
        ''')
        
        return code

    def _generate_provider_code(self, entity_class_names: List[str],
                               repository_class_names: List[str],
                               service_class_names: List[str]) -> str:
        """Generate code for the domain provider."""
        # Import statements are already in the template
        
        # Generate registration statements
        registration_code = []
        
        for repo_class in repository_class_names:
            registration_code.append(f"    register_service({repo_class})")
            
        for i, service_class in enumerate(service_class_names):
            repo_class = repository_class_names[i]
            registration_code.append(f"    register_service({service_class}, depends=[{repo_class}])")
            
        registration_str = "\n".join(registration_code)
        
        # Generate the provider code
        code = textwrap.dedent(f'''\
        """
        Domain provider for the {self.module_name} module.
        
        This module configures the dependency injection container for
        {self.module_name} domain services and repositories.
        """
        
        from uno.dependencies.service import register_service
        
        from .domain_repositories import {", ".join(repository_class_names)}
        from .domain_services import {", ".join(service_class_names)}
        
        
        def register_{self.module_name}_services():
            """Register {self.module_name} services in the dependency container."""
        {registration_str}
        ''')
        
        return code

    def _generate_endpoints_code(self, entity_class_names: List[str],
                                custom_endpoints: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> str:
        """Generate code for domain endpoints."""
        # Generate router functions for each entity
        router_functions = []
        
        for entity_name in entity_class_names:
            snake_name = self._to_snake_case(entity_name)
            plural_name = self._pluralize(snake_name)
            service_name = f"{entity_name}Service"
            
            # Generate custom endpoint functions
            custom_endpoint_code = ""
            if custom_endpoints and entity_name in custom_endpoints:
                for endpoint in custom_endpoints[entity_name]:
                    method = endpoint.get("method", "get")
                    path = endpoint.get("path", "/custom")
                    func_name = endpoint.get("name", f"custom_{snake_name}_endpoint")
                    params = endpoint.get("params", [])
                    
                    # Generate parameter list
                    param_list = []
                    for param in params:
                        param_type = param.get("type", "str")
                        if param.get("source") == "path":
                            param_list.append(f"{param['name']}: {param_type} = Path(..., description=\"Parameter description\")")
                        elif param.get("source") == "query":
                            param_list.append(f"{param['name']}: {param_type} = Query(None, description=\"Parameter description\")")
                        elif param.get("source") == "body":
                            param_list.append(f"data: Dict[str, Any] = Body(...)")
                        else:
                            param_list.append(f"{param['name']}: {param_type}")
                    
                    param_list.append(f"service: {service_name} = Depends(lambda: get_service({service_name}))")
                    params_str = ", ".join(param_list)
                    
                    response_model = endpoint.get("response_model", None)
                    response_model_str = f", response_model={response_model}" if response_model else ""
                    
                    custom_endpoint_code += textwrap.dedent(f'''
                    @router.{method}("{path}"{response_model_str})
                    @domain_endpoint(entity_type={entity_name}, service_type={service_name})
                    async def {func_name}({params_str}):
                        """
                        Custom endpoint for {entity_name}.
                        
                        Add detailed description here.
                        """
                        # Implementation to be added
                        pass
                    ''')
            
            # Generate router function
            router_func = textwrap.dedent(f'''
            def create_{snake_name}_router() -> APIRouter:
                """Create router for {entity_name} endpoints."""
                router = create_domain_router(
                    entity_type={entity_name},
                    service_type={service_name},
                    prefix="/{plural_name}",
                    tags=["{entity_name}"]
                )
                {custom_endpoint_code}
                return router
            ''')
            
            router_functions.append(router_func)
        
        # Generate main router function
        snake_names = [self._to_snake_case(name) for name in entity_class_names]
        router_calls = [f"    app.include_router(create_{name}_router())" for name in snake_names]
        router_calls_str = "\n".join(router_calls)
        
        main_router_func = textwrap.dedent(f'''
        def create_{self.module_name}_router() -> APIRouter:
            """Create combined router for all {self.module_name} endpoints."""
            router = APIRouter(tags=["{self.module_name.capitalize()}"])
            
            # Add any module-level routes here
            
            return router
            
        def register_{self.module_name}_routes(app):
            """Register all {self.module_name} routes with the app."""
        {router_calls_str}
            app.include_router(create_{self.module_name}_router())
        ''')
        
        # Generate the full endpoints code
        imports = textwrap.dedent('''\
        """
        Domain endpoints for the {module_name} module.
        
        This module provides FastAPI endpoints for {module_name} domain entities,
        exposing them through a RESTful API.
        """
        
        from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
        from typing import List, Dict, Optional, Any
        from uno.dependencies.scoped_container import get_service
        
        from uno.domain.api_integration import create_domain_router, domain_endpoint
        
        from .entities import {entity_imports}
        from .domain_services import {service_imports}
        ''').format(
            module_name=self.module_name,
            entity_imports=", ".join(entity_class_names),
            service_imports=", ".join([f"{name}Service" for name in entity_class_names])
        )
        
        code = imports + "\n" + "\n".join(router_functions) + "\n" + main_router_func
        
        return code

    def _to_pascal_case(self, s: str) -> str:
        """Convert a string to PascalCase."""
        # Remove non-alphanumeric characters and split by word boundaries
        words = re.findall(r'[a-zA-Z0-9]+', s)
        # Capitalize each word and join
        return "".join(word.capitalize() for word in words)

    def _to_snake_case(self, s: str) -> str:
        """Convert a PascalCase or camelCase string to snake_case."""
        # Insert underscore before capital letters and convert to lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _pluralize(self, s: str) -> str:
        """Pluralize a word (simple English rules)."""
        if s.endswith('y'):
            return s[:-1] + 'ies'
        elif s.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return s + 'es'
        else:
            return s + 's'


def parse_field_spec(field_spec: str) -> Dict[str, str]:
    """
    Parse field specifications in the format 'name:type'.
    
    Args:
        field_spec: Field specification string
        
    Returns:
        Dictionary mapping field names to types
    """
    fields = {}
    for spec in field_spec.split(','):
        if not spec.strip():
            continue
            
        parts = spec.split(':')
        if len(parts) != 2:
            logger.error(f"Invalid field specification: {spec}")
            sys.exit(1)
            
        name, field_type = parts
        fields[name.strip()] = field_type.strip()
        
    return fields


def main():
    """Run the DDD generator CLI tool."""
    parser = argparse.ArgumentParser(
        description="Generate domain-driven design components for Uno modules"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Entity command
    entity_parser = subparsers.add_parser("entity", help="Generate a domain entity")
    entity_parser.add_argument("module_path", help="Path to the module directory")
    entity_parser.add_argument("module_name", help="Name of the module")
    entity_parser.add_argument("entity_name", help="Name of the entity class")
    entity_parser.add_argument(
        "--fields", 
        help="Comma-separated list of fields in format 'name:type'"
    )
    entity_parser.add_argument(
        "--aggregate", 
        action="store_true", 
        help="Whether this is an aggregate root entity"
    )
    entity_parser.add_argument(
        "--description", 
        help="Description for the entity class"
    )
    
    # Repository command
    repo_parser = subparsers.add_parser("repository", help="Generate a domain repository")
    repo_parser.add_argument("module_path", help="Path to the module directory")
    repo_parser.add_argument("module_name", help="Name of the module")
    repo_parser.add_argument("entity_name", help="Name of the entity class")
    
    # Service command
    service_parser = subparsers.add_parser("service", help="Generate a domain service")
    service_parser.add_argument("module_path", help="Path to the module directory")
    service_parser.add_argument("module_name", help="Name of the module")
    service_parser.add_argument("entity_name", help="Name of the entity class")
    
    # Provider command
    provider_parser = subparsers.add_parser("provider", help="Generate a domain provider")
    provider_parser.add_argument("module_path", help="Path to the module directory")
    provider_parser.add_argument("module_name", help="Name of the module")
    provider_parser.add_argument(
        "entity_names", 
        nargs="+", 
        help="Names of the entity classes"
    )
    
    # Endpoints command
    endpoints_parser = subparsers.add_parser("endpoints", help="Generate domain endpoints")
    endpoints_parser.add_argument("module_path", help="Path to the module directory")
    endpoints_parser.add_argument("module_name", help="Name of the module")
    endpoints_parser.add_argument(
        "entity_names", 
        nargs="+", 
        help="Names of the entity classes"
    )
    
    # Module command (generate a full module)
    module_parser = subparsers.add_parser("module", help="Generate a complete DDD module")
    module_parser.add_argument("module_path", help="Path to the module directory")
    module_parser.add_argument("module_name", help="Name of the module")
    module_parser.add_argument(
        "entity_specs",
        nargs="+",
        help="Entity specifications in format 'name:field1:type1,field2:type2'"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    try:
        if args.command == "entity":
            # Parse fields
            fields = {}
            if args.fields:
                fields = parse_field_spec(args.fields)
                
            # Create generator and generate entity
            generator = DDDGenerator(args.module_path, args.module_name)
            generator.create_entity(
                args.entity_name, 
                fields, 
                is_aggregate=args.aggregate,
                description=args.description
            )
            
        elif args.command == "repository":
            # Create generator and generate repository
            generator = DDDGenerator(args.module_path, args.module_name)
            generator.create_repository(args.entity_name)
            
        elif args.command == "service":
            # Create generator and generate service
            generator = DDDGenerator(args.module_path, args.module_name)
            generator.create_service(args.entity_name)
            
        elif args.command == "provider":
            # Create generator and generate provider
            generator = DDDGenerator(args.module_path, args.module_name)
            generator.create_provider(args.entity_names)
            
        elif args.command == "endpoints":
            # Create generator and generate endpoints
            generator = DDDGenerator(args.module_path, args.module_name)
            generator.create_endpoints(args.entity_names)
            
        elif args.command == "module":
            # Parse entity specifications
            entity_specs = []
            for spec in args.entity_specs:
                parts = spec.split(':')
                if len(parts) < 2:
                    logger.error(f"Invalid entity specification: {spec}")
                    sys.exit(1)
                    
                entity_name = parts[0]
                field_specs = ':'.join(parts[1:])
                fields = parse_field_spec(field_specs)
                
                entity_specs.append({
                    "name": entity_name,
                    "fields": fields,
                    "is_aggregate": True
                })
                
            # Create generator and generate module
            generator = DDDGenerator(args.module_path, args.module_name)
            generator.create_module(entity_specs)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
        

if __name__ == "__main__":
    main()