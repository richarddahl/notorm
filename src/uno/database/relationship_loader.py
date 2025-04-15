"""
Relationship loading utilities for optimized database queries.

This module provides utilities for loading relationships between entities
in an efficient manner, supporting selective loading to improve performance.
Features include:
- Selective relationship loading
- Batch loading of relationships
- Lazy loading through proxies
- Relationship caching for frequently accessed associations
- Optimized query generation
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast, Callable
import asyncio
import functools
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field

from sqlalchemy import select, and_, or_, not_, join, outerjoin
from sqlalchemy.orm import joinedload, selectinload, lazyload, load_only
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.enhanced_session import enhanced_async_session
from uno.core.errors import ObjectNotFoundError, OperationFailedError
from uno.database.errors import (
    DatabaseErrorCode,
    DatabaseResourceNotFoundError,
    DatabaseOperationalError
)
from uno.database.query_cache import QueryCache, cached, CachedResult
from uno.core.errors.result import Result as OpResult, Success, Failure


T = TypeVar('T')


@dataclass
class RelationshipCacheConfig:
    """
    Configuration for relationship caching.
    
    Controls the behavior of the relationship cache system.
    """
    
    # Cache behavior
    enabled: bool = True
    default_ttl: float = 300.0  # 5 minutes
    
    # Cache sizing
    max_entries: int = 5000
    
    # Cache strategies
    cache_to_one: bool = True  # Cache to-one relationships (foreign key in this entity)
    cache_to_many: bool = True  # Cache to-many relationships (foreign key in related entity)
    
    # Cache invalidation
    auto_invalidate: bool = True
    
    # Entity-specific TTLs
    entity_ttls: Dict[str, float] = field(default_factory=dict)
    
    # Relationship-specific TTLs
    relationship_ttls: Dict[str, float] = field(default_factory=dict)
    
    def get_ttl_for_entity(self, entity_class_name: str) -> float:
        """Get the TTL for a specific entity type."""
        return self.entity_ttls.get(entity_class_name, self.default_ttl)
    
    def get_ttl_for_relationship(self, entity_class_name: str, relationship_name: str) -> float:
        """Get the TTL for a specific relationship."""
        key = f"{entity_class_name}.{relationship_name}"
        return self.relationship_ttls.get(key, self.get_ttl_for_entity(entity_class_name))


class RelationshipCache:
    """
    Cache for entity relationships.
    
    Provides caching for frequently accessed relationships to improve performance
    and reduce database load.
    """
    
    def __init__(
        self,
        config: Optional[RelationshipCacheConfig] = None,
        query_cache: Optional[QueryCache] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the relationship cache.
        
        Args:
            config: Optional configuration for the cache
            query_cache: Optional query cache to use for storage
            logger: Optional logger for diagnostic output
        """
        self.config = config or RelationshipCacheConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # Use the provided query cache or create a new one
        self.query_cache = query_cache or QueryCache()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.stores = 0
        self.invalidations = 0
    
    async def get_to_one(
        self,
        parent_entity: Any,
        relationship_name: str,
        target_class: Type[Any],
        fk_value: Any,
    ) -> OpResult[Any]:
        """
        Get a to-one relationship from the cache.
        
        Args:
            parent_entity: The entity that owns the relationship
            relationship_name: The name of the relationship
            target_class: The class of the related entity
            fk_value: The foreign key value
            
        Returns:
            Result containing the cached entity or an error
        """
        if not self.config.enabled or not self.config.cache_to_one:
            return Failure("Cache disabled for to-one relationships")
        
        # Generate cache key
        cache_key = self._generate_to_one_key(
            target_class.__name__,
            fk_value,
        )
        
        # Try to get from cache
        result = await self.query_cache.get(cache_key)
        
        if result.is_success:
            self.hits += 1
            if self.logger and self.hits % 100 == 0:
                self.logger.debug(
                    f"Relationship cache stats - hits: {self.hits}, "
                    f"misses: {self.misses}, stores: {self.stores}"
                )
            return Success(result.value)
        
        self.misses += 1
        return Failure("Cache miss")
    
    async def store_to_one(
        self,
        parent_entity: Any,
        relationship_name: str,
        related_entity: Any,
    ) -> None:
        """
        Store a to-one relationship in the cache.
        
        Args:
            parent_entity: The entity that owns the relationship
            relationship_name: The name of the relationship
            related_entity: The related entity to cache
        """
        if not self.config.enabled or not self.config.cache_to_one:
            return
        
        # Generate cache key
        cache_key = self._generate_to_one_key(
            related_entity.__class__.__name__,
            related_entity.id,
        )
        
        # Calculate TTL
        ttl = self.config.get_ttl_for_relationship(
            parent_entity.__class__.__name__,
            relationship_name,
        )
        
        # Store in cache
        await self.query_cache.set(
            cache_key,
            related_entity,
            ttl=ttl,
            dependencies=[related_entity.__class__.__tablename__],
        )
        
        self.stores += 1
    
    async def get_to_many(
        self,
        parent_entity: Any,
        relationship_name: str,
        target_class: Type[Any],
    ) -> OpResult[List[Any]]:
        """
        Get a to-many relationship from the cache.
        
        Args:
            parent_entity: The entity that owns the relationship
            relationship_name: The name of the relationship
            target_class: The class of the related entities
            
        Returns:
            Result containing the cached entities or an error
        """
        if not self.config.enabled or not self.config.cache_to_many:
            return Failure("Cache disabled for to-many relationships")
        
        # Generate cache key
        cache_key = self._generate_to_many_key(
            parent_entity.__class__.__name__,
            parent_entity.id,
            relationship_name,
        )
        
        # Try to get from cache
        result = await self.query_cache.get(cache_key)
        
        if result.is_success:
            self.hits += 1
            if self.logger and self.hits % 100 == 0:
                self.logger.debug(
                    f"Relationship cache stats - hits: {self.hits}, "
                    f"misses: {self.misses}, stores: {self.stores}"
                )
            return Success(result.value)
        
        self.misses += 1
        return Failure("Cache miss")
    
    async def store_to_many(
        self,
        parent_entity: Any,
        relationship_name: str,
        related_entities: List[Any],
    ) -> None:
        """
        Store a to-many relationship in the cache.
        
        Args:
            parent_entity: The entity that owns the relationship
            relationship_name: The name of the relationship
            related_entities: The related entities to cache
        """
        if not self.config.enabled or not self.config.cache_to_many:
            return
        
        # Skip if no related entities (don't cache empty lists)
        if not related_entities:
            return
        
        # Generate cache key
        cache_key = self._generate_to_many_key(
            parent_entity.__class__.__name__,
            parent_entity.id,
            relationship_name,
        )
        
        # Calculate TTL
        ttl = self.config.get_ttl_for_relationship(
            parent_entity.__class__.__name__,
            relationship_name,
        )
        
        # Get the table name of the related entities
        table_name = related_entities[0].__class__.__tablename__
        
        # Store in cache
        await self.query_cache.set(
            cache_key,
            related_entities,
            ttl=ttl,
            dependencies=[table_name],
        )
        
        self.stores += 1
    
    async def invalidate_entity(self, entity: Any) -> None:
        """
        Invalidate all cache entries for an entity.
        
        Args:
            entity: The entity to invalidate
        """
        if not self.config.enabled:
            return
        
        # Invalidate by table name
        await self.query_cache.invalidate_by_table(entity.__class__.__tablename__)
        
        # Invalidate specific to-one relationships
        cache_key = self._generate_to_one_key(
            entity.__class__.__name__,
            entity.id,
        )
        await self.query_cache.invalidate(cache_key)
        
        # We don't invalidate to-many relationships here because
        # they are already covered by the table invalidation
        
        self.invalidations += 1
    
    def _generate_to_one_key(self, target_class_name: str, fk_value: Any) -> str:
        """Generate a cache key for a to-one relationship."""
        key = f"rel:one:{target_class_name}:{fk_value}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()
    
    def _generate_to_many_key(
        self,
        parent_class_name: str,
        parent_id: Any,
        relationship_name: str,
    ) -> str:
        """Generate a cache key for a to-many relationship."""
        key = f"rel:many:{parent_class_name}:{parent_id}:{relationship_name}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()


