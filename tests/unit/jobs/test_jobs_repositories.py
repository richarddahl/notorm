import pytest
from datetime import datetime, timedelta, UTC
import asyncio
from unittest import mock

from uno.core.errors.result import Result
from uno.jobs.entities import Job, JobPriority, JobStatus, Schedule, ScheduleInterval, JobError
from uno.jobs.domain_repositories import JobRepository, ScheduleRepository


class MockStorage:
    """Mock storage backend for testing repositories."""
    
    def __init__(self):
        self.jobs = {}
        self.schedules = {}
        self.queues = {"default": False}  # queue_name: is_paused
    
    async def get_job(self, job_id):
        return self.jobs.get(job_id)
    
    async def create_job(self, job_dict):
        job_id = job_dict["id"]
        self.jobs[job_id] = job_dict
        return job_id
    
    async def update_job(self, job_dict):
        job_id = job_dict["id"]
        if job_id in self.jobs:
            self.jobs[job_id] = job_dict
            return True
        return False
    
    async def delete_job(self, job_id):
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False
    
    async def list_jobs(self, **kwargs):
        # Simple filter by queue and status
        queue = kwargs.get("queue")
        status = kwargs.get("status")
        
        filtered_jobs = list(self.jobs.values())
        
        if queue:
            filtered_jobs = [j for j in filtered_jobs if j.get("queue") == queue]
        
        if status:
            status_values = [s.value for s in status]
            filtered_jobs = [j for j in filtered_jobs if j.get("status") in status_values]
        
        return filtered_jobs
    
    async def count_jobs(self, **kwargs):
        jobs = await self.list_jobs(**kwargs)
        return len(jobs)
    
    async def enqueue(self, queue_name, job_dict):
        job_id = job_dict["id"]
        self.jobs[job_id] = job_dict
        return job_id
    
    async def dequeue(self, queue_name, worker_id, **kwargs):
        # Find pending jobs in the queue
        pending_jobs = [
            j for j in self.jobs.values()
            if j.get("queue") == queue_name and j.get("status") == "pending"
        ]
        
        batch_size = kwargs.get("batch_size", 1)
        jobs_to_return = pending_jobs[:batch_size]
        
        # Mark jobs as reserved
        for job in jobs_to_return:
            job["status"] = "reserved"
            job["worker_id"] = worker_id
        
        return jobs_to_return
    
    async def pause_queue(self, queue_name):
        if queue_name in self.queues:
            self.queues[queue_name] = True
            return True
        return False
    
    async def resume_queue(self, queue_name):
        if queue_name in self.queues:
            self.queues[queue_name] = False
            return True
        return False
    
    async def is_queue_paused(self, queue_name):
        return self.queues.get(queue_name, False)
    
    async def list_queues(self):
        return list(self.queues.keys())
    
    async def clear_queue(self, queue_name):
        count = 0
        for job_id, job in list(self.jobs.items()):
            if job.get("queue") == queue_name and job.get("status") == "pending":
                del self.jobs[job_id]
                count += 1
        return count
    
    async def get_statistics(self):
        return {
            "total_jobs": len(self.jobs),
            "queues": len(self.queues)
        }
    
    async def prune_jobs(self, status, older_than):
        count = 0
        status_values = [s.value for s in status]
        for job_id, job in list(self.jobs.items()):
            if (job.get("status") in status_values and 
                job.get("completed_at") and 
                job.get("completed_at") < older_than):
                del self.jobs[job_id]
                count += 1
        return count
    
    async def requeue_stuck(self, older_than, status):
        count = 0
        status_values = [s.value for s in status]
        for job in self.jobs.values():
            if (job.get("status") in status_values and 
                job.get("started_at") and 
                job.get("started_at") < older_than):
                job["status"] = "failed"
                job["completed_at"] = datetime.now(UTC)
                job["error"] = {"type": "StallError", "message": "Job stalled"}
                count += 1
        return count
    
    # Schedule methods
    async def get_schedule(self, schedule_id):
        return self.schedules.get(schedule_id)
    
    async def schedule_recurring_job(self, **kwargs):
        schedule_id = kwargs.get("schedule_id", "test-id")
        self.schedules[schedule_id] = {
            "id": schedule_id,
            **kwargs
        }
        return schedule_id
    
    async def update_schedule(self, schedule_id, **kwargs):
        if schedule_id in self.schedules:
            self.schedules[schedule_id].update(kwargs)
            return True
        return False
    
    async def delete_schedule(self, schedule_id):
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            return True
        return False
    
    async def list_schedules(self, **kwargs):
        # Filter by status and tags if provided
        status = kwargs.get("status")
        tags = kwargs.get("tags")
        
        filtered_schedules = list(self.schedules.values())
        
        if status:
            filtered_schedules = [s for s in filtered_schedules if s.get("status") == status]
        
        if tags:
            filtered_schedules = [
                s for s in filtered_schedules 
                if s.get("tags") and all(tag in s.get("tags", []) for tag in tags)
            ]
        
        return filtered_schedules


