"""
Middleware for profiling FastAPI applications.

This module provides a FastAPI middleware for profiling HTTP requests and
identifying performance bottlenecks.
"""

import time
import logging
import json
import random
from typing import Callable, Dict, List, Optional, Set, Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from uno.devtools.profiling.profiler import Profiler
from uno.devtools.profiling.memory import MemoryProfiler


logger = logging.getLogger("uno.profiler")


class ProfilerMiddleware(BaseHTTPMiddleware):
    """Middleware for profiling FastAPI requests."""
    
    def __init__(
        self,
        app: FastAPI,
        profile_responses: bool = True,
        profile_memory: bool = False,
        profile_queries: bool = True,
        skip_paths: Optional[List[str]] = None,
        sample_rate: float = 1.0,
        min_duration_ms: float = 0.0,
        max_profiles: int = 100,
        save_profiles: bool = False,
        save_directory: Optional[str] = None,
    ):
        """Initialize the profiler middleware.
        
        Args:
            app: The FastAPI application
            profile_responses: Whether to profile response generation
            profile_memory: Whether to profile memory usage
            profile_queries: Whether to track SQL queries
            skip_paths: Paths to exclude from profiling
            sample_rate: Fraction of requests to profile (0.0-1.0)
            min_duration_ms: Only save profiles for requests that take longer than this
            max_profiles: Maximum number of profiles to keep in memory
            save_profiles: Whether to save profiles to disk
            save_directory: Directory to save profiles to
        """
        super().__init__(app)
        self.profile_responses = profile_responses
        self.profile_memory = profile_memory
        self.profile_queries = profile_queries
        self.skip_paths = skip_paths or ["/docs", "/openapi.json", "/redoc", "/static"]
        self.sample_rate = sample_rate
        self.min_duration_ms = min_duration_ms
        self.max_profiles = max_profiles
        self.save_profiles = save_profiles
        self.save_directory = save_directory
        
        # Profiles
        self.profiles: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process a request, optionally profiling it.
        
        Args:
            request: The incoming request
            call_next: The next middleware handler
            
        Returns:
            The response
        """
        # Skip profiling for specific paths
        path = request.url.path
        
        if any(path.startswith(skip_path) for skip_path in self.skip_paths):
            return await call_next(request)
        
        # Decide whether to profile this request
        should_profile = random.random() < self.sample_rate
        
        if not should_profile:
            return await call_next(request)
        
        # Generate a unique profile ID
        profile_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Set up profilers
        time_profiler = Profiler(detailed=True)
        memory_profiler = MemoryProfiler(detailed=True) if self.profile_memory else None
        
        # Set up SQL query tracking if enabled
        if self.profile_queries:
            try:
                from uno.devtools.debugging.sql_debug import SQLQueryDebugger, get_query_tracker
                sql_tracker = get_query_tracker()
                sql_tracker.clear()
            except ImportError:
                self.profile_queries = False
        
        # Set up profile data
        profile_data = {
            "id": profile_id,
            "path": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else None,
            "start_time": time.time(),
            "end_time": None,
            "duration_ms": None,
            "status_code": None,
            "query_count": None,
            "memory_delta": None,
        }
        
        # Run profilers
        try:
            # Time profiling
            result = None
            
            with time_profiler.profile_block("request"):
                # Memory profiling if enabled
                if self.profile_memory and memory_profiler:
                    with memory_profiler.profile_block("request"):
                        result = await call_next(request)
                else:
                    result = await call_next(request)
            
            # Calculate metrics
            end_time = time.time()
            duration_ms = (end_time - profile_data["start_time"]) * 1000
            
            # Update profile data
            profile_data["end_time"] = end_time
            profile_data["duration_ms"] = duration_ms
            
            if hasattr(result, "status_code"):
                profile_data["status_code"] = result.status_code
            
            # Add SQL query information if tracked
            if self.profile_queries:
                profile_data["query_count"] = len(sql_tracker.queries)
                if sql_tracker.queries:
                    profile_data["queries"] = [
                        {
                            "query": q.query,
                            "duration_ms": q.duration_ms,
                            "context": q.context,
                        }
                        for q in sql_tracker.queries
                    ]
                    
                    # Calculate total query time
                    profile_data["total_query_time_ms"] = sum(q.duration_ms for q in sql_tracker.queries)
                
            # Add memory profiling information if enabled
            if self.profile_memory and memory_profiler:
                memory_result = memory_profiler.get_stats("request")
                if memory_result:
                    profile_data["memory_delta"] = memory_result.delta
            
            # Add profiling results
            profile_data["profiler_output"] = time_profiler.print_stats("request")
            
            # Save profile if it meets criteria
            if duration_ms >= self.min_duration_ms:
                self._save_profile(profile_id, profile_data)
            
            # Add profile headers
            if hasattr(result, "headers"):
                result.headers["X-Profile-Id"] = profile_id
                result.headers["X-Profile-Time"] = f"{duration_ms:.2f}ms"
                
                if self.profile_queries:
                    result.headers["X-Profile-Queries"] = str(profile_data.get("query_count", 0))
                    if "total_query_time_ms" in profile_data:
                        result.headers["X-Profile-Query-Time"] = f"{profile_data['total_query_time_ms']:.2f}ms"
            
            return result
        except Exception as e:
            logger.exception(f"Error during profiling: {str(e)}")
            if not profile_data["end_time"]:
                profile_data["end_time"] = time.time()
                profile_data["duration_ms"] = (profile_data["end_time"] - profile_data["start_time"]) * 1000
            
            profile_data["error"] = {
                "type": type(e).__name__,
                "message": str(e),
            }
            
            self._save_profile(profile_id, profile_data)
            
            # Re-raise the exception
            raise
    
    def _save_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """Save a profile.
        
        Args:
            profile_id: The profile ID
            profile_data: The profile data
        """
        # Save in memory
        self.profiles[profile_id] = profile_data
        
        # Trim profiles if we have too many
        if len(self.profiles) > self.max_profiles:
            # Remove oldest profiles
            oldest_profiles = sorted(
                self.profiles.items(),
                key=lambda x: x[1]["start_time"]
            )[:len(self.profiles) - self.max_profiles]
            
            for old_id, _ in oldest_profiles:
                del self.profiles[old_id]
        
        # Save to disk if enabled
        if self.save_profiles and self.save_directory:
            try:
                import os
                import json
                
                os.makedirs(self.save_directory, exist_ok=True)
                
                filepath = os.path.join(
                    self.save_directory, 
                    f"profile_{profile_id}.json"
                )
                
                with open(filepath, "w") as f:
                    json.dump(profile_data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Error saving profile to disk: {str(e)}")
    
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get a profile by ID.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            The profile data if found, None otherwise
        """
        return self.profiles.get(profile_id)
    
    def get_profiles(
        self,
        min_duration_ms: Optional[float] = None,
        path_prefix: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get profiles matching the specified filters.
        
        Args:
            min_duration_ms: Minimum duration in milliseconds
            path_prefix: Path prefix to filter by
            method: HTTP method to filter by
            status_code: Status code to filter by
            limit: Maximum number of profiles to return
            
        Returns:
            List of matching profiles
        """
        filtered_profiles = []
        
        for profile in self.profiles.values():
            # Apply filters
            if min_duration_ms is not None and profile.get("duration_ms", 0) < min_duration_ms:
                continue
                
            if path_prefix is not None and not profile.get("path", "").startswith(path_prefix):
                continue
                
            if method is not None and profile.get("method") != method:
                continue
                
            if status_code is not None and profile.get("status_code") != status_code:
                continue
                
            filtered_profiles.append(profile)
        
        # Sort by duration (descending)
        filtered_profiles.sort(key=lambda p: p.get("duration_ms", 0), reverse=True)
        
        # Apply limit
        return filtered_profiles[:limit]
    
    def clear_profiles(self) -> None:
        """Clear all saved profiles."""
        self.profiles = {}


def profile_fastapi(
    app: FastAPI,
    profile_responses: bool = True,
    profile_memory: bool = False,
    profile_queries: bool = True,
    skip_paths: Optional[List[str]] = None,
    sample_rate: float = 1.0,
    min_duration_ms: float = 0.0,
    max_profiles: int = 100,
    save_profiles: bool = False,
    save_directory: Optional[str] = None,
) -> FastAPI:
    """Add profiler middleware to a FastAPI application.
    
    Args:
        app: The FastAPI application
        profile_responses: Whether to profile response generation
        profile_memory: Whether to profile memory usage
        profile_queries: Whether to track SQL queries
        skip_paths: Paths to exclude from profiling
        sample_rate: Fraction of requests to profile (0.0-1.0)
        min_duration_ms: Only save profiles for requests that take longer than this
        max_profiles: Maximum number of profiles to keep in memory
        save_profiles: Whether to save profiles to disk
        save_directory: Directory to save profiles to
        
    Returns:
        The FastAPI application with profiler middleware
    """
    middleware = ProfilerMiddleware(
        app,
        profile_responses=profile_responses,
        profile_memory=profile_memory,
        profile_queries=profile_queries,
        skip_paths=skip_paths,
        sample_rate=sample_rate,
        min_duration_ms=min_duration_ms,
        max_profiles=max_profiles,
        save_profiles=save_profiles,
        save_directory=save_directory,
    )
    
    app.add_middleware(ProfilerMiddleware, middleware=middleware)
    
    # Add a route to get profiles
    @app.get("/profiles/{profile_id}")
    def get_profile(profile_id: str):
        profile = middleware.get_profile(profile_id)
        if profile:
            return profile
        return JSONResponse(status_code=404, content={"error": "Profile not found"})
    
    @app.get("/profiles")
    def get_profiles(
        min_duration: Optional[float] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[int] = None,
        limit: int = 100,
    ):
        profiles = middleware.get_profiles(
            min_duration_ms=min_duration,
            path_prefix=path,
            method=method,
            status_code=status,
            limit=limit,
        )
        return profiles
    
    @app.delete("/profiles")
    def clear_profiles():
        middleware.clear_profiles()
        return {"status": "ok"}
    
    return app