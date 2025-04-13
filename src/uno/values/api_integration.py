# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API integration for the values module.

This module provides a convenient way to register value endpoints
with a FastAPI application.
"""

from fastapi import APIRouter
from typing import List, Optional

from uno.values.services import ValueService
from uno.values.endpoints import create_value_endpoints


def register_value_endpoints(
    router: APIRouter,
    value_service: ValueService,
    prefix: str = "/values",
    tags: List[str] = ["Values"]
):
    """
    Register all value endpoints with a FastAPI router.
    
    Args:
        router: FastAPI router
        value_service: Value service instance
        prefix: API route prefix for values
        tags: API tags for value endpoints
    """
    # Create value endpoints
    create_value_endpoints(
        router=router,
        value_service=value_service,
        prefix=prefix,
        tags=tags
    )
    
    return router