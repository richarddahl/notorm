"""
Middleware examples for UnoEndpoint-based APIs.

This module demonstrates how to implement various middleware for UnoEndpoint-based
APIs, including:

1. Request logging middleware
2. Response timing middleware
3. Rate limiting middleware
4. CORS middleware with fine-grained control
5. Request validation middleware
6. Error handling middleware
7. Caching middleware
8. Request context middleware
9. Content negotiation middleware
10. Metrics collection middleware

These examples show how to address cross-cutting concerns in your APIs
while maintaining clean code and separation of concerns.
"""

import time
import json
import logging
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Type, Tuple
from contextvars import ContextVar
import uuid
import hashlib

from fastapi import FastAPI, Request, Response, status, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.requests import Request
from starlette.datastructures import MutableHeaders

import redis
from redis import Redis


# Set up logging
logger = logging.getLogger(__name__)

# Set up context variables for request-scoped data
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
request_start_time_var: ContextVar[float] = ContextVar("request_start_time", default=0.0)
request_path_var: ContextVar[str] = ContextVar("request_path", default="")


# Mock Redis client for rate limiting and caching
mock_redis = {}  # In-memory dict as a Redis substitute
redis_prefix = "middleware_examples:"


def redis_get(key: str) -> Optional[bytes]:
    """Mock Redis GET command."""
    return mock_redis.get(redis_prefix + key)


def redis_set(key: str, value: bytes, ex: Optional[int] = None) -> None:
    """Mock Redis SET command with optional expiration."""
    mock_redis[redis_prefix + key] = value
    
    # If expiration is set, schedule removal
    if ex:
        async def remove_after_expiry():
            await asyncio.sleep(ex)
            mock_redis.pop(redis_prefix + key, None)
        
        # Start the expiry task
        asyncio.create_task(remove_after_expiry())


def redis_incr(key: str) -> int:
    """Mock Redis INCR command."""
    current = mock_redis.get(redis_prefix + key)
    if current is None:
        mock_redis[redis_prefix + key] = b"1"
        return 1
    
    value = int(current) + 1
    mock_redis[redis_prefix + key] = str(value).encode()
    return value


def redis_expire(key: str, seconds: int) -> None:
    """Mock Redis EXPIRE command."""
    key_with_prefix = redis_prefix + key
    if key_with_prefix in mock_redis:
        async def remove_after_expiry():
            await asyncio.sleep(seconds)
            mock_redis.pop(key_with_prefix, None)
        
        # Start the expiry task
        asyncio.create_task(remove_after_expiry())


# ===== MIDDLEWARE CLASSES =====

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging incoming requests and responses.
    
    This middleware logs detailed information about each request and response,
    including headers, body (optionally), status code, and timing information.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        log_headers: bool = True,
        exclude_paths: List[str] = None,
        exclude_extensions: List[str] = None,
        log_level: int = logging.INFO
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_headers = log_headers
        self.exclude_paths = exclude_paths or []
        self.exclude_extensions = exclude_extensions or [".jpg", ".png", ".gif", ".css", ".js"]
        self.log_level = log_level
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Store the request path for other middleware
        request_path_var.set(request.url.path)
        
        # Check if this path should be excluded from logging
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Check if this file extension should be excluded
        if any(request.url.path.endswith(ext) for ext in self.exclude_extensions):
            return await call_next(request)
        
        # Capture request information
        start_time = time.time()
        request_start_time_var.set(start_time)
        
        # Create the log entry for the request
        request_log = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Add headers if configured
        if self.log_headers:
            request_log["headers"] = dict(request.headers)
        
        # Add body if configured (and possible)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Get the request body - this requires consuming the stream
                body = await request.body()
                
                # Try to parse as JSON for better readability
                try:
                    if body:
                        if "application/json" in request.headers.get("content-type", ""):
                            request_log["body"] = json.loads(body)
                        else:
                            request_log["body"] = body.decode("utf-8")
                except:
                    request_log["body"] = f"<binary data, length: {len(body)}>"
                
                # Reset the request body since we've consumed it
                # Create a new request with the same scope but different body
                async def receive():
                    return {"type": "http.request", "body": body, "more_body": False}
                
                request._receive = receive
            except Exception as e:
                request_log["body_error"] = str(e)
        
        # Log the request
        logger.log(self.log_level, f"Request: {json.dumps(request_log)}")
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Capture response information
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Create the log entry for the response
            response_log = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length"),
            }
            
            # Add response headers if configured
            if self.log_headers:
                response_log["headers"] = dict(response.headers)
            
            # Add response body if configured (and possible)
            if self.log_response_body and "application/json" in response.headers.get("content-type", ""):
                try:
                    # Save the original response body
                    original_body = b""
                    
                    # Create a new response to capture the body
                    async def sender(message):
                        nonlocal original_body
                        if message["type"] == "http.response.body":
                            original_body += message.get("body", b"")
                        await original_send(message)
                    
                    original_send = response.background.send
                    response.background.send = sender
                    
                    # Log the response body once it's available
                    response_log["body"] = json.loads(original_body.decode("utf-8"))
                except Exception as e:
                    response_log["body_error"] = str(e)
            
            # Log the response
            logger.log(self.log_level, f"Response: {json.dumps(response_log)}")
            
            return response
        
        except Exception as e:
            # Log the exception
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            logger.error(
                f"Error processing request {request_id}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration_ms, 2),
                    "exception": str(e),
                    "traceback": logging.traceback.format_exc()
                }
            )
            
            # Re-raise the exception for the app to handle
            raise


class ResponseTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding response timing information.
    
    This middleware adds an X-Response-Time header to responses with
    the time taken to process the request in milliseconds.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Start timing
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate the duration in milliseconds
        duration_ms = (time.time() - start_time) * 1000
        
        # Add the timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests based on IP address or other identifiers.
    
    This middleware implements a sliding window rate limiting algorithm
    to restrict the number of requests from a single source within a given time period.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        limit: int = 100,  # Maximum requests per window
        window: int = 60,   # Window size in seconds
        header_prefix: str = "X-RateLimit",
        identifier_func: Optional[Callable[[Request], str]] = None,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.header_prefix = header_prefix
        self.exclude_paths = exclude_paths or []
        
        # Function to identify the client (default to IP address)
        self.identifier_func = identifier_func or (lambda request: request.client.host if request.client else "unknown")
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check if this path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get the client identifier
        identifier = self.identifier_func(request)
        key = f"rate_limit:{identifier}"
        
        # Increment the request count
        count = redis_incr(key)
        
        # Set expiration on the first request
        if count == 1:
            redis_expire(key, self.window)
        
        # Calculate remaining requests
        remaining = max(0, self.limit - count)
        
        # Check if the rate limit has been exceeded
        if count > self.limit:
            # Create the rate limit exceeded response
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": self.limit,
                    "window": f"{self.window} seconds",
                    "retry_after": self.window
                }
            )
            
            # Add rate limit headers
            response.headers[f"{self.header_prefix}-Limit"] = str(self.limit)
            response.headers[f"{self.header_prefix}-Remaining"] = "0"
            response.headers[f"{self.header_prefix}-Reset"] = str(self.window)
            response.headers["Retry-After"] = str(self.window)
            
            return response
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers[f"{self.header_prefix}-Limit"] = str(self.limit)
        response.headers[f"{self.header_prefix}-Remaining"] = str(remaining)
        response.headers[f"{self.header_prefix}-Reset"] = str(self.window)
        
        return response


class CustomCORSMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling Cross-Origin Resource Sharing (CORS) with fine-grained control.
    
    This middleware extends the built-in CORS middleware with additional features like
    path-specific rules and dynamic origin validation.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = False,
        expose_headers: List[str] = None,
        max_age: int = 600,
        path_specific_rules: Dict[str, Dict[str, Any]] = None,
        origin_validator: Optional[Callable[[str], bool]] = None
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = allow_headers or ["Authorization", "Content-Type"]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age
        self.path_specific_rules = path_specific_rules or {}
        self.origin_validator = origin_validator
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Get the origin from the request
        origin = request.headers.get("origin")
        
        # If no origin, just pass through
        if not origin:
            return await call_next(request)
        
        # Check if there are path-specific rules for this path
        path_rules = None
        for path_prefix, rules in self.path_specific_rules.items():
            if request.url.path.startswith(path_prefix):
                path_rules = rules
                break
        
        # Use path-specific rules if they exist, otherwise use default rules
        allow_origins = path_rules.get("allow_origins", self.allow_origins) if path_rules else self.allow_origins
        allow_methods = path_rules.get("allow_methods", self.allow_methods) if path_rules else self.allow_methods
        allow_headers = path_rules.get("allow_headers", self.allow_headers) if path_rules else self.allow_headers
        allow_credentials = path_rules.get("allow_credentials", self.allow_credentials) if path_rules else self.allow_credentials
        expose_headers = path_rules.get("expose_headers", self.expose_headers) if path_rules else self.expose_headers
        max_age = path_rules.get("max_age", self.max_age) if path_rules else self.max_age
        
        # Check if the origin is allowed
        origin_allowed = False
        
        # If we have a custom validator, use it
        if self.origin_validator and self.origin_validator(origin):
            origin_allowed = True
        
        # Otherwise check against the allowed origins list
        elif "*" in allow_origins:
            origin_allowed = True
        
        elif origin in allow_origins:
            origin_allowed = True
        
        # If the origin is not allowed, just process without CORS headers
        if not origin_allowed:
            return await call_next(request)
        
        # For OPTIONS requests (preflight)
        if request.method == "OPTIONS":
            response = Response()
            
            # Set the appropriate CORS headers
            if allow_origins == ["*"] and not allow_credentials:
                response.headers["Access-Control-Allow-Origin"] = "*"
            else:
                response.headers["Access-Control-Allow-Origin"] = origin
            
            if allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            if allow_methods:
                response.headers["Access-Control-Allow-Methods"] = ", ".join(allow_methods)
            
            if allow_headers:
                response.headers["Access-Control-Allow-Headers"] = ", ".join(allow_headers)
            
            if expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)
            
            if max_age:
                response.headers["Access-Control-Max-Age"] = str(max_age)
            
            return response
        
        # For regular requests
        response = await call_next(request)
        
        # Set the appropriate CORS headers
        if allow_origins == ["*"] and not allow_credentials:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = origin
        
        if allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        if expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating requests before they reach the endpoints.
    
    This middleware performs basic validation like content type checking,
    request size limits, and other common validations.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        max_content_length: int = 10 * 1024 * 1024,  # 10 MB
        required_content_types: Dict[str, List[str]] = None,
        excluded_paths: List[str] = None
    ):
        super().__init__(app)
        self.max_content_length = max_content_length
        self.required_content_types = required_content_types or {
            "POST": ["application/json"],
            "PUT": ["application/json"],
            "PATCH": ["application/json"]
        }
        self.excluded_paths = excluded_paths or ["/static", "/media"]
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check if path is excluded
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Validate Content-Length if present
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": f"Request body too large. Maximum size is {self.max_content_length} bytes."}
            )
        
        # Validate Content-Type for specific methods
        if request.method in self.required_content_types:
            content_type = request.headers.get("content-type", "")
            valid_types = self.required_content_types[request.method]
            
            # Allow any Content-Type that starts with one of the valid types
            if not any(content_type.startswith(valid_type) for valid_type in valid_types):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "detail": f"Unsupported media type. Must be one of: {', '.join(valid_types)}",
                        "content_type": content_type
                    }
                )
        
        # If validation passes, call the next middleware or endpoint
        return await call_next(request)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for globally handling exceptions and returning appropriate responses.
    
    This middleware catches exceptions raised during request processing
    and transforms them into standardized error responses.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        default_error_message: str = "An unexpected error occurred",
        include_traceback: bool = False  # Should be False in production
    ):
        super().__init__(app)
        self.default_error_message = default_error_message
        self.include_traceback = include_traceback
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            # Process the request
            return await call_next(request)
        
        except HTTPException as exc:
            # FastAPI HTTPExceptions are already formatted appropriately
            # Just let them through
            raise
        
        except ValueError as exc:
            # Handle validation errors
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=self._format_error_response(
                    request=request,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=str(exc),
                    error_type="validation_error",
                    exc=exc
                )
            )
        
        except KeyError as exc:
            # Handle missing key errors
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=self._format_error_response(
                    request=request,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Missing required field: {str(exc)}",
                    error_type="missing_field",
                    exc=exc
                )
            )
        
        except Exception as exc:
            # Handle unexpected errors
            # Log the exception with traceback
            logger.exception(f"Unhandled exception in request {request_id_var.get()}: {str(exc)}")
            
            # Return a generic error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=self._format_error_response(
                    request=request,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.default_error_message,
                    error_type="server_error",
                    exc=exc
                )
            )
    
    def _format_error_response(
        self,
        request: Request,
        status_code: int,
        message: str,
        error_type: str,
        exc: Exception
    ) -> Dict[str, Any]:
        """Format a standardized error response."""
        error = {
            "status": "error",
            "status_code": status_code,
            "message": message,
            "type": error_type,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id_var.get()
        }
        
        # Include exception details in development mode
        if self.include_traceback:
            import traceback
            error["exception"] = str(exc)
            error["traceback"] = traceback.format_exc()
        
        return error


class CachingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for caching responses to improve performance.
    
    This middleware caches responses for GET requests and serves them
    for subsequent requests to the same path with the same parameters.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        ttl: int = 300,  # Time to live in seconds
        vary_headers: List[str] = None,
        excluded_paths: List[str] = None,
        excluded_query_params: List[str] = None,
        cache_control_header: str = "public, max-age={ttl}"
    ):
        super().__init__(app)
        self.ttl = ttl
        self.vary_headers = vary_headers or ["accept", "accept-encoding"]
        self.excluded_paths = excluded_paths or ["/admin", "/auth"]
        self.excluded_query_params = excluded_query_params or ["token", "refresh"]
        self.cache_control_header = cache_control_header
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if path is excluded
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Check if there are excluded query parameters
        if any(param in request.query_params for param in self.excluded_query_params):
            return await call_next(request)
        
        # Create a cache key based on the path, query params, and relevant headers
        cache_parts = [request.url.path, str(request.query_params)]
        
        # Add vary headers to the cache key
        for header in self.vary_headers:
            if header in request.headers:
                cache_parts.append(f"{header}:{request.headers[header]}")
        
        # Create a hash of all the parts for the cache key
        cache_key = f"cache:{hashlib.md5(':'.join(cache_parts).encode()).hexdigest()}"
        
        # Check if the response is in the cache
        cached_response = redis_get(cache_key)
        if cached_response:
            # Deserialize the cached response
            cached_data = json.loads(cached_response.decode("utf-8"))
            
            # Create a response from the cached data
            response = Response(
                content=cached_data["content"],
                status_code=cached_data["status_code"],
                headers=cached_data["headers"],
                media_type=cached_data["media_type"]
            )
            
            # Add a header to indicate a cache hit
            response.headers["X-Cache"] = "HIT"
            
            return response
        
        # Not in cache, so process the request
        response = await call_next(request)
        
        # Only cache successful responses
        if 200 <= response.status_code < 400:
            # Get the response body - this requires consuming it
            body = b""
            
            async def send_wrapper(message: Message) -> None:
                nonlocal body
                if message["type"] == "http.response.body":
                    body += message.get("body", b"")
                await original_send(message)
            
            # Replace the send function to capture the response body
            original_send = response.background.send
            response.background.send = send_wrapper
            
            # Prepare the data to cache
            cache_data = {
                "content": body.decode("utf-8") if body else "",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }
            
            # Cache the response
            redis_set(cache_key, json.dumps(cache_data).encode(), ex=self.ttl)
            
            # Add cache-control header
            response.headers["Cache-Control"] = self.cache_control_header.format(ttl=self.ttl)
            
            # Add a header to indicate a cache miss
            response.headers["X-Cache"] = "MISS"
        
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for setting up a request context with useful information.
    
    This middleware populates context variables that can be accessed
    throughout the request processing lifecycle.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate a unique request ID if not already set
        request_id = request_id_var.get()
        if not request_id:
            request_id = str(uuid.uuid4())
            request_id_var.set(request_id)
        
        # Store the request path
        request_path_var.set(request.url.path)
        
        # Store the request start time
        start_time = time.time()
        request_start_time_var.set(start_time)
        
        # Extract and store the user ID if available
        # This would typically come from authenticated requests
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # In a real application, you would decode the JWT token
            # For this example, we'll just set a dummy user ID
            user_id_var.set("user-123")
        
        # Set request ID header on the response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class ContentNegotiationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for content negotiation based on Accept headers.
    
    This middleware determines the most appropriate response format
    based on the client's Accept header and the available representations.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        default_media_type: str = "application/json",
        available_media_types: Dict[str, Callable[[Dict[str, Any]], Response]] = None,
        excluded_paths: List[str] = None
    ):
        super().__init__(app)
        self.default_media_type = default_media_type
        self.available_media_types = available_media_types or {
            "application/json": self._json_response,
            "text/html": self._html_response,
            "text/plain": self._text_response,
            "application/xml": self._xml_response
        }
        self.excluded_paths = excluded_paths or ["/static", "/media"]
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check if path is excluded
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Process the request
        response = await call_next(request)
        
        # Only handle JSON responses that haven't been explicitly formatted
        if (
            response.headers.get("content-type", "").startswith("application/json") and
            not response.headers.get("x-content-negotiated")
        ):
            # Get the Accept header
            accept_header = request.headers.get("accept", self.default_media_type)
            
            # Parse the Accept header
            parsed_accept = self._parse_accept_header(accept_header)
            
            # Find the best match
            best_match = self._find_best_match(parsed_accept)
            
            # If we found a match and it's not JSON, transform the response
            if best_match and best_match != "application/json":
                # Get the response data
                try:
                    # This is a simplification - in a real app you'd need to read the response body
                    # which is more complex since it's already been sent as a stream
                    data = json.loads(response.body.decode("utf-8"))
                    
                    # Transform the response
                    new_response = self.available_media_types[best_match](data)
                    
                    # Mark as content negotiated
                    new_response.headers["X-Content-Negotiated"] = "true"
                    
                    return new_response
                except Exception as e:
                    # If there's an error, just return the original response
                    logger.warning(f"Content negotiation failed: {str(e)}")
            
            # Add the Vary header
            response.headers["Vary"] = "Accept"
        
        return response
    
    def _parse_accept_header(self, accept_header: str) -> List[Tuple[str, float]]:
        """Parse the Accept header into a list of (media_type, quality) tuples."""
        result = []
        
        # Split by comma
        for media_range in accept_header.split(","):
            media_range = media_range.strip()
            
            # Check for quality parameter
            parts = media_range.split(";")
            media_type = parts[0].strip()
            
            quality = 1.0
            for param in parts[1:]:
                param = param.strip()
                if param.startswith("q="):
                    try:
                        quality = float(param[2:])
                    except ValueError:
                        # If quality is invalid, use default
                        quality = 1.0
            
            # Add to result
            result.append((media_type, quality))
        
        # Sort by quality, highest first
        return sorted(result, key=lambda x: x[1], reverse=True)
    
    def _find_best_match(self, parsed_accept: List[Tuple[str, float]]) -> Optional[str]:
        """Find the best match for the client's preferences."""
        # Try exact matches first
        for media_type, quality in parsed_accept:
            if quality <= 0:
                continue
            
            if media_type in self.available_media_types:
                return media_type
        
        # If no exact match, try wildcard matches
        for media_type, quality in parsed_accept:
            if quality <= 0:
                continue
            
            if media_type == "*/*":
                # Any media type - return default
                return self.default_media_type
            
            if media_type.endswith("/*"):
                # Media type family (e.g., "text/*")
                type_prefix = media_type[:-2]
                for available in self.available_media_types:
                    if available.startswith(type_prefix):
                        return available
        
        # No match found - use default
        return self.default_media_type
    
    def _json_response(self, data: Dict[str, Any]) -> Response:
        """Convert data to JSON response."""
        return JSONResponse(content=data)
    
    def _html_response(self, data: Dict[str, Any]) -> Response:
        """Convert data to HTML response."""
        # A very simple HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>API Response</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .json-data {{ background: #f5f5f5; padding: 10px; border-radius: 4px; }}
                pre {{ margin: 0; }}
            </style>
        </head>
        <body>
            <h1>API Response</h1>
            <div class="json-data">
                <pre>{json.dumps(data, indent=2)}</pre>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)
    
    def _text_response(self, data: Dict[str, Any]) -> Response:
        """Convert data to plain text response."""
        # Simple text representation
        text = "API Response:\n\n"
        for key, value in data.items():
            text += f"{key}: {value}\n"
        
        return PlainTextResponse(content=text)
    
    def _xml_response(self, data: Dict[str, Any]) -> Response:
        """Convert data to XML response."""
        # A simple XML conversion
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<response>\n'
        
        def add_xml_element(key, value, indent=2):
            nonlocal xml
            spaces = " " * indent
            
            if isinstance(value, dict):
                xml += f"{spaces}<{key}>\n"
                for k, v in value.items():
                    add_xml_element(k, v, indent + 2)
                xml += f"{spaces}</{key}>\n"
            elif isinstance(value, list):
                xml += f"{spaces}<{key}>\n"
                for item in value:
                    if isinstance(item, dict):
                        xml += f"{spaces}  <item>\n"
                        for k, v in item.items():
                            add_xml_element(k, v, indent + 4)
                        xml += f"{spaces}  </item>\n"
                    else:
                        xml += f"{spaces}  <item>{item}</item>\n"
                xml += f"{spaces}</{key}>\n"
            else:
                xml += f"{spaces}<{key}>{value}</{key}>\n"
        
        for key, value in data.items():
            add_xml_element(key, value)
        
        xml += '</response>'
        
        return Response(content=xml, media_type="application/xml")


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting metrics on request processing.
    
    This middleware collects various metrics like request counts, response times,
    status code distribution, etc. for monitoring and analysis.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        metrics_path: str = "/metrics",
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.metrics_path = metrics_path
        self.exclude_paths = exclude_paths or ["/static", "/media", "/metrics"]
        
        # Initialize metrics counters
        self.metrics = {
            "requests_total": 0,
            "requests_by_method": {},
            "requests_by_path": {},
            "responses_by_status": {},
            "response_time_sum": 0,
            "response_time_count": 0,
            "errors_total": 0
        }
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Special handling for metrics endpoint
        if request.url.path == self.metrics_path:
            return self._metrics_response()
        
        # Check if path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(request, response, response_time)
            
            return response
        
        except Exception as e:
            # Calculate response time even for errors
            response_time = time.time() - start_time
            
            # Update error metrics
            self.metrics["errors_total"] += 1
            
            # Re-raise the exception
            raise
    
    def _update_metrics(self, request: Request, response: Response, response_time: float):
        """Update the metrics after processing a request."""
        # Total requests
        self.metrics["requests_total"] += 1
        
        # Requests by method
        method = request.method
        self.metrics["requests_by_method"][method] = self.metrics["requests_by_method"].get(method, 0) + 1
        
        # Requests by path (simplified to avoid too many unique paths)
        # In a real app, you might use a route template or pattern
        path = request.url.path
        self.metrics["requests_by_path"][path] = self.metrics["requests_by_path"].get(path, 0) + 1
        
        # Responses by status
        status_code = response.status_code
        status_group = f"{status_code // 100}xx"
        self.metrics["responses_by_status"][status_code] = self.metrics["responses_by_status"].get(status_code, 0) + 1
        self.metrics["responses_by_status"][status_group] = self.metrics["responses_by_status"].get(status_group, 0) + 1
        
        # Response time metrics (for calculating average later)
        self.metrics["response_time_sum"] += response_time
        self.metrics["response_time_count"] += 1
    
    def _metrics_response(self) -> Response:
        """Generate a response with the current metrics."""
        # Calculate derived metrics
        avg_response_time = self.metrics["response_time_sum"] / max(1, self.metrics["response_time_count"])
        error_rate = self.metrics["errors_total"] / max(1, self.metrics["requests_total"])
        
        # Format the metrics
        metrics_data = {
            "requests": {
                "total": self.metrics["requests_total"],
                "by_method": self.metrics["requests_by_method"],
                "by_path": {k: v for k, v in sorted(self.metrics["requests_by_path"].items(), key=lambda x: x[1], reverse=True)[:10]}
            },
            "responses": {
                "by_status": self.metrics["responses_by_status"]
            },
            "performance": {
                "average_response_time_ms": round(avg_response_time * 1000, 2),
                "error_rate": round(error_rate, 4)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=metrics_data)


# ===== CREATE AND CONFIGURE APPLICATION =====

def create_app():
    """Create a FastAPI application with middleware examples."""
    app = FastAPI(title="Middleware Examples", description="Examples of various middleware for FastAPI applications")
    
    # Add the middleware in the desired order (from outermost to innermost)
    
    # 1. Request Context Middleware (should be first to set up context for other middleware)
    app.add_middleware(RequestContextMiddleware)
    
    # 2. Metrics Middleware (early to capture all requests)
    app.add_middleware(MetricsMiddleware)
    
    # 3. Error Handling Middleware (early to catch all exceptions)
    app.add_middleware(
        ErrorHandlingMiddleware, 
        default_error_message="An error occurred while processing your request",
        include_traceback=False  # Set to True in development
    )
    
    # 4. Response Timing Middleware
    app.add_middleware(ResponseTimingMiddleware)
    
    # 5. Request Logging Middleware
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=False,
        log_response_body=False,
        exclude_paths=["/static", "/media", "/metrics"],
        exclude_extensions=[".jpg", ".png", ".gif", ".css", ".js"]
    )
    
    # 6. Custom CORS Middleware
    app.add_middleware(
        CustomCORSMiddleware,
        allow_origins=["http://localhost:3000", "https://example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        allow_credentials=True,
        path_specific_rules={
            "/api/v1/public": {
                "allow_origins": ["*"],
                "allow_credentials": False
            }
        }
    )
    
    # 7. Request Validation Middleware
    app.add_middleware(
        RequestValidationMiddleware,
        max_content_length=5 * 1024 * 1024,  # 5 MB
        required_content_types={
            "POST": ["application/json"],
            "PUT": ["application/json"],
            "PATCH": ["application/json"]
        }
    )
    
    # 8. Rate Limiting Middleware
    app.add_middleware(
        RateLimitingMiddleware,
        limit=100,
        window=60,
        exclude_paths=["/static", "/media", "/metrics"]
    )
    
    # 9. Caching Middleware
    app.add_middleware(
        CachingMiddleware,
        ttl=300,  # 5 minutes
        excluded_paths=["/api/v1/private", "/auth"]
    )
    
    # 10. Content Negotiation Middleware
    app.add_middleware(ContentNegotiationMiddleware)
    
    # 11. GZip Middleware (built-in, for compressed responses)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 12. Trusted Host Middleware (built-in, for security)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "example.com"]
    )
    
    # Add some example endpoints
    
    @app.get("/")
    async def root():
        """Root endpoint - returns basic information."""
        return {
            "app": "Middleware Examples",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/api/v1/items")
    async def get_items():
        """Example endpoint that returns a list of items."""
        return {
            "items": [
                {"id": 1, "name": "Item 1", "price": 10.99},
                {"id": 2, "name": "Item 2", "price": 20.99},
                {"id": 3, "name": "Item 3", "price": 30.99}
            ],
            "count": 3,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/api/v1/items")
    async def create_item(item: dict):
        """Example endpoint that creates a new item."""
        # Simulate item creation
        return {
            "id": 4,
            "name": item.get("name", "New Item"),
            "price": item.get("price", 0),
            "created_at": datetime.now().isoformat()
        }
    
    @app.get("/api/v1/error")
    async def trigger_error():
        """Example endpoint that triggers an error."""
        # Deliberately raise an exception to demonstrate error handling
        raise ValueError("This is a deliberate error for demonstration purposes")
    
    @app.get("/api/v1/slow")
    async def slow_response():
        """Example endpoint with a deliberately slow response."""
        # Simulate a slow operation
        await asyncio.sleep(2)
        return {
            "message": "This response was deliberately delayed",
            "timestamp": datetime.now().isoformat()
        }
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Create the app
    app = create_app()
    
    # Run the app
    uvicorn.run(app, host="127.0.0.1", port=8000)