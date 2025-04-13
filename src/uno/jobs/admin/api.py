from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel, Field

# Define dependency functions to replace the old fastapi imports
def get_job_manager():
    from uno.dependencies.modern_provider import get_service_provider
    provider = get_service_provider()
    from uno.jobs.manager import JobManager
    return provider.get_service(JobManager)

def get_job_metrics():
    from uno.dependencies.modern_provider import get_service_provider
    provider = get_service_provider()
    from uno.jobs.monitoring.metrics import JobMetrics
    return provider.get_service(JobMetrics)
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus
from uno.jobs.scheduler.schedules import ScheduleDefinition, Schedule
from uno.jobs.manager import JobManager
from uno.jobs.monitoring.metrics import JobMetrics


# ----- Pydantic Models ------

class JobStatusInfo(BaseModel):
    """Information about a job status."""
    status: str
    count: int


class QueueInfo(BaseModel):
    """Information about a job queue."""
    name: str
    length: int
    jobs_by_status: List[JobStatusInfo]


class JobInfo(BaseModel):
    """Information about a job."""
    id: str
    queue_name: str
    status: str
    task_name: str
    priority: str
    created_at: datetime
    updated_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int
    max_retries: int
    is_scheduled: bool
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[Set[str]] = None


class WorkerInfo(BaseModel):
    """Information about a worker."""
    name: str
    status: str
    queue_names: List[str]
    current_job_id: Optional[str] = None
    jobs_processed: int
    is_healthy: bool
    details: Dict[str, Any]


class ScheduleInfo(BaseModel):
    """Information about a schedule."""
    id: str
    name: str
    task_name: str
    queue_name: str
    schedule_type: str
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class SystemInfo(BaseModel):
    """Information about the job system."""
    worker_count: int
    queue_count: int
    schedule_count: int
    total_jobs: int
    health_status: str


class CreateJobRequest(BaseModel):
    """Request to create a new job."""
    task_name: str
    args: Optional[List[Any]] = Field(default_factory=list)
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    queue_name: str = "default"
    priority: str = "NORMAL"
    scheduled_at: Optional[datetime] = None
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[Set[str]] = Field(default_factory=set)


class CreateScheduleRequest(BaseModel):
    """Request to create a new schedule."""
    name: str
    task_name: str
    schedule_type: str
    schedule_params: Dict[str, Any]
    args: Optional[List[Any]] = Field(default_factory=list)
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    queue_name: str = "default"
    priority: str = "NORMAL"
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    enabled: bool = True


class MetricsResponse(BaseModel):
    """Response with metrics data."""
    metrics: Dict[str, Any]
    timestamp: datetime


class HealthCheckResponse(BaseModel):
    """Response with health check data."""
    status: str
    message: str
    checks: Dict[str, Any]
    timestamp: datetime


# ----- API Router ------

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={404: {"description": "Not found"}},
)


# ----- Helper Functions ------

def _job_to_info(job) -> JobInfo:
    """Convert a job object to a JobInfo model.
    
    Args:
        job: The job object.
        
    Returns:
        JobInfo object.
    """
    return JobInfo(
        id=job.id,
        queue_name=job.queue_name,
        status=job.status.name,
        task_name=job.task_name,
        priority=job.priority.name,
        created_at=job.created_at,
        updated_at=job.updated_at,
        scheduled_at=job.scheduled_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        retries=job.retries,
        max_retries=job.max_retries,
        is_scheduled=job.is_scheduled,
        result=job.result,
        error=job.error,
        metadata=job.metadata,
        tags=job.tags,
    )


def _worker_to_info(worker) -> WorkerInfo:
    """Convert a worker object to a WorkerInfo model.
    
    Args:
        worker: The worker object.
        
    Returns:
        WorkerInfo object.
    """
    return WorkerInfo(
        name=worker.name,
        status="running" if worker.running else "stopped",
        queue_names=worker.queue_names,
        current_job_id=worker.current_job.id if worker.current_job else None,
        jobs_processed=worker.jobs_processed,
        is_healthy=worker.is_healthy(),
        details=worker.get_health_details(),
    )


