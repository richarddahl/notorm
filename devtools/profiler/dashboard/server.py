"""
FastAPI server for the performance profiling dashboard.

This module provides a FastAPI application for serving the performance profiling dashboard,
which displays metrics collected by the profiling middleware.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta, UTC

from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uno.devtools.profiler.middleware.profiling_middleware import ProfilerMiddleware

# Set up logging
logger = logging.getLogger(__name__)

# Templates directory - relative to this file
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "profiler"
STATIC_DIR = TEMPLATE_DIR / "static"

# Create directories if they don't exist
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Uno Profiler Dashboard",
    description="Performance profiling dashboard for Uno applications",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Set up templates
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Store profiler middleware instance
_profiler_middleware = None


def get_profiler() -> ProfilerMiddleware:
    """
    Get the profiler middleware instance.
    
    Returns:
        ProfilerMiddleware instance
    
    Raises:
        HTTPException: If profiler middleware is not configured
    """
    if _profiler_middleware is None:
        raise HTTPException(
            status_code=500,
            detail="Profiler middleware not configured. Initialize the dashboard with a profiler instance."
        )
    return _profiler_middleware


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve the dashboard index page.
    
    Args:
        request: FastAPI request
        
    Returns:
        HTML response
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Uno Profiler Dashboard"}
    )


@app.get("/api/metrics/summary")
async def get_metrics_summary(profiler: ProfilerMiddleware = Depends(get_profiler)):
    """
    Get a summary of all metrics.
    
    Args:
        profiler: ProfilerMiddleware instance
        
    Returns:
        Dictionary with metrics summary
    """
    analysis = profiler.get_analysis()
    
    # Create summary
    summary = {
        "timestamp": analysis.get("timestamp"),
        "queries": {
            "total": analysis.get("queries", {}).get("total_queries", 0),
            "unique_patterns": analysis.get("queries", {}).get("unique_patterns", 0),
            "slow_count": len(analysis.get("queries", {}).get("slow_queries", [])),
        },
        "endpoints": {
            "total": analysis.get("endpoints", {}).get("total_endpoints", 0),
            "total_requests": analysis.get("endpoints", {}).get("total_requests", 0),
            "slow_count": len(analysis.get("endpoints", {}).get("slow_endpoints", [])),
            "error_prone_count": len(analysis.get("endpoints", {}).get("error_prone_endpoints", [])),
        },
        "resources": {
            "memory": {
                "latest_percent": (
                    analysis.get("resources", {})
                    .get("memory", {})
                    .get("latest", {})
                    .get("percent", 0)
                ),
                "latest_process_percent": (
                    analysis.get("resources", {})
                    .get("memory", {})
                    .get("latest", {})
                    .get("process_percent", 0)
                ),
            },
            "cpu": {
                "latest_percent": (
                    analysis.get("resources", {})
                    .get("cpu", {})
                    .get("latest", {})
                    .get("percent", 0)
                ),
                "latest_process_percent": (
                    analysis.get("resources", {})
                    .get("cpu", {})
                    .get("latest", {})
                    .get("process_percent", 0)
                ),
            },
        },
        "functions": {
            "total": analysis.get("functions", {}).get("total_functions", 0),
            "total_calls": analysis.get("functions", {}).get("total_calls", 0),
            "slow_count": len(analysis.get("functions", {}).get("slow_functions", [])),
            "hotspot_count": len(analysis.get("functions", {}).get("hotspots", [])),
        },
    }
    
    return summary


@app.get("/api/metrics/queries")
async def get_query_metrics(
    profiler: ProfilerMiddleware = Depends(get_profiler),
    limit: int = Query(20, ge=1, le=100),
    include_patterns: bool = Query(False),
    include_slow: bool = Query(True),
    include_n_plus_1: bool = Query(True),
):
    """
    Get query metrics.
    
    Args:
        profiler: ProfilerMiddleware instance
        limit: Maximum number of results to return
        include_patterns: Whether to include query patterns
        include_slow: Whether to include slow queries
        include_n_plus_1: Whether to include N+1 query candidates
        
    Returns:
        Dictionary with query metrics
    """
    analysis = profiler.get_analysis()
    queries = analysis.get("queries", {})
    
    result = {
        "total_queries": queries.get("total_queries", 0),
        "unique_patterns": queries.get("unique_patterns", 0),
    }
    
    if include_slow:
        result["slow_queries"] = queries.get("slow_queries", [])[:limit]
    
    if include_n_plus_1:
        result["n_plus_1_candidates"] = list(queries.get("n_plus_1_candidates", {}).values())[:limit]
    
    if include_patterns:
        # Sort patterns by avg duration (highest first)
        patterns = queries.get("patterns", {})
        sorted_patterns = sorted(
            patterns.items(),
            key=lambda x: x[1]["avg"],
            reverse=True
        )
        result["patterns"] = dict(sorted_patterns[:limit])
    
    return result


@app.get("/api/metrics/endpoints")
async def get_endpoint_metrics(
    profiler: ProfilerMiddleware = Depends(get_profiler),
    limit: int = Query(20, ge=1, le=100),
    include_stats: bool = Query(False),
    include_slow: bool = Query(True),
    include_error_prone: bool = Query(True),
):
    """
    Get endpoint metrics.
    
    Args:
        profiler: ProfilerMiddleware instance
        limit: Maximum number of results to return
        include_stats: Whether to include endpoint statistics
        include_slow: Whether to include slow endpoints
        include_error_prone: Whether to include error-prone endpoints
        
    Returns:
        Dictionary with endpoint metrics
    """
    analysis = profiler.get_analysis()
    endpoints = analysis.get("endpoints", {})
    
    result = {
        "total_endpoints": endpoints.get("total_endpoints", 0),
        "total_requests": endpoints.get("total_requests", 0),
    }
    
    if include_slow:
        result["slow_endpoints"] = endpoints.get("slow_endpoints", [])[:limit]
    
    if include_error_prone:
        result["error_prone_endpoints"] = endpoints.get("error_prone_endpoints", [])[:limit]
    
    if include_stats:
        # Sort endpoint stats by avg duration (highest first)
        stats = endpoints.get("endpoint_stats", {})
        sorted_stats = sorted(
            stats.items(),
            key=lambda x: x[1]["avg"],
            reverse=True
        )
        result["endpoint_stats"] = dict(sorted_stats[:limit])
    
    return result


@app.get("/api/metrics/resources")
async def get_resource_metrics(
    profiler: ProfilerMiddleware = Depends(get_profiler),
    window: str = Query("1h", regex=r"^\d+[mhdw]$"),
):
    """
    Get resource metrics.
    
    Args:
        profiler: ProfilerMiddleware instance
        window: Time window to get metrics for (e.g. "5m", "1h", "1d", "1w")
        
    Returns:
        Dictionary with resource metrics
    """
    analysis = profiler.get_analysis()
    resources = analysis.get("resources", {})
    
    # Parse time window
    match = re.match(r"^(\d+)([mhdw])$", window)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid time window format. Must be in the format <number><unit>, e.g. 5m, 1h, 1d, 1w"
        )
    
    value = int(match.group(1))
    unit = match.group(2)
    
    # Convert to timedelta
    if unit == "m":
        delta = timedelta(minutes=value)
    elif unit == "h":
        delta = timedelta(hours=value)
    elif unit == "d":
        delta = timedelta(days=value)
    elif unit == "w":
        delta = timedelta(weeks=value)
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid time window unit. Must be one of m, h, d, w"
        )
    
    # Filter metrics by time window
    if not hasattr(profiler, "resource_collector"):
        return resources
    
    # Get raw metrics for the time window
    memory_metrics = profiler.resource_collector.get_memory_metrics()
    cpu_metrics = profiler.resource_collector.get_cpu_metrics()
    
    # Convert to time series
    memory_series = []
    cpu_series = []
    cutoff_time = datetime.now(datetime.UTC) - delta
    
    for metric in memory_metrics:
        if metric.timestamp >= cutoff_time:
            memory_series.append({
                "timestamp": metric.timestamp.isoformat(),
                "percent": metric.percent,
                "process_percent": metric.process_percent,
            })
    
    for metric in cpu_metrics:
        if metric.timestamp >= cutoff_time:
            cpu_series.append({
                "timestamp": metric.timestamp.isoformat(),
                "percent": metric.percent,
                "process_percent": metric.process_percent,
            })
    
    return {
        "memory": {
            "latest": resources.get("memory", {}).get("latest"),
            "avg_percent": resources.get("memory", {}).get("avg_percent"),
            "max_percent": resources.get("memory", {}).get("max_percent"),
            "avg_process_percent": resources.get("memory", {}).get("avg_process_percent"),
            "max_process_percent": resources.get("memory", {}).get("max_process_percent"),
            "series": memory_series,
        },
        "cpu": {
            "latest": resources.get("cpu", {}).get("latest"),
            "avg_percent": resources.get("cpu", {}).get("avg_percent"),
            "max_percent": resources.get("cpu", {}).get("max_percent"),
            "avg_process_percent": resources.get("cpu", {}).get("avg_process_percent"),
            "max_process_percent": resources.get("cpu", {}).get("max_process_percent"),
            "series": cpu_series,
        },
    }


@app.get("/api/metrics/functions")
async def get_function_metrics(
    profiler: ProfilerMiddleware = Depends(get_profiler),
    limit: int = Query(20, ge=1, le=100),
    include_stats: bool = Query(False),
    include_slow: bool = Query(True),
    include_hotspots: bool = Query(True),
):
    """
    Get function metrics.
    
    Args:
        profiler: ProfilerMiddleware instance
        limit: Maximum number of results to return
        include_stats: Whether to include function statistics
        include_slow: Whether to include slow functions
        include_hotspots: Whether to include hotspot functions
        
    Returns:
        Dictionary with function metrics
    """
    analysis = profiler.get_analysis()
    functions = analysis.get("functions", {})
    
    result = {
        "total_functions": functions.get("total_functions", 0),
        "total_calls": functions.get("total_calls", 0),
    }
    
    if include_slow:
        result["slow_functions"] = functions.get("slow_functions", [])[:limit]
    
    if include_hotspots:
        result["hotspots"] = functions.get("hotspots", [])[:limit]
    
    if include_stats:
        # Sort function stats by avg duration (highest first)
        stats = functions.get("function_stats", {})
        sorted_stats = sorted(
            stats.items(),
            key=lambda x: x[1]["avg"],
            reverse=True
        )
        result["function_stats"] = dict(sorted_stats[:limit])
    
    return result


@app.post("/api/metrics/reset")
async def reset_metrics(profiler: ProfilerMiddleware = Depends(get_profiler)):
    """
    Reset all metrics.
    
    Args:
        profiler: ProfilerMiddleware instance
        
    Returns:
        Success message
    """
    profiler.reset_metrics()
    return {"status": "success", "message": "Metrics reset successfully"}


def initialize_dashboard(
    profiler_middleware: ProfilerMiddleware,
    host: str = "localhost",
    port: int = 8081,
    open_browser: bool = True,
):
    """
    Initialize and start the profiler dashboard.
    
    Args:
        profiler_middleware: ProfilerMiddleware instance
        host: Host to bind to
        port: Port to bind to
        open_browser: Whether to open a browser window
    """
    global _profiler_middleware
    _profiler_middleware = profiler_middleware
    
    try:
        import uvicorn
        import threading
        import time
        
        def run_server():
            uvicorn.run(app, host=host, port=port)
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Open browser if requested
        if open_browser:
            import webbrowser
            time.sleep(1.0)  # Wait for server to start
            webbrowser.open(f"http://{host}:{port}")
        
        print(f"Profiler dashboard running at http://{host}:{port}")
        print("Press Ctrl+C to stop")
        
        # Keep the main thread alive
        while True:
            time.sleep(1.0)
    
    except KeyboardInterrupt:
        print("Stopping profiler dashboard...")
    except Exception as e:
        logger.exception(f"Error starting profiler dashboard: {e}")


if __name__ == "__main__":
    # If run directly, try to load an existing profiler middleware
    # This is mainly for development/testing
    try:
        from uno.devtools.profiler.middleware.profiling_middleware import ProfilerMiddleware
        
        # Create a dummy profiler middleware
        dummy_profiler = ProfilerMiddleware(app=None)
        
        # Initialize the dashboard
        initialize_dashboard(
            profiler_middleware=dummy_profiler,
            host="localhost",
            port=8081,
            open_browser=True,
        )
    except ImportError:
        print("Failed to load profiling middleware. Please install the required dependencies.")
        import sys
        sys.exit(1)