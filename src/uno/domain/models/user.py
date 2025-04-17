"""
User domain models.
"""

from typing import Optional
from datetime import datetime, timezone
from enum import Enum, auto

from pydantic import EmailStr, Field, field_validator

from uno.domain.models.base import Entity


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"


class User(Entity):
    """
    User entity in the domain model.
    
    This represents a user in the system, with authentication and authorization data.
    """
    
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password_hash: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        # Simple validation - a more comprehensive validator would use EmailStr
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()  # Normalize email to lowercase
    
    def set_role(self, role: UserRole) -> None:
        """
        Set the user's role.
        
        Args:
            role: The new role
        """
        self.role = role
        self.updated_at = datetime.now(timezone.utc)
    
    def activate(self) -> None:
        """Activate the user."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Deactivate the user."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def has_role(self, role: UserRole) -> bool:
        """
        Check if the user has a specific role.
        
        Args:
            role: The role to check
            
        Returns:
            True if the user has the role, False otherwise
        """
        return self.role == role
    
    def is_admin(self) -> bool:
        """
        Check if the user is an admin.
        
        Returns:
            True if the user is an admin, False otherwise
        """
        return self.role == UserRole.ADMIN