def _schedule_to_info(schedule) -> ScheduleInfo:
    """Convert a schedule object to a ScheduleInfo model.
    
    Args:
        schedule: The schedule object.
        
    Returns:
        ScheduleInfo object.
    """
    return ScheduleInfo(
        id=schedule.id,
        name=schedule.name,
        task_name=schedule.task_name,
        queue_name=schedule.queue_name,
        schedule_type=schedule.schedule.schedule_type,
        next_run_at=schedule.next_run_at,
        last_run_at=schedule.last_run_at,
        enabled=schedule.enabled,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


# ----- API Endpoints ------

@router.get("/info", response_model=SystemInfo)
async def get_system_info(
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get information about the job system."""
    # Get queue names
    queues_result = await job_manager.get_queue_names()
    if not queues_result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue names: {queues_result.error}",
        )
    
    queue_count = len(queues_result.value)
    
    # Get schedules
    schedule_count = 0
    if job_manager.scheduler:
        schedules_result = await job_manager.scheduler.get_all_schedules()
        if schedules_result.is_success:
            schedule_count = len(schedules_result.value)
    
    # Count total jobs
    total_jobs = 0
    for queue_name in queues_result.value:
        queue = await job_manager.get_queue(queue_name)
        
        # Get jobs by status
        for job_status in JobStatus:
            status_result = await job_manager.storage.get_jobs_by_status([job_status], queue_name, limit=0)
            if status_result.is_success:
                total_jobs += len(status_result.value)
    
    # Get health status
    health_status = "healthy"
    for worker in job_manager.workers:
        if not worker.is_healthy():
            health_status = "degraded"
            break
    
    if job_manager.scheduler and not job_manager.scheduler.is_healthy():
        health_status = "degraded"
    
    return SystemInfo(
        worker_count=len(job_manager.workers),
        queue_count=queue_count,
        schedule_count=schedule_count,
        total_jobs=total_jobs,
        health_status=health_status,
    )


@router.get("/queues", response_model=List[QueueInfo])
async def get_queues(
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get all job queues."""
    # Get queue names
    queues_result = await job_manager.get_queue_names()
    if not queues_result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue names: {queues_result.error}",
        )
    
    queue_names = queues_result.value
    queues = []
    
    for queue_name in queue_names:
        queue = await job_manager.get_queue(queue_name)
        
        # Get queue length
        length_result = await queue.get_length()
        if not length_result.is_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get queue length: {length_result.error}",
            )
        
        # Get jobs by status
        jobs_by_status = []
        for job_status in JobStatus:
            status_result = await job_manager.storage.get_jobs_by_status([job_status], queue_name, limit=0)
            if status_result.is_success:
                jobs_by_status.append(
                    JobStatusInfo(
                        status=job_status.name,
                        count=len(status_result.value),
                    )
                )
        
        queues.append(
            QueueInfo(
                name=queue_name,
                length=length_result.value,
                jobs_by_status=jobs_by_status,
            )
        )
    
    return queues


