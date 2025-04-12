import pytest
from datetime import datetime, timedelta

from uno.jobs.queue.job import Job
from uno.jobs.queue.priority import Priority
from uno.jobs.queue.status import JobStatus


class TestJob:
    def test_job_creation(self):
        """Test basic job creation."""
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
        
        assert job.id == "test-job-1"
        assert job.queue_name == "test"
        assert job.task_name == "test_task"
        assert job.args == ["arg1", "arg2"]
        assert job.kwargs == {"key1": "value1"}
        assert job.status == JobStatus.PENDING
        assert job.priority == Priority.NORMAL
        assert job.max_retries == 3
        assert job.retries == 0
        assert job.created_at is not None
        assert job.updated_at is not None
    
    def test_job_factory_method(self):
        """Test job creation using the factory method."""
        job = Job.create(
            task_name="test_task",
            queue_name="test",
            args=["arg1", "arg2"],
            kwargs={"key1": "value1"},
            priority=Priority.HIGH,
            max_retries=5,
        )
        
        assert job.id is not None
        assert job.queue_name == "test"
        assert job.task_name == "test_task"
        assert job.args == ["arg1", "arg2"]
        assert job.kwargs == {"key1": "value1"}
        assert job.status == JobStatus.PENDING
        assert job.priority == Priority.HIGH
        assert job.max_retries == 5
        assert job.retries == 0
        assert job.created_at is not None
        assert job.updated_at is not None
    
    def test_job_status_properties(self):
        """Test job status properties."""
        job = Job.create(
            task_name="test_task",
            queue_name="test",
        )
        
        # Pending status
        job.status = JobStatus.PENDING
        assert job.is_pending() is True
        assert job.is_active() is False
        assert job.is_finished() is False
        assert job.is_failed() is False
        
        # Running status
        job.status = JobStatus.RUNNING
        assert job.is_pending() is False
        assert job.is_active() is True
        assert job.is_finished() is False
        assert job.is_failed() is False
        
        # Completed status
        job.status = JobStatus.COMPLETED
        assert job.is_pending() is False
        assert job.is_active() is False
        assert job.is_finished() is True
        assert job.is_failed() is False
        
        # Failed status
        job.status = JobStatus.FAILED
        assert job.is_pending() is False
        assert job.is_active() is False
        assert job.is_finished() is True
        assert job.is_failed() is True
    
    def test_job_should_retry(self):
        """Test job retry logic."""
        job = Job.create(
            task_name="test_task",
            queue_name="test",
            max_retries=3,
        )
        
        # Job is not failed
        job.status = JobStatus.PENDING
        assert job.should_retry() is False
        
        # Job is failed but hasn't reached max retries
        job.status = JobStatus.FAILED
        job.retries = 0
        assert job.should_retry() is True
        
        job.retries = 1
        assert job.should_retry() is True
        
        job.retries = 2
        assert job.should_retry() is True
        
        # Job is failed and has reached max retries
        job.retries = 3
        assert job.should_retry() is False
        
        # Job has max_retries = 0
        job = Job.create(
            task_name="test_task",
            queue_name="test",
            max_retries=0,
        )
        job.status = JobStatus.FAILED
        assert job.should_retry() is False
    
    def test_job_next_retry_at(self):
        """Test job retry scheduling."""
        now = datetime.utcnow()
        job = Job.create(
            task_name="test_task",
            queue_name="test",
            max_retries=3,
            retry_delay=timedelta(seconds=10),
        )
        job.status = JobStatus.FAILED
        job.retries = 1
        
        next_retry = job.next_retry_at(now)
        assert next_retry > now
        assert next_retry <= now + timedelta(seconds=11)  # Add a small margin for execution time
        
        # Test exponential backoff
        job.retries = 2
        next_retry_2 = job.next_retry_at(now)
        assert next_retry_2 > next_retry
        
        # Test max retries
        job.retries = 3
        assert job.next_retry_at(now) is None