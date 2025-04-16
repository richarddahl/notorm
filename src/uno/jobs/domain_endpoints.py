# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from uno.jobs.dtos import (
    JobViewDto, JobListDto, CreateJobDto, JobFilterParams, CancelJobDto, JobStatsDto,
    ScheduleViewDto, ScheduleListDto, CreateScheduleDto, UpdateScheduleDto, ScheduleFilterParams,
    TaskInfoDto, TaskListDto, QueueInfoDto, QueueListDto, RunSyncJobDto,
)
from uno.jobs.domain_services import JobManagerServiceProtocol, TaskRegistryProtocol
from uno.jobs.schemas import (
    JobSchemaManager, ScheduleSchemaManager, TaskSchemaManager, QueueSchemaManager
)
from uno.jobs.entities import JobStatus
from uno.dependencies.service import inject_dependency


def register_job_endpoints(
    router: APIRouter,
    prefix: str = "/jobs",
    tags: List[str] = None,
    dependencies: List[Any] = None,
) -> Dict[str, Any]:
    """Register job API endpoints."""
    if tags is None:
        tags = ["jobs"]
    
    if dependencies is None:
        dependencies = []
    
    # Schema managers
    job_schema_manager = JobSchemaManager()
    
    # Dependency for job manager service
    def get_job_manager() -> JobManagerServiceProtocol:
        """Get job manager service."""
        return inject_dependency(JobManagerServiceProtocol)
    
    # GET /jobs
    @router.get(
        f"{prefix}",
        response_model=JobListDto,
        tags=tags,
        dependencies=dependencies,
        summary="List jobs",
        description="List jobs with filtering and pagination"
    )
    async def list_jobs(
        queue_name: Optional[str] = Query(None, description="Filter by queue name"),
        status: Optional[List[str]] = Query(None, description="Filter by job status"),
        priority: Optional[str] = Query(None, description="Filter by priority level"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        worker_id: Optional[str] = Query(None, description="Filter by worker ID"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
        offset: int = Query(0, ge=0, description="Number of jobs to skip"),
        order_by: str = Query("created_at", description="Field to order by"),
        order_dir: str = Query("desc", description="Order direction (asc/desc)"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> JobListDto:
        """List jobs with filtering and pagination."""
        try:
            # Create filter params
            filter_params = JobFilterParams(
                queue_name=queue_name,
                status=status,
                priority=priority,
                tags=tags,
                worker_id=worker_id,
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_dir=order_dir,
            )
            
            # Convert to query params
            query_params = job_schema_manager.filter_params_to_query_params(filter_params)
            
            # Get jobs
            result = await job_manager.get_job_repository().list_jobs(**query_params)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to list jobs: {result.error}"
                )
            
            jobs = result.value
            
            # Get total count
            count_params = query_params.copy()
            count_params.pop("limit", None)
            count_params.pop("offset", None)
            count_params.pop("order_by", None)
            count_params.pop("order_dir", None)
            
            count_result = await job_manager.get_job_repository().count_jobs(**count_params)
            if not count_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to count jobs: {count_result.error}"
                )
            
            # Convert to DTO
            return job_schema_manager.entities_to_list_dto(
                entities=jobs,
                total=count_result.value,
                page=(offset // limit) + 1,
                page_size=limit,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list jobs: {str(e)}"
            )
    
    # GET /jobs/{job_id}
    @router.get(
        f"{prefix}/{{job_id}}",
        response_model=JobViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get job",
        description="Get a job by ID"
    )
    async def get_job(
        job_id: str = Path(..., description="Job ID"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> JobViewDto:
        """Get a job by ID."""
        try:
            result = await job_manager.get_job(job_id)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get job: {result.error}"
                )
            
            job = result.value
            if job is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            
            return job_schema_manager.entity_to_dto(job)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get job: {str(e)}"
            )
    
    # POST /jobs
    @router.post(
        f"{prefix}",
        response_model=JobViewDto,
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        dependencies=dependencies,
        summary="Create job",
        description="Create a new job"
    )
    async def create_job(
        job_data: CreateJobDto,
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> JobViewDto:
        """Create a new job."""
        try:
            # Convert to service params
            params = job_schema_manager.create_dto_to_params(job_data)
            
            # Create job
            result = await job_manager.enqueue(**params)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create job: {result.error}"
                )
            
            job_id = result.value
            
            # Get the created job
            job_result = await job_manager.get_job(job_id)
            if not job_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get created job: {job_result.error}"
                )
            
            job = job_result.value
            if job is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Created job {job_id} not found"
                )
            
            return job_schema_manager.entity_to_dto(job)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create job: {str(e)}"
            )
    
    # POST /jobs/{job_id}/cancel
    @router.post(
        f"{prefix}/{{job_id}}/cancel",
        response_model=JobViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Cancel job",
        description="Cancel a job"
    )
    async def cancel_job(
        job_id: str = Path(..., description="Job ID"),
        cancel_data: CancelJobDto = None,
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> JobViewDto:
        """Cancel a job."""
        try:
            reason = None
            if cancel_data is not None:
                reason = cancel_data.reason
            
            result = await job_manager.cancel_job(job_id, reason)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to cancel job: {result.error}"
                )
            
            # Get the updated job
            job_result = await job_manager.get_job(job_id)
            if not job_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get cancelled job: {job_result.error}"
                )
            
            job = job_result.value
            if job is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Cancelled job {job_id} not found"
                )
            
            return job_schema_manager.entity_to_dto(job)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel job: {str(e)}"
            )
    
    # POST /jobs/{job_id}/retry
    @router.post(
        f"{prefix}/{{job_id}}/retry",
        response_model=JobViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Retry job",
        description="Retry a failed job"
    )
    async def retry_job(
        job_id: str = Path(..., description="Job ID"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> JobViewDto:
        """Retry a failed job."""
        try:
            result = await job_manager.retry_job(job_id)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to retry job: {result.error}"
                )
            
            # Get the updated job
            job_result = await job_manager.get_job(job_id)
            if not job_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get retried job: {job_result.error}"
                )
            
            job = job_result.value
            if job is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Retried job {job_id} not found"
                )
            
            return job_schema_manager.entity_to_dto(job)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retry job: {str(e)}"
            )
    
    # POST /jobs/run-sync
    @router.post(
        f"{prefix}/run-sync",
        tags=tags,
        dependencies=dependencies,
        summary="Run job synchronously",
        description="Run a job synchronously and wait for the result"
    )
    async def run_job_sync(
        job_data: RunSyncJobDto,
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> Any:
        """Run a job synchronously and wait for the result."""
        try:
            # Convert to service params
            params = job_schema_manager.run_sync_dto_to_params(job_data)
            
            # Run job
            result = await job_manager.run_job_sync(**params)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to run job: {result.error}"
                )
            
            return result.value
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to run job: {str(e)}"
            )
    
    # GET /jobs/stats
    @router.get(
        f"{prefix}/stats",
        response_model=JobStatsDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get job statistics",
        description="Get statistics about jobs"
    )
    async def get_job_stats(
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> JobStatsDto:
        """Get statistics about jobs."""
        try:
            result = await job_manager.get_job_repository().get_statistics()
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get job statistics: {result.error}"
                )
            
            stats = result.value
            return job_schema_manager.stats_to_dto(stats)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get job statistics: {str(e)}"
            )
    
    # Return the endpoints
    endpoints = {
        "list_jobs": list_jobs,
        "get_job": get_job,
        "create_job": create_job,
        "cancel_job": cancel_job,
        "retry_job": retry_job,
        "run_job_sync": run_job_sync,
        "get_job_stats": get_job_stats,
    }
    
    return endpoints


