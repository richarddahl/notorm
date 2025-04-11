"""
Service provider for vector search components.

This module implements the service provider pattern for vector search
services, allowing for clean dependency injection and integration.
"""

import logging
from typing import Dict, List, Any, Optional, Type

from uno.dependencies.provider import ServiceProvider
from uno.dependencies.interfaces import UnoConfigProtocol
from uno.dependencies.vector_interfaces import (
    VectorSearchServiceProtocol,
    RAGServiceProtocol,
    VectorUpdateServiceProtocol,
    BatchVectorUpdateServiceProtocol,
    VectorConfigServiceProtocol
)
from uno.domain.vector_search import VectorSearchService, RAGService
from uno.domain.vector_update_service import VectorUpdateService, BatchVectorUpdateService
from uno.domain.event_dispatcher import EventDispatcher
from uno.domain.vector_events import VectorEventHandler, VectorUpdateHandler


class VectorConfigService:
    """
    Configuration service for vector search.
    
    This service provides configuration for vector search components,
    managing dimensions, index types, and vectorizable fields.
    """
    
    def __init__(self, config: UnoConfigProtocol):
        """
        Initialize the vector configuration service.
        
        Args:
            config: The application configuration
        """
        self.config = config
        self._default_dimensions = self.config.get_value("VECTOR_DIMENSIONS", 1536)
        self._default_index_type = self.config.get_value("VECTOR_INDEX_TYPE", "hnsw")
        
        # Entity-specific configurations
        self._entity_configs: Dict[str, Dict[str, Any]] = {}
        
        # Initialize from config if available
        vector_entities = self.config.get_value("VECTOR_ENTITIES", {})
        for entity_type, entity_config in vector_entities.items():
            self.register_vectorizable_entity(
                entity_type=entity_type,
                fields=entity_config.get("fields", []),
                dimensions=entity_config.get("dimensions", self._default_dimensions),
                index_type=entity_config.get("index_type", self._default_index_type)
            )
    
    def get_dimensions(self, entity_type: Optional[str] = None) -> int:
        """
        Get the embedding dimensions for an entity type.
        
        Args:
            entity_type: Optional entity type to get dimensions for
            
        Returns:
            Number of dimensions for embeddings
        """
        if entity_type and entity_type in self._entity_configs:
            return self._entity_configs[entity_type].get("dimensions", self._default_dimensions)
        return self._default_dimensions
    
    def get_index_type(self, entity_type: Optional[str] = None) -> str:
        """
        Get the index type for an entity type.
        
        Args:
            entity_type: Optional entity type to get index type for
            
        Returns:
            Index type ("hnsw", "ivfflat", or "none")
        """
        if entity_type and entity_type in self._entity_configs:
            return self._entity_configs[entity_type].get("index_type", self._default_index_type)
        return self._default_index_type
    
    def get_vectorizable_fields(self, entity_type: str) -> List[str]:
        """
        Get fields that should be vectorized for an entity type.
        
        Args:
            entity_type: The entity type to get fields for
            
        Returns:
            List of field names to vectorize
        """
        if entity_type in self._entity_configs:
            return self._entity_configs[entity_type].get("fields", [])
        return []
    
    def is_vectorizable(self, entity_type: str) -> bool:
        """
        Check if an entity type is vectorizable.
        
        Args:
            entity_type: The entity type to check
            
        Returns:
            True if the entity type is vectorizable
        """
        return entity_type in self._entity_configs
    
    def register_vectorizable_entity(
        self,
        entity_type: str,
        fields: List[str],
        dimensions: int = 1536,
        index_type: str = "hnsw"
    ) -> None:
        """
        Register an entity type as vectorizable.
        
        Args:
            entity_type: The entity type to register
            fields: Fields to vectorize
            dimensions: Embedding dimensions
            index_type: Index type
        """
        self._entity_configs[entity_type] = {
            "fields": fields,
            "dimensions": dimensions,
            "index_type": index_type
        }
    
    def get_all_vectorizable_entities(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered vectorizable entity configurations.
        
        Returns:
            Dictionary of entity configs keyed by entity type
        """
        return dict(self._entity_configs)


class VectorSearchProvider(ServiceProvider):
    """
    Service provider for vector search services.
    
    This provider registers vector search services with the
    dependency injection container.
    """
    
    def register(self) -> None:
        """Register vector search services with the container."""
        # Register the configuration service
        self._logger.info("Registering vector search services")
        
        # Note: in this codebase, ServiceProvider doesn't have a 'container' property.
        # We need to use the inject.instance() directly or register with the global container
        
        # Register vector config service
        vector_config = VectorConfigService(self.get_config())
        self.register_service(VectorConfigServiceProtocol, vector_config)
        
        # Get or create event dispatcher
        dispatcher = None
        try:
            dispatcher = self.get_service(EventDispatcher)
        except (ValueError, KeyError):
            # Create a new dispatcher if not available
            dispatcher = EventDispatcher(logger=logging.getLogger('uno.vector.events'))
            self.register_service(EventDispatcher, dispatcher)
        
        # Register event handlers
        event_handler = self._create_vector_event_handler(
            config_service=vector_config,
            dispatcher=dispatcher
        )
        self.register_service(VectorEventHandler, event_handler)
        
        update_handler = VectorUpdateHandler(
            dispatcher=dispatcher,
            logger=logging.getLogger('uno.vector.handlers')
        )
        self.register_service(VectorUpdateHandler, update_handler)
        
        # Create and register vector update services
        update_service = self._create_vector_update_service(
            config=self.get_config(),
            dispatcher=dispatcher
        )
        self.register_service(VectorUpdateServiceProtocol, update_service)
        
        batch_service = BatchVectorUpdateService(
            dispatcher=dispatcher,
            batch_size=self.get_config().get_value("VECTOR_BATCH_SIZE", 100),
            logger=logging.getLogger('uno.vector.batch')
        )
        self.register_service(BatchVectorUpdateServiceProtocol, batch_service)
        
        # Register the vector services in the module namespace for easy access
        from uno.dependencies.vector_provider import set_vector_factories
        set_vector_factories(
            search_factory=lambda entity_type, table_name, repository=None: VectorSearchService(
                entity_type=entity_type,
                table_name=table_name,
                repository=repository,
                logger=logging.getLogger(f'uno.vector.search.{entity_type}')
            ),
            rag_factory=lambda vector_search: RAGService(
                vector_search=vector_search,
                logger=logging.getLogger('uno.vector.rag')
            )
        )
        
        self._logger.info("Vector search services registered successfully")
    
    def _create_vector_event_handler(self, config_service: VectorConfigServiceProtocol, 
                                    dispatcher: EventDispatcher) -> VectorEventHandler:
        """
        Create a vector event handler with the correct configuration.
        
        Args:
            config_service: The vector configuration service
            dispatcher: The event dispatcher
            
        Returns:
            Configured VectorEventHandler
        """
        # Build vectorizable types dictionary
        vectorizable_types = {}
        
        for entity_type, entity_config in config_service.get_all_vectorizable_entities().items():
            vectorizable_types[entity_type] = entity_config["fields"]
        
        # Create the handler
        return VectorEventHandler(
            dispatcher=dispatcher,
            vectorizable_types=vectorizable_types,
            logger=logging.getLogger('uno.vector.events')
        )
    
    def _create_vector_update_service(self, config: UnoConfigProtocol, 
                                     dispatcher: EventDispatcher) -> VectorUpdateService:
        """
        Create and configure the vector update service.
        
        Args:
            config: The application configuration
            dispatcher: The event dispatcher
            
        Returns:
            Configured VectorUpdateService
        """
        service = VectorUpdateService(
            dispatcher=dispatcher,
            batch_size=config.get_value("VECTOR_BATCH_SIZE", 10),
            update_interval=config.get_value("VECTOR_UPDATE_INTERVAL", 1.0),
            logger=logging.getLogger('uno.vector.updates')
        )
        
        # Start the service if auto-start is enabled
        if config.get_value("VECTOR_AUTO_START", True):
            import asyncio
            
            async def start_service():
                await service.start()
            
            # Run in background
            asyncio.create_task(start_service())
        
        return service
    
    def boot(self) -> None:
        """Perform any necessary boot operations for the vector services."""
        self._logger.info("Booting vector search services")
        
        # Get the update service and ensure it's started
        try:
            update_service = self.get_service(VectorUpdateServiceProtocol)
            
            # Start the service if not already running
            if not getattr(update_service, '_running', False):
                import asyncio
                
                async def start_service():
                    await update_service.start()
                
                # Run in background
                asyncio.create_task(start_service())
                
                self._logger.info("Vector update service started")
        except (ValueError, KeyError) as e:
            self._logger.error(f"Failed to boot vector update service: {e}")


# Global factory functions for vector services
_vector_search_factory = None
_rag_service_factory = None


def set_vector_factories(search_factory, rag_factory):
    """
    Set the global factory functions for vector services.
    
    Args:
        search_factory: Factory function for creating vector search services
        rag_factory: Factory function for creating RAG services
    """
    global _vector_search_factory, _rag_service_factory
    _vector_search_factory = search_factory
    _rag_service_factory = rag_factory


def get_vector_search_service(entity_type, table_name, repository=None):
    """
    Get a vector search service for a specific entity type.
    
    Args:
        entity_type: The entity type to search
        table_name: The database table name
        repository: Optional repository to use
        
    Returns:
        Vector search service
        
    Raises:
        RuntimeError: If vector services are not initialized
    """
    if _vector_search_factory is None:
        raise RuntimeError("Vector services not initialized")
    return _vector_search_factory(entity_type, table_name, repository)


def get_rag_service(vector_search):
    """
    Get a RAG service using a vector search service.
    
    Args:
        vector_search: The vector search service to use
        
    Returns:
        RAG service
        
    Raises:
        RuntimeError: If vector services are not initialized
    """
    if _rag_service_factory is None:
        raise RuntimeError("Vector services not initialized")
    return _rag_service_factory(vector_search)