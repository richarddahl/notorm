# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    Identity,
    text,
)
from sqlalchemy.dialects.postgresql import (
    ENUM,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uno.db.tables import (
    Base,
    RelatedObject,
    BaseMetaMixin,
    RecordUserAuditMixin,
    str_26,
    str_255,
)

from uno.wkflw.enums import (
    WorkflowRecordStatus,
    WorkflowRecordState,
    WorkflowFlag,
    WorkflowDBEvent,
    WorkflowTrigger,
)
from uno.config import settings


class Workflow(RelatedObject, RecordUserAuditMixin):
    __tablename__ = "workflow"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "User-defined workflows",
    }

    display_name = "Workflow"
    display_name_plural = "Workflows"

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
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
            schema="uno",
        ),
        default=WorkflowTrigger.DB_EVENT,
        doc="The type of event that triggers execution of the workflow",
    )
    repeat_every: Mapped[int] = mapped_column(
        server_default=text("0"), doc="Repeat every x days"
    )
    flag: Mapped[WorkflowFlag] = mapped_column(
        ENUM(
            WorkflowFlag,
            name="workflowflag",
            create_type=True,
            schema="uno",
        ),
        default=WorkflowFlag.MEDIUM,
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
            schema="uno",
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
    applicable_object_type_name: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.objecttype.name", ondelete="CASCADE"),
    )
    record_object_type_name: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.objecttype.name", ondelete="CASCADE"),
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
        "ix_workflow_applicable_object_type_name",
        "applicable_object_type_name",
        unique=True,
    )
    Index(
        "ix_workflowrecord_object_type_name",
        "record_object_type_name",
        unique=True,
    )

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "workflow",
        "inherit_condition": id == RelatedObject.id,
    }


class WorkflowEvent(RelatedObject, RecordUserAuditMixin):
    __tablename__ = "workflowevent"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Manually created or trigger created workflow activities",
    }
    display_name = "Workflow Event"
    display_name_plural = "Workflow Events"

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    workflow_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.workflow.id", ondelete="CASCADE"),
        index=True,
    )
    date_due: Mapped[datetime.date] = mapped_column(doc="Date the workflow is due")
    workflow_object_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id", ondelete="CASCADE"),
        index=True,
    )
    objectfunction_return_value: Mapped[Optional[bool]] = mapped_column(
        doc="Value returned by the Object Function to indicate the workflow is complete"
    )
    __mapper_args__ = {
        "polymorphic_identity": "workflowevent",
        "inherit_condition": id == RelatedObject.id,
    }

    # Relationships


class WorkflowRecord(RelatedObject, RecordUserAuditMixin, BaseMetaMixin):
    __tablename__ = "workflowrecord"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Records of workflow events",
    }
    display_name = "Workflow Record"
    display_name_plural = "Workflow Records"

    sql_emitters = []

    # graph_edge_defs = workflow_record_edge_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    workflowevent_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.workflowevent.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[WorkflowRecordStatus] = mapped_column(
        ENUM(
            WorkflowRecordStatus,
            name="workflowrecordstatus",
            create_type=True,
            schema="uno",
        ),
        default=WorkflowRecordStatus.OPEN,
        doc="Status of the workflow record",
    )
    state: Mapped[WorkflowRecordState] = mapped_column(
        ENUM(
            WorkflowRecordState,
            name="workflowrecordstate",
            create_type=True,
            schema="uno",
        ),
        default=WorkflowRecordState.PENDING,
        doc="State of the workflow record",
    )
    comment: Mapped[str] = mapped_column(
        doc="User defined or auto-generated comment on the workflow execution",
    )
    """
    workflowrecord_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id", ondelete="CASCADE"),
        index=True,
    )
    """
    # ForeignKeyConstraint(
    #    ["workflowrecord_id"],
    #    [f"{settings.DB_SCHEMA}.relatedobject.id"],
    #    name="fk_workflowrecord_record_related_object_id",
    #    ondelete="CASCADE",
    # )

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "workflowrecord",
        "inherit_condition": id == RelatedObject.id,
    }


class ObjectFunction(Base):
    __tablename__ = "objectfunction"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Functions that can be called by user-defined workflows and reports",
    }
    display_name = "Object Function"
    display_name_plural = "Object Functions"
    include_in_graph = False

    sql_emitters = []

    # Columns
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)

    name: Mapped[str] = mapped_column(doc="Label of the function")
    documentation: Mapped[Optional[str]] = mapped_column(
        doc="Documentation of the function"
    )
    name: Mapped[str] = mapped_column(doc="Name of the function")
    """
    function_object_type_name: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.object_type_name", ondelete="CASCADE"),
        index=True,
    )
    """
    # Relationships
