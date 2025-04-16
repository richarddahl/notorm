# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
import enum
import logging
from typing import Optional, ClassVar, Annotated, Dict, Any, Type, Union, Protocol

from pydantic import BaseModel, ConfigDict, computed_field
from fastapi import (
    FastAPI,
    status,
    APIRouter,
    HTTPException,
    Response,
    Request,
    Body,
    Depends,
    Query,
)

from uno.dto import UnoDTO
from uno.registry_errors import RegistryClassNotFoundError
from uno.settings import uno_settings
from uno.api.repository_adapter import RepositoryAdapter

# Set up logger
logger = logging.getLogger(__name__)


class UnoRouter(BaseModel, ABC):
    """Base router class for creating FastAPI endpoints."""
    
    # API model can be a domain model or a repository adapter
    model: Union[Type[BaseModel], RepositoryAdapter]
    response_model: Type[BaseModel] | None = None
    body_model: Type[BaseModel] | None = None
    path_suffix: str
    method: str
    path_prefix: str = "/api"
    api_version: str = uno_settings.API_VERSION
    include_in_schema: bool = True
    tags: list[str | enum.StrEnum] | None = None
    return_list: bool = False
    app: FastAPI = None
    router: APIRouter = None  # Optional router to use instead of app
    status_code: int = status.HTTP_200_OK
    dependencies: list[Depends] = []  # Dependencies to add to the endpoint

    model_config: dict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint_factory()
        
        # Determine the model name to use in the path
        model_name = self._get_model_name().lower()
        
        # Create a router or use the provided one
        router = self.router or APIRouter()
        
        # Determine tags to use
        tags = self.tags or self._get_model_tags()
        
        # Add the route to the router
        router.add_api_route(
            f"{self.path_prefix}/{self.api_version}/{model_name}{self.path_suffix}",
            endpoint=self.endpoint,
            methods=[self.method],
            include_in_schema=self.include_in_schema,
            tags=tags,
            summary=self.summary,
            description=self.description,
            status_code=self.status_code,
            response_model_exclude_none=True,
            dependencies=self.dependencies,
        )
        
        # If using app directly, include the router
        if self.app and not self.router:
            self.app.include_router(router)

    def _get_model_name(self) -> str:
        """Get the model name for use in the endpoint path."""
        # For repository adapters
        if isinstance(self.model, RepositoryAdapter):
            # Try to get entity type name
            if hasattr(self.model, 'entity_type') and hasattr(self.model.entity_type, '__name__'):
                return self.model.entity_type.__name__
            else:
                # Fall back to class name
                return self.model.__class__.__name__.replace('Adapter', '')
                
        # For regular models
        return self.model.__name__
        
    def _get_model_tags(self) -> list[str]:
        """Get the display name for OpenAPI tags."""
        # For repository adapters
        if isinstance(self.model, RepositoryAdapter):
            # Use display_name_plural if available
            if hasattr(self.model, 'display_name_plural'):
                return [self.model.display_name_plural]
            
        # For regular models
        if hasattr(self.model, 'display_name_plural'):
            return [self.model.display_name_plural]
            
        # Fall back to model name + 's'
        return [f"{self._get_model_name()}s"]

    @abstractmethod
    def endpoint_factory(self):
        """Create the endpoint method."""
        raise NotImplementedError


