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

from uno.domain.repositories import (
    BooleanValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    DecimalValueRepository,
    DateValueRepository,
    DateTimeValueRepository,
    TimeValueRepository,
    AttachmentRepository,
)
from uno.values.domain_endpoints import register_values_routers


def register_domain_value_endpoints_api(
    app: FastAPI,
    include_auth: bool = True,
) -> None:
    """
    Register value endpoints with the FastAPI app using domain-driven design.

    This function registers domain service-based endpoints for each value type,
    following domain-driven design principles with entities, repositories, and services.

    Args:
        app: FastAPI app to register endpoints with
        include_auth: Whether to include authorization dependencies
    """
    # Register domain endpoints
    register_values_routers(app)

    # Register authorization middleware if needed
    if include_auth:
        try:
            from uno.authorization.middleware import register_auth_middleware

            register_auth_middleware(app)
        except ImportError:
            # Auth module not available or not configured
            pass
