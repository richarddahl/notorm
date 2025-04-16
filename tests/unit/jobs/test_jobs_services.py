import pytest
from datetime import datetime, timedelta, UTC
import asyncio
from unittest import mock
import uuid
import logging

from uno.core.errors.result import Result
from uno.jobs.entities import Job, JobPriority, JobStatus, Schedule, ScheduleInterval, JobError
from uno.jobs.domain_services import TaskRegistryService, JobManagerService
from uno.jobs.domain_repositories import JobRepositoryProtocol, ScheduleRepositoryProtocol


class TestTaskRegistryService:
    
    def setup_method(self):
        self.registry = TaskRegistryService()
    
    def test_register_task(self):
        def test_func(a, b):
            return a + b
        
        self.registry.register_task(
            name="test_task",
            handler=test_func,
            description="Test function",
            timeout=timedelta(seconds=30),
            max_retries=5,
            retry_delay=timedelta(seconds=120),
            queue="test_queue",
            version="1.0"
        )
        
        # Check that task was registered
        task = self.registry.get_task("test_task")
        assert task is not None
        assert task["name"] == "test_task"
        assert task["func"] == test_func
        assert task["description"] == "Test function"
        assert task["is_async"] is False
        assert task["options"]["timeout"] == timedelta(seconds=30)
        assert task["options"]["max_retries"] == 5
        assert task["options"]["retry_delay"] == timedelta(seconds=120)
        assert task["options"]["queue"] == "test_queue"
        assert task["version"] == "1.0"
    
    def test_register_async_task(self):
        async def test_async_func(a, b):
            return a + b
        
        self.registry.register_task(
            name="test_async_task",
            handler=test_async_func
        )
        
        task = self.registry.get_task("test_async_task")
        assert task is not None
        assert task["is_async"] is True
    
    def test_get_task_with_version(self):
        def test_func_v1():
            return "v1"
        
        def test_func_v2():
            return "v2"
        
        self.registry.register_task(
            name="test_task",
            handler=test_func_v1,
            version="1.0"
        )
        
        self.registry.register_task(
            name="test_task",
            handler=test_func_v2,
            version="2.0"
        )
        
        # Get task with specific version
        task_v1 = self.registry.get_task("test_task", version="1.0")
        assert task_v1 is not None
        assert task_v1["func"] == test_func_v1
        
        task_v2 = self.registry.get_task("test_task", version="2.0")
        assert task_v2 is not None
        assert task_v2["func"] == test_func_v2
    
    def test_list_tasks(self):
        self.registry.register_task(name="task1", handler=lambda: "one")
        self.registry.register_task(name="task2", handler=lambda: "two")
        
        tasks = self.registry.list_tasks()
        assert len(tasks) == 2
        assert any(t["name"] == "task1" for t in tasks)
        assert any(t["name"] == "task2" for t in tasks)
    
    def test_import_task(self):
        # Mock the importlib.import_module and getattr
        with mock.patch("importlib.import_module") as mock_import:
            mock_module = mock.MagicMock()
            mock_import.return_value = mock_module
            
            def mock_test_func():
                return "imported"
            
            mock_module.test_func = mock_test_func
            
            # Import a task
            imported_task = self.registry.import_task("module.test_func")
            
            # Verify import was called correctly
            mock_import.assert_called_once_with("module")
            
            # Verify task was registered
            assert imported_task is not None
            assert imported_task["name"] == "module.test_func"
            assert imported_task["func"] == mock_test_func
    
    def test_import_task_failure(self):
        # Test import failure
        with mock.patch("importlib.import_module", side_effect=ImportError("Module not found")):
            imported_task = self.registry.import_task("nonexistent.function")
            assert imported_task is None
        
        # Test attribute failure
        with mock.patch("importlib.import_module") as mock_import:
            mock_module = mock.MagicMock()
            mock_import.return_value = mock_module
            
            # Function doesn't exist on module
            mock_module.configure_mock(**{"__getattr__.side_effect": AttributeError("No such attribute")})
            
            imported_task = self.registry.import_task("module.nonexistent")
            assert imported_task is None
    
    @pytest.mark.asyncio
    async def test_execute_task_sync(self):
        def test_sync_func(a, b):
            return a + b
        
        self.registry.register_task(
            name="test_sync_task",
            handler=test_sync_func
        )
        
        # Execute the task
        result = await self.registry.execute_task(
            task_name="test_sync_task",
            args=[1, 2],
            kwargs={}
        )
        
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_execute_task_async(self):
        async def test_async_func(a, b):
            await asyncio.sleep(0.01)  # Small delay to simulate async work
            return a + b
        
        self.registry.register_task(
            name="test_async_task",
            handler=test_async_func
        )
        
        # Execute the task
        result = await self.registry.execute_task(
            task_name="test_async_task",
            args=[3, 4],
            kwargs={}
        )
        
        assert result == 7
    
    @pytest.mark.asyncio
    async def test_execute_task_not_found(self):
        # Try to execute a task that doesn't exist
        with pytest.raises(ValueError) as exc:
            await self.registry.execute_task(
                task_name="nonexistent_task",
                args=[],
                kwargs={}
            )
        
        assert "Task not found: nonexistent_task" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_execute_task_with_auto_import(self):
        # Setup mocks for import
        with mock.patch("importlib.import_module") as mock_import:
            mock_module = mock.MagicMock()
            mock_import.return_value = mock_module
            
            # Mock a function that we'll "import"
            async def mock_imported_func(x):
                return x * 2
            
            mock_module.imported_func = mock_imported_func
            
            # Execute task that will be auto-imported
            result = await self.registry.execute_task(
                task_name="module.imported_func",
                args=[21],
                kwargs={}
            )
            
            assert result == 42
            mock_import.assert_called_once_with("module")


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
        
        filtered_jobs = self.jobs.values()
        
        if queue:
            filtered_jobs = [j for j in filtered_jobs if j.get("queue") == queue]
        
        if status:
            status_values = [s.value for s in status]
            filtered_jobs = [j for j in filtered_jobs if j.get("status") in status_values]
        
        return list(filtered_jobs)
    
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
        schedule_id = kwargs.get("schedule_id", str(uuid.uuid4()))
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
        
        filtered_schedules = self.schedules.values()
        
        if status:
            filtered_schedules = [s for s in filtered_schedules if s.get("status") == status]
        
        if tags:
            filtered_schedules = [
                s for s in filtered_schedules 
                if s.get("tags") and all(tag in s.get("tags", []) for tag in tags)
            ]
        
        return list(filtered_schedules)