class ListRouter(UnoRouter):
    """Router for listing entities."""
    
    path_suffix: str = ""
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    return_list: bool = True

    @computed_field
    def summary(self) -> str:
        """Get summary for OpenAPI documentation."""
        # Get display name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name_plural = self.model.display_name_plural
        else:
            display_name_plural = getattr(self.model, 'display_name_plural', f"{self._get_model_name()}s")
            
        return f"List {display_name_plural}"

    @computed_field
    def description(self) -> str:
        """Get description for OpenAPI documentation."""
        # Get display name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name_plural = self.model.display_name_plural
            schema_name = self.model.entity_type.__name__ if hasattr(self.model, 'entity_type') else self._get_model_name()
        else:
            display_name_plural = getattr(self.model, 'display_name_plural', f"{self._get_model_name()}s")
            schema_name = self.model.__name__
            
        return f"""Returns a list of {display_name_plural} with the __{schema_name}View__ schema.
        
        Supports the following query parameters:
        - `stream`: Set to `true` to enable streaming response for large result sets
        - `fields`: Comma-separated list of fields to include in the response (partial response)
        - `page`: Page number for pagination (starting from 1)
        - `page_size`: Number of items per page (default: 50, max: 500)
        """

    def endpoint_factory(self) -> None:
        """Create the list endpoint."""
        from fastapi.responses import StreamingResponse
        from fastapi import Request, Header, Query as QueryParam
        from typing import Optional, List
        import json
        import asyncio
        from uno.database.streaming import stream_query, StreamingMode
        
        # Get filter parameters model
        if isinstance(self.model, RepositoryAdapter):
            # Repository adapter has create_filter_params method
            filter_params = self.model.create_filter_params()
        else:
            # Legacy model class method
            filter_params = self.model.create_filter_params() if hasattr(self.model, 'create_filter_params') else None

        async def endpoint(
            self,
            request: Request,
            filter_params: Optional[Any] = None,  # Will be annotated below
            fields: Optional[str] = QueryParam(None, description="Comma-separated list of fields to include in the response"),
            stream: bool = QueryParam(False, description="Enable streaming response for large result sets"),
            page: int = QueryParam(1, description="Page number (starting from 1)", ge=1),
            page_size: int = QueryParam(50, description="Number of items per page", ge=1, le=500),
            accept: Optional[str] = Header(None)
        ) -> list[BaseModel]:
            # Parse fields for partial response
            selected_fields = fields.split(',') if fields else None
            
            # Determine if client supports streaming (based on accept header)
            supports_streaming = stream and (
                accept and ('application/x-ndjson' in accept or 'text/event-stream' in accept)
            )
            
            # Validate filters - use the appropriate method based on model type
            if isinstance(self.model, RepositoryAdapter):
                # Repository adapter validates filter parameters
                filters = self.model.validate_filter_params(filter_params)
            else:
                # Legacy model class method
                if hasattr(self.model, 'validate_filter_params'):
                    filters = self.model.validate_filter_params(filter_params)
                else:
                    filters = filter_params
            
            # If streaming is requested and supported
            if supports_streaming:
                # Check if repository supports streaming
                if not (hasattr(self.model, 'stream') or hasattr(self.model, 'get_filter_query')):
                    # Fallback to standard response if streaming not supported
                    logger.warning(f"Streaming requested but not supported by {self._get_model_name()}")
                    supports_streaming = False
                else:
                    try:
                        # Get raw query - use appropriate method
                        if hasattr(self.model, 'get_filter_query'):
                            # Legacy model method
                            raw_query = await self.model.get_filter_query(filters=filters)
                        else:
                            # For newer APIs that don't expose raw queries,
                            # we can't support streaming without a compatible method
                            supports_streaming = False
                    except Exception as e:
                        logger.error(f"Error getting filter query: {str(e)}")
                        supports_streaming = False
            
            # Handle streaming if still supported
            if supports_streaming:
                # Define the transformation to include only selected fields
                def transform_entity(entity):
                    # Convert entity to dict
                    if hasattr(entity, "to_dict"):
                        entity_dict = entity.to_dict()
                    elif hasattr(entity, "model_dump"):
                        entity_dict = entity.model_dump()
                    else:
                        entity_dict = entity
                        
                    # Apply field selection if specified
                    if selected_fields:
                        return {k: v for k, v in entity_dict.items() if k in selected_fields}
                    return entity_dict
                
                # Define the streaming function
                async def stream_results():
                    # Initial response with content type header
                    yield '{"type":"meta","total_count":null,"streaming":true}\n'
                    
                    count = 0
                    # Stream entities in chunks using database streaming
                    async with stream_query(
                        query=raw_query,
                        mode=StreamingMode.CURSOR,
                        chunk_size=100,  # Reasonable chunk size for streaming
                        transform_fn=None  # We'll transform after fetching
                    ) as stream:
                        async for entity in stream:
                            # Transform entity to include only selected fields
                            entity_dict = transform_entity(entity)
                            # Stream as newline-delimited JSON
                            yield f"{json.dumps(entity_dict)}\n"
                            count += 1
                            
                            # Add progress updates every 1000 items
                            if count % 1000 == 0:
                                yield f'{{"type":"progress","count":{count}}}\n'
                    
                    # Final count
                    yield f'{{"type":"end","total_count":{count}}}\n'
                
                # Return streaming response
                return StreamingResponse(
                    stream_results(),
                    media_type="application/x-ndjson"
                )
            
            # Standard paginated response
            else:
                try:
                    # Get results with pagination using appropriate method
                    results = await self.model.filter(
                        filters=filters, 
                        page=page, 
                        page_size=page_size
                    )
                except Exception as e:
                    logger.error(f"Error filtering entities: {str(e)}")
                    # Return empty list on error rather than failing
                    return []
                
                # If field selection is requested, filter the results
                if selected_fields:
                    # Process entities to include only selected fields
                    if hasattr(results, "items"):  # Paginated response
                        filtered_items = []
                        for item in results.items:
                            # Get item as dict using appropriate method
                            if hasattr(item, "to_dict"):
                                item_dict = item.to_dict()
                            elif hasattr(item, "model_dump"):
                                item_dict = item.model_dump()
                            else:
                                item_dict = item
                                
                            # Filter fields
                            filtered_item = {k: v for k, v in item_dict.items() if k in selected_fields}
                            filtered_items.append(filtered_item)
                        
                        # Replace items with filtered items
                        results.items = filtered_items
                    elif isinstance(results, list):  # List response
                        filtered_results = []
                        for item in results:
                            # Get item as dict using appropriate method
                            if hasattr(item, "to_dict"):
                                item_dict = item.to_dict()
                            elif hasattr(item, "model_dump"):
                                item_dict = item.model_dump()
                            else:
                                item_dict = item
                                
                            # Filter fields
                            filtered_item = {k: v for k, v in item_dict.items() if k in selected_fields}
                            filtered_results.append(filtered_item)
                        
                        # Replace results with filtered results
                        results = filtered_results
                
                return results

        # Set up return annotation based on response model
        if self.response_model:
            endpoint.__annotations__["return"] = list[self.response_model]
        else:
            endpoint.__annotations__["return"] = list[dict]
            
        # Add filter_params annotation if available
        if filter_params:
            endpoint.__annotations__["filter_params"] = Annotated[filter_params, Query()]
            
        # Set the endpoint on the class
        setattr(self.__class__, "endpoint", endpoint)


