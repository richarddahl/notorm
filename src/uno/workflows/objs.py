# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List, Dict, Any
from typing_extensions import Self
from datetime import datetime
from pydantic import model_validator, Field

# Import shared base objects and schema configuration from internal modules
from uno.obj import UnoObj
from uno.schema.schema import UnoSchemaConfig
from uno.authorization.mixins import DefaultObjectMixin

# Import additional types from auth objs to mirror their patterns
from uno.authorization.objs import User, MetaType, MetaRecord
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


# Legacy object models for backward compatibility - will be removed in future
class WorkflowStep(UnoObj, DefaultObjectMixin):
    # Fields
    name: str
    description: Optional[str] = None
    step_type: str  # manual, automatic, approval, notification
    workflow_id: str
    workflow: Optional["Workflow"] = None
    is_start: bool = False
    is_end: bool = False
    config: Dict[str, Any] = {}

    def __str__(self) -> str:
        return self.name

    @model_validator(mode="after")
    def validate_step(self) -> Self:
        # Validate step_type is one of the allowed types
        allowed_types = ["manual", "automatic", "approval", "notification"]
        if self.step_type not in allowed_types:
            raise ValueError(f"Step type must be one of: {', '.join(allowed_types)}")
        return self


class WorkflowTransition(UnoObj, DefaultObjectMixin):
    # Fields
    name: str
    description: Optional[str] = None
    workflow_id: str
    workflow: Optional["Workflow"] = None
    from_step_id: str
    from_step: Optional[WorkflowStep] = None
    to_step_id: str
    to_step: Optional[WorkflowStep] = None
    condition: Optional[str] = None  # Python expression

    def __str__(self) -> str:
        return self.name


class Workflow(UnoObj, DefaultObjectMixin):
    # Fields
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    is_active: bool = True
    applicable_type_ids: List[str] = []
    applicable_types: List[MetaType] = []
    steps: List[WorkflowStep] = []
    transitions: List[WorkflowTransition] = []

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class WorkflowTask(UnoObj, DefaultObjectMixin):
    # Fields
    title: str
    description: Optional[str] = None
    instance_id: str
    instance: Optional["WorkflowInstance"] = None
    step_id: str
    step: Optional[WorkflowStep] = None
    assigned_to_id: Optional[str] = None
    assigned_to: Optional[User] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, in_progress, completed, cancelled
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.title

    @model_validator(mode="after")
    def validate_task(self) -> Self:
        # Validate priority is one of the allowed values
        allowed_priorities = ["low", "medium", "high"]
        if self.priority not in allowed_priorities:
            raise ValueError(
                f"Priority must be one of: {', '.join(allowed_priorities)}"
            )

        # Validate status is one of the allowed values
        allowed_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if self.status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return self


class WorkflowInstance(UnoObj, DefaultObjectMixin):
    # Fields
    workflow_id: str
    workflow: Optional[Workflow] = None
    record_type_id: str
    record_id: str
    record: Optional[MetaRecord] = None
    current_step_id: Optional[str] = None
    current_step: Optional[WorkflowStep] = None
    status: str = "active"  # active, completed, cancelled
    context: Dict[str, Any] = {}
    tasks: List[WorkflowTask] = []
    completed_at: Optional[datetime] = None

    def __str__(self) -> str:
        workflow_name = self.workflow.name if self.workflow else "Unknown"
        return f"{workflow_name} - {self.record_id}"

    @model_validator(mode="after")
    def validate_instance(self) -> Self:
        # Validate status is one of the allowed values
        allowed_statuses = ["active", "completed", "cancelled"]
        if self.status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return self
