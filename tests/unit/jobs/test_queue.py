import pytest
import asyncio
from datetime import datetime, timedelta

from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus
from uno.jobs.queue.queue import JobQueue


class TestJobQueue:
    @pytest.mark.asyncio
    async def test_enqueue_job(self, job_queue, memory_storage):
        """Test enqueueing a job."""
        # Test enqueueing with job object
        job = Job.create(
            task_name="test_task",
            queue_name="test",
            args=["arg1", "arg2"],
            kwargs={"key1": "value1"},
            priority=Priority.NORMAL,
        )
        
        result = await job_queue.enqueue_job(job)
        assert result.is_success is True
        assert result.value is True
        
        # Verify the job was added to storage
        get_result = await memory_storage.get_job(job.id)
        assert get_result.is_success is True
        assert get_result.value is not None
        assert get_result.value.id == job.id
        assert get_result.value.status == JobStatus.PENDING
        
        # Test enqueueing with parameters
        result = await job_queue.enqueue(
            task_name="test_task2",
            args=["arg3", "arg4"],
            kwargs={"key2": "value2"},
            priority=Priority.HIGH,
        )
        
        assert result.is_success is True
        assert result.value is not None
        
        # Verify the job was added to storage
        get_result = await memory_storage.get_job(result.value)
        assert get_result.is_success is True
        assert get_result.value is not None
        assert get_result.value.task_name == "test_task2"
        assert get_result.value.args == ["arg3", "arg4"]
        assert get_result.value.kwargs == {"key2": "value2"}
        assert get_result.value.priority == Priority.HIGH
    
    @pytest.mark.asyncio
    async def test_dequeue_job(self, job_queue, memory_storage):
        """Test dequeueing a job."""
        # Enqueue multiple jobs with different priorities
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
        
        await job_queue.enqueue_job(high_job)
        await job_queue.enqueue_job(normal_job)
        await job_queue.enqueue_job(low_job)
        
        # Dequeue jobs - should come in priority order
        result1 = await job_queue.dequeue()
        assert result1.is_success is True
        assert result1.value is not None
        assert result1.value.id == high_job.id
        assert result1.value.status == JobStatus.RUNNING
        
        result2 = await job_queue.dequeue()
        assert result2.is_success is True
        assert result2.value is not None
        assert result2.value.id == normal_job.id
        assert result2.value.status == JobStatus.RUNNING
        
        result3 = await job_queue.dequeue()
        assert result3.is_success is True
        assert result3.value is not None
        assert result3.value.id == low_job.id
        assert result3.value.status == JobStatus.RUNNING
        
        # No more jobs to dequeue
        result4 = await job_queue.dequeue()
        assert result4.is_success is True
        assert result4.value is None
    
    @pytest.mark.asyncio
    async def test_scheduled_jobs(self, job_queue, memory_storage):
        """Test jobs scheduled for the future."""
        now = datetime.utcnow()
        
        # Create a job scheduled for the future
        future_job = Job.create(
            task_name="test_task",
            queue_name="test",
            scheduled_at=now + timedelta(hours=1),
        )
        
        # Create a job scheduled for the past
        past_job = Job.create(
            task_name="test_task",
            queue_name="test",
            scheduled_at=now - timedelta(hours=1),
        )
        
        await job_queue.enqueue_job(future_job)
        await job_queue.enqueue_job(past_job)
        
        # Should only dequeue the past job
        result = await job_queue.dequeue()
        assert result.is_success is True
        assert result.value is not None
        assert result.value.id == past_job.id
        
        # The future job should not be dequeued
        result = await job_queue.dequeue()
        assert result.is_success is True
        assert result.value is None
    
    @pytest.mark.asyncio
    async def test_job_completion(self, job_queue, memory_storage):
        """Test marking a job as completed."""
        job = Job.create(
            task_name="test_task",
            queue_name="test",
        )
        
        await job_queue.enqueue_job(job)
        
        # Dequeue the job
        result = await job_queue.dequeue()
        dequeued_job = result.value
        
        # Mark the job as completed
        complete_result = await job_queue.complete_job(
            dequeued_job.id,
            result={"success": True, "data": "test data"},
        )
        
        assert complete_result.is_success is True
        assert complete_result.value is True
        
        # Verify the job status
        get_result = await memory_storage.get_job(job.id)
        completed_job = get_result.value
        
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.result == {"success": True, "data": "test data"}
        assert completed_job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_job_failure(self, job_queue, memory_storage):
        """Test marking a job as failed."""
        job = Job.create(
            task_name="test_task",
            queue_name="test",
            max_retries=3,
        )
        
        await job_queue.enqueue_job(job)
        
        # Dequeue the job
        result = await job_queue.dequeue()
        dequeued_job = result.value
        
        # Mark the job as failed
        error = {
            "message": "Test error",
            "type": "TestError",
            "traceback": "Traceback information",
        }
        
        fail_result = await job_queue.fail_job(dequeued_job.id, error=error)
        assert fail_result.is_success is True
        assert fail_result.value is True
        
        # Verify the job status
        get_result = await memory_storage.get_job(job.id)
        failed_job = get_result.value
        
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error == error
        assert failed_job.completed_at is not None
        assert failed_job.retries == 1  # Retry count should be incremented
    
    @pytest.mark.asyncio
    async def test_queue_management(self, job_queue, memory_storage):
        """Test queue management operations."""
        # Add some jobs
        for i in range(5):
            job = Job.create(
                task_name="test_task",
                queue_name="test",
            )
            await job_queue.enqueue_job(job)
        
        # Check queue length
        length_result = await job_queue.get_length()
        assert length_result.is_success is True
        assert length_result.value == 5
        
        # Pause the queue
        pause_result = await job_queue.pause()
        assert pause_result.is_success is True
        assert pause_result.value is True
        
        # Check that no jobs can be dequeued when paused
        dequeue_result = await job_queue.dequeue()
        assert dequeue_result.is_success is True
        assert dequeue_result.value is None
        
        # Resume the queue
        resume_result = await job_queue.resume()
        assert resume_result.is_success is True
        assert resume_result.value is True
        
        # Check that jobs can be dequeued again
        dequeue_result = await job_queue.dequeue()
        assert dequeue_result.is_success is True
        assert dequeue_result.value is not None
        
        # Clear the queue
        clear_result = await job_queue.clear()
        assert clear_result.is_success is True
        assert clear_result.value > 0  # Should have cleared at least one job
        
        # Check queue is empty
        length_result = await job_queue.get_length()
        assert length_result.is_success is True
        assert length_result.value == 0