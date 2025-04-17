"""Background processing system for Uno.

This module provides a robust, scalable job processing system with support for:
- Job queues with priority levels
- Scheduled tasks
- Worker pools for job execution
- Multiple storage backends
- Task definition and discovery
"""

# Domain entities
from uno.jobs.entities import (
    Job,
    JobPriority,
    JobStatus,
    JobError,
    Schedule,
    ScheduleInterval
)

# Domain repositories
from uno.jobs.domain_repositories import (
    JobRepositoryProtocol,
    ScheduleRepositoryProtocol,
    JobRepository,
    ScheduleRepository
)

# Domain services
from uno.jobs.domain_services import (
    TaskRegistryProtocol,
    JobManagerServiceProtocol,
    TaskRegistryService,
    JobManagerService
)

# DTOs
from uno.jobs.dtos import (
    # Job DTOs
    JobViewDto,
    JobListDto,
    CreateJobDto,
    JobFilterParams,
    CancelJobDto,
    JobStatsDto,
    RunSyncJobDto,
    
    # Schedule DTOs
    ScheduleViewDto,
    ScheduleListDto,
    CreateScheduleDto,
    UpdateScheduleDto,
    ScheduleFilterParams,
    ScheduleIntervalDto,
    
    # Task DTOs
    TaskInfoDto,
    TaskListDto,
    
    # Queue DTOs
    QueueInfoDto,
    QueueListDto,
    
    # Enums
    PriorityEnum,
    StatusEnum
)

# Schema managers
from uno.jobs.schemas import (
    JobSchemaManager,
    ScheduleSchemaManager,
    TaskSchemaManager,
    QueueSchemaManager
)

# API integration
from uno.jobs.api_integration import register_jobs_endpoints
from uno.jobs.domain_endpoints import (
    register_job_endpoints,
    register_schedule_endpoints,
    register_queue_endpoints,
    register_task_endpoints,
    register_all_job_endpoints
)

# Domain provider
from uno.jobs.domain_provider import (
    configure_jobs_dependencies,
    get_jobs_di_config
)

# Legacy imports (for backward compatibility)
from uno.jobs.queue import (
    Queue,
    JobPriority as LegacyJobPriority,
    JobStatus as LegacyJobStatus,
    Job as LegacyJob
)

from uno.jobs.worker import (
    Worker,
    AsyncWorker,
    WorkerMiddleware
)

from uno.jobs.scheduler import (
    Scheduler,
    Schedule as LegacySchedule
)

from uno.jobs.tasks import (
    Task,
    TaskMiddleware,
    TaskWorkflow,
    TaskContext
)

from uno.jobs.storage import (
    StorageBackend,
    MemoryStorage,
    DatabaseStorage,
    RedisStorage
)

from uno.jobs.manager import JobManager as LegacyJobManager

__all__ = [
    # Domain entities
    "Job",
    "JobPriority",
    "JobStatus",
    "JobError",
    "Schedule",
    "ScheduleInterval",
    
    # Domain repositories
    "JobRepositoryProtocol",
    "ScheduleRepositoryProtocol",
    "JobRepository",
    "ScheduleRepository",
    
    # Domain services
    "TaskRegistryProtocol",
    "JobManagerServiceProtocol",
    "TaskRegistryService",
    "JobManagerService",
    
    # DTOs
    "JobViewDto",
    "JobListDto",
    "CreateJobDto",
    "JobFilterParams",
    "CancelJobDto",
    "JobStatsDto",
    "RunSyncJobDto",
    "ScheduleViewDto",
    "ScheduleListDto",
    "CreateScheduleDto",
    "UpdateScheduleDto",
    "ScheduleFilterParams",
    "ScheduleIntervalDto",
    "TaskInfoDto",
    "TaskListDto",
    "QueueInfoDto",
    "QueueListDto",
    "PriorityEnum",
    "StatusEnum",
    
    # Schema managers
    "JobSchemaManager",
    "ScheduleSchemaManager",
    "TaskSchemaManager",
    "QueueSchemaManager",
    
    # API integration
    "register_jobs_endpoints",
    "register_job_endpoints",
    "register_schedule_endpoints",
    "register_queue_endpoints",
    "register_task_endpoints",
    "register_all_job_endpoints",
    
    # Domain provider
    "configure_jobs_dependencies",
    "get_jobs_di_config",
    
    # Legacy classes (for backward compatibility)
    "Queue",
    "LegacyJobPriority",
    "LegacyJobStatus",
    "LegacyJob",
    "Worker",
    "AsyncWorker",
    "WorkerMiddleware",
    "Scheduler",
    "LegacySchedule",
    "Task",
    "TaskMiddleware",
    "TaskWorkflow",
    "TaskContext",
    "StorageBackend",
    "MemoryStorage",
    "DatabaseStorage",
    "RedisStorage",
    "LegacyJobManager",
]