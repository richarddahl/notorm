import pytest
from datetime import datetime, timedelta, UTC
import uuid
from unittest import mock

from uno.jobs.entities import (
    Job, JobPriority, JobStatus, JobError, Schedule, ScheduleInterval
)


class TestJobPriority:
    
    def test_priority_values(self):
        assert JobPriority.CRITICAL.value == 0
        assert JobPriority.HIGH.value == 1
        assert JobPriority.NORMAL.value == 2
        assert JobPriority.LOW.value == 3
    
    def test_from_string_valid(self):
        assert JobPriority.from_string("critical") == JobPriority.CRITICAL
        assert JobPriority.from_string("high") == JobPriority.HIGH
        assert JobPriority.from_string("normal") == JobPriority.NORMAL
        assert JobPriority.from_string("low") == JobPriority.LOW
        
        # Test case insensitivity
        assert JobPriority.from_string("CRITICAL") == JobPriority.CRITICAL
        assert JobPriority.from_string("High") == JobPriority.HIGH
    
    def test_from_string_invalid(self):
        with pytest.raises(ValueError) as exc:
            JobPriority.from_string("invalid")
        
        assert "Invalid priority: invalid" in str(exc.value)
        assert "critical, high, normal, low" in str(exc.value).lower()


class TestJobStatus:
    
    def test_status_values(self):
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RESERVED.value == "reserved"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.RETRYING.value == "retrying"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.TIMEOUT.value == "timeout"
    
    def test_is_active(self):
        assert JobStatus.PENDING.is_active is True
        assert JobStatus.RESERVED.is_active is True
        assert JobStatus.RUNNING.is_active is True
        assert JobStatus.RETRYING.is_active is True
        
        assert JobStatus.COMPLETED.is_active is False
        assert JobStatus.FAILED.is_active is False
        assert JobStatus.CANCELLED.is_active is False
        assert JobStatus.TIMEOUT.is_active is False
    
    def test_is_terminal(self):
        assert JobStatus.COMPLETED.is_terminal is True
        assert JobStatus.FAILED.is_terminal is True
        assert JobStatus.CANCELLED.is_terminal is True
        assert JobStatus.TIMEOUT.is_terminal is True
        
        assert JobStatus.PENDING.is_terminal is False
        assert JobStatus.RESERVED.is_terminal is False
        assert JobStatus.RUNNING.is_terminal is False
        assert JobStatus.RETRYING.is_terminal is False


class TestJobError:
    
    def test_create_job_error(self):
        error = JobError(type="ValueError", message="Something went wrong", traceback="traceback content")
        
        assert error.type == "ValueError"
        assert error.message == "Something went wrong"
        assert error.traceback == "traceback content"
    
    def test_create_without_traceback(self):
        error = JobError(type="ValueError", message="Something went wrong")
        
        assert error.type == "ValueError"
        assert error.message == "Something went wrong"
        assert error.traceback is None
    
    def test_from_exception(self):
        exception = ValueError("Test exception")
        
        with mock.patch("traceback.format_exc", return_value="mocked traceback"):
            error = JobError.from_exception(exception)
        
        assert error.type == "ValueError"
        assert error.message == "Test exception"
        assert error.traceback == "mocked traceback"
    
    def test_from_exception_without_traceback(self):
        exception = ValueError("Test exception")
        
        error = JobError.from_exception(exception, include_traceback=False)
        
        assert error.type == "ValueError"
        assert error.message == "Test exception"
        assert error.traceback is None


