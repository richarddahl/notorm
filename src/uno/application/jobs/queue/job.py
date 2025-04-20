"""Job data model for the background processing system.

This module defines the core Job class used throughout the system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
import json

from pydantic import BaseModel, Field, validator
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus


class Job(BaseModel):
    """Represents a job to be processed by the background processing system.

    A job encapsulates a task to be executed, along with its parameters,
    status information, and metadata.
    """

    # Core job identity and task
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task: str  # Module.function reference
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)

    # Queue and scheduling
    queue: str = "default"
    priority: Priority = Priority.NORMAL
    status: JobStatus = JobStatus.PENDING
    scheduled_for: Optional[datetime] = None

    # Execution tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: dict[str, Any] | None = None

    # Retry configuration
    retry_count: int = 0
    max_retries: int = 0
    retry_delay: int = 60  # seconds

    # Metadata
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Worker tracking
    worker_id: str | None = None

    # Timeout configuration
    timeout: int | None = None  # seconds

    # Version
    version: str | None = None

    @property
    def duration(self) -> Optional[float]:
        """Calculate the duration of the job execution in seconds.

        Returns:
            Duration in seconds or None if the job hasn't started or completed
        """
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.now(datetime.UTC)
        return (end_time - self.started_at).total_seconds()

    @property
    def is_due(self) -> bool:
        """Check if the job is due for execution.

        Returns:
            True if the job is due for execution, False otherwise
        """
        if not self.scheduled_for:
            return True

        return datetime.now(datetime.UTC) >= self.scheduled_for

    @property
    def can_retry(self) -> bool:
        """Check if the job can be retried after a failure.

        Returns:
            True if the job can be retried, False otherwise
        """
        return self.retry_count < self.max_retries

    def mark_reserved(self, worker_id: str) -> None:
        """Mark the job as reserved by a worker.

        Args:
            worker_id: The ID of the worker reserving the job
        """
        self.status = JobStatus.RESERVED
        self.worker_id = worker_id

    def mark_running(self) -> None:
        """Mark the job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(datetime.UTC)

    def mark_completed(self, result: Any = None) -> None:
        """Mark the job as completed.

        Args:
            result: Optional result data from the job execution
        """
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(datetime.UTC)
        self.result = result

    def mark_failed(self, error_info: dict[str, Any]) -> None:
        """Mark the job as failed.

        Args:
            error_info: Information about the error that caused the failure
        """
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(datetime.UTC)
        self.error = error_info

    def mark_retry(self, error_info: dict[str, Any]) -> None:
        """Mark the job for retry after a failure.

        Args:
            error_info: Information about the error that caused the failure
        """
        self.status = JobStatus.RETRYING
        self.retry_count += 1
        self.error = error_info
        self.worker_id = None

    def mark_cancelled(self, reason: str | None = None) -> None:
        """Mark the job as cancelled.

        Args:
            reason: Optional reason for cancellation
        """
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(datetime.UTC)

        if reason:
            self.metadata["cancel_reason"] = reason

    def mark_timeout(self) -> None:
        """Mark the job as timed out."""
        self.status = JobStatus.TIMEOUT
        self.completed_at = datetime.now(datetime.UTC)
        self.error = {
            "type": "TimeoutError",
            "message": f"Job exceeded timeout of {self.timeout} seconds",
        }

    @field_validator("priority", pre=True)
    def validate_priority(cls, value: Union[Priority, str, int]) -> Priority:
        """Validate and convert priority value.

        Args:
            value: Priority as enum, string, or integer

        Returns:
            Priority enum value

        Raises:
            ValueError: If the priority value is not valid
        """
        if isinstance(value, Priority):
            return value

        if isinstance(value, str):
            return Priority.from_string(value)

        if isinstance(value, int):
            for priority in Priority:
                if priority.value == value:
                    return priority

            # If not found, find the closest one
            valid_values = sorted([p.value for p in Priority])

            # Use normal priority as a fallback
            if value < valid_values[0]:
                return Priority.CRITICAL
            elif value > valid_values[-1]:
                return Priority.LOW
            else:
                return Priority.NORMAL

        raise ValueError(f"Invalid priority value: {value}")

    def to_dict(self) -> dict[str, Any]:
        """Convert the job to a dictionary suitable for storage.

        Returns:
            Dictionary representation of the job
        """
        data = self.dict(exclude_none=True)

        # Convert enum values to their string representations for better readability
        if "priority" in data:
            data["priority"] = self.priority.name

        if "status" in data:
            data["status"] = self.status.name

        # Convert datetime objects to ISO format strings
        for field in ["created_at", "started_at", "completed_at", "scheduled_for"]:
            if field in data and data[field] is not None:
                data[field] = data[field].isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        """Create a job from a dictionary.

        Args:
            data: Dictionary representation of a job

        Returns:
            Job instance
        """
        # Make a copy to avoid modifying the input
        job_data = data.copy()

        # Convert string values back to enums
        if "priority" in job_data and isinstance(job_data["priority"], str):
            job_data["priority"] = Priority.from_string(job_data["priority"])

        if "status" in job_data and isinstance(job_data["status"], str):
            job_data["status"] = JobStatus[job_data["status"]]

        # Convert ISO format strings back to datetime objects
        for field in ["created_at", "started_at", "completed_at", "scheduled_for"]:
            if (
                field in job_data
                and job_data[field] is not None
                and isinstance(job_data[field], str)
            ):
                job_data[field] = datetime.fromisoformat(job_data[field])

        return cls(**job_data)
