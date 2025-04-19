# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integration with FastAPI application startup and shutdown.

This module provides the necessary hooks to integrate the workflow module
with FastAPI application startup and shutdown events.
"""

import logging
from typing import Callable, Any

import inject
from fastapi import FastAPI, Depends
from uno.core.errors.result import Result
from uno.workflows.errors import WorkflowErrorCode, WorkflowEventError
from uno.dependencies.scoped_container import get_service, get_scoped_service

from uno.workflows.integration import (
    get_workflow_integration,
    register_workflow_integrations,
)


def setup_workflow_module(app: FastAPI) -> None:
    """
    Set up the workflow module with a FastAPI application.
    
    This function registers the workflow module with FastAPI startup
    and shutdown events to ensure proper initialization and cleanup.
    
    Args:
        app: The FastAPI application instance
    """
    logger = logging.getLogger(__name__)
    logger.info("Setting up workflow module with FastAPI")
    
    # Configure the workflow module dependency injection here, when the application
    # has been initialized and the main injector is already configured
    try:
        
        
        logger.info("Workflow module dependency injection configured")
    except Exception as e:
        logger.error(f"Failed to configure workflow module dependency injection: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {e.__traceback__}")
        
        # Log a user-friendly message
        logger.error("Workflow functionality may be unavailable due to initialization error")
    
    @app.on_event("startup")
    async def startup_workflow_module() -> None:
        """Register workflow integrations on application startup."""
        logger.info("Initializing workflow module")
        result = await register_workflow_integrations(
            register_domain_events=True,
            start_postgres_listener=True,
        )
        
        if result.is_failure:
            logger.error(f"Failed to initialize workflow module: {result.error}")
            
            # Log additional information if available
            if isinstance(result.error, WorkflowEventError):
                logger.error(f"Event type: {result.error.context.get('event_type')}")
                logger.error(f"Reason: {result.error.context.get('reason')}")
        else:
            logger.info("Workflow module initialized successfully")
    
    @app.on_event("shutdown")
    async def shutdown_workflow_module() -> None:
        """Clean up workflow integrations on application shutdown."""
        logger.info("Shutting down workflow module")
        integration = get_workflow_integration()
        result = await integration.stop_postgres_listener()
        
        if result.is_failure:
            logger.error(f"Error shutting down workflow module: {result.error}")
            
            # Log additional information if available
            if isinstance(result.error, WorkflowEventError):
                logger.error(f"Event type: {result.error.context.get('event_type')}")
                logger.error(f"Reason: {result.error.context.get('reason')}")
                
            # Even if shutdown fails, we proceed to ensure a clean exit
            logger.warning("Continuing with application shutdown despite workflow shutdown failure")
        else:
            logger.info("Workflow module shutdown complete")
    
    # Include workflow API endpoints
    try:
        from uno.workflows.endpoints import router as api_router
        from uno.workflows.routes import router as ui_router
        
        app.include_router(api_router)
        app.include_router(ui_router)
        
        logger.info("Workflow API endpoints registered")
    except Exception as e:
        logger.error(f"Failed to register workflow API endpoints: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {e.__traceback__}")
        
        # Log a user-friendly message
        logger.error("Workflow UI and API routes may be unavailable due to registration error")


def get_workflow_dependency() -> Callable[[Any], Any]:
    """
    Get a FastAPI dependency for the workflow module.
    
    This function returns a FastAPI dependency that can be used to
    inject the workflow service into route handlers.
    
    Returns:
        A FastAPI dependency function
    """
    from uno.workflows.provider import WorkflowService
    
    async def get_workflow_service() -> WorkflowService:
        """Get the workflow service instance."""
        return await get_scoped_service(WorkflowService)
    
    return Depends(get_workflow_service)


# Convenience exports
workflow_dependency = get_workflow_dependency()