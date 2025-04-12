"""Job queue implementation for the background processing system.

This module defines the core JobQueue class for managing job queues.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast
import logging

from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus
from uno.jobs.storage.base import Storage


class JobQueue:
    """Job queue for the background processing system.
    
    This class provides high-level operations for working with job queues,
    including enqueueing jobs, dequeuing jobs, and managing job lifecycle.
    """
    
    def __init__(
        self,
        storage: Storage,
        name: str = "default",
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a job queue.
        
        Args:
            storage: Storage backend for persisting jobs
            name: Name of the queue
            logger: Optional logger instance
        """
        self.storage = storage
        self.name = name
        self.logger = logger or logging.getLogger(f"uno.jobs.queue.{name}")
    
    async def enqueue(
        self,
        task: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: Union[Priority, str, int] = Priority.NORMAL,
        scheduled_for: Optional[datetime] = None,
        max_retries: int = 0,
        retry_delay: int = 60,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        version: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> str:
        """Enqueue a new job.
        
        Args:
            task: Task to execute (module.function reference)
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            priority: Priority level for the job
            scheduled_for: When to process the job (None for immediate)
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            tags: Optional tags for categorization and filtering
            metadata: Optional metadata for the job
            timeout: Optional timeout in seconds
            version: Optional version of the task to use
            job_id: Optional specific ID for the job
            
        Returns:
            The ID of the enqueued job
            
        Raises:
            ValueError: If the task is not specified
            Exception: If job enqueueing fails
        """
        if not task:
            raise ValueError("Task must be specified")
        
        # Create a new job
        job = Job(
            id=job_id or Job().id,  # Use provided ID or generate a new one
            task=task,
            args=args or [],
            kwargs=kwargs or {},
            queue=self.name,
            priority=priority,
            status=JobStatus.PENDING,
            scheduled_for=scheduled_for,
            max_retries=max_retries,
            retry_delay=retry_delay,
            tags=tags or [],
            metadata=metadata or {},
            timeout=timeout,
            version=version,
        )
        
        # Enqueue the job
        try:
            job_id = await self.storage.enqueue(self.name, job)
            self.logger.debug(
                f"Enqueued job {job_id} (task={task}, priority={job.priority.name})"
            )
            return job_id
        except Exception as e:
            self.logger.error(f"Failed to enqueue job: {e}")
            raise
    
    async def dequeue(
        self,
        worker_id: str,
        priority_levels: Optional[List[Priority]] = None,
        batch_size: int = 1,
    ) -> List[Job]:
        """Dequeue the next job(s) from the queue.
        
        Args:
            worker_id: ID of the worker requesting the job
            priority_levels: Optional list of priority levels to consider
            batch_size: Maximum number of jobs to dequeue
            
        Returns:
            List of jobs (may be empty if queue is empty)
            
        Raises:
            Exception: If job dequeuing fails
        """
        try:
            jobs = await self.storage.dequeue(
                self.name,
                worker_id,
                priority_levels=priority_levels,
                batch_size=batch_size,
            )
            
            if jobs:
                job_ids = ", ".join(job.id for job in jobs)
                self.logger.debug(f"Dequeued {len(jobs)} jobs: {job_ids}")
            else:
                self.logger.debug("No jobs available for dequeuing")
            
            return jobs
        except Exception as e:
            self.logger.error(f"Failed to dequeue job: {e}")
            raise
    
    async def complete(self, job_id: str, result: Any = None) -> bool:
        """Mark a job as completed.
        
        Args:
            job_id: ID of the job to complete
            result: Optional result data from the job execution
            
        Returns:
            True if the job was completed, False otherwise
            
        Raises:
            Exception: If job completion fails
        """
        try:
            success = await self.storage.complete_job(job_id, result)
            if success:
                self.logger.debug(f"Completed job {job_id}")
            else:
                self.logger.warning(f"Failed to complete job {job_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error completing job {job_id}: {e}")
            raise
    
    async def fail(
        self,
        job_id: str,
        error: Union[Dict[str, Any], Exception, str],
        retry: bool = False,
    ) -> bool:
        """Mark a job as failed.
        
        Args:
            job_id: ID of the job to fail
            error: Error information or exception
            retry: Whether to retry the job if retries are available
            
        Returns:
            True if the job was failed, False otherwise
            
        Raises:
            Exception: If job failure marking fails
        """
        # Convert the error to a dictionary if it's not already
        error_dict: Dict[str, Any]
        if isinstance(error, dict):
            error_dict = error
        elif isinstance(error, Exception):
            error_dict = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": None,  # Traceback would be added by the worker
            }
        else:  # string or other
            error_dict = {
                "type": "Error",
                "message": str(error),
            }
        
        try:
            success = await self.storage.fail_job(job_id, error_dict, retry=retry)
            if success:
                self.logger.debug(
                    f"Failed job {job_id} (retry={retry}): {error_dict.get('message')}"
                )
            else:
                self.logger.warning(f"Could not mark job {job_id} as failed")
            return success
        except Exception as e:
            self.logger.error(f"Error failing job {job_id}: {e}")
            raise
    
    async def cancel(self, job_id: str, reason: Optional[str] = None) -> bool:
        """Cancel a pending job.
        
        Args:
            job_id: ID of the job to cancel
            reason: Optional reason for cancellation
            
        Returns:
            True if the job was cancelled, False otherwise
            
        Raises:
            Exception: If job cancellation fails
        """
        try:
            success = await self.storage.cancel_job(job_id, reason)
            if success:
                self.logger.debug(f"Cancelled job {job_id}")
            else:
                self.logger.warning(f"Could not cancel job {job_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error cancelling job {job_id}: {e}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.
        
        Args:
            job_id: ID of the job to get
            
        Returns:
            The job if found, None otherwise
            
        Raises:
            Exception: If job retrieval fails
        """
        try:
            job = await self.storage.get_job(job_id)
            return job
        except Exception as e:
            self.logger.error(f"Error getting job {job_id}: {e}")
            raise
    
    async def list_jobs(
        self,
        status: Optional[List[Union[JobStatus, str]]] = None,
        priority: Optional[Union[Priority, str, int]] = None,
        tags: Optional[List[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> List[Job]:
        """List jobs with filtering.
        
        Args:
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
        # Convert string status values to JobStatus enums
        status_enums: Optional[List[JobStatus]] = None
        if status:
            status_enums = []
            for s in status:
                if isinstance(s, str):
                    try:
                        status_enums.append(JobStatus[s.upper()])
                    except KeyError:
                        valid_statuses = ", ".join(s.name.lower() for s in JobStatus)
                        raise ValueError(
                            f"Invalid status: {s}. Valid values are: {valid_statuses}"
                        )
                else:
                    status_enums.append(s)
        
        # Convert priority to Priority enum if needed
        priority_enum: Optional[Priority] = None
        if priority is not None:
            if isinstance(priority, Priority):
                priority_enum = priority
            elif isinstance(priority, str):
                priority_enum = Priority.from_string(priority)
            elif isinstance(priority, int):
                for p in Priority:
                    if p.value == priority:
                        priority_enum = p
                        break
        
        try:
            jobs = await self.storage.list_jobs(
                queue=self.name,
                status=status_enums,
                priority=priority_enum,
                tags=tags,
                worker_id=worker_id,
                before=before,
                after=after,
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_dir=order_dir,
            )
            self.logger.debug(f"Listed {len(jobs)} jobs")
            return jobs
        except Exception as e:
            self.logger.error(f"Error listing jobs: {e}")
            raise
    
    async def count_jobs(
        self,
        status: Optional[List[Union[JobStatus, str]]] = None,
        priority: Optional[Union[Priority, str, int]] = None,
        tags: Optional[List[str]] = None,
        worker_id: Optional[str] = None,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> int:
        """Count jobs with filtering.
        
        Args:
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
        # Convert string status values to JobStatus enums
        status_enums: Optional[List[JobStatus]] = None
        if status:
            status_enums = []
            for s in status:
                if isinstance(s, str):
                    try:
                        status_enums.append(JobStatus[s.upper()])
                    except KeyError:
                        valid_statuses = ", ".join(s.name.lower() for s in JobStatus)
                        raise ValueError(
                            f"Invalid status: {s}. Valid values are: {valid_statuses}"
                        )
                else:
                    status_enums.append(s)
        
        # Convert priority to Priority enum if needed
        priority_enum: Optional[Priority] = None
        if priority is not None:
            if isinstance(priority, Priority):
                priority_enum = priority
            elif isinstance(priority, str):
                priority_enum = Priority.from_string(priority)
            elif isinstance(priority, int):
                for p in Priority:
                    if p.value == priority:
                        priority_enum = p
                        break
        
        try:
            count = await self.storage.count_jobs(
                queue=self.name,
                status=status_enums,
                priority=priority_enum,
                tags=tags,
                worker_id=worker_id,
                before=before,
                after=after,
            )
            return count
        except Exception as e:
            self.logger.error(f"Error counting jobs: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for this queue.
        
        Returns:
            Dictionary with queue statistics
            
        Raises:
            Exception: If statistics retrieval fails
        """
        try:
            # Get overall statistics
            stats = await self.storage.get_statistics()
            
            # Filter to just this queue's statistics if available
            if "by_queue" in stats and self.name in stats["by_queue"]:
                queue_stats = stats["by_queue"][self.name]
            else:
                # Calculate queue-specific statistics
                queue_stats = {}
                
                # Get count of jobs by status
                for status in JobStatus:
                    count = await self.count_jobs(status=[status])
                    queue_stats[status.name.lower() + "_jobs"] = count
                
                # Get count by priority
                for priority in Priority:
                    count = await self.count_jobs(priority=priority)
                    queue_stats["priority_" + priority.name.lower()] = count
                
                # Calculate total
                queue_stats["total_jobs"] = sum(
                    queue_stats.get(status.name.lower() + "_jobs", 0)
                    for status in JobStatus
                )
            
            return queue_stats
        except Exception as e:
            self.logger.error(f"Error getting queue statistics: {e}")
            raise
    
    async def pause(self) -> bool:
        """Pause this queue to stop processing new jobs.
        
        Returns:
            True if the queue was paused, False otherwise
            
        Raises:
            Exception: If queue pausing fails
        """
        try:
            success = await self.storage.pause_queue(self.name)
            if success:
                self.logger.info(f"Paused queue {self.name}")
            else:
                self.logger.warning(f"Failed to pause queue {self.name}")
            return success
        except Exception as e:
            self.logger.error(f"Error pausing queue {self.name}: {e}")
            raise
    
    async def resume(self) -> bool:
        """Resume a paused queue.
        
        Returns:
            True if the queue was resumed, False otherwise
            
        Raises:
            Exception: If queue resuming fails
        """
        try:
            success = await self.storage.resume_queue(self.name)
            if success:
                self.logger.info(f"Resumed queue {self.name}")
            else:
                self.logger.warning(f"Failed to resume queue {self.name}")
            return success
        except Exception as e:
            self.logger.error(f"Error resuming queue {self.name}: {e}")
            raise
    
    async def clear(self) -> int:
        """Clear all jobs from this queue.
        
        Returns:
            Number of jobs removed
            
        Raises:
            Exception: If queue clearing fails
        """
        try:
            count = await self.storage.clear_queue(self.name)
            self.logger.info(f"Cleared {count} jobs from queue {self.name}")
            return count
        except Exception as e:
            self.logger.error(f"Error clearing queue {self.name}: {e}")
            raise
    
    async def prune(
        self,
        status: Optional[List[Union[JobStatus, str]]] = None,
        older_than: Optional[Union[datetime, timedelta]] = None,
    ) -> int:
        """Remove old jobs with the specified statuses.
        
        Args:
            status: List of job statuses to prune (defaults to terminal statuses)
            older_than: Jobs older than this will be pruned
                (can be a datetime or a timedelta from now)
            
        Returns:
            Number of jobs pruned
            
        Raises:
            Exception: If job pruning fails
        """
        # Default to terminal statuses
        status_enums: List[JobStatus]
        if status is None:
            status_enums = [s for s in JobStatus if s.is_terminal]
        else:
            status_enums = []
            for s in status:
                if isinstance(s, str):
                    try:
                        status_enums.append(JobStatus[s.upper()])
                    except KeyError:
                        valid_statuses = ", ".join(s.name.lower() for s in JobStatus)
                        raise ValueError(
                            f"Invalid status: {s}. Valid values are: {valid_statuses}"
                        )
                else:
                    status_enums.append(s)
        
        # Calculate the cutoff time
        cutoff: Optional[datetime] = None
        if isinstance(older_than, datetime):
            cutoff = older_than
        elif isinstance(older_than, timedelta):
            cutoff = datetime.utcnow() - older_than
        
        try:
            count = await self.storage.prune_jobs(status_enums, cutoff)
            status_names = ", ".join(s.name.lower() for s in status_enums)
            self.logger.info(
                f"Pruned {count} jobs with status {status_names} "
                f"from queue {self.name}"
            )
            return count
        except Exception as e:
            self.logger.error(f"Error pruning jobs: {e}")
            raise
    
    async def requeue_stuck(
        self,
        older_than: Union[datetime, timedelta],
        status: Optional[List[Union[JobStatus, str]]] = None,
    ) -> int:
        """Requeue jobs that appear to be stuck.
        
        Args:
            older_than: Jobs in an active state for longer than this will be requeued
                (can be a datetime or a timedelta from now)
            status: Optional list of job statuses to consider (defaults to active statuses)
            
        Returns:
            Number of jobs requeued
            
        Raises:
            Exception: If job requeuing fails
        """
        # Default to active statuses
        status_enums: List[JobStatus]
        if status is None:
            status_enums = [s for s in JobStatus if s.is_active]
        else:
            status_enums = []
            for s in status:
                if isinstance(s, str):
                    try:
                        status_enums.append(JobStatus[s.upper()])
                    except KeyError:
                        valid_statuses = ", ".join(s.name.lower() for s in JobStatus)
                        raise ValueError(
                            f"Invalid status: {s}. Valid values are: {valid_statuses}"
                        )
                else:
                    status_enums.append(s)
        
        # Calculate the cutoff time
        cutoff: datetime
        if isinstance(older_than, datetime):
            cutoff = older_than
        else:  # timedelta
            cutoff = datetime.utcnow() - older_than
        
        try:
            count = await self.storage.requeue_stuck(cutoff, status_enums)
            status_names = ", ".join(s.name.lower() for s in status_enums)
            self.logger.info(
                f"Requeued {count} stuck jobs with status {status_names} "
                f"from queue {self.name}"
            )
            return count
        except Exception as e:
            self.logger.error(f"Error requeuing stuck jobs: {e}")
            raise
    
    async def is_paused(self) -> bool:
        """Check if this queue is paused.
        
        Returns:
            True if the queue is paused, False otherwise
            
        Raises:
            Exception: If queue status check fails
        """
        try:
            return await self.storage.is_queue_paused(self.name)
        except Exception as e:
            self.logger.error(f"Error checking if queue {self.name} is paused: {e}")
            raise
