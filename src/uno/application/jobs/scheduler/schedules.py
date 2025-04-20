"""Schedule definitions for the background processing system.

This module defines the schedule types used for recurring job execution.
"""

from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional, Set, Union, cast
import calendar
from croniter import croniter


class Schedule(ABC):
    """Abstract base class for all schedule types.

    This class defines the interface for schedule types that determine
    when recurring jobs should be executed.
    """

    @abstractmethod
    def get_next_run_time(self, after: datetime) -> Optional[datetime]:
        """Get the next time this schedule should run.

        Args:
            after: The time to start looking from

        Returns:
            The next run time or None if no future runs are scheduled
        """
        pass

    @abstractmethod
    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Args:
            after: The time to start looking from
            n: Number of run times to return

        Returns:
            List of the next N run times
        """
        pass

    @abstractmethod
    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        Args:
            current_time: The current time

        Returns:
            True if the schedule is due, False otherwise
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        pass

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Schedule":
        """Create a schedule from a dictionary representation.

        Args:
            data: Dictionary representation of a schedule

        Returns:
            Schedule instance

        Raises:
            ValueError: If the schedule type is not recognized
        """
        schedule_type = data.get("type")

        if schedule_type == "cron":
            return CronSchedule.from_dict(data)
        elif schedule_type == "interval":
            return IntervalSchedule.from_dict(data)
        elif schedule_type == "one_time":
            return OneTimeSchedule.from_dict(data)
        elif schedule_type == "daily":
            return DailySchedule.from_dict(data)
        elif schedule_type == "weekly":
            return WeeklySchedule.from_dict(data)
        elif schedule_type == "monthly":
            return MonthlySchedule.from_dict(data)
        elif schedule_type == "event":
            return EventTrigger.from_dict(data)
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")


class CronSchedule(Schedule):
    """Cron-based schedule for complex time patterns.

    This schedule type uses cron expressions to specify when jobs should run,
    providing maximum flexibility for scheduling.
    """

    def __init__(self, cron_expression: str, timezone: str = "UTC"):
        """Initialize a cron schedule.

        Args:
            cron_expression: Cron expression in format "minute hour day month day_of_week"
            timezone: Timezone for the schedule
        """
        self.cron_expression = cron_expression
        self.timezone = timezone

        # Validate the cron expression
        try:
            croniter(self.cron_expression, datetime.now())
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {cron_expression}. Error: {e}")

    def get_next_run_time(self, after: datetime) -> datetime:
        """Get the next time this schedule should run.

        Args:
            after: The time to start looking from

        Returns:
            The next run time
        """
        cron = croniter(self.cron_expression, after)
        return cron.get_next(datetime)

    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Args:
            after: The time to start looking from
            n: Number of run times to return

        Returns:
            List of the next N run times
        """
        cron = croniter(self.cron_expression, after)
        return [cron.get_next(datetime) for _ in range(n)]

    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        For cron schedules, this checks if the current time matches the
        cron expression.

        Args:
            current_time: The current time

        Returns:
            True if the schedule is due, False otherwise
        """
        # Get the previous run time that would have been scheduled
        cron = croniter(self.cron_expression, current_time)
        prev_run = cron.get_prev(datetime)

        # Check if the previous run time is within 1 minute of the current time
        return (current_time - prev_run).total_seconds() < 60

    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        return {
            "type": "cron",
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CronSchedule":
        """Create a cron schedule from a dictionary representation.

        Args:
            data: Dictionary representation of a cron schedule

        Returns:
            CronSchedule instance
        """
        return CronSchedule(
            cron_expression=data["cron_expression"],
            timezone=data.get("timezone", "UTC"),
        )


class IntervalSchedule(Schedule):
    """Interval-based schedule for regular time periods.

    This schedule type runs jobs at fixed time intervals, such as
    every 5 minutes or every 2 hours.
    """

    def __init__(self, interval: timedelta, start_time: Optional[datetime] = None):
        """Initialize an interval schedule.

        Args:
            interval: The time interval between job runs
            start_time: Optional start time for the first run
        """
        self.interval = interval
        self.start_time = start_time or datetime.now()

    def get_next_run_time(self, after: datetime) -> datetime:
        """Get the next time this schedule should run.

        Args:
            after: The time to start looking from

        Returns:
            The next run time
        """
        # Calculate how many intervals have passed since the start time
        delta = after - self.start_time
        intervals_passed = delta.total_seconds() / self.interval.total_seconds()
        intervals_passed_int = int(intervals_passed)

        # If we're exactly on an interval point, we need to move to the next one
        if intervals_passed == intervals_passed_int:
            intervals_to_add = intervals_passed_int + 1
        else:
            intervals_to_add = intervals_passed_int + 1

        # Calculate the next run time
        return self.start_time + (self.interval * intervals_to_add)

    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Args:
            after: The time to start looking from
            n: Number of run times to return

        Returns:
            List of the next N run times
        """
        result = []
        current = self.get_next_run_time(after)

        for _ in range(n):
            result.append(current)
            current = current + self.interval

        return result

    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        Args:
            current_time: The current time

        Returns:
            True if the schedule is due, False otherwise
        """
        # Get the previous run time that would have been scheduled
        delta = current_time - self.start_time
        intervals_passed = delta.total_seconds() / self.interval.total_seconds()
        intervals_passed_int = int(intervals_passed)

        prev_run = self.start_time + (self.interval * intervals_passed_int)

        # Check if the previous run time is within 1 second of the current time
        # This allows for slight timing variations
        return (current_time - prev_run).total_seconds() < 1

    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        return {
            "type": "interval",
            "interval_seconds": self.interval.total_seconds(),
            "start_time": self.start_time.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "IntervalSchedule":
        """Create an interval schedule from a dictionary representation.

        Args:
            data: Dictionary representation of an interval schedule

        Returns:
            IntervalSchedule instance
        """
        interval_seconds = data["interval_seconds"]
        interval = timedelta(seconds=interval_seconds)

        start_time = None
        if "start_time" in data:
            start_time = datetime.fromisoformat(data["start_time"])

        return IntervalSchedule(interval=interval, start_time=start_time)


class OneTimeSchedule(Schedule):
    """One-time schedule for executing a job once at a specific time.

    This schedule type runs a job exactly once at a specified time.
    """

    def __init__(self, run_time: datetime):
        """Initialize a one-time schedule.

        Args:
            run_time: The time to run the job
        """
        self.run_time = run_time

    def get_next_run_time(self, after: datetime) -> Optional[datetime]:
        """Get the next time this schedule should run.

        Args:
            after: The time to start looking from

        Returns:
            The run time if it's after the given time, None otherwise
        """
        if after < self.run_time:
            return self.run_time
        return None

    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Since this is a one-time schedule, this will return at most one time.

        Args:
            after: The time to start looking from
            n: Number of run times to return (ignored for one-time schedules)

        Returns:
            List containing at most one run time
        """
        next_run = self.get_next_run_time(after)
        return [next_run] if next_run else []

    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        Args:
            current_time: The current time

        Returns:
            True if current_time is after run_time, False otherwise
        """
        # Allow a 1-second window to account for timing variations
        return (
            current_time >= self.run_time
            and (current_time - self.run_time).total_seconds() < 1
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        return {
            "type": "one_time",
            "run_time": self.run_time.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "OneTimeSchedule":
        """Create a one-time schedule from a dictionary representation.

        Args:
            data: Dictionary representation of a one-time schedule

        Returns:
            OneTimeSchedule instance
        """
        run_time = datetime.fromisoformat(data["run_time"])
        return OneTimeSchedule(run_time=run_time)


class DailySchedule(Schedule):
    """Daily schedule for running jobs at specific times each day.

    This schedule type runs jobs at the same time(s) every day.
    """

    def __init__(self, times: list[str], timezone: str = "UTC"):
        """Initialize a daily schedule.

        Args:
            times: List of times in 24-hour format ("HH:MM")
            timezone: Timezone for the schedule
        """
        self.times = sorted(times)  # Sort times for consistent ordering
        self.timezone = timezone

        # Validate time formats
        for t in self.times:
            try:
                hour, minute = t.split(":")
                if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                    raise ValueError(
                        f"Invalid time: {t}. Must be in format 'HH:MM' (24-hour)."
                    )
            except Exception:
                raise ValueError(
                    f"Invalid time: {t}. Must be in format 'HH:MM' (24-hour)."
                )

    def get_next_run_time(self, after: datetime) -> datetime:
        """Get the next time this schedule should run.

        Args:
            after: The time to start looking from

        Returns:
            The next run time
        """
        after_time = after.strftime("%H:%M")
        today = after.date()
        tomorrow = today + timedelta(days=1)

        # Check if any times are still remaining today
        remaining_today = [t for t in self.times if t > after_time]

        if remaining_today:
            # Run later today
            next_time = remaining_today[0]
            hour, minute = map(int, next_time.split(":"))
            return datetime.combine(today, time(hour, minute))
        else:
            # Run tomorrow at the earliest time
            next_time = self.times[0]
            hour, minute = map(int, next_time.split(":"))
            return datetime.combine(tomorrow, time(hour, minute))

    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Args:
            after: The time to start looking from
            n: Number of run times to return

        Returns:
            List of the next N run times
        """
        result = []
        current = after

        while len(result) < n:
            next_run = self.get_next_run_time(current)
            result.append(next_run)
            current = next_run + timedelta(
                minutes=1
            )  # Advance time to get the next run

        return result

    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        Args:
            current_time: The current time

        Returns:
            True if the current time matches one of the scheduled times
        """
        current_time_str = current_time.strftime("%H:%M")

        # Check if the current time matches any of the scheduled times
        # Allow a 1-minute window to account for timing variations
        for scheduled_time in self.times:
            scheduled_hour, scheduled_minute = map(int, scheduled_time.split(":"))
            scheduled_datetime = datetime.combine(
                current_time.date(), time(scheduled_hour, scheduled_minute)
            )

            # Check if we're within 1 minute of the scheduled time
            time_diff = abs((current_time - scheduled_datetime).total_seconds())
            if time_diff < 60:
                return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        return {
            "type": "daily",
            "times": self.times,
            "timezone": self.timezone,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "DailySchedule":
        """Create a daily schedule from a dictionary representation.

        Args:
            data: Dictionary representation of a daily schedule

        Returns:
            DailySchedule instance
        """
        return DailySchedule(
            times=data["times"],
            timezone=data.get("timezone", "UTC"),
        )


class WeeklySchedule(Schedule):
    """Weekly schedule for running jobs on specific days of the week.

    This schedule type runs jobs on the same day(s) and time each week.
    """

    # Valid day names and their numeric values
    DAY_NAMES = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    def __init__(self, days: list[Union[str, int]], time: str, timezone: str = "UTC"):
        """Initialize a weekly schedule.

        Args:
            days: List of days (can be strings like "monday" or integers 0-6)
            time: Time in 24-hour format ("HH:MM")
            timezone: Timezone for the schedule
        """
        # Convert day names to integers if needed
        self.days = set()
        for day in days:
            if isinstance(day, str):
                day_lower = day.lower()
                if day_lower not in self.DAY_NAMES:
                    valid_days = ", ".join(self.DAY_NAMES.keys())
                    raise ValueError(
                        f"Invalid day name: {day}. Valid values are: {valid_days}"
                    )
                self.days.add(self.DAY_NAMES[day_lower])
            elif isinstance(day, int):
                if not (0 <= day <= 6):
                    raise ValueError("Day integers must be between 0 and 6")
                self.days.add(day)
            else:
                raise ValueError(
                    f"Invalid day format: {day}. Must be a string or integer."
                )

        # Convert set to sorted list for consistency
        self.days = sorted(list(self.days))

        # Validate time format
        try:
            hour, minute = time.split(":")
            if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                raise ValueError(
                    f"Invalid time: {time}. Must be in format 'HH:MM' (24-hour)."
                )
        except Exception:
            raise ValueError(
                f"Invalid time: {time}. Must be in format 'HH:MM' (24-hour)."
            )

        self.time = time
        self.timezone = timezone

    def get_next_run_time(self, after: datetime) -> datetime:
        """Get the next time this schedule should run.

        Args:
            after: The time to start looking from

        Returns:
            The next run time
        """
        # Current day of week (0-6, where 0 is Monday)
        current_day = after.weekday()

        # Current time as string
        current_time = after.strftime("%H:%M")

        # Parse run time
        hour, minute = map(int, self.time.split(":"))

        # Find the next day to run
        days_to_add = 0
        found = False

        # Check if we can still run today
        if current_day in self.days and current_time < self.time:
            days_to_add = 0
            found = True
        else:
            # Find the next day to run
            for i in range(1, 8):  # Check the next 7 days
                check_day = (current_day + i) % 7
                if check_day in self.days:
                    days_to_add = i
                    found = True
                    break

        if not found:
            # This should not happen as long as self.days is not empty
            raise ValueError("No valid run days found")

        # Calculate the next run date
        next_date = after.date() + timedelta(days=days_to_add)
        return datetime.combine(next_date, time(hour, minute))

    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Args:
            after: The time to start looking from
            n: Number of run times to return

        Returns:
            List of the next N run times
        """
        result = []
        current = after

        while len(result) < n:
            next_run = self.get_next_run_time(current)
            result.append(next_run)
            current = next_run + timedelta(
                minutes=1
            )  # Advance time to get the next run

        return result

    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        Args:
            current_time: The current time

        Returns:
            True if the current day and time match the schedule
        """
        # Check if today is a scheduled day
        if current_time.weekday() not in self.days:
            return False

        # Check if we're at the scheduled time
        hour, minute = map(int, self.time.split(":"))
        scheduled_time = time(hour, minute)
        scheduled_datetime = datetime.combine(current_time.date(), scheduled_time)

        # Check if we're within 1 minute of the scheduled time
        time_diff = abs((current_time - scheduled_datetime).total_seconds())
        return time_diff < 60

    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        # Convert numeric days to names for better readability
        day_names = []
        for day in self.days:
            for name, value in self.DAY_NAMES.items():
                if value == day:
                    day_names.append(name)
                    break

        return {
            "type": "weekly",
            "days": day_names,
            "time": self.time,
            "timezone": self.timezone,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "WeeklySchedule":
        """Create a weekly schedule from a dictionary representation.

        Args:
            data: Dictionary representation of a weekly schedule

        Returns:
            WeeklySchedule instance
        """
        return WeeklySchedule(
            days=data["days"],
            time=data["time"],
            timezone=data.get("timezone", "UTC"),
        )


class MonthlySchedule(Schedule):
    """Monthly schedule for running jobs on specific days of the month.

    This schedule type runs jobs on the same day(s) and time each month.
    """

    def __init__(self, days: list[int], time: str, timezone: str = "UTC"):
        """Initialize a monthly schedule.

        Args:
            days: List of days of the month (1-31)
            time: Time in 24-hour format ("HH:MM")
            timezone: Timezone for the schedule
        """
        # Validate days
        self.days = sorted(
            [int(day) for day in days]
        )  # Sort days for consistent ordering
        for day in self.days:
            if not (1 <= day <= 31):
                raise ValueError(f"Invalid day: {day}. Must be between 1 and 31.")

        # Validate time format
        try:
            hour, minute = time.split(":")
            if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                raise ValueError(
                    f"Invalid time: {time}. Must be in format 'HH:MM' (24-hour)."
                )
        except Exception:
            raise ValueError(
                f"Invalid time: {time}. Must be in format 'HH:MM' (24-hour)."
            )

        self.time = time
        self.timezone = timezone

    def get_next_run_time(self, after: datetime) -> datetime:
        """Get the next time this schedule should run.

        Args:
            after: The time to start looking from

        Returns:
            The next run time
        """
        current_date = after.date()
        current_day = current_date.day
        current_time = after.strftime("%H:%M")

        # Parse run time
        hour, minute = map(int, self.time.split(":"))

        # Check if we have any days left in the current month
        remaining_days = [day for day in self.days if day > current_day]

        if remaining_days and (
            current_day < remaining_days[0]
            or (current_day == remaining_days[0] and current_time < self.time)
        ):
            # We can still run this month
            next_day = remaining_days[0]
            next_month = current_date.month
            next_year = current_date.year
        else:
            # Move to the next month
            if current_date.month == 12:
                next_month = 1
                next_year = current_date.year + 1
            else:
                next_month = current_date.month + 1
                next_year = current_date.year

            # Use the first scheduled day of the month
            next_day = self.days[0]

        # Adjust for days that don't exist in the target month
        days_in_month = calendar.monthrange(next_year, next_month)[1]
        while next_day > days_in_month:
            # Try the previous day in our list
            if len([d for d in self.days if d < next_day]) > 0:
                next_day = max([d for d in self.days if d < next_day])
            else:
                # No earlier days in this month, move to the next month
                if next_month == 12:
                    next_month = 1
                    next_year += 1
                else:
                    next_month += 1
                next_day = self.days[0]
                days_in_month = calendar.monthrange(next_year, next_month)[1]

        # Construct the next run datetime
        return datetime(next_year, next_month, next_day, hour, minute)

    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Args:
            after: The time to start looking from
            n: Number of run times to return

        Returns:
            List of the next N run times
        """
        result = []
        current = after

        while len(result) < n:
            next_run = self.get_next_run_time(current)
            result.append(next_run)
            current = next_run + timedelta(
                minutes=1
            )  # Advance time to get the next run

        return result

    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        Args:
            current_time: The current time

        Returns:
            True if the current day and time match the schedule
        """
        # Check if today is a scheduled day
        if current_time.day not in self.days:
            return False

        # Check if we're at the scheduled time
        hour, minute = map(int, self.time.split(":"))
        scheduled_time = time(hour, minute)
        scheduled_datetime = datetime.combine(current_time.date(), scheduled_time)

        # Check if we're within 1 minute of the scheduled time
        time_diff = abs((current_time - scheduled_datetime).total_seconds())
        return time_diff < 60

    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        return {
            "type": "monthly",
            "days": self.days,
            "time": self.time,
            "timezone": self.timezone,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "MonthlySchedule":
        """Create a monthly schedule from a dictionary representation.

        Args:
            data: Dictionary representation of a monthly schedule

        Returns:
            MonthlySchedule instance
        """
        return MonthlySchedule(
            days=data["days"],
            time=data["time"],
            timezone=data.get("timezone", "UTC"),
        )


class EventTrigger(Schedule):
    """Event-based schedule that is triggered by specific events.

    This schedule type is not time-based but rather runs when a specific
    event occurs in the system.
    """

    def __init__(self, event_name: str):
        """Initialize an event trigger.

        Args:
            event_name: Name of the event that triggers this schedule
        """
        self.event_name = event_name
        self.last_triggered: Optional[datetime] = None

    def get_next_run_time(self, after: datetime) -> Optional[datetime]:
        """Get the next time this schedule should run.

        Event triggers don't have predictable future run times, so this
        always returns None.

        Args:
            after: The time to start looking from (ignored for event triggers)

        Returns:
            None, as event triggers don't have predictable future run times
        """
        return None

    def get_next_n_run_times(self, after: datetime, n: int) -> list[datetime]:
        """Get the next N times this schedule should run.

        Event triggers don't have predictable future run times, so this
        always returns an empty list.

        Args:
            after: The time to start looking from (ignored for event triggers)
            n: Number of run times to return (ignored for event triggers)

        Returns:
            Empty list, as event triggers don't have predictable future run times
        """
        return []

    def is_due(self, current_time: datetime) -> bool:
        """Check if this schedule is due for execution.

        Event triggers are only due when explicitly triggered, not based
        on the current time.

        Args:
            current_time: The current time (ignored for event triggers)

        Returns:
            False, as event triggers are only due when explicitly triggered
        """
        return False

    def trigger(self, event_data: dict[str, Any] | None = None) -> datetime:
        """Trigger this event schedule.

        Args:
            event_data: Optional data associated with the event

        Returns:
            The timestamp when the trigger occurred
        """
        self.last_triggered = datetime.now()
        return self.last_triggered

    def to_dict(self) -> dict[str, Any]:
        """Convert this schedule to a dictionary representation.

        Returns:
            Dictionary representation of the schedule
        """
        data = {
            "type": "event",
            "event_name": self.event_name,
        }

        if self.last_triggered:
            data["last_triggered"] = self.last_triggered.isoformat()

        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "EventTrigger":
        """Create an event trigger from a dictionary representation.

        Args:
            data: Dictionary representation of an event trigger

        Returns:
            EventTrigger instance
        """
        trigger = EventTrigger(event_name=data["event_name"])

        if "last_triggered" in data and data["last_triggered"]:
            trigger.last_triggered = datetime.fromisoformat(data["last_triggered"])

        return trigger


class ScheduleTemplate:
    """Template for creating schedules with shared configuration.

    This class allows for creating schedule templates that can be used
    to create multiple schedules with shared configuration options.
    """

    def __init__(
        self,
        schedule: Optional[Schedule] = None,
        timezone: str = "UTC",
        queue: str = "default",
        priority: str = "normal",
        max_retries: int = 0,
        retry_delay: int = 60,
        timeout: int | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a schedule template.

        Args:
            schedule: Optional base schedule
            timezone: Timezone for schedules
            queue: Queue for scheduled jobs
            priority: Priority for scheduled jobs
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Optional timeout in seconds
            tags: Optional tags for scheduled jobs
            metadata: Optional metadata for scheduled jobs
        """
        self.schedule = schedule
        self.timezone = timezone
        self.queue = queue
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.tags = tags or []
        self.metadata = metadata or {}

    def create_schedule(
        self, schedule: Optional[Schedule] = None, **overrides: Any
    ) -> dict[str, Any]:
        """Create a schedule from this template.

        Args:
            schedule: Optional schedule to use instead of the template's schedule
            **overrides: Additional options to override template defaults

        Returns:
            Dictionary with schedule configuration

        Raises:
            ValueError: If no schedule is provided and the template has no schedule
        """
        if schedule is None and self.schedule is None:
            raise ValueError(
                "No schedule provided and template has no default schedule"
            )

        # Start with template values
        config = {
            "schedule": schedule or self.schedule,
            "timezone": self.timezone,
            "queue": self.queue,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "tags": self.tags.copy() if self.tags else [],
            "metadata": self.metadata.copy() if self.metadata else {},
        }

        # Apply overrides
        for key, value in overrides.items():
            if key in config:
                # Special handling for tags and metadata (merge instead of replace)
                if key == "tags" and value and config["tags"]:
                    config["tags"].extend(value)
                elif key == "metadata" and value and config["metadata"]:
                    config["metadata"].update(value)
                else:
                    config[key] = value

        return config
