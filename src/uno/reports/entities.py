"""Domain entities for the Reports module."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union

from uno.domain.core import Entity, AggregateRoot, safe_dataclass
from uno.core.errors.result import Result, Success, Failure


# Define enum values
class ReportFieldType:
    """Types of report fields."""

    DB_COLUMN = "db_column"
    ATTRIBUTE = "attribute"
    METHOD = "method"
    QUERY = "query"
    AGGREGATE = "aggregate"
    RELATED = "related"
    CUSTOM = "custom"


class ReportTriggerType:
    """Types of report triggers."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    QUERY = "query"


class ReportOutputType:
    """Types of report outputs."""

    FILE = "file"
    EMAIL = "email"
    WEBHOOK = "webhook"
    NOTIFICATION = "notification"


class ReportFormat:
    """Report output formats."""

    CSV = "csv"
    PDF = "pdf"
    JSON = "json"
    HTML = "html"
    EXCEL = "excel"
    TEXT = "text"


class ReportExecutionStatus:
    """Status of report execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@safe_dataclass
@dataclass
class ReportFieldDefinition(Entity[str]):
    """A field definition for a report template."""

    name: str
    display: str
    field_type: str
    field_config: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    order: int = 0
    format_string: Optional[str] = None
    conditional_formats: Optional[Dict[str, Any]] = None
    is_visible: bool = True
    parent_field_id: Optional[str] = None

    # Relationships
    parent_field: Optional["ReportFieldDefinition"] = None
    child_fields: List["ReportFieldDefinition"] = field(default_factory=list)
    report_templates: List["ReportTemplate"] = field(default_factory=list)

    # ORM mapping
    __uno_model__ = "ReportFieldDefinitionModel"

    def __post_init__(self):
        """Initialize after dataclass creation."""
        super().__post_init__()
        # Ensure collections are initialized properly
        if self.child_fields is None:
            self.child_fields = []
        if self.report_templates is None:
            self.report_templates = []

    def validate(self) -> Result[None]:
        """Validate the field definition."""
        # Validate field_type
        allowed_types = [
            ReportFieldType.DB_COLUMN,
            ReportFieldType.ATTRIBUTE,
            ReportFieldType.METHOD,
            ReportFieldType.QUERY,
            ReportFieldType.AGGREGATE,
            ReportFieldType.RELATED,
            ReportFieldType.CUSTOM,
        ]

        if self.field_type not in allowed_types:
            return Failure(f"Field type must be one of: {', '.join(allowed_types)}")

        # Validate field_config based on field_type
        if self.field_type == ReportFieldType.DB_COLUMN:
            required_props = ["table", "column"]
            for prop in required_props:
                if prop not in self.field_config:
                    return Failure(f"Field config for DB_COLUMN must include {prop}")

        elif self.field_type == ReportFieldType.ATTRIBUTE:
            if "attribute_type_id" not in self.field_config:
                return Failure(
                    "Field config for ATTRIBUTE must include attribute_type_id"
                )

        elif self.field_type == ReportFieldType.METHOD:
            required_props = ["method", "module"]
            for prop in required_props:
                if prop not in self.field_config:
                    return Failure(f"Field config for METHOD must include {prop}")

        elif self.field_type == ReportFieldType.QUERY:
            if "query_id" not in self.field_config:
                return Failure("Field config for QUERY must include query_id")

        elif self.field_type == ReportFieldType.AGGREGATE:
            required_props = ["function", "field"]
            for prop in required_props:
                if prop not in self.field_config:
                    return Failure(f"Field config for AGGREGATE must include {prop}")

        elif self.field_type == ReportFieldType.RELATED:
            required_props = ["relation", "field"]
            for prop in required_props:
                if prop not in self.field_config:
                    return Failure(f"Field config for RELATED must include {prop}")

        return Success(None)

    def add_to_template(self, template: "ReportTemplate") -> None:
        """Add this field to a report template."""
        if template not in self.report_templates:
            self.report_templates.append(template)
            if self not in template.fields:
                template.fields.append(self)

    def remove_from_template(self, template: "ReportTemplate") -> None:
        """Remove this field from a report template."""
        if template in self.report_templates:
            self.report_templates.remove(template)
            if self in template.fields:
                template.fields.remove(self)

    def add_child_field(self, child_field: "ReportFieldDefinition") -> None:
        """Add a child field to this field."""
        if child_field not in self.child_fields:
            self.child_fields.append(child_field)
            child_field.parent_field = self
            child_field.parent_field_id = self.id


@safe_dataclass
@dataclass
class ReportTemplate(AggregateRoot[str]):
    """A template defining a report's structure and behavior."""

    name: str
    description: str
    base_object_type: str
    format_config: Dict[str, Any] = field(default_factory=dict)
    parameter_definitions: Dict[str, Any] = field(default_factory=dict)
    cache_policy: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    # Relationships
    fields: List[ReportFieldDefinition] = field(default_factory=list)
    triggers: List["ReportTrigger"] = field(default_factory=list)
    outputs: List["ReportOutput"] = field(default_factory=list)
    executions: List["ReportExecution"] = field(default_factory=list)

    # ORM mapping
    __uno_model__ = "ReportTemplateModel"

    def __post_init__(self):
        """Initialize after dataclass creation."""
        super().__post_init__()
        # Ensure collections are initialized properly
        if self.fields is None:
            self.fields = []
        if self.triggers is None:
            self.triggers = []
        if self.outputs is None:
            self.outputs = []
        if self.executions is None:
            self.executions = []

    def validate(self) -> Result[None]:
        """Validate the report template."""
        # Ensure parameter definitions are valid
        for param_name, param_def in self.parameter_definitions.items():
            if not isinstance(param_def, dict):
                return Failure(
                    f"Parameter definition for {param_name} must be a dictionary"
                )
            if "type" not in param_def:
                return Failure(
                    f"Parameter definition for {param_name} must include a type"
                )

        # Validate each field
        for field in self.fields:
            field_result = field.validate()
            if field_result.is_failure:
                return Failure(f"Invalid field '{field.name}': {field_result.error}")

        # Validate each trigger
        for trigger in self.triggers:
            trigger_result = trigger.validate()
            if trigger_result.is_failure:
                return Failure(f"Invalid trigger: {trigger_result.error}")

        # Validate each output
        for output in self.outputs:
            output_result = output.validate()
            if output_result.is_failure:
                return Failure(f"Invalid output: {output_result.error}")

        return Success(None)

    def add_field(self, field: ReportFieldDefinition) -> None:
        """Add a field to this template."""
        if field not in self.fields:
            self.fields.append(field)
            field.add_to_template(self)

    def remove_field(self, field: ReportFieldDefinition) -> None:
        """Remove a field from this template."""
        if field in self.fields:
            self.fields.remove(field)
            field.remove_from_template(self)

    def add_trigger(self, trigger: "ReportTrigger") -> None:
        """Add a trigger to this template."""
        if trigger not in self.triggers:
            self.triggers.append(trigger)
            trigger.report_template = self
            trigger.report_template_id = self.id

    def remove_trigger(self, trigger: "ReportTrigger") -> None:
        """Remove a trigger from this template."""
        if trigger in self.triggers:
            self.triggers.remove(trigger)
            trigger.report_template = None
            trigger.report_template_id = None

    def add_output(self, output: "ReportOutput") -> None:
        """Add an output to this template."""
        if output not in self.outputs:
            self.outputs.append(output)
            output.report_template = self
            output.report_template_id = self.id

    def remove_output(self, output: "ReportOutput") -> None:
        """Remove an output from this template."""
        if output in self.outputs:
            self.outputs.remove(output)
            output.report_template = None
            output.report_template_id = None

    def add_execution(self, execution: "ReportExecution") -> None:
        """Add an execution record to this template."""
        if execution not in self.executions:
            self.executions.append(execution)
            execution.report_template = self
            execution.report_template_id = self.id


