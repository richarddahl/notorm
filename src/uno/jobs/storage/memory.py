"""In-memory storage backend for the background processing system.

This module provides an in-memory implementation of the Storage interface,
primarily for development and testing purposes.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, AsyncContextManager, cast
import asyncio
import contextlib
import copy
import logging
import uuid
import heapq
from dataclasses import dataclass, field

from croniter import croniter

from uno.jobs.storage.base import Storage
from uno.jobs.queue.job import Job
from uno.jobs.queue.status import JobStatus
from uno.jobs.queue.priority import Priority
from uno.core.async_utils import AsyncLock


class LockAcquisitionError(Exception):
    """Exception raised when a lock cannot be acquired."""
    pass


@dataclass(order=True)
class PrioritizedJob:
    """Job with priority for the priority queue."""
    priority: int
    created_at: datetime
    job_id: str = field(compare=False)


class InMemoryStorage(Storage):
    """In-memory implementation of the Storage interface.
    
    This implementation stores all data in memory and is intended for
    development and testing purposes only. It provides all the functionality
    of the Storage interface but does not persist data across restarts.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize in-memory storage.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger("uno.jobs.storage.memory")
        
        # Main storage dictionaries
        self.jobs: Dict[str, Job] = {}
        self.queues: Dict[str, List[PrioritizedJob]] = {}
        self.queue_pause_status: Dict[str, bool] = {}
        self.schedules: Dict[str, Dict[str, Any]] = {}
        
        # Locks for concurrency control
        self.jobs_lock = AsyncLock()
        self.queues_lock = AsyncLock()
        self.schedules_lock = AsyncLock()
        
        # Distributed locks
        self.locks: Dict[str, Dict[str, Any]] = {}
        self.locks_lock = AsyncLock()
        
        # Initialization flag
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        if not self.initialized:
            self.logger.info("Initializing in-memory storage")
            self.initialized = True
    
    async def shutdown(self) -> None:
        """Shut down the storage backend."""
        self.logger.info("Shutting down in-memory storage")
    
    async def create_job(self, job: Job) -> str:
        """Create a new job record.
        
        Args:
            job: The job to create
            
        Returns:
            The ID of the created job
        """
        async with self.jobs_lock:
            # Store a deep copy to prevent external modifications
            self.jobs[job.id] = copy.deepcopy(job)
            return job.id
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.
        
        Args:
            job_id: The ID of the job to get
            
        Returns:
            The job if found, None otherwise
        """
        async with self.jobs_lock:
            job = self.jobs.get(job_id)
            if job:
                # Return a deep copy to prevent external modifications
                return copy.deepcopy(job)
            return None
    
    async def update_job(self, job: Job) -> bool:
        """Update a job.
        
        Args:
            job: The job to update
            
        Returns:
            True if the job was updated, False otherwise
        """
        async with self.jobs_lock:
            if job.id in self.jobs:
                # Store a deep copy to prevent external modifications
                self.jobs[job.id] = copy.deepcopy(job)
                return True
            return False
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job.
        
        Args:
            job_id: The ID of the job to delete
            
        Returns:
            True if the job was deleted, False otherwise
        """
        async with self.jobs_lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                
                # Also remove from queues if present
                async with self.queues_lock:
                    for queue_name, queue in self.queues.items():
                        # Create a new queue without the deleted job
                        new_queue = [pj for pj in queue if pj.job_id != job_id]
                        if len(new_queue) != len(queue):
                            self.queues[queue_name] = new_queue
                            heapq.heapify(self.queues[queue_name])
                
                return True
            return False
    
    async def enqueue(self, queue_name: str, job: Job) -> str:
        """Add a job to a queue.
        
        Args:
            queue_name: The name of the queue
            job: The job to enqueue
            
        Returns:
            The ID of the enqueued job
        """
        # First, create or update the job
        job_copy = copy.deepcopy(job)
        job_copy.queue = queue_name
        
        async with self.jobs_lock:
            self.jobs[job_copy.id] = job_copy
        
        # Then, add it to the queue
        async with self.queues_lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = []
            
            # Create a prioritized job entry
            pjob = PrioritizedJob(
                priority=job_copy.priority.value,
                created_at=job_copy.created_at,
                job_id=job_copy.id,
            )
            
            # Add to the priority queue
            heapq.heappush(self.queues[queue_name], pjob)
        
        return job_copy.id
    
    async def dequeue(
        self, 
        queue_name: str, 
        worker_id: str,
        priority_levels: Optional[List[Priority]] = None,
        batch_size: int = 1
    ) -> List[Job]:
        """Get the next job(s) from a queue.
        
        Args:
            queue_name: The name of the queue
            worker_id: The ID of the worker
            priority_levels: Optional list of priority levels to consider
            batch_size: Maximum number of jobs to dequeue
            
        Returns:
            List of jobs (may be empty if queue is empty)
        """
        dequeued_jobs: List[Job] = []
        
        # Check if queue is paused
        is_paused = await self.is_queue_paused(queue_name)
        if is_paused:
            return dequeued_jobs
        
        # Convert priority levels to values if provided
        priority_values: Optional[Set[int]] = None
        if priority_levels:
            priority_values = {p.value for p in priority_levels}
        
        async with self.queues_lock:
            if queue_name not in self.queues or not self.queues[queue_name]:
                return dequeued_jobs
            
            # Create a copy of the queue for processing
            queue = self.queues[queue_name].copy()
            
            # Pop jobs until we have the requested batch size or the queue is empty
            while queue and len(dequeued_jobs) < batch_size:
                # Peek at the top job
                top_job_id = queue[0].job_id
                
                async with self.jobs_lock:
                    job = self.jobs.get(top_job_id)
                
                # If job doesn't exist or is not pending, skip it
                if not job or job.status != JobStatus.PENDING:
                    heapq.heappop(queue)  # Remove from queue
                    continue
                
                # Skip jobs that aren't due yet
                if job.scheduled_for and job.scheduled_for > datetime.utcnow():
                    heapq.heappop(queue)  # Remove from queue for now
                    continue
                
                # Skip jobs with priority levels not in the requested set
                if priority_values and job.priority.value not in priority_values:
                    heapq.heappop(queue)  # Remove from queue
                    continue
                
                # Pop the job from the queue
                heapq.heappop(queue)
                
                # Mark job as reserved
                job.mark_reserved(worker_id)
                
                # Add to dequeued jobs
                dequeued_jobs.append(copy.deepcopy(job))
            
            # Update the actual queue
            self.queues[queue_name] = queue
        
        return dequeued_jobs
    
    async def complete_job(self, job_id: str, result: Any = None) -> bool:
        """Mark a job as completed.
        
        Args:
            job_id: The ID of the job
            result: Optional result data
            
        Returns:
            True if the job was marked as completed, False otherwise
        """
        async with self.jobs_lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.mark_completed(result)
                return True
            return False
    
    async def fail_job(
        self, 
        job_id: str, 
        error: Dict[str, Any],
        retry: bool = False
    ) -> bool:
        """Mark a job as failed.
        
        Args:
            job_id: The ID of the job
            error: Error information
            retry: Whether to retry the job
            
        Returns:
            True if the job was marked as failed, False otherwise
        """
        async with self.jobs_lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            
            if retry and job.can_retry:
                job.mark_retry(error)
                
                # Calculate next execution time
                next_run = datetime.utcnow() + timedelta(seconds=job.retry_delay)
                job.scheduled_for = next_run
                
                # Add back to queue
                async with self.queues_lock:
                    if job.queue not in self.queues:
                        self.queues[job.queue] = []
                    
                    pjob = PrioritizedJob(
                        priority=job.priority.value,
                        created_at=job.created_at,
                        job_id=job.id,
                    )
                    
                    heapq.heappush(self.queues[job.queue], pjob)
            else:
                job.mark_failed(error)
            
            return True
    
    async def cancel_job(self, job_id: str, reason: Optional[str] = None) -> bool:
        """Cancel a pending job.
        
        Args:
            job_id: The ID of the job
            reason: Optional reason for cancellation
            
        Returns:
            True if the job was cancelled, False otherwise
        """
        async with self.jobs_lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            
            # Only pending or retrying jobs can be cancelled
            if job.status not in (JobStatus.PENDING, JobStatus.RETRYING):
                return False
            
            job.mark_cancelled(reason)
            return True
    
    async def list_jobs(
        self,
        queue: Optional[str] = None,
        status: Optional[List[JobStatus]] = None,
        priority: Optional[Priority] = None,
        tags: Optional[List[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "desc"
    ) -> List[Job]:
        """List jobs with filtering.
        
        Args:
            queue: Optional queue name filter
            status: Optional list of status values to include
            priority: Optional priority filter
            tags: Optional list of tags to filter by
            worker_id: Optional worker ID filter
            before: Optional created_at upper bound
            after: Optional created_at lower bound
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            order_by: Field to order by
            order_dir: Order direction ("asc" or "desc")
            
        Returns:
            List of jobs matching the filters
        """
        async with self.jobs_lock:
            # Filter jobs
            filtered_jobs = []
            for job in self.jobs.values():
                # Apply filters
                if queue and job.queue != queue:
                    continue
                
                if status and job.status not in status:
                    continue
                
                if priority and job.priority != priority:
                    continue
                
                if tags and not all(tag in job.tags for tag in tags):
                    continue
                
                if worker_id and job.worker_id != worker_id:
                    continue
                
                if before and job.created_at >= before:
                    continue
                
                if after and job.created_at <= after:
                    continue
                
                filtered_jobs.append(job)
            
            # Sort jobs
            reverse = order_dir.lower() == "desc"
            if order_by == "created_at":
                filtered_jobs.sort(key=lambda j: j.created_at, reverse=reverse)
            elif order_by == "priority":
                filtered_jobs.sort(key=lambda j: j.priority.value, reverse=reverse)
            elif order_by == "scheduled_for":
                # Handle None values for scheduled_for
                def scheduled_for_key(j):
                    return j.scheduled_for or datetime.min
                filtered_jobs.sort(key=scheduled_for_key, reverse=reverse)
            
            # Apply pagination
            paginated_jobs = filtered_jobs[offset:offset + limit]
            
            # Return deep copies to prevent external modifications
            return [copy.deepcopy(job) for job in paginated_jobs]
    
    async def count_jobs(
        self,
        queue: Optional[str] = None,
        status: Optional[List[JobStatus]] = None,
        priority: Optional[Priority] = None,
        tags: Optional[List[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> int:
        """Count jobs with filtering.
        
        Args:
            queue: Optional queue name filter
            status: Optional list of status values to include
            priority: Optional priority filter
            tags: Optional list of tags to filter by
            worker_id: Optional worker ID filter
            before: Optional created_at upper bound
            after: Optional created_at lower bound
            
        Returns:
            Count of jobs matching the filters
        """
        async with self.jobs_lock:
            # Filter jobs
            count = 0
            for job in self.jobs.values():
                # Apply filters
                if queue and job.queue != queue:
                    continue
                
                if status and job.status not in status:
                    continue
                
                if priority and job.priority != priority:
                    continue
                
                if tags and not all(tag in job.tags for tag in tags):
                    continue
                
                if worker_id and job.worker_id != worker_id:
                    continue
                
                if before and job.created_at >= before:
                    continue
                
                if after and job.created_at <= after:
                    continue
                
                count += 1
            
            return count
    
    async def get_queue_sizes(self) -> Dict[str, int]:
        """Get the sizes of all queues.
        
        Returns:
            Dictionary mapping queue names to their sizes
        """
        async with self.queues_lock:
            return {name: len(queue) for name, queue in self.queues.items()}
    
    async def clear_queue(self, queue_name: str) -> int:
        """Clear all jobs from a queue.
        
        Args:
            queue_name: The name of the queue to clear
            
        Returns:
            Number of jobs removed
        """
        async with self.queues_lock:
            if queue_name not in self.queues:
                return 0
            
            count = len(self.queues[queue_name])
            self.queues[queue_name] = []
            return count
    
    async def pause_queue(self, queue_name: str) -> bool:
        """Pause a queue to stop processing new jobs.
        
        Args:
            queue_name: The name of the queue to pause
            
        Returns:
            True if the queue was paused, False otherwise
        """
        async with self.queues_lock:
            self.queue_pause_status[queue_name] = True
            return True
    
    async def resume_queue(self, queue_name: str) -> bool:
        """Resume a paused queue.
        
        Args:
            queue_name: The name of the queue to resume
            
        Returns:
            True if the queue was resumed, False otherwise
        """
        async with self.queues_lock:
            self.queue_pause_status[queue_name] = False
            return True
    
    async def is_queue_paused(self, queue_name: str) -> bool:
        """Check if a queue is paused.
        
        Args:
            queue_name: The name of the queue to check
            
        Returns:
            True if the queue is paused, False otherwise
        """
        async with self.queues_lock:
            return self.queue_pause_status.get(queue_name, False)
    
    async def list_queues(self) -> List[str]:
        """List all queue names.
        
        Returns:
            List of queue names
        """
        async with self.queues_lock:
            return list(self.queues.keys())
    
    async def prune_jobs(
        self,
        status: List[JobStatus],
        older_than: Optional[datetime] = None,
    ) -> int:
        """Remove old jobs with the specified statuses.
        
        Args:
            status: List of job statuses to prune
            older_than: Optional timestamp; jobs older than this will be pruned
            
        Returns:
            Number of jobs pruned
        """
        count = 0
        
        async with self.jobs_lock:
            # Identify jobs to prune
            jobs_to_prune = []
            for job_id, job in self.jobs.items():
                if job.status in status:
                    if older_than is None or job.created_at < older_than:
                        jobs_to_prune.append(job_id)
            
            # Prune the jobs
            for job_id in jobs_to_prune:
                del self.jobs[job_id]
                count += 1
        
        return count
    
    async def requeue_stuck(
        self,
        older_than: datetime,
        status: Optional[List[JobStatus]] = None,
    ) -> int:
        """Requeue jobs that appear to be stuck.
        
        Args:
            older_than: Jobs in an active state for longer than this will be requeued
            status: Optional list of job statuses to consider
            
        Returns:
            Number of jobs requeued
        """
        # Default to active statuses if none provided
        if status is None:
            status = [s for s in JobStatus if s.is_active]
        
        count = 0
        
        async with self.jobs_lock:
            # Find stuck jobs
            stuck_jobs = []
            for job in self.jobs.values():
                if job.status in status:
                    # Check if started and stuck
                    if (job.started_at and job.started_at < older_than and 
                            not job.completed_at):
                        stuck_jobs.append(job)
                    # Or if reserved but never started
                    elif (job.status == JobStatus.RESERVED and 
                          job.created_at < older_than and 
                          not job.started_at):
                        stuck_jobs.append(job)
            
            # Requeue stuck jobs
            for job in stuck_jobs:
                # Reset job status and worker
                job.status = JobStatus.PENDING
                job.worker_id = None
                
                # Add back to queue
                job_queue = job.queue
                
                # Create prioritized job
                pjob = PrioritizedJob(
                    priority=job.priority.value,
                    created_at=job.created_at,
                    job_id=job.id
                )
                
                # Add to the queue
                async with self.queues_lock:
                    if job_queue not in self.queues:
                        self.queues[job_queue] = []
                    
                    heapq.heappush(self.queues[job_queue], pjob)
                
                count += 1
        
        return count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the storage backend.
        
        Returns:
            Dictionary of statistics
        """
        stats: Dict[str, Any] = {}
        
        # Jobs by status
        status_counts: Dict[str, int] = {status.name.lower(): 0 for status in JobStatus}
        
        # Jobs by priority
        priority_counts: Dict[str, int] = {priority.name.lower(): 0 for priority in Priority}
        
        # Jobs by queue
        queue_counts: Dict[str, Dict[str, int]] = {}
        
        # Get counts from jobs
        async with self.jobs_lock:
            total_jobs = len(self.jobs)
            
            for job in self.jobs.values():
                # Count by status
                status_counts[job.status.name.lower()] += 1
                
                # Count by priority
                priority_counts[job.priority.name.lower()] += 1
                
                # Count by queue
                if job.queue not in queue_counts:
                    queue_counts[job.queue] = {status.name.lower(): 0 for status in JobStatus}
                
                queue_counts[job.queue][job.status.name.lower()] += 1
        
        # Compile statistics
        stats["total_jobs"] = total_jobs
        
        # Status counts
        for status, count in status_counts.items():
            stats[f"{status}_jobs"] = count
        
        # Priority counts
        stats["by_priority"] = priority_counts
        
        # Queue counts
        stats["by_queue"] = queue_counts
        
        # Queue size counts (waiting jobs)
        queue_sizes = await self.get_queue_sizes()
        stats["queue_sizes"] = queue_sizes
        
        return stats
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the storage backend.
        
        Returns:
            Dictionary with health check results
        """
        return {
            "status": "healthy",
            "type": "memory",
            "job_count": len(self.jobs),
            "queue_count": len(self.queues),
        }
    
    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncContextManager["Storage"]:
        """Create a transaction context.
        
        For the in-memory implementation, this is a no-op since all operations
        are already atomic within their respective locks.
        
        Yields:
            The storage instance itself
        """
        yield self
    
    @contextlib.asynccontextmanager
    async def create_lock(
        self, 
        lock_name: str, 
        timeout: int = 60,
        owner: Optional[str] = None,
    ) -> AsyncContextManager[bool]:
        """Create a distributed lock.
        
        Args:
            lock_name: Name of the lock
            timeout: Number of seconds until the lock expires
            owner: Optional owner identifier for the lock
            
        Yields:
            True if the lock was acquired
            
        Raises:
            LockAcquisitionError: If the lock could not be acquired
        """
        lock_id = str(uuid.uuid4())
        owner_id = owner or lock_id
        acquired = False
        
        try:
            # Try to acquire the lock
            async with self.locks_lock:
                now = datetime.utcnow()
                
                # Check if lock exists and is expired
                if lock_name in self.locks:
                    lock_info = self.locks[lock_name]
                    expires_at = lock_info["expires_at"]
                    
                    if now >= expires_at:
                        # Lock is expired, we can take it
                        acquired = True
                    else:
                        # Lock is still valid
                        acquired = False
                else:
                    # Lock doesn't exist, we can take it
                    acquired = True
                
                if acquired:
                    # Set the lock
                    self.locks[lock_name] = {
                        "owner": owner_id,
                        "acquired_at": now,
                        "expires_at": now + timedelta(seconds=timeout),
                        "lock_id": lock_id,
                    }
            
            if not acquired:
                raise LockAcquisitionError(f"Failed to acquire lock '{lock_name}'")
            
            # Lock acquired, yield control
            yield acquired
        
        finally:
            # Release the lock if we acquired it
            if acquired:
                async with self.locks_lock:
                    # Only remove if we still own the lock
                    if (lock_name in self.locks and 
                            self.locks[lock_name]["lock_id"] == lock_id):
                        del self.locks[lock_name]
    
    async def batch_create_jobs(self, jobs: List[Job]) -> List[str]:
        """Create multiple jobs in a batch operation.
        
        Args:
            jobs: List of jobs to create
            
        Returns:
            List of created job IDs
        """
        job_ids = []
        
        async with self.jobs_lock:
            for job in jobs:
                # Store a deep copy to prevent external modifications
                self.jobs[job.id] = copy.deepcopy(job)
                job_ids.append(job.id)
        
        return job_ids
    
    async def batch_update_jobs(self, jobs: List[Job]) -> int:
        """Update multiple jobs in a batch operation.
        
        Args:
            jobs: List of jobs to update
            
        Returns:
            Number of jobs updated
        """
        count = 0
        
        async with self.jobs_lock:
            for job in jobs:
                if job.id in self.jobs:
                    # Store a deep copy to prevent external modifications
                    self.jobs[job.id] = copy.deepcopy(job)
                    count += 1
        
        return count
    
    async def schedule_recurring_job(
        self,
        schedule_id: str,
        task: str,
        args: List[Any],
        kwargs: Dict[str, Any],
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        queue: str = "default",
        priority: Priority = Priority.NORMAL,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 0,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
    ) -> str:
        """Schedule a recurring job.
        
        Args:
            schedule_id: Unique identifier for this schedule
            task: Task to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            cron_expression: Cron expression for scheduling (mutually exclusive with interval_seconds)
            interval_seconds: Interval in seconds (mutually exclusive with cron_expression)
            queue: Queue to use
            priority: Priority level
            tags: Optional tags for the job
            metadata: Optional metadata for the job
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Optional timeout in seconds
            
        Returns:
            The schedule ID
            
        Raises:
            ValueError: If neither cron_expression nor interval_seconds is provided
        """
        if not cron_expression and interval_seconds is None:
            raise ValueError(
                "Either cron_expression or interval_seconds must be provided"
            )
        
        if cron_expression and interval_seconds is not None:
            raise ValueError(
                "Only one of cron_expression or interval_seconds should be provided"
            )
        
        # Calculate next run time
        now = datetime.utcnow()
        next_run: Optional[datetime] = None
        
        if cron_expression:
            # Use croniter to calculate next run time from cron expression
            cron = croniter(cron_expression, now)
            next_run = cron.get_next(datetime)
        elif interval_seconds is not None:
            # Simple interval scheduling
            next_run = now + timedelta(seconds=interval_seconds)
        
        # Create schedule record
        schedule = {
            "id": schedule_id,
            "task": task,
            "args": args,
            "kwargs": kwargs,
            "cron_expression": cron_expression,
            "interval_seconds": interval_seconds,
            "queue": queue,
            "priority": priority.name if isinstance(priority, Priority) else priority,
            "tags": tags or [],
            "metadata": metadata or {},
            "max_retries": max_retries,
            "retry_delay": retry_delay,
            "timeout": timeout,
            "created_at": now,
            "updated_at": now,
            "next_run": next_run,
            "last_run": None,
            "last_result": None,
            "run_count": 0,
            "status": "active",  # active or paused
        }
        
        # Store schedule
        async with self.schedules_lock:
            self.schedules[schedule_id] = schedule
        
        return schedule_id
    
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a schedule by ID.
        
        Args:
            schedule_id: The ID of the schedule to get
            
        Returns:
            The schedule if found, None otherwise
        """
        async with self.schedules_lock:
            schedule = self.schedules.get(schedule_id)
            if schedule:
                # Return a deep copy to prevent external modifications
                return copy.deepcopy(schedule)
            return None
    
    async def list_schedules(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List schedules with filtering.
        
        Args:
            status: Optional status filter ("active" or "paused")
            tags: Optional list of tags to filter by
            
        Returns:
            List of schedules matching the filters
        """
        async with self.schedules_lock:
            # Filter schedules
            filtered_schedules = []
            for schedule in self.schedules.values():
                # Apply filters
                if status and schedule["status"] != status:
                    continue
                
                if tags and not all(tag in schedule["tags"] for tag in tags):
                    continue
                
                # Add a deep copy to the results
                filtered_schedules.append(copy.deepcopy(schedule))
            
            return filtered_schedules
    
    async def update_schedule(
        self,
        schedule_id: str,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        queue: Optional[str] = None,
        priority: Optional[Priority] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        timeout: Optional[int] = None,
        status: Optional[str] = None,
    ) -> bool:
        """Update a schedule.
        
        Args:
            schedule_id: The ID of the schedule to update
            cron_expression: Optional new cron expression
            interval_seconds: Optional new interval in seconds
            queue: Optional new queue
            priority: Optional new priority level
            tags: Optional new tags
            metadata: Optional new metadata
            max_retries: Optional new maximum retry attempts
            retry_delay: Optional new delay between retries in seconds
            timeout: Optional new timeout in seconds
            status: Optional new status ("active" or "paused")
            
        Returns:
            True if the schedule was updated, False otherwise
        """
        async with self.schedules_lock:
            if schedule_id not in self.schedules:
                return False
            
            schedule = self.schedules[schedule_id]
            
            # Update fields if provided
            if cron_expression is not None:
                schedule["cron_expression"] = cron_expression
                schedule["interval_seconds"] = None
                
                # Recalculate next run time
                now = datetime.utcnow()
                cron = croniter(cron_expression, now)
                schedule["next_run"] = cron.get_next(datetime)
            
            if interval_seconds is not None:
                schedule["interval_seconds"] = interval_seconds
                schedule["cron_expression"] = None
                
                # Recalculate next run time
                now = datetime.utcnow()
                schedule["next_run"] = now + timedelta(seconds=interval_seconds)
            
            if queue is not None:
                schedule["queue"] = queue
            
            if priority is not None:
                schedule["priority"] = priority.name if isinstance(priority, Priority) else priority
            
            if tags is not None:
                schedule["tags"] = tags
            
            if metadata is not None:
                # Merge metadata rather than replace
                if schedule["metadata"] is None:
                    schedule["metadata"] = {}
                schedule["metadata"].update(metadata)
            
            if max_retries is not None:
                schedule["max_retries"] = max_retries
            
            if retry_delay is not None:
                schedule["retry_delay"] = retry_delay
            
            if timeout is not None:
                schedule["timeout"] = timeout
            
            if status is not None:
                if status not in ("active", "paused"):
                    raise ValueError("Status must be 'active' or 'paused'")
                schedule["status"] = status
            
            # Update the updated_at timestamp
            schedule["updated_at"] = datetime.utcnow()
            
            return True
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule.
        
        Args:
            schedule_id: The ID of the schedule to delete
            
        Returns:
            True if the schedule was deleted, False otherwise
        """
        async with self.schedules_lock:
            if schedule_id in self.schedules:
                del self.schedules[schedule_id]
                return True
            return False
    
    async def get_due_jobs(
        self,
        limit: int = 100,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Get jobs that are due for execution based on their schedules.
        
        Args:
            limit: Maximum number of due jobs to return
            
        Returns:
            List of (schedule_id, job_data) tuples for due jobs
        """
        due_jobs: List[Tuple[str, Dict[str, Any]]] = []
        now = datetime.utcnow()
        
        async with self.schedules_lock:
            # Find due schedules
            for schedule_id, schedule in self.schedules.items():
                # Skip paused schedules
                if schedule["status"] != "active":
                    continue
                
                # Skip schedules without a next run time
                if not schedule["next_run"]:
                    continue
                
                # Check if the schedule is due
                if schedule["next_run"] <= now:
                    # Create job data for this schedule
                    job_data = {
                        "task": schedule["task"],
                        "args": schedule["args"],
                        "kwargs": schedule["kwargs"],
                        "queue": schedule["queue"],
                        "priority": schedule["priority"],
                        "tags": schedule["tags"],
                        "metadata": {
                            **(schedule["metadata"] or {}),
                            "schedule_id": schedule_id,
                            "scheduled_run": schedule["next_run"].isoformat(),
                        },
                        "max_retries": schedule["max_retries"],
                        "retry_delay": schedule["retry_delay"],
                        "timeout": schedule["timeout"],
                    }
                    
                    due_jobs.append((schedule_id, job_data))
                    
                    # Update schedule for next run
                    if len(due_jobs) >= limit:
                        break
            
            # Update schedules with new next run times
            for schedule_id, _ in due_jobs:
                schedule = self.schedules[schedule_id]
                
                # Update run statistics
                schedule["last_run"] = now
                schedule["run_count"] += 1
                
                # Calculate next run time
                if schedule["cron_expression"]:
                    cron = croniter(schedule["cron_expression"], now)
                    schedule["next_run"] = cron.get_next(datetime)
                elif schedule["interval_seconds"] is not None:
                    schedule["next_run"] = now + timedelta(seconds=schedule["interval_seconds"])
        
        return due_jobs


from datetime import timedelta