def register_schedule_endpoints(
    router: APIRouter,
    prefix: str = "/schedules",
    tags: List[str] = None,
    dependencies: List[Any] = None,
) -> Dict[str, Any]:
    """Register schedule API endpoints."""
    if tags is None:
        tags = ["schedules"]
    
    if dependencies is None:
        dependencies = []
    
    # Schema managers
    schedule_schema_manager = ScheduleSchemaManager()
    
    # Dependency for job manager service
    def get_job_manager() -> JobManagerServiceProtocol:
        """Get job manager service."""
        return inject_dependency(JobManagerServiceProtocol)
    
    # GET /schedules
    @router.get(
        f"{prefix}",
        response_model=ScheduleListDto,
        tags=tags,
        dependencies=dependencies,
        summary="List schedules",
        description="List schedules with filtering and pagination"
    )
    async def list_schedules(
        status: Optional[str] = Query(None, description="Filter by status (active/paused)"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of schedules to return"),
        offset: int = Query(0, ge=0, description="Number of schedules to skip"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> ScheduleListDto:
        """List schedules with filtering and pagination."""
        try:
            # Create filter params
            filter_params = ScheduleFilterParams(
                status=status,
                tags=tags,
                limit=limit,
                offset=offset,
            )
            
            # Convert to query params
            query_params = schedule_schema_manager.filter_params_to_query_params(filter_params)
            
            # Get schedules
            result = await job_manager.list_schedules(**query_params)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to list schedules: {result.error}"
                )
            
            schedules = result.value
            
            # For simplicity, use the actual count as the total
            total = len(schedules)
            
            # Convert to DTO
            return schedule_schema_manager.entities_to_list_dto(
                entities=schedules,
                total=total,
                page=(offset // limit) + 1,
                page_size=limit,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list schedules: {str(e)}"
            )
    
    # GET /schedules/{schedule_id}
    @router.get(
        f"{prefix}/{{schedule_id}}",
        response_model=ScheduleViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get schedule",
        description="Get a schedule by ID"
    )
    async def get_schedule(
        schedule_id: str = Path(..., description="Schedule ID"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> ScheduleViewDto:
        """Get a schedule by ID."""
        try:
            result = await job_manager.get_schedule(schedule_id)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get schedule: {result.error}"
                )
            
            schedule = result.value
            if schedule is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schedule {schedule_id} not found"
                )
            
            return schedule_schema_manager.entity_to_dto(schedule)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get schedule: {str(e)}"
            )
    
    # POST /schedules
    @router.post(
        f"{prefix}",
        response_model=ScheduleViewDto,
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        dependencies=dependencies,
        summary="Create schedule",
        description="Create a new schedule"
    )
    async def create_schedule(
        schedule_data: CreateScheduleDto,
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> ScheduleViewDto:
        """Create a new schedule."""
        try:
            # Convert to service params
            params = schedule_schema_manager.create_dto_to_params(schedule_data)
            
            # Create schedule
            result = await job_manager.schedule_job(**params)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create schedule: {result.error}"
                )
            
            schedule_id = result.value
            
            # Get the created schedule
            schedule_result = await job_manager.get_schedule(schedule_id)
            if not schedule_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get created schedule: {schedule_result.error}"
                )
            
            schedule = schedule_result.value
            if schedule is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Created schedule {schedule_id} not found"
                )
            
            return schedule_schema_manager.entity_to_dto(schedule)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create schedule: {str(e)}"
            )
    
    # PUT /schedules/{schedule_id}
    @router.put(
        f"{prefix}/{{schedule_id}}",
        response_model=ScheduleViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Update schedule",
        description="Update an existing schedule"
    )
    async def update_schedule(
        schedule_id: str = Path(..., description="Schedule ID"),
        schedule_data: UpdateScheduleDto = None,
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> ScheduleViewDto:
        """Update an existing schedule."""
        try:
            if schedule_data is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Schedule data is required"
                )
            
            # Convert to service params
            params = schedule_schema_manager.update_dto_to_params(schedule_data)
            
            # Update schedule
            result = await job_manager.update_schedule(schedule_id, **params)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to update schedule: {result.error}"
                )
            
            # Get the updated schedule
            schedule_result = await job_manager.get_schedule(schedule_id)
            if not schedule_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get updated schedule: {schedule_result.error}"
                )
            
            schedule = schedule_result.value
            if schedule is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Updated schedule {schedule_id} not found"
                )
            
            return schedule_schema_manager.entity_to_dto(schedule)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update schedule: {str(e)}"
            )
    
    # DELETE /schedules/{schedule_id}
    @router.delete(
        f"{prefix}/{{schedule_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        dependencies=dependencies,
        summary="Delete schedule",
        description="Delete a schedule"
    )
    async def delete_schedule(
        schedule_id: str = Path(..., description="Schedule ID"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> None:
        """Delete a schedule."""
        try:
            result = await job_manager.delete_schedule(schedule_id)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to delete schedule: {result.error}"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete schedule: {str(e)}"
            )
    
    # POST /schedules/{schedule_id}/pause
    @router.post(
        f"{prefix}/{{schedule_id}}/pause",
        response_model=ScheduleViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Pause schedule",
        description="Pause a schedule"
    )
    async def pause_schedule(
        schedule_id: str = Path(..., description="Schedule ID"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> ScheduleViewDto:
        """Pause a schedule."""
        try:
            result = await job_manager.pause_schedule(schedule_id)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to pause schedule: {result.error}"
                )
            
            # Get the updated schedule
            schedule_result = await job_manager.get_schedule(schedule_id)
            if not schedule_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get paused schedule: {schedule_result.error}"
                )
            
            schedule = schedule_result.value
            if schedule is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Paused schedule {schedule_id} not found"
                )
            
            return schedule_schema_manager.entity_to_dto(schedule)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to pause schedule: {str(e)}"
            )
    
    # POST /schedules/{schedule_id}/resume
    @router.post(
        f"{prefix}/{{schedule_id}}/resume",
        response_model=ScheduleViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Resume schedule",
        description="Resume a paused schedule"
    )
    async def resume_schedule(
        schedule_id: str = Path(..., description="Schedule ID"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> ScheduleViewDto:
        """Resume a paused schedule."""
        try:
            result = await job_manager.resume_schedule(schedule_id)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to resume schedule: {result.error}"
                )
            
            # Get the updated schedule
            schedule_result = await job_manager.get_schedule(schedule_id)
            if not schedule_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get resumed schedule: {schedule_result.error}"
                )
            
            schedule = schedule_result.value
            if schedule is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resumed schedule {schedule_id} not found"
                )
            
            return schedule_schema_manager.entity_to_dto(schedule)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resume schedule: {str(e)}"
            )
    
    # Return the endpoints
    endpoints = {
        "list_schedules": list_schedules,
        "get_schedule": get_schedule,
        "create_schedule": create_schedule,
        "update_schedule": update_schedule,
        "delete_schedule": delete_schedule,
        "pause_schedule": pause_schedule,
        "resume_schedule": resume_schedule,
    }
    
    return endpoints


