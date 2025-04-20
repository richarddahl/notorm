#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Advanced recipient resolution for workflow notifications.

This module provides enhanced recipient targeting capabilities, supporting
complex recipient resolution like attribute-based, dynamic, and query-based targeting.
"""

import logging
import json
import asyncio
import re
from datetime import datetime
from typing import (
    Dict,
    Any,
    List,
    Set,
    Optional,
    Callable,
    Union,
    Type,
    Protocol,
    runtime_checkable,
)
from enum import Enum

import inject

from uno.core.errors.result import Result
from uno.core.base.error import BaseError
from uno.workflows.errors import (
    WorkflowErrorCode,
    WorkflowRecipientError,
    WorkflowInvalidDefinitionError,
)
from uno.settings import uno_settings
from uno.database.db_manager import DBManager

from uno.workflows.models import WorkflowRecipientType
from uno.workflows.entities import WorkflowRecipient, User


class RecipientError(BaseError):
    """Error raised when there's an issue resolving recipients."""

    pass


@runtime_checkable
class RecipientResolver(Protocol):
    """Interface for recipient resolvers."""

    async def resolve(
        self, recipient: WorkflowRecipient, context: Dict[str, Any]
    ) -> Result[list[User]]:
        """Resolve a recipient to a list of users."""
        ...


class UserResolver:
    """Resolver for user recipients."""

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: logging.Logger | None = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def resolve(
        self, recipient: WorkflowRecipient, context: Dict[str, Any]
    ) -> Result[list[User]]:
        """Resolve a user recipient."""
        try:
            # Check if user ID contains a template variable
            recipient_id = recipient.recipient_id
            if "{{" in recipient_id and "}}" in recipient_id:
                recipient_id = self._interpolate_template(recipient_id, context)

            # If the ID contains multiple values (comma-separated), split them
            user_ids = [id.strip() for id in recipient_id.split(",") if id.strip()]

            users = []
            for user_id in user_ids:
                user = await self._get_user(user_id)
                if user:
                    users.append(user)

            if not users:
                self.logger.warning(f"No users found for IDs: {recipient_id}")
                return Success([])

            return Success(users)

        except Exception as e:
            self.logger.exception(f"Error resolving user recipient: {e}")
            return Failure(RecipientError(f"Error resolving user recipient: {str(e)}"))

    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            if not self.db_manager:
                # Create a placeholder user for testing
                return User(
                    id=user_id,
                    username=f"user_{user_id}",
                    email=f"user_{user_id}@example.com",
                    is_active=True,
                )

            async with self.db_manager.get_enhanced_session() as session:
                query = """
                SELECT id, username, email, first_name, last_name, is_active, created_at
                FROM "user"
                WHERE id = :user_id
                """

                result = await session.execute(query, {"user_id": user_id})
                user_data = result.fetchone()

                if not user_data:
                    return None

                return User.from_record(user_data)

        except Exception as e:
            self.logger.error(f"Error fetching user {user_id}: {e}")
            return None

    def _interpolate_template(self, template: str, context: Dict[str, Any]) -> str:
        """Interpolate template variables in a string."""
        result = template

        # Match {{ variable }} pattern
        matches = re.findall(r"{{([^}]+)}}", template)
        for match in matches:
            var_name = match.strip()

            # Handle nested properties using dot notation
            if "." in var_name:
                parts = var_name.split(".")
                value = context
                for part in parts:
                    part = part.strip()
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
            else:
                value = context.get(var_name)

            if value is not None:
                placeholder = "{{" + match + "}}"
                result = result.replace(placeholder, str(value))

        return result


