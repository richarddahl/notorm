"""
Domain knowledge integration for AI features.

This module provides tools for integrating domain-specific knowledge into
the AI features, enhancing content generation, search, and recommendations
with specialized terminology, concepts, and relationships.
"""

import asyncio
import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import asyncpg
from pydantic import BaseModel, Field, validator


class KnowledgeSource(str, Enum):
    """Source of domain knowledge."""

    TAXONOMY = "taxonomy"
    ONTOLOGY = "ontology"
    GLOSSARY = "glossary"
    FAQ = "faq"
    GUIDELINES = "guidelines"
    STANDARDS = "standards"
    REGULATIONS = "regulations"
    BEST_PRACTICES = "best_practices"
    RESEARCH = "research"
    CASE_STUDIES = "case_studies"
    CUSTOM = "custom"


class PromptEnhancementMode(str, Enum):
    """Method for enhancing prompts with domain knowledge."""

    APPEND = "append"
    PREPEND = "prepend"
    CONTEXT = "context"
    SYSTEM_MESSAGE = "system_message"
    INJECTION = "injection"
    TEMPLATE = "template"
    CUSTOM = "custom"


class KnowledgeImportConfig(BaseModel):
    """Configuration for importing domain knowledge."""

    source_type: KnowledgeSource
    source_path: str | None = None
    source_url: str | None = None
    source_database: str | None = None
    connection_string: str | None = None
    domain: str
    format: str = "json"  # json, csv, xml, sql, txt, etc.
    auto_index: bool = True
    create_embeddings: bool = True
    parse_relationships: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_path")
    def validate_source_path(cls, v, values, **kwargs):
        """Validate that source path exists if provided."""
        if v is not None and not os.path.exists(v):
            raise ValueError(f"Source path does not exist: {v}")
        return v


class KnowledgeItem(BaseModel):
    """Single item of domain knowledge."""

    id: str
    domain: str
    source: KnowledgeSource
    type: str  # concept, term, rule, guideline, etc.
    name: str
    definition: str | None = None
    content: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    relationships: Dict[str, list[str]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[list[float]] = None
    importance: float = 1.0  # 0.0 to 1.0
    created_at: str | None = None
    updated_at: str | None = None


class PromptEnhancementConfig(BaseModel):
    """Configuration for enhancing prompts with domain knowledge."""

    mode: PromptEnhancementMode
    domain: str
    relevance_threshold: float = 0.7
    max_items: int = 5
    include_definitions: bool = True
    include_relationships: bool = False
    template: str | None = None
    custom_formatter: str | None = None
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)


