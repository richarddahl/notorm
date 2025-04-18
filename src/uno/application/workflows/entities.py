"""
Domain entities for the workflows module.

These entities represent the core domain objects for workflows, including workflow
definitions, triggers, conditions, actions, and recipients. They provide a clean,
domain-driven interface for working with the workflow system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, ClassVar, Union
from datetime import datetime
from enum import Enum

from uno.domain.core import Entity, AggregateRoot
from uno.core.errors.base import ValidationError

from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowExecutionStatus,
    WorkflowConditionType,
)


@dataclass
class User(Entity[str]):
    """Domain entity for users that can receive workflow notifications."""

    id: str  # Primary identifier
    username: str
    email: str
    is_active: bool = True
    display_name: Optional[str] = None
    roles: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validate the user entity."""
        if not self.id:
            raise ValidationError("User ID is required")
        if not self.username:
            raise ValidationError("Username is required")
        if not self.email:
            raise ValidationError("Email is required")


@dataclass
class WorkflowTrigger(Entity[str]):
    """Domain entity for workflow triggers.

    A workflow trigger defines the conditions under which a workflow should be activated,
    typically in response to specific database events.
    """

    # Base properties
    id: str
    workflow_id: str
    entity_type: str
    operation: str
    field_conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 100
    is_active: bool = True

    # Mapping to DB model
    __uno_model__: ClassVar[str] = "WorkflowTriggerModel"

    def validate(self) -> None:
        """Validate the workflow trigger entity."""
        if not self.entity_type:
            raise ValidationError("Entity type is required")
        if not self.operation:
            raise ValidationError("Operation is required")

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "WorkflowTrigger":
        """Create a WorkflowTrigger entity from a database record."""
        return cls(
            id=record["id"],
            workflow_id=record["workflow_id"],
            entity_type=record["entity_type"],
            operation=record["operation"],
            field_conditions=record["field_conditions"],
            priority=record["priority"],
            is_active=record["is_active"],
        )


@dataclass
class WorkflowCondition(Entity[str]):
    """Domain entity for workflow conditions.

    A workflow condition defines criteria that must be satisfied for a workflow to execute
    after it has been triggered.
    """

    # Base properties
    id: str
    workflow_id: str
    condition_type: WorkflowConditionType
    condition_config: Dict[str, Any] = field(default_factory=dict)
    query_id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    order: int = 0

    # Mapping to DB model
    __uno_model__: ClassVar[str] = "WorkflowConditionModel"

    def validate(self) -> None:
        """Validate the workflow condition entity."""
        if not self.condition_type:
            raise ValidationError("Condition type is required")
        if self.condition_type == WorkflowConditionType.FIELD_VALUE:
            if not self.condition_config or "field" not in self.condition_config:
                raise ValidationError("Field is required for field value conditions")
        elif self.condition_type == WorkflowConditionType.QUERY_MATCH:
            if not self.query_id:
                raise ValidationError("Query ID is required for query match conditions")

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "WorkflowCondition":
        """Create a WorkflowCondition entity from a database record."""
        return cls(
            id=record["id"],
            workflow_id=record["workflow_id"],
            condition_type=record["condition_type"],
            condition_config=record["condition_config"],
            query_id=record["query_id"],
            name=record["name"],
            description=record["description"],
            order=record["order"],
        )


@dataclass
class WorkflowRecipient(Entity[str]):
    """Domain entity for workflow recipients.

    A workflow recipient is a user, role, or group that should receive notifications
    or actions from a workflow.
    """

    # Base properties
    id: str
    workflow_id: str
    recipient_type: WorkflowRecipientType
    recipient_id: str
    name: Optional[str] = None
    action_id: Optional[str] = None
    notification_config: Dict[str, Any] = field(default_factory=dict)

    # Mapping to DB model
    __uno_model__: ClassVar[str] = "WorkflowRecipientModel"

    def validate(self) -> None:
        """Validate the workflow recipient entity."""
        if not self.recipient_type:
            raise ValidationError("Recipient type is required")
        if not self.recipient_id:
            raise ValidationError("Recipient ID is required")

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "WorkflowRecipient":
        """Create a WorkflowRecipient entity from a database record."""
        return cls(
            id=record["id"],
            workflow_id=record["workflow_id"],
            recipient_type=record["recipient_type"],
            recipient_id=record["recipient_id"],
            name=record["name"],
            action_id=record["action_id"],
            notification_config=record["notification_config"]
            if record.get("notification_config")
            else {},
        )


