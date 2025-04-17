"""
User repository implementation for SQLAlchemy.
"""

from typing import List, Optional, Callable, Dict, Any, Type, cast
from datetime import datetime, timezone
import logging

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.repository_results import FindResult
from uno.domain.specifications import AttributeSpecification, AndSpecification, OrSpecification
from uno.domain.repositories.sqlalchemy.base import SQLAlchemyRepository
from uno.domain.models import User, UserRole
from uno.model import UnoModel


class UserModel(UnoModel):
    """SQLAlchemy model for users."""
    
    __tablename__ = "users"
    
    id = UnoModel.Column(UnoModel.String, primary_key=True)
    username = UnoModel.Column(UnoModel.String, unique=True, nullable=False)
    email = UnoModel.Column(UnoModel.String, unique=True, nullable=False)
    password_hash = UnoModel.Column(UnoModel.String, nullable=False)
    full_name = UnoModel.Column(UnoModel.String, nullable=True)
    role = UnoModel.Column(UnoModel.String, nullable=False, default="user")
    is_active = UnoModel.Column(UnoModel.Boolean, nullable=False, default=True)
    created_at = UnoModel.Column(UnoModel.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = UnoModel.Column(UnoModel.DateTime(timezone=True), nullable=True)


class UserRepository(SQLAlchemyRepository[User, UserModel]):
    """Repository for User entities."""
    
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the user repository.
        
        Args:
            session_factory: Factory function for creating SQLAlchemy sessions
            logger: Optional logger for diagnostic output
        """
        super().__init__(
            entity_type=User,
            model_class=UserModel,
            session_factory=session_factory,
            logger=logger or logging.getLogger(__name__)
        )
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """
        Find a user by username.
        
        Args:
            username: The username to search for
            
        Returns:
            The user if found, None otherwise
        """
        spec = AttributeSpecification("username", username)
        return await self.find_one(spec)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email.
        
        Args:
            email: The email to search for
            
        Returns:
            The user if found, None otherwise
        """
        spec = AttributeSpecification("email", email)
        return await self.find_one(spec)
    
    async def find_by_username_or_email(self, value: str) -> Optional[User]:
        """
        Find a user by username or email.
        
        Args:
            value: The username or email to search for
            
        Returns:
            The user if found, None otherwise
        """
        spec = OrSpecification(
            AttributeSpecification("username", value),
            AttributeSpecification("email", value)
        )
        return await self.find_one(spec)
    
    async def find_active(self) -> List[User]:
        """
        Find all active users.
        
        Returns:
            List of active users
        """
        spec = AttributeSpecification("is_active", True)
        return await self.find(spec)
    
    async def find_by_role(self, role: UserRole) -> List[User]:
        """
        Find users by role.
        
        Args:
            role: The role to search for
            
        Returns:
            List of users with the specified role
        """
        spec = AttributeSpecification("role", role.value)
        return await self.find(spec)
    
    async def find_active_by_role(self, role: UserRole) -> List[User]:
        """
        Find active users by role.
        
        Args:
            role: The role to search for
            
        Returns:
            List of active users with the specified role
        """
        spec = AndSpecification(
            AttributeSpecification("is_active", True),
            AttributeSpecification("role", role.value)
        )
        return await self.find(spec)
    
    async def deactivate(self, user: User) -> None:
        """
        Deactivate a user.
        
        Args:
            user: The user to deactivate
        """
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await self.update(user)
    
    async def activate(self, user: User) -> None:
        """
        Activate a user.
        
        Args:
            user: The user to activate
        """
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        await self.update(user)
    
    async def change_role(self, user: User, role: UserRole) -> None:
        """
        Change a user's role.
        
        Args:
            user: The user to update
            role: The new role
        """
        user.role = role
        user.updated_at = datetime.now(timezone.utc)
        await self.update(user)