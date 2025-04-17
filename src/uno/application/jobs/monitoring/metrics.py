from typing import Dict, List, Optional, Union, Any
import time
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

from uno.core.monitoring.metrics import MetricsManager, Metric, MetricType


class JobMetricType(str, Enum):
    """Types of job metrics."""
    JOB_ENQUEUED = "job_enqueued"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_RETRY = "job_retry"
    JOB_CANCELLED = "job_cancelled"
    QUEUE_LENGTH = "queue_length"
    WORKER_BUSY = "worker_busy"
    WORKER_IDLE = "worker_idle"
    EXECUTION_TIME = "execution_time"
    WAIT_TIME = "wait_time"


class JobMetrics:
    """Monitors and records metrics for the background processing system."""
    
    def __init__(
        self,
        metrics_manager: Optional[MetricsManager] = None,
        namespace: str = "uno_jobs",
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the job metrics.
        
        Args:
            metrics_manager: Optional metrics manager. If not provided, a new one will be created.
            namespace: The namespace for the metrics.
            logger: Optional logger.
        """
        self.metrics_manager = metrics_manager or MetricsManager()
        self.namespace = namespace
        self.logger = logger or logging.getLogger(__name__)
        
        # Register metrics
        self._register_metrics()
    
    def _register_metrics(self) -> None:
        """Register all job metrics."""
        # Counter metrics
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.JOB_ENQUEUED}",
            description="Number of jobs enqueued",
            type=MetricType.COUNTER,
            labels=["queue", "task", "priority"],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.JOB_STARTED}",
            description="Number of jobs started",
            type=MetricType.COUNTER,
            labels=["queue", "task", "worker"],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.JOB_COMPLETED}",
            description="Number of jobs completed successfully",
            type=MetricType.COUNTER,
            labels=["queue", "task", "worker"],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.JOB_FAILED}",
            description="Number of jobs that failed",
            type=MetricType.COUNTER,
            labels=["queue", "task", "worker", "error_type"],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.JOB_RETRY}",
            description="Number of job retries",
            type=MetricType.COUNTER,
            labels=["queue", "task"],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.JOB_CANCELLED}",
            description="Number of jobs cancelled",
            type=MetricType.COUNTER,
            labels=["queue", "task"],
        )
        
        # Gauge metrics
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.QUEUE_LENGTH}",
            description="Number of jobs in queue",
            type=MetricType.GAUGE,
            labels=["queue", "status"],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.WORKER_BUSY}",
            description="Number of busy workers",
            type=MetricType.GAUGE,
            labels=["worker_type"],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.WORKER_IDLE}",
            description="Number of idle workers",
            type=MetricType.GAUGE,
            labels=["worker_type"],
        )
        
        # Histogram metrics
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.EXECUTION_TIME}",
            description="Job execution time in seconds",
            type=MetricType.HISTOGRAM,
            labels=["queue", "task"],
            buckets=[0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
        )
        
        self.metrics_manager.register_metric(
            name=f"{self.namespace}.{JobMetricType.WAIT_TIME}",
            description="Job wait time in seconds",
            type=MetricType.HISTOGRAM,
            labels=["queue", "task", "priority"],
            buckets=[0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0],
        )
    
    def record_job_enqueued(self, queue: str, task: str, priority: str) -> None:
        """Record a job enqueued metric.
        
        Args:
            queue: The queue name.
            task: The task name.
            priority: The priority level.
        """
        self.metrics_manager.increment_counter(
            name=f"{self.namespace}.{JobMetricType.JOB_ENQUEUED}",
            labels={"queue": queue, "task": task, "priority": priority},
        )
    
    def record_job_started(self, queue: str, task: str, worker: str) -> None:
        """Record a job started metric.
        
        Args:
            queue: The queue name.
            task: The task name.
            worker: The worker name.
        """
        self.metrics_manager.increment_counter(
            name=f"{self.namespace}.{JobMetricType.JOB_STARTED}",
            labels={"queue": queue, "task": task, "worker": worker},
        )
    
    def record_job_completed(self, queue: str, task: str, worker: str) -> None:
        """Record a job completed metric.
        
        Args:
            queue: The queue name.
            task: The task name.
            worker: The worker name.
        """
        self.metrics_manager.increment_counter(
            name=f"{self.namespace}.{JobMetricType.JOB_COMPLETED}",
            labels={"queue": queue, "task": task, "worker": worker},
        )
    
    def record_job_failed(self, queue: str, task: str, worker: str, error_type: str) -> None:
        """Record a job failed metric.
        
        Args:
            queue: The queue name.
            task: The task name.
            worker: The worker name.
            error_type: The type of error.
        """
        self.metrics_manager.increment_counter(
            name=f"{self.namespace}.{JobMetricType.JOB_FAILED}",
            labels={"queue": queue, "task": task, "worker": worker, "error_type": error_type},
        )
    
    def record_job_retry(self, queue: str, task: str) -> None:
        """Record a job retry metric.
        
        Args:
            queue: The queue name.
            task: The task name.
        """
        self.metrics_manager.increment_counter(
            name=f"{self.namespace}.{JobMetricType.JOB_RETRY}",
            labels={"queue": queue, "task": task},
        )
    
    def record_job_cancelled(self, queue: str, task: str) -> None:
        """Record a job cancelled metric.
        
        Args:
            queue: The queue name.
            task: The task name.
        """
        self.metrics_manager.increment_counter(
            name=f"{self.namespace}.{JobMetricType.JOB_CANCELLED}",
            labels={"queue": queue, "task": task},
        )
    
    def set_queue_length(self, queue: str, status: str, length: int) -> None:
        """Set the queue length metric.
        
        Args:
            queue: The queue name.
            status: The job status.
            length: The queue length.
        """
        self.metrics_manager.set_gauge(
            name=f"{self.namespace}.{JobMetricType.QUEUE_LENGTH}",
            value=length,
            labels={"queue": queue, "status": status},
        )
    
    def set_worker_busy(self, worker_type: str, count: int) -> None:
        """Set the worker busy metric.
        
        Args:
            worker_type: The type of worker.
            count: The number of busy workers.
        """
        self.metrics_manager.set_gauge(
            name=f"{self.namespace}.{JobMetricType.WORKER_BUSY}",
            value=count,
            labels={"worker_type": worker_type},
        )
    
    def set_worker_idle(self, worker_type: str, count: int) -> None:
        """Set the worker idle metric.
        
        Args:
            worker_type: The type of worker.
            count: The number of idle workers.
        """
        self.metrics_manager.set_gauge(
            name=f"{self.namespace}.{JobMetricType.WORKER_IDLE}",
            value=count,
            labels={"worker_type": worker_type},
        )
    
    def record_execution_time(self, queue: str, task: str, seconds: float) -> None:
        """Record a job execution time metric.
        
        Args:
            queue: The queue name.
            task: The task name.
            seconds: The execution time in seconds.
        """
        self.metrics_manager.observe_histogram(
            name=f"{self.namespace}.{JobMetricType.EXECUTION_TIME}",
            value=seconds,
            labels={"queue": queue, "task": task},
        )
    
    def record_wait_time(self, queue: str, task: str, priority: str, seconds: float) -> None:
        """Record a job wait time metric.
        
        Args:
            queue: The queue name.
            task: The task name.
            priority: The priority level.
            seconds: The wait time in seconds.
        """
        self.metrics_manager.observe_histogram(
            name=f"{self.namespace}.{JobMetricType.WAIT_TIME}",
            value=seconds,
            labels={"queue": queue, "task": task, "priority": priority},
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics.
        
        Returns:
            A dictionary of all metrics.
        """
        return self.metrics_manager.get_metrics()


class JobMetricsCollector:
    """Collects metrics from the job system periodically."""
    
    def __init__(
        self,
        job_manager,
        metrics: JobMetrics,
        collection_interval: timedelta = timedelta(seconds=15),
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the job metrics collector.
        
        Args:
            job_manager: The job manager to collect metrics from.
            metrics: The job metrics instance.
            collection_interval: How often to collect metrics.
            logger: Optional logger.
        """
        self.job_manager = job_manager
        self.metrics = metrics
        self.collection_interval = collection_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the metrics collector."""
        if self.running:
            return
        
        self.running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._collection_loop())
        self.logger.info("Job metrics collector started")
    
    async def stop(self) -> None:
        """Stop the metrics collector."""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
        if self._task and not self._task.done():
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._task = None
        self.logger.info("Job metrics collector stopped")
    
    async def _collection_loop(self) -> None:
        """Background task to collect metrics periodically."""
        while self.running:
            try:
                # Wait for the collection interval or stop event
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.collection_interval.total_seconds())
                    return  # Stop event was set
                except asyncio.TimeoutError:
                    pass  # Continue with collection
                
                # Collect queue metrics
                await self._collect_queue_metrics()
                
                # Collect worker metrics
                await self._collect_worker_metrics()
            except Exception as e:
                self.logger.exception(f"Error in metrics collection loop: {str(e)}")
    
    async def _collect_queue_metrics(self) -> None:
        """Collect queue metrics."""
        try:
            # Get all queue names
            queue_names_result = await self.job_manager.get_queue_names()
            if not queue_names_result.is_success:
                self.logger.error(f"Failed to get queue names: {queue_names_result.error}")
                return
                
            queue_names = queue_names_result.value
            
            # For each queue, get the length for different statuses
            for queue_name in queue_names:
                # Pending jobs
                pending_result = await self.job_manager.storage.get_queue_length(queue_name)
                if pending_result.is_success:
                    self.metrics.set_queue_length(queue_name, "pending", pending_result.value)
                
                # Running jobs
                running_result = await self.job_manager.storage.get_jobs_by_status(
                    [self.job_manager.storage.JobStatus.RUNNING], queue_name
                )
                if running_result.is_success:
                    self.metrics.set_queue_length(queue_name, "running", len(running_result.value))
                
                # Failed jobs
                failed_result = await self.job_manager.storage.get_jobs_by_status(
                    [self.job_manager.storage.JobStatus.FAILED], queue_name
                )
                if failed_result.is_success:
                    self.metrics.set_queue_length(queue_name, "failed", len(failed_result.value))
                
                # Completed jobs
                completed_result = await self.job_manager.storage.get_jobs_by_status(
                    [self.job_manager.storage.JobStatus.COMPLETED], queue_name
                )
                if completed_result.is_success:
                    self.metrics.set_queue_length(queue_name, "completed", len(completed_result.value))
        except Exception as e:
            self.logger.exception(f"Error collecting queue metrics: {str(e)}")
    
    async def _collect_worker_metrics(self) -> None:
        """Collect worker metrics."""
        try:
            # Group workers by type
            worker_types = {}
            
            for worker in self.job_manager.workers:
                worker_type = worker.__class__.__name__
                if worker_type not in worker_types:
                    worker_types[worker_type] = {"busy": 0, "idle": 0}
                
                if worker.is_busy():
                    worker_types[worker_type]["busy"] += 1
                else:
                    worker_types[worker_type]["idle"] += 1
            
            # Set metrics for each worker type
            for worker_type, counts in worker_types.items():
                self.metrics.set_worker_busy(worker_type, counts["busy"])
                self.metrics.set_worker_idle(worker_type, counts["idle"])
        except Exception as e:
            self.logger.exception(f"Error collecting worker metrics: {str(e)}")


