from typing import Dict, List, Optional, Any, Set
import asyncio
from datetime import datetime, timedelta, UTC
import uuid

from sqlalchemy import (
    Table,
    Column,
    String,
    DateTime,
    Integer,
    JSON,
    Boolean,
    ForeignKey,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import and_, or_

from uno.core.errors.result import Result
from uno.database.enhanced_session import get_enhanced_session
from uno.database.db_manager import get_db_manager
from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus
from uno.jobs.scheduler.schedules import Schedule, ScheduleDefinition
from uno.jobs.storage.base import JobStorageProtocol


class DatabaseJobStorage(JobStorageProtocol):
    """Database-backed job storage implementation using SQLAlchemy."""

    def __init__(self, session_factory=None):
        """Initialize the database storage backend.

        Args:
            session_factory: Optional function to provide database sessions.
                If not provided, will use the default session factory.
        """
        self._session_factory = session_factory or get_enhanced_session
        self._setup_tables()
        self._lock = asyncio.Lock()

    def _setup_tables(self):
        """Set up the database tables for job storage."""
        db_manager = get_db_manager()
        metadata = db_manager.metadata

        # Define the jobs table
        self.jobs_table = Table(
            "jobs",
            metadata,
            Column("id", String, primary_key=True),
            Column("queue_name", String, nullable=False, index=True),
            Column("status", String, nullable=False, index=True),
            Column("task_name", String, nullable=False, index=True),
            Column("args", JSON, nullable=True),
            Column("kwargs", JSON, nullable=True),
            Column("result", JSON, nullable=True),
            Column("error", JSON, nullable=True),
            Column("created_at", DateTime, nullable=False, index=True),
            Column("updated_at", DateTime, nullable=False),
            Column("scheduled_at", DateTime, nullable=True, index=True),
            Column("started_at", DateTime, nullable=True),
            Column("completed_at", DateTime, nullable=True),
            Column("priority", Integer, nullable=False, index=True),
            Column("retries", Integer, nullable=False, default=0),
            Column("max_retries", Integer, nullable=False),
            Column("retry_delay", Integer, nullable=True),
            Column("timeout", Integer, nullable=True),
            Column("is_scheduled", Boolean, nullable=False, default=False),
            Column("metadata", JSON, nullable=True),
            Column("tags", JSON, nullable=True),
        )

        # Define the schedules table
        self.schedules_table = Table(
            "job_schedules",
            metadata,
            Column("id", String, primary_key=True),
            Column("name", String, nullable=False, unique=True, index=True),
            Column("task_name", String, nullable=False, index=True),
            Column("schedule_type", String, nullable=False),
            Column("schedule_data", JSON, nullable=False),
            Column("args", JSON, nullable=True),
            Column("kwargs", JSON, nullable=True),
            Column("queue_name", String, nullable=False),
            Column("priority", Integer, nullable=False),
            Column("max_retries", Integer, nullable=False),
            Column("retry_delay", Integer, nullable=True),
            Column("timeout", Integer, nullable=True),
            Column("created_at", DateTime, nullable=False),
            Column("updated_at", DateTime, nullable=False),
            Column("last_run_at", DateTime, nullable=True),
            Column("next_run_at", DateTime, nullable=True, index=True),
            Column("metadata", JSON, nullable=True),
            Column("enabled", Boolean, nullable=False, default=True),
        )

    async def _get_session(self) -> AsyncSession:
        """Get a database session.

        Returns:
            An async database session.
        """
        return await self._session_factory()

    async def add_job(self, job: Job) -> Result[str]:
        """Add a job to storage.

        Args:
            job: The job to add.

        Returns:
            Result with the job ID if successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                job_data = {
                    "id": job.id,
                    "queue_name": job.queue_name,
                    "status": job.status.value,
                    "task_name": job.task_name,
                    "args": job.args or [],
                    "kwargs": job.kwargs or {},
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "scheduled_at": job.scheduled_at,
                    "priority": job.priority.value,
                    "retries": job.retries,
                    "max_retries": job.max_retries,
                    "retry_delay": (
                        job.retry_delay.total_seconds() if job.retry_delay else None
                    ),
                    "timeout": job.timeout.total_seconds() if job.timeout else None,
                    "is_scheduled": job.is_scheduled,
                    "metadata": job.metadata,
                    "tags": list(job.tags) if job.tags else [],
                }

                await session.execute(self.jobs_table.insert().values(**job_data))
                await session.commit()

                return Result.success(job.id)
        except Exception as e:
            return Result.failure(f"Failed to add job to database: {str(e)}")

    async def get_job(self, job_id: str) -> Result[Optional[Job]]:
        """Get a job by ID.

        Args:
            job_id: The ID of the job to retrieve.

        Returns:
            Result with the job if found, None if not found.
        """
        try:
            session = await self._get_session()
            query = select([self.jobs_table]).where(self.jobs_table.c.id == job_id)
            result = await session.execute(query)
            job_data = result.fetchone()

            if not job_data:
                return Result.success(None)

            job = self._job_from_row(dict(job_data))
            return Result.success(job)
        except Exception as e:
            return Result.failure(f"Failed to retrieve job from database: {str(e)}")

    async def update_job(self, job: Job) -> Result[bool]:
        """Update a job in storage.

        Args:
            job: The job to update.

        Returns:
            Result with True if the update was successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                job_data = {
                    "status": job.status.value,
                    "result": job.result,
                    "error": job.error,
                    "updated_at": datetime.now(datetime.UTC),
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "retries": job.retries,
                    "metadata": job.metadata,
                }

                update_query = (
                    self.jobs_table.update()
                    .where(self.jobs_table.c.id == job.id)
                    .values(**job_data)
                )

                await session.execute(update_query)
                await session.commit()

                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to update job in database: {str(e)}")

    async def delete_job(self, job_id: str) -> Result[bool]:
        """Delete a job from storage.

        Args:
            job_id: The ID of the job to delete.

        Returns:
            Result with True if the deletion was successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                delete_query = self.jobs_table.delete().where(
                    self.jobs_table.c.id == job_id
                )
                await session.execute(delete_query)
                await session.commit()

                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to delete job from database: {str(e)}")

    async def enqueue_job(self, job: Job) -> Result[bool]:
        """Enqueue a job by adding it to storage or updating its status if it exists.

        Args:
            job: The job to enqueue.

        Returns:
            Result with True if the operation was successful.
        """
        try:
            job.status = JobStatus.PENDING
            job.updated_at = datetime.now(datetime.UTC)

            # Check if job already exists
            get_result = await self.get_job(job.id)
            if not get_result.is_success:
                return Result.failure(
                    f"Failed to check if job exists: {get_result.error}"
                )

            existing_job = get_result.value

            if existing_job:
                return await self.update_job(job)
            else:
                add_result = await self.add_job(job)
                return Result.success(add_result.is_success)
        except Exception as e:
            return Result.failure(f"Failed to enqueue job: {str(e)}")

    async def dequeue_job(
        self, queue_name: str, statuses: Optional[list[JobStatus]] = None
    ) -> Result[Optional[Job]]:
        """Dequeue a job from the specified queue with the given statuses.

        Args:
            queue_name: The name of the queue to dequeue from.
            statuses: Optional list of statuses to filter by. Defaults to [JobStatus.PENDING].

        Returns:
            Result with the dequeued job, or None if no job is available.
        """
        if statuses is None:
            statuses = [JobStatus.PENDING]

        try:
            async with self._lock:
                session = await self._get_session()

                # Construct the query to find the highest priority job matching criteria
                status_values = [s.value for s in statuses]

                query = (
                    select([self.jobs_table])
                    .where(
                        and_(
                            self.jobs_table.c.queue_name == queue_name,
                            self.jobs_table.c.status.in_(status_values),
                            or_(
                                self.jobs_table.c.scheduled_at.is_(None),
                                self.jobs_table.c.scheduled_at
                                <= datetime.now(datetime.UTC),
                            ),
                        )
                    )
                    .order_by(
                        self.jobs_table.c.priority.asc(),  # Lower priority value = higher priority
                        self.jobs_table.c.created_at.asc(),  # Older jobs first (FIFO)
                    )
                    .limit(1)
                )

                result = await session.execute(query)
                job_data = result.fetchone()

                if not job_data:
                    return Result.success(None)

                job_dict = dict(job_data)
                job = self._job_from_row(job_dict)

                # Update the job status to RUNNING
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(datetime.UTC)
                job.updated_at = datetime.now(datetime.UTC)

                update_result = await self.update_job(job)
                if not update_result.is_success:
                    return update_result

                return Result.success(job)
        except Exception as e:
            return Result.failure(f"Failed to dequeue job from database: {str(e)}")

    async def get_queue_length(
        self, queue_name: str, statuses: Optional[list[JobStatus]] = None
    ) -> Result[int]:
        """Get the length of a queue with jobs in the specified statuses.

        Args:
            queue_name: The name of the queue.
            statuses: Optional list of statuses to filter by. Defaults to [JobStatus.PENDING].

        Returns:
            Result with the number of jobs in the queue.
        """
        if statuses is None:
            statuses = [JobStatus.PENDING]

        try:
            session = await self._get_session()

            status_values = [s.value for s in statuses]

            query = select([self.jobs_table.c.id]).where(
                and_(
                    self.jobs_table.c.queue_name == queue_name,
                    self.jobs_table.c.status.in_(status_values),
                )
            )

            result = await session.execute(query)
            count = len(result.fetchall())

            return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to get queue length from database: {str(e)}")

    async def get_jobs_by_status(
        self,
        statuses: list[JobStatus],
        queue_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[list[Job]]:
        """Get jobs by status.

        Args:
            statuses: List of statuses to filter by.
            queue_name: Optional queue name to filter by.
            limit: Maximum number of jobs to return.
            offset: Offset for pagination.

        Returns:
            Result with a list of jobs.
        """
        try:
            session = await self._get_session()

            status_values = [s.value for s in statuses]

            query = select([self.jobs_table]).where(
                self.jobs_table.c.status.in_(status_values)
            )

            if queue_name:
                query = query.where(self.jobs_table.c.queue_name == queue_name)

            query = (
                query.order_by(self.jobs_table.c.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(query)
            job_rows = result.fetchall()

            jobs = [self._job_from_row(dict(row)) for row in job_rows]

            return Result.success(jobs)
        except Exception as e:
            return Result.failure(
                f"Failed to get jobs by status from database: {str(e)}"
            )

    async def add_schedule(self, schedule_def: ScheduleDefinition) -> Result[str]:
        """Add a schedule to storage.

        Args:
            schedule_def: The schedule definition to add.

        Returns:
            Result with the schedule ID if successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                schedule_id = str(uuid.uuid4())
                now = datetime.now(datetime.UTC)

                # Calculate the next run time based on the schedule
                next_run = schedule_def.schedule.next_run_time(now)

                schedule_data = {
                    "id": schedule_id,
                    "name": schedule_def.name,
                    "task_name": schedule_def.task_name,
                    "schedule_type": schedule_def.schedule.schedule_type,
                    "schedule_data": schedule_def.schedule.to_dict(),
                    "args": schedule_def.args or [],
                    "kwargs": schedule_def.kwargs or {},
                    "queue_name": schedule_def.queue_name,
                    "priority": schedule_def.priority.value,
                    "max_retries": schedule_def.max_retries,
                    "retry_delay": (
                        schedule_def.retry_delay.total_seconds()
                        if schedule_def.retry_delay
                        else None
                    ),
                    "timeout": (
                        schedule_def.timeout.total_seconds()
                        if schedule_def.timeout
                        else None
                    ),
                    "created_at": now,
                    "updated_at": now,
                    "next_run_at": next_run,
                    "metadata": schedule_def.metadata,
                    "enabled": schedule_def.enabled,
                }

                await session.execute(
                    self.schedules_table.insert().values(**schedule_data)
                )
                await session.commit()

                return Result.success(schedule_id)
        except Exception as e:
            return Result.failure(f"Failed to add schedule to database: {str(e)}")

    async def get_schedule(
        self, schedule_id: str
    ) -> Result[Optional[ScheduleDefinition]]:
        """Get a schedule by ID.

        Args:
            schedule_id: The ID of the schedule to retrieve.

        Returns:
            Result with the schedule if found, None if not found.
        """
        try:
            session = await self._get_session()

            query = select([self.schedules_table]).where(
                self.schedules_table.c.id == schedule_id
            )
            result = await session.execute(query)
            schedule_data = result.fetchone()

            if not schedule_data:
                return Result.success(None)

            schedule = self._schedule_from_row(dict(schedule_data))
            return Result.success(schedule)
        except Exception as e:
            return Result.failure(
                f"Failed to retrieve schedule from database: {str(e)}"
            )

    async def get_schedule_by_name(
        self, name: str
    ) -> Result[Optional[ScheduleDefinition]]:
        """Get a schedule by name.

        Args:
            name: The name of the schedule to retrieve.

        Returns:
            Result with the schedule if found, None if not found.
        """
        try:
            session = await self._get_session()

            query = select([self.schedules_table]).where(
                self.schedules_table.c.name == name
            )
            result = await session.execute(query)
            schedule_data = result.fetchone()

            if not schedule_data:
                return Result.success(None)

            schedule = self._schedule_from_row(dict(schedule_data))
            return Result.success(schedule)
        except Exception as e:
            return Result.failure(
                f"Failed to retrieve schedule from database: {str(e)}"
            )

    async def update_schedule(self, schedule_def: ScheduleDefinition) -> Result[bool]:
        """Update a schedule in storage.

        Args:
            schedule_def: The schedule definition to update.

        Returns:
            Result with True if the update was successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                now = datetime.now(datetime.UTC)
                next_run = schedule_def.schedule.next_run_time(now)

                schedule_data = {
                    "task_name": schedule_def.task_name,
                    "schedule_type": schedule_def.schedule.schedule_type,
                    "schedule_data": schedule_def.schedule.to_dict(),
                    "args": schedule_def.args or [],
                    "kwargs": schedule_def.kwargs or {},
                    "queue_name": schedule_def.queue_name,
                    "priority": schedule_def.priority.value,
                    "max_retries": schedule_def.max_retries,
                    "retry_delay": (
                        schedule_def.retry_delay.total_seconds()
                        if schedule_def.retry_delay
                        else None
                    ),
                    "timeout": (
                        schedule_def.timeout.total_seconds()
                        if schedule_def.timeout
                        else None
                    ),
                    "updated_at": now,
                    "next_run_at": next_run,
                    "metadata": schedule_def.metadata,
                    "enabled": schedule_def.enabled,
                }

                update_query = (
                    self.schedules_table.update()
                    .where(self.schedules_table.c.id == schedule_def.id)
                    .values(**schedule_data)
                )

                await session.execute(update_query)
                await session.commit()

                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to update schedule in database: {str(e)}")

    async def delete_schedule(self, schedule_id: str) -> Result[bool]:
        """Delete a schedule from storage.

        Args:
            schedule_id: The ID of the schedule to delete.

        Returns:
            Result with True if the deletion was successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                delete_query = self.schedules_table.delete().where(
                    self.schedules_table.c.id == schedule_id
                )
                await session.execute(delete_query)
                await session.commit()

                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to delete schedule from database: {str(e)}")

    async def get_due_schedules(self) -> Result[list[ScheduleDefinition]]:
        """Get schedules that are due to run.

        Returns:
            Result with a list of due schedules.
        """
        try:
            session = await self._get_session()

            now = datetime.now(datetime.UTC)

            query = select([self.schedules_table]).where(
                and_(
                    self.schedules_table.c.next_run_at <= now,
                    self.schedules_table.c.enabled == True,
                )
            )

            result = await session.execute(query)
            schedule_rows = result.fetchall()

            schedules = [self._schedule_from_row(dict(row)) for row in schedule_rows]

            return Result.success(schedules)
        except Exception as e:
            return Result.failure(
                f"Failed to get due schedules from database: {str(e)}"
            )

    async def update_schedule_run_time(
        self, schedule_id: str, last_run: datetime, next_run: datetime
    ) -> Result[bool]:
        """Update a schedule's last run time and next run time.

        Args:
            schedule_id: The ID of the schedule to update.
            last_run: The last run time to set.
            next_run: The next run time to set.

        Returns:
            Result with True if the update was successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                update_query = (
                    self.schedules_table.update()
                    .where(self.schedules_table.c.id == schedule_id)
                    .values(
                        last_run_at=last_run,
                        next_run_at=next_run,
                        updated_at=datetime.now(datetime.UTC),
                    )
                )

                await session.execute(update_query)
                await session.commit()

                return Result.success(True)
        except Exception as e:
            return Result.failure(
                f"Failed to update schedule run times in database: {str(e)}"
            )

    async def get_all_schedules(self) -> Result[list[ScheduleDefinition]]:
        """Get all schedules.

        Returns:
            Result with a list of all schedules.
        """
        try:
            session = await self._get_session()

            query = select([self.schedules_table])
            result = await session.execute(query)
            schedule_rows = result.fetchall()

            schedules = [self._schedule_from_row(dict(row)) for row in schedule_rows]

            return Result.success(schedules)
        except Exception as e:
            return Result.failure(
                f"Failed to get all schedules from database: {str(e)}"
            )

    async def clear_queue(self, queue_name: str) -> Result[int]:
        """Clear all pending jobs from a queue.

        Args:
            queue_name: The name of the queue to clear.

        Returns:
            Result with the number of jobs cleared.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                query = (
                    self.jobs_table.delete()
                    .where(
                        and_(
                            self.jobs_table.c.queue_name == queue_name,
                            self.jobs_table.c.status == JobStatus.PENDING.value,
                        )
                    )
                    .returning(self.jobs_table.c.id)
                )

                result = await session.execute(query)
                deleted_rows = result.fetchall()
                await session.commit()

                return Result.success(len(deleted_rows))
        except Exception as e:
            return Result.failure(f"Failed to clear queue in database: {str(e)}")

    async def pause_queue(self, queue_name: str) -> Result[bool]:
        """Pause a queue by marking all pending jobs as paused.

        Args:
            queue_name: The name of the queue to pause.

        Returns:
            Result with True if the operation was successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                update_query = (
                    self.jobs_table.update()
                    .where(
                        and_(
                            self.jobs_table.c.queue_name == queue_name,
                            self.jobs_table.c.status == JobStatus.PENDING.value,
                        )
                    )
                    .values(
                        status=JobStatus.PAUSED.value,
                        updated_at=datetime.now(datetime.UTC),
                    )
                )

                await session.execute(update_query)
                await session.commit()

                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to pause queue in database: {str(e)}")

    async def resume_queue(self, queue_name: str) -> Result[bool]:
        """Resume a queue by marking all paused jobs as pending.

        Args:
            queue_name: The name of the queue to resume.

        Returns:
            Result with True if the operation was successful.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                update_query = (
                    self.jobs_table.update()
                    .where(
                        and_(
                            self.jobs_table.c.queue_name == queue_name,
                            self.jobs_table.c.status == JobStatus.PAUSED.value,
                        )
                    )
                    .values(
                        status=JobStatus.PENDING.value,
                        updated_at=datetime.now(datetime.UTC),
                    )
                )

                await session.execute(update_query)
                await session.commit()

                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to resume queue in database: {str(e)}")

    async def get_queue_names(self) -> Result[Set[str]]:
        """Get all queue names.

        Returns:
            Result with a set of all queue names.
        """
        try:
            session = await self._get_session()

            query = select([self.jobs_table.c.queue_name]).distinct()
            result = await session.execute(query)
            queue_names = {row[0] for row in result.fetchall()}

            return Result.success(queue_names)
        except Exception as e:
            return Result.failure(f"Failed to get queue names from database: {str(e)}")

    async def cleanup_old_jobs(self, max_age: timedelta) -> Result[int]:
        """Clean up old completed/failed jobs.

        Args:
            max_age: The maximum age of jobs to keep.

        Returns:
            Result with the number of jobs cleaned up.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                cutoff_date = datetime.now(datetime.UTC) - max_age

                # Only delete completed, failed, or cancelled jobs
                terminal_statuses = [
                    JobStatus.COMPLETED.value,
                    JobStatus.FAILED.value,
                    JobStatus.CANCELLED.value,
                ]

                query = (
                    self.jobs_table.delete()
                    .where(
                        and_(
                            self.jobs_table.c.updated_at < cutoff_date,
                            self.jobs_table.c.status.in_(terminal_statuses),
                        )
                    )
                    .returning(self.jobs_table.c.id)
                )

                result = await session.execute(query)
                deleted_rows = result.fetchall()
                await session.commit()

                return Result.success(len(deleted_rows))
        except Exception as e:
            return Result.failure(f"Failed to clean up old jobs in database: {str(e)}")

    async def mark_stalled_jobs_as_failed(
        self, stall_timeout: timedelta
    ) -> Result[int]:
        """Mark stalled jobs as failed.

        Args:
            stall_timeout: The time after which a running job is considered stalled.

        Returns:
            Result with the number of jobs marked as failed.
        """
        try:
            async with self._lock:
                session = await self._get_session()

                cutoff_date = datetime.now(datetime.UTC) - stall_timeout
                now = datetime.now(datetime.UTC)

                # Find and update stalled jobs
                query = (
                    self.jobs_table.update()
                    .where(
                        and_(
                            self.jobs_table.c.status == JobStatus.RUNNING.value,
                            self.jobs_table.c.updated_at < cutoff_date,
                        )
                    )
                    .values(
                        status=JobStatus.FAILED.value,
                        error={
                            "message": f"Job stalled and marked as failed after {stall_timeout.total_seconds()} seconds",
                            "type": "StallError",
                        },
                        updated_at=now,
                        completed_at=now,
                    )
                    .returning(self.jobs_table.c.id)
                )

                result = await session.execute(query)
                updated_rows = result.fetchall()
                await session.commit()

                return Result.success(len(updated_rows))
        except Exception as e:
            return Result.failure(
                f"Failed to mark stalled jobs as failed in database: {str(e)}"
            )

    def _job_from_row(self, row: dict[str, Any]) -> Job:
        """Convert a database row to a Job object.

        Args:
            row: The database row as a dictionary.

        Returns:
            A Job object.
        """
        # Convert the status string to enum
        status = JobStatus(row["status"])

        # Convert the priority integer to enum
        priority = Priority(row["priority"])

        # Convert timedeltas from seconds to timedelta objects
        retry_delay = (
            timedelta(seconds=row["retry_delay"])
            if row["retry_delay"] is not None
            else None
        )
        timeout = (
            timedelta(seconds=row["timeout"]) if row["timeout"] is not None else None
        )

        # Convert tags from list to set
        tags = set(row["tags"]) if row["tags"] else set()

        return Job(
            id=row["id"],
            queue_name=row["queue_name"],
            status=status,
            task_name=row["task_name"],
            args=row["args"],
            kwargs=row["kwargs"],
            result=row["result"],
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            scheduled_at=row["scheduled_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            priority=priority,
            retries=row["retries"],
            max_retries=row["max_retries"],
            retry_delay=retry_delay,
            timeout=timeout,
            is_scheduled=row["is_scheduled"],
            metadata=row["metadata"],
            tags=tags,
        )

    def _schedule_from_row(self, row: dict[str, Any]) -> ScheduleDefinition:
        """Convert a database row to a ScheduleDefinition object.

        Args:
            row: The database row as a dictionary.

        Returns:
            A ScheduleDefinition object.
        """
        # Convert the priority integer to enum
        priority = Priority(row["priority"])

        # Convert timedeltas from seconds to timedelta objects
        retry_delay = (
            timedelta(seconds=row["retry_delay"])
            if row["retry_delay"] is not None
            else None
        )
        timeout = (
            timedelta(seconds=row["timeout"]) if row["timeout"] is not None else None
        )

        # Create the schedule object from the stored data
        schedule_type = row["schedule_type"]
        schedule_data = row["schedule_data"]
        schedule = Schedule.from_dict(schedule_type, schedule_data)

        return ScheduleDefinition(
            id=row["id"],
            name=row["name"],
            task_name=row["task_name"],
            schedule=schedule,
            args=row["args"],
            kwargs=row["kwargs"],
            queue_name=row["queue_name"],
            priority=priority,
            max_retries=row["max_retries"],
            retry_delay=retry_delay,
            timeout=timeout,
            metadata=row["metadata"],
            enabled=row["enabled"],
        )