class ImportRouter(UnoRouter):
    """Router for importing an entity."""
    
    path_suffix: str = ""
    method: str = "PUT"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None

    @computed_field
    def summary(self) -> str:
        """Get summary for OpenAPI documentation."""
        # Get display name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            
        return f"Import a {display_name}"

    @computed_field
    def description(self) -> str:
        """Get description for OpenAPI documentation."""
        # Get display name and schema name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
            schema_name = self.model.entity_type.__name__ if hasattr(self.model, 'entity_type') else self._get_model_name()
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            schema_name = self.model.__name__
            
        return f"""
            Import a {display_name} to the database.
            This will overwrite all of the entity's fields.
            Generally, this is used to import data from another
            instance of the database. The {display_name} 
            data must be in the format of the
            __{schema_name}View__ schema.   
        """

    def endpoint_factory(self):
        """Create the import endpoint."""
        from typing import Dict, Any, List, Union

        async def endpoint(self, body: Union[BaseModel, List[BaseModel]]):
            try:
                # Check if this is a batch import (list of entities)
                if isinstance(body, list):
                    # Check if batch operations are supported
                    if isinstance(self.model, RepositoryAdapter) and hasattr(self.model, 'batch_save'):
                        # Use batch import
                        results = await self.model.batch_save(body)
                    else:
                        # Fall back to individual imports
                        results = []
                        for item in body:
                            result = await self.model.save(item, importing=True)
                            if result:
                                results.append(result)
                    
                    return results
                else:
                    # Single entity import
                    result = await self.model.save(body, importing=True)
                    
                    # Handle import failure
                    if result is None:
                        raise HTTPException(status_code=400, detail="Entity import failed")
                        
                    return result
                    
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error importing entity: {str(e)}")
                raise HTTPException(status_code=500, detail="Error importing entity")

        # Set up parameter and return annotations
        endpoint.__annotations__["body"] = Union[self.body_model or Dict[str, Any], List[self.body_model or Dict[str, Any]]]
        
        if self.response_model:
            endpoint.__annotations__["return"] = Union[self.response_model, List[self.response_model]]
        else:
            endpoint.__annotations__["return"] = Any
            
        setattr(self.__class__, "endpoint", endpoint)


