"""API integration for the Workflows module."""

from typing import Any, Dict, List, Optional, Union, Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, FastAPI
from pydantic import BaseModel

from uno.workflows.entities import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
)
from uno.workflows.schemas import (
    WorkflowDefSchemaManager,
    WorkflowTriggerSchemaManager,
    WorkflowConditionSchemaManager,
    WorkflowActionSchemaManager,
    WorkflowRecipientSchemaManager,
    WorkflowExecutionRecordSchemaManager,
)
from uno.workflows.dtos import (
    # Workflow Definition DTOs
    WorkflowDefCreateDto,
    WorkflowDefUpdateDto,
    WorkflowDefViewDto,
    WorkflowDefFilterParams,
    # Workflow Trigger DTOs
    WorkflowTriggerCreateDto,
    WorkflowTriggerUpdateDto,
    WorkflowTriggerViewDto,
    WorkflowTriggerFilterParams,
    # Workflow Condition DTOs
    WorkflowConditionCreateDto,
    WorkflowConditionUpdateDto,
    WorkflowConditionViewDto,
    WorkflowConditionFilterParams,
    # Workflow Action DTOs
    WorkflowActionCreateDto,
    WorkflowActionUpdateDto,
    WorkflowActionViewDto,
    WorkflowActionFilterParams,
    # Workflow Recipient DTOs
    WorkflowRecipientCreateDto,
    WorkflowRecipientUpdateDto,
    WorkflowRecipientViewDto,
    WorkflowRecipientFilterParams,
    # Workflow Execution Record DTOs
    WorkflowExecutionRecordViewDto,
    WorkflowExecutionRecordFilterParams,
    WorkflowEventDto,
)
from uno.workflows.provider import WorkflowService