def register_queue_endpoints(
    router: APIRouter,
    prefix: str = "/queues",
    tags: List[str] = None,
    dependencies: List[Any] = None,
) -> Dict[str, Any]:
    """Register queue API endpoints."""
    if tags is None:
        tags = ["queues"]
    
    if dependencies is None:
        dependencies = []
    
    # Schema managers
    queue_schema_manager = QueueSchemaManager()
    
    # Dependency for job manager service
    def get_job_manager() -> JobManagerServiceProtocol:
        """Get job manager service."""
        return inject_dependency(JobManagerServiceProtocol)
    
    # GET /queues
    @router.get(
        f"{prefix}",
        response_model=QueueListDto,
        tags=tags,
        dependencies=dependencies,
        summary="List queues",
        description="List all queues"
    )
    async def list_queues(
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> QueueListDto:
        """List all queues."""
        try:
            # Get all queue names
            queue_names_result = await job_manager.get_queue_names()
            if not queue_names_result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get queue names: {queue_names_result.error}"
                )
            
            queue_names = list(queue_names_result.value)
            
            # Get queue information
            queue_info = []
            for queue_name in queue_names:
                # Get queue length
                length_result = await job_manager.get_queue_length(queue_name)
                if not length_result.is_success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to get queue length: {length_result.error}"
                    )
                
                # Check if queue is paused
                paused_result = await job_manager.get_job_repository().is_queue_paused(queue_name)
                if not paused_result.is_success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to check if queue is paused: {paused_result.error}"
                    )
                
                queue_info.append((queue_name, length_result.value, paused_result.value))
            
            return queue_schema_manager.queues_to_list_dto(queue_info)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list queues: {str(e)}"
            )
    
    # POST /queues/{queue_name}/pause
    @router.post(
        f"{prefix}/{{queue_name}}/pause",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        dependencies=dependencies,
        summary="Pause queue",
        description="Pause a queue"
    )
    async def pause_queue(
        queue_name: str = Path(..., description="Queue name"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> None:
        """Pause a queue."""
        try:
            result = await job_manager.pause_queue(queue_name)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to pause queue: {result.error}"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to pause queue: {str(e)}"
            )
    
    # POST /queues/{queue_name}/resume
    @router.post(
        f"{prefix}/{{queue_name}}/resume",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        dependencies=dependencies,
        summary="Resume queue",
        description="Resume a paused queue"
    )
    async def resume_queue(
        queue_name: str = Path(..., description="Queue name"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> None:
        """Resume a paused queue."""
        try:
            result = await job_manager.resume_queue(queue_name)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to resume queue: {result.error}"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resume queue: {str(e)}"
            )
    
    # POST /queues/{queue_name}/clear
    @router.post(
        f"{prefix}/{{queue_name}}/clear",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        dependencies=dependencies,
        summary="Clear queue",
        description="Clear all jobs from a queue"
    )
    async def clear_queue(
        queue_name: str = Path(..., description="Queue name"),
        job_manager: JobManagerServiceProtocol = Depends(get_job_manager)
    ) -> None:
        """Clear all jobs from a queue."""
        try:
            result = await job_manager.clear_queue(queue_name)
            if not result.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to clear queue: {result.error}"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear queue: {str(e)}"
            )
    
    # Return the endpoints
    endpoints = {
        "list_queues": list_queues,
        "pause_queue": pause_queue,
        "resume_queue": resume_queue,
        "clear_queue": clear_queue,
    }
    
    return endpoints


def register_task_endpoints(
    router: APIRouter,
    prefix: str = "/tasks",
    tags: List[str] = None,
    dependencies: List[Any] = None,
) -> Dict[str, Any]:
    """Register task API endpoints."""
    if tags is None:
        tags = ["tasks"]
    
    if dependencies is None:
        dependencies = []
    
    # Schema managers
    task_schema_manager = TaskSchemaManager()
    
    # Dependency for task registry
    def get_task_registry() -> TaskRegistryProtocol:
        """Get task registry."""
        return inject_dependency(TaskRegistryProtocol)
    
    # GET /tasks
    @router.get(
        f"{prefix}",
        response_model=TaskListDto,
        tags=tags,
        dependencies=dependencies,
        summary="List tasks",
        description="List all registered tasks"
    )
    async def list_tasks(
        task_registry: TaskRegistryProtocol = Depends(get_task_registry)
    ) -> TaskListDto:
        """List all registered tasks."""
        try:
            tasks = task_registry.list_tasks()
            return task_schema_manager.tasks_to_list_dto(tasks)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list tasks: {str(e)}"
            )
    
    # GET /tasks/{task_name}
    @router.get(
        f"{prefix}/{{task_name}}",
        response_model=TaskInfoDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get task",
        description="Get a task by name"
    )
    async def get_task(
        task_name: str = Path(..., description="Task name"),
        version: Optional[str] = Query(None, description="Task version"),
        task_registry: TaskRegistryProtocol = Depends(get_task_registry)
    ) -> TaskInfoDto:
        """Get a task by name."""
        try:
            task = task_registry.get_task(task_name, version)
            if task is None:
                # Try to import the task
                task = task_registry.import_task(task_name)
                if task is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Task {task_name} not found"
                    )
            
            return task_schema_manager.task_to_dto(task)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get task: {str(e)}"
            )
    
    # Return the endpoints
    endpoints = {
        "list_tasks": list_tasks,
        "get_task": get_task,
    }
    
    return endpoints


def register_all_job_endpoints(
    router: APIRouter,
    dependencies: List[Any] = None,
) -> Dict[str, Dict[str, Any]]:
    """Register all job-related API endpoints."""
    if dependencies is None:
        dependencies = []
    
    # Register endpoints
    job_endpoints = register_job_endpoints(router, dependencies=dependencies)
    schedule_endpoints = register_schedule_endpoints(router, dependencies=dependencies)
    queue_endpoints = register_queue_endpoints(router, dependencies=dependencies)
    task_endpoints = register_task_endpoints(router, dependencies=dependencies)
    
    # Return all endpoints
    return {
        "jobs": job_endpoints,
        "schedules": schedule_endpoints,
        "queues": queue_endpoints,
        "tasks": task_endpoints,
    }