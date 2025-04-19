from typing import Dict, List, Optional, Set, Any
import asyncio
import json
import uuid
from datetime import datetime, timedelta, UTC

import aioredis

from uno.core.errors.result import Result
from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus
from uno.jobs.scheduler.schedules import Schedule, ScheduleDefinition
from uno.jobs.storage.base import JobStorageProtocol


class RedisJobStorage(JobStorageProtocol):
    """Redis-backed job storage implementation optimized for high throughput."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "uno:jobs"):
        """Initialize the Redis storage backend.
        
        Args:
            redis_url: The Redis connection URL.
            prefix: Prefix for Redis keys to avoid collisions.
        """
        self._redis_url = redis_url
        self._prefix = prefix
        self._redis: Optional[aioredis.Redis] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Redis connection pool."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
    
    def _get_job_key(self, job_id: str) -> str:
        """Get the Redis key for a job.
        
        Args:
            job_id: The job ID.
            
        Returns:
            The Redis key.
        """
        return f"{self._prefix}:job:{job_id}"
    
    def _get_queue_key(self, queue_name: str, priority: Priority) -> str:
        """Get the Redis key for a queue.
        
        Args:
            queue_name: The queue name.
            priority: The priority level.
            
        Returns:
            The Redis key.
        """
        return f"{self._prefix}:queue:{queue_name}:{priority.value}"
    
    def _get_schedule_key(self, schedule_id: str) -> str:
        """Get the Redis key for a schedule.
        
        Args:
            schedule_id: The schedule ID.
            
        Returns:
            The Redis key.
        """
        return f"{self._prefix}:schedule:{schedule_id}"
    
    def _get_schedule_name_index_key(self) -> str:
        """Get the Redis key for the schedule name index.
        
        Returns:
            The Redis key.
        """
        return f"{self._prefix}:schedule_name_index"
    
    def _get_schedule_due_key(self) -> str:
        """Get the Redis key for the sorted set of due schedules.
        
        Returns:
            The Redis key.
        """
        return f"{self._prefix}:schedule_due"
    
    def _get_queue_set_key(self) -> str:
        """Get the Redis key for the set of queue names.
        
        Returns:
            The Redis key.
        """
        return f"{self._prefix}:queues"
    
    def _get_status_index_key(self, status: JobStatus) -> str:
        """Get the Redis key for a status index.
        
        Args:
            status: The job status.
            
        Returns:
            The Redis key.
        """
        return f"{self._prefix}:status:{status.value}"
    
    def _serialize_job(self, job: Job) -> dict:
        """Serialize a job to a dictionary for Redis storage.
        
        Args:
            job: The job to serialize.
            
        Returns:
            A dictionary representation of the job.
        """
        return {
            "id": job.id,
            "queue_name": job.queue_name,
            "status": job.status.value,
            "task_name": job.task_name,
            "args": json.dumps(job.args or []),
            "kwargs": json.dumps(job.kwargs or {}),
            "result": json.dumps(job.result) if job.result is not None else None,
            "error": json.dumps(job.error) if job.error is not None else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "priority": job.priority.value,
            "retries": job.retries,
            "max_retries": job.max_retries,
            "retry_delay": job.retry_delay.total_seconds() if job.retry_delay else None,
            "timeout": job.timeout.total_seconds() if job.timeout else None,
            "is_scheduled": int(job.is_scheduled),
            "metadata": json.dumps(job.metadata or {}),
            "tags": json.dumps(list(job.tags) if job.tags else []),
        }
    
    def _deserialize_job(self, data: dict) -> Job:
        """Deserialize a job from Redis data.
        
        Args:
            data: The Redis data.
            
        Returns:
            A Job object.
        """
        # Handle timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        scheduled_at = datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None
        started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        
        # Handle JSON fields
        args = json.loads(data["args"]) if data.get("args") else []
        kwargs = json.loads(data["kwargs"]) if data.get("kwargs") else {}
        result = json.loads(data["result"]) if data.get("result") else None
        error = json.loads(data["error"]) if data.get("error") else None
        metadata = json.loads(data["metadata"]) if data.get("metadata") else {}
        tags = set(json.loads(data["tags"])) if data.get("tags") else set()
        
        # Handle other fields
        status = JobStatus(data["status"])
        priority = Priority(int(data["priority"]))
        retry_delay = timedelta(seconds=float(data["retry_delay"])) if data.get("retry_delay") else None
        timeout = timedelta(seconds=float(data["timeout"])) if data.get("timeout") else None
        is_scheduled = bool(int(data["is_scheduled"])) if "is_scheduled" in data else False
        
        return Job(
            id=data["id"],
            queue_name=data["queue_name"],
            status=status,
            task_name=data["task_name"],
            args=args,
            kwargs=kwargs,
            result=result,
            error=error,
            created_at=created_at,
            updated_at=updated_at,
            scheduled_at=scheduled_at,
            started_at=started_at,
            completed_at=completed_at,
            priority=priority,
            retries=int(data["retries"]),
            max_retries=int(data["max_retries"]),
            retry_delay=retry_delay,
            timeout=timeout,
            is_scheduled=is_scheduled,
            metadata=metadata,
            tags=tags,
        )
    
    def _serialize_schedule(self, schedule_def: ScheduleDefinition) -> dict:
        """Serialize a schedule definition to a dictionary for Redis storage.
        
        Args:
            schedule_def: The schedule definition to serialize.
            
        Returns:
            A dictionary representation of the schedule definition.
        """
        return {
            "id": schedule_def.id,
            "name": schedule_def.name,
            "task_name": schedule_def.task_name,
            "schedule_type": schedule_def.schedule.schedule_type,
            "schedule_data": json.dumps(schedule_def.schedule.to_dict()),
            "args": json.dumps(schedule_def.args or []),
            "kwargs": json.dumps(schedule_def.kwargs or {}),
            "queue_name": schedule_def.queue_name,
            "priority": schedule_def.priority.value,
            "max_retries": schedule_def.max_retries,
            "retry_delay": schedule_def.retry_delay.total_seconds() if schedule_def.retry_delay else None,
            "timeout": schedule_def.timeout.total_seconds() if schedule_def.timeout else None,
            "created_at": schedule_def.created_at.isoformat() if schedule_def.created_at else datetime.now(datetime.UTC).isoformat(),
            "updated_at": schedule_def.updated_at.isoformat() if schedule_def.updated_at else datetime.now(datetime.UTC).isoformat(),
            "last_run_at": schedule_def.last_run_at.isoformat() if schedule_def.last_run_at else None,
            "next_run_at": schedule_def.next_run_at.isoformat() if schedule_def.next_run_at else None,
            "metadata": json.dumps(schedule_def.metadata or {}),
            "enabled": int(schedule_def.enabled),
        }
    
    def _deserialize_schedule(self, data: dict) -> ScheduleDefinition:
        """Deserialize a schedule definition from Redis data.
        
        Args:
            data: The Redis data.
            
        Returns:
            A ScheduleDefinition object.
        """
        # Handle timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        last_run_at = datetime.fromisoformat(data["last_run_at"]) if data.get("last_run_at") else None
        next_run_at = datetime.fromisoformat(data["next_run_at"]) if data.get("next_run_at") else None
        
        # Handle JSON fields
        schedule_data = json.loads(data["schedule_data"])
        args = json.loads(data["args"]) if data.get("args") else []
        kwargs = json.loads(data["kwargs"]) if data.get("kwargs") else {}
        metadata = json.loads(data["metadata"]) if data.get("metadata") else {}
        
        # Handle other fields
        schedule_type = data["schedule_type"]
        priority = Priority(int(data["priority"]))
        retry_delay = timedelta(seconds=float(data["retry_delay"])) if data.get("retry_delay") else None
        timeout = timedelta(seconds=float(data["timeout"])) if data.get("timeout") else None
        enabled = bool(int(data["enabled"])) if "enabled" in data else True
        
        # Create schedule object
        schedule = Schedule.from_dict(schedule_type, schedule_data)
        
        return ScheduleDefinition(
            id=data["id"],
            name=data["name"],
            task_name=data["task_name"],
            schedule=schedule,
            args=args,
            kwargs=kwargs,
            queue_name=data["queue_name"],
            priority=priority,
            max_retries=int(data["max_retries"]),
            retry_delay=retry_delay,
            timeout=timeout,
            created_at=created_at,
            updated_at=updated_at,
            last_run_at=last_run_at,
            next_run_at=next_run_at,
            metadata=metadata,
            enabled=enabled,
        )
    
    async def add_job(self, job: Job) -> Result[str]:
        """Add a job to storage.
        
        Args:
            job: The job to add.
            
        Returns:
            Result with the job ID if successful.
        """
        try:
            await self.initialize()
            
            # Set default values for timestamps if not provided
            if not job.created_at:
                job.created_at = datetime.now(datetime.UTC)
            if not job.updated_at:
                job.updated_at = datetime.now(datetime.UTC)
                
            job_data = self._serialize_job(job)
            job_key = self._get_job_key(job.id)
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Store the job data
                pipeline.hset(job_key, mapping=job_data)
                
                # Add to the queue (if pending)
                if job.status == JobStatus.PENDING:
                    queue_key = self._get_queue_key(job.queue_name, job.priority)
                    score = job.created_at.timestamp()  # Use created_at timestamp as score for FIFO
                    pipeline.zadd(queue_key, {job.id: score})
                    
                # Add to the status index
                status_key = self._get_status_index_key(job.status)
                pipeline.sadd(status_key, job.id)
                
                # Add to the queue set
                pipeline.sadd(self._get_queue_set_key(), job.queue_name)
                
                await pipeline.execute()
                
                return Result.success(job.id)
        except Exception as e:
            return Result.failure(f"Failed to add job to Redis: {str(e)}")
    
    async def get_job(self, job_id: str) -> Result[Optional[Job]]:
        """Get a job by ID.
        
        Args:
            job_id: The ID of the job to retrieve.
            
        Returns:
            Result with the job if found, None if not found.
        """
        try:
            await self.initialize()
            
            job_key = self._get_job_key(job_id)
            job_data = await self._redis.hgetall(job_key)
            
            if not job_data:
                return Result.success(None)
                
            job = self._deserialize_job(job_data)
            return Result.success(job)
        except Exception as e:
            return Result.failure(f"Failed to get job from Redis: {str(e)}")
    
    async def update_job(self, job: Job) -> Result[bool]:
        """Update a job in storage.
        
        Args:
            job: The job to update.
            
        Returns:
            Result with True if the update was successful.
        """
        try:
            await self.initialize()
            
            # Update the updated_at timestamp
            job.updated_at = datetime.now(datetime.UTC)
            
            job_data = self._serialize_job(job)
            job_key = self._get_job_key(job.id)
            
            # Get the current job to check if status has changed
            current_job_result = await self.get_job(job.id)
            if not current_job_result.is_success:
                return Result.failure(f"Failed to get current job state: {current_job_result.error}")
                
            current_job = current_job_result.value
            if current_job is None:
                return Result.failure(f"Job {job.id} does not exist")
                
            old_status = current_job.status
            new_status = job.status
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Update the job data
                pipeline.hset(job_key, mapping=job_data)
                
                # Handle status changes
                if old_status != new_status:
                    # Remove from old status index
                    old_status_key = self._get_status_index_key(old_status)
                    pipeline.srem(old_status_key, job.id)
                    
                    # Add to new status index
                    new_status_key = self._get_status_index_key(new_status)
                    pipeline.sadd(new_status_key, job.id)
                    
                    # Handle queue changes
                    if old_status == JobStatus.PENDING:
                        # Remove from queue if it was pending
                        old_queue_key = self._get_queue_key(job.queue_name, job.priority)
                        pipeline.zrem(old_queue_key, job.id)
                    
                    if new_status == JobStatus.PENDING:
                        # Add to queue if it's now pending
                        new_queue_key = self._get_queue_key(job.queue_name, job.priority)
                        score = datetime.now(datetime.UTC).timestamp()
                        pipeline.zadd(new_queue_key, {job.id: score})
                
                await pipeline.execute()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to update job in Redis: {str(e)}")
    
    async def delete_job(self, job_id: str) -> Result[bool]:
        """Delete a job from storage.
        
        Args:
            job_id: The ID of the job to delete.
            
        Returns:
            Result with True if the deletion was successful.
        """
        try:
            await self.initialize()
            
            # Get the current job to find out its status and queue
            job_result = await self.get_job(job_id)
            if not job_result.is_success:
                return Result.failure(f"Failed to get job for deletion: {job_result.error}")
                
            job = job_result.value
            if job is None:
                return Result.success(True)  # Job doesn't exist, consider it deleted
                
            job_key = self._get_job_key(job_id)
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Delete the job data
                pipeline.delete(job_key)
                
                # Remove from status index
                status_key = self._get_status_index_key(job.status)
                pipeline.srem(status_key, job_id)
                
                # Remove from queue if it's pending
                if job.status == JobStatus.PENDING:
                    queue_key = self._get_queue_key(job.queue_name, job.priority)
                    pipeline.zrem(queue_key, job_id)
                
                await pipeline.execute()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to delete job from Redis: {str(e)}")
    
    async def enqueue_job(self, job: Job) -> Result[bool]:
        """Enqueue a job by adding it to storage or updating its status if it exists.
        
        Args:
            job: The job to enqueue.
            
        Returns:
            Result with True if the operation was successful.
        """
        try:
            await self.initialize()
            
            job.status = JobStatus.PENDING
            job.updated_at = datetime.now(datetime.UTC)
            
            # Check if job already exists
            job_exists_result = await self.get_job(job.id)
            if not job_exists_result.is_success:
                return Result.failure(f"Failed to check if job exists: {job_exists_result.error}")
                
            if job_exists_result.value:
                return await self.update_job(job)
            else:
                add_result = await self.add_job(job)
                return Result.success(add_result.is_success)
        except Exception as e:
            return Result.failure(f"Failed to enqueue job in Redis: {str(e)}")
    
    async def dequeue_job(self, queue_name: str, statuses: Optional[List[JobStatus]] = None) -> Result[Optional[Job]]:
        """Dequeue a job from the specified queue with the given statuses.
        
        Args:
            queue_name: The name of the queue to dequeue from.
            statuses: Optional list of statuses to filter by. Defaults to [JobStatus.PENDING].
            
        Returns:
            Result with the dequeued job, or None if no job is available.
        """
        if statuses is None:
            statuses = [JobStatus.PENDING]
            
        if JobStatus.PENDING not in statuses:
            return Result.success(None)  # Only pending jobs can be dequeued
            
        try:
            await self.initialize()
            
            now = datetime.now(datetime.UTC).timestamp()
            
            # Try each priority queue in order (highest to lowest)
            for priority in sorted(Priority, key=lambda p: p.value):
                queue_key = self._get_queue_key(queue_name, priority)
                
                # Get the first job ID with score <= now (not scheduled for the future)
                # This is an atomic operation in Redis
                async with self._lock:
                    job_ids_with_scores = await self._redis.zrangebyscore(
                        queue_key, 
                        min="-inf", 
                        max=now, 
                        start=0, 
                        num=1, 
                        withscores=True
                    )
                    
                    if not job_ids_with_scores:
                        continue  # No jobs in this priority queue
                        
                    job_id, score = job_ids_with_scores[0]
                    
                    # Get the job data
                    job_result = await self.get_job(job_id)
                    if not job_result.is_success:
                        continue  # Skip this job if we can't get its data
                        
                    job = job_result.value
                    if job is None:
                        # Job ID exists in queue but not in storage, remove it
                        await self._redis.zrem(queue_key, job_id)
                        continue
                        
                    # Update the job status to RUNNING
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now(datetime.UTC)
                    job.updated_at = datetime.now(datetime.UTC)
                    
                    # Remove the job from the pending queue
                    await self._redis.zrem(queue_key, job_id)
                    
                    # Update the job data
                    update_result = await self.update_job(job)
                    if not update_result.is_success:
                        return update_result
                    
                    return Result.success(job)
            
            # No jobs found in any priority queue
            return Result.success(None)
        except Exception as e:
            return Result.failure(f"Failed to dequeue job from Redis: {str(e)}")
    
    async def get_queue_length(self, queue_name: str, statuses: Optional[List[JobStatus]] = None) -> Result[int]:
        """Get the length of a queue with jobs in the specified statuses.
        
        Args:
            queue_name: The name of the queue.
            statuses: Optional list of statuses to filter by. Defaults to [JobStatus.PENDING].
            
        Returns:
            Result with the number of jobs in the queue.
        """
        if statuses is None:
            statuses = [JobStatus.PENDING]
            
        try:
            await self.initialize()
            
            total_count = 0
            
            if JobStatus.PENDING in statuses:
                # For pending jobs, count across all priority queues
                for priority in Priority:
                    queue_key = self._get_queue_key(queue_name, priority)
                    count = await self._redis.zcard(queue_key)
                    total_count += count
            
            # For other statuses, we need to iterate through all jobs with those statuses
            for status in [s for s in statuses if s != JobStatus.PENDING]:
                status_key = self._get_status_index_key(status)
                all_job_ids = await self._redis.smembers(status_key)
                
                # Check each job to see if it's in the requested queue
                for job_id in all_job_ids:
                    job_key = self._get_job_key(job_id)
                    job_queue = await self._redis.hget(job_key, "queue_name")
                    
                    if job_queue == queue_name:
                        total_count += 1
                        
            return Result.success(total_count)
        except Exception as e:
            return Result.failure(f"Failed to get queue length from Redis: {str(e)}")
    
    async def get_jobs_by_status(
        self, 
        statuses: List[JobStatus], 
        queue_name: Optional[str] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> Result[List[Job]]:
        """Get jobs by status.
        
        Args:
            statuses: List of statuses to filter by.
            queue_name: Optional queue name to filter by.
            limit: Maximum number of jobs to return.
            offset: Offset for pagination.
            
        Returns:
            Result with a list of jobs.
        """
        try:
            await self.initialize()
            
            all_matching_jobs = []
            
            # Collect job IDs from all requested statuses
            for status in statuses:
                status_key = self._get_status_index_key(status)
                job_ids = await self._redis.smembers(status_key)
                
                # If filtering by queue, check each job
                if queue_name:
                    filtered_job_ids = []
                    for job_id in job_ids:
                        job_key = self._get_job_key(job_id)
                        job_queue = await self._redis.hget(job_key, "queue_name")
                        
                        if job_queue == queue_name:
                            filtered_job_ids.append(job_id)
                    
                    job_ids = filtered_job_ids
                
                # Apply offset and limit
                if offset >= len(job_ids):
                    continue
                    
                job_ids = list(job_ids)[offset:offset + limit]
                
                # Fetch job data for each ID
                for job_id in job_ids:
                    job_result = await self.get_job(job_id)
                    if job_result.is_success and job_result.value:
                        all_matching_jobs.append(job_result.value)
                        
                        if len(all_matching_jobs) >= limit:
                            break
                
                if len(all_matching_jobs) >= limit:
                    break
                    
            # Sort by updated_at
            all_matching_jobs.sort(key=lambda j: j.updated_at or datetime.min, reverse=True)
            
            return Result.success(all_matching_jobs)
        except Exception as e:
            return Result.failure(f"Failed to get jobs by status from Redis: {str(e)}")
    
    async def add_schedule(self, schedule_def: ScheduleDefinition) -> Result[str]:
        """Add a schedule to storage.
        
        Args:
            schedule_def: The schedule definition to add.
            
        Returns:
            Result with the schedule ID if successful.
        """
        try:
            await self.initialize()
            
            # Generate ID if not provided
            if not schedule_def.id:
                schedule_def.id = str(uuid.uuid4())
            
            # Set timestamps if not provided
            now = datetime.now(datetime.UTC)
            if not schedule_def.created_at:
                schedule_def.created_at = now
            if not schedule_def.updated_at:
                schedule_def.updated_at = now
                
            # Calculate next run time if not provided
            if not schedule_def.next_run_at:
                schedule_def.next_run_at = schedule_def.schedule.next_run_time(now)
                
            schedule_data = self._serialize_schedule(schedule_def)
            schedule_key = self._get_schedule_key(schedule_def.id)
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Store the schedule data
                pipeline.hset(schedule_key, mapping=schedule_data)
                
                # Add to name index
                name_index_key = self._get_schedule_name_index_key()
                pipeline.hset(name_index_key, schedule_def.name, schedule_def.id)
                
                # Add to due schedules sorted set if enabled
                if schedule_def.enabled and schedule_def.next_run_at:
                    due_key = self._get_schedule_due_key()
                    score = schedule_def.next_run_at.timestamp()
                    pipeline.zadd(due_key, {schedule_def.id: score})
                
                await pipeline.execute()
                
                return Result.success(schedule_def.id)
        except Exception as e:
            return Result.failure(f"Failed to add schedule to Redis: {str(e)}")
    
    async def get_schedule(self, schedule_id: str) -> Result[Optional[ScheduleDefinition]]:
        """Get a schedule by ID.
        
        Args:
            schedule_id: The ID of the schedule to retrieve.
            
        Returns:
            Result with the schedule if found, None if not found.
        """
        try:
            await self.initialize()
            
            schedule_key = self._get_schedule_key(schedule_id)
            schedule_data = await self._redis.hgetall(schedule_key)
            
            if not schedule_data:
                return Result.success(None)
                
            schedule = self._deserialize_schedule(schedule_data)
            return Result.success(schedule)
        except Exception as e:
            return Result.failure(f"Failed to get schedule from Redis: {str(e)}")
    
    async def get_schedule_by_name(self, name: str) -> Result[Optional[ScheduleDefinition]]:
        """Get a schedule by name.
        
        Args:
            name: The name of the schedule to retrieve.
            
        Returns:
            Result with the schedule if found, None if not found.
        """
        try:
            await self.initialize()
            
            name_index_key = self._get_schedule_name_index_key()
            schedule_id = await self._redis.hget(name_index_key, name)
            
            if not schedule_id:
                return Result.success(None)
                
            return await self.get_schedule(schedule_id)
        except Exception as e:
            return Result.failure(f"Failed to get schedule by name from Redis: {str(e)}")
    
    async def update_schedule(self, schedule_def: ScheduleDefinition) -> Result[bool]:
        """Update a schedule in storage.
        
        Args:
            schedule_def: The schedule definition to update.
            
        Returns:
            Result with True if the update was successful.
        """
        try:
            await self.initialize()
            
            # Update the updated_at timestamp
            schedule_def.updated_at = datetime.now(datetime.UTC)
            
            # Get current schedule to check if enabled status changed
            current_schedule_result = await self.get_schedule(schedule_def.id)
            if not current_schedule_result.is_success:
                return Result.failure(f"Failed to get current schedule: {current_schedule_result.error}")
                
            current_schedule = current_schedule_result.value
            if current_schedule is None:
                return Result.failure(f"Schedule {schedule_def.id} does not exist")
                
            # Calculate next run time if schedule changed
            if (schedule_def.schedule.schedule_type != current_schedule.schedule.schedule_type or
                schedule_def.schedule.to_dict() != current_schedule.schedule.to_dict() or
                schedule_def.next_run_at is None):
                schedule_def.next_run_at = schedule_def.schedule.next_run_time(datetime.now(datetime.UTC))
                
            schedule_data = self._serialize_schedule(schedule_def)
            schedule_key = self._get_schedule_key(schedule_def.id)
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Update the schedule data
                pipeline.hset(schedule_key, mapping=schedule_data)
                
                # Update name index if name changed
                if schedule_def.name != current_schedule.name:
                    name_index_key = self._get_schedule_name_index_key()
                    pipeline.hdel(name_index_key, current_schedule.name)
                    pipeline.hset(name_index_key, schedule_def.name, schedule_def.id)
                
                # Update due schedules sorted set
                due_key = self._get_schedule_due_key()
                
                # Remove from due set if disabled or was enabled and is now disabled
                if not schedule_def.enabled or (current_schedule.enabled and not schedule_def.enabled):
                    pipeline.zrem(due_key, schedule_def.id)
                
                # Add/update in due set if enabled and has a next run time
                if schedule_def.enabled and schedule_def.next_run_at:
                    score = schedule_def.next_run_at.timestamp()
                    pipeline.zadd(due_key, {schedule_def.id: score})
                
                await pipeline.execute()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to update schedule in Redis: {str(e)}")
    
    async def delete_schedule(self, schedule_id: str) -> Result[bool]:
        """Delete a schedule from storage.
        
        Args:
            schedule_id: The ID of the schedule to delete.
            
        Returns:
            Result with True if the deletion was successful.
        """
        try:
            await self.initialize()
            
            # Get the schedule first to get its name
            schedule_result = await self.get_schedule(schedule_id)
            if not schedule_result.is_success:
                return Result.failure(f"Failed to get schedule for deletion: {schedule_result.error}")
                
            schedule = schedule_result.value
            if schedule is None:
                return Result.success(True)  # Schedule doesn't exist, consider it deleted
                
            schedule_key = self._get_schedule_key(schedule_id)
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Delete the schedule data
                pipeline.delete(schedule_key)
                
                # Remove from name index
                name_index_key = self._get_schedule_name_index_key()
                pipeline.hdel(name_index_key, schedule.name)
                
                # Remove from due schedules sorted set
                due_key = self._get_schedule_due_key()
                pipeline.zrem(due_key, schedule_id)
                
                await pipeline.execute()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to delete schedule from Redis: {str(e)}")
    
    async def get_due_schedules(self) -> Result[List[ScheduleDefinition]]:
        """Get schedules that are due to run.
        
        Returns:
            Result with a list of due schedules.
        """
        try:
            await self.initialize()
            
            now = datetime.now(datetime.UTC).timestamp()
            due_key = self._get_schedule_due_key()
            
            # Get all schedules with a next run time <= now
            schedule_ids = await self._redis.zrangebyscore(due_key, min="-inf", max=now)
            
            due_schedules = []
            for schedule_id in schedule_ids:
                schedule_result = await self.get_schedule(schedule_id)
                if schedule_result.is_success and schedule_result.value:
                    due_schedules.append(schedule_result.value)
                    
            return Result.success(due_schedules)
        except Exception as e:
            return Result.failure(f"Failed to get due schedules from Redis: {str(e)}")
    
    async def update_schedule_run_time(self, schedule_id: str, last_run: datetime, next_run: datetime) -> Result[bool]:
        """Update a schedule's last run time and next run time.
        
        Args:
            schedule_id: The ID of the schedule to update.
            last_run: The last run time to set.
            next_run: The next run time to set.
            
        Returns:
            Result with True if the update was successful.
        """
        try:
            await self.initialize()
            
            # Get the current schedule
            schedule_result = await self.get_schedule(schedule_id)
            if not schedule_result.is_success:
                return Result.failure(f"Failed to get schedule: {schedule_result.error}")
                
            schedule = schedule_result.value
            if schedule is None:
                return Result.failure(f"Schedule {schedule_id} does not exist")
                
            # Update the schedule
            schedule.last_run_at = last_run
            schedule.next_run_at = next_run
            schedule.updated_at = datetime.now(datetime.UTC)
            
            schedule_data = {
                "last_run_at": last_run.isoformat(),
                "next_run_at": next_run.isoformat(),
                "updated_at": datetime.now(datetime.UTC).isoformat(),
            }
            
            schedule_key = self._get_schedule_key(schedule_id)
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Update the schedule data
                pipeline.hset(schedule_key, mapping=schedule_data)
                
                # Update in due schedules sorted set if enabled
                if schedule.enabled:
                    due_key = self._get_schedule_due_key()
                    score = next_run.timestamp()
                    pipeline.zadd(due_key, {schedule_id: score})
                
                await pipeline.execute()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to update schedule run times in Redis: {str(e)}")
    
    async def get_all_schedules(self) -> Result[List[ScheduleDefinition]]:
        """Get all schedules.
        
        Returns:
            Result with a list of all schedules.
        """
        try:
            await self.initialize()
            
            name_index_key = self._get_schedule_name_index_key()
            schedule_map = await self._redis.hgetall(name_index_key)
            
            all_schedules = []
            for schedule_id in schedule_map.values():
                schedule_result = await self.get_schedule(schedule_id)
                if schedule_result.is_success and schedule_result.value:
                    all_schedules.append(schedule_result.value)
                    
            return Result.success(all_schedules)
        except Exception as e:
            return Result.failure(f"Failed to get all schedules from Redis: {str(e)}")
    
    async def clear_queue(self, queue_name: str) -> Result[int]:
        """Clear all pending jobs from a queue.
        
        Args:
            queue_name: The name of the queue to clear.
            
        Returns:
            Result with the number of jobs cleared.
        """
        try:
            await self.initialize()
            
            count = 0
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Clear each priority queue
                for priority in Priority:
                    queue_key = self._get_queue_key(queue_name, priority)
                    job_ids = await self._redis.zrange(queue_key, 0, -1)
                    count += len(job_ids)
                    
                    if job_ids:
                        # Remove from queue
                        pipeline.delete(queue_key)
                        
                        # Update each job's status to CANCELLED
                        for job_id in job_ids:
                            job_key = self._get_job_key(job_id)
                            pipeline.hset(job_key, "status", JobStatus.CANCELLED.value)
                            pipeline.hset(job_key, "updated_at", datetime.now(datetime.UTC).isoformat())
                            
                            # Remove from PENDING status set
                            pipeline.srem(self._get_status_index_key(JobStatus.PENDING), job_id)
                            
                            # Add to CANCELLED status set
                            pipeline.sadd(self._get_status_index_key(JobStatus.CANCELLED), job_id)
                
                await pipeline.execute()
                
                return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to clear queue in Redis: {str(e)}")
    
    async def pause_queue(self, queue_name: str) -> Result[bool]:
        """Pause a queue by marking all pending jobs as paused.
        
        Args:
            queue_name: The name of the queue to pause.
            
        Returns:
            Result with True if the operation was successful.
        """
        try:
            await self.initialize()
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Process each priority queue
                for priority in Priority:
                    queue_key = self._get_queue_key(queue_name, priority)
                    job_ids = await self._redis.zrange(queue_key, 0, -1)
                    
                    if job_ids:
                        # Save the job IDs and scores to a temporary key
                        temp_key = f"{queue_key}:paused"
                        
                        # Get scores for each job
                        for job_id in job_ids:
                            score = await self._redis.zscore(queue_key, job_id)
                            pipeline.zadd(temp_key, {job_id: score})
                            
                            # Update job status
                            job_key = self._get_job_key(job_id)
                            pipeline.hset(job_key, "status", JobStatus.PAUSED.value)
                            pipeline.hset(job_key, "updated_at", datetime.now(datetime.UTC).isoformat())
                            
                            # Update status sets
                            pipeline.srem(self._get_status_index_key(JobStatus.PENDING), job_id)
                            pipeline.sadd(self._get_status_index_key(JobStatus.PAUSED), job_id)
                        
                        # Clear the actual queue
                        pipeline.delete(queue_key)
                
                await pipeline.execute()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to pause queue in Redis: {str(e)}")
    
    async def resume_queue(self, queue_name: str) -> Result[bool]:
        """Resume a queue by marking all paused jobs as pending.
        
        Args:
            queue_name: The name of the queue to resume.
            
        Returns:
            Result with True if the operation was successful.
        """
        try:
            await self.initialize()
            
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                # Process each priority queue
                for priority in Priority:
                    queue_key = self._get_queue_key(queue_name, priority)
                    temp_key = f"{queue_key}:paused"
                    
                    # Check if we have paused jobs
                    paused_jobs = await self._redis.zrange(temp_key, 0, -1, withscores=True)
                    
                    if paused_jobs:
                        # Add jobs back to the queue with their original scores
                        for job_id, score in paused_jobs:
                            pipeline.zadd(queue_key, {job_id: score})
                            
                            # Update job status
                            job_key = self._get_job_key(job_id)
                            pipeline.hset(job_key, "status", JobStatus.PENDING.value)
                            pipeline.hset(job_key, "updated_at", datetime.now(datetime.UTC).isoformat())
                            
                            # Update status sets
                            pipeline.srem(self._get_status_index_key(JobStatus.PAUSED), job_id)
                            pipeline.sadd(self._get_status_index_key(JobStatus.PENDING), job_id)
                        
                        # Remove temporary key
                        pipeline.delete(temp_key)
                
                await pipeline.execute()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to resume queue in Redis: {str(e)}")
    
    async def get_queue_names(self) -> Result[Set[str]]:
        """Get all queue names.
        
        Returns:
            Result with a set of all queue names.
        """
        try:
            await self.initialize()
            
            queue_set_key = self._get_queue_set_key()
            queue_names = await self._redis.smembers(queue_set_key)
            
            return Result.success(set(queue_names))
        except Exception as e:
            return Result.failure(f"Failed to get queue names from Redis: {str(e)}")
    
    async def cleanup_old_jobs(self, max_age: timedelta) -> Result[int]:
        """Clean up old completed/failed jobs.
        
        Args:
            max_age: The maximum age of jobs to keep.
            
        Returns:
            Result with the number of jobs cleaned up.
        """
        try:
            await self.initialize()
            
            cutoff_time = datetime.now(datetime.UTC) - max_age
            cutoff_str = cutoff_time.isoformat()
            
            # Get all jobs with terminal statuses
            terminal_statuses = [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
            
            jobs_to_delete = []
            for status in terminal_statuses:
                status_key = self._get_status_index_key(status)
                job_ids = await self._redis.smembers(status_key)
                
                for job_id in job_ids:
                    job_key = self._get_job_key(job_id)
                    updated_at = await self._redis.hget(job_key, "updated_at")
                    
                    if updated_at and updated_at < cutoff_str:
                        jobs_to_delete.append((job_id, status))
            
            # Delete the old jobs
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                for job_id, status in jobs_to_delete:
                    job_key = self._get_job_key(job_id)
                    pipeline.delete(job_key)
                    
                    # Remove from status index
                    status_key = self._get_status_index_key(status)
                    pipeline.srem(status_key, job_id)
                
                await pipeline.execute()
                
                return Result.success(len(jobs_to_delete))
        except Exception as e:
            return Result.failure(f"Failed to clean up old jobs in Redis: {str(e)}")
    
    async def mark_stalled_jobs_as_failed(self, stall_timeout: timedelta) -> Result[int]:
        """Mark stalled jobs as failed.
        
        Args:
            stall_timeout: The time after which a running job is considered stalled.
            
        Returns:
            Result with the number of jobs marked as failed.
        """
        try:
            await self.initialize()
            
            cutoff_time = datetime.now(datetime.UTC) - stall_timeout
            cutoff_str = cutoff_time.isoformat()
            now = datetime.now(datetime.UTC)
            
            # Get all running jobs
            running_key = self._get_status_index_key(JobStatus.RUNNING)
            running_job_ids = await self._redis.smembers(running_key)
            
            stalled_jobs = []
            
            for job_id in running_job_ids:
                job_key = self._get_job_key(job_id)
                updated_at = await self._redis.hget(job_key, "updated_at")
                
                if updated_at and updated_at < cutoff_str:
                    stalled_jobs.append(job_id)
            
            # Mark stalled jobs as failed
            async with self._lock:
                pipeline = self._redis.pipeline()
                
                for job_id in stalled_jobs:
                    job_key = self._get_job_key(job_id)
                    
                    # Update job data
                    pipeline.hset(job_key, "status", JobStatus.FAILED.value)
                    pipeline.hset(job_key, "updated_at", now.isoformat())
                    pipeline.hset(job_key, "completed_at", now.isoformat())
                    pipeline.hset(
                        job_key, 
                        "error", 
                        json.dumps({
                            "message": f"Job stalled and marked as failed after {stall_timeout.total_seconds()} seconds",
                            "type": "StallError",
                        })
                    )
                    
                    # Update status sets
                    pipeline.srem(running_key, job_id)
                    pipeline.sadd(self._get_status_index_key(JobStatus.FAILED), job_id)
                
                await pipeline.execute()
                
                return Result.success(len(stalled_jobs))
        except Exception as e:
            return Result.failure(f"Failed to mark stalled jobs as failed in Redis: {str(e)}")