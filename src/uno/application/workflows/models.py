# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
import enum
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    text,
    Column,
    String,
    DateTime,
    JSON,
    Index,
    Boolean,
    Integer,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    ENUM,
    VARCHAR,
    BIGINT,
    JSONB,
)

from uno.domain.base.model import ModelBase, PostgresTypes
from uno.mixins import ModelMixin
from uno.authorization.mixins import RecordAuditModelMixin
from uno.enums import (
    SQLOperation,
    WorkflowDBEvent,
    WorkflowTrigger,
    Status,
    State,
    Flag,
)

# Import domain entities only when type checking to avoid circular imports
if TYPE_CHECKING:
    from uno.workflows.entities import WorkflowTrigger, User
from uno.settings import uno_settings


# Extended Workflow Enums
class WorkflowStatus(enum.StrEnum):
    """Workflow status states"""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class WorkflowActionType(enum.StrEnum):
    """Types of actions a workflow can perform"""

    NOTIFICATION = "notification"
    EMAIL = "email"
    WEBHOOK = "webhook"
    DATABASE = "database"
    CUSTOM = "custom"


class WorkflowRecipientType(enum.StrEnum):
    """Types of workflow notification recipients"""

    USER = "user"
    ROLE = "role"
    GROUP = "group"
    ATTRIBUTE = "attribute"


class WorkflowExecutionStatus(enum.StrEnum):
    """Status of workflow execution"""

    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELED = "canceled"


class WorkflowConditionType(enum.StrEnum):
    """Types of workflow conditions"""

    FIELD_VALUE = "field_value"
    TIME_BASED = "time_based"
    ROLE_BASED = "role_based"
    QUERY_MATCH = "query_match"  # Uses existing QueryModel for complex conditions
    CUSTOM = "custom"


class WorkflowDefinition(ModelMixin, BaseModel, RecordAuditModelMixin):
    """Defines a workflow that can be triggered by database events."""

    __tablename__ = "workflow_definition"
    __table_args__ = ({"comment": "User-defined workflow definitions"},)

    # Basic workflow information
    name: Mapped[PostgresTypes.String255] = mapped_column(doc="Name of the workflow")
    description: Mapped[str] = mapped_column(
        doc="Explanation of the workflow indicating its purpose and expected outcome"
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        ENUM(
            WorkflowStatus,
            name="workflow_status",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowStatus.DRAFT,
        doc="Current status of the workflow definition",
    )
    version: Mapped[str] = mapped_column(
        default="1.0.0",
        doc="Version of the workflow definition",
    )

    # Relationships
    triggers: Mapped[list["WorkflowTriggerModel"]] = relationship(
        "WorkflowTriggerModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    conditions: Mapped[list["WorkflowConditionModel"]] = relationship(
        "WorkflowConditionModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    actions: Mapped[list["WorkflowActionModel"]] = relationship(
        "WorkflowActionModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    recipients: Mapped[list["WorkflowRecipientModel"]] = relationship(
        "WorkflowRecipientModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    logs: Mapped[list["WorkflowExecutionLog"]] = relationship(
        "WorkflowExecutionLog",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )


class WorkflowTriggerModel(ModelMixin, BaseModel, RecordAuditModelMixin):
    """Defines what triggers a workflow."""

    __tablename__ = "workflow_trigger"
    __table_args__ = (
        Index("idx_workflow_trigger_entity", "entity_type"),
        {"comment": "Triggers that activate workflows"},
    )

    # Foreign key to workflow
    workflow_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("workflow_definition.id", ondelete="CASCADE"),
        index=True,
        doc="The workflow this trigger belongs to",
    )
    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="triggers",
    )

    # Trigger configuration
    entity_type: Mapped[str] = mapped_column(
        doc="Entity type to watch (e.g., 'user', 'order')",
    )
    operation: Mapped[WorkflowDBEvent] = mapped_column(
        ENUM(
            WorkflowDBEvent,
            name="workflowdbevent",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowDBEvent.INSERT,
        doc="The database operation that triggers the workflow",
    )
    field_conditions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default={},
        doc="Field conditions that must be met to trigger (e.g., {'status': 'approved'})",
    )
    priority: Mapped[int] = mapped_column(
        default=100,
        doc="Priority of this trigger (lower values have higher priority)",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether this trigger is active",
    )


