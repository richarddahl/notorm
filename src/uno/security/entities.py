"""
Domain entities for the Security module.

This module defines the core domain entities for the Security module,
including security events, encryption keys, and security configurations.
"""

from datetime import datetime, timedelta, UTC
import uuid
import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union, Set

from uno.domain.core import Entity, AggregateRoot, ValueObject

# Enums
class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms."""
    AES_GCM = "aes-gcm"
    AES_CBC = "aes-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    RSA = "rsa"
    NONE = "none"

class KeyManagementType(str, Enum):
    """Key management types for encryption."""
    LOCAL = "local"
    VAULT = "vault"
    AWS_KMS = "aws-kms"
    AZURE_KEY_VAULT = "azure-key-vault"
    GCP_KMS = "gcp-kms"

class MFAType(str, Enum):
    """Multi-factor authentication types."""
    NONE = "none"
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    HARDWARE = "hardware"
    PUSH = "push"

class TokenType(str, Enum):
    """Type of JWT token."""
    ACCESS = "access"
    REFRESH = "refresh"

class EventSeverity(str, Enum):
    """Security event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# Value Objects
@dataclass(frozen=True)
class EncryptionKeyId(ValueObject):
    """Identifier for an encryption key."""
    value: str

@dataclass(frozen=True)
class TokenId(ValueObject):
    """Identifier for a token."""
    value: str

# Entities
@dataclass
class SecurityEvent(Entity):
    """A security event in the system."""
    id: str
    event_type: str
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    message: Optional[str] = None
    details: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    severity: EventSeverity = EventSeverity.INFO
    
    @classmethod
    def create_login_event(
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
        severity = EventSeverity.INFO if success else EventSeverity.WARNING
        message = message or (
            f"Successful login for user {user_id}" if success
            else f"Failed login attempt for user {user_id}"
        )
        
        return cls(
            id=str(uuid.uuid4()),
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
    def create_logout_event(
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
            id=str(uuid.uuid4()),
            event_type="logout",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            message=f"Logout for user {user_id}",
            context=context
        )
    
    @classmethod
    def create_access_denied_event(
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
            id=str(uuid.uuid4()),
            event_type="access_denied",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            message=message,
            severity=EventSeverity.WARNING,
            context={"resource": resource, "action": action, **context}
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.
        
        Returns:
            Dictionary representation of the event
        """
        result = {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "message": self.message,
            "details": self.details,
            "context": self.context,
            "severity": self.severity.value if self.severity else None
        }
        
        # Convert details to string if it's not already a string
        if self.details and not isinstance(self.details, str):
            result["details"] = json.dumps(self.details)
        
        return result

@dataclass
class EncryptionKey(Entity):
    """An encryption key used for securing data."""
    id: EncryptionKeyId
    algorithm: EncryptionAlgorithm
    key_data: str  # Typically encoded as base64
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None
    key_version: int = 1
    purpose: str = "encryption"  # e.g., "encryption", "signing", "master"
    associated_data: Dict[str, Any] = field(default_factory=dict)
    
    def mark_as_rotated(self) -> None:
        """Mark this key as rotated (no longer active)."""
        self.is_active = False
    
    def is_expired(self) -> bool:
        """Check if the key is expired."""
        if not self.expires_at:
            return False
        
        return datetime.now(UTC) >= self.expires_at
    
    def set_expiration(self, days: int) -> None:
        """
        Set the expiration date for this key.
        
        Args:
            days: Number of days until expiration
        """
        self.expires_at = datetime.now(UTC) + timedelta(days=days)

@dataclass
class JWTToken(Entity):
    """A JWT token for authentication."""
    id: TokenId
    user_id: str
    token_type: TokenType
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    revoked: bool = False
    revoked_reason: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    tenant_id: Optional[str] = None
    claims: Dict[str, Any] = field(default_factory=dict)
    
    def revoke(self, reason: Optional[str] = None) -> None:
        """
        Revoke this token.
        
        Args:
            reason: Reason for revocation
        """
        self.revoked = True
        self.revoked_reason = reason
    
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.now(UTC) >= self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not revoked)."""
        return not self.revoked and not self.is_expired()

@dataclass
class MFACredential(Entity):
    """Multi-factor authentication credentials."""
    id: str
    user_id: str
    type: MFAType
    secret_key: str  # Encrypted secret key
    backup_codes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used_at: Optional[datetime] = None
    is_active: bool = True
    verification_attempts: int = 0
    
    def use_backup_code(self, code: str) -> bool:
        """
        Use a backup code for authentication.
        
        Args:
            code: Backup code to use
            
        Returns:
            True if the code was valid, False otherwise
        """
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.last_used_at = datetime.now(UTC)
            return True
        
        return False
    
    def record_verification_attempt(self, success: bool) -> None:
        """
        Record a verification attempt.
        
        Args:
            success: Whether the verification was successful
        """
        if success:
            self.verification_attempts = 0
            self.last_used_at = datetime.now(UTC)
        else:
            self.verification_attempts += 1
    
    def deactivate(self) -> None:
        """Deactivate these credentials."""
        self.is_active = False