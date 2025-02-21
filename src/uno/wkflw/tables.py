# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional, ClassVar

from sqlalchemy import (
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import (
    ENUM,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uno.db.base import str_26, str_255
from uno.db.tables import (
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
)
from uno.db.sql.sql_emitter import SQLEmitter
from uno.wkflw.enums import (
    WorkflowDBEvent,
    WorkflowTrigger,
)
from uno.rprt.enums import Status, State, Flag
from uno.config import settings


class Workflow(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
):
    __tablename__ = "workflow"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "User-defined workflows",
    }

    display_name: ClassVar[str] = "Workflow"
    display_name_plural: ClassVar[str] = "Workflows"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    name: Mapped[str_255] = mapped_column(doc="Name of the workflow")
    explanation: Mapped[str] = mapped_column(
        doc="Explanation of the workflow indicating the purpose and the expected outcome"
    )
    trigger: Mapped[WorkflowTrigger] = mapped_column(
        ENUM(
            WorkflowTrigger,
            name="workflowtrigger",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        default=WorkflowTrigger.DB_EVENT,
        doc="The type of event that triggers execution of the workflow",
    )
    repeat_every: Mapped[int] = mapped_column(
        server_default=text("0"), doc="Repeat every x days"
    )
    flag: Mapped[Flag] = mapped_column(
        ENUM(
            Flag,
            name="workflowflag",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        default=Flag.MEDIUM,
        doc="Flag indicating the importance of the workflow",
    )
    due_within: Mapped[int] = mapped_column(
        server_default=text("7"), doc="Due within x days"
    )
    db_event: Mapped[WorkflowDBEvent] = mapped_column(
        ENUM(
            WorkflowDBEvent,
            name="workflowdbevent",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        default=WorkflowDBEvent.INSERT,
        doc="The database event that triggers the workflow, if applicable",
    )
    auto_run: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates if the workflow should be run automatically",
    )
    record_required: Mapped[bool] = mapped_column(
        server_default=text("false"), doc="Indicats if a Workflow Record is required"
    )
    """
    limiting_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(
            f"{settings.DB_SCHEMA}.query.id",
            ondelete="SET NULL",
            name="fk_workflow_query_id",
        ),
        index=True,
    )
    parent_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.workflow.id", ondelete="CASCADE"),
        index=True,
    )
    applicable_meta_type_name: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
    )
    record_meta_type_name: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
    )
    objectfunction_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.objectfunction.id", ondelete="SET NULL"),
        index=True,
    )
    """
    process_child_value: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="The value returned by the Object Function that indicates that any child Workflows must be processed",
    )
    Index(
        "ix_workflow_applicable_meta_type_name",
        "applicable_meta_type_name",
        unique=True,
    )
    Index(
        "ix_workflowrecord_meta_type_name",
        "record_meta_type_name",
        unique=True,
    )

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "workflow",
        "inherit_condition": id == MetaRecord.id,
    }


class WorkflowStep(
    MetaRecord, MetaObjectMixin, RecordAuditMixin, HistoryTableAuditMixin
):
    __tablename__ = "workflow_step"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Manually created or trigger created workflow activities",
    }
    display_name: ClassVar[str] = "Workflow Step"
    display_name_plural: ClassVar[str] = "Workflow Steps"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    workflow_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.workflow.id", ondelete="CASCADE"),
        index=True,
    )
    date_due: Mapped[datetime.date] = mapped_column(doc="Date the workflow is due")
    workflow_object_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id", ondelete="CASCADE"),
        index=True,
    )
    objectfunction_return_value: Mapped[Optional[bool]] = mapped_column(
        doc="Value returned by the Object Function to indicate the workflow is complete"
    )
    __mapper_args__ = {
        "polymorphic_identity": "workflow_step",
        "inherit_condition": id == MetaRecord.id,
    }

    # Relationships
