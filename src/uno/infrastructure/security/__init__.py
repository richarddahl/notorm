"""
Uno Security Framework.

This module provides comprehensive security features for Uno applications,
including encryption, authentication, authorization, audit logging, and security testing.
"""

from uno.security.config import SecurityConfig
from uno.security.entities import (
    SecurityEvent,
    EncryptionKey,
    JWTToken,
    MFACredential,
    TokenType,
    MFAType,
    EncryptionAlgorithm,
    EventSeverity
)
from uno.security.domain_services import (
    SecurityService,
    AuditService,
    EncryptionService,
    AuthenticationService,
    MFAService,
    AuditServiceProtocol,
    EncryptionServiceProtocol,
    AuthenticationServiceProtocol,
    MFAServiceProtocol
)
from uno.security.domain_repositories import (
    SecurityEventRepository,
    EncryptionKeyRepository,
    JWTTokenRepository,
    MFACredentialRepository,
    SecurityEventRepositoryProtocol,
    EncryptionKeyRepositoryProtocol,
    JWTTokenRepositoryProtocol,
    MFACredentialRepositoryProtocol
)
from uno.security.domain_provider import (
    configure_security_dependencies,
    get_security_service,
    get_audit_service,
    get_encryption_service,
    get_authentication_service,
    get_mfa_service
)
from uno.security.domain_endpoints import create_security_router

__version__ = "0.1.0"

__all__ = [
    # Config
    "SecurityConfig",
    
    # Entities
    "SecurityEvent",
    "EncryptionKey",
    "JWTToken",
    "MFACredential",
    "TokenType",
    "MFAType",
    "EncryptionAlgorithm",
    "EventSeverity",
    
    # Services
    "SecurityService",
    "AuditService",
    "EncryptionService",
    "AuthenticationService",
    "MFAService",
    "AuditServiceProtocol",
    "EncryptionServiceProtocol",
    "AuthenticationServiceProtocol",
    "MFAServiceProtocol",
    
    # Repositories
    "SecurityEventRepository",
    "EncryptionKeyRepository",
    "JWTTokenRepository",
    "MFACredentialRepository",
    "SecurityEventRepositoryProtocol",
    "EncryptionKeyRepositoryProtocol",
    "JWTTokenRepositoryProtocol",
    "MFACredentialRepositoryProtocol",
    
    # Providers
    "configure_security_dependencies",
    "get_security_service",
    "get_audit_service",
    "get_encryption_service",
    "get_authentication_service",
    "get_mfa_service",
    
    # Endpoints
    "create_security_router"
]