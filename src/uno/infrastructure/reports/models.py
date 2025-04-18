# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, Any, List
from datetime import datetime, UTC

from sqlalchemy import (
    ForeignKey,
    Index,
    UniqueConstraint,
    Table,
    Column,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM, ARRAY, VARCHAR, JSONB

from uno.domain.base.model import BaseModel, PostgresTypes
from uno.authorization.mixins import DefaultModelMixin
from uno.enums import ValueType
from uno.settings import uno_settings


# Junction table for report templates and report field definitions
report_template__field = Table(
    "report_template__field",
    BaseModel.metadata,
    Column(
        "report_template_id",
        ForeignKey("report_template.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "FIELDS"},
    ),
    Column(
        "report_field_definition_id",
        ForeignKey("report_field_definition.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "TEMPLATES"},
    ),
    Index(
        "ix_report_template_id__field_id",
        "report_template_id",
        "report_field_definition_id",
    ),
)


# Enum for report field types
class ReportFieldType(str):
    """Types of report fields."""

    DB_COLUMN = "db_column"
    ATTRIBUTE = "attribute"
    METHOD = "method"
    QUERY = "query"
    AGGREGATE = "aggregate"
    RELATED = "related"
    CUSTOM = "custom"


# Enum for report trigger types
class ReportTriggerType(str):
    """Types of report triggers."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    QUERY = "query"


# Enum for report output types
class ReportOutputType(str):
    """Types of report outputs."""

    FILE = "file"
    EMAIL = "email"
    WEBHOOK = "webhook"
    NOTIFICATION = "notification"


# Enum for report formats
class ReportFormat(str):
    """Report output formats."""

    CSV = "csv"
    PDF = "pdf"
    JSON = "json"
    HTML = "html"
    EXCEL = "excel"
    TEXT = "text"


# Enum for report execution status
class ReportExecutionStatus(str):
    """Status of report execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ReportFieldConfigModel(DefaultModelMixin, BaseModel):
    __tablename__ = "report_field_config"
    __table_args__ = {"comment": "Configuration of fields in a report"}

    # Columns
    report_field_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_field.id", ondelete="CASCADE"),
        doc="The report field",
        info={"edge": "REPORT_FIELD", "reverse_edge": "REPORT_FIELD_CONFIGS"},
    )
    report_type_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_type.id", ondelete="CASCADE"),
        doc="The report type",
        info={"edge": "REPORT_TYPE", "reverse_edge": "REPORT_FIELD_CONFIGS"},
    )
    parent_field_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("report_field.id", ondelete="CASCADE"),
        doc="The parent field for this field",
        info={"edge": "PARENT_FIELD", "reverse_edge": "CHILD_FIELDS"},
    )
    is_label_included: Mapped[bool] = mapped_column(
        doc="Whether the label for this field is included in the report",
    )
    field_format: Mapped[Optional[str]] = mapped_column(
        doc="Format for the field in the report",
    )


class ReportFieldModel(DefaultModelMixin, BaseModel):
    __tablename__ = "report_field"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name"),
        Index("ix_report_field_tenant_id_name", "tenant_id", "name"),
        {"comment": "Fields that can be included in reports"},
    )

    # Columns
    field_meta_type: Mapped[PostgresTypes.String255] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        doc="The meta_record type of the report field",
        info={"edge": "META_TYPE", "reverse_edge": "REPORT_FIELDS"},
    )
    field_type: Mapped[str] = mapped_column(
        VARCHAR(50),
        doc="The type of the report field",
    )
    name: Mapped[Optional[PostgresTypes.String255]] = mapped_column(
        doc="The name of the report field."
    )
    explanation: Mapped[str] = mapped_column(
        doc="Explanation of the report field",
    )


class ReportTypeModel(DefaultModelMixin, BaseModel):
    __tablename__ = "report_type"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name"),
        Index("ix_report_type_tenant_id_name", "tenant_id", "name"),
        Index("ix_report_type_meta_type", "meta_type"),
        {"comment": "The types of reports that can be generated"},
    )

    # Columns
    meta_type: Mapped[PostgresTypes.String255] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        doc="The meta_record type of the report",
        info={"edge": "META_TYPE", "reverse_edge": "REPORT_TYPES"},
    )
    name: Mapped[PostgresTypes.String128] = mapped_column(
        doc="The name of the report type",
    )
    description: Mapped[str] = mapped_column(
        doc="Description of the report type",
    )


class ReportModel(DefaultModelMixin, BaseModel):
    __tablename__ = "report"
    __table_args__ = {"comment": "Reports generated by the system"}

    # Columns
    name: Mapped[PostgresTypes.String255] = mapped_column(
        doc="Name of the report",
    )
    report_type: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_type.id", ondelete="CASCADE"),
        doc="The type of the report",
        info={"edge": "REPORT_TYPE", "reverse_edge": "REPORTS"},
    )
    data: Mapped[PostgresTypes.ByteA] = mapped_column(
        doc="Data for the report",
    )
    data_hash: Mapped[PostgresTypes.String64] = mapped_column(
        doc="Hash of the data for the report",
    )


