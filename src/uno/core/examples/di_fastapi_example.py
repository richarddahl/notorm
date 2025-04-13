"""
Example FastAPI application using Uno's dependency injection system.

This example demonstrates how to integrate the Uno DI container with FastAPI,
including service registration, dependency resolution, and middleware configuration.
"""

import logging
from typing import List, Optional, Protocol, runtime_checkable
from fastapi import FastAPI, Depends, APIRouter, Request

from uno.core.di import initialize_container, get_container
from uno.core.di_fastapi import (
    FromDI, ScopedDeps, create_request_scope, get_service,
    configure_di_middleware, register_app_shutdown
)


# =============================================================================
# Service Interfaces and Implementations
# =============================================================================

@runtime_checkable
class UserRepository(Protocol):
    """Repository for users."""
    
    async def get_all(self) -> List[dict]:
        """Get all users."""
        ...
    
    async def get_by_id(self, user_id: int) -> Optional[dict]:
        """Get a user by ID."""
        ...
    
    async def create(self, user: dict) -> dict:
        """Create a new user."""
        ...
    
    async def update(self, user_id: int, user: dict) -> Optional[dict]:
        """Update a user."""
        ...
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user."""
        ...


@runtime_checkable
class UserService(Protocol):
    """Service for user management."""
    
    async def get_all_users(self) -> List[dict]:
        """Get all users."""
        ...
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get a user by ID."""
        ...
    
    async def create_user(self, user: dict) -> dict:
        """Create a new user."""
        ...
    
    async def update_user(self, user_id: int, user: dict) -> Optional[dict]:
        """Update a user."""
        ...
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        ...


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository."""
    
    def __init__(self):
        """Initialize with some test data."""
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ]
        self.next_id = 4
    
    async def get_all(self) -> List[dict]:
        """Get all users."""
        return self.users.copy()
    
    async def get_by_id(self, user_id: int) -> Optional[dict]:
        """Get a user by ID."""
        for user in self.users:
            if user["id"] == user_id:
                return user.copy()
        return None
    
    async def create(self, user: dict) -> dict:
        """Create a new user."""
        new_user = user.copy()
        new_user["id"] = self.next_id
        self.next_id += 1
        self.users.append(new_user)
        return new_user.copy()
    
    async def update(self, user_id: int, user: dict) -> Optional[dict]:
        """Update a user."""
        for i, existing_user in enumerate(self.users):
            if existing_user["id"] == user_id:
                updated_user = user.copy()
                updated_user["id"] = user_id
                self.users[i] = updated_user
                return updated_user.copy()
        return None
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user."""
        for i, user in enumerate(self.users):
            if user["id"] == user_id:
                self.users.pop(i)
                return True
        return False


class DefaultUserService(UserService):
    """Default implementation of UserService."""
    
    def __init__(self, repository: UserRepository, logger: logging.Logger):
        """Initialize with a repository and logger."""
        self.repository = repository
        self.logger = logger
    
    async def get_all_users(self) -> List[dict]:
        """Get all users."""
        self.logger.info("Getting all users")
        return await self.repository.get_all()
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get a user by ID."""
        self.logger.info(f"Getting user {user_id}")
        return await self.repository.get_by_id(user_id)
    
    async def create_user(self, user: dict) -> dict:
        """Create a new user."""
        self.logger.info(f"Creating new user: {user}")
        return await self.repository.create(user)
    
    async def update_user(self, user_id: int, user: dict) -> Optional[dict]:
        """Update a user."""
        self.logger.info(f"Updating user {user_id}: {user}")
        return await self.repository.update(user_id, user)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        self.logger.info(f"Deleting user {user_id}")
        return await self.repository.delete(user_id)


# =============================================================================
# Configure DI Container
# =============================================================================

def configure_services():
    """Configure the DI container with services."""
    # Initialize the container
    initialize_container()
    container = get_container()
    
    # Register logger
    logger = logging.getLogger("example")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    container.register_instance(logging.Logger, logger)
    
    # Register repository as a singleton
    container.register_singleton(UserRepository, InMemoryUserRepository)
    
    # Register service as a scoped service
    container.register_scoped(UserService, DefaultUserService)


# =============================================================================
# FastAPI Application
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Configure services
    configure_services()
    
    # Create FastAPI app
    app = FastAPI(title="Uno DI Example", description="Example of Uno DI with FastAPI")
    
    # Configure DI middleware
    configure_di_middleware(app)
    
    # Register shutdown handler
    register_app_shutdown(app)
    
    # Create router
    router = APIRouter()
    
    # Define routes
    @router.get("/users")
    async def get_users(
        request: Request,
        user_service: UserService = Depends(get_service(UserService))
    ):
        """Get all users."""
        return await user_service.get_all_users()
    
    @router.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        user_service: UserService = Depends(get_service(UserService))
    ):
        """Get a user by ID."""
        user = await user_service.get_user(user_id)
        if user is None:
            return {"error": "User not found"}, 404
        return user
    
    @router.post("/users")
    async def create_user(
        user: dict,
        user_service: UserService = Depends(get_service(UserService))
    ):
        """Create a new user."""
        return await user_service.create_user(user)
    
    @router.put("/users/{user_id}")
    async def update_user(
        user_id: int,
        user: dict,
        user_service: UserService = Depends(get_service(UserService))
    ):
        """Update a user."""
        updated_user = await user_service.update_user(user_id, user)
        if updated_user is None:
            return {"error": "User not found"}, 404
        return updated_user
    
    @router.delete("/users/{user_id}")
    async def delete_user(
        user_id: int,
        user_service: UserService = Depends(get_service(UserService))
    ):
        """Delete a user."""
        result = await user_service.delete_user(user_id)
        if not result:
            return {"error": "User not found"}, 404
        return {"message": "User deleted"}
    
    # Alternative route using FromDI
    @router.get("/users2")
    async def get_users_alternative(
        scoped_deps: ScopedDeps = Depends(),
        user_service: UserService = Depends(FromDI(UserService))
    ):
        """Get all users using FromDI."""
        with scoped_deps:
            return await user_service.get_all_users()
    
    # Add router to app
    app.include_router(router)
    
    return app


# Entry point
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)