class MockJobRepository:
    """Mock job repository for testing job manager."""
    
    def __init__(self):
        self.jobs = {}
        self.next_job_id = 1
    
    async def get_job(self, job_id):
        if job_id in self.jobs:
            return Result.success(self.jobs[job_id])
        return Result.success(None)
    
    async def create_job(self, job):
        job_id = job.id
        self.jobs[job_id] = job
        return Result.success(job_id)
    
    async def update_job(self, job):
        if job.id in self.jobs:
            self.jobs[job.id] = job
            return Result.success(True)
        return Result.success(False)
    
    async def delete_job(self, job_id):
        if job_id in self.jobs:
            del self.jobs[job_id]
            return Result.success(True)
        return Result.success(False)
    
    async def list_jobs(self, **kwargs):
        # Simple implementation that just returns all jobs
        return Result.success(list(self.jobs.values()))
    
    async def count_jobs(self, **kwargs):
        return Result.success(len(self.jobs))
    
    async def enqueue(self, job):
        job_id = job.id
        self.jobs[job_id] = job
        return Result.success(job_id)
    
    async def dequeue(self, queue_name, worker_id, **kwargs):
        # Find eligible jobs
        eligible_jobs = [
            j for j in self.jobs.values()
            if j.queue_name == queue_name and j.status == JobStatus.PENDING
        ]
        
        batch_size = kwargs.get("batch_size", 1)
        jobs_to_return = eligible_jobs[:batch_size]
        
        # Mark jobs as reserved
        for job in jobs_to_return:
            job.mark_reserved(worker_id)
        
        return Result.success(jobs_to_return)
    
    async def mark_job_completed(self, job_id, result=None):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.mark_completed(result)
            return Result.success(True)
        return Result.failure(f"Job {job_id} not found")
    
    async def mark_job_failed(self, job_id, error, retry=False):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if retry and job.can_retry:
                job.mark_retry(error)
            else:
                job.mark_failed(error)
            return Result.success(True)
        return Result.failure(f"Job {job_id} not found")
    
    async def mark_job_cancelled(self, job_id, reason=None):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.mark_cancelled(reason)
            return Result.success(True)
        return Result.failure(f"Job {job_id} not found")
    
    async def retry_job(self, job_id):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = JobStatus.PENDING
            job.error = None
            job.worker_id = None
            return Result.success(True)
        return Result.failure(f"Job {job_id} not found")
    
    async def get_queue_length(self, queue_name):
        count = sum(1 for j in self.jobs.values() 
                 if j.queue_name == queue_name and j.status == JobStatus.PENDING)
        return Result.success(count)
    
    async def get_queue_names(self):
        queues = set(j.queue_name for j in self.jobs.values())
        return Result.success(queues)
    
    async def pause_queue(self, queue_name):
        # Just return success for testing
        return Result.success(True)
    
    async def resume_queue(self, queue_name):
        # Just return success for testing
        return Result.success(True)
    
    async def is_queue_paused(self, queue_name):
        # Just return False for testing
        return Result.success(False)
    
    async def clear_queue(self, queue_name):
        count = 0
        for job_id, job in list(self.jobs.items()):
            if job.queue_name == queue_name and job.status == JobStatus.PENDING:
                del self.jobs[job_id]
                count += 1
        return Result.success(count)
    
    async def get_statistics(self):
        return Result.success({
            "total_jobs": len(self.jobs)
        })
    
    async def cleanup_old_jobs(self, older_than):
        # Just return a count for testing
        return Result.success(0)
    
    async def mark_stalled_jobs_as_failed(self, older_than):
        # Just return a count for testing
        return Result.success(0)