@safe_dataclass
@dataclass
class ReportTrigger(Entity[str]):
    """Defines when a report should be generated."""

    report_template_id: str
    trigger_type: str
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None
    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    query_id: Optional[str] = None
    is_active: bool = True
    last_triggered: Optional[datetime] = None

    # Relationships
    report_template: Optional[ReportTemplate] = None

    # ORM mapping
    __uno_model__ = "ReportTriggerModel"

    def __post_init__(self):
        """Initialize after dataclass creation."""
        super().__post_init__()
        # Ensure trigger_config is initialized
        if self.trigger_config is None:
            self.trigger_config = {}

    def validate(self) -> Result[None]:
        """Validate the trigger configuration based on type."""
        # Validate trigger_type
        allowed_types = [
            ReportTriggerType.MANUAL,
            ReportTriggerType.SCHEDULED,
            ReportTriggerType.EVENT,
            ReportTriggerType.QUERY,
        ]

        if self.trigger_type not in allowed_types:
            return Failure(f"Trigger type must be one of: {', '.join(allowed_types)}")

        # Validate type-specific requirements
        if self.trigger_type == ReportTriggerType.SCHEDULED:
            if not self.schedule:
                return Failure("Scheduled triggers must include a schedule")

        elif self.trigger_type == ReportTriggerType.EVENT:
            if not self.event_type:
                return Failure("Event triggers must include an event_type")

        elif self.trigger_type == ReportTriggerType.QUERY:
            if not self.query_id:
                return Failure("Query triggers must include a query_id")

        return Success(None)


