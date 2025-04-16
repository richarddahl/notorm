# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain endpoints for the Schema module.

This module defines FastAPI endpoints for the Schema module,
exposing schema management functionality via HTTP.
"""

from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from uno.core.errors.result import Failure
from uno.schema.entities import (
    SchemaId, SchemaType, 
    SchemaCreationRequest, SchemaUpdateRequest, SchemaValidationRequest,
    ApiSchemaCreationRequest
)
from uno.schema.domain_services import (
    SchemaManagerServiceProtocol,
    SchemaValidationServiceProtocol,
    SchemaTransformationServiceProtocol
)
from uno.schema.domain_provider import SchemaProvider


# Response Models

class SchemaResponse(Dict[str, Any]):
    """Response model for schema responses."""
    pass


class SchemaListResponse(Dict[str, Any]):
    """Response model for schema list responses."""
    pass


class ValidationResponse(Dict[str, Any]):
    """Response model for validation responses."""
    pass


# Dependency Injection

def get_schema_manager() -> SchemaManagerServiceProtocol:
    """Get the schema manager service."""
    return SchemaProvider.get_schema_manager()


def get_schema_validation() -> SchemaValidationServiceProtocol:
    """Get the schema validation service."""
    return SchemaProvider.get_schema_validation()


def get_schema_transformation() -> SchemaTransformationServiceProtocol:
    """Get the schema transformation service."""
    return SchemaProvider.get_schema_transformation()


# Router

router = APIRouter(prefix="/api/schemas", tags=["schemas"])


# Schema Definition Endpoints

@router.post("", response_model=SchemaResponse)
async def create_schema(
    request: SchemaCreationRequest,
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> SchemaResponse:
    """
    Create a new schema definition.
    
    Args:
        request: The schema creation request
        schema_manager: The schema manager service
        
    Returns:
        The created schema definition
        
    Raises:
        HTTPException: If schema creation fails
    """
    result = schema_manager.create_schema_definition(request)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error.message
        )
    
    schema = result.value
    return schema.to_dict()


@router.get("", response_model=SchemaListResponse)
async def list_schemas(
    schema_type: Optional[str] = Query(None, description="Filter by schema type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Page size"),
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> SchemaListResponse:
    """
    List schema definitions with optional filtering.
    
    Args:
        schema_type: Optional schema type to filter by
        page: Page number for pagination
        page_size: Items per page
        schema_manager: The schema manager service
        
    Returns:
        Paginated schema definitions
        
    Raises:
        HTTPException: If listing schemas fails
    """
    # Convert schema type string to enum if provided
    schema_type_enum = None
    if schema_type:
        try:
            schema_type_enum = SchemaType[schema_type]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid schema type: {schema_type}"
            )
    
    result = schema_manager.list_schema_definitions(schema_type_enum, page, page_size)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    paginated_result = result.value
    return paginated_result.to_dict()


@router.get("/{schema_id}", response_model=SchemaResponse)
async def get_schema(
    schema_id: str,
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> SchemaResponse:
    """
    Get a schema definition by ID.
    
    Args:
        schema_id: The ID of the schema to retrieve
        schema_manager: The schema manager service
        
    Returns:
        The schema definition
        
    Raises:
        HTTPException: If schema retrieval fails
    """
    result = schema_manager.get_schema_definition(SchemaId(schema_id))
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error.message
        )
    
    schema = result.value
    return schema.to_dict()


@router.put("/{schema_id}", response_model=SchemaResponse)
async def update_schema(
    schema_id: str,
    request: SchemaUpdateRequest,
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> SchemaResponse:
    """
    Update a schema definition.
    
    Args:
        schema_id: The ID of the schema to update
        request: The schema update request
        schema_manager: The schema manager service
        
    Returns:
        The updated schema definition
        
    Raises:
        HTTPException: If schema update fails
    """
    result = schema_manager.update_schema_definition(SchemaId(schema_id), request)
    
    if isinstance(result, Failure):
        if result.error.code == "SCHEMA_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )
    
    schema = result.value
    return schema.to_dict()


@router.delete("/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schema(
    schema_id: str,
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> None:
    """
    Delete a schema definition.
    
    Args:
        schema_id: The ID of the schema to delete
        schema_manager: The schema manager service
        
    Raises:
        HTTPException: If schema deletion fails
    """
    result = schema_manager.delete_schema_definition(SchemaId(schema_id))
    
    if isinstance(result, Failure):
        if result.error.code == "SCHEMA_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )


# Schema Validation Endpoints

@router.post("/validate", response_model=ValidationResponse)
async def validate_data(
    request: SchemaValidationRequest,
    schema_validation: SchemaValidationServiceProtocol = Depends(get_schema_validation)
) -> ValidationResponse:
    """
    Validate data against a schema.
    
    Args:
        request: The validation request
        schema_validation: The schema validation service
        
    Returns:
        The validated data
        
    Raises:
        HTTPException: If validation fails
    """
    result = schema_validation.validate_data(SchemaId(request.schema_id), request.data)
    
    if isinstance(result, Failure):
        if result.error.code == "SCHEMA_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )
        elif result.error.code == "VALIDATION_ERROR":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": result.error.message,
                    "details": result.error.details if hasattr(result.error, "details") else None
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )
    
    return result.value


# Schema Configuration Endpoints

@router.post("/configs/{name}", status_code=status.HTTP_201_CREATED)
async def create_config(
    name: str,
    config: Dict[str, Any],
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> Dict[str, Any]:
    """
    Create a schema configuration.
    
    Args:
        name: The name of the configuration
        config: The configuration
        schema_manager: The schema manager service
        
    Returns:
        The created configuration
        
    Raises:
        HTTPException: If configuration creation fails
    """
    from uno.schema.entities import SchemaConfiguration
    
    # Create a schema configuration from the dictionary
    schema_config = SchemaConfiguration(
        schema_base=config.get("schema_base", None),
        exclude_fields=set(config.get("exclude_fields", [])),
        include_fields=set(config.get("include_fields", []))
    )
    
    # Validate the configuration
    validation_result = schema_config.validate()
    if isinstance(validation_result, Failure):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result.error.message
        )
    
    # Add the configuration
    result = schema_manager.add_schema_configuration(name, schema_config)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error.message
        )
    
    return {"name": name, "config": schema_config.to_dict()}


@router.get("/configs", response_model=List[str])
async def list_configs(
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> List[str]:
    """
    List all schema configurations.
    
    Args:
        schema_manager: The schema manager service
        
    Returns:
        List of configuration names
        
    Raises:
        HTTPException: If listing configurations fails
    """
    result = schema_manager.list_schema_configurations()
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


@router.get("/configs/{name}", response_model=Dict[str, Any])
async def get_config(
    name: str,
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> Dict[str, Any]:
    """
    Get a schema configuration by name.
    
    Args:
        name: The name of the configuration to retrieve
        schema_manager: The schema manager service
        
    Returns:
        The configuration
        
    Raises:
        HTTPException: If configuration retrieval fails
    """
    result = schema_manager.get_schema_configuration(name)
    
    if isinstance(result, Failure):
        if result.error.code == "SCHEMA_CONFIG_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )
    
    config = result.value
    return {"name": name, "config": config.to_dict()}


@router.delete("/configs/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    name: str,
    schema_manager: SchemaManagerServiceProtocol = Depends(get_schema_manager)
) -> None:
    """
    Delete a schema configuration.
    
    Args:
        name: The name of the configuration to delete
        schema_manager: The schema manager service
        
    Raises:
        HTTPException: If configuration deletion fails
    """
    result = schema_manager.delete_schema_configuration(name)
    
    if isinstance(result, Failure):
        if result.error.code == "SCHEMA_CONFIG_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )


# API Schema Endpoints

@router.post("/api-schemas", response_model=Dict[str, Any])
async def create_api_schemas(
    request: ApiSchemaCreationRequest,
    schema_transformation: SchemaTransformationServiceProtocol = Depends(get_schema_transformation)
) -> Dict[str, Any]:
    """
    Create a complete set of API schemas.
    
    Args:
        request: The API schema creation request
        schema_transformation: The schema transformation service
        
    Returns:
        The created schema definitions
        
    Raises:
        HTTPException: If schema creation fails
    """
    result = schema_transformation.create_api_schemas(request)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error.message
        )
    
    # Convert schemas to dictionary representation
    schemas_dict = {
        key: schema.to_dict() for key, schema in result.value.items()
    }
    
    return {
        "entity_name": request.entity_name,
        "schemas": schemas_dict
    }