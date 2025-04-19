from typing import Dict, List, Optional, Set, Type, Union, Any, Callable
import asyncio
import logging
from datetime import datetime, timedelta, UTC

from uno.core.errors.result import Result
from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.queue import JobQueue
from uno.jobs.queue.status import JobStatus
from uno.jobs.storage.base import JobStorageProtocol
from uno.jobs.worker.base import WorkerBase
from uno.jobs.scheduler.scheduler import Scheduler
from uno.jobs.tasks.task import Task, TaskRegistry


class JobManager:
    """Manages job execution, worker coordination, and system health."""
    
    def __init__(
        self,
        storage: JobStorageProtocol,
        worker_classes: Optional[List[Type[WorkerBase]]] = None,
        scheduler: Optional[Scheduler] = None,
        stall_timeout: timedelta = timedelta(minutes=30),
        cleanup_age: timedelta = timedelta(days=7),
        cleanup_interval: timedelta = timedelta(hours=1),
        health_check_interval: timedelta = timedelta(seconds=30),
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the job manager.
        
        Args:
            storage: The job storage backend to use.
            worker_classes: Optional list of worker classes to instantiate.
            scheduler: Optional scheduler for time-based job creation.
            stall_timeout: Time after which a running job is considered stalled.
            cleanup_age: Age after which completed jobs are deleted.
            cleanup_interval: How often to run cleanup operations.
            health_check_interval: How often to run health checks.
            logger: Optional logger instance.
        """
        self.storage = storage
        self.worker_classes = worker_classes or []
        self.scheduler = scheduler
        self.stall_timeout = stall_timeout
        self.cleanup_age = cleanup_age
        self.cleanup_interval = cleanup_interval
        self.health_check_interval = health_check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self.workers: List[WorkerBase] = []
        self.queues: Dict[str, JobQueue] = {}
        self.running = False
        self._tasks: Set[asyncio.Task] = set()
        self._stop_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the job manager and its workers."""
        if self.running:
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Initialize workers
        for worker_class in self.worker_classes:
            worker = worker_class(storage=self.storage)
            self.workers.append(worker)
            await worker.start()
        
        # Start scheduler if provided
        if self.scheduler:
            await self.scheduler.start()
        
        # Start background tasks
        self._start_background_task(self._cleanup_loop())
        self._start_background_task(self._health_check_loop())
        
        self.logger.info("Job manager started")
    
    async def stop(self) -> None:
        """Stop the job manager and its workers."""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
        # Stop scheduler if provided
        if self.scheduler:
            await self.scheduler.stop()
        
        # Stop all workers
        for worker in self.workers:
            await worker.stop()
        
        # Wait for background tasks to complete
        for task in list(self._tasks):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._tasks.clear()
        self.workers.clear()
        
        self.logger.info("Job manager stopped")
    
    def _start_background_task(self, coro) -> asyncio.Task:
        """Start a background task and add it to the task set.
        
        Args:
            coro: The coroutine to run.
            
        Returns:
            The created task.
        """
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
    async def get_queue(self, queue_name: str) -> JobQueue:
        """Get or create a job queue.
        
        Args:
            queue_name: The name of the queue.
            
        Returns:
            The job queue.
        """
        if queue_name not in self.queues:
            self.queues[queue_name] = JobQueue(queue_name=queue_name, storage=self.storage)
        
        return self.queues[queue_name]
    
    async def enqueue(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        queue_name: str = "default",
        priority: Priority = Priority.NORMAL,
        job_id: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        timeout: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
    ) -> Result[str]:
        """Enqueue a job for execution.
        
        Args:
            task_name: The name of the task to execute.
            args: Optional positional arguments for the task.
            kwargs: Optional keyword arguments for the task.
            queue_name: The name of the queue to place the job in.
            priority: The priority of the job.
            job_id: Optional ID for the job. If not provided, one will be generated.
            scheduled_at: Optional time to execute the job. If not provided, it will be executed ASAP.
            max_retries: Maximum number of retries for the job.
            retry_delay: Time to wait between retries.
            timeout: Optional timeout for job execution.
            metadata: Optional metadata for the job.
            tags: Optional set of tags for the job.
            
        Returns:
            Result with the job ID.
        """
        # Get the queue
        queue = await self.get_queue(queue_name)
        
        # Enqueue the job
        return await queue.enqueue(
            task_name=task_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            job_id=job_id,
            scheduled_at=scheduled_at,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            metadata=metadata,
            tags=tags,
        )
    
    async def get_job(self, job_id: str) -> Result[Optional[Job]]:
        """Get a job by ID.
        
        Args:
            job_id: The ID of the job to retrieve.
            
        Returns:
            Result with the job if found, None if not found.
        """
        return await self.storage.get_job(job_id)
    
    async def cancel_job(self, job_id: str) -> Result[bool]:
        """Cancel a job if it hasn't started yet.
        
        Args:
            job_id: The ID of the job to cancel.
            
        Returns:
            Result with True if the job was cancelled, False if it couldn't be cancelled.
        """
        job_result = await self.get_job(job_id)
        if not job_result.is_success:
            return job_result
            
        job = job_result.value
        if job is None:
            return Result.failure(f"Job {job_id} not found")
            
        if job.status in [JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED]:
            return Result.failure(f"Job {job_id} cannot be cancelled in status {job.status.name}")
            
        job.status = JobStatus.CANCELLED
        job.updated_at = datetime.now(datetime.UTC)
        
        return await self.storage.update_job(job)
    
    async def retry_job(self, job_id: str) -> Result[bool]:
        """Retry a failed job.
        
        Args:
            job_id: The ID of the job to retry.
            
        Returns:
            Result with True if the job was retried, False if it couldn't be retried.
        """
        job_result = await self.get_job(job_id)
        if not job_result.is_success:
            return job_result
            
        job = job_result.value
        if job is None:
            return Result.failure(f"Job {job_id} not found")
            
        if job.status not in [JobStatus.FAILED, JobStatus.CANCELLED]:
            return Result.failure(f"Job {job_id} cannot be retried in status {job.status.name}")
            
        job.status = JobStatus.PENDING
        job.updated_at = datetime.now(datetime.UTC)
        job.error = None
        
        return await self.storage.update_job(job)
    
    async def pause_queue(self, queue_name: str) -> Result[bool]:
        """Pause a queue, preventing jobs from being processed.
        
        Args:
            queue_name: The name of the queue to pause.
            
        Returns:
            Result with True if the queue was paused.
        """
        queue = await self.get_queue(queue_name)
        return await queue.pause()
    
    async def resume_queue(self, queue_name: str) -> Result[bool]:
        """Resume a paused queue.
        
        Args:
            queue_name: The name of the queue to resume.
            
        Returns:
            Result with True if the queue was resumed.
        """
        queue = await self.get_queue(queue_name)
        return await queue.resume()
    
    async def clear_queue(self, queue_name: str) -> Result[int]:
        """Clear all pending jobs from a queue.
        
        Args:
            queue_name: The name of the queue to clear.
            
        Returns:
            Result with the number of jobs cleared.
        """
        queue = await self.get_queue(queue_name)
        return await queue.clear()
    
    async def get_queue_length(self, queue_name: str) -> Result[int]:
        """Get the number of pending jobs in a queue.
        
        Args:
            queue_name: The name of the queue.
            
        Returns:
            Result with the queue length.
        """
        queue = await self.get_queue(queue_name)
        return await queue.get_length()
    
    async def get_queue_names(self) -> Result[Set[str]]:
        """Get all queue names.
        
        Returns:
            Result with a set of queue names.
        """
        return await self.storage.get_queue_names()
    
    async def get_failed_jobs(self, queue_name: Optional[str] = None, limit: int = 100, offset: int = 0) -> Result[List[Job]]:
        """Get failed jobs.
        
        Args:
            queue_name: Optional queue name to filter by.
            limit: Maximum number of jobs to return.
            offset: Offset for pagination.
            
        Returns:
            Result with a list of failed jobs.
        """
        return await self.storage.get_jobs_by_status([JobStatus.FAILED], queue_name, limit, offset)
    
    async def get_running_jobs(self, queue_name: Optional[str] = None, limit: int = 100, offset: int = 0) -> Result[List[Job]]:
        """Get running jobs.
        
        Args:
            queue_name: Optional queue name to filter by.
            limit: Maximum number of jobs to return.
            offset: Offset for pagination.
            
        Returns:
            Result with a list of running jobs.
        """
        return await self.storage.get_jobs_by_status([JobStatus.RUNNING], queue_name, limit, offset)
    
    async def get_pending_jobs(self, queue_name: Optional[str] = None, limit: int = 100, offset: int = 0) -> Result[List[Job]]:
        """Get pending jobs.
        
        Args:
            queue_name: Optional queue name to filter by.
            limit: Maximum number of jobs to return.
            offset: Offset for pagination.
            
        Returns:
            Result with a list of pending jobs.
        """
        return await self.storage.get_jobs_by_status([JobStatus.PENDING], queue_name, limit, offset)
    
    async def get_completed_jobs(self, queue_name: Optional[str] = None, limit: int = 100, offset: int = 0) -> Result[List[Job]]:
        """Get completed jobs.
        
        Args:
            queue_name: Optional queue name to filter by.
            limit: Maximum number of jobs to return.
            offset: Offset for pagination.
            
        Returns:
            Result with a list of completed jobs.
        """
        return await self.storage.get_jobs_by_status([JobStatus.COMPLETED], queue_name, limit, offset)
    
    async def run_job_sync(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[timedelta] = None,
    ) -> Result[Any]:
        """Run a job synchronously, waiting for the result.
        
        Args:
            task_name: The name of the task to run.
            args: Optional positional arguments for the task.
            kwargs: Optional keyword arguments for the task.
            metadata: Optional metadata for the job.
            timeout: Optional timeout for job execution.
            
        Returns:
            Result with the job result.
        """
        # Get the task
        task = TaskRegistry.get_task(task_name)
        if task is None:
            return Result.failure(f"Task {task_name} not found")
            
        # Create a job with a unique ID
        job = Job.create(
            task_name=task_name,
            queue_name="sync",
            args=args or [],
            kwargs=kwargs or {},
            metadata=metadata or {},
            max_retries=0,
            timeout=timeout,
        )
        
        # Run the task
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(datetime.UTC)
            
            # Execute the task
            result = await task.execute(job)
            
            # Update the job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(datetime.UTC)
            job.result = result
            
            return Result.success(result)
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(datetime.UTC)
            job.error = {
                "message": str(e),
                "type": type(e).__name__,
            }
            return Result.failure(str(e))
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up old jobs."""
        while self.running:
            try:
                # Wait for the cleanup interval or stop event
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.cleanup_interval.total_seconds())
                    return  # Stop event was set
                except asyncio.TimeoutError:
                    pass  # Continue with cleanup
                
                # Clean up old jobs
                result = await self.storage.cleanup_old_jobs(self.cleanup_age)
                if result.is_success:
                    self.logger.debug(f"Cleaned up {result.value} old jobs")
                else:
                    self.logger.error(f"Failed to clean up old jobs: {result.error}")
                
                # Mark stalled jobs as failed
                result = await self.storage.mark_stalled_jobs_as_failed(self.stall_timeout)
                if result.is_success and result.value > 0:
                    self.logger.warning(f"Marked {result.value} stalled jobs as failed")
            except Exception as e:
                self.logger.exception(f"Error in cleanup loop: {str(e)}")
    
    async def _health_check_loop(self) -> None:
        """Background task to check system health."""
        while self.running:
            try:
                # Wait for the health check interval or stop event
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.health_check_interval.total_seconds())
                    return  # Stop event was set
                except asyncio.TimeoutError:
                    pass  # Continue with health check
                
                # Check worker health
                for worker in self.workers:
                    if not worker.is_healthy():
                        self.logger.warning(f"Worker {worker.name} is not healthy")
                
                # Check scheduler health
                if self.scheduler and not self.scheduler.is_healthy():
                    self.logger.warning("Scheduler is not healthy")
            except Exception as e:
                self.logger.exception(f"Error in health check loop: {str(e)}")
    
    def register_task(
        self,
        name: str,
        handler: Callable,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
    ) -> None:
        """Register a task with the system.
        
        Args:
            name: The name of the task.
            handler: The function to execute for the task.
            description: Optional description of the task.
            timeout: Optional timeout for the task.
            max_retries: Default max retries for the task.
            retry_delay: Default retry delay for the task.
            queue: Default queue for the task.
        """
        TaskRegistry.register_task(
            name=name,
            handler=handler,
            description=description,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            queue=queue,
        )
    
    def task(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
    ) -> Callable:
        """Decorator to register a task.
        
        Args:
            name: Optional name for the task. Defaults to the function name.
            description: Optional description of the task.
            timeout: Optional timeout for the task.
            max_retries: Default max retries for the task.
            retry_delay: Default retry delay for the task.
            queue: Default queue for the task.
            
        Returns:
            The decorated function.
        """
        def decorator(func):
            task_name = name or func.__name__
            self.register_task(
                name=task_name,
                handler=func,
                description=description,
                timeout=timeout,
                max_retries=max_retries,
                retry_delay=retry_delay,
                queue=queue,
            )
            return func
        return decorator