@router.get("/queues/{queue_name}", response_model=QueueInfo)
async def get_queue(
    queue_name: str = Path(..., description="Name of the queue"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get information about a specific queue."""
    queue = await job_manager.get_queue(queue_name)
    
    # Get queue length
    length_result = await queue.get_length()
    if not length_result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue length: {length_result.error}",
        )
    
    # Get jobs by status
    jobs_by_status = []
    for job_status in JobStatus:
        status_result = await job_manager.storage.get_jobs_by_status([job_status], queue_name, limit=0)
        if status_result.is_success:
            jobs_by_status.append(
                JobStatusInfo(
                    status=job_status.name,
                    count=len(status_result.value),
                )
            )
    
    return QueueInfo(
        name=queue_name,
        length=length_result.value,
        jobs_by_status=jobs_by_status,
    )


@router.post("/queues/{queue_name}/clear", response_model=Dict[str, Any])
async def clear_queue(
    queue_name: str = Path(..., description="Name of the queue"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Clear all pending jobs from a queue."""
    result = await job_manager.clear_queue(queue_name)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear queue: {result.error}",
        )
    
    return {
        "success": True,
        "jobs_cleared": result.value,
        "queue_name": queue_name,
    }


@router.post("/queues/{queue_name}/pause", response_model=Dict[str, Any])
async def pause_queue(
    queue_name: str = Path(..., description="Name of the queue"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Pause a queue."""
    result = await job_manager.pause_queue(queue_name)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause queue: {result.error}",
        )
    
    return {
        "success": True,
        "queue_name": queue_name,
        "status": "paused",
    }


@router.post("/queues/{queue_name}/resume", response_model=Dict[str, Any])
async def resume_queue(
    queue_name: str = Path(..., description="Name of the queue"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Resume a paused queue."""
    result = await job_manager.resume_queue(queue_name)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume queue: {result.error}",
        )
    
    return {
        "success": True,
        "queue_name": queue_name,
        "status": "resumed",
    }


@router.get("/jobs", response_model=List[JobInfo])
async def get_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    queue_name: Optional[str] = Query(None, description="Filter by queue name"),
    limit: int = Query(100, description="Maximum number of jobs to return"),
    offset: int = Query(0, description="Offset for pagination"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get jobs with optional filtering."""
    try:
        # Convert status string to enum if provided
        statuses = [JobStatus[status.upper()]] if status else list(JobStatus)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job status: {status}",
        )
    
    result = await job_manager.storage.get_jobs_by_status(statuses, queue_name, limit, offset)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get jobs: {result.error}",
        )
    
    return [_job_to_info(job) for job in result.value]


@router.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(
    job_id: str = Path(..., description="ID of the job"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get a specific job."""
    result = await job_manager.get_job(job_id)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {result.error}",
        )
    
    if result.value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    return _job_to_info(result.value)


@router.post("/jobs", response_model=Dict[str, Any])
async def create_job(
    job_data: CreateJobRequest,
    job_manager: JobManager = Depends(get_job_manager),
):
    """Create a new job."""
    try:
        # Convert priority string to enum
        priority = Priority[job_data.priority.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority: {job_data.priority}",
        )
    
    # Convert timeout and retry delay
    timeout = timedelta(seconds=job_data.timeout_seconds) if job_data.timeout_seconds else None
    retry_delay = timedelta(seconds=job_data.retry_delay_seconds)
    
    result = await job_manager.enqueue(
        task_name=job_data.task_name,
        args=job_data.args,
        kwargs=job_data.kwargs,
        queue_name=job_data.queue_name,
        priority=priority,
        scheduled_at=job_data.scheduled_at,
        max_retries=job_data.max_retries,
        retry_delay=retry_delay,
        timeout=timeout,
        metadata=job_data.metadata,
        tags=job_data.tags,
    )
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {result.error}",
        )
    
    return {
        "success": True,
        "job_id": result.value,
    }


@router.post("/jobs/{job_id}/cancel", response_model=Dict[str, Any])
async def cancel_job(
    job_id: str = Path(..., description="ID of the job"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Cancel a job."""
    result = await job_manager.cancel_job(job_id)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {result.error}",
        )
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "cancelled",
    }


@router.post("/jobs/{job_id}/retry", response_model=Dict[str, Any])
async def retry_job(
    job_id: str = Path(..., description="ID of the job"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Retry a failed job."""
    result = await job_manager.retry_job(job_id)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry job: {result.error}",
        )
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "pending",
    }


@router.get("/workers", response_model=List[WorkerInfo])
async def get_workers(
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get all workers."""
    return [_worker_to_info(worker) for worker in job_manager.workers]


@router.get("/workers/{worker_name}", response_model=WorkerInfo)
async def get_worker(
    worker_name: str = Path(..., description="Name of the worker"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get a specific worker."""
    for worker in job_manager.workers:
        if worker.name == worker_name:
            return _worker_to_info(worker)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Worker {worker_name} not found",
    )


@router.get("/schedules", response_model=List[ScheduleInfo])
async def get_schedules(
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get all schedules."""
    if not job_manager.scheduler:
        return []
    
    result = await job_manager.scheduler.get_all_schedules()
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedules: {result.error}",
        )
    
    return [_schedule_to_info(schedule) for schedule in result.value]


@router.get("/schedules/{schedule_id}", response_model=ScheduleInfo)
async def get_schedule(
    schedule_id: str = Path(..., description="ID of the schedule"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get a specific schedule."""
    if not job_manager.scheduler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduler not available",
        )
    
    result = await job_manager.scheduler.get_schedule(schedule_id)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedule: {result.error}",
        )
    
    if result.value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    
    return _schedule_to_info(result.value)


