# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import ForeignKey, Table, Column, FetchedValue, func, text, Identity
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db import UnoModel, str_255, str_26, datetime_tz
from uno.mixins import ModelMixin
from uno.meta.objects import MetaRecordModel
from uno.auth.mixins import GroupModelMixin
from uno.auth.models import UserModel
from uno.enums import MessageImportance
from uno.config import settings


message__meta_record = Table(
    "message__meta_record",
    UnoModel.metadata,
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


class MessageModel(GroupModelMixin, ModelMixin, UnoModel):
    __tablename__ = "message"
    __table_args__ = {"comment": "Messages are used to communicate between users"}

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        index=True,
        nullable=False,
        doc="Primary Key",
        info={"graph_excludes": True},
    )
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=True,
        doc="Parent message",
        info={"edge": "PARENT", "reverse_edge": "CHILD_MESSAGES"},
    )
    flag: Mapped[MessageImportance] = mapped_column(
        ENUM(
            MessageImportance,
            name="importance_enum",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        default=MessageImportance.INFORMATION.value,
        doc="Importance of the message",
    )
    subject: Mapped[str_255] = mapped_column(
        doc="Subject of the message",
    )
    body: Mapped[str_255] = mapped_column(
        doc="Body of the message",
    )
    is_draft: Mapped[bool] = mapped_column(
        server_default=text("TRUE"),
        doc="Whether the message is a draft",
    )
    sent_at: Mapped[datetime_tz] = mapped_column(
        server_default=func.current_timestamp(),
        doc="Time the message was sent",
    )

    # Relationships
    users: Mapped[list["MessageUserModel"]] = relationship(
        back_populates="message",
        doc="Users associated with the message",
    )
    meta_records: Mapped[list[MetaRecordModel]] = relationship(
        secondary=message__meta_record,
        doc="Meta records associated with the message",
    )
    parent: Mapped["MessageModel"] = relationship(
        foreign_keys=[parent_id],
        back_populates="children",
        doc="The parent attribute type",
    )
    children: Mapped[list["MessageModel"]] = relationship(
        back_populates="parent",
        remote_side=[id],
        doc="The child attribute types",
    )


class MessageUserModel(UnoModel):
    __tablename__ = "message_user"
    __table_args__ = {"comment": "Message Users"}

    # Columns
    # ID  necessary on this base as it does not inherit from ModelMixin
    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="The unique identifier for the attribute type",
        info={"graph_excludes": True},
    )
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "MESSAGE", "reverse_edge": "MESSAGE_USERS"},
    )
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "USER", "reverse_edge": "MESSAGE_USERS"},
    )
    is_sender: Mapped[bool] = mapped_column(
        server_default=text("FALSE"),
        primary_key=True,
        index=True,
        doc="Whether the user is the sender of the message",
    )
    is_addressee: Mapped[bool] = mapped_column(
        server_default=text("TRUE"),
        primary_key=True,
        index=True,
        doc="Whether the message was addressed to the user",
    )
    is_copied_on: Mapped[bool] = mapped_column(
        server_default=text("FALSE"),
        primary_key=True,
        index=True,
        doc="Whether the user was copied on the message",
    )
    is_blind_copied_on: Mapped[bool] = mapped_column(
        server_default=text("FALSE"),
        primary_key=True,
        index=True,
        doc="Whether the user was blind copied on the message",
    )
    is_read: Mapped[bool] = mapped_column(
        server_default=text("FALSE"),
        doc="Whether the message was read",
    )
    read_at: Mapped[Optional[datetime_tz]] = mapped_column(
        nullable=True,
        doc="Time the message was read",
    )

    # Relationships
    message: Mapped[MessageModel] = relationship(
        back_populates="users",
        foreign_keys=[message_id],
        doc="Message associated with the user",
    )
    user: Mapped[UserModel] = relationship(
        back_populates="messages",
        foreign_keys=[user_id],
        doc="User associated with the message",
    )
