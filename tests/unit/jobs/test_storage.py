import pytest
from datetime import datetime, timedelta

from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus
from uno.jobs.scheduler.schedules import IntervalSchedule, ScheduleDefinition


class TestInMemoryJobStorage:
    @pytest.mark.asyncio
    async def test_job_crud_operations(self, memory_storage):
        """Test basic CRUD operations for jobs."""
        # Create a job
        job = Job.create(
            task_name="test_task",
            queue_name="test",
            args=["arg1", "arg2"],
            kwargs={"key1": "value1"},
            priority=Priority.NORMAL,
        )
        
        # Add the job
        add_result = await memory_storage.add_job(job)
        assert add_result.is_success is True
        assert add_result.value == job.id
        
        # Get the job
        get_result = await memory_storage.get_job(job.id)
        assert get_result.is_success is True
        assert get_result.value is not None
        assert get_result.value.id == job.id
        assert get_result.value.task_name == "test_task"
        
        # Update the job
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        update_result = await memory_storage.update_job(job)
        assert update_result.is_success is True
        assert update_result.value is True
        
        # Verify the update
        get_result = await memory_storage.get_job(job.id)
        assert get_result.value.status == JobStatus.RUNNING
        assert get_result.value.started_at is not None
        
        # Delete the job
        delete_result = await memory_storage.delete_job(job.id)
        assert delete_result.is_success is True
        assert delete_result.value is True
        
        # Verify deletion
        get_result = await memory_storage.get_job(job.id)
        assert get_result.value is None
    
    @pytest.mark.asyncio
    async def test_job_queue_operations(self, memory_storage):
        """Test queue operations for jobs."""
        # Create jobs with different priorities
        high_job = Job.create(
            task_name="test_task",
            queue_name="test",
            priority=Priority.HIGH,
        )
        
        normal_job = Job.create(
            task_name="test_task",
            queue_name="test",
            priority=Priority.NORMAL,
        )
        
        low_job = Job.create(
            task_name="test_task",
            queue_name="test",
            priority=Priority.LOW,
        )
        
        # Enqueue jobs
        await memory_storage.enqueue_job(high_job)
        await memory_storage.enqueue_job(normal_job)
        await memory_storage.enqueue_job(low_job)
        
        # Check queue length
        length_result = await memory_storage.get_queue_length("test")
        assert length_result.is_success is True
        assert length_result.value == 3
        
        # Dequeue jobs (should come in priority order)
        result1 = await memory_storage.dequeue_job("test")
        assert result1.is_success is True
        assert result1.value.id == high_job.id
        
        result2 = await memory_storage.dequeue_job("test")
        assert result2.is_success is True
        assert result2.value.id == normal_job.id
        
        result3 = await memory_storage.dequeue_job("test")
        assert result3.is_success is True
        assert result3.value.id == low_job.id
        
        # Queue should be empty now
        length_result = await memory_storage.get_queue_length("test")
        assert length_result.value == 0
    
    @pytest.mark.asyncio
    async def test_job_filtering(self, memory_storage):
        """Test filtering jobs by status."""
        # Create jobs with different statuses
        pending_job = Job.create(
            task_name="test_task",
            queue_name="test",
            status=JobStatus.PENDING,
        )
        
        running_job = Job.create(
            task_name="test_task",
            queue_name="test",
            status=JobStatus.RUNNING,
        )
        
        completed_job = Job.create(
            task_name="test_task",
            queue_name="test",
            status=JobStatus.COMPLETED,
        )
        
        failed_job = Job.create(
            task_name="test_task",
            queue_name="test",
            status=JobStatus.FAILED,
        )
        
        # Add jobs to storage
        await memory_storage.add_job(pending_job)
        await memory_storage.add_job(running_job)
        await memory_storage.add_job(completed_job)
        await memory_storage.add_job(failed_job)
        
        # Get jobs by status
        pending_result = await memory_storage.get_jobs_by_status([JobStatus.PENDING])
        assert len(pending_result.value) == 1
        assert pending_result.value[0].id == pending_job.id
        
        running_result = await memory_storage.get_jobs_by_status([JobStatus.RUNNING])
        assert len(running_result.value) == 1
        assert running_result.value[0].id == running_job.id
        
        completed_result = await memory_storage.get_jobs_by_status([JobStatus.COMPLETED])
        assert len(completed_result.value) == 1
        assert completed_result.value[0].id == completed_job.id
        
        failed_result = await memory_storage.get_jobs_by_status([JobStatus.FAILED])
        assert len(failed_result.value) == 1
        assert failed_result.value[0].id == failed_job.id
        
        # Get multiple statuses
        active_result = await memory_storage.get_jobs_by_status([JobStatus.PENDING, JobStatus.RUNNING])
        assert len(active_result.value) == 2
        
        # Filter by queue name
        queue_result = await memory_storage.get_jobs_by_status([JobStatus.PENDING], queue_name="test")
        assert len(queue_result.value) == 1
        
        # Test pagination
        all_result = await memory_storage.get_jobs_by_status(
            [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED],
            limit=2
        )
        assert len(all_result.value) == 2
    
    @pytest.mark.asyncio
    async def test_queue_management(self, memory_storage):
        """Test queue management operations."""
        # Create some pending jobs
        for i in range(5):
            job = Job.create(
                task_name="test_task",
                queue_name="test",
                status=JobStatus.PENDING,
            )
            await memory_storage.add_job(job)
        
        # Pause the queue
        pause_result = await memory_storage.pause_queue("test")
        assert pause_result.is_success is True
        assert pause_result.value is True
        
        # Check that jobs are now paused
        paused_jobs = await memory_storage.get_jobs_by_status([JobStatus.PAUSED], queue_name="test")
        assert len(paused_jobs.value) == 5
        
        # Resume the queue
        resume_result = await memory_storage.resume_queue("test")
        assert resume_result.is_success is True
        assert resume_result.value is True
        
        # Check that jobs are now pending again
        pending_jobs = await memory_storage.get_jobs_by_status([JobStatus.PENDING], queue_name="test")
        assert len(pending_jobs.value) == 5
        
        # Clear the queue
        clear_result = await memory_storage.clear_queue("test")
        assert clear_result.is_success is True
        assert clear_result.value == 5
        
        # Check that there are no pending jobs
        pending_jobs = await memory_storage.get_jobs_by_status([JobStatus.PENDING], queue_name="test")
        assert len(pending_jobs.value) == 0
    
    @pytest.mark.asyncio
    async def test_schedule_operations(self, memory_storage, interval_schedule):
        """Test schedule operations."""
        # Create a schedule
        schedule_def = ScheduleDefinition(
            name="test_schedule",
            task_name="test_task",
            schedule=interval_schedule,
            queue_name="test",
            priority=Priority.NORMAL,
            max_retries=3,
        )
        
        # Add the schedule
        add_result = await memory_storage.add_schedule(schedule_def)
        assert add_result.is_success is True
        schedule_id = add_result.value
        
        # Get the schedule by ID
        get_result = await memory_storage.get_schedule(schedule_id)
        assert get_result.is_success is True
        assert get_result.value is not None
        assert get_result.value.name == "test_schedule"
        
        # Get the schedule by name
        name_result = await memory_storage.get_schedule_by_name("test_schedule")
        assert name_result.is_success is True
        assert name_result.value is not None
        assert name_result.value.id == schedule_id
        
        # Update the schedule
        schedule_def.id = schedule_id
        schedule_def.enabled = False
        update_result = await memory_storage.update_schedule(schedule_def)
        assert update_result.is_success is True
        assert update_result.value is True
        
        # Verify the update
        get_result = await memory_storage.get_schedule(schedule_id)
        assert get_result.value.enabled is False
        
        # Update run times
        now = datetime.utcnow()
        run_time_result = await memory_storage.update_schedule_run_time(
            schedule_id,
            last_run=now,
            next_run=now + timedelta(minutes=5)
        )
        assert run_time_result.is_success is True
        assert run_time_result.value is True
        
        # Verify run time update
        get_result = await memory_storage.get_schedule(schedule_id)
        assert get_result.value.last_run_at == now
        assert get_result.value.next_run_at > now
        
        # Get all schedules
        all_result = await memory_storage.get_all_schedules()
        assert all_result.is_success is True
        assert len(all_result.value) == 1
        
        # Get due schedules (shouldn't be due yet)
        due_result = await memory_storage.get_due_schedules()
        assert due_result.is_success is True
        assert len(due_result.value) == 0
        
        # Update to make it due
        run_time_result = await memory_storage.update_schedule_run_time(
            schedule_id,
            last_run=now - timedelta(minutes=10),
            next_run=now - timedelta(minutes=5)
        )
        
        # Now it should be due
        due_result = await memory_storage.get_due_schedules()
        assert len(due_result.value) == 1
        
        # Delete the schedule
        delete_result = await memory_storage.delete_schedule(schedule_id)
        assert delete_result.is_success is True
        assert delete_result.value is True
        
        # Verify deletion
        get_result = await memory_storage.get_schedule(schedule_id)
        assert get_result.value is None