class TestJob:
    
    def test_create_job(self):
        job = Job.create(
            task_name="test_task",
            args=[1, 2, 3],
            kwargs={"key": "value"},
            queue_name="test_queue",
            priority=JobPriority.HIGH,
            scheduled_at=datetime.now(UTC) + timedelta(hours=1),
            max_retries=5,
            retry_delay=120,
            timeout=300,
            tags={"tag1", "tag2"},
            metadata={"meta": "data"},
            version="1.0",
            job_id="test-id"
        )
        
        assert job.id == "test-id"
        assert job.task_name == "test_task"
        assert job.args == [1, 2, 3]
        assert job.kwargs == {"key": "value"}
        assert job.queue_name == "test_queue"
        assert job.priority == JobPriority.HIGH
        assert job.status == JobStatus.PENDING
        assert job.scheduled_at is not None
        assert job.retry_count == 0
        assert job.max_retries == 5
        assert job.retry_delay == timedelta(seconds=120)
        assert job.timeout == timedelta(seconds=300)
        assert job.tags == {"tag1", "tag2"}
        assert job.metadata == {"meta": "data"}
        assert job.version == "1.0"
    
    def test_create_job_default_values(self):
        job = Job.create(task_name="test_task")
        
        assert job.id != ""
        assert len(job.id) > 0
        assert job.task_name == "test_task"
        assert job.args == []
        assert job.kwargs == {}
        assert job.queue_name == "default"
        assert job.priority == JobPriority.NORMAL
        assert job.status == JobStatus.PENDING
        assert job.scheduled_at is None
        assert job.retry_count == 0
        assert job.max_retries == 3
        assert job.retry_delay == timedelta(seconds=60)
        assert job.timeout is None
        assert job.tags == set()
        assert job.metadata == {}
        assert job.version is None
    
    def test_duration(self):
        job = Job.create(task_name="test_task")
        
        # No start time, duration should be None
        assert job.duration is None
        
        # Set start time but no complete time
        now = datetime.now(UTC)
        job.started_at = now - timedelta(seconds=10)
        
        # Duration should be positive and around 10 seconds
        assert job.duration is not None
        assert job.duration.total_seconds() >= 9.9
        
        # Set complete time
        job.completed_at = now
        assert job.duration.total_seconds() == 10
    
    def test_is_due(self):
        job = Job.create(task_name="test_task")
        
        # No scheduled time, should be due
        assert job.is_due is True
        
        # Scheduled for the future
        job.scheduled_at = datetime.now(UTC) + timedelta(hours=1)
        assert job.is_due is False
        
        # Scheduled for the past
        job.scheduled_at = datetime.now(UTC) - timedelta(hours=1)
        assert job.is_due is True
    
    def test_can_retry(self):
        job = Job.create(task_name="test_task", max_retries=3)
        
        # No retries yet, should be retryable
        assert job.can_retry is True
        
        # Some retries, but not max
        job.retry_count = 2
        assert job.can_retry is True
        
        # Max retries reached
        job.retry_count = 3
        assert job.can_retry is False
    
    def test_job_state_transitions(self):
        job = Job.create(task_name="test_task")
        assert job.status == JobStatus.PENDING
        
        # Reserve job
        job.mark_reserved("worker-1")
        assert job.status == JobStatus.RESERVED
        assert job.worker_id == "worker-1"
        
        # Start job
        job.mark_running()
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        
        # Complete job
        result = {"result": "success"}
        job.mark_completed(result)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result == result
    
    def test_job_failure_states(self):
        job = Job.create(task_name="test_task", max_retries=2)
        job.mark_reserved("worker-1")
        job.mark_running()
        
        # Test failure with a string error
        job.mark_failed("Something went wrong")
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert job.error is not None
        assert job.error.type == "Error"
        assert job.error.message == "Something went wrong"
        
        # Reset job for retry
        job.status = JobStatus.PENDING
        job.completed_at = None
        job.error = None
        job.mark_reserved("worker-1")
        job.mark_running()
        
        # Test failure with an exception
        exception = ValueError("Bad value")
        with mock.patch("traceback.format_exc", return_value="mocked traceback"):
            job.mark_failed(exception)
        assert job.status == JobStatus.FAILED
        assert job.error is not None
        assert job.error.type == "ValueError"
        assert job.error.message == "Bad value"
        assert job.error.traceback == "mocked traceback"
        
        # Reset job for retry
        job.status = JobStatus.PENDING
        job.completed_at = None
        job.error = None
        job.mark_reserved("worker-1")
        job.mark_running()
        
        # Test retry
        with mock.patch("traceback.format_exc", return_value="mocked traceback"):
            job.mark_retry(exception)
        assert job.status == JobStatus.RETRYING
        assert job.retry_count == 1
        assert job.error is not None
        assert job.error.type == "ValueError"
        assert job.worker_id is None  # Worker ID should be cleared on retry
    
    def test_mark_cancelled(self):
        job = Job.create(task_name="test_task")
        job.mark_cancelled("User requested")
        
        assert job.status == JobStatus.CANCELLED
        assert job.completed_at is not None
        assert job.metadata["cancel_reason"] == "User requested"
    
    def test_mark_timeout(self):
        job = Job.create(task_name="test_task", timeout=60)
        job.mark_timeout()
        
        assert job.status == JobStatus.TIMEOUT
        assert job.completed_at is not None
        assert job.error is not None
        assert job.error.type == "TimeoutError"
        assert "Job exceeded timeout of 60" in job.error.message


class TestScheduleInterval:
    
    def test_create_interval(self):
        interval = ScheduleInterval(
            seconds=30,
            minutes=15,
            hours=2,
            days=1
        )
        
        assert interval.seconds == 30
        assert interval.minutes == 15
        assert interval.hours == 2
        assert interval.days == 1
    
    def test_total_seconds(self):
        interval = ScheduleInterval(
            seconds=30,
            minutes=15,
            hours=2,
            days=1
        )
        
        # 1 day = 86400 seconds
        # 2 hours = 7200 seconds
        # 15 minutes = 900 seconds
        # 30 seconds = 30 seconds
        # Total = 94530 seconds
        assert interval.total_seconds == 94530
    
    def test_timedelta(self):
        interval = ScheduleInterval(
            seconds=30,
            minutes=15,
            hours=2,
            days=1
        )
        
        delta = interval.timedelta
        assert isinstance(delta, timedelta)
        assert delta.total_seconds() == 94530