class WorkflowConditionModel(ModelMixin, BaseModel, RecordAuditModelMixin):
    """Additional conditions that must be met for workflow to execute."""

    __tablename__ = "workflow_condition"
    __table_args__ = ({"comment": "Conditions for workflow execution"},)

    # Foreign key to workflow
    workflow_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("workflow_definition.id", ondelete="CASCADE"),
        index=True,
        doc="The workflow this condition belongs to",
    )
    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="conditions",
    )

    # Condition configuration
    condition_type: Mapped[WorkflowConditionType] = mapped_column(
        ENUM(
            WorkflowConditionType,
            name="workflow_condition_type",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowConditionType.FIELD_VALUE,
        doc="Type of condition to evaluate",
    )
    condition_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default={},
        doc="Configuration for the condition",
    )
    query_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("query.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to a QueryModel for complex condition evaluation (used with QUERY_MATCH type)",
        info={"edge": "USES_QUERY", "reverse_edge": "USED_BY_CONDITIONS"},
    )
    name: Mapped[str] = mapped_column(
        default="",
        doc="Optional name for the condition",
    )
    description: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        doc="Description of what this condition checks",
    )
    order: Mapped[int] = mapped_column(
        default=0,
        doc="Order in which conditions are evaluated",
    )


class WorkflowActionModel(ModelMixin, BaseModel, RecordAuditModelMixin):
    """Action to take when workflow is triggered and conditions are met."""

    __tablename__ = "workflow_action"
    __table_args__ = ({"comment": "Actions to execute when workflow is triggered"},)

    # Foreign key to workflow
    workflow_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("workflow_definition.id", ondelete="CASCADE"),
        index=True,
        doc="The workflow this action belongs to",
    )
    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="actions",
    )

    # Action configuration
    action_type: Mapped[WorkflowActionType] = mapped_column(
        ENUM(
            WorkflowActionType,
            name="workflow_action_type",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowActionType.NOTIFICATION,
        doc="Type of action to perform",
    )
    action_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default={},
        doc="Configuration for the action",
    )
    name: Mapped[str] = mapped_column(
        default="",
        doc="Optional name for the action",
    )
    description: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        doc="Description of what this action does",
    )
    order: Mapped[int] = mapped_column(
        default=0,
        doc="Order in which actions are executed",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether this action is active",
    )
    retry_policy: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Policy for retrying failed actions",
    )


class WorkflowRecipientModel(ModelMixin, BaseModel, RecordAuditModelMixin):
    """Recipients for workflow notifications."""

    __tablename__ = "workflow_recipient"
    __table_args__ = ({"comment": "Recipients for workflow notifications"},)

    # Foreign key to workflow
    workflow_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("workflow_definition.id", ondelete="CASCADE"),
        index=True,
        doc="The workflow this recipient belongs to",
    )
    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="recipients",
    )

    # Recipient configuration
    recipient_type: Mapped[WorkflowRecipientType] = mapped_column(
        ENUM(
            WorkflowRecipientType,
            name="workflow_recipient_type",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowRecipientType.USER,
        doc="Type of recipient",
    )
    recipient_id: Mapped[str] = mapped_column(
        doc="ID of the recipient (user ID, role name, group ID, etc.)",
    )
    name: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        doc="Optional descriptive name for this recipient",
    )
    action_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("workflow_action.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="If specified, this recipient is only for a specific action",
    )
    notification_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional notification configuration for this recipient",
    )


class WorkflowExecutionLog(ModelMixin, BaseModel, RecordAuditModelMixin):
    """Logs of workflow executions."""

    __tablename__ = "workflow_execution_log"
    __table_args__ = (
        Index("idx_workflow_execution_status", "status"),
        Index("idx_workflow_execution_timestamp", "executed_at"),
        {"comment": "Log of workflow executions"},
    )

    # Foreign key to workflow
    workflow_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("workflow_definition.id", ondelete="CASCADE"),
        index=True,
        doc="The workflow that was executed",
    )
    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="logs",
    )

    # Execution details
    trigger_event_id: Mapped[str] = mapped_column(
        doc="Reference to the event that triggered this workflow execution",
    )
    status: Mapped[WorkflowExecutionStatus] = mapped_column(
        ENUM(
            WorkflowExecutionStatus,
            name="workflow_execution_status",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowExecutionStatus.PENDING,
        doc="Status of the workflow execution",
    )
    executed_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(datetime.UTC),
        doc="When the workflow was executed",
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        doc="When the workflow execution completed",
    )
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Results of the workflow execution",
    )
    error: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        doc="Error message if execution failed",
    )
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Context data for this execution",
    )
    execution_time: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        doc="Execution time in milliseconds",
    )


# Legacy models to maintain backward compatibility - marked for future removal
class Workflow(ModelMixin, BaseModel, RecordAuditModelMixin):
    __tablename__ = "workflow"
    __table_args__ = {
        "comment": "DEPRECATED: User-defined workflows, use workflow_definition instead"
    }

    # Columns
    name: Mapped[PostgresTypes.String255] = mapped_column(doc="Name of the workflow")
    description: Mapped[str] = mapped_column(
        doc="Explanation of the workflow indicating its purpose and expected outcome"
    )


