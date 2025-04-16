"""
Domain endpoints for the SQL module.

This module provides API endpoints for the SQL module using FastAPI.
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field, validator

from uno.core.result import Failure
from uno.dependencies.fastapi_integration import inject_dependency

from uno.sql.entities import (
    SQLStatementId,
    SQLEmitterId,
    SQLConfigId,
    SQLStatementType,
    SQLFunction,
    SQLTrigger,
    DatabaseConnectionInfo,
    SQLConfiguration
)
from uno.sql.domain_services import (
    SQLStatementServiceProtocol,
    SQLEmitterServiceProtocol,
    SQLConfigurationServiceProtocol,
    SQLFunctionServiceProtocol,
    SQLTriggerServiceProtocol,
    SQLConnectionServiceProtocol
)


# Schema models for API request/response
class SQLStatementTypeEnum(str, Enum):
    """Enum for SQL statement types in API."""
    FUNCTION = "function"
    TRIGGER = "trigger"
    INDEX = "index"
    CONSTRAINT = "constraint"
    GRANT = "grant"
    VIEW = "view"
    PROCEDURE = "procedure"
    TABLE = "table"
    ROLE = "role"
    SCHEMA = "schema"
    EXTENSION = "extension"
    DATABASE = "database"
    INSERT = "insert"


class SQLFunctionLanguageEnum(str, Enum):
    """Enum for SQL function languages in API."""
    PLPGSQL = "plpgsql"
    SQL = "sql"
    PYTHON = "plpython3u"
    PLTCL = "pltcl"


class SQLFunctionVolatilityEnum(str, Enum):
    """Enum for SQL function volatility types in API."""
    VOLATILE = "VOLATILE"
    STABLE = "STABLE"
    IMMUTABLE = "IMMUTABLE"


class SQLStatementCreateRequest(BaseModel):
    """Request model for creating a SQL statement."""
    name: str
    statement_type: SQLStatementTypeEnum
    sql: str
    depends_on: List[str] = Field(default_factory=list)


class SQLStatementUpdateRequest(BaseModel):
    """Request model for updating a SQL statement."""
    sql: Optional[str] = None
    depends_on: Optional[List[str]] = None


class SQLStatementResponse(BaseModel):
    """Response model for a SQL statement."""
    id: str
    name: str
    type: SQLStatementTypeEnum
    sql: str
    depends_on: List[str]
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class SQLEmitterCreateRequest(BaseModel):
    """Request model for creating a SQL emitter."""
    name: str
    statement_types: List[SQLStatementTypeEnum]
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class SQLEmitterUpdateRequest(BaseModel):
    """Request model for updating a SQL emitter."""
    statement_types: Optional[List[SQLStatementTypeEnum]] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class SQLEmitterResponse(BaseModel):
    """Response model for a SQL emitter."""
    id: str
    name: str
    description: Optional[str]
    statement_types: List[SQLStatementTypeEnum]
    configuration: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class DatabaseConnectionInfoRequest(BaseModel):
    """Request model for database connection information."""
    db_name: str
    db_user: str
    db_host: str
    db_port: int = 5432
    db_schema: str = "public"
    admin_role: Optional[str] = None
    writer_role: Optional[str] = None
    reader_role: Optional[str] = None


class DatabaseConnectionInfoResponse(BaseModel):
    """Response model for database connection information."""
    id: str
    db_name: str
    db_user: str
    db_host: str
    db_port: int
    db_schema: str
    admin_role: str
    writer_role: str
    reader_role: str

    class Config:
        """Pydantic config."""
        from_attributes = True


class SQLConfigurationCreateRequest(BaseModel):
    """Request model for creating a SQL configuration."""
    name: str
    description: Optional[str] = None
    connection_info: Optional[DatabaseConnectionInfoRequest] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SQLConfigurationUpdateRequest(BaseModel):
    """Request model for updating a SQL configuration."""
    name: Optional[str] = None
    description: Optional[str] = None
    connection_info: Optional[DatabaseConnectionInfoRequest] = None
    metadata: Optional[Dict[str, Any]] = None


class SQLConfigurationResponse(BaseModel):
    """Response model for a SQL configuration."""
    id: str
    name: str
    description: Optional[str]
    connection_info: Optional[DatabaseConnectionInfoResponse] = None
    emitters: List[SQLEmitterResponse]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class SQLFunctionCreateRequest(BaseModel):
    """Request model for creating a SQL function."""
    schema: str
    name: str
    body: str
    args: str = ""
    return_type: str = "TRIGGER"
    language: SQLFunctionLanguageEnum = SQLFunctionLanguageEnum.PLPGSQL
    volatility: SQLFunctionVolatilityEnum = SQLFunctionVolatilityEnum.VOLATILE
    security_definer: bool = False


class SQLFunctionUpdateRequest(BaseModel):
    """Request model for updating a SQL function."""
    body: Optional[str] = None
    args: Optional[str] = None
    return_type: Optional[str] = None
    language: Optional[SQLFunctionLanguageEnum] = None
    volatility: Optional[SQLFunctionVolatilityEnum] = None
    security_definer: Optional[bool] = None


class SQLFunctionResponse(BaseModel):
    """Response model for a SQL function."""
    id: str
    schema: str
    name: str
    body: str
    args: str
    return_type: str
    language: SQLFunctionLanguageEnum
    volatility: SQLFunctionVolatilityEnum
    security_definer: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class SQLTriggerCreateRequest(BaseModel):
    """Request model for creating a SQL trigger."""
    schema: str
    name: str
    table: str
    function_name: str
    events: List[str]
    when: Optional[str] = None
    for_each: str = "ROW"


class SQLTriggerUpdateRequest(BaseModel):
    """Request model for updating a SQL trigger."""
    events: Optional[List[str]] = None
    when: Optional[str] = None
    for_each: Optional[str] = None


class SQLTriggerResponse(BaseModel):
    """Response model for a SQL trigger."""
    id: str
    schema: str
    name: str
    table: str
    function_name: str
    events: List[str]
    when: Optional[str]
    for_each: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class SQLExecutionResponse(BaseModel):
    """Response model for a SQL execution."""
    id: str
    statement_id: str
    executed_at: datetime
    duration_ms: float
    success: bool
    error_message: Optional[str]

    class Config:
        """Pydantic config."""
        from_attributes = True


class SQLExecuteRequest(BaseModel):
    """Request model for executing SQL."""
    sql: str
    params: Dict[str, Any] = Field(default_factory=dict)


class SQLExecuteResponse(BaseModel):
    """Response model for SQL execution result."""
    result: Any
    row_count: Optional[int] = None
    duration_ms: float


# Create API router
router = APIRouter(prefix="/api/sql", tags=["sql"])


def create_entity_response(entity, response_class):
    """Helper to convert domain entities to response models."""
    # Handle SQL statement types
    if hasattr(entity, 'type') and isinstance(entity.type, SQLStatementType):
        entity_dict = entity.__dict__.copy()
        entity_dict['type'] = SQLStatementTypeEnum(entity.type.value)
        return response_class(**entity_dict)
    
    # Handle SQL function languages
    if hasattr(entity, 'language') and hasattr(entity.language, 'value'):
        entity_dict = entity.__dict__.copy()
        entity_dict['language'] = SQLFunctionLanguageEnum(entity.language.value)
        return response_class(**entity_dict)
    
    # Handle SQL function volatility
    if hasattr(entity, 'volatility') and hasattr(entity.volatility, 'value'):
        entity_dict = entity.__dict__.copy()
        entity_dict['volatility'] = SQLFunctionVolatilityEnum(entity.volatility.value)
        return response_class(**entity_dict)
    
    # Handle ValueObjects (IDs)
    entity_dict = entity.__dict__.copy()
    for key, value in entity_dict.items():
        if hasattr(value, 'value') and key.endswith('_id'):
            entity_dict[key] = value.value
    
    # For configurations with emitters
    if isinstance(entity, SQLConfiguration) and hasattr(entity, 'emitters'):
        entity_dict = entity.__dict__.copy()
        
        # Convert emitters
        entity_dict['emitters'] = [
            create_entity_response(emitter, SQLEmitterResponse) 
            for emitter in entity.emitters
        ]
        
        # Convert connection_info
        if entity.connection_info:
            entity_dict['connection_info'] = DatabaseConnectionInfoResponse(
                **entity.connection_info.__dict__
            )
        
        return response_class(**entity_dict)
    
    return response_class(**entity_dict)


# SQL Statement endpoints
@router.post("/statements", response_model=SQLStatementResponse, status_code=201)
async def create_statement(
    request: SQLStatementCreateRequest,
    statement_service: SQLStatementServiceProtocol = Depends(inject_dependency(SQLStatementServiceProtocol))
):
    """Create a new SQL statement."""
    result = await statement_service.create_statement(
        name=request.name,
        statement_type=SQLStatementType(request.statement_type.value),
        sql=request.sql,
        depends_on=request.depends_on
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create SQL statement")
    
    return create_entity_response(result.value, SQLStatementResponse)


@router.get("/statements", response_model=List[SQLStatementResponse])
async def list_statements(
    statement_type: Optional[SQLStatementTypeEnum] = Query(None, description="Filter by statement type"),
    statement_service: SQLStatementServiceProtocol = Depends(inject_dependency(SQLStatementServiceProtocol))
):
    """List all SQL statements."""
    if statement_type:
        result = await statement_service.get_statements_by_type(SQLStatementType(statement_type.value))
    else:
        result = await statement_service.list_statements()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list SQL statements")
    
    return [create_entity_response(statement, SQLStatementResponse) for statement in result.value]


@router.get("/statements/{statement_id}", response_model=SQLStatementResponse)
async def get_statement(
    statement_id: str = Path(..., description="The statement ID"),
    statement_service: SQLStatementServiceProtocol = Depends(inject_dependency(SQLStatementServiceProtocol))
):
    """Get a SQL statement by ID."""
    result = await statement_service.get_statement(SQLStatementId(statement_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL statement")
    
    return create_entity_response(result.value, SQLStatementResponse)


@router.get("/statements/by-name/{name}", response_model=SQLStatementResponse)
async def get_statement_by_name(
    name: str = Path(..., description="The statement name"),
    statement_service: SQLStatementServiceProtocol = Depends(inject_dependency(SQLStatementServiceProtocol))
):
    """Get a SQL statement by name."""
    result = await statement_service.get_statement_by_name(name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL statement")
    
    return create_entity_response(result.value, SQLStatementResponse)


@router.put("/statements/{statement_id}", response_model=SQLStatementResponse)
async def update_statement(
    request: SQLStatementUpdateRequest,
    statement_id: str = Path(..., description="The statement ID"),
    statement_service: SQLStatementServiceProtocol = Depends(inject_dependency(SQLStatementServiceProtocol))
):
    """Update a SQL statement."""
    result = await statement_service.update_statement(
        statement_id=SQLStatementId(statement_id),
        sql=request.sql,
        depends_on=request.depends_on
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update SQL statement")
    
    return create_entity_response(result.value, SQLStatementResponse)


@router.delete("/statements/{statement_id}", status_code=204)
async def delete_statement(
    statement_id: str = Path(..., description="The statement ID"),
    statement_service: SQLStatementServiceProtocol = Depends(inject_dependency(SQLStatementServiceProtocol))
):
    """Delete a SQL statement."""
    result = await statement_service.delete_statement(SQLStatementId(statement_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete SQL statement")


# SQL Emitter endpoints
@router.post("/emitters", response_model=SQLEmitterResponse, status_code=201)
async def create_emitter(
    request: SQLEmitterCreateRequest,
    emitter_service: SQLEmitterServiceProtocol = Depends(inject_dependency(SQLEmitterServiceProtocol))
):
    """Create a new SQL emitter."""
    result = await emitter_service.register_emitter(
        name=request.name,
        statement_types=[SQLStatementType(t.value) for t in request.statement_types],
        description=request.description,
        configuration=request.configuration
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create SQL emitter")
    
    return create_entity_response(result.value, SQLEmitterResponse)


@router.get("/emitters", response_model=List[SQLEmitterResponse])
async def list_emitters(
    statement_type: Optional[SQLStatementTypeEnum] = Query(None, description="Filter by statement type"),
    emitter_service: SQLEmitterServiceProtocol = Depends(inject_dependency(SQLEmitterServiceProtocol))
):
    """List all SQL emitters."""
    if statement_type:
        result = await emitter_service.get_emitters_by_statement_type(SQLStatementType(statement_type.value))
    else:
        result = await emitter_service.list_emitters()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list SQL emitters")
    
    return [create_entity_response(emitter, SQLEmitterResponse) for emitter in result.value]


@router.get("/emitters/{emitter_id}", response_model=SQLEmitterResponse)
async def get_emitter(
    emitter_id: str = Path(..., description="The emitter ID"),
    emitter_service: SQLEmitterServiceProtocol = Depends(inject_dependency(SQLEmitterServiceProtocol))
):
    """Get a SQL emitter by ID."""
    result = await emitter_service.get_emitter(SQLEmitterId(emitter_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL emitter")
    
    return create_entity_response(result.value, SQLEmitterResponse)


@router.get("/emitters/by-name/{name}", response_model=SQLEmitterResponse)
async def get_emitter_by_name(
    name: str = Path(..., description="The emitter name"),
    emitter_service: SQLEmitterServiceProtocol = Depends(inject_dependency(SQLEmitterServiceProtocol))
):
    """Get a SQL emitter by name."""
    result = await emitter_service.get_emitter_by_name(name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL emitter")
    
    return create_entity_response(result.value, SQLEmitterResponse)


@router.put("/emitters/{emitter_id}", response_model=SQLEmitterResponse)
async def update_emitter(
    request: SQLEmitterUpdateRequest,
    emitter_id: str = Path(..., description="The emitter ID"),
    emitter_service: SQLEmitterServiceProtocol = Depends(inject_dependency(SQLEmitterServiceProtocol))
):
    """Update a SQL emitter."""
    statement_types = None
    if request.statement_types:
        statement_types = [SQLStatementType(t.value) for t in request.statement_types]
    
    result = await emitter_service.update_emitter(
        emitter_id=SQLEmitterId(emitter_id),
        statement_types=statement_types,
        description=request.description,
        configuration=request.configuration
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update SQL emitter")
    
    return create_entity_response(result.value, SQLEmitterResponse)


@router.delete("/emitters/{emitter_id}", status_code=204)
async def delete_emitter(
    emitter_id: str = Path(..., description="The emitter ID"),
    emitter_service: SQLEmitterServiceProtocol = Depends(inject_dependency(SQLEmitterServiceProtocol))
):
    """Delete a SQL emitter."""
    result = await emitter_service.delete_emitter(SQLEmitterId(emitter_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete SQL emitter")


@router.post("/emitters/{emitter_id}/generate", response_model=List[SQLStatementResponse])
async def generate_statements(
    emitter_id: str = Path(..., description="The emitter ID"),
    configuration: Dict[str, Any] = Body({}, description="Optional configuration overrides"),
    emitter_service: SQLEmitterServiceProtocol = Depends(inject_dependency(SQLEmitterServiceProtocol))
):
    """Generate statements using an emitter."""
    result = await emitter_service.generate_statements(
        emitter_id=SQLEmitterId(emitter_id),
        configuration=configuration
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to generate SQL statements")
    
    return [create_entity_response(statement, SQLStatementResponse) for statement in result.value]


# SQL Configuration endpoints
@router.post("/configurations", response_model=SQLConfigurationResponse, status_code=201)
async def create_configuration(
    request: SQLConfigurationCreateRequest,
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """Create a new SQL configuration."""
    connection_info = None
    if request.connection_info:
        connection_service = await inject_dependency(SQLConnectionServiceProtocol)()
        conn_result = await connection_service.create_connection(
            db_name=request.connection_info.db_name,
            db_user=request.connection_info.db_user,
            db_host=request.connection_info.db_host,
            db_port=request.connection_info.db_port,
            db_schema=request.connection_info.db_schema,
            admin_role=request.connection_info.admin_role,
            writer_role=request.connection_info.writer_role,
            reader_role=request.connection_info.reader_role
        )
        
        if not conn_result.is_success():
            raise HTTPException(status_code=400, detail=conn_result.error)
        
        connection_info = conn_result.value
    
    result = await config_service.create_configuration(
        name=request.name,
        description=request.description,
        connection_info=connection_info,
        metadata=request.metadata
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create SQL configuration")
    
    return create_entity_response(result.value, SQLConfigurationResponse)


@router.get("/configurations", response_model=List[SQLConfigurationResponse])
async def list_configurations(
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """List all SQL configurations."""
    result = await config_service.list_configurations()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list SQL configurations")
    
    return [create_entity_response(config, SQLConfigurationResponse) for config in result.value]


@router.get("/configurations/{config_id}", response_model=SQLConfigurationResponse)
async def get_configuration(
    config_id: str = Path(..., description="The configuration ID"),
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """Get a SQL configuration by ID."""
    result = await config_service.get_configuration(SQLConfigId(config_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL configuration")
    
    return create_entity_response(result.value, SQLConfigurationResponse)


@router.get("/configurations/by-name/{name}", response_model=SQLConfigurationResponse)
async def get_configuration_by_name(
    name: str = Path(..., description="The configuration name"),
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """Get a SQL configuration by name."""
    result = await config_service.get_configuration_by_name(name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL configuration")
    
    return create_entity_response(result.value, SQLConfigurationResponse)


@router.put("/configurations/{config_id}", response_model=SQLConfigurationResponse)
async def update_configuration(
    request: SQLConfigurationUpdateRequest,
    config_id: str = Path(..., description="The configuration ID"),
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """Update a SQL configuration."""
    connection_info = None
    if request.connection_info:
        connection_service = await inject_dependency(SQLConnectionServiceProtocol)()
        conn_result = await connection_service.create_connection(
            db_name=request.connection_info.db_name,
            db_user=request.connection_info.db_user,
            db_host=request.connection_info.db_host,
            db_port=request.connection_info.db_port,
            db_schema=request.connection_info.db_schema,
            admin_role=request.connection_info.admin_role,
            writer_role=request.connection_info.writer_role,
            reader_role=request.connection_info.reader_role
        )
        
        if not conn_result.is_success():
            raise HTTPException(status_code=400, detail=conn_result.error)
        
        connection_info = conn_result.value
    
    result = await config_service.update_configuration(
        config_id=SQLConfigId(config_id),
        name=request.name,
        description=request.description,
        connection_info=connection_info,
        metadata=request.metadata
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update SQL configuration")
    
    return create_entity_response(result.value, SQLConfigurationResponse)


@router.delete("/configurations/{config_id}", status_code=204)
async def delete_configuration(
    config_id: str = Path(..., description="The configuration ID"),
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """Delete a SQL configuration."""
    result = await config_service.delete_configuration(SQLConfigId(config_id))
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete SQL configuration")


@router.post("/configurations/{config_id}/emitters/{emitter_id}", response_model=SQLConfigurationResponse)
async def add_emitter_to_configuration(
    config_id: str = Path(..., description="The configuration ID"),
    emitter_id: str = Path(..., description="The emitter ID"),
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """Add an emitter to a configuration."""
    result = await config_service.add_emitter_to_configuration(
        config_id=SQLConfigId(config_id),
        emitter_id=SQLEmitterId(emitter_id)
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to add emitter to configuration")
    
    return create_entity_response(result.value, SQLConfigurationResponse)


@router.delete("/configurations/{config_id}/emitters/{emitter_id}", response_model=SQLConfigurationResponse)
async def remove_emitter_from_configuration(
    config_id: str = Path(..., description="The configuration ID"),
    emitter_id: str = Path(..., description="The emitter ID"),
    config_service: SQLConfigurationServiceProtocol = Depends(inject_dependency(SQLConfigurationServiceProtocol))
):
    """Remove an emitter from a configuration."""
    result = await config_service.remove_emitter_from_configuration(
        config_id=SQLConfigId(config_id),
        emitter_id=SQLEmitterId(emitter_id)
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to remove emitter from configuration")
    
    return create_entity_response(result.value, SQLConfigurationResponse)


# SQL Function endpoints
@router.post("/functions", response_model=SQLFunctionResponse, status_code=201)
async def create_function(
    request: SQLFunctionCreateRequest,
    function_service: SQLFunctionServiceProtocol = Depends(inject_dependency(SQLFunctionServiceProtocol))
):
    """Create a new SQL function."""
    result = await function_service.create_function(
        schema=request.schema,
        name=request.name,
        body=request.body,
        args=request.args,
        return_type=request.return_type,
        language=request.language.value,
        volatility=request.volatility.value,
        security_definer=request.security_definer
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create SQL function")
    
    return create_entity_response(result.value, SQLFunctionResponse)


@router.get("/functions", response_model=List[SQLFunctionResponse])
async def list_functions(
    schema: Optional[str] = Query(None, description="Filter by schema"),
    function_service: SQLFunctionServiceProtocol = Depends(inject_dependency(SQLFunctionServiceProtocol))
):
    """List all SQL functions."""
    if schema:
        result = await function_service.get_functions_by_schema(schema)
    else:
        result = await function_service.list_functions()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list SQL functions")
    
    return [create_entity_response(function, SQLFunctionResponse) for function in result.value]


@router.get("/functions/{function_id}", response_model=SQLFunctionResponse)
async def get_function(
    function_id: str = Path(..., description="The function ID"),
    function_service: SQLFunctionServiceProtocol = Depends(inject_dependency(SQLFunctionServiceProtocol))
):
    """Get a SQL function by ID."""
    result = await function_service.get_function(function_id)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL function")
    
    return create_entity_response(result.value, SQLFunctionResponse)


@router.get("/functions/{schema}/{name}", response_model=SQLFunctionResponse)
async def get_function_by_name(
    schema: str = Path(..., description="The schema name"),
    name: str = Path(..., description="The function name"),
    function_service: SQLFunctionServiceProtocol = Depends(inject_dependency(SQLFunctionServiceProtocol))
):
    """Get a SQL function by schema and name."""
    result = await function_service.get_function_by_name(schema, name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL function")
    
    return create_entity_response(result.value, SQLFunctionResponse)


@router.put("/functions/{function_id}", response_model=SQLFunctionResponse)
async def update_function(
    request: SQLFunctionUpdateRequest,
    function_id: str = Path(..., description="The function ID"),
    function_service: SQLFunctionServiceProtocol = Depends(inject_dependency(SQLFunctionServiceProtocol))
):
    """Update a SQL function."""
    language = None
    if request.language:
        language = request.language.value
    
    volatility = None
    if request.volatility:
        volatility = request.volatility.value
    
    result = await function_service.update_function(
        function_id=function_id,
        body=request.body,
        args=request.args,
        return_type=request.return_type,
        language=language,
        volatility=volatility,
        security_definer=request.security_definer
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update SQL function")
    
    return create_entity_response(result.value, SQLFunctionResponse)


@router.delete("/functions/{function_id}", status_code=204)
async def delete_function(
    function_id: str = Path(..., description="The function ID"),
    function_service: SQLFunctionServiceProtocol = Depends(inject_dependency(SQLFunctionServiceProtocol))
):
    """Delete a SQL function."""
    result = await function_service.delete_function(function_id)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete SQL function")


# SQL Trigger endpoints
@router.post("/triggers", response_model=SQLTriggerResponse, status_code=201)
async def create_trigger(
    request: SQLTriggerCreateRequest,
    trigger_service: SQLTriggerServiceProtocol = Depends(inject_dependency(SQLTriggerServiceProtocol))
):
    """Create a new SQL trigger."""
    result = await trigger_service.create_trigger(
        schema=request.schema,
        name=request.name,
        table=request.table,
        function_name=request.function_name,
        events=request.events,
        when=request.when,
        for_each=request.for_each
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to create SQL trigger")
    
    return create_entity_response(result.value, SQLTriggerResponse)


@router.get("/triggers", response_model=List[SQLTriggerResponse])
async def list_triggers(
    schema: Optional[str] = Query(None, description="Filter by schema"),
    table: Optional[str] = Query(None, description="Filter by table"),
    trigger_service: SQLTriggerServiceProtocol = Depends(inject_dependency(SQLTriggerServiceProtocol))
):
    """List all SQL triggers."""
    if schema and table:
        result = await trigger_service.get_triggers_by_table(schema, table)
    else:
        result = await trigger_service.list_triggers()
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=400, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to list SQL triggers")
    
    return [create_entity_response(trigger, SQLTriggerResponse) for trigger in result.value]


@router.get("/triggers/{trigger_id}", response_model=SQLTriggerResponse)
async def get_trigger(
    trigger_id: str = Path(..., description="The trigger ID"),
    trigger_service: SQLTriggerServiceProtocol = Depends(inject_dependency(SQLTriggerServiceProtocol))
):
    """Get a SQL trigger by ID."""
    result = await trigger_service.get_trigger(trigger_id)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL trigger")
    
    return create_entity_response(result.value, SQLTriggerResponse)


@router.get("/triggers/{schema}/{name}", response_model=SQLTriggerResponse)
async def get_trigger_by_name(
    schema: str = Path(..., description="The schema name"),
    name: str = Path(..., description="The trigger name"),
    trigger_service: SQLTriggerServiceProtocol = Depends(inject_dependency(SQLTriggerServiceProtocol))
):
    """Get a SQL trigger by schema and name."""
    result = await trigger_service.get_trigger_by_name(schema, name)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to get SQL trigger")
    
    return create_entity_response(result.value, SQLTriggerResponse)


@router.put("/triggers/{trigger_id}", response_model=SQLTriggerResponse)
async def update_trigger(
    request: SQLTriggerUpdateRequest,
    trigger_id: str = Path(..., description="The trigger ID"),
    trigger_service: SQLTriggerServiceProtocol = Depends(inject_dependency(SQLTriggerServiceProtocol))
):
    """Update a SQL trigger."""
    result = await trigger_service.update_trigger(
        trigger_id=trigger_id,
        events=request.events,
        when=request.when,
        for_each=request.for_each
    )
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to update SQL trigger")
    
    return create_entity_response(result.value, SQLTriggerResponse)


@router.delete("/triggers/{trigger_id}", status_code=204)
async def delete_trigger(
    trigger_id: str = Path(..., description="The trigger ID"),
    trigger_service: SQLTriggerServiceProtocol = Depends(inject_dependency(SQLTriggerServiceProtocol))
):
    """Delete a SQL trigger."""
    result = await trigger_service.delete_trigger(trigger_id)
    
    if not result.is_success():
        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail="Failed to delete SQL trigger")