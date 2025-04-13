# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List, Dict, Any
from typing_extensions import Self
from datetime import datetime
from pydantic import model_validator, field_validator, ConfigDict

from uno.schema.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.authorization.mixins import DefaultObjectMixin
from uno.meta.objs import MetaType
from uno.reports.models import (
    # Original models
    ReportFieldConfigModel,
    ReportFieldModel,
    ReportTypeModel,
    ReportModel,
    # Enhanced models
    ReportTemplateModel,
    ReportFieldDefinitionModel,
    ReportTriggerModel,
    ReportOutputModel,
    ReportExecutionModel,
    ReportOutputExecutionModel,
    # Enums
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
)


# Original classes (for backward compatibility)

class ReportFieldConfig(UnoObj[ReportFieldConfigModel], DefaultObjectMixin):
    # Class variables
    model = ReportFieldConfigModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "report_field",
                "report_type",
                "parent_field",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "report_field_id",
                "report_type_id",
                "parent_field_id",
                "is_label_included",
                "field_format",
            ],
        ),
    }

    # Fields
    report_field_id: str
    report_field: "ReportField"
    report_type_id: str
    report_type: "ReportType"
    parent_field_id: Optional[str] = None
    parent_field: Optional["ReportField"] = None
    is_label_included: bool
    field_format: str

    def __str__(self) -> str:
        return f"{self.report_field.name} config"


class ReportField(UnoObj[ReportFieldModel], DefaultObjectMixin):
    # Class variables
    model = ReportFieldModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "field_meta_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "field_meta_type_id",
                "field_type",
                "name",
                "description",
            ],
        ),
    }

    # Fields
    field_meta_type_id: str
    field_meta_type: Optional[MetaType] = None
    field_type: str
    name: str
    description: Optional[str] = None

    def __str__(self) -> str:
        return self.name

    @model_validator(mode="after")
    def validate_field(self) -> Self:
        # Validate field_type is one of the allowed types
        allowed_types = ["string", "number", "boolean", "date", "object", "array"]
        if self.field_type not in allowed_types:
            raise ValueError(f"Field type must be one of: {', '.join(allowed_types)}")

        return self


class ReportType(UnoObj[ReportTypeModel], DefaultObjectMixin):
    # Class variables
    model = ReportTypeModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "report_fields",
                "report_field_configs",
                "report_type_configs",
                "report_type_field_configs",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
            ],
        ),
    }

    # Fields
    name: str
    description: Optional[str] = None
    report_fields: List[ReportField] = []
    report_field_configs: List[ReportFieldConfig] = []
    report_type_configs: List[ReportFieldConfig] = []
    report_type_field_configs: List[ReportFieldConfig] = []

    def __str__(self) -> str:
        return self.name


class Report(UnoObj[ReportModel], DefaultObjectMixin):
    # Class variables
    model = ReportModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "report_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "report_type_id",
            ],
        ),
    }

    # Fields
    name: str
    description: Optional[str] = None
    report_type_id: str
    report_type: Optional[ReportType] = None

    def __str__(self) -> str:
        return self.name


# Enhanced classes for the new reporting system

class ReportFieldDefinition(UnoObj[ReportFieldDefinitionModel], DefaultObjectMixin):
    """A field definition for a report template."""

    # Class variables
    model = ReportFieldDefinitionModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "display_name",
                "description",
                "field_type",
                "field_config",
                "order",
                "format_string",
                "conditional_formats",
                "is_visible",
                "parent_field_id",
            ],
        ),
    }

    # Fields
    name: str
    display_name: str
    description: Optional[str] = None
    field_type: str  # DB_COLUMN, ATTRIBUTE, METHOD, QUERY, AGGREGATE, RELATED, CUSTOM
    field_config: Dict[str, Any] = {}
    order: int = 0
    format_string: Optional[str] = None
    conditional_formats: Optional[Dict[str, Any]] = None
    is_visible: bool = True
    parent_field_id: Optional[str] = None
    parent_field: Optional["ReportFieldDefinition"] = None
    child_fields: List["ReportFieldDefinition"] = []
    templates: List["ReportTemplate"] = []

    model_config = ConfigDict(
        extra="allow"
    )

    def __str__(self) -> str:
        return self.display_name

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, field_type: str) -> str:
        """Validate field_type is one of the defined types."""
        allowed_types = [t.value for t in ReportFieldType]
        if field_type not in allowed_types:
            raise ValueError(f"Field type must be one of: {', '.join(allowed_types)}")
        return field_type

    @model_validator(mode="after")
    def validate_field_config(self) -> Self:
        """Validate field_config is appropriate for the field_type."""
        # Different field types require different config properties
        if self.field_type == ReportFieldType.DB_COLUMN:
            required_props = ["table", "column"]
            for prop in required_props:
                if prop not in self.field_config:
                    raise ValueError(f"Field config for DB_COLUMN must include {prop}")
        
        elif self.field_type == ReportFieldType.ATTRIBUTE:
            if "attribute_type_id" not in self.field_config:
                raise ValueError("Field config for ATTRIBUTE must include attribute_type_id")
        
        elif self.field_type == ReportFieldType.METHOD:
            required_props = ["method", "module"]
            for prop in required_props:
                if prop not in self.field_config:
                    raise ValueError(f"Field config for METHOD must include {prop}")
        
        elif self.field_type == ReportFieldType.QUERY:
            if "query_id" not in self.field_config:
                raise ValueError("Field config for QUERY must include query_id")
        
        elif self.field_type == ReportFieldType.AGGREGATE:
            required_props = ["function", "field"]
            for prop in required_props:
                if prop not in self.field_config:
                    raise ValueError(f"Field config for AGGREGATE must include {prop}")
        
        elif self.field_type == ReportFieldType.RELATED:
            required_props = ["relation", "field"]
            for prop in required_props:
                if prop not in self.field_config:
                    raise ValueError(f"Field config for RELATED must include {prop}")
        
        return self


