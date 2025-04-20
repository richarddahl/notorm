"""
API integration for the Meta module.

This module provides functions to register meta-related API endpoints with FastAPI,
following the domain-driven design approach with a clean separation between domain logic
and API contracts.
"""

from typing import List, Dict, Any, Optional, Union, Callable
from fastapi import APIRouter, FastAPI, Depends, Query, Path, HTTPException, status

from uno.meta.entities import MetaType, MetaRecord
from uno.meta.dtos import (
    # Meta Type DTOs
    MetaTypeCreateDto,
    MetaTypeUpdateDto,
    MetaTypeViewDto,
    MetaTypeFilterParams,
    MetaTypeListDto,
    # Meta Record DTOs
    MetaRecordCreateDto,
    MetaRecordUpdateDto,
    MetaRecordViewDto,
    MetaRecordFilterParams,
    MetaRecordListDto,
)
from uno.meta.schemas import MetaTypeSchemaManager, MetaRecordSchemaManager
from uno.meta.domain_services import MetaTypeDomainService, MetaRecordDomainService


def register_meta_type_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    meta_type_service: Optional[MetaTypeDomainService] = None,
) -> dict[str, Any]:
    """
    Register API endpoints for meta type management.

    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        meta_type_service: Optional MetaTypeDomainService instance (for testing)

    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/meta/types",
            tags=["Meta Types"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router

    # Create schema manager
    schema_manager = MetaTypeSchemaManager()

    # GET /meta/types
    @router.get(
        "",
        response_model=MetaTypeListDto,
        summary="List meta types",
        description="Retrieve a paginated list of meta types with optional filtering",
    )
    async def list_meta_types(
        filters: MetaTypeFilterParams = Depends(),
        service: MetaTypeDomainService = Depends(lambda: meta_type_service),
    ) -> MetaTypeListDto:
        types, record_counts, total = await service.list_meta_types(filters)
        return schema_manager.entities_to_list_dto(
            types, record_counts, total, filters.limit, filters.offset
        )

    # POST /meta/types
    @router.post(
        "",
        response_model=MetaTypeViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create meta type",
        description="Create a new meta type",
    )
    async def create_meta_type(
        meta_type_data: MetaTypeCreateDto,
        service: MetaTypeDomainService = Depends(lambda: meta_type_service),
    ) -> MetaTypeViewDto:
        meta_type_entity = schema_manager.dto_to_entity(meta_type_data)
        created_meta_type = await service.create_meta_type(meta_type_entity)
        return schema_manager.entity_to_dto(created_meta_type)

    # GET /meta/types/{meta_type_id}
    @router.get(
        "/{meta_type_id}",
        response_model=MetaTypeViewDto,
        summary="Get meta type",
        description="Retrieve a specific meta type by ID",
    )
    async def get_meta_type(
        meta_type_id: str = Path(
            ..., description="The ID of the meta type to retrieve"
        ),
        service: MetaTypeDomainService = Depends(lambda: meta_type_service),
    ) -> MetaTypeViewDto:
        meta_type, record_count = await service.get_meta_type_by_id(meta_type_id)
        if not meta_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meta type with ID {meta_type_id} not found",
            )
        return schema_manager.entity_to_dto(meta_type, record_count)

    # PATCH /meta/types/{meta_type_id}
    @router.patch(
        "/{meta_type_id}",
        response_model=MetaTypeViewDto,
        summary="Update meta type",
        description="Update an existing meta type",
    )
    async def update_meta_type(
        meta_type_data: MetaTypeUpdateDto,
        meta_type_id: str = Path(..., description="The ID of the meta type to update"),
        service: MetaTypeDomainService = Depends(lambda: meta_type_service),
    ) -> MetaTypeViewDto:
        meta_type, record_count = await service.get_meta_type_by_id(meta_type_id)
        if not meta_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meta type with ID {meta_type_id} not found",
            )

        updated_entity = schema_manager.dto_to_entity(meta_type_data, meta_type)
        updated_meta_type = await service.update_meta_type(updated_entity)
        return schema_manager.entity_to_dto(updated_meta_type, record_count)

    # DELETE /meta/types/{meta_type_id}
    @router.delete(
        "/{meta_type_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete meta type",
        description="Delete an existing meta type",
    )
    async def delete_meta_type(
        meta_type_id: str = Path(..., description="The ID of the meta type to delete"),
        service: MetaTypeDomainService = Depends(lambda: meta_type_service),
    ) -> None:
        meta_type, _ = await service.get_meta_type_by_id(meta_type_id)
        if not meta_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meta type with ID {meta_type_id} not found",
            )

        await service.delete_meta_type(meta_type_id)
        return None

    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)

    # Return registered endpoints
    return {
        "list_meta_types": list_meta_types,
        "create_meta_type": create_meta_type,
        "get_meta_type": get_meta_type,
        "update_meta_type": update_meta_type,
        "delete_meta_type": delete_meta_type,
    }


def register_meta_record_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    meta_record_service: Optional[MetaRecordDomainService] = None,
) -> dict[str, Any]:
    """
    Register API endpoints for meta record management.

    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        meta_record_service: Optional MetaRecordDomainService instance (for testing)

    Returns:
        Dictionary of registered endpoints
    """
    # Create router if not using an existing one
    if isinstance(app_or_router, FastAPI):
        router = APIRouter(
            prefix=f"{path_prefix}/meta/records",
            tags=["Meta Records"],
            dependencies=dependencies or [],
        )
    else:
        router = app_or_router

    # Create schema manager
    schema_manager = MetaRecordSchemaManager()

    # GET /meta/records
    @router.get(
        "",
        response_model=MetaRecordListDto,
        summary="List meta records",
        description="Retrieve a paginated list of meta records with optional filtering",
    )
    async def list_meta_records(
        filters: MetaRecordFilterParams = Depends(),
        service: MetaRecordDomainService = Depends(lambda: meta_record_service),
    ) -> MetaRecordListDto:
        records, total = await service.list_meta_records(filters)
        return schema_manager.entities_to_list_dto(
            records, total, filters.limit, filters.offset
        )

    # POST /meta/records
    @router.post(
        "",
        response_model=MetaRecordViewDto,
        status_code=status.HTTP_201_CREATED,
        summary="Create meta record",
        description="Create a new meta record",
    )
    async def create_meta_record(
        meta_record_data: MetaRecordCreateDto,
        service: MetaRecordDomainService = Depends(lambda: meta_record_service),
    ) -> MetaRecordViewDto:
        meta_record_entity = schema_manager.dto_to_entity(meta_record_data)
        created_meta_record = await service.create_meta_record(meta_record_entity)
        return schema_manager.entity_to_dto(created_meta_record)

    # GET /meta/records/{meta_record_id}
    @router.get(
        "/{meta_record_id}",
        response_model=MetaRecordViewDto,
        summary="Get meta record",
        description="Retrieve a specific meta record by ID",
    )
    async def get_meta_record(
        meta_record_id: str = Path(
            ..., description="The ID of the meta record to retrieve"
        ),
        service: MetaRecordDomainService = Depends(lambda: meta_record_service),
    ) -> MetaRecordViewDto:
        meta_record = await service.get_meta_record_by_id(meta_record_id)
        if not meta_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meta record with ID {meta_record_id} not found",
            )
        return schema_manager.entity_to_dto(meta_record)

    # PATCH /meta/records/{meta_record_id}
    @router.patch(
        "/{meta_record_id}",
        response_model=MetaRecordViewDto,
        summary="Update meta record",
        description="Update an existing meta record",
    )
    async def update_meta_record(
        meta_record_data: MetaRecordUpdateDto,
        meta_record_id: str = Path(
            ..., description="The ID of the meta record to update"
        ),
        service: MetaRecordDomainService = Depends(lambda: meta_record_service),
    ) -> MetaRecordViewDto:
        meta_record = await service.get_meta_record_by_id(meta_record_id)
        if not meta_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meta record with ID {meta_record_id} not found",
            )

        updated_entity = schema_manager.dto_to_entity(meta_record_data, meta_record)
        updated_meta_record = await service.update_meta_record(updated_entity)
        return schema_manager.entity_to_dto(updated_meta_record)

    # DELETE /meta/records/{meta_record_id}
    @router.delete(
        "/{meta_record_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete meta record",
        description="Delete an existing meta record",
    )
    async def delete_meta_record(
        meta_record_id: str = Path(
            ..., description="The ID of the meta record to delete"
        ),
        service: MetaRecordDomainService = Depends(lambda: meta_record_service),
    ) -> None:
        meta_record = await service.get_meta_record_by_id(meta_record_id)
        if not meta_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meta record with ID {meta_record_id} not found",
            )

        await service.delete_meta_record(meta_record_id)
        return None

    # Include router in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)

    # Return registered endpoints
    return {
        "list_meta_records": list_meta_records,
        "create_meta_record": create_meta_record,
        "get_meta_record": get_meta_record,
        "update_meta_record": update_meta_record,
        "delete_meta_record": delete_meta_record,
    }


def register_meta_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    meta_type_service: Optional[MetaTypeDomainService] = None,
    meta_record_service: Optional[MetaRecordDomainService] = None,
) -> dict[str, dict[str, Any]]:
    """
    Register all meta-related API endpoints.

    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: URL path prefix
        dependencies: List of FastAPI dependencies
        include_auth: Whether to include authentication dependencies
        meta_type_service: Optional MetaTypeDomainService instance (for testing)
        meta_record_service: Optional MetaRecordDomainService instance (for testing)

    Returns:
        Dictionary of registered endpoints by resource type
    """
    # Create routers for each resource type
    if isinstance(app_or_router, FastAPI):
        meta_type_router = APIRouter(
            prefix=f"{path_prefix}/meta/types",
            tags=["Meta Types"],
            dependencies=dependencies or [],
        )
        meta_record_router = APIRouter(
            prefix=f"{path_prefix}/meta/records",
            tags=["Meta Records"],
            dependencies=dependencies or [],
        )
    else:
        # Use the provided router for everything
        meta_type_router = meta_record_router = app_or_router

    # Register endpoints for each resource type
    meta_type_endpoints = register_meta_type_endpoints(
        meta_type_router,
        path_prefix="",
        dependencies=None,
        include_auth=include_auth,
        meta_type_service=meta_type_service,
    )
    meta_record_endpoints = register_meta_record_endpoints(
        meta_record_router,
        path_prefix="",
        dependencies=None,
        include_auth=include_auth,
        meta_record_service=meta_record_service,
    )

    # Include routers in app if using FastAPI app
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(meta_type_router)
        app_or_router.include_router(meta_record_router)

    # Return all registered endpoints
    return {
        "meta_types": meta_type_endpoints,
        "meta_records": meta_record_endpoints,
    }
