import pytest
import asyncio
from datetime import datetime, timedelta

from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus


class TestJobManager:
    @pytest.mark.asyncio
    async def test_job_manager_lifecycle(self, job_manager):
        """Test job manager start and stop."""
        try:
            # Start the job manager
            await job_manager.start()
            assert job_manager.running is True
            assert len(job_manager.workers) > 0
            
            # All workers should be running
            for worker in job_manager.workers:
                assert worker.running is True
            
            # Scheduler should be running
            assert job_manager.scheduler.running is True
            
            # Stop the job manager
            await job_manager.stop()
            assert job_manager.running is False
            
            # All workers should be stopped
            for worker in job_manager.workers:
                assert worker.running is False
            
            # Scheduler should be stopped
            assert job_manager.scheduler.running is False
        finally:
            # Make sure to stop if test fails
            if job_manager.running:
                await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_job_enqueuing(self, job_manager, register_test_task):
        """Test enqueueing jobs through the manager."""
        try:
            await job_manager.start()
            
            # Enqueue a job
            result = await job_manager.enqueue(
                task_name="test_task",
                args=["arg1", "arg2"],
                kwargs={"key1": "value1"},
                queue_name="test",
                priority=Priority.HIGH,
            )
            
            assert result.is_success is True
            job_id = result.value
            
            # Get the job
            job_result = await job_manager.get_job(job_id)
            assert job_result.is_success is True
            job = job_result.value
            
            assert job is not None
            assert job.task_name == "test_task"
            assert job.args == ["arg1", "arg2"]
            assert job.kwargs == {"key1": "value1"}
            assert job.queue_name == "test"
            assert job.priority == Priority.HIGH
        finally:
            await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_job_execution(self, job_manager, register_test_task):
        """Test job execution through the manager."""
        try:
            await job_manager.start()
            
            # Enqueue a job
            result = await job_manager.enqueue(
                task_name="test_task",
                args=["arg1", "arg2"],
                kwargs={"key1": "value1"},
                queue_name="test",
            )
            
            assert result.is_success is True
            job_id = result.value
            
            # Wait for job to be processed
            max_wait = 10  # Maximum seconds to wait
            for _ in range(max_wait * 2):
                job_result = await job_manager.get_job(job_id)
                job = job_result.value
                
                if job.status == JobStatus.COMPLETED:
                    break
                
                await asyncio.sleep(0.5)
            
            # Check that job was completed
            assert job.status == JobStatus.COMPLETED
            assert job.result is not None
            assert job.result["result"] == "success"
            assert job.result["args"] == ["arg1", "arg2"]
            assert job.result["kwargs"] == {"key1": "value1"}
        finally:
            await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_job_cancellation(self, job_manager, register_test_task):
        """Test job cancellation."""
        try:
            await job_manager.start()
            
            # Enqueue a job for the future
            future_time = datetime.utcnow() + timedelta(hours=1)
            result = await job_manager.enqueue(
                task_name="test_task",
                scheduled_at=future_time,
                queue_name="test",
            )
            
            assert result.is_success is True
            job_id = result.value
            
            # Cancel the job
            cancel_result = await job_manager.cancel_job(job_id)
            assert cancel_result.is_success is True
            assert cancel_result.value is True
            
            # Check that job is cancelled
            job_result = await job_manager.get_job(job_id)
            job = job_result.value
            assert job.status == JobStatus.CANCELLED
        finally:
            await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_job_retry(self, job_manager, register_test_task):
        """Test retrying a failed job."""
        try:
            await job_manager.start()
            
            # Register a failing task
            async def failing_task(*args, **kwargs):
                raise Exception("Test error")
            
            job_manager.register_task(
                name="failing_task",
                handler=failing_task,
                description="Task that fails",
                max_retries=1,  # Only retry once
            )
            
            # Enqueue the failing job
            result = await job_manager.enqueue(
                task_name="failing_task",
                queue_name="test",
            )
            
            assert result.is_success is True
            job_id = result.value
            
            # Wait for job to fail
            max_wait = 10  # Maximum seconds to wait
            for _ in range(max_wait * 2):
                job_result = await job_manager.get_job(job_id)
                job = job_result.value
                
                if job.status == JobStatus.FAILED and job.retries >= 1:
                    break
                
                await asyncio.sleep(0.5)
            
            # Check that job failed and was retried
            assert job.status == JobStatus.FAILED
            assert job.retries >= 1
            assert job.error is not None
            
            # Manually retry the job
            retry_result = await job_manager.retry_job(job_id)
            assert retry_result.is_success is True
            assert retry_result.value is True
            
            # Check that job status is now pending
            job_result = await job_manager.get_job(job_id)
            job = job_result.value
            assert job.status == JobStatus.PENDING
        finally:
            await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_queue_management(self, job_manager, register_test_task):
        """Test queue management operations."""
        try:
            await job_manager.start()
            
            # Enqueue some jobs
            for i in range(5):
                await job_manager.enqueue(
                    task_name="test_task",
                    queue_name="test",
                )
            
            # Check queue length
            length_result = await job_manager.get_queue_length("test")
            assert length_result.is_success is True
            assert length_result.value > 0
            
            # Pause the queue
            pause_result = await job_manager.pause_queue("test")
            assert pause_result.is_success is True
            assert pause_result.value is True
            
            # Resume the queue
            resume_result = await job_manager.resume_queue("test")
            assert resume_result.is_success is True
            assert resume_result.value is True
            
            # Clear the queue
            clear_result = await job_manager.clear_queue("test")
            assert clear_result.is_success is True
            assert clear_result.value > 0
            
            # Queue should be empty now
            length_result = await job_manager.get_queue_length("test")
            assert length_result.value == 0
        finally:
            await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_job_filtering(self, job_manager, register_test_task):
        """Test getting jobs by status."""
        try:
            await job_manager.start()
            
            # Enqueue a normal job
            result1 = await job_manager.enqueue(
                task_name="test_task",
                queue_name="test",
            )
            
            # Enqueue a future job
            future_time = datetime.utcnow() + timedelta(hours=1)
            result2 = await job_manager.enqueue(
                task_name="test_task",
                scheduled_at=future_time,
                queue_name="test",
            )
            
            # Enqueue a job and immediately cancel it
            result3 = await job_manager.enqueue(
                task_name="test_task",
                queue_name="test",
            )
            await job_manager.cancel_job(result3.value)
            
            # Get pending jobs
            pending_result = await job_manager.get_pending_jobs()
            assert pending_result.is_success is True
            assert len(pending_result.value) > 0
            
            # Get cancelled jobs
            cancelled_result = await job_manager.storage.get_jobs_by_status([JobStatus.CANCELLED])
            assert cancelled_result.is_success is True
            assert len(cancelled_result.value) > 0
            
            # Wait for job1 to complete
            max_wait = 10  # Maximum seconds to wait
            for _ in range(max_wait * 2):
                job_result = await job_manager.get_job(result1.value)
                job = job_result.value
                
                if job.status == JobStatus.COMPLETED:
                    break
                
                await asyncio.sleep(0.5)
            
            # Get completed jobs
            completed_result = await job_manager.get_completed_jobs()
            assert completed_result.is_success is True
            assert len(completed_result.value) > 0
        finally:
            await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_run_job_sync(self, job_manager, register_test_task):
        """Test running a job synchronously."""
        try:
            # No need to start the job manager for synchronous execution
            
            # Run a job synchronously
            result = await job_manager.run_job_sync(
                task_name="test_task",
                args=["arg1", "arg2"],
                kwargs={"key1": "value1"},
            )
            
            assert result.is_success is True
            assert result.value is not None
            assert result.value["result"] == "success"
            assert result.value["args"] == ["arg1", "arg2"]
            assert result.value["kwargs"] == {"key1": "value1"}
        finally:
            if job_manager.running:
                await job_manager.stop()
    
    @pytest.mark.asyncio
    async def test_task_registration(self, job_manager):
        """Test task registration."""
        # Register a task using the decorator
        @job_manager.task(
            name="decorated_task",
            description="Task registered with decorator",
            max_retries=5,
            queue="custom",
        )
        async def decorated_task(*args, **kwargs):
            return {"success": True}
        
        # Register a task directly
        async def direct_task(*args, **kwargs):
            return {"success": True}
            
        job_manager.register_task(
            name="direct_task",
            handler=direct_task,
            description="Task registered directly",
        )
        
        # Verify tasks are registered
        from uno.jobs.tasks.task import TaskRegistry
        
        assert "decorated_task" in TaskRegistry._tasks
        assert "direct_task" in TaskRegistry._tasks
        
        decorated_task_obj = TaskRegistry._tasks["decorated_task"]
        assert decorated_task_obj.description == "Task registered with decorator"
        assert decorated_task_obj.default_max_retries == 5
        assert decorated_task_obj.default_queue == "custom"
        
        direct_task_obj = TaskRegistry._tasks["direct_task"]
        assert direct_task_obj.description == "Task registered directly"