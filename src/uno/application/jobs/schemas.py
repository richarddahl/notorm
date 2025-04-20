# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union

from uno.jobs.entities import (
    Job,
    JobPriority,
    JobStatus,
    Schedule,
    ScheduleInterval,
    JobError,
)
from uno.jobs.dtos import (
    JobViewDto,
    JobListDto,
    CreateJobDto,
    JobFilterParams,
    CancelJobDto,
    JobStatsDto,
    ScheduleViewDto,
    ScheduleListDto,
    CreateScheduleDto,
    UpdateScheduleDto,
    ScheduleFilterParams,
    TaskInfoDto,
    TaskListDto,
    QueueInfoDto,
    QueueListDto,
    RunSyncJobDto,
    PriorityEnum,
    StatusEnum,
    JobErrorDto,
    ScheduleIntervalDto,
)


class JobSchemaManager:
    """Schema manager for job entities."""

    def entity_to_dto(self, entity: Job) -> JobViewDto:
        """Convert a job entity to a DTO."""
        # Calculate duration if possible
        duration = None
        if entity.duration is not None:
            duration = entity.duration.total_seconds()

        # Convert error if present
        error = None
        if entity.error is not None:
            error = JobErrorDto(
                type=entity.error.type,
                message=entity.error.message,
                traceback=entity.error.traceback,
            )

        # Convert enums
        priority = PriorityEnum.NORMAL
        for p in PriorityEnum:
            if p.name.lower() == entity.priority.name.lower():
                priority = p
                break

        status = StatusEnum.PENDING
        for s in StatusEnum:
            if s.value == entity.status.value:
                status = s
                break

        # Convert timeout to seconds
        timeout = None
        if entity.timeout is not None:
            timeout = int(entity.timeout.total_seconds())

        # Convert retry_delay to seconds
        retry_delay = 60
        if entity.retry_delay is not None:
            retry_delay = int(entity.retry_delay.total_seconds())

        return JobViewDto(
            id=entity.id,
            task_name=entity.task_name,
            args=entity.args,
            kwargs=entity.kwargs,
            queue_name=entity.queue_name,
            priority=priority,
            status=status,
            scheduled_at=entity.scheduled_at,
            created_at=entity.created_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            result=entity.result,
            error=error,
            retry_count=entity.retry_count,
            max_retries=entity.max_retries,
            retry_delay=retry_delay,
            tags=list(entity.tags),
            metadata=entity.metadata,
            worker_id=entity.worker_id,
            timeout=timeout,
            version=entity.version,
            duration=duration,
        )

    def entities_to_list_dto(
        self,
        entities: list[Job],
        total: int,
        page: int,
        page_size: int,
    ) -> JobListDto:
        """Convert a list of job entities to a list DTO with pagination."""
        items = [self.entity_to_dto(entity) for entity in entities]
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return JobListDto(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def create_dto_to_params(self, dto: CreateJobDto) -> Dict[str, Any]:
        """Convert a create DTO to parameters for the domain service."""
        # Convert string enum to domain enum
        priority = JobPriority.NORMAL
        for p in JobPriority:
            if p.name.lower() == dto.priority.value:
                priority = p
                break

        params = {
            "task_name": dto.task_name,
            "args": dto.args,
            "kwargs": dto.kwargs,
            "queue_name": dto.queue_name,
            "priority": priority,
            "scheduled_at": dto.scheduled_at,
            "max_retries": dto.max_retries,
            "retry_delay": dto.retry_delay,
            "metadata": dto.metadata,
            "tags": set(dto.tags),
            "version": dto.version,
        }

        # Add job_id if provided
        if dto.job_id:
            params["job_id"] = dto.job_id

        # Add timeout if provided
        if dto.timeout is not None:
            params["timeout"] = dto.timeout

        return params

    def filter_params_to_query_params(self, params: JobFilterParams) -> Dict[str, Any]:
        """Convert filter parameters to query parameters for the repository."""
        query_params = {}

        if params.queue_name is not None:
            query_params["queue_name"] = params.queue_name

        if params.status is not None:
            status_enums = []
            for status_str in params.status:
                for status_enum in JobStatus:
                    if status_enum.value == status_str:
                        status_enums.append(status_enum)
                        break
            query_params["status"] = status_enums

        if params.priority is not None:
            for priority_enum in JobPriority:
                if priority_enum.name.lower() == params.priority:
                    query_params["priority"] = priority_enum
                    break

        if params.tags is not None:
            query_params["tags"] = set(params.tags)

        if params.worker_id is not None:
            query_params["worker_id"] = params.worker_id

        if params.before is not None:
            query_params["before"] = params.before

        if params.after is not None:
            query_params["after"] = params.after

        query_params["limit"] = params.limit
        query_params["offset"] = params.offset
        query_params["order_by"] = params.order_by
        query_params["order_dir"] = params.order_dir

        return query_params

    def stats_to_dto(self, stats: Dict[str, Any]) -> JobStatsDto:
        """Convert job statistics to a DTO."""
        dto = JobStatsDto(
            total_jobs=stats.get("total_jobs", 0),
            pending_jobs=stats.get("pending_jobs", 0),
            running_jobs=stats.get("running_jobs", 0),
            completed_jobs=stats.get("completed_jobs", 0),
            failed_jobs=stats.get("failed_jobs", 0),
            cancelled_jobs=stats.get("cancelled_jobs", 0),
            avg_wait_time=stats.get("avg_wait_time"),
            avg_run_time=stats.get("avg_run_time"),
            by_queue=stats.get("by_queue", {}),
            by_priority={},
        )

        # Convert priority counters
        for priority in JobPriority:
            key = f"priority_{priority.name.lower()}"
            if key in stats:
                dto.by_priority[priority.name.lower()] = stats[key]

        return dto

    def run_sync_dto_to_params(self, dto: RunSyncJobDto) -> Dict[str, Any]:
        """Convert a run sync DTO to parameters for the domain service."""
        params = {
            "task_name": dto.task_name,
            "args": dto.args,
            "kwargs": dto.kwargs,
            "metadata": dto.metadata,
            "version": dto.version,
        }

        # Add timeout if provided
        if dto.timeout is not None:
            params["timeout"] = dto.timeout

        return params


class ScheduleSchemaManager:
    """Schema manager for schedule entities."""

    def entity_to_dto(self, entity: Schedule) -> ScheduleViewDto:
        """Convert a schedule entity to a DTO."""
        # Convert interval if present
        interval = None
        if entity.interval is not None:
            interval = ScheduleIntervalDto(
                seconds=entity.interval.seconds,
                minutes=entity.interval.minutes,
                hours=entity.interval.hours,
                days=entity.interval.days,
            )

        # Convert enums
        priority = PriorityEnum.NORMAL
        for p in PriorityEnum:
            if p.name.lower() == entity.priority.name.lower():
                priority = p
                break

        # Convert timeout to seconds
        timeout = None
        if entity.timeout is not None:
            timeout = int(entity.timeout.total_seconds())

        # Convert retry_delay to seconds
        retry_delay = 60
        if entity.retry_delay is not None:
            retry_delay = int(entity.retry_delay.total_seconds())

        return ScheduleViewDto(
            id=entity.id,
            name=entity.name,
            task_name=entity.task_name,
            status=entity.status,
            cron_expression=entity.cron_expression,
            interval=interval,
            args=entity.args,
            kwargs=entity.kwargs,
            queue_name=entity.queue_name,
            priority=priority,
            tags=list(entity.tags),
            metadata=entity.metadata,
            max_retries=entity.max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            last_run_at=entity.last_run_at,
            next_run_at=entity.next_run_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            version=entity.version,
        )

    def entities_to_list_dto(
        self,
        entities: list[Schedule],
        total: int,
        page: int,
        page_size: int,
    ) -> ScheduleListDto:
        """Convert a list of schedule entities to a list DTO with pagination."""
        items = [self.entity_to_dto(entity) for entity in entities]
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return ScheduleListDto(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def create_dto_to_params(self, dto: CreateScheduleDto) -> Dict[str, Any]:
        """Convert a create DTO to parameters for the domain service."""
        # Convert string enum to domain enum
        priority = JobPriority.NORMAL
        for p in JobPriority:
            if p.name.lower() == dto.priority.value:
                priority = p
                break

        # Convert interval if present
        interval = None
        if dto.interval is not None:
            interval = ScheduleInterval(
                seconds=dto.interval.seconds,
                minutes=dto.interval.minutes,
                hours=dto.interval.hours,
                days=dto.interval.days,
            )

        params = {
            "name": dto.name,
            "task_name": dto.task_name,
            "cron_expression": dto.cron_expression,
            "interval": interval,
            "args": dto.args,
            "kwargs": dto.kwargs,
            "queue_name": dto.queue_name,
            "priority": priority,
            "tags": set(dto.tags),
            "metadata": dto.metadata,
            "max_retries": dto.max_retries,
            "retry_delay": dto.retry_delay,
            "version": dto.version,
        }

        # Add timeout if provided
        if dto.timeout is not None:
            params["timeout"] = dto.timeout

        return params

    def update_dto_to_params(self, dto: UpdateScheduleDto) -> Dict[str, Any]:
        """Convert an update DTO to parameters for the domain service."""
        params = {}

        if dto.name is not None:
            params["name"] = dto.name

        if dto.cron_expression is not None:
            params["cron_expression"] = dto.cron_expression

        if dto.interval is not None:
            params["interval"] = ScheduleInterval(
                seconds=dto.interval.seconds,
                minutes=dto.interval.minutes,
                hours=dto.interval.hours,
                days=dto.interval.days,
            )

        if dto.args is not None:
            params["args"] = dto.args

        if dto.kwargs is not None:
            params["kwargs"] = dto.kwargs

        if dto.queue_name is not None:
            params["queue_name"] = dto.queue_name

        if dto.priority is not None:
            for p in JobPriority:
                if p.name.lower() == dto.priority.value:
                    params["priority"] = p
                    break

        if dto.tags is not None:
            params["tags"] = set(dto.tags)

        if dto.metadata is not None:
            params["metadata"] = dto.metadata

        if dto.max_retries is not None:
            params["max_retries"] = dto.max_retries

        if dto.retry_delay is not None:
            params["retry_delay"] = dto.retry_delay

        if dto.timeout is not None:
            params["timeout"] = dto.timeout

        if dto.status is not None:
            params["status"] = dto.status

        return params

    def filter_params_to_query_params(
        self, params: ScheduleFilterParams
    ) -> Dict[str, Any]:
        """Convert filter parameters to query parameters for the repository."""
        query_params = {}

        if params.status is not None:
            query_params["status"] = params.status

        if params.tags is not None:
            query_params["tags"] = set(params.tags)

        query_params["limit"] = params.limit
        query_params["offset"] = params.offset

        return query_params


class TaskSchemaManager:
    """Schema manager for task information."""

    def task_to_dto(self, task: Dict[str, Any]) -> TaskInfoDto:
        """Convert a task definition to a DTO."""
        timeout = None
        if (
            "options" in task
            and "timeout" in task["options"]
            and task["options"]["timeout"] is not None
        ):
            timeout = int(task["options"]["timeout"].total_seconds())

        retry_delay = 60
        if (
            "options" in task
            and "retry_delay" in task["options"]
            and task["options"]["retry_delay"] is not None
        ):
            retry_delay = int(task["options"]["retry_delay"].total_seconds())

        return TaskInfoDto(
            name=task["name"],
            description=task.get("description"),
            is_async=task.get("is_async", False),
            timeout=timeout,
            max_retries=task.get("options", {}).get("max_retries", 3),
            retry_delay=retry_delay,
            queue=task.get("options", {}).get("queue", "default"),
            version=task.get("version"),
        )

    def tasks_to_list_dto(self, tasks: list[dict[str, Any]]) -> TaskListDto:
        """Convert a list of task definitions to a list DTO."""
        items = [self.task_to_dto(task) for task in tasks]

        return TaskListDto(
            items=items,
            total=len(items),
        )


class QueueSchemaManager:
    """Schema manager for queue information."""

    def queue_to_dto(self, name: str, size: int, is_paused: bool) -> QueueInfoDto:
        """Convert queue information to a DTO."""
        return QueueInfoDto(
            name=name,
            size=size,
            is_paused=is_paused,
        )

    def queues_to_list_dto(self, queues: list[Tuple[str, int, bool]]) -> QueueListDto:
        """Convert a list of queue information to a list DTO."""
        items = [
            self.queue_to_dto(name, size, is_paused) for name, size, is_paused in queues
        ]

        return QueueListDto(
            items=items,
            total=len(items),
        )
