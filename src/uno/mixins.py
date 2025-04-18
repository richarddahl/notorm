# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
from typing import Optional

from sqlalchemy import ForeignKey, FetchedValue, text
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from pydantic import BaseModel

from uno.domain.base.model import PostgresTypes


class ObjectMixin(BaseModel):
    id: Optional[str] = None
    is_active: Optional[bool] = True
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime.datetime] = None
    modified_at: Optional[datetime.datetime] = None
    deleted_at: Optional[datetime.datetime] = None


class ModelMixin:

    id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Primary Key and Foreign Key to MetaRecord Model",
        info={"graph_excludes": True},
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("TRUE"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("FALSE"),
        doc="Indicates that the record has been soft deleted",
    )
    created_at: Mapped[PostgresTypes.Timestamp] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was created",
    )
    modified_at: Mapped[PostgresTypes.Timestamp] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was last modified",
    )
    deleted_at: Mapped[Optional[PostgresTypes.Timestamp]] = mapped_column(
        nullable=True,
        server_default=FetchedValue(),
        doc="Timestamp when the record was soft deleted",
    )
