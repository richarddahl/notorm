# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API integration for the values module.

This module provides a convenient way to register value endpoints
with a FastAPI application using the domain-driven approach.
"""

from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, Depends, Security, APIRouter

# Domain-driven approach
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.api.repository_adapter import RepositoryAdapter
from uno.values.domain_repositories import (
    ValueRepository,
    TextValueRepository,
    IntegerValueRepository,
    BooleanValueRepository,
    DateValueRepository,
    TimeValueRepository,
    DateTimeValueRepository,
    DecimalValueRepository,
    AttachmentRepository,
)
from uno.values.entities import (
    BaseValue,
    TextValue,
    IntegerValue,
    BooleanValue,
    DateValue,
    TimeValue,
    DateTimeValue,
    DecimalValue,
    Attachment,
)
from uno.values.schemas import (
    ValueSchemaManager,
    TextValueSchemaManager,
    IntegerValueSchemaManager,
    BooleanValueSchemaManager,
    DateValueSchemaManager,
    TimeValueSchemaManager,
    DateTimeValueSchemaManager,
    DecimalValueSchemaManager,
    AttachmentSchemaManager,
)
from uno.values.domain_services import (
    ValueService,
    TextValueService,
    IntegerValueService,
    BooleanValueService,
    DateValueService,
    TimeValueService,
    DateTimeValueService,
    DecimalValueService,
    AttachmentService,
)


def register_domain_value_endpoints_api(
    app_or_router: FastAPI | APIRouter,
    path_prefix: str = "/api/v1/values",
    dependencies: list[Any] | None = None,
    include_auth: bool = True,
) -> dict[str, list[Any]]:
    """
    Register value endpoints with the FastAPI app or router using domain-driven design.

    This function creates RESTful API endpoints for the Values module, including
    CRUD operations for different value types following DDD principles.

    Args:
        app_or_router: The FastAPI application or router to register the endpoints with
        path_prefix: Prefix for all endpoint URLs
        dependencies: List of dependencies to apply to all endpoints
        include_auth: Whether to include authentication dependencies

    Returns:
        A dictionary containing the registered endpoints

    Raises:
        ValueError: If app_or_router is neither a FastAPI app nor an APIRouter
    """
    # Determine if app_or_router is a FastAPI app or an APIRouter
    is_app = isinstance(app_or_router, FastAPI)
    is_router = isinstance(app_or_router, APIRouter)

    if not (is_app or is_router):
        raise ValueError("app_or_router must be either a FastAPI app or an APIRouter")

    # Set up endpoint factory
    endpoint_factory = UnoEndpointFactory()

    # Create repositories
    repositories = {
        "text": TextValueRepository(),
        "integer": IntegerValueRepository(),
        "boolean": BooleanValueRepository(),
        "date": DateValueRepository(),
        "time": TimeValueRepository(),
        "datetime": DateTimeValueRepository(),
        "decimal": DecimalValueRepository(),
        "attachment": AttachmentRepository(),
    }

    # Create schema managers
    schema_managers = {
        "text": TextValueSchemaManager(),
        "integer": IntegerValueSchemaManager(),
        "boolean": BooleanValueSchemaManager(),
        "date": DateValueSchemaManager(),
        "time": TimeValueSchemaManager(),
        "datetime": DateTimeValueSchemaManager(),
        "decimal": DecimalValueSchemaManager(),
        "attachment": AttachmentSchemaManager(),
    }

    # Entity types
    entity_types = {
        "text": TextValue,
        "integer": IntegerValue,
        "boolean": BooleanValue,
        "date": DateValue,
        "time": TimeValue,
        "datetime": DateTimeValue,
        "decimal": DecimalValue,
        "attachment": Attachment,
    }

    # Create default dependencies if none provided
    if dependencies is None:
        dependencies = []

        # Add authentication dependencies if requested
        if include_auth:
            # This would typically check for auth providers and add appropriate dependencies
            pass

    # Create endpoint target
    target = app_or_router

    endpoints = {}

    # Create endpoints for each value type
    for value_type, repository in repositories.items():
        entity_type = entity_types[value_type]
        schema_manager = schema_managers[value_type]

        endpoints[value_type] = endpoint_factory.create_endpoints(
            app=target if is_app else None,
            router=target if is_router else None,
            repository=repository,
            entity_type=entity_type,
            schema_manager=schema_manager,
            endpoints=["Create", "View", "List", "Update", "Delete"],
            path_prefix=f"{path_prefix}/{value_type}",
            endpoint_tags=["Values", value_type.capitalize()],
            dependencies=dependencies,
        )

    return endpoints
