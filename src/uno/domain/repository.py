"""
Repository pattern implementation for the Uno framework.

This module provides a repository pattern implementation for the domain layer,
abstracting the data access and persistence logic from the domain models.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type, Set, Union, Tuple

from uno.domain.core import Entity, AggregateRoot


T = TypeVar('T', bound=Entity)


class Repository(Generic[T], ABC):
    """
    Abstract base class for repositories.
    
    Repositories provide data access for domain entities and aggregates, hiding the
    complexity of data retrieval and persistence behind a collection-like interface.
    """
    
    @abstractmethod
    async def get(self, id: str, load_relations: Optional[Union[bool, List[str]]] = None) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The unique identifier of the entity
            load_relations: Controls which relationships to load
                - True: Load all relationships
                - False or None: Load no relationships
                - List[str]: Load only specified relationships
                
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        load_relations: Optional[Union[bool, List[str]]] = None
    ) -> List[T]:
        """
        List entities with optional filtering, ordering, and pagination.
        
        Args:
            filters: Filters to apply, typically field=value pairs
            order_by: Fields to order by, with optional direction (e.g., ['name', '-created_at'])
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            load_relations: Controls which relationships to load
                - True: Load all relationships
                - False or None: Load no relationships
                - List[str]: Load only specified relationships
                
        Returns:
            List of entities matching the criteria
        """
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        Add a new entity to the repository.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity, typically with generated IDs and timestamps
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity in the repository.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        pass
    
    @abstractmethod
    async def remove(self, entity: T) -> None:
        """
        Remove an entity from the repository.
        
        Args:
            entity: The entity to remove
        """
        pass
    
    @abstractmethod
    async def remove_by_id(self, id: str) -> bool:
        """
        Remove an entity by ID.
        
        Args:
            id: The ID of the entity to remove
            
        Returns:
            True if the entity was removed, False if it wasn't found
        """
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: The ID to check
            
        Returns:
            True if an entity with the given ID exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching the given filters.
        
        Args:
            filters: Filters to apply
            
        Returns:
            The number of entities matching the criteria
        """
        pass
    
    @abstractmethod
    async def load_relations(
        self, 
        entity: T, 
        relation_names: Optional[Union[bool, List[str]]] = True
    ) -> T:
        """
        Load relationships for an entity.
        
        Args:
            entity: The entity to load relationships for
            relation_names: Which relationships to load
                - True: Load all relationships
                - List[str]: Load only specified relationships
                
        Returns:
            The entity with relationships loaded
        """
        pass
    
    @abstractmethod
    async def load_relations_batch(
        self, 
        entities: List[T], 
        relation_names: Optional[Union[bool, List[str]]] = True
    ) -> List[T]:
        """
        Load relationships for multiple entities in a batch.
        
        This is more efficient than loading relationships individually
        as it can optimize database queries.
        
        Args:
            entities: The entities to load relationships for
            relation_names: Which relationships to load
                - True: Load all relationships
                - List[str]: Load only specified relationships
                
        Returns:
            The entities with relationships loaded
        """
        pass
    
    @abstractmethod
    async def batch_get(
        self,
        ids: List[str],
        load_relations: Optional[Union[bool, List[str]]] = None,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> List[T]:
        """
        Get multiple entities by ID in batch.
        
        This is more efficient than getting entities individually,
        especially for large numbers of entities.
        
        Args:
            ids: List of entity IDs to retrieve
            load_relations: Which relationships to load
            batch_size: Size of each batch
            parallel: Whether to execute in parallel
            
        Returns:
            List of entities found
        """
        pass
    
    @abstractmethod
    async def batch_add(
        self,
        entities: List[T],
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> List[T]:
        """
        Add multiple entities in batch.
        
        This is more efficient than adding entities individually,
        especially for large numbers of entities.
        
        Args:
            entities: List of entities to add
            batch_size: Size of each batch
            parallel: Whether to execute in parallel
            
        Returns:
            List of added entities
        """
        pass
    
    @abstractmethod
    async def batch_update(
        self,
        entities: List[T],
        fields: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> int:
        """
        Update multiple entities in batch.
        
        This is more efficient than updating entities individually,
        especially for large numbers of entities.
        
        Args:
            entities: List of entities to update
            fields: Specific fields to update (if None, update all fields)
            batch_size: Size of each batch
            parallel: Whether to execute in parallel
            
        Returns:
            Number of entities updated
        """
        pass
    
    @abstractmethod
    async def batch_remove(
        self,
        ids: List[str],
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> int:
        """
        Remove multiple entities by ID in batch.
        
        This is more efficient than removing entities individually,
        especially for large numbers of entities.
        
        Args:
            ids: List of entity IDs to remove
            batch_size: Size of each batch
            parallel: Whether to execute in parallel
            
        Returns:
            Number of entities removed
        """
        pass


class UnoDBRepository(Repository[T]):
    """
    Repository implementation using UnoDB.
    
    This implementation uses the UnoDB database layer to persist and retrieve
    domain entities.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        db_factory=None,
        use_batch_operations: bool = True,
        batch_size: int = 500,
    ):
        """
        Initialize the repository.
        
        Args:
            entity_type: The type of entity this repository manages
            db_factory: The database factory to use
            use_batch_operations: Whether to use batch operations for bulk operations
            batch_size: Default batch size for batch operations
        """
        self.entity_type = entity_type
        self.db_factory = db_factory
        self.use_batch_operations = use_batch_operations
        self.batch_size = batch_size
        
        # Lazy-loaded db
        self._db = None
        
        # Lazy-loaded batch operations
        self._batch_ops = None
        
        # Cache for relation metadata
        self._relation_metadata = None
    
    @property
    def db(self):
        """Get the database instance, creating it if necessary."""
        if self._db is None:
            from uno.database.db import UnoDBFactory
            from uno.model import UnoModel
            # Convert domain entity to UnoModel wrapper if needed
            model_type = getattr(self.entity_type, '__uno_model__', None)
            model_instance = model_type() if model_type else UnoModel()
            self._db = self.db_factory or UnoDBFactory(model_instance)
        return self._db
    
    @property
    def batch_ops(self):
        """Get the batch operations instance, creating it if necessary."""
        if self._batch_ops is None and self.use_batch_operations:
            from uno.queries.batch_operations import BatchOperations, BatchConfig
            
            # Get the model class
            model_class = getattr(self.entity_type, '__uno_model__', self.entity_type)
            
            # Create batch operations with default config
            self._batch_ops = BatchOperations(
                model_class=model_class,
                batch_config=BatchConfig(
                    batch_size=self.batch_size,
                    collect_metrics=True,
                ),
            )
        return self._batch_ops
    
    async def get(self, id: str, load_relations: Optional[Union[bool, List[str]]] = None) -> Optional[T]:
        """Get an entity by ID with optional relationship loading."""
        try:
            # The select_related parameter is used to generate JOIN clauses in the SQL query
            # True means all relations, False/None means no relations, list means specific relations
            result = await self.db.get(id=id, select_related=load_relations)
            if result:
                entity = self._convert_to_entity(result)
                
                # If relationships were requested but not auto-loaded via JOINs,
                # we need to manually load them
                if load_relations and not getattr(self.db, 'supports_joins', True):
                    entity = await self.load_relations(entity, load_relations)
                    
                return entity
            return None
        except Exception as e:
            from uno.database.db import NotFoundException
            if isinstance(e, NotFoundException):
                return None
            raise
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        load_relations: Optional[Union[bool, List[str]]] = None
    ) -> List[T]:
        """List entities with filtering, ordering, and pagination."""
        from uno.database.db import FilterParam
        
        # Convert filters to FilterParam objects if provided
        filter_params = None
        if filters:
            filter_params = []
            for key, value in filters.items():
                if isinstance(value, dict) and 'lookup' in value and 'val' in value:
                    filter_params.append(FilterParam(
                        label=key,
                        lookup=value['lookup'],
                        val=value['val']
                    ))
                else:
                    filter_params.append(FilterParam(
                        label=key,
                        lookup='eq',
                        val=value
                    ))
            
            # Add ordering parameters if provided
            if order_by:
                for field in order_by:
                    if field.startswith('-'):
                        filter_params.append(FilterParam(
                            label='order_by',
                            lookup='desc',
                            val=field[1:]
                        ))
                    else:
                        filter_params.append(FilterParam(
                            label='order_by',
                            lookup='asc',
                            val=field
                        ))
                        
            # Add pagination parameters if provided
            if limit is not None:
                filter_params.append(FilterParam(
                    label='limit',
                    lookup='eq',
                    val=limit
                ))
                
            if offset is not None:
                filter_params.append(FilterParam(
                    label='offset',
                    lookup='eq',
                    val=offset
                ))
        
        try:
            # Pass the select_related parameter to control which relationships to eager load
            results = await self.db.filter(filter_params, select_related=load_relations)
            entities = [self._convert_to_entity(result) for result in results]
            
            # If relationships were requested but not auto-loaded via JOINs,
            # we need to manually load them in batch
            if load_relations and not getattr(self.db, 'supports_joins', True) and entities:
                entities = await self.load_relations_batch(entities, load_relations)
                
            return entities
        except Exception as e:
            # Log error and return empty list
            import logging
            logging.getLogger(__name__).error(f"Error in repository list: {e}")
            return []
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        try:
            model_data = self._convert_to_model_data(entity)
            result, created = await self.db.create(model_data)
            if not created:
                raise DomainException("Failed to create entity", "CREATE_FAILED")
            return self._convert_to_entity(result)
        except Exception as e:
            from uno.database.db import UniqueViolationError
            if isinstance(e, UniqueViolationError):
                raise DomainException("Entity already exists", "ALREADY_EXISTS")
            raise DomainException(f"Error creating entity: {str(e)}", "CREATE_ERROR")
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            # Ensure entity exists before updating
            if not await self.exists(entity.id):
                raise DomainException(f"Entity with ID {entity.id} not found", "NOT_FOUND")
            
            model_data = self._convert_to_model_data(entity)
            result = await self.db.update(model_data)
            return self._convert_to_entity(result)
        except Exception as e:
            from uno.database.db import UniqueViolationError, NotFoundException
            if isinstance(e, UniqueViolationError):
                raise DomainException("Unique constraint violation", "CONSTRAINT_VIOLATED")
            if isinstance(e, NotFoundException):
                raise DomainException(f"Entity with ID {entity.id} not found", "NOT_FOUND")
            raise DomainException(f"Error updating entity: {str(e)}", "UPDATE_ERROR")
    
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        await self.remove_by_id(entity.id)
    
    async def remove_by_id(self, id: str) -> bool:
        """Remove an entity by ID."""
        try:
            result = await self.db.delete(id=id)
            return result
        except Exception as e:
            # If entity doesn't exist, return False rather than raising an exception
            from uno.database.db import NotFoundException
            if isinstance(e, NotFoundException):
                return False
            raise DomainException(f"Error removing entity: {str(e)}", "DELETE_ERROR")
    
    async def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        try:
            # Try to get the entity - if it exists, return True
            result = await self.db.get(id=id)
            return result is not None
        except Exception as e:
            from uno.database.db import NotFoundException
            if isinstance(e, NotFoundException):
                return False
            # For other errors, propagate the exception
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        from uno.database.db import FilterParam
        
        # Convert filters to FilterParam objects if provided
        filter_params = None
        if filters:
            filter_params = []
            for key, value in filters.items():
                if isinstance(value, dict) and 'lookup' in value and 'val' in value:
                    filter_params.append(FilterParam(
                        label=key,
                        lookup=value['lookup'],
                        val=value['val']
                    ))
                else:
                    filter_params.append(FilterParam(
                        label=key,
                        lookup='eq',
                        val=value
                    ))
        
        try:
            # Use count method directly if available, otherwise fall back to list
            if hasattr(self.db, 'count'):
                return await self.db.count(filter_params)
            else:
                # Use list method with a limit of 0 to just get count
                entities = await self.list(filters=filters, limit=0)
                return len(entities)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in repository count: {e}")
            return 0
    
    async def load_relations(
        self, 
        entity: T, 
        relation_names: Optional[Union[bool, List[str]]] = True
    ) -> T:
        """Load relationships for an entity."""
        if not entity:
            return entity
            
        # Handle case where no relationships are requested
        if relation_names is None or relation_names is False:
            return entity
            
        # Get relationship metadata if we haven't already
        if self._relation_metadata is None:
            self._relation_metadata = await self._get_relationship_metadata()
            
        # If no metadata is available, return the entity unchanged
        if not self._relation_metadata:
            return entity
            
        # Determine which relationships to load
        to_load = self._relation_metadata.keys()
        if isinstance(relation_names, list):
            to_load = [r for r in relation_names if r in self._relation_metadata]
            
        # Load each relationship
        for relation_name in to_load:
            entity = await self._load_relationship(entity, relation_name)
            
        return entity
    
    async def load_relations_batch(
        self, 
        entities: List[T], 
        relation_names: Optional[Union[bool, List[str]]] = True
    ) -> List[T]:
        """Load relationships for multiple entities in a batch."""
        if not entities:
            return entities
            
        # Handle case where no relationships are requested
        if relation_names is None or relation_names is False:
            return entities
            
        # Get relationship metadata if we haven't already
        if self._relation_metadata is None:
            self._relation_metadata = await self._get_relationship_metadata()
            
        # If no metadata is available, return the entities unchanged
        if not self._relation_metadata:
            return entities
            
        # Determine which relationships to load
        to_load = self._relation_metadata.keys()
        if isinstance(relation_names, list):
            to_load = [r for r in relation_names if r in self._relation_metadata]
            
        # Load each relationship for all entities
        for relation_name in to_load:
            entities = await self._load_relationship_batch(entities, relation_name)
            
        return entities
    
    async def batch_get(
        self,
        ids: List[str],
        load_relations: Optional[Union[bool, List[str]]] = None,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> List[T]:
        """
        Get multiple entities by ID in batch.
        
        This method is optimized for retrieving large numbers of entities 
        efficiently using batch operations.
        
        Args:
            ids: List of IDs to retrieve
            load_relations: Which relationships to load
            batch_size: Size of each batch (overrides default)
            parallel: Whether to execute in parallel
            
        Returns:
            List of entities
        """
        # If no IDs, return empty list
        if not ids:
            return []
        
        # If batch operations are disabled, fall back to individual gets
        if not self.use_batch_operations or self.batch_ops is None:
            # Fall back to individual gets
            entities = []
            for id in ids:
                entity = await self.get(id, load_relations=load_relations)
                if entity:
                    entities.append(entity)
            return entities
        
        # Use batch operations
        model_entities = await self.batch_ops.batch_get(
            id_values=ids,
            load_relations=load_relations,
            batch_size=batch_size or self.batch_size,
            parallel=parallel,
        )
        
        # Convert models to domain entities
        domain_entities = []
        for model in model_entities:
            domain_entity = self._convert_to_entity(model)
            domain_entities.append(domain_entity)
        
        return domain_entities
    
    async def batch_update(
        self,
        entities: List[T],
        fields: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> int:
        """
        Update multiple entities in batch.
        
        This method is optimized for updating large numbers of entities
        efficiently using batch operations.
        
        Args:
            entities: List of entities to update
            fields: Specific fields to update (if None, update all fields)
            batch_size: Size of each batch (overrides default)
            parallel: Whether to execute in parallel
            
        Returns:
            Number of entities updated
        """
        # If no entities, return 0
        if not entities:
            return 0
        
        # If batch operations are disabled, fall back to individual updates
        if not self.use_batch_operations or self.batch_ops is None:
            # Fall back to individual updates
            count = 0
            for entity in entities:
                try:
                    await self.update(entity)
                    count += 1
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error updating entity {entity.id}: {e}")
            return count
        
        # Convert entities to model data
        records = []
        for entity in entities:
            # Convert to model data
            model_data = self._convert_to_model_data(entity)
            
            # Filter fields if specified
            if fields:
                model_data = {k: v for k, v in model_data.items() if k in fields or k == 'id'}
            
            records.append(model_data)
        
        # Use batch operations
        updated = await self.batch_ops.batch_update(
            records=records,
            id_field='id',
            fields_to_update=fields,
            return_models=False,
            batch_size=batch_size or self.batch_size,
            parallel=parallel,
        )
        
        return updated
    
    async def batch_add(
        self,
        entities: List[T],
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> List[T]:
        """
        Add multiple entities in batch.
        
        This method is optimized for adding large numbers of entities
        efficiently using batch operations.
        
        Args:
            entities: List of entities to add
            batch_size: Size of each batch (overrides default)
            parallel: Whether to execute in parallel
            
        Returns:
            List of added entities
        """
        # If no entities, return empty list
        if not entities:
            return []
        
        # If batch operations are disabled, fall back to individual adds
        if not self.use_batch_operations or self.batch_ops is None:
            # Fall back to individual adds
            added_entities = []
            for entity in entities:
                try:
                    added_entity = await self.add(entity)
                    added_entities.append(added_entity)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error adding entity: {e}")
            return added_entities
        
        # Convert entities to model data
        records = []
        for entity in entities:
            model_data = self._convert_to_model_data(entity)
            records.append(model_data)
        
        # Use batch operations
        model_entities = await self.batch_ops.batch_insert(
            records=records,
            return_models=True,
            batch_size=batch_size or self.batch_size,
            parallel=parallel,
        )
        
        # Convert models to domain entities
        domain_entities = []
        for model in model_entities:
            domain_entity = self._convert_to_entity(model)
            domain_entities.append(domain_entity)
        
        return domain_entities
    
    async def batch_remove(
        self,
        ids: List[str],
        batch_size: Optional[int] = None,
        parallel: bool = False,
    ) -> int:
        """
        Remove multiple entities by ID in batch.
        
        This method is optimized for removing large numbers of entities
        efficiently using batch operations.
        
        Args:
            ids: List of IDs to remove
            batch_size: Size of each batch (overrides default)
            parallel: Whether to execute in parallel
            
        Returns:
            Number of entities removed
        """
        # If no IDs, return 0
        if not ids:
            return 0
        
        # If batch operations are disabled, fall back to individual removes
        if not self.use_batch_operations or self.batch_ops is None:
            # Fall back to individual removes
            count = 0
            for id in ids:
                try:
                    success = await self.remove_by_id(id)
                    if success:
                        count += 1
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error removing entity {id}: {e}")
            return count
        
        # Use batch operations
        removed = await self.batch_ops.batch_delete(
            id_values=ids,
            return_models=False,
            batch_size=batch_size or self.batch_size,
            parallel=parallel,
        )
        
        return removed
    
    async def _get_relationship_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about relationships for this entity type.
        
        Returns a dictionary mapping relationship names to their metadata:
        {
            'relation_name': {
                'field': 'field_name', 
                'target_type': TargetEntity, 
                'is_collection': bool,
                'foreign_key': 'fk_field'
            }
        }
        """
        from uno.model import UnoModel
        import inspect
        
        # Check if the entity type has relationships defined
        if not hasattr(self.entity_type, '__relationships__'):
            # Try to get from model if available
            model_type = getattr(self.entity_type, '__uno_model__', None)
            if model_type and hasattr(model_type, '__relationships__'):
                return model_type.__relationships__
                
            # Otherwise try to infer relationships from sqlalchemy model
            try:
                from sqlalchemy.orm import class_mapper
                from sqlalchemy.orm.properties import RelationshipProperty
                
                if hasattr(self.entity_type, '__table__'):
                    # Get the mapper for this entity type
                    mapper = class_mapper(self.entity_type)
                    
                    # Get relationships from mapper
                    rel_metadata = {}
                    for rel in mapper.relationships:
                        rel_metadata[rel.key] = {
                            'field': rel.key,
                            'target_type': rel.mapper.class_,
                            'is_collection': rel.uselist,
                            'foreign_key': list(rel.local_columns)[0].name if rel.local_columns else None
                        }
                    return rel_metadata
            except Exception:
                # If we can't get from sqlalchemy, try to infer from pydantic model
                pass
                
            # If all else fails, try to infer from field types
            rel_metadata = {}
            for name, field in inspect.get_annotations(self.entity_type).items():
                # Skip private fields
                if name.startswith('_'):
                    continue
                    
                # Check if field is a list of entities
                origin = getattr(field, '__origin__', None)
                args = getattr(field, '__args__', [])
                if origin is list and args and issubclass(args[0], Entity):
                    rel_metadata[name] = {
                        'field': name,
                        'target_type': args[0],
                        'is_collection': True,
                        'foreign_key': f'{self.entity_type.__name__.lower()}_id'
                    }
                # Check if field is a single entity
                elif inspect.isclass(field) and issubclass(field, Entity):
                    rel_metadata[name] = {
                        'field': name,
                        'target_type': field,
                        'is_collection': False,
                        'foreign_key': f'{name}_id'
                    }
            
            return rel_metadata
            
        return self.entity_type.__relationships__
    
    async def _load_relationship(self, entity: T, relation_name: str) -> T:
        """Load a specific relationship for an entity."""
        # Get relationship metadata
        rel_meta = self._relation_metadata.get(relation_name)
        if not rel_meta:
            return entity
            
        try:
            # Handle to-one relationships (foreign key in this entity)
            if not rel_meta['is_collection'] and hasattr(entity, f"{rel_meta['field']}_id"):
                fk_value = getattr(entity, f"{rel_meta['field']}_id")
                if fk_value:
                    # Create a repository for the target type
                    target_repo = UnoDBRepository(rel_meta['target_type'], self.db_factory)
                    
                    # Load the related entity
                    related_entity = await target_repo.get(fk_value)
                    
                    # Set the relationship
                    setattr(entity, rel_meta['field'], related_entity)
            
            # Handle to-many relationships (foreign key in related entity)
            elif rel_meta['is_collection']:
                # Create a repository for the target type
                target_repo = UnoDBRepository(rel_meta['target_type'], self.db_factory)
                
                # Load the related entities
                fk_field = rel_meta.get('foreign_key') or f"{self.entity_type.__name__.lower()}_id"
                related_entities = await target_repo.list(filters={fk_field: entity.id})
                
                # Set the relationship
                setattr(entity, rel_meta['field'], related_entities)
                
        except Exception as e:
            # Log error but don't fail the whole operation
            import logging
            logging.getLogger(__name__).warning(
                f"Error loading relationship '{relation_name}' for entity {entity.id}: {e}"
            )
            
        return entity
    
    async def _load_relationship_batch(self, entities: List[T], relation_name: str) -> List[T]:
        """Load a specific relationship for multiple entities in a batch."""
        # Get relationship metadata
        rel_meta = self._relation_metadata.get(relation_name)
        if not rel_meta:
            return entities
            
        try:
            # Handle to-one relationships (foreign key in this entity)
            if not rel_meta['is_collection']:
                # Collect all foreign keys
                fk_field = f"{rel_meta['field']}_id"
                fk_values = []
                for entity in entities:
                    if hasattr(entity, fk_field) and getattr(entity, fk_field):
                        fk_values.append(getattr(entity, fk_field))
                
                if not fk_values:
                    return entities
                    
                # Create a repository for the target type
                target_repo = UnoDBRepository(rel_meta['target_type'], self.db_factory)
                
                # Load all related entities in one query
                related_entities = await target_repo.list(filters={'id': {'lookup': 'in', 'val': fk_values}})
                
                # Create a lookup map for efficiency
                related_map = {entity.id: entity for entity in related_entities}
                
                # Set the relationships
                for entity in entities:
                    if hasattr(entity, fk_field) and getattr(entity, fk_field):
                        fk_value = getattr(entity, fk_field)
                        if fk_value in related_map:
                            setattr(entity, rel_meta['field'], related_map[fk_value])
            
            # Handle to-many relationships (foreign key in related entity)
            else:
                # Collect all entity IDs
                entity_ids = [entity.id for entity in entities]
                
                # Create a repository for the target type
                target_repo = UnoDBRepository(rel_meta['target_type'], self.db_factory)
                
                # Load all related entities in one query
                fk_field = rel_meta.get('foreign_key') or f"{self.entity_type.__name__.lower()}_id"
                related_entities = await target_repo.list(filters={fk_field: {'lookup': 'in', 'val': entity_ids}})
                
                # Group by parent entity ID
                relations_map = {}
                for related in related_entities:
                    parent_id = getattr(related, fk_field)
                    if parent_id not in relations_map:
                        relations_map[parent_id] = []
                    relations_map[parent_id].append(related)
                
                # Set the relationships
                for entity in entities:
                    setattr(entity, rel_meta['field'], relations_map.get(entity.id, []))
                
        except Exception as e:
            # Log error but don't fail the whole operation
            import logging
            logging.getLogger(__name__).warning(
                f"Error batch loading relationship '{relation_name}': {e}"
            )
            
        return entities
    
    def _convert_to_entity(self, data: Dict[str, Any]) -> T:
        """Convert database result to a domain entity."""
        if isinstance(data, dict):
            # Remove any database-specific fields not needed in domain entity
            # Convert to appropriate types where needed
            return self.entity_type(**data)
        else:
            # Handle case where data is already a model or mapping
            data_dict = data._mapping if hasattr(data, '_mapping') else data
            return self.entity_type(**dict(data_dict))
    
    def _convert_to_model_data(self, entity: T) -> Dict[str, Any]:
        """Convert domain entity to data for database model."""
        # Get model data excluding private fields and entity relationships
        exclude_fields = {"_events", "_child_entities"}
        
        # Add relationship fields to exclude list
        if self._relation_metadata:
            exclude_fields.update(self._relation_metadata.keys())
        
        # Use model_dump if available, otherwise fallback to dict conversion
        if hasattr(entity, 'model_dump'):
            model_data = entity.model_dump(exclude=exclude_fields)
        else:
            model_data = vars(entity).copy()
            for field in exclude_fields:
                if field in model_data:
                    del model_data[field]
        
        # Process any special conversions needed for the database
        # For example, converting datetime objects to strings
        return model_data


from uno.domain.core import DomainException


# Utility decorator for lazy loading relationships
def lazy_relationship(relation_name: str):
    """
    Decorator for creating lazy-loaded relationships.
    
    When the decorated property is accessed, it will load the relationship
    if it hasn't been loaded already.
    
    Args:
        relation_name: The name of the relationship to load
        
    Returns:
        A property that lazy-loads the relationship
    """
    def decorator(func):
        @property
        def wrapper(self):
            # Check if the relationship has been loaded
            attr_name = f"_{func.__name__}"
            if not hasattr(self, attr_name) or getattr(self, attr_name) is None:
                # We need to load it, but we can't do async in a property
                # So we return a proxy that will load it when needed
                return LazyRelationshipProxy(self, relation_name, attr_name)
            
            # Return the cached relationship
            return getattr(self, attr_name)
        
        return wrapper
    
    return decorator


class LazyRelationshipProxy:
    """
    Proxy for lazy-loaded relationships.
    
    This class allows lazy loading of relationships even though
    properties can't use async functions.
    """
    
    def __init__(self, entity, relation_name, attr_name):
        """
        Initialize the proxy.
        
        Args:
            entity: The entity that owns the relationship
            relation_name: The name of the relationship to load
            attr_name: The attribute name to store the loaded relationship in
        """
        self.entity = entity
        self.relation_name = relation_name
        self.attr_name = attr_name
        self._loaded = False
        
    def __str__(self):
        return f"<LazyRelationship '{self.relation_name}' for {self.entity.__class__.__name__} {self.entity.id}>"
        
    def __repr__(self):
        return self.__str__()
    
    async def load(self):
        """Load the relationship if not already loaded."""
        if self._loaded:
            return
            
        # Create a repository for the entity type
        from uno.domain.repository import UnoDBRepository
        repo = UnoDBRepository(self.entity.__class__)
        
        # Load the relationship
        loaded_entity = await repo.load_relations(self.entity, [self.relation_name])
        
        # Update the entity with the loaded relationship
        setattr(self.entity, self.attr_name, getattr(loaded_entity, self.relation_name, None))
        self._loaded = True


# Helper for relationship definitions
def define_relationship(field, target_type, is_collection=False, foreign_key=None):
    """
    Helper function to define a relationship.
    
    Args:
        field: The field name on the entity
        target_type: The type of the related entity
        is_collection: Whether this is a to-many relationship
        foreign_key: The name of the foreign key field
        
    Returns:
        A dictionary with relationship metadata
    """
    return {
        'field': field,
        'target_type': target_type,
        'is_collection': is_collection,
        'foreign_key': foreign_key
    }