class RoleResolver:
    """Resolver for role recipients."""

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: logging.Logger | None = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def resolve(
        self, recipient: WorkflowRecipient, context: Dict[str, Any]
    ) -> Result[list[User]]:
        """Resolve a role recipient to a list of users."""
        try:
            # Get the role name
            role_name = recipient.recipient_id

            # Get users with this role
            users = await self._get_users_by_role(role_name)

            if not users:
                self.logger.warning(f"No users found for role: {role_name}")
                return Success([])

            return Success(users)

        except Exception as e:
            self.logger.exception(f"Error resolving role recipient: {e}")
            return Failure(RecipientError(f"Error resolving role recipient: {str(e)}"))

    async def _get_users_by_role(self, role_name: str) -> list[User]:
        """Get all users with a specific role."""
        try:
            if not self.db_manager:
                # Return empty list for testing
                return []

            async with self.db_manager.get_enhanced_session() as session:
                query = """
                SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active, u.created_at
                FROM "user" u
                JOIN user_role ur ON u.id = ur.user_id
                JOIN role r ON ur.role_id = r.id
                WHERE r.name = :role_name AND u.is_active = TRUE
                """

                result = await session.execute(query, {"role_name": role_name})
                users = []

                for user_data in result:
                    user = User.from_record(user_data)
                    users.append(user)

                return users

        except Exception as e:
            self.logger.error(f"Error fetching users for role {role_name}: {e}")
            return []


class GroupResolver:
    """Resolver for group recipients."""

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: logging.Logger | None = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def resolve(
        self, recipient: WorkflowRecipient, context: Dict[str, Any]
    ) -> Result[list[User]]:
        """Resolve a group recipient to a list of users."""
        try:
            # Get the group ID or name
            group_id = recipient.recipient_id

            # Get users in this group
            users = await self._get_users_by_group(group_id)

            if not users:
                self.logger.warning(f"No users found for group: {group_id}")
                return Success([])

            return Success(users)

        except Exception as e:
            self.logger.exception(f"Error resolving group recipient: {e}")
            return Failure(RecipientError(f"Error resolving group recipient: {str(e)}"))

    async def _get_users_by_group(self, group_id: str) -> list[User]:
        """Get all users in a specific group."""
        try:
            if not self.db_manager:
                # Return empty list for testing
                return []

            async with self.db_manager.get_enhanced_session() as session:
                # First try to resolve by ID
                query = """
                SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active, u.created_at
                FROM "user" u
                JOIN user_group ug ON u.id = ug.user_id
                JOIN "group" g ON ug.group_id = g.id
                WHERE g.id = :group_id AND u.is_active = TRUE
                """

                result = await session.execute(query, {"group_id": group_id})
                users = []

                for user_data in result:
                    user = User.from_record(user_data)
                    users.append(user)

                # If no users found, try resolving by name
                if not users:
                    query = """
                    SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active, u.created_at
                    FROM "user" u
                    JOIN user_group ug ON u.id = ug.user_id
                    JOIN "group" g ON ug.group_id = g.id
                    WHERE g.name = :group_name AND u.is_active = TRUE
                    """

                    result = await session.execute(query, {"group_name": group_id})

                    for user_data in result:
                        user = User.from_record(user_data)
                        users.append(user)

                return users

        except Exception as e:
            self.logger.error(f"Error fetching users for group {group_id}: {e}")
            return []