# Enhanced models for the new reporting system


class ReportTemplateModel(DefaultModelMixin, BaseModel):
    """Defines the structure and behavior of a report."""

    __tablename__ = "report_template"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name"),
        Index("ix_report_template_tenant_id_name", "tenant_id", "name"),
        {"comment": "Defines the structure and behavior of a report"},
    )

    # Basic information
    name: Mapped[PostgresTypes.String255] = mapped_column(
        doc="Name of the report template"
    )
    description: Mapped[str] = mapped_column(doc="Description of the report template")

    # Configuration
    base_object_type: Mapped[str] = mapped_column(
        doc="What type of entity this report is based on"
    )
    format_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="JSON configuration for output format"
    )
    parameter_definitions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="User parameters the report accepts"
    )
    cache_policy: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="How report results are cached"
    )
    version: Mapped[str] = mapped_column(default="1.0.0", doc="For template versioning")

    # Relationships
    fields: Mapped[List["ReportFieldDefinitionModel"]] = relationship(
        secondary=report_template__field,
        back_populates="templates",
        doc="Fields in this report template",
    )
    triggers: Mapped[List["ReportTriggerModel"]] = relationship(
        back_populates="report_template",
        cascade="all, delete-orphan",
        doc="Triggers for this report template",
    )
    outputs: Mapped[List["ReportOutputModel"]] = relationship(
        back_populates="report_template",
        cascade="all, delete-orphan",
        doc="Output configurations for this report template",
    )
    executions: Mapped[List["ReportExecutionModel"]] = relationship(
        back_populates="report_template",
        cascade="all, delete-orphan",
        doc="Execution records for this report template",
    )


class ReportFieldDefinitionModel(DefaultModelMixin, BaseModel):
    """Defines a field within a report template."""

    __tablename__ = "report_field_definition"
    __table_args__ = (
        Index("ix_report_field_def_type", "field_type"),
        {"comment": "Defines a field within a report template"},
    )

    # Field identification
    name: Mapped[PostgresTypes.String255] = mapped_column(
        doc="Internal name of the field"
    )
    display: Mapped[str] = mapped_column(doc="Display for the field")
    description: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Description of the field"
    )

    # Field configuration
    field_type: Mapped[str] = mapped_column(
        VARCHAR(50),
        doc="Type of field (db_column, attribute, method, query, aggregate, etc.)",
    )
    field_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="Configuration specific to field_type"
    )

    # Presentation
    order: Mapped[int] = mapped_column(default=0, doc="Display order of the field")
    format_string: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Format string for the field value"
    )
    conditional_formats: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, doc="Conditional formatting rules"
    )
    is_visible: Mapped[bool] = mapped_column(
        default=True, doc="Whether the field is visible in the report"
    )

    # Relations
    parent_field_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("report_field_definition.id", ondelete="CASCADE"),
        nullable=True,
        doc="Parent field ID for nested fields",
        info={"edge": "PARENT_FIELD", "reverse_edge": "CHILD_FIELDS"},
    )
    parent_field: Mapped[Optional["ReportFieldDefinitionModel"]] = relationship(
        "ReportFieldDefinitionModel",
        remote_side="ReportFieldDefinitionModel.id",
        foreign_keys=[parent_field_id],
        backref="child_fields",
        doc="Parent field for nested fields",
    )
    templates: Mapped[List[ReportTemplateModel]] = relationship(
        secondary=report_template__field,
        back_populates="fields",
        doc="Report templates using this field",
    )


class ReportTriggerModel(DefaultModelMixin, BaseModel):
    """Defines when a report should be generated."""

    __tablename__ = "report_trigger"
    __table_args__ = (
        Index("ix_report_trigger_type", "trigger_type"),
        {"comment": "Defines when a report should be generated"},
    )

    # Trigger configuration
    report_template_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_template.id", ondelete="CASCADE"),
        doc="The report template this trigger belongs to",
        info={"edge": "REPORT_TEMPLATE", "reverse_edge": "TRIGGERS"},
    )
    trigger_type: Mapped[str] = mapped_column(
        VARCHAR(50), doc="Type of trigger (manual, scheduled, event, query)"
    )
    trigger_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="Configuration specific to trigger_type"
    )

    # For scheduled triggers
    schedule: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Cron-style schedule expression"
    )

    # For event triggers
    event_type: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Type of event that triggers the report"
    )
    entity_type: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Type of entity involved in the event"
    )

    # For query triggers
    query_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
        ForeignKey("query.id", ondelete="SET NULL"),
        nullable=True,
        doc="ID of the query that triggers the report",
        info={"edge": "QUERY", "reverse_edge": "REPORT_TRIGGERS"},
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True, doc="Whether this trigger is active"
    )
    last_triggered: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, doc="When this trigger was last activated"
    )

    # Relations
    report_template: Mapped[ReportTemplateModel] = relationship(
        ReportTemplateModel,
        back_populates="triggers",
        doc="The report template this trigger belongs to",
    )


