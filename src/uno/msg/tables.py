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

from uno.db.base import (
    Base,
    str_26,
    str_255,
)
from uno.db.tables import (
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
)
from uno.db.sql_emitters import RecordVersionAuditSQL
from uno.db.sql_emitters import SQLEmitter
from uno.msg.enums import MessageImportance
from uno.config import settings


class MessageAddressedTo(Base):
    __tablename__ = "message__addressed_to"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "User addressed on a message",
    }
    display_name: ClassVar[str] = "Message Addressed To"
    display_name_plural: ClassVar[str] = "Messages Addressed To"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    include_in_graph = False

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.message.id", ondelete="CASCADE"),
        primary_key=True,
    )
    addressed_to_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
    )
    read_at: Mapped[datetime.datetime] = mapped_column()


class MessageCopiedTo(Base):
    __tablename__ = "message__copied_to"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "User copied on a message",
    }
    display_name: ClassVar[str] = "Message Copied To"
    display_name_plural: ClassVar[str] = "Messages Copied To"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    include_in_graph = False

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.message.id", ondelete="CASCADE"),
        primary_key=True,
    )
    copied_to_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
    )
    read_at: Mapped[datetime.datetime] = mapped_column()


class MessageRelatedObject(Base):
    __tablename__ = "message__meta"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Messages to MetaRecord Objects",
    }

    display_name: ClassVar[str] = "Message MetaRecord Object"
    display_name_plural: ClassVar[str] = "Message MetaRecord Objects"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    include_in_graph = False

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.message.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Message(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "message"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Messages are used to communicate between users",
    }
    display_name: ClassVar[str] = "Message"
    display_name_plural: ClassVar[str] = "Messages"

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        RecordVersionAuditSQL,
    ]

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    sender_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        index=True,
    )
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.message.id", ondelete="CASCADE"),
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
        back_populates="messages_sent",
        foreign_keys=[sender_id],
        doc="User who sent the message",
        info={"edge": "IS_SENDER"},
    )
    addressed_to: Mapped["User"] = relationship(
        back_populates="messages_recieved",
        secondary=MessageAddressedTo.__table__,
        doc="Users addressed on the message",
        info={"edge": "RECEIVED"},
    )

    copied_to: Mapped["User"] = relationship(
        back_populates="copied_messages",
        secondary=MessageCopiedTo.__table__,
        doc="Users copied on the message",
        info={"edge": "COPIED_ON"},
    )
    parent: Mapped["Message"] = relationship(
        back_populates="children",
        foreign_keys=[parent_id],
        doc="Parent message",
        info={"edge": "IS_PARENT_OF"},
    )
    children: Mapped["Message"] = relationship(
        back_populates="parent",
        foreign_keys=[parent_id],
        remote_side=[id],
        doc="Child messages",
        info={"edge": "IS_CHILD_OF"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "message",
        "inherit_condition": id == MetaRecord.id,
    }
