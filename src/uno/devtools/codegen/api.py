"""
API code generation utilities for Uno applications.

This module provides tools for generating FastAPI endpoints for Uno models.
"""

import re
from typing import Dict, List, Optional, Set, Union, Any
import inspect
import logging
from pathlib import Path

from uno.devtools.codegen.formatter import format_code


logger = logging.getLogger("uno.codegen")


def generate_api(
    name: str,
    model_name: str,
    schema_name: Optional[str] = None,
    repository_name: Optional[str] = None,
    module_name: Optional[str] = None,
    include_imports: bool = True,
    include_docstrings: bool = True,
    include_crud: bool = True,
    include_pagination: bool = True,
    include_filtering: bool = True,
    include_validation: bool = True,
    id_type: str = "str",
    prefix: Optional[str] = None,
    tag: Optional[str] = None,
    security: Optional[List[Dict[str, Any]]] = None,
    endpoint_config: Optional[Dict[str, Dict[str, Any]]] = None,
    output_file: Optional[Union[str, Path]] = None,
) -> str:
    """Generate FastAPI endpoint code for a model.

    Args:
        name: Name of the router or endpoints module
        model_name: Name of the model class
        schema_name: Name of the schema class (defaults to {model_name}Schema)
        repository_name: Name of the repository class (defaults to {model_name}Repository)
        module_name: Optional module name for imports
        include_imports: Whether to include import statements
        include_docstrings: Whether to include docstrings
        include_crud: Whether to include CRUD endpoints
        include_pagination: Whether to include pagination
        include_filtering: Whether to include filtering
        include_validation: Whether to include validation
        id_type: Type of the model's ID field
        prefix: Optional API path prefix
        tag: Optional API tag
        security: Optional security requirements
        endpoint_config: Optional configuration for specific endpoints
        output_file: Optional file path to write the generated code to

    Returns:
        The generated code
    """
    # Prepare names
    if not schema_name:
        schema_name = f"{model_name}Schema"

    if not repository_name:
        repository_name = f"{model_name}Repository"

    if not prefix:
        prefix = f"/{_camel_to_snake(model_name)}s"

    if not tag:
        tag = f"{model_name}s"

    # Start building the code
    code_parts = []

    # Add imports
    if include_imports:
        imports = _generate_api_imports(
            module_name=module_name,
            model_name=model_name,
            schema_name=schema_name,
            repository_name=repository_name,
            include_crud=include_crud,
            include_pagination=include_pagination,
            include_filtering=include_filtering,
            include_validation=include_validation,
            id_type=id_type,
        )
        code_parts.append(imports)

    # Add router setup
    router_setup = _generate_router_setup(
        prefix=prefix,
        tag=tag,
        include_docstrings=include_docstrings,
    )
    code_parts.append(router_setup)

    # Add endpoints
    if include_crud:
        crud_endpoints = _generate_crud_endpoints(
            model_name=model_name,
            schema_name=schema_name,
            repository_name=repository_name,
            include_docstrings=include_docstrings,
            include_pagination=include_pagination,
            include_filtering=include_filtering,
            include_validation=include_validation,
            id_type=id_type,
            security=security,
            endpoint_config=endpoint_config,
        )
        code_parts.append(crud_endpoints)

    # Join code parts
    code = "\n\n".join(code_parts)

    # Format the code
    code = format_code(code)

    # Write to file if requested
    if output_file:
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
            logger.info(f"Generated API code written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing to {output_file}: {str(e)}")

    return code


