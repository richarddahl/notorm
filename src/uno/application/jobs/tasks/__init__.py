"""Task definition and execution for the background processing system.

This package provides tools for defining tasks, configuring their behavior,
and composing them into workflows.
"""

from uno.jobs.tasks.task import task, Task, TaskRegistry
from uno.jobs.tasks.workflow import chain, group
from uno.jobs.tasks.middleware import TaskMiddleware, register_middleware
from uno.jobs.tasks.context import get_current_job

__all__ = [
    "task",
    "Task",
    "TaskRegistry",
    "chain",
    "group",
    "TaskMiddleware",
    "register_middleware",
    "get_current_job",
]
