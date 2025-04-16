"""
Domain services for the Security module.

This module defines the core domain services for the Security module,
providing high-level security operations built on domain entities.
"""

import hashlib
import uuid
import os
import base64
import secrets
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any, Union, Protocol, runtime_checkable, Tuple

import jwt
import pyotp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from uno.core.result import Result
from uno.domain.service import DomainService
from uno.security.entities import (
    SecurityEvent,
    EncryptionKey,
    EncryptionKeyId,
    JWTToken,
    TokenId,
    MFACredential,
    TokenType,
    MFAType,
    EncryptionAlgorithm,
    EventSeverity
)
from uno.security.domain_repositories import (
    SecurityEventRepositoryProtocol,
    EncryptionKeyRepositoryProtocol,
    JWTTokenRepositoryProtocol,
    MFACredentialRepositoryProtocol
)
from uno.security.config import SecurityConfig


@runtime_checkable
class AuditServiceProtocol(Protocol):
    """Protocol for security audit service."""
    
    async def log_event(self, event: SecurityEvent) -> Result[SecurityEvent]:
        """
        Log a security event.
        
        Args:
            event: Security event to log
            
        Returns:
            Result containing the logged event or an error
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
    
    async def cleanup_old_events(self, retention_days: int) -> Result[int]:
        """
        Clean up old security events.
        
        Args:
            retention_days: Number of days to retain events
            
        Returns:
            Result containing the number of deleted events or an error
        """
        ...


@runtime_checkable
class EncryptionServiceProtocol(Protocol):
    """Protocol for encryption service."""
    
    async def encrypt(
        self, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Result[str]:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            context: Encryption context
            
        Returns:
            Result containing the encrypted data or an error
        """
        ...
    
    async def decrypt(
        self, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Result[str]:
        """
        Decrypt data.
        
        Args:
            data: Data to decrypt
            context: Encryption context
            
        Returns:
            Result containing the decrypted data or an error
        """
        ...
    
    async def encrypt_field(
        self, 
        field_name: str, 
        value: str, 
        entity_type: Optional[str] = None
    ) -> Result[str]:
        """
        Encrypt a field value.
        
        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type
            
        Returns:
            Result containing the encrypted field value or an error
        """
        ...
    
    async def decrypt_field(
        self, 
        field_name: str, 
        value: str, 
        entity_type: Optional[str] = None
    ) -> Result[str]:
        """
        Decrypt a field value.
        
        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type
            
        Returns:
            Result containing the decrypted field value or an error
        """
        ...
    
    async def rotate_keys(self) -> Result[EncryptionKey]:
        """
        Rotate encryption keys.
        
        Returns:
            Result containing the new key or an error
        """
        ...
    
    async def get_active_key(self) -> Result[EncryptionKey]:
        """
        Get the currently active encryption key.
        
        Returns:
            Result containing the active key or an error
        """
        ...


@runtime_checkable
class AuthenticationServiceProtocol(Protocol):
    """Protocol for authentication service."""
    
    async def hash_password(self, password: str) -> Result[str]:
        """
        Hash a password.
        
        Args:
            password: Password to hash
            
        Returns:
            Result containing the hashed password or an error
        """
        ...
    
    async def verify_password(self, password: str, hashed_password: str) -> Result[bool]:
        """
        Verify a password.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password
            
        Returns:
            Result containing a boolean indicating validity or an error
        """
        ...
    
    async def validate_password_policy(self, password: str) -> Result[Dict[str, Any]]:
        """
        Validate a password against the password policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Result containing validation results or an error
        """
        ...
    
    async def generate_token(
        self, 
        user_id: str, 
        token_type: TokenType, 
        roles: List[str] = None, 
        tenant_id: Optional[str] = None, 
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> Result[Tuple[str, JWTToken]]:
        """
        Generate a new JWT token.
        
        Args:
            user_id: User ID
            token_type: Token type
            roles: User roles
            tenant_id: Tenant ID
            custom_claims: Custom claims
            
        Returns:
            Result containing the token string and token entity or an error
        """
        ...
    
    async def validate_token(self, token: str) -> Result[Dict[str, Any]]:
        """
        Validate a JWT token.
        
        Args:
            token: Token to validate
            
        Returns:
            Result containing the token claims or an error
        """
        ...
    
    async def revoke_token(
        self, 
        token_id: TokenId, 
        reason: Optional[str] = None
    ) -> Result[bool]:
        """
        Revoke a JWT token.
        
        Args:
            token_id: ID of the token to revoke
            reason: Optional reason for revocation
            
        Returns:
            Result containing a boolean indicating success or an error
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


@runtime_checkable
class MFAServiceProtocol(Protocol):
    """Protocol for MFA service."""
    
    async def setup_mfa(
        self, 
        user_id: str, 
        mfa_type: MFAType = MFAType.TOTP
    ) -> Result[Dict[str, Any]]:
        """
        Set up multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            mfa_type: MFA type
            
        Returns:
            Result containing setup information or an error
        """
        ...
    
    async def verify_mfa(
        self, 
        user_id: str, 
        code: str, 
        mfa_type: Optional[MFAType] = None
    ) -> Result[bool]:
        """
        Verify a multi-factor authentication code.
        
        Args:
            user_id: User ID
            code: MFA code
            mfa_type: MFA type
            
        Returns:
            Result containing a boolean indicating validity or an error
        """
        ...
    
    async def verify_backup_code(self, user_id: str, code: str) -> Result[bool]:
        """
        Verify a backup code.
        
        Args:
            user_id: User ID
            code: Backup code
            
        Returns:
            Result containing a boolean indicating validity or an error
        """
        ...
    
    async def deactivate_mfa(self, user_id: str) -> Result[bool]:
        """
        Deactivate multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def regenerate_backup_codes(self, user_id: str) -> Result[List[str]]:
        """
        Regenerate backup codes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing the new backup codes or an error
        """
        ...


class AuditService(DomainService, AuditServiceProtocol):
    """Service for security audit logging."""
    
    def __init__(
        self, 
        repository: SecurityEventRepositoryProtocol,
        config: SecurityConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the audit service.
        
        Args:
            repository: Security event repository
            config: Security configuration
            logger: Logger
        """
        self.repository = repository
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.audit")
    
    async def log_event(self, event: SecurityEvent) -> Result[SecurityEvent]:
        """
        Log a security event.
        
        Args:
            event: Security event to log
            
        Returns:
            Result containing the logged event or an error
        """
        try:
            # Check if this event type should be logged
            if (not self.config.auditing.enabled or 
                event.event_type not in self.config.auditing.include_events):
                # Event should not be logged based on configuration
                return Result.success(event)
            
            # Log the event
            result = await self.repository.create(event)
            
            if result.is_success():
                self.logger.info(f"Security event logged: {event.event_type} for user {event.user_id}")
            else:
                self.logger.error(f"Failed to log security event: {result.error}")
            
            return result
        except Exception as e:
            self.logger.error(f"Error logging security event: {str(e)}")
            return Result.failure(f"Failed to log security event: {str(e)}")
    
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
        return await self.repository.get_events_by_user(user_id, page, page_size)
    
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
        return await self.repository.get_events_by_type(event_type, page, page_size)
    
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
        return await self.repository.search_events(query, page, page_size)
    
    async def cleanup_old_events(self, retention_days: int = None) -> Result[int]:
        """
        Clean up old security events.
        
        Args:
            retention_days: Number of days to retain events
            
        Returns:
            Result containing the number of deleted events or an error
        """
        # Use configured retention days if not specified
        if retention_days is None:
            retention_days = self.config.auditing.retention_days
        
        # Calculate cutoff time
        cutoff_time = datetime.now(UTC) - timedelta(days=retention_days)
        
        # Delete old events
        return await self.repository.delete_events_older_than(cutoff_time)


class EncryptionService(DomainService, EncryptionServiceProtocol):
    """Service for encryption operations."""
    
    def __init__(
        self, 
        repository: EncryptionKeyRepositoryProtocol,
        config: SecurityConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the encryption service.
        
        Args:
            repository: Encryption key repository
            config: Security configuration
            logger: Logger
        """
        self.repository = repository
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.encryption")
    
    async def encrypt(
        self, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Result[str]:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            context: Encryption context
            
        Returns:
            Result containing the encrypted data or an error
        """
        try:
            # Get active key
            key_result = await self.repository.get_active_key()
            if key_result.is_failure():
                return Result.failure(f"Failed to encrypt data: {key_result.error}")
            
            key = key_result.value
            
            # Perform encryption based on algorithm
            if key.algorithm == EncryptionAlgorithm.AES_GCM:
                # Example implementation (would use a proper crypto library in real code)
                key_data = base64.b64decode(key.key_data)
                f = Fernet(key_data)
                encrypted = f.encrypt(data.encode()).decode()
                return Result.success(encrypted)
            else:
                return Result.failure(f"Encryption algorithm not implemented: {key.algorithm}")
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            return Result.failure(f"Failed to encrypt data: {str(e)}")
    
    async def decrypt(
        self, 
        data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Result[str]:
        """
        Decrypt data.
        
        Args:
            data: Data to decrypt
            context: Encryption context
            
        Returns:
            Result containing the decrypted data or an error
        """
        try:
            # Get active key
            key_result = await self.repository.get_active_key()
            if key_result.is_failure():
                return Result.failure(f"Failed to decrypt data: {key_result.error}")
            
            key = key_result.value
            
            # Perform decryption based on algorithm
            if key.algorithm == EncryptionAlgorithm.AES_GCM:
                # Example implementation (would use a proper crypto library in real code)
                key_data = base64.b64decode(key.key_data)
                f = Fernet(key_data)
                decrypted = f.decrypt(data.encode()).decode()
                return Result.success(decrypted)
            else:
                return Result.failure(f"Decryption algorithm not implemented: {key.algorithm}")
        except Exception as e:
            self.logger.error(f"Decryption error: {str(e)}")
            return Result.failure(f"Failed to decrypt data: {str(e)}")
    
    async def encrypt_field(
        self, 
        field_name: str, 
        value: str, 
        entity_type: Optional[str] = None
    ) -> Result[str]:
        """
        Encrypt a field value.
        
        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type
            
        Returns:
            Result containing the encrypted field value or an error
        """
        # Check if field should be encrypted
        if field_name in self.config.encryption.encrypted_fields:
            context = {"field_name": field_name}
            if entity_type:
                context["entity_type"] = entity_type
            
            return await self.encrypt(value, context)
        
        # Field doesn't need encryption
        return Result.success(value)
    
    async def decrypt_field(
        self, 
        field_name: str, 
        value: str, 
        entity_type: Optional[str] = None
    ) -> Result[str]:
        """
        Decrypt a field value.
        
        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type
            
        Returns:
            Result containing the decrypted field value or an error
        """
        # Check if field should be decrypted
        if field_name in self.config.encryption.encrypted_fields:
            context = {"field_name": field_name}
            if entity_type:
                context["entity_type"] = entity_type
            
            return await self.decrypt(value, context)
        
        # Field doesn't need decryption
        return Result.success(value)
    
    async def rotate_keys(self) -> Result[EncryptionKey]:
        """
        Rotate encryption keys.
        
        Returns:
            Result containing the new key or an error
        """
        try:
            # Get current active key
            current_key_result = await self.repository.get_active_key()
            if current_key_result.is_success():
                current_key = current_key_result.value
                
                # Mark current key as rotated
                await self.repository.mark_key_as_rotated(current_key.id)
            
            # Create new key
            algorithm = self.config.encryption.algorithm
            key_data = Fernet.generate_key().decode()
            
            new_key = EncryptionKey(
                id=EncryptionKeyId(str(uuid.uuid4())),
                algorithm=algorithm,
                key_data=key_data,
                is_active=True,
                key_version=1 if current_key_result.is_failure() else current_key.key_version + 1
            )
            
            # Set expiration if configured
            if self.config.encryption.key_rotation_days > 0:
                new_key.set_expiration(self.config.encryption.key_rotation_days)
            
            # Save new key
            result = await self.repository.create(new_key)
            
            if result.is_success():
                self.logger.info(f"Encryption key rotated successfully: {new_key.id.value}")
            
            return result
        except Exception as e:
            self.logger.error(f"Key rotation error: {str(e)}")
            return Result.failure(f"Failed to rotate encryption keys: {str(e)}")
    
    async def get_active_key(self) -> Result[EncryptionKey]:
        """
        Get the currently active encryption key.
        
        Returns:
            Result containing the active key or an error
        """
        return await self.repository.get_active_key()


class AuthenticationService(DomainService, AuthenticationServiceProtocol):
    """Service for authentication operations."""
    
    def __init__(
        self, 
        token_repository: JWTTokenRepositoryProtocol,
        config: SecurityConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the authentication service.
        
        Args:
            token_repository: JWT token repository
            config: Security configuration
            logger: Logger
        """
        self.token_repository = token_repository
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.authentication")
    
    async def hash_password(self, password: str) -> Result[str]:
        """
        Hash a password.
        
        Args:
            password: Password to hash
            
        Returns:
            Result containing the hashed password or an error
        """
        try:
            # Generate salt
            salt = os.urandom(16)
            
            # Use PBKDF2 with SHA-256
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            # Derive key
            key = kdf.derive(password.encode())
            
            # Return base64-encoded salt and hash
            hashed = base64.b64encode(salt + key).decode()
            
            return Result.success(hashed)
        except Exception as e:
            self.logger.error(f"Password hashing error: {str(e)}")
            return Result.failure(f"Failed to hash password: {str(e)}")
    
    async def verify_password(self, password: str, hashed_password: str) -> Result[bool]:
        """
        Verify a password.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password
            
        Returns:
            Result containing a boolean indicating validity or an error
        """
        try:
            # Decode base64
            decoded = base64.b64decode(hashed_password)
            
            # Extract salt and hash
            salt = decoded[:16]
            stored_key = decoded[16:]
            
            # Use PBKDF2 with SHA-256
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            # Derive key
            key = kdf.derive(password.encode())
            
            # Compare keys in constant time
            is_valid = secrets.compare_digest(key, stored_key)
            
            return Result.success(is_valid)
        except Exception as e:
            self.logger.error(f"Password verification error: {str(e)}")
            return Result.failure(f"Failed to verify password: {str(e)}")
    
    async def validate_password_policy(self, password: str) -> Result[Dict[str, Any]]:
        """
        Validate a password against the password policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Result containing validation results or an error
        """
        try:
            policy = self.config.authentication.password_policy
            
            # Check length
            if len(password) < policy.min_length:
                return Result.success({
                    "valid": False,
                    "message": f"Password must be at least {policy.min_length} characters long"
                })
            
            # Check complexity requirements
            if policy.require_uppercase and not any(c.isupper() for c in password):
                return Result.success({
                    "valid": False,
                    "message": "Password must contain at least one uppercase letter"
                })
            
            if policy.require_lowercase and not any(c.islower() for c in password):
                return Result.success({
                    "valid": False,
                    "message": "Password must contain at least one lowercase letter"
                })
            
            if policy.require_numbers and not any(c.isdigit() for c in password):
                return Result.success({
                    "valid": False,
                    "message": "Password must contain at least one number"
                })
            
            if policy.require_special_chars and not any(not c.isalnum() for c in password):
                return Result.success({
                    "valid": False,
                    "message": "Password must contain at least one special character"
                })
            
            # Check common passwords and patterns
            # This would check against a database of common passwords in a real implementation
            
            return Result.success({"valid": True, "message": "Password meets all requirements"})
        except Exception as e:
            self.logger.error(f"Password policy validation error: {str(e)}")
            return Result.failure(f"Failed to validate password: {str(e)}")
    
    async def generate_token(
        self, 
        user_id: str, 
        token_type: TokenType, 
        roles: List[str] = None, 
        tenant_id: Optional[str] = None, 
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> Result[Tuple[str, JWTToken]]:
        """
        Generate a new JWT token.
        
        Args:
            user_id: User ID
            token_type: Token type
            roles: User roles
            tenant_id: Tenant ID
            custom_claims: Custom claims
            
        Returns:
            Result containing the token string and token entity or an error
        """
        try:
            # Initialize claims
            roles = roles or []
            custom_claims = custom_claims or {}
            
            # Set expiration time
            if token_type == TokenType.ACCESS:
                expires_in = timedelta(minutes=self.config.authentication.jwt_expiration_minutes)
            else:  # TokenType.REFRESH
                expires_in = timedelta(days=self.config.authentication.refresh_token_expiration_days)
            
            expires_at = datetime.now(UTC) + expires_in
            
            # Set token ID
            token_id = TokenId(str(uuid.uuid4()))
            
            # Create token entity
            token_entity = JWTToken(
                id=token_id,
                user_id=user_id,
                token_type=token_type,
                roles=roles,
                tenant_id=tenant_id,
                claims=custom_claims,
                expires_at=expires_at
            )
            
            # Save token entity
            entity_result = await self.token_repository.create(token_entity)
            if entity_result.is_failure():
                return Result.failure(f"Failed to save token: {entity_result.error}")
            
            # Create JWT claims
            jwt_claims = {
                "sub": user_id,
                "exp": int(expires_at.timestamp()),
                "iat": int(datetime.now(UTC).timestamp()),
                "jti": token_id.value,
                "token_type": token_type.value,
                "roles": roles
            }
            
            # Add optional claims
            if tenant_id:
                jwt_claims["tenant_id"] = tenant_id
                
            # Add custom claims
            jwt_claims.update(custom_claims)
            
            # Add issuer and audience if configured
            if self.config.authentication.jwt_issuer:
                jwt_claims["iss"] = self.config.authentication.jwt_issuer
                
            if self.config.authentication.jwt_audience:
                jwt_claims["aud"] = self.config.authentication.jwt_audience
            
            # Encode token
            token_string = jwt.encode(
                jwt_claims,
                self.config.authentication.jwt_secret_key,
                algorithm=self.config.authentication.jwt_algorithm
            )
            
            return Result.success((token_string, token_entity))
        except Exception as e:
            self.logger.error(f"Token generation error: {str(e)}")
            return Result.failure(f"Failed to generate token: {str(e)}")
    
    async def validate_token(self, token: str) -> Result[Dict[str, Any]]:
        """
        Validate a JWT token.
        
        Args:
            token: Token to validate
            
        Returns:
            Result containing the token claims or an error
        """
        try:
            # Decode token
            jwt_claims = jwt.decode(
                token,
                self.config.authentication.jwt_secret_key,
                algorithms=[self.config.authentication.jwt_algorithm],
                options={"verify_signature": True}
            )
            
            # Get token ID
            token_id = jwt_claims.get("jti")
            if not token_id:
                return Result.failure("Token has no ID")
            
            # Check if token is valid in database
            validity_result = await self.token_repository.is_token_valid(TokenId(token_id))
            if validity_result.is_failure():
                return Result.failure(f"Token validation error: {validity_result.error}")
            
            if not validity_result.value:
                return Result.failure("Token is not valid (revoked or expired)")
            
            return Result.success(jwt_claims)
        except jwt.ExpiredSignatureError:
            return Result.failure("Token has expired")
        except jwt.InvalidTokenError as e:
            return Result.failure(f"Invalid token: {str(e)}")
        except Exception as e:
            self.logger.error(f"Token validation error: {str(e)}")
            return Result.failure(f"Failed to validate token: {str(e)}")
    
    async def revoke_token(
        self, 
        token_id: TokenId, 
        reason: Optional[str] = None
    ) -> Result[bool]:
        """
        Revoke a JWT token.
        
        Args:
            token_id: ID of the token to revoke
            reason: Optional reason for revocation
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            result = await self.token_repository.revoke_token(token_id, reason)
            if result.is_success():
                self.logger.info(f"Token revoked: {token_id.value}")
                
            return Result.success(result.is_success())
        except Exception as e:
            self.logger.error(f"Token revocation error: {str(e)}")
            return Result.failure(f"Failed to revoke token: {str(e)}")
    
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
        try:
            result = await self.token_repository.revoke_all_user_tokens(user_id, reason)
            if result.is_success():
                self.logger.info(f"All tokens revoked for user {user_id}")
                
            return result
        except Exception as e:
            self.logger.error(f"Token revocation error: {str(e)}")
            return Result.failure(f"Failed to revoke tokens: {str(e)}")


class MFAService(DomainService, MFAServiceProtocol):
    """Service for multi-factor authentication."""
    
    def __init__(
        self, 
        repository: MFACredentialRepositoryProtocol,
        config: SecurityConfig,
        encryption_service: EncryptionServiceProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the MFA service.
        
        Args:
            repository: MFA credential repository
            config: Security configuration
            encryption_service: Encryption service for securing secrets
            logger: Logger
        """
        self.repository = repository
        self.config = config
        self.encryption_service = encryption_service
        self.logger = logger or logging.getLogger("uno.security.mfa")
    
    async def setup_mfa(
        self, 
        user_id: str, 
        mfa_type: MFAType = MFAType.TOTP
    ) -> Result[Dict[str, Any]]:
        """
        Set up multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            mfa_type: MFA type
            
        Returns:
            Result containing setup information or an error
        """
        try:
            # Check if MFA is already set up
            existing_credential_result = await self.repository.get_by_user_id(user_id)
            if existing_credential_result.is_success():
                return Result.failure("MFA is already set up for this user")
            
            # Generate secret key
            if mfa_type == MFAType.TOTP:
                # Generate TOTP secret
                secret = pyotp.random_base32()
                
                # Generate backup codes
                backup_codes = []
                for _ in range(10):
                    code = "".join(secrets.choice("0123456789ABCDEF") for _ in range(8))
                    backup_codes.append(code)
                
                # Encrypt secret key
                encrypt_result = await self.encryption_service.encrypt(secret)
                if encrypt_result.is_failure():
                    return Result.failure(f"Failed to encrypt MFA secret: {encrypt_result.error}")
                
                encrypted_secret = encrypt_result.value
                
                # Create MFA credential
                credential = MFACredential(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    type=mfa_type,
                    secret_key=encrypted_secret,
                    backup_codes=backup_codes
                )
                
                # Save credential
                result = await self.repository.create(credential)
                if result.is_failure():
                    return Result.failure(f"Failed to save MFA credential: {result.error}")
                
                # Get provision URI for QR code
                app_name = "Uno App"  # This should come from configuration
                totp = pyotp.TOTP(secret)
                provision_uri = totp.provisioning_uri(user_id, issuer_name=app_name)
                
                # Return setup information
                return Result.success({
                    "secret": secret,  # Only returned during setup
                    "backup_codes": backup_codes,  # Only returned during setup
                    "provision_uri": provision_uri,
                    "type": mfa_type.value
                })
            else:
                return Result.failure(f"MFA type not implemented: {mfa_type}")
        except Exception as e:
            self.logger.error(f"MFA setup error: {str(e)}")
            return Result.failure(f"Failed to set up MFA: {str(e)}")
    
    async def verify_mfa(
        self, 
        user_id: str, 
        code: str, 
        mfa_type: Optional[MFAType] = None
    ) -> Result[bool]:
        """
        Verify a multi-factor authentication code.
        
        Args:
            user_id: User ID
            code: MFA code
            mfa_type: MFA type
            
        Returns:
            Result containing a boolean indicating validity or an error
        """
        try:
            # Get user's MFA credentials
            credential_result = await self.repository.get_by_user_id(user_id)
            if credential_result.is_failure():
                return Result.failure(f"MFA not set up for user: {credential_result.error}")
            
            credential = credential_result.value
            
            # Check if credential is active
            if not credential.is_active:
                return Result.failure("MFA is not active for this user")
            
            # Check MFA type if specified
            if mfa_type and credential.type != mfa_type:
                return Result.failure(f"MFA type mismatch: expected {mfa_type}, got {credential.type}")
            
            # Verify code based on MFA type
            if credential.type == MFAType.TOTP:
                # Decrypt secret key
                decrypt_result = await self.encryption_service.decrypt(credential.secret_key)
                if decrypt_result.is_failure():
                    return Result.failure(f"Failed to decrypt MFA secret: {decrypt_result.error}")
                
                secret = decrypt_result.value
                
                # Verify TOTP code
                totp = pyotp.TOTP(secret)
                is_valid = totp.verify(code)
                
                # Record verification attempt
                credential.record_verification_attempt(is_valid)
                await self.repository.update(credential)
                
                return Result.success(is_valid)
            else:
                return Result.failure(f"MFA type not implemented: {credential.type}")
        except Exception as e:
            self.logger.error(f"MFA verification error: {str(e)}")
            return Result.failure(f"Failed to verify MFA: {str(e)}")
    
    async def verify_backup_code(self, user_id: str, code: str) -> Result[bool]:
        """
        Verify a backup code.
        
        Args:
            user_id: User ID
            code: Backup code
            
        Returns:
            Result containing a boolean indicating validity or an error
        """
        try:
            # Get user's MFA credentials
            credential_result = await self.repository.get_by_user_id(user_id)
            if credential_result.is_failure():
                return Result.failure(f"MFA not set up for user: {credential_result.error}")
            
            credential = credential_result.value
            
            # Check if credential is active
            if not credential.is_active:
                return Result.failure("MFA is not active for this user")
            
            # Verify backup code
            is_valid = credential.use_backup_code(code)
            
            # Update credential if valid
            if is_valid:
                await self.repository.update(credential)
            
            return Result.success(is_valid)
        except Exception as e:
            self.logger.error(f"Backup code verification error: {str(e)}")
            return Result.failure(f"Failed to verify backup code: {str(e)}")
    
    async def deactivate_mfa(self, user_id: str) -> Result[bool]:
        """
        Deactivate multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            result = await self.repository.deactivate_by_user_id(user_id)
            if result.is_success():
                self.logger.info(f"MFA deactivated for user {user_id}")
                
            return result
        except Exception as e:
            self.logger.error(f"MFA deactivation error: {str(e)}")
            return Result.failure(f"Failed to deactivate MFA: {str(e)}")
    
    async def regenerate_backup_codes(self, user_id: str) -> Result[List[str]]:
        """
        Regenerate backup codes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing the new backup codes or an error
        """
        try:
            # Get user's MFA credentials
            credential_result = await self.repository.get_by_user_id(user_id)
            if credential_result.is_failure():
                return Result.failure(f"MFA not set up for user: {credential_result.error}")
            
            credential = credential_result.value
            
            # Check if credential is active
            if not credential.is_active:
                return Result.failure("MFA is not active for this user")
            
            # Generate new backup codes
            backup_codes = []
            for _ in range(10):
                code = "".join(secrets.choice("0123456789ABCDEF") for _ in range(8))
                backup_codes.append(code)
            
            # Update credential
            credential.backup_codes = backup_codes
            await self.repository.update(credential)
            
            return Result.success(backup_codes)
        except Exception as e:
            self.logger.error(f"Backup code regeneration error: {str(e)}")
            return Result.failure(f"Failed to regenerate backup codes: {str(e)}")


class SecurityService(DomainService):
    """Coordinating service for security operations."""
    
    def __init__(
        self,
        audit_service: AuditServiceProtocol,
        encryption_service: EncryptionServiceProtocol,
        authentication_service: AuthenticationServiceProtocol,
        mfa_service: MFAServiceProtocol,
        config: SecurityConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the security service.
        
        Args:
            audit_service: Audit service
            encryption_service: Encryption service
            authentication_service: Authentication service
            mfa_service: MFA service
            config: Security configuration
            logger: Logger
        """
        self.audit_service = audit_service
        self.encryption_service = encryption_service
        self.authentication_service = authentication_service
        self.mfa_service = mfa_service
        self.config = config
        self.logger = logger or logging.getLogger("uno.security")