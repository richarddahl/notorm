"""API integration for the Reports module."""

from typing import Any, Dict, List, Optional, Union, Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, FastAPI, JSONResponse
from pydantic import BaseModel

from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
)
from uno.reports.domain_repositories import (
    ReportFieldDefinitionRepository,
    ReportTemplateRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)
from uno.reports.domain_services import (
    ReportFieldDefinitionService,
    ReportTemplateService,
    ReportTriggerService,
    ReportOutputService,
    ReportExecutionService,
    ReportOutputExecutionService,
)
from uno.reports.schemas import (
    ReportFieldDefinitionSchemaManager,
    ReportTemplateSchemaManager,
    ReportTriggerSchemaManager,
    ReportOutputSchemaManager,
    ReportExecutionSchemaManager,
    ReportOutputExecutionSchemaManager,
)
from uno.reports.dtos import (
    # Field Definition DTOs
    ReportFieldDefinitionCreateDto,
    ReportFieldDefinitionUpdateDto,
    ReportFieldDefinitionViewDto,
    ReportFieldDefinitionFilterParams,
    # Template DTOs
    ReportTemplateCreateDto,
    ReportTemplateUpdateDto,
    ReportTemplateViewDto,
    ReportTemplateFilterParams,
    # Trigger DTOs
    ReportTriggerCreateDto,
    ReportTriggerUpdateDto,
    ReportTriggerViewDto,
    ReportTriggerFilterParams,
    # Output DTOs
    ReportOutputCreateDto,
    ReportOutputUpdateDto,
    ReportOutputViewDto,
    ReportOutputFilterParams,
    # Execution DTOs
    ReportExecutionCreateDto,
    ReportExecutionUpdateStatusDto,
    ReportExecutionViewDto,
    ReportExecutionFilterParams,
    # Output Execution DTOs
    ReportOutputExecutionCreateDto,
    ReportOutputExecutionUpdateStatusDto,
    ReportOutputExecutionViewDto,
    ReportOutputExecutionFilterParams,
)


