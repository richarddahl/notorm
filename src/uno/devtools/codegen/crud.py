"""
CRUD (Create, Read, Update, Delete) code generation for Uno applications.

This module provides tools for generating complete CRUD functionality
including models, repositories, services, and API endpoints using the
Uno framework's conventions and patterns.
"""

import os
from typing import Dict, List, Optional, Any, Tuple, Set

from uno.devtools.codegen.model import generate_model
from uno.devtools.codegen.repository import generate_repository
from uno.devtools.codegen.service import generate_service
from uno.devtools.codegen.api import generate_api
from uno.devtools.codegen.formatter import format_code


def generate_crud(
    name: str,
    module_path: str,
    fields: Dict[str, str],
    table_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    with_api: bool = True,
    api_prefix: Optional[str] = None,
    api_tags: Optional[List[str]] = None,
    imports: Optional[Dict[str, List[str]]] = None,
    relationships: Optional[Dict[str, Dict[str, Any]]] = None,
    validators: Optional[Dict[str, List[str]]] = None,
    methods: Optional[Dict[str, List[Dict[str, Any]]]] = None
) -> Dict[str, Tuple[str, str]]:
    """
    Generate complete CRUD functionality for a model.
    
    Args:
        name: Name of the model class (CamelCase)
        module_path: Module path for imports (e.g. 'myapp.users')
        fields: Dictionary of field names and types
        table_name: Optional table name for database (default is pluralized snake_case of name)
        output_dir: Optional directory to write files to
        with_api: Whether to generate API endpoints
        api_prefix: Optional API prefix path (default is pluralized snake_case of name)
        api_tags: Optional list of tags for API endpoints
        imports: Optional dictionary of additional imports for each file type
        relationships: Optional dictionary defining model relationships
        validators: Optional dictionary of field validation rules
        methods: Optional dictionary of methods for repository, service, and API
        
    Returns:
        Dictionary of generated code with keys "model", "repository", "service", "api"
    """
    if imports is None:
        imports = {}
    
    if relationships is None:
        relationships = {}
    
    if validators is None:
        validators = {}
    
    if methods is None:
        methods = {}
    
    # Ensure output directory exists
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Generate model
    model_code, model_file = generate_model(
        name=name,
        fields=fields,
        table_name=table_name,
        relationships=relationships,
        validators=validators,
        imports=imports.get("model", []),
        output_dir=output_dir
    )
    
    # Generate repository
    repository_methods = methods.get("repository", [])
    repository_code, repository_file = generate_repository(
        name=name,
        module_path=module_path,
        fields=fields,
        methods=repository_methods,
        imports=imports.get("repository", []),
        output_dir=output_dir
    )
    
    # Generate service
    service_methods = methods.get("service", [])
    service_code, service_file = generate_service(
        name=name,
        module_path=module_path,
        fields={},  # Services typically don't need field properties
        methods=service_methods,
        dependencies=[],
        imports=imports.get("service", []),
        output_dir=output_dir
    )
    
    # Generate API if requested
    api_code = ""
    api_file = ""
    if with_api:
        api_methods = methods.get("api", [])
        api_code, api_file = generate_api(
            name=name,
            module_path=module_path,
            prefix=api_prefix,
            tags=api_tags,
            methods=api_methods,
            imports=imports.get("api", []),
            output_dir=output_dir
        )
    
    # Return generated code
    result = {
        "model": (model_code, model_file),
        "repository": (repository_code, repository_file),
        "service": (service_code, service_file)
    }
    
    if with_api:
        result["api"] = (api_code, api_file)
    
    return result