class AttributeResolver:
    """Resolver for attribute-based recipients."""

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: logging.Logger | None = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def resolve(
        self, recipient: WorkflowRecipient, context: Dict[str, Any]
    ) -> Result[list[User]]:
        """
        Resolve recipients based on attribute values.

        This supports finding users based on attributes like:
        - department:engineering (users in engineering department)
        - location:remote (users with remote location)
        - skill:python (users with Python skill)
        """
        try:
            # Parse the attribute specification (format: attribute_name:attribute_value)
            attribute_spec = recipient.recipient_id

            # Check for a template in the attribute spec
            if "{{" in attribute_spec and "}}" in attribute_spec:
                attribute_spec = self._interpolate_template(attribute_spec, context)

            parts = attribute_spec.split(":", 1)
            if len(parts) != 2:
                return Failure(
                    RecipientError(
                        f"Invalid attribute specification: {attribute_spec}. Format should be attribute_name:attribute_value"
                    )
                )

            attribute_name = parts[0].strip()
            attribute_value = parts[1].strip()

            # Get users with this attribute
            users = await self._get_users_by_attribute(attribute_name, attribute_value)

            if not users:
                self.logger.warning(
                    f"No users found with attribute {attribute_name}:{attribute_value}"
                )
                return Success([])

            return Success(users)

        except Exception as e:
            self.logger.exception(f"Error resolving attribute recipient: {e}")
            return Failure(
                RecipientError(f"Error resolving attribute recipient: {str(e)}")
            )

    async def _get_users_by_attribute(
        self, attribute_name: str, attribute_value: str
    ) -> list[User]:
        """Get all users with a specific attribute value."""
        try:
            if not self.db_manager:
                # Return empty list for testing
                return []

            async with self.db_manager.get_enhanced_session() as session:
                # Query depends on whether we're using attributes_values system or user_attribute table
                # First, try using attributes_values if it exists
                try:
                    query = """
                    SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active, u.created_at
                    FROM "user" u
                    JOIN attribute_value av ON av.record_id = u.id
                    JOIN attribute a ON av.attribute_id = a.id
                    WHERE a.name = :attribute_name 
                      AND av.value_text = :attribute_value
                      AND u.is_active = TRUE
                    """

                    result = await session.execute(
                        query,
                        {
                            "attribute_name": attribute_name,
                            "attribute_value": attribute_value,
                        },
                    )

                    users = []
                    for user_data in result:
                        user = User.from_record(user_data)
                        users.append(user)

                    if users:
                        return users

                except Exception:
                    # Table might not exist, fall back to user_attribute
                    pass

                # Try using user_attribute table if available
                try:
                    query = """
                    SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active, u.created_at
                    FROM "user" u
                    JOIN user_attribute ua ON u.id = ua.user_id
                    WHERE ua.name = :attribute_name 
                      AND ua.value = :attribute_value
                      AND u.is_active = TRUE
                    """

                    result = await session.execute(
                        query,
                        {
                            "attribute_name": attribute_name,
                            "attribute_value": attribute_value,
                        },
                    )

                    users = []
                    for user_data in result:
                        user = User.from_record(user_data)
                        users.append(user)

                    return users

                except Exception:
                    # Table might not exist
                    return []

                return []

        except Exception as e:
            self.logger.error(
                f"Error fetching users for attribute {attribute_name}:{attribute_value}: {e}"
            )
            return []

    def _interpolate_template(self, template: str, context: Dict[str, Any]) -> str:
        """Interpolate template variables in a string."""
        result = template

        # Match {{ variable }} pattern
        matches = re.findall(r"{{([^}]+)}}", template)
        for match in matches:
            var_name = match.strip()

            # Handle nested properties using dot notation
            if "." in var_name:
                parts = var_name.split(".")
                value = context
                for part in parts:
                    part = part.strip()
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
            else:
                value = context.get(var_name)

            if value is not None:
                placeholder = "{{" + match + "}}"
                result = result.replace(placeholder, str(value))

        return result