def register_report_field_definition_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    field_definition_service: Optional[ReportFieldDefinitionService] = None,
) -> dict[str, Any]:
    """Register API endpoints for report field definitions.

    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        field_definition_service: Optional field definition service to use.

    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-field-definitions",
        tags=["Report Field Definitions"],
        dependencies=dependencies or [],
    )

    handlers = {}

    # Get service from DI container if not provided
    if field_definition_service is None:
        from uno.dependencies import get_service

        field_definition_service = get_service(ReportFieldDefinitionService)

    schema_manager = ReportFieldDefinitionSchemaManager()

    # Create field definition
    @router.post(
        "",
        response_model=ReportFieldDefinitionViewDto,
        status_code=201,
        summary="Create a new report field definition",
    )
    async def create_field_definition(
        data: ReportFieldDefinitionCreateDto = Body(...),
    ) -> ReportFieldDefinitionViewDto:
        """Create a new report field definition."""
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data)

        # Create entity
        result = await field_definition_service.create(entity)
        if result.is_failure:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

        # Convert entity to DTO
        return schema_manager.entity_to_dto(result.value)

    handlers["create_field_definition"] = create_field_definition

    # Get field definition by ID
    @router.get(
        "/{field_definition_id}",
        response_model=ReportFieldDefinitionViewDto,
        summary="Get a report field definition by ID",
    )
    async def get_field_definition(
        field_definition_id: str = Path(
            ..., description="The ID of the field definition"
        ),
    ) -> ReportFieldDefinitionViewDto:
        """Get a report field definition by ID."""
        result = await field_definition_service.get(field_definition_id)
        if result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Field definition with ID {field_definition_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        return schema_manager.entity_to_dto(result.value)

    handlers["get_field_definition"] = get_field_definition

    # List field definitions with filtering
    @router.get(
        "",
        response_model=list[ReportFieldDefinitionViewDto],
        summary="List report field definitions",
    )
    async def list_field_definitions(
        name: str | None = Query(None, description="Filter by field name"),
        field_type: str | None = Query(None, description="Filter by field type"),
        parent_field_id: str | None = Query(
            None, description="Filter by parent field ID"
        ),
        template_id: str | None = Query(None, description="Filter by template ID"),
        is_visible: Optional[bool] = Query(None, description="Filter by visibility"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> list[ReportFieldDefinitionViewDto]:
        """List report field definitions with filtering."""
        filters = {}

        if name:
            filters["name"] = {"lookup": "eq", "val": name}
        if field_type:
            filters["field_type"] = {"lookup": "eq", "val": field_type}
        if parent_field_id:
            filters["parent_field_id"] = {"lookup": "eq", "val": parent_field_id}
        if is_visible is not None:
            filters["is_visible"] = {"lookup": "eq", "val": is_visible}

        # Handle template_id special case
        if template_id:
            # Using the repository method that joins through the junction table
            field_definition_repository = field_definition_service.repository
            entities = await field_definition_repository.find_by_template_id(
                template_id
            )
            # Apply skip and limit
            entities = entities[skip : skip + limit]
            return schema_manager.entity_list_to_dto_list(entities)

        # Standard filtering
        result = await field_definition_service.list(
            filters=filters, skip=skip, limit=limit
        )
        if result.is_failure:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

        return schema_manager.entity_list_to_dto_list(result.value)

    handlers["list_field_definitions"] = list_field_definitions

    # Update field definition
    @router.patch(
        "/{field_definition_id}",
        response_model=ReportFieldDefinitionViewDto,
        summary="Update a report field definition",
    )
    async def update_field_definition(
        field_definition_id: str = Path(
            ..., description="The ID of the field definition"
        ),
        data: ReportFieldDefinitionUpdateDto = Body(...),
    ) -> ReportFieldDefinitionViewDto:
        """Update a report field definition."""
        # Get existing entity
        get_result = await field_definition_service.get(field_definition_id)
        if get_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Field definition with ID {field_definition_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)

        # Update entity
        update_result = await field_definition_service.update(entity)
        if update_result.is_failure:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

        return schema_manager.entity_to_dto(update_result.value)

    handlers["update_field_definition"] = update_field_definition

    # Delete field definition
    @router.delete(
        "/{field_definition_id}",
        status_code=204,
        summary="Delete a report field definition",
    )
    async def delete_field_definition(
        field_definition_id: str = Path(
            ..., description="The ID of the field definition"
        ),
    ) -> None:
        """Delete a report field definition."""
        delete_result = await field_definition_service.delete(field_definition_id)
        if delete_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Field definition with ID {field_definition_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

    handlers["delete_field_definition"] = delete_field_definition

    # Register router
    app_or_router.include_router(router)

    return handlers


def register_report_template_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    template_service: Optional[ReportTemplateService] = None,
    field_definition_service: Optional[ReportFieldDefinitionService] = None,
) -> dict[str, Any]:
    """Register API endpoints for report templates.

    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        template_service: Optional template service to use.
        field_definition_service: Optional field definition service to use.

    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-templates",
        tags=["Report Templates"],
        dependencies=dependencies or [],
    )

    handlers = {}

    # Get services from DI container if not provided
    if template_service is None or field_definition_service is None:
        from uno.dependencies import get_service

        template_service = template_service or get_service(ReportTemplateService)
        field_definition_service = field_definition_service or get_service(
            ReportFieldDefinitionService
        )

    schema_manager = ReportTemplateSchemaManager()
    field_definition_schema_manager = ReportFieldDefinitionSchemaManager()

    # Create template
    @router.post(
        "",
        response_model=ReportTemplateViewDto,
        status_code=201,
        summary="Create a new report template",
    )
    async def create_template(
        data: ReportTemplateCreateDto = Body(...),
    ) -> ReportTemplateViewDto:
        """Create a new report template."""
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data)

        # If field_ids are provided, use create_with_relationships
        if hasattr(data, "field_ids") and data.field_ids:
            result = await template_service.create_with_relationships(
                entity, data.field_ids
            )
        else:
            result = await template_service.create(entity)

        if result.is_failure:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

        # Get with relationships
        get_result = await template_service.get_with_relationships(result.value.id)
        if get_result.is_failure:
            # Fall back to entity without relationships
            return schema_manager.entity_to_dto(result.value)

        return schema_manager.entity_to_dto(get_result.value)

    handlers["create_template"] = create_template

    # Get template by ID
    @router.get(
        "/{template_id}",
        response_model=ReportTemplateViewDto,
        summary="Get a report template by ID",
    )
    async def get_template(
        template_id: str = Path(..., description="The ID of the template"),
    ) -> ReportTemplateViewDto:
        """Get a report template by ID."""
        result = await template_service.get_with_relationships(template_id)
        if result.is_failure:
            # Try getting without relationships
            simple_result = await template_service.get(template_id)
            if simple_result.is_failure:
                return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Resource not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )
                    status_code=404, detail=f"Template with ID {template_id} not found"
                )
            return schema_manager.entity_to_dto(simple_result.value)

        return schema_manager.entity_to_dto(result.value)

    handlers["get_template"] = get_template

    # List templates with filtering
    @router.get(
        "",
        response_model=list[ReportTemplateViewDto],
        summary="List report templates",
    )
    async def list_templates(
        name: str | None = Query(None, description="Filter by template name"),
        base_object_type: str | None = Query(
            None, description="Filter by base object type"
        ),
        field_id: str | None = Query(None, description="Filter by associated field ID"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> list[ReportTemplateViewDto]:
        """List report templates with filtering."""
        filters = {}

        if name:
            filters["name"] = {"lookup": "eq", "val": name}
        if base_object_type:
            filters["base_object_type"] = {"lookup": "eq", "val": base_object_type}

        # Handle field_id special case
        if field_id:
            # This would need a custom repository method
            # For this example, we'll just get all templates and filter in memory
            result = await template_service.list()
            if result.is_failure:
                return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

            # Load relationships for all templates
            templates_with_fields = []
            for template in result.value:
                template_result = await template_service.get_with_relationships(
                    template.id
                )
                if template_result.is_success:
                    templates_with_fields.append(template_result.value)

            # Filter templates by field_id
            filtered_templates = [
                template
                for template in templates_with_fields
                if any(field.id == field_id for field in template.fields)
            ]

            # Apply skip and limit
            paginated_templates = filtered_templates[skip : skip + limit]

            return schema_manager.entity_list_to_dto_list(paginated_templates)

        # Standard filtering
        result = await template_service.list(filters=filters, skip=skip, limit=limit)
        if result.is_failure:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

        # Load relationships for all templates
        templates_with_fields = []
        for template in result.value:
            template_result = await template_service.get_with_relationships(template.id)
            if template_result.is_success:
                templates_with_fields.append(template_result.value)
            else:
                templates_with_fields.append(template)

        return schema_manager.entity_list_to_dto_list(templates_with_fields)

    handlers["list_templates"] = list_templates

    # Update template
    @router.patch(
        "/{template_id}",
        response_model=ReportTemplateViewDto,
        summary="Update a report template",
    )
    async def update_template(
        template_id: str = Path(..., description="The ID of the template"),
        data: ReportTemplateUpdateDto = Body(...),
    ) -> ReportTemplateViewDto:
        """Update a report template."""
        # Get existing entity
        get_result = await template_service.get(template_id)
        if get_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Template with ID {template_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)

{{ ... }}
    ) -> None:
        """Delete a report template."""
        delete_result = await template_service.delete(template_id)
        if delete_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Template with ID {template_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

    handlers["delete_template"] = delete_template

    # Execute template
{{ ... }}
    ) -> ReportTriggerViewDto:
        """Get a report trigger by ID."""
        result = await trigger_service.get(trigger_id)
        if result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Trigger with ID {trigger_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        return schema_manager.entity_to_dto(result.value)

    handlers["get_trigger"] = get_trigger
{{ ... }}
        """Update a report trigger."""
        # Get existing entity
        get_result = await trigger_service.get(trigger_id)
        if get_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Trigger with ID {trigger_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)

{{ ... }}
    ) -> None:
        """Delete a report trigger."""
        delete_result = await trigger_service.delete(trigger_id)
        if delete_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Trigger with ID {trigger_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

    handlers["delete_trigger"] = delete_trigger

    # Process due triggers
{{ ... }}
    ) -> ReportOutputViewDto:
        """Get a report output by ID."""
        result = await output_service.get(output_id)
        if result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Output with ID {output_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        return schema_manager.entity_to_dto(result.value)

    handlers["get_output"] = get_output
{{ ... }}
        """Update a report output."""
        # Get existing entity
        get_result = await output_service.get(output_id)
        if get_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Output with ID {output_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)

{{ ... }}
    ) -> None:
        """Delete a report output."""
        delete_result = await output_service.delete(output_id)
        if delete_result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Output with ID {output_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

    handlers["delete_output"] = delete_output

    # Register router
{{ ... }}
        if result.is_failure:
            # Try getting without output executions
            simple_result = await execution_service.get(execution_id)
            if simple_result.is_failure:
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Execution with ID {execution_id} not found",
                            "details": {
                                "error": str(e)
                            }
                        }
                    }
                )

            return schema_manager.entity_to_dto(simple_result.value)

        return schema_manager.entity_to_dto(result.value)

