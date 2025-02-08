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
from uno.db.mixins import BaseFieldMixin, RelatedObjectPKMixin
from uno.db.sql_emitters import RecordVersionAuditSQL, AlterGrantSQL
from uno.objs.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
)
from uno.comms.enums import MessageImportance


class Message(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "message"
    __table_args__ = {
        "schema": "uno",
        "comment": "Messages are used to communicate between users",
    }
    sql_emitters = [
        AlterGrantSQL,
        RecordVersionAuditSQL,
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]
    # Columns
    sender_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_SENT_BY"},
    )
    previous_message_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "HAS_PREVIOUS_MESSAGE"},
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


class MessageAddressedTo(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "message_addressed_to"
    __table_args__ = {
        "schema": "uno",
        "comment": "Messages addressed to users",
        "info": {"rls_policy": False, "vertex": False},
    }

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
        info={"edge": "WAS_SENT_TO"},
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
        nullable=False,
    )
    read_at: Mapped[datetime.datetime] = mapped_column()

    # Relationships


class MessageCopiedTo(Base):
    __tablename__ = "message_copied_to"
    __table_args__ = {
        "schema": "uno",
        "comment": "Messages copied to users",
    }

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "WAS_CCD_ON"},
    )
    copied_to_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "WAS_CCD_TO"},
    )
    read: Mapped[bool] = mapped_column(
        server_default=text("false"),
        nullable=False,
    )
    read_at: Mapped[datetime.datetime] = mapped_column()

    # Relationships


class Attachment(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "attachment"
    __table_args__ = {
        "schema": "uno",
        "comment": "Files attached to db objects",
    }

    # Columns
    name: Mapped[str_255] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str_255] = mapped_column(doc="Path to the file")

    # Relationships


class MessageAttachment(Base):
    __tablename__ = "message_attachment"
    __table_args__ = {
        "schema": "uno",
        "comment": "Attachments to messages",
    }

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "WAS_ATTACHED_TO"},
    )
    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attachment.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "HAS_ATTACHMENT"},
    )

    # Relationships
