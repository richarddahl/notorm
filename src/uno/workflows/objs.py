# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List, Dict, Any, ClassVar
from typing_extensions import Self
from datetime import datetime
from pydantic import model_validator, Field

# Import shared base objects and schema configuration from internal modules
from uno.obj import UnoObj
from uno.schema.schema import UnoSchemaConfig
from uno.authorization.mixins import DefaultObjectMixin

# Import additional types from auth objs to mirror their patterns
from uno.authorization.objs import User
from uno.meta.objs import MetaType, MetaRecord
from uno.queries.objs import Query
from uno.workflows.models import (
    WorkflowDefinition,
    WorkflowTriggerModel,
    WorkflowConditionModel,
    WorkflowActionModel,
    WorkflowRecipientModel,
    WorkflowExecutionLog,
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowExecutionStatus,
    WorkflowConditionType,
    WorkflowDBEvent,
)


class WorkflowTrigger(UnoObj[WorkflowTriggerModel], DefaultObjectMixin):
    """Defines what triggers a workflow."""
    # Class variables
    model = WorkflowTriggerModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "workflow_id",
                "entity_type",
                "operation",
                "field_conditions",
                "priority",
                "is_active",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    workflow_id: str
    workflow: Optional["WorkflowDef"] = None
    entity_type: str
    operation: WorkflowDBEvent = WorkflowDBEvent.INSERT
    field_conditions: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 100
    is_active: bool = True

    def __str__(self) -> str:
        return f"{self.entity_type} {self.operation.value}"


class WorkflowCondition(UnoObj[WorkflowConditionModel], DefaultObjectMixin):
    """Additional conditions that must be met for workflow to execute."""
    # Class variables
    model = WorkflowConditionModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "workflow_id",
                "condition_type",
                "condition_config",
                "query_id",
                "name",
                "description",
                "order",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    workflow_id: str
    workflow: Optional["WorkflowDef"] = None
    condition_type: WorkflowConditionType = WorkflowConditionType.FIELD_VALUE
    condition_config: Dict[str, Any] = Field(default_factory=dict)
    query_id: Optional[str] = None
    query: Optional["Query"] = None  # Will be filled from relationship
    name: str = ""
    description: Optional[str] = None
    order: int = 0

    def __str__(self) -> str:
        if self.name:
            return self.name
        return f"{self.condition_type.value} condition"


class WorkflowAction(UnoObj[WorkflowActionModel], DefaultObjectMixin):
    """Action to take when workflow is triggered and conditions are met."""
    # Class variables
    model = WorkflowActionModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "workflow_id",
                "action_type",
                "action_config",
                "name",
                "description",
                "order",
                "is_active",
                "retry_policy",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    workflow_id: str
    workflow: Optional["WorkflowDef"] = None
    action_type: WorkflowActionType = WorkflowActionType.NOTIFICATION
    action_config: Dict[str, Any] = Field(default_factory=dict)
    name: str = ""
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True
    retry_policy: Optional[Dict[str, Any]] = None
    recipients: List["WorkflowRecipient"] = []

    def __str__(self) -> str:
        if self.name:
            return self.name
        return f"{self.action_type.value} action"


class WorkflowRecipient(UnoObj[WorkflowRecipientModel], DefaultObjectMixin):
    """Recipients for workflow notifications."""
    # Class variables
    model = WorkflowRecipientModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "workflow_id",
                "recipient_type",
                "recipient_id",
                "name",
                "action_id",
                "notification_config",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    workflow_id: str
    workflow: Optional["WorkflowDef"] = None
    recipient_type: WorkflowRecipientType = WorkflowRecipientType.USER
    recipient_id: str
    name: Optional[str] = None
    action_id: Optional[str] = None
    notification_config: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        if self.name:
            return self.name
        return f"{self.recipient_type.value}:{self.recipient_id}"


class WorkflowExecutionRecord(UnoObj[WorkflowExecutionLog], DefaultObjectMixin):
    """Logs of workflow executions."""
    # Class variables
    model = WorkflowExecutionLog
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "workflow",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "workflow_id",
                "trigger_event_id",
                "status",
                "result",
                "error",
                "context",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    workflow_id: str
    workflow: Optional["WorkflowDef"] = None
    trigger_event_id: str
    status: WorkflowExecutionStatus = WorkflowExecutionStatus.PENDING
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

    def __str__(self) -> str:
        return f"Execution {self.id} - {self.status.value}"


class WorkflowDef(UnoObj[WorkflowDefinition], DefaultObjectMixin):
    """Defines a workflow that can be triggered by database events."""
    # Class variables
    model = WorkflowDefinition
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "status",
                "version",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    name: str
    description: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: str = "1.0.0"
    
    # Relationships
    triggers: List[WorkflowTrigger] = []
    conditions: List[WorkflowCondition] = []
    actions: List[WorkflowAction] = []
    recipients: List[WorkflowRecipient] = []
    logs: List[WorkflowExecutionRecord] = []

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"

    @model_validator(mode="after")
    def validate_workflow(self) -> Self:
        # Add additional validation as needed
        return self


# We've removed the legacy models and UnoObj classes to simplify the codebase.
# If you need to handle workflow steps, transitions, tasks, or instances,
# please create proper model classes in models.py and implement UnoObj classes here.
#
# The following classes were removed:
# - WorkflowStep
# - WorkflowTransition
# - Workflow (legacy version)
# - WorkflowTask
# - WorkflowInstance
#
# Only the modern WorkflowDef class is kept for managing workflow definitions.
