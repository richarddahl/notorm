# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example of using domain-driven design with API endpoints.

This demonstrates how to set up API endpoints for domain entities using
the repository pattern and domain-driven design approach.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from uno.api.endpoint_factory import UnoEndpointFactory
from uno.api.repository_adapter import RepositoryAdapter
from uno.core.protocols import Repository
from uno.api.entities import ApiResource, EndpointConfig, HttpMethod


# ==========================================
# Domain entities
# ==========================================


@dataclass
class UserEntity:
    """Domain entity for users."""

    email: str
    username: str
    full_name: str
    is_active: bool = True
    id: str | None = None
    created_at: str | None = None

    # Display names for OpenAPI documentation
    display_name: str = "User"
    display_name_plural: str = "Users"

    def __post_init__(self):
        """Initialize ID if not provided."""
        if self.id is None:
            self.id = str(uuid4())


# ==========================================
# API Schemas (DTOs)
# ==========================================


class UserCreateDto(BaseModel):
    """Data transfer object for creating users."""

    email: str
    username: str
    full_name: str
    is_active: bool = True


class UserViewDto(BaseModel):
    """Data transfer object for viewing users."""

    id: str
    email: str
    username: str
    full_name: str
    is_active: bool
    created_at: str | None = None


class UserUpdateDto(BaseModel):
    """Data transfer object for updating users."""

    id: str
    email: str | None = None
    username: str | None = None
    full_name: str | None = None
    is_active: Optional[bool] = None


# ==========================================
# Schema Manager
# ==========================================


class UserSchemaManager:
    """Schema manager for user entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": UserViewDto,
            "edit_schema": UserCreateDto,
            "update_schema": UserUpdateDto,
        }

    def get_schema(self, schema_name: str) -> type[BaseModel]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: UserEntity) -> UserViewDto:
        """Convert an entity to a DTO."""
        return UserViewDto(
            id=entity.id,
            email=entity.email,
            username=entity.username,
            full_name=entity.full_name,
            is_active=entity.is_active,
            created_at=entity.created_at,
        )

    def dto_to_entity(self, dto: BaseModel) -> UserEntity:
        """Convert a DTO to an entity."""
        data = dto.model_dump()
        return UserEntity(**data)


# ==========================================
# Repository
# ==========================================


class UserRepository(Repository):
    """Repository for user entities."""

    def __init__(self):
        """Initialize the repository with an in-memory store."""
        self.users: dict[str, UserEntity] = {}

    async def get_by_id(self, id: str) -> Optional[UserEntity]:
        """Get a user by ID."""
        return self.users.get(id)

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[UserEntity]:
        """List users with optional filtering and pagination."""
        # Extract pagination options
        if options and "pagination" in options:
            limit = options["pagination"].get("limit", 100)
            offset = options["pagination"].get("offset", 0)
        else:
            limit = 100
            offset = 0

        # Get all users as a list
        all_users = list(self.users.values())

        # Apply simple filtering if provided
        if filters:
            filtered_users = []
            for user in all_users:
                match = True
                for key, value in filters.items():
                    if hasattr(user, key) and getattr(user, key) != value:
                        match = False
                        break
                if match:
                    filtered_users.append(user)
            all_users = filtered_users

        # Apply pagination
        return all_users[offset : offset + limit]

    async def add(self, entity: UserEntity) -> UserEntity:
        """Add a user to the repository."""
        # Ensure ID is set
        if not entity.id:
            entity.id = str(uuid4())

        # Store the user
        self.users[entity.id] = entity
        return entity

    async def update(self, entity: UserEntity) -> UserEntity:
        """Update a user in the repository."""
        # Check if user exists
        if entity.id not in self.users:
            return None

        # Update the user
        existing = self.users[entity.id]

        # Only update fields that are provided
        for field in ["email", "username", "full_name", "is_active"]:
            if hasattr(entity, field) and getattr(entity, field) is not None:
                setattr(existing, field, getattr(entity, field))

        # Store the updated user
        self.users[entity.id] = existing
        return existing

    async def delete(self, id: str) -> bool:
        """Delete a user from the repository."""
        if id in self.users:
            del self.users[id]
            return True
        return False


# ==========================================
# API Endpoint Setup
# ==========================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Domain-Driven API Example")

    # Create repository and schema manager
    user_repository = UserRepository()
    user_schema_manager = UserSchemaManager()

    # Create endpoint factory
    endpoint_factory = UnoEndpointFactory()

    # Create endpoints for the User entity
    endpoints = endpoint_factory.create_endpoints(
        app=app,
        repository=user_repository,
        entity_type=UserEntity,
        schema_manager=user_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix="/api/v1",
        endpoint_tags=["Users"],
    )

    # Add demo data
    @app.on_event("startup")
    async def add_demo_data():
        # Create some demo users
        demo_users = [
            UserEntity(
                email="john@example.com",
                username="john",
                full_name="John Doe",
            ),
            UserEntity(
                email="jane@example.com",
                username="jane",
                full_name="Jane Smith",
            ),
            UserEntity(
                email="admin@example.com",
                username="admin",
                full_name="Admin User",
            ),
        ]

        # Add demo users to repository
        for user in demo_users:
            await user_repository.add(user)

    return app


# Create FastAPI application
app = create_app()


# For local development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