class RelationshipLoader:
    """
    Utility for loading entity relationships efficiently.
    
    This class provides methods to selectively load relationships between entities,
    optimizing database queries to reduce unnecessary data transfer and processing.
    Features include:
    - Selective relationship loading with different strategies
    - Batch loading of relationships for improved performance
    - Lazy loading through proxies for on-demand access
    - Relationship caching for frequently accessed associations
    - Cache invalidation when entities are modified
    - Optimized query generation with minimal data transfer
    """
    
    def __init__(
        self, 
        model_class: Type[Any], 
        logger=None,
        cache: Optional[RelationshipCache] = None,
        cache_config: Optional[RelationshipCacheConfig] = None,
    ):
        """
        Initialize the relationship loader.
        
        Args:
            model_class: The SQLAlchemy model class this loader operates on
            logger: Optional logger for diagnostic output
            cache: Optional relationship cache to use
            cache_config: Optional cache configuration
        """
        self.model_class = model_class
        self.logger = logger or logging.getLogger(__name__)
        
        # Get relationship metadata
        self.relationships = self._get_relationships()
        
        # Initialize cache
        self.cache = cache or RelationshipCache(
            config=cache_config, 
            logger=self.logger
        )
        
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
    
    async def invalidate_relationships(self, entity: Any) -> None:
        """
        Invalidate all cached relationships for an entity.
        
        This should be called whenever an entity is updated or deleted to ensure
        that any cached relationships involving this entity are invalidated.
        
        Args:
            entity: The entity whose relationships should be invalidated
        """
        if not entity:
            return
        
        # Invalidate in cache
        await self.cache.invalidate_entity(entity)
        
        # If the entity has known relationships, invalidate those too
        for rel_name, rel_meta in self.relationships.items():
            if not rel_meta.get('is_collection', False):
                # For to-one relationships, check if we have a related entity
                if hasattr(entity, rel_name) and getattr(entity, rel_name) is not None:
                    related_entity = getattr(entity, rel_name)
                    await self.cache.invalidate_entity(related_entity)
    
    @staticmethod
    async def invalidate_entity_type(entity_class: Type[Any]) -> None:
        """
        Invalidate all cached relationships for an entity type.
        
        This should be called when entities of a certain type are bulk updated or
        when the underlying table structure changes.
        
        Args:
            entity_class: The entity class whose cached relationships should be invalidated
        """
        # Create a loader for this entity type
        loader = RelationshipLoader(entity_class)
        
        # Build a pattern for invalidation based on table name
        if hasattr(entity_class, '__tablename__'):
            table_name = entity_class.__tablename__
            # Invalidate by table name in the query cache
            await loader.cache.query_cache.invalidate_by_table(table_name)
    
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
                            # Get the target class
                            target_class = rel_meta['target_type']
                            
                            # Try to get from cache first
                            cache_result = await self.cache.get_to_one(
                                entity,
                                rel_name,
                                target_class,
                                fk_value
                            )
                            
                            if cache_result.is_success:
                                # Use cached related entity
                                related_entity = cache_result.value
                                setattr(entity, rel_name, related_entity)
                            else:
                                # Cache miss, query the database
                                query = select(target_class).where(getattr(target_class, 'id') == fk_value)
                                result = await session.execute(query)
                                related_entity = result.scalar_one_or_none()
                                
                                # Set the relationship
                                if related_entity:
                                    setattr(entity, rel_name, related_entity)
                                    
                                    # Store in cache for future use
                                    await self.cache.store_to_one(
                                        entity,
                                        rel_name,
                                        related_entity
                                    )
                
                # Handle to-many relationships (foreign key in related entity)
                else:
                    # Get the target class
                    target_class = rel_meta['target_type']
                    
                    # Try to get from cache first
                    cache_result = await self.cache.get_to_many(
                        entity,
                        rel_name,
                        target_class
                    )
                    
                    if cache_result.is_success:
                        # Use cached related entities
                        related_entities = cache_result.value
                        setattr(entity, rel_name, related_entities)
                    else:
                        # Cache miss, query the database
                        fk_field = rel_meta.get('foreign_key') or f"{self.model_class.__name__.lower()}_id"
                        
                        # Get related entities
                        if hasattr(target_class, fk_field):
                            query = select(target_class).where(getattr(target_class, fk_field) == entity.id)
                            result = await session.execute(query)
                            related_entities = result.scalars().all()
                            
                            # Set the relationship
                            setattr(entity, rel_name, related_entities)
                            
                            # Store in cache for future use
                            await self.cache.store_to_many(
                                entity,
                                rel_name,
                                related_entities
                            )
            
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
                    # Collect all foreign keys and track entities by FK
                    fk_field = f"{rel_name}_id"
                    fk_values = set()
                    entities_by_fk = {}  # fk_value -> entity
                    
                    for entity in entities:
                        if hasattr(entity, fk_field):
                            fk_value = getattr(entity, fk_field)
                            if fk_value:
                                fk_values.add(fk_value)
                                if fk_value not in entities_by_fk:
                                    entities_by_fk[fk_value] = []
                                entities_by_fk[fk_value].append(entity)
                    
                    if not fk_values:
                        continue
                    
                    # Get the target class
                    target_class = rel_meta['target_type']
                    
                    # Try to get cached entities first
                    cached_entities = {}  # fk_value -> related_entity
                    db_query_fk_values = set()  # FKs we still need to query
                    
                    # Check cache for each foreign key
                    for fk_value in fk_values:
                        # Use the first entity for each FK for cache lookup
                        entity = entities_by_fk[fk_value][0]
                        
                        cache_result = await self.cache.get_to_one(
                            entity,
                            rel_name,
                            target_class,
                            fk_value
                        )
                        
                        if cache_result.is_success:
                            # Cache hit
                            cached_entities[fk_value] = cache_result.value
                        else:
                            # Cache miss, need to query DB
                            db_query_fk_values.add(fk_value)
                    
                    # Query database for any missing values
                    db_entities = {}  # fk_value -> related_entity
                    if db_query_fk_values:
                        query = select(target_class).where(getattr(target_class, 'id').in_(db_query_fk_values))
                        result = await session.execute(query)
                        fetched_entities = result.scalars().all()
                        
                        # Build lookup map for database results
                        for related_entity in fetched_entities:
                            db_entities[related_entity.id] = related_entity
                            
                            # Store in cache for future use
                            # Use any entity with this FK for storing
                            if related_entity.id in entities_by_fk:
                                entity = entities_by_fk[related_entity.id][0]
                                await self.cache.store_to_one(
                                    entity,
                                    rel_name,
                                    related_entity
                                )
                    
                    # Combine cached and database results
                    all_related_entities = {**cached_entities, **db_entities}
                    
                    # Set relationships for all entities
                    for entity in entities:
                        if hasattr(entity, fk_field):
                            fk_value = getattr(entity, fk_field)
                            if fk_value and fk_value in all_related_entities:
                                setattr(entity, rel_name, all_related_entities[fk_value])
                
                # Handle to-many relationships (foreign key in related entity)
                else:
                    # Get foreign key field name
                    target_class = rel_meta['target_type']
                    fk_field = rel_meta.get('foreign_key') or f"{self.model_class.__name__.lower()}_id"
                    
                    # Try cache for each entity first
                    to_query_entities = []  # Entities we need to query for
                    cache_results = {}  # entity.id -> related_entities
                    
                    # Check cache for each entity
                    for entity in entities:
                        cache_result = await self.cache.get_to_many(
                            entity,
                            rel_name,
                            target_class
                        )
                        
                        if cache_result.is_success:
                            # Cache hit
                            cache_results[entity.id] = cache_result.value
                        else:
                            # Cache miss, need to query DB
                            to_query_entities.append(entity)
                    
                    # Query database for any entities with cache misses
                    if to_query_entities:
                        # Collect all entity IDs that need to be queried
                        entity_ids = [entity.id for entity in to_query_entities]
                        
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
                            
                            # Set relationships and cache the results
                            for entity in to_query_entities:
                                related_list = relations_map.get(entity.id, [])
                                setattr(entity, rel_name, related_list)
                                
                                # Store in cache for future use (if not empty)
                                if related_list:
                                    await self.cache.store_to_many(
                                        entity,
                                        rel_name,
                                        related_list
                                    )
                    
                    # Set relationships for cached results
                    for entity_id, related_list in cache_results.items():
                        # Find the entity by ID
                        for entity in entities:
                            if entity.id == entity_id:
                                setattr(entity, rel_name, related_list)
                                break
            
            except Exception as e:
                # Log error but continue with other relationships
                if self.logger:
                    self.logger.warning(f"Error batch loading relationship '{rel_name}': {e}")
        
        return entities


