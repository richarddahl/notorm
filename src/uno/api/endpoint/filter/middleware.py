"""
Filter middleware for the unified endpoint framework.

This module provides middleware for processing filter requests in the unified endpoint framework.
"""

from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .protocol import FilterProtocol
from .query_parser import QueryParser


class FilterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for processing filter requests.
    
    This middleware extracts filter parameters from requests and adds them to the request state.
    """
    
    def __init__(
        self,
        app,
        filter_backend: Optional[FilterProtocol] = None,
    ):
        """
        Initialize a new filter middleware.
        
        Args:
            app: The FastAPI application
            filter_backend: Optional filter backend to use
        """
        super().__init__(app)
        self.filter_backend = filter_backend
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and extract filter parameters.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response
        """
        # Extract query parameters
        query_params = dict(request.query_params)
        
        # Parse filter parameters
        filter_params = []
        for key, value in query_params.items():
            if key.startswith("filter."):
                # Extract field, operator, and value
                parts = key.split(".", 2)
                if len(parts) >= 2:
                    field = parts[1]
                    operator = parts[2] if len(parts) > 2 else "eq"
                    
                    # Add to filter parameters
                    filter_params.append(f"{field}:{operator}:{value}")
        
        # Get sort, limit, and offset parameters
        sort_params = query_params.get("sort", "").split(",") if "sort" in query_params else None
        limit = int(query_params.get("limit")) if "limit" in query_params else None
        offset = int(query_params.get("offset")) if "offset" in query_params else None
        
        # Parse filter criteria
        filter_criteria = QueryParser.parse_filter_params(
            filter_field=filter_params,
            sort=sort_params,
            limit=limit,
            offset=offset,
        )
        
        # Add filter criteria to request state
        request.state.filter_criteria = filter_criteria
        
        # Add filter backend to request state
        if self.filter_backend:
            request.state.filter_backend = self.filter_backend
        
        # Continue processing the request
        return await call_next(request)