class JobMonitor:
    """Monitors job execution and records metrics."""
    
    def __init__(self, metrics: JobMetrics):
        """Initialize the job monitor.
        
        Args:
            metrics: The job metrics instance.
        """
        self.metrics = metrics
        self._job_start_times = {}
        self._job_created_times = {}
    
    def record_job_enqueued(self, job) -> None:
        """Record a job being enqueued.
        
        Args:
            job: The job being enqueued.
        """
        self.metrics.record_job_enqueued(
            queue=job.queue_name,
            task=job.task_name,
            priority=job.priority.name,
        )
        self._job_created_times[job.id] = job.created_at
    
    def record_job_started(self, job, worker_name: str) -> None:
        """Record a job being started.
        
        Args:
            job: The job being started.
            worker_name: The name of the worker.
        """
        self.metrics.record_job_started(
            queue=job.queue_name,
            task=job.task_name,
            worker=worker_name,
        )
        
        # Record wait time
        if job.id in self._job_created_times and job.started_at:
            created_at = self._job_created_times[job.id]
            wait_time = (job.started_at - created_at).total_seconds()
            
            self.metrics.record_wait_time(
                queue=job.queue_name,
                task=job.task_name,
                priority=job.priority.name,
                seconds=wait_time,
            )
        
        # Store start time for execution time calculation
        self._job_start_times[job.id] = time.time()
    
    def record_job_completed(self, job, worker_name: str) -> None:
        """Record a job being completed.
        
        Args:
            job: The completed job.
            worker_name: The name of the worker.
        """
        self.metrics.record_job_completed(
            queue=job.queue_name,
            task=job.task_name,
            worker=worker_name,
        )
        
        # Record execution time
        if job.id in self._job_start_times:
            start_time = self._job_start_times.pop(job.id)
            execution_time = time.time() - start_time
            
            self.metrics.record_execution_time(
                queue=job.queue_name,
                task=job.task_name,
                seconds=execution_time,
            )
        
        # Clean up
        if job.id in self._job_created_times:
            del self._job_created_times[job.id]
    
    def record_job_failed(self, job, worker_name: str, error_type: str) -> None:
        """Record a job failing.
        
        Args:
            job: The failed job.
            worker_name: The name of the worker.
            error_type: The type of error.
        """
        self.metrics.record_job_failed(
            queue=job.queue_name,
            task=job.task_name,
            worker=worker_name,
            error_type=error_type,
        )
        
        # Record execution time
        if job.id in self._job_start_times:
            start_time = self._job_start_times.pop(job.id)
            execution_time = time.time() - start_time
            
            self.metrics.record_execution_time(
                queue=job.queue_name,
                task=job.task_name,
                seconds=execution_time,
            )
        
        # Clean up
        if job.id in self._job_created_times:
            del self._job_created_times[job.id]
    
    def record_job_retry(self, job) -> None:
        """Record a job being retried.
        
        Args:
            job: The job being retried.
        """
        self.metrics.record_job_retry(
            queue=job.queue_name,
            task=job.task_name,
        )
    
    def record_job_cancelled(self, job) -> None:
        """Record a job being cancelled.
        
        Args:
            job: The job being cancelled.
        """
        self.metrics.record_job_cancelled(
            queue=job.queue_name,
            task=job.task_name,
        )
        
        # Clean up
        if job.id in self._job_start_times:
            del self._job_start_times[job.id]
        if job.id in self._job_created_times:
            del self._job_created_times[job.id]