# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, APIRouter, Depends

from uno.messaging.domain_endpoints import register_message_endpoints
from uno.messaging.domain_services import MessageDomainServiceProtocol


def register_messaging_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: list[Any] = None,
    include_auth: bool = True,
    message_service: Optional[MessageDomainServiceProtocol] = None,
) -> Dict[str, Dict[str, Any]]:
    """Register all messaging-related API endpoints.

    Args:
        app_or_router: The FastAPI app or router to register endpoints on
        path_prefix: The prefix for all API paths
        dependencies: List of dependencies to apply to all endpoints
        include_auth: Whether to include authentication dependencies
        message_service: Optional message service dependency override

    Returns:
        Dictionary containing all registered endpoint functions
    """
    if dependencies is None:
        dependencies = []

    # Create a router for messaging endpoints
    router = APIRouter()

    # Register message endpoints
    message_endpoints = register_message_endpoints(
        router=router,
        prefix=f"{path_prefix}/messages",
        tags=["messages"],
        dependencies=dependencies,
    )

    # Include router in the app or parent router
    app_or_router.include_router(router)

    # Return all registered endpoints
    return {
        "messages": message_endpoints,
    }
