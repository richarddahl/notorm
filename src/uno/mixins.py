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

from uno.db import str_26, datetime_tz


class ModelMixin(BaseModel):
    id: Optional[str] = None
    is_active: Optional[bool] = True
    is_deleted: Optional[bool] = False
    created_at: Optional[datetime.datetime] = None
    modified_at: Optional[datetime.datetime] = None
    deleted_at: Optional[datetime.datetime] = None


class BaseMixin:

    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Primary Key and Foreign Key to MetaRecord Base",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("TRUE"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("FALSE"),
        doc="Indicates that the record has been soft deleted",
    )
    created_at: Mapped[datetime_tz] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was created",
    )
    modified_at: Mapped[datetime_tz] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was last modified",
    )
    deleted_at: Mapped[Optional[datetime_tz]] = mapped_column(
        nullable=True,
        server_default=FetchedValue(),
        doc="Timestamp when the record was soft deleted",
    )
