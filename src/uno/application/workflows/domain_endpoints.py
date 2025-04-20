"""
API endpoints for the Workflows module using the Domain approach.

This module provides FastAPI endpoints for workflow entities using the domain-driven
design approach with domain services and entities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from enum import Enum

from uno.domain.api_integration import (
    create_domain_router,
    domain_endpoint,
)
from uno.dependencies.scoped_container import container
from uno.workflows.entities import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
)
from uno.workflows.domain_services import (
    WorkflowDefService,
    WorkflowTriggerService,
    WorkflowConditionService,
    WorkflowActionService,
    WorkflowRecipientService,
    WorkflowExecutionService,
)
from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowConditionType,
    WorkflowExecutionStatus,
)


# Create routers using the domain_router factory
workflow_def_router = create_domain_router(
    entity_type=WorkflowDef,
    service_type=WorkflowDefService,
    prefix="/api/workflows",
    tags=["Workflows", "Workflow Definitions"],
)

workflow_trigger_router = create_domain_router(
    entity_type=WorkflowTrigger,
    service_type=WorkflowTriggerService,
    prefix="/api/workflow-triggers",
    tags=["Workflows", "Workflow Triggers"],
)

workflow_condition_router = create_domain_router(
    entity_type=WorkflowCondition,
    service_type=WorkflowConditionService,
    prefix="/api/workflow-conditions",
    tags=["Workflows", "Workflow Conditions"],
)

workflow_action_router = create_domain_router(
    entity_type=WorkflowAction,
    service_type=WorkflowActionService,
    prefix="/api/workflow-actions",
    tags=["Workflows", "Workflow Actions"],
)

workflow_recipient_router = create_domain_router(
    entity_type=WorkflowRecipient,
    service_type=WorkflowRecipientService,
    prefix="/api/workflow-recipients",
    tags=["Workflows", "Workflow Recipients"],
)

workflow_execution_router = create_domain_router(
    entity_type=WorkflowExecutionRecord,
    service_type=WorkflowExecutionService,
    prefix="/api/workflow-executions",
    tags=["Workflows", "Workflow Executions"],
)


# Custom endpoints for WorkflowDef

@workflow_def_router.post("/create")
@domain_endpoint(entity_type=WorkflowDef, service_type=WorkflowDefService)
async def create_workflow(
    name: str = Body(..., description="The name of the workflow"),
    description: str = Body(..., description="The description of the workflow"),
    status: WorkflowStatus = Body(WorkflowStatus.DRAFT, description="The initial status of the workflow"),
    version: str = Body("1.0.0", description="The version of the workflow"),
    service: WorkflowDefService = Depends(container.resolve(WorkflowDefService))
):
    """Create a new workflow definition."""
    result = await service.create_workflow(name, description, status, version)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_def_router.get("/active")
@domain_endpoint(entity_type=WorkflowDef, service_type=WorkflowDefService)
async def get_active_workflows(
    service: WorkflowDefService = Depends(container.resolve(WorkflowDefService))
):
    """Get all active workflows."""
    result = await service.find_active_workflows()
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [workflow.to_dict() for workflow in result.value]


@workflow_def_router.get("/{id}/with-relationships")
@domain_endpoint(entity_type=WorkflowDef, service_type=WorkflowDefService)
async def get_workflow_with_relationships(
    id: str = Path(..., description="The ID of the workflow"),
    service: WorkflowDefService = Depends(container.resolve(WorkflowDefService))
):
    """Get a workflow with all its relationships loaded."""
    result = await service.get_workflow_with_relationships(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_def_router.post("/{id}/activate")
@domain_endpoint(entity_type=WorkflowDef, service_type=WorkflowDefService)
async def activate_workflow(
    id: str = Path(..., description="The ID of the workflow"),
    service: WorkflowDefService = Depends(container.resolve(WorkflowDefService))
):
    """Activate a workflow."""
    result = await service.activate_workflow(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_def_router.post("/{id}/deactivate")
@domain_endpoint(entity_type=WorkflowDef, service_type=WorkflowDefService)
async def deactivate_workflow(
    id: str = Path(..., description="The ID of the workflow"),
    service: WorkflowDefService = Depends(container.resolve(WorkflowDefService))
):
    """Deactivate a workflow."""
    result = await service.deactivate_workflow(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


# Custom endpoints for WorkflowTrigger

@workflow_trigger_router.post("/create")
@domain_endpoint(entity_type=WorkflowTrigger, service_type=WorkflowTriggerService)
async def create_trigger(
    workflow_id: str = Body(..., description="The ID of the workflow"),
    entity_type: str = Body(..., description="The type of entity that triggers the workflow"),
    operation: str = Body(..., description="The operation that triggers the workflow"),
    field_conditions: Dict[str, Any] = Body({}, description="Optional conditions on fields"),
    priority: int = Body(100, description="The priority of the trigger"),
    is_active: bool = Body(True, description="Whether the trigger is active"),
    service: WorkflowTriggerService = Depends(container.resolve(WorkflowTriggerService))
):
    """Create a new workflow trigger."""
    result = await service.create_trigger(
        workflow_id=workflow_id,
        entity_type=entity_type,
        operation=operation,
        field_conditions=field_conditions,
        priority=priority,
        is_active=is_active
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_trigger_router.get("/by-workflow/{workflow_id}")
@domain_endpoint(entity_type=WorkflowTrigger, service_type=WorkflowTriggerService)
async def get_triggers_by_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    service: WorkflowTriggerService = Depends(container.resolve(WorkflowTriggerService))
):
    """Get triggers for a specific workflow."""
    result = await service.find_by_workflow(workflow_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [trigger.to_dict() for trigger in result.value]


# Custom endpoints for WorkflowCondition

@workflow_condition_router.post("/create")
@domain_endpoint(entity_type=WorkflowCondition, service_type=WorkflowConditionService)
async def create_condition(
    workflow_id: str = Body(..., description="The ID of the workflow"),
    condition_type: WorkflowConditionType = Body(..., description="The type of condition"),
    condition_config: Dict[str, Any] = Body({}, description="The configuration for the condition"),
    query_id: Optional[str] = Body(None, description="Optional query ID for query match conditions"),
    name: str = Body("", description="Optional name for the condition"),
    description: Optional[str] = Body(None, description="Optional description"),
    order: int = Body(0, description="The order of the condition"),
    service: WorkflowConditionService = Depends(container.resolve(WorkflowConditionService))
):
    """Create a new workflow condition."""
    result = await service.create_condition(
        workflow_id=workflow_id,
        condition_type=condition_type,
        condition_config=condition_config,
        query_id=query_id,
        name=name,
        description=description,
        order=order
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_condition_router.get("/by-workflow/{workflow_id}")
@domain_endpoint(entity_type=WorkflowCondition, service_type=WorkflowConditionService)
async def get_conditions_by_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    service: WorkflowConditionService = Depends(container.resolve(WorkflowConditionService))
):
    """Get conditions for a specific workflow."""
    result = await service.find_by_workflow(workflow_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [condition.to_dict() for condition in result.value]


# Custom endpoints for WorkflowAction

@workflow_action_router.post("/create")
@domain_endpoint(entity_type=WorkflowAction, service_type=WorkflowActionService)
async def create_action(
    workflow_id: str = Body(..., description="The ID of the workflow"),
    action_type: WorkflowActionType = Body(..., description="The type of action"),
    action_config: Dict[str, Any] = Body({}, description="The configuration for the action"),
    name: str = Body("", description="Optional name for the action"),
    description: Optional[str] = Body(None, description="Optional description"),
    order: int = Body(0, description="The order of the action"),
    is_active: bool = Body(True, description="Whether the action is active"),
    retry_policy: Optional[Dict[str, Any]] = Body(None, description="Optional retry policy"),
    service: WorkflowActionService = Depends(container.resolve(WorkflowActionService))
):
    """Create a new workflow action."""
    result = await service.create_action(
        workflow_id=workflow_id,
        action_type=action_type,
        action_config=action_config,
        name=name,
        description=description,
        order=order,
        is_active=is_active,
        retry_policy=retry_policy
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_action_router.get("/by-workflow/{workflow_id}")
@domain_endpoint(entity_type=WorkflowAction, service_type=WorkflowActionService)
async def get_actions_by_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    service: WorkflowActionService = Depends(container.resolve(WorkflowActionService))
):
    """Get actions for a specific workflow."""
    result = await service.find_by_workflow(workflow_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [action.to_dict() for action in result.value]


@workflow_action_router.get("/{id}/with-recipients")
@domain_endpoint(entity_type=WorkflowAction, service_type=WorkflowActionService)
async def get_action_with_recipients(
    id: str = Path(..., description="The ID of the action"),
    service: WorkflowActionService = Depends(container.resolve(WorkflowActionService))
):
    """Get an action with its recipients loaded."""
    result = await service.get_with_recipients(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


# Custom endpoints for WorkflowRecipient

@workflow_recipient_router.post("/create")
@domain_endpoint(entity_type=WorkflowRecipient, service_type=WorkflowRecipientService)
async def create_recipient(
    workflow_id: str = Body(..., description="The ID of the workflow"),
    recipient_type: WorkflowRecipientType = Body(..., description="The type of recipient"),
    recipient_id: str = Body(..., description="The ID of the recipient"),
    name: Optional[str] = Body(None, description="Optional name for the recipient"),
    action_id: Optional[str] = Body(None, description="Optional action ID if this recipient is for a specific action"),
    notification_config: Dict[str, Any] = Body({}, description="Optional notification configuration"),
    service: WorkflowRecipientService = Depends(container.resolve(WorkflowRecipientService))
):
    """Create a new workflow recipient."""
    result = await service.create_recipient(
        workflow_id=workflow_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        name=name,
        action_id=action_id,
        notification_config=notification_config
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_recipient_router.get("/by-workflow/{workflow_id}")
@domain_endpoint(entity_type=WorkflowRecipient, service_type=WorkflowRecipientService)
async def get_recipients_by_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    service: WorkflowRecipientService = Depends(container.resolve(WorkflowRecipientService))
):
    """Get recipients for a specific workflow."""
    result = await service.find_by_workflow(workflow_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [recipient.to_dict() for recipient in result.value]


@workflow_recipient_router.get("/by-action/{action_id}")
@domain_endpoint(entity_type=WorkflowRecipient, service_type=WorkflowRecipientService)
async def get_recipients_by_action(
    action_id: str = Path(..., description="The ID of the action"),
    service: WorkflowRecipientService = Depends(container.resolve(WorkflowRecipientService))
):
    """Get recipients for a specific action."""
    result = await service.find_by_action(action_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [recipient.to_dict() for recipient in result.value]


# Custom endpoints for WorkflowExecution

@workflow_execution_router.post("/create")
@domain_endpoint(entity_type=WorkflowExecutionRecord, service_type=WorkflowExecutionService)
async def create_execution_record(
    workflow_id: str = Body(..., description="The ID of the workflow"),
    trigger_event_id: str = Body(..., description="The ID of the trigger event"),
    status: WorkflowExecutionStatus = Body(WorkflowExecutionStatus.PENDING, description="The initial status of the execution"),
    context: Optional[Dict[str, Any]] = Body(None, description="Optional execution context"),
    service: WorkflowExecutionService = Depends(container.resolve(WorkflowExecutionService))
):
    """Create a new workflow execution record."""
    result = await service.create_execution_record(
        workflow_id=workflow_id,
        trigger_event_id=trigger_event_id,
        status=status,
        context=context
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_execution_router.post("/{id}/update-status")
@domain_endpoint(entity_type=WorkflowExecutionRecord, service_type=WorkflowExecutionService)
async def update_execution_status(
    id: str = Path(..., description="The ID of the execution record"),
    status: WorkflowExecutionStatus = Body(..., description="The new status"),
    result: Optional[Dict[str, Any]] = Body(None, description="Optional result data"),
    error: Optional[str] = Body(None, description="Optional error message"),
    service: WorkflowExecutionService = Depends(container.resolve(WorkflowExecutionService))
):
    """Update the status of a workflow execution."""
    result = await service.update_execution_status(
        execution_id=id,
        status=status,
        result=result,
        error=error
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@workflow_execution_router.get("/by-workflow/{workflow_id}")
@domain_endpoint(entity_type=WorkflowExecutionRecord, service_type=WorkflowExecutionService)
async def get_executions_by_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    limit: int = Query(100, description="Maximum number of records to return"),
    service: WorkflowExecutionService = Depends(container.resolve(WorkflowExecutionService))
):
    """Get execution records for a specific workflow."""
    result = await service.find_by_workflow(workflow_id, limit)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [record.to_dict() for record in result.value]



    """