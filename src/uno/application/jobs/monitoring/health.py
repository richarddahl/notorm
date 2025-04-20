from typing import Dict, List, Optional, Any, Callable
import asyncio
from datetime import datetime, timedelta, UTC
import logging

from uno.core.monitoring.health import HealthCheck, HealthStatus
from uno.jobs.queue.status import JobStatus


class JobQueueHealthCheck(HealthCheck):
    """Health check for job queues."""

    def __init__(
        self,
        job_manager,
        queue_name: str,
        max_queue_length: int = 1000,
        max_failed_jobs: int = 100,
        alert_on_stalled_jobs: bool = True,
        check_interval: timedelta = timedelta(minutes=1),
        logger: logging.Logger | None = None,
    ):
        """Initialize the job queue health check.

        Args:
            job_manager: The job manager to check.
            queue_name: The name of the queue to check.
            max_queue_length: Maximum acceptable queue length before degraded status.
            max_failed_jobs: Maximum acceptable failed jobs before degraded status.
            alert_on_stalled_jobs: Whether to alert on stalled jobs.
            check_interval: How often to run the health check.
            logger: Optional logger.
        """
        super().__init__(
            name=f"job_queue_{queue_name}",
            description=f"Health check for job queue {queue_name}",
            check_interval=check_interval,
        )
        self.job_manager = job_manager
        self.queue_name = queue_name
        self.max_queue_length = max_queue_length
        self.max_failed_jobs = max_failed_jobs
        self.alert_on_stalled_jobs = alert_on_stalled_jobs
        self.logger = logger or logging.getLogger(__name__)

    async def check_health(self) -> Dict[str, Any]:
        """Perform the health check.

        Returns:
            Dictionary with health status and details.
        """
        try:
            # Check queue length
            queue_length_result = await self.job_manager.get_queue_length(
                self.queue_name
            )
            if not queue_length_result.is_success:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Failed to get queue length: {queue_length_result.error}",
                    "queue_name": self.queue_name,
                }

            queue_length = queue_length_result.value

            # Check failed jobs
            failed_jobs_result = await self.job_manager.get_failed_jobs(
                self.queue_name, limit=0
            )
            if not failed_jobs_result.is_success:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Failed to get failed jobs: {failed_jobs_result.error}",
                    "queue_name": self.queue_name,
                }

            failed_jobs_count = len(failed_jobs_result.value)

            # Check for stalled jobs if enabled
            stalled_jobs_count = 0
            if self.alert_on_stalled_jobs:
                running_jobs_result = await self.job_manager.get_running_jobs(
                    self.queue_name
                )
                if running_jobs_result.is_success:
                    now = datetime.now(datetime.UTC)
                    stall_threshold = now - self.job_manager.stall_timeout

                    for job in running_jobs_result.value:
                        if job.updated_at and job.updated_at < stall_threshold:
                            stalled_jobs_count += 1

            # Determine health status
            status = HealthStatus.HEALTHY
            message = "Job queue is healthy"

            if queue_length > self.max_queue_length:
                status = HealthStatus.DEGRADED
                message = f"Queue length ({queue_length}) exceeds maximum ({self.max_queue_length})"

            if failed_jobs_count > self.max_failed_jobs:
                status = HealthStatus.DEGRADED
                message = f"Failed jobs count ({failed_jobs_count}) exceeds maximum ({self.max_failed_jobs})"

            if stalled_jobs_count > 0:
                status = HealthStatus.DEGRADED
                message = f"Found {stalled_jobs_count} stalled jobs"

            # Return health details
            return {
                "status": status,
                "message": message,
                "queue_name": self.queue_name,
                "queue_length": queue_length,
                "failed_jobs": failed_jobs_count,
                "stalled_jobs": stalled_jobs_count,
            }
        except Exception as e:
            self.logger.exception(f"Error checking job queue health: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Error checking health: {str(e)}",
                "queue_name": self.queue_name,
            }


class WorkerHealthCheck(HealthCheck):
    """Health check for job workers."""

    def __init__(
        self,
        worker,
        check_interval: timedelta = timedelta(seconds=30),
        logger: logging.Logger | None = None,
    ):
        """Initialize the worker health check.

        Args:
            worker: The worker to check.
            check_interval: How often to run the health check.
            logger: Optional logger.
        """
        super().__init__(
            name=f"worker_{worker.name}",
            description=f"Health check for worker {worker.name}",
            check_interval=check_interval,
        )
        self.worker = worker
        self.logger = logger or logging.getLogger(__name__)

    async def check_health(self) -> Dict[str, Any]:
        """Perform the health check.

        Returns:
            Dictionary with health status and details.
        """
        try:
            # Check if worker is running
            if not self.worker.running:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Worker is not running",
                    "worker_name": self.worker.name,
                }

            # Check if worker is processing jobs
            if not self.worker.is_healthy():
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Worker is not processing jobs properly",
                    "worker_name": self.worker.name,
                    "details": self.worker.get_health_details(),
                }

            # Worker is healthy
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Worker is healthy",
                "worker_name": self.worker.name,
                "details": self.worker.get_health_details(),
            }
        except Exception as e:
            self.logger.exception(f"Error checking worker health: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Error checking health: {str(e)}",
                "worker_name": self.worker.name,
            }


