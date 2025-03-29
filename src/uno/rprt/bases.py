# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar, Optional


from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import ENUM

from uno.db import Base, str_26, str_64, str_255, bytea
from uno.meta.bases import (
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
)
from uno.sqlemitter import SQLEmitter
from uno.enums import ValueType
from uno.config import settings


class ReportTypeReportField(RBACBaseMixin, BaseMixin, UnoBase):
    # __tablename__ = "report_type__report_field"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The relationship between report_types and their fields",
        },
    )

    display_name: ClassVar[str] = "Report Type Field"
    display_name_plural: ClassVar[str] = "Report Type Fields"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    report_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("report_type.id", ondelete="CASCADE"),
        primary_key=True,
    )
    report_field_id: Mapped[str_26] = mapped_column(
        ForeignKey("report_field.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ReportField(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "report_field"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Fields that can be included in reports",
        },
    )

    display_name: ClassVar[str] = "Report Field"
    display_name_plural: ClassVar[str] = "Report Fields"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id"),
        primary_key=True,
    )
    field_meta_type: Mapped[str_255] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        doc="The meta_record type of the report field",
    )
    field_type: Mapped[ValueType] = mapped_column(
        ENUM(
            ValueType,
            name="report_field_type",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        doc="The type of the report field",
    )
    label: Mapped[Optional[str_255]] = mapped_column(
        doc="The label for the report field displayed on the report",
    )
    explanation: Mapped[str] = mapped_column(
        doc="Explanation of the report field",
    )

    __mapper_args__ = {
        "polymorphic_identity": "report_field",
        "inherit_condition": id == MetaBase.id,
    }


class ReportType(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "report_type"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The types of reports that can be generated",
        },
    )

    display_name: ClassVar[str] = "Report Type"
    display_name_plural: ClassVar[str] = "Report Types"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id"),
        primary_key=True,
    )
    applicable_meta_type: Mapped[str_255] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        doc="The meta_record type of the report",
    )
    explanation: Mapped[str] = mapped_column(
        doc="Explanation of the report type",
    )

    __mapper_args__ = {
        "polymorphic_identity": "report_type",
        "inherit_condition": id == MetaBase.id,
    }


class Report(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    BaseVersionAuditMixin,
):
    # __tablename__ = "report"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Reports generated by the system",
        },
    )

    display_name: ClassVar[str] = "Report"
    display_name_plural: ClassVar[str] = "Reports"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id"),
        primary_key=True,
    )
    name: Mapped[str_255] = mapped_column(
        doc="Name of the report",
    )
    report_type: Mapped[str_26] = mapped_column(
        ForeignKey("report_type.id", ondelete="CASCADE"),
        doc="The type of the report",
    )
    data: Mapped[bytea] = mapped_column(
        doc="Data for the report",
    )
    data_hash: Mapped[str_64] = mapped_column(
        doc="Hash of the data for the report",
    )
    __mapper_args__ = {
        "polymorphic_identity": "report",
        "inherit_condition": id == MetaBase.id,
    }

    def insert_schema(self):
        """Create the BaseModel used for the report"""
        pass
