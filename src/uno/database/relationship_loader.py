"""
Relationship loading utilities for optimized database queries.

This module provides utilities for loading relationships between entities
in an efficient manner, supporting selective loading to improve performance.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast

from sqlalchemy import select, and_, or_, not_, join, outerjoin
from sqlalchemy.orm import joinedload, selectinload, lazyload, load_only
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.enhanced_session import enhanced_async_session
from uno.errors import UnoError


T = TypeVar('T')


class RelationshipLoader:
    """
    Utility for loading entity relationships efficiently.
    
    This class provides methods to selectively load relationships between entities,
    optimizing database queries to reduce unnecessary data transfer and processing.
    """
    
    def __init__(self, model_class: Type[Any], logger=None):
        """
        Initialize the relationship loader.
        
        Args:
            model_class: The SQLAlchemy model class this loader operates on
            logger: Optional logger for diagnostic output
        """
        self.model_class = model_class
        self.logger = logger
        
        # Get relationship metadata
        self.relationships = self._get_relationships()
        
    def _get_relationships(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the relationship metadata for the model.
        
        Returns:
            Dictionary mapping relationship names to their metadata
        """
        # Try to get explicitly defined relationships
        if hasattr(self.model_class, '__relationships__'):
            return getattr(self.model_class, '__relationships__')
        
        # Try to get from SQLAlchemy metadata
        relationships = {}
        
        try:
            from sqlalchemy.orm import class_mapper
            from sqlalchemy.orm.properties import RelationshipProperty
            
            mapper = class_mapper(self.model_class)
            
            for rel in mapper.relationships:
                relationships[rel.key] = {
                    'field': rel.key,
                    'target_type': rel.mapper.class_,
                    'is_collection': rel.uselist,
                    'foreign_key': list(rel.local_columns)[0].name if rel.local_columns else None
                }
        except Exception as e:
            # Unable to get relationships from SQLAlchemy
            if self.logger:
                self.logger.debug(f"Unable to get relationships from SQLAlchemy: {e}")
        
        return relationships
    
    def apply_relationship_options(
        self, 
        query,
        load_relations: Optional[Union[bool, List[str]]],
        strategy: str = 'select'
    ):
        """
        Apply relationship loading options to a SQLAlchemy query.
        
        Args:
            query: The base query to modify
            load_relations: Which relationships to load
                - None/False: Load no relationships
                - True: Load all relationships
                - List[str]: Load only specified relationships
            strategy: The loading strategy to use
                - 'select': Use selectinload (good for many-to-one and one-to-many)
                - 'joined': Use joinedload (good for one-to-one)
                - 'lazy': Use lazy loading (load on access)
                
        Returns:
            Modified query with relationship loading options applied
        """
        # Early return if no relationships to load
        if not load_relations or not self.relationships:
            return query
        
        # Determine which relationships to load
        to_load = list(self.relationships.keys())
        if isinstance(load_relations, list):
            to_load = [r for r in load_relations if r in self.relationships]
        
        # Apply appropriate loading strategy
        for rel_name in to_load:
            rel_meta = self.relationships.get(rel_name)
            if not rel_meta:
                continue
            
            # Get the relationship attribute
            if not hasattr(self.model_class, rel_name):
                continue
                
            relationship = getattr(self.model_class, rel_name)
            
            # Apply the selected loading strategy
            if strategy == 'select':
                query = query.options(selectinload(relationship))
            elif strategy == 'joined':
                query = query.options(joinedload(relationship))
            elif strategy == 'lazy':
                query = query.options(lazyload(relationship))
        
        return query
    
    async def load_relationships(
        self,
        entity: Any,
        load_relations: Optional[Union[bool, List[str]]],
        session: Optional[AsyncSession] = None
    ) -> Any:
        """
        Load relationships for a single entity.
        
        Args:
            entity: The entity to load relationships for
            load_relations: Which relationships to load
            session: Optional database session to use
                
        Returns:
            Entity with relationships loaded
        """
        # Early return if no entity or no relationships to load
        if not entity or not load_relations or not self.relationships:
            return entity
        
        # Determine which relationships to load
        to_load = list(self.relationships.keys())
        if isinstance(load_relations, list):
            to_load = [r for r in load_relations if r in self.relationships]
        
        # Create a session if not provided
        if session is None:
            async with enhanced_async_session() as session:
                return await self._load_entity_relationships(entity, to_load, session)
        else:
            return await self._load_entity_relationships(entity, to_load, session)
    
    async def load_relationships_batch(
        self,
        entities: List[Any],
        load_relations: Optional[Union[bool, List[str]]],
        session: Optional[AsyncSession] = None
    ) -> List[Any]:
        """
        Load relationships for multiple entities in batch.
        
        Args:
            entities: The entities to load relationships for
            load_relations: Which relationships to load
            session: Optional database session to use
                
        Returns:
            Entities with relationships loaded
        """
        # Early return if no entities or no relationships to load
        if not entities or not load_relations or not self.relationships:
            return entities
        
        # Determine which relationships to load
        to_load = list(self.relationships.keys())
        if isinstance(load_relations, list):
            to_load = [r for r in load_relations if r in self.relationships]
        
        # Create a session if not provided
        if session is None:
            async with enhanced_async_session() as session:
                return await self._load_batch_relationships(entities, to_load, session)
        else:
            return await self._load_batch_relationships(entities, to_load, session)
    
    async def _load_entity_relationships(
        self,
        entity: Any,
        relationship_names: List[str],
        session: AsyncSession
    ) -> Any:
        """Load relationships for a single entity with an active session."""
        # Work through each relationship
        for rel_name in relationship_names:
            rel_meta = self.relationships.get(rel_name)
            if not rel_meta:
                continue
            
            try:
                # Handle to-one relationships (foreign key in this entity)
                if not rel_meta['is_collection']:
                    # Get the foreign key value
                    fk_field = f"{rel_name}_id"
                    if hasattr(entity, fk_field):
                        fk_value = getattr(entity, fk_field)
                        if fk_value:
                            # Get the related entity
                            target_class = rel_meta['target_type']
                            query = select(target_class).where(getattr(target_class, 'id') == fk_value)
                            result = await session.execute(query)
                            related_entity = result.scalar_one_or_none()
                            
                            # Set the relationship
                            if related_entity:
                                setattr(entity, rel_name, related_entity)
                
                # Handle to-many relationships (foreign key in related entity)
                else:
                    # Get foreign key field name
                    target_class = rel_meta['target_type']
                    fk_field = rel_meta.get('foreign_key') or f"{self.model_class.__name__.lower()}_id"
                    
                    # Get related entities
                    if hasattr(target_class, fk_field):
                        query = select(target_class).where(getattr(target_class, fk_field) == entity.id)
                        result = await session.execute(query)
                        related_entities = result.scalars().all()
                        
                        # Set the relationship
                        setattr(entity, rel_name, related_entities)
            
            except Exception as e:
                # Log error but continue with other relationships
                if self.logger:
                    self.logger.warning(
                        f"Error loading relationship '{rel_name}' for entity {entity.id}: {e}"
                    )
        
        return entity
    
    async def _load_batch_relationships(
        self,
        entities: List[Any],
        relationship_names: List[str],
        session: AsyncSession
    ) -> List[Any]:
        """Load relationships for multiple entities with an active session."""
        # Handle each relationship
        for rel_name in relationship_names:
            rel_meta = self.relationships.get(rel_name)
            if not rel_meta:
                continue
            
            try:
                # Handle to-one relationships (foreign key in this entity)
                if not rel_meta['is_collection']:
                    # Collect all foreign keys
                    fk_field = f"{rel_name}_id"
                    fk_values = set()
                    
                    for entity in entities:
                        if hasattr(entity, fk_field):
                            fk_value = getattr(entity, fk_field)
                            if fk_value:
                                fk_values.add(fk_value)
                    
                    if not fk_values:
                        continue
                    
                    # Get all related entities in one query
                    target_class = rel_meta['target_type']
                    query = select(target_class).where(getattr(target_class, 'id').in_(fk_values))
                    result = await session.execute(query)
                    related_entities = result.scalars().all()
                    
                    # Create lookup map for efficiency
                    related_map = {entity.id: entity for entity in related_entities}
                    
                    # Set relationships
                    for entity in entities:
                        if hasattr(entity, fk_field):
                            fk_value = getattr(entity, fk_field)
                            if fk_value and fk_value in related_map:
                                setattr(entity, rel_name, related_map[fk_value])
                
                # Handle to-many relationships (foreign key in related entity)
                else:
                    # Collect all entity IDs
                    entity_ids = [entity.id for entity in entities]
                    
                    # Get foreign key field name
                    target_class = rel_meta['target_type']
                    fk_field = rel_meta.get('foreign_key') or f"{self.model_class.__name__.lower()}_id"
                    
                    # Get all related entities in one query
                    if hasattr(target_class, fk_field):
                        query = select(target_class).where(getattr(target_class, fk_field).in_(entity_ids))
                        result = await session.execute(query)
                        related_entities = result.scalars().all()
                        
                        # Group by parent entity ID
                        relations_map = {}
                        for related in related_entities:
                            parent_id = getattr(related, fk_field)
                            if parent_id not in relations_map:
                                relations_map[parent_id] = []
                            relations_map[parent_id].append(related)
                        
                        # Set relationships
                        for entity in entities:
                            setattr(entity, rel_name, relations_map.get(entity.id, []))
            
            except Exception as e:
                # Log error but continue with other relationships
                if self.logger:
                    self.logger.warning(f"Error batch loading relationship '{rel_name}': {e}")
        
        return entities


