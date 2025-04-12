"""Base worker implementation for the background processing system.

This module defines the abstract base class for all worker implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast
import asyncio
import importlib
import inspect
import logging
import signal
import sys
import time
import traceback
import uuid

from uno.jobs.queue import Job, JobQueue, Priority, JobStatus
from uno.jobs.tasks import TaskRegistry, task, TaskMiddleware, get_current_job, set_current_job, reset_current_job


class WorkerError(Exception):
    """Base class for worker-related errors."""
    pass


class WorkerShutdownError(WorkerError):
    """Error raised when a worker is shutting down."""
    pass


class WorkerTaskError(WorkerError):
    """Error raised when a task execution fails."""
    pass


class Worker(ABC):
    """Abstract base class for all worker implementations.
    
    Workers are responsible for processing jobs from a queue, executing
    the corresponding tasks, and reporting results.
    """
    
    def __init__(
        self,
        queue_name: str = "default",
        worker_id: Optional[str] = None,
        priority_levels: Optional[List[Priority]] = None,
        prefetch: bool = True,
        poll_interval: float = 1.0,
        shutdown_timeout: float = 30.0,
        heartbeat_interval: float = 30.0,
        max_job_duration: Optional[float] = None,
        max_failures: int = 100,
        metrics_enabled: bool = True,
        metrics_interval: float = 10.0,
        healthcheck_interval: float = 60.0,
        middleware: Optional[List["Middleware"]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a worker.
        
        Args:
            queue_name: Name of the queue to process
            worker_id: Unique identifier for this worker (generated if not provided)
            priority_levels: Optional list of priority levels to process
            prefetch: Whether to prefetch next jobs while processing
            poll_interval: Seconds to wait between polling when queue is empty
            shutdown_timeout: Maximum time to wait for graceful shutdown
            heartbeat_interval: Seconds between worker heartbeats
            max_job_duration: Maximum job runtime in seconds
            max_failures: Maximum consecutive failures before shutdown
            metrics_enabled: Whether to collect metrics
            metrics_interval: Seconds between metrics collection
            healthcheck_interval: Seconds between health checks
            middleware: Optional list of middleware
            logger: Optional logger instance
        """
        self.queue_name = queue_name
        self.worker_id = worker_id or f"worker-{uuid.uuid4()}"
        self.priority_levels = priority_levels
        self.prefetch = prefetch
        self.poll_interval = poll_interval
        self.shutdown_timeout = shutdown_timeout
        self.heartbeat_interval = heartbeat_interval
        self.max_job_duration = max_job_duration
        self.max_failures = max_failures
        self.metrics_enabled = metrics_enabled
        self.metrics_interval = metrics_interval
        self.healthcheck_interval = healthcheck_interval
        self.middleware = middleware or []
        self.logger = logger or logging.getLogger(f"uno.jobs.worker.{self.worker_id}")
        
        # State tracking
        self.queue: Optional[JobQueue] = None
        self.shutdown_event = asyncio.Event()
        self.paused = False
        self.running = False
        self.failure_count = 0
        self.start_time: Optional[datetime] = None
        
        # Statistics
        self._stats = {
            "jobs_processed_total": 0,
            "jobs_succeeded": 0,
            "jobs_failed": 0,
            "processing_time_ms": [],
            "queue_wait_time_ms": [],
            "active_jobs": 0,
            "errors": {},
        }
    
    @abstractmethod
    async def start(self) -> None:
        """Start the worker.
        
        This method should initialize the worker, set up the queue,
        and begin processing jobs.
        """
        pass
    
    @abstractmethod
    async def shutdown(self, wait: bool = True) -> None:
        """Shut down the worker.
        
        Args:
            wait: Whether to wait for current jobs to complete
        """
        pass
    
    @abstractmethod
    async def pause(self) -> None:
        """Pause job processing.
        
        This method should temporarily stop processing new jobs.
        """
        pass
    
    @abstractmethod
    async def resume(self) -> None:
        """Resume job processing.
        
        This method should resume processing jobs after a pause.
        """
        pass
    
    @abstractmethod
    async def process_job(self, job: Job) -> None:
        """Process a single job.
        
        Args:
            job: The job to process
        """
        pass
    
    @abstractmethod
    async def process_batch(self, jobs: List[Job]) -> None:
        """Process a batch of jobs.
        
        Args:
            jobs: The jobs to process
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the worker.
        
        Returns:
            Dictionary with health check results
        """
        pass
    
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the worker.
        
        Returns:
            Dictionary with metrics
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the worker is running.
        
        Returns:
            True if the worker is running, False otherwise
        """
        pass
    
    @abstractmethod
    def is_paused(self) -> bool:
        """Check if the worker is paused.
        
        Returns:
            True if the worker is paused, False otherwise
        """
        pass
    
    async def _execute_task(self, job: Job) -> Any:
        """Execute a task for a job.
        
        This method handles the actual execution of the task, including
        importing the task module, calling the task function, and handling
        any exceptions that may occur.
        
        Args:
            job: The job containing the task to execute
            
        Returns:
            The result of the task execution
            
        Raises:
            WorkerTaskError: If the task execution fails
        """
        task_name = job.task
        args = job.args
        kwargs = job.kwargs
        version = job.version
        
        try:
            # Get task definition from registry or import it
            task_def = TaskRegistry.get_task(task_name, version=version)
            if task_def is None:
                task_def = TaskRegistry.import_task(task_name)
                if task_def is None:
                    raise WorkerTaskError(f"Task not found: {task_name}")
            
            # Get the task function
            task_func = task_def["func"]
            is_async = task_def["is_async"]
            task_options = task_def["options"]
            
            # Set up job context
            job_context = job.to_dict()
            token = set_current_job(job_context)
            
            try:
                # Apply middleware before task execution
                task_middleware = task_options.get("middleware", [])
                global_middleware = []
                
                # Apply worker middleware
                for mw in self.middleware:
                    modified_args, modified_kwargs = await mw.before_execution(job, task_func, args, kwargs)
                    args, kwargs = modified_args, modified_kwargs
                
                # Apply task middleware
                for mw in task_middleware:
                    args, kwargs = await mw.before_task(task_func, args, kwargs, job_context)
                
                # Execute the task
                if is_async:
                    result = await task_func(*args, **kwargs)
                else:
                    # Run sync function in a thread pool
                    result = await asyncio.to_thread(task_func, *args, **kwargs)
                
                # Apply task middleware for result
                for mw in task_middleware:
                    result = await mw.after_task(task_func, args, kwargs, result, job_context)
                
                # Apply worker middleware for result
                for mw in self.middleware:
                    result = await mw.after_execution(job, task_func, args, kwargs, result)
                
                return result
            
            finally:
                # Reset job context
                reset_current_job(token)
        
        except Exception as e:
            # Capture traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            error_info = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": tb_str,
            }
            
            # Update error statistics
            error_type = type(e).__name__
            self._stats["errors"][error_type] = self._stats["errors"].get(error_type, 0) + 1
            
            raise WorkerTaskError(f"Task execution failed: {e}") from e
    
    def _update_stats(self, success: bool, processing_time_ms: float, queue_wait_time_ms: float) -> None:
        """Update worker statistics.
        
        Args:
            success: Whether the job was processed successfully
            processing_time_ms: Time taken to process the job in milliseconds
            queue_wait_time_ms: Time the job spent in the queue in milliseconds
        """
        if not self.metrics_enabled:
            return
        
        self._stats["jobs_processed_total"] += 1
        
        if success:
            self._stats["jobs_succeeded"] += 1
        else:
            self._stats["jobs_failed"] += 1
        
        # Keep the last 1000 processing times for calculating averages
        self._stats["processing_time_ms"].append(processing_time_ms)
        if len(self._stats["processing_time_ms"]) > 1000:
            self._stats["processing_time_ms"].pop(0)
        
        # Keep the last 1000 queue wait times for calculating averages
        self._stats["queue_wait_time_ms"].append(queue_wait_time_ms)
        if len(self._stats["queue_wait_time_ms"]) > 1000:
            self._stats["queue_wait_time_ms"].pop(0)