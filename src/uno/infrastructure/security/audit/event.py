# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Security events for Uno applications.

This module defines security events for audit logging.
"""

import time
import uuid
import json
from typing import Optional, Any, Dict
from uno.core.events.event import Event as BaseEvent
from dataclasses import asdict


class SecurityEvent(BaseEvent):
    """
    Security event for audit logging, inheriting from the canonical Event class.
    Propagates all canonical event metadata fields and adds security-specific fields.
    """

    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    success: bool = True
    message: str | None = None
    details: str | None = None
    severity: str = "info"

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "user_id": self.user_id,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "success": self.success,
                "message": self.message,
                "details": self.details,
                "severity": self.severity,
            }
        )
        return base

    def to_json(self) -> str:
        return super().to_json()

    def __post_init__(self) -> None:
        """Post-initialization validation."""
        # Ensure timestamp is a float
        if isinstance(self.timestamp, int):
            self.timestamp = float(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        event_dict = asdict(self)

        # Convert details to string if it's not already a string
        if self.details and not isinstance(self.details, str):
            event_dict["details"] = json.dumps(self.details)

        return event_dict

    def to_json(self) -> str:
        """
        Convert the event to a JSON string.

        Returns:
            JSON string representation of the event
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityEvent":
        """
        Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            SecurityEvent instance
        """
        # Convert details from JSON string if necessary
        if "details" in data and isinstance(data["details"], str):
            try:
                data["details"] = json.loads(data["details"])
            except json.JSONDecodeError:
                pass

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "SecurityEvent":
        """
        Create an event from a JSON string.

        Args:
            json_str: JSON string representation of the event

        Returns:
            SecurityEvent instance
        """
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def login(
        cls,
        user_id: str,
        success: bool = True,
        ip_address: str | None = None,
        user_agent: str | None = None,
        message: str | None = None,
        **context,
    ) -> "SecurityEvent":
        """
        Create a login event.

        Args:
            user_id: User ID
            success: Whether the login was successful
            ip_address: IP address of the client
            user_agent: User agent of the client
            message: Optional message
            **context: Additional context

        Returns:
            SecurityEvent instance
        """
        event_type = "login" if success else "failed_login"
        severity = "info" if success else "warning"
        message = message or (
            f"Successful login for user {user_id}"
            if success
            else f"Failed login attempt for user {user_id}"
        )

        return cls(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            message=message,
            severity=severity,
            context=context,
        )

    @classmethod
    def logout(
        cls,
        user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        **context,
    ) -> "SecurityEvent":
        """
        Create a logout event.

        Args:
            user_id: User ID
            ip_address: IP address of the client
            user_agent: User agent of the client
            **context: Additional context

        Returns:
            SecurityEvent instance
        """
        return cls(
            event_type="logout",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            message=f"Logout for user {user_id}",
            severity="info",
        )

    @classmethod
    def password_change(
        cls,
        user_id: str,
        success: bool = True,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "SecurityEvent":
        """
        Create a password change event with canonical event metadata fields.
        """
        msg = (
            f"Password changed for user {user_id}"
            if success
            else f"Failed password change attempt for user {user_id}"
        )
        return cls(
            event_type="security.password_change",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            message=msg,
            severity="info" if success else "warning",
        )

    @classmethod
    def access_denied(
        cls,
        user_id: str | None,
        resource: str,
        action: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "SecurityEvent":
        """
        Create an access denied event with canonical event metadata fields.
        """
        user_info = f"user {user_id}" if user_id else "unauthenticated user"
        msg = f"Access denied for {user_info}: {action} on {resource}"
        return cls(
            event_type="security.access_denied",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            message=msg,
            severity="warning",
            details=f"action={action}, resource={resource}",
        )

    @classmethod
    def admin_action(
        cls,
        user_id: str,
        action: str,
        target_id: str | None = None,
        target_type: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: str | None = None,
    ) -> "SecurityEvent":
        """
        Create an admin action event with canonical event metadata fields.
        """
        target_info = ""
        if target_type and target_id:
            target_info = f" on {target_type} {target_id}"
        elif target_type:
            target_info = f" on {target_type}"
        elif target_id:
            target_info = f" on {target_id}"

        message = f"Admin action by {user_id}: {action}{target_info}"

        return cls(
            event_type="admin_action",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            message=message,
            details=details,
            severity="info",
            context={
                "action": action,
                "target_id": target_id,
                "target_type": target_type,
                **context,
            },
        )
