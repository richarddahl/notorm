"""
Domain repositories for the Security module.

This module defines repository interfaces and implementations for the Security module.
"""

from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, AsyncIterator
from dataclasses import dataclass

from uno.core.result import Result
from uno.domain.repository import DomainRepository, AsyncDomainRepository

from uno.security.entities import (
    SecurityEvent, 
    EncryptionKey, 
    EncryptionKeyId,
    JWTToken, 
    TokenId,
    MFACredential,
    EventSeverity,
    TokenType
)


@runtime_checkable
class SecurityEventRepositoryProtocol(Protocol):
    """Protocol for security event repository."""
    
    async def create(self, event: SecurityEvent) -> Result[SecurityEvent]:
        """
        Create a new security event.
        
        Args:
            event: Security event to create
            
        Returns:
            Result containing the created event or an error
        """
        ...
    
    async def get_by_id(self, event_id: str) -> Result[SecurityEvent]:
        """
        Get a security event by ID.
        
        Args:
            event_id: ID of the event to retrieve
            
        Returns:
            Result containing the event or an error if not found
        """
        ...
    
    async def get_events_by_user(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[SecurityEvent]]:
        """
        Get security events for a specific user.
        
        Args:
            user_id: User ID
            page: Page number (1-based)
            page_size: Number of events per page
            
        Returns:
            Result containing a list of events or an error
        """
        ...
    
    async def get_events_by_type(
        self, 
        event_type: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[SecurityEvent]]:
        """
        Get security events of a specific type.
        
        Args:
            event_type: Event type
            page: Page number (1-based)
            page_size: Number of events per page
            
        Returns:
            Result containing a list of events or an error
        """
        ...
    
    async def get_events_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[SecurityEvent]]:
        """
        Get security events within a specific time range.
        
        Args:
            start_time: Start time
            end_time: End time
            page: Page number (1-based)
            page_size: Number of events per page
            
        Returns:
            Result containing a list of events or an error
        """
        ...
    
    async def get_events_by_severity(
        self, 
        severity: EventSeverity, 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[SecurityEvent]]:
        """
        Get security events with a specific severity.
        
        Args:
            severity: Event severity
            page: Page number (1-based)
            page_size: Number of events per page
            
        Returns:
            Result containing a list of events or an error
        """
        ...
    
    async def search_events(
        self, 
        query: Dict[str, Any], 
        page: int = 1, 
        page_size: int = 20
    ) -> Result[List[SecurityEvent]]:
        """
        Search for security events matching a query.
        
        Args:
            query: Search query
            page: Page number (1-based)
            page_size: Number of events per page
            
        Returns:
            Result containing a list of events or an error
        """
        ...
    
    async def delete_events_older_than(self, cutoff_time: datetime) -> Result[int]:
        """
        Delete security events older than a specific time.
        
        Args:
            cutoff_time: Cutoff time for deletion
            
        Returns:
            Result containing the number of deleted events or an error
        """
        ...


@runtime_checkable
class EncryptionKeyRepositoryProtocol(Protocol):
    """Protocol for encryption key repository."""
    
    async def create(self, key: EncryptionKey) -> Result[EncryptionKey]:
        """
        Create a new encryption key.
        
        Args:
            key: Encryption key to create
            
        Returns:
            Result containing the created key or an error
        """
        ...
    
    async def get_by_id(self, key_id: EncryptionKeyId) -> Result[EncryptionKey]:
        """
        Get an encryption key by ID.
        
        Args:
            key_id: ID of the key to retrieve
            
        Returns:
            Result containing the key or an error if not found
        """
        ...
    
    async def get_active_key(self, algorithm: Optional[str] = None) -> Result[EncryptionKey]:
        """
        Get the currently active encryption key.
        
        Args:
            algorithm: Optional algorithm filter
            
        Returns:
            Result containing the active key or an error if not found
        """
        ...
    
    async def update(self, key: EncryptionKey) -> Result[EncryptionKey]:
        """
        Update an encryption key.
        
        Args:
            key: Encryption key to update
            
        Returns:
            Result containing the updated key or an error
        """
        ...
    
    async def get_keys_by_algorithm(self, algorithm: str) -> Result[List[EncryptionKey]]:
        """
        Get encryption keys for a specific algorithm.
        
        Args:
            algorithm: Algorithm to filter by
            
        Returns:
            Result containing a list of keys or an error
        """
        ...
    
    async def get_all_active_keys(self) -> Result[List[EncryptionKey]]:
        """
        Get all active encryption keys.
        
        Returns:
            Result containing a list of keys or an error
        """
        ...
    
    async def mark_key_as_rotated(self, key_id: EncryptionKeyId) -> Result[EncryptionKey]:
        """
        Mark an encryption key as rotated.
        
        Args:
            key_id: ID of the key to rotate
            
        Returns:
            Result containing the updated key or an error
        """
        ...
    
    async def delete_expired_keys(self) -> Result[int]:
        """
        Delete expired encryption keys.
        
        Returns:
            Result containing the number of deleted keys or an error
        """
        ...