# Decorators

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


def invalidate_entity_cache(entity_param_name: str = 'entity'):
    """
    Decorator to invalidate relationship cache after a repository method.
    
    This decorator is designed for repository methods that update entities.
    It automatically invalidates the relationship cache for the entity
    after the method is executed.
    
    Args:
        entity_param_name: The name of the parameter containing the entity
            
    Returns:
        Function decorator that invalidates relationship cache
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Get the entity from args or kwargs
            entity = None
            if entity_param_name in kwargs:
                entity = kwargs[entity_param_name]
            elif len(args) > 1:  # Assuming first arg is self
                # Try to find entity in positional args
                # This is a bit heuristic, but works for common repository methods
                param_names = inspect.signature(func).parameters
                param_list = list(param_names.keys())
                if len(param_list) > 1 and param_list[1] == entity_param_name:
                    entity = args[1]
            
            # If result is an entity and no entity param was found, use the result
            if entity is None and hasattr(result, '__class__') and hasattr(result, 'id'):
                entity = result
            
            # If we have an entity, invalidate its relationships
            if entity is not None:
                # Create loader for the entity's class
                loader = RelationshipLoader(entity.__class__)
                
                # Invalidate the entity's relationships
                await loader.invalidate_relationships(entity)
            
            return result
            
        return wrapper
    
    return decorator


def invalidate_entities_cache(entities_param_name: str = 'entities'):
    """
    Decorator to invalidate relationship cache for multiple entities.
    
    This decorator is designed for repository methods that update multiple entities.
    It automatically invalidates the relationship cache for all entities
    after the method is executed.
    
    Args:
        entities_param_name: The name of the parameter containing the entities
            
    Returns:
        Function decorator that invalidates relationship cache
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Get the entities from args or kwargs
            entities = None
            if entities_param_name in kwargs:
                entities = kwargs[entities_param_name]
            elif len(args) > 1:  # Assuming first arg is self
                # Try to find entities in positional args
                param_names = inspect.signature(func).parameters
                param_list = list(param_names.keys())
                if len(param_list) > 1 and param_list[1] == entities_param_name:
                    entities = args[1]
            
            # If result is a list of entities and no entities param was found, use the result
            if entities is None and isinstance(result, list) and result and hasattr(result[0], 'id'):
                entities = result
            
            # If we have entities, invalidate their relationships
            if entities and isinstance(entities, (list, tuple, set)) and entities:
                # Create loader for the first entity's class
                # Assume all entities are of the same type
                loader = RelationshipLoader(entities[0].__class__)
                
                # Invalidate relationships for each entity
                for entity in entities:
                    await loader.invalidate_relationships(entity)
            
            return result
            
        return wrapper
    
    return decorator


