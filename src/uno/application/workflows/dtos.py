"""DTOs for the Workflows module API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, model_validator, ConfigDict


# Enums for validation and documentation
class WorkflowStatusEnum(str, Enum):
    """Workflow status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class WorkflowDBEventEnum(str, Enum):
    """Database events that can trigger workflows."""

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SELECT = "select"


class WorkflowActionTypeEnum(str, Enum):
    """Types of workflow actions."""

    NOTIFICATION = "notification"
    EMAIL = "email"
    WEBHOOK = "webhook"
    DATABASE = "database"
    CUSTOM = "custom"


class WorkflowRecipientTypeEnum(str, Enum):
    """Types of workflow recipients."""

    USER = "user"
    ROLE = "role"
    GROUP = "group"
    ATTRIBUTE = "attribute"
    QUERY = "query"
    DYNAMIC = "dynamic"


class WorkflowConditionTypeEnum(str, Enum):
    """Types of workflow conditions."""

    FIELD_VALUE = "field_value"
    TIME_BASED = "time_based"
    ROLE_BASED = "role_based"
    QUERY_MATCH = "query_match"
    CUSTOM = "custom"
    COMPOSITE = "composite"


class WorkflowExecutionStatusEnum(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class LogicalOperatorEnum(str, Enum):
    """Logical operators for combining conditions."""

    AND = "and"
    OR = "or"
    NOT = "not"


class ComparisonOperatorEnum(str, Enum):
    """Comparison operators for field value conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUALS = "greater_than_or_equals"
    LESS_THAN_OR_EQUALS = "less_than_or_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    IN = "in"
    NOT_IN = "not_in"


class TimeUnitEnum(str, Enum):
    """Time units for time-based conditions."""

    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class TimeOperatorEnum(str, Enum):
    """Time operators for time-based conditions."""

    BEFORE = "before"
    AFTER = "after"
    BETWEEN = "between"
    ON = "on"
    NOT_ON = "not_on"


class WeekdayEnum(str, Enum):
    """Days of the week for time-based conditions."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class NotificationPriorityEnum(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationTypeEnum(str, Enum):
    """Types of notifications."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"


# Workflow Trigger DTOs
class WorkflowTriggerBaseDto(BaseModel):
    """Base DTO for workflow triggers."""

    entity_type: str = Field(
        ..., description="Type of entity that triggers the workflow"
    )
    operation: WorkflowDBEventEnum = Field(
        ..., description="Database operation that triggers the workflow"
    )
    field_conditions: Dict[str, Any] = Field(
        default_factory=dict, description="Field conditions to filter events"
    )
    priority: int = Field(
        100, description="Priority of the trigger (lower numbers run first)"
    )
    is_active: bool = Field(True, description="Whether the trigger is active")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "entity_type": "user",
                "operation": "update",
                "field_conditions": {
                    "email": {"operator": "contains", "value": "@example.com"},
                    "status": {"operator": "equals", "value": "active"},
                },
                "priority": 100,
                "is_active": True,
            }
        })


class WorkflowTriggerCreateDto(WorkflowTriggerBaseDto):
    """DTO for creating workflow triggers."""

    pass


class WorkflowTriggerUpdateDto(BaseModel):
    """DTO for updating workflow triggers."""

    entity_type: Optional[str] = Field(
        None, description="Type of entity that triggers the workflow"
    )
    operation: Optional[WorkflowDBEventEnum] = Field(
        None, description="Database operation that triggers the workflow"
    )
    field_conditions: Optional[Dict[str, Any]] = Field(
        None, description="Field conditions to filter events"
    )
    priority: Optional[int] = Field(
        None, description="Priority of the trigger (lower numbers run first)"
    )
    is_active: Optional[bool] = Field(None, description="Whether the trigger is active")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "field_conditions": {
                    "email": {"operator": "contains", "value": "@newdomain.com"}
                },
                "priority": 50,
                "is_active": False,
            }
        })


class WorkflowTriggerViewDto(WorkflowTriggerBaseDto):
    """DTO for viewing workflow triggers."""

    id: str = Field(..., description="Unique identifier")
    workflow_id: str = Field(..., description="ID of the associated workflow")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "tr123e4567-e89b-12d3-a456-426614174000",
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "entity_type": "user",
                "operation": "update",
                "field_conditions": {
                    "email": {"operator": "contains", "value": "@example.com"},
                    "status": {"operator": "equals", "value": "active"},
                },
                "priority": 100,
                "is_active": True,
            }
        })


class WorkflowTriggerFilterParams(BaseModel):
    """Filter parameters for workflow triggers."""

    workflow_id: Optional[str] = Field(None, description="Filter by workflow ID")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    operation: Optional[WorkflowDBEventEnum] = Field(
        None, description="Filter by operation"
    )
    is_active: Optional[bool] = Field(None, description="Filter by active status")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "entity_type": "user",
                "is_active": True,
            }
        })


# Workflow Condition DTOs
class WorkflowConditionBaseDto(BaseModel):
    """Base DTO for workflow conditions."""

    condition_type: WorkflowConditionTypeEnum = Field(
        ..., description="Type of condition"
    )
    condition_config: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration for the condition"
    )
    query_id: Optional[str] = Field(
        None, description="ID of the query for query match conditions"
    )
    name: str = Field("", description="Name of the condition")
    description: Optional[str] = Field(None, description="Description of the condition")
    order: int = Field(0, description="Order in which the condition is evaluated")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "condition_type": "field_value",
                "condition_config": {
                    "field": "status",
                    "operator": "equals",
                    "value": "active",
                },
                "name": "Active User Check",
                "description": "Checks if the user is active",
                "order": 0,
            }
        })


class WorkflowConditionCreateDto(WorkflowConditionBaseDto):
    """DTO for creating workflow conditions."""

    pass


class WorkflowConditionUpdateDto(BaseModel):
    """DTO for updating workflow conditions."""

    condition_type: Optional[WorkflowConditionTypeEnum] = Field(
        None, description="Type of condition"
    )
    condition_config: Optional[Dict[str, Any]] = Field(
        None, description="Configuration for the condition"
    )
    query_id: Optional[str] = Field(
        None, description="ID of the query for query match conditions"
    )
    name: Optional[str] = Field(None, description="Name of the condition")
    description: Optional[str] = Field(None, description="Description of the condition")
    order: Optional[int] = Field(
        None, description="Order in which the condition is evaluated"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "condition_config": {
                    "field": "status",
                    "operator": "not_equals",
                    "value": "inactive",
                },
                "name": "Not Inactive Check",
                "order": 1,
            }
        })


class WorkflowConditionViewDto(WorkflowConditionBaseDto):
    """DTO for viewing workflow conditions."""

    id: str = Field(..., description="Unique identifier")
    workflow_id: str = Field(..., description="ID of the associated workflow")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "wc123e4567-e89b-12d3-a456-426614174000",
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "condition_type": "field_value",
                "condition_config": {
                    "field": "status",
                    "operator": "equals",
                    "value": "active",
                },
                "name": "Active User Check",
                "description": "Checks if the user is active",
                "order": 0,
            }
        })


class WorkflowConditionFilterParams(BaseModel):
    """Filter parameters for workflow conditions."""

    workflow_id: Optional[str] = Field(None, description="Filter by workflow ID")
    condition_type: Optional[WorkflowConditionTypeEnum] = Field(
        None, description="Filter by condition type"
    )
    name: Optional[str] = Field(None, description="Filter by name")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "condition_type": "field_value",
            }
        })


# Workflow Recipient DTOs
class WorkflowRecipientBaseDto(BaseModel):
    """Base DTO for workflow recipients."""

    recipient_type: WorkflowRecipientTypeEnum = Field(
        ..., description="Type of recipient"
    )
    recipient_id: str = Field(..., description="ID of the recipient")
    name: Optional[str] = Field(None, description="Display name for the recipient")
    notification_config: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration for notifications"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "recipient_type": "user",
                "recipient_id": "user123",
                "name": "John Doe",
                "notification_config": {"channel": "email", "priority": "high"},
            }
        })


class WorkflowRecipientCreateDto(WorkflowRecipientBaseDto):
    """DTO for creating workflow recipients."""

    action_id: Optional[str] = Field(None, description="ID of the associated action")


class WorkflowRecipientUpdateDto(BaseModel):
    """DTO for updating workflow recipients."""

    recipient_type: Optional[WorkflowRecipientTypeEnum] = Field(
        None, description="Type of recipient"
    )
    recipient_id: Optional[str] = Field(None, description="ID of the recipient")
    name: Optional[str] = Field(None, description="Display name for the recipient")
    notification_config: Optional[Dict[str, Any]] = Field(
        None, description="Configuration for notifications"
    )
    action_id: Optional[str] = Field(None, description="ID of the associated action")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "notification_config": {"channel": "sms", "priority": "urgent"},
            }
        })


class WorkflowRecipientViewDto(WorkflowRecipientBaseDto):
    """DTO for viewing workflow recipients."""

    id: str = Field(..., description="Unique identifier")
    workflow_id: str = Field(..., description="ID of the associated workflow")
    action_id: Optional[str] = Field(None, description="ID of the associated action")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "wr123e4567-e89b-12d3-a456-426614174000",
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "recipient_type": "user",
                "recipient_id": "user123",
                "name": "John Doe",
                "notification_config": {"channel": "email", "priority": "high"},
                "action_id": "wa123e4567-e89b-12d3-a456-426614174000",
            }
        })


class WorkflowRecipientFilterParams(BaseModel):
    """Filter parameters for workflow recipients."""

    workflow_id: Optional[str] = Field(None, description="Filter by workflow ID")
    recipient_type: Optional[WorkflowRecipientTypeEnum] = Field(
        None, description="Filter by recipient type"
    )
    action_id: Optional[str] = Field(None, description="Filter by action ID")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "recipient_type": "user",
            }
        })


# Workflow Action DTOs
class WorkflowActionBaseDto(BaseModel):
    """Base DTO for workflow actions."""

    action_type: WorkflowActionTypeEnum = Field(..., description="Type of action")
    action_config: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration for the action"
    )
    name: str = Field("", description="Name of the action")
    description: Optional[str] = Field(None, description="Description of the action")
    order: int = Field(0, description="Order in which the action is executed")
    is_active: bool = Field(True, description="Whether the action is active")
    retry_policy: Optional[Dict[str, Any]] = Field(
        None, description="Policy for retrying failed actions"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "action_type": "email",
                "action_config": {
                    "subject": "User Account Updated",
                    "template": "user-update-notification",
                    "from_email": "notifications@example.com",
                },
                "name": "Send Email Notification",
                "description": "Sends an email notification when a user account is updated",
                "order": 0,
                "is_active": True,
                "retry_policy": {"max_retries": 3, "retry_delay": 300},
            }
        }
    )

class WorkflowActionCreateDto(WorkflowActionBaseDto):
    """DTO for creating workflow actions."""

    recipients: Optional[List[WorkflowRecipientCreateDto]] = Field(
        None, description="Recipients for this action"
    )


class WorkflowActionUpdateDto(BaseModel):
    """DTO for updating workflow actions."""

    action_type: Optional[WorkflowActionTypeEnum] = Field(
        None, description="Type of action"
    )
    action_config: Optional[Dict[str, Any]] = Field(
        None, description="Configuration for the action"
    )
    name: Optional[str] = Field(None, description="Name of the action")
    description: Optional[str] = Field(None, description="Description of the action")
    order: Optional[int] = Field(
        None, description="Order in which the action is executed"
    )
    is_active: Optional[bool] = Field(None, description="Whether the action is active")
    retry_policy: Optional[Dict[str, Any]] = Field(
        None, description="Policy for retrying failed actions"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "action_config": {
                    "subject": "IMPORTANT: User Account Updated",
                    "template": "user-update-urgent-notification",
                },
                "name": "Send Urgent Email Notification",
                "is_active": False,
            }
        })


class WorkflowActionViewDto(WorkflowActionBaseDto):
    """DTO for viewing workflow actions."""

    id: str = Field(..., description="Unique identifier")
    workflow_id: str = Field(..., description="ID of the associated workflow")
    recipients: List[WorkflowRecipientViewDto] = Field(
        default_factory=list, description="Recipients for this action"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "wa123e4567-e89b-12d3-a456-426614174000",
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "action_type": "email",
                "action_config": {
                    "subject": "User Account Updated",
                    "template": "user-update-notification",
                    "from_email": "notifications@example.com",
                },
                "name": "Send Email Notification",
                "description": "Sends an email notification when a user account is updated",
                "order": 0,
                "is_active": True,
                "retry_policy": {"max_retries": 3, "retry_delay": 300},
                "recipients": [],
            }
        })


class WorkflowActionFilterParams(BaseModel):
    """Filter parameters for workflow actions."""

    workflow_id: Optional[str] = Field(None, description="Filter by workflow ID")
    action_type: Optional[WorkflowActionTypeEnum] = Field(
        None, description="Filter by action type"
    )
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    name: Optional[str] = Field(None, description="Filter by name")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "action_type": "email",
                "is_active": True,
            }
        })


# Workflow Execution Record DTOs
class WorkflowExecutionRecordBaseDto(BaseModel):
    """Base DTO for workflow execution records."""

    workflow_id: str = Field(..., description="ID of the associated workflow")
    trigger_event_id: str = Field(
        ..., description="ID of the event that triggered the workflow"
    )
    status: WorkflowExecutionStatusEnum = Field(
        WorkflowExecutionStatusEnum.PENDING, description="Status of the execution"
    )
    executed_at: datetime = Field(..., description="When the workflow was executed")
    completed_at: Optional[datetime] = Field(
        None, description="When the workflow execution completed"
    )
    result: Optional[Dict[str, Any]] = Field(
        None, description="Result of the workflow execution"
    )
    error: Optional[str] = Field(
        None, description="Error message if the workflow execution failed"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Context data for the workflow execution"
    )
    execution_time: Optional[float] = Field(
        None, description="Time taken to execute the workflow in milliseconds"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "trigger_event_id": "ev123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "executed_at": "2023-01-15T10:30:00Z",
                "completed_at": "2023-01-15T10:30:05Z",
                "result": {
                    "notifications_sent": 3,
                    "action_results": {"email": "success", "webhook": "success"},
                },
                "error": None,
                "context": {
                    "user_id": "user123",
                    "entity_type": "user",
                    "operation": "update",
                },
                "execution_time": 5000,
            }
        })


class WorkflowExecutionRecordCreateDto(WorkflowExecutionRecordBaseDto):
    """DTO for creating workflow execution records."""

    pass


class WorkflowExecutionRecordUpdateDto(BaseModel):
    """DTO for updating workflow execution records."""

    status: Optional[WorkflowExecutionStatusEnum] = Field(
        None, description="Status of the execution"
    )
    completed_at: Optional[datetime] = Field(
        None, description="When the workflow execution completed"
    )
    result: Optional[Dict[str, Any]] = Field(
        None, description="Result of the workflow execution"
    )
    error: Optional[str] = Field(
        None, description="Error message if the workflow execution failed"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Context data for the workflow execution"
    )
    execution_time: Optional[float] = Field(
        None, description="Time taken to execute the workflow in milliseconds"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "status": "failed",
                "completed_at": "2023-01-15T10:30:10Z",
                "error": "Failed to send email notification",
                "execution_time": 10000,
            }
        })


class WorkflowExecutionRecordViewDto(WorkflowExecutionRecordBaseDto):
    """DTO for viewing workflow execution records."""

    id: str = Field(..., description="Unique identifier")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "we123e4567-e89b-12d3-a456-426614174000",
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "trigger_event_id": "ev123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "executed_at": "2023-01-15T10:30:00Z",
                "completed_at": "2023-01-15T10:30:05Z",
                "result": {
                    "notifications_sent": 3,
                    "action_results": {"email": "success", "webhook": "success"},
                },
                "error": None,
                "context": {
                    "user_id": "user123",
                    "entity_type": "user",
                    "operation": "update",
                },
                "execution_time": 5000,
            }
        })


class WorkflowExecutionRecordFilterParams(BaseModel):
    """Filter parameters for workflow execution records."""

    workflow_id: Optional[str] = Field(None, description="Filter by workflow ID")
    status: Optional[WorkflowExecutionStatusEnum] = Field(
        None, description="Filter by status"
    )
    executed_after: Optional[datetime] = Field(
        None, description="Filter by executed after date"
    )
    executed_before: Optional[datetime] = Field(
        None, description="Filter by executed before date"
    )
    trigger_event_id: Optional[str] = Field(
        None, description="Filter by trigger event ID"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "workflow_id": "wf123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "executed_after": "2023-01-01T00:00:00Z",
            }
        })


# Workflow Definition DTOs
class WorkflowDefBaseDto(BaseModel):
    """Base DTO for workflow definitions."""

    name: str = Field(..., description="Name of the workflow")
    description: str = Field(..., description="Description of the workflow")
    status: WorkflowStatusEnum = Field(
        WorkflowStatusEnum.DRAFT, description="Status of the workflow"
    )
    version: str = Field("1.0.0", description="Version of the workflow")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "User Update Notification",
                "description": "Sends notifications when a user account is updated",
                "status": "draft",
                "version": "1.0.0",
            }
        })


class WorkflowDefCreateDto(WorkflowDefBaseDto):
    """DTO for creating workflow definitions."""

    triggers: Optional[List[WorkflowTriggerCreateDto]] = Field(
        None, description="Triggers for this workflow"
    )
    conditions: Optional[List[WorkflowConditionCreateDto]] = Field(
        None, description="Conditions for this workflow"
    )
    actions: Optional[List[WorkflowActionCreateDto]] = Field(
        None, description="Actions for this workflow"
    )
    recipients: Optional[List[WorkflowRecipientCreateDto]] = Field(
        None, description="Global recipients for this workflow"
    )


class WorkflowDefUpdateDto(BaseModel):
    """DTO for updating workflow definitions."""

    name: Optional[str] = Field(None, description="Name of the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    status: Optional[WorkflowStatusEnum] = Field(
        None, description="Status of the workflow"
    )
    version: Optional[str] = Field(None, description="Version of the workflow")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "User Profile Update Notification",
                "status": "active",
                "version": "1.1.0",
            }
        })


class WorkflowDefViewDto(WorkflowDefBaseDto):
    """DTO for viewing workflow definitions."""

    id: str = Field(..., description="Unique identifier")
    triggers: List[WorkflowTriggerViewDto] = Field(
        default_factory=list, description="Triggers for this workflow"
    )
    conditions: List[WorkflowConditionViewDto] = Field(
        default_factory=list, description="Conditions for this workflow"
    )
    actions: List[WorkflowActionViewDto] = Field(
        default_factory=list, description="Actions for this workflow"
    )
    recipients: List[WorkflowRecipientViewDto] = Field(
        default_factory=list, description="Global recipients for this workflow"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "wf123e4567-e89b-12d3-a456-426614174000",
                "name": "User Update Notification",
                "description": "Sends notifications when a user account is updated",
                "status": "active",
                "version": "1.0.0",
                "triggers": [],
                "conditions": [],
                "actions": [],
                "recipients": [],
            }
        })


class WorkflowDefFilterParams(BaseModel):
    """Filter parameters for workflow definitions."""

    name: Optional[str] = Field(None, description="Filter by name")
    status: Optional[WorkflowStatusEnum] = Field(None, description="Filter by status")
    entity_type: Optional[str] = Field(
        None, description="Filter by entity type (via triggers)"
    )
    operation: Optional[WorkflowDBEventEnum] = Field(
        None, description="Filter by operation (via triggers)"
    )
    contains_action_type: Optional[WorkflowActionTypeEnum] = Field(
        None, description="Filter by containing a specific action type"
    )

    model_config = ConfigDict(
        json_schema_extra = {"example": {"status": "active", "entity_type": "user"}}
    )


# Workflow Event DTOs
class WorkflowEventDto(BaseModel):
    """DTO for workflow events."""

    table_name: str = Field(
        ..., description="Name of the table that triggered the event"
    )
    schema_name: str = Field(
        ..., description="Name of the schema that contains the table"
    )
    operation: WorkflowDBEventEnum = Field(
        ..., description="Database operation that triggered the event"
    )
    timestamp: float = Field(..., description="Timestamp when the event occurred")
    payload: Dict[str, Any] = Field(..., description="Payload of the event")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Context data for the event"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "table_name": "users",
                "schema_name": "public",
                "operation": "update",
                "timestamp": 1673782200.0,
                "payload": {
                    "id": "user123",
                    "email": "user@example.com",
                    "status": "active",
                    "updated_at": "2023-01-15T10:30:00Z",
                },
                "context": {"user_id": "admin123", "session_id": "sess123456"},
            }
        })


# User DTOs for recipients
class UserViewDto(BaseModel):
    """DTO for viewing users."""

    id: str = Field(..., description="Unique identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(True, description="Whether the user is active")
    display_name: Optional[str] = Field(None, description="Display name")
    roles: List[str] = Field(
        default_factory=list, description="Roles assigned to the user"
    )

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "user123",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "is_active": True,
                "display_name": "John Doe",
                "roles": ["admin", "editor"],
            }
        })


# Update forward references
WorkflowActionViewDto.model_rebuild()
WorkflowDefViewDto.model_rebuild()
