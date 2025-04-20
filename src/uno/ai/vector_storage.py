"""
Vector storage for embedding vectors.

This module provides a storage layer for vector embeddings,
supporting different backend options like PostgreSQL with pgvector.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, TypeVar, Generic, Union

import numpy as np

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for vector storage
T = TypeVar("T")


class VectorStorage(Generic[T], ABC):
    """Abstract base class for vector storage implementations."""

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the vector store.

        Ensures schema and indexes are ready.
        """
        pass

    @abstractmethod
    async def store(
        self,
        entity_id: str,
        entity_type: str,
        embedding: np.ndarray,
        metadata: dict[str, Any] | None = None,
    ) -> T:
        """
        Store a vector embedding for an entity.

        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity
            embedding: Vector embedding
            metadata: Additional metadata about the entity

        Returns:
            Identifier or record for the stored embedding
        """
        pass

    @abstractmethod
    async def store_batch(self, items: list[dict[str, Any]]) -> list[T]:
        """
        Store multiple vector embeddings in batch.

        Args:
            items: List of dictionaries with entity_id, entity_type, embedding, and metadata

        Returns:
            List of identifiers or records for the stored embeddings
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: np.ndarray,
        entity_type: str | None = None,
        limit: int = 10,
        similarity_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search for similar entities using vector similarity.

        Args:
            query_embedding: Vector embedding to search with
            entity_type: Optional filter by entity type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of matches with similarity scores
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: str, entity_type: str | None = None) -> int:
        """
        Delete entity embeddings from the store.

        Args:
            entity_id: ID of entity to delete
            entity_type: Optional entity type filter

        Returns:
            Number of records deleted
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the vector store connection."""
        pass


class PGVectorStorage(VectorStorage[int]):
    """
    Vector storage implementation using PostgreSQL with pgvector extension.
    """

    def __init__(
        self,
        connection_string: str,
        table_name: str = "vector_embeddings",
        dimensions: int = 384,
        schema: str = "public",
    ):
        """
        Initialize the PostgreSQL vector storage.

        Args:
            connection_string: Database connection string
            table_name: Name of the table to store embeddings
            dimensions: Dimensions of the embedding vectors
            schema: Database schema
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.dimensions = dimensions
        self.schema = schema
        self.pool = None
        self.initialized = False

    async def initialize(self) -> None:
        """
        Initialize the vector store and ensure schema is ready.

        Creates the necessary tables and indexes if they don't exist.
        """
        try:
            import asyncpg
        except ImportError:
            raise ImportError(
                "asyncpg package is required for PGVectorStorage. "
                "Install it with: pip install asyncpg"
            )

        # Create connection pool
        self.pool = await asyncpg.create_pool(self.connection_string)

        # Check for pgvector extension
        async with self.pool.acquire() as conn:
            # Check if pgvector extension is installed
            extension_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )

            if not extension_exists:
                try:
                    # Try to create the extension
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    logger.info("Created pgvector extension")
                except Exception as e:
                    raise RuntimeError(
                        f"PostgreSQL pgvector extension is required but could not be created: {e}. "
                        "Please install the extension manually."
                    )

            # Create qualified table name
            qualified_table = f"{self.schema}.{self.table_name}"

            # Create the vector table if it doesn't exist
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {qualified_table} (
                    id SERIAL PRIMARY KEY,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    embedding vector({self.dimensions}) NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_entity_id 
                ON {qualified_table}(entity_id)
            """
            )

            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_entity_type 
                ON {qualified_table}(entity_type)
            """
            )

            # Create vector index (this might take time for large tables)
            try:
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding 
                    ON {qualified_table} USING ivfflat (embedding vector_l2_ops)
                    WITH (lists = 100)
                """
                )
            except Exception as e:
                logger.warning(f"Could not create vector index: {e}")
                logger.warning("Vector search will still work but may be slower.")

        self.initialized = True
        logger.info(f"Initialized PGVectorStorage with table {qualified_table}")

    async def store(
        self,
        entity_id: str,
        entity_type: str,
        embedding: np.ndarray,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Store a vector embedding for an entity.

        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity
            embedding: Vector embedding
            metadata: Additional metadata about the entity

        Returns:
            ID of the stored embedding
        """
        if not self.initialized:
            await self.initialize()

        # Convert embedding to database format
        embedding_str = f"[{','.join(map(str, embedding.tolist()))}]"

        async with self.pool.acquire() as conn:
            # Check if entity already exists
            existing_id = await conn.fetchval(
                f"SELECT id FROM {self.schema}.{self.table_name} "
                f"WHERE entity_id = $1 AND entity_type = $2",
                entity_id,
                entity_type,
            )

            if existing_id:
                # Update existing record
                record_id = await conn.fetchval(
                    f"""
                    UPDATE {self.schema}.{self.table_name}
                    SET embedding = $1::vector, metadata = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                    RETURNING id
                """,
                    embedding_str,
                    json.dumps(metadata or {}),
                    existing_id,
                )

                logger.debug(
                    f"Updated existing embedding for {entity_type}/{entity_id}"
                )
                return record_id
            else:
                # Insert new record
                record_id = await conn.fetchval(
                    f"""
                    INSERT INTO {self.schema}.{self.table_name}
                    (entity_id, entity_type, embedding, metadata)
                    VALUES ($1, $2, $3::vector, $4)
                    RETURNING id
                """,
                    entity_id,
                    entity_type,
                    embedding_str,
                    json.dumps(metadata or {}),
                )

                logger.debug(f"Stored new embedding for {entity_type}/{entity_id}")
                return record_id

    async def store_batch(self, items: list[dict[str, Any]]) -> list[int]:
        """
        Store multiple vector embeddings in batch.

        Args:
            items: List of dictionaries with entity_id, entity_type, embedding, and metadata

        Returns:
            List of stored embedding IDs
        """
        if not self.initialized:
            await self.initialize()

        ids = []
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for item in items:
                    entity_id = item["entity_id"]
                    entity_type = item["entity_type"]
                    embedding = item["embedding"]
                    metadata = item.get("metadata", {})

                    # Convert embedding to database format
                    embedding_str = f"[{','.join(map(str, embedding.tolist()))}]"

                    # Check if entity already exists
                    existing_id = await conn.fetchval(
                        f"SELECT id FROM {self.schema}.{self.table_name} "
                        f"WHERE entity_id = $1 AND entity_type = $2",
                        entity_id,
                        entity_type,
                    )

                    if existing_id:
                        # Update existing record
                        record_id = await conn.fetchval(
                            f"""
                            UPDATE {self.schema}.{self.table_name}
                            SET embedding = $1::vector, metadata = $2, updated_at = CURRENT_TIMESTAMP
                            WHERE id = $3
                            RETURNING id
                        """,
                            embedding_str,
                            json.dumps(metadata or {}),
                            existing_id,
                        )
                    else:
                        # Insert new record
                        record_id = await conn.fetchval(
                            f"""
                            INSERT INTO {self.schema}.{self.table_name}
                            (entity_id, entity_type, embedding, metadata)
                            VALUES ($1, $2, $3::vector, $4)
                            RETURNING id
                        """,
                            entity_id,
                            entity_type,
                            embedding_str,
                            json.dumps(metadata or {}),
                        )

                    ids.append(record_id)

        logger.debug(f"Stored batch of {len(ids)} embeddings")
        return ids

    async def search(
        self,
        query_embedding: np.ndarray,
        entity_type: str | None = None,
        limit: int = 10,
        similarity_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search for similar entities using vector similarity.

        Args:
            query_embedding: Vector embedding to search with
            entity_type: Optional filter by entity type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of matches with similarity scores
        """
        if not self.initialized:
            await self.initialize()

        # Convert embedding to database format
        embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"

        # Prepare query
        query = f"""
            SELECT 
                id, 
                entity_id, 
                entity_type, 
                metadata,
                1 - (embedding <-> $1::vector) as similarity
            FROM {self.schema}.{self.table_name}
            WHERE 1 - (embedding <-> $1::vector) >= $2
        """

        params = [embedding_str, similarity_threshold]

        if entity_type:
            query += " AND entity_type = $3"
            params.append(entity_type)

        query += f" ORDER BY similarity DESC LIMIT {limit}"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                # Parse JSON metadata
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}

                results.append(
                    {
                        "id": row["id"],
                        "entity_id": row["entity_id"],
                        "entity_type": row["entity_type"],
                        "metadata": metadata,
                        "similarity": row["similarity"],
                    }
                )

            logger.debug(
                f"Found {len(results)} results for {entity_type or 'any'} search"
            )
            return results

    async def delete(self, entity_id: str, entity_type: str | None = None) -> int:
        """
        Delete entity embeddings from the store.

        Args:
            entity_id: ID of entity to delete
            entity_type: Optional entity type filter

        Returns:
            Number of records deleted
        """
        if not self.initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            if entity_type:
                query = f"""
                    DELETE FROM {self.schema}.{self.table_name} 
                    WHERE entity_id = $1 AND entity_type = $2
                """
                result = await conn.execute(query, entity_id, entity_type)
            else:
                query = f"""
                    DELETE FROM {self.schema}.{self.table_name} 
                    WHERE entity_id = $1
                """
                result = await conn.execute(query, entity_id)

            # Parse the DELETE 'n' to get count
            count = int(result.split()[1])
            logger.debug(f"Deleted {count} embeddings for entity {entity_id}")

            return count

    async def close(self) -> None:
        """Close the vector store connection."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self.initialized = False
            logger.debug("Closed PGVectorStorage connection")


async def create_vector_storage(
    storage_type: str = "pgvector", **kwargs: Any
) -> VectorStorage:
    """
    Create a vector storage instance.

    Args:
        storage_type: Type of vector storage ("pgvector")
        **kwargs: Additional arguments for the storage constructor

    Returns:
        Initialized vector storage

    Raises:
        ValueError: For unknown storage type
    """
    if storage_type == "pgvector":
        storage = PGVectorStorage(**kwargs)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")

    # Initialize the storage
    await storage.initialize()

    return storage
