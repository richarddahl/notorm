"""
Secure endpoint classes for the unified endpoint framework.

This module provides secure versions of the endpoint classes in the unified endpoint framework.
"""

from typing import Callable, Dict, List, Optional, Type, Union

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
from uno.domain.entity.service import ApplicationService, CrudService, DomainService

from ..base import BaseEndpoint, CrudEndpoint
from ..cqrs import CommandHandler, CqrsEndpoint, QueryHandler
from .dependencies import RequirePermissions, RequireRoles, get_user_context
from .models import Permission, UserContext
from .protocols import AuthenticationBackend


class SecureBaseEndpoint(BaseEndpoint):
    """
    Base class for secure API endpoints.

    This class extends BaseEndpoint to add authentication and authorization support.
    """

    def __init__(
        self,
        *,
        auth_backend: AuthenticationBackend,
        require_auth: bool = True,
        required_roles: list[str] | None = None,
        required_permissions: list[str] | None = None,
        **kwargs,
    ):
        """
        Initialize a new secure endpoint instance.

        Args:
            auth_backend: The authentication backend to use
            require_auth: Whether to require authentication for all routes
            required_roles: Optional list of required roles for all routes
            required_permissions: Optional list of required permissions for all routes
            **kwargs: Additional arguments for the parent class
        """
        super().__init__(**kwargs)
        self.auth_backend = auth_backend
        self.require_auth = require_auth
        self.required_roles = required_roles or []
        self.required_permissions = required_permissions or []

        # Add authentication and authorization dependencies
        if self.require_auth:
            self.router.dependencies.append(Depends(get_user_context))

            if self.required_roles:
                self.router.dependencies.append(
                    Depends(RequireRoles(self.required_roles))
                )

            if self.required_permissions:
                self.router.dependencies.append(
                    Depends(RequirePermissions(self.required_permissions))
                )


class SecureCrudEndpoint(CrudEndpoint):
    """
    Base class for secure CRUD endpoints.

    This class extends CrudEndpoint to add authentication and authorization support.
    """

    def __init__(
        self,
        *,
        auth_backend: AuthenticationBackend,
        create_permissions: list[str] | None = None,
        read_permissions: list[str] | None = None,
        update_permissions: list[str] | None = None,
        delete_permissions: list[str] | None = None,
        **kwargs,
    ):
        """
        Initialize a new secure CRUD endpoint instance.

        Args:
            auth_backend: The authentication backend to use
            create_permissions: Optional list of required permissions for create operations
            read_permissions: Optional list of required permissions for read operations
            update_permissions: Optional list of required permissions for update operations
            delete_permissions: Optional list of required permissions for delete operations
            **kwargs: Additional arguments for the parent class
        """
        # Store permission requirements before calling parent constructor
        self.auth_backend = auth_backend
        self.create_permissions = create_permissions or []
        self.read_permissions = read_permissions or []
        self.update_permissions = update_permissions or []
        self.delete_permissions = delete_permissions or []

        # Call parent constructor, but prevent it from registering routes
        kwargs["_register_routes"] = False
        super().__init__(**kwargs)

        # Register routes with permissions
        self._register_routes()

    def _register_routes(self) -> None:
        """Register the default CRUD routes with permissions."""
        self._register_create_route()
        self._register_get_route()
        self._register_list_route()
        self._register_update_route()
        self._register_delete_route()

    def _register_create_route(self) -> None:
        """Register the route for creating a new entity with permissions."""

        @self.router.post(
            self.path,
            response_model=self.response_model,
            status_code=status.HTTP_201_CREATED,
            dependencies=(
                [Depends(RequirePermissions(self.create_permissions))]
                if self.create_permissions
                else None
            ),
        )
        async def create(
            data: self.create_model,
            user_context: UserContext = Depends(get_user_context),
        ):
            result = await self.service.create(data)
            return self.handle_result(result, success_status=status.HTTP_201_CREATED)

    def _register_get_route(self) -> None:
        """Register the route for retrieving a single entity with permissions."""

        @self.router.get(
            f"{self.path}/{{id}}",
            response_model=self.response_model,
            dependencies=(
                [Depends(RequirePermissions(self.read_permissions))]
                if self.read_permissions
                else None
            ),
        )
        async def get(
            id: str,
            user_context: UserContext = Depends(get_user_context),
        ):
            result = await self.service.get_by_id(id)
            return self.handle_result(result)

    def _register_list_route(self) -> None:
        """Register the route for listing entities with permissions."""

        @self.router.get(
            self.path,
            response_model=list[self.response_model],
            dependencies=(
                [Depends(RequirePermissions(self.read_permissions))]
                if self.read_permissions
                else None
            ),
        )
        async def list_entities(
            user_context: UserContext = Depends(get_user_context),
        ):
            result = await self.service.get_all()
            return self.handle_result(result)

    def _register_update_route(self) -> None:
        """Register the route for updating an entity with permissions."""

        @self.router.put(
            f"{self.path}/{{id}}",
            response_model=self.response_model,
            dependencies=(
                [Depends(RequirePermissions(self.update_permissions))]
                if self.update_permissions
                else None
            ),
        )
        async def update(
            id: str,
            data: self.update_model,
            user_context: UserContext = Depends(get_user_context),
        ):
            result = await self.service.update(id, data)
            return self.handle_result(result)

    def _register_delete_route(self) -> None:
        """Register the route for deleting an entity with permissions."""

        @self.router.delete(
            f"{self.path}/{{id}}",
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=(
                [Depends(RequirePermissions(self.delete_permissions))]
                if self.delete_permissions
                else None
            ),
        )
        async def delete(
            id: str,
            user_context: UserContext = Depends(get_user_context),
        ):
            result = await self.service.delete(id)
            if isinstance(result, Success):
                return None
            self.handle_result(result)  # Will raise HTTPException