{{ ... }}
    ) -> ReportOutputExecutionViewDto:
        """Get a report output execution by ID."""
        result = await output_execution_service.get(output_execution_id)
        if result.is_failure:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Output execution with ID {output_execution_id} not found",
                        "details": {
                            "error": str(e)
                        }
                    }
                }
            )

        return schema_manager.entity_to_dto(result.value)

    handlers["get_output_execution"] = get_output_execution
{{ ... }}
    # List output executions with filtering
    @router.get(
        "",
        response_model=list[ReportOutputExecutionViewDto],
        summary="List report output executions",
    )
    async def list_output_executions(
        report_execution_id: str | None = Query(
            None, description="Filter by execution ID"
        ),
        report_output_id: str | None = Query(None, description="Filter by output ID"),
        status: str | None = Query(None, description="Filter by status"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> list[ReportOutputExecutionViewDto]:
        """List report output executions with filtering."""
        filters = {}

        if report_execution_id:
            filters["report_execution_id"] = {
                "lookup": "eq",
                "val": report_execution_id,
            }
        if report_output_id:
            filters["report_output_id"] = {"lookup": "eq", "val": report_output_id}
        if status:
            filters["status"] = {"lookup": "eq", "val": status}

        result = await output_execution_service.list(
            filters=filters, skip=skip, limit=limit
        )
        if result.is_failure:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

        return schema_manager.entity_list_to_dto_list(result.value)

    handlers["list_output_executions"] = list_output_executions

    # Update output execution status
    @router.patch(
        "/{output_execution_id}/status",
        response_model=ReportOutputExecutionViewDto,
        summary="Update a report output execution status",
    )
    async def update_output_execution_status(
        output_execution_id: str = Path(
            ..., description="The ID of the output execution"
        ),
        data: ReportOutputExecutionUpdateStatusDto = Body(...),
    ) -> ReportOutputExecutionViewDto:
        """Update a report output execution status."""
        result = await output_execution_service.update_output_execution_status(
            output_execution_id=output_execution_id,
            status=data.status,
            error_details=data.error_details,
        )

        if result.is_failure:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": result.error.code,
                        "message": result.error.message,
                        "details": result.error.details
                    }
                }
            )

        return schema_manager.entity_to_dto(result.value)

    handlers["update_output_execution_status"] = update_output_execution_status

    # Register router
    app_or_router.include_router(router)

    return handlers


def register_reports_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
) -> dict[str, dict[str, Any]]:
    """Register all Reports module API endpoints.

    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.

    Returns:
        A dictionary of all endpoint handlers.
    """
    handlers = {}

    # Register field definition endpoints
    handlers["field_definitions"] = register_report_field_definition_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )

    # Register template endpoints
    handlers["templates"] = register_report_template_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )

    # Register trigger endpoints
    handlers["triggers"] = register_report_trigger_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )

    # Register output endpoints
    handlers["outputs"] = register_report_output_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )

    # Register execution endpoints
    handlers["executions"] = register_report_execution_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )

    # Register output execution endpoints
    handlers["output_executions"] = register_report_output_execution_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )

    return handlers
