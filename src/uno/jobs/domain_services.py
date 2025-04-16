# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import logging
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, Union, runtime_checkable, Type
import uuid

from uno.core.errors.result import Result
from uno.domain.service import DomainService
from uno.jobs.entities import Job, JobPriority, JobStatus, Schedule, ScheduleInterval, JobError
from uno.jobs.domain_repositories import JobRepositoryProtocol, ScheduleRepositoryProtocol


@runtime_checkable
class TaskRegistryProtocol(Protocol):
    """Protocol for task registry."""
    
    def register_task(
        self,
        name: str,
        handler: Any,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
        version: Optional[str] = None,
    ) -> None:
        """Register a task with the system."""
        ...
    
    def get_task(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a task by name and optional version."""
        ...
    
    def list_tasks(
        self,
    ) -> List[Dict[str, Any]]:
        """List all registered tasks."""
        ...
    
    def import_task(
        self,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """Import a task by name."""
        ...
    
    async def execute_task(
        self,
        task_name: str,
        args: List[Any],
        kwargs: Dict[str, Any],
        version: Optional[str] = None,
    ) -> Any:
        """Execute a task."""
        ...


@runtime_checkable
class JobManagerServiceProtocol(Protocol):
    """Protocol for job manager service."""
    
    async def enqueue(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        queue_name: str = "default",
        priority: JobPriority = JobPriority.NORMAL,
        job_id: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay: Union[int, timedelta] = 60,
        timeout: Optional[Union[int, timedelta]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
        version: Optional[str] = None,
    ) -> Result[str]:
        """Enqueue a job for execution."""
        ...
    
    async def get_job(
        self,
        job_id: str,
    ) -> Result[Optional[Job]]:
        """Get a job by ID."""
        ...
    
    async def cancel_job(
        self,
        job_id: str,
        reason: Optional[str] = None,
    ) -> Result[bool]:
        """Cancel a job if it hasn't started yet."""
        ...
    
    async def retry_job(
        self,
        job_id: str,
    ) -> Result[bool]:
        """Retry a failed job."""
        ...
    
    async def pause_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Pause a queue, preventing jobs from being processed."""
        ...
    
    async def resume_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Resume a paused queue."""
        ...
    
    async def clear_queue(
        self,
        queue_name: str,
    ) -> Result[int]:
        """Clear all pending jobs from a queue."""
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
    
    async def get_failed_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get failed jobs."""
        ...
    
    async def get_running_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get running jobs."""
        ...
    
    async def get_pending_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get pending jobs."""
        ...
    
    async def get_completed_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get completed jobs."""
        ...
    
    async def run_job_sync(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[Union[int, timedelta]] = None,
        version: Optional[str] = None,
    ) -> Result[Any]:
        """Run a job synchronously, waiting for the result."""
        ...
    
    async def schedule_job(
        self,
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
    ) -> Result[str]:
        """Schedule a recurring job."""
        ...
    
    async def get_schedule(
        self,
        schedule_id: str,
    ) -> Result[Optional[Schedule]]:
        """Get a schedule by ID."""
        ...
    
    async def update_schedule(
        self,
        schedule_id: str,
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        interval: Optional[ScheduleInterval] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        queue_name: Optional[str] = None,
        priority: Optional[JobPriority] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[Union[int, timedelta]] = None,
        timeout: Optional[Union[int, timedelta]] = None,
        status: Optional[str] = None,
    ) -> Result[bool]:
        """Update a schedule."""
        ...
    
    async def delete_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Delete a schedule."""
        ...
    
    async def pause_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Pause a schedule."""
        ...
    
    async def resume_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Resume a schedule."""
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
    
    async def start(self) -> None:
        """Start the job manager and its workers."""
        ...
    
    async def stop(self) -> None:
        """Stop the job manager and its workers."""
        ...
    
    def is_running(self) -> bool:
        """Check if the job manager is running."""
        ...
    
    def register_task(
        self,
        name: str,
        handler: Any,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
        version: Optional[str] = None,
    ) -> None:
        """Register a task with the system."""
        ...
    
    def task(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
        version: Optional[str] = None,
    ) -> Any:
        """Decorator to register a task."""
        ...


class TaskRegistryService(DomainService, TaskRegistryProtocol):
    """Service for managing task registry."""
    
    def __init__(self):
        """Initialize the task registry service."""
        self.tasks = {}
    
    def register_task(
        self,
        name: str,
        handler: Any,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
        version: Optional[str] = None,
    ) -> None:
        """Register a task with the system."""
        # Validate task name
        if not name:
            raise ValueError("Task name must be provided")
        
        # Determine if the handler is an async function
        import inspect
        is_async = inspect.iscoroutinefunction(handler)
        
        # Create task definition
        task_def = {
            "name": name,
            "func": handler,
            "description": description,
            "is_async": is_async,
            "options": {
                "timeout": timeout,
                "max_retries": max_retries,
                "retry_delay": retry_delay,
                "queue": queue,
            },
            "version": version,
        }
        
        # Register the task
        task_key = self._get_task_key(name, version)
        self.tasks[task_key] = task_def
    
    def get_task(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a task by name and optional version."""
        task_key = self._get_task_key(name, version)
        return self.tasks.get(task_key)
    
    def list_tasks(
        self,
    ) -> List[Dict[str, Any]]:
        """List all registered tasks."""
        return list(self.tasks.values())
    
    def import_task(
        self,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """Import a task by name."""
        if "." not in name:
            return None
        
        try:
            module_name, func_name = name.rsplit(".", 1)
            
            # Import the module
            import importlib
            module = importlib.import_module(module_name)
            
            # Get the function
            func = getattr(module, func_name, None)
            
            if func is None:
                return None
            
            # Register the imported task
            self.register_task(
                name=name,
                handler=func,
                description=func.__doc__,
            )
            
            return self.get_task(name)
        except (ImportError, AttributeError) as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to import task {name}: {str(e)}")
            return None
    
    async def execute_task(
        self,
        task_name: str,
        args: List[Any],
        kwargs: Dict[str, Any],
        version: Optional[str] = None,
    ) -> Any:
        """Execute a task."""
        # Get the task
        task = self.get_task(task_name, version)
        if task is None:
            task = self.import_task(task_name)
            if task is None:
                raise ValueError(f"Task not found: {task_name}")
        
        # Get the task function
        task_func = task["func"]
        is_async = task["is_async"]
        
        # Execute the task
        if is_async:
            return await task_func(*args, **kwargs)
        else:
            # Run sync function in a thread pool
            return await asyncio.to_thread(task_func, *args, **kwargs)
    
    def _get_task_key(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> str:
        """Get a unique key for a task based on name and version."""
        if version:
            return f"{name}@{version}"
        else:
            return name


class JobManagerService(DomainService, JobManagerServiceProtocol):
    """Service for managing jobs and schedules."""
    
    def __init__(
        self,
        job_repository: JobRepositoryProtocol,
        schedule_repository: ScheduleRepositoryProtocol,
        task_registry: TaskRegistryProtocol,
        worker_classes: Optional[List[Any]] = None,
        stall_timeout: timedelta = timedelta(minutes=30),
        cleanup_age: timedelta = timedelta(days=7),
        cleanup_interval: timedelta = timedelta(hours=1),
        health_check_interval: timedelta = timedelta(seconds=30),
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the job manager service."""
        self.job_repository = job_repository
        self.schedule_repository = schedule_repository
        self.task_registry = task_registry
        self.worker_classes = worker_classes or []
        self.stall_timeout = stall_timeout
        self.cleanup_age = cleanup_age
        self.cleanup_interval = cleanup_interval
        self.health_check_interval = health_check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        # State tracking
        self.workers = []
        self.running = False
        self._tasks = set()
        self._stop_event = asyncio.Event()
    
    async def enqueue(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        queue_name: str = "default",
        priority: JobPriority = JobPriority.NORMAL,
        job_id: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay: Union[int, timedelta] = 60,
        timeout: Optional[Union[int, timedelta]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
        version: Optional[str] = None,
    ) -> Result[str]:
        """Enqueue a job for execution."""
        # Verify task exists
        task = self.task_registry.get_task(task_name, version)
        if task is None:
            # Try to import the task
            task = self.task_registry.import_task(task_name)
            if task is None:
                return Result.failure(f"Task not found: {task_name}")
        
        # Create the job entity
        job = Job.create(
            task_name=task_name,
            args=args,
            kwargs=kwargs,
            queue_name=queue_name,
            priority=priority,
            job_id=job_id,
            scheduled_at=scheduled_at,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            metadata=metadata,
            tags=tags,
            version=version,
        )
        
        # Enqueue the job
        return await self.job_repository.enqueue(job)
    
    async def get_job(
        self,
        job_id: str,
    ) -> Result[Optional[Job]]:
        """Get a job by ID."""
        return await self.job_repository.get_job(job_id)
    
    async def cancel_job(
        self,
        job_id: str,
        reason: Optional[str] = None,
    ) -> Result[bool]:
        """Cancel a job if it hasn't started yet."""
        return await self.job_repository.mark_job_cancelled(job_id, reason)
    
    async def retry_job(
        self,
        job_id: str,
    ) -> Result[bool]:
        """Retry a failed job."""
        return await self.job_repository.retry_job(job_id)
    
    async def pause_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Pause a queue, preventing jobs from being processed."""
        return await self.job_repository.pause_queue(queue_name)
    
    async def resume_queue(
        self,
        queue_name: str,
    ) -> Result[bool]:
        """Resume a paused queue."""
        return await self.job_repository.resume_queue(queue_name)
    
    async def clear_queue(
        self,
        queue_name: str,
    ) -> Result[int]:
        """Clear all pending jobs from a queue."""
        return await self.job_repository.clear_queue(queue_name)
    
    async def get_queue_length(
        self,
        queue_name: str,
    ) -> Result[int]:
        """Get the number of pending jobs in a queue."""
        return await self.job_repository.get_queue_length(queue_name)
    
    async def get_queue_names(
        self,
    ) -> Result[Set[str]]:
        """Get all queue names."""
        return await self.job_repository.get_queue_names()
    
    async def get_failed_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get failed jobs."""
        return await self.job_repository.list_jobs(
            queue_name=queue_name,
            status=[JobStatus.FAILED],
            limit=limit,
            offset=offset,
        )
    
    async def get_running_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get running jobs."""
        return await self.job_repository.list_jobs(
            queue_name=queue_name,
            status=[JobStatus.RUNNING],
            limit=limit,
            offset=offset,
        )
    
    async def get_pending_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get pending jobs."""
        return await self.job_repository.list_jobs(
            queue_name=queue_name,
            status=[JobStatus.PENDING],
            limit=limit,
            offset=offset,
        )
    
    async def get_completed_jobs(
        self,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Job]]:
        """Get completed jobs."""
        return await self.job_repository.list_jobs(
            queue_name=queue_name,
            status=[JobStatus.COMPLETED],
            limit=limit,
            offset=offset,
        )
    
    async def run_job_sync(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[Union[int, timedelta]] = None,
        version: Optional[str] = None,
    ) -> Result[Any]:
        """Run a job synchronously, waiting for the result."""
        try:
            # Create a unique job ID
            job_id = str(uuid.uuid4())
            
            # Create a job entity
            job = Job.create(
                task_name=task_name,
                args=args or [],
                kwargs=kwargs or {},
                metadata=metadata or {},
                max_retries=0,
                timeout=timeout,
                job_id=job_id,
                version=version,
                queue_name="sync",  # Use special queue name for sync jobs
            )
            
            # Mark the job as running
            job.mark_running()
            
            # Execute the task directly
            result = await self.task_registry.execute_task(
                task_name=task_name,
                args=args or [],
                kwargs=kwargs or {},
                version=version,
            )
            
            # Mark the job as completed
            job.mark_completed(result)
            
            return Result.success(result)
        except Exception as e:
            return Result.failure(str(e))
    
    async def schedule_job(
        self,
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
    ) -> Result[str]:
        """Schedule a recurring job."""
        # Verify task exists
        task = self.task_registry.get_task(task_name, version)
        if task is None:
            # Try to import the task
            task = self.task_registry.import_task(task_name)
            if task is None:
                return Result.failure(f"Task not found: {task_name}")
        
        # Create the schedule entity
        try:
            schedule = Schedule.create(
                name=name,
                task_name=task_name,
                cron_expression=cron_expression,
                interval=interval,
                args=args,
                kwargs=kwargs,
                queue_name=queue_name,
                priority=priority,
                tags=tags,
                metadata=metadata,
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout,
                version=version,
                schedule_id=schedule_id,
            )
        except ValueError as e:
            return Result.failure(str(e))
        
        # Create the schedule
        return await self.schedule_repository.create_schedule(schedule)
    
    async def get_schedule(
        self,
        schedule_id: str,
    ) -> Result[Optional[Schedule]]:
        """Get a schedule by ID."""
        return await self.schedule_repository.get_schedule(schedule_id)
    
    async def update_schedule(
        self,
        schedule_id: str,
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        interval: Optional[ScheduleInterval] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        queue_name: Optional[str] = None,
        priority: Optional[JobPriority] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[Union[int, timedelta]] = None,
        timeout: Optional[Union[int, timedelta]] = None,
        status: Optional[str] = None,
    ) -> Result[bool]:
        """Update a schedule."""
        # Get the existing schedule
        schedule_result = await self.schedule_repository.get_schedule(schedule_id)
        if not schedule_result.is_success:
            return schedule_result
        
        schedule = schedule_result.value
        if schedule is None:
            return Result.failure(f"Schedule {schedule_id} not found")
        
        # Update schedule fields
        if name is not None:
            schedule.name = name
        
        if cron_expression is not None and interval is not None:
            return Result.failure("Cannot specify both cron_expression and interval")
        
        if cron_expression is not None:
            schedule.cron_expression = cron_expression
            schedule.interval = None
        
        if interval is not None:
            schedule.interval = interval
            schedule.cron_expression = None
        
        if args is not None:
            schedule.args = args
        
        if kwargs is not None:
            schedule.kwargs = kwargs
        
        if queue_name is not None:
            schedule.queue_name = queue_name
        
        if priority is not None:
            schedule.priority = priority
        
        if tags is not None:
            schedule.tags = tags
        
        if metadata is not None:
            schedule.metadata = metadata
        
        if max_retries is not None:
            schedule.max_retries = max_retries
        
        if retry_delay is not None:
            if isinstance(retry_delay, int):
                retry_delay = timedelta(seconds=retry_delay)
            schedule.retry_delay = retry_delay
        
        if timeout is not None:
            if isinstance(timeout, int):
                timeout = timedelta(seconds=timeout)
            schedule.timeout = timeout
        
        if status is not None:
            if status not in ["active", "paused"]:
                return Result.failure("Status must be either 'active' or 'paused'")
            schedule.status = status
        
        # Update the schedule's updated_at timestamp
        schedule.updated_at = datetime.now(UTC)
        
        # Update the schedule
        return await self.schedule_repository.update_schedule(schedule)
    
    async def delete_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Delete a schedule."""
        return await self.schedule_repository.delete_schedule(schedule_id)
    
    async def pause_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Pause a schedule."""
        # Get the schedule
        schedule_result = await self.schedule_repository.get_schedule(schedule_id)
        if not schedule_result.is_success:
            return schedule_result
        
        schedule = schedule_result.value
        if schedule is None:
            return Result.failure(f"Schedule {schedule_id} not found")
        
        # Pause the schedule
        schedule.pause()
        
        # Update the schedule
        return await self.schedule_repository.update_schedule(schedule)
    
    async def resume_schedule(
        self,
        schedule_id: str,
    ) -> Result[bool]:
        """Resume a schedule."""
        # Get the schedule
        schedule_result = await self.schedule_repository.get_schedule(schedule_id)
        if not schedule_result.is_success:
            return schedule_result
        
        schedule = schedule_result.value
        if schedule is None:
            return Result.failure(f"Schedule {schedule_id} not found")
        
        # Resume the schedule
        schedule.resume()
        
        # Update the schedule
        return await self.schedule_repository.update_schedule(schedule)
    
    async def list_schedules(
        self,
        status: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[List[Schedule]]:
        """List schedules with filtering."""
        return await self.schedule_repository.list_schedules(
            status=status,
            tags=tags,
            limit=limit,
            offset=offset,
        )
    
    async def start(self) -> None:
        """Start the job manager and its workers."""
        if self.running:
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Initialize workers
        for worker_class in self.worker_classes:
            worker = worker_class(storage=self.job_repository)
            self.workers.append(worker)
            await worker.start()
        
        # Start background tasks
        self._start_background_task(self._cleanup_loop())
        self._start_background_task(self._health_check_loop())
        self._start_background_task(self._scheduler_loop())
        
        self.logger.info("Job manager started")
    
    async def stop(self) -> None:
        """Stop the job manager and its workers."""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
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
    
    def is_running(self) -> bool:
        """Check if the job manager is running."""
        return self.running
    
    def register_task(
        self,
        name: str,
        handler: Any,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
        version: Optional[str] = None,
    ) -> None:
        """Register a task with the system."""
        self.task_registry.register_task(
            name=name,
            handler=handler,
            description=description,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            queue=queue,
            version=version,
        )
    
    def task(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=60),
        queue: str = "default",
        version: Optional[str] = None,
    ) -> Any:
        """Decorator to register a task."""
        def decorator(func):
            task_name = name or func.__name__
            self.register_task(
                name=task_name,
                handler=func,
                description=description or func.__doc__,
                timeout=timeout,
                max_retries=max_retries,
                retry_delay=retry_delay,
                queue=queue,
                version=version,
            )
            return func
        return decorator
    
    def _start_background_task(self, coro) -> asyncio.Task:
        """Start a background task and add it to the task set."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
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
                result = await self.job_repository.cleanup_old_jobs(self.cleanup_age)
                if result.is_success:
                    self.logger.debug(f"Cleaned up {result.value} old jobs")
                else:
                    self.logger.error(f"Failed to clean up old jobs: {result.error}")
                
                # Mark stalled jobs as failed
                result = await self.job_repository.mark_stalled_jobs_as_failed(self.stall_timeout)
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
                
            except Exception as e:
                self.logger.exception(f"Error in health check loop: {str(e)}")
    
    async def _scheduler_loop(self) -> None:
        """Background task to run scheduled jobs."""
        while self.running:
            try:
                # Wait for 1 minute or stop event
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=60)
                    return  # Stop event was set
                except asyncio.TimeoutError:
                    pass  # Continue with scheduler
                
                # Get due schedules
                due_schedules_result = await self.schedule_repository.get_due_schedules()
                if not due_schedules_result.is_success:
                    self.logger.error(f"Failed to get due schedules: {due_schedules_result.error}")
                    continue
                
                due_schedules = due_schedules_result.value
                if not due_schedules:
                    continue
                
                # Process each due schedule
                for schedule in due_schedules:
                    try:
                        # Create a job from the schedule
                        job = schedule.create_job()
                        
                        # Enqueue the job
                        job_result = await self.job_repository.enqueue(job)
                        if job_result.is_success:
                            self.logger.debug(f"Created job {job_result.value} from schedule {schedule.id}")
                            
                            # Update the schedule's next run time
                            await self.schedule_repository.update_schedule_next_run(schedule.id)
                        else:
                            self.logger.error(f"Failed to create job from schedule {schedule.id}: {job_result.error}")
                    except Exception as e:
                        self.logger.exception(f"Error processing schedule {schedule.id}: {str(e)}")
            except Exception as e:
                self.logger.exception(f"Error in scheduler loop: {str(e)}")