from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from uno.core.errors.monitoring import error_aggregator
from uno.core.errors.framework import FrameworkError

router = APIRouter(prefix="/api/errors", tags=["Error Dashboard"])

class ErrorStats:
    """Class for error statistics."""
    
    def __init__(self):
        self.error_count = 0
        self.error_types: Dict[str, int] = {}
        self.error_severities: Dict[str, int] = {}
        self.error_categories: Dict[str, int] = {}
        
    def update_from_error(self, error: FrameworkError) -> None:
        """Update statistics from an error."""
        self.error_count += 1
        self.error_types[error.code] = self.error_types.get(error.code, 0) + 1
        self.error_severities[error.severity.value] = self.error_severities.get(error.severity.value, 0) + 1
        self.error_categories[error.category.value] = self.error_categories.get(error.category.value, 0) + 1

class ErrorDashboard:
    """Class for managing error dashboard data."""
    
    def __init__(self):
        self.stats = ErrorStats()
        self.error_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
    def add_error(self, error: FrameworkError, context: Optional[Dict[str, Any]] = None) -> None:
        """Add an error to the dashboard."""
        self.stats.update_from_error(error)
        
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "code": error.code,
            "message": error.message,
            "severity": error.severity.value,
            "category": error.category.value,
            "context": context or {}
        }
        
        self.error_history.append(error_entry)
        
        # Maintain history size
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
            
    def get_error_trends(self, timeframe: str = "hour") -> Dict[str, Any]:
        """Get error trends for a given timeframe."""
        now = datetime.utcnow()
        
        if timeframe == "hour":
            start_time = now - timedelta(hours=1)
        elif timeframe == "day":
            start_time = now - timedelta(days=1)
        else:
            start_time = now - timedelta(days=7)
            
        recent_errors = [
            err for err in self.error_history
            if datetime.fromisoformat(err["timestamp"]) >= start_time
        ]
        
        return {
            "timeframe": timeframe,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "error_count": len(recent_errors),
            "error_types": self._count_by_field(recent_errors, "code"),
            "error_severities": self._count_by_field(recent_errors, "severity"),
            "error_categories": self._count_by_field(recent_errors, "category")
        }
        
    def _count_by_field(self, errors: List[Dict[str, Any]], field: str) -> Dict[str, int]:
        """Count occurrences of unique values in a field."""
        counts: Dict[str, int] = {}
        for error in errors:
            value = error.get(field)
            if value:
                counts[value] = counts.get(value, 0) + 1
        return counts

# Create singleton instance
dashboard = ErrorDashboard()

@router.get("/stats")
async def get_error_stats():
    """Get current error statistics."""
    return JSONResponse({
        "total_errors": dashboard.stats.error_count,
        "error_types": dashboard.stats.error_types,
        "error_severities": dashboard.stats.error_severities,
        "error_categories": dashboard.stats.error_categories,
        "last_updated": datetime.utcnow().isoformat()
    })

@router.get("/trends")
async def get_error_trends(timeframe: str = "hour"):
    """Get error trends over time."""
    return JSONResponse(dashboard.get_error_trends(timeframe))

@router.get("/history")
async def get_error_history(limit: int = 100):
    """Get recent error history."""
    return JSONResponse({
        "errors": dashboard.error_history[-limit:],
        "total_count": len(dashboard.error_history)
    })
