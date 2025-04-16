"""
Domain provider for the Security module.

This module configures dependency injection for the Security module.
"""

import logging
from typing import Optional

import inject
from uno.database.provider import get_db_session

from uno.security.config import SecurityConfig
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
from uno.security.domain_services import (
    AuditService,
    EncryptionService,
    AuthenticationService,
    MFAService,
    SecurityService,
    AuditServiceProtocol,
    EncryptionServiceProtocol,
    AuthenticationServiceProtocol,
    MFAServiceProtocol
)


def configure_security_dependencies(binder: inject.Binder) -> None:
    """
    Configure dependencies for the Security module.
    
    Args:
        binder: Dependency injection binder
    """
    # Create logger
    logger = logging.getLogger("uno.security")
    
    # Bind repositories
    binder.bind(
        SecurityEventRepositoryProtocol,
        lambda: SecurityEventRepository(get_db_session())
    )
    binder.bind(
        EncryptionKeyRepositoryProtocol,
        lambda: EncryptionKeyRepository(get_db_session())
    )
    binder.bind(
        JWTTokenRepositoryProtocol,
        lambda: JWTTokenRepository(get_db_session())
    )
    binder.bind(
        MFACredentialRepositoryProtocol,
        lambda: MFACredentialRepository(get_db_session())
    )
    
    # Get configuration
    config = inject.instance(SecurityConfig)
    
    # Bind services
    binder.bind(
        AuditServiceProtocol,
        lambda: AuditService(
            inject.instance(SecurityEventRepositoryProtocol),
            config,
            logger
        )
    )
    binder.bind(
        EncryptionServiceProtocol,
        lambda: EncryptionService(
            inject.instance(EncryptionKeyRepositoryProtocol),
            config,
            logger
        )
    )
    binder.bind(
        AuthenticationServiceProtocol,
        lambda: AuthenticationService(
            inject.instance(JWTTokenRepositoryProtocol),
            config,
            logger
        )
    )
    binder.bind(
        MFAServiceProtocol,
        lambda: MFAService(
            inject.instance(MFACredentialRepositoryProtocol),
            config,
            inject.instance(EncryptionServiceProtocol),
            logger
        )
    )
    
    # Bind coordinating service
    binder.bind(
        SecurityService,
        lambda: SecurityService(
            inject.instance(AuditServiceProtocol),
            inject.instance(EncryptionServiceProtocol),
            inject.instance(AuthenticationServiceProtocol),
            inject.instance(MFAServiceProtocol),
            config,
            logger
        )
    )


def get_security_service() -> SecurityService:
    """
    Get the security service.
    
    Returns:
        SecurityService instance
    """
    return inject.instance(SecurityService)


def get_audit_service() -> AuditServiceProtocol:
    """
    Get the audit service.
    
    Returns:
        AuditService instance
    """
    return inject.instance(AuditServiceProtocol)


def get_encryption_service() -> EncryptionServiceProtocol:
    """
    Get the encryption service.
    
    Returns:
        EncryptionService instance
    """
    return inject.instance(EncryptionServiceProtocol)


def get_authentication_service() -> AuthenticationServiceProtocol:
    """
    Get the authentication service.
    
    Returns:
        AuthenticationService instance
    """
    return inject.instance(AuthenticationServiceProtocol)


def get_mfa_service() -> MFAServiceProtocol:
    """
    Get the MFA service.
    
    Returns:
        MFAService instance
    """
    return inject.instance(MFAServiceProtocol)