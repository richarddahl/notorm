"""
User domain models.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

from pydantic import Field, field_validator

from uno.domain.core import AggregateRoot
from uno.domain.value_objects import Email, Address


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    MANAGER = "manager"
    CUSTOMER = "customer"
    GUEST = "guest"


class User(AggregateRoot):
    """
    User aggregate root in the domain model.

    This represents a user in the system, with personal information, authentication,
    and role data.
    """

    username: str = Field(..., min_length=3, max_length=50)
    email: Email
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.CUSTOMER)
    is_active: bool = Field(default=True)
    addresses: List[Address] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    last_login: Optional[datetime] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username."""
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    def change_email(self, new_email: Email) -> None:
        """
        Change the user's email.

        Args:
            new_email: The new email
        """
        old_email = self.email
        self.email = new_email
        self.updated_at = datetime.now(timezone.utc)
        self.add_event(
            UserEmailChangedEvent(
                user_id=str(self.id),
                old_email=str(old_email.value) if old_email else None,
                new_email=str(new_email.value),
            )
        )

    def change_role(self, role: UserRole) -> None:
        """
        Change the user's role.

        Args:
            role: The new role
        """
        old_role = self.role
        self.role = role
        self.updated_at = datetime.now(timezone.utc)
        self.add_event(
            UserRoleChangedEvent(user_id=str(self.id), old_role=old_role, new_role=role)
        )

    def add_address(self, address: Address) -> None:
        """
        Add an address to the user.

        Args:
            address: The address to add
        """
        self.addresses.append(address)
        self.updated_at = datetime.now(timezone.utc)

    def remove_address(self, index: int) -> None:
        """
        Remove an address from the user.

        Args:
            index: The index of the address to remove
        """
        if 0 <= index < len(self.addresses):
            del self.addresses[index]
            self.updated_at = datetime.now(timezone.utc)

    def set_preference(self, key: str, value: Any) -> None:
        """
        Set a user preference.

        Args:
            key: The preference key
            value: The preference value
        """
        self.preferences[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def record_login(self) -> None:
        """Record a user login."""
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = self.last_login

    def activate(self) -> None:
        """Activate the user."""
        if not self.is_active:
            self.is_active = True
            self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate the user."""
        if self.is_active:
            self.is_active = False
            self.updated_at = datetime.now(timezone.utc)

    def get_full_name(self) -> str:
        """
        Get the user's full name.

        Returns:
            The full name, or username if no name is set
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    def check_invariants(self) -> None:
        """Check that user invariants are maintained."""
        if not self.username:
            raise ValueError("Username is required")

        # Additional business rules can be added here


# Domain Events
from uno.core.events.event import Event


class UserEmailChangedEvent(Event):
    """Event fired when a user's email is changed."""

    user_id: str
    old_email: Optional[str]
    new_email: str


class UserRoleChangedEvent(Event):
    """Event fired when a user's role is changed."""

    user_id: str
    old_role: UserRole
    new_role: UserRole