def register_workflow_definition_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    workflow_service: Optional[WorkflowService] = None,
) -> dict[str, Any]:
    """Register API endpoints for workflow definitions.

    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        workflow_service: Optional workflow service to use.

    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/workflows",
        tags=["Workflows"],
        dependencies=dependencies or [],
    )

    handlers = {}

    # Get service from DI container if not provided
    if workflow_service is None:
        from uno.dependencies import get_service

        workflow_service = get_service(WorkflowService)

    schema_manager = WorkflowDefSchemaManager()

    # Create workflow
    @router.post(
        "",
        response_model=WorkflowDefViewDto,
        status_code=201,
        summary="Create a new workflow definition",
    )
    async def create_workflow(
        data: WorkflowDefCreateDto = Body(...),
    ) -> WorkflowDefViewDto:
        """Create a new workflow definition."""
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data)

        # Create entity
        result = await workflow_service.create_workflow(entity)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))

        # Get with relationships
        get_result = await workflow_service.get_workflow_by_id(result.value)
        if get_result.is_failure:
            # Fall back to basic info
            return schema_manager.entity_to_dto(entity)

        return schema_manager.entity_to_dto(get_result.value)

    handlers["create_workflow"] = create_workflow

    # Get workflow by ID
    @router.get(
        "/{workflow_id}",
        response_model=WorkflowDefViewDto,
        summary="Get a workflow definition by ID",
    )
    async def get_workflow(
        workflow_id: str = Path(..., description="The ID of the workflow"),
    ) -> WorkflowDefViewDto:
        """Get a workflow definition by ID."""
        result = await workflow_service.get_workflow_by_id(workflow_id)
        if result.is_failure:
            raise HTTPException(
                status_code=404, detail=f"Workflow with ID {workflow_id} not found"
            )

        return schema_manager.entity_to_dto(result.value)

    handlers["get_workflow"] = get_workflow

    # List workflows with filtering
    @router.get(
        "",
        response_model=list[WorkflowDefViewDto],
        summary="List workflows",
    )
    async def list_workflows(
        name: str | None = Query(None, description="Filter by name"),
        status: str | None = Query(None, description="Filter by status"),
        entity_type: str | None = Query(
            None, description="Filter by entity type (triggers)"
        ),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> list[WorkflowDefViewDto]:
        """List workflows with filtering."""
        # Get active workflows first and then filter in memory
        # This is a simplified approach - in a real implementation, you'd use more
        # sophisticated querying
        result = await workflow_service.get_active_workflows()
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))

        workflows = result.value
        filtered_workflows = []

        for workflow in workflows:
            # Apply filters
            if name and name.lower() not in workflow.name.lower():
                continue

            if status and workflow.status != status:
                continue

            if entity_type:
                # Check if any trigger matches the entity_type
                if not any(t.entity_type == entity_type for t in workflow.triggers):
                    continue

            filtered_workflows.append(workflow)

        # Apply pagination
        paginated_workflows = filtered_workflows[skip : skip + limit]

        return schema_manager.entity_list_to_dto_list(paginated_workflows)

    handlers["list_workflows"] = list_workflows

    # Update workflow
    @router.patch(
        "/{workflow_id}",
        response_model=WorkflowDefViewDto,
        summary="Update a workflow definition",
    )
    async def update_workflow(
        workflow_id: str = Path(..., description="The ID of the workflow"),
        data: WorkflowDefUpdateDto = Body(...),
    ) -> WorkflowDefViewDto:
        """Update a workflow definition."""
        # Get existing entity
        get_result = await workflow_service.get_workflow_by_id(workflow_id)
        if get_result.is_failure:
            raise HTTPException(
                status_code=404, detail=f"Workflow with ID {workflow_id} not found"
            )

        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)

        # Update entity
        update_result = await workflow_service.update_workflow(entity)
        if update_result.is_failure:
            raise HTTPException(status_code=400, detail=str(update_result.error))

        # Get updated entity with relationships
        updated_result = await workflow_service.get_workflow_by_id(workflow_id)
        if updated_result.is_failure:
            # Fall back to basic info
            return schema_manager.entity_to_dto(entity)

        return schema_manager.entity_to_dto(updated_result.value)

    handlers["update_workflow"] = update_workflow

    # Delete workflow
    @router.delete(
        "/{workflow_id}",
        status_code=204,
        summary="Delete a workflow definition",
    )
    async def delete_workflow(
        workflow_id: str = Path(..., description="The ID of the workflow"),
    ) -> None:
        """Delete a workflow definition."""
        result = await workflow_service.delete_workflow(workflow_id)
        if result.is_failure:
            raise HTTPException(
                status_code=404, detail=f"Workflow with ID {workflow_id} not found"
            )

    handlers["delete_workflow"] = delete_workflow

    # Process workflow event
    @router.post(
        "/events",
        response_model=dict[str, Any],
        summary="Process a workflow event",
    )
    async def process_event(
        event: WorkflowEventDto = Body(...),
    ) -> dict[str, Any]:
        """Process a workflow event."""
        result = await workflow_service.process_event(event.dict())
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))

        return result.value

    handlers["process_event"] = process_event

    # Get workflow execution logs
    @router.get(
        "/{workflow_id}/executions",
        response_model=list[WorkflowExecutionRecordViewDto],
        summary="Get execution logs for a workflow",
    )
    async def get_workflow_executions(
        workflow_id: str = Path(..., description="The ID of the workflow"),
        status: str | None = Query(None, description="Filter by status"),
        limit: int = Query(100, description="Maximum number of records to return"),
        offset: int = Query(0, description="Number of records to skip"),
    ) -> list[WorkflowExecutionRecordViewDto]:
        """Get execution logs for a workflow."""
        result = await workflow_service.get_execution_logs(
            workflow_id=workflow_id, status=status, limit=limit, offset=offset
        )
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))

        execution_schema_manager = WorkflowExecutionRecordSchemaManager()
        return execution_schema_manager.entity_list_to_dto_list(result.value)

    handlers["get_workflow_executions"] = get_workflow_executions

    # Register router
    app_or_router.include_router(router)

    return handlers


def register_workflow_component_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    workflow_service: Optional[WorkflowService] = None,
) -> dict[str, Any]:
    """Register API endpoints for workflow components (triggers, conditions, etc.).

    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        workflow_service: Optional workflow service to use.

    Returns:
        A dictionary of endpoint handlers.
    """
    # This function would register CRUD endpoints for individual workflow components
    # such as triggers, conditions, actions, and recipients.
    # For brevity, we're skipping the implementation, as these components are typically
    # managed through the parent workflow definition.

    # In a complete implementation, you would register endpoints for:
    # - /api/v1/workflow-triggers
    # - /api/v1/workflow-conditions
    # - /api/v1/workflow-actions
    # - /api/v1/workflow-recipients
    # - /api/v1/workflow-executions

    return {}


def register_workflow_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    workflow_service: Optional[WorkflowService] = None,
) -> dict[str, dict[str, Any]]:
    """Register all workflow module API endpoints.

    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        workflow_service: Optional workflow service to use.

    Returns:
        A dictionary of all endpoint handlers.
    """
    handlers = {}

    # Register workflow definition endpoints
    handlers["workflows"] = register_workflow_definition_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
        workflow_service=workflow_service,
    )

    # Register workflow component endpoints
    handlers["components"] = register_workflow_component_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
        workflow_service=workflow_service,
    )

    return handlers