class DomainKnowledgeManager:
    """
    Manager for domain-specific knowledge integration.

    This class provides tools for importing, storing, retrieving, and
    utilizing domain-specific knowledge to enhance AI features.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        knowledge_table: str = "domain_knowledge",
        embedding_service=None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the domain knowledge manager.

        Args:
            connection_string: Database connection string
            knowledge_table: Table for storing knowledge items
            embedding_service: Service for generating embeddings
            logger: Optional logger
        """
        self.connection_string = connection_string
        self.knowledge_table = knowledge_table
        self.embedding_service = embedding_service
        self.logger = logger or logging.getLogger(__name__)

        # Database connection
        self.pool = None

        # In-memory cache
        self.knowledge_cache: Dict[str, Dict[str, KnowledgeItem]] = {}
        self.domain_glossaries: Dict[str, Dict[str, str]] = {}
        self.domain_taxonomies: Dict[str, Dict[str, list[str]]] = {}

        # Initialization flag
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the knowledge manager."""
        if self.initialized:
            return

        if self.connection_string:
            try:
                # Initialize database connection
                self.pool = await asyncpg.create_pool(self.connection_string)

                # Create tables if they don't exist
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self.knowledge_table} (
                            id TEXT PRIMARY KEY,
                            domain TEXT NOT NULL,
                            source TEXT NOT NULL,
                            type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            definition TEXT,
                            content TEXT,
                            synonyms JSONB,
                            relationships JSONB,
                            metadata JSONB,
                            embedding VECTOR(384),
                            importance REAL NOT NULL DEFAULT 1.0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        )
                    """
                    )

                    # Create indexes
                    await conn.execute(
                        f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.knowledge_table}_domain 
                        ON {self.knowledge_table}(domain)
                    """
                    )

                    await conn.execute(
                        f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.knowledge_table}_name 
                        ON {self.knowledge_table}(name)
                    """
                    )

                    # Create vector index if not exists
                    try:
                        await conn.execute(
                            f"""
                            CREATE INDEX IF NOT EXISTS idx_{self.knowledge_table}_embedding 
                            ON {self.knowledge_table} USING ivfflat (embedding vector_l2_ops)
                            WITH (lists = 100) WHERE embedding IS NOT NULL
                        """
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not create vector index: {e}")

            except Exception as e:
                self.logger.error(f"Database initialization error: {e}")

        self.initialized = True

    async def import_knowledge(self, config: KnowledgeImportConfig) -> Dict[str, Any]:
        """
        Import domain knowledge from a source.

        Args:
            config: Import configuration

        Returns:
            Dictionary with import statistics
        """
        if not self.initialized:
            await self.initialize()

        # Statistics
        stats = {
            "total_items": 0,
            "imported_items": 0,
            "updated_items": 0,
            "failed_items": 0,
            "domain": config.domain,
            "source_type": config.source_type,
        }

        try:
            # Load data from source
            if config.source_path:
                items = await self._load_from_file(config)
            elif config.source_url:
                items = await self._load_from_url(config)
            elif config.source_database:
                items = await self._load_from_database(config)
            else:
                self.logger.error("No source specified for knowledge import")
                return {"error": "No source specified"}

            stats["total_items"] = len(items)

            # Process and store items
            for item in items:
                try:
                    # Ensure domain matches config
                    item.domain = config.domain

                    # Generate embeddings if requested and service available
                    if (
                        config.create_embeddings
                        and self.embedding_service
                        and not item.embedding
                    ):
                        text_to_embed = (
                            f"{item.name} {item.definition or ''} {item.content or ''}"
                        )
                        embedding = await self.embedding_service.embed_text(
                            text_to_embed
                        )
                        item.embedding = embedding.tolist()

                    # Store in database if available
                    if self.pool:
                        await self._store_item(item)

                    # Store in cache
                    if item.domain not in self.knowledge_cache:
                        self.knowledge_cache[item.domain] = {}

                    self.knowledge_cache[item.domain][item.id] = item

                    # Update domain glossary
                    if item.definition:
                        if item.domain not in self.domain_glossaries:
                            self.domain_glossaries[item.domain] = {}

                        self.domain_glossaries[item.domain][item.name] = item.definition

                        # Add synonyms to glossary
                        for synonym in item.synonyms:
                            self.domain_glossaries[item.domain][
                                synonym
                            ] = item.definition

                    # Update taxonomy if relationships exist
                    if item.relationships:
                        if item.domain not in self.domain_taxonomies:
                            self.domain_taxonomies[item.domain] = {}

                        # Process each relationship type
                        for rel_type, related_items in item.relationships.items():
                            key = f"{item.name}:{rel_type}"
                            self.domain_taxonomies[item.domain][key] = related_items

                    stats["imported_items"] += 1

                except Exception as e:
                    self.logger.error(f"Failed to process knowledge item: {e}")
                    stats["failed_items"] += 1

            return stats

        except Exception as e:
            self.logger.error(f"Knowledge import error: {e}")
            return {"error": str(e)}

    async def _load_from_file(
        self, config: KnowledgeImportConfig
    ) -> list[KnowledgeItem]:
        """
        Load knowledge items from a file.

        Args:
            config: Import configuration

        Returns:
            List of knowledge items
        """
        items = []

        if not config.source_path:
            return items

        try:
            with open(config.source_path, "r", encoding="utf-8") as f:
                if config.format.lower() == "json":
                    data = json.load(f)

                    # Handle different JSON formats
                    if isinstance(data, list):
                        # List of items
                        for item_data in data:
                            item = KnowledgeItem(
                                id=item_data.get("id", f"{config.domain}_{len(items)}"),
                                domain=config.domain,
                                source=config.source_type,
                                type=item_data.get("type", "concept"),
                                name=item_data.get("name", ""),
                                definition=item_data.get("definition"),
                                content=item_data.get("content"),
                                synonyms=item_data.get("synonyms", []),
                                relationships=item_data.get("relationships", {}),
                                metadata=item_data.get("metadata", {}),
                                embedding=item_data.get("embedding"),
                                importance=item_data.get("importance", 1.0),
                            )
                            items.append(item)

                    elif isinstance(data, dict):
                        if "items" in data:
                            # Dictionary with items
                            for item_data in data["items"]:
                                item = KnowledgeItem(
                                    id=item_data.get(
                                        "id", f"{config.domain}_{len(items)}"
                                    ),
                                    domain=config.domain,
                                    source=config.source_type,
                                    type=item_data.get("type", "concept"),
                                    name=item_data.get("name", ""),
                                    definition=item_data.get("definition"),
                                    content=item_data.get("content"),
                                    synonyms=item_data.get("synonyms", []),
                                    relationships=item_data.get("relationships", {}),
                                    metadata=item_data.get("metadata", {}),
                                    embedding=item_data.get("embedding"),
                                    importance=item_data.get("importance", 1.0),
                                )
                                items.append(item)
                        else:
                            # Dictionary of terms
                            for name, definition in data.items():
                                if isinstance(definition, dict):
                                    # Structured definition
                                    item = KnowledgeItem(
                                        id=f"{config.domain}_{name.lower().replace(' ', '_')}",
                                        domain=config.domain,
                                        source=config.source_type,
                                        type=definition.get("type", "term"),
                                        name=name,
                                        definition=definition.get("definition"),
                                        content=definition.get("content"),
                                        synonyms=definition.get("synonyms", []),
                                        relationships=definition.get(
                                            "relationships", {}
                                        ),
                                        metadata=definition.get("metadata", {}),
                                        importance=definition.get("importance", 1.0),
                                    )
                                else:
                                    # Simple string definition
                                    item = KnowledgeItem(
                                        id=f"{config.domain}_{name.lower().replace(' ', '_')}",
                                        domain=config.domain,
                                        source=config.source_type,
                                        type="term",
                                        name=name,
                                        definition=(
                                            definition
                                            if isinstance(definition, str)
                                            else str(definition)
                                        ),
                                        synonyms=[],
                                        relationships={},
                                        metadata={},
                                    )
                                items.append(item)

                elif config.format.lower() == "csv":
                    import csv

                    csv_reader = csv.DictReader(f)

                    for i, row in enumerate(csv_reader):
                        # Handle required fields
                        if "name" not in row:
                            continue

                        # Process relationships if present
                        relationships = {}
                        for key in row:
                            if key.startswith("rel_") and row[key]:
                                rel_type = key[4:]
                                rel_values = [x.strip() for x in row[key].split(",")]
                                relationships[rel_type] = rel_values

                        # Process synonyms if present
                        synonyms = []
                        if "synonyms" in row and row["synonyms"]:
                            synonyms = [x.strip() for x in row["synonyms"].split(",")]

                        # Create knowledge item
                        item = KnowledgeItem(
                            id=row.get("id", f"{config.domain}_{i}"),
                            domain=config.domain,
                            source=config.source_type,
                            type=row.get("type", "concept"),
                            name=row["name"],
                            definition=row.get("definition"),
                            content=row.get("content"),
                            synonyms=synonyms,
                            relationships=relationships,
                            metadata={
                                k: v
                                for k, v in row.items()
                                if k
                                not in [
                                    "id",
                                    "domain",
                                    "source",
                                    "type",
                                    "name",
                                    "definition",
                                    "content",
                                    "synonyms",
                                    "importance",
                                ]
                                and not k.startswith("rel_")
                            },
                            importance=float(row.get("importance", 1.0)),
                        )
                        items.append(item)

                else:
                    self.logger.error(f"Unsupported file format: {config.format}")

        except Exception as e:
            self.logger.error(f"Error loading knowledge from file: {e}")

        return items

    async def _load_from_url(
        self, config: KnowledgeImportConfig
    ) -> list[KnowledgeItem]:
        """
        Load knowledge items from a URL.

        Args:
            config: Import configuration

        Returns:
            List of knowledge items
        """
        items = []

        if not config.source_url:
            return items

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(config.source_url) as response:
                    if response.status != 200:
                        self.logger.error(
                            f"Failed to fetch data from URL: {response.status}"
                        )
                        return items

                    if config.format.lower() == "json":
                        data = await response.json()

                        # Handle different JSON formats
                        if isinstance(data, list):
                            # List of items
                            for item_data in data:
                                item = KnowledgeItem(
                                    id=item_data.get(
                                        "id", f"{config.domain}_{len(items)}"
                                    ),
                                    domain=config.domain,
                                    source=config.source_type,
                                    type=item_data.get("type", "concept"),
                                    name=item_data.get("name", ""),
                                    definition=item_data.get("definition"),
                                    content=item_data.get("content"),
                                    synonyms=item_data.get("synonyms", []),
                                    relationships=item_data.get("relationships", {}),
                                    metadata=item_data.get("metadata", {}),
                                    embedding=item_data.get("embedding"),
                                    importance=item_data.get("importance", 1.0),
                                )
                                items.append(item)

                        elif isinstance(data, dict):
                            if "items" in data:
                                # Dictionary with items
                                for item_data in data["items"]:
                                    item = KnowledgeItem(
                                        id=item_data.get(
                                            "id", f"{config.domain}_{len(items)}"
                                        ),
                                        domain=config.domain,
                                        source=config.source_type,
                                        type=item_data.get("type", "concept"),
                                        name=item_data.get("name", ""),
                                        definition=item_data.get("definition"),
                                        content=item_data.get("content"),
                                        synonyms=item_data.get("synonyms", []),
                                        relationships=item_data.get(
                                            "relationships", {}
                                        ),
                                        metadata=item_data.get("metadata", {}),
                                        embedding=item_data.get("embedding"),
                                        importance=item_data.get("importance", 1.0),
                                    )
                                    items.append(item)
                            else:
                                # Dictionary of terms
                                for name, definition in data.items():
                                    if isinstance(definition, dict):
                                        # Structured definition
                                        item = KnowledgeItem(
                                            id=f"{config.domain}_{name.lower().replace(' ', '_')}",
                                            domain=config.domain,
                                            source=config.source_type,
                                            type=definition.get("type", "term"),
                                            name=name,
                                            definition=definition.get("definition"),
                                            content=definition.get("content"),
                                            synonyms=definition.get("synonyms", []),
                                            relationships=definition.get(
                                                "relationships", {}
                                            ),
                                            metadata=definition.get("metadata", {}),
                                            importance=definition.get(
                                                "importance", 1.0
                                            ),
                                        )
                                    else:
                                        # Simple string definition
                                        item = KnowledgeItem(
                                            id=f"{config.domain}_{name.lower().replace(' ', '_')}",
                                            domain=config.domain,
                                            source=config.source_type,
                                            type="term",
                                            name=name,
                                            definition=(
                                                definition
                                                if isinstance(definition, str)
                                                else str(definition)
                                            ),
                                            synonyms=[],
                                            relationships={},
                                            metadata={},
                                        )
                                    items.append(item)
                    else:
                        # Handle other formats (CSV, XML, etc.)
                        content = await response.text()
                        if config.format.lower() == "csv":
                            import csv
                            import io

                            csv_reader = csv.DictReader(io.StringIO(content))

                            for i, row in enumerate(csv_reader):
                                # Handle required fields
                                if "name" not in row:
                                    continue

                                # Process relationships if present
                                relationships = {}
                                for key in row:
                                    if key.startswith("rel_") and row[key]:
                                        rel_type = key[4:]
                                        rel_values = [
                                            x.strip() for x in row[key].split(",")
                                        ]
                                        relationships[rel_type] = rel_values

                                # Process synonyms if present
                                synonyms = []
                                if "synonyms" in row and row["synonyms"]:
                                    synonyms = [
                                        x.strip() for x in row["synonyms"].split(",")
                                    ]

                                # Create knowledge item
                                item = KnowledgeItem(
                                    id=row.get("id", f"{config.domain}_{i}"),
                                    domain=config.domain,
                                    source=config.source_type,
                                    type=row.get("type", "concept"),
                                    name=row["name"],
                                    definition=row.get("definition"),
                                    content=row.get("content"),
                                    synonyms=synonyms,
                                    relationships=relationships,
                                    metadata={
                                        k: v
                                        for k, v in row.items()
                                        if k
                                        not in [
                                            "id",
                                            "domain",
                                            "source",
                                            "type",
                                            "name",
                                            "definition",
                                            "content",
                                            "synonyms",
                                            "importance",
                                        ]
                                        and not k.startswith("rel_")
                                    },
                                    importance=float(row.get("importance", 1.0)),
                                )
                                items.append(item)

        except Exception as e:
            self.logger.error(f"Error loading knowledge from URL: {e}")

        return items

    async def _load_from_database(
        self, config: KnowledgeImportConfig
    ) -> list[KnowledgeItem]:
        """
        Load knowledge items from a database.

        Args:
            config: Import configuration

        Returns:
            List of knowledge items
        """
        items = []

        if not config.source_database or not config.connection_string:
            return items

        try:
            # Create a separate connection for import
            import_pool = await asyncpg.create_pool(config.connection_string)

            async with import_pool.acquire() as conn:
                # Query the database
                rows = await conn.fetch(
                    f"""
                    SELECT * FROM {config.source_database}
                    WHERE domain = $1
                """,
                    config.domain,
                )

                for row in rows:
                    # Convert row to dictionary
                    row_dict = dict(row)

                    # Process JSON fields
                    for field in ["synonyms", "relationships", "metadata"]:
                        if field in row_dict and isinstance(row_dict[field], str):
                            try:
                                row_dict[field] = json.loads(row_dict[field])
                            except:
                                row_dict[field] = {}

                    # Create knowledge item
                    item = KnowledgeItem(
                        id=row_dict.get("id", f"{config.domain}_{len(items)}"),
                        domain=config.domain,
                        source=config.source_type,
                        type=row_dict.get("type", "concept"),
                        name=row_dict.get("name", ""),
                        definition=row_dict.get("definition"),
                        content=row_dict.get("content"),
                        synonyms=row_dict.get("synonyms", []),
                        relationships=row_dict.get("relationships", {}),
                        metadata=row_dict.get("metadata", {}),
                        embedding=row_dict.get("embedding"),
                        importance=float(row_dict.get("importance", 1.0)),
                        created_at=row_dict.get("created_at"),
                        updated_at=row_dict.get("updated_at"),
                    )
                    items.append(item)

            # Close the import pool
            await import_pool.close()

        except Exception as e:
            self.logger.error(f"Error loading knowledge from database: {e}")

        return items

    async def _store_item(self, item: KnowledgeItem) -> bool:
        """
        Store a knowledge item in the database.

        Args:
            item: Knowledge item to store

        Returns:
            True if storage was successful
        """
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                # Check if item exists
                existing = await conn.fetchval(
                    f"SELECT id FROM {self.knowledge_table} WHERE id = $1", item.id
                )

                if existing:
                    # Update existing item
                    await conn.execute(
                        f"""
                        UPDATE {self.knowledge_table}
                        SET 
                            domain = $2,
                            source = $3,
                            type = $4,
                            name = $5,
                            definition = $6,
                            content = $7,
                            synonyms = $8,
                            relationships = $9,
                            metadata = $10,
                            embedding = $11,
                            importance = $12,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """,
                        item.id,
                        item.domain,
                        item.source,
                        item.type,
                        item.name,
                        item.definition,
                        item.content,
                        json.dumps(item.synonyms),
                        json.dumps(item.relationships),
                        json.dumps(item.metadata),
                        item.embedding,
                        item.importance,
                    )
                else:
                    # Insert new item
                    await conn.execute(
                        f"""
                        INSERT INTO {self.knowledge_table} (
                            id, domain, source, type, name, definition, content,
                            synonyms, relationships, metadata, embedding, importance
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                        item.id,
                        item.domain,
                        item.source,
                        item.type,
                        item.name,
                        item.definition,
                        item.content,
                        json.dumps(item.synonyms),
                        json.dumps(item.relationships),
                        json.dumps(item.metadata),
                        item.embedding,
                        item.importance,
                    )

                return True

        except Exception as e:
            self.logger.error(f"Error storing knowledge item: {e}")
            return False

    async def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """
        Get a knowledge item by ID.

        Args:
            item_id: ID of the knowledge item

        Returns:
            Knowledge item if found, None otherwise
        """
        if not self.initialized:
            await self.initialize()

        # Check cache first
        for domain_items in self.knowledge_cache.values():
            if item_id in domain_items:
                return domain_items[item_id]

        # Check database
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow(
                        f"""
                        SELECT * FROM {self.knowledge_table}
                        WHERE id = $1
                    """,
                        item_id,
                    )

                    if row:
                        # Convert row to knowledge item
                        item = KnowledgeItem(
                            id=row["id"],
                            domain=row["domain"],
                            source=KnowledgeSource(row["source"]),
                            type=row["type"],
                            name=row["name"],
                            definition=row["definition"],
                            content=row["content"],
                            synonyms=(
                                json.loads(row["synonyms"]) if row["synonyms"] else []
                            ),
                            relationships=(
                                json.loads(row["relationships"])
                                if row["relationships"]
                                else {}
                            ),
                            metadata=(
                                json.loads(row["metadata"]) if row["metadata"] else {}
                            ),
                            embedding=row["embedding"],
                            importance=row["importance"],
                            created_at=(
                                row["created_at"].isoformat()
                                if row["created_at"]
                                else None
                            ),
                            updated_at=(
                                row["updated_at"].isoformat()
                                if row["updated_at"]
                                else None
                            ),
                        )

                        # Update cache
                        if item.domain not in self.knowledge_cache:
                            self.knowledge_cache[item.domain] = {}

                        self.knowledge_cache[item.domain][item.id] = item

                        return item

            except Exception as e:
                self.logger.error(f"Error retrieving knowledge item: {e}")

        return None

    async def search_knowledge(
        self,
        query: str,
        domain: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        item_types: list[str] | None = None,
    ) -> list[Tuple[KnowledgeItem, float]]:
        """
        Search for knowledge items by similarity.

        Args:
            query: Search query
            domain: Domain to search in
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            item_types: Optional filter by item types

        Returns:
            List of (knowledge item, similarity score) tuples
        """
        if not self.initialized:
            await self.initialize()

        results = []

        # Generate query embedding
        if self.embedding_service:
            query_embedding = await self.embedding_service.embed_text(query)

            # Search in database with vector similarity
            if self.pool:
                try:
                    async with self.pool.acquire() as conn:
                        # Convert embedding to database format
                        embedding_str = (
                            f"[{','.join(map(str, query_embedding.tolist()))}]"
                        )

                        # Prepare query
                        sql_query = f"""
                            SELECT 
                                id, domain, source, type, name, definition, content,
                                synonyms, relationships, metadata, embedding, importance,
                                created_at, updated_at,
                                1 - (embedding <-> $1::vector) as similarity
                            FROM {self.knowledge_table}
                            WHERE domain = $2
                            AND embedding IS NOT NULL
                            AND 1 - (embedding <-> $1::vector) >= $3
                        """

                        params = [embedding_str, domain, similarity_threshold]

                        # Add type filter if provided
                        if item_types:
                            placeholders = []
                            for i, item_type in enumerate(item_types):
                                placeholders.append(f"${len(params) + 1 + i}")
                                params.append(item_type)

                            sql_query += f" AND type IN ({','.join(placeholders)})"

                        sql_query += f" ORDER BY similarity DESC LIMIT {limit}"

                        rows = await conn.fetch(sql_query, *params)

                        for row in rows:
                            # Convert row to knowledge item
                            item = KnowledgeItem(
                                id=row["id"],
                                domain=row["domain"],
                                source=KnowledgeSource(row["source"]),
                                type=row["type"],
                                name=row["name"],
                                definition=row["definition"],
                                content=row["content"],
                                synonyms=(
                                    json.loads(row["synonyms"])
                                    if row["synonyms"]
                                    else []
                                ),
                                relationships=(
                                    json.loads(row["relationships"])
                                    if row["relationships"]
                                    else {}
                                ),
                                metadata=(
                                    json.loads(row["metadata"])
                                    if row["metadata"]
                                    else {}
                                ),
                                embedding=row["embedding"],
                                importance=row["importance"],
                                created_at=(
                                    row["created_at"].isoformat()
                                    if row["created_at"]
                                    else None
                                ),
                                updated_at=(
                                    row["updated_at"].isoformat()
                                    if row["updated_at"]
                                    else None
                                ),
                            )

                            # Get similarity score
                            similarity = row["similarity"]

                            # Update cache
                            if item.domain not in self.knowledge_cache:
                                self.knowledge_cache[item.domain] = {}

                            self.knowledge_cache[item.domain][item.id] = item

                            # Add to results
                            results.append((item, similarity))

                except Exception as e:
                    self.logger.error(f"Error searching knowledge: {e}")

        # If embedding search failed or no results, try text search
        if not results and domain in self.knowledge_cache:
            # Calculate text similarity with query
            from difflib import SequenceMatcher

            for item_id, item in self.knowledge_cache[domain].items():
                # Filter by type if needed
                if item_types and item.type not in item_types:
                    continue

                # Check name, definition, and content
                name_similarity = SequenceMatcher(
                    None, query.lower(), item.name.lower()
                ).ratio()
                def_similarity = 0.0
                if item.definition:
                    def_similarity = SequenceMatcher(
                        None, query.lower(), item.definition.lower()
                    ).ratio()

                content_similarity = 0.0
                if item.content:
                    content_similarity = SequenceMatcher(
                        None, query.lower(), item.content.lower()
                    ).ratio()

                # Use maximum similarity
                similarity = max(name_similarity, def_similarity, content_similarity)

                # Apply threshold
                if similarity >= similarity_threshold:
                    results.append((item, similarity))

            # Sort by similarity (descending)
            results.sort(key=lambda x: x[1], reverse=True)

            # Apply limit
            if limit > 0 and len(results) > limit:
                results = results[:limit]

        return results

    async def get_domain_glossary(self, domain: str) -> Dict[str, str]:
        """
        Get a glossary for a specific domain.

        Args:
            domain: Domain name

        Returns:
            Dictionary mapping terms to definitions
        """
        if not self.initialized:
            await self.initialize()

        # Check if glossary is already cached
        if domain in self.domain_glossaries:
            return self.domain_glossaries[domain]

        # Compile glossary from database
        glossary = {}

        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(
                        f"""
                        SELECT name, definition, synonyms
                        FROM {self.knowledge_table}
                        WHERE domain = $1
                        AND definition IS NOT NULL
                    """,
                        domain,
                    )

                    for row in rows:
                        name = row["name"]
                        definition = row["definition"]

                        # Add to glossary
                        glossary[name] = definition

                        # Add synonyms
                        if row["synonyms"]:
                            synonyms = json.loads(row["synonyms"])
                            for synonym in synonyms:
                                glossary[synonym] = definition

            except Exception as e:
                self.logger.error(f"Error retrieving domain glossary: {e}")

        # Cache the glossary
        self.domain_glossaries[domain] = glossary

        return glossary

    async def get_domain_taxonomy(self, domain: str) -> Dict[str, list[str]]:
        """
        Get a taxonomy for a specific domain.

        Args:
            domain: Domain name

        Returns:
            Dictionary mapping concepts to related concepts
        """
        if not self.initialized:
            await self.initialize()

        # Check if taxonomy is already cached
        if domain in self.domain_taxonomies:
            return self.domain_taxonomies[domain]

        # Compile taxonomy from database
        taxonomy = {}

        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(
                        f"""
                        SELECT name, relationships
                        FROM {self.knowledge_table}
                        WHERE domain = $1
                        AND relationships IS NOT NULL
                        AND relationships != 'null'
                        AND relationships != '{{}}'
                    """,
                        domain,
                    )

                    for row in rows:
                        name = row["name"]
                        relationships = json.loads(row["relationships"])

                        # Add each relationship type
                        for rel_type, related_items in relationships.items():
                            key = f"{name}:{rel_type}"
                            taxonomy[key] = related_items

            except Exception as e:
                self.logger.error(f"Error retrieving domain taxonomy: {e}")

        # Cache the taxonomy
        self.domain_taxonomies[domain] = taxonomy

        return taxonomy

    async def enhance_prompt(self, prompt: str, config: PromptEnhancementConfig) -> str:
        """
        Enhance a prompt with domain knowledge.

        Args:
            prompt: Original prompt
            config: Enhancement configuration

        Returns:
            Enhanced prompt
        """
        if not self.initialized:
            await self.initialize()

        # Search for relevant knowledge
        relevant_items = []
        if self.embedding_service:
            search_results = await self.search_knowledge(
                query=prompt,
                domain=config.domain,
                limit=config.max_items,
                similarity_threshold=config.relevance_threshold,
            )
            relevant_items = [item for item, score in search_results]

        # If no items found, return original prompt
        if not relevant_items:
            return prompt

        # Enhance prompt based on mode
        if config.mode == PromptEnhancementMode.APPEND:
            # Append knowledge to prompt
            knowledge_text = "\n\n## Domain Knowledge:\n\n"
            for item in relevant_items:
                knowledge_text += f"- {item.name}"
                if config.include_definitions and item.definition:
                    knowledge_text += f": {item.definition}"
                knowledge_text += "\n"

                # Add relationships if requested
                if config.include_relationships and item.relationships:
                    for rel_type, related_items in item.relationships.items():
                        knowledge_text += (
                            f"  - {rel_type}: {', '.join(related_items)}\n"
                        )

            return prompt + knowledge_text

        elif config.mode == PromptEnhancementMode.PREPEND:
            # Prepend knowledge to prompt
            knowledge_text = "## Domain Knowledge:\n\n"
            for item in relevant_items:
                knowledge_text += f"- {item.name}"
                if config.include_definitions and item.definition:
                    knowledge_text += f": {item.definition}"
                knowledge_text += "\n"

                # Add relationships if requested
                if config.include_relationships and item.relationships:
                    for rel_type, related_items in item.relationships.items():
                        knowledge_text += (
                            f"  - {rel_type}: {', '.join(related_items)}\n"
                        )

            return knowledge_text + "\n\n" + prompt

        elif config.mode == PromptEnhancementMode.CONTEXT:
            # Use knowledge as context
            context_text = "Consider the following domain-specific knowledge:\n\n"
            for item in relevant_items:
                context_text += f"- {item.name}"
                if config.include_definitions and item.definition:
                    context_text += f": {item.definition}"
                context_text += "\n"

                # Add relationships if requested
                if config.include_relationships and item.relationships:
                    for rel_type, related_items in item.relationships.items():
                        context_text += f"  - {rel_type}: {', '.join(related_items)}\n"

            return f"{context_text}\n\nWith that context, please respond to: {prompt}"

        elif config.mode == PromptEnhancementMode.SYSTEM_MESSAGE:
            # Format as system message (for chat models)
            system_message = {
                "role": "system",
                "content": "You are a domain expert with specialized knowledge in the following concepts:\n\n",
            }

            for item in relevant_items:
                system_message["content"] += f"- {item.name}"
                if config.include_definitions and item.definition:
                    system_message["content"] += f": {item.definition}"
                system_message["content"] += "\n"

                # Add relationships if requested
                if config.include_relationships and item.relationships:
                    for rel_type, related_items in item.relationships.items():
                        system_message[
                            "content"
                        ] += f"  - {rel_type}: {', '.join(related_items)}\n"

            user_message = {"role": "user", "content": prompt}

            # Return as JSON string for integration with chat models
            return json.dumps([system_message, user_message])

        elif config.mode == PromptEnhancementMode.INJECTION:
            # Inject knowledge directly into prompt
            enhanced_prompt = prompt

            # Find terms in the prompt that match domain knowledge
            for item in relevant_items:
                term = item.name
                if term in prompt:
                    if config.include_definitions and item.definition:
                        # Inject definition
                        definition = f" ({item.definition})"
                        enhanced_prompt = enhanced_prompt.replace(
                            term, f"{term}{definition}"
                        )

            return enhanced_prompt

        elif config.mode == PromptEnhancementMode.TEMPLATE:
            # Use custom template
            if not config.template:
                return prompt

            # Prepare knowledge variables
            knowledge_vars = {
                "domain": config.domain,
                "terms": [],
                "definitions": {},
                "relationships": {},
            }

            for item in relevant_items:
                knowledge_vars["terms"].append(item.name)
                if item.definition:
                    knowledge_vars["definitions"][item.name] = item.definition
                if item.relationships:
                    knowledge_vars["relationships"][item.name] = item.relationships

            # Apply template
            template = config.template
            template = template.replace("{{prompt}}", prompt)
            template = template.replace("{{domain}}", config.domain)

            # Replace terms list
            if "{{terms}}" in template:
                terms_text = ", ".join(knowledge_vars["terms"])
                template = template.replace("{{terms}}", terms_text)

            # Replace definitions dictionary
            if "{{definitions}}" in template:
                definitions_text = ""
                for term, definition in knowledge_vars["definitions"].items():
                    definitions_text += f"- {term}: {definition}\n"
                template = template.replace("{{definitions}}", definitions_text)

            # Replace relationships
            if "{{relationships}}" in template:
                relationships_text = ""
                for term, relations in knowledge_vars["relationships"].items():
                    relationships_text += f"- {term} relationships:\n"
                    for rel_type, related_items in relations.items():
                        relationships_text += (
                            f"  - {rel_type}: {', '.join(related_items)}\n"
                        )
                template = template.replace("{{relationships}}", relationships_text)

            return template

        elif config.mode == PromptEnhancementMode.CUSTOM:
            # Use custom formatter
            if not config.custom_formatter:
                return prompt

            # Try to get custom formatter
            try:
                import importlib

                module_path, formatter_name = config.custom_formatter.rsplit(".", 1)
                module = importlib.import_module(module_path)
                formatter = getattr(module, formatter_name)

                return formatter(prompt, relevant_items, config)

            except Exception as e:
                self.logger.error(f"Error using custom formatter: {e}")
                return prompt

        else:
            return prompt

    async def close(self) -> None:
        """Close the knowledge manager and release resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None

        self.initialized = False


# Factory function for domain knowledge managers
async def create_domain_knowledge_manager(
    domain: str,
    connection_string: str | None = None,
    embedding_service=None,
    logger: logging.Logger | None = None,
) -> Tuple[DomainKnowledgeManager, Dict[str, Any]]:
    """
    Create a domain knowledge manager and load domain knowledge.

    Args:
        domain: Domain name
        connection_string: Database connection string
        embedding_service: Service for generating embeddings
        logger: Optional logger

    Returns:
        Tuple of (knowledge manager, domain statistics)
    """
    # Create knowledge manager
    manager = DomainKnowledgeManager(
        connection_string=connection_string,
        embedding_service=embedding_service,
        logger=logger,
    )

    # Initialize manager
    await manager.initialize()

    # Get domain statistics
    stats = {"domain": domain, "glossary_terms": 0, "taxonomy_relationships": 0}

    # Load glossary
    glossary = await manager.get_domain_glossary(domain)
    stats["glossary_terms"] = len(glossary)

    # Load taxonomy
    taxonomy = await manager.get_domain_taxonomy(domain)
    stats["taxonomy_relationships"] = len(taxonomy)

    return manager, stats