class TaskType(ModelMixin, BaseModel, RecordAuditModelMixin):
    __tablename__ = "task_type"
    __table_args__ = {
        "comment": "DEPRECATED: Manually created or trigger-created tasks"
    }

    # Columns
    name: Mapped[PostgresTypes.String255] = mapped_column(doc="Name of the task type")
    description: Mapped[str] = mapped_column(
        doc="Explanation of the task type indicating its purpose and expected outcome"
    )
    workflow_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("workflow.id", ondelete="CASCADE"),
        index=True,
    )
    responsibility_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("responsibility.id", ondelete="CASCADE"),
        index=True,
    )
    due_within: Mapped[Optional[int]] = mapped_column(
        server_default=text("7"),
        nullable=True,
        doc="Number of days within which the task must be completed",
    )
    record_required: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates if a task record is required",
    )
    applicable_meta_type_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey(
            "meta_type.id",
            ondelete="CASCADE",
        ),
    )
    applicablity_limiting_query_id: Mapped[Optional[PostgresTypes.String26]] = (
        mapped_column(
            ForeignKey(
                "query.id",
                ondelete="SET NULL",
            ),
            nullable=True,
        )
    )
    record_meta_type_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
    )
    parent_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("step.id", ondelete="CASCADE"),
        index=True,
    )
    trigger: Mapped[WorkflowTrigger] = mapped_column(
        ENUM(
            WorkflowTrigger,
            name="workflowtrigger",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowTrigger.DB_EVENT,
        doc="The type of event that triggers the execution of the workflow",
    )
    repeat_every: Mapped[int] = mapped_column(
        server_default=text("0"), doc="Repeat every x days"
    )
    flag: Mapped[Flag] = mapped_column(
        ENUM(
            Flag,
            name="workflowflag",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=Flag.MEDIUM,
        doc="Flag indicating the importance of the workflow",
    )
    db_event: Mapped[Optional[WorkflowDBEvent]] = mapped_column(
        ENUM(
            WorkflowDBEvent,
            name="workflowdbevent",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        default=WorkflowDBEvent.INSERT,
        doc="The database event that triggers the workflow, if applicable",
    )
    responsible_role_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("responsibility_role.id", ondelete="CASCADE"),
        nullable=True,
        doc="The role responsible for completing the task",
        info={"edge": "RESPONSIBLE", "reverse_edge": "RESPONSIBLE_TASKS"},
    )
    accountable_role_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("responsibility_role.id", ondelete="CASCADE"),
        nullable=True,
        doc="The role accountable for the task",
        info={"edge": "ACCOUNTABLE", "reverse_edge": "ACCOUNTABLE_TASKS"},
    )
    consulted_role_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("responsibility_role.id", ondelete="CASCADE"),
        nullable=True,
        doc="The role consulted for the task",
        info={"edge": "CONSULTED", "reverse_edge": "CONSULTED_TASKS"},
    )
    informed_role_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("responsibility_role.id", ondelete="CASCADE"),
        nullable=True,
        doc="The role informed for the task",
        info={"edge": "INFORMED", "reverse_edge": "INFORMED_TASKS"},
    )


class Task(ModelMixin, BaseModel, RecordAuditModelMixin):
    __tablename__ = "task"
    __table_args__ = {
        "comment": "DEPRECATED: Manually created or trigger created tasks"
    }

    # Columns
    task_type_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("task_type.id", ondelete="CASCADE"),
        index=True,
    )
    task_object_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        index=True,
    )
    due_date: Mapped[Optional[datetime.date]] = mapped_column(
        nullable=True,
        doc="Date the task is due",
    )
    completed_date: Mapped[Optional[datetime.date]] = mapped_column(
        nullable=True,
        doc="Date the task was completed",
    )
    record_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("task_record.id", ondelete="CASCADE"),
        nullable=True,
        doc="Record of the task completion",
        info={"edge": "RECORD", "reverse_edge": "RECORDS"},
    )


class TaskRecord(ModelMixin, BaseModel, RecordAuditModelMixin):
    __tablename__ = "task_record"
    __table_args__ = {"comment": "DEPRECATED: Records of task completions"}

    # Columns
    task_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("task.id", ondelete="CASCADE"),
        index=True,
    )
    completion_date: Mapped[PostgresTypes.Date] = mapped_column(
        doc="Date the task was completed",
    )
    notes: Mapped[str] = mapped_column(
        doc="Notes about the completion of the task",
    )
    record_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        nullable=True,
    )