class ReportTemplate(UnoObj[ReportTemplateModel], DefaultObjectMixin):
    """A template defining a report's structure and behavior."""

    # Class variables
    model = ReportTemplateModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "base_object_type",
                "format_config",
                "parameter_definitions",
                "cache_policy",
                "version",
            ],
        ),
    }

    # Fields
    name: str
    description: str
    base_object_type: str
    format_config: Dict[str, Any] = {}
    parameter_definitions: Dict[str, Any] = {}
    cache_policy: Dict[str, Any] = {}
    version: str = "1.0.0"
    fields: List[ReportFieldDefinition] = []
    triggers: List["ReportTrigger"] = []
    outputs: List["ReportOutput"] = []
    executions: List["ReportExecution"] = []

    model_config = ConfigDict(
        extra="allow"
    )

    def __str__(self) -> str:
        return self.name

    @model_validator(mode="after")
    def validate_template(self) -> Self:
        """Validate the report template."""
        # Ensure parameter definitions are valid
        for param_name, param_def in self.parameter_definitions.items():
            if not isinstance(param_def, dict):
                raise ValueError(f"Parameter definition for {param_name} must be a dictionary")
            if "type" not in param_def:
                raise ValueError(f"Parameter definition for {param_name} must include a type")
        
        return self


class ReportTrigger(UnoObj[ReportTriggerModel], DefaultObjectMixin):
    """Defines when a report should be generated."""

    # Class variables
    model = ReportTriggerModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "report_template_id",
                "trigger_type",
                "trigger_config",
                "schedule",
                "event_type",
                "entity_type",
                "query_id",
                "is_active",
            ],
        ),
    }

    # Fields
    report_template_id: str
    report_template: Optional[ReportTemplate] = None
    trigger_type: str  # MANUAL, SCHEDULED, EVENT, QUERY
    trigger_config: Dict[str, Any] = {}
    schedule: Optional[str] = None
    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    query_id: Optional[str] = None
    is_active: bool = True
    last_triggered: Optional[datetime] = None

    model_config = ConfigDict(
        extra="allow"
    )

    def __str__(self) -> str:
        return f"{self.trigger_type} trigger for {self.report_template_id}"

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, trigger_type: str) -> str:
        """Validate trigger_type is one of the defined types."""
        allowed_types = [t.value for t in ReportTriggerType]
        if trigger_type not in allowed_types:
            raise ValueError(f"Trigger type must be one of: {', '.join(allowed_types)}")
        return trigger_type

    @model_validator(mode="after")
    def validate_trigger(self) -> Self:
        """Validate the trigger configuration based on type."""
        if self.trigger_type == ReportTriggerType.SCHEDULED:
            if not self.schedule:
                raise ValueError("Scheduled triggers must include a schedule")
        
        elif self.trigger_type == ReportTriggerType.EVENT:
            if not self.event_type:
                raise ValueError("Event triggers must include an event_type")
        
        elif self.trigger_type == ReportTriggerType.QUERY:
            if not self.query_id:
                raise ValueError("Query triggers must include a query_id")
        
        return self


