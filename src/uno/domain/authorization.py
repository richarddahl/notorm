"""
Advanced authorization system for the Uno framework.

This module provides a comprehensive authorization system that integrates
with the service context to provide fine-grained access control.
"""

import logging
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union, cast

from uno.domain.application_services import ServiceContext
from uno.domain.exceptions import AuthorizationError
from uno.domain.model import Entity, AggregateRoot


# Type variables
T = TypeVar('T')
EntityT = TypeVar('EntityT', bound=Entity)
AggregateT = TypeVar('AggregateT', bound=AggregateRoot)


class Permission:
    """
    Represents a permission in the system.
    
    Permissions follow a resource:action format (e.g., products:read),
    with support for wildcards (e.g., products:* or *:read).
    """
    
    def __init__(self, resource: str, action: str):
        """
        Initialize a permission.
        
        Args:
            resource: The resource this permission applies to
            action: The action this permission allows
        """
        self.resource = resource
        self.action = action
    
    @classmethod
    def from_string(cls, permission_string: str) -> 'Permission':
        """
        Create a permission from a string.
        
        Args:
            permission_string: The permission string (format: resource:action)
            
        Returns:
            Permission instance
            
        Raises:
            ValueError: If the permission string is invalid
        """
        if ":" not in permission_string:
            raise ValueError(f"Invalid permission format: {permission_string}. Expected format: resource:action")
        
        resource, action = permission_string.split(":", 1)
        return cls(resource, action)
    
    def __str__(self) -> str:
        """
        Convert permission to string.
        
        Returns:
            String representation (format: resource:action)
        """
        return f"{self.resource}:{self.action}"
    
    def __eq__(self, other: Any) -> bool:
        """
        Check if this permission equals another.
        
        Args:
            other: The object to compare with
            
        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, Permission):
            return False
        return self.resource == other.resource and self.action == other.action
    
    def __hash__(self) -> int:
        """
        Hash based on resource and action.
        
        Returns:
            Hash value
        """
        return hash((self.resource, self.action))
    
    def matches(self, other: 'Permission') -> bool:
        """
        Check if this permission matches another.
        
        A permission matches another if:
        - It has the same resource and action, or
        - It has a wildcard resource (*) and the same action, or
        - It has the same resource and a wildcard action (*), or
        - It has a wildcard resource and a wildcard action (*:*)
        
        Args:
            other: The permission to check against
            
        Returns:
            True if this permission matches the other, False otherwise
        """
        # Exact match
        if self.resource == other.resource and self.action == other.action:
            return True
        
        # Wildcard resource
        if self.resource == "*" and (self.action == other.action or self.action == "*"):
            return True
        
        # Wildcard action
        if self.action == "*" and (self.resource == other.resource or self.resource == "*"):
            return True
        
        return False


class Role:
    """
    Represents a role in the system.
    
    Roles are collections of permissions that can be assigned to users.
    """
    
    def __init__(self, name: str, permissions: Optional[List[Permission]] = None):
        """
        Initialize a role.
        
        Args:
            name: The role name
            permissions: Optional list of permissions
        """
        self.name = name
        self._permissions: Set[Permission] = set(permissions or [])
    
    def add_permission(self, permission: Permission) -> None:
        """
        Add a permission to this role.
        
        Args:
            permission: The permission to add
        """
        self._permissions.add(permission)
    
    def remove_permission(self, permission: Permission) -> None:
        """
        Remove a permission from this role.
        
        Args:
            permission: The permission to remove
        """
        self._permissions.discard(permission)
    
    def has_permission(self, permission: Permission) -> bool:
        """
        Check if this role has a specific permission.
        
        Args:
            permission: The permission to check
            
        Returns:
            True if the role has the permission, False otherwise
        """
        # Check for direct match
        if permission in self._permissions:
            return True
        
        # Check for wildcard matches
        for role_permission in self._permissions:
            if role_permission.matches(permission):
                return True
        
        return False
    
    @property
    def permissions(self) -> List[Permission]:
        """
        Get all permissions in this role.
        
        Returns:
            List of permissions
        """
        return list(self._permissions)


class AuthorizationPolicy(ABC, Generic[T]):
    """
    Base class for authorization policies.
    
    Authorization policies determine whether a user is allowed to perform
    an action on a resource based on the service context and optional
    target object.
    """
    
    def __init__(self, resource: str, action: str, logger: Optional[logging.Logger] = None):
        """
        Initialize an authorization policy.
        
        Args:
            resource: The resource this policy applies to
            action: The action this policy applies to
            logger: Optional logger instance
        """
        self.resource = resource
        self.action = action
        self.permission = Permission(resource, action)
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def authorize(self, context: ServiceContext, target: Optional[T] = None) -> bool:
        """
        Check if the user is authorized to perform the action.
        
        Args:
            context: The service context
            target: Optional target object
            
        Returns:
            True if authorized, False otherwise
        """
        # Check if the user is authenticated
        if not context.is_authenticated:
            self.logger.warning("Authorization failed: User is not authenticated")
            return False
        
        # Check if the user has the required permission
        if not self._check_permission(context):
            self.logger.warning(f"Authorization failed: Missing permission {self.permission}")
            return False
        
        # Perform additional authorization logic
        return await self._authorize_internal(context, target)
    
    def _check_permission(self, context: ServiceContext) -> bool:
        """
        Check if the user has the required permission.
        
        Args:
            context: The service context
            
        Returns:
            True if the user has the permission, False otherwise
        """
        # Check for exact permission
        permission_str = str(self.permission)
        if permission_str in context.permissions:
            return True
        
        # Check for wildcard permissions
        for permission in context.permissions:
            if permission == "*":  # Full wildcard
                return True
            
            if ":" in permission:
                # Check for resource wildcard (e.g., *:read)
                resource, action = permission.split(":", 1)
                if resource == "*" and action == self.action:
                    return True
                
                # Check for action wildcard (e.g., products:*)
                if resource == self.resource and action == "*":
                    return True
                
                # Check for resource prefix wildcard (e.g., products.*:read)
                if resource.endswith(".*") and action == self.action:
                    prefix = resource[:-2]  # Remove .* suffix
                    if self.resource.startswith(prefix):
                        return True
        
        return False
    
    @abstractmethod
    async def _authorize_internal(self, context: ServiceContext, target: Optional[T] = None) -> bool:
        """
        Perform internal authorization logic.
        
        This method should be implemented by subclasses to provide
        specific authorization logic.
        
        Args:
            context: The service context
            target: Optional target object
            
        Returns:
            True if authorized, False otherwise
        """
        pass


class SimplePolicy(AuthorizationPolicy[T]):
    """
    Simple authorization policy that only checks permissions.
    
    This policy doesn't perform any additional authorization logic
    beyond checking if the user has the required permission.
    """
    
    async def _authorize_internal(self, context: ServiceContext, target: Optional[T] = None) -> bool:
        """
        Simply return True as the permission check was already done.
        
        Args:
            context: The service context
            target: Optional target object
            
        Returns:
            True always
        """
        return True


class OwnershipPolicy(AuthorizationPolicy[EntityT]):
    """
    Authorization policy that checks ownership.
    
    This policy checks if the user is the owner of the target entity.
    """
    
    def __init__(
        self,
        resource: str,
        action: str,
        owner_field: str = "owner_id",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize an ownership policy.
        
        Args:
            resource: The resource this policy applies to
            action: The action this policy applies to
            owner_field: The field in the entity that identifies the owner
            logger: Optional logger instance
        """
        super().__init__(resource, action, logger)
        self.owner_field = owner_field
    
    async def _authorize_internal(self, context: ServiceContext, target: Optional[EntityT] = None) -> bool:
        """
        Check if the user is the owner of the target entity.
        
        Args:
            context: The service context
            target: Optional target entity
            
        Returns:
            True if the user is the owner, False otherwise
        """
        # If no target is provided, we can't check ownership
        if target is None:
            self.logger.warning("Ownership check failed: No target provided")
            return False
        
        # Check if the target has the owner field
        if not hasattr(target, self.owner_field):
            self.logger.warning(f"Ownership check failed: Target has no {self.owner_field} field")
            return False
        
        # Check if the user is the owner
        owner_id = getattr(target, self.owner_field)
        is_owner = owner_id == context.user_id
        
        if not is_owner:
            self.logger.warning(f"Ownership check failed: User {context.user_id} is not owner {owner_id}")
        
        return is_owner


