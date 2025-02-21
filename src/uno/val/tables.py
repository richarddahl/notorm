# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import ClassVar, Optional
from decimal import Decimal

from sqlalchemy import ForeignKey, Identity
from sqlalchemy.dialects.postgresql import ENUM, ARRAY
from sqlalchemy.orm import relationship, mapped_column, Mapped

from uno.db.base import Base, str_26, str_255, str_list_255
from uno.db.tables import (
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
)
from uno.db.sql_emitters import SQLEmitter

from uno.val.enums import (
    Lookup,
    boolean_lookups,
    numeric_lookups,
    text_lookups,
    date_lookups,
)
from uno.config import settings


class AttachmentMeta(Base):
    __tablename__ = "attachment__meta"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "The relationship between attachments and meta objects",
    }
    display_name: ClassVar[str] = "Attachment MetaRecord"
    display_name_plural: ClassVar[str] = "Attachment RelatedObjects"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    include_in_graph = False

    # Columns
    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.attachment.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id", ondelete="CASCADE"),
        primary_key=True,
    )


class BooleanValue(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "boolean_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User defined boolean (True/False) values.",
        },
    )
    display_name: ClassVar[str] = "Boolean Value"
    display_name_plural: ClassVar[str] = "Boolean Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=boolean_lookups,
        doc="The lookups for the value.",
    )
    boolean_value: Mapped[bool] = mapped_column(unique=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "boolean_value",
        "inherit_condition": id == MetaRecord.id,
    }


class DateTimeValue(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "datetime_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User defined datetime values.",
        },
    )
    display_name: ClassVar[str] = "Datetime Value"
    display_name_plural: ClassVar[str] = "Datetime Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=date_lookups,
        doc="The lookups for the value.",
    )
    datetime_value: Mapped[datetime.datetime] = mapped_column(unique=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "datetime_value",
        "inherit_condition": id == MetaRecord.id,
    }


class DateValue(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "date_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User defined date values.",
        },
    )
    display_name: ClassVar[str] = "Date Value"
    display_name_plural: ClassVar[str] = "Date Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=date_lookups,
        doc="The lookups for the value.",
    )
    date_value: Mapped[datetime.date] = mapped_column(unique=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "date_value",
        "inherit_condition": id == MetaRecord.id,
    }


class DecimalValue(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "decimal_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User defined decimal values.",
        },
    )
    display_name: ClassVar[str] = "Decimal Value"
    display_name_plural: ClassVar[str] = "Decimal Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=numeric_lookups,
        doc="The lookups for the value.",
    )
    decimal_value: Mapped[Decimal] = mapped_column(unique=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "decimal_value",
        "inherit_condition": id == MetaRecord.id,
    }


class IntegerValue(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "integer_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User defined integer (whole number) values.",
        },
    )
    display_name: ClassVar[str] = "Integer Value"
    display_name_plural: ClassVar[str] = "Integer Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=numeric_lookups,
        doc="The lookups for the value.",
    )
    bigint_value: Mapped[int] = mapped_column(unique=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "integer_value",
        "inherit_condition": id == MetaRecord.id,
    }


class TextValue(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "text_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User defined values.",
        },
    )
    display_name: ClassVar[str] = "Text Value"
    display_name_plural: ClassVar[str] = "Text Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=text_lookups,
        doc="The lookups for the value.",
    )
    text_value: Mapped[str] = mapped_column(unique=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "text_value",
        "inherit_condition": id == MetaRecord.id,
    }


class TimeValue(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "time_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User defined time values.",
        },
    )
    display_name: ClassVar[str] = "Time Value"
    display_name_plural: ClassVar[str] = "Time Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=date_lookups,
        doc="The lookups for the value.",
    )
    time_value: Mapped[datetime.time] = mapped_column(unique=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "time_value",
        "inherit_condition": id == MetaRecord.id,
    }


class Attachment(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "attachment"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Files attached to db objects",
    }

    display_name: ClassVar[str] = "Attachment"
    display_name_plural: ClassVar[str] = "Attachments"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str] = mapped_column(doc="Path to the file")

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "attachment",
        "inherit_condition": id == MetaRecord.id,
    }


class Method(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "method"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Methods that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Object Function"
    display_name_plural: ClassVar[str] = "Object Functions"
    include_in_graph = False

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"),
        primary_key=True,
    )

    method_meta_type: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(doc="Label of the function")
    documentation: Mapped[str] = mapped_column(doc="Documentation of the function")
    accessor: Mapped[str] = mapped_column(doc="Name of the function")
    return_type: Mapped[str] = mapped_column(doc="Return type of the function")
    args: Mapped[str] = mapped_column(doc="Arguments of the function")
    kwargs: Mapped[str] = mapped_column(doc="Keyword arguments of the function")
    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "method",
        "inherit_condition": id == MetaRecord.id,
    }


"""

This is something for Jeff to look at and see if it is useful and feasible, using sympy



class CalculationSymbol(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "calculation_symbol"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Inputs to calculations that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Calculation Input"
    display_name_plural: ClassVar[str] = "Calculation Inputs"
    include_in_graph = False

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    symbol: Mapped[str] = mapped_column(doc="Symbol of the calculation")

    __mapper_args__ = {
        "polymorphic_identity": "calculation_symbol",
        "inherit_condition": id == MetaRecord.id,
    }


class Calculation(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
):
    __tablename__ = "calculation"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Calculations that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Calculation"
    display_name_plural: ClassVar[str] = "Calculations"
    include_in_graph = False

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)

    meta_type_name: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(doc="Name of the calculation.")
    documentation: Mapped[str] = mapped_column(doc="An Explanation of the calculation.")
    content: Mapped[str] = mapped_column(doc="Content of the calculation.")

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "calculation",
        "inherit_condition": id == MetaRecord.id,
    }

"""