class LazyRelationship:
    """
    Proxy for lazy-loaded relationships.
    
    This class provides a proxy object that loads a relationship on demand.
    It allows for more efficient loading patterns when not all relationships
    are needed. It leverages caching for improved performance.
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
            # Create loader with cache
            loader = RelationshipLoader(self.entity.__class__)
            
            # Check if we have relationship metadata for the model
            rel_meta = loader.relationships.get(self.relation_name)
            if not rel_meta:
                # Fallback to direct loading if we don't have metadata
                async with enhanced_async_session() as session:
                    loaded_entity = await loader._load_entity_relationships(
                        self.entity, 
                        [self.relation_name],
                        session
                    )
                    
                    # Get the loaded relationship value
                    self._value = getattr(loaded_entity, self.relation_name)
            else:
                # Try to load from cache first
                if not rel_meta['is_collection']:
                    # To-one relationship
                    fk_field = f"{self.relation_name}_id"
                    if hasattr(self.entity, fk_field):
                        fk_value = getattr(self.entity, fk_field)
                        if fk_value:
                            target_class = rel_meta['target_type']
                            
                            # Try to get from cache
                            cache_result = await loader.cache.get_to_one(
                                self.entity,
                                self.relation_name,
                                target_class,
                                fk_value
                            )
                            
                            if cache_result.is_success:
                                # Use cached value
                                self._value = cache_result.value
                            else:
                                # Cache miss, load from database
                                async with enhanced_async_session() as session:
                                    query = select(target_class).where(getattr(target_class, 'id') == fk_value)
                                    result = await session.execute(query)
                                    related_entity = result.scalar_one_or_none()
                                    
                                    if related_entity:
                                        self._value = related_entity
                                        
                                        # Store in cache for future use
                                        await loader.cache.store_to_one(
                                            self.entity,
                                            self.relation_name,
                                            related_entity
                                        )
                else:
                    # To-many relationship
                    target_class = rel_meta['target_type']
                    
                    # Try to get from cache
                    cache_result = await loader.cache.get_to_many(
                        self.entity,
                        self.relation_name,
                        target_class
                    )
                    
                    if cache_result.is_success:
                        # Use cached value
                        self._value = cache_result.value
                    else:
                        # Cache miss, load from database
                        async with enhanced_async_session() as session:
                            fk_field = rel_meta.get('foreign_key') or f"{self.entity.__class__.__name__.lower()}_id"
                            
                            if hasattr(target_class, fk_field):
                                query = select(target_class).where(getattr(target_class, fk_field) == self.entity.id)
                                result = await session.execute(query)
                                related_entities = result.scalars().all()
                                
                                self._value = related_entities
                                
                                # Store in cache for future use (if not empty)
                                if related_entities:
                                    await loader.cache.store_to_many(
                                        self.entity,
                                        self.relation_name,
                                        related_entities
                                    )
            
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