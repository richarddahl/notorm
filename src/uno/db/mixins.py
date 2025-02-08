# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime


from typing import Optional

from sqlalchemy import ForeignKey, text, func
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    declared_attr,
    relationship,
)

from uno.objs.tables import DBObject
from uno.db.base import str_26


class RelatedObjectPKMixin:
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        # #server_default=func.uno.insert_related_object(),
        doc="Primary Key and Related Object",
        info={"edge": "HAS_ID"},
    )

    @declared_attr
    def related_object(self) -> Mapped[DBObject]:
        return relationship(back_populates="related_object")


class BaseFieldMixin:
    is_active: Mapped[bool] = mapped_column(
        # server_default=text("true"),
        doc="Indicates if the record is active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        # server_default=text("false"),
        doc="Indicates if the record has been deleted",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        # server_default=func.current_timestamp(),
        doc="Time the record was created",
        info={"editable": False},
    )
    owner_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "BELONGS_TO_USER"},
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
        # server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_LAST_MODIFIED_BY", "editable": False},
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
        info={"editable": False},
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_DELETED_BY", "editable": False},
    )

    @declared_attr
    def tenant(self) -> Mapped["Tenant"]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def group(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def owner(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def modified_by(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def deleted_by(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")


class AuditMixin:
    is_active: Mapped[bool] = mapped_column(
        # server_default=text("true"),
        doc="Indicates if the record is active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        # server_default=text("false"),
        doc="Indicates if the record has been deleted",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        # server_default=func.current_timestamp(),
        doc="Time the record was created",
        info={"editable": False},
    )
    owner_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "BELONGS_TO_USER"},
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
        # server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_LAST_MODIFIED_BY", "editable": False},
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
        info={"editable": False},
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_DELETED_BY", "editable": False},
    )

    @declared_attr
    def tenant(self) -> Mapped["Tenant"]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def group(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def owner(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def modified_by(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def deleted_by(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")


class AuditMixin:
    is_active: Mapped[bool] = mapped_column(
        # server_default=text("true"),
        doc="Indicates if the record is active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        # server_default=text("false"),
        doc="Indicates if the record has been deleted",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        # server_default=func.current_timestamp(),
        doc="Time the record was created",
        info={"editable": False},
    )
    owner_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "BELONGS_TO_USER"},
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
        # server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_LAST_MODIFIED_BY", "editable": False},
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
        info={"editable": False},
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_DELETED_BY", "editable": False},
    )

    @declared_attr
    def tenant(self) -> Mapped["Tenant"]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def group(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def owner(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def modified_by(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")

    @declared_attr
    def deleted_by(self) -> Mapped[DBObject]:
        return relationship("DBObject", back_populates="related_object")
