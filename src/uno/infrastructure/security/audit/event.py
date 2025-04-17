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
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union


@dataclass
class SecurityEvent:
    """
    Security event for audit logging.
    
    This class represents a security event that can be logged and analyzed.
    """
    
    event_type: str
    user_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    message: Optional[str] = None
    details: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"
    
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
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        message: Optional[str] = None,
        **context
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
            f"Successful login for user {user_id}" if success
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
            context=context
        )
    
    @classmethod
    def logout(
        cls,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **context
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
            message=f"Logout for user {user_id}",
            context=context
        )
    
    @classmethod
    def password_change(
        cls,
        user_id: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **context
    ) -> "SecurityEvent":
        """
        Create a password change event.
        
        Args:
            user_id: User ID
            success: Whether the password change was successful
            ip_address: IP address of the client
            user_agent: User agent of the client
            **context: Additional context
            
        Returns:
            SecurityEvent instance
        """
        message = (
            f"Password changed for user {user_id}" if success
            else f"Failed password change attempt for user {user_id}"
        )
        
        return cls(
            event_type="password_change",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            message=message,
            context=context
        )
    
    @classmethod
    def access_denied(
        cls,
        user_id: Optional[str],
        resource: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **context
    ) -> "SecurityEvent":
        """
        Create an access denied event.
        
        Args:
            user_id: User ID (if authenticated)
            resource: Resource being accessed
            action: Action being attempted
            ip_address: IP address of the client
            user_agent: User agent of the client
            **context: Additional context
            
        Returns:
            SecurityEvent instance
        """
        user_info = f"user {user_id}" if user_id else "unauthenticated user"
        message = f"Access denied for {user_info}: {action} on {resource}"
        
        return cls(
            event_type="access_denied",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            message=message,
            severity="warning",
            context={"resource": resource, "action": action, **context}
        )
    
    @classmethod
    def admin_action(
        cls,
        user_id: str,
        action: str,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Any] = None,
        **context
    ) -> "SecurityEvent":
        """
        Create an admin action event.
        
        Args:
            user_id: User ID of the administrator
            action: Action being performed
            target_id: ID of the target resource (if applicable)
            target_type: Type of the target resource (if applicable)
            ip_address: IP address of the client
            user_agent: User agent of the client
            details: Additional details about the action
            **context: Additional context
            
        Returns:
            SecurityEvent instance
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
                **context
            }
        )