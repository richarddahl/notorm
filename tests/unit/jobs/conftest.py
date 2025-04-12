import asyncio
import pytest
from datetime import datetime, timedelta

from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus
from uno.jobs.queue.queue import JobQueue
from uno.jobs.storage.memory import InMemoryJobStorage
from uno.jobs.worker.async_worker import AsyncWorker
from uno.jobs.scheduler.scheduler import Scheduler
from uno.jobs.scheduler.schedules import IntervalSchedule
from uno.jobs.manager import JobManager
from uno.jobs.tasks.task import Task, TaskRegistry


# Clear task registry before each test
@pytest.fixture(autouse=True)
def clear_task_registry():
    TaskRegistry._tasks = {}
    yield


@pytest.fixture
def memory_storage():
    storage = InMemoryJobStorage()
    yield storage


@pytest.fixture
def job_queue(memory_storage):
    queue = JobQueue(queue_name="test", storage=memory_storage)
    yield queue


@pytest.fixture
def test_job():
    job = Job(
        id="test-job-1",
        queue_name="test",
        task_name="test_task",
        args=["arg1", "arg2"],
        kwargs={"key1": "value1"},
        status=JobStatus.PENDING,
        priority=Priority.NORMAL,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        max_retries=3,
        retries=0,
    )
    yield job


@pytest.fixture
def worker(memory_storage):
    worker = AsyncWorker(storage=memory_storage, concurrency=1, poll_interval=0.1)
    yield worker


@pytest.fixture
def scheduler(memory_storage):
    scheduler = Scheduler(storage=memory_storage, poll_interval=0.1)
    yield scheduler


@pytest.fixture
def interval_schedule():
    schedule = IntervalSchedule(seconds=10)
    yield schedule


@pytest.fixture
def job_manager(memory_storage, worker, scheduler):
    manager = JobManager(
        storage=memory_storage,
        worker_classes=[type(worker)],
        scheduler=scheduler,
        stall_timeout=timedelta(minutes=5),
        cleanup_age=timedelta(days=1),
        cleanup_interval=timedelta(minutes=10),
        health_check_interval=timedelta(seconds=5),
    )
    yield manager


# Task registration for testing
@pytest.fixture
def register_test_task():
    async def test_task_handler(*args, **kwargs):
        await asyncio.sleep(0.1)
        return {"result": "success", "args": args, "kwargs": kwargs}
    
    task = Task(
        name="test_task",
        handler=test_task_handler,
        description="Test task for testing",
    )
    
    TaskRegistry.register_task(
        name="test_task",
        handler=test_task_handler,
        description="Test task for testing",
    )
    
    yield task