class ReportOutputModel(DefaultModelMixin, BaseModel):
    """Defines how report results should be delivered."""

    __tablename__ = "report_output"
    __table_args__ = (
        Index("ix_report_output_type", "output_type"),
        {"comment": "Defines how report results should be delivered"},
    )

    # Output configuration
    report_template_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_template.id", ondelete="CASCADE"),
        doc="The report template this output belongs to",
        info={"edge": "REPORT_TEMPLATE", "reverse_edge": "OUTPUTS"},
    )
    output_type: Mapped[str] = mapped_column(
        VARCHAR(50), doc="Type of output (file, email, webhook, notification)"
    )
    output_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="Configuration specific to output_type"
    )

    # Format
    format: Mapped[str] = mapped_column(
        VARCHAR(50), doc="Format of the output (csv, pdf, json, html, excel, text)"
    )
    format_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="Configuration specific to format"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True, doc="Whether this output is active"
    )

    # Relations
    report_template: Mapped[ReportTemplateModel] = relationship(
        ReportTemplateModel,
        back_populates="outputs",
        doc="The report template this output belongs to",
    )
    output_executions: Mapped[List["ReportOutputExecutionModel"]] = relationship(
        back_populates="report_output",
        cascade="all, delete-orphan",
        doc="Execution records for this output",
    )


class ReportExecutionModel(DefaultModelMixin, BaseModel):
    """Records of report generation executions."""

    __tablename__ = "report_execution"
    __table_args__ = (
        Index("ix_report_execution_status", "status"),
        Index("ix_report_execution_started_at", "started_at"),
        {"comment": "Records of report generation executions"},
    )

    # Execution details
    report_template_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_template.id", ondelete="CASCADE"),
        doc="The report template that was executed",
        info={"edge": "REPORT_TEMPLATE", "reverse_edge": "EXECUTIONS"},
    )
    triggered_by: Mapped[str] = mapped_column(
        doc="ID of trigger or user that initiated execution"
    )
    trigger_type: Mapped[str] = mapped_column(
        VARCHAR(50), doc="Type of trigger that initiated execution"
    )

    # Parameters provided
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default={}, doc="Parameters provided for this execution"
    )

    # Execution status
    status: Mapped[str] = mapped_column(
        VARCHAR(50),
        default=ReportExecutionStatus.PENDING,
        doc="Status of the execution",
    )
    started_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(datetime.UTC), doc="When execution started"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, doc="When execution completed"
    )
    error_details: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Error details if execution failed"
    )

    # Result
    row_count: Mapped[Optional[int]] = mapped_column(
        nullable=True, doc="Number of rows in the result"
    )
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        nullable=True, doc="Execution time in milliseconds"
    )
    result_hash: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Hash of the result data for caching"
    )

    # Relations
    report_template: Mapped[ReportTemplateModel] = relationship(
        ReportTemplateModel,
        back_populates="executions",
        doc="The report template that was executed",
    )
    output_executions: Mapped[List["ReportOutputExecutionModel"]] = relationship(
        back_populates="report_execution",
        cascade="all, delete-orphan",
        doc="Output delivery records for this execution",
    )


class ReportOutputExecutionModel(DefaultModelMixin, BaseModel):
    """Records of report output delivery."""

    __tablename__ = "report_output_execution"
    __table_args__ = (
        Index("ix_report_output_execution_status", "status"),
        {"comment": "Records of report output delivery"},
    )

    # Execution reference
    report_execution_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_execution.id", ondelete="CASCADE"),
        doc="The report execution this output delivery is for",
        info={"edge": "REPORT_EXECUTION", "reverse_edge": "OUTPUT_EXECUTIONS"},
    )
    report_output_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("report_output.id", ondelete="CASCADE"),
        doc="The report output configuration used",
        info={"edge": "REPORT_OUTPUT", "reverse_edge": "OUTPUT_EXECUTIONS"},
    )

    # Output status
    status: Mapped[str] = mapped_column(
        VARCHAR(50),
        default=ReportExecutionStatus.PENDING,
        doc="Status of the output delivery",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, doc="When output delivery completed"
    )
    error_details: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Error details if output delivery failed"
    )

    # Result details
    output_location: Mapped[Optional[str]] = mapped_column(
        nullable=True, doc="Location of the output (URL, file path, etc.)"
    )
    output_size_bytes: Mapped[Optional[int]] = mapped_column(
        nullable=True, doc="Size of the output in bytes"
    )

    # Relations
    report_execution: Mapped[ReportExecutionModel] = relationship(
        ReportExecutionModel,
        back_populates="output_executions",
        doc="The report execution this output delivery is for",
    )
    report_output: Mapped[ReportOutputModel] = relationship(
        ReportOutputModel,
        back_populates="output_executions",
        doc="The report output configuration used",
    )