class TestSchedule:
    
    def test_create_schedule_with_cron(self):
        schedule = Schedule.create(
            name="test_schedule",
            task_name="test_task",
            cron_expression="*/5 * * * *",  # Every 5 minutes
            args=[1, 2, 3],
            kwargs={"key": "value"},
            queue_name="test_queue",
            priority=JobPriority.HIGH,
            tags={"tag1", "tag2"},
            metadata={"meta": "data"},
            max_retries=5,
            retry_delay=120,
            timeout=300,
            version="1.0",
            schedule_id="test-id"
        )
        
        assert schedule.id == "test-id"
        assert schedule.name == "test_schedule"
        assert schedule.task_name == "test_task"
        assert schedule.status == "active"
        assert schedule.cron_expression == "*/5 * * * *"
        assert schedule.interval is None
        assert schedule.args == [1, 2, 3]
        assert schedule.kwargs == {"key": "value"}
        assert schedule.queue_name == "test_queue"
        assert schedule.priority == JobPriority.HIGH
        assert schedule.tags == {"tag1", "tag2"}
        assert schedule.metadata == {"meta": "data"}
        assert schedule.max_retries == 5
        assert schedule.retry_delay == timedelta(seconds=120)
        assert schedule.timeout == timedelta(seconds=300)
        assert schedule.version == "1.0"
    
    def test_create_schedule_with_interval(self):
        interval = ScheduleInterval(minutes=30)
        schedule = Schedule.create(
            name="test_schedule",
            task_name="test_task",
            interval=interval,
            schedule_id="test-id"
        )
        
        assert schedule.id == "test-id"
        assert schedule.name == "test_schedule"
        assert schedule.task_name == "test_task"
        assert schedule.status == "active"
        assert schedule.cron_expression is None
        assert schedule.interval is interval
        assert schedule.next_run_at is not None  # Should be set to now + interval
    
    def test_create_schedule_validation(self):
        # Neither cron nor interval provided
        with pytest.raises(ValueError) as exc:
            Schedule.create(
                name="test_schedule",
                task_name="test_task"
            )
        assert "Either cron_expression or interval must be provided" in str(exc.value)
        
        # Both cron and interval provided
        with pytest.raises(ValueError) as exc:
            Schedule.create(
                name="test_schedule",
                task_name="test_task",
                cron_expression="*/5 * * * *",
                interval=ScheduleInterval(minutes=30)
            )
        assert "Only one of cron_expression or interval should be provided" in str(exc.value)
    
    def test_pause_resume(self):
        interval = ScheduleInterval(minutes=30)
        schedule = Schedule.create(
            name="test_schedule",
            task_name="test_task",
            interval=interval
        )
        
        assert schedule.status == "active"
        
        # Pause the schedule
        schedule.pause()
        assert schedule.status == "paused"
        
        # Resume the schedule
        with mock.patch.object(Schedule, 'update_next_run') as mock_update:
            schedule.resume()
            assert schedule.status == "active"
            
            # Should not call update_next_run as we mocked it
            assert mock_update.call_count == 0
    
    def test_update_next_run(self):
        # Test with interval
        interval = ScheduleInterval(minutes=30)
        schedule = Schedule.create(
            name="test_schedule",
            task_name="test_task",
            interval=interval
        )
        
        old_next_run = schedule.next_run_at
        assert old_next_run is not None
        
        # Update next run
        schedule.update_next_run()
        
        # Last run should be set to now
        assert schedule.last_run_at is not None
        
        # Next run should be last run + interval
        assert schedule.next_run_at is not None
        expected_next_run = schedule.last_run_at + interval.timedelta
        assert schedule.next_run_at.timestamp() == pytest.approx(expected_next_run.timestamp(), abs=1)
    
    def test_is_due(self):
        interval = ScheduleInterval(minutes=30)
        schedule = Schedule.create(
            name="test_schedule",
            task_name="test_task",
            interval=interval
        )
        
        # Not due yet (next_run_at is in the future)
        assert schedule.is_due() is False
        
        # Set next run to the past
        schedule.next_run_at = datetime.now(UTC) - timedelta(minutes=5)
        assert schedule.is_due() is True
        
        # Pause schedule
        schedule.pause()
        assert schedule.is_due() is False
    
    def test_create_job(self):
        schedule = Schedule.create(
            name="test_schedule",
            task_name="test_task",
            cron_expression="*/5 * * * *",
            args=[1, 2, 3],
            kwargs={"key": "value"},
            queue_name="test_queue",
            priority=JobPriority.HIGH,
            tags={"tag1", "tag2"},
            metadata={"meta": "data"},
            max_retries=5,
            retry_delay=120,
            timeout=300,
            version="1.0",
            schedule_id="test-id"
        )
        
        job = schedule.create_job()
        
        assert job.task_name == "test_task"
        assert job.args == [1, 2, 3]
        assert job.kwargs == {"key": "value"}
        assert job.queue_name == "test_queue"
        assert job.priority == JobPriority.HIGH
        assert job.tags == {"tag1", "tag2"}
        assert job.metadata == {
            "meta": "data",
            "schedule_id": "test-id",
            "schedule_name": "test_schedule"
        }
        assert job.max_retries == 5
        assert job.retry_delay == timedelta(seconds=120)
        assert job.timeout == timedelta(seconds=300)
        assert job.version == "1.0"