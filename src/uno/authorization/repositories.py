"""
Repository implementations for authorization models.

This module provides repository implementations for the authorization 
domain models, following the repository pattern defined in the dependencies module.
"""

from typing import List, Optional, Dict, Any
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_

from uno.dependencies.repository import UnoRepository
from uno.authorization.models import (
    UserModel,
    GroupModel,
    RoleModel,
    TenantModel,
    PermissionModel,
    ResponsibilityRoleModel
)


class UserRepository(UnoRepository[UserModel]):
    """
    Repository for User entities.
    
    Provides data access methods for User management.
    """
    
    def __init__(
        self, 
        session: AsyncSession,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the repository with a database session."""
        super().__init__(session, UserModel, logger)
    
    async def find_by_email(self, email: str) -> Optional[UserModel]:
        """
        Find a user by email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            The user if found, None otherwise
        """
        stmt = select(self.model_class).where(self.model_class.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def find_by_handle(self, handle: str, tenant_id: Optional[str] = None) -> Optional[UserModel]:
        """
        Find a user by handle, optionally within a specific tenant.
        
        Args:
            handle: The user handle to search for
            tenant_id: Optional tenant ID to restrict the search
            
        Returns:
            The user if found, None otherwise
        """
        conditions = [self.model_class.handle == handle]
        
        if tenant_id:
            conditions.append(self.model_class.tenant_id == tenant_id)
            
        stmt = select(self.model_class).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def find_by_tenant(
        self, 
        tenant_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserModel]:
        """
        Find all users in a specific tenant.
        
        Args:
            tenant_id: The tenant ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of users in the tenant
        """
        stmt = select(self.model_class).where(self.model_class.tenant_id == tenant_id)
        
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_by_group(
        self, 
        group_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserModel]:
        """
        Find all users in a specific group.
        
        Args:
            group_id: The group ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of users in the group
        """
        # This query needs to account for users where this is their default group
        # or they're explicitly in the group through the many-to-many relationship
        stmt = select(self.model_class).where(
            or_(
                self.model_class.default_group_id == group_id,
                self.model_class.groups.any(id=group_id)
            )
        )
        
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_by_role(
        self, 
        role_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserModel]:
        """
        Find all users with a specific role.
        
        Args:
            role_id: The role ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of users with the role
        """
        stmt = select(self.model_class).where(
            self.model_class.roles.any(id=role_id)
        )
        
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_superusers(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserModel]:
        """
        Find all superusers.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of superusers
        """
        stmt = select(self.model_class).where(self.model_class.is_superuser == True)
        
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class GroupRepository(UnoRepository[GroupModel]):
    """
    Repository for Group entities.
    
    Provides data access methods for Group management.
    """
    
    def __init__(
        self, 
        session: AsyncSession,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the repository with a database session."""
        super().__init__(session, GroupModel, logger)
    
    async def find_by_name(
        self, 
        name: str, 
        tenant_id: str
    ) -> Optional[GroupModel]:
        """
        Find a group by name in a specific tenant.
        
        Args:
            name: The group name to search for
            tenant_id: The tenant ID to restrict the search
            
        Returns:
            The group if found, None otherwise
        """
        stmt = select(self.model_class).where(
            and_(
                self.model_class.name == name,
                self.model_class.tenant_id == tenant_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def find_by_tenant(
        self, 
        tenant_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[GroupModel]:
        """
        Find all groups in a specific tenant.
        
        Args:
            tenant_id: The tenant ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of groups in the tenant
        """
        stmt = select(self.model_class).where(self.model_class.tenant_id == tenant_id)
        
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_by_user(
        self, 
        user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[GroupModel]:
        """
        Find all groups for a specific user.
        
        Args:
            user_id: The user ID to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of groups the user belongs to
        """
        stmt = select(self.model_class).where(
            self.model_class.users.any(id=user_id)
        )
        
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())