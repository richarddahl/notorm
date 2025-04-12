"""Context utilities for tasks in the background processing system.

This module provides utilities for accessing contextual information during
task execution.
"""

from typing import Any, Dict, Optional
import contextvars

# Context variable for the current job
_current_job = contextvars.ContextVar[Optional[Dict[str, Any]]]("current_job", default=None)


def get_current_job() -> Optional[Dict[str, Any]]:
    """Get the job context for the currently executing task.
    
    Returns:
        The job context or None if not in a task context
    """
    return _current_job.get()


def set_current_job(job: Dict[str, Any]) -> contextvars.Token:
    """Set the job context for the current task execution.
    
    Args:
        job: The job context
        
    Returns:
        Token for resetting the context variable
    """
    return _current_job.set(job)


def reset_current_job(token: contextvars.Token) -> None:
    """Reset the job context using a token.
    
    Args:
        token: Token from set_current_job
    """
    _current_job.reset(token)