"""
Content generation engine for the Uno framework.

This module provides a unified interface for text generation, summarization,
and transformation, leveraging both PostgreSQL pgvector and Apache AGE graph
database for enhanced contextual understanding.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from enum import Enum

import numpy as np

from uno.ai.embeddings import EmbeddingModel, get_embedding_model
from uno.ai.vector_storage import VectorStorage, create_vector_storage

# Set up logger
logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Type of content to generate."""

    TEXT = "text"
    SUMMARY = "summary"
    BULLETS = "bullets"
    TITLE = "title"
    DESCRIPTION = "description"
    RESPONSE = "response"
    QUESTION = "question"


class ContentMode(str, Enum):
    """Mode of content generation."""

    CREATIVE = "creative"
    BALANCED = "balanced"
    PRECISE = "precise"


class ContentFormat(str, Enum):
    """Format of generated content."""

    PLAIN = "plain"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"


class RAGStrategy(str, Enum):
    """Strategy for Retrieval Augmented Generation."""

    VECTOR_ONLY = "vector_only"  # Only use vector search
    GRAPH_ONLY = "graph_only"  # Only use graph traversal
    HYBRID = "hybrid"  # Use both with equal weight
    ADAPTIVE = "adaptive"  # Dynamically choose based on query


class ContentEngine:
    """
    Engine for content generation using retrieval augmented generation.

    Combines vector search with graph database for enhanced context awareness
    in generating, summarizing, and transforming content.
    """

    def __init__(
        self,
        embedding_model: Union[str, EmbeddingModel] = "default",
        vector_storage: Optional[VectorStorage] = None,
        connection_string: str | None = None,
        table_name: str = "content_embeddings",
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        use_graph_db: bool = True,
        graph_schema: str | None = None,
        rag_strategy: RAGStrategy = RAGStrategy.HYBRID,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ):
        """
        Initialize the content engine.

        Args:
            embedding_model: Embedding model or name of registered model
            vector_storage: Vector storage instance (optional)
            connection_string: Database connection string (if no storage provided)
            table_name: Table name for vector storage
            llm_provider: Provider for language model (openai, anthropic, local)
            llm_model: Model name for language model
            api_key: API key for language model provider
            use_graph_db: Whether to use Apache AGE graph database
            graph_schema: Schema for graph database
            rag_strategy: Strategy for retrieval augmented generation
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0-1)
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
                "storage_type": "pgvector",
                "connection_string": connection_string,
                "table_name": table_name,
                "dimensions": self.embedding_model.dimensions,
            }

        # Set up LLM
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Set up graph DB
        self.use_graph_db = use_graph_db
        self.graph_schema = graph_schema
        self.graph_connection = None

        # Set RAG strategy
        self.rag_strategy = rag_strategy

        # Tracking
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the content engine."""
        if self.initialized:
            return

        # Create vector storage if needed
        if self.vector_storage is None:
            self.vector_storage = await create_vector_storage(**self._storage_params)

        # Initialize LLM client
        await self._initialize_llm()

        # Initialize graph database connection if enabled
        if self.use_graph_db:
            await self._initialize_graph_db()

        self.initialized = True
        logger.info(
            f"Initialized ContentEngine with model {self.embedding_model.model_name} "
            f"and LLM {self.llm_provider}/{self.llm_model}"
        )

    async def _initialize_llm(self) -> None:
        """Initialize the language model client."""
        if self.llm_provider == "openai":
            try:
                import openai
                import os
            except ImportError:
                raise ImportError(
                    "openai package is required for OpenAI provider. "
                    "Install it with: pip install openai"
                )

            # Set API key from parameter or environment
            api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key is required. Provide it as a parameter "
                    "or set the OPENAI_API_KEY environment variable."
                )

            openai.api_key = api_key
            self.llm_client = openai.OpenAI()

        elif self.llm_provider == "anthropic":
            try:
                import anthropic
                import os
            except ImportError:
                raise ImportError(
                    "anthropic package is required for Anthropic provider. "
                    "Install it with: pip install anthropic"
                )

            # Set API key from parameter or environment
            api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "Anthropic API key is required. Provide it as a parameter "
                    "or set the ANTHROPIC_API_KEY environment variable."
                )

            self.llm_client = anthropic.Anthropic(api_key=api_key)

        elif self.llm_provider == "local":
            # Local implementation would depend on the specific framework
            # This is a placeholder for a local LLM implementation
            logger.warning("Local LLM provider not fully implemented")
            self.llm_client = None

        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    async def _initialize_graph_db(self) -> None:
        """Initialize the Apache AGE graph database connection."""
        try:
            import asyncpg
        except ImportError:
            raise ImportError(
                "asyncpg package is required for graph database connection. "
                "Install it with: pip install asyncpg"
            )

        # Extract connection parameters from the vector storage connection string
        conn_params = {}
        if hasattr(self.vector_storage, "connection_string"):
            conn_string = self.vector_storage.connection_string
            # Simple parsing for common formats
            parts = conn_string.split("://")[1].split("@")
            if len(parts) > 1:
                auth = parts[0].split(":")
                if len(auth) > 1:
                    conn_params["user"] = auth[0]
                    conn_params["password"] = auth[1]

                host_parts = parts[1].split("/")
                if len(host_parts) > 1:
                    host_port = host_parts[0].split(":")
                    conn_params["host"] = host_port[0]
                    if len(host_port) > 1:
                        conn_params["port"] = int(host_port[1])
                    conn_params["database"] = host_parts[1]

        # Create connection
        try:
            self.graph_connection = await asyncpg.connect(**conn_params)

            # Check if Apache AGE extension is available
            extension_exists = await self.graph_connection.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'age')"
            )

            if not extension_exists:
                logger.warning(
                    "Apache AGE extension is not installed in the database. "
                    "Graph capabilities will be limited."
                )
                self.use_graph_db = False
            else:
                # Load AGE extension
                await self.graph_connection.execute("LOAD 'age';")

                # Create graph if schema is provided
                if self.graph_schema:
                    await self.graph_connection.execute(
                        f"SELECT create_graph('{self.graph_schema}');"
                    )

                logger.info("Successfully connected to Apache AGE graph database")
        except Exception as e:
            logger.error(f"Failed to connect to graph database: {e}")
            self.use_graph_db = False

    async def index_content(
        self,
        content: str,
        entity_id: str,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        graph_nodes: Optional[list[dict[str, Any]]] = None,
        graph_relationships: Optional[list[dict[str, Any]]] = None,
    ) -> Any:
        """
        Index content for retrieval augmented generation.

        Args:
            content: Text content to index
            entity_id: Unique identifier for the content
            entity_type: Type of content
            metadata: Additional metadata about the content
            graph_nodes: Optional additional nodes to add to the graph
            graph_relationships: Optional relationships to add to the graph

        Returns:
            ID of the indexed content
        """
        if not self.initialized:
            await self.initialize()

        # Create combined metadata
        combined_metadata = metadata or {}

        # Generate embedding
        embedding = self.embedding_model.embed(content)

        # Store in vector database
        record_id = await self.vector_storage.store(
            entity_id=entity_id,
            entity_type=entity_type,
            embedding=embedding,
            metadata=combined_metadata,
        )

        # Add to graph database if enabled
        if self.use_graph_db and self.graph_connection:
            try:
                await self._add_to_graph(
                    content=content,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    metadata=combined_metadata,
                    additional_nodes=graph_nodes,
                    relationships=graph_relationships,
                )
            except Exception as e:
                logger.error(f"Failed to add content to graph database: {e}")

        logger.debug(f"Indexed content {entity_id} of type {entity_type}")
        return record_id

    async def _add_to_graph(
        self,
        content: str,
        entity_id: str,
        entity_type: str,
        metadata: Dict[str, Any],
        additional_nodes: Optional[list[dict[str, Any]]] = None,
        relationships: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """
        Add content to the graph database.

        Args:
            content: Text content
            entity_id: Unique identifier for the content
            entity_type: Type of content
            metadata: Additional metadata about the content
            additional_nodes: Additional nodes to add to the graph
            relationships: Relationships to add to the graph
        """
        if not self.graph_connection:
            return

        # Create content node
        content_props = {
            "id": entity_id,
            "type": entity_type,
            "content": content[:1000],  # Limit content length
            **metadata,
        }

        # Convert properties to json for Cypher
        content_props_json = json.dumps(content_props)

        # Add content node
        try:
            # Use the graph schema if provided, otherwise use 'public'
            graph_name = self.graph_schema or "public"

            # Create node using AGE Cypher
            await self.graph_connection.execute(
                f"""
                SELECT * FROM cypher('{graph_name}', $$ 
                    MERGE (c:{entity_type} {{id: '{entity_id}'}})
                    SET c = {content_props_json}::jsonb
                    RETURN c
                $$) as (c agtype);
                """
            )

            # Add additional nodes
            if additional_nodes:
                for node in additional_nodes:
                    node_label = node.get("label", "Entity")
                    node_id = node.get("id")
                    if not node_id:
                        continue

                    node_props = json.dumps(node)

                    await self.graph_connection.execute(
                        f"""
                        SELECT * FROM cypher('{graph_name}', $$ 
                            MERGE (n:{node_label} {{id: '{node_id}'}})
                            SET n = {node_props}::jsonb
                            RETURN n
                        $$) as (n agtype);
                        """
                    )

            # Add relationships
            if relationships:
                for rel in relationships:
                    from_id = rel.get("from_id")
                    to_id = rel.get("to_id")
                    from_type = rel.get("from_type", "Entity")
                    to_type = rel.get("to_type", "Entity")
                    rel_type = rel.get("type", "RELATED_TO")
                    rel_props = json.dumps(rel.get("properties", {}))

                    if not from_id or not to_id:
                        continue

                    await self.graph_connection.execute(
                        f"""
                        SELECT * FROM cypher('{graph_name}', $$ 
                            MATCH (a:{from_type} {{id: '{from_id}'}}), (b:{to_type} {{id: '{to_id}'}})
                            MERGE (a)-[r:{rel_type}]->(b)
                            SET r = {rel_props}::jsonb
                            RETURN r
                        $$) as (r agtype);
                        """
                    )

        except Exception as e:
            logger.error(f"Error adding to graph database: {e}")
            # Continue without failing the indexing process

    async def generate_content(
        self,
        prompt: str,
        content_type: ContentType = ContentType.TEXT,
        mode: ContentMode = ContentMode.BALANCED,
        format: ContentFormat = ContentFormat.PLAIN,
        max_length: int = 500,
        context_entity_ids: list[str] | None = None,
        context_entity_types: list[str] | None = None,
        rag_strategy: Optional[RAGStrategy] = None,
        max_context_items: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate content using retrieval augmented generation.

        Args:
            prompt: Content generation prompt
            content_type: Type of content to generate
            mode: Generation mode (creative, balanced, precise)
            format: Output format
            max_length: Maximum length of generated content
            context_entity_ids: Optional specific entity IDs to include as context
            context_entity_types: Optional entity types to search for context
            rag_strategy: Strategy for retrieval (overrides default)
            max_context_items: Maximum number of context items to retrieve

        Returns:
            Generated content with metadata
        """
        if not self.initialized:
            await self.initialize()

        # Set strategy
        strategy = rag_strategy or self.rag_strategy

        # Retrieve context
        context = await self._retrieve_context(
            query=prompt,
            strategy=strategy,
            entity_ids=context_entity_ids,
            entity_types=context_entity_types,
            max_items=max_context_items,
        )

        # Format prompt with context
        formatted_prompt = self._format_prompt(
            prompt=prompt,
            context=context,
            content_type=content_type,
            mode=mode,
            format=format,
            max_length=max_length,
        )

        # Generate content
        content = await self._generate(
            prompt=formatted_prompt,
            max_tokens=min(self.max_tokens, max_length * 4),  # Estimate tokens
            temperature=self._get_temperature(mode),
        )

        # Process response
        processed_content = self._process_response(content, format)

        # Put together the result
        result = {
            "content": processed_content,
            "content_type": content_type,
            "mode": mode,
            "format": format,
            "prompt": prompt,
            "context_count": len(context),
            "context_sources": [item.get("entity_id") for item in context],
        }

        return result

    async def summarize(
        self,
        text: str,
        max_length: int = 200,
        format: ContentFormat = ContentFormat.PLAIN,
        mode: ContentMode = ContentMode.BALANCED,
        bullet_points: bool = False,
    ) -> Dict[str, Any]:
        """
        Summarize text content.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            format: Output format
            mode: Summarization mode
            bullet_points: Whether to generate bullet points

        Returns:
            Summary with metadata
        """
        if not self.initialized:
            await self.initialize()

        # Determine content type
        content_type = ContentType.BULLETS if bullet_points else ContentType.SUMMARY

        # Create prompt
        prompt = f"Summarize the following text"
        if bullet_points:
            prompt += " as a list of bullet points"
        if max_length:
            prompt += f" in {max_length} characters or less"

        prompt += ":\n\n" + text

        # Generate summary without RAG (we already have the content)
        formatted_prompt = self._format_prompt(
            prompt=prompt,
            context=[],  # No additional context needed
            content_type=content_type,
            mode=mode,
            format=format,
            max_length=max_length,
        )

        # Generate content
        content = await self._generate(
            prompt=formatted_prompt,
            max_tokens=min(self.max_tokens, max_length * 4),
            temperature=self._get_temperature(mode),
        )

        # Process response
        processed_content = self._process_response(content, format)

        # Put together the result
        result = {
            "content": processed_content,
            "content_type": content_type,
            "mode": mode,
            "format": format,
            "original_length": len(text),
            "summary_length": len(processed_content),
            "reduction_ratio": (
                len(processed_content) / len(text) if len(text) > 0 else 0
            ),
        }

        return result

    async def _retrieve_context(
        self,
        query: str,
        strategy: RAGStrategy,
        entity_ids: list[str] | None = None,
        entity_types: list[str] | None = None,
        max_items: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve context for generation.

        Args:
            query: Query text
            strategy: Retrieval strategy
            entity_ids: Optional specific entity IDs to include
            entity_types: Optional entity types to search for
            max_items: Maximum number of context items

        Returns:
            List of context items
        """
        # If specific entity IDs are provided, use those directly
        if entity_ids:
            # Stub for direct entity retrieval
            # In a real implementation, we would fetch these entities
            # from the vector storage or graph DB
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.embed(query)

        vector_results = []
        graph_results = []

        # Get vector search results if strategy calls for it
        if strategy in [
            RAGStrategy.VECTOR_ONLY,
            RAGStrategy.HYBRID,
            RAGStrategy.ADAPTIVE,
        ]:
            # Search vector database
            vector_results = await self.vector_storage.search(
                query_embedding=query_embedding,
                entity_type=(
                    entity_types[0] if entity_types and len(entity_types) == 1 else None
                ),
                limit=max_items,
                similarity_threshold=0.6,
            )

        # Get graph results if strategy calls for it
        if (
            strategy
            in [RAGStrategy.GRAPH_ONLY, RAGStrategy.HYBRID, RAGStrategy.ADAPTIVE]
            and self.use_graph_db
            and self.graph_connection
        ):
            # Get related content from graph
            try:
                graph_results = await self._retrieve_from_graph(
                    query=query, entity_types=entity_types, max_items=max_items
                )
            except Exception as e:
                logger.error(f"Error retrieving from graph: {e}")

        # Combine results based on strategy
        if strategy == RAGStrategy.VECTOR_ONLY:
            return vector_results
        elif strategy == RAGStrategy.GRAPH_ONLY:
            return graph_results
        elif strategy == RAGStrategy.HYBRID:
            # Simple interleaving of results
            combined = []
            max_len = max(len(vector_results), len(graph_results))

            for i in range(max_len):
                if i < len(vector_results):
                    combined.append(vector_results[i])
                if i < len(graph_results):
                    combined.append(graph_results[i])

            # Deduplicate by entity_id
            seen_ids = set()
            unique_results = []

            for result in combined[:max_items]:
                entity_id = result.get("entity_id")
                if entity_id not in seen_ids:
                    seen_ids.add(entity_id)
                    unique_results.append(result)

            return unique_results
        elif strategy == RAGStrategy.ADAPTIVE:
            # Choose best strategy based on query analysis
            # This is a placeholder for more sophisticated logic
            # For now, prefer vector results for factual queries,
            # and graph results for relationship-oriented queries

            # Simple heuristic: check if query contains relationship keywords
            relationship_keywords = [
                "related",
                "connection",
                "linked",
                "associated",
                "between",
            ]
            has_relationship_focus = any(
                keyword in query.lower() for keyword in relationship_keywords
            )

            if has_relationship_focus and graph_results:
                primary_results = graph_results
                secondary_results = vector_results
            else:
                primary_results = vector_results
                secondary_results = graph_results

            # Combine with preference for primary results
            combined = list(primary_results)

            # Add secondary results not already included
            seen_ids = {result.get("entity_id") for result in combined}

            for result in secondary_results:
                entity_id = result.get("entity_id")
                if entity_id not in seen_ids and len(combined) < max_items:
                    seen_ids.add(entity_id)
                    combined.append(result)

            return combined[:max_items]

        # Default fallback
        return vector_results

    async def _retrieve_from_graph(
        self, query: str, entity_types: list[str] | None = None, max_items: int = 5
    ) -> list[dict[str, Any]]:
        """
        Retrieve context from graph database.

        Args:
            query: Query text
            entity_types: Optional entity types to search for
            max_items: Maximum number of context items

        Returns:
            List of context items from graph
        """
        if not self.graph_connection:
            return []

        # Extract key terms from query for graph search
        # This is a simplified approach - in a real implementation,
        # we might use NLP to extract entities, concepts, etc.
        key_terms = self._extract_key_terms(query)

        # Skip common words
        common_words = {
            "the",
            "and",
            "is",
            "in",
            "to",
            "a",
            "of",
            "for",
            "with",
            "on",
            "at",
        }
        key_terms = [term for term in key_terms if term.lower() not in common_words]

        # Limit to the most significant terms
        key_terms = key_terms[:3]

        if not key_terms:
            return []

        # Create graph query
        graph_name = self.graph_schema or "public"
        type_clause = ""

        if entity_types and len(entity_types) > 0:
            type_labels = [f"n:{entity_type}" for entity_type in entity_types]
            type_clause = f"WHERE {' OR '.join(type_labels)}"

        # Build term matching conditions
        term_conditions = []
        for term in key_terms:
            # Escape single quotes
            escaped_term = term.replace("'", "\\'")
            term_conditions.append(f"n.content CONTAINS '{escaped_term}'")

        term_clause = f"WHERE {' OR '.join(term_conditions)}"
        if type_clause:
            term_clause = f"AND ({' OR '.join(term_conditions)})"

        # Cypher query
        cypher_query = f"""
        SELECT * FROM cypher('{graph_name}', $$ 
            MATCH (n)
            {type_clause}
            {term_clause}
            RETURN n
            LIMIT {max_items}
        $$) as (n agtype);
        """

        try:
            rows = await self.graph_connection.fetch(cypher_query)

            # Parse results
            results = []
            for row in rows:
                # Parse AGE JSON format to Python dict
                graph_node = self._parse_agtype(row["n"])

                if not graph_node:
                    continue

                # Extract properties
                entity_id = graph_node.get("id")
                entity_type = graph_node.get("type", "unknown")
                content = graph_node.get("content", "")

                # Add result
                results.append(
                    {
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "content": content,
                        "metadata": {
                            k: v
                            for k, v in graph_node.items()
                            if k not in ["id", "type", "content"]
                        },
                        "source": "graph",
                    }
                )

            return results
        except Exception as e:
            logger.error(f"Error executing graph query: {e}")
            return []

    def _parse_agtype(self, agtype_value: str) -> Dict[str, Any]:
        """
        Parse AGE agtype value to Python dictionary.

        Args:
            agtype_value: AGE agtype value

        Returns:
            Parsed Python dictionary
        """
        # This is a simplified parser for AGE agtype
        # In a real implementation, we would use proper AGE parsing

        try:
            # Try direct JSON parsing first
            return json.loads(agtype_value)
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: simple string parsing
        try:
            if isinstance(agtype_value, str):
                # Extract properties part
                properties_match = agtype_value.split("{", 1)
                if len(properties_match) > 1:
                    properties_str = "{" + properties_match[1]
                    # Remove trailing parentheses if present
                    if properties_str.endswith("}"):
                        properties_str = properties_str[:-1]

                    # Try parsing as JSON
                    return json.loads(properties_str)
        except Exception:
            pass

        # Return empty dict if parsing fails
        return {}

    def _extract_key_terms(self, text: str) -> list[str]:
        """
        Extract key terms from text for graph search.

        Args:
            text: Input text

        Returns:
            List of key terms
        """
        # Simple word-based extraction
        # In a real implementation, we might use NLP techniques
        words = text.split()

        # Remove punctuation and normalize
        terms = []
        for word in words:
            # Remove common punctuation
            word = word.strip(".,;:!?\"'()[]{}")
            if word and len(word) > 2:  # Skip short words
                terms.append(word)

        return terms

    def _format_prompt(
        self,
        prompt: str,
        context: list[dict[str, Any]],
        content_type: ContentType,
        mode: ContentMode,
        format: ContentFormat,
        max_length: int,
    ) -> str:
        """
        Format prompt with context and instructions.

        Args:
            prompt: User prompt
            context: Retrieved context items
            content_type: Type of content to generate
            mode: Generation mode
            format: Output format
            max_length: Maximum content length

        Returns:
            Formatted prompt
        """
        formatted_prompt = ""

        # Add system instructions
        formatted_prompt += (
            "You are an AI assistant that generates high-quality content. "
        )

        # Add mode-specific instructions
        if mode == ContentMode.CREATIVE:
            formatted_prompt += "Be creative, expressive, and engaging. "
        elif mode == ContentMode.PRECISE:
            formatted_prompt += "Be concise, accurate, and factual. "
        else:  # BALANCED
            formatted_prompt += "Balance creativity with accuracy and clarity. "

        # Add content type instructions
        if content_type == ContentType.SUMMARY:
            formatted_prompt += "Create a concise summary. "
        elif content_type == ContentType.BULLETS:
            formatted_prompt += "Create a bulleted list of key points. "
        elif content_type == ContentType.TITLE:
            formatted_prompt += "Generate an attention-grabbing title. "
        elif content_type == ContentType.DESCRIPTION:
            formatted_prompt += "Write a descriptive overview. "
        elif content_type == ContentType.RESPONSE:
            formatted_prompt += "Craft a helpful response. "
        elif content_type == ContentType.QUESTION:
            formatted_prompt += "Generate thoughtful questions. "

        # Add format instructions
        if format == ContentFormat.HTML:
            formatted_prompt += "Format the output as HTML. "
        elif format == ContentFormat.MARKDOWN:
            formatted_prompt += "Format the output as Markdown. "
        elif format == ContentFormat.JSON:
            formatted_prompt += "Format the output as valid JSON. "

        # Add length constraint
        if max_length:
            formatted_prompt += f"Keep the output under {max_length} characters. "

        # Add context
        if context:
            formatted_prompt += "\n\nRelevant context:\n"

            for i, item in enumerate(context):
                content = item.get("content", "")
                entity_id = item.get("entity_id", "unknown")
                formatted_prompt += (
                    f"[{i+1}] Source: {entity_id}\nContent: {content}\n\n"
                )

        # Add user prompt
        formatted_prompt += f"\nTask: {prompt}\n\n"

        return formatted_prompt

    def _get_temperature(self, mode: ContentMode) -> float:
        """
        Get temperature value for generation mode.

        Args:
            mode: Generation mode

        Returns:
            Temperature value (0-1)
        """
        if mode == ContentMode.CREATIVE:
            return min(1.0, self.temperature + 0.2)
        elif mode == ContentMode.PRECISE:
            return max(0.0, self.temperature - 0.4)
        else:  # BALANCED
            return self.temperature

    async def _generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """
        Generate content using language model.

        Args:
            prompt: Formatted prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature value

        Returns:
            Generated content
        """
        if self.llm_provider == "openai":
            try:
                response = await self._generate_openai(
                    prompt=prompt, max_tokens=max_tokens, temperature=temperature
                )
                return response
            except Exception as e:
                logger.error(f"Error generating with OpenAI: {e}")
                return f"Error generating content: {str(e)}"

        elif self.llm_provider == "anthropic":
            try:
                response = await self._generate_anthropic(
                    prompt=prompt, max_tokens=max_tokens, temperature=temperature
                )
                return response
            except Exception as e:
                logger.error(f"Error generating with Anthropic: {e}")
                return f"Error generating content: {str(e)}"

        elif self.llm_provider == "local":
            # Placeholder for local LLM
            return "Local LLM generation not implemented"

        else:
            return "Unsupported LLM provider"

    async def _generate_openai(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Generate content using OpenAI.

        Args:
            prompt: Formatted prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature value

        Returns:
            Generated content
        """
        response = self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that generates high-quality content.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()

    async def _generate_anthropic(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Generate content using Anthropic.

        Args:
            prompt: Formatted prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature value

        Returns:
            Generated content
        """
        response = self.llm_client.completions.create(
            prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
            model=self.llm_model,
            max_tokens_to_sample=max_tokens,
            temperature=temperature,
        )

        return response.completion.strip()

    def _process_response(self, content: str, format: ContentFormat) -> str:
        """
        Process and validate the response format.

        Args:
            content: Generated content
            format: Expected format

        Returns:
            Processed content
        """
        if format == ContentFormat.JSON:
            # Ensure valid JSON
            try:
                # Extract JSON if surrounded by backticks or markdown code block
                if "```json" in content and "```" in content.split("```json", 1)[1]:
                    json_str = content.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in content and "```" in content.split("```", 1)[1]:
                    json_str = content.split("```", 1)[1].split("```", 1)[0].strip()
                else:
                    json_str = content

                # Validate by parsing
                parsed = json.loads(json_str)
                return json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                # If not valid JSON, try to clean up
                logger.warning("Generated content is not valid JSON, attempting to fix")

                try:
                    # Try to find content that looks like JSON
                    if "{" in content and "}" in content:
                        potential_json = content[
                            content.find("{") : content.rfind("}") + 1
                        ]
                        parsed = json.loads(potential_json)
                        return json.dumps(parsed, ensure_ascii=False)
                except:
                    # Return as is if fixing fails
                    return content

        return content

    async def close(self) -> None:
        """Close the content engine and release resources."""
        if self.vector_storage:
            await self.vector_storage.close()

        if self.graph_connection:
            await self.graph_connection.close()

        self.initialized = False
