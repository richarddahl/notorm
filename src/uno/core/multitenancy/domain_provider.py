"""
Dependency injection provider for multi-tenancy.

This module configures and provides dependencies for the multi-tenancy module,
including repositories and services.
"""

import logging
from typing import Optional, Dict, Any, ClassVar

import inject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from .domain_repositories import (
    TenantRepositoryProtocol,
    UserTenantAssociationRepositoryProtocol,
    TenantInvitationRepositoryProtocol,
    TenantSettingRepositoryProtocol,
    TenantSQLAlchemyRepository,
    UserTenantAssociationSQLAlchemyRepository
)
from .domain_services import (
    TenantServiceProtocol,
    UserTenantServiceProtocol,
    TenantInvitationServiceProtocol,
    TenantService,
    UserTenantService,
    TenantInvitationService
)


class MultitenancyProvider:
    """
    Provider for multi-tenancy dependencies.
    
    This class configures and provides dependencies for the multi-tenancy module,
    including repositories and services.
    """
    
    _configured: ClassVar[bool] = False
    _logger: ClassVar[logging.Logger] = logging.getLogger(__name__)
    
    @classmethod
    def configure(
        cls,
        session_factory: Optional[sessionmaker] = None,
        tenant_repository: Optional[TenantRepositoryProtocol] = None,
        user_tenant_repository: Optional[UserTenantAssociationRepositoryProtocol] = None,
        tenant_invitation_repository: Optional[TenantInvitationRepositoryProtocol] = None,
        tenant_setting_repository: Optional[TenantSettingRepositoryProtocol] = None
    ) -> None:
        """
        Configure the multi-tenancy module.
        
        Args:
            session_factory: SQLAlchemy session factory
            tenant_repository: Optional custom tenant repository
            user_tenant_repository: Optional custom user-tenant association repository
            tenant_invitation_repository: Optional custom tenant invitation repository
            tenant_setting_repository: Optional custom tenant setting repository
        """
        if cls._configured:
            cls._logger.warning("MultitenancyProvider is already configured, reconfiguring")
        
        def config_multitenancy(binder: inject.Binder) -> None:
            """Configure the dependency injection bindings."""
            # Bind repositories
            if tenant_repository:
                binder.bind(TenantRepositoryProtocol, tenant_repository)
            elif session_factory:
                binder.bind_to_provider(
                    TenantRepositoryProtocol,
                    lambda: TenantSQLAlchemyRepository(session_factory())
                )
            
            if user_tenant_repository:
                binder.bind(UserTenantAssociationRepositoryProtocol, user_tenant_repository)
            elif session_factory:
                binder.bind_to_provider(
                    UserTenantAssociationRepositoryProtocol,
                    lambda: UserTenantAssociationSQLAlchemyRepository(session_factory())
                )
            
            if tenant_invitation_repository:
                binder.bind(TenantInvitationRepositoryProtocol, tenant_invitation_repository)
            
            if tenant_setting_repository:
                binder.bind(TenantSettingRepositoryProtocol, tenant_setting_repository)
            
            # Bind services
            binder.bind_to_provider(
                TenantServiceProtocol,
                lambda: TenantService(
                    tenant_repository=inject.instance(TenantRepositoryProtocol)
                )
            )
            
            binder.bind_to_provider(
                UserTenantServiceProtocol,
                lambda: UserTenantService(
                    association_repository=inject.instance(UserTenantAssociationRepositoryProtocol),
                    tenant_repository=inject.instance(TenantRepositoryProtocol)
                )
            )
            
            binder.bind_to_provider(
                TenantInvitationServiceProtocol,
                lambda: TenantInvitationService(
                    invitation_repository=inject.instance(TenantInvitationRepositoryProtocol),
                    tenant_repository=inject.instance(TenantRepositoryProtocol),
                    user_tenant_service=inject.instance(UserTenantServiceProtocol)
                )
            )
        
        # Install the configuration
        inject.configure(config_multitenancy)
        cls._configured = True
    
    @classmethod
    def get_tenant_service(cls) -> TenantServiceProtocol:
        """
        Get the tenant service.
        
        Returns:
            The tenant service instance
        """
        return inject.instance(TenantServiceProtocol)
    
    @classmethod
    def get_user_tenant_service(cls) -> UserTenantServiceProtocol:
        """
        Get the user-tenant service.
        
        Returns:
            The user-tenant service instance
        """
        return inject.instance(UserTenantServiceProtocol)
    
    @classmethod
    def get_tenant_invitation_service(cls) -> TenantInvitationServiceProtocol:
        """
        Get the tenant invitation service.
        
        Returns:
            The tenant invitation service instance
        """
        return inject.instance(TenantInvitationServiceProtocol)


class TestingMultitenancyProvider:
    """
    Provider for multi-tenancy dependencies in tests.
    
    This class configures mock repositories and services for testing the multi-tenancy module.
    """
    
    @classmethod
    def configure(
        cls,
        tenant_repository: Optional[TenantRepositoryProtocol] = None,
        user_tenant_repository: Optional[UserTenantAssociationRepositoryProtocol] = None,
        tenant_invitation_repository: Optional[TenantInvitationRepositoryProtocol] = None,
        tenant_setting_repository: Optional[TenantSettingRepositoryProtocol] = None
    ) -> Dict[str, Any]:
        """
        Configure the multi-tenancy module for testing.
        
        Args:
            tenant_repository: Mock tenant repository
            user_tenant_repository: Mock user-tenant association repository
            tenant_invitation_repository: Mock tenant invitation repository
            tenant_setting_repository: Mock tenant setting repository
            
        Returns:
            A dictionary of configured dependencies
        """
        # Create tenant service
        tenant_service = TenantService(
            tenant_repository=tenant_repository
        )
        
        # Create user-tenant service
        user_tenant_service = UserTenantService(
            association_repository=user_tenant_repository,
            tenant_repository=tenant_repository
        )
        
        # Create tenant invitation service
        tenant_invitation_service = TenantInvitationService(
            invitation_repository=tenant_invitation_repository,
            tenant_repository=tenant_repository,
            user_tenant_service=user_tenant_service
        )
        
        # Configure dependency injection
        def config_testing(binder: inject.Binder) -> None:
            """Configure the dependency injection bindings for testing."""
            # Bind repositories
            if tenant_repository:
                binder.bind(TenantRepositoryProtocol, tenant_repository)
            
            if user_tenant_repository:
                binder.bind(UserTenantAssociationRepositoryProtocol, user_tenant_repository)
            
            if tenant_invitation_repository:
                binder.bind(TenantInvitationRepositoryProtocol, tenant_invitation_repository)
            
            if tenant_setting_repository:
                binder.bind(TenantSettingRepositoryProtocol, tenant_setting_repository)
            
            # Bind services
            binder.bind(TenantServiceProtocol, tenant_service)
            binder.bind(UserTenantServiceProtocol, user_tenant_service)
            binder.bind(TenantInvitationServiceProtocol, tenant_invitation_service)
        
        # Install the test configuration
        inject.clear_and_configure(config_testing)
        
        # Return the dependencies for test verification
        return {
            "tenant_repository": tenant_repository,
            "user_tenant_repository": user_tenant_repository,
            "tenant_invitation_repository": tenant_invitation_repository,
            "tenant_setting_repository": tenant_setting_repository,
            "tenant_service": tenant_service,
            "user_tenant_service": user_tenant_service,
            "tenant_invitation_service": tenant_invitation_service
        }