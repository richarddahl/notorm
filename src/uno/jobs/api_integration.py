# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, APIRouter, Depends

from uno.jobs.domain_endpoints import (
    register_job_endpoints,
    register_schedule_endpoints,
    register_queue_endpoints,
    register_task_endpoints,
    register_all_job_endpoints
)
from uno.jobs.domain_services import JobManagerServiceProtocol, TaskRegistryProtocol


def register_jobs_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    job_manager_service: Optional[JobManagerServiceProtocol] = None,
    task_registry_service: Optional[TaskRegistryProtocol] = None,
) -> Dict[str, Dict[str, Any]]:
    """Register all jobs-related API endpoints.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints on
        path_prefix: The prefix for all API paths
        dependencies: List of dependencies to apply to all endpoints
        include_auth: Whether to include authentication dependencies
        job_manager_service: Optional job manager service dependency override
        task_registry_service: Optional task registry service dependency override
        
    Returns:
        Dictionary containing all registered endpoint functions
    """
    if dependencies is None:
        dependencies = []
    
    # Create a router for jobs endpoints
    router = APIRouter()
    
    # Register all endpoints
    endpoints = register_all_job_endpoints(router, dependencies=dependencies)
    
    # Include router in the app or parent router
    app_or_router.include_router(router, prefix=path_prefix)
    
    # Return all registered endpoints
    return endpoints