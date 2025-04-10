# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    text,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    ENUM,
    VARCHAR,
    BIGINT,
)

from uno.model import UnoModel, PostgresTypes
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
from uno.settings import uno_settings


class Workflow(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "workflow"
    __table_args__ = {"comment": "User-defined workflows"}

    # Columns
    name: Mapped[PostgresTypes.String255] = mapped_column(doc="Name of the workflow")
    description: Mapped[str] = mapped_column(
        doc="Explanation of the workflow indicating its purpose and expected outcome"
    )

    # Relationships (if needed in the future)


class TaskType(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "task_type"
    __table_args__ = {"comment": "Manually created or trigger-created tasks"}

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


class Task(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "task"
    __table_args__ = {"comment": "Manually created or trigger created tasks"}

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


class TaskRecord(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "task_record"
    __table_args__ = {"comment": "Records of task completions"}

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
