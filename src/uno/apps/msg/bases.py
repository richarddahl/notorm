# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional, ClassVar

from sqlalchemy import (
    ForeignKey,
    Identity,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import (
    ENUM,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uno.db.obj import (
    Base,
    str_26,
    str_255,
)
from uno.apps.meta.bases import (
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
)
from uno.db.sql.table_sql_emitters import BaseVersionAudit
from uno.db.sql.sql_emitter import SQLEmitter
from uno.msg.enums import MessageImportance
from uno.config import settings


class MessageAddressedTo(Base):
    # __tablename__ = "message__addressed_to"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "User addressed on a message",
    }
    display_name: ClassVar[str] = "Message Addressed To"
    display_name_plural: ClassVar[str] = "Messages Addressed To"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        primary_key=True,
    )
    addressed_to_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
    )
    read_at: Mapped[datetime.datetime] = mapped_column()


class MessageCopiedTo(Base):
    # __tablename__ = "message__copied_to"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "User copied on a message",
    }
    display_name: ClassVar[str] = "Message Copied To"
    display_name_plural: ClassVar[str] = "Messages Copied To"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        primary_key=True,
    )
    copied_to_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
    )
    read_at: Mapped[datetime.datetime] = mapped_column()


class MessageRelatedObject(Base):
    # __tablename__ = "message__meta"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Messages to MetaBase Objects",
    }

    display_name: ClassVar[str] = "Message MetaBase Object"
    display_name_plural: ClassVar[str] = "Message MetaBase Objects"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Message(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    __tablename__ = "message"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Messages are used to communicate between users",
    }
    display_name: ClassVar[str] = "Message"
    display_name_plural: ClassVar[str] = "Messages"

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        BaseVersionAudit,
    ]

    # Columns
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    sender_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        index=True,
    )
    flag: Mapped[MessageImportance] = mapped_column(
        ENUM(
            MessageImportance,
            name="importance_enum",
            create_type=True,
            schema=settings.DB_SCHEMA,
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
        foreign_keys=[sender_id],
        doc="User who sent the message",
        info={"edge": "IS_SENDER"},
    )
    addressed_to: Mapped[list["User"]] = relationship(
        secondary=MessageAddressedTo.__table__,
        doc="Users addressed on the message",
        info={"edge": "RECEIVED"},
    )

    copied_to: Mapped[list["User"]] = relationship(
        secondary=MessageCopiedTo.__table__,
        doc="Users copied on the message",
        info={"edge": "COPIED_ON"},
    )
    parent: Mapped["Message"] = relationship(
        foreign_keys=[parent_id],
        remote_side=[id],
        doc="Parent message",
        info={"edge": "IS_PARENT_OF"},
    )
    children: Mapped["Message"] = relationship(
        foreign_keys=[id],
        doc="Child messages",
        info={"edge": "IS_CHILD_OF"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "message",
        "inherit_condition": id == MetaBase.id,
    }
