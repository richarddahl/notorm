# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional

from sqlalchemy import MetaData, ForeignKey, FetchedValue, text
from sqlalchemy.orm import (
    registry,
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
    relationship,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import (
    BIGINT,
    TIMESTAMP,
    DATE,
    TIME,
    VARCHAR,
    ENUM,
    BOOLEAN,
    ARRAY,
    NUMERIC,
)

from uno.config import settings


# configures the naming convention for the database implicit constraints and indexes
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


meta_data = MetaData(
    naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION,
    schema=settings.DB_SCHEMA,
)

str_26 = Annotated[VARCHAR, 26]
str_63 = Annotated[VARCHAR, 63]
str_128 = Annotated[VARCHAR, 128]
str_255 = Annotated[VARCHAR, 255]
decimal = Annotated[Decimal, 19]


class UnoBase(AsyncAttrs, DeclarativeBase):
    registry = registry(
        type_annotation_map={
            int: BIGINT,
            datetime.datetime: TIMESTAMP(timezone=True),
            datetime.date: DATE,
            datetime.time: TIME,
            str: VARCHAR,
            Enum: ENUM,
            bool: BOOLEAN,
            list: ARRAY,
            decimal: NUMERIC,
            str_26: VARCHAR(26),
            str_63: VARCHAR(63),
            str_128: VARCHAR(128),
            str_255: VARCHAR(255),
        }
    )
    metadata = meta_data


class GeneralBaseMixin:

    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Primary Key and Foreign Key to Meta Base",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the record has been soft deleted",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was created",
    )
    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        server_default=FetchedValue(),
        doc="User that created the record",
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was last modified",
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        server_default=FetchedValue(),
        doc="User that last modified the record",
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        server_default=FetchedValue(),
        doc="Timestamp when the record was soft deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="User that deleted the record",
    )

    # Relationships
    @declared_attr
    def created_by(cls) -> Mapped["UserBase"]:
        return relationship(
            foreign_keys=[cls.created_by_id],
            doc="User that created the record",
        )

    @declared_attr
    def modified_by(cls) -> Mapped["UserBase"]:
        return relationship(
            foreign_keys=[cls.modified_by_id],
            doc="User that last modified the record",
        )

    @declared_attr
    def deleted_by(cls) -> Mapped["UserBase"]:
        return relationship(
            foreign_keys=[cls.deleted_by_id],
            doc="User that deleted the record",
        )
