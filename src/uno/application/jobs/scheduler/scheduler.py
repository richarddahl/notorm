"""Scheduler implementation for the background processing system.

This module provides the Scheduler class which manages scheduled jobs
and ensures they're executed at the appropriate times.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union, Tuple, cast
import asyncio
import logging
import uuid

from uno.jobs.queue.job import Job
from uno.jobs.queue.queue import JobQueue
from uno.jobs.scheduler.schedules import (
    Schedule,
    CronSchedule,
    IntervalSchedule,
    OneTimeSchedule,
    DailySchedule,
    WeeklySchedule,
    MonthlySchedule,
    EventTrigger,
)
from uno.jobs.storage.base import Storage
from uno.core.asynchronous import AsyncLock


class SchedulerError(Exception):
    """Base class for scheduler-related errors."""

    pass


class Scheduler:
    """Scheduler for managing recurring and scheduled jobs.

    This class manages schedules and ensures jobs are created and
    enqueued at the appropriate times based on the schedule definitions.
    """

    def __init__(
        self,
        storage: Storage,
        queue_name: str = "scheduled",
        timezone: str = "UTC",
        check_interval: int = 60,
        missed_threshold: int = 300,
        lock_timeout: int = 300,
        metrics_enabled: bool = True,
        instance_id: str | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize a scheduler.

        Args:
            storage: Storage backend for persisting schedules and jobs
            queue_name: Name of the queue for scheduled jobs
            timezone: Default timezone for schedules
            check_interval: Seconds between scheduler ticks
            missed_threshold: Seconds after which a job is considered missed
            lock_timeout: Seconds until a scheduler lock expires
            metrics_enabled: Whether to collect metrics
            instance_id: Unique identifier for this scheduler instance
            logger: Optional logger instance
        """
        self.storage = storage
        self.queue_name = queue_name
        self.timezone = timezone
        self.check_interval = check_interval
        self.missed_threshold = missed_threshold
        self.lock_timeout = lock_timeout
        self.metrics_enabled = metrics_enabled
        self.instance_id = instance_id or f"scheduler-{uuid.uuid4()}"
        self.logger = logger or logging.getLogger(
            f"uno.jobs.scheduler.{self.instance_id}"
        )

        # State tracking
        self.running = False
        self.paused = False
        self.shutdown_event = asyncio.Event()
        self.lock = AsyncLock()

        # Tasks
        self.main_task: Optional[asyncio.Task] = None
        self.metrics_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "schedules_total": 0,
            "schedules_active": 0,
            "schedules_paused": 0,
            "jobs_triggered_total": 0,
            "jobs_triggered_last_24h": 0,
            "triggered_by_type": {},
            "errors": {},
        }

    async def start(self) -> None:
        """Start the scheduler.

        This method initializes the scheduler and starts the main loop
        that checks for due jobs.
        """
        if self.running:
            self.logger.warning("Scheduler is already running")
            return

        self.logger.info(f"Starting scheduler {self.instance_id}")
        self.running = True

        # Initialize storage if needed
        await self.storage.initialize()

        # Start the main scheduler loop
        self.main_task = asyncio.create_task(self._scheduler_loop())

        # Start metrics collection if enabled
        if self.metrics_enabled:
            self.metrics_task = asyncio.create_task(self._metrics_loop())

        self.logger.info("Scheduler started successfully")

    async def shutdown(self, wait: bool = True) -> None:
        """Shut down the scheduler.

        Args:
            wait: Whether to wait for current operations to complete
        """
        if not self.running:
            return

        self.logger.info(f"Shutting down scheduler {self.instance_id}")

        # Set shutdown flag
        self.running = False
        self.shutdown_event.set()

        # Cancel tasks
        for task in [self.main_task, self.metrics_task]:
            if task and not task.done():
                task.cancel()
                if wait:
                    try:
                        await asyncio.wait_for(task, timeout=10)
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Task cancellation timed out")
                    except asyncio.CancelledError:
                        pass

        self.logger.info("Scheduler shutdown complete")

    async def pause(self) -> bool:
        """Pause the scheduler.

        This temporarily stops the scheduler from checking for due jobs.

        Returns:
            True if the scheduler was paused, False if already paused
        """
        if not self.running:
            return False

        if self.paused:
            return False

        self.logger.info(f"Pausing scheduler {self.instance_id}")
        self.paused = True
        return True

    async def resume(self) -> bool:
        """Resume a paused scheduler.

        Returns:
            True if the scheduler was resumed, False if not paused
        """
        if not self.running:
            return False

        if not self.paused:
            return False

        self.logger.info(f"Resuming scheduler {self.instance_id}")
        self.paused = False
        return True

    async def schedule(
        self,
        task: str,
        schedule: Union[Schedule, dict[str, Any]],
        args: Optional[list[Any]] = None,
        kwargs: dict[str, Any] | None = None,
        queue: str | None = None,
        priority: str = "normal",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timezone: str | None = None,
        max_retries: int = 0,
        retry_delay: int = 60,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        timeout: int | None = None,
        unique: bool = False,
        name: str | None = None,
    ) -> str:
        """Schedule a task to run according to a schedule.

        Args:
            task: Task to execute (module.function reference)
            schedule: Schedule definition or dict representation
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            queue: Queue to use (defaults to scheduler's queue)
            priority: Priority level for the job
            start_date: When to start scheduling
            end_date: When to stop scheduling
            timezone: Timezone for this schedule
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            tags: Optional tags for categorization and filtering
            metadata: Optional metadata for the job
            timeout: Optional timeout in seconds
            unique: Whether the task should be unique
            name: Unique name for this schedule

        Returns:
            The schedule ID

        Raises:
            ValueError: If the task or schedule is invalid
        """
        if not task:
            raise ValueError("Task must be specified")

        # Generate a schedule ID
        schedule_id = name or str(uuid.uuid4())

        # Convert dict schedule to Schedule object if needed
        schedule_obj: Schedule
        if isinstance(schedule, dict):
            schedule_obj = Schedule.from_dict(schedule)
        else:
            schedule_obj = schedule

        # Schedule the job with the storage backend
        await self.storage.schedule_recurring_job(
            schedule_id=schedule_id,
            task=task,
            args=args or [],
            kwargs=kwargs or {},
            cron_expression=getattr(schedule_obj, "cron_expression", None),
            interval_seconds=getattr(schedule_obj, "interval", None)
            and getattr(schedule_obj, "interval").total_seconds(),
            queue=queue or self.queue_name,
            priority=priority,
            tags=tags or [],
            metadata={
                **(metadata or {}),
                "schedule_id": schedule_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "timezone": timezone or self.timezone,
                "unique": unique,
            },
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )

        self.logger.info(f"Scheduled task '{task}' with ID '{schedule_id}'")
        return schedule_id

    async def get_schedule(self, schedule_id: str) -> dict[str, Any] | None:
        """Get a schedule by ID.

        Args:
            schedule_id: The ID of the schedule to get

        Returns:
            The schedule if found, None otherwise
        """
        return await self.storage.get_schedule(schedule_id)

    async def get_schedule_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a schedule by name.

        Args:
            name: The name of the schedule to get

        Returns:
            The schedule if found, None otherwise
        """
        # Get all schedules and filter by name
        # This is inefficient, but we don't have a direct lookup by name in the storage interface
        schedules = await self.storage.list_schedules()
        for schedule in schedules:
            if schedule.get("id") == name:
                return schedule
        return None

    async def update_schedule(
        self,
        schedule_id: str,
        schedule: Optional[Schedule] = None,
        args: Optional[list[Any]] = None,
        kwargs: dict[str, Any] | None = None,
        queue: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        max_retries: int | None = None,
        retry_delay: int | None = None,
        timeout: int | None = None,
        status: str | None = None,
        version: int | None = None,
        changelog: str | None = None,
    ) -> bool:
        """Update a schedule.

        Args:
            schedule_id: The ID of the schedule to update
            schedule: Optional new schedule
            args: Optional new positional arguments
            kwargs: Optional new keyword arguments
            queue: Optional new queue
            priority: Optional new priority level
            tags: Optional new tags
            metadata: Optional new metadata
            max_retries: Optional new maximum retry attempts
            retry_delay: Optional new delay between retries in seconds
            timeout: Optional new timeout in seconds
            status: Optional new status ("active" or "paused")
            version: Optional version for optimistic concurrency control
            changelog: Optional description of the changes made

        Returns:
            True if the schedule was updated, False otherwise

        Raises:
            ValueError: If the new schedule values are invalid
        """
        # Get current schedule to check version if provided
        if version is not None:
            current = await self.storage.get_schedule(schedule_id)
            if current is None:
                return False

            current_version = current.get("version", 1)
            if current_version != version:
                raise ValueError(
                    f"Version mismatch: expected {version}, got {current_version}"
                )

        # Update metadata with changelog if provided
        updated_metadata = None
        if metadata or changelog:
            updated_metadata = metadata or {}
            if changelog:
                updated_metadata["changelog"] = changelog
                updated_metadata["updated_at"] = datetime.now(datetime.UTC).isoformat()

        # Extract schedule parameters if a schedule object is provided
        cron_expression = None
        interval_seconds = None
        if schedule is not None:
            if hasattr(schedule, "cron_expression"):
                cron_expression = getattr(schedule, "cron_expression")
            elif hasattr(schedule, "interval"):
                interval = getattr(schedule, "interval")
                if interval is not None:
                    interval_seconds = interval.total_seconds()

        # Update the schedule in storage
        success = await self.storage.update_schedule(
            schedule_id=schedule_id,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            queue=queue,
            priority=priority,
            tags=tags,
            metadata=updated_metadata,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            status=status,
        )

        if success:
            self.logger.info(f"Updated schedule '{schedule_id}'")
        else:
            self.logger.warning(f"Failed to update schedule '{schedule_id}'")

        return success

    async def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule temporarily.

        Args:
            schedule_id: The ID of the schedule to pause

        Returns:
            True if the schedule was paused, False otherwise
        """
        return await self.update_schedule(schedule_id, status="paused")

    async def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule.

        Args:
            schedule_id: The ID of the schedule to resume

        Returns:
            True if the schedule was resumed, False otherwise
        """
        return await self.update_schedule(schedule_id, status="active")

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule.

        Args:
            schedule_id: The ID of the schedule to delete

        Returns:
            True if the schedule was deleted, False otherwise
        """
        success = await self.storage.delete_schedule(schedule_id)

        if success:
            self.logger.info(f"Deleted schedule '{schedule_id}'")
        else:
            self.logger.warning(f"Failed to delete schedule '{schedule_id}'")

        return success

    async def list_schedules(
        self,
        status: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List schedules with filtering.

        Args:
            status: Optional status filter ("active" or "paused")
            tags: Optional list of tags to filter by

        Returns:
            List of schedules matching the filters
        """
        return await self.storage.list_schedules(status=status, tags=tags)

    async def get_next_run_times(
        self, schedule_id: str, count: int = 5
    ) -> list[datetime]:
        """Get the next N run times for a schedule.

        Args:
            schedule_id: ID of the schedule
            count: Number of run times to retrieve

        Returns:
            List of the next N run times

        Raises:
            ValueError: If the schedule does not exist
        """
        schedule_data = await self.storage.get_schedule(schedule_id)
        if not schedule_data:
            raise ValueError(f"Schedule not found: {schedule_id}")

        # Create a Schedule object from the data
        schedule_dict = {
            "type": "interval" if schedule_data.get("interval_seconds") else "cron",
            "interval_seconds": schedule_data.get("interval_seconds"),
            "cron_expression": schedule_data.get("cron_expression"),
        }

        schedule = Schedule.from_dict(schedule_dict)

        # Get the next run times starting from the next run time in the schedule
        next_run = schedule_data.get("next_run")
        if next_run and isinstance(next_run, str):
            next_run = datetime.fromisoformat(next_run)
        else:
            next_run = datetime.now(datetime.UTC)

        return schedule.get_next_n_run_times(next_run, count)

    async def get_schedule_status(self, schedule_id: str) -> dict[str, Any]:
        """Get detailed status information for a schedule.

        Args:
            schedule_id: ID of the schedule

        Returns:
            Dictionary with schedule status information

        Raises:
            ValueError: If the schedule does not exist
        """
        schedule_data = await self.storage.get_schedule(schedule_id)
        if not schedule_data:
            raise ValueError(f"Schedule not found: {schedule_id}")

        # Extract basic information
        name = schedule_data.get("id", schedule_id)
        status = schedule_data.get("status", "unknown")
        last_run = schedule_data.get("last_run")
        last_result = schedule_data.get("last_result")
        next_run = schedule_data.get("next_run")
        run_count = schedule_data.get("run_count", 0)

        # Parse datetime strings if needed
        if last_run and isinstance(last_run, str):
            last_run = datetime.fromisoformat(last_run)
        if next_run and isinstance(next_run, str):
            next_run = datetime.fromisoformat(next_run)

        # Count successes and failures if possible
        success_count = schedule_data.get("success_count", None)
        error_count = schedule_data.get("error_count", None)

        # Get average duration if available
        average_duration = schedule_data.get("average_duration", None)

        result = {
            "name": name,
            "status": status,
            "last_run": last_run.isoformat() if last_run else None,
            "next_run": next_run.isoformat() if next_run else None,
            "run_count": run_count,
        }

        if last_result:
            result["last_result"] = last_result

        if success_count is not None:
            result["success_count"] = success_count

        if error_count is not None:
            result["error_count"] = error_count

        if average_duration is not None:
            result["average_duration"] = average_duration

        return result

    async def trigger_now(
        self,
        schedule_id: str,
        args: Optional[list[Any]] = None,
        kwargs: dict[str, Any] | None = None,
    ) -> str:
        """Trigger a scheduled job immediately.

        Args:
            schedule_id: ID of the schedule to trigger
            args: Optional arguments to override the schedule's arguments
            kwargs: Optional keyword arguments to override the schedule's kwargs

        Returns:
            The ID of the triggered job

        Raises:
            ValueError: If the schedule does not exist
        """
        schedule_data = await self.storage.get_schedule(schedule_id)
        if not schedule_data:
            raise ValueError(f"Schedule not found: {schedule_id}")

        # Get the job data for this schedule
        job_data = {
            "task": schedule_data["task"],
            "args": args if args is not None else schedule_data["args"],
            "kwargs": kwargs if kwargs is not None else schedule_data["kwargs"],
            "queue": schedule_data["queue"],
            "priority": schedule_data["priority"],
            "tags": schedule_data.get("tags", []),
            "metadata": {
                **(schedule_data.get("metadata") or {}),
                "schedule_id": schedule_id,
                "manual_trigger": True,
                "scheduled_run": datetime.now(datetime.UTC).isoformat(),
            },
            "max_retries": schedule_data.get("max_retries", 0),
            "retry_delay": schedule_data.get("retry_delay", 60),
            "timeout": schedule_data.get("timeout"),
        }

        # Create a job and enqueue it
        job = Job(**job_data)
        job_id = await self.storage.create_job(job)
        await self.storage.enqueue(job.queue, job)

        # Update statistics
        self._stats["jobs_triggered_total"] += 1
        self._stats["jobs_triggered_last_24h"] += 1

        # Get schedule type for statistics
        schedule_type = "unknown"
        if schedule_data.get("cron_expression"):
            schedule_type = "cron"
        elif schedule_data.get("interval_seconds"):
            schedule_type = "interval"

        # Update type-specific statistics
        self._stats["triggered_by_type"][schedule_type] = (
            self._stats["triggered_by_type"].get(schedule_type, 0) + 1
        )

        self.logger.info(f"Manually triggered schedule '{schedule_id}'")
        return job_id

    async def trigger_event(
        self,
        event_name: str,
        event_data: dict[str, Any] | None = None,
    ) -> list[str]:
        """Trigger all schedules associated with an event.

        Args:
            event_name: Name of the event to trigger
            event_data: Optional data associated with the event

        Returns:
            List of job IDs created by this event
        """
        # Find all schedules triggered by this event
        all_schedules = await self.storage.list_schedules()
        event_schedules = []

        for schedule in all_schedules:
            # Check if this is an event trigger for the specified event
            if (
                schedule.get("type") == "event"
                and schedule.get("event_name") == event_name
            ):
                event_schedules.append(schedule)

        # Trigger each matching schedule
        job_ids = []
        for schedule in event_schedules:
            try:
                # Create a job for this schedule
                schedule_id = schedule["id"]

                # Get the job data for this schedule
                job_data = {
                    "task": schedule["task"],
                    "args": schedule["args"],
                    "kwargs": schedule["kwargs"],
                    "queue": schedule["queue"],
                    "priority": schedule["priority"],
                    "tags": schedule.get("tags", []),
                    "metadata": {
                        **(schedule.get("metadata") or {}),
                        "schedule_id": schedule_id,
                        "event_trigger": True,
                        "event_name": event_name,
                        "event_data": event_data,
                        "scheduled_run": datetime.now(datetime.UTC).isoformat(),
                    },
                    "max_retries": schedule.get("max_retries", 0),
                    "retry_delay": schedule.get("retry_delay", 60),
                    "timeout": schedule.get("timeout"),
                }

                # Create a job and enqueue it
                job = Job(**job_data)
                job_id = await self.storage.create_job(job)
                await self.storage.enqueue(job.queue, job)
                job_ids.append(job_id)

                # Update schedule information
                await self.storage.update_schedule(
                    schedule_id=schedule_id,
                    metadata={
                        "last_triggered": datetime.now(datetime.UTC).isoformat(),
                        "last_event_data": event_data,
                    },
                )

                # Update statistics
                self._stats["jobs_triggered_total"] += 1
                self._stats["jobs_triggered_last_24h"] += 1
                self._stats["triggered_by_type"]["event"] = (
                    self._stats["triggered_by_type"].get("event", 0) + 1
                )

                self.logger.info(
                    f"Triggered schedule '{schedule_id}' for event '{event_name}'"
                )

            except Exception as e:
                # Log error but continue with other schedules
                self.logger.error(f"Error triggering event schedule: {e}")

                # Update error statistics
                error_type = type(e).__name__
                self._stats["errors"][error_type] = (
                    self._stats["errors"].get(error_type, 0) + 1
                )

        return job_ids

    async def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics.

        Returns:
            Dictionary with scheduler statistics
        """
        # Get current statistics
        stats = self._stats.copy()

        # Get current schedule counts
        all_schedules = await self.storage.list_schedules()

        # Reset counts
        stats["schedules_total"] = len(all_schedules)
        stats["schedules_active"] = len(
            [s for s in all_schedules if s.get("status") == "active"]
        )
        stats["schedules_paused"] = len(
            [s for s in all_schedules if s.get("status") == "paused"]
        )

        # Add types distribution
        schedule_types = {}
        for schedule in all_schedules:
            schedule_type = "unknown"
            if schedule.get("cron_expression"):
                schedule_type = "cron"
            elif schedule.get("interval_seconds"):
                schedule_type = "interval"
            elif schedule.get("type"):
                schedule_type = schedule.get("type")

            schedule_types[schedule_type] = schedule_types.get(schedule_type, 0) + 1

        stats["schedules_by_type"] = schedule_types

        # Add scheduler status information
        stats["status"] = "paused" if self.paused else "running"
        stats["instance_id"] = self.instance_id

        return stats

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop.

        This method periodically checks for due jobs and enqueues them.
        """
        while self.running and not self.shutdown_event.is_set():
            try:
                if not self.paused:
                    # Try to acquire the scheduler lock
                    async with self.storage.create_lock(
                        f"scheduler:lock",
                        timeout=self.lock_timeout,
                        owner=self.instance_id,
                    ):
                        # Process due jobs
                        await self._process_due_jobs()

                # Wait for the next check interval or until shutdown
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(), timeout=self.check_interval
                    )
                except asyncio.TimeoutError:
                    # Check interval elapsed, continue the loop
                    pass

            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")

                # Update error statistics
                error_type = type(e).__name__
                self._stats["errors"][error_type] = (
                    self._stats["errors"].get(error_type, 0) + 1
                )

                # Wait a bit before retrying
                await asyncio.sleep(5)

    async def _process_due_jobs(self, limit: int = 100) -> None:
        """Process jobs that are due for execution.

        Args:
            limit: Maximum number of due jobs to process
        """
        # Get due jobs from storage
        due_jobs = await self.storage.get_due_jobs(limit=limit)

        if not due_jobs:
            return

        self.logger.debug(f"Found {len(due_jobs)} due jobs")

        # Process each due job
        for schedule_id, job_data in due_jobs:
            try:
                # Create and enqueue the job
                job = Job(**job_data)
                job_id = await self.storage.create_job(job)
                await self.storage.enqueue(job.queue, job)

                # Update statistics
                self._stats["jobs_triggered_total"] += 1
                self._stats["jobs_triggered_last_24h"] += 1

                # Get schedule type for statistics
                schedule = await self.storage.get_schedule(schedule_id)
                schedule_type = "unknown"
                if schedule and schedule.get("cron_expression"):
                    schedule_type = "cron"
                elif schedule and schedule.get("interval_seconds"):
                    schedule_type = "interval"

                # Update type-specific statistics
                self._stats["triggered_by_type"][schedule_type] = (
                    self._stats["triggered_by_type"].get(schedule_type, 0) + 1
                )

                self.logger.debug(f"Triggered job {job_id} for schedule {schedule_id}")

            except Exception as e:
                self.logger.error(
                    f"Error processing due job for schedule {schedule_id}: {e}"
                )

                # Update error statistics
                error_type = type(e).__name__
                self._stats["errors"][error_type] = (
                    self._stats["errors"].get(error_type, 0) + 1
                )

    async def _metrics_loop(self) -> None:
        """Metrics collection loop.

        This method periodically updates and logs scheduler metrics.
        """
        while self.running and not self.shutdown_event.is_set():
            try:
                # Update 24-hour triggered jobs counter
                # In a real implementation, this would track actual 24-hour metrics
                self._stats["jobs_triggered_last_24h"] = 0

                # Log metrics
                self.logger.debug(f"Scheduler metrics: {self._stats}")

                # Wait for the next metrics interval or until shutdown
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=60,  # Update metrics every minute
                    )
                except asyncio.TimeoutError:
                    # Metric interval elapsed, continue the loop
                    pass

            except Exception as e:
                self.logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(60)  # Wait a bit before retrying
