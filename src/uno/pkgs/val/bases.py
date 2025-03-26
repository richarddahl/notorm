# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import ClassVar
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, ARRAY
from sqlalchemy.orm import relationship, mapped_column, Mapped

from uno.db.obj import Base, str_26, str_63
from uno.pkgs.meta.bases import (
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
)
from uno.db.sql.sqlemitter import SQLEmitter

from uno.pkgs.val.enums import (
    Lookup,
    boolean_lookups,
    numeric_lookups,
    text_lookups,
    date_lookups,
)
from uno.config import settings


class AttachmentMetaBase(Base):
    # __tablename__ = "attachment__meta_record"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "The relationship between attachments and meta_record objects",
    }
    display_name: ClassVar[str] = "Attachment MetaBase"
    display_name_plural: ClassVar[str] = "Attachment RelatedObjects"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns

    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey("attachment.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
    )


class BooleanValue(MetaBase):
    # __tablename__ = "boolean_value"
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta.id"), primary_key=True)
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
        "inherit_condition": id == MetaBase.id,
    }


class DateTimeValue(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "datetime_value"
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta.id"), primary_key=True)
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
        "inherit_condition": id == MetaBase.id,
    }


class DateValue(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "date_value"
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta.id"), primary_key=True)
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
        "inherit_condition": id == MetaBase.id,
    }


class DecimalValue(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "decimal_value"
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta.id"), primary_key=True)
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
        "inherit_condition": id == MetaBase.id,
    }


class IntegerValue(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "integer_value"
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta.id"), primary_key=True)
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
        "inherit_condition": id == MetaBase.id,
    }


class TextValue(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "text_value"
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta.id"), primary_key=True)
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
        "inherit_condition": id == MetaBase.id,
    }


class TimeValue(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "time_value"
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta.id"), primary_key=True)
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
        "inherit_condition": id == MetaBase.id,
    }


class Attachment(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "attachment"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Files attached to db objects",
    }

    display_name: ClassVar[str] = "Attachment"
    display_name_plural: ClassVar[str] = "Attachments"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str] = mapped_column(doc="Path to the file")

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "attachment",
        "inherit_condition": id == MetaBase.id,
    }


class Method(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "method"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Methods that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Object Function"
    display_name_plural: ClassVar[str] = "Object Functions"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id"),
        primary_key=True,
    )

    method_meta_type: Mapped[str_26] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
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
        "inherit_condition": id == MetaBase.id,
    }


"""

This is something for Jeff to look at and see if it is useful and feasible, using sympy



class CalculationSymbol(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    #__tablename__ = "calculation_symbol"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Inputs to calculations that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Calculation Input"
    display_name_plural: ClassVar[str] = "Calculation Inputs"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    symbol: Mapped[str] = mapped_column(doc="Symbol of the calculation")

    __mapper_args__ = {
        "polymorphic_identity": "calculation_symbol",
        "inherit_condition": id == MetaBase.id,
    }


class Calculation(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    #__tablename__ = "calculation"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Calculations that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Calculation"
    display_name_plural: ClassVar[str] = "Calculations"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)

    meta_type_id: Mapped[str_63] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(doc="Name of the calculation.")
    documentation: Mapped[str] = mapped_column(doc="An Explanation of the calculation.")
    content: Mapped[str] = mapped_column(doc="Content of the calculation.")

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "calculation",
        "inherit_condition": id == MetaBase.id,
    }

"""