class MockScheduleRepository:
    """Mock schedule repository for testing job manager."""
    
    def __init__(self):
        self.schedules = {}
    
    async def get_schedule(self, schedule_id):
        if schedule_id in self.schedules:
            return Result.success(self.schedules[schedule_id])
        return Result.success(None)
    
    async def create_schedule(self, schedule):
        schedule_id = schedule.id
        self.schedules[schedule_id] = schedule
        return Result.success(schedule_id)
    
    async def update_schedule(self, schedule):
        if schedule.id in self.schedules:
            self.schedules[schedule.id] = schedule
            return Result.success(True)
        return Result.success(False)
    
    async def delete_schedule(self, schedule_id):
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            return Result.success(True)
        return Result.success(False)
    
    async def list_schedules(self, **kwargs):
        # Simple implementation that just returns all schedules
        return Result.success(list(self.schedules.values()))
    
    async def get_due_schedules(self, limit=100):
        due_schedules = [s for s in self.schedules.values() if s.is_due()]
        return Result.success(due_schedules[:limit])
    
    async def update_schedule_next_run(self, schedule_id):
        if schedule_id in self.schedules:
            schedule = self.schedules[schedule_id]
            schedule.update_next_run()
            return Result.success(True)
        return Result.failure(f"Schedule {schedule_id} not found")


