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

from uno.db.base import Base, RelatedObjectBase, str_26, str_255
from uno.db.mixins import BaseFieldMixin

# from uno.obj.sql_emitters import InsertObjectTypeRecordSQL

from uno.wkflw.enums import (
    WorkflowRecordStatus,
    WorkflowRecordState,
    WorkflowFlag,
    WorkflowDBEvent,
    WorkflowTrigger,
)
from uno.wkflw.graphs import (
    workflow_edge_defs,
    workflow_event_edge_defs,
    workflow_record_edge_defs,
)


class Workflow(RelatedObjectBase, BaseFieldMixin):
    __tablename__ = "workflow"
    __table_args__ = {
        "schema": "uno",
        "comment": "User-defined workflows",
    }
    __mapper_args__ = {"polymorphic_identity": "workflow"}

    display_name = "Workflow"
    display_name_plural = "Workflows"

    sql_emitters = []

    graph_edge_defs = workflow_edge_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
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
            "uno.query.id",
            ondelete="SET NULL",
            name="fk_workflow_query_id",
        ),
        index=True,
        # info={"edge": "LIMITS_WORKFLOWS_TO_QUERY"},
    )
    parent_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.workflow.id", ondelete="CASCADE"),
        index=True,
        # info={"edge": "IS_CHILD_OF_WORKFLOW"},
    )
    applicable_object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        # info={"edge": "IS_WORKFLOW_FOR_ObjectType"},
    )
    record_object_type_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        # info={"edge": "HAS_workflowrecord_OF_ObjectType"},
    )
    objectfunction_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.object_function.id", ondelete="SET NULL"),
        index=True,
        # info={"edge": "IS_COMPLETED_BY_objectfunction"},
    )
    """
    process_child_value: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="The value returned by the Object Function that indicates that any child Workflows must be processed",
    )
    Index(
        "ix_workflow_applicable_object_type_id",
        "applicable_object_type_id",
        unique=True,
    )
    Index(
        "ix_workflowrecord_object_type_id",
        "record_object_type_id",
        unique=True,
    )

    # Relationships


class WorkflowEvent(RelatedObjectBase, BaseFieldMixin):
    __tablename__ = "workflow_event"
    __table_args__ = {
        "schema": "uno",
        "comment": "Manually created or trigger created workflow activities",
    }
    display_name = "Workflow Event"
    display_name_plural = "Workflow Events"

    sql_emitters = []

    graph_edge_defs = workflow_event_edge_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    workflow_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.workflow.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "IS_TYPE_OF"},
    )
    date_due: Mapped[datetime.date] = mapped_column(doc="Date the workflow is due")
    workflow_object_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "IS_EVENT_FOR"},
    )
    objectfunction_return_value: Mapped[Optional[bool]] = mapped_column(
        doc="Value returned by the Object Function to indicate the workflow is complete"
    )
    __mapper_args__ = {
        "polymorphic_identity": "workflow_event",
        "inherit_condition": id == RelatedObjectBase.id,
    }

    # Relationships


class WorkflowRecord(RelatedObjectBase, BaseFieldMixin):
    __tablename__ = "workflow_record"
    __table_args__ = {
        "schema": "uno",
        "comment": "Records of workflow events",
    }
    __mapper_args__ = {"polymorphic_identity": "workflow_record"}

    display_name = "Workflow Record"
    display_name_plural = "Workflow Records"

    sql_emitters = []

    graph_edge_defs = workflow_record_edge_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    workflowevent_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.workflow_event.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "IS_RECORD_OF"},
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
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "RECORDS_EXECUTION"},
    )
    """
    # ForeignKeyConstraint(
    #    ["workflowrecord_id"],
    #    ["uno.related_object.id"],
    #    name="fk_workflowrecord_record_related_object_id",
    #    ondelete="CASCADE",
    # )

    # Relationships


class ObjectFunction(Base):
    __tablename__ = "object_function"
    __table_args__ = {
        "schema": "uno",
        "comment": "Functions that can be called by user-defined workflows and reports",
        "info": {"rls_policy": "superuser", "in_graph": False},
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
    function_object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
    )
    """
    # Relationships
