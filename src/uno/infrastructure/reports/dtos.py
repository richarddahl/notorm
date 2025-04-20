"""DTOs for the Reports module API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator, ConfigDict


# Enums for validation and documentation
class ReportFieldTypeEnum(str, Enum):
    """Types of report fields."""

    DB_COLUMN = "db_column"
    ATTRIBUTE = "attribute"
    METHOD = "method"
    QUERY = "query"
    AGGREGATE = "aggregate"
    RELATED = "related"
    CUSTOM = "custom"


class ReportTriggerTypeEnum(str, Enum):
    """Types of report triggers."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    QUERY = "query"


class ReportOutputTypeEnum(str, Enum):
    """Types of report outputs."""

    FILE = "file"
    EMAIL = "email"
    WEBHOOK = "webhook"
    NOTIFICATION = "notification"


class ReportFormatEnum(str, Enum):
    """Report output formats."""

    CSV = "csv"
    PDF = "pdf"
    JSON = "json"
    HTML = "html"
    EXCEL = "excel"
    TEXT = "text"


class ReportExecutionStatusEnum(str, Enum):
    """Status of report execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


# Field Definition DTOs
class ReportFieldDefinitionBaseDto(BaseModel):
    """Base DTO for report field definitions."""

    name: str = Field(..., description="Field name")
    display: str = Field(..., description="Display name for the field")
    field_type: ReportFieldTypeEnum = Field(..., description="Type of field")
    field_config: dict[str, Any] = Field(
        default_factory=dict, description="Configuration for the field"
    )
    description: Optional[str] = Field(None, description="Field description")
    order: int = Field(0, description="Display order")
    format_string: Optional[str] = Field(None, description="Format string for display")
    conditional_formats: Optional[Dict[str, Any]] = Field(
        None, description="Conditional formatting rules"
    )
    is_visible: bool = Field(True, description="Whether the field is visible")
    parent_field_id: Optional[str] = Field(None, description="ID of the parent field")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "customer_name",
                "display": "Customer Name",
                "field_type": "db_column",
                "field_config": {"table": "customers", "column": "name"},
                "description": "The customer's full name",
                "order": 1,
                "format_string": None,
                "conditional_formats": None,
                "is_visible": True,
                "parent_field_id": None,
            }
        }
    )


class ReportFieldDefinitionCreateDto(ReportFieldDefinitionBaseDto):
    """DTO for creating report field definitions."""

    pass


class ReportFieldDefinitionUpdateDto(BaseModel):
    """DTO for updating report field definitions."""

    name: Optional[str] = Field(None, description="Field name")
    display: Optional[str] = Field(None, description="Display name for the field")
    field_type: Optional[ReportFieldTypeEnum] = Field(None, description="Type of field")
    field_config: dict[str, Any] | None = Field(
        None, description="Configuration for the field"
    )
    description: Optional[str] = Field(None, description="Field description")
    order: Optional[int] = Field(None, description="Display order")
    format_string: Optional[str] = Field(None, description="Format string for display")
    conditional_formats: Optional[Dict[str, Any]] = Field(
        None, description="Conditional formatting rules"
    )
    is_visible: Optional[bool] = Field(None, description="Whether the field is visible")
    parent_field_id: Optional[str] = Field(None, description="ID of the parent field")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display": "Customer Full Name",
                "description": "The customer's full legal name",
                "order": 2,
                "is_visible": True,
            }
        }
    )


class ReportFieldDefinitionViewDto(ReportFieldDefinitionBaseDto):
    """DTO for viewing report field definitions."""

    id: str = Field(..., description="Unique identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "fd123e4567-e89b-12d3-a456-426614174000",
                "name": "customer_name",
                "display": "Customer Name",
                "field_type": "db_column",
                "field_config": {"table": "customers", "column": "name"},
                "description": "The customer's full name",
                "order": 1,
                "format_string": None,
                "conditional_formats": None,
                "is_visible": True,
                "parent_field_id": None,
            }
        }
    )


class ReportFieldDefinitionFilterParams(BaseModel):
    """Filter parameters for report field definitions."""

    name: Optional[str] = Field(None, description="Filter by field name")
    field_type: Optional[ReportFieldTypeEnum] = Field(
        None, description="Filter by field type"
    )
    parent_field_id: Optional[str] = Field(
        None, description="Filter by parent field ID"
    )
    template_id: Optional[str] = Field(None, description="Filter by template ID")
    is_visible: Optional[bool] = Field(None, description="Filter by visibility")

    model_config = ConfigDict(
        json_schema_extra={"example": {"field_type": "db_column", "is_visible": True}}
    )


# Report Template DTOs
class ReportTemplateBaseDto(BaseModel):
    """Base DTO for report templates."""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    base_object_type: str = Field(..., description="Base object type for the report")
    format_config: Dict[str, Any] = Field(
        default_factory=dict, description="Format configuration"
    )
    parameter_definitions: Dict[str, Any] = Field(
        default_factory=dict, description="Parameter definitions"
    )
    cache_policy: Dict[str, Any] = Field(
        default_factory=dict, description="Cache policy configuration"
    )
    version: str = Field("1.0.0", description="Template version")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "monthly_sales_report",
                "description": "Monthly sales by customer and product",
                "base_object_type": "Order",
                "format_config": {"page_size": "letter", "orientation": "landscape"},
                "parameter_definitions": {
                    "start_date": {"type": "date", "required": True},
                    "end_date": {"type": "date", "required": True},
                    "customer_id": {"type": "string", "required": False},
                },
                "cache_policy": {"max_age_seconds": 3600},
                "version": "1.0.0",
            }
        }
    )


class ReportTemplateCreateDto(ReportTemplateBaseDto):
    """DTO for creating report templates."""

    field_ids: Optional[List[str]] = Field(
        None, description="IDs of fields to associate with the template"
    )


class ReportTemplateUpdateDto(BaseModel):
    """DTO for updating report templates."""

    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    base_object_type: Optional[str] = Field(
        None, description="Base object type for the report"
    )
    format_config: Optional[Dict[str, Any]] = Field(
        None, description="Format configuration"
    )
    parameter_definitions: Optional[Dict[str, Any]] = Field(
        None, description="Parameter definitions"
    )
    cache_policy: Optional[Dict[str, Any]] = Field(
        None, description="Cache policy configuration"
    )
    version: Optional[str] = Field(None, description="Template version")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Updated monthly sales by customer and product",
                "format_config": {"page_size": "letter", "orientation": "portrait"},
                "cache_policy": {"max_age_seconds": 1800},
            }
        }
    )


class ReportTemplateViewDto(ReportTemplateBaseDto):
    """DTO for viewing report templates."""

    id: str = Field(..., description="Unique identifier")
    fields: List[ReportFieldDefinitionViewDto] = Field(
        default_factory=list, description="Associated fields"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rt123e4567-e89b-12d3-a456-426614174000",
                "name": "monthly_sales_report",
                "description": "Monthly sales by customer and product",
                "base_object_type": "Order",
                "format_config": {"page_size": "letter", "orientation": "landscape"},
                "parameter_definitions": {
                    "start_date": {"type": "date", "required": True},
                    "end_date": {"type": "date", "required": True},
                    "customer_id": {"type": "string", "required": False},
                },
                "cache_policy": {"max_age_seconds": 3600},
                "version": "1.0.0",
                "fields": [],
            }
        }
    )


class ReportTemplateFilterParams(BaseModel):
    """Filter parameters for report templates."""

    name: Optional[str] = Field(None, description="Filter by template name")
    base_object_type: Optional[str] = Field(
        None, description="Filter by base object type"
    )
    field_id: Optional[str] = Field(None, description="Filter by associated field ID")

    model_config = ConfigDict(
        json_schema_extra={"example": {"base_object_type": "Order"}}
    )


# Report Trigger DTOs
class ReportTriggerBaseDto(BaseModel):
    """Base DTO for report triggers."""

    report_template_id: str = Field(..., description="Associated template ID")
    trigger_type: ReportTriggerTypeEnum = Field(..., description="Type of trigger")
    trigger_config: dict[str, Any] = Field(
        default_factory=dict, description="Trigger configuration"
    )
    schedule: Optional[str] = Field(
        None, description="Cron expression for scheduled triggers"
    )
    event_type: Optional[str] = Field(None, description="Event type for event triggers")
    entity_type: Optional[str] = Field(
        None, description="Entity type for event triggers"
    )
    query_id: Optional[str] = Field(None, description="Query ID for query triggers")
    is_active: bool = Field(True, description="Whether the trigger is active")

    @model_validator(mode="before")
    def validate_schedule(cls, values):
        """Validate that schedule is provided for scheduled triggers."""
        if values.get("trigger_type") == ReportTriggerTypeEnum.SCHEDULED and not values.get("schedule"):
            return Failure("Schedule is required for scheduled triggers", convert=True)
        return values

    @model_validator(mode="before")
    def validate_event_type(cls, values):
        """Validate that event_type is provided for event triggers."""
        if values.get("trigger_type") == ReportTriggerTypeEnum.EVENT and not values.get("event_type"):
            return Failure("Event type is required for event triggers", convert=True)
        return values

    @model_validator(mode="before")
    def validate_query_id(cls, values):
        """Validate that query_id is provided for query triggers."""
        if values.get("trigger_type") == ReportTriggerTypeEnum.QUERY and not values.get("query_id"):
            return Failure("Query ID is required for query triggers", convert=True)
        return values

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
                "trigger_type": "scheduled",
                "trigger_config": {"retry_count": 3},
                "schedule": "0 0 1 * *",  # First day of the month at midnight
                "is_active": True,
            }
        }
    )


class ReportTriggerCreateDto(ReportTriggerBaseDto):
    """DTO for creating report triggers."""

    pass


class ReportTriggerUpdateDto(BaseModel):
    """DTO for updating report triggers."""

    trigger_type: Optional[ReportTriggerTypeEnum] = Field(
        None, description="Type of trigger"
    )
    trigger_config: Optional[Dict[str, Any]] = Field(
        None, description="Trigger configuration"
    )
    schedule: Optional[str] = Field(
        None, description="Cron expression for scheduled triggers"
    )
    event_type: Optional[str] = Field(None, description="Event type for event triggers")
    entity_type: Optional[str] = Field(
        None, description="Entity type for event triggers"
    )
    query_id: Optional[str] = Field(None, description="Query ID for query triggers")
    is_active: Optional[bool] = Field(None, description="Whether the trigger is active")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schedule": "0 0 15 * *",  # 15th day of the month at midnight
                "is_active": False,
            }
        }
    )


class ReportTriggerViewDto(ReportTriggerBaseDto):
    """DTO for viewing report triggers."""

    id: str = Field(..., description="Unique identifier")
    last_triggered: Optional[datetime] = Field(
        None, description="When the trigger was last fired"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "tr123e4567-e89b-12d3-a456-426614174000",
                "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
                "trigger_type": "scheduled",
                "trigger_config": {"retry_count": 3},
                "schedule": "0 0 1 * *",  # First day of the month at midnight
                "is_active": True,
                "last_triggered": "2023-05-01T00:00:00Z",
            }
        }
    )


class ReportTriggerFilterParams(BaseModel):
    """Filter parameters for report triggers."""

    report_template_id: Optional[str] = Field(None, description="Filter by template ID")
    trigger_type: Optional[ReportTriggerTypeEnum] = Field(
        None, description="Filter by trigger type"
    )
    is_active: Optional[bool] = Field(None, description="Filter by active status")

    model_config = ConfigDict(
        json_schema_extra={"example": {"trigger_type": "scheduled", "is_active": True}}
    )


# Report Output DTOs
class ReportOutputBaseDto(BaseModel):
    """Base DTO for report outputs."""

    report_template_id: str = Field(..., description="Associated template ID")
    output_type: ReportOutputTypeEnum = Field(..., description="Type of output")
    format: ReportFormatEnum = Field(..., description="Output format")
    output_config: Dict[str, Any] = Field(
        default_factory=dict, description="Output configuration"
    )
    format_config: Dict[str, Any] = Field(
        default_factory=dict, description="Format configuration"
    )
    is_active: bool = Field(True, description="Whether the output is active")

    @model_validator(mode="before")
    def validate_output_config(cls, values):
        """Validate output_config based on output_type."""
        output_config = values.get("output_config", {})
        if (
            values.get("output_type") == ReportOutputTypeEnum.FILE
            and "path" not in output_config
        ):
            raise ValueError("File output must include a path in output_config")
        elif (
            values.get("output_type") == ReportOutputTypeEnum.EMAIL
            and "recipients" not in output_config
        ):
            raise ValueError("Email output must include recipients in output_config")
        elif (
            values.get("output_type") == ReportOutputTypeEnum.WEBHOOK
            and "url" not in output_config
        ):
            raise ValueError("Webhook output must include a URL in output_config")
        return values

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
                "output_type": "email",
                "format": "pdf",
                "output_config": {
                    "recipients": ["user@example.com"],
                    "subject": "Monthly Sales Report",
                },
                "format_config": {"page_size": "letter", "orientation": "landscape"},
                "is_active": True,
            }
        }
    )


class ReportOutputCreateDto(ReportOutputBaseDto):
    """DTO for creating report outputs."""

    pass


class ReportOutputUpdateDto(BaseModel):
    """DTO for updating report outputs."""

    output_type: Optional[ReportOutputTypeEnum] = Field(
        None, description="Type of output"
    )
    format: Optional[ReportFormatEnum] = Field(None, description="Output format")
    output_config: Optional[Dict[str, Any]] = Field(
        None, description="Output configuration"
    )
    format_config: Optional[Dict[str, Any]] = Field(
        None, description="Format configuration"
    )
    is_active: Optional[bool] = Field(None, description="Whether the output is active")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "output_config": {
                    "recipients": ["user@example.com", "manager@example.com"],
                    "subject": "Updated: Monthly Sales Report",
                },
                "is_active": False,
            }
        }
    )


class ReportOutputViewDto(ReportOutputBaseDto):
    """DTO for viewing report outputs."""

    id: str = Field(..., description="Unique identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ro123e4567-e89b-12d3-a456-426614174000",
                "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
                "output_type": "email",
                "format": "pdf",
                "output_config": {
                    "recipients": ["user@example.com"],
                    "subject": "Monthly Sales Report",
                },
                "format_config": {"page_size": "letter", "orientation": "landscape"},
                "is_active": True,
            }
        }
    )


class ReportOutputFilterParams(BaseModel):
    """Filter parameters for report outputs."""

    report_template_id: Optional[str] = Field(None, description="Filter by template ID")
    output_type: Optional[ReportOutputTypeEnum] = Field(
        None, description="Filter by output type"
    )
    format: Optional[ReportFormatEnum] = Field(None, description="Filter by format")
    is_active: Optional[bool] = Field(None, description="Filter by active status")

    model_config = ConfigDict(
        json_schema_extra={"example": {"output_type": "email", "is_active": True}}
    )


# Report Execution DTOs
class ReportExecutionBaseDto(BaseModel):
    """Base DTO for report executions."""

    report_template_id: str = Field(..., description="Associated template ID")
    triggered_by: str = Field(
        ..., description="ID or name of the entity that triggered the execution"
    )
    trigger_type: ReportTriggerTypeEnum = Field(
        ..., description="Type of trigger that initiated the execution"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Execution parameters"
    )
    status: ReportExecutionStatusEnum = Field(
        ReportExecutionStatusEnum.PENDING, description="Execution status"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
                "triggered_by": "user@example.com",
                "trigger_type": "manual",
                "parameters": {"start_date": "2023-01-01", "end_date": "2023-01-31"},
                "status": "pending",
            }
        }
    )


class ReportExecutionCreateDto(ReportExecutionBaseDto):
    """DTO for creating report executions."""

    status: Optional[ReportExecutionStatusEnum] = Field(
        None, description="Execution status"
    )


class ReportExecutionUpdateStatusDto(BaseModel):
    """DTO for updating report execution status."""

    status: ReportExecutionStatusEnum = Field(..., description="New execution status")
    error_details: Optional[str] = Field(
        None, description="Error details if status is failed"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "completed", "error_details": None}}
    )


class ReportExecutionViewDto(ReportExecutionBaseDto):
    """DTO for viewing report executions."""

    id: str = Field(..., description="Unique identifier")
    started_at: datetime = Field(..., description="When the execution started")
    completed_at: Optional[datetime] = Field(
        None, description="When the execution completed"
    )
    error_details: Optional[str] = Field(
        None, description="Error details if status is failed"
    )
    row_count: Optional[int] = Field(None, description="Number of rows in the report")
    execution_time_ms: Optional[int] = Field(
        None, description="Execution time in milliseconds"
    )
    result_hash: Optional[str] = Field(None, description="Hash of the execution result")
    output_executions: List["ReportOutputExecutionViewDto"] = Field(
        default_factory=list, description="Output executions"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "re123e4567-e89b-12d3-a456-426614174000",
                "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
                "triggered_by": "user@example.com",
                "trigger_type": "manual",
                "parameters": {"start_date": "2023-01-01", "end_date": "2023-01-31"},
                "status": "completed",
                "started_at": "2023-02-01T10:00:00Z",
                "completed_at": "2023-02-01T10:01:30Z",
                "error_details": None,
                "row_count": 1500,
                "execution_time_ms": 90000,
                "result_hash": "a1b2c3d4e5f6",
                "output_executions": [],
            }
        }
    )


class ReportExecutionFilterParams(BaseModel):
    """Filter parameters for report executions."""

    report_template_id: Optional[str] = Field(None, description="Filter by template ID")
    triggered_by: Optional[str] = Field(None, description="Filter by triggered by")
    trigger_type: Optional[ReportTriggerTypeEnum] = Field(
        None, description="Filter by trigger type"
    )
    status: Optional[ReportExecutionStatusEnum] = Field(
        None, description="Filter by status"
    )
    created_after: Optional[datetime] = Field(
        None, description="Filter by created after date"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by created before date"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_template_id": "rt123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "created_after": "2023-01-01T00:00:00Z",
            }
        }
    )


# Report Output Execution DTOs
class ReportOutputExecutionBaseDto(BaseModel):
    """Base DTO for report output executions."""

    report_execution_id: str = Field(..., description="Associated execution ID")
    report_output_id: str = Field(..., description="Associated output ID")
    status: ReportExecutionStatusEnum = Field(
        ReportExecutionStatusEnum.PENDING, description="Execution status"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_execution_id": "re123e4567-e89b-12d3-a456-426614174000",
                "report_output_id": "ro123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
            }
        }
    )


class ReportOutputExecutionCreateDto(ReportOutputExecutionBaseDto):
    """DTO for creating report output executions."""

    status: Optional[ReportExecutionStatusEnum] = Field(
        None, description="Execution status"
    )


class ReportOutputExecutionUpdateStatusDto(BaseModel):
    """DTO for updating report output execution status."""

    status: ReportExecutionStatusEnum = Field(..., description="New execution status")
    error_details: Optional[str] = Field(
        None, description="Error details if status is failed"
    )
    output_location: Optional[str] = Field(None, description="Location of the output")
    output_size_bytes: Optional[int] = Field(
        None, description="Size of the output in bytes"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "completed",
                "error_details": None,
                "output_location": "/reports/monthly_sales_report/202301.pdf",
                "output_size_bytes": 1024000,
            }
        }
    )


class ReportOutputExecutionViewDto(ReportOutputExecutionBaseDto):
    """DTO for viewing report output executions."""

    id: str = Field(..., description="Unique identifier")
    completed_at: Optional[datetime] = Field(
        None, description="When the execution completed"
    )
    error_details: Optional[str] = Field(
        None, description="Error details if status is failed"
    )
    output_location: Optional[str] = Field(None, description="Location of the output")
    output_size_bytes: Optional[int] = Field(
        None, description="Size of the output in bytes"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "roe123e4567-e89b-12d3-a456-426614174000",
                "report_execution_id": "re123e4567-e89b-12d3-a456-426614174000",
                "report_output_id": "ro123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "completed_at": "2023-02-01T10:01:30Z",
                "error_details": None,
                "output_location": "/reports/monthly_sales_report/202301.pdf",
                "output_size_bytes": 1024000,
            }
        }
    )


class ReportOutputExecutionFilterParams(BaseModel):
    """Filter parameters for report output executions."""

    report_execution_id: Optional[str] = Field(
        None, description="Filter by execution ID"
    )
    report_output_id: Optional[str] = Field(None, description="Filter by output ID")
    status: Optional[ReportExecutionStatusEnum] = Field(
        None, description="Filter by status"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_execution_id": "re123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
            }
        }
    )


# Fix forward references for nested DTOs
ReportExecutionViewDto.model_rebuild()
