# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import (
    ENUM,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uno.db.base import Base, str_26, str_255
from uno.db.mixins import BaseFieldMixin, DBObjectPKMixin
from uno.db.sql_emitters import RecordVersionAuditSQL, AlterGrantSQL
from uno.obj.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertDBObjectFunctionSQL,
)
from uno.msg.enums import MessageImportance
from uno.msg.graphs import message_node, message_edges


class Message(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "message"
    __table_args__ = {
        "schema": "uno",
        "comment": "Messages are used to communicate between users",
    }
    display_name = "Message"
    display_name_plural = "Messages"

    sql_emitters = [
        AlterGrantSQL,
        RecordVersionAuditSQL,
        InsertObjectTypeRecordSQL,
        InsertDBObjectFunctionSQL,
    ]

    graph_node = message_node
    graph_edges = message_edges

    # Columns
    sender_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
    )
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
    )
    flag: Mapped[MessageImportance] = mapped_column(
        ENUM(
            MessageImportance,
            name="importance_enum",
            create_type=True,
            schema="uno",
        ),
        doc="Importance of the message",
    )
    subject: Mapped[str_255] = mapped_column(doc="Subject of the message")
    body: Mapped[str_255] = mapped_column(doc="Body of the message")
    sent_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.current_timestamp(),
        doc="Time the message was sent",
    )

    # Relationships
    sender: Mapped["User"] = relationship(
        back_populates="sent_messages",
    )
    parent: Mapped["Message"] = relationship(
        back_populates="children",
    )
    children: Mapped["Message"] = relationship(
        back_populates="parent",
    )


class MessageAddressedTo(Base):
    __tablename__ = "message__addressed_to"
    __table_args__ = {
        "schema": "uno",
        "comment": "User addressed on a message",
    }
    display_name = "Message Addressed To"
    display_name_plural = "Messages Addressed To"

    sql_emitters = []
    # include_in_graph = False

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "WAS_SENT"},
    )
    addressed_to_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "RECEIEVED"},
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
        nullable=False,
    )
    read_at: Mapped[datetime.datetime] = mapped_column()

    # Relationships


class MessageCopiedTo(Base):
    __tablename__ = "message__copied_to"
    __table_args__ = {
        "schema": "uno",
        "comment": "User copied on a message",
    }
    display_name = "Message Copied To"
    display_name_plural = "Messages Copied To"
    # include_in_graph = False

    sql_emitters = []

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "WAS_COPIED"},
    )
    copied_to_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "RECEIEVED_COPY"},
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
        nullable=False,
    )
    read_at: Mapped[datetime.datetime] = mapped_column()

    # Relationships


class MessageDBObject(Base):
    __tablename__ = "message__dbobject"
    __table_args__ = {
        "schema": "uno",
        "comment": "Messages to DBObjects",
    }
    display_name = "Message DBObject"
    display_name_plural = "Message DBObjects"

    sql_emitters = []

    # include_in_graph = False

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "IS_COMMUNICATING_ABOUT"},
    )
    db_object_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.db_object.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "IS_COMMUNICATED_VIA"},
    )
