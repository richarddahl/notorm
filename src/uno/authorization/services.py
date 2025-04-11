"""
Service implementations for authorization domain.

This module provides service implementations that encapsulate business logic
for the authorization domain.
"""

from typing import List, Optional, Dict, Any, Union
import logging

from uno.dependencies.service import UnoService
from uno.dependencies.interfaces import UnoRepositoryProtocol
from uno.authorization.models import UserModel, GroupModel, RoleModel


class UserService(UnoService[UserModel, List[UserModel]]):
    """
    Service for User management.
    
    Encapsulates business logic for user operations.
    """
    
    def __init__(
        self,
        repository: UnoRepositoryProtocol[UserModel],
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the service with a repository."""
        super().__init__(repository, logger)
    
    async def execute(
        self, 
        tenant_id: Optional[str] = None,
        group_id: Optional[str] = None,
        role_id: Optional[str] = None,
        superusers_only: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserModel]:
        """
        Execute a user search query based on the provided criteria.
        
        Args:
            tenant_id: Optional tenant ID to filter by
            group_id: Optional group ID to filter by
            role_id: Optional role ID to filter by
            superusers_only: If True, only return superusers
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of users matching the criteria
        """
        repository = self.repository
        
        if hasattr(repository, 'find_superusers') and superusers_only:
            # If superusers_only is True, use the dedicated method
            return await repository.find_superusers(limit=limit, offset=offset)
            
        elif hasattr(repository, 'find_by_tenant') and tenant_id:
            # If tenant_id is provided, use the tenant filter
            return await repository.find_by_tenant(
                tenant_id=tenant_id, 
                limit=limit, 
                offset=offset
            )
            
        elif hasattr(repository, 'find_by_group') and group_id:
            # If group_id is provided, use the group filter
            return await repository.find_by_group(
                group_id=group_id, 
                limit=limit, 
                offset=offset
            )
            
        elif hasattr(repository, 'find_by_role') and role_id:
            # If role_id is provided, use the role filter
            return await repository.find_by_role(
                role_id=role_id, 
                limit=limit, 
                offset=offset
            )
            
        else:
            # If no specific filter is provided, use the generic list method
            filters = {}
            if tenant_id:
                filters['tenant_id'] = tenant_id
                
            return await repository.list(
                filters=filters, 
                limit=limit, 
                offset=offset
            )
    
    async def get_user_by_email_or_handle(
        self, 
        identifier: str,
        tenant_id: Optional[str] = None
    ) -> Optional[UserModel]:
        """
        Get a user by email or handle.
        
        This method tries to find a user by email first, then by handle
        if no user is found by email.
        
        Args:
            identifier: Email address or handle to search for
            tenant_id: Optional tenant ID to restrict the search
            
        Returns:
            The user if found, None otherwise
        """
        # Try to find by email first (unique across all tenants)
        if hasattr(self.repository, 'find_by_email'):
            user = await self.repository.find_by_email(identifier)
            if user:
                return user
        
        # If not found by email and handle search is supported, try handle
        if hasattr(self.repository, 'find_by_handle'):
            return await self.repository.find_by_handle(
                handle=identifier,
                tenant_id=tenant_id
            )
            
        # As a fallback, use the list method with filtering
        filters = {}
        if '@' in identifier:
            filters['email'] = identifier
        else:
            filters['handle'] = identifier
            
        if tenant_id:
            filters['tenant_id'] = tenant_id
            
        users = await self.repository.list(filters=filters, limit=1)
        return users[0] if users else None
    
    
class GroupService(UnoService[GroupModel, List[GroupModel]]):
    """
    Service for Group management.
    
    Encapsulates business logic for group operations.
    """
    
    def __init__(
        self,
        repository: UnoRepositoryProtocol[GroupModel],
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the service with a repository."""
        super().__init__(repository, logger)
    
    async def execute(
        self, 
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[GroupModel]:
        """
        Execute a group search query based on the provided criteria.
        
        Args:
            tenant_id: Optional tenant ID to filter by
            user_id: Optional user ID to filter by
            name: Optional group name to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of groups matching the criteria
        """
        repository = self.repository
        
        if hasattr(repository, 'find_by_name') and name and tenant_id:
            # If name and tenant_id are provided, try to find by name
            group = await repository.find_by_name(name=name, tenant_id=tenant_id)
            return [group] if group else []
            
        elif hasattr(repository, 'find_by_tenant') and tenant_id:
            # If tenant_id is provided, use the tenant filter
            return await repository.find_by_tenant(
                tenant_id=tenant_id, 
                limit=limit, 
                offset=offset
            )
            
        elif hasattr(repository, 'find_by_user') and user_id:
            # If user_id is provided, use the user filter
            return await repository.find_by_user(
                user_id=user_id, 
                limit=limit, 
                offset=offset
            )
            
        else:
            # If no specific filter is provided, use the generic list method
            filters = {}
            if tenant_id:
                filters['tenant_id'] = tenant_id
            if name:
                filters['name'] = name
                
            return await repository.list(
                filters=filters, 
                limit=limit, 
                offset=offset
            )