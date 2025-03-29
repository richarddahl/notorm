# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import ForeignKey, Table, Column, FetchedValue, func, text
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db import UnoBase, str_255, str_26, datetime_tz
from uno.mixins import BaseMixin
from uno.meta.bases import MetaTypeBase, MetaRecordBase
from uno.auth.mixins import GroupBaseMixin
from uno.qry.bases import QueryBase
from uno.enums import MessageImportance
from uno.config import settings


message__meta_record = Table(
    "message__meta_record",
    UnoBase.metadata,
    Column(
        "message_id",
        ForeignKey("message.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "META_RECORDS"},
    ),
    Column(
        "meta_record_id",
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "MESSAGES"},
    ),
)


class MessageUser(GroupBaseMixin, BaseMixin, UnoBase):
    __tablename__ = "message_user"
    __table_args__ = {"comment": "Message Users"}

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "USERS"},
    )
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "MESSAGES"},
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("FALSE"),
        info={"edge": "READ", "reverse_edge": "READ_MESSAGES"},
    )
    read_at: Mapped[datetime_tz] = mapped_column(
        server_default=FetchedValue(),
        info={"edge": "READ_AT", "reverse_edge": "READ_AT_MESSAGES"},
    )


class MessageCopiedTo(GroupBaseMixin, BaseMixin, UnoBase):
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
    read_at: Mapped[datetime_tz] = mapped_column()


class Message(
    MetaRecordBase,
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
    sent_at: Mapped[datetime_tz] = mapped_column(
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
        "inherit_condition": id == MetaRecordBase.id,
    }
