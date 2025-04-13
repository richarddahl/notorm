"""
FastAPI middleware for debugging Uno applications.

This module provides a debug middleware that can be added to FastAPI applications to
enhance debugging capabilities, including request/response logging, timing, SQL query tracking,
dependency tracking, and error handling.
"""

import time
import inspect
import json
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from contextlib import contextmanager

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from uno.core.errors.base import UnoError
from uno.database.db_manager import get_db_manager


logger = logging.getLogger("uno.debug")


class DebugMiddleware(BaseHTTPMiddleware):
    """Middleware for debugging FastAPI applications with Uno.
    
    Features:
    - Request/response logging
    - Request timing
    - SQL query tracking
    - Dependency tracking
    - Error enhancement
    - Custom debug headers
    """
    
    def __init__(
        self,
        app: FastAPI,
        enable_request_logging: bool = True,
        enable_sql_tracking: bool = True,
        enable_dependency_tracking: bool = True,
        enable_error_enhancement: bool = True,
        exclude_paths: Optional[List[str]] = None,
        debug_headers: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        pretty_json: bool = True,
        max_body_length: int = 10000,
    ):
        """Initialize the debug middleware.
        
        Args:
            app: The FastAPI application
            enable_request_logging: Whether to log requests and responses
            enable_sql_tracking: Whether to track SQL queries
            enable_dependency_tracking: Whether to track dependencies
            enable_error_enhancement: Whether to enhance error information
            exclude_paths: Paths to exclude from debugging (e.g., ["/docs", "/openapi.json"])
            debug_headers: Whether to add debug headers to responses
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            pretty_json: Whether to pretty-print JSON in logs
            max_body_length: Maximum length to log for request/response bodies
        """
        super().__init__(app)
        self.enable_request_logging = enable_request_logging
        self.enable_sql_tracking = enable_sql_tracking
        self.enable_dependency_tracking = enable_dependency_tracking
        self.enable_error_enhancement = enable_error_enhancement
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/redoc", "/static"]
        self.debug_headers = debug_headers
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.pretty_json = pretty_json
        self.max_body_length = max_body_length
        
        # Setup SQL query tracking
        if self.enable_sql_tracking:
            try:
                from uno.devtools.debugging.sql_debug import setup_sql_tracking
                self.sql_tracker = setup_sql_tracking()
            except ImportError:
                logger.warning("SQL tracking not available - required modules not found")
                self.enable_sql_tracking = False
        
        # Setup dependency tracking
        if self.enable_dependency_tracking:
            try:
                # Legacy dependency tracking removed as part of backward compatibility cleanup
                self.enable_dependency_tracking = False
            except ImportError:
                logger.warning("Dependency tracking not available - container not accessible")
                self.enable_dependency_tracking = False
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response from the endpoint
        """
        # Skip debugging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Initialize debug context
        debug_info = {
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None,
            },
            "timing": {
                "start_time": time.time(),
                "end_time": None,
                "duration_ms": None,
            },
            "sql_queries": [],
            "dependencies": [],
            "errors": [],
        }
        
        # Log request body if enabled
        if self.enable_request_logging and self.log_request_body:
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if len(body) > 0:
                        try:
                            json_body = json.loads(body)
                            debug_info["request"]["body"] = self._truncate_data(
                                json_body, pretty=self.pretty_json
                            )
                        except json.JSONDecodeError:
                            debug_info["request"]["body"] = f"<non-JSON body of length {len(body)}>"
                except Exception as e:
                    debug_info["request"]["body"] = f"<error reading body: {str(e)}>"
        
        # Start SQL tracking if enabled
        if self.enable_sql_tracking:
            with self._track_sql_queries(debug_info["sql_queries"]):
                response = await self._process_request(request, call_next, debug_info)
        else:
            response = await self._process_request(request, call_next, debug_info)
        
        # Add debug headers if enabled
        if self.debug_headers:
            response.headers["X-Debug-Time-Ms"] = str(int(debug_info["timing"]["duration_ms"]))
            response.headers["X-Debug-SQL-Queries"] = str(len(debug_info["sql_queries"]))
            if debug_info["errors"]:
                response.headers["X-Debug-Errors"] = str(len(debug_info["errors"]))
        
        # Log complete debug info
        if self.enable_request_logging:
            self._log_debug_info(debug_info, response)
        
        return response
    
    async def _process_request(
        self, request: Request, call_next: RequestResponseEndpoint, debug_info: Dict[str, Any]
    ) -> Response:
        """Process the request and capture debug information.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            debug_info: Dictionary to store debug information
            
        Returns:
            The response from the endpoint
        """
        try:
            # Track dependencies if enabled
            if self.enable_dependency_tracking:
                with self._track_dependencies(debug_info["dependencies"]):
                    response = await call_next(request)
            else:
                response = await call_next(request)
            
            # Record timing
            debug_info["timing"]["end_time"] = time.time()
            debug_info["timing"]["duration_ms"] = (
                debug_info["timing"]["end_time"] - debug_info["timing"]["start_time"]
            ) * 1000
            
            # Log response body if enabled
            if self.enable_request_logging and self.log_response_body:
                if hasattr(response, "body"):
                    body = response.body
                    if body:
                        try:
                            json_body = json.loads(body)
                            debug_info["response"] = {
                                "status_code": response.status_code,
                                "body": self._truncate_data(json_body, pretty=self.pretty_json),
                            }
                        except json.JSONDecodeError:
                            debug_info["response"] = {
                                "status_code": response.status_code,
                                "body": f"<non-JSON body of length {len(body)}>",
                            }
                    else:
                        debug_info["response"] = {
                            "status_code": response.status_code,
                            "body": "<empty body>",
                        }
                else:
                    debug_info["response"] = {
                        "status_code": response.status_code,
                        "body": "<no body attribute>",
                    }
            else:
                debug_info["response"] = {
                    "status_code": response.status_code,
                }
            
            return response
        
        except Exception as exc:
            # Record timing for error case
            debug_info["timing"]["end_time"] = time.time()
            debug_info["timing"]["duration_ms"] = (
                debug_info["timing"]["end_time"] - debug_info["timing"]["start_time"]
            ) * 1000
            
            # Enhance error information if enabled
            if self.enable_error_enhancement:
                error_info = self._enhance_error(exc)
                debug_info["errors"].append(error_info)
                
                # Create enhanced error response
                if isinstance(exc, UnoError):
                    status_code = exc.status_code
                    error_content = {
                        "error": exc.error_code,
                        "message": str(exc),
                        "detail": exc.detail if hasattr(exc, "detail") else None,
                        "context": exc.context if hasattr(exc, "context") else None,
                    }
                else:
                    status_code = 500
                    error_content = {
                        "error": "internal_server_error",
                        "message": str(exc),
                        "detail": error_info.get("traceback"),
                    }
                
                response = JSONResponse(
                    status_code=status_code,
                    content=error_content,
                )
                
                debug_info["response"] = {
                    "status_code": status_code,
                    "body": error_content,
                }
                
                # Log error
                logger.error(
                    f"Error processing request: {error_info['error_type']}: {error_info['message']}",
                    exc_info=exc,
                )
                
                return response
            
            # Re-raise if error enhancement is disabled
            raise
    
    def _enhance_error(self, exc: Exception) -> Dict[str, Any]:
        """Enhance error information with additional context.
        
        Args:
            exc: The exception to enhance
            
        Returns:
            Dictionary with enhanced error information
        """
        tb = traceback.extract_tb(exc.__traceback__)
        frames = []
        
        for frame in tb:
            frames.append({
                "filename": frame.filename,
                "lineno": frame.lineno,
                "name": frame.name,
                "line": frame.line,
            })
        
        error_info = {
            "error_type": exc.__class__.__name__,
            "message": str(exc),
            "traceback": frames,
            "module": exc.__class__.__module__,
        }
        
        # Add Uno specific error information
        if isinstance(exc, UnoError):
            error_info.update({
                "error_code": getattr(exc, "error_code", None),
                "status_code": getattr(exc, "status_code", 500),
                "detail": getattr(exc, "detail", None),
                "context": getattr(exc, "context", None),
            })
        
        return error_info
    
    def _log_debug_info(self, debug_info: Dict[str, Any], response: Response) -> None:
        """Log debug information for a request.
        
        Args:
            debug_info: The debug information to log
            response: The response from the endpoint
        """
        # Basic request info
        log_message = (
            f"\n{'-' * 80}\n"
            f"DEBUG: {debug_info['request']['method']} {debug_info['request']['path']} "
            f"- {debug_info['response']['status_code']} "
            f"({debug_info['timing']['duration_ms']:.2f}ms)"
        )
        
        # SQL query info
        if self.enable_sql_tracking:
            sql_count = len(debug_info["sql_queries"])
            if sql_count > 0:
                total_sql_time = sum(q.get("duration_ms", 0) for q in debug_info["sql_queries"])
                log_message += f"\nSQL Queries: {sql_count} ({total_sql_time:.2f}ms)"
                
                # Top 5 slowest queries
                if sql_count > 1:
                    slowest = sorted(
                        debug_info["sql_queries"],
                        key=lambda q: q.get("duration_ms", 0),
                        reverse=True,
                    )[:5]
                    
                    log_message += "\nTop 5 slowest queries:"
                    for i, query in enumerate(slowest, 1):
                        log_message += (
                            f"\n  {i}. {query.get('duration_ms', 0):.2f}ms: "
                            f"{query.get('query', '')[:100]}..."
                        )
        
        # Dependencies info
        if self.enable_dependency_tracking and debug_info["dependencies"]:
            log_message += f"\nDependencies: {len(debug_info['dependencies'])}"
            
            # Top 5 slowest dependencies
            deps = sorted(
                debug_info["dependencies"],
                key=lambda d: d.get("duration_ms", 0),
                reverse=True,
            )[:5]
            
            log_message += "\nTop 5 slowest dependencies:"
            for i, dep in enumerate(deps, 1):
                log_message += (
                    f"\n  {i}. {dep.get('duration_ms', 0):.2f}ms: "
                    f"{dep.get('name', 'Unknown')}"
                )
        
        # Error info
        if debug_info["errors"]:
            log_message += f"\nErrors: {len(debug_info['errors'])}"
            for i, error in enumerate(debug_info["errors"], 1):
                log_message += (
                    f"\n  {i}. {error.get('error_type', 'Unknown')}: "
                    f"{error.get('message', 'No message')}"
                )
        
        log_message += f"\n{'-' * 80}"
        logger.debug(log_message)
    
    def _truncate_data(self, data: Any, pretty: bool = True) -> str:
        """Truncate data for logging purposes.
        
        Args:
            data: The data to truncate
            pretty: Whether to pretty-print JSON
            
        Returns:
            Truncated string representation of the data
        """
        if pretty:
            result = json.dumps(data, indent=2, default=str)
        else:
            result = json.dumps(data, default=str)
        
        if len(result) > self.max_body_length:
            return result[:(self.max_body_length - 3)] + "..."
        
        return result
    
    @contextmanager
    def _track_sql_queries(self, queries_list: List[Dict[str, Any]]) -> None:
        """Context manager to track SQL queries.
        
        Args:
            queries_list: List to append SQL queries to
        """
        if not self.enable_sql_tracking:
            yield
            return
        
        original_execute = None
        
        try:
            # Get the database connections
            db_manager = get_db_manager()
            if hasattr(db_manager, "engine") and hasattr(db_manager.engine, "execute"):
                # Store original execute method
                original_execute = db_manager.engine.execute
                
                # Create tracking execute method
                def tracking_execute(query, *args, **kwargs):
                    start_time = time.time()
                    result = original_execute(query, *args, **kwargs)
                    end_time = time.time()
                    
                    queries_list.append({
                        "query": str(query),
                        "parameters": args if args else kwargs.get("parameters"),
                        "duration_ms": (end_time - start_time) * 1000,
                        "timestamp": start_time,
                    })
                    
                    return result
                
                # Replace with tracking method
                db_manager.engine.execute = tracking_execute
            
            yield
        finally:
            # Restore original execute method
            if original_execute and db_manager and hasattr(db_manager, "engine"):
                db_manager.engine.execute = original_execute
    
    @contextmanager
    def _track_dependencies(self, dependencies_list: List[Dict[str, Any]]) -> None:
        """Context manager to track dependencies.
        
        Args:
            dependencies_list: List to append dependency info to
        """
        if not self.enable_dependency_tracking or not hasattr(self, "container"):
            yield
            return
        
        original_get = None
        
        try:
            # Store original get method
            if hasattr(self.container, "get"):
                original_get = self.container.get
                
                # Create tracking get method
                def tracking_get(interface_type, *args, **kwargs):
                    start_time = time.time()
                    result = original_get(interface_type, *args, **kwargs)
                    end_time = time.time()
                    
                    # Get name for the dependency
                    name = getattr(interface_type, "__name__", str(interface_type))
                    
                    dependencies_list.append({
                        "name": name,
                        "type": str(interface_type),
                        "duration_ms": (end_time - start_time) * 1000,
                        "timestamp": start_time,
                    })
                    
                    return result
                
                # Replace with tracking method
                self.container.get = tracking_get
            
            yield
        finally:
            # Restore original get method
            if original_get and hasattr(self, "container"):
                self.container.get = original_get


def debug_fastapi(
    app: FastAPI,
    enable_request_logging: bool = True,
    enable_sql_tracking: bool = True,
    enable_dependency_tracking: bool = True,
    enable_error_enhancement: bool = True,
    exclude_paths: Optional[List[str]] = None,
    debug_headers: bool = True,
    log_request_body: bool = False,
    log_response_body: bool = False,
    pretty_json: bool = True,
    max_body_length: int = 10000,
) -> FastAPI:
    """Add debug middleware and tools to a FastAPI application.
    
    Args:
        app: The FastAPI application
        enable_request_logging: Whether to log requests and responses
        enable_sql_tracking: Whether to track SQL queries
        enable_dependency_tracking: Whether to track dependencies
        enable_error_enhancement: Whether to enhance error information
        exclude_paths: Paths to exclude from debugging
        debug_headers: Whether to add debug headers to responses
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        pretty_json: Whether to pretty-print JSON in logs
        max_body_length: Maximum length to log for request/response bodies
        
    Returns:
        The FastAPI application with debug middleware
    """
    # Add the debug middleware
    app.add_middleware(
        DebugMiddleware,
        enable_request_logging=enable_request_logging,
        enable_sql_tracking=enable_sql_tracking,
        enable_dependency_tracking=enable_dependency_tracking,
        enable_error_enhancement=enable_error_enhancement,
        exclude_paths=exclude_paths,
        debug_headers=debug_headers,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        pretty_json=pretty_json,
        max_body_length=max_body_length,
    )
    
    return app