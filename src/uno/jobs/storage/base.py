"""Base storage interface for the background processing system.

This module defines the abstract base class for all storage backends.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncContextManager, Tuple
import contextlib

from uno.jobs.queue.job import Job
from uno.jobs.queue.status import JobStatus
from uno.jobs.queue.priority import Priority


class Storage(ABC):
    """Abstract base class for job storage backends.
    
    Storage backends are responsible for persisting jobs, queues, and
    schedules in the background processing system.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend.
        
        This method is called when the storage backend is first created.
        It should set up any necessary connections, tables, or indexes.
        
        Raises:
            Exception: If initialization fails
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shut down the storage backend.
        
        This method is called when the storage backend is being shut down.
        It should clean up any resources, close connections, etc.
        """
        pass
    
    @abstractmethod
    async def create_job(self, job: Job) -> str:
        """Create a new job record.
        
        Args:
            job: The job to create
            
        Returns:
            The ID of the created job
            
        Raises:
            Exception: If job creation fails
        """
        pass
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.
        
        Args:
            job_id: The ID of the job to get
            
        Returns:
            The job if found, None otherwise
            
        Raises:
            Exception: If job retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_job(self, job: Job) -> bool:
        """Update a job.
        
        Args:
            job: The job to update
            
        Returns:
            True if the job was updated, False otherwise
            
        Raises:
            Exception: If job update fails
        """
        pass
    
    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job.
        
        Args:
            job_id: The ID of the job to delete
            
        Returns:
            True if the job was deleted, False otherwise
            
        Raises:
            Exception: If job deletion fails
        """
        pass
    
    @abstractmethod
    async def enqueue(self, queue_name: str, job: Job) -> str:
        """Add a job to a queue.
        
        Args:
            queue_name: The name of the queue
            job: The job to enqueue
            
        Returns:
            The ID of the enqueued job
            
        Raises:
            Exception: If job enqueuing fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If job dequeuing fails
        """
        pass
    
    @abstractmethod
    async def complete_job(self, job_id: str, result: Any = None) -> bool:
        """Mark a job as completed.
        
        Args:
            job_id: The ID of the job
            result: Optional result data
            
        Returns:
            True if the job was marked as completed, False otherwise
            
        Raises:
            Exception: If job completion fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If job failure marking fails
        """
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str, reason: Optional[str] = None) -> bool:
        """Cancel a pending job.
        
        Args:
            job_id: The ID of the job
            reason: Optional reason for cancellation
            
        Returns:
            True if the job was cancelled, False otherwise
            
        Raises:
            Exception: If job cancellation fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If job listing fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If job counting fails
        """
        pass
    
    @abstractmethod
    async def get_queue_sizes(self) -> Dict[str, int]:
        """Get the sizes of all queues.
        
        Returns:
            Dictionary mapping queue names to their sizes
            
        Raises:
            Exception: If queue size retrieval fails
        """
        pass
    
    @abstractmethod
    async def clear_queue(self, queue_name: str) -> int:
        """Clear all jobs from a queue.
        
        Args:
            queue_name: The name of the queue to clear
            
        Returns:
            Number of jobs removed
            
        Raises:
            Exception: If queue clearing fails
        """
        pass
    
    @abstractmethod
    async def pause_queue(self, queue_name: str) -> bool:
        """Pause a queue to stop processing new jobs.
        
        Args:
            queue_name: The name of the queue to pause
            
        Returns:
            True if the queue was paused, False otherwise
            
        Raises:
            Exception: If queue pausing fails
        """
        pass
    
    @abstractmethod
    async def resume_queue(self, queue_name: str) -> bool:
        """Resume a paused queue.
        
        Args:
            queue_name: The name of the queue to resume
            
        Returns:
            True if the queue was resumed, False otherwise
            
        Raises:
            Exception: If queue resuming fails
        """
        pass
    
    @abstractmethod
    async def is_queue_paused(self, queue_name: str) -> bool:
        """Check if a queue is paused.
        
        Args:
            queue_name: The name of the queue to check
            
        Returns:
            True if the queue is paused, False otherwise
            
        Raises:
            Exception: If queue status check fails
        """
        pass
    
    @abstractmethod
    async def list_queues(self) -> List[str]:
        """List all queue names.
        
        Returns:
            List of queue names
            
        Raises:
            Exception: If queue listing fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If job pruning fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If job requeuing fails
        """
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the storage backend.
        
        Returns:
            Dictionary of statistics
            
        Raises:
            Exception: If statistics retrieval fails
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the storage backend.
        
        Returns:
            Dictionary with health check results
            
        Raises:
            Exception: If health check fails
        """
        pass
    
    @abstractmethod
    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncContextManager["Storage"]:
        """Create a transaction context.
        
        This context manager allows multiple operations to be performed
        atomically within a single transaction.
        
        Yields:
            A storage instance for use within the transaction
            
        Raises:
            Exception: If transaction creation fails
        """
        yield self
    
    @abstractmethod
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
            
        Returns:
            An async context manager that yields True if the lock was acquired
            
        Raises:
            Exception: If lock creation fails
        """
        pass
    
    @abstractmethod
    async def batch_create_jobs(self, jobs: List[Job]) -> List[str]:
        """Create multiple jobs in a batch operation.
        
        Args:
            jobs: List of jobs to create
            
        Returns:
            List of created job IDs
            
        Raises:
            Exception: If batch job creation fails
        """
        pass
    
    @abstractmethod
    async def batch_update_jobs(self, jobs: List[Job]) -> int:
        """Update multiple jobs in a batch operation.
        
        Args:
            jobs: List of jobs to update
            
        Returns:
            Number of jobs updated
            
        Raises:
            Exception: If batch job update fails
        """
        pass
    
    @abstractmethod
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
            Exception: If schedule creation fails
        """
        pass
    
    @abstractmethod
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a schedule by ID.
        
        Args:
            schedule_id: The ID of the schedule to get
            
        Returns:
            The schedule if found, None otherwise
            
        Raises:
            Exception: If schedule retrieval fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If schedule listing fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            Exception: If schedule update fails
        """
        pass
    
    @abstractmethod
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule.
        
        Args:
            schedule_id: The ID of the schedule to delete
            
        Returns:
            True if the schedule was deleted, False otherwise
            
        Raises:
            Exception: If schedule deletion fails
        """
        pass
    
    @abstractmethod
    async def get_due_jobs(
        self,
        limit: int = 100,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Get jobs that are due for execution based on their schedules.
        
        Args:
            limit: Maximum number of due jobs to return
            
        Returns:
            List of (schedule_id, job_data) tuples for due jobs
            
        Raises:
            Exception: If due job retrieval fails
        """
        pass
