"""
Domain entities for the Read Model module.

This module defines the core domain entities for the Read Model module,
providing a rich domain model for read model management in CQRS applications.
"""

from datetime import datetime, UTC
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union, TypeVar, Generic

from pydantic import BaseModel

from uno.domain.core import Entity, AggregateRoot, ValueObject


@dataclass(frozen=True)
class ReadModelId(ValueObject):
    """Identifier for a read model."""
    value: str


@dataclass(frozen=True)
class ProjectionId(ValueObject):
    """Identifier for a projection."""
    value: str


@dataclass(frozen=True)
class QueryId(ValueObject):
    """Identifier for a query."""
    value: str


class CacheLevel(str, Enum):
    """Cache level in read model caching."""
    MEMORY = "memory"
    REDIS = "redis"
    DISTRIBUTED = "distributed"
    NONE = "none"


class ProjectionType(str, Enum):
    """Types of projections."""
    STANDARD = "standard"
    BATCH = "batch"
    ASYNC = "async"
    SNAPSHOT = "snapshot"


class QueryType(str, Enum):
    """Types of read model queries."""
    GET_BY_ID = "get_by_id"
    FIND = "find"
    LIST = "list"
    CUSTOM = "custom"


@dataclass
class ReadModel(Entity):
    """
    Base class for read models.
    
    Read models are optimized data structures for specific query use cases.
    They are updated by projections based on domain events.
    """
    
    id: ReadModelId
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def model_type(self) -> str:
        """Get the type of this read model."""
        return self.__class__.__name__
    
    def update(self, data: Dict[str, Any]) -> 'ReadModel':
        """
        Update the read model with new data.
        
        Args:
            data: The new data to update the read model with
            
        Returns:
            The updated read model
        """
        updated_data = self.data.copy()
        updated_data.update(data)
        
        new_model = self.__class__(
            id=self.id,
            version=self.version + 1,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
            data=updated_data,
            metadata=self.metadata
        )
        
        return new_model
    
    def set_metadata(self, key: str, value: Any) -> 'ReadModel':
        """
        Set metadata for the read model.
        
        Args:
            key: The metadata key
            value: The metadata value
            
        Returns:
            The updated read model
        """
        updated_metadata = self.metadata.copy()
        updated_metadata[key] = value
        
        new_model = self.__class__(
            id=self.id,
            version=self.version,
            created_at=self.created_at,
            updated_at=self.updated_at,
            data=self.data,
            metadata=updated_metadata
        )
        
        return new_model


@dataclass
class Projection(Entity):
    """
    Base class for projections.
    
    Projections transform domain events into read models, defining how
    domain events are applied to keep the query side of the application
    in sync with the command side.
    """
    
    id: ProjectionId
    name: str
    event_type: str
    read_model_type: str
    projection_type: ProjectionType = ProjectionType.STANDARD
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    def activate(self) -> None:
        """Activate the projection."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)
    
    def deactivate(self) -> None:
        """Deactivate the projection."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)
    
    def update_configuration(self, config: Dict[str, Any]) -> None:
        """
        Update the projection configuration.
        
        Args:
            config: The new configuration values
        """
        self.configuration.update(config)
        self.updated_at = datetime.now(UTC)


@dataclass
class Query(Entity):
    """
    Base class for read model queries.
    
    Queries are used to retrieve read models in a type-safe way.
    """
    
    id: QueryId
    query_type: QueryType
    read_model_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    @property
    def has_id_parameter(self) -> bool:
        """Check if this query has an ID parameter."""
        return "id" in self.parameters
    
    @property
    def has_criteria_parameter(self) -> bool:
        """Check if this query has criteria parameters."""
        return "criteria" in self.parameters


@dataclass
class QueryResult(Entity):
    """
    Result of a read model query.
    
    Query results contain the results of a query execution.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_id: QueryId
    execution_time_ms: float = 0.0
    result_count: int = 0
    results: Union[List[ReadModel], ReadModel, None] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_cached: bool = False
    

@dataclass
class CacheEntry(Entity):
    """
    A cache entry for a read model.
    
    Cache entries store read models for faster access.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    read_model_id: ReadModelId
    read_model_type: str
    key: str
    value: Any
    level: CacheLevel
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if this cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at


@dataclass
class ProjectorConfiguration(AggregateRoot):
    """
    Configuration for a projector.
    
    The projector configuration controls how projections are applied.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    async_processing: bool = True
    batch_size: int = 100
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    rebuild_on_startup: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    projections: List[Projection] = field(default_factory=list)
    
    def add_projection(self, projection: Projection) -> None:
        """
        Add a projection to the configuration.
        
        Args:
            projection: The projection to add
        """
        # Check if projection already exists
        for p in self.projections:
            if p.id.value == projection.id.value:
                return
        
        self.projections.append(projection)
        self.updated_at = datetime.now(UTC)
    
    def remove_projection(self, projection_id: ProjectionId) -> bool:
        """
        Remove a projection from the configuration.
        
        Args:
            projection_id: The ID of the projection to remove
            
        Returns:
            True if the projection was removed, False if not found
        """
        for i, projection in enumerate(self.projections):
            if projection.id.value == projection_id.value:
                self.projections.pop(i)
                self.updated_at = datetime.now(UTC)
                return True
        return False
    
    def enable_async_processing(self) -> None:
        """Enable asynchronous processing of projections."""
        self.async_processing = True
        self.updated_at = datetime.now(UTC)
    
    def disable_async_processing(self) -> None:
        """Disable asynchronous processing of projections."""
        self.async_processing = False
        self.updated_at = datetime.now(UTC)
    
    def enable_caching(self) -> None:
        """Enable caching of read models."""
        self.cache_enabled = True
        self.updated_at = datetime.now(UTC)
    
    def disable_caching(self) -> None:
        """Disable caching of read models."""
        self.cache_enabled = False
        self.updated_at = datetime.now(UTC)
    
    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """
        Set the cache time-to-live.
        
        Args:
            ttl_seconds: The time-to-live in seconds
        """
        self.cache_ttl_seconds = ttl_seconds
        self.updated_at = datetime.now(UTC)
    
    def set_batch_size(self, batch_size: int) -> None:
        """
        Set the batch size for processing projections.
        
        Args:
            batch_size: The batch size
        """
        self.batch_size = batch_size
        self.updated_at = datetime.now(UTC)
    
    def enable_rebuild_on_startup(self) -> None:
        """Enable rebuilding of read models on startup."""
        self.rebuild_on_startup = True
        self.updated_at = datetime.now(UTC)
    
    def disable_rebuild_on_startup(self) -> None:
        """Disable rebuilding of read models on startup."""
        self.rebuild_on_startup = False
        self.updated_at = datetime.now(UTC)