def _generate_api_imports(
    module_name: Optional[str],
    model_name: str,
    schema_name: str,
    repository_name: str,
    include_crud: bool,
    include_pagination: bool,
    include_filtering: bool,
    include_validation: bool,
    id_type: str,
) -> str:
    """Generate import statements for API endpoints.

    Args:
        module_name: Optional module name for imports
        model_name: Name of the model class
        schema_name: Name of the schema class
        repository_name: Name of the repository class
        include_crud: Whether to include CRUD endpoints
        include_pagination: Whether to include pagination
        include_filtering: Whether to include filtering
        include_validation: Whether to include validation
        id_type: Type of the model's ID field

    Returns:
        Import statements as a string
    """
    imports = [
        "from typing import Dict, List, Optional, Set, Union, Any",
        "from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body",
    ]

    # Import model classes
    if module_name:
        base_module = f"{module_name}"
        imports.append(f"from {base_module}.model import {model_name}")
        imports.append(f"from {base_module}.schema import {schema_name}")
        imports.append(f"from {base_module}.repository import {repository_name}")
    else:
        imports.append(f"from uno.domain.base.model import {model_name}")
        imports.append(f"from uno.schema import {schema_name}")
        imports.append(f"from uno.repository import {repository_name}")

    # Import session dependency
    imports.append("from uno.dependencies.database import get_db_session")
    imports.append("from sqlalchemy.ext.asyncio import AsyncSession")

    # Additional imports for pagination
    if include_pagination:
        imports.append("from uno.api.pagination import Page, Params")

    # Additional imports for filtering
    if include_filtering:
        imports.append("from uno.queries.filter import Filter")

    # Type imports
    if id_type.lower() == "uuid":
        imports.append("from uuid import UUID")

    # Additional imports for validation
    if include_validation:
        imports.append("from pydantic import BaseModel, Field")

    return "\n".join(imports)


def _generate_router_setup(
    prefix: str,
    tag: str,
    include_docstrings: bool,
) -> str:
    """Generate router setup code.

    Args:
        prefix: API path prefix
        tag: API tag
        include_docstrings: Whether to include docstrings

    Returns:
        Router setup code as a string
    """
    lines = []

    # Create router
    lines.append(f'router = APIRouter(prefix="{prefix}", tags=["{tag}"])')

    # Add repository dependency
    lines.append("")
    lines.append("def get_repository(session: AsyncSession = Depends(get_db_session)):")
    if include_docstrings:
        lines.append('    """Get repository instance.')
        lines.append("")
        lines.append("    Args:")
        lines.append("        session: Database session")
        lines.append("")
        lines.append("    Returns:")
        lines.append("        Repository instance")
        lines.append('    """')
    lines.append(f"    return {repository_name}(session=session)")

    return "\n".join(lines)