class ReportOutput(UnoObj[ReportOutputModel], DefaultObjectMixin):
    """Defines how report results should be delivered."""

    # Class variables
    model = ReportOutputModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "report_template_id",
                "output_type",
                "output_config",
                "format",
                "format_config",
                "is_active",
            ],
        ),
    }

    # Fields
    report_template_id: str
    report_template: Optional[ReportTemplate] = None
    output_type: str  # FILE, EMAIL, WEBHOOK, NOTIFICATION
    output_config: Dict[str, Any] = {}
    format: str  # CSV, PDF, JSON, HTML, EXCEL, TEXT
    format_config: Dict[str, Any] = {}
    is_active: bool = True
    output_executions: List["ReportOutputExecution"] = []

    model_config = ConfigDict(
        extra="allow"
    )

    def __str__(self) -> str:
        return f"{self.output_type} output in {self.format} format"

    @field_validator("output_type")
    @classmethod
    def validate_output_type(cls, output_type: str) -> str:
        """Validate output_type is one of the defined types."""
        allowed_types = [t.value for t in ReportOutputType]
        if output_type not in allowed_types:
            raise ValueError(f"Output type must be one of: {', '.join(allowed_types)}")
        return output_type

    @field_validator("format")
    @classmethod
    def validate_format(cls, format: str) -> str:
        """Validate format is one of the defined types."""
        allowed_formats = [f.value for f in ReportFormat]
        if format not in allowed_formats:
            raise ValueError(f"Format must be one of: {', '.join(allowed_formats)}")
        return format

    @model_validator(mode="after")
    def validate_output(self) -> Self:
        """Validate the output configuration based on type."""
        # Different output types require different config properties
        if self.output_type == ReportOutputType.FILE:
            if "path" not in self.output_config:
                raise ValueError("File output must include a path in output_config")
        
        elif self.output_type == ReportOutputType.EMAIL:
            if "recipients" not in self.output_config:
                raise ValueError("Email output must include recipients in output_config")
        
        elif self.output_type == ReportOutputType.WEBHOOK:
            if "url" not in self.output_config:
                raise ValueError("Webhook output must include a URL in output_config")
        
        return self


class ReportExecution(UnoObj[ReportExecutionModel], DefaultObjectMixin):
    """Record of a report execution."""

    # Class variables
    model = ReportExecutionModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "report_template_id",
                "triggered_by",
                "trigger_type",
                "parameters",
                "status",
            ],
        ),
    }

    # Fields
    report_template_id: str
    report_template: Optional[ReportTemplate] = None
    triggered_by: str
    trigger_type: str  # MANUAL, SCHEDULED, EVENT, QUERY
    parameters: Dict[str, Any] = {}
    status: str = ReportExecutionStatus.PENDING
    started_at: datetime = datetime.utcnow()
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    row_count: Optional[int] = None
    execution_time_ms: Optional[int] = None
    result_hash: Optional[str] = None
    output_executions: List["ReportOutputExecution"] = []

    model_config = ConfigDict(
        extra="allow"
    )

    def __str__(self) -> str:
        return f"Execution of {self.report_template_id} ({self.status})"

    @field_validator("status")
    @classmethod
    def validate_status(cls, status: str) -> str:
        """Validate status is one of the defined types."""
        allowed_statuses = [s.value for s in ReportExecutionStatus]
        if status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return status

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, trigger_type: str) -> str:
        """Validate trigger_type is one of the defined types."""
        allowed_types = [t.value for t in ReportTriggerType]
        if trigger_type not in allowed_types:
            raise ValueError(f"Trigger type must be one of: {', '.join(allowed_types)}")
        return trigger_type


class ReportOutputExecution(UnoObj[ReportOutputExecutionModel], DefaultObjectMixin):
    """Record of a report output delivery."""

    # Class variables
    model = ReportOutputExecutionModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "report_execution_id",
                "report_output_id",
                "status",
            ],
        ),
    }

    # Fields
    report_execution_id: str
    report_execution: Optional[ReportExecution] = None
    report_output_id: str
    report_output: Optional[ReportOutput] = None
    status: str = ReportExecutionStatus.PENDING
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    output_location: Optional[str] = None
    output_size_bytes: Optional[int] = None

    model_config = ConfigDict(
        extra="allow"
    )

    def __str__(self) -> str:
        return f"Output execution for {self.report_execution_id} ({self.status})"

    @field_validator("status")
    @classmethod
    def validate_status(cls, status: str) -> str:
        """Validate status is one of the defined types."""
        allowed_statuses = [s.value for s in ReportExecutionStatus]
        if status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return status