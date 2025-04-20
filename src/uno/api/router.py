"""
Central router registration for all domain endpoints.

This module imports all routers from domain endpoint modules and registers them with the FastAPI app.
"""

from fastapi import FastAPI

# Import routers from each domain
from uno.application.queries.domain_endpoints import query_router, query_path_router
from uno.application.workflows.domain_endpoints import (
    workflow_def_router,
    workflow_trigger_router,
    workflow_condition_router,
    workflow_action_router,
    workflow_recipient_router,
    workflow_execution_router,
)
from uno.domain.domain_endpoints import attribute_router, attribute_type_router
from uno.meta.domain_endpoints import meta_type_router, meta_record_router


def register_all_routers(app: FastAPI):
    """
    Register all domain routers with the FastAPI application.
    """
    # Queries
    app.include_router(query_router)
    app.include_router(query_path_router)
    # Workflows
    app.include_router(workflow_def_router)
    app.include_router(workflow_trigger_router)
    app.include_router(workflow_condition_router)
    app.include_router(workflow_action_router)
    app.include_router(workflow_recipient_router)
    app.include_router(workflow_execution_router)
    # Attributes
    app.include_router(attribute_router)
    app.include_router(attribute_type_router)
    # Meta
    app.include_router(meta_type_router)
    app.include_router(meta_record_router)
