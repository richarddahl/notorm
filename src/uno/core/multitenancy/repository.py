"""
Tenant-aware repositories.

This module provides repository classes that automatically filter queries
by tenant ID, ensuring tenant isolation at the repository level.
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func, text
from sqlalchemy.sql import Select

from uno.model import UnoModel
from uno.database.repository import UnoBaseRepository
from uno.core.multitenancy.context import get_current_tenant_context
from uno.core.multitenancy.models import TenantAwareModel


ModelT = TypeVar('ModelT', bound=TenantAwareModel)


class TenantAwareRepository(UnoBaseRepository[ModelT]):
    """
    Repository for tenant-aware models.
    
    This repository automatically filters all queries by the current tenant ID,
    ensuring that data is properly isolated between tenants.
    """
    
    def __init__(self, session: AsyncSession, model_class: Type[ModelT], **kwargs):
        """
        Initialize the repository.
        
        Args:
            session: SQLAlchemy async session
            model_class: Model class this repository works with (must be a TenantAwareModel)
            **kwargs: Additional arguments to pass to the parent constructor
        """
        super().__init__(session, model_class, **kwargs)
        
        # Verify that the model class is tenant-aware
        if not issubclass(model_class, TenantAwareModel):
            raise TypeError(
                f"Model class {model_class.__name__} is not tenant-aware. "
                f"Tenant-aware models must inherit from TenantAwareModel."
            )
    
    def _apply_tenant_filter(self, stmt: Select) -> Select:
        """
        Apply tenant filtering to a query.
        
        This method adds a tenant_id filter to the query based on the current tenant context.
        
        Args:
            stmt: SQLAlchemy select statement
            
        Returns:
            The statement with tenant filtering applied
        """
        tenant_id = get_current_tenant_context()
        if tenant_id:
            return stmt.where(self.model_class.tenant_id == tenant_id)
        
        # If no tenant is set in the context, return a query that will never match anything
        # This is a safety measure to ensure that tenant isolation is maintained
        return stmt.where(False)
    
    async def get(self, id: str) -> Optional[ModelT]:
        """
        Get a model by ID, filtered by the current tenant.
        
        Args:
            id: The model's unique identifier
            
        Returns:
            The model if found, None otherwise
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        stmt = self._apply_tenant_filter(stmt)
        
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelT]:
        """
        List models with optional filtering, ordering, and pagination.
        
        This method automatically filters by the current tenant ID.
        
        Args:
            filters: Dictionary of filters to apply
            order_by: List of fields to order by
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of models matching the criteria
        """
        # Start with a basic select statement
        stmt = select(self.model_class)
        
        # Apply tenant filtering
        stmt = self._apply_tenant_filter(stmt)
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    stmt = stmt.where(getattr(self.model_class, field) == value)
        
        # Apply ordering
        if order_by:
            for field in order_by:
                descending = field.startswith('-')
                field_name = field[1:] if descending else field
                
                if hasattr(self.model_class, field_name):
                    column = getattr(self.model_class, field_name)
                    stmt = stmt.order_by(column.desc() if descending else column)
        
        # Apply pagination
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
        
        # Execute and return results
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, data: Dict[str, Any]) -> ModelT:
        """
        Create a new model in the current tenant's context.
        
        This method automatically sets the tenant_id based on the current tenant context.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            The created model
        """
        # Get current tenant ID
        tenant_id = get_current_tenant_context()
        if not tenant_id:
            raise ValueError(
                "Cannot create tenant-aware model without a tenant context. "
                "Use TenantContext or tenant_context to set the current tenant."
            )
        
        # Set tenant_id in the data
        data["tenant_id"] = tenant_id
        
        # Create the model
        return await super().create(data)
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelT]:
        """
        Update an existing model, ensuring it belongs to the current tenant.
        
        Args:
            id: The model's unique identifier
            data: Dictionary of field values to update
            
        Returns:
            The updated model if found, None otherwise
        """
        # Prevent changing the tenant_id
        if "tenant_id" in data:
            raise ValueError("Cannot change tenant_id of an existing model")
        
        # Use get() to verify the model exists and belongs to the current tenant
        model = await self.get(id)
        if not model:
            return None
        
        # Perform the update
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**data)
            .returning(self.model_class)
        )
        # Apply tenant filtering for extra safety
        stmt = self._apply_tenant_filter(stmt)
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()
    
    async def delete(self, id: str) -> bool:
        """
        Delete a model, ensuring it belongs to the current tenant.
        
        Args:
            id: The model's unique identifier
            
        Returns:
            True if the model was deleted, False if it wasn't found
        """
        # Use get() to verify the model exists and belongs to the current tenant
        model = await self.get(id)
        if not model:
            return False
        
        # Perform the delete
        stmt = delete(self.model_class).where(self.model_class.id == id)
        # Apply tenant filtering for extra safety
        stmt = self._apply_tenant_filter(stmt)
        
        await self.session.execute(stmt)
        await self.session.commit()
        return True
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count models matching the given filters, filtered by the current tenant.
        
        Args:
            filters: Dictionary of filters to apply
            
        Returns:
            The number of matching models
        """
        stmt = select(func.count()).select_from(self.model_class)
        
        # Apply tenant filtering
        stmt = self._apply_tenant_filter(stmt)
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    stmt = stmt.where(getattr(self.model_class, field) == value)
        
        # Execute and return result
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def save(self, obj: Union[TenantAwareModel, Dict[str, Any]]) -> ModelT:
        """
        Save an object to the database, ensuring proper tenant isolation.
        
        This method handles both creation and update based on whether
        the object has an ID. For new objects, it automatically sets the tenant_id.
        
        Args:
            obj: Model instance or dictionary
            
        Returns:
            The saved model
        """
        # Get data dictionary
        if isinstance(obj, TenantAwareModel):
            data = obj.model_dump(exclude={'id'} if obj.id is None else set())
            obj_id = obj.id
        elif isinstance(obj, dict):
            data = obj.copy()
            obj_id = data.pop('id', None)
        else:
            raise TypeError(f"Expected TenantAwareModel or dict, got {type(obj)}")
        
        # Handle tenant_id for new objects
        tenant_id = get_current_tenant_context()
        if obj_id is None:
            # New object, set tenant_id
            if not tenant_id:
                raise ValueError(
                    "Cannot create tenant-aware model without a tenant context. "
                    "Use TenantContext or tenant_context to set the current tenant."
                )
            data["tenant_id"] = tenant_id
        else:
            # Existing object, ensure it belongs to the current tenant
            # and prevent changing the tenant_id
            existing = await self.get(obj_id)
            if not existing:
                raise ValueError(f"Object with ID {obj_id} not found or does not belong to the current tenant")
            
            if "tenant_id" in data and data["tenant_id"] != existing.tenant_id:
                raise ValueError("Cannot change tenant_id of an existing model")
        
        # Create or update
        if obj_id is None:
            return await self.create(data)
        else:
            return await self.update(obj_id, data)
    
    async def exists(self, id: str) -> bool:
        """
        Check if a model with the given ID exists in the current tenant.
        
        Args:
            id: The model's unique identifier
            
        Returns:
            True if the model exists, False otherwise
        """
        stmt = select(func.count()).select_from(self.model_class)
        stmt = stmt.where(self.model_class.id == id)
        stmt = self._apply_tenant_filter(stmt)
        
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0
    
    async def find_by(self, **kwargs) -> List[ModelT]:
        """
        Find models matching the given criteria in the current tenant.
        
        This is a convenience method for filtering by field values.
        
        Args:
            **kwargs: Field values to filter by
            
        Returns:
            List of matching models
        """
        return await self.list(filters=kwargs)
    
    async def find_one_by(self, **kwargs) -> Optional[ModelT]:
        """
        Find a single model matching the given criteria in the current tenant.
        
        This is a convenience method for filtering by field values.
        
        Args:
            **kwargs: Field values to filter by
            
        Returns:
            The matching model, or None if not found
        """
        models = await self.list(filters=kwargs, limit=1)
        return models[0] if models else None
    
    async def batch_create(self, items: List[Dict[str, Any]]) -> List[ModelT]:
        """
        Create multiple models in a single batch operation.
        
        This method automatically sets the tenant_id for all items.
        
        Args:
            items: List of dictionaries with field values
            
        Returns:
            List of created models
        """
        if not items:
            return []
        
        # Get current tenant ID
        tenant_id = get_current_tenant_context()
        if not tenant_id:
            raise ValueError(
                "Cannot create tenant-aware models without a tenant context. "
                "Use TenantContext or tenant_context to set the current tenant."
            )
        
        # Set tenant_id for all items
        for item in items:
            item["tenant_id"] = tenant_id
        
        # Create all items in a single batch
        stmt = insert(self.model_class).values(items).returning(self.model_class)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return list(result.scalars().all())


class TenantRepository(UnoBaseRepository):
    """
    Repository for managing tenants.
    
    This repository is not tenant-aware as tenants themselves are global entities.
    """
    pass  # Uses the base implementation

    
class UserTenantAssociationRepository(UnoBaseRepository):
    """
    Repository for managing user-tenant associations.
    
    This repository is not tenant-aware as associations are global entities.
    """
    
    async def get_user_tenants(self, user_id: str) -> List:
        """
        Get all tenants associated with a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of tenant associations for the user
        """
        stmt = select(self.model_class).where(self.model_class.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_tenant_users(self, tenant_id: str) -> List:
        """
        Get all users associated with a tenant.
        
        Args:
            tenant_id: The tenant's ID
            
        Returns:
            List of user associations for the tenant
        """
        stmt = select(self.model_class).where(self.model_class.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_user_tenant(self, user_id: str, tenant_id: str) -> Optional:
        """
        Get a specific user-tenant association.
        
        Args:
            user_id: The user's ID
            tenant_id: The tenant's ID
            
        Returns:
            The association if it exists, None otherwise
        """
        stmt = select(self.model_class).where(
            self.model_class.user_id == user_id,
            self.model_class.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def user_has_access_to_tenant(self, user_id: str, tenant_id: str) -> bool:
        """
        Check if a user has access to a tenant.
        
        Args:
            user_id: The user's ID
            tenant_id: The tenant's ID
            
        Returns:
            True if the user has access to the tenant, False otherwise
        """
        association = await self.get_user_tenant(user_id, tenant_id)
        return association is not None and association.status == "active"