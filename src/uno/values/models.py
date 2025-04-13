# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import (
    ForeignKey,
    Index,
    UniqueConstraint,
    Table,
    Column,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import VARCHAR, ARRAY

from uno.model import UnoModel, PostgresTypes
from uno.authorization.mixins import DefaultModelMixin
from uno.queries.filter import (
    boolean_lookups,
    numeric_lookups,
    text_lookups,
    datetime_lookups,
)


attachment__meta_record = Table(
    "attachment__meta_record",
    UnoModel.metadata,
    Column(
        "attachment_id",
        VARCHAR(26),
        ForeignKey("attachment.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "META_RECORDS"},
    ),
    Column(
        "meta_record_id",
        VARCHAR(26),
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "ATTACHMENTS"},
    ),
    Index(
        "ix_attachment__meta_record_attachment_id_meta_record_id",
        "attachment_id",
        "meta_record_id",
    ),
)


class AttachmentModel(DefaultModelMixin, UnoModel):
    __tablename__ = "attachment"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "file_path", name="uq_attachment_tenant_id_file_path"
        ),
        Index("ix_attachment_tenant_id_file_path", "tenant_id", "file_path"),
        {"comment": "User defined file attachments."},
    )
    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=text_lookups,
        doc="The lookups for the value.",
    )
    name: Mapped[PostgresTypes.String255] = mapped_column(doc="Name of the file")
    file_path: Mapped[str] = mapped_column(doc="Path to the file")

    # Relationships


class BooleanValueModel(DefaultModelMixin, UnoModel):
    __tablename__ = "boolean_value"
    __table_args__ = (
        UniqueConstraint("tenant_id", "value", name="uq_boolean_value_tenant_id_value"),
        Index("ix_boolean_value_tenant_id_value", "tenant_id", "value"),
        {"comment": "User defined boolean (True/False) values."},
    )

    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=boolean_lookups,
        doc="The lookups for the value.",
    )
    value: Mapped[bool] = mapped_column(
        doc="The boolean value.",
    )


class DateTimeValueModel(DefaultModelMixin, UnoModel):
    __tablename__ = "datetime_value"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "value", name="uq_datetime_value_tenant_id_value"
        ),
        Index("ix_datetime_value_tenant_id_value", "tenant_id", "value"),
        {"comment": "User defined datetime values."},
    )

    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=datetime_lookups,
        doc="The lookups for the value.",
    )
    value: Mapped[PostgresTypes.Timestamp] = mapped_column(doc="The datetime value.")


class DateValueModel(DefaultModelMixin, UnoModel):
    __tablename__ = "date_value"
    __table_args__ = (
        UniqueConstraint("tenant_id", "value", name="uq_date_value_tenant_id_value"),
        Index("ix_date_value_tenant_id_value", "tenant_id", "value"),
        {"comment": "User defined date values."},
    )

    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=datetime_lookups,
        doc="The lookups for the value.",
    )
    value: Mapped[PostgresTypes.Date] = mapped_column(doc="The date value.")


class DecimalValueModel(DefaultModelMixin, UnoModel):
    __tablename__ = "decimal_value"
    __table_args__ = (
        UniqueConstraint("tenant_id", "value", name="uq_decimal_value_tenant_id_value"),
        Index("ix_decimal_value_tenant_id_value", "tenant_id", "value"),
        {"comment": "User defined decimal values."},
    )

    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=numeric_lookups,
        doc="The lookups for the value.",
    )
    value: Mapped[PostgresTypes.Decimal] = mapped_column(doc="The decimal value.")


class IntegerValueModel(DefaultModelMixin, UnoModel):
    __tablename__ = "integer_value"
    __table_args__ = (
        UniqueConstraint("tenant_id", "value", name="uq_integer_value_tenant_id_value"),
        Index("ix_integer_value_tenant_id_value", "tenant_id", "value"),
        {"comment": "User defined integer (whole number) values."},
    )

    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=numeric_lookups,
        doc="The lookups for the value.",
    )
    value: Mapped[int] = mapped_column()


class TextValueModel(DefaultModelMixin, UnoModel):
    __tablename__ = "text_value"
    __table_args__ = (
        UniqueConstraint("tenant_id", "value", name="uq_text_value_tenant_id_value"),
        Index("ix_text_value_tenant_id_value", "tenant_id", "value"),
        {"comment": "User defined text values."},
    )

    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=text_lookups,
        doc="The lookups for the value.",
    )
    value: Mapped[str] = mapped_column()


class TimeValueModel(DefaultModelMixin, UnoModel):
    __tablename__ = "time_value"
    __table_args__ = (
        UniqueConstraint("tenant_id", "value", name="uq_time_value_tenant_id_value"),
        Index("ix_time_value_tenant_id_value", "tenant_id", "value"),
        {"comment": "User defined time values."},
    )

    # Columns
    lookups: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(12)),
        default=datetime_lookups,
        doc="The lookups for the value.",
    )
    value: Mapped[PostgresTypes.Time] = mapped_column()


"""
class Method(
):
    __tablename__ = "method"
    __table_args__ = {
        "comment": "Methods that can be used in attributes, workflows, and reports",
    }

    # Columns
    id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("meta_record.id"),
        primary_key=True,
    )

    method_meta_type: Mapped[PostgresTypes.String26] = mapped_column(
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



This is something for Jeff to look at and see if it is useful and feasible, using sympy



class CalculationSymbol(
    MetaRecordModel,
    MetaModelMixin,
    ModelAuditMixin,
    ModelVersionAuditMixin,
):
    #__tablename__ = "calculation_symbol"
    __table_args__ = {
        "schema": uno_settings.DB_SCHEMA,
        "comment": "Inputs to calculations that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Calculation Input"
    display_name_plural: ClassVar[str] = "Calculation Inputs"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    symbol: Mapped[str] = mapped_column(doc="Symbol of the calculation")


class Calculation(
    MetaRecordModel,
    MetaModelMixin,
    ModelAuditMixin,
    ModelVersionAuditMixin,
):
    #__tablename__ = "calculation"
    __table_args__ = {
        "schema": uno_settings.DB_SCHEMA,
        "comment": "Calculations that can be used in attributes, workflows, and reports",
    }
    display_name: ClassVar[str] = "Calculation"
    display_name_plural: ClassVar[str] = "Calculations"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)

    meta_type_id: Mapped[PostgresTypes.String63] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(doc="Name of the calculation.")
    documentation: Mapped[str] = mapped_column(doc="An Explanation of the calculation.")
    content: Mapped[str] = mapped_column(doc="Content of the calculation.")

    # Relationships

"""
