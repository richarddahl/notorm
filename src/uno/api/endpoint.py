# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
import enum
from typing import Optional, ClassVar, Annotated

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

from uno.schema.schema import UnoSchema
from uno.registry_errors import RegistryClassNotFoundError
from uno.settings import uno_settings


class UnoRouter(BaseModel, ABC):
    model: type[BaseModel]
    response_model: type[BaseModel] | None = None
    body_model: type[BaseModel] | None = None
    path_suffix: str
    method: str
    path_prefix: str = "/api"
    api_version: str = uno_settings.API_VERSION
    include_in_schema: bool = True
    tags: list[str | enum.StrEnum] | None = None
    return_list: bool = False
    app: FastAPI = None
    status_code: int = status.HTTP_200_OK

    model_config: dict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint_factory()
        router = APIRouter()
        router.add_api_route(
            f"{self.path_prefix}/{self.api_version}/{self.model.__name__.lower()}{self.path_suffix}",
            endpoint=self.endpoint,
            methods=[self.method],
            include_in_schema=self.include_in_schema,
            tags=[self.model.display_name_plural],
            summary=self.summary,
            description=self.description,
            status_code=self.status_code,
            response_model_exclude_none=True,
        )
        self.app.include_router(router)

    @abstractmethod
    def endpoint_factory(self):
        raise NotImplementedError