@safe_dataclass
@dataclass
class ReportOutput(Entity[str]):
    """Defines how report results should be delivered."""

    report_template_id: str
    output_type: str
    format: str
    output_config: Dict[str, Any] = field(default_factory=dict)
    format_config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    # Relationships
    report_template: Optional[ReportTemplate] = None
    output_executions: List["ReportOutputExecution"] = field(default_factory=list)

    # ORM mapping
    __uno_model__ = "ReportOutputModel"

    def __post_init__(self):
        """Initialize after dataclass creation."""
        super().__post_init__()
        # Ensure collections and dictionaries are initialized properly
        if self.output_config is None:
            self.output_config = {}
        if self.format_config is None:
            self.format_config = {}
        if self.output_executions is None:
            self.output_executions = []

    def validate(self) -> Result[None]:
        """Validate the output configuration based on type."""
        # Validate output_type
        allowed_types = [
            ReportOutputType.FILE,
            ReportOutputType.EMAIL,
            ReportOutputType.WEBHOOK,
            ReportOutputType.NOTIFICATION,
        ]

        if self.output_type not in allowed_types:
            return Failure(f"Output type must be one of: {', '.join(allowed_types)}")

        # Validate format
        allowed_formats = [
            ReportFormat.CSV,
            ReportFormat.PDF,
            ReportFormat.JSON,
            ReportFormat.HTML,
            ReportFormat.EXCEL,
            ReportFormat.TEXT,
        ]

        if self.format not in allowed_formats:
            return Failure(f"Format must be one of: {', '.join(allowed_formats)}")

        # Validate type-specific requirements
        if self.output_type == ReportOutputType.FILE:
            if "path" not in self.output_config:
                return Failure("File output must include a path in output_config")

        elif self.output_type == ReportOutputType.EMAIL:
            if "recipients" not in self.output_config:
                return Failure("Email output must include recipients in output_config")

        elif self.output_type == ReportOutputType.WEBHOOK:
            if "url" not in self.output_config:
                return Failure("Webhook output must include a URL in output_config")

        return Success(None)

    def add_execution(self, execution: "ReportOutputExecution") -> None:
        """Add an output execution record."""
        if execution not in self.output_executions:
            self.output_executions.append(execution)
            execution.report_output = self
            execution.report_output_id = self.id