class TenantPolicy(AuthorizationPolicy[EntityT]):
    """
    Authorization policy that checks tenant isolation.
    
    This policy checks if the entity belongs to the user's tenant.
    """
    
    def __init__(
        self,
        resource: str,
        action: str,
        tenant_field: str = "tenant_id",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize a tenant policy.
        
        Args:
            resource: The resource this policy applies to
            action: The action this policy applies to
            tenant_field: The field in the entity that identifies the tenant
            logger: Optional logger instance
        """
        super().__init__(resource, action, logger)
        self.tenant_field = tenant_field
    
    async def _authorize_internal(self, context: ServiceContext, target: Optional[EntityT] = None) -> bool:
        """
        Check if the entity belongs to the user's tenant.
        
        Args:
            context: The service context
            target: Optional target entity
            
        Returns:
            True if the entity belongs to the user's tenant, False otherwise
        """
        # If no target is provided, we can't check tenant
        if target is None:
            self.logger.warning("Tenant check failed: No target provided")
            return False
        
        # If no tenant_id in context, we can't check tenant
        if context.tenant_id is None:
            self.logger.warning("Tenant check failed: No tenant_id in context")
            return False
        
        # Check if the target has the tenant field
        if not hasattr(target, self.tenant_field):
            self.logger.warning(f"Tenant check failed: Target has no {self.tenant_field} field")
            return False
        
        # Check if the entity belongs to the user's tenant
        entity_tenant_id = getattr(target, self.tenant_field)
        same_tenant = entity_tenant_id == context.tenant_id
        
        if not same_tenant:
            self.logger.warning(f"Tenant check failed: Entity tenant {entity_tenant_id} != user tenant {context.tenant_id}")
        
        return same_tenant


class FunctionPolicy(AuthorizationPolicy[T]):
    """
    Authorization policy that delegates to a function.
    
    This policy delegates authorization logic to a callable function.
    """
    
    def __init__(
        self,
        resource: str,
        action: str,
        func: Callable[[ServiceContext, Optional[T]], bool],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize a function policy.
        
        Args:
            resource: The resource this policy applies to
            action: The action this policy applies to
            func: The authorization function
            logger: Optional logger instance
        """
        super().__init__(resource, action, logger)
        self.func = func
    
    async def _authorize_internal(self, context: ServiceContext, target: Optional[T] = None) -> bool:
        """
        Delegate authorization to the function.
        
        Args:
            context: The service context
            target: Optional target object
            
        Returns:
            True if authorized, False otherwise
        """
        try:
            return self.func(context, target)
        except Exception as e:
            self.logger.error(f"Authorization function failed: {str(e)}")
            return False


class CompositePolicy(AuthorizationPolicy[T]):
    """
    Authorization policy that combines multiple policies.
    
    This policy applies multiple policies and returns True if any/all of them pass.
    """
    
    class CombinationMode(Enum):
        """Policy combination modes."""
        
        ANY = "any"  # Any policy must pass (OR)
        ALL = "all"  # All policies must pass (AND)
    
    def __init__(
        self,
        resource: str,
        action: str,
        policies: List[AuthorizationPolicy[T]],
        mode: CombinationMode = CombinationMode.ALL,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize a composite policy.
        
        Args:
            resource: The resource this policy applies to
            action: The action this policy applies to
            policies: List of policies to combine
            mode: How to combine the policies (ANY or ALL)
            logger: Optional logger instance
        """
        super().__init__(resource, action, logger)
        self.policies = policies
        self.mode = mode
    
    async def _authorize_internal(self, context: ServiceContext, target: Optional[T] = None) -> bool:
        """
        Apply all policies according to the combination mode.
        
        Args:
            context: The service context
            target: Optional target object
            
        Returns:
            True if authorized according to the combination mode, False otherwise
        """
        if not self.policies:
            self.logger.warning("No policies to apply")
            return False
        
        results = []
        for policy in self.policies:
            result = await policy.authorize(context, target)
            results.append(result)
            
            # Short-circuit evaluation
            if self.mode == self.CombinationMode.ANY and result:
                return True
            if self.mode == self.CombinationMode.ALL and not result:
                return False
        
        # If we get here, it means:
        # - In ANY mode, no policy passed
        # - In ALL mode, all policies passed
        return self.mode == self.CombinationMode.ALL


class AuthorizationService:
    """
    Service for performing authorization checks.
    
    This service provides methods for registering and applying
    authorization policies.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the authorization service.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._policies: Dict[str, AuthorizationPolicy] = {}
    
    def register_policy(self, policy: AuthorizationPolicy) -> None:
        """
        Register an authorization policy.
        
        Args:
            policy: The policy to register
        """
        key = f"{policy.resource}:{policy.action}"
        self._policies[key] = policy
        self.logger.debug(f"Registered policy for {key}")
    
    def get_policy(self, resource: str, action: str) -> Optional[AuthorizationPolicy]:
        """
        Get a policy for a specific resource and action.
        
        Args:
            resource: The resource
            action: The action
            
        Returns:
            The policy if found, None otherwise
        """
        key = f"{resource}:{action}"
        return self._policies.get(key)
    
    async def authorize(
        self,
        context: ServiceContext,
        resource: str,
        action: str,
        target: Optional[Any] = None
    ) -> bool:
        """
        Check if the user is authorized to perform the action on the resource.
        
        Args:
            context: The service context
            resource: The resource
            action: The action
            target: Optional target object
            
        Returns:
            True if authorized, False otherwise
        """
        # Get the policy
        policy = self.get_policy(resource, action)
        
        # If no policy is registered, check only permissions
        if policy is None:
            self.logger.debug(f"No policy registered for {resource}:{action}, checking permissions only")
            simple_policy = SimplePolicy(resource, action)
            return await simple_policy.authorize(context, target)
        
        # Apply the policy
        return await policy.authorize(context, target)
    
    async def authorize_or_raise(
        self,
        context: ServiceContext,
        resource: str,
        action: str,
        target: Optional[Any] = None
    ) -> None:
        """
        Check if the user is authorized and raise an exception if not.
        
        Args:
            context: The service context
            resource: The resource
            action: The action
            target: Optional target object
            
        Raises:
            AuthorizationError: If authorization fails
        """
        if not await self.authorize(context, resource, action, target):
            permission = f"{resource}:{action}"
            raise AuthorizationError(f"Not authorized to {action} {resource}")


# Create a default authorization service
default_authorization_service = AuthorizationService()


def get_authorization_service() -> AuthorizationService:
    """Get the default authorization service."""
    return default_authorization_service