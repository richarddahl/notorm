"""
Schema definitions for the workflows module.

This module provides schema definitions for the workflow entities
to support API endpoints and data validation.
"""

from typing import Dict, List, Optional, Any, TypeVar, Generic, Union
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, model_validator, ConfigDict

from uno.schema.schema import UnoSchema, PaginatedList
from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowConditionType,
)
from uno.workflows.entities import WorkflowDef


# Common fields for all schemas
class WorkflowBaseSchema(UnoSchema):
    """Base schema for workflow entities with common fields."""

    id: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    deleted_at: Optional[str] = None
    created_by_id: Optional[str] = None
    modified_by_id: Optional[str] = None
    deleted_by_id: Optional[str] = None
    tenant_id: Optional[str] = None
    group_id: Optional[str] = None


class WorkflowOperationType(str, Enum):
    """Workflow operation type enumeration."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class WorkflowTriggerSchema(BaseModel):
    """Workflow trigger schema."""

    entity_type: str = Field(..., description="The entity type this trigger applies to")
    operations: List[str] = Field(
        ..., description="The operations that will trigger the workflow"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowConditionSchema(BaseModel):
    """Workflow condition schema."""

    id: Optional[str] = Field(None, description="The condition ID")
    type: str = Field(..., description="The type of condition")
    field: Optional[str] = Field(
        None, description="The field to evaluate for field conditions"
    )
    operator: Optional[str] = Field(
        None, description="The operator for field conditions"
    )
    value: Optional[str] = Field(None, description="The value for field conditions")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Additional configuration for the condition"
    )
    order: Optional[int] = Field(
        0, description="The order of evaluation for the condition"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowRecipientSchema(BaseModel):
    """Workflow recipient schema."""

    id: Optional[str] = Field(None, description="The recipient ID")
    type: str = Field(..., description="The type of recipient")
    value: str = Field(
        ..., description="The value for the recipient (user ID, role name, etc.)"
    )
    action_id: Optional[str] = Field(
        None, description="The action this recipient is associated with"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowActionSchema(BaseModel):
    """Workflow action schema."""

    id: Optional[str] = Field(None, description="The action ID")
    type: str = Field(..., description="The type of action")
    title: Optional[str] = Field(None, description="The title for notification actions")
    body: Optional[str] = Field(
        None, description="The body for notification and email actions"
    )
    subject: Optional[str] = Field(None, description="The subject for email actions")
    url: Optional[str] = Field(None, description="The URL for webhook actions")
    method: Optional[str] = Field(
        "POST", description="The HTTP method for webhook actions"
    )
    priority: Optional[str] = Field(
        "normal", description="The priority for notification actions"
    )
    template: Optional[str] = Field(None, description="The template for email actions")
    operation: Optional[str] = Field(
        None, description="The operation for database actions"
    )
    target_entity: Optional[str] = Field(
        None, description="The target entity for database actions"
    )
    field_mapping: Optional[Dict[str, Any]] = Field(
        None, description="Field mapping for database actions"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Additional configuration for the action"
    )
    order: Optional[int] = Field(0, description="The order of execution for the action")
    recipients: Optional[List[WorkflowRecipientSchema]] = Field(
        [], description="Recipients for the action"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowDefinitionSchema(BaseModel):
    """Workflow definition schema."""

    id: Optional[str] = Field(None, description="The workflow ID")
    name: str = Field(..., description="The name of the workflow")
    description: Optional[str] = Field(
        None, description="The description of the workflow"
    )
    status: str = Field("active", description="The status of the workflow")
    version: int = Field(1, description="The version of the workflow")
    trigger: WorkflowTriggerSchema = Field(
        ..., description="The trigger for the workflow"
    )
    conditions: Optional[List[WorkflowConditionSchema]] = Field(
        [], description="Conditions for the workflow"
    )
    actions: List[WorkflowActionSchema] = Field(
        ..., description="Actions for the workflow"
    )
    created_at: Optional[datetime] = Field(
        None, description="When the workflow was created"
    )
    updated_at: Optional[datetime] = Field(
        None, description="When the workflow was last updated"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionStatus(str, Enum):
    """Workflow execution status enumeration."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class WorkflowActionResultSchema(BaseModel):
    """Workflow action execution result schema."""

    id: Optional[str] = Field(None, description="The action result ID")
    action_id: str = Field(..., description="The ID of the action that was executed")
    type: str = Field(..., description="The type of action that was executed")
    status: str = Field(..., description="The status of the action execution")
    started_at: Optional[datetime] = Field(None, description="When the action started")
    completed_at: Optional[datetime] = Field(
        None, description="When the action completed"
    )
    duration_ms: Optional[int] = Field(
        None, description="The duration of the action execution in milliseconds"
    )
    recipients_count: Optional[int] = Field(
        None, description="The number of recipients for the action"
    )
    error: Optional[str] = Field(
        None, description="The error message if the action failed"
    )
    details: Optional[str] = Field(
        None, description="Additional details about the action execution"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionLogSchema(BaseModel):
    """Workflow execution log schema."""

    id: str = Field(..., description="The execution log ID")
    workflow_id: str = Field(
        ..., description="The ID of the workflow that was executed"
    )
    workflow_name: str = Field(
        ..., description="The name of the workflow that was executed"
    )
    status: str = Field(..., description="The status of the execution")
    entity_type: str = Field(
        ..., description="The entity type that triggered the workflow"
    )
    entity_id: str = Field(
        ..., description="The ID of the entity that triggered the workflow"
    )
    operation: str = Field(..., description="The operation that triggered the workflow")
    started_at: datetime = Field(..., description="When the execution started")
    completed_at: datetime = Field(..., description="When the execution completed")
    duration_ms: int = Field(
        ..., description="The duration of the execution in milliseconds"
    )
    conditions_result: bool = Field(..., description="Whether all conditions passed")
    actions_total: int = Field(..., description="The total number of actions")
    actions_success: int = Field(..., description="The number of successful actions")
    actions_failed: int = Field(..., description="The number of failed actions")
    action_results: List[WorkflowActionResultSchema] = Field(
        ..., description="The results of the action executions"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionSchema(BaseModel):
    """Workflow execution schema."""

    workflow_id: str = Field(..., description="The ID of the workflow to execute")
    entity_type: str = Field(
        ..., description="The entity type that triggered the workflow"
    )
    entity_id: str = Field(
        ..., description="The ID of the entity that triggered the workflow"
    )
    operation: str = Field(..., description="The operation that triggered the workflow")
    data: Dict[str, Any] = Field(..., description="The entity data for the execution")

    model_config = ConfigDict(from_attributes=True)


class WorkflowSimulationRequestSchema(BaseModel):
    """Workflow simulation request schema."""

    operation: str = Field(..., description="The operation to simulate")
    entity_data: Dict[str, Any] = Field(
        ..., description="The entity data for the simulation"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowConditionResultSchema(BaseModel):
    """Workflow condition evaluation result schema."""

    type: str = Field(..., description="The type of condition")
    field: Optional[str] = Field(None, description="The field that was evaluated")
    operator: Optional[str] = Field(None, description="The operator that was used")
    value: Optional[str] = Field(
        None, description="The value that was compared against"
    )
    result: bool = Field(..., description="Whether the condition passed")
    description: Optional[str] = Field(
        None, description="A human-readable description of the condition evaluation"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowSimulationActionResultSchema(BaseModel):
    """Workflow simulation action result schema."""

    type: str = Field(..., description="The type of action")
    status: str = Field(..., description="The status of the action execution")
    config: Dict[str, Any] = Field(..., description="The configuration for the action")
    recipients: Optional[List[Dict[str, Any]]] = Field(
        None, description="The recipients for the action"
    )
    result: Dict[str, Any] = Field(
        ..., description="The result of the action execution"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkflowSimulationResultSchema(BaseModel):
    """Workflow simulation result schema."""

    workflow_id: str = Field(
        ..., description="The ID of the workflow that was simulated"
    )
    workflow_name: str = Field(
        ..., description="The name of the workflow that was simulated"
    )
    status: str = Field(..., description="The status of the simulation")
    trigger: Dict[str, Any] = Field(..., description="The trigger for the simulation")
    conditions: List[WorkflowConditionResultSchema] = Field(
        ..., description="The condition evaluation results"
    )
    conditions_result: bool = Field(..., description="Whether all conditions passed")
    actions: List[WorkflowSimulationActionResultSchema] = Field(
        ..., description="The action simulation results"
    )
    simulation_time: datetime = Field(..., description="When the simulation was run")

    model_config = ConfigDict(from_attributes=True)


# Workflow Step Schemas
class WorkflowStepCreate(WorkflowBaseSchema):
    """Schema for creating workflow steps."""

    name: str
    description: Optional[str] = None
    step_type: str
    workflow_id: str
    is_start: bool = False
    is_end: bool = False
    config: Dict[str, Any] = {}


class WorkflowStepEdit(WorkflowBaseSchema):
    """Schema for updating workflow steps."""

    name: Optional[str] = None
    description: Optional[str] = None
    step_type: Optional[str] = None
    is_start: Optional[bool] = None
    is_end: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class WorkflowStepDetail(WorkflowBaseSchema):
    """Schema for workflow step details."""

    name: str
    description: Optional[str] = None
    step_type: str
    workflow_id: str
    is_start: bool = False
    is_end: bool = False
    config: Dict[str, Any] = {}


class WorkflowStepList(WorkflowBaseSchema):
    """Schema for listing workflow steps."""

    name: str
    description: Optional[str] = None
    step_type: str
    workflow_id: str
    is_start: bool = False
    is_end: bool = False


# Workflow Transition Schemas
class WorkflowTransitionCreate(WorkflowBaseSchema):
    """Schema for creating workflow transitions."""

    name: str
    description: Optional[str] = None
    workflow_id: str
    from_step_id: str
    to_step_id: str
    condition: Optional[str] = None


class WorkflowTransitionEdit(WorkflowBaseSchema):
    """Schema for updating workflow transitions."""

    name: Optional[str] = None
    description: Optional[str] = None
    from_step_id: Optional[str] = None
    to_step_id: Optional[str] = None
    condition: Optional[str] = None


class WorkflowTransitionDetail(WorkflowBaseSchema):
    """Schema for workflow transition details."""

    name: str
    description: Optional[str] = None
    workflow_id: str
    from_step_id: str
    to_step_id: str
    condition: Optional[str] = None


class WorkflowTransitionList(WorkflowBaseSchema):
    """Schema for listing workflow transitions."""

    name: str
    description: Optional[str] = None
    workflow_id: str
    from_step_id: str
    to_step_id: str


# Workflow Task Schemas
class WorkflowTaskCreate(WorkflowBaseSchema):
    """Schema for creating workflow tasks."""

    title: str
    description: Optional[str] = None
    instance_id: str
    step_id: str
    assignee_id: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, in_progress, completed, cancelled
    due_date: Optional[str] = None
    data: Dict[str, Any] = {}


class WorkflowTaskEdit(WorkflowBaseSchema):
    """Schema for updating workflow tasks."""

    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowTaskDetail(WorkflowBaseSchema):
    """Schema for workflow task details."""

    title: str
    description: Optional[str] = None
    instance_id: str
    step_id: str
    assignee_id: Optional[str] = None
    priority: str
    status: str
    due_date: Optional[str] = None
    data: Dict[str, Any] = {}


class WorkflowTaskList(WorkflowBaseSchema):
    """Schema for listing workflow tasks."""

    title: str
    description: Optional[str] = None
    instance_id: str
    step_id: str
    priority: str
    status: str
    due_date: Optional[str] = None


# Workflow Instance Schemas
class WorkflowInstanceCreate(WorkflowBaseSchema):
    """Schema for creating workflow instances."""

    workflow_id: str
    record_type_id: str
    record_id: str
    current_step_id: Optional[str] = None
    status: str = "active"  # active, completed, cancelled
    data: Dict[str, Any] = {}


class WorkflowInstanceEdit(WorkflowBaseSchema):
    """Schema for updating workflow instances."""

    current_step_id: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowInstanceDetail(WorkflowBaseSchema):
    """Schema for workflow instance details."""

    workflow_id: str
    record_type_id: str
    record_id: str
    current_step_id: Optional[str] = None
    status: str
    data: Dict[str, Any] = {}


class WorkflowInstanceList(WorkflowBaseSchema):
    """Schema for listing workflow instances."""

    workflow_id: str
    record_type_id: str
    record_id: str
    current_step_id: Optional[str] = None
    status: str


# Workflow Schemas
class WorkflowCreate(WorkflowBaseSchema):
    """Schema for creating workflows."""

    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    status: WorkflowStatus = WorkflowStatus.DRAFT


class WorkflowEdit(WorkflowBaseSchema):
    """Schema for updating workflows."""

    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[WorkflowStatus] = None


class WorkflowDetail(WorkflowBaseSchema):
    """Schema for workflow details."""

    name: str
    description: Optional[str] = None
    version: str
    status: WorkflowStatus
    # Include relationships in detail view
    steps: List[WorkflowStepDetail] = []
    transitions: List[WorkflowTransitionDetail] = []


class WorkflowList(WorkflowBaseSchema):
    """Schema for listing workflows."""

    name: str
    description: Optional[str] = None
    version: str
    status: WorkflowStatus


# Register all schemas with UnoSchemaManager for each model
def register_workflow_schemas():
    """Register all workflow schemas with their respective model schema managers."""
    from uno.schema.schema_manager import UnoSchemaManager

    # The legacy workflow classes have been removed for simplicity.
    # Only the WorkflowDef class is supported for schema registration.

    # In the future, if you implement new workflow-related models and objects,
    # you can register their schemas here.

    # For now, we'll just log a message that this function was called
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        "Workflow schemas registration function called - legacy schemas have been removed."
    )
