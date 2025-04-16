"""
Workflow API endpoints for the UI interface.

This module provides FastAPI endpoints for the workflow management UI,
including workflow creation, updating, deletion, execution monitoring,
and simulation capabilities.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from pydantic import BaseModel, Field

from uno.core.errors.result import Result, Success, Failure
from uno.workflows.app_integration import workflow_dependency
from uno.workflows.provider import WorkflowService
from uno.workflows.entities import WorkflowDef
from uno.workflows.schemas import (
    WorkflowDefinitionSchema,
    WorkflowTriggerSchema,
    WorkflowConditionSchema,
    WorkflowActionSchema,
    WorkflowRecipientSchema,
    WorkflowExecutionSchema,
    WorkflowExecutionLogSchema,
    WorkflowSimulationRequestSchema,
    WorkflowSimulationResultSchema,
)

# Create a router for workflow endpoints
router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("/", response_model=List[WorkflowDefinitionSchema])
async def get_workflows(
    status: Optional[str] = Query(None, description="Filter by workflow status"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Get all workflows, optionally filtered by status.

    Args:
        status: Optional status filter (active, inactive, etc.)
        workflow_service: Injected workflow service

    Returns:
        List of workflow definitions
    """
    if status:
        # Get workflows with the specified status
        result = await workflow_service.get_workflows_by_status(status)
    else:
        # Get all workflows
        result = await workflow_service.get_active_workflows()

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error)
        )

    return [WorkflowDefinitionSchema.from_orm(wf) for wf in result.value]


@router.get("/{workflow_id}", response_model=WorkflowDefinitionSchema)
async def get_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow to retrieve"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Get a single workflow by ID.

    Args:
        workflow_id: The ID of the workflow to retrieve
        workflow_service: Injected workflow service

    Returns:
        The workflow definition
    """
    result = await workflow_service.get_workflow_by_id(workflow_id)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found",
        )

    return WorkflowDefinitionSchema.from_orm(result.value)


@router.post("/", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowDefinitionSchema,
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Create a new workflow.

    Args:
        workflow: The workflow definition to create
        workflow_service: Injected workflow service

    Returns:
        The ID of the created workflow
    """
    # Convert schema to domain model
    workflow_def = WorkflowDef.from_dict(workflow.dict())

    result = await workflow_service.create_workflow(workflow_def)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error)
        )

    return {"id": result.value}


