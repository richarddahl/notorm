"""
CQRS pattern implementation for HTTP endpoints.

This module provides classes for implementing the Command Query Responsibility Segregation
(CQRS) pattern with HTTP endpoints, separating read and write operations.
"""

from typing import Callable, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel

from uno.core.errors.result import Result
from uno.domain.entity.service import ApplicationService, DomainService

from . import EndpointProtocol, IdType, RequestModel, ResponseModel
from .base import BaseEndpoint, CommandEndpoint, QueryEndpoint

__all__ = [
    "QueryHandler",
    "CommandHandler",
    "CqrsEndpoint",
]


class QueryHandler(Generic[RequestModel, ResponseModel]):
    """Handler for a query operation in a CQRS endpoint."""

    def __init__(
        self,
        service: Union[ApplicationService, DomainService],
        response_model: Type[ResponseModel],
        query_model: Optional[Type[RequestModel]] = None,
        path: str = "",
        method: str = "get",
    ):
        """
        Initialize a new query handler.

        Args:
            service: The service to use for query operations.
            response_model: The Pydantic model for responses.
            query_model: Optional model for query parameters.
            path: The path for the query endpoint (added to the base path).
            method: The HTTP method to use (default: "get").
        """
        self.service = service
        self.response_model = response_model
        self.query_model = query_model
        self.path = path
        self.method = method


class CommandHandler(Generic[RequestModel, ResponseModel]):
    """Handler for a command operation in a CQRS endpoint."""

    def __init__(
        self,
        service: Union[ApplicationService, DomainService],
        command_model: Type[RequestModel],
        response_model: Optional[Type[ResponseModel]] = None,
        path: str = "",
        method: str = "post",
    ):
        """
        Initialize a new command handler.

        Args:
            service: The service to use for command operations.
            command_model: The Pydantic model for command data.
            response_model: Optional model for command responses.
            path: The path for the command endpoint (added to the base path).
            method: The HTTP method to use (default: "post").
        """
        self.service = service
        self.command_model = command_model
        self.response_model = response_model
        self.path = path
        self.method = method


class CqrsEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """
    Endpoint that implements the CQRS pattern.

    This class provides a way to create API endpoints that follow the Command Query
    Responsibility Segregation (CQRS) pattern, separating read and write operations.
    """

    def __init__(
        self,
        *,
        queries: list[QueryHandler] = None,
        commands: list[CommandHandler] = None,
        router: Optional[APIRouter] = None,
        tags: list[str] | None = None,
        base_path: str = "",
    ):
        """
        Initialize a new CQRS endpoint instance.

        Args:
            queries: List of query handlers for this endpoint.
            commands: List of command handlers for this endpoint.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            base_path: The base path for all routes.
        """
        super().__init__(router=router, tags=tags)
        self.queries = queries or []
        self.commands = commands or []
        self.base_path = base_path

        # Register all query and command handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all query and command handlers."""
        # Register query handlers
        for query in self.queries:
            path = f"{self.base_path}{query.path}"
            endpoint = QueryEndpoint(
                service=query.service,
                response_model=query.response_model,
                query_model=query.query_model,
                router=self.router,
                tags=self.tags,
                path=path,
                method=query.method,
            )

        # Register command handlers
        for command in self.commands:
            path = f"{self.base_path}{command.path}"
            endpoint = CommandEndpoint(
                service=command.service,
                command_model=command.command_model,
                response_model=command.response_model,
                router=self.router,
                tags=self.tags,
                path=path,
                method=command.method,
            )

    def add_query(self, query: QueryHandler) -> "CqrsEndpoint":
        """
        Add a query handler to this endpoint.

        Args:
            query: The query handler to add.

        Returns:
            This endpoint instance for chaining.
        """
        self.queries.append(query)
        path = f"{self.base_path}{query.path}"

        # Register the query handler
        endpoint = QueryEndpoint(
            service=query.service,
            response_model=query.response_model,
            query_model=query.query_model,
            router=self.router,
            tags=self.tags,
            path=path,
            method=query.method,
        )

        return self

    def add_command(self, command: CommandHandler) -> "CqrsEndpoint":
        """
        Add a command handler to this endpoint.

        Args:
            command: The command handler to add.

        Returns:
            This endpoint instance for chaining.
        """
        self.commands.append(command)
        path = f"{self.base_path}{command.path}"

        # Register the command handler
        endpoint = CommandEndpoint(
            service=command.service,
            command_model=command.command_model,
            response_model=command.response_model,
            router=self.router,
            tags=self.tags,
            path=path,
            method=command.method,
        )

        return self
