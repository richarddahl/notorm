"""
Semantic search engine for the Uno framework.

This module provides a search engine that uses vector embeddings
to find semantically similar content.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple

import numpy as np

from uno.ai.embeddings import EmbeddingModel, get_embedding_model
from uno.ai.vector_storage import VectorStorage, create_vector_storage

# Set up logger
logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """
    Core semantic search engine that combines embedding models with vector storage.
    """

    def __init__(
        self,
        embedding_model: Union[str, EmbeddingModel] = "default",
        vector_storage: Optional[VectorStorage] = None,
        connection_string: str | None = None,
        storage_type: str = "pgvector",
        table_name: str = "vector_embeddings",
        schema: str = "public",
    ):
        """
        Initialize the search engine.

        Args:
            embedding_model: Embedding model or name of registered model
            vector_storage: Vector storage instance (optional)
            connection_string: Database connection string (if no storage provided)
            storage_type: Type of vector storage to create (if no storage provided)
            table_name: Table name for storage (if no storage provided)
            schema: Database schema (if no storage provided)

        Raises:
            ValueError: If neither vector_storage nor connection_string is provided
        """
        # Set up embedding model
        if isinstance(embedding_model, str):
            self.embedding_model = get_embedding_model(embedding_model)
        else:
            self.embedding_model = embedding_model

        # Set up vector storage
        self.vector_storage = vector_storage
        self._storage_params = {}

        if vector_storage is None:
            if connection_string is None:
                raise ValueError(
                    "Either vector_storage or connection_string must be provided"
                )

            # Store params for lazy initialization
            self._storage_params = {
                "storage_type": storage_type,
                "connection_string": connection_string,
                "table_name": table_name,
                "dimensions": self.embedding_model.dimensions,
                "schema": schema,
            }

        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the search engine."""
        if self.initialized:
            return

        # Create vector storage if needed
        if self.vector_storage is None:
            self.vector_storage = await create_vector_storage(**self._storage_params)

        self.initialized = True
        logger.info(
            f"Initialized SemanticSearchEngine with model {self.embedding_model.model_name} "
            f"({self.embedding_model.dimensions} dimensions)"
        )

    async def index_document(
        self,
        document: str,
        entity_id: str,
        entity_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """
        Index a document for semantic search.

        Args:
            document: Text content to index
            entity_id: Unique identifier for the document
            entity_type: Type of document
            metadata: Additional metadata about the document

        Returns:
            ID of the indexed document
        """
        if not self.initialized:
            await self.initialize()

        # Generate embedding
        embedding = self.embedding_model.embed(document)

        # Store in vector database
        record_id = await self.vector_storage.store(
            entity_id=entity_id,
            entity_type=entity_type,
            embedding=embedding,
            metadata=metadata or {},
        )

        logger.debug(f"Indexed document {entity_id} of type {entity_type}")
        return record_id

    async def index_batch(self, documents: list[dict[str, Any]]) -> list[Any]:
        """
        Index multiple documents in batch.

        Args:
            documents: List of dictionaries with text, entity_id, entity_type, and metadata

        Returns:
            List of indexed document IDs
        """
        if not self.initialized:
            await self.initialize()

        # Prepare texts for batch embedding
        texts = [doc["text"] for doc in documents]

        # Generate embeddings in batch
        embeddings = self.embedding_model.embed_batch(texts)

        # Prepare items for batch storage
        items_to_store = []
        for i, doc in enumerate(documents):
            items_to_store.append(
                {
                    "entity_id": doc["entity_id"],
                    "entity_type": doc["entity_type"],
                    "embedding": embeddings[i],
                    "metadata": doc.get("metadata", {}),
                }
            )

        # Store in vector database
        record_ids = await self.vector_storage.store_batch(items_to_store)

        logger.debug(f"Indexed batch of {len(documents)} documents")
        return record_ids

    async def search(
        self,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search for documents similar to the query.

        Args:
            query: Search query text
            entity_type: Optional filter by entity type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of matches with similarity scores
        """
        if not self.initialized:
            await self.initialize()

        # Generate query embedding
        query_embedding = self.embedding_model.embed(query)

        # Search vector database
        results = await self.vector_storage.search(
            query_embedding=query_embedding,
            entity_type=entity_type,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )

        logger.debug(f"Search for '{query}' found {len(results)} results")
        return results

    async def delete_document(
        self, entity_id: str, entity_type: str | None = None
    ) -> int:
        """
        Delete document from the index.

        Args:
            entity_id: ID of document to delete
            entity_type: Optional entity type filter

        Returns:
            Number of documents deleted
        """
        if not self.initialized:
            await self.initialize()

        count = await self.vector_storage.delete(
            entity_id=entity_id, entity_type=entity_type
        )

        logger.debug(f"Deleted {count} documents with ID {entity_id}")
        return count

    async def close(self) -> None:
        """Close the search engine and its connections."""
        if self.vector_storage:
            await self.vector_storage.close()

        self.initialized = False
        logger.debug("Closed SemanticSearchEngine")
