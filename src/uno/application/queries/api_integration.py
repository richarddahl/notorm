# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API integration for the Queries module.

This module provides a convenient way to register query endpoints
with a FastAPI application using domain-driven design principles.
"""

from fastapi import APIRouter, FastAPI, Depends
from typing import List, Dict, Any, Optional, Union

from uno.api.endpoint_factory import UnoEndpointFactory
from uno.queries.domain_repositories import (
    QueryPathRepository,
    QueryValueRepository,
    QueryRepository,
)
from uno.queries.domain_services import (
    QueryPathService,
    QueryValueService,
    QueryService,
)
from uno.queries.entities import (
    QueryPath,
    QueryValue,
    Query,
)
from uno.queries.schemas import (
    QueryPathSchemaManager,
    QueryValueSchemaManager,
    QuerySchemaManager,
)


def register_query_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    query_path_repository: Optional[QueryPathRepository] = None,
    query_value_repository: Optional[QueryValueRepository] = None,
    query_repository: Optional[QueryRepository] = None,
) -> Dict[str, Any]:
    """
    Register query endpoints with the FastAPI app or router.
    
    This function registers endpoints for query paths, query values, and queries
    using domain-driven design principles.
    
    Args:
        app_or_router: FastAPI app or router to register endpoints with
        path_prefix: API route prefix (default: "/api/v1")
        dependencies: List of FastAPI dependencies for all endpoints
        include_auth: Whether to include authorization dependencies
        query_path_repository: Repository for query paths (optional)
        query_value_repository: Repository for query values (optional)
        query_repository: Repository for queries (optional)
    
    Returns:
        Dict mapping entity types to their respective endpoints
    """
    # Create a router if an app was provided
    if isinstance(app_or_router, FastAPI):
        router = APIRouter()
    else:
        router = app_or_router
    
    # Default repositories if not provided
    from uno.database.db_manager import DBManager
    db_manager = DBManager()
    
    if query_path_repository is None:
        query_path_repository = QueryPathRepository(db_manager)
    
    if query_value_repository is None:
        query_value_repository = QueryValueRepository(db_manager)
    
    if query_repository is None:
        query_repository = QueryRepository(db_manager)
    
    # Build default dependencies list
    if dependencies is None:
        dependencies = []
    
    if include_auth:
        # Add auth dependencies if needed
        try:
            from uno.authorization.endpoints import get_current_user
            dependencies.append(Depends(get_current_user))
        except ImportError:
            # Auth module not available or not configured
            pass
    
    # Create services
    query_path_service = QueryPathService(query_path_repository)
    query_value_service = QueryValueService(query_value_repository)
    query_service = QueryService(
        repository=query_repository,
        query_value_service=query_value_service,
        query_path_service=query_path_service,
    )
    
    # Create schema managers
    query_path_schema_manager = QueryPathSchemaManager()
    query_value_schema_manager = QueryValueSchemaManager()
    query_schema_manager = QuerySchemaManager(query_value_schema_manager)
    
    # Initialize endpoint factory
    endpoint_factory = UnoEndpointFactory()
    
    # Create endpoints for query paths
    query_path_endpoints = endpoint_factory.create_endpoints(
        app=router,
        repository=query_path_repository,
        entity_type=QueryPath,
        schema_manager=query_path_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{path_prefix}/query-paths",
        endpoint_tags=["Query Paths"],
        dependencies=dependencies,
    )
    
    # Create endpoints for query values
    query_value_endpoints = endpoint_factory.create_endpoints(
        app=router,
        repository=query_value_repository,
        entity_type=QueryValue,
        schema_manager=query_value_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{path_prefix}/query-values",
        endpoint_tags=["Query Values"],
        dependencies=dependencies,
    )
    
    # Create endpoints for queries
    query_endpoints = endpoint_factory.create_endpoints(
        app=router,
        repository=query_repository,
        entity_type=Query,
        schema_manager=query_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{path_prefix}/queries",
        endpoint_tags=["Queries"],
        dependencies=dependencies,
    )
    
    # Add specialized endpoints for query execution
    
    # TODO: Add custom endpoints for:
    # - Query execution
    # - Query with values creation
    # - Sub-query management
    # These would need custom implementations to handle the complex relationships
    
    # If an app was provided, include the router
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    return {
        "query_path_endpoints": query_path_endpoints,
        "query_value_endpoints": query_value_endpoints,
        "query_endpoints": query_endpoints,
    }