@router.post("/schedules", response_model=Dict[str, Any])
async def create_schedule(
    schedule_data: CreateScheduleRequest,
    job_manager: JobManager = Depends(get_job_manager),
):
    """Create a new schedule."""
    if not job_manager.scheduler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduler not available",
        )
    
    try:
        # Convert priority string to enum
        priority = Priority[schedule_data.priority.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority: {schedule_data.priority}",
        )
    
    # Create schedule
    try:
        schedule = Schedule.create(
            schedule_type=schedule_data.schedule_type,
            **schedule_data.schedule_params,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid schedule parameters: {str(e)}",
        )
    
    # Convert timeout and retry delay
    timeout = timedelta(seconds=schedule_data.timeout_seconds) if schedule_data.timeout_seconds else None
    retry_delay = timedelta(seconds=schedule_data.retry_delay_seconds)
    
    # Create schedule definition
    schedule_def = ScheduleDefinition(
        name=schedule_data.name,
        task_name=schedule_data.task_name,
        schedule=schedule,
        args=schedule_data.args,
        kwargs=schedule_data.kwargs,
        queue_name=schedule_data.queue_name,
        priority=priority,
        max_retries=schedule_data.max_retries,
        retry_delay=retry_delay,
        timeout=timeout,
        metadata=schedule_data.metadata,
        enabled=schedule_data.enabled,
    )
    
    result = await job_manager.scheduler.add_schedule(schedule_def)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {result.error}",
        )
    
    return {
        "success": True,
        "schedule_id": result.value,
    }


@router.post("/schedules/{schedule_id}/enable", response_model=Dict[str, Any])
async def enable_schedule(
    schedule_id: str = Path(..., description="ID of the schedule"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Enable a schedule."""
    if not job_manager.scheduler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduler not available",
        )
    
    result = await job_manager.scheduler.enable_schedule(schedule_id)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable schedule: {result.error}",
        )
    
    return {
        "success": True,
        "schedule_id": schedule_id,
        "status": "enabled",
    }


@router.post("/schedules/{schedule_id}/disable", response_model=Dict[str, Any])
async def disable_schedule(
    schedule_id: str = Path(..., description="ID of the schedule"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Disable a schedule."""
    if not job_manager.scheduler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduler not available",
        )
    
    result = await job_manager.scheduler.disable_schedule(schedule_id)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable schedule: {result.error}",
        )
    
    return {
        "success": True,
        "schedule_id": schedule_id,
        "status": "disabled",
    }


@router.delete("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def delete_schedule(
    schedule_id: str = Path(..., description="ID of the schedule"),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Delete a schedule."""
    if not job_manager.scheduler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduler not available",
        )
    
    result = await job_manager.scheduler.delete_schedule(schedule_id)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schedule: {result.error}",
        )
    
    return {
        "success": True,
        "schedule_id": schedule_id,
    }


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    metrics: JobMetrics = Depends(get_job_metrics),
):
    """Get job system metrics."""
    return MetricsResponse(
        metrics=metrics.get_metrics(),
        timestamp=datetime.utcnow(),
    )


@router.get("/health", response_model=HealthCheckResponse)
async def get_health(
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get job system health check."""
    # Check if health checker is available
    if not hasattr(job_manager, 'health_checker'):
        # Simple health check
        health_status = "healthy"
        health_checks = {}
        
        for worker in job_manager.workers:
            worker_name = worker.name
            is_healthy = worker.is_healthy()
            health_checks[f"worker_{worker_name}"] = {
                "status": "healthy" if is_healthy else "degraded",
                "message": f"Worker {worker_name} is {'healthy' if is_healthy else 'not processing jobs properly'}",
                "details": worker.get_health_details(),
            }
            
            if not is_healthy:
                health_status = "degraded"
        
        if job_manager.scheduler:
            is_healthy = job_manager.scheduler.is_healthy()
            health_checks["scheduler"] = {
                "status": "healthy" if is_healthy else "degraded",
                "message": f"Scheduler is {'healthy' if is_healthy else 'not processing schedules properly'}",
                "details": job_manager.scheduler.get_health_details(),
            }
            
            if not is_healthy:
                health_status = "degraded"
    else:
        # Use health checker
        health_result = await job_manager.health_checker.get_system_health()
        health_status = health_result["status"]
        health_checks = health_result["checks"]
    
    return HealthCheckResponse(
        status=health_status,
        message=f"Job system is {health_status}",
        checks=health_checks,
        timestamp=datetime.utcnow(),
    )