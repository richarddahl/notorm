"""Asynchronous worker implementation for the background processing system.

This module provides an asynchronous worker implementation that processes
jobs concurrently using asyncio tasks.
"""

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List, Optional, Set, Tuple, cast
import asyncio
import logging
import statistics
import time

from uno.jobs.queue import Job, JobQueue, JobStatus, Priority
from uno.jobs.storage.base import Storage
from uno.jobs.worker.base import Worker, WorkerTaskError
from uno.jobs.worker.middleware import Middleware


class AsyncWorker(Worker):
    """Asynchronous worker for processing jobs.

    This worker uses asyncio for concurrent job processing, making it
    efficient for I/O-bound tasks that can benefit from asynchronous
    execution.
    """

    def __init__(
        self,
        queue: JobQueue,
        max_concurrent: int = 10,
        batch_size: int = 10,
        **kwargs: Any,
    ):
        """Initialize an async worker.

        Args:
            queue: Job queue to process
            max_concurrent: Maximum number of concurrent jobs
            batch_size: Maximum number of jobs to fetch at once
            **kwargs: Additional arguments passed to Worker.__init__
        """
        super().__init__(**kwargs)
        self.queue = queue
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size

        # Concurrency management
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks: Set[asyncio.Task] = set()

        # Tasks
        self.main_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.metrics_task: Optional[asyncio.Task] = None
        self.healthcheck_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the async worker.

        This method initializes the worker and begins processing jobs.
        """
        if self.running:
            self.logger.warning("Worker is already running")
            return

        self.logger.info(
            f"Starting async worker {self.worker_id} for queue {self.queue_name}"
        )
        self.running = True
        self.start_time = datetime.now(datetime.UTC)

        # Start background tasks
        self.main_task = asyncio.create_task(self._process_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        if self.metrics_enabled:
            self.metrics_task = asyncio.create_task(self._metrics_loop())

        self.healthcheck_task = asyncio.create_task(self._healthcheck_loop())

        # Log startup
        self.logger.info(
            f"Async worker started with {self.max_concurrent} concurrent workers"
        )

    async def shutdown(self, wait: bool = True) -> None:
        """Shut down the async worker.

        Args:
            wait: Whether to wait for current jobs to complete
        """
        if not self.running:
            return

        self.logger.info(f"Shutting down async worker {self.worker_id}")

        # Set shutdown flag
        self.running = False
        self.shutdown_event.set()

        # Cancel background tasks
        for task in [
            self.main_task,
            self.heartbeat_task,
            self.metrics_task,
            self.healthcheck_task,
        ]:
            if task and not task.done():
                task.cancel()

        if wait and self.active_tasks:
            # Wait for active tasks to complete
            self.logger.info(
                f"Waiting for {len(self.active_tasks)} active tasks to complete"
            )
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_tasks, return_exceptions=True),
                    timeout=self.shutdown_timeout,
                )
                self.logger.info("All active tasks completed")
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Shutdown timed out after {self.shutdown_timeout} seconds. "
                    f"{len(self.active_tasks)} tasks still running."
                )
        else:
            # Cancel all active tasks
            for task in self.active_tasks:
                if not task.done():
                    task.cancel()

        self.logger.info("Async worker shutdown complete")

    async def pause(self) -> None:
        """Pause job processing.

        This method temporarily stops processing new jobs.
        """
        if not self.running:
            return

        self.logger.info(f"Pausing async worker {self.worker_id}")
        self.paused = True

    async def resume(self) -> None:
        """Resume job processing.

        This method resumes processing jobs after a pause.
        """
        if not self.running:
            return

        self.logger.info(f"Resuming async worker {self.worker_id}")
        self.paused = False

    async def process_job(self, job: Job) -> None:
        """Process a single job.

        Args:
            job: The job to process
        """
        # Check if job is already taken or not pending
        if job.status != JobStatus.RESERVED or job.worker_id != self.worker_id:
            self.logger.warning(f"Job {job.id} is not reserved for this worker")
            return

        queue_wait_time_ms = 0
        if job.created_at and job.started_at:
            queue_wait_time_ms = (
                job.started_at - job.created_at
            ).total_seconds() * 1000

        # Mark job as running
        job.mark_running()
        self._stats["active_jobs"] += 1

        start_time = time.time()
        success = False

        try:
            # Set up timeout if specified
            timeout = job.timeout

            if timeout is not None:
                # Use asyncio.wait_for for timeout
                result = await asyncio.wait_for(
                    self._execute_task(job), timeout=timeout
                )
            else:
                # No timeout
                result = await self._execute_task(job)

            # Job completed successfully
            await self.queue.complete(job.id, result)
            success = True
            self.failure_count = 0  # Reset failure counter on success

            self.logger.debug(f"Job {job.id} completed successfully")

        except asyncio.TimeoutError:
            # Job timed out
            self.logger.warning(f"Job {job.id} timed out after {timeout} seconds")
            job.mark_timeout()
            await self.queue.fail(
                job.id,
                {
                    "type": "TimeoutError",
                    "message": f"Job timed out after {timeout} seconds",
                },
            )
            self.failure_count += 1

        except WorkerTaskError as e:
            # Job failed with a task error
            self.logger.error(f"Job {job.id} failed: {e}")

            # Check if job should be retried
            retry = job.can_retry

            # Mark job as failed in the queue
            await self.queue.fail(
                job.id,
                {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": getattr(e, "__cause__", None)
                    and getattr(e.__cause__, "__traceback__", None)
                    and traceback.format_exception(
                        None, e.__cause__, e.__cause__.__traceback__
                    ),
                },
                retry=retry,
            )

            self.failure_count += 1

        except Exception as e:
            # Unexpected error
            self.logger.exception(f"Unexpected error processing job {job.id}: {e}")

            # Mark job as failed in the queue
            await self.queue.fail(
                job.id,
                {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                },
            )

            self.failure_count += 1

        finally:
            # Job is no longer active
            self._stats["active_jobs"] -= 1

            # Update statistics
            processing_time = time.time() - start_time
            processing_time_ms = processing_time * 1000
            self._update_stats(success, processing_time_ms, queue_wait_time_ms)

            # Log processing time
            self.logger.debug(
                f"Job {job.id} processed in {processing_time:.2f}s "
                f"(success={success})"
            )

            # Check if max failures reached
            if self.failure_count >= self.max_failures:
                self.logger.error(
                    f"Max consecutive failures reached ({self.max_failures}). "
                    f"Shutting down worker."
                )
                await self.shutdown(wait=False)

    async def process_batch(self, jobs: list[Job]) -> None:
        """Process a batch of jobs concurrently.

        Args:
            jobs: The jobs to process
        """
        if not jobs:
            return

        # Process jobs concurrently
        tasks = []
        for job in jobs:
            # Create a task for each job within the semaphore
            task = asyncio.create_task(self._process_job_with_semaphore(job))
            self.active_tasks.add(task)
            task.add_done_callback(self.active_tasks.discard)
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_job_with_semaphore(self, job: Job) -> None:
        """Process a job while respecting the concurrency limit.

        Args:
            job: The job to process
        """
        async with self.semaphore:
            await self.process_job(job)

    async def _process_loop(self) -> None:
        """Main processing loop.

        This method continuously polls the queue for jobs and processes them.
        """
        while self.running:
            if self.paused or self.shutdown_event.is_set():
                await asyncio.sleep(self.poll_interval)
                continue

            try:
                # Calculate how many jobs to fetch based on available capacity
                capacity = min(
                    self.max_concurrent - self._stats["active_jobs"], self.batch_size
                )
                if capacity <= 0:
                    # No capacity available, wait a bit
                    await asyncio.sleep(0.1)
                    continue

                # Dequeue jobs from the queue
                jobs = await self.queue.dequeue(
                    self.worker_id,
                    priority_levels=self.priority_levels,
                    batch_size=capacity,
                )

                if not jobs:
                    # No jobs available, wait before polling again
                    await asyncio.sleep(self.poll_interval)
                    continue

                # Process the jobs
                await self.process_batch(jobs)

            except Exception as e:
                self.logger.exception(f"Error in processing loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop.

        This method periodically sends a heartbeat to indicate the worker is alive.
        """
        while self.running and not self.shutdown_event.is_set():
            try:
                # TODO: Implement actual heartbeat mechanism
                # This could update a timestamp in a distributed storage
                # or send a message to a monitoring system
                self.logger.debug(f"Heartbeat from worker {self.worker_id}")

                # Sleep until next heartbeat
                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def _metrics_loop(self) -> None:
        """Metrics collection loop.

        This method periodically collects and logs performance metrics.
        """
        while self.running and not self.shutdown_event.is_set():
            try:
                # Get current metrics
                metrics = await self.get_metrics()

                self.logger.debug(f"Worker metrics: {metrics}")

                # Sleep until next metrics collection
                await asyncio.sleep(self.metrics_interval)

            except Exception as e:
                self.logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(self.metrics_interval)

    async def _healthcheck_loop(self) -> None:
        """Health check loop.

        This method periodically checks the health of the worker.
        """
        while self.running and not self.shutdown_event.is_set():
            try:
                # Check health
                health = await self.check_health()

                # Log health status
                if health["status"] == "healthy":
                    self.logger.debug(f"Worker health: {health['status']}")
                else:
                    self.logger.warning(f"Worker health: {health}")

                # Sleep until next health check
                await asyncio.sleep(self.healthcheck_interval)

            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.healthcheck_interval)

    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the worker.

        Returns:
            Dictionary with health check results
        """
        health = {
            "status": "healthy",
            "worker_id": self.worker_id,
            "queue": self.queue_name,
            "running": self.running,
            "paused": self.paused,
            "active_jobs": self._stats["active_jobs"],
            "failure_count": self.failure_count,
        }

        # Add uptime if available
        if self.start_time:
            health["uptime"] = (
                datetime.now(datetime.UTC) - self.start_time
            ).total_seconds()

        # Check if shutting down
        if self.shutdown_event.is_set():
            health["status"] = "shutting_down"

        # Check if paused
        if self.paused:
            health["status"] = "paused"

        # Check if failure threshold approaching
        if self.failure_count > self.max_failures * 0.8:
            health["status"] = "degraded"
            health["warnings"] = [
                f"High failure count: {self.failure_count}/{self.max_failures}"
            ]

        return health

    async def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the worker.

        Returns:
            Dictionary with metrics
        """
        metrics = {
            "worker_id": self.worker_id,
            "queue": self.queue_name,
            "jobs_processed_total": self._stats["jobs_processed_total"],
            "jobs_succeeded": self._stats["jobs_succeeded"],
            "jobs_failed": self._stats["jobs_failed"],
            "active_jobs": self._stats["active_jobs"],
        }

        # Calculate error rate
        if metrics["jobs_processed_total"] > 0:
            metrics["error_rate"] = (
                metrics["jobs_failed"] / metrics["jobs_processed_total"]
            )
        else:
            metrics["error_rate"] = 0.0

        # Calculate processing time statistics if available
        if self._stats["processing_time_ms"]:
            processing_times = self._stats["processing_time_ms"]
            metrics["processing_time_avg_ms"] = statistics.mean(processing_times)
            if (
                len(processing_times) >= 20
            ):  # Only calculate percentiles with enough data
                metrics["processing_time_p95_ms"] = statistics.quantiles(
                    processing_times, n=20
                )[
                    18
                ]  # 95th percentile
                metrics["processing_time_p99_ms"] = statistics.quantiles(
                    processing_times, n=100
                )[
                    98
                ]  # 99th percentile

        # Calculate queue wait time statistics if available
        if self._stats["queue_wait_time_ms"]:
            wait_times = self._stats["queue_wait_time_ms"]
            metrics["queue_wait_time_avg_ms"] = statistics.mean(wait_times)
            if len(wait_times) >= 20:  # Only calculate percentiles with enough data
                metrics["queue_wait_time_p95_ms"] = statistics.quantiles(
                    wait_times, n=20
                )[
                    18
                ]  # 95th percentile

        # Calculate throughput (jobs per minute)
        if self.start_time:
            uptime_seconds = (
                datetime.now(datetime.UTC) - self.start_time
            ).total_seconds()
            if uptime_seconds > 0:
                metrics["throughput_jobs_per_minute"] = (
                    metrics["jobs_processed_total"] / uptime_seconds * 60
                )

        # Add error statistics
        metrics["errors_by_type"] = self._stats["errors"]

        return metrics

    def is_running(self) -> bool:
        """Check if the worker is running.

        Returns:
            True if the worker is running, False otherwise
        """
        return self.running and not self.shutdown_event.is_set()

    def is_paused(self) -> bool:
        """Check if the worker is paused.

        Returns:
            True if the worker is paused, False otherwise
        """
        return self.paused


import traceback  # Added to support error handling
