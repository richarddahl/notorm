"""
Repository implementations for the Read Model module.

This module provides complete implementations of the read model repository interfaces
for different storage backends, including PostgreSQL, Redis, and hybrid solutions.
"""

import logging
import json
import pickle
from typing import Dict, List, Optional, Any, Type, TypeVar, Generic, cast, Tuple, Union
from datetime import datetime, timedelta, UTC
import uuid

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails
from uno.database.provider import DatabaseProvider
from uno.caching.distributed.redis import RedisCache

from uno.read_model.entities import (
    ReadModel, ReadModelId, Projection, ProjectionId, 
    Query, QueryId, CacheEntry, ProjectorConfiguration,
    CacheLevel
)
from uno.read_model.domain_repositories import (
    ReadModelRepositoryProtocol, ProjectionRepositoryProtocol,
    QueryRepositoryProtocol, CacheRepositoryProtocol,
    ProjectorConfigurationRepositoryProtocol
)

# Type variables
T = TypeVar('T', bound=ReadModel)
P = TypeVar('P', bound=Projection)
Q = TypeVar('Q', bound=Query)

class PostgresReadModelRepository(Generic[T], ReadModelRepositoryProtocol[T]):
    """
    PostgreSQL implementation of the read model repository.
    
    This implementation stores read models in a PostgreSQL database
    with a dedicated table per read model type.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        db_provider: DatabaseProvider,
        table_name: Optional[str] = None,
        schema_name: str = "read_models",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of read model this repository manages
            db_provider: The database provider
            table_name: Optional table name, defaults to model_type.__name__.lower()
            schema_name: PostgreSQL schema name for read model tables
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.db_provider = db_provider
        self.table_name = table_name or f"{model_type.__name__.lower()}"
        self.qualified_table_name = f"{schema_name}.{self.table_name}"
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def create_table_if_not_exists(self) -> Result[bool]:
        """
        Create the read model table if it doesn't exist.
        
        Returns:
            Result containing True if the table was created or already exists
        """
        try:
            async with self.db_provider.async_connection() as conn:
                # Check if the schema exists
                schema_query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = $1
                );
                """
                schema_exists = await conn.fetchval(schema_query, self.qualified_table_name.split('.')[0])
                
                if not schema_exists:
                    # Create schema
                    create_schema_query = f"CREATE SCHEMA IF NOT EXISTS {self.qualified_table_name.split('.')[0]};"
                    await conn.execute(create_schema_query)
                
                # Create table if doesn't exist
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.qualified_table_name} (
                    id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    data JSONB NOT NULL DEFAULT '{}',
                    metadata JSONB NOT NULL DEFAULT '{{}}'
                );
                """
                await conn.execute(create_table_query)
                
                # Add index on updated_at for efficient querying
                index_query = f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_updated_at_idx 
                ON {self.qualified_table_name} (updated_at);
                """
                await conn.execute(index_query)
                
                return Success(True)
        except Exception as e:
            self.logger.error(f"Error creating read model table {self.qualified_table_name}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to create read model table: {str(e)}",
                    context={"table_name": self.qualified_table_name}
                )
            )
    
    async def get_by_id(self, id: ReadModelId) -> Result[Optional[T]]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing the read model if found, None otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT id, version, created_at, updated_at, data, metadata
                FROM {self.qualified_table_name}
                WHERE id = $1;
                """
                record = await conn.fetchrow(query, id.value)
                
                if not record:
                    return Success(None)
                
                model = self._record_to_model(record)
                return Success(model)
        except Exception as e:
            self.logger.error(f"Error getting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get read model: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[T]]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            Result containing list of matching read models
        """
        try:
            # Convert criteria to PostgreSQL JSON query conditions
            conditions = []
            params = []
            param_idx = 1
            
            for key, value in criteria.items():
                # Handle nested paths using -> operator
                if "." in key:
                    path_parts = key.split(".")
                    if path_parts[0] == "data":
                        # Data field query
                        json_path = '->'.join([f"'{part}'" for part in path_parts[1:]])
                        conditions.append(f"data->{json_path} = ${param_idx}")
                    elif path_parts[0] == "metadata":
                        # Metadata field query
                        json_path = '->'.join([f"'{part}'" for part in path_parts[1:]])
                        conditions.append(f"metadata->{json_path} = ${param_idx}")
                    else:
                        # Other nested field
                        self.logger.warning(f"Unsupported nested path: {key}")
                        continue
                else:
                    # Top-level fields
                    if key in ["id", "version", "created_at", "updated_at"]:
                        conditions.append(f"{key} = ${param_idx}")
                    elif key.startswith("data."):
                        field = key[5:]  # Remove 'data.' prefix
                        conditions.append(f"data->'{field}' = ${param_idx}")
                    elif key.startswith("metadata."):
                        field = key[9:]  # Remove 'metadata.' prefix
                        conditions.append(f"metadata->'{field}' = ${param_idx}")
                    else:
                        # Assume it's in the data object
                        conditions.append(f"data->'{key}' = ${param_idx}")
                
                # Convert value to JSON string if it's a complex type
                if isinstance(value, (dict, list)):
                    params.append(json.dumps(value))
                else:
                    params.append(value)
                
                param_idx += 1
            
            # Build the query
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT id, version, created_at, updated_at, data, metadata
                FROM {self.qualified_table_name}
                WHERE {where_clause}
                ORDER BY updated_at DESC;
                """
                records = await conn.fetch(query, *params)
                
                models = [self._record_to_model(record) for record in records]
                return Success(models)
        except Exception as e:
            self.logger.error(f"Error finding read models: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to find read models: {str(e)}",
                    context={"criteria": criteria}
                )
            )
    
    async def save(self, model: T) -> Result[T]:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            Result containing the saved read model
        """
        try:
            # Convert model to database record
            model_dict = {
                "id": model.id.value,
                "version": model.version,
                "created_at": model.created_at,
                "updated_at": model.updated_at or datetime.now(UTC),
                "data": json.dumps(model.data),
                "metadata": json.dumps(model.metadata)
            }
            
            async with self.db_provider.async_connection() as conn:
                # Check if the model exists
                exists_query = f"SELECT 1 FROM {self.qualified_table_name} WHERE id = $1"
                exists = await conn.fetchval(exists_query, model.id.value)
                
                if exists:
                    # Update existing model
                    query = f"""
                    UPDATE {self.qualified_table_name}
                    SET version = $1, updated_at = $2, data = $3, metadata = $4
                    WHERE id = $5
                    RETURNING id;
                    """
                    await conn.fetchval(query, 
                        model.version, 
                        model.updated_at, 
                        model_dict["data"], 
                        model_dict["metadata"], 
                        model.id.value
                    )
                else:
                    # Insert new model
                    query = f"""
                    INSERT INTO {self.qualified_table_name}
                    (id, version, created_at, updated_at, data, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id;
                    """
                    await conn.fetchval(query, 
                        model.id.value, 
                        model.version, 
                        model.created_at, 
                        model.updated_at, 
                        model_dict["data"], 
                        model_dict["metadata"]
                    )
                
                return Success(model)
        except Exception as e:
            self.logger.error(f"Error saving read model {model.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save read model: {str(e)}",
                    context={"id": model.id.value}
                )
            )
    
    async def delete(self, id: ReadModelId) -> Result[bool]:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the read model was deleted, False otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"DELETE FROM {self.qualified_table_name} WHERE id = $1"
                result = await conn.execute(query, id.value)
                
                # Check if any rows were affected
                deleted = result.split(' ')[1] if hasattr(result, 'split') else 0
                return Success(int(deleted) > 0)
        except Exception as e:
            self.logger.error(f"Error deleting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete read model: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def find_with_pagination(
        self, 
        criteria: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "updated_at",
        sort_direction: str = "DESC"
    ) -> Result[Tuple[List[T], int]]:
        """
        Find read models with pagination.
        
        Args:
            criteria: The search criteria
            page: The page number (1-based)
            page_size: The page size
            sort_by: The field to sort by
            sort_direction: The sort direction (ASC or DESC)
            
        Returns:
            Result containing a tuple of (models, total_count)
        """
        try:
            # Convert criteria to PostgreSQL JSON query conditions
            conditions = []
            params = []
            param_idx = 1
            
            for key, value in criteria.items():
                # Handle nested paths using -> operator
                if "." in key:
                    path_parts = key.split(".")
                    if path_parts[0] == "data":
                        # Data field query
                        json_path = '->'.join([f"'{part}'" for part in path_parts[1:]])
                        conditions.append(f"data->{json_path} = ${param_idx}")
                    elif path_parts[0] == "metadata":
                        # Metadata field query
                        json_path = '->'.join([f"'{part}'" for part in path_parts[1:]])
                        conditions.append(f"metadata->{json_path} = ${param_idx}")
                    else:
                        # Other nested field
                        self.logger.warning(f"Unsupported nested path: {key}")
                        continue
                else:
                    # Top-level fields
                    if key in ["id", "version", "created_at", "updated_at"]:
                        conditions.append(f"{key} = ${param_idx}")
                    elif key.startswith("data."):
                        field = key[5:]  # Remove 'data.' prefix
                        conditions.append(f"data->'{field}' = ${param_idx}")
                    elif key.startswith("metadata."):
                        field = key[9:]  # Remove 'metadata.' prefix
                        conditions.append(f"metadata->'{field}' = ${param_idx}")
                    else:
                        # Assume it's in the data object
                        conditions.append(f"data->'{key}' = ${param_idx}")
                
                # Convert value to JSON string if it's a complex type
                if isinstance(value, (dict, list)):
                    params.append(json.dumps(value))
                else:
                    params.append(value)
                
                param_idx += 1
            
            # Build the query
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            # Validate sort direction
            sort_direction = sort_direction.upper()
            if sort_direction not in ["ASC", "DESC"]:
                sort_direction = "DESC"
            
            # Validate sort field
            valid_sort_fields = ["id", "version", "created_at", "updated_at"]
            if sort_by not in valid_sort_fields:
                # Default to updated_at if invalid sort field
                sort_by = "updated_at"
            
            # Pagination parameters
            offset = (page - 1) * page_size
            limit = page_size
            
            async with self.db_provider.async_connection() as conn:
                # Get total count
                count_query = f"""
                SELECT COUNT(*) FROM {self.qualified_table_name}
                WHERE {where_clause}
                """
                total_count = await conn.fetchval(count_query, *params)
                
                # Get paginated results
                query = f"""
                SELECT id, version, created_at, updated_at, data, metadata
                FROM {self.qualified_table_name}
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_direction}
                LIMIT {limit} OFFSET {offset}
                """
                records = await conn.fetch(query, *params)
                
                models = [self._record_to_model(record) for record in records]
                return Success((models, total_count))
        except Exception as e:
            self.logger.error(f"Error finding read models with pagination: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to find read models with pagination: {str(e)}",
                    context={
                        "criteria": criteria,
                        "page": page,
                        "page_size": page_size
                    }
                )
            )
    
    async def batch_save(self, models: List[T]) -> Result[List[T]]:
        """
        Save multiple read models in a batch.
        
        Args:
            models: The read models to save
            
        Returns:
            Result containing the saved read models
        """
        if not models:
            return Success([])
        
        try:
            async with self.db_provider.async_connection() as conn:
                # Start a transaction
                async with conn.transaction():
                    for model in models:
                        model_dict = {
                            "id": model.id.value,
                            "version": model.version,
                            "created_at": model.created_at,
                            "updated_at": model.updated_at or datetime.now(UTC),
                            "data": json.dumps(model.data),
                            "metadata": json.dumps(model.metadata)
                        }
                        
                        # Upsert query (INSERT ... ON CONFLICT ... DO UPDATE)
                        query = f"""
                        INSERT INTO {self.qualified_table_name}
                        (id, version, created_at, updated_at, data, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (id) DO UPDATE SET
                            version = $2,
                            updated_at = $4,
                            data = $5,
                            metadata = $6
                        """
                        
                        await conn.execute(
                            query,
                            model.id.value,
                            model.version,
                            model.created_at,
                            model.updated_at,
                            model_dict["data"],
                            model_dict["metadata"]
                        )
            
            return Success(models)
        except Exception as e:
            model_ids = [model.id.value for model in models]
            self.logger.error(f"Error batch saving read models {model_ids}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to batch save read models: {str(e)}",
                    context={"model_ids": model_ids}
                )
            )
    
    def _record_to_model(self, record: Any) -> T:
        """
        Convert a database record to a read model.
        
        Args:
            record: The database record
            
        Returns:
            The read model
        """
        # Parse JSON fields
        data = json.loads(record["data"]) if isinstance(record["data"], str) else record["data"]
        metadata = json.loads(record["metadata"]) if isinstance(record["metadata"], str) else record["metadata"]
        
        # Create model instance
        model = self.model_type(
            id=ReadModelId(value=record["id"]),
            version=record["version"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            data=data,
            metadata=metadata
        )
        
        return model


class PostgresProjectionRepository(Generic[P], ProjectionRepositoryProtocol[P]):
    """
    PostgreSQL implementation of the projection repository.
    
    This implementation stores projections in a PostgreSQL database.
    """
    
    def __init__(
        self,
        model_type: Type[P],
        db_provider: DatabaseProvider,
        table_name: str = "projections",
        schema_name: str = "read_models",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of projection this repository manages
            db_provider: The database provider
            table_name: Table name for projections
            schema_name: PostgreSQL schema name
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.db_provider = db_provider
        self.table_name = table_name
        self.qualified_table_name = f"{schema_name}.{table_name}"
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def create_table_if_not_exists(self) -> Result[bool]:
        """
        Create the projections table if it doesn't exist.
        
        Returns:
            Result containing True if the table was created or already exists
        """
        try:
            async with self.db_provider.async_connection() as conn:
                # Check if the schema exists
                schema_query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = $1
                );
                """
                schema_exists = await conn.fetchval(schema_query, self.qualified_table_name.split('.')[0])
                
                if not schema_exists:
                    # Create schema
                    create_schema_query = f"CREATE SCHEMA IF NOT EXISTS {self.qualified_table_name.split('.')[0]};"
                    await conn.execute(create_schema_query)
                
                # Create projections table
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.qualified_table_name} (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    read_model_type TEXT NOT NULL,
                    projection_type TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    configuration JSONB NOT NULL DEFAULT '{{}}'
                );
                """
                await conn.execute(create_table_query)
                
                # Create indices
                indices_queries = [
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_event_type_idx ON {self.qualified_table_name} (event_type);",
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_read_model_type_idx ON {self.qualified_table_name} (read_model_type);",
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_is_active_idx ON {self.qualified_table_name} (is_active);"
                ]
                
                for query in indices_queries:
                    await conn.execute(query)
                
                return Success(True)
        except Exception as e:
            self.logger.error(f"Error creating projections table {self.qualified_table_name}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to create projections table: {str(e)}",
                    context={"table_name": self.qualified_table_name}
                )
            )
    
    async def get_by_id(self, id: ProjectionId) -> Result[Optional[P]]:
        """
        Get a projection by ID.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing the projection if found, None otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT * FROM {self.qualified_table_name}
                WHERE id = $1;
                """
                record = await conn.fetchrow(query, id.value)
                
                if not record:
                    return Success(None)
                
                projection = self._record_to_projection(record)
                return Success(projection)
        except Exception as e:
            self.logger.error(f"Error getting projection {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projection: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def get_by_event_type(self, event_type: str) -> Result[List[P]]:
        """
        Get projections by event type.
        
        Args:
            event_type: The event type
            
        Returns:
            Result containing list of projections for the event type
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT * FROM {self.qualified_table_name}
                WHERE event_type = $1
                ORDER BY name;
                """
                records = await conn.fetch(query, event_type)
                
                projections = [self._record_to_projection(record) for record in records]
                return Success(projections)
        except Exception as e:
            self.logger.error(f"Error getting projections for event type {event_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projections by event type: {str(e)}",
                    context={"event_type": event_type}
                )
            )
    
    async def get_by_read_model_type(self, read_model_type: str) -> Result[List[P]]:
        """
        Get projections by read model type.
        
        Args:
            read_model_type: The read model type
            
        Returns:
            Result containing list of projections for the read model type
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT * FROM {self.qualified_table_name}
                WHERE read_model_type = $1
                ORDER BY name;
                """
                records = await conn.fetch(query, read_model_type)
                
                projections = [self._record_to_projection(record) for record in records]
                return Success(projections)
        except Exception as e:
            self.logger.error(f"Error getting projections for read model type {read_model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projections by read model type: {str(e)}",
                    context={"read_model_type": read_model_type}
                )
            )
    
    async def save(self, projection: P) -> Result[P]:
        """
        Save a projection.
        
        Args:
            projection: The projection to save
            
        Returns:
            Result containing the saved projection
        """
        try:
            # Prepare data for database
            projection_dict = {
                "id": projection.id.value,
                "name": projection.name,
                "event_type": projection.event_type,
                "read_model_type": projection.read_model_type,
                "projection_type": projection.projection_type.value,
                "created_at": projection.created_at,
                "updated_at": projection.updated_at or datetime.now(UTC),
                "is_active": projection.is_active,
                "configuration": json.dumps(projection.configuration)
            }
            
            async with self.db_provider.async_connection() as conn:
                # Check if the projection exists
                exists_query = f"SELECT 1 FROM {self.qualified_table_name} WHERE id = $1"
                exists = await conn.fetchval(exists_query, projection.id.value)
                
                if exists:
                    # Update existing projection
                    query = f"""
                    UPDATE {self.qualified_table_name}
                    SET name = $1, event_type = $2, read_model_type = $3,
                        projection_type = $4, updated_at = $5, is_active = $6,
                        configuration = $7
                    WHERE id = $8
                    RETURNING id;
                    """
                    await conn.fetchval(query, 
                        projection.name,
                        projection.event_type,
                        projection.read_model_type,
                        projection_dict["projection_type"],
                        projection.updated_at,
                        projection.is_active,
                        projection_dict["configuration"],
                        projection.id.value
                    )
                else:
                    # Insert new projection
                    query = f"""
                    INSERT INTO {self.qualified_table_name}
                    (id, name, event_type, read_model_type, projection_type, 
                     created_at, updated_at, is_active, configuration)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id;
                    """
                    await conn.fetchval(query, 
                        projection.id.value,
                        projection.name,
                        projection.event_type,
                        projection.read_model_type,
                        projection_dict["projection_type"],
                        projection.created_at,
                        projection.updated_at,
                        projection.is_active,
                        projection_dict["configuration"]
                    )
                
                return Success(projection)
        except Exception as e:
            self.logger.error(f"Error saving projection {projection.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save projection: {str(e)}",
                    context={"id": projection.id.value}
                )
            )
    
    async def delete(self, id: ProjectionId) -> Result[bool]:
        """
        Delete a projection.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing True if the projection was deleted, False otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"DELETE FROM {self.qualified_table_name} WHERE id = $1"
                result = await conn.execute(query, id.value)
                
                # Check if any rows were affected
                deleted = result.split(' ')[1] if hasattr(result, 'split') else 0
                return Success(int(deleted) > 0)
        except Exception as e:
            self.logger.error(f"Error deleting projection {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete projection: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    def _record_to_projection(self, record: Any) -> P:
        """
        Convert a database record to a projection.
        
        Args:
            record: The database record
            
        Returns:
            The projection
        """
        from uno.read_model.entities import ProjectionType
        
        # Parse configuration JSON
        configuration = json.loads(record["configuration"]) if isinstance(record["configuration"], str) else record["configuration"]
        
        # Create projection instance
        projection = self.model_type(
            id=ProjectionId(value=record["id"]),
            name=record["name"],
            event_type=record["event_type"],
            read_model_type=record["read_model_type"],
            projection_type=ProjectionType(record["projection_type"]),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            is_active=record["is_active"],
            configuration=configuration
        )
        
        return projection


class PostgresQueryRepository(Generic[Q], QueryRepositoryProtocol[Q]):
    """
    PostgreSQL implementation of the query repository.
    
    This implementation stores queries in a PostgreSQL database.
    """
    
    def __init__(
        self,
        model_type: Type[Q],
        db_provider: DatabaseProvider,
        table_name: str = "queries",
        schema_name: str = "read_models",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of query this repository manages
            db_provider: The database provider
            table_name: Table name for queries
            schema_name: PostgreSQL schema name
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.db_provider = db_provider
        self.table_name = table_name
        self.qualified_table_name = f"{schema_name}.{table_name}"
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def create_table_if_not_exists(self) -> Result[bool]:
        """
        Create the queries table if it doesn't exist.
        
        Returns:
            Result containing True if the table was created or already exists
        """
        try:
            async with self.db_provider.async_connection() as conn:
                # Check if the schema exists
                schema_query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = $1
                );
                """
                schema_exists = await conn.fetchval(schema_query, self.qualified_table_name.split('.')[0])
                
                if not schema_exists:
                    # Create schema
                    create_schema_query = f"CREATE SCHEMA IF NOT EXISTS {self.qualified_table_name.split('.')[0]};"
                    await conn.execute(create_schema_query)
                
                # Create queries table
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.qualified_table_name} (
                    id TEXT PRIMARY KEY,
                    query_type TEXT NOT NULL,
                    read_model_type TEXT NOT NULL,
                    parameters JSONB NOT NULL DEFAULT '{{}}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
                await conn.execute(create_table_query)
                
                # Create indices
                indices_queries = [
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_query_type_idx ON {self.qualified_table_name} (query_type);",
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_read_model_type_idx ON {self.qualified_table_name} (read_model_type);"
                ]
                
                for query in indices_queries:
                    await conn.execute(query)
                
                return Success(True)
        except Exception as e:
            self.logger.error(f"Error creating queries table {self.qualified_table_name}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to create queries table: {str(e)}",
                    context={"table_name": self.qualified_table_name}
                )
            )
    
    async def get_by_id(self, id: QueryId) -> Result[Optional[Q]]:
        """
        Get a query by ID.
        
        Args:
            id: The query ID
            
        Returns:
            Result containing the query if found, None otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT * FROM {self.qualified_table_name}
                WHERE id = $1;
                """
                record = await conn.fetchrow(query, id.value)
                
                if not record:
                    return Success(None)
                
                query_obj = self._record_to_query(record)
                return Success(query_obj)
        except Exception as e:
            self.logger.error(f"Error getting query {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get query: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[Q]]:
        """
        Find queries matching criteria.
        
        Args:
            criteria: The search criteria
            
        Returns:
            Result containing list of matching queries
        """
        try:
            # Convert criteria to SQL conditions
            conditions = []
            params = []
            param_idx = 1
            
            for key, value in criteria.items():
                if key in ["id", "query_type", "read_model_type", "created_at"]:
                    # Direct column
                    conditions.append(f"{key} = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                elif key.startswith("parameters."):
                    # Parameter field
                    path = key[11:]  # Remove 'parameters.' prefix
                    conditions.append(f"parameters->'{path}' = ${param_idx}")
                    
                    # Convert value to JSON if it's a complex type
                    if isinstance(value, (dict, list)):
                        params.append(json.dumps(value))
                    else:
                        params.append(value)
                    
                    param_idx += 1
            
            # Build the query
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT * FROM {self.qualified_table_name}
                WHERE {where_clause}
                ORDER BY created_at DESC;
                """
                records = await conn.fetch(query, *params)
                
                query_objects = [self._record_to_query(record) for record in records]
                return Success(query_objects)
        except Exception as e:
            self.logger.error(f"Error finding queries: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to find queries: {str(e)}",
                    context={"criteria": criteria}
                )
            )
    
    async def save(self, query: Q) -> Result[Q]:
        """
        Save a query.
        
        Args:
            query: The query to save
            
        Returns:
            Result containing the saved query
        """
        try:
            # Prepare data for database
            query_dict = {
                "id": query.id.value,
                "query_type": query.query_type.value,
                "read_model_type": query.read_model_type,
                "parameters": json.dumps(query.parameters),
                "created_at": query.created_at
            }
            
            async with self.db_provider.async_connection() as conn:
                # Upsert query
                upsert_query = f"""
                INSERT INTO {self.qualified_table_name}
                (id, query_type, read_model_type, parameters, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET
                    query_type = $2,
                    read_model_type = $3,
                    parameters = $4
                RETURNING id;
                """
                
                await conn.fetchval(
                    upsert_query,
                    query.id.value,
                    query_dict["query_type"],
                    query.read_model_type,
                    query_dict["parameters"],
                    query.created_at
                )
                
                return Success(query)
        except Exception as e:
            self.logger.error(f"Error saving query {query.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save query: {str(e)}",
                    context={"id": query.id.value}
                )
            )
    
    async def delete(self, id: QueryId) -> Result[bool]:
        """
        Delete a query.
        
        Args:
            id: The query ID
            
        Returns:
            Result containing True if the query was deleted, False otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"DELETE FROM {self.qualified_table_name} WHERE id = $1"
                result = await conn.execute(query, id.value)
                
                # Check if any rows were affected
                deleted = result.split(' ')[1] if hasattr(result, 'split') else 0
                return Success(int(deleted) > 0)
        except Exception as e:
            self.logger.error(f"Error deleting query {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete query: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    def _record_to_query(self, record: Any) -> Q:
        """
        Convert a database record to a query.
        
        Args:
            record: The database record
            
        Returns:
            The query
        """
        from uno.read_model.entities import QueryType
        
        # Parse parameters JSON
        parameters = json.loads(record["parameters"]) if isinstance(record["parameters"], str) else record["parameters"]
        
        # Create query instance
        query_obj = self.model_type(
            id=QueryId(value=record["id"]),
            query_type=QueryType(record["query_type"]),
            read_model_type=record["read_model_type"],
            parameters=parameters,
            created_at=record["created_at"]
        )
        
        return query_obj


class PostgresProjectorConfigurationRepository(ProjectorConfigurationRepositoryProtocol):
    """
    PostgreSQL implementation of the projector configuration repository.
    
    This implementation stores projector configurations in a PostgreSQL database.
    """
    
    def __init__(
        self,
        db_provider: DatabaseProvider,
        table_name: str = "projector_configurations",
        schema_name: str = "read_models",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            db_provider: The database provider
            table_name: Table name for projector configurations
            schema_name: PostgreSQL schema name
            logger: Optional logger instance
        """
        self.db_provider = db_provider
        self.table_name = table_name
        self.qualified_table_name = f"{schema_name}.{table_name}"
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def create_table_if_not_exists(self) -> Result[bool]:
        """
        Create the projector configurations table if it doesn't exist.
        
        Returns:
            Result containing True if the table was created or already exists
        """
        try:
            async with self.db_provider.async_connection() as conn:
                # Check if the schema exists
                schema_query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = $1
                );
                """
                schema_exists = await conn.fetchval(schema_query, self.qualified_table_name.split('.')[0])
                
                if not schema_exists:
                    # Create schema
                    create_schema_query = f"CREATE SCHEMA IF NOT EXISTS {self.qualified_table_name.split('.')[0]};"
                    await conn.execute(create_schema_query)
                
                # Create table
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.qualified_table_name} (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    async_processing BOOLEAN NOT NULL DEFAULT TRUE,
                    batch_size INTEGER NOT NULL DEFAULT 100,
                    cache_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    cache_ttl_seconds INTEGER NOT NULL DEFAULT 3600,
                    rebuild_on_startup BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    projections JSONB NOT NULL DEFAULT '[]'
                );
                """
                await conn.execute(create_table_query)
                
                # Create index on name
                index_query = f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_name_idx 
                ON {self.qualified_table_name} (name);
                """
                await conn.execute(index_query)
                
                return Success(True)
        except Exception as e:
            self.logger.error(f"Error creating projector configuration table {self.qualified_table_name}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to create projector configuration table: {str(e)}",
                    context={"table_name": self.qualified_table_name}
                )
            )
    
    async def get_by_id(self, id: str) -> Result[Optional[ProjectorConfiguration]]:
        """
        Get a projector configuration by ID.
        
        Args:
            id: The configuration ID
            
        Returns:
            Result containing the configuration if found, None otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT * FROM {self.qualified_table_name}
                WHERE id = $1;
                """
                record = await conn.fetchrow(query, id)
                
                if not record:
                    return Success(None)
                
                config = self._record_to_config(record)
                return Success(config)
        except Exception as e:
            self.logger.error(f"Error getting projector configuration {id}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projector configuration: {str(e)}",
                    context={"id": id}
                )
            )
    
    async def get_by_name(self, name: str) -> Result[Optional[ProjectorConfiguration]]:
        """
        Get a projector configuration by name.
        
        Args:
            name: The configuration name
            
        Returns:
            Result containing the configuration if found, None otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"""
                SELECT * FROM {self.qualified_table_name}
                WHERE name = $1;
                """
                record = await conn.fetchrow(query, name)
                
                if not record:
                    return Success(None)
                
                config = self._record_to_config(record)
                return Success(config)
        except Exception as e:
            self.logger.error(f"Error getting projector configuration by name {name}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projector configuration by name: {str(e)}",
                    context={"name": name}
                )
            )
    
    async def save(self, config: ProjectorConfiguration) -> Result[ProjectorConfiguration]:
        """
        Save a projector configuration.
        
        Args:
            config: The configuration to save
            
        Returns:
            Result containing the saved configuration
        """
        try:
            # Serialize projections to JSON
            projections_json = json.dumps([
                {
                    "id": p.id.value,
                    "name": p.name,
                    "event_type": p.event_type,
                    "read_model_type": p.read_model_type,
                    "projection_type": p.projection_type.value,
                    "created_at": p.created_at.isoformat() if isinstance(p.created_at, datetime) else p.created_at,
                    "updated_at": p.updated_at.isoformat() if isinstance(p.updated_at, datetime) else p.updated_at,
                    "is_active": p.is_active,
                    "configuration": p.configuration
                }
                for p in config.projections
            ])
            
            async with self.db_provider.async_connection() as conn:
                # Check if the configuration exists
                exists_query = f"SELECT 1 FROM {self.qualified_table_name} WHERE id = $1"
                exists = await conn.fetchval(exists_query, config.id)
                
                if exists:
                    # Update existing configuration
                    query = f"""
                    UPDATE {self.qualified_table_name}
                    SET name = $1, async_processing = $2, batch_size = $3,
                        cache_enabled = $4, cache_ttl_seconds = $5,
                        rebuild_on_startup = $6, updated_at = $7,
                        projections = $8
                    WHERE id = $9
                    RETURNING id;
                    """
                    await conn.fetchval(
                        query,
                        config.name,
                        config.async_processing,
                        config.batch_size,
                        config.cache_enabled,
                        config.cache_ttl_seconds,
                        config.rebuild_on_startup,
                        config.updated_at,
                        projections_json,
                        config.id
                    )
                else:
                    # Insert new configuration
                    query = f"""
                    INSERT INTO {self.qualified_table_name}
                    (id, name, async_processing, batch_size, cache_enabled,
                     cache_ttl_seconds, rebuild_on_startup, created_at,
                     updated_at, projections)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id;
                    """
                    await conn.fetchval(
                        query,
                        config.id,
                        config.name,
                        config.async_processing,
                        config.batch_size,
                        config.cache_enabled,
                        config.cache_ttl_seconds,
                        config.rebuild_on_startup,
                        config.created_at,
                        config.updated_at,
                        projections_json
                    )
                
                return Success(config)
        except Exception as e:
            self.logger.error(f"Error saving projector configuration {config.id}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save projector configuration: {str(e)}",
                    context={"id": config.id, "name": config.name}
                )
            )
    
    async def delete(self, id: str) -> Result[bool]:
        """
        Delete a projector configuration.
        
        Args:
            id: The configuration ID
            
        Returns:
            Result containing True if the configuration was deleted, False otherwise
        """
        try:
            async with self.db_provider.async_connection() as conn:
                query = f"DELETE FROM {self.qualified_table_name} WHERE id = $1"
                result = await conn.execute(query, id)
                
                # Check if any rows were affected
                deleted = result.split(' ')[1] if hasattr(result, 'split') else 0
                return Success(int(deleted) > 0)
        except Exception as e:
            self.logger.error(f"Error deleting projector configuration {id}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete projector configuration: {str(e)}",
                    context={"id": id}
                )
            )
    
    def _record_to_config(self, record: Any) -> ProjectorConfiguration:
        """
        Convert a database record to a projector configuration.
        
        Args:
            record: The database record
            
        Returns:
            The projector configuration
        """
        from uno.read_model.entities import ProjectionType, ProjectionId, Projection
        
        # Parse projections JSON
        projections_data = json.loads(record["projections"]) if isinstance(record["projections"], str) else record["projections"]
        
        # Convert projection data to Projection objects
        projections = []
        for p_data in projections_data:
            projection = Projection(
                id=ProjectionId(value=p_data["id"]),
                name=p_data["name"],
                event_type=p_data["event_type"],
                read_model_type=p_data["read_model_type"],
                projection_type=ProjectionType(p_data["projection_type"]),
                created_at=datetime.fromisoformat(p_data["created_at"]) if isinstance(p_data["created_at"], str) else p_data["created_at"],
                updated_at=datetime.fromisoformat(p_data["updated_at"]) if isinstance(p_data["updated_at"], str) else p_data["updated_at"],
                is_active=p_data["is_active"],
                configuration=p_data["configuration"]
            )
            projections.append(projection)
        
        # Create configuration instance
        config = ProjectorConfiguration(
            id=record["id"],
            name=record["name"],
            async_processing=record["async_processing"],
            batch_size=record["batch_size"],
            cache_enabled=record["cache_enabled"],
            cache_ttl_seconds=record["cache_ttl_seconds"],
            rebuild_on_startup=record["rebuild_on_startup"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            projections=projections
        )
        
        return config


class HybridReadModelRepository(Generic[T], ReadModelRepositoryProtocol[T]):
    """
    Hybrid implementation of the read model repository.
    
    This implementation combines a PostgreSQL database for persistence
    with Redis caching for improved read performance.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        db_provider: DatabaseProvider,
        redis_cache: RedisCache,
        table_name: Optional[str] = None,
        schema_name: str = "read_models",
        cache_ttl: int = 3600,  # 1 hour
        cache_prefix: str = "read_model:",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of read model this repository manages
            db_provider: The database provider
            redis_cache: The Redis cache instance
            table_name: Optional table name, defaults to model_type.__name__.lower()
            schema_name: PostgreSQL schema name for read model tables
            cache_ttl: Cache time-to-live in seconds
            cache_prefix: Prefix for cache keys
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.db_provider = db_provider
        self.redis_cache = redis_cache
        self.table_name = table_name or f"{model_type.__name__.lower()}"
        self.qualified_table_name = f"{schema_name}.{self.table_name}"
        self.cache_ttl = cache_ttl
        self.cache_prefix = cache_prefix
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Create the underlying PostgreSQL repository
        self.db_repo = PostgresReadModelRepository(
            model_type=model_type,
            db_provider=db_provider,
            table_name=table_name,
            schema_name=schema_name,
            logger=logger
        )
    
    async def create_table_if_not_exists(self) -> Result[bool]:
        """
        Create the read model table if it doesn't exist.
        
        Returns:
            Result containing True if the table was created or already exists
        """
        return await self.db_repo.create_table_if_not_exists()
    
    async def get_by_id(self, id: ReadModelId) -> Result[Optional[T]]:
        """
        Get a read model by ID.
        
        This method first checks the cache, then falls back to the database.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing the read model if found, None otherwise
        """
        try:
            # Generate cache key
            cache_key = f"{self.cache_prefix}{self.model_type.__name__}:{id.value}"
            
            # Try to get from cache
            cached_data = await self.redis_cache.get_async(cache_key)
            
            if cached_data is not None:
                self.logger.debug(f"Cache hit for read model {id.value}")
                return Success(cached_data)
            
            # Cache miss, get from database
            self.logger.debug(f"Cache miss for read model {id.value}")
            result = await self.db_repo.get_by_id(id)
            
            if result.is_error():
                return result
            
            model = result.value
            
            # Cache the result if found
            if model is not None:
                await self.redis_cache.set_async(cache_key, model, self.cache_ttl)
            
            return Success(model)
        except Exception as e:
            self.logger.error(f"Error getting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get read model: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[T]]:
        """
        Find read models matching criteria.
        
        This method bypasses the cache due to the complexity of caching
        query results, and goes directly to the database.
        
        Args:
            criteria: The query criteria
            
        Returns:
            Result containing list of matching read models
        """
        # For find operations, we go directly to the database
        # as caching these results would be complex
        return await self.db_repo.find(criteria)
    
    async def save(self, model: T) -> Result[T]:
        """
        Save a read model.
        
        This method saves to the database and updates the cache.
        
        Args:
            model: The read model to save
            
        Returns:
            Result containing the saved read model
        """
        try:
            # Save to database
            result = await self.db_repo.save(model)
            
            if result.is_error():
                return result
            
            # Update cache
            cache_key = f"{self.cache_prefix}{model.model_type}:{model.id.value}"
            await self.redis_cache.set_async(cache_key, model, self.cache_ttl)
            
            return Success(model)
        except Exception as e:
            self.logger.error(f"Error saving read model {model.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save read model: {str(e)}",
                    context={"id": model.id.value}
                )
            )
    
    async def delete(self, id: ReadModelId) -> Result[bool]:
        """
        Delete a read model.
        
        This method deletes from the database and invalidates the cache.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the read model was deleted, False otherwise
        """
        try:
            # Delete from database
            result = await self.db_repo.delete(id)
            
            if result.is_error():
                return result
            
            # Invalidate cache
            cache_key = f"{self.cache_prefix}{self.model_type.__name__}:{id.value}"
            await self.redis_cache.delete_async(cache_key)
            
            return result
        except Exception as e:
            self.logger.error(f"Error deleting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete read model: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def invalidate_cache(self, id: ReadModelId) -> Result[bool]:
        """
        Invalidate the cache for a specific read model.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the cache was invalidated
        """
        try:
            cache_key = f"{self.cache_prefix}{self.model_type.__name__}:{id.value}"
            await self.redis_cache.delete_async(cache_key)
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error invalidating cache for read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to invalidate cache: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def invalidate_all_cache(self) -> Result[bool]:
        """
        Invalidate the cache for all read models of this type.
        
        Returns:
            Result containing True if the cache was invalidated
        """
        try:
            pattern = f"{self.cache_prefix}{self.model_type.__name__}:*"
            count = await self.redis_cache.invalidate_pattern_async(pattern)
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error invalidating all cache for read model type {self.model_type.__name__}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to invalidate all cache: {str(e)}",
                    context={"model_type": self.model_type.__name__}
                )
            )
    
    async def find_with_pagination(
        self, 
        criteria: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "updated_at",
        sort_direction: str = "DESC"
    ) -> Result[Tuple[List[T], int]]:
        """
        Find read models with pagination.
        
        This method bypasses the cache due to the complexity of caching
        paginated results, and goes directly to the database.
        
        Args:
            criteria: The search criteria
            page: The page number (1-based)
            page_size: The page size
            sort_by: The field to sort by
            sort_direction: The sort direction (ASC or DESC)
            
        Returns:
            Result containing a tuple of (models, total_count)
        """
        # For paginated find operations, we go directly to the database
        return await self.db_repo.find_with_pagination(
            criteria, page, page_size, sort_by, sort_direction
        )
    
    async def batch_save(self, models: List[T]) -> Result[List[T]]:
        """
        Save multiple read models in a batch.
        
        This method saves to the database and updates the cache for each model.
        
        Args:
            models: The read models to save
            
        Returns:
            Result containing the saved read models
        """
        try:
            # Save to database
            result = await self.db_repo.batch_save(models)
            
            if result.is_error():
                return result
            
            # Update cache for each model
            cache_updates = {}
            for model in models:
                cache_key = f"{self.cache_prefix}{model.model_type}:{model.id.value}"
                cache_updates[cache_key] = model
            
            # Use multi_set for efficiency
            await self.redis_cache.multi_set_async(cache_updates, self.cache_ttl)
            
            return Success(models)
        except Exception as e:
            model_ids = [model.id.value for model in models]
            self.logger.error(f"Error batch saving read models {model_ids}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to batch save read models: {str(e)}",
                    context={"model_ids": model_ids}
                )
            )