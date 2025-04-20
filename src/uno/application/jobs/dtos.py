# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import (
    BaseModel,
    Field,
    validator,
    field_validator,
    ConfigDict,
    model_validator,
)


class PriorityEnum(str, Enum):
    """Priority levels for jobs."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class StatusEnum(str, Enum):
    """Status values for jobs."""

    PENDING = "pending"
    RESERVED = "reserved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobErrorDto(BaseModel):
    """DTO for job error information."""

    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    traceback: Optional[str] = Field(None, description="Error traceback")


class JobBaseDto(BaseModel):
    """Base DTO for job data."""

    task_name: str = Field(..., description="Task to execute")
    args: list[Any] = Field(
        default_factory=list, description="Positional arguments for task"
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Keyword arguments for task"
    )
    queue_name: str = Field("default", description="Queue to place job in")
    priority: PriorityEnum = Field(
        PriorityEnum.NORMAL, description="Job priority level"
    )


class CreateJobDto(JobBaseDto):
    """DTO for creating a new job."""

    scheduled_at: Optional[datetime] = Field(
        None, description="When to execute the job (None for immediate)"
    )
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    retry_delay: int = Field(60, ge=0, description="Delay between retries in seconds")
    timeout: Optional[int] = Field(
        None, ge=1, description="Timeout for job execution in seconds"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    version: Optional[str] = Field(None, description="Specific version of task to use")
    job_id: Optional[str] = Field(
        None, description="Specific ID for the job (generated if not provided)"
    )


class JobViewDto(BaseModel):
    """DTO for viewing job details."""

    id: str = Field(..., description="Unique job identifier")
    task_name: str = Field(..., description="Task being executed")
    args: list[Any] = Field(..., description="Positional arguments for task")
    kwargs: Dict[str, Any] = Field(..., description="Keyword arguments for task")
    queue_name: str = Field(..., description="Queue the job is in")
    priority: PriorityEnum = Field(..., description="Job priority level")
    status: StatusEnum = Field(..., description="Current job status")
    scheduled_at: Optional[datetime] = Field(
        None, description="When the job is scheduled to run"
    )
    created_at: datetime = Field(..., description="When the job was created")
    started_at: Optional[datetime] = Field(
        None, description="When the job started execution"
    )
    completed_at: Optional[datetime] = Field(
        None, description="When the job finished execution"
    )
    result: Optional[Any] = Field(None, description="Job execution result")
    error: Optional[JobErrorDto] = Field(
        None, description="Error information if job failed"
    )
    retry_count: int = Field(..., description="Current retry count")
    max_retries: int = Field(..., description="Maximum retry attempts")
    retry_delay: int = Field(..., description="Delay between retries in seconds")
    tags: list[str] = Field(..., description="Tags for categorization")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    worker_id: Optional[str] = Field(
        None, description="ID of worker processing the job"
    )
    timeout: Optional[int] = Field(
        None, description="Timeout for job execution in seconds"
    )
    version: Optional[str] = Field(None, description="Version of task being used")
    duration: Optional[float] = Field(
        None, description="Duration of execution in seconds"
    )


class JobFilterParams(BaseModel):
    """Parameters for filtering jobs."""

    queue_name: Optional[str] = Field(None, description="Filter by queue name")
    status: list[str] | None = Field(None, description="Filter by job status")
    priority: Optional[str] = Field(None, description="Filter by priority level")
    tags: list[str] | None = Field(None, description="Filter by tags")
    worker_id: Optional[str] = Field(None, description="Filter by worker ID")
    before: Optional[datetime] = Field(
        None, description="Filter by creation before this time"
    )
    after: Optional[datetime] = Field(
        None, description="Filter by creation after this time"
    )
    limit: int = Field(
        100, ge=1, le=1000, description="Maximum number of jobs to return"
    )
    offset: int = Field(0, ge=0, description="Number of jobs to skip")
    order_by: str = Field("created_at", description="Field to order by")
    order_dir: str = Field("desc", description="Order direction (asc/desc)")

    @field_validator("status")
    def validate_status(cls, v):
        if v is not None:
            for status in v:
                if status not in [s.value for s in StatusEnum]:
                    raise ValueError(f"Invalid status: {status}")
        return v

    @field_validator("priority")
    def validate_priority(cls, v):
        if v is not None and v not in [p.value for p in PriorityEnum]:
            raise ValueError(f"Invalid priority: {v}")
        return v

    @field_validator("order_by")
    def validate_order_by(cls, v):
        valid_fields = [
            "created_at",
            "started_at",
            "completed_at",
            "priority",
            "status",
        ]
        if v not in valid_fields:
            raise ValueError(
                f"Invalid order_by field: {v}. Valid fields are: {', '.join(valid_fields)}"
            )
        return v

    @field_validator("order_dir")
    def validate_order_dir(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("Order direction must be 'asc' or 'desc'")
        return v


class JobListDto(BaseModel):
    """DTO for a list of jobs with pagination information."""

    items: list[JobViewDto] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs matching the filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class CancelJobDto(BaseModel):
    """DTO for cancelling a job."""

    reason: Optional[str] = Field(None, description="Reason for cancellation")


class JobStatsDto(BaseModel):
    """DTO for job statistics."""

    total_jobs: int = Field(..., description="Total number of jobs")
    pending_jobs: int = Field(..., description="Number of pending jobs")
    running_jobs: int = Field(..., description="Number of running jobs")
    completed_jobs: int = Field(..., description="Number of completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    cancelled_jobs: int = Field(..., description="Number of cancelled jobs")
    avg_wait_time: Optional[float] = Field(
        None, description="Average wait time in seconds"
    )
    avg_run_time: Optional[float] = Field(
        None, description="Average run time in seconds"
    )
    by_queue: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Statistics by queue"
    )
    by_priority: Dict[str, int] = Field(
        default_factory=dict, description="Job count by priority"
    )


class ScheduleIntervalDto(BaseModel):
    """DTO for interval-based scheduling."""

    seconds: int = Field(0, ge=0, description="Seconds component of interval")
    minutes: int = Field(0, ge=0, description="Minutes component of interval")
    hours: int = Field(0, ge=0, description="Hours component of interval")
    days: int = Field(0, ge=0, description="Days component of interval")

    @model_validator(mode="after")
    def validate_interval(self):
        if (self.seconds + self.minutes + self.hours + self.days) == 0:
            raise ValueError("At least one interval field must be greater than 0")
        return self


class CreateScheduleDto(BaseModel):
    """DTO for creating a new schedule."""

    name: str = Field(..., description="Name for the schedule")
    task_name: str = Field(..., description="Task to execute")
    cron_expression: Optional[str] = Field(
        None,
        description="Cron expression for scheduling (mutually exclusive with interval)",
    )
    interval: Optional[ScheduleIntervalDto] = Field(
        None,
        description="Interval for scheduling (mutually exclusive with cron_expression)",
    )
    args: list[Any] = Field(
        default_factory=list, description="Positional arguments for task"
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Keyword arguments for task"
    )
    queue_name: str = Field("default", description="Queue to use")
    priority: PriorityEnum = Field(
        PriorityEnum.NORMAL, description="Job priority level"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    retry_delay: int = Field(60, ge=0, description="Delay between retries in seconds")
    timeout: Optional[int] = Field(
        None, ge=1, description="Timeout for job execution in seconds"
    )
    version: Optional[str] = Field(None, description="Specific version of task to use")

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.cron_expression is None and self.interval is None:
            raise ValueError("Either cron_expression or interval must be provided")
        if self.cron_expression is not None and self.interval is not None:
            raise ValueError(
                "Only one of cron_expression or interval should be provided"
            )
        return self


class UpdateScheduleDto(BaseModel):
    """DTO for updating an existing schedule."""

    name: Optional[str] = Field(None, description="Name for the schedule")
    cron_expression: Optional[str] = Field(
        None, description="Cron expression for scheduling"
    )
    interval: Optional[ScheduleIntervalDto] = Field(
        None, description="Interval for scheduling"
    )
    args: Optional[list[Any]] = Field(None, description="Positional arguments for task")
    kwargs: Optional[Dict[str, Any]] = Field(
        None, description="Keyword arguments for task"
    )
    queue_name: Optional[str] = Field(None, description="Queue to use")
    priority: Optional[PriorityEnum] = Field(None, description="Job priority level")
    tags: list[str] | None = Field(None, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    max_retries: Optional[int] = Field(None, ge=0, description="Maximum retry attempts")
    retry_delay: Optional[int] = Field(
        None, ge=0, description="Delay between retries in seconds"
    )
    timeout: Optional[int] = Field(
        None, ge=1, description="Timeout for job execution in seconds"
    )
    status: Optional[str] = Field(None, description="Schedule status (active/paused)")

    @field_validator("status")
    def validate_status(cls, v):
        if v is not None and v not in ["active", "paused"]:
            raise ValueError("Status must be either 'active' or 'paused'")
        return v


class ScheduleViewDto(BaseModel):
    """DTO for viewing schedule details."""

    id: str = Field(..., description="Unique schedule identifier")
    name: str = Field(..., description="Schedule name")
    task_name: str = Field(..., description="Task being executed")
    status: str = Field(..., description="Schedule status (active/paused)")
    cron_expression: Optional[str] = Field(
        None, description="Cron expression for scheduling"
    )
    interval: Optional[ScheduleIntervalDto] = Field(
        None, description="Interval for scheduling"
    )
    args: list[Any] = Field(..., description="Positional arguments for task")
    kwargs: Dict[str, Any] = Field(..., description="Keyword arguments for task")
    queue_name: str = Field(..., description="Queue to use")
    priority: PriorityEnum = Field(..., description="Job priority level")
    tags: list[str] = Field(..., description="Tags for categorization")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    max_retries: int = Field(..., description="Maximum retry attempts")
    retry_delay: int = Field(..., description="Delay between retries in seconds")
    timeout: Optional[int] = Field(
        None, description="Timeout for job execution in seconds"
    )
    last_run_at: Optional[datetime] = Field(
        None, description="When the schedule last ran"
    )
    next_run_at: Optional[datetime] = Field(
        None, description="When the schedule will next run"
    )
    created_at: datetime = Field(..., description="When the schedule was created")
    updated_at: datetime = Field(..., description="When the schedule was last updated")
    version: Optional[str] = Field(None, description="Version of task being used")


class ScheduleFilterParams(BaseModel):
    """Parameters for filtering schedules."""

    status: Optional[str] = Field(None, description="Filter by status (active/paused)")
    tags: list[str] | None = Field(None, description="Filter by tags")
    limit: int = Field(
        100, ge=1, le=1000, description="Maximum number of schedules to return"
    )
    offset: int = Field(0, ge=0, description="Number of schedules to skip")

    @field_validator("status")
    def validate_status(cls, v):
        if v is not None and v not in ["active", "paused"]:
            raise ValueError("Status must be either 'active' or 'paused'")
        return v


class ScheduleListDto(BaseModel):
    """DTO for a list of schedules with pagination information."""

    items: list[ScheduleViewDto] = Field(..., description="List of schedules")
    total: int = Field(..., description="Total number of schedules matching the filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class TaskInfoDto(BaseModel):
    """DTO for task information."""

    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    is_async: bool = Field(..., description="Whether the task is async")
    timeout: Optional[int] = Field(None, description="Task timeout in seconds")
    max_retries: int = Field(..., description="Default max retries")
    retry_delay: int = Field(..., description="Default retry delay in seconds")
    queue: str = Field(..., description="Default queue")
    version: Optional[str] = Field(None, description="Task version")


class TaskListDto(BaseModel):
    """DTO for a list of tasks."""

    items: list[TaskInfoDto] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")


class QueueInfoDto(BaseModel):
    """DTO for queue information."""

    name: str = Field(..., description="Queue name")
    size: int = Field(..., description="Number of jobs in queue")
    is_paused: bool = Field(..., description="Whether the queue is paused")


class QueueListDto(BaseModel):
    """DTO for a list of queues."""

    items: list[QueueInfoDto] = Field(..., description="List of queues")
    total: int = Field(..., description="Total number of queues")


class RunSyncJobDto(JobBaseDto):
    """DTO for running a job synchronously."""

    timeout: Optional[int] = Field(
        None, ge=1, description="Timeout for job execution in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    version: Optional[str] = Field(None, description="Specific version of task to use")
