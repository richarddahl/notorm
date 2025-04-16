# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain-driven API integration for the Values module.

This module provides a convenient way to register value endpoints
with a FastAPI application using domain-driven design principles.
"""

from fastapi import APIRouter, FastAPI
from typing import List, Dict, Any, Optional, Union

from uno.values.repositories import (
    BooleanValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    DecimalValueRepository,
    DateValueRepository,
    DateTimeValueRepository,
    TimeValueRepository,
    AttachmentRepository,
)
from uno.values.domain_endpoints_factory import register_domain_value_endpoints


def register_domain_value_endpoints_api(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    boolean_repository: Optional[BooleanValueRepository] = None,
    integer_repository: Optional[IntegerValueRepository] = None,
    text_repository: Optional[TextValueRepository] = None,
    decimal_repository: Optional[DecimalValueRepository] = None,
    date_repository: Optional[DateValueRepository] = None,
    datetime_repository: Optional[DateTimeValueRepository] = None,
    time_repository: Optional[TimeValueRepository] = None,
    attachment_repository: Optional[AttachmentRepository] = None,
) -> Dict[str, List[Any]]:
    """
    Register value endpoints with the FastAPI app or router using domain-driven design.
    
    This function automatically creates a router if you provide an app, or uses the
    provided router directly. It then creates endpoints for each value type, following
    domain-driven design principles with entities, repositories, and DTOs.
    
    Args:
        app_or_router: FastAPI app or router to register endpoints with
        path_prefix: API route prefix (default: "/api/v1")
        dependencies: List of FastAPI dependencies for all endpoints
        include_auth: Whether to include authorization dependencies
        boolean_repository: Repository for boolean values (optional)
        integer_repository: Repository for integer values (optional)
        text_repository: Repository for text values (optional)
        decimal_repository: Repository for decimal values (optional)
        date_repository: Repository for date values (optional)
        datetime_repository: Repository for datetime values (optional)
        time_repository: Repository for time values (optional)
        attachment_repository: Repository for file attachments (optional)
    
    Returns:
        Dict mapping value types to their respective endpoints
    """
    # Create a router if an app was provided
    if isinstance(app_or_router, FastAPI):
        router = APIRouter()
    else:
        router = app_or_router
    
    # Default repositories if not provided
    from uno.database.db_manager import DBManager
    db_manager = DBManager()
    
    if boolean_repository is None:
        boolean_repository = BooleanValueRepository(db_manager)
    
    if integer_repository is None:
        integer_repository = IntegerValueRepository(db_manager)
    
    if text_repository is None:
        text_repository = TextValueRepository(db_manager)
    
    if decimal_repository is None:
        decimal_repository = DecimalValueRepository(db_manager)
    
    if date_repository is None:
        date_repository = DateValueRepository(db_manager)
    
    if datetime_repository is None:
        datetime_repository = DateTimeValueRepository(db_manager)
    
    if time_repository is None:
        time_repository = TimeValueRepository(db_manager)
    
    if attachment_repository is None:
        attachment_repository = AttachmentRepository(db_manager)
    
    # Build default dependencies list
    if dependencies is None:
        dependencies = []
    
    if include_auth:
        # Add auth dependencies if needed
        try:
            from uno.authorization.endpoints import get_current_user
            dependencies.append(get_current_user)
        except ImportError:
            # Auth module not available or not configured
            pass
    
    # Register domain endpoints
    endpoints = register_domain_value_endpoints(
        router=router,
        boolean_repository=boolean_repository,
        integer_repository=integer_repository,
        text_repository=text_repository,
        decimal_repository=decimal_repository,
        date_repository=date_repository,
        datetime_repository=datetime_repository,
        time_repository=time_repository,
        attachment_repository=attachment_repository,
        prefix=f"{path_prefix}/values",
        tags=["Values"],
        dependencies=dependencies,
    )
    
    # If an app was provided, include the router
    if isinstance(app_or_router, FastAPI):
        app_or_router.include_router(router)
    
    return endpoints