class InsertRouter(UnoRouter):
    """Router for creating a new entity."""
    
    path_suffix: str = ""
    method: str = "POST"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None

    @computed_field
    def summary(self) -> str:
        """Get summary for OpenAPI documentation."""
        # Get display name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            
        return f"Create a new {display_name}"

    @computed_field
    def description(self) -> str:
        """Get description for OpenAPI documentation."""
        # Get display name and schema name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
            schema_name = self.model.entity_type.__name__ if hasattr(self.model, 'entity_type') else self._get_model_name()
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            schema_name = self.model.__name__
            
        return f"Create a new {display_name} using the __{schema_name}Insert__ schema."

    def endpoint_factory(self):
        """Create the insert endpoint."""
        from typing import Dict, Any

        async def endpoint(self, body: BaseModel, response: Response) -> BaseModel:
            try:
                # Create the entity using the appropriate method
                result = await self.model.save(body)
                
                # Handle creation failure
                if result is None:
                    raise HTTPException(status_code=400, detail="Entity creation failed")
                    
                # Set the response status code to 201 Created
                response.status_code = status.HTTP_201_CREATED
                
                return result
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error creating entity: {str(e)}")
                raise HTTPException(status_code=500, detail="Error creating entity")

        # Set up parameter and return annotations
        endpoint.__annotations__["body"] = self.body_model or Dict[str, Any]
        
        if self.response_model:
            endpoint.__annotations__["return"] = self.response_model
        else:
            endpoint.__annotations__["return"] = Any
            
        setattr(self.__class__, "endpoint", endpoint)