class TestJobManagerService:
    
    @pytest.fixture
    def job_manager(self):
        job_repo = MockJobRepository()
        schedule_repo = MockScheduleRepository()
        task_registry = TaskRegistryService()
        
        # Register some test tasks
        def test_task(a, b):
            return a + b
        
        async def test_async_task(a, b):
            await asyncio.sleep(0.01)
            return a + b
        
        task_registry.register_task(name="test_task", handler=test_task)
        task_registry.register_task(name="test_async_task", handler=test_async_task)
        
        manager = JobManagerService(
            job_repository=job_repo,
            schedule_repository=schedule_repo,
            task_registry=task_registry,
            logger=logging.getLogger("test")
        )
        
        return manager
    
    @pytest.mark.asyncio
    async def test_enqueue(self, job_manager):
        # Enqueue a job
        result = await job_manager.enqueue(
            task_name="test_task",
            args=[1, 2],
            kwargs={"key": "value"},
            queue_name="test_queue",
            priority=JobPriority.HIGH
        )
        
        assert result.is_success
        job_id = result.value
        assert job_id is not None
        
        # Verify job was created
        job_result = await job_manager.get_job(job_id)
        assert job_result.is_success
        job = job_result.value
        
        assert job is not None
        assert job.task_name == "test_task"
        assert job.args == [1, 2]
        assert job.kwargs == {"key": "value"}
        assert job.queue_name == "test_queue"
        assert job.priority == JobPriority.HIGH
        assert job.status == JobStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_enqueue_nonexistent_task(self, job_manager):
        # Try to enqueue a job with a task that doesn't exist
        result = await job_manager.enqueue(
            task_name="nonexistent_task"
        )
        
        assert not result.is_success
        assert "Task not found" in result.error
    
    @pytest.mark.asyncio
    async def test_get_job(self, job_manager):
        # First enqueue a job
        enqueue_result = await job_manager.enqueue(task_name="test_task")
        assert enqueue_result.is_success
        job_id = enqueue_result.value
        
        # Get the job
        get_result = await job_manager.get_job(job_id)
        assert get_result.is_success
        job = get_result.value
        
        assert job is not None
        assert job.id == job_id
        assert job.task_name == "test_task"
    
    @pytest.mark.asyncio
    async def test_cancel_job(self, job_manager):
        # Enqueue a job
        enqueue_result = await job_manager.enqueue(task_name="test_task")
        assert enqueue_result.is_success
        job_id = enqueue_result.value
        
        # Cancel the job
        cancel_result = await job_manager.cancel_job(job_id, reason="Testing cancellation")
        assert cancel_result.is_success
        assert cancel_result.value is True
        
        # Verify job status
        job_result = await job_manager.get_job(job_id)
        job = job_result.value
        
        assert job.status == JobStatus.CANCELLED
        assert job.metadata.get("cancel_reason") == "Testing cancellation"
    
    @pytest.mark.asyncio
    async def test_retry_job(self, job_manager):
        # Enqueue a job
        enqueue_result = await job_manager.enqueue(task_name="test_task")
        assert enqueue_result.is_success
        job_id = enqueue_result.value
        
        # Mark the job as failed
        job_result = await job_manager.get_job(job_id)
        job = job_result.value
        job.mark_failed("Test failure")
        await job_manager.job_repository.update_job(job)
        
        # Retry the job
        retry_result = await job_manager.retry_job(job_id)
        assert retry_result.is_success
        assert retry_result.value is True
        
        # Verify job status
        job_result = await job_manager.get_job(job_id)
        job = job_result.value
        
        assert job.status == JobStatus.PENDING
        assert job.error is None
    
    @pytest.mark.asyncio
    async def test_queue_operations(self, job_manager):
        # Enqueue some jobs
        await job_manager.enqueue(task_name="test_task", queue_name="queue1")
        await job_manager.enqueue(task_name="test_task", queue_name="queue1")
        await job_manager.enqueue(task_name="test_task", queue_name="queue2")
        
        # Test get_queue_length
        queue1_length = await job_manager.get_queue_length("queue1")
        assert queue1_length.is_success
        assert queue1_length.value == 2
        
        queue2_length = await job_manager.get_queue_length("queue2")
        assert queue2_length.is_success
        assert queue2_length.value == 1
        
        # Test get_queue_names
        queue_names = await job_manager.get_queue_names()
        assert queue_names.is_success
        assert "queue1" in queue_names.value
        assert "queue2" in queue_names.value
        
        # Test pause_queue and resume_queue
        pause_result = await job_manager.pause_queue("queue1")
        assert pause_result.is_success
        
        resume_result = await job_manager.resume_queue("queue1")
        assert resume_result.is_success
        
        # Test clear_queue
        clear_result = await job_manager.clear_queue("queue1")
        assert clear_result.is_success
        assert clear_result.value == 2  # Should have removed 2 jobs
        
        queue1_length = await job_manager.get_queue_length("queue1")
        assert queue1_length.value == 0
    
    @pytest.mark.asyncio
    async def test_get_jobs_by_status(self, job_manager):
        # Create jobs with different statuses
        job1_id = (await job_manager.enqueue(task_name="test_task")).value
        job2_id = (await job_manager.enqueue(task_name="test_task")).value
        job3_id = (await job_manager.enqueue(task_name="test_task")).value
        job4_id = (await job_manager.enqueue(task_name="test_task")).value
        
        # Mark jobs with different statuses
        await job_manager.job_repository.mark_job_completed(job1_id, "result1")
        await job_manager.job_repository.mark_job_failed(job2_id, "error1")
        # job3 stays pending
        job4_result = await job_manager.get_job(job4_id)
        job4 = job4_result.value
        job4.mark_running()
        await job_manager.job_repository.update_job(job4)
        
        # Test get_completed_jobs
        completed = await job_manager.get_completed_jobs()
        assert completed.is_success
        assert len(completed.value) == 1
        assert completed.value[0].id == job1_id
        
        # Test get_failed_jobs
        failed = await job_manager.get_failed_jobs()
        assert failed.is_success
        assert len(failed.value) == 1
        assert failed.value[0].id == job2_id
        
        # Test get_pending_jobs
        pending = await job_manager.get_pending_jobs()
        assert pending.is_success
        assert len(pending.value) == 1
        assert pending.value[0].id == job3_id
        
        # Test get_running_jobs
        running = await job_manager.get_running_jobs()
        assert running.is_success
        assert len(running.value) == 1
        assert running.value[0].id == job4_id
    
    @pytest.mark.asyncio
    async def test_run_job_sync(self, job_manager):
        # Run a job synchronously
        result = await job_manager.run_job_sync(
            task_name="test_task",
            args=[5, 7]
        )
        
        assert result.is_success
        assert result.value == 12
    
    @pytest.mark.asyncio
    async def test_run_async_job_sync(self, job_manager):
        # Run an async job synchronously
        result = await job_manager.run_job_sync(
            task_name="test_async_task",
            args=[10, 20]
        )
        
        assert result.is_success
        assert result.value == 30
    
    @pytest.mark.asyncio
    async def test_schedule_job_with_cron(self, job_manager):
        # Schedule a job with cron expression
        result = await job_manager.schedule_job(
            name="test_cron_schedule",
            task_name="test_task",
            cron_expression="*/5 * * * *",  # Every 5 minutes
            args=[1, 2],
            queue_name="scheduled"
        )
        
        assert result.is_success
        schedule_id = result.value
        
        # Get the schedule
        schedule_result = await job_manager.get_schedule(schedule_id)
        assert schedule_result.is_success
        schedule = schedule_result.value
        
        assert schedule is not None
        assert schedule.name == "test_cron_schedule"
        assert schedule.task_name == "test_task"
        assert schedule.cron_expression == "*/5 * * * *"
        assert schedule.args == [1, 2]
        assert schedule.queue_name == "scheduled"
    
    @pytest.mark.asyncio
    async def test_schedule_job_with_interval(self, job_manager):
        # Schedule a job with interval
        interval = ScheduleInterval(minutes=30)
        result = await job_manager.schedule_job(
            name="test_interval_schedule",
            task_name="test_task",
            interval=interval,
            args=[3, 4],
            queue_name="scheduled"
        )
        
        assert result.is_success
        schedule_id = result.value
        
        # Get the schedule
        schedule_result = await job_manager.get_schedule(schedule_id)
        assert schedule_result.is_success
        schedule = schedule_result.value
        
        assert schedule is not None
        assert schedule.name == "test_interval_schedule"
        assert schedule.task_name == "test_task"
        assert schedule.interval == interval
        assert schedule.args == [3, 4]
        assert schedule.queue_name == "scheduled"
    
    @pytest.mark.asyncio
    async def test_schedule_operations(self, job_manager):
        # Create a schedule
        interval = ScheduleInterval(minutes=30)
        schedule_id = (await job_manager.schedule_job(
            name="test_schedule",
            task_name="test_task",
            interval=interval
        )).value
        
        # Test pause_schedule
        pause_result = await job_manager.pause_schedule(schedule_id)
        assert pause_result.is_success
        
        schedule = (await job_manager.get_schedule(schedule_id)).value
        assert schedule.status == "paused"
        
        # Test resume_schedule
        resume_result = await job_manager.resume_schedule(schedule_id)
        assert resume_result.is_success
        
        schedule = (await job_manager.get_schedule(schedule_id)).value
        assert schedule.status == "active"
        
        # Test update_schedule
        update_result = await job_manager.update_schedule(
            schedule_id=schedule_id,
            name="updated_name",
            queue_name="updated_queue"
        )
        assert update_result.is_success
        
        schedule = (await job_manager.get_schedule(schedule_id)).value
        assert schedule.name == "updated_name"
        assert schedule.queue_name == "updated_queue"
        
        # Test list_schedules
        list_result = await job_manager.list_schedules()
        assert list_result.is_success
        assert len(list_result.value) == 1
        assert list_result.value[0].id == schedule_id
        
        # Test delete_schedule
        delete_result = await job_manager.delete_schedule(schedule_id)
        assert delete_result.is_success
        
        list_result = await job_manager.list_schedules()
        assert len(list_result.value) == 0
    
    @pytest.mark.asyncio
    async def test_scheduler_loop(self, job_manager):
        # This tests the _scheduler_loop method which is responsible for
        # running due schedules and creating jobs from them
        
        # Create a schedule that is due (next_run_at in the past)
        interval = ScheduleInterval(minutes=30)
        schedule = Schedule.create(
            name="due_schedule",
            task_name="test_task",
            interval=interval
        )
        schedule.next_run_at = datetime.now(UTC) - timedelta(minutes=5)  # Due 5 minutes ago
        
        # Add the schedule to the repository
        await job_manager.schedule_repository.create_schedule(schedule)
        
        # Run the scheduler loop once
        # We need to patch the _stop_event.wait to make it return immediately
        original_wait = job_manager._stop_event.wait
        
        async def mock_wait(timeout=None):
            return False  # Pretend the wait timed out
        
        job_manager._stop_event.wait = mock_wait
        
        try:
            # Start the job manager
            await job_manager.start()
            
            # Give the scheduler loop time to run
            await asyncio.sleep(0.1)
            
            # Stop the job manager
            await job_manager.stop()
            
            # Check that a job was created from the schedule
            pending_jobs = await job_manager.get_pending_jobs()
            assert pending_jobs.is_success
            assert len(pending_jobs.value) > 0
            
            # The job should have properties from the schedule
            job = pending_jobs.value[0]
            assert job.task_name == "test_task"
            assert "schedule_id" in job.metadata
            
            # The schedule should have had next_run_at updated
            updated_schedule = await job_manager.schedule_repository.get_schedule(schedule.id)
            assert updated_schedule.is_success
            assert updated_schedule.value.last_run_at is not None
            assert updated_schedule.value.next_run_at > datetime.now(UTC)
            
        finally:
            # Restore original wait method
            job_manager._stop_event.wait = original_wait
    
    @pytest.mark.asyncio
    async def test_register_task_via_decorator(self, job_manager):
        # Test the task decorator
        @job_manager.task(
            name="decorated_task",
            description="Task registered via decorator",
            queue="decorator_queue"
        )
        def decorated_func(x, y):
            return x * y
        
        # Check if the task was registered
        task = job_manager.task_registry.get_task("decorated_task")
        assert task is not None
        assert task["description"] == "Task registered via decorator"
        assert task["options"]["queue"] == "decorator_queue"
        
        # Execute the task to verify it works
        result = await job_manager.run_job_sync(
            task_name="decorated_task",
            args=[6, 7]
        )
        
        assert result.is_success
        assert result.value == 42