@dataclass
class WorkflowAction(Entity[str]):
    """Domain entity for workflow actions.

    A workflow action defines what should happen when a workflow is triggered and
    its conditions are met.
    """

    # Base properties
    id: str
    workflow_id: str
    action_type: WorkflowActionType
    action_config: Dict[str, Any] = field(default_factory=dict)
    name: str = ""
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True
    retry_policy: Optional[Dict[str, Any]] = None
    # Relationships
    recipients: List["WorkflowRecipient"] = field(default_factory=list)
    workflow: Optional["WorkflowDef"] = field(default=None, repr=False)

    # Mapping to DB model
    __uno_model__: ClassVar[str] = "WorkflowActionModel"

    def validate(self) -> None:
        """Validate the workflow action entity."""
        if not self.action_type:
            raise ValidationError("Action type is required")
        if self.action_type == WorkflowActionType.EMAIL:
            if not self.action_config or "subject" not in self.action_config:
                raise ValidationError("Subject is required for email actions")
        elif self.action_type == WorkflowActionType.WEBHOOK:
            if not self.action_config or "url" not in self.action_config:
                raise ValidationError("URL is required for webhook actions")

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "WorkflowAction":
        """Create a WorkflowAction entity from a database record."""
        return cls(
            id=record["id"],
            workflow_id=record["workflow_id"],
            action_type=record["action_type"],
            action_config=record["action_config"],
            name=record["name"],
            description=record["description"],
            order=record["order"],
            is_active=record["is_active"],
            retry_policy=record["retry_policy"],
            recipients=[],  # Recipients are populated separately
        )


@dataclass
class WorkflowExecutionRecord(Entity[str]):
    """Domain entity for workflow execution records.

    A workflow execution record tracks the execution of a workflow, including its status,
    results, and any errors that occurred.
    """

    # Base properties
    id: str
    workflow_id: str
    trigger_event_id: str
    status: WorkflowExecutionStatus = WorkflowExecutionStatus.PENDING
    executed_at: datetime = field(default_factory=lambda: datetime.now())
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

    # Mapping to DB model
    __uno_model__: ClassVar[str] = "WorkflowExecutionLog"

    def validate(self) -> None:
        """Validate the workflow execution record entity."""
        if not self.workflow_id:
            raise ValidationError("Workflow ID is required")
        if not self.trigger_event_id:
            raise ValidationError("Trigger event ID is required")

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "WorkflowExecutionRecord":
        """Create a WorkflowExecutionRecord entity from a database record."""
        return cls(
            id=record["id"],
            workflow_id=record["workflow_id"],
            trigger_event_id=record["trigger_event_id"],
            status=record["status"],
            executed_at=record["executed_at"],
            completed_at=record["completed_at"],
            result=record["result"],
            error=record["error"],
            context=record["context"],
            execution_time=record["execution_time"],
        )


@dataclass
class WorkflowDef(AggregateRoot[str]):
    """Domain entity for workflow definitions.

    A workflow definition is the main entity that defines a complete workflow, including
    its triggers, conditions, actions, and recipients.
    """

    # Base properties
    name: str
    description: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: str = "1.0.0"
    # Relationships
    triggers: List["WorkflowTrigger"] = field(default_factory=list)
    conditions: List["WorkflowCondition"] = field(default_factory=list)
    actions: List["WorkflowAction"] = field(default_factory=list)
    recipients: List["WorkflowRecipient"] = field(default_factory=list)
    logs: List["WorkflowExecutionRecord"] = field(default_factory=list)

    # Mapping to DB model
    __uno_model__: ClassVar[str] = "WorkflowDefinition"

    def validate(self) -> None:
        """Validate the workflow definition entity."""
        if not self.name:
            raise ValidationError("Name is required")
        if not self.description:
            raise ValidationError("Description is required")
        if not isinstance(self.status, WorkflowStatus):
            try:
                self.status = WorkflowStatus(self.status)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid status: {self.status}")

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "WorkflowDef":
        """Create a WorkflowDef entity from a database record."""
        return cls(
            id=record["id"],
            name=record["name"],
            description=record["description"],
            status=record["status"],
            version=record["version"],
            triggers=[],  # These are populated separately
            conditions=[],
            actions=[],
            recipients=[],
            logs=[],
        )