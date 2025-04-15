# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Database model definitions for the Uno framework.

This module provides base classes and type definitions for SQLAlchemy models
used within the Uno framework. It defines standardized column types and
a common base class with appropriate type annotations.
"""

import datetime
import decimal
import enum
from typing import Annotated, Any, Optional, Type, TypeVar

from sqlalchemy import MetaData
from sqlalchemy.orm import registry, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    BIGINT,
    TIMESTAMP,
    DATE,
    TIME,
    VARCHAR,
    ENUM,
    BOOLEAN,
    NUMERIC,
    INTERVAL,
    UUID,
    JSONB,
    BYTEA,
    TEXT,
)

from uno.settings import uno_settings


# Custom type definitions for common column types
# These make the type annotations more readable and maintainable
class PostgresTypes:
    """Common PostgreSQL column type definitions for use in models."""

    # String types with specific lengths
    String12 = Annotated[str, VARCHAR(12)]
    String26 = Annotated[str, VARCHAR(26)]
    String50 = Annotated[str, VARCHAR(50)]
    String63 = Annotated[str, VARCHAR(63)]
    String64 = Annotated[str, VARCHAR(64)]
    String100 = Annotated[str, VARCHAR(100)]
    String128 = Annotated[str, VARCHAR(128)]
    String255 = Annotated[str, VARCHAR(255)]
    Text = Annotated[str, TEXT]
    UUID = Annotated[str, UUID]

    # Numeric types
    BigInt = Annotated[int, BIGINT]
    Decimal = Annotated[decimal.Decimal, NUMERIC]

    # Boolean type
    Boolean = Annotated[bool, BOOLEAN]

    # Date and time types
    Timestamp = Annotated[datetime.datetime, TIMESTAMP(timezone=True)]
    Date = Annotated[datetime.date, DATE]
    Time = Annotated[datetime.time, TIME]
    Interval = Annotated[datetime.timedelta, INTERVAL]

    # Binary data
    ByteA = Annotated[bytes, BYTEA]

    # JSON data
    JSONB = Annotated[dict, JSONB]

    # Array type
    Array = Annotated[list, ARRAY]

    # Enum type
    StrEnum = Annotated[enum.StrEnum, ENUM]


class MetadataFactory:
    """Factory for creating SQLAlchemy metadata with consistent configuration."""

    @staticmethod
    def create_metadata(
        schema: Optional[str] = None, naming_convention: Optional[dict] = None
    ) -> MetaData:
        """
        Create a new SQLAlchemy metadata instance with the specified schema and naming convention.

        Args:
            schema: The database schema to use (defaults to the value from uno_settings)
            naming_convention: Naming convention for constraints and indexes

        Returns:
            A configured SQLAlchemy MetaData instance
        """
        # Default naming convention for PostgreSQL
        default_naming_convention = {
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s",
            "pk": "pk_%(table_name)s",
        }

        return MetaData(
            naming_convention=naming_convention or default_naming_convention,
            schema=schema or uno_settings.DB_SCHEMA,
        )


# Create the default metadata instance
default_metadata = MetadataFactory.create_metadata()

# Type variable for generic model classes
T = TypeVar("T", bound="UnoModel")


class UnoModel(AsyncAttrs, DeclarativeBase):
    """
    Base class for all database models in the Uno framework.

    This class provides common functionality and type mapping for SQLAlchemy models.
    All models should inherit from this class to ensure consistent behavior.
    """

    # Registry with type annotations mapping Python types to SQL types
    registry = registry(
        type_annotation_map={
            int: BIGINT,
            str: TEXT,
            enum.StrEnum: ENUM,
            bool: BOOLEAN,
            bytes: BYTEA,
            list: ARRAY,
            PostgresTypes.Timestamp: TIMESTAMP(timezone=True),
            PostgresTypes.Date: DATE,
            PostgresTypes.Time: TIME,
            PostgresTypes.Interval: INTERVAL,
            PostgresTypes.Decimal: NUMERIC,
            PostgresTypes.String12: VARCHAR(12),
            PostgresTypes.String26: VARCHAR(26),
            PostgresTypes.String50: VARCHAR(50),
            PostgresTypes.String63: VARCHAR(63),
            PostgresTypes.String64: VARCHAR(64),
            PostgresTypes.String100: VARCHAR(100),
            PostgresTypes.String128: VARCHAR(128),
            PostgresTypes.String255: VARCHAR(255),
            PostgresTypes.UUID: UUID,
            PostgresTypes.JSONB: JSONB,
        }
    )

    # Use the default metadata
    metadata = default_metadata

    @classmethod
    def with_custom_metadata(cls, metadata: MetaData) -> Type[T]:
        """
        Create a subclass of UnoModel with custom metadata.

        This is useful when models need to be mapped to different schemas.

        Args:
            metadata: The custom metadata to use

        Returns:
            A new UnoModel subclass with the specified metadata
        """
        return type(f"{cls.__name__}WithCustomMetadata", (cls,), {"metadata": metadata})
