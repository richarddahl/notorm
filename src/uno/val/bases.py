# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
import decimal

from typing import ClassVar

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, ARRAY
from sqlalchemy.orm import relationship, mapped_column, Mapped

from uno.db import Base, str_26, str_63
from uno.sqlemitter import SQLEmitter
from uno.enums import (
    ComparisonOperator,
    graph_boolean_comparison_operators,
    graph_numeric_comparison_operators,
    graph_text_comparison_operators,
)
from uno.config import settings


class AttachmentMetaBase(GroupBaseMixin, BaseMixin, UnoBase):
    # __tablename__ = "attachment__meta_record"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "The relationship between attachments and meta_record objects",
    }
    display_name: ClassVar[str] = "Attachment MetaRecordBase"
    display_name_plural: ClassVar[str] = "Attachment RelatedObjects"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns

    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey("attachment.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
    )


class BooleanValue(MetaRecordBase):
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    comparison_operators: Mapped[list[ComparisonOperator]] = mapped_column(
        ARRAY(
            ENUM(
                ComparisonOperator,
                name="comparison_operator",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=graph_boolean_comparison_operators,
        doc="The comparison_operators for the value.",
    )
    boolean_value: Mapped[bool] = mapped_column(unique=True, index=True)


class DateTimeValue(
    MetaRecordBase,
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    comparison_operators: Mapped[list[ComparisonOperator]] = mapped_column(
        ARRAY(
            ENUM(
                ComparisonOperator,
                name="comparison_operator",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=graph_numeric_comparison_operators,
        doc="The comparison_operators for the value.",
    )
    datetime_value: Mapped[datetime_tz] = mapped_column(unique=True, index=True)


class DateValue(
    MetaRecordBase,
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    comparison_operators: Mapped[list[ComparisonOperator]] = mapped_column(
        ARRAY(
            ENUM(
                ComparisonOperator,
                name="comparison_operator",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=graph_numeric_comparison_operators,
        doc="The comparison_operators for the value.",
    )
    date_value: Mapped[date_] = mapped_column(unique=True, index=True)


class DecimalValue(
    MetaRecordBase,
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    comparison_operators: Mapped[list[ComparisonOperator]] = mapped_column(
        ARRAY(
            ENUM(
                ComparisonOperator,
                name="comparison_operator",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=graph_numeric_comparison_operators,
        doc="The comparison_operators for the value.",
    )
    decimal_value: Mapped[Decimal] = mapped_column(unique=True, index=True)


class IntegerValue(
    MetaRecordBase,
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    comparison_operators: Mapped[list[ComparisonOperator]] = mapped_column(
        ARRAY(
            ENUM(
                ComparisonOperator,
                name="comparison_operator",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=graph_numeric_comparison_operators,
        doc="The comparison_operators for the value.",
    )
    bigint_value: Mapped[int] = mapped_column(unique=True, index=True)


class TextValue(
    MetaRecordBase,
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    comparison_operators: Mapped[list[ComparisonOperator]] = mapped_column(
        ARRAY(
            ENUM(
                ComparisonOperator,
                name="comparison_operator",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=graph_text_comparison_operators,
        doc="The comparison_operators for the value.",
    )
    text_value: Mapped[str] = mapped_column(unique=True, index=True)


class TimeValue(
    MetaRecordBase,
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
    id: Mapped[str_26] = mapped_column(ForeignKey("meta_record.id"), primary_key=True)
    comparison_operators: Mapped[list[ComparisonOperator]] = mapped_column(
        ARRAY(
            ENUM(
                ComparisonOperator,
                name="comparison_operator",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        default=graph_numeric_comparison_operators,
        doc="The comparison_operators for the value.",
    )
    time_value: Mapped[time_] = mapped_column(unique=True, index=True)


class Attachment(
    MetaRecordBase,
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
        ForeignKey("meta_record.id"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str] = mapped_column(doc="Path to the file")

    # Relationships


class Method(
    MetaRecordBase,
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
        ForeignKey("meta_record.id"),
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


"""

This is something for Jeff to look at and see if it is useful and feasible, using sympy



class CalculationSymbol(
    MetaRecordBase,
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


class Calculation(
    MetaRecordBase,
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

"""