@runtime_checkable
class JWTTokenRepositoryProtocol(Protocol):
    """Protocol for JWT token repository."""
    
    async def create(self, token: JWTToken) -> Result[JWTToken]:
        """
        Create a new JWT token.
        
        Args:
            token: JWT token to create
            
        Returns:
            Result containing the created token or an error
        """
        ...
    
    async def get_by_id(self, token_id: TokenId) -> Result[JWTToken]:
        """
        Get a JWT token by ID.
        
        Args:
            token_id: ID of the token to retrieve
            
        Returns:
            Result containing the token or an error if not found
        """
        ...
    
    async def get_tokens_by_user(
        self, 
        user_id: str, 
        token_type: Optional[TokenType] = None
    ) -> Result[List[JWTToken]]:
        """
        Get JWT tokens for a specific user.
        
        Args:
            user_id: User ID
            token_type: Optional token type filter
            
        Returns:
            Result containing a list of tokens or an error
        """
        ...
    
    async def update(self, token: JWTToken) -> Result[JWTToken]:
        """
        Update a JWT token.
        
        Args:
            token: JWT token to update
            
        Returns:
            Result containing the updated token or an error
        """
        ...
    
    async def revoke_token(self, token_id: TokenId, reason: Optional[str] = None) -> Result[JWTToken]:
        """
        Revoke a JWT token.
        
        Args:
            token_id: ID of the token to revoke
            reason: Optional reason for revocation
            
        Returns:
            Result containing the revoked token or an error
        """
        ...
    
    async def revoke_all_user_tokens(
        self, 
        user_id: str, 
        reason: Optional[str] = None
    ) -> Result[int]:
        """
        Revoke all tokens for a specific user.
        
        Args:
            user_id: User ID
            reason: Optional reason for revocation
            
        Returns:
            Result containing the number of revoked tokens or an error
        """
        ...
    
    async def delete_expired_tokens(self) -> Result[int]:
        """
        Delete expired JWT tokens.
        
        Returns:
            Result containing the number of deleted tokens or an error
        """
        ...
    
    async def is_token_valid(self, token_id: TokenId) -> Result[bool]:
        """
        Check if a JWT token is valid.
        
        Args:
            token_id: ID of the token to check
            
        Returns:
            Result containing a boolean indicating validity or an error
        """
        ...


@runtime_checkable
class MFACredentialRepositoryProtocol(Protocol):
    """Protocol for MFA credential repository."""
    
    async def create(self, credential: MFACredential) -> Result[MFACredential]:
        """
        Create new MFA credentials.
        
        Args:
            credential: MFA credential to create
            
        Returns:
            Result containing the created credential or an error
        """
        ...
    
    async def get_by_id(self, credential_id: str) -> Result[MFACredential]:
        """
        Get MFA credentials by ID.
        
        Args:
            credential_id: ID of the credential to retrieve
            
        Returns:
            Result containing the credential or an error if not found
        """
        ...
    
    async def get_by_user_id(self, user_id: str) -> Result[MFACredential]:
        """
        Get MFA credentials for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing the credential or an error if not found
        """
        ...
    
    async def update(self, credential: MFACredential) -> Result[MFACredential]:
        """
        Update MFA credentials.
        
        Args:
            credential: MFA credential to update
            
        Returns:
            Result containing the updated credential or an error
        """
        ...
    
    async def delete(self, credential_id: str) -> Result[bool]:
        """
        Delete MFA credentials.
        
        Args:
            credential_id: ID of the credential to delete
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def deactivate_by_user_id(self, user_id: str) -> Result[bool]:
        """
        Deactivate MFA credentials for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...


class SecurityEventRepository(AsyncDomainRepository, SecurityEventRepositoryProtocol):
    """Implementation of security event repository."""
    
    async def create(self, event: SecurityEvent) -> Result[SecurityEvent]:
        """
        Create a new security event.
        
        Args:
            event: Security event to create
            
        Returns:
            Result containing the created event or an error
        """
        try:
            # Convert to dictionary for database insertion
            event_dict = event.to_dict()
            
            # Store in database
            query = """
                INSERT INTO security_events (
                    id, event_type, user_id, timestamp, 
                    ip_address, user_agent, success, message, 
                    details, context, severity
                ) VALUES (
                    :id, :event_type, :user_id, :timestamp, 
                    :ip_address, :user_agent, :success, :message, 
                    :details, :context, :severity
                )
                RETURNING *
            """
            
            result = await self.db.query_one(query, event_dict)
            
            # Create new event from result
            return Result.success(event)
        except Exception as e:
            return Result.failure(f"Failed to create security event: {str(e)}")
    
    async def get_by_id(self, event_id: str) -> Result[SecurityEvent]:
        """
        Get a security event by ID.
        
        Args:
            event_id: ID of the event to retrieve
            
        Returns:
            Result containing the event or an error if not found
        """
        try:
            query = "SELECT * FROM security_events WHERE id = :id"
            result = await self.db.query_one(query, {"id": event_id})
            
            if not result:
                return Result.failure(f"Security event with ID {event_id} not found")
            
            # Convert result to SecurityEvent
            event = SecurityEvent(
                id=result["id"],
                event_type=result["event_type"],
                user_id=result["user_id"],
                timestamp=result["timestamp"],
                ip_address=result["ip_address"],
                user_agent=result["user_agent"],
                success=result["success"],
                message=result["message"],
                details=result["details"],
                context=result["context"],
                severity=EventSeverity(result["severity"])
            )
            
            return Result.success(event)
        except Exception as e:
            return Result.failure(f"Failed to get security event: {str(e)}")
    
    # Implement other methods as defined in the protocol...
    
    
class EncryptionKeyRepository(AsyncDomainRepository, EncryptionKeyRepositoryProtocol):
    """Implementation of encryption key repository."""
    
    # Implement methods as defined in the protocol...
    
    
class JWTTokenRepository(AsyncDomainRepository, JWTTokenRepositoryProtocol):
    """Implementation of JWT token repository."""
    
    # Implement methods as defined in the protocol...
    
    
class MFACredentialRepository(AsyncDomainRepository, MFACredentialRepositoryProtocol):
    """Implementation of MFA credential repository."""
    
    # Implement methods as defined in the protocol...