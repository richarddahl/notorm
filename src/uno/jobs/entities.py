# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from uno.domain.core import Entity, AggregateRoot, ValueObject


class JobPriority(IntEnum):
    """Priority levels for jobs."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    
    @classmethod
    def from_string(cls, value: str) -> "JobPriority":
        """Convert a string to a priority enum value."""
        try:
            return cls[value.upper()]
        except KeyError:
            valid_values = ", ".join(p.name.lower() for p in cls)
            raise ValueError(f"Invalid priority: {value}. Valid values are: {valid_values}")


class JobStatus(Enum):
    """Status values for jobs."""
    PENDING = "pending"     # Waiting to be processed
    RESERVED = "reserved"   # Reserved by a worker but not started
    RUNNING = "running"     # Currently being processed
    COMPLETED = "completed" # Successfully completed
    FAILED = "failed"       # Failed and won't be retried
    RETRYING = "retrying"   # Failed but will be retried
    CANCELLED = "cancelled" # Cancelled by user
    TIMEOUT = "timeout"     # Exceeded timeout limit
    
    @property
    def is_active(self) -> bool:
        """Check if the status is an active status."""
        return self in [self.PENDING, self.RESERVED, self.RUNNING, self.RETRYING]
    
    @property
    def is_terminal(self) -> bool:
        """Check if the status is a terminal status."""
        return self in [self.COMPLETED, self.FAILED, self.CANCELLED, self.TIMEOUT]


@dataclass
class JobError(ValueObject):
    """Error information for a failed job."""
    type: str
    message: str
    traceback: Optional[str] = None
    
    @classmethod
    def from_exception(cls, exception: Exception, include_traceback: bool = True) -> "JobError":
        """Create a JobError from an exception."""
        import traceback
        
        return cls(
            type=type(exception).__name__,
            message=str(exception),
            traceback=traceback.format_exc() if include_traceback else None
        )


@dataclass
class Job(Entity):
    """A job to be processed by the background system."""
    
    id: str
    task_name: str
    queue_name: str = "default"
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[JobError] = None
    retry_count: int = 0
    max_retries: int = 0
    retry_delay: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    worker_id: Optional[str] = None
    timeout: Optional[timedelta] = None
    version: Optional[str] = None

    @classmethod
    def create(
        cls,
        task_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        queue_name: str = "default",
        priority: JobPriority = JobPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay: Union[int, timedelta] = 60,
        timeout: Optional[Union[int, timedelta]] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> "Job":
        """Create a new job entity."""
        # Convert retry_delay to timedelta if it's an integer
        if isinstance(retry_delay, int):
            retry_delay = timedelta(seconds=retry_delay)
        
        # Convert timeout to timedelta if it's an integer
        if isinstance(timeout, int):
            timeout = timedelta(seconds=timeout)
        
        return cls(
            id=job_id or str(uuid.uuid4()),
            task_name=task_name,
            args=args or [],
            kwargs=kwargs or {},
            queue_name=queue_name,
            priority=priority,
            scheduled_at=scheduled_at,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            tags=tags or set(),
            metadata=metadata or {},
            version=version,
        )
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate the duration of the job execution."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(UTC)
        return end_time - self.started_at
    
    @property
    def is_due(self) -> bool:
        """Check if the job is due for execution."""
        if not self.scheduled_at:
            return True
        
        return datetime.now(UTC) >= self.scheduled_at
    
    @property
    def can_retry(self) -> bool:
        """Check if the job can be retried after a failure."""
        return self.retry_count < self.max_retries
    
    def mark_reserved(self, worker_id: str) -> None:
        """Mark the job as reserved by a worker."""
        self.status = JobStatus.RESERVED
        self.worker_id = worker_id
    
    def mark_running(self) -> None:
        """Mark the job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(UTC)
    
    def mark_completed(self, result: Any = None) -> None:
        """Mark the job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.result = result
    
    def mark_failed(self, error: Union[JobError, Exception, str, Dict[str, Any]]) -> None:
        """Mark the job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(UTC)
        
        # Convert the error to a JobError if it's not already
        if isinstance(error, JobError):
            self.error = error
        elif isinstance(error, Exception):
            self.error = JobError.from_exception(error)
        elif isinstance(error, str):
            self.error = JobError(type="Error", message=error, traceback=None)
        elif isinstance(error, dict):
            self.error = JobError(
                type=error.get("type", "Error"),
                message=error.get("message", str(error)),
                traceback=error.get("traceback"),
            )
    
    def mark_retry(self, error: Union[JobError, Exception, str, Dict[str, Any]]) -> None:
        """Mark the job for retry after a failure."""
        self.status = JobStatus.RETRYING
        self.retry_count += 1
        
        # Convert the error to a JobError if it's not already
        if isinstance(error, JobError):
            self.error = error
        elif isinstance(error, Exception):
            self.error = JobError.from_exception(error)
        elif isinstance(error, str):
            self.error = JobError(type="Error", message=error, traceback=None)
        elif isinstance(error, dict):
            self.error = JobError(
                type=error.get("type", "Error"),
                message=error.get("message", str(error)),
                traceback=error.get("traceback"),
            )
        
        self.worker_id = None
    
    def mark_cancelled(self, reason: Optional[str] = None) -> None:
        """Mark the job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(UTC)
        
        if reason:
            self.metadata["cancel_reason"] = reason
    
    def mark_timeout(self) -> None:
        """Mark the job as timed out."""
        self.status = JobStatus.TIMEOUT
        self.completed_at = datetime.now(UTC)
        self.error = JobError(
            type="TimeoutError",
            message=f"Job exceeded timeout of {self.timeout.total_seconds() if self.timeout else 'unknown'} seconds",
            traceback=None,
        )


@dataclass
class ScheduleInterval(ValueObject):
    """Interval-based scheduling configuration."""
    seconds: int = 0
    minutes: int = 0
    hours: int = 0
    days: int = 0
    
    @property
    def total_seconds(self) -> int:
        """Get the total duration in seconds."""
        return (
            self.seconds +
            self.minutes * 60 +
            self.hours * 3600 +
            self.days * 86400
        )
    
    @property
    def timedelta(self) -> timedelta:
        """Convert to a timedelta."""
        return timedelta(
            seconds=self.seconds,
            minutes=self.minutes,
            hours=self.hours,
            days=self.days,
        )


@dataclass
class Schedule(Entity):
    """A schedule for recurring job execution."""
    
    id: str
    name: str
    task_name: str
    status: str = "active"  # active or paused
    cron_expression: Optional[str] = None
    interval: Optional[ScheduleInterval] = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    queue_name: str = "default"
    priority: JobPriority = JobPriority.NORMAL
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    retry_delay: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    timeout: Optional[timedelta] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        name: str,
        task_name: str,
        cron_expression: Optional[str] = None,
        interval: Optional[ScheduleInterval] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        queue_name: str = "default",
        priority: JobPriority = JobPriority.NORMAL,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: Union[int, timedelta] = 60,
        timeout: Optional[Union[int, timedelta]] = None,
        version: Optional[str] = None,
        schedule_id: Optional[str] = None,
    ) -> "Schedule":
        """Create a new schedule entity."""
        # Validate that either cron_expression or interval is provided
        if cron_expression is None and interval is None:
            raise ValueError("Either cron_expression or interval must be provided")
        
        if cron_expression is not None and interval is not None:
            raise ValueError("Only one of cron_expression or interval should be provided")
        
        # Convert retry_delay to timedelta if it's an integer
        if isinstance(retry_delay, int):
            retry_delay = timedelta(seconds=retry_delay)
        
        # Convert timeout to timedelta if it's an integer
        if isinstance(timeout, int):
            timeout = timedelta(seconds=timeout)
        
        # Calculate next_run_at
        next_run_at = None
        if cron_expression:
            # Use croniter if available
            try:
                from croniter import croniter
                next_run_at = croniter(cron_expression, datetime.now(UTC)).get_next(datetime)
            except ImportError:
                pass
        elif interval:
            next_run_at = datetime.now(UTC) + interval.timedelta
        
        return cls(
            id=schedule_id or str(uuid.uuid4()),
            name=name,
            task_name=task_name,
            cron_expression=cron_expression,
            interval=interval,
            args=args or [],
            kwargs=kwargs or {},
            queue_name=queue_name,
            priority=priority,
            tags=tags or set(),
            metadata=metadata or {},
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            next_run_at=next_run_at,
            version=version,
        )
    
    def pause(self) -> None:
        """Pause the schedule."""
        self.status = "paused"
        self.updated_at = datetime.now(UTC)
    
    def resume(self) -> None:
        """Resume the schedule."""
        self.status = "active"
        self.updated_at = datetime.now(UTC)
        
        # Recalculate next_run_at if needed
        if not self.next_run_at or self.next_run_at < datetime.now(UTC):
            if self.cron_expression:
                try:
                    from croniter import croniter
                    self.next_run_at = croniter(self.cron_expression, datetime.now(UTC)).get_next(datetime)
                except ImportError:
                    pass
            elif self.interval:
                self.next_run_at = datetime.now(UTC) + self.interval.timedelta
    
    def update_next_run(self) -> None:
        """Update the next run time based on the schedule configuration."""
        self.last_run_at = datetime.now(UTC)
        
        if self.cron_expression:
            try:
                from croniter import croniter
                self.next_run_at = croniter(self.cron_expression, self.last_run_at).get_next(datetime)
            except ImportError:
                pass
        elif self.interval:
            self.next_run_at = self.last_run_at + self.interval.timedelta
        
        self.updated_at = datetime.now(UTC)
    
    def is_due(self) -> bool:
        """Check if the schedule is due for execution."""
        if self.status != "active":
            return False
        
        if not self.next_run_at:
            return False
        
        return datetime.now(UTC) >= self.next_run_at
    
    def create_job(self) -> Job:
        """Create a job from this schedule."""
        return Job.create(
            task_name=self.task_name,
            args=self.args,
            kwargs=self.kwargs,
            queue_name=self.queue_name,
            priority=self.priority,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            timeout=self.timeout,
            tags=self.tags,
            metadata={
                **self.metadata,
                "schedule_id": self.id,
                "schedule_name": self.name,
            },
            version=self.version,
        )