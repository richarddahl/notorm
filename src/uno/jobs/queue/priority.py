"""Priority levels for job processing.

This module defines the priority levels used for job processing in the queue.
"""

from enum import IntEnum


class Priority(IntEnum):
    """Priority levels for jobs in the queue.
    
    Jobs with higher priority (lower numerical value) are processed before
    jobs with lower priority, regardless of when they were added to the queue.
    """
    
    CRITICAL = 0  # Highest priority, processed immediately
    HIGH = 10     # Higher than normal, but below critical
    NORMAL = 20   # Default priority level
    LOW = 30      # Lowest priority, processed when resources allow
    
    @classmethod
    def from_string(cls, priority_name: str) -> 'Priority':
        """Convert a string priority name to a Priority enum value.
        
        Args:
            priority_name: The name of the priority level (case-insensitive)
            
        Returns:
            Priority enum value
            
        Raises:
            ValueError: If the priority name is not valid
        """
        try:
            return cls[priority_name.upper()]
        except KeyError:
            valid_names = ", ".join(p.name.lower() for p in cls)
            raise ValueError(
                f"Invalid priority name: {priority_name}. "
                f"Valid values are: {valid_names}"
            )