@router.put("/{workflow_id}", response_model=Dict[str, str])
async def update_workflow(
    workflow: WorkflowDefinitionSchema,
    workflow_id: str = Path(..., description="The ID of the workflow to update"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Update an existing workflow.

    Args:
        workflow: The updated workflow definition
        workflow_id: The ID of the workflow to update
        workflow_service: Injected workflow service

    Returns:
        The ID of the updated workflow
    """
    # Ensure the path ID matches the body ID
    if workflow_id != workflow.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path ID must match the workflow ID in the request body",
        )

    # Convert schema to domain model
    workflow_def = WorkflowDef.from_dict(workflow.dict())

    result = await workflow_service.update_workflow(workflow_def)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(result.error)
        )

    return {"id": result.value}


@router.delete("/{workflow_id}", response_model=Dict[str, bool])
async def delete_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow to delete"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Delete a workflow.

    Args:
        workflow_id: The ID of the workflow to delete
        workflow_service: Injected workflow service

    Returns:
        Success indicator
    """
    result = await workflow_service.delete_workflow(workflow_id)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(result.error)
        )

    return {"success": result.value}


@router.patch("/{workflow_id}/status", response_model=Dict[str, str])
async def update_workflow_status(
    status_update: Dict[str, str] = Body(..., description="Status update"),
    workflow_id: str = Path(..., description="The ID of the workflow to update"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Update the status of a workflow (enable/disable).

    Args:
        status_update: The new status (status: active/inactive)
        workflow_id: The ID of the workflow to update
        workflow_service: Injected workflow service

    Returns:
        The ID of the updated workflow
    """
    if "status" not in status_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Status field is required"
        )

    result = await workflow_service.update_workflow_status(
        workflow_id, status_update["status"]
    )

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(result.error)
        )

    return {"id": result.value}


@router.get("/executions", response_model=List[WorkflowExecutionLogSchema])
async def get_workflow_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    execution_status: Optional[str] = Query(
        None, description="Filter by execution status"
    ),
    limit: int = Query(100, description="Maximum number of executions to return"),
    offset: int = Query(0, description="Number of executions to skip"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Get workflow execution logs.

    Args:
        workflow_id: Optional workflow ID filter
        execution_status: Optional execution status filter
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        workflow_service: Injected workflow service

    Returns:
        List of workflow execution logs
    """
    result = await workflow_service.get_execution_logs(
        workflow_id=workflow_id, status=execution_status, limit=limit, offset=offset
    )

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error)
        )

    return [WorkflowExecutionLogSchema.from_orm(log) for log in result.value]


@router.get(
    "/{workflow_id}/executions/{execution_id}",
    response_model=WorkflowExecutionLogSchema,
)
async def get_workflow_execution(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    execution_id: str = Path(..., description="The ID of the execution to retrieve"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Get a specific workflow execution log.

    Args:
        workflow_id: The ID of the workflow
        execution_id: The ID of the execution to retrieve
        workflow_service: Injected workflow service

    Returns:
        The workflow execution log
    """
    result = await workflow_service.get_execution_log(execution_id)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution log with ID {execution_id} not found",
        )

    # Verify that this execution is for the specified workflow
    if result.value.workflow_id != workflow_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution log with ID {execution_id} not found for workflow {workflow_id}",
        )

    return WorkflowExecutionLogSchema.from_orm(result.value)


@router.post(
    "/{workflow_id}/executions/{execution_id}/actions/{action_id}/retry",
    response_model=Dict[str, bool],
)
async def retry_workflow_action(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    execution_id: str = Path(..., description="The ID of the execution"),
    action_id: str = Path(..., description="The ID of the action to retry"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Retry a failed workflow action.

    Args:
        workflow_id: The ID of the workflow
        execution_id: The ID of the execution
        action_id: The ID of the action to retry
        workflow_service: Injected workflow service

    Returns:
        Success indicator
    """
    result = await workflow_service.retry_workflow_action(execution_id, action_id)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(result.error)
        )

    return {"success": result.value}


@router.post("/{workflow_id}/simulate", response_model=WorkflowSimulationResultSchema)
async def simulate_workflow(
    simulation_request: WorkflowSimulationRequestSchema,
    workflow_id: str = Path(..., description="The ID of the workflow to simulate"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Simulate a workflow execution with test data.

    Args:
        simulation_request: The simulation request containing test data
        workflow_id: The ID of the workflow to simulate
        workflow_service: Injected workflow service

    Returns:
        The simulation results
    """
    result = await workflow_service.simulate_workflow(
        workflow_id, simulation_request.operation, simulation_request.entity_data
    )

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(result.error)
        )

    return result.value


# Additional API endpoints for schema information needed by the UI


@router.get("/entity-types", response_model=List[Dict[str, str]])
async def get_entity_types(workflow_service: WorkflowService = workflow_dependency):
    """
    Get a list of available entity types.

    Args:
        workflow_service: Injected workflow service

    Returns:
        List of entity types with labels
    """
    result = await workflow_service.get_entity_types()

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error)
        )

    return result.value


@router.get("/entity-types/{entity_type}/fields", response_model=List[Dict[str, Any]])
async def get_entity_fields(
    entity_type: str = Path(..., description="The entity type to get fields for"),
    workflow_service: WorkflowService = workflow_dependency,
):
    """
    Get a list of fields for an entity type.

    Args:
        entity_type: The entity type to get fields for
        workflow_service: Injected workflow service

    Returns:
        List of fields with their types and metadata
    """
    result = await workflow_service.get_entity_fields(entity_type)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity type {entity_type} not found",
        )

    return result.value


@router.get("/action-types", response_model=List[Dict[str, Any]])
async def get_action_types(workflow_service: WorkflowService = workflow_dependency):
    """
    Get a list of available action types.

    Args:
        workflow_service: Injected workflow service

    Returns:
        List of action types with metadata
    """
    result = await workflow_service.get_action_types()

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error)
        )

    return result.value


@router.get("/condition-types", response_model=List[Dict[str, Any]])
async def get_condition_types(workflow_service: WorkflowService = workflow_dependency):
    """
    Get a list of available condition types.

    Args:
        workflow_service: Injected workflow service

    Returns:
        List of condition types with metadata
    """
    result = await workflow_service.get_condition_types()

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error)
        )

    return result.value


@router.get("/recipient-types", response_model=List[Dict[str, Any]])
async def get_recipient_types(workflow_service: WorkflowService = workflow_dependency):
    """
    Get a list of available recipient types.

    Args:
        workflow_service: Injected workflow service

    Returns:
        List of recipient types with metadata
    """
    result = await workflow_service.get_recipient_types()

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.error)
        )

    return result.value