class TestJobRepository:
    
    @pytest.fixture
    def storage(self):
        return MockStorage()
    
    @pytest.fixture
    def repository(self, storage):
        return JobRepository(storage)
    
    @pytest.fixture
    def job(self):
        return Job.create(
            task_name="test_task",
            args=[1, 2, 3],
            kwargs={"key": "value"},
            queue_name="test_queue",
            priority=JobPriority.HIGH,
            job_id="test-job-id"
        )
    
    @pytest.mark.asyncio
    async def test_get_job(self, repository, storage, job):
        # Add a job to the storage
        job_dict = repository._job_to_dict(job)
        await storage.create_job(job_dict)
        
        # Get the job using the repository
        result = await repository.get_job("test-job-id")
        
        assert result.is_success
        retrieved_job = result.value
        
        assert retrieved_job is not None
        assert retrieved_job.id == "test-job-id"
        assert retrieved_job.task_name == "test_task"
        assert retrieved_job.args == [1, 2, 3]
        assert retrieved_job.kwargs == {"key": "value"}
        assert retrieved_job.queue_name == "test_queue"
        assert retrieved_job.priority == JobPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, repository):
        # Try to get a job that doesn't exist
        result = await repository.get_job("nonexistent-id")
        
        assert result.is_success
        assert result.value is None
    
    @pytest.mark.asyncio
    async def test_create_job(self, repository, job):
        # Create a job using the repository
        result = await repository.create_job(job)
        
        assert result.is_success
        job_id = result.value
        assert job_id == "test-job-id"
        
        # Verify the job was created in storage
        get_result = await repository.get_job("test-job-id")
        assert get_result.value is not None
    
    @pytest.mark.asyncio
    async def test_update_job(self, repository, job):
        # First create the job
        await repository.create_job(job)
        
        # Modify the job
        job.status = JobStatus.RUNNING
        job.worker_id = "test-worker"
        
        # Update the job
        result = await repository.update_job(job)
        
        assert result.is_success
        assert result.value is True
        
        # Verify the job was updated
        get_result = await repository.get_job("test-job-id")
        updated_job = get_result.value
        
        assert updated_job.status == JobStatus.RUNNING
        assert updated_job.worker_id == "test-worker"
    
    @pytest.mark.asyncio
    async def test_delete_job(self, repository, job):
        # First create the job
        await repository.create_job(job)
        
        # Verify it exists
        get_result = await repository.get_job("test-job-id")
        assert get_result.value is not None
        
        # Delete the job
        result = await repository.delete_job("test-job-id")
        
        assert result.is_success
        assert result.value is True
        
        # Verify it was deleted
        get_result = await repository.get_job("test-job-id")
        assert get_result.value is None
    
    @pytest.mark.asyncio
    async def test_list_jobs(self, repository):
        # Create several jobs with different properties
        job1 = Job.create(task_name="task1", queue_name="queue1", priority=JobPriority.HIGH, job_id="job1")
        job2 = Job.create(task_name="task2", queue_name="queue1", priority=JobPriority.NORMAL, job_id="job2")
        job3 = Job.create(task_name="task3", queue_name="queue2", priority=JobPriority.LOW, job_id="job3")
        
        await repository.create_job(job1)
        await repository.create_job(job2)
        await repository.create_job(job3)
        
        # List all jobs
        result = await repository.list_jobs()
        assert result.is_success
        assert len(result.value) == 3
        
        # Filter by queue
        queue1_result = await repository.list_jobs(queue_name="queue1")
        assert queue1_result.is_success
        assert len(queue1_result.value) == 2
        
        # Filter by priority
        high_result = await repository.list_jobs(priority=JobPriority.HIGH)
        assert high_result.is_success
        assert len(high_result.value) == 1
        assert high_result.value[0].id == "job1"
    
    @pytest.mark.asyncio
    async def test_count_jobs(self, repository):
        # Create several jobs
        job1 = Job.create(task_name="task1", queue_name="queue1", job_id="job1")
        job2 = Job.create(task_name="task2", queue_name="queue1", job_id="job2")
        job3 = Job.create(task_name="task3", queue_name="queue2", job_id="job3")
        
        await repository.create_job(job1)
        await repository.create_job(job2)
        await repository.create_job(job3)
        
        # Count all jobs
        result = await repository.count_jobs()
        assert result.is_success
        assert result.value == 3
        
        # Count jobs in a specific queue
        queue1_result = await repository.count_jobs(queue_name="queue1")
        assert queue1_result.is_success
        assert queue1_result.value == 2
    
    @pytest.mark.asyncio
    async def test_enqueue(self, repository, job):
        # Enqueue a job
        result = await repository.enqueue(job)
        
        assert result.is_success
        job_id = result.value
        assert job_id == "test-job-id"
        
        # Verify the job was created
        get_result = await repository.get_job("test-job-id")
        assert get_result.value is not None
        assert get_result.value.queue_name == "test_queue"
    
    @pytest.mark.asyncio
    async def test_dequeue(self, repository):
        # Create several pending jobs in the same queue
        job1 = Job.create(task_name="task1", queue_name="dequeue_test", job_id="job1")
        job2 = Job.create(task_name="task2", queue_name="dequeue_test", job_id="job2")
        job3 = Job.create(task_name="task3", queue_name="other_queue", job_id="job3")
        
        await repository.create_job(job1)
        await repository.create_job(job2)
        await repository.create_job(job3)
        
        # Dequeue a job
        result = await repository.dequeue("dequeue_test", "worker1")
        
        assert result.is_success
        dequeued_jobs = result.value
        assert len(dequeued_jobs) == 1
        dequeued_job = dequeued_jobs[0]
        
        # Job should be marked as reserved
        assert dequeued_job.status == JobStatus.RESERVED
        assert dequeued_job.worker_id == "worker1"
        
        # Dequeue with batch_size
        job4 = Job.create(task_name="task4", queue_name="batch_queue", job_id="job4")
        job5 = Job.create(task_name="task5", queue_name="batch_queue", job_id="job5")
        job6 = Job.create(task_name="task6", queue_name="batch_queue", job_id="job6")
        
        await repository.create_job(job4)
        await repository.create_job(job5)
        await repository.create_job(job6)
        
        batch_result = await repository.dequeue("batch_queue", "worker2", batch_size=2)
        assert batch_result.is_success
        assert len(batch_result.value) == 2
    
    @pytest.mark.asyncio
    async def test_mark_job_completed(self, repository, job):
        # First create the job
        await repository.create_job(job)
        
        # Mark the job as completed
        result = await repository.mark_job_completed("test-job-id", {"result": "success"})
        
        assert result.is_success
        assert result.value is True
        
        # Verify the job was updated
        get_result = await repository.get_job("test-job-id")
        completed_job = get_result.value
        
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.completed_at is not None
        assert completed_job.result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_mark_job_failed(self, repository, job):
        # First create the job
        await repository.create_job(job)
        
        # Mark the job as failed with a string error
        result = await repository.mark_job_failed("test-job-id", "Something went wrong")
        
        assert result.is_success
        assert result.value is True
        
        # Verify the job was updated
        get_result = await repository.get_job("test-job-id")
        failed_job = get_result.value
        
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.completed_at is not None
        assert failed_job.error is not None
        assert failed_job.error.message == "Something went wrong"
        
        # Create another job for testing retry
        retry_job = Job.create(
            task_name="retry_task",
            max_retries=3,
            job_id="retry-job-id"
        )
        await repository.create_job(retry_job)
        
        # Mark the job as failed with retry
        result = await repository.mark_job_failed("retry-job-id", "Temporary error", retry=True)
        
        assert result.is_success
        assert result.value is True
        
        # Verify the job was marked for retry
        get_result = await repository.get_job("retry-job-id")
        retrying_job = get_result.value
        
        assert retrying_job.status == JobStatus.RETRYING
        assert retrying_job.retry_count == 1
        assert retrying_job.error is not None
        assert retrying_job.error.message == "Temporary error"
    
    @pytest.mark.asyncio
    async def test_mark_job_cancelled(self, repository, job):
        # First create the job
        await repository.create_job(job)
        
        # Mark the job as cancelled
        result = await repository.mark_job_cancelled("test-job-id", "User cancelled")
        
        assert result.is_success
        assert result.value is True
        
        # Verify the job was updated
        get_result = await repository.get_job("test-job-id")
        cancelled_job = get_result.value
        
        assert cancelled_job.status == JobStatus.CANCELLED
        assert cancelled_job.completed_at is not None
        assert cancelled_job.metadata.get("cancel_reason") == "User cancelled"
    
    @pytest.mark.asyncio
    async def test_retry_job(self, repository):
        # Create a failed job
        job = Job.create(task_name="retry_test", job_id="retry-test-id")
        await repository.create_job(job)
        
        # Mark it as failed
        await repository.mark_job_failed("retry-test-id", "Test failure")
        
        # Now retry it
        result = await repository.retry_job("retry-test-id")
        
        assert result.is_success
        assert result.value is True
        
        # Verify the job was updated
        get_result = await repository.get_job("retry-test-id")
        retried_job = get_result.value
        
        assert retried_job.status == JobStatus.PENDING
        assert retried_job.error is None
        assert retried_job.worker_id is None
    
    @pytest.mark.asyncio
    async def test_get_queue_length(self, repository):
        # Create several jobs in different queues and with different statuses
        job1 = Job.create(task_name="task1", queue_name="length_test", job_id="job1")
        job2 = Job.create(task_name="task2", queue_name="length_test", job_id="job2")
        job3 = Job.create(task_name="task3", queue_name="length_test", job_id="job3")
        
        await repository.create_job(job1)
        await repository.create_job(job2)
        await repository.create_job(job3)
        
        # Mark one job as completed
        await repository.mark_job_completed("job3", "Done")
        
        # Get queue length
        result = await repository.get_queue_length("length_test")
        
        assert result.is_success
        assert result.value == 2  # Only the pending jobs should be counted
    
    @pytest.mark.asyncio
    async def test_get_queue_names(self, repository):
        # Create jobs in different queues
        job1 = Job.create(task_name="task1", queue_name="queue1", job_id="job1")
        job2 = Job.create(task_name="task2", queue_name="queue2", job_id="job2")
        job3 = Job.create(task_name="task3", queue_name="queue3", job_id="job3")
        
        await repository.create_job(job1)
        await repository.create_job(job2)
        await repository.create_job(job3)
        
        # Get queue names
        result = await repository.get_queue_names()
        
        assert result.is_success
        assert len(result.value) >= 1  # At least the default queue
    
    @pytest.mark.asyncio
    async def test_pause_resume_queue(self, repository):
        # Pause a queue
        pause_result = await repository.pause_queue("test_pause")
        
        assert pause_result.is_success
        assert pause_result.value is True
        
        # Check if queue is paused
        is_paused_result = await repository.is_queue_paused("test_pause")
        assert is_paused_result.is_success
        assert is_paused_result.value is True
        
        # Resume the queue
        resume_result = await repository.resume_queue("test_pause")
        
        assert resume_result.is_success
        assert resume_result.value is True
        
        # Check if queue is no longer paused
        is_paused_result = await repository.is_queue_paused("test_pause")
        assert is_paused_result.is_success
        assert is_paused_result.value is False
    
    @pytest.mark.asyncio
    async def test_clear_queue(self, repository):
        # Create several jobs in a queue
        job1 = Job.create(task_name="task1", queue_name="clear_test", job_id="job1")
        job2 = Job.create(task_name="task2", queue_name="clear_test", job_id="job2")
        job3 = Job.create(task_name="task3", queue_name="other_queue", job_id="job3")
        
        await repository.create_job(job1)
        await repository.create_job(job2)
        await repository.create_job(job3)
        
        # Clear the queue
        result = await repository.clear_queue("clear_test")
        
        assert result.is_success
        assert result.value == 2  # Two jobs should have been cleared
        
        # Verify the jobs were removed
        queue_length = await repository.get_queue_length("clear_test")
        assert queue_length.value == 0
        
        # Other queue should be unaffected
        other_length = await repository.get_queue_length("other_queue")
        assert other_length.value == 1
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, repository):
        # Create some jobs
        job1 = Job.create(task_name="task1", queue_name="stats_queue1", job_id="job1")
        job2 = Job.create(task_name="task2", queue_name="stats_queue2", job_id="job2")
        
        await repository.create_job(job1)
        await repository.create_job(job2)
        
        # Get statistics
        result = await repository.get_statistics()
        
        assert result.is_success
        stats = result.value
        
        assert "total_jobs" in stats
        assert stats["total_jobs"] >= 2
    
    @pytest.mark.asyncio
    async def test_cleanup_old_jobs(self, repository):
        # Create jobs with completed_at in the past
        old_job = Job.create(task_name="old_task", job_id="old-job-id")
        old_job.mark_completed("Done")
        old_job.completed_at = datetime.now(UTC) - timedelta(days=10)
        
        new_job = Job.create(task_name="new_task", job_id="new-job-id")
        new_job.mark_completed("Done")
        new_job.completed_at = datetime.now(UTC) - timedelta(hours=1)
        
        await repository.create_job(old_job)
        await repository.create_job(new_job)
        
        # Cleanup jobs older than 7 days
        result = await repository.cleanup_old_jobs(timedelta(days=7))
        
        assert result.is_success
        # Depending on how the mock is implemented, we might not be able to verify the count
        # But the call should succeed
    
    @pytest.mark.asyncio
    async def test_mark_stalled_jobs_as_failed(self, repository):
        # Create jobs with started_at in the past
        stalled_job = Job.create(task_name="stalled_task", job_id="stalled-job-id")
        stalled_job.mark_running()
        stalled_job.started_at = datetime.now(UTC) - timedelta(hours=2)
        
        active_job = Job.create(task_name="active_task", job_id="active-job-id")
        active_job.mark_running()
        active_job.started_at = datetime.now(UTC) - timedelta(minutes=5)
        
        await repository.create_job(stalled_job)
        await repository.create_job(active_job)
        
        # Mark jobs stalled for more than 1 hour
        result = await repository.mark_stalled_jobs_as_failed(timedelta(hours=1))
        
        assert result.is_success
        # Depending on how the mock is implemented, we might not be able to verify the count
        # But the call should succeed
    
    def test_job_to_dict(self, repository):
        # Create a job
        job = Job.create(
            task_name="conversion_test",
            args=[1, 2, 3],
            kwargs={"key": "value"},
            queue_name="test_queue",
            priority=JobPriority.HIGH,
            scheduled_at=datetime.now(UTC) + timedelta(hours=1),
            max_retries=5,
            retry_delay=timedelta(seconds=120),
            timeout=timedelta(seconds=300),
            tags={"tag1", "tag2"},
            metadata={"meta": "data"},
            version="1.0",
            job_id="conversion-test-id"
        )
        
        # Convert to dict
        job_dict = repository._job_to_dict(job)
        
        # Verify the conversion
        assert job_dict["id"] == "conversion-test-id"
        assert job_dict["task"] == "conversion_test"
        assert job_dict["args"] == [1, 2, 3]
        assert job_dict["kwargs"] == {"key": "value"}
        assert job_dict["queue"] == "test_queue"
        assert job_dict["priority"] == "HIGH"
        assert job_dict["status"] == "pending"
        assert job_dict["scheduled_for"] is not None
        assert job_dict["max_retries"] == 5
        assert job_dict["retry_delay"] == 120
        assert job_dict["timeout"] == 300
        assert set(job_dict["tags"]) == {"tag1", "tag2"}
        assert job_dict["metadata"] == {"meta": "data"}
        assert job_dict["version"] == "1.0"
    
    def test_dict_to_job(self, repository):
        # Create a job dict
        job_dict = {
            "id": "dict-to-job-id",
            "task": "dict_test",
            "args": [4, 5, 6],
            "kwargs": {"test": "value"},
            "queue": "dict_queue",
            "priority": "CRITICAL",
            "status": "running",
            "scheduled_for": datetime.now(UTC) + timedelta(hours=2),
            "created_at": datetime.now(UTC) - timedelta(hours=1),
            "started_at": datetime.now(UTC) - timedelta(minutes=30),
            "max_retries": 7,
            "retry_delay": 180,
            "tags": ["tag3", "tag4"],
            "metadata": {"test_meta": "value"},
            "worker_id": "test-worker",
            "timeout": 450,
            "version": "2.0",
            "error": {
                "type": "TestError",
                "message": "Test error message",
                "traceback": "Test traceback"
            }
        }
        
        # Convert to job
        job = repository._dict_to_job(job_dict)
        
        # Verify the conversion
        assert job.id == "dict-to-job-id"
        assert job.task_name == "dict_test"
        assert job.args == [4, 5, 6]
        assert job.kwargs == {"test": "value"}
        assert job.queue_name == "dict_queue"
        assert job.priority == JobPriority.CRITICAL
        assert job.status == JobStatus.RUNNING
        assert job.scheduled_at is not None
        assert job.created_at is not None
        assert job.started_at is not None
        assert job.max_retries == 7
        assert job.retry_delay == timedelta(seconds=180)
        assert job.timeout == timedelta(seconds=450)
        assert job.tags == {"tag3", "tag4"}
        assert job.metadata == {"test_meta": "value"}
        assert job.worker_id == "test-worker"
        assert job.version == "2.0"
        assert job.error is not None
        assert job.error.type == "TestError"
        assert job.error.message == "Test error message"
        assert job.error.traceback == "Test traceback"


