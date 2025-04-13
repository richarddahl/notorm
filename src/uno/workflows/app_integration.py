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
        from uno.workflows.provider import configure_workflow_module
        inject.configure_once(configure_workflow_module)
        logger.info("Workflow module dependency injection configured")
    except Exception as e:
        logger.error(f"Failed to configure workflow module dependency injection: {e}")
    
    @app.on_event("startup")
    async def startup_workflow_module() -> None:
        """Register workflow integrations on application startup."""
        logger.info("Initializing workflow module")
        await register_workflow_integrations(
            register_domain_events=True,
            start_postgres_listener=True,
        )
    
    @app.on_event("shutdown")
    async def shutdown_workflow_module() -> None:
        """Clean up workflow integrations on application shutdown."""
        logger.info("Shutting down workflow module")
        integration = get_workflow_integration()
        await integration.stop_postgres_listener()


def get_workflow_dependency() -> Callable[[Any], Any]:
    """
    Get a FastAPI dependency for the workflow module.
    
    This function returns a FastAPI dependency that can be used to
    inject the workflow service into route handlers.
    
    Returns:
        A FastAPI dependency function
    """
    from uno.workflows.provider import WorkflowService
    
    def get_workflow_service() -> WorkflowService:
        """Get the workflow service instance."""
        return inject.instance(WorkflowService)
    
    return Depends(get_workflow_service)


# Convenience exports
workflow_dependency = get_workflow_dependency()