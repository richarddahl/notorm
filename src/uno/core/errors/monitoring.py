from typing import Dict, Any, Optional
from datetime import datetime
import logging
from uno.core.errors.framework import FrameworkError


class ErrorMonitor:
    """Class for monitoring and tracking errors."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_count = 0
        self.error_types: Dict[str, int] = {}
        
    def track_error(self, error: FrameworkError, context: Optional[Dict[str, Any]] = None) -> None:
        """Track an error occurrence."""
        self.error_count += 1
        
        # Track error type
        error_type = error.code
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        
        # Log error with context
        error_context = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error.code,
            "error_message": error.message,
            "error_category": error.category.value,
            "error_severity": error.severity.value,
            **(context or {})
        }
        
        # Log error based on severity
        if error.severity == FrameworkError.ErrorSeverity.ERROR:
            self.logger.error(f"Error occurred: {error_context}")
        elif error.severity == FrameworkError.ErrorSeverity.WARNING:
            self.logger.warning(f"Warning: {error_context}")
        else:
            self.logger.info(f"Info: {error_context}")
            
    def get_error_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked errors."""
        return {
            "total_errors": self.error_count,
            "error_types": self.error_types,
            "last_updated": datetime.utcnow().isoformat()
        }


class ErrorAggregator:
    """Class for aggregating and analyzing errors."""
    
    def __init__(self):
        self.monitor = ErrorMonitor()
        self.error_patterns: Dict[str, int] = {}
        
    def analyze_errors(self, timeframe: str = "hour") -> Dict[str, Any]:
        """Analyze errors within a specified timeframe."""
        # TODO: Implement actual error analysis logic
        return {
            "total_errors": self.monitor.error_count,
            "error_types": self.monitor.error_types,
            "timeframe": timeframe
        }

    def get_error_patterns(self) -> Dict[str, int]:
        """Get patterns of common errors."""
        return self.error_patterns

# Create singleton instance
error_aggregator = ErrorAggregator()