@safe_dataclass
@dataclass
class ReportExecution(Entity[str]):
    """Record of a report execution."""

    report_template_id: str
    triggered_by: str
    trigger_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = ReportExecutionStatus.PENDING
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    row_count: Optional[int] = None
    execution_time_ms: Optional[int] = None
    result_hash: Optional[str] = None

    # Relationships
    report_template: Optional[ReportTemplate] = None
    output_executions: List["ReportOutputExecution"] = field(default_factory=list)

    # ORM mapping
    __uno_model__ = "ReportExecutionModel"

    def __post_init__(self):
        """Initialize after dataclass creation."""
        super().__post_init__()
        # Ensure collections and dictionaries are initialized properly
        if self.parameters is None:
            self.parameters = {}
        if self.output_executions is None:
            self.output_executions = []

    def validate(self) -> Result[None]:
        """Validate the execution record."""
        # Validate status
        allowed_statuses = [
            ReportExecutionStatus.PENDING,
            ReportExecutionStatus.RUNNING,
            ReportExecutionStatus.COMPLETED,
            ReportExecutionStatus.FAILED,
            ReportExecutionStatus.CANCELED,
        ]

        if self.status not in allowed_statuses:
            return Failure(f"Status must be one of: {', '.join(allowed_statuses)}")

        # Validate trigger_type
        allowed_types = [
            ReportTriggerType.MANUAL,
            ReportTriggerType.SCHEDULED,
            ReportTriggerType.EVENT,
            ReportTriggerType.QUERY,
        ]

        if self.trigger_type not in allowed_types:
            return Failure(f"Trigger type must be one of: {', '.join(allowed_types)}")

        return Success(None)

    def add_output_execution(self, output_execution: "ReportOutputExecution") -> None:
        """Add an output execution record."""
        if output_execution not in self.output_executions:
            self.output_executions.append(output_execution)
            output_execution.report_execution = self
            output_execution.report_execution_id = self.id

    def update_status(
        self, status: str, error_details: Optional[str] = None
    ) -> Result[None]:
        """Update the execution status."""
        allowed_statuses = [
            ReportExecutionStatus.PENDING,
            ReportExecutionStatus.RUNNING,
            ReportExecutionStatus.COMPLETED,
            ReportExecutionStatus.FAILED,
            ReportExecutionStatus.CANCELED,
        ]

        if status not in allowed_statuses:
            return Failure(f"Status must be one of: {', '.join(allowed_statuses)}")

        self.status = status

        if status in [
            ReportExecutionStatus.COMPLETED,
            ReportExecutionStatus.FAILED,
            ReportExecutionStatus.CANCELED,
        ]:
            self.completed_at = datetime.now(timezone.utc)

        if status == ReportExecutionStatus.FAILED and error_details:
            self.error_details = error_details

        return Success(None)


@safe_dataclass
@dataclass
class ReportOutputExecution(Entity[str]):
    """Record of a report output delivery."""

    report_execution_id: str
    report_output_id: str
    status: str = ReportExecutionStatus.PENDING
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    output_location: Optional[str] = None
    output_size_bytes: Optional[int] = None

    # Relationships
    report_execution: Optional[ReportExecution] = None
    report_output: Optional[ReportOutput] = None

    # ORM mapping
    __uno_model__ = "ReportOutputExecutionModel"

    def __post_init__(self):
        """Initialize after dataclass creation."""
        super().__post_init__()

    def validate(self) -> Result[None]:
        """Validate the output execution record."""
        # Validate status
        allowed_statuses = [
            ReportExecutionStatus.PENDING,
            ReportExecutionStatus.RUNNING,
            ReportExecutionStatus.COMPLETED,
            ReportExecutionStatus.FAILED,
            ReportExecutionStatus.CANCELED,
        ]

        if self.status not in allowed_statuses:
            return Failure(f"Status must be one of: {', '.join(allowed_statuses)}")

        return Success(None)

    def update_status(
        self, status: str, error_details: Optional[str] = None
    ) -> Result[None]:
        """Update the output execution status."""
        allowed_statuses = [
            ReportExecutionStatus.PENDING,
            ReportExecutionStatus.RUNNING,
            ReportExecutionStatus.COMPLETED,
            ReportExecutionStatus.FAILED,
            ReportExecutionStatus.CANCELED,
        ]

        if status not in allowed_statuses:
            return Failure(f"Status must be one of: {', '.join(allowed_statuses)}")

        self.status = status

        if status in [
            ReportExecutionStatus.COMPLETED,
            ReportExecutionStatus.FAILED,
            ReportExecutionStatus.CANCELED,
        ]:
            self.completed_at = datetime.now(timezone.utc)

        if status == ReportExecutionStatus.FAILED and error_details:
            self.error_details = error_details

        return Success(None)