class QueryRecipientResolver:
    """Resolver for query-based recipients."""

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: logging.Logger | None = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def resolve(
        self, recipient: WorkflowRecipient, context: Dict[str, Any]
    ) -> Result[list[User]]:
        """
        Resolve recipients based on a saved query.

        This allows using the same query system that's used for workflow conditions
        to find users matching complex criteria.
        """
        try:
            # Get the query ID
            query_id = recipient.recipient_id

            # The notification_config should contain details about how to use the query
            config = recipient.notification_config or {}

            # Get the query
            query = await Query.get(query_id)
            if not query:
                return Failure(RecipientError(f"Query with ID {query_id} not found"))

            # Execute the query to get matching users
            # How this is done depends on whether the query is targeting users directly
            # or if we need to extract user IDs from the results

            # Check if query targets users directly or needs extraction
            target_type = config.get("target_type", "user")

            if target_type == "user":
                # Query returns users directly
                result = await query.execute()

                if result.is_failure:
                    return Failure(
                        RecipientError(f"Error executing query: {result.error}")
                    )

                # Convert query results to User objects
                users = []
                for record in result.value:
                    # If the record is already a User object, use it directly
                    if isinstance(record, User):
                        users.append(record)
                    # Otherwise, try to create a User from the record
                    elif isinstance(record, dict) and "id" in record:
                        user = await self._get_user(record["id"])
                        if user:
                            users.append(user)

                return Success(users)

            elif target_type == "extract":
                # Need to extract user IDs from query results
                result = await query.execute()

                if result.is_failure:
                    return Failure(
                        RecipientError(f"Error executing query: {result.error}")
                    )

                # Extract user IDs from the results
                user_id_field = config.get("user_id_field", "user_id")
                user_ids = []

                for record in result.value:
                    if isinstance(record, dict) and user_id_field in record:
                        user_ids.append(record[user_id_field])
                    # If the record is a string, assume it's a user ID
                    elif isinstance(record, str):
                        user_ids.append(record)

                # Resolve the user IDs to User objects
                users = []
                for user_id in user_ids:
                    user = await self._get_user(user_id)
                    if user:
                        users.append(user)

                return Success(users)

            else:
                return Failure(
                    RecipientError(f"Unsupported target type: {target_type}")
                )

        except Exception as e:
            self.logger.exception(f"Error resolving query recipient: {e}")
            return Failure(RecipientError(f"Error resolving query recipient: {str(e)}"))

    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            if not self.db_manager:
                # Create a placeholder user for testing
                return User(
                    id=user_id,
                    username=f"user_{user_id}",
                    email=f"user_{user_id}@example.com",
                    is_active=True,
                )

            async with self.db_manager.get_enhanced_session() as session:
                query = """
                SELECT id, username, email, first_name, last_name, is_active, created_at
                FROM "user"
                WHERE id = :user_id
                """

                result = await session.execute(query, {"user_id": user_id})
                user_data = result.fetchone()

                if not user_data:
                    return None

                return User.from_record(user_data)

        except Exception as e:
            self.logger.error(f"Error fetching user {user_id}: {e}")
            return None