class SecureCqrsEndpoint(CqrsEndpoint):
    """
    Endpoint that implements the CQRS pattern with security.

    This class extends CqrsEndpoint to add authentication and authorization support.
    """

    def __init__(
        self,
        *,
        auth_backend: AuthenticationBackend,
        query_permissions: Optional[dict[str, list[str]]] = None,
        command_permissions: Optional[dict[str, list[str]]] = None,
        **kwargs,
    ):
        """
        Initialize a new secure CQRS endpoint instance.

        Args:
            auth_backend: The authentication backend to use
            query_permissions: Optional dict mapping query names to required permissions
            command_permissions: Optional dict mapping command names to required permissions
            **kwargs: Additional arguments for the parent class
        """
        # Store permission requirements before calling parent constructor
        self.auth_backend = auth_backend
        self.query_permissions = query_permissions or {}
        self.command_permissions = command_permissions or {}

        # Override handlers to add permissions
        if "queries" in kwargs:
            self._add_query_permissions(kwargs["queries"])

        if "commands" in kwargs:
            self._add_command_permissions(kwargs["commands"])

        # Call parent constructor
        super().__init__(**kwargs)

    def _add_query_permissions(self, queries: list[QueryHandler]) -> None:
        """
        Add permissions to query handlers.

        Args:
            queries: List of query handlers
        """
        for query in queries:
            name = query.path.strip("/").replace("/", "_") or "default"
            permissions = self.query_permissions.get(name, [])
            if permissions:
                query.dependencies = query.dependencies or []
                query.dependencies.append(Depends(RequirePermissions(permissions)))

    def _add_command_permissions(self, commands: list[CommandHandler]) -> None:
        """
        Add permissions to command handlers.

        Args:
            commands: List of command handlers
        """
        for command in commands:
            name = command.path.strip("/").replace("/", "_") or "default"
            permissions = self.command_permissions.get(name, [])
            if permissions:
                command.dependencies = command.dependencies or []
                command.dependencies.append(Depends(RequirePermissions(permissions)))

    def add_query(self, query: QueryHandler) -> "SecureCqrsEndpoint":
        """
        Add a query handler with permissions.

        Args:
            query: The query handler to add

        Returns:
            This endpoint instance for chaining
        """
        # Add permissions
        name = query.path.strip("/").replace("/", "_") or "default"
        permissions = self.query_permissions.get(name, [])
        if permissions:
            query.dependencies = query.dependencies or []
            query.dependencies.append(Depends(RequirePermissions(permissions)))

        # Add the query handler
        super().add_query(query)

        return self

    def add_command(self, command: CommandHandler) -> "SecureCqrsEndpoint":
        """
        Add a command handler with permissions.

        Args:
            command: The command handler to add

        Returns:
            This endpoint instance for chaining
        """
        # Add permissions
        name = command.path.strip("/").replace("/", "_") or "default"
        permissions = self.command_permissions.get(name, [])
        if permissions:
            command.dependencies = command.dependencies or []
            command.dependencies.append(Depends(RequirePermissions(permissions)))

        # Add the command handler
        super().add_command(command)

        return self
