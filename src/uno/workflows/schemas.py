"""
Schema definitions for the workflows module.

This module provides schema definitions for the workflow entities
to support API endpoints and data validation.
"""

from typing import Dict, List, Optional, Any, TypeVar, Generic, Union
from enum import Enum

from pydantic import BaseModel, Field, model_validator, ConfigDict

from uno.schema.schema import UnoSchema, PaginatedList
from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowConditionType,
)


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
    from uno.workflows.objs import WorkflowDef
    from uno.schema.schema_manager import UnoSchemaManager
    
    # The legacy workflow classes have been removed for simplicity.
    # Only the WorkflowDef class is supported for schema registration.
    
    # In the future, if you implement new workflow-related models and objects,
    # you can register their schemas here.
    
    # For now, we'll just log a message that this function was called
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Workflow schemas registration function called - legacy schemas have been removed.")