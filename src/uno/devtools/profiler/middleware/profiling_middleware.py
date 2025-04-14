"""
Profiling middleware for FastAPI applications.

This module provides middleware for collecting performance metrics from FastAPI applications,
including request/response timing, SQL query profiling, and resource utilization.
"""

import time
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Callable, Union, Set
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send, Message

from uno.devtools.profiler.core.collector import (
    QueryCollector, EndpointCollector, ResourceCollector, FunctionCollector
)

# Setup logging
logger = logging.getLogger(__name__)


class SQLQueryCapture:
    """
    Context manager for capturing SQL queries.
    
    This class allows capturing SQL queries from different database libraries
    by setting up appropriate hooks and monkey patching if necessary.
    """
    
    def __init__(self, collector: QueryCollector):
        """
        Initialize the capture.
        
        Args:
            collector: QueryCollector instance for storing metrics
        """
        self.collector = collector
        self.original_execute = None
        self.original_executemany = None
        self.original_async_execute = None
        self.original_asyncpg_execute = None
    
    def __enter__(self):
        """Set up hooks for capturing SQL queries."""
        # Try to set up psycopg2 hooks
        try:
            self._setup_psycopg2_hooks()
        except (ImportError, AttributeError):
            logger.debug("psycopg2 not available or hooks failed")
        
        # Try to set up psycopg3 hooks
        try:
            self._setup_psycopg3_hooks()
        except (ImportError, AttributeError):
            logger.debug("psycopg3 not available or hooks failed")
        
        # Try to set up asyncpg hooks
        try:
            self._setup_asyncpg_hooks()
        except (ImportError, AttributeError):
            logger.debug("asyncpg not available or hooks failed")
        
        # Try to set up SQLAlchemy hooks
        try:
            self._setup_sqlalchemy_hooks()
        except (ImportError, AttributeError):
            logger.debug("SQLAlchemy not available or hooks failed")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original functions."""
        # Restore psycopg2 hooks
        try:
            if hasattr(self, 'original_execute') and self.original_execute:
                import psycopg2.extensions
                psycopg2.extensions.cursor.execute = self.original_execute
                
            if hasattr(self, 'original_executemany') and self.original_executemany:
                import psycopg2.extensions
                psycopg2.extensions.cursor.executemany = self.original_executemany
        except (ImportError, AttributeError):
            pass
        
        # Restore asyncpg hooks
        try:
            if hasattr(self, 'original_asyncpg_execute') and self.original_asyncpg_execute:
                import asyncpg.connection
                asyncpg.connection.Connection.execute = self.original_asyncpg_execute
        except (ImportError, AttributeError):
            pass
        
        # No need to restore SQLAlchemy hooks, they use event listeners
    
    def _setup_psycopg2_hooks(self):
        """Set up hooks for capturing psycopg2 queries."""
        import psycopg2.extensions
        collector = self.collector
        
        # Save original methods
        self.original_execute = psycopg2.extensions.cursor.execute
        self.original_executemany = psycopg2.extensions.cursor.executemany
        
        # Define wrapped methods
        def execute_wrapper(cursor, query, vars=None):
            start_time = time.time()
            try:
                return self.original_execute(cursor, query, vars)
            finally:
                duration = time.time() - start_time
                collector.add_query(
                    query=query,
                    duration=duration,
                    params=vars,
                    db_name="psycopg2",
                    source="execute",
                )
        
        def executemany_wrapper(cursor, query, vars_list):
            start_time = time.time()
            try:
                return self.original_executemany(cursor, query, vars_list)
            finally:
                duration = time.time() - start_time
                collector.add_query(
                    query=query,
                    duration=duration,
                    params={"batch_size": len(vars_list) if vars_list else 0},
                    db_name="psycopg2",
                    source="executemany",
                )
        
        # Replace original methods
        psycopg2.extensions.cursor.execute = execute_wrapper
        psycopg2.extensions.cursor.executemany = executemany_wrapper
    
    def _setup_psycopg3_hooks(self):
        """Set up hooks for capturing psycopg3 queries."""
        # psycopg3 has a different API than psycopg2, so we need different hooks
        import psycopg
        from psycopg.connection import Connection
        from psycopg.cursor import Cursor
        collector = self.collector
        
        # We'll use the prepared statement execute hook
        original_execute_prepared = Cursor.execute
        
        def execute_prepared_wrapper(cursor, query, params=None, *args, **kwargs):
            start_time = time.time()
            try:
                return original_execute_prepared(cursor, query, params, *args, **kwargs)
            finally:
                duration = time.time() - start_time
                collector.add_query(
                    query=query,
                    duration=duration,
                    params=params,
                    db_name="psycopg3",
                    source="execute_prepared",
                )
        
        # Replace the method
        Cursor.execute = execute_prepared_wrapper
        
        # Save for restoration
        self.original_psycopg3_execute = original_execute_prepared
    
    def _setup_asyncpg_hooks(self):
        """Set up hooks for capturing asyncpg queries."""
        import asyncpg.connection
        import asyncio
        collector = self.collector
        
        # Save original execute method
        self.original_asyncpg_execute = asyncpg.connection.Connection.execute
        
        # Define wrapper for execute
        async def execute_wrapper(conn, query, *args, **kwargs):
            start_time = time.time()
            try:
                return await self.original_asyncpg_execute(conn, query, *args, **kwargs)
            finally:
                duration = time.time() - start_time
                collector.add_query(
                    query=query,
                    duration=duration,
                    params={"args": args, "kwargs": kwargs},
                    db_name="asyncpg",
                    source="execute",
                )
        
        # Replace the method
        asyncpg.connection.Connection.execute = execute_wrapper
    
    def _setup_sqlalchemy_hooks(self):
        """Set up hooks for capturing SQLAlchemy queries."""
        import sqlalchemy
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        collector = self.collector
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            conn.info.setdefault('query_statement', []).append(statement)
            conn.info.setdefault('query_parameters', []).append(parameters)
            conn.info.setdefault('query_executemany', []).append(executemany)
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            start_time = conn.info['query_start_time'].pop()
            statement = conn.info['query_statement'].pop()
            parameters = conn.info['query_parameters'].pop()
            executemany = conn.info['query_executemany'].pop()
            
            duration = time.time() - start_time
            collector.add_query(
                query=statement,
                duration=duration,
                params=parameters,
                db_name="sqlalchemy",
                source="cursor_execute" if not executemany else "cursor_executemany",
            )


class ProfilerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting profiling metrics from FastAPI applications.
    
    This middleware collects information about HTTP requests, SQL queries,
    and system resource utilization, and provides tools for analyzing performance.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        collect_sql: bool = True,
        collect_resources: bool = True,
        slow_request_threshold: float = 1.0,
        slow_query_threshold: float = 0.5,
        query_capacity: int = 1000,
        endpoint_capacity: int = 1000,
        resource_capacity: int = 1000,
        function_capacity: int = 1000,
        resource_collect_interval: int = 60,
        report_interval: Optional[int] = None,
        report_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
            enabled: Whether the middleware is enabled
            collect_sql: Whether to collect SQL query metrics
            collect_resources: Whether to collect resource metrics
            slow_request_threshold: Threshold in seconds for identifying slow requests
            slow_query_threshold: Threshold in seconds for identifying slow queries
            query_capacity: Maximum number of query metrics to store
            endpoint_capacity: Maximum number of endpoint metrics to store
            resource_capacity: Maximum number of resource metrics to store
            function_capacity: Maximum number of function metrics to store
            resource_collect_interval: Interval in seconds for collecting resource metrics
            report_interval: Interval in seconds for reporting metrics
            report_callback: Callback function for reporting metrics
        """
        super().__init__(app)
        self.enabled = enabled
        self.collect_sql = collect_sql
        self.collect_resources = collect_resources
        self.slow_request_threshold = slow_request_threshold
        self.slow_query_threshold = slow_query_threshold
        
        # Create collectors
        self.query_collector = QueryCollector(
            capacity=query_capacity,
            report_interval=report_interval,
            slow_query_threshold=slow_query_threshold,
        )
        
        self.endpoint_collector = EndpointCollector(
            capacity=endpoint_capacity,
            report_interval=report_interval,
            slow_endpoint_threshold=slow_request_threshold,
        )
        
        self.resource_collector = ResourceCollector(
            capacity=resource_capacity,
            report_interval=report_interval,
            collect_interval=resource_collect_interval,
        )
        
        self.function_collector = FunctionCollector(
            capacity=function_capacity,
            report_interval=report_interval,
        )
        
        # Start resource collection if enabled
        if self.enabled and self.collect_resources:
            self.resource_collector.start_collection()
        
        # Set up report callback if provided
        if report_callback and report_interval:
            if not hasattr(self, "_original_report_callback"):
                self._original_report_callback = report_callback
            
            # Create a wrapper to include all metrics
            def wrapped_report_callback(metrics):
                # Analyze metrics
                query_analysis = self.query_collector.analyze_queries()
                endpoint_analysis = self.endpoint_collector.analyze_endpoints()
                resource_analysis = self.resource_collector.analyze_resources()
                function_analysis = self.function_collector.analyze_functions()
                
                # Create report
                report = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "queries": query_analysis,
                    "endpoints": endpoint_analysis,
                    "resources": resource_analysis,
                    "functions": function_analysis,
                }
                
                # Call original callback
                self._original_report_callback(report)
            
            # Set report callback for each collector
            self.query_collector.report_callback = wrapped_report_callback
            self.endpoint_collector.report_callback = wrapped_report_callback
            self.resource_collector.report_callback = wrapped_report_callback
            self.function_collector.report_callback = wrapped_report_callback
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and collect metrics.
        
        Args:
            request: HTTP request
            call_next: Function to call the next middleware/application
            
        Returns:
            HTTP response
        """
        if not self.enabled:
            return await call_next(request)
        
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract request information
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else None
        
        # Get user ID from request if available
        user_id = None
        if hasattr(request, "user") and request.user:
            user_id = str(getattr(request.user, "id", None))
        
        # Initialize a query counter for this request
        query_count = 0
        query_time = 0.0
        
        # Set up SQL query capture if enabled
        if self.collect_sql:
            sql_capture = SQLQueryCapture(self.query_collector)
            sql_capture.__enter__()
        else:
            sql_capture = None
        
        try:
            # Measure request time
            start_time = time.time()
            
            # Process request
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Get response information
            status_code = response.status_code
            response_size = len(response.body) if hasattr(response, "body") else None
            
            # Log slow requests
            if duration >= self.slow_request_threshold:
                logger.warning(f"Slow request detected ({duration:.3f}s): {method} {path}")
            
            # Get query count and time if available
            if hasattr(request.state, "query_count"):
                query_count = request.state.query_count
            
            if hasattr(request.state, "query_time"):
                query_time = request.state.query_time
            
            # Create endpoint metric
            self.endpoint_collector.add_endpoint_metric(
                path=path,
                method=method,
                duration=duration,
                status_code=status_code,
                user_id=user_id,
                request_id=request_id,
                query_count=query_count,
                query_time=query_time,
                response_size=response_size,
                client_ip=client_ip,
            )
            
            return response
        
        finally:
            # Clean up SQL query capture
            if sql_capture:
                sql_capture.__exit__(None, None, None)
    
    def profile_function(self, func: Callable) -> Callable:
        """
        Decorator for profiling functions.
        
        Args:
            func: Function to profile
            
        Returns:
            Wrapped function
        """
        if not self.enabled:
            return func
        
        return self.function_collector.profile_function(func)
    
    def get_analysis(self) -> Dict[str, Any]:
        """
        Get a comprehensive analysis of all collected metrics.
        
        Returns:
            Dictionary with analysis results
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Profiler is disabled",
            }
        
        # Analyze metrics
        query_analysis = self.query_collector.analyze_queries()
        endpoint_analysis = self.endpoint_collector.analyze_endpoints()
        resource_analysis = self.resource_collector.analyze_resources()
        function_analysis = self.function_collector.analyze_functions()
        
        # Create report
        return {
            "enabled": True,
            "timestamp": datetime.utcnow().isoformat(),
            "queries": query_analysis,
            "endpoints": endpoint_analysis,
            "resources": resource_analysis,
            "functions": function_analysis,
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        if not self.enabled:
            return
        
        self.query_collector.clear_metrics()
        self.endpoint_collector.clear_metrics()
        self.resource_collector.clear_metrics()
        self.function_collector.clear_metrics()
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, "resource_collector") and self.resource_collector:
            self.resource_collector.stop_collection()


class DebugResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding profiling information to responses.
    
    This middleware adds profiling information to JSON responses for debugging.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        profiler: ProfilerMiddleware,
        enabled: bool = False,
        debug_header: str = "X-Debug-Profile",
        include_request_header: str = "X-Include-Profile",
    ):
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
            profiler: ProfilerMiddleware instance
            enabled: Whether to enable debug information by default
            debug_header: Header to send with debug information
            include_request_header: Header in request to include debug information
        """
        super().__init__(app)
        self.profiler = profiler
        self.enabled = enabled
        self.debug_header = debug_header
        self.include_request_header = include_request_header
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and add debug information to the response.
        
        Args:
            request: HTTP request
            call_next: Function to call the next middleware/application
            
        Returns:
            HTTP response
        """
        # Check if debug information should be included
        include_debug = self.enabled
        if self.include_request_header in request.headers:
            include_debug = request.headers[self.include_request_header].lower() in ("true", "1", "yes")
        
        # Process request
        response = await call_next(request)
        
        # Add debug information if enabled and response is JSON
        if include_debug and isinstance(response, JSONResponse):
            # Get profiling analysis
            analysis = self.profiler.get_analysis()
            
            # Add header with link to profiling information
            response.headers[self.debug_header] = "/profiler/dashboard"
            
            # Add debug information to response if JSON
            if isinstance(response, JSONResponse):
                data = response.body.decode("utf-8")
                try:
                    json_data = json.loads(data)
                    if isinstance(json_data, dict):
                        json_data["__debug"] = {
                            "request_id": getattr(request.state, "request_id", None),
                            "queries": {
                                "count": analysis["queries"].get("total_queries", 0),
                                "slow_count": len(analysis["queries"].get("slow_queries", [])),
                            },
                            "endpoints": {
                                "path": request.url.path,
                                "method": request.method,
                                "status_code": response.status_code,
                            },
                            "profile_link": "/profiler/dashboard",
                        }
                        response.body = json.dumps(json_data).encode("utf-8")
                except Exception as e:
                    logger.warning(f"Failed to add debug information to response: {e}")
        
        return response