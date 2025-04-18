# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
FastAPI endpoints for the DTO schema operations.

This module provides FastAPI endpoints for working with schema definitions,
including creation, updating, validation, and transformation.
"""

import uuid
from typing import List, Optional, Dict, Any, Union

from fastapi import APIRouter, Depends, HTTPException

from uno.dependencies.fastapi_integration import depends_interface, get_interface
from uno.core.base.error import BaseError

from uno.dto.entities import (
    SchemaDefinition,
    SchemaId,
    SchemaConfiguration,
    SchemaCreationRequest,
    SchemaUpdateRequest,
    SchemaValidationRequest,
    ApiSchemaCreationRequest,
    PaginatedResult,
    PaginationMetadata,
)

from uno.dto.domain_services import (
    SchemaManagerServiceProtocol,
    SchemaValidationServiceProtocol,
    SchemaTransformationServiceProtocol,
)

# Create a router
router = APIRouter(
    prefix="/api/schemas",
    tags=["schemas"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
    },
)


# Endpoints for schema management
@router.post("/", response_model=SchemaDefinition, status_code=201)
async def create_schema(
    request: ApiSchemaCreationRequest,
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
) -> SchemaDefinition:
    """
    Create a new schema definition.
    
    Args:
        request: The schema creation request
        schema_manager: The schema manager service
        
    Returns:
        The created schema definition
    """
    try:
        # Convert API request to domain request
        creation_request = request.to_schema_creation_request()
        
        # Create the schema
        schema = await schema_manager.create_schema(creation_request)
        return schema
    except BaseError as e:
        if e.error_code == "SCHEMA_ALREADY_EXISTS":
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schema_id}", response_model=SchemaDefinition)
async def get_schema(
    schema_id: uuid.UUID,
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
) -> SchemaDefinition:
    """
    Get a schema definition by ID.
    
    Args:
        schema_id: The schema ID
        schema_manager: The schema manager service
        
    Returns:
        The schema definition
    """
    schema = await schema_manager.get_schema(schema_id)
    if not schema:
        raise HTTPException(
            status_code=404, detail=f"Schema with ID {schema_id} not found"
        )
    return schema


@router.get("/", response_model=PaginatedResult[SchemaDefinition])
async def list_schemas(
    page: int = 1,
    page_size: int = 20,
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
) -> PaginatedResult[SchemaDefinition]:
    """
    List schema definitions with pagination.
    
    Args:
        page: The page number
        page_size: The page size
        schema_manager: The schema manager service
        
    Returns:
        The paginated schema definitions
    """
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100
        
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get schemas
    schemas = await schema_manager.list_schemas(limit=page_size, offset=offset)
    
    # Prepare the response
    total_schemas = len(await schema_manager.list_schemas(limit=1000, offset=0))
    total_pages = (total_schemas + page_size - 1) // page_size
    
    # Create pagination metadata
    metadata = PaginationMetadata(
        page=page,
        page_size=page_size,
        total=total_schemas,
        pages=total_pages
    )
    
    return PaginatedResult(
        items=schemas,
        metadata=metadata
    )


@router.get("/by-name/{name}/{version}", response_model=SchemaDefinition)
async def get_schema_by_name_version(
    name: str,
    version: str,
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
) -> SchemaDefinition:
    """
    Get a schema definition by name and version.
    
    Args:
        name: The schema name
        version: The schema version
        schema_manager: The schema manager service
        
    Returns:
        The schema definition
    """
    schema = await schema_manager.get_schema_by_name_version(name, version)
    if not schema:
        raise HTTPException(
            status_code=404, 
            detail=f"Schema with name {name} and version {version} not found"
        )
    return schema


@router.put("/{schema_id}", response_model=SchemaDefinition)
async def update_schema(
    schema_id: uuid.UUID,
    request: SchemaUpdateRequest,
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
) -> SchemaDefinition:
    """
    Update a schema definition.
    
    Args:
        schema_id: The schema ID
        request: The schema update request
        schema_manager: The schema manager service
        
    Returns:
        The updated schema definition
    """
    try:
        schema = await schema_manager.update_schema(schema_id, request)
        return schema
    except BaseError as e:
        if e.error_code == "SCHEMA_NOT_FOUND":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{schema_id}", status_code=204)
async def delete_schema(
    schema_id: uuid.UUID,
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
) -> None:
    """
    Delete a schema definition.
    
    Args:
        schema_id: The schema ID
        schema_manager: The schema manager service
    """
    schema = await schema_manager.get_schema(schema_id)
    if not schema:
        raise HTTPException(
            status_code=404, detail=f"Schema with ID {schema_id} not found"
        )
        
    success = await schema_manager.delete_schema(schema_id)
    if not success:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete schema with ID {schema_id}"
        )


@router.post("/{schema_id}/validate", response_model=Dict[str, List[str]])
async def validate_data(
    schema_id: uuid.UUID,
    data: Dict[str, Any],
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
    validation_service: SchemaValidationServiceProtocol = Depends(
        depends_interface(SchemaValidationServiceProtocol)
    ),
) -> Dict[str, List[str]]:
    """
    Validate data against a schema.
    
    Args:
        schema_id: The schema ID
        data: The data to validate
        schema_manager: The schema manager service
        validation_service: The schema validation service
        
    Returns:
        Dictionary of validation errors by field name
    """
    # Get the schema
    schema = await schema_manager.get_schema(schema_id)
    if not schema:
        raise HTTPException(
            status_code=404, detail=f"Schema with ID {schema_id} not found"
        )
        
    # Get the schema configuration
    config = await schema_manager.get_schema_configuration(schema_id)
    
    # Validate the data
    errors = await validation_service.validate(schema, data, config)
    return errors


@router.post("/{schema_id}/transform/{target_schema_id}", response_model=Dict[str, Any])
async def transform_data(
    schema_id: uuid.UUID,
    target_schema_id: uuid.UUID,
    data: Dict[str, Any],
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
    transformation_service: SchemaTransformationServiceProtocol = Depends(
        depends_interface(SchemaTransformationServiceProtocol)
    ),
) -> Dict[str, Any]:
    """
    Transform data from one schema to another.
    
    Args:
        schema_id: The source schema ID
        target_schema_id: The target schema ID
        data: The data to transform
        schema_manager: The schema manager service
        transformation_service: The schema transformation service
        
    Returns:
        The transformed data
    """
    # Get the source schema
    source_schema = await schema_manager.get_schema(schema_id)
    if not source_schema:
        raise HTTPException(
            status_code=404, detail=f"Source schema with ID {schema_id} not found"
        )
        
    # Get the target schema
    target_schema = await schema_manager.get_schema(target_schema_id)
    if not target_schema:
        raise HTTPException(
            status_code=404, detail=f"Target schema with ID {target_schema_id} not found"
        )
        
    # Get the schema configuration
    config = await schema_manager.get_schema_configuration(target_schema_id)
    
    # Transform the data
    try:
        result = await transformation_service.transform(
            data, source_schema, target_schema, config
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Transformation error: {str(e)}"
        )


@router.post("/{schema_id}/generate-code/{language}", response_model=str)
async def generate_code(
    schema_id: uuid.UUID,
    language: str,
    config: Dict[str, Any] = {},
    schema_manager: SchemaManagerServiceProtocol = Depends(
        depends_interface(SchemaManagerServiceProtocol)
    ),
    transformation_service: SchemaTransformationServiceProtocol = Depends(
        depends_interface(SchemaTransformationServiceProtocol)
    ),
) -> str:
    """
    Generate code from a schema.
    
    Args:
        schema_id: The schema ID
        language: The programming language to generate code for
        config: Configuration for code generation
        schema_manager: The schema manager service
        transformation_service: The schema transformation service
        
    Returns:
        The generated code
    """
    # Get the schema
    schema = await schema_manager.get_schema(schema_id)
    if not schema:
        raise HTTPException(
            status_code=404, detail=f"Schema with ID {schema_id} not found"
        )
        
    # Generate the code
    try:
        code = await transformation_service.generate_code(schema, language, config)
        return code
    except BaseError as e:
        if e.error_code == "UNSUPPORTED_LANGUAGE":
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Code generation error: {str(e)}"
        )