def _generate_crud_endpoints(
    model_name: str,
    schema_name: str,
    repository_name: str,
    include_docstrings: bool,
    include_pagination: bool,
    include_filtering: bool,
    include_validation: bool,
    id_type: str,
    security: Optional[List[Dict[str, Any]]] = None,
    endpoint_config: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """Generate CRUD endpoint definitions.

    Args:
        model_name: Name of the model class
        schema_name: Name of the schema class
        repository_name: Name of the repository class
        include_docstrings: Whether to include docstrings
        include_pagination: Whether to include pagination
        include_filtering: Whether to include filtering
        include_validation: Whether to include validation
        id_type: Type of the model's ID field
        security: Optional security requirements
        endpoint_config: Optional configuration for specific endpoints

    Returns:
        CRUD endpoint definitions as a string
    """
    lines = []

    # Create validation models if requested
    if include_validation:
        validation_models = _generate_validation_models(
            model_name=model_name,
            include_docstrings=include_docstrings,
        )
        lines.append(validation_models)

    # Generate endpoints

    # GET all endpoint
    get_all_enabled = True
    if endpoint_config and "get_all" in endpoint_config:
        get_all_enabled = endpoint_config["get_all"].get("enabled", True)

    if get_all_enabled:
        get_all = _generate_get_all_endpoint(
            model_name=model_name,
            schema_name=schema_name,
            include_docstrings=include_docstrings,
            include_pagination=include_pagination,
            include_filtering=include_filtering,
            security=security,
            config=endpoint_config.get("get_all") if endpoint_config else None,
        )
        lines.append(get_all)

    # GET by ID endpoint
    get_by_id_enabled = True
    if endpoint_config and "get_by_id" in endpoint_config:
        get_by_id_enabled = endpoint_config["get_by_id"].get("enabled", True)

    if get_by_id_enabled:
        get_by_id = _generate_get_by_id_endpoint(
            model_name=model_name,
            schema_name=schema_name,
            include_docstrings=include_docstrings,
            id_type=id_type,
            security=security,
            config=endpoint_config.get("get_by_id") if endpoint_config else None,
        )
        lines.append(get_by_id)

    # POST (create) endpoint
    create_enabled = True
    if endpoint_config and "create" in endpoint_config:
        create_enabled = endpoint_config["create"].get("enabled", True)

    if create_enabled:
        create = _generate_create_endpoint(
            model_name=model_name,
            schema_name=schema_name,
            include_docstrings=include_docstrings,
            include_validation=include_validation,
            security=security,
            config=endpoint_config.get("create") if endpoint_config else None,
        )
        lines.append(create)

    # PUT (update) endpoint
    update_enabled = True
    if endpoint_config and "update" in endpoint_config:
        update_enabled = endpoint_config["update"].get("enabled", True)

    if update_enabled:
        update = _generate_update_endpoint(
            model_name=model_name,
            schema_name=schema_name,
            include_docstrings=include_docstrings,
            include_validation=include_validation,
            id_type=id_type,
            security=security,
            config=endpoint_config.get("update") if endpoint_config else None,
        )
        lines.append(update)

    # DELETE endpoint
    delete_enabled = True
    if endpoint_config and "delete" in endpoint_config:
        delete_enabled = endpoint_config["delete"].get("enabled", True)

    if delete_enabled:
        delete = _generate_delete_endpoint(
            model_name=model_name,
            include_docstrings=include_docstrings,
            id_type=id_type,
            security=security,
            config=endpoint_config.get("delete") if endpoint_config else None,
        )
        lines.append(delete)

    return "\n\n".join(lines)


def _generate_validation_models(
    model_name: str,
    include_docstrings: bool,
) -> str:
    """Generate Pydantic validation models.

    Args:
        model_name: Name of the model class
        include_docstrings: Whether to include docstrings

    Returns:
        Validation model definitions as a string
    """
    lines = []

    # Create model
    lines.append(f"class Create{model_name}(BaseModel):")
    if include_docstrings:
        lines.append(f'    """{model_name} creation model."""')
    lines.append("    pass  # Add fields as needed")

    # Update model
    lines.append("")
    lines.append(f"class Update{model_name}(BaseModel):")
    if include_docstrings:
        lines.append(f'    """{model_name} update model."""')
    lines.append("    pass  # Add fields as needed")

    return "\n".join(lines)


def _generate_get_all_endpoint(
    model_name: str,
    schema_name: str,
    include_docstrings: bool,
    include_pagination: bool,
    include_filtering: bool,
    security: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate GET all endpoint.

    Args:
        model_name: Name of the model class
        schema_name: Name of the schema class
        include_docstrings: Whether to include docstrings
        include_pagination: Whether to include pagination
        include_filtering: Whether to include filtering
        security: Optional security requirements
        config: Optional endpoint-specific configuration

    Returns:
        GET all endpoint definition as a string
    """
    lines = []

    # Endpoint decorator
    path = config.get("path", "") if config else ""
    response_model = f"List[{schema_name}]"

    if include_pagination:
        response_model = f"Page[{schema_name}]"

    decorator = f'@router.get("{path}", response_model={response_model}'

    # Add security if provided
    if security:
        security_args = ", ".join(f"dependencies=[{s}]" for s in security)
        decorator += f", {security_args}"

    lines.append(decorator + ")")

    # Endpoint function
    params = []

    if include_pagination:
        params.append("params: Params = Depends()")

    if include_filtering:
        params.append(f"filters: Optional[List[Filter]] = Query(None)")

    params.append(f"repository: {repository_name} = Depends(get_repository)")

    func_def = f"async def get_all_{_camel_to_snake(model_name)}s({', '.join(params)}):"
    lines.append(func_def)

    # Docstring
    if include_docstrings:
        lines.append(f'    """Get all {model_name}s.')
        lines.append("")
        if include_pagination:
            lines.append("    Args:")
            lines.append("        params: Pagination parameters")
            if include_filtering:
                lines.append("        filters: Optional filters")
            lines.append("        repository: Repository instance")
        elif include_filtering:
            lines.append("    Args:")
            lines.append("        filters: Optional filters")
            lines.append("        repository: Repository instance")
        else:
            lines.append("    Args:")
            lines.append("        repository: Repository instance")
        lines.append("")
        lines.append("    Returns:")
        if include_pagination:
            lines.append(f"        Paginated list of {model_name}s")
        else:
            lines.append(f"        List of {model_name}s")
        lines.append('    """')

    # Implementation
    if include_pagination:
        if include_filtering:
            lines.append(
                f"    return await repository.get_paginated(params=params, filters=filters)"
            )
        else:
            lines.append(f"    return await repository.get_paginated(params=params)")
    else:
        if include_filtering:
            lines.append(f"    items = await repository.get_filtered(filters=filters)")
        else:
            lines.append(f"    items = await repository.get_all()")
        lines.append(f"    return items")

    return "\n".join(lines)


def _generate_get_by_id_endpoint(
    model_name: str,
    schema_name: str,
    include_docstrings: bool,
    id_type: str,
    security: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate GET by ID endpoint.

    Args:
        model_name: Name of the model class
        schema_name: Name of the schema class
        include_docstrings: Whether to include docstrings
        id_type: Type of the model's ID field
        security: Optional security requirements
        config: Optional endpoint-specific configuration

    Returns:
        GET by ID endpoint definition as a string
    """
    lines = []

    # Endpoint decorator
    path = config.get("path", "/{id}") if config else "/{id}"
    response_model = schema_name

    decorator = f'@router.get("{path}", response_model={response_model}'

    # Add security if provided
    if security:
        security_args = ", ".join(f"dependencies=[{s}]" for s in security)
        decorator += f", {security_args}"

    lines.append(decorator + ")")

    # Endpoint function
    func_def = f"async def get_{_camel_to_snake(model_name)}_by_id(id: {id_type} = Path(...), repository: {repository_name} = Depends(get_repository)):"
    lines.append(func_def)

    # Docstring
    if include_docstrings:
        lines.append(f'    """Get a {model_name} by ID.')
        lines.append("")
        lines.append("    Args:")
        lines.append(f"        id: The {model_name} ID")
        lines.append("        repository: Repository instance")
        lines.append("")
        lines.append("    Returns:")
        lines.append(f"        The {model_name}")
        lines.append("")
        lines.append("    Raises:")
        lines.append("        HTTPException: If the item is not found")
        lines.append('    """')

    # Implementation
    lines.append(f"    item = await repository.get_by_id(id)")
    lines.append(f"    if item is None:")
    lines.append(
        f'        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_name} not found")'
    )
    lines.append(f"    return item")

    return "\n".join(lines)


def _generate_create_endpoint(
    model_name: str,
    schema_name: str,
    include_docstrings: bool,
    include_validation: bool,
    security: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate POST (create) endpoint.

    Args:
        model_name: Name of the model class
        schema_name: Name of the schema class
        include_docstrings: Whether to include docstrings
        include_validation: Whether to include validation
        security: Optional security requirements
        config: Optional endpoint-specific configuration

    Returns:
        POST endpoint definition as a string
    """
    lines = []

    # Endpoint decorator
    path = config.get("path", "") if config else ""
    response_model = schema_name

    decorator = f'@router.post("{path}", response_model={response_model}, status_code=status.HTTP_201_CREATED'

    # Add security if provided
    if security:
        security_args = ", ".join(f"dependencies=[{s}]" for s in security)
        decorator += f", {security_args}"

    lines.append(decorator + ")")

    # Endpoint function
    item_param = f"item: Create{model_name}" if include_validation else f"item: dict"
    func_def = f"async def create_{_camel_to_snake(model_name)}({item_param} = Body(...), repository: {repository_name} = Depends(get_repository)):"
    lines.append(func_def)

    # Docstring
    if include_docstrings:
        lines.append(f'    """Create a new {model_name}.')
        lines.append("")
        lines.append("    Args:")
        lines.append(f"        item: The {model_name} data")
        lines.append("        repository: Repository instance")
        lines.append("")
        lines.append("    Returns:")
        lines.append(f"        The created {model_name}")
        lines.append('    """')

    # Implementation
    if include_validation:
        lines.append(f"    created_item = await repository.create(**item.dict())")
    else:
        lines.append(f"    created_item = await repository.create(**item)")
    lines.append(f"    return created_item")

    return "\n".join(lines)


def _generate_update_endpoint(
    model_name: str,
    schema_name: str,
    include_docstrings: bool,
    include_validation: bool,
    id_type: str,
    security: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate PUT (update) endpoint.

    Args:
        model_name: Name of the model class
        schema_name: Name of the schema class
        include_docstrings: Whether to include docstrings
        include_validation: Whether to include validation
        id_type: Type of the model's ID field
        security: Optional security requirements
        config: Optional endpoint-specific configuration

    Returns:
        PUT endpoint definition as a string
    """
    lines = []

    # Endpoint decorator
    path = config.get("path", "/{id}") if config else "/{id}"
    response_model = schema_name

    decorator = f'@router.put("{path}", response_model={response_model}'

    # Add security if provided
    if security:
        security_args = ", ".join(f"dependencies=[{s}]" for s in security)
        decorator += f", {security_args}"

    lines.append(decorator + ")")

    # Endpoint function
    item_param = f"item: Update{model_name}" if include_validation else f"item: dict"
    func_def = f"async def update_{_camel_to_snake(model_name)}(id: {id_type} = Path(...), {item_param} = Body(...), repository: {repository_name} = Depends(get_repository)):"
    lines.append(func_def)

    # Docstring
    if include_docstrings:
        lines.append(f'    """Update a {model_name}.')
        lines.append("")
        lines.append("    Args:")
        lines.append(f"        id: The {model_name} ID")
        lines.append(f"        item: The updated {model_name} data")
        lines.append("        repository: Repository instance")
        lines.append("")
        lines.append("    Returns:")
        lines.append(f"        The updated {model_name}")
        lines.append("")
        lines.append("    Raises:")
        lines.append("        HTTPException: If the item is not found")
        lines.append('    """')

    # Implementation
    if include_validation:
        lines.append(
            f"    updated_item = await repository.update(id, **item.dict(exclude_unset=True))"
        )
    else:
        lines.append(f"    updated_item = await repository.update(id, **item)")
    lines.append(f"    if updated_item is None:")
    lines.append(
        f'        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_name} not found")'
    )
    lines.append(f"    return updated_item")

    return "\n".join(lines)


def _generate_delete_endpoint(
    model_name: str,
    include_docstrings: bool,
    id_type: str,
    security: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate DELETE endpoint.

    Args:
        model_name: Name of the model class
        include_docstrings: Whether to include docstrings
        id_type: Type of the model's ID field
        security: Optional security requirements
        config: Optional endpoint-specific configuration

    Returns:
        DELETE endpoint definition as a string
    """
    lines = []

    # Endpoint decorator
    path = config.get("path", "/{id}") if config else "/{id}"

    decorator = f'@router.delete("{path}", status_code=status.HTTP_204_NO_CONTENT'

    # Add security if provided
    if security:
        security_args = ", ".join(f"dependencies=[{s}]" for s in security)
        decorator += f", {security_args}"

    lines.append(decorator + ")")

    # Endpoint function
    func_def = f"async def delete_{_camel_to_snake(model_name)}(id: {id_type} = Path(...), repository: {repository_name} = Depends(get_repository)):"
    lines.append(func_def)

    # Docstring
    if include_docstrings:
        lines.append(f'    """Delete a {model_name}.')
        lines.append("")
        lines.append("    Args:")
        lines.append(f"        id: The {model_name} ID")
        lines.append("        repository: Repository instance")
        lines.append("")
        lines.append("    Raises:")
        lines.append("        HTTPException: If the item is not found")
        lines.append('    """')

    # Implementation
    lines.append(f"    deleted = await repository.delete(id)")
    lines.append(f"    if not deleted:")
    lines.append(
        f'        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_name} not found")'
    )
    lines.append(f"    return None")

    return "\n".join(lines)


def _camel_to_snake(name: str) -> str:
    """Convert a CamelCase string to snake_case.

    Args:
        name: CamelCase string

    Returns:
        snake_case string
    """
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