class DynamicRecipientResolver:
    """Resolver for dynamically determined recipients."""

    @inject.params(logger=logging.Logger)
    def __init__(
        self,
        logger: logging.Logger | None = None,
        dynamic_resolvers: Dict[str, Callable] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.dynamic_resolvers = dynamic_resolvers or {}

    def register_dynamic_resolver(
        self, resolver_type: str, resolver_func: Callable
    ) -> None:
        """Register a dynamic resolver function for a specific type."""
        self.dynamic_resolvers[resolver_type] = resolver_func

    async def resolve(
        self, recipient: WorkflowRecipient, context: Dict[str, Any]
    ) -> Result[list[User]]:
        """
        Resolve recipients using a dynamic resolver function.

        This allows for custom logic to determine recipients based on
        business rules, complex conditions, or external systems.
        """
        try:
            # Get the resolver type
            resolver_type = recipient.recipient_id

            # Find the corresponding resolver function
            resolver_func = self.dynamic_resolvers.get(resolver_type)
            if not resolver_func:
                return Failure(
                    RecipientError(
                        f"No resolver found for dynamic recipient type: {resolver_type}"
                    )
                )

            # Add the recipient object to the context for additional configuration
            resolver_context = context.copy()
            resolver_context["recipient"] = recipient

            # Execute the dynamic function
            result = resolver_func(resolver_context)

            # Handle both synchronous and asynchronous functions
            if asyncio.iscoroutine(result):
                result = await result

            # If the result is already a Result object, return it
            if isinstance(result, Result):
                return result

            # If the result is a list of User objects, wrap it in a Success
            if isinstance(result, list) and all(isinstance(u, User) for u in result):
                return Success(result)

            # If the result is something else, try to convert it to a list of User objects
            if isinstance(result, list):
                users = []
                for item in result:
                    if isinstance(item, User):
                        users.append(item)
                    elif isinstance(item, dict) and "id" in item:
                        # Create a User object from a dict
                        users.append(
                            User(
                                id=item["id"],
                                username=item.get("username", f"user_{item['id']}"),
                                email=item.get(
                                    "email", f"user_{item['id']}@example.com"
                                ),
                                is_active=item.get("is_active", True),
                            )
                        )
                    elif isinstance(item, str):
                        # Assume string is a user ID
                        users.append(
                            User(
                                id=item,
                                username=f"user_{item}",
                                email=f"user_{item}@example.com",
                                is_active=True,
                            )
                        )
                return Success(users)

            # If we can't handle the result, return an error
            return Failure(
                RecipientError(
                    f"Dynamic resolver returned unrecognized result type: {type(result)}"
                )
            )

        except Exception as e:
            self.logger.exception(f"Error resolving dynamic recipient: {e}")
            return Failure(
                RecipientError(f"Error resolving dynamic recipient: {str(e)}")
            )


class RecipientResolverRegistry:
    """Registry for recipient resolvers."""

    def __init__(self):
        self.resolvers: Dict[WorkflowRecipientType, RecipientResolver] = {}

    def register(
        self,
        recipient_type: Union[WorkflowRecipientType, str],
        resolver: RecipientResolver,
    ) -> None:
        """Register a recipient resolver."""
        self.resolvers[recipient_type] = resolver

    def get(
        self, recipient_type: Union[WorkflowRecipientType, str]
    ) -> Optional[RecipientResolver]:
        """Get a recipient resolver by recipient type."""
        return self.resolvers.get(recipient_type)

    def has(self, recipient_type: Union[WorkflowRecipientType, str]) -> bool:
        """Check if a resolver exists for the recipient type."""
        return recipient_type in self.resolvers


# Add new recipient types for enhanced targeting
class ExtendedRecipientType(str, Enum):
    """Extended recipient types for enhanced targeting."""

    USER = WorkflowRecipientType.USER
    ROLE = WorkflowRecipientType.ROLE
    GROUP = WorkflowRecipientType.GROUP
    ATTRIBUTE = WorkflowRecipientType.ATTRIBUTE
    QUERY = "query"  # Query-based recipient targeting
    DYNAMIC = "dynamic"  # Dynamic resolver-based targeting


# Singleton registry instance
_registry = RecipientResolverRegistry()


def get_resolver_registry() -> RecipientResolverRegistry:
    """Get the global recipient resolver registry."""
    return _registry


def register_resolver(
    recipient_type: Union[WorkflowRecipientType, str], resolver: RecipientResolver
) -> None:
    """Register a recipient resolver in the global registry."""
    _registry.register(recipient_type, resolver)


def get_resolver(
    recipient_type: Union[WorkflowRecipientType, str],
) -> Optional[RecipientResolver]:
    """Get a recipient resolver from the global registry."""
    return _registry.get(recipient_type)


# Initialize standard resolvers
def init_resolvers() -> None:
    """Initialize and register the standard resolvers."""
    # Create resolvers
    user_resolver = UserResolver()
    role_resolver = RoleResolver()
    group_resolver = GroupResolver()
    attribute_resolver = AttributeResolver()
    query_resolver = QueryRecipientResolver()
    dynamic_resolver = DynamicRecipientResolver()

    # Register standard resolvers
    register_resolver(WorkflowRecipientType.USER, user_resolver)
    register_resolver(WorkflowRecipientType.ROLE, role_resolver)
    register_resolver(WorkflowRecipientType.GROUP, group_resolver)
    register_resolver(WorkflowRecipientType.ATTRIBUTE, attribute_resolver)

    # Register extended resolvers
    register_resolver(ExtendedRecipientType.QUERY, query_resolver)
    register_resolver(ExtendedRecipientType.DYNAMIC, dynamic_resolver)