class ListRouter(UnoRouter):
    path_suffix: str = ""
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    return_list: bool = True
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"List {self.model.display_name_plural}"

    @computed_field
    def description(self) -> str:
        return f"""Returns a list of {self.model.display_name_plural} with the __{self.model.__name__.title()}View__ schema.
        
        Supports the following query parameters:
        - `stream`: Set to `true` to enable streaming response for large result sets
        - `fields`: Comma-separated list of fields to include in the response (partial response)
        - `page`: Page number for pagination (starting from 1)
        - `page_size`: Number of items per page (default: 50, max: 500)
        """

    def endpoint_factory(self) -> None:
        from fastapi.responses import StreamingResponse
        from fastapi import Request, Header, Query as QueryParam
        from typing import Optional, List
        import json
        import asyncio
        from uno.database.streaming import stream_query, StreamingMode
        
        filter_params = self.model.create_filter_params()

        async def endpoint(
            self,
            request: Request,
            filter_params: Annotated[filter_params, Query()] = None,
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
            
            # Validate the filters
            filters = self.model.validate_filter_params(filter_params)
            
            # If streaming is requested and supported
            if supports_streaming:
                # Get raw query from model's filter method
                raw_query = await self.model.get_filter_query(filters=filters)
                
                # Define the transformation to include only selected fields
                def transform_entity(entity):
                    # Convert entity to dict
                    if hasattr(entity, "to_dict"):
                        entity_dict = entity.to_dict()
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
                # Get results with pagination
                results = await self.model.filter(
                    filters=filters, 
                    page=page, 
                    page_size=page_size
                )
                
                # If field selection is requested, filter the results
                if selected_fields:
                    # Process entities to include only selected fields
                    if hasattr(results, "items"):  # Paginated response
                        filtered_items = []
                        for item in results.items:
                            if hasattr(item, "to_dict"):
                                item_dict = item.to_dict()
                                filtered_item = {k: v for k, v in item_dict.items() if k in selected_fields}
                                filtered_items.append(filtered_item)
                            else:
                                filtered_items.append(item)
                        
                        # Replace items with filtered items
                        results.items = filtered_items
                    elif isinstance(results, list):  # List response
                        filtered_results = []
                        for item in results:
                            if hasattr(item, "to_dict"):
                                item_dict = item.to_dict()
                                filtered_item = {k: v for k, v in item_dict.items() if k in selected_fields}
                                filtered_results.append(filtered_item)
                            else:
                                filtered_results.append(item)
                        
                        # Replace results with filtered results
                        results = filtered_results
                
                return results

        endpoint.__annotations__["return"] = list[self.response_model]
        setattr(self.__class__, "endpoint", endpoint)


class ImportRouter(UnoRouter):
    path_suffix: str = ""
    method: str = "PUT"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None

    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Import a new {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"""
            Import a new {self.model.display_name} to the database.
            This will overwrite the all of the object's fields.
            Generally, this is used to import data from another
            instance of the database. The {self.model.display_name} 
            data must be in the format of the
            __{self.model.__name__.title()}Insert__ schema.   
        """

    def endpoint_factory(self):

        async def endpoint(self, body: BaseModel):
            result = await self.model.save(body, importing=True)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class InsertRouter(UnoRouter):
    path_suffix: str = ""
    method: str = "POST"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Create a new {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Create a new {self.model.display_name} using the __{self.model.__name__.title()}Insert__ schema."

    def endpoint_factory(self):

        async def endpoint(self, body: BaseModel, response: Response) -> BaseModel:
            response.status_code = status.HTTP_201_CREATED
            result = await self.model.save(body)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class SelectRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Select a {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"""Select a {self.model.display_name}, by its ID. Returns the __{self.model.__name__.title()}Select__ schema.
        
        Supports the following query parameters:
        - `fields`: Comma-separated list of fields to include in the response (partial response)
        """

    def endpoint_factory(self):
        from fastapi import Query as QueryParam
        from typing import Optional

        async def endpoint(
            self, 
            id: str,
            fields: Optional[str] = QueryParam(None, description="Comma-separated list of fields to include in the response")
        ) -> BaseModel:
            # Get the entity
            result = await self.model.get(id=id)
            if result is None:
                raise HTTPException(status_code=404, detail="Object not found")
                
            # If field selection is requested, filter the response
            if fields:
                selected_fields = fields.split(',')
                
                # Apply field selection
                if hasattr(result, "to_dict"):
                    entity_dict = result.to_dict()
                    # Filter to include only selected fields
                    filtered_entity = {k: v for k, v in entity_dict.items() if k in selected_fields}
                    
                    # Return filtered entity
                    return filtered_entity
                    
            # Return full entity
            return result

        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class UpdateRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "PATCH"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Update a new {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Update a {self.model.display_name}, by its ID, using the __{self.model.__name__.title()}Update__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str, body: BaseModel):
            result = await self.model.save(body)
            return result

        endpoint.__annotations__["body"] = self.body_model
        endpoint.__annotations__["return"] = self.response_model
        setattr(self.__class__, "endpoint", endpoint)


class DeleteRouter(UnoRouter):
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    path_prefix: str = "/api"
    tags: list[str | enum.StrEnum] | None = None
    # summary: str = "" <- computed_field
    # description: str = "" <- computed_field

    @computed_field
    def summary(self) -> str:
        return f"Delete a {self.model.display_name}"

    @computed_field
    def description(self) -> str:
        return f"Delete a {self.model.display_name}, by its ID, using the __{self.model.__name__.title()}Delete__ schema."

    def endpoint_factory(self):

        async def endpoint(self, id: str) -> BaseModel:
            result = await self.model.delete_(id)
            return {"message": "delete"}

        endpoint.__annotations__["return"] = bool
        setattr(self.__class__, "endpoint", endpoint)


class UnoEndpoint(BaseModel):
    registry: ClassVar[dict[str, "UnoEndpoint"]] = {}

    model: type[BaseModel]
    router: UnoRouter
    body_model: Optional[str | None] = None
    response_model: Optional[str]
    include_in_schema: bool = True
    status_code: int = 200

    model_config: ConfigDict = {"arbitrary_types_allowed": True}

    def __init__(self, *args, app: FastAPI, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Retrieve schemas from the model's schema_manager
        if self.body_model is not None:
            # Ensure that the schemas have been created
            body_schema = self.model.schema_manager.get_schema(self.body_model)
            if body_schema is None:
                raise Exception(
                    f"Body schema '{self.body_model}' not found in schema manager for {self.model.__name__}"
                )
        else:
            body_schema = None

        if self.response_model is not None:
            response_schema = self.model.schema_manager.get_schema(self.response_model)
            if response_schema is None:
                raise Exception(
                    f"Response schema '{self.response_model}' not found in schema manager"
                )
        else:
            response_schema = None

        self.router(
            app=app,
            model=self.model,
            body_model=body_schema,
            response_model=response_schema,
            include_in_schema=self.include_in_schema,
            status_code=self.status_code,
        )

    def __init_subclass__(cls, **kwargs) -> None:

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
    body_model: UnoSchema = "edit_schema"
    response_model: UnoSchema = "view_schema"
    status_code: int = status.HTTP_201_CREATED


class ViewEndpoint(UnoEndpoint):
    router: UnoRouter = SelectRouter
    body_model: UnoSchema = None
    response_model: UnoSchema = "view_schema"


class ListEndpoint(UnoEndpoint):
    router: UnoRouter = ListRouter
    body_model: UnoSchema = None
    response_model: UnoSchema = "view_schema"


class UpdateEndpoint(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoSchema = "edit_schema"
    response_model: UnoSchema = "view_schema"


class DeleteEndpoint(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    body_model: UnoSchema = None
    response_model: UnoSchema = None


class ImportEndpoint(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoSchema = "view_schema"
    response_model: UnoSchema = "view_schema"
    status_code: int = status.HTTP_201_CREATED