class SelectRouter(UnoRouter):
    """Router for selecting a single entity by ID."""
    
    path_suffix: str = "/{id}"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None

    @computed_field
    def summary(self) -> str:
        """Get summary for OpenAPI documentation."""
        # Get display name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            
        return f"Select a {display_name}"

    @computed_field
    def description(self) -> str:
        """Get description for OpenAPI documentation."""
        # Get display name and schema name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
            schema_name = self.model.entity_type.__name__ if hasattr(self.model, 'entity_type') else self._get_model_name()
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            schema_name = self.model.__name__
            
        return f"""Select a {display_name}, by its ID. Returns the __{schema_name}Select__ schema.
        
        Supports the following query parameters:
        - `fields`: Comma-separated list of fields to include in the response (partial response)
        """

    def endpoint_factory(self):
        """Create the select endpoint."""
        from fastapi import Query as QueryParam
        from typing import Optional

        async def endpoint(
            self, 
            id: str,
            fields: Optional[str] = QueryParam(None, description="Comma-separated list of fields to include in the response")
        ) -> BaseModel:
            try:
                # Get the entity using the appropriate method
                result = await self.model.get(id=id)
                
                # Handle not found
                if result is None:
                    raise HTTPException(status_code=404, detail="Object not found")
                    
                # If field selection is requested, filter the response
                if fields:
                    selected_fields = fields.split(',')
                    
                    # Apply field selection based on result type
                    if hasattr(result, "to_dict"):
                        entity_dict = result.to_dict()
                    elif hasattr(result, "model_dump"):
                        entity_dict = result.model_dump()
                    else:
                        # For other types, try to convert to dict
                        try:
                            entity_dict = dict(result)
                        except:
                            # If conversion fails, return as is
                            return result
                    
                    # Filter to include only selected fields
                    filtered_entity = {k: v for k, v in entity_dict.items() if k in selected_fields}
                    
                    # Return filtered entity
                    return filtered_entity
                        
                # Return full entity
                return result
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error getting entity {id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving entity")

        # Set up return annotation based on response model
        if self.response_model:
            endpoint.__annotations__["return"] = self.response_model
        else:
            endpoint.__annotations__["return"] = Any
            
        setattr(self.__class__, "endpoint", endpoint)


class UpdateRouter(UnoRouter):
    """Router for updating an entity by ID."""
    
    path_suffix: str = "/{id}"
    method: str = "PATCH"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None

    @computed_field
    def summary(self) -> str:
        """Get summary for OpenAPI documentation."""
        # Get display name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            
        return f"Update a {display_name}"

    @computed_field
    def description(self) -> str:
        """Get description for OpenAPI documentation."""
        # Get display name and schema name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
            schema_name = self.model.entity_type.__name__ if hasattr(self.model, 'entity_type') else self._get_model_name()
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            schema_name = self.model.__name__
            
        return f"Update a {display_name}, by its ID, using the __{schema_name}Update__ schema."

    def endpoint_factory(self):
        """Create the update endpoint."""
        from typing import Dict, Any

        async def endpoint(self, id: str, body: BaseModel) -> BaseModel:
            try:
                # Ensure body data includes the ID
                if hasattr(body, "model_dump"):
                    data = body.model_dump()
                else:
                    data = dict(body)
                
                # Add ID to data if not present
                if "id" not in data or not data["id"]:
                    data["id"] = id
                    
                # Update the entity using the appropriate method
                result = await self.model.save(body if isinstance(body, BaseModel) else data)
                
                # Handle update failure
                if result is None:
                    raise HTTPException(status_code=404, detail="Entity not found or update failed")
                    
                return result
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error updating entity {id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error updating entity")

        # Set up parameter and return annotations
        endpoint.__annotations__["body"] = self.body_model or Dict[str, Any]
        
        if self.response_model:
            endpoint.__annotations__["return"] = self.response_model
        else:
            endpoint.__annotations__["return"] = Any
            
        setattr(self.__class__, "endpoint", endpoint)


class DeleteRouter(UnoRouter):
    """Router for deleting an entity by ID."""
    
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None

    @computed_field
    def summary(self) -> str:
        """Get summary for OpenAPI documentation."""
        # Get display name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            
        return f"Delete a {display_name}"

    @computed_field
    def description(self) -> str:
        """Get description for OpenAPI documentation."""
        # Get display name and schema name from model or adapter
        if isinstance(self.model, RepositoryAdapter):
            display_name = self.model.display_name
            schema_name = self.model.entity_type.__name__ if hasattr(self.model, 'entity_type') else self._get_model_name()
        else:
            display_name = getattr(self.model, 'display_name', self._get_model_name())
            schema_name = self.model.__name__
            
        return f"Delete a {display_name} by its ID."

    def endpoint_factory(self):
        """Create the delete endpoint."""
        from typing import Dict

        async def endpoint(self, id: str) -> Dict[str, str]:
            try:
                # Delete the entity using the appropriate method
                result = await self.model.delete_(id)
                
                # Handle deletion failure
                if not result:
                    raise HTTPException(status_code=404, detail="Entity not found or deletion failed")
                    
                return {"message": "Entity deleted successfully"}
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error deleting entity {id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error deleting entity")

        # Set return annotation
        endpoint.__annotations__["return"] = Dict[str, str]
        setattr(self.__class__, "endpoint", endpoint)


class UnoEndpoint(BaseModel):
    """Base endpoint class for creating API endpoints."""
    
    registry: ClassVar[dict[str, "UnoEndpoint"]] = {}

    # Model can be a domain model class or a repository adapter
    model: Union[Type[BaseModel], RepositoryAdapter]
    router: Type[UnoRouter]
    body_model: Optional[str | Type[BaseModel] | None] = None
    response_model: Optional[str | Type[BaseModel]]
    include_in_schema: bool = True
    status_code: int = 200
    app: Optional[FastAPI] = None
    api_router: Optional[APIRouter] = None
    dependencies: list[Depends] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, *args, app: Optional[FastAPI] = None, router: Optional[APIRouter] = None, **kwargs) -> None:
        """
        Initialize the endpoint.
        
        Args:
            *args: Positional arguments for the superclass
            app: FastAPI application
            router: Optional API router
            **kwargs: Keyword arguments for the superclass
        """
        # Set app and router from parameters or class attributes
        kwargs['app'] = app or self.app
        kwargs['router'] = router or self.api_router
        super().__init__(*args, **kwargs)
        
        # Ensure either app or router is provided
        if not kwargs['app'] and not kwargs['router']:
            raise ValueError("Either app or router must be provided")
            
        # Resolve body and response schemas
        body_schema = None
        response_schema = None
        
        # Handle different model types
        if isinstance(self.model, RepositoryAdapter):
            # For repository adapters
            if isinstance(self.body_model, str) and hasattr(self.model, 'schema_manager') and hasattr(self.model.schema_manager, 'get_schema'):
                # Use schema manager to get schema
                body_schema = self.model.schema_manager.get_schema(self.body_model)
                if body_schema is None and self.body_model is not None:
                    logger.warning(f"Body schema '{self.body_model}' not found in schema manager")
            elif isinstance(self.body_model, type):
                # Use provided schema class directly
                body_schema = self.body_model
                
            if isinstance(self.response_model, str) and hasattr(self.model, 'schema_manager') and hasattr(self.model.schema_manager, 'get_schema'):
                # Use schema manager to get schema
                response_schema = self.model.schema_manager.get_schema(self.response_model)
                if response_schema is None and self.response_model is not None:
                    logger.warning(f"Response schema '{self.response_model}' not found in schema manager")
            elif isinstance(self.response_model, type):
                # Use provided schema class directly
                response_schema = self.response_model
        else:
            # For legacy model classes
            if hasattr(self.model, 'schema_manager'):
                # Legacy models have a schema_manager attribute
                if isinstance(self.body_model, str) and self.body_model is not None:
                    body_schema = self.model.schema_manager.get_schema(self.body_model)
                    if body_schema is None:
                        raise Exception(
                            f"Body schema '{self.body_model}' not found in schema manager for {self.model.__name__}"
                        )
                else:
                    body_schema = self.body_model
                    
                if isinstance(self.response_model, str) and self.response_model is not None:
                    response_schema = self.model.schema_manager.get_schema(self.response_model)
                    if response_schema is None:
                        raise Exception(
                            f"Response schema '{self.response_model}' not found in schema manager"
                        )
                else:
                    response_schema = self.response_model

        # Create the router instance with model and schemas
        self.router(
            app=kwargs['app'],
            router=kwargs['router'],
            model=self.model,
            body_model=body_schema,
            response_model=response_schema,
            include_in_schema=self.include_in_schema,
            status_code=self.status_code,
            dependencies=self.dependencies,
        )

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Initialize a subclass.
        
        This method registers the subclass in the registry.
        
        Args:
            **kwargs: Keyword arguments for the superclass
        
        Raises:
            RegistryClassNotFoundError: If a class with the same name already exists in the registry
        """
        super().__init_subclass__(**kwargs)
        
        # Don't add the UnoEndpoint class itself to the registry
        if cls is UnoEndpoint:
            return
            
        # Add the subclass to the registry if it is not already there
        if cls.__name__ not in cls.registry:
            cls.registry.update({cls.__name__: cls})
        else:
            raise RegistryClassNotFoundError(
                f"An Endpoint class with the name {cls.__name__} already exists in the registry."
            )


class CreateEndpoint(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoDTO = "edit_schema"
    response_model: UnoDTO = "view_schema"
    status_code: int = status.HTTP_201_CREATED


class ViewEndpoint(UnoEndpoint):
    router: UnoRouter = SelectRouter
    body_model: UnoDTO = None
    response_model: UnoDTO = "view_schema"


class ListEndpoint(UnoEndpoint):
    router: UnoRouter = ListRouter
    body_model: UnoDTO = None
    response_model: UnoDTO = "view_schema"


class UpdateEndpoint(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoDTO = "edit_schema"
    response_model: UnoDTO = "view_schema"


class DeleteEndpoint(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    body_model: UnoDTO = None
    response_model: UnoDTO = None


class ImportEndpoint(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoDTO = "view_schema"
    response_model: UnoDTO = "view_schema"
    status_code: int = status.HTTP_201_CREATED