class SchedulerHealthCheck(HealthCheck):
    """Health check for job scheduler."""

    def __init__(
        self,
        scheduler,
        check_interval: timedelta = timedelta(minutes=1),
        logger: logging.Logger | None = None,
    ):
        """Initialize the scheduler health check.

        Args:
            scheduler: The scheduler to check.
            check_interval: How often to run the health check.
            logger: Optional logger.
        """
        super().__init__(
            name="scheduler",
            description="Health check for job scheduler",
            check_interval=check_interval,
        )
        self.scheduler = scheduler
        self.logger = logger or logging.getLogger(__name__)

    async def check_health(self) -> Dict[str, Any]:
        """Perform the health check.

        Returns:
            Dictionary with health status and details.
        """
        try:
            # Check if scheduler is running
            if not self.scheduler.running:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Scheduler is not running",
                }

            # Check if scheduler is healthy
            if not self.scheduler.is_healthy():
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Scheduler is not processing schedules properly",
                    "details": self.scheduler.get_health_details(),
                }

            # Scheduler is healthy
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Scheduler is healthy",
                "details": self.scheduler.get_health_details(),
            }
        except Exception as e:
            self.logger.exception(f"Error checking scheduler health: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Error checking health: {str(e)}",
            }


class JobSystemHealthChecker:
    """Manages health checks for the entire job system."""

    def __init__(
        self,
        job_manager,
        check_interval: timedelta = timedelta(minutes=1),
        logger: logging.Logger | None = None,
    ):
        """Initialize the job system health checker.

        Args:
            job_manager: The job manager to check.
            check_interval: Default check interval for health checks.
            logger: Optional logger.
        """
        self.job_manager = job_manager
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)

        self.health_checks: list[HealthCheck] = []
        self._setup_health_checks()

        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    def _setup_health_checks(self) -> None:
        """Set up health checks for the job system."""
        # Add health checks for all workers
        for worker in self.job_manager.workers:
            self.health_checks.append(
                WorkerHealthCheck(
                    worker=worker,
                    check_interval=self.check_interval,
                    logger=self.logger,
                )
            )

        # Add health check for scheduler if available
        if self.job_manager.scheduler:
            self.health_checks.append(
                SchedulerHealthCheck(
                    scheduler=self.job_manager.scheduler,
                    check_interval=self.check_interval,
                    logger=self.logger,
                )
            )

        # Add health checks for all queues
        queue_names_task = asyncio.create_task(self.job_manager.get_queue_names())
        queue_names_result = asyncio.get_event_loop().run_until_complete(
            queue_names_task
        )

        if queue_names_result.is_success:
            for queue_name in queue_names_result.value:
                self.health_checks.append(
                    JobQueueHealthCheck(
                        job_manager=self.job_manager,
                        queue_name=queue_name,
                        check_interval=self.check_interval,
                        logger=self.logger,
                    )
                )

    def add_health_check(self, health_check: HealthCheck) -> None:
        """Add a custom health check.

        Args:
            health_check: The health check to add.
        """
        self.health_checks.append(health_check)

    async def start(self) -> None:
        """Start the health checker."""
        if self.running:
            return

        self.running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._check_loop())
        self.logger.info("Job system health checker started")

    async def stop(self) -> None:
        """Stop the health checker."""
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
        self.logger.info("Job system health checker stopped")

    async def _check_loop(self) -> None:
        """Background task to run health checks periodically."""
        while self.running:
            try:
                # Wait for the minimum check interval or stop event
                min_interval = min(check.check_interval for check in self.health_checks)
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=min_interval.total_seconds()
                    )
                    return  # Stop event was set
                except asyncio.TimeoutError:
                    pass  # Continue with health checks

                # Run health checks that are due
                now = datetime.now(datetime.UTC)
                for check in self.health_checks:
                    if (
                        not hasattr(check, "last_check_time")
                        or now - check.last_check_time >= check.check_interval
                    ):
                        result = await check.check_health()
                        check.last_check_time = now

                        # Log degraded or unhealthy checks
                        if result["status"] != HealthStatus.HEALTHY:
                            self.logger.warning(
                                f"Health check {check.name} is {result['status']}: {result['message']}"
                            )
            except Exception as e:
                self.logger.exception(f"Error in health check loop: {str(e)}")

    async def get_system_health(self) -> Dict[str, Any]:
        """Get the overall health of the job system.

        Returns:
            Dictionary with health status and details.
        """
        results = {}
        overall_status = HealthStatus.HEALTHY

        for check in self.health_checks:
            try:
                check_result = await check.check_health()
                results[check.name] = check_result

                # Update overall status
                if check_result["status"] == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif (
                    check_result["status"] == HealthStatus.DEGRADED
                    and overall_status != HealthStatus.UNHEALTHY
                ):
                    overall_status = HealthStatus.DEGRADED
            except Exception as e:
                self.logger.exception(
                    f"Error running health check {check.name}: {str(e)}"
                )
                results[check.name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Error running health check: {str(e)}",
                }
                overall_status = HealthStatus.UNHEALTHY

        return {
            "status": overall_status,
            "message": f"Job system is {overall_status.value}",
            "checks": results,
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }
