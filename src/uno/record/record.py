# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from sqlalchemy import MetaData
from sqlalchemy.orm import registry, DeclarativeBase
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


class UnoRecord(AsyncAttrs, DeclarativeBase):
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
            str_26: VARCHAR(26),
            str_63: VARCHAR(63),
            str_128: VARCHAR(128),
            str_255: VARCHAR(255),
            decimal: NUMERIC,
        }
    )
    metadata = meta_data
