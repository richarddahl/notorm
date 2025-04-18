# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Table, Column, FetchedValue, func, text, Identity
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.domain.base.model import BaseModel, PostgresTypes
from uno.mixins import ModelMixin
from uno.authorization.mixins import GroupModelMixin
from uno.enums import MessageImportance
from uno.meta.models import MetaRecordModel 
from uno.settings import uno_settings

# Handle circular imports
if TYPE_CHECKING:
    from uno.authorization.models import UserModel


message__meta_record = Table(
    "message__meta_record",
    BaseModel.metadata,
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


class MessageModel(GroupModelMixin, ModelMixin, BaseModel):
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
    parent_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
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
            schema=uno_settings.DB_SCHEMA,
        ),
        default=MessageImportance.INFORMATION.value,
        doc="Importance of the message",
    )
    subject: Mapped[PostgresTypes.String255] = mapped_column(
        doc="Subject of the message",
    )
    body: Mapped[PostgresTypes.String255] = mapped_column(
        doc="Body of the message",
    )
    is_draft: Mapped[bool] = mapped_column(
        server_default=text("TRUE"),
        doc="Whether the message is a draft",
    )
    sent_at: Mapped[PostgresTypes.Timestamp] = mapped_column(
        server_default=func.current_timestamp(),
        doc="Time the message was sent",
    )

    users: Mapped[list["MessageUserModel"]] = relationship(
        "MessageUserModel",
        back_populates="message",
        doc="Users associated with the message",
    meta_records: Mapped[list["MetaRecordModel"]] = relationship(
        "MetaRecordModel",
        secondary=message__meta_record,
        doc="Meta records associated with the message",
    parent: Mapped["MessageModel"] = relationship(
        "MessageModel",
        foreign_keys=[parent_id],
        back_populates="children",
        doc="The parent attribute type",
    children: Mapped[list["MessageModel"]] = relationship(
        "MessageModel",
        back_populates="parent",
        remote_side=[id],
        doc="The child attribute types",
    )
        back_populates="parent",
        remote_side=[id],
        doc="The child attribute types",
    )


class MessageUserModel(BaseModel):
    __tablename__ = "message_user"
    __table_args__ = {"comment": "Message Users"}

    # Columns
    # ID  necessary on this base as it does not inherit from ModelMixin
    id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="The unique identifier for the attribute type",
        info={"graph_excludes": True},
    )
    message_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "MESSAGE", "reverse_edge": "MESSAGE_USERS"},
    )
    user_id: Mapped[PostgresTypes.String26] = mapped_column(
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
    read_at: Mapped[Optional[PostgresTypes.Timestamp]] = mapped_column(
        nullable=True,
        doc="Time the message was read",
    )

    # Relationships
    message: Mapped[MessageModel] = relationship(
        back_populates="users",
        foreign_keys=[message_id],
        doc="Message associated with the user",
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel",  # Use string literal to avoid circular import issues
        back_populates="messages",
        foreign_keys=[user_id],
        doc="User associated with the message",
    )
