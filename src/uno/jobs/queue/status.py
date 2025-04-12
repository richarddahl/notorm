"""Job status definitions for the queue system.

This module defines the possible states of a job during its lifecycle.
"""

from enum import Enum, auto


class JobStatus(Enum):
    """Status values for jobs in the queue system.
    
    Jobs move through these states during their lifecycle, from creation
    to completion or failure.
    """
    
    PENDING = auto()    # Job is waiting in the queue
    RESERVED = auto()   # Job has been claimed by a worker but not yet started
    RUNNING = auto()    # Job is currently being processed
    COMPLETED = auto()  # Job has finished successfully
    FAILED = auto()     # Job has encountered an error
    RETRYING = auto()   # Job failed but will be retried
    CANCELLED = auto()  # Job was manually cancelled before completion
    TIMEOUT = auto()    # Job exceeded its execution time limit
    
    @property
    def is_terminal(self) -> bool:
        """Check if this status is a terminal state.
        
        Terminal states are those where the job has finished processing
        and will not be processed further.
        
        Returns:
            True if the status is terminal, False otherwise
        """
        return self in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT
        )
    
    @property
    def is_active(self) -> bool:
        """Check if this status represents an active job.
        
        Active states are those where the job is currently being processed
        or is about to be processed.
        
        Returns:
            True if the status is active, False otherwise
        """
        return self in (
            JobStatus.RESERVED,
            JobStatus.RUNNING,
            JobStatus.RETRYING
        )
    
    @property
    def is_pending(self) -> bool:
        """Check if this status represents a pending job.
        
        Pending jobs are those waiting to be processed.
        
        Returns:
            True if the status is pending, False otherwise
        """
        return self == JobStatus.PENDING
    
    @property
    def is_successful(self) -> bool:
        """Check if this status represents a successful job.
        
        Returns:
            True if the job completed successfully, False otherwise
        """
        return self == JobStatus.COMPLETED
