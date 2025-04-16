# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, Union, runtime_checkable

from uno.core.errors.result import Result
from uno.domain.repository import Repository
from uno.jobs.entities import Job, JobPriority, JobStatus, Schedule, JobError


@runtime_checkable
class JobRepositoryProtocol(Protocol):
    """Protocol for job repositories."""
    
    async def get_job(self, job_id: str) -> Result[Optional[Job]]:
        """Get a job by ID."""
        ...
    
    async def create_job(self, job: Job) -> Result[str]:
        """Create a new job."""
        ...
    
    async def update_job(self, job: Job) -> Result[bool]:
        """Update an existing job."""
        ...
    
    async def delete_job(self, job_id: str) -> Result[bool]:
        """Delete a job."""
        ...
    
    async def list_jobs(
        self,
        queue_name: Optional[str] = None,
        status: Optional[List[JobStatus]] = None,
        priority: Optional[JobPriority] = None,
        tags: Optional[Set[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Result[List[Job]]:
        """List jobs with filtering."""
        ...
    
    async def count_jobs(
        self,
        queue_name: Optional[str] = None,
        status: Optional[List[JobStatus]] = None,
        priority: Optional[JobPriority] = None,
        tags: Optional[Set[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> Result[int]:
        """Count jobs with filtering."""
        ...
    
    async def enqueue(
        self,
        job: Job,
    ) -> Result[str]:
        """Add a job to a queue for processing."""
        ...
    
    async def dequeue(
        self,
        queue_name: str,
        worker_id: str,
        priority_levels: Optional[List[JobPriority]] = None,
        batch_size: int = 1,
    ) -> Result[List[Job]]:
        """Get the next job(s) from a queue."""
        ...
    
    async def mark_job_completed(
        self,
        job_id: str,
        result: Any = None,
    ) -> Result[bool]:
        """Mark a job as completed."""
        ...
    
    async def mark_job_failed(
        self,
        job_id: str,
        error: Union[JobError, Dict[str, Any], str, Exception],
        retry: bool = False,
    ) -> Result[bool]:
        """Mark a job as failed."""
        ...
    
    async def mark_job_cancelled(
        self,
        job_id: str,
        reason: Optional[str] = None,
    ) -> Result[bool]:
        """Mark a job as cancelled."""
        ...
    
    async def retry_job(
        self,
        job_id: str,
    ) -> Result[bool]:
        """Retry a failed job."""
        ...
    
    async def get_queue_length(
        self,
        queue_name: str,
    ) -> Result[int]:
        """Get the number of pending jobs in a queue."""
        ...
    
    async def get_queue_names(
        self,
    ) -> Result[Set[str]]:
        """Get all queue names."""
        ...
    
    async def pause_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Pause a queue to stop processing new jobs."""
        ...
    
    async def resume_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Resume a paused queue."""
        ...
    
    async def is_queue_paused(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Check if a queue is paused."""
        ...
    
    async def clear_queue(
        self,
        queue_name: str,
    ) -> Result[int]:
        """Clear all jobs from a queue."""
        ...
    
    async def get_statistics(
        self,
    ) -> Result[Dict[str, Any]]:
        """Get statistics about jobs and queues."""
        ...
    
    async def cleanup_old_jobs(
        self,
        older_than: timedelta,
    ) -> Result[int]:
        """Clean up old completed jobs."""
        ...
    
    async def mark_stalled_jobs_as_failed(
        self,
        older_than: timedelta,
    ) -> Result[int]:
        """Mark stalled jobs as failed."""
        ...


@runtime_checkable
class ScheduleRepositoryProtocol(Protocol):
    """Protocol for schedule repositories."""
    
    async def get_schedule(
        self,
        schedule_id: str,
    ) -> Result[Optional[Schedule]]:
        """Get a schedule by ID."""
        ...
    
    async def create_schedule(
        self,
        schedule: Schedule,
    ) -> Result[str]:
        """Create a new schedule."""
        ...
    
    async def update_schedule(
        self,
        schedule: Schedule,
    ) -> Result[bool]:
        """Update an existing schedule."""
        ...
    
    async def delete_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Delete a schedule."""
        ...
    
    async def list_schedules(
        self,
        status: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Schedule]]:
        """List schedules with filtering."""
        ...
    
    async def get_due_schedules(
        self,
        limit: int = 100,
    ) -> Result[List[Schedule]]:
        """Get schedules that are due for execution."""
        ...
    
    async def update_schedule_next_run(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Update a schedule's next run time after execution."""
        ...


class JobRepository(Repository, JobRepositoryProtocol):
    """Implementation of job repository using the storage backend."""
    
    def __init__(self, storage):
        """Initialize the repository with a storage backend."""
        self.storage = storage
    
    async def get_job(self, job_id: str) -> Result[Optional[Job]]:
        """Get a job by ID."""
        try:
            job_dict = await self.storage.get_job(job_id)
            if job_dict is None:
                return Result.success(None)
            
            # Convert storage job to domain entity
            job = self._dict_to_job(job_dict)
            return Result.success(job)
        except Exception as e:
            return Result.failure(f"Failed to get job: {str(e)}")
    
    async def create_job(self, job: Job) -> Result[str]:
        """Create a new job."""
        try:
            # Convert domain entity to storage dict
            job_dict = self._job_to_dict(job)
            job_id = await self.storage.create_job(job_dict)
            return Result.success(job_id)
        except Exception as e:
            return Result.failure(f"Failed to create job: {str(e)}")
    
    async def update_job(self, job: Job) -> Result[bool]:
        """Update an existing job."""
        try:
            # Convert domain entity to storage dict
            job_dict = self._job_to_dict(job)
            success = await self.storage.update_job(job_dict)
            return Result.success(success)
        except Exception as e:
            return Result.failure(f"Failed to update job: {str(e)}")
    
    async def delete_job(self, job_id: str) -> Result[bool]:
        """Delete a job."""
        try:
            success = await self.storage.delete_job(job_id)
            return Result.success(success)
        except Exception as e:
            return Result.failure(f"Failed to delete job: {str(e)}")
    
    async def list_jobs(
        self,
        queue_name: Optional[str] = None,
        status: Optional[List[JobStatus]] = None,
        priority: Optional[JobPriority] = None,
        tags: Optional[Set[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Result[List[Job]]:
        """List jobs with filtering."""
        try:
            job_dicts = await self.storage.list_jobs(
                queue=queue_name,
                status=status,
                priority=priority,
                tags=tags,
                worker_id=worker_id,
                before=before,
                after=after,
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_dir=order_dir,
            )
            
            # Convert storage dicts to domain entities
            jobs = [self._dict_to_job(job_dict) for job_dict in job_dicts]
            return Result.success(jobs)
        except Exception as e:
            return Result.failure(f"Failed to list jobs: {str(e)}")
    
    async def count_jobs(
        self,
        queue_name: Optional[str] = None,
        status: Optional[List[JobStatus]] = None,
        priority: Optional[JobPriority] = None,
        tags: Optional[Set[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> Result[int]:
        """Count jobs with filtering."""
        try:
            count = await self.storage.count_jobs(
                queue=queue_name,
                status=status,
                priority=priority,
                tags=tags,
                worker_id=worker_id,
                before=before,
                after=after,
            )
            return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to count jobs: {str(e)}")
    
    async def enqueue(
        self,
        job: Job,
    ) -> Result[str]:
        """Add a job to a queue for processing."""
        try:
            # Convert domain entity to storage dict
            job_dict = self._job_to_dict(job)
            job_id = await self.storage.enqueue(job.queue_name, job_dict)
            return Result.success(job_id)
        except Exception as e:
            return Result.failure(f"Failed to enqueue job: {str(e)}")
    
    async def dequeue(
        self,
        queue_name: str,
        worker_id: str,
        priority_levels: Optional[List[JobPriority]] = None,
        batch_size: int = 1,
    ) -> Result[List[Job]]:
        """Get the next job(s) from a queue."""
        try:
            job_dicts = await self.storage.dequeue(
                queue_name,
                worker_id,
                priority_levels=priority_levels,
                batch_size=batch_size,
            )
            
            # Convert storage dicts to domain entities
            jobs = [self._dict_to_job(job_dict) for job_dict in job_dicts]
            return Result.success(jobs)
        except Exception as e:
            return Result.failure(f"Failed to dequeue jobs: {str(e)}")
    
    async def mark_job_completed(
        self,
        job_id: str,
        result: Any = None,
    ) -> Result[bool]:
        """Mark a job as completed."""
        try:
            job_result = await self.get_job(job_id)
            if not job_result.is_success:
                return job_result
            
            job = job_result.value
            if job is None:
                return Result.failure(f"Job {job_id} not found")
            
            job.mark_completed(result)
            update_result = await self.update_job(job)
            return update_result
        except Exception as e:
            return Result.failure(f"Failed to mark job as completed: {str(e)}")
    
    async def mark_job_failed(
        self,
        job_id: str,
        error: Union[JobError, Dict[str, Any], str, Exception],
        retry: bool = False,
    ) -> Result[bool]:
        """Mark a job as failed."""
        try:
            job_result = await self.get_job(job_id)
            if not job_result.is_success:
                return job_result
            
            job = job_result.value
            if job is None:
                return Result.failure(f"Job {job_id} not found")
            
            if retry and job.can_retry:
                job.mark_retry(error)
            else:
                job.mark_failed(error)
            
            update_result = await self.update_job(job)
            return update_result
        except Exception as e:
            return Result.failure(f"Failed to mark job as failed: {str(e)}")
    
    async def mark_job_cancelled(
        self,
        job_id: str,
        reason: Optional[str] = None,
    ) -> Result[bool]:
        """Mark a job as cancelled."""
        try:
            job_result = await self.get_job(job_id)
            if not job_result.is_success:
                return job_result
            
            job = job_result.value
            if job is None:
                return Result.failure(f"Job {job_id} not found")
            
            job.mark_cancelled(reason)
            update_result = await self.update_job(job)
            return update_result
        except Exception as e:
            return Result.failure(f"Failed to mark job as cancelled: {str(e)}")
    
    async def retry_job(
        self,
        job_id: str,
    ) -> Result[bool]:
        """Retry a failed job."""
        try:
            job_result = await self.get_job(job_id)
            if not job_result.is_success:
                return job_result
            
            job = job_result.value
            if job is None:
                return Result.failure(f"Job {job_id} not found")
            
            if job.status not in [JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT]:
                return Result.failure(f"Job {job_id} cannot be retried (status: {job.status.value})")
            
            # Reset the job to pending status
            job.status = JobStatus.PENDING
            job.worker_id = None
            job.error = None
            job.updated_at = datetime.now(UTC)
            
            update_result = await self.update_job(job)
            return update_result
        except Exception as e:
            return Result.failure(f"Failed to retry job: {str(e)}")
    
    async def get_queue_length(
        self,
        queue_name: str,
    ) -> Result[int]:
        """Get the number of pending jobs in a queue."""
        try:
            count = await self.storage.count_jobs(
                queue=queue_name,
                status=[JobStatus.PENDING],
            )
            return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to get queue length: {str(e)}")
    
    async def get_queue_names(
        self,
    ) -> Result[Set[str]]:
        """Get all queue names."""
        try:
            queues = await self.storage.list_queues()
            return Result.success(set(queues))
        except Exception as e:
            return Result.failure(f"Failed to get queue names: {str(e)}")
    
    async def pause_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Pause a queue to stop processing new jobs."""
        try:
            success = await self.storage.pause_queue(queue_name)
            return Result.success(success)
        except Exception as e:
            return Result.failure(f"Failed to pause queue: {str(e)}")
    
    async def resume_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Resume a paused queue."""
        try:
            success = await self.storage.resume_queue(queue_name)
            return Result.success(success)
        except Exception as e:
            return Result.failure(f"Failed to resume queue: {str(e)}")
    
    async def is_queue_paused(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Check if a queue is paused."""
        try:
            is_paused = await self.storage.is_queue_paused(queue_name)
            return Result.success(is_paused)
        except Exception as e:
            return Result.failure(f"Failed to check queue status: {str(e)}")
    
    async def clear_queue(
        self,
        queue_name: str,
    ) -> Result[int]:
        """Clear all jobs from a queue."""
        try:
            count = await self.storage.clear_queue(queue_name)
            return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to clear queue: {str(e)}")
    
    async def get_statistics(
        self,
    ) -> Result[Dict[str, Any]]:
        """Get statistics about jobs and queues."""
        try:
            stats = await self.storage.get_statistics()
            return Result.success(stats)
        except Exception as e:
            return Result.failure(f"Failed to get statistics: {str(e)}")
    
    async def cleanup_old_jobs(
        self,
        older_than: timedelta,
    ) -> Result[int]:
        """Clean up old completed jobs."""
        try:
            count = await self.storage.prune_jobs(
                status=[s for s in JobStatus if s.is_terminal],
                older_than=datetime.now(UTC) - older_than,
            )
            return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to clean up old jobs: {str(e)}")
    
    async def mark_stalled_jobs_as_failed(
        self,
        older_than: timedelta,
    ) -> Result[int]:
        """Mark stalled jobs as failed."""
        try:
            count = await self.storage.requeue_stuck(
                older_than=datetime.now(UTC) - older_than,
                status=[JobStatus.RUNNING, JobStatus.RESERVED],
            )
            return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to mark stalled jobs: {str(e)}")
    
    def _job_to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert a job entity to a storage dictionary."""
        job_dict = {
            "id": job.id,
            "task": job.task_name,
            "args": job.args,
            "kwargs": job.kwargs,
            "queue": job.queue_name,
            "priority": job.priority.name,
            "status": job.status.value,
            "scheduled_for": job.scheduled_at,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "result": job.result,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "retry_delay": job.retry_delay.total_seconds() if job.retry_delay else 60,
            "tags": list(job.tags),
            "metadata": job.metadata,
            "worker_id": job.worker_id,
            "timeout": job.timeout.total_seconds() if job.timeout else None,
            "version": job.version,
        }
        
        # Convert error if present
        if job.error:
            job_dict["error"] = {
                "type": job.error.type,
                "message": job.error.message,
                "traceback": job.error.traceback,
            }
        
        return job_dict
    
    def _dict_to_job(self, job_dict: Dict[str, Any]) -> Job:
        """Convert a storage dictionary to a job entity."""
        # Extract and convert error if present
        error = None
        if "error" in job_dict and job_dict["error"]:
            error_dict = job_dict["error"]
            error = JobError(
                type=error_dict.get("type", "Error"),
                message=error_dict.get("message", "Unknown error"),
                traceback=error_dict.get("traceback"),
            )
        
        # Convert string values to enums
        priority = JobPriority.NORMAL
        if "priority" in job_dict and job_dict["priority"]:
            if isinstance(job_dict["priority"], str):
                try:
                    priority = JobPriority[job_dict["priority"].upper()]
                except KeyError:
                    pass
            elif isinstance(job_dict["priority"], int):
                try:
                    priority = JobPriority(job_dict["priority"])
                except ValueError:
                    pass
        
        status = JobStatus.PENDING
        if "status" in job_dict and job_dict["status"]:
            for s in JobStatus:
                if s.value == job_dict["status"]:
                    status = s
                    break
        
        # Convert retry_delay and timeout to timedelta
        retry_delay = job_dict.get("retry_delay", 60)
        if isinstance(retry_delay, (int, float)):
            retry_delay = timedelta(seconds=retry_delay)
        
        timeout = job_dict.get("timeout")
        if isinstance(timeout, (int, float)) and timeout > 0:
            timeout = timedelta(seconds=timeout)
        elif timeout == 0:
            timeout = None
        
        # Create the job entity
        job = Job(
            id=job_dict["id"],
            task_name=job_dict.get("task", ""),
            args=job_dict.get("args", []),
            kwargs=job_dict.get("kwargs", {}),
            queue_name=job_dict.get("queue", "default"),
            priority=priority,
            status=status,
            scheduled_at=job_dict.get("scheduled_for"),
            created_at=job_dict.get("created_at", datetime.now(UTC)),
            started_at=job_dict.get("started_at"),
            completed_at=job_dict.get("completed_at"),
            result=job_dict.get("result"),
            error=error,
            retry_count=job_dict.get("retry_count", 0),
            max_retries=job_dict.get("max_retries", 0),
            retry_delay=retry_delay,
            tags=set(job_dict.get("tags", [])),
            metadata=job_dict.get("metadata", {}),
            worker_id=job_dict.get("worker_id"),
            timeout=timeout,
            version=job_dict.get("version"),
        )
        
        return job


class ScheduleRepository(Repository, ScheduleRepositoryProtocol):
    """Implementation of schedule repository using the storage backend."""
    
    def __init__(self, storage):
        """Initialize the repository with a storage backend."""
        self.storage = storage
    
    async def get_schedule(
        self,
        schedule_id: str,
    ) -> Result[Optional[Schedule]]:
        """Get a schedule by ID."""
        try:
            schedule_dict = await self.storage.get_schedule(schedule_id)
            if schedule_dict is None:
                return Result.success(None)
            
            # Convert storage dict to domain entity
            schedule = self._dict_to_schedule(schedule_dict)
            return Result.success(schedule)
        except Exception as e:
            return Result.failure(f"Failed to get schedule: {str(e)}")
    
    async def create_schedule(
        self,
        schedule: Schedule,
    ) -> Result[str]:
        """Create a new schedule."""
        try:
            # Convert domain entity to storage dict
            schedule_dict = self._schedule_to_dict(schedule)
            schedule_id = await self.storage.schedule_recurring_job(**schedule_dict)
            return Result.success(schedule_id)
        except Exception as e:
            return Result.failure(f"Failed to create schedule: {str(e)}")
    
    async def update_schedule(
        self,
        schedule: Schedule,
    ) -> Result[bool]:
        """Update an existing schedule."""
        try:
            # Convert domain entity to storage dict
            schedule_dict = self._schedule_to_dict(schedule)
            success = await self.storage.update_schedule(schedule.id, **schedule_dict)
            return Result.success(success)
        except Exception as e:
            return Result.failure(f"Failed to update schedule: {str(e)}")
    
    async def delete_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Delete a schedule."""
        try:
            success = await self.storage.delete_schedule(schedule_id)
            return Result.success(success)
        except Exception as e:
            return Result.failure(f"Failed to delete schedule: {str(e)}")
    
    async def list_schedules(
        self,
        status: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Schedule]]:
        """List schedules with filtering."""
        try:
            schedule_dicts = await self.storage.list_schedules(
                status=status,
                tags=list(tags) if tags else None,
            )
            
            # Apply limit and offset
            if offset >= len(schedule_dicts):
                return Result.success([])
            
            end_index = min(offset + limit, len(schedule_dicts))
            schedules = [
                self._dict_to_schedule(schedule_dict)
                for schedule_dict in schedule_dicts[offset:end_index]
            ]
            
            return Result.success(schedules)
        except Exception as e:
            return Result.failure(f"Failed to list schedules: {str(e)}")
    
    async def get_due_schedules(
        self,
        limit: int = 100,
    ) -> Result[List[Schedule]]:
        """Get schedules that are due for execution."""
        try:
            # Get all schedules first
            schedules_result = await self.list_schedules(status="active")
            if not schedules_result.is_success:
                return schedules_result
            
            schedules = schedules_result.value
            
            # Filter to only due schedules
            due_schedules = [
                schedule for schedule in schedules
                if schedule.is_due()
            ]
            
            # Apply limit
            due_schedules = due_schedules[:limit]
            
            return Result.success(due_schedules)
        except Exception as e:
            return Result.failure(f"Failed to get due schedules: {str(e)}")
    
    async def update_schedule_next_run(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Update a schedule's next run time after execution."""
        try:
            schedule_result = await self.get_schedule(schedule_id)
            if not schedule_result.is_success:
                return schedule_result
            
            schedule = schedule_result.value
            if schedule is None:
                return Result.failure(f"Schedule {schedule_id} not found")
            
            schedule.update_next_run()
            update_result = await self.update_schedule(schedule)
            return update_result
        except Exception as e:
            return Result.failure(f"Failed to update schedule next run: {str(e)}")
    
    def _schedule_to_dict(self, schedule: Schedule) -> Dict[str, Any]:
        """Convert a schedule entity to a storage dictionary."""
        schedule_dict = {
            "schedule_id": schedule.id,
            "task": schedule.task_name,
            "args": schedule.args,
            "kwargs": schedule.kwargs,
            "queue": schedule.queue_name,
            "priority": schedule.priority,
            "tags": list(schedule.tags) if schedule.tags else None,
            "metadata": schedule.metadata,
            "max_retries": schedule.max_retries,
            "retry_delay": int(schedule.retry_delay.total_seconds()) if schedule.retry_delay else 60,
            "timeout": int(schedule.timeout.total_seconds()) if schedule.timeout else None,
        }
        
        # Add either cron_expression or interval_seconds
        if schedule.cron_expression:
            schedule_dict["cron_expression"] = schedule.cron_expression
        elif schedule.interval:
            schedule_dict["interval_seconds"] = schedule.interval.total_seconds
        
        # Add status if updating
        if schedule.status:
            schedule_dict["status"] = schedule.status
        
        return schedule_dict
    
    def _dict_to_schedule(self, schedule_dict: Dict[str, Any]) -> Schedule:
        """Convert a storage dictionary to a schedule entity."""
        from uno.jobs.entities import ScheduleInterval
        
        # Convert interval if present
        interval = None
        if "interval_seconds" in schedule_dict and schedule_dict["interval_seconds"]:
            seconds = int(schedule_dict["interval_seconds"])
            
            # Convert to a more human-readable format
            days = seconds // 86400
            seconds %= 86400
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            
            interval = ScheduleInterval(
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
            )
        
        # Convert priority if present
        priority = JobPriority.NORMAL
        if "priority" in schedule_dict and schedule_dict["priority"]:
            if isinstance(schedule_dict["priority"], str):
                try:
                    priority = JobPriority[schedule_dict["priority"].upper()]
                except KeyError:
                    pass
            elif isinstance(schedule_dict["priority"], int):
                try:
                    priority = JobPriority(schedule_dict["priority"])
                except ValueError:
                    pass
        
        # Convert retry_delay and timeout to timedelta
        retry_delay = schedule_dict.get("retry_delay", 60)
        if isinstance(retry_delay, (int, float)):
            retry_delay = timedelta(seconds=retry_delay)
        
        timeout = schedule_dict.get("timeout")
        if isinstance(timeout, (int, float)) and timeout > 0:
            timeout = timedelta(seconds=timeout)
        elif timeout == 0:
            timeout = None
        
        # Create the schedule entity
        schedule = Schedule(
            id=schedule_dict.get("id", schedule_dict.get("schedule_id", "")),
            name=schedule_dict.get("name", schedule_dict.get("id", "")),
            task_name=schedule_dict.get("task", ""),
            status=schedule_dict.get("status", "active"),
            cron_expression=schedule_dict.get("cron_expression"),
            interval=interval,
            args=schedule_dict.get("args", []),
            kwargs=schedule_dict.get("kwargs", {}),
            queue_name=schedule_dict.get("queue", "default"),
            priority=priority,
            tags=set(schedule_dict.get("tags", [])),
            metadata=schedule_dict.get("metadata", {}),
            max_retries=schedule_dict.get("max_retries", 3),
            retry_delay=retry_delay,
            timeout=timeout,
            last_run_at=schedule_dict.get("last_run_at"),
            next_run_at=schedule_dict.get("next_run_at"),
            created_at=schedule_dict.get("created_at", datetime.now(UTC)),
            updated_at=schedule_dict.get("updated_at", datetime.now(UTC)),
            version=schedule_dict.get("version"),
        )
        
        return schedule