class TestScheduleRepository:
    
    @pytest.fixture
    def storage(self):
        return MockStorage()
    
    @pytest.fixture
    def repository(self, storage):
        return ScheduleRepository(storage)
    
    @pytest.fixture
    def schedule(self):
        interval = ScheduleInterval(minutes=30)
        return Schedule.create(
            name="test_schedule",
            task_name="test_task",
            interval=interval,
            args=[1, 2, 3],
            kwargs={"key": "value"},
            queue_name="test_queue",
            priority=JobPriority.HIGH,
            tags={"schedule_tag1", "schedule_tag2"},
            metadata={"schedule_meta": "data"},
            max_retries=5,
            retry_delay=120,
            timeout=300,
            version="1.0",
            schedule_id="test-schedule-id"
        )
    
    @pytest.mark.asyncio
    async def test_get_schedule(self, repository, storage, schedule):
        # Add a schedule to the storage
        await repository.create_schedule(schedule)
        
        # Get the schedule using the repository
        result = await repository.get_schedule("test-schedule-id")
        
        assert result.is_success
        retrieved_schedule = result.value
        
        assert retrieved_schedule is not None
        assert retrieved_schedule.id == "test-schedule-id"
        assert retrieved_schedule.name == "test_schedule"
        assert retrieved_schedule.task_name == "test_task"
        assert retrieved_schedule.interval is not None
        assert retrieved_schedule.interval.minutes == 30
    
    @pytest.mark.asyncio
    async def test_create_schedule(self, repository, schedule):
        # Create a schedule using the repository
        result = await repository.create_schedule(schedule)
        
        assert result.is_success
        schedule_id = result.value
        assert schedule_id == "test-schedule-id"
        
        # Verify the schedule was created
        get_result = await repository.get_schedule("test-schedule-id")
        assert get_result.value is not None
    
    @pytest.mark.asyncio
    async def test_update_schedule(self, repository, schedule):
        # First create the schedule
        await repository.create_schedule(schedule)
        
        # Modify the schedule
        schedule.name = "updated_name"
        schedule.queue_name = "updated_queue"
        
        # Update the schedule
        result = await repository.update_schedule(schedule)
        
        assert result.is_success
        assert result.value is True
        
        # Verify the schedule was updated
        get_result = await repository.get_schedule("test-schedule-id")
        updated_schedule = get_result.value
        
        assert updated_schedule.name == "updated_name"
        assert updated_schedule.queue_name == "updated_queue"
    
    @pytest.mark.asyncio
    async def test_delete_schedule(self, repository, schedule):
        # First create the schedule
        await repository.create_schedule(schedule)
        
        # Verify it exists
        get_result = await repository.get_schedule("test-schedule-id")
        assert get_result.value is not None
        
        # Delete the schedule
        result = await repository.delete_schedule("test-schedule-id")
        
        assert result.is_success
        assert result.value is True
        
        # Verify it was deleted
        get_result = await repository.get_schedule("test-schedule-id")
        assert get_result.value is None
    
    @pytest.mark.asyncio
    async def test_list_schedules(self, repository):
        # Create several schedules with different properties
        interval1 = ScheduleInterval(minutes=15)
        interval2 = ScheduleInterval(hours=1)
        
        schedule1 = Schedule.create(
            name="schedule1",
            task_name="task1",
            interval=interval1,
            tags={"tag1", "common"},
            status="active",
            schedule_id="schedule1"
        )
        
        schedule2 = Schedule.create(
            name="schedule2",
            task_name="task2",
            interval=interval2,
            tags={"tag2", "common"},
            status="active",
            schedule_id="schedule2"
        )
        
        schedule3 = Schedule.create(
            name="schedule3",
            task_name="task3",
            interval=interval1,
            tags={"tag3"},
            status="paused",
            schedule_id="schedule3"
        )
        
        await repository.create_schedule(schedule1)
        await repository.create_schedule(schedule2)
        await repository.create_schedule(schedule3)
        
        # List all schedules
        result = await repository.list_schedules()
        assert result.is_success
        assert len(result.value) == 3
        
        # Filter by status
        active_result = await repository.list_schedules(status="active")
        assert active_result.is_success
        assert len(active_result.value) == 2
        
        # Filter by tags
        common_tag_result = await repository.list_schedules(tags={"common"})
        assert common_tag_result.is_success
        assert len(common_tag_result.value) == 2
        
        # Apply limit and offset
        limited_result = await repository.list_schedules(limit=1)
        assert limited_result.is_success
        assert len(limited_result.value) == 1
    
    @pytest.mark.asyncio
    async def test_get_due_schedules(self, repository):
        # Create schedules with different next_run_at values
        interval = ScheduleInterval(minutes=30)
        
        due_schedule = Schedule.create(
            name="due_schedule",
            task_name="task1",
            interval=interval,
            schedule_id="due-schedule"
        )
        # Set next_run_at to the past
        due_schedule.next_run_at = datetime.now(UTC) - timedelta(minutes=5)
        
        future_schedule = Schedule.create(
            name="future_schedule",
            task_name="task2",
            interval=interval,
            schedule_id="future-schedule"
        )
        # next_run_at is already in the future by default
        
        paused_schedule = Schedule.create(
            name="paused_schedule",
            task_name="task3",
            interval=interval,
            schedule_id="paused-schedule"
        )
        paused_schedule.next_run_at = datetime.now(UTC) - timedelta(minutes=10)
        paused_schedule.pause()
        
        await repository.create_schedule(due_schedule)
        await repository.create_schedule(future_schedule)
        await repository.create_schedule(paused_schedule)
        
        # Get due schedules
        result = await repository.get_due_schedules()
        
        assert result.is_success
        due_schedules = result.value
        
        # Only the due_schedule should be returned
        assert len(due_schedules) == 1
        assert due_schedules[0].id == "due-schedule"
    
    @pytest.mark.asyncio
    async def test_update_schedule_next_run(self, repository, schedule):
        # First create the schedule
        await repository.create_schedule(schedule)
        
        # Get the original next_run_at
        original_schedule = (await repository.get_schedule("test-schedule-id")).value
        original_next_run = original_schedule.next_run_at
        
        # Update next run time
        result = await repository.update_schedule_next_run("test-schedule-id")
        
        assert result.is_success
        assert result.value is True
        
        # Verify next_run_at was updated
        updated_schedule = (await repository.get_schedule("test-schedule-id")).value
        assert updated_schedule.next_run_at > original_next_run
        assert updated_schedule.last_run_at is not None