# Decorator for lazy-loading relationships
def lazy_load(relation_name: str):
    """
    Decorator for lazy loading of relationships.
    
    When the decorated property is accessed, it will automatically load
    the relationship if it hasn't been loaded yet. This allows for more
    efficient loading patterns when not all relationships are needed.
    
    Args:
        relation_name: The name of the relationship to load
        
    Returns:
        Property decorator that implements lazy loading
    """
    def decorator(func):
        attr_name = f"_{func.__name__}"
        
        def getter(self):
            # If we've already loaded this relationship, return the cached value
            if hasattr(self, attr_name) and getattr(self, attr_name) is not None:
                return getattr(self, attr_name)
            
            # Otherwise return a proxy that will load it when needed
            return LazyRelationship(self, relation_name, attr_name)
            
        def setter(self, value):
            # Store the relationship value
            setattr(self, attr_name, value)
            
        # Create property with getter and setter
        return property(getter, setter)
    
    return decorator


class LazyRelationship:
    """
    Proxy for lazy-loaded relationships.
    
    This class provides a proxy object that loads a relationship on demand.
    It allows for more efficient loading patterns when not all relationships
    are needed.
    """
    
    def __init__(self, entity, relation_name, attr_name):
        """
        Initialize the lazy relationship.
        
        Args:
            entity: The entity that owns the relationship
            relation_name: The name of the relationship to load
            attr_name: The attribute name to store the loaded relationship
        """
        self.entity = entity
        self.relation_name = relation_name
        self.attr_name = attr_name
        self._loaded = False
        self._loading = False
        self._value = None
        
    def __repr__(self):
        """String representation of the lazy relationship."""
        if self._loaded:
            return f"<LazyRelationship '{self.relation_name}' (loaded): {self._value}>"
        else:
            return f"<LazyRelationship '{self.relation_name}' for {self.entity.__class__.__name__} {getattr(self.entity, 'id', 'unknown')}>"
    
    async def load(self):
        """
        Load the relationship if not already loaded.
        
        Returns:
            The loaded relationship value
        """
        # Avoid loading multiple times or recursion
        if self._loaded or self._loading:
            return self._value
            
        self._loading = True
        
        try:
            # Create loader and session
            loader = RelationshipLoader(self.entity.__class__)
            
            # Load the relationship
            async with enhanced_async_session() as session:
                loaded_entity = await loader._load_entity_relationships(
                    self.entity, 
                    [self.relation_name],
                    session
                )
                
                # Get the loaded relationship value
                self._value = getattr(loaded_entity, self.relation_name)
                
                # Update the entity
                setattr(self.entity, self.attr_name, self._value)
                
                # Mark as loaded
                self._loaded = True
                
                return self._value
        finally:
            self._loading = False
    
    def __await__(self):
        """Support for awaiting the lazy relationship."""
        return self.load().__await__()