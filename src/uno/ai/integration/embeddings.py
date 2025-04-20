"""
Shared embedding infrastructure for AI features.

This module provides a centralized service for text embedding across different
AI features, including semantic search, recommendations, content generation,
anomaly detection, and other AI capabilities.
"""

import asyncio
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field, validator

# Try to import various embedding libraries based on availability
try:
    import torch
    import transformers

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import sentence_transformers

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import openai

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class EmbeddingType(str, Enum):
    """Type of embedding model to use."""

    SENTENCE_TRANSFORMER = "sentence_transformer"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    CUSTOM = "custom"


class EmbeddingModelConfig(BaseModel):
    """Configuration for embedding models."""

    model_type: EmbeddingType
    model_name: str
    dimension: int = 384
    api_key: str | None = None
    cache_dir: str | None = None
    batch_size: int = 32
    max_length: int = 512
    normalize: bool = True
    pooling_strategy: str = "mean"
    device: str | None = None
    additional_config: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingCacheEntry(BaseModel):
    """Cache entry for embeddings."""

    text_hash: str
    embedding: list[float]
    model_name: str
    created_at: float = Field(default_factory=lambda: asyncio.get_event_loop().time())

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SharedEmbeddingService:
    """
    Shared embedding service for all AI features.

    This service provides a unified interface for creating text embeddings
    across different AI features, with support for multiple embedding models,
    caching, and batch processing.
    """

    def __init__(
        self,
        default_model_config: Optional[EmbeddingModelConfig] = None,
        models: Optional[Dict[str, EmbeddingModelConfig]] = None,
        cache_size: int = 10000,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the shared embedding service.

        Args:
            default_model_config: Configuration for the default embedding model
            models: Dictionary mapping model names to their configurations
            cache_size: Maximum number of embeddings to keep in memory
            logger: Logger to use
        """
        self.default_model_config = default_model_config
        self.models = models or {}
        self.cache_size = cache_size
        self.logger = logger or logging.getLogger(__name__)

        # Embedding models
        self.embedding_models = {}

        # In-memory cache
        self.embedding_cache: Dict[str, EmbeddingCacheEntry] = {}

        # Initialize locks for thread safety
        self.model_locks = {}

        # Initialized flag
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the embedding service and load models."""
        if self.initialized:
            return

        # Set up default model config if not provided
        if not self.default_model_config:
            if HAS_SENTENCE_TRANSFORMERS:
                self.default_model_config = EmbeddingModelConfig(
                    model_type=EmbeddingType.SENTENCE_TRANSFORMER,
                    model_name="all-MiniLM-L6-v2",
                    dimension=384,
                )
            elif HAS_TRANSFORMERS:
                self.default_model_config = EmbeddingModelConfig(
                    model_type=EmbeddingType.HUGGINGFACE,
                    model_name="bert-base-uncased",
                    dimension=768,
                )
            elif HAS_OPENAI:
                self.default_model_config = EmbeddingModelConfig(
                    model_type=EmbeddingType.OPENAI,
                    model_name="text-embedding-3-small",
                    dimension=1536,
                    api_key=os.environ.get("OPENAI_API_KEY"),
                )
            else:
                raise ImportError(
                    "No embedding libraries found. Please install at least one of: "
                    "sentence-transformers, transformers, or openai"
                )

        # Load default model
        await self._load_model(self.default_model_config)

        # Load additional models
        for model_name, model_config in self.models.items():
            try:
                await self._load_model(model_config)
            except Exception as e:
                self.logger.warning(f"Failed to load model {model_name}: {e}")

        self.initialized = True

    async def close(self) -> None:
        """Close the embedding service and release resources."""
        # Clear cache
        self.embedding_cache.clear()

        # Close any resources
        self.embedding_models.clear()

        self.initialized = False

    async def embed_text(
        self,
        text: str,
        model_name: str | None = None,
        normalize: Optional[bool] = None,
    ) -> np.ndarray:
        """
        Embed a single text string.

        Args:
            text: The text to embed
            model_name: Name of the model to use, or None for default
            normalize: Whether to normalize the embedding vector

        Returns:
            Embedding vector as numpy array
        """
        if not self.initialized:
            await self.initialize()

        embeddings = await self.embed_batch([text], model_name, normalize)
        return embeddings[0]

    async def embed_batch(
        self,
        texts: list[str],
        model_name: str | None = None,
        normalize: Optional[bool] = None,
    ) -> list[np.ndarray]:
        """
        Embed a batch of text strings.

        Args:
            texts: List of texts to embed
            model_name: Name of the model to use, or None for default
            normalize: Whether to normalize the embedding vectors

        Returns:
            List of embedding vectors as numpy arrays
        """
        if not self.initialized:
            await self.initialize()

        if not texts:
            return []

        # Use default model if not specified
        if not model_name:
            model_name = self.default_model_config.model_name

        # Check if model is loaded
        if model_name not in self.embedding_models:
            if model_name in self.models:
                await self._load_model(self.models[model_name])
            else:
                self.logger.warning(
                    f"Model {model_name} not found, using default model"
                )
                model_name = self.default_model_config.model_name

        # Get model and config
        model = self.embedding_models[model_name]
        config = self.models.get(model_name, self.default_model_config)

        # Check cache for each text
        uncached_texts = []
        uncached_indices = []
        cached_embeddings = {}

        for i, text in enumerate(texts):
            text_hash = self._hash_text(text, model_name)
            if text_hash in self.embedding_cache:
                cached_embeddings[i] = self.embedding_cache[text_hash].embedding
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # If there are uncached texts, compute embeddings
        if uncached_texts:
            # Acquire lock for this model to prevent concurrent computation
            if model_name not in self.model_locks:
                self.model_locks[model_name] = asyncio.Lock()

            async with self.model_locks[model_name]:
                # Compute embeddings
                try:
                    if config.model_type == EmbeddingType.SENTENCE_TRANSFORMER:
                        embeddings = await self._embed_with_sentence_transformer(
                            model, uncached_texts, config
                        )
                    elif config.model_type == EmbeddingType.HUGGINGFACE:
                        embeddings = await self._embed_with_huggingface(
                            model, uncached_texts, config
                        )
                    elif config.model_type == EmbeddingType.OPENAI:
                        embeddings = await self._embed_with_openai(
                            model, uncached_texts, config
                        )
                    elif config.model_type == EmbeddingType.CUSTOM:
                        embeddings = await self._embed_with_custom_model(
                            model, uncached_texts, config
                        )
                    else:
                        raise ValueError(f"Unsupported model type: {config.model_type}")

                    # Normalize if requested
                    if normalize is not None and normalize:
                        for i in range(len(embeddings)):
                            norm = np.linalg.norm(embeddings[i])
                            if norm > 0:
                                embeddings[i] = embeddings[i] / norm
                    elif normalize is None and config.normalize:
                        for i in range(len(embeddings)):
                            norm = np.linalg.norm(embeddings[i])
                            if norm > 0:
                                embeddings[i] = embeddings[i] / norm

                    # Cache embeddings
                    for i, text in enumerate(uncached_texts):
                        text_hash = self._hash_text(text, model_name)
                        self.embedding_cache[text_hash] = EmbeddingCacheEntry(
                            text_hash=text_hash,
                            embedding=embeddings[i].tolist(),
                            model_name=model_name,
                        )

                    # Store in result dictionary
                    for i, idx in enumerate(uncached_indices):
                        cached_embeddings[idx] = embeddings[i]

                except Exception as e:
                    self.logger.error(f"Failed to compute embeddings: {e}")
                    # Return zeros for failed embeddings
                    for idx in uncached_indices:
                        cached_embeddings[idx] = np.zeros(config.dimension)

        # Prune cache if it exceeds size limit
        if len(self.embedding_cache) > self.cache_size:
            self._prune_cache()

        # Return embeddings in original order
        result = []
        for i in range(len(texts)):
            if i in cached_embeddings:
                if isinstance(cached_embeddings[i], list):
                    result.append(np.array(cached_embeddings[i], dtype=np.float32))
                else:
                    result.append(cached_embeddings[i])
            else:
                result.append(np.zeros(config.dimension, dtype=np.float32))

        return result

    async def import_embeddings(
        self, embeddings: Dict[str, list[float]], model_name: str | None = None
    ) -> None:
        """
        Import pre-computed embeddings into the cache.

        Args:
            embeddings: Dictionary mapping text to embedding vectors
            model_name: Name of the model used for the embeddings
        """
        if not self.initialized:
            await self.initialize()

        # Use default model if not specified
        if not model_name:
            model_name = self.default_model_config.model_name

        # Add embeddings to cache
        for text, embedding in embeddings.items():
            text_hash = self._hash_text(text, model_name)
            self.embedding_cache[text_hash] = EmbeddingCacheEntry(
                text_hash=text_hash, embedding=embedding, model_name=model_name
            )

        # Prune cache if it exceeds size limit
        if len(self.embedding_cache) > self.cache_size:
            self._prune_cache()

    def compute_similarity(
        self,
        embedding1: Union[list[float], np.ndarray],
        embedding2: Union[list[float], np.ndarray],
        method: str = "cosine",
    ) -> float:
        """
        Compute similarity between two embedding vectors.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            method: Similarity method ("cosine", "dot", "euclidean")

        Returns:
            Similarity score (higher means more similar)
        """
        # Convert to numpy arrays
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1, dtype=np.float32)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2, dtype=np.float32)

        # Compute similarity
        if method == "cosine":
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            if norm1 > 0 and norm2 > 0:
                return np.dot(embedding1, embedding2) / (norm1 * norm2)
            return 0.0
        elif method == "dot":
            return float(np.dot(embedding1, embedding2))
        elif method == "euclidean":
            dist = np.linalg.norm(embedding1 - embedding2)
            # Convert to similarity (0-1 range, higher is more similar)
            return float(1.0 / (1.0 + dist))
        else:
            raise ValueError(f"Unsupported similarity method: {method}")

    async def nearest_neighbors(
        self,
        query_embedding: Union[list[float], np.ndarray],
        texts: list[str],
        model_name: str | None = None,
        k: int = 5,
        similarity_method: str = "cosine",
        threshold: Optional[float] = None,
    ) -> list[Tuple[str, float]]:
        """
        Find nearest neighbors to a query embedding among a list of texts.

        Args:
            query_embedding: Query embedding vector
            texts: List of texts to search
            model_name: Name of the model to use for text embedding
            k: Number of neighbors to return
            similarity_method: Method to compute similarity
            threshold: Minimum similarity threshold

        Returns:
            List of (text, similarity) tuples
        """
        if not self.initialized:
            await self.initialize()

        # Convert query embedding to numpy array
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding, dtype=np.float32)

        # Embed texts
        text_embeddings = await self.embed_batch(texts, model_name)

        # Compute similarities
        similarities = []
        for i, embedding in enumerate(text_embeddings):
            similarity = self.compute_similarity(
                query_embedding, embedding, similarity_method
            )
            if threshold is None or similarity >= threshold:
                similarities.append((texts[i], similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top k
        return similarities[:k]

    async def _load_model(self, config: EmbeddingModelConfig) -> None:
        """
        Load an embedding model based on configuration.

        Args:
            config: Model configuration
        """
        model_name = config.model_name
        model_type = config.model_type

        # Check if model is already loaded
        if model_name in self.embedding_models:
            return

        try:
            # Load model based on type
            if model_type == EmbeddingType.SENTENCE_TRANSFORMER:
                if not HAS_SENTENCE_TRANSFORMERS:
                    raise ImportError("sentence-transformers is not installed")

                model = sentence_transformers.SentenceTransformer(
                    model_name, cache_folder=config.cache_dir
                )

                # Set device if specified
                if config.device:
                    model = model.to(config.device)

            elif model_type == EmbeddingType.HUGGINGFACE:
                if not HAS_TRANSFORMERS:
                    raise ImportError("transformers is not installed")

                # Get tokenizer and model
                tokenizer = transformers.AutoTokenizer.from_pretrained(
                    model_name, cache_dir=config.cache_dir
                )

                model = transformers.AutoModel.from_pretrained(
                    model_name, cache_dir=config.cache_dir
                )

                # Set device if specified
                if config.device:
                    model = model.to(config.device)

                # Store tokenizer along with the model
                model = (model, tokenizer)

            elif model_type == EmbeddingType.OPENAI:
                if not HAS_OPENAI:
                    raise ImportError("openai is not installed")

                # For OpenAI, we just need a client
                if config.api_key:
                    client = openai.Client(api_key=config.api_key)
                else:
                    client = openai.Client()

                model = client

            elif model_type == EmbeddingType.CUSTOM:
                # For custom models, we need a user-provided model
                if "model" not in config.additional_config:
                    raise ValueError(
                        "Custom model requires a 'model' in additional_config"
                    )

                model = config.additional_config["model"]

            else:
                raise ValueError(f"Unsupported model type: {model_type}")

            # Store model
            self.embedding_models[model_name] = model

            # Store config
            self.models[model_name] = config

            self.logger.info(f"Loaded embedding model {model_name}")

        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            raise

    async def _embed_with_sentence_transformer(
        self, model, texts: list[str], config: EmbeddingModelConfig
    ) -> list[np.ndarray]:
        """
        Embed texts with a SentenceTransformer model.

        Args:
            model: SentenceTransformer model
            texts: List of texts to embed
            config: Model configuration

        Returns:
            List of embedding vectors
        """
        # Process in batches
        all_embeddings = []

        # Create batches
        for start_idx in range(0, len(texts), config.batch_size):
            end_idx = min(start_idx + config.batch_size, len(texts))
            batch = texts[start_idx:end_idx]

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, model.encode, batch, None, None, config.pooling_strategy
            )

            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _embed_with_huggingface(
        self, model_tuple, texts: list[str], config: EmbeddingModelConfig
    ) -> list[np.ndarray]:
        """
        Embed texts with a Hugging Face Transformers model.

        Args:
            model_tuple: (Model, Tokenizer) tuple
            texts: List of texts to embed
            config: Model configuration

        Returns:
            List of embedding vectors
        """
        model, tokenizer = model_tuple

        # Process in batches
        all_embeddings = []

        # Run in a non-blocking way
        for start_idx in range(0, len(texts), config.batch_size):
            end_idx = min(start_idx + config.batch_size, len(texts))
            batch = texts[start_idx:end_idx]

            # Tokenize
            loop = asyncio.get_event_loop()
            encoded_input = await loop.run_in_executor(
                None,
                lambda: tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=config.max_length,
                    return_tensors="pt",
                ),
            )

            # Move to device if needed
            if config.device:
                encoded_input = {
                    k: v.to(config.device) for k, v in encoded_input.items()
                }

            # Get embeddings
            with torch.no_grad():
                loop = asyncio.get_event_loop()
                outputs = await loop.run_in_executor(
                    None, lambda: model(**encoded_input)
                )

            # Use pooling strategy
            if config.pooling_strategy == "cls":
                embeddings = outputs.last_hidden_state[:, 0].cpu().numpy()
            elif config.pooling_strategy == "mean":
                attention_mask = encoded_input["attention_mask"]
                embeddings = (
                    self._mean_pooling(outputs.last_hidden_state, attention_mask)
                    .cpu()
                    .numpy()
                )
            else:
                raise ValueError(
                    f"Unsupported pooling strategy: {config.pooling_strategy}"
                )

            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _embed_with_openai(
        self, client, texts: list[str], config: EmbeddingModelConfig
    ) -> list[np.ndarray]:
        """
        Embed texts with an OpenAI embedding model.

        Args:
            client: OpenAI client
            texts: List of texts to embed
            config: Model configuration

        Returns:
            List of embedding vectors
        """
        # Process in batches
        all_embeddings = []

        # OpenAI has rate limits, so we need to handle batching
        for start_idx in range(0, len(texts), config.batch_size):
            end_idx = min(start_idx + config.batch_size, len(texts))
            batch = texts[start_idx:end_idx]

            # Handle API rate limits
            max_retries = 3
            retry_delay = 1.0

            for retry in range(max_retries):
                try:
                    response = await client.embeddings.create(
                        model=config.model_name, input=batch
                    )

                    for embedding_data in response.data:
                        all_embeddings.append(
                            np.array(embedding_data.embedding, dtype=np.float32)
                        )

                    break

                except Exception as e:
                    if retry < max_retries - 1:
                        self.logger.warning(
                            f"OpenAI API error, retrying in {retry_delay}s: {e}"
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        self.logger.error(
                            f"OpenAI API error after {max_retries} retries: {e}"
                        )
                        # Return zeros for failed embeddings
                        for _ in range(len(batch)):
                            all_embeddings.append(
                                np.zeros(config.dimension, dtype=np.float32)
                            )

        return all_embeddings

    async def _embed_with_custom_model(
        self, model, texts: list[str], config: EmbeddingModelConfig
    ) -> list[np.ndarray]:
        """
        Embed texts with a custom model.

        Args:
            model: Custom model
            texts: List of texts to embed
            config: Model configuration

        Returns:
            List of embedding vectors
        """
        # Custom embedding function should be provided in additional_config
        if "embed_function" not in config.additional_config:
            raise ValueError(
                "Custom model requires an 'embed_function' in additional_config"
            )

        embed_function = config.additional_config["embed_function"]

        # Check if function is async
        if asyncio.iscoroutinefunction(embed_function):
            return await embed_function(model, texts, config)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, embed_function, model, texts, config
            )

    def _mean_pooling(self, token_embeddings, attention_mask):
        """
        Mean pooling for transformer models.

        Args:
            token_embeddings: Token embeddings from model
            attention_mask: Attention mask

        Returns:
            Pooled embeddings
        """
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def _hash_text(self, text: str, model_name: str) -> str:
        """
        Create a hash for text and model name.

        Args:
            text: Text to hash
            model_name: Model name

        Returns:
            Hash string
        """
        import hashlib

        return hashlib.md5(f"{text}:{model_name}".encode()).hexdigest()

    def _prune_cache(self) -> None:
        """Prune the least recently used items from the cache."""
        # Sort items by creation time (oldest first)
        items = sorted(self.embedding_cache.items(), key=lambda x: x[1].created_at)

        # Remove oldest items until we're under the limit
        items_to_remove = max(len(items) - self.cache_size, len(items) // 4)
        for text_hash, _ in items[:items_to_remove]:
            if text_hash in self.embedding_cache:
                del self.embedding_cache[text_hash]


class EnhancedRAGService:
    """
    Enhanced RAG (Retrieval Augmented Generation) service.

    This service integrates context management, embedding, and content generation
    to provide sophisticated RAG capabilities for the application.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        context_manager=None,
        embedding_service=None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the enhanced RAG service.

        Args:
            connection_string: Database connection string
            context_manager: Optional context manager to use
            embedding_service: Optional embedding service to use
            logger: Logger to use
        """
        self.connection_string = connection_string
        self.context_manager = context_manager
        self.embedding_service = embedding_service
        self.logger = logger or logging.getLogger(__name__)

        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the RAG service."""
        if self.initialized:
            return

        # Initialize context manager if not provided
        if not self.context_manager:
            from uno.ai.integration.context import UnifiedContextManager

            self.context_manager = UnifiedContextManager(
                connection_string=self.connection_string, logger=self.logger
            )
            await self.context_manager.initialize()

        # Initialize embedding service if not provided
        if not self.embedding_service:
            self.embedding_service = SharedEmbeddingService(logger=self.logger)
            await self.embedding_service.initialize()

        self.initialized = True

    async def close(self) -> None:
        """Close the RAG service and release resources."""
        if self.context_manager:
            await self.context_manager.close()

        if self.embedding_service:
            await self.embedding_service.close()

        self.initialized = False

    async def retrieve_context(
        self,
        query: str,
        user_id: str | None = None,
        session_id: str | None = None,
        entity_id: str | None = None,
        entity_type: str | None = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant context for a query.

        Args:
            query: The query to find context for
            user_id: Optional user ID
            session_id: Optional session ID
            entity_id: Optional entity ID
            entity_type: Optional entity type
            limit: Maximum number of context items to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of context items
        """
        if not self.initialized:
            await self.initialize()

        # Create embedding for query
        query_embedding = await self.embedding_service.embed_text(query)

        # Use context manager to find relevant context by embedding
        context_items = await self.context_manager.query_by_embedding(
            embedding=query_embedding.tolist(),
            entity_type=entity_type,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )

        # Also get recent context for the user/session/entity
        recent_items = []

        if user_id:
            user_items = await self.context_manager.get_user_context(
                user_id=user_id, limit=limit
            )
            recent_items.extend(user_items)

        if session_id:
            session_items = await self.context_manager.get_session_context(
                session_id=session_id, limit=limit
            )
            recent_items.extend(session_items)

        if entity_id:
            entity_items = await self.context_manager.get_entity_context(
                entity_id=entity_id, entity_type=entity_type, limit=limit
            )
            recent_items.extend(entity_items)

        # Combine embedding-based and recent items
        all_items = set()
        results = []

        # Add embedding-based items first (with similarity score)
        for item, similarity in context_items:
            if item.id not in all_items:
                all_items.add(item.id)
                result_dict = item.to_dict()
                result_dict["similarity"] = similarity
                results.append(result_dict)

        # Add recent items if not already included
        for item in recent_items:
            if item.id not in all_items:
                all_items.add(item.id)
                result_dict = item.to_dict()
                result_dict["recency"] = True
                results.append(result_dict)

        # Sort by similarity or recency
        results.sort(
            key=lambda x: x.get("similarity", 0.0) if "similarity" in x else 0.5,
            reverse=True,
        )

        # Apply final limit
        if len(results) > limit:
            results = results[:limit]

        return results

    async def enrich_rag_prompt(
        self,
        prompt: str,
        user_id: str | None = None,
        session_id: str | None = None,
        entity_id: str | None = None,
        entity_type: str | None = None,
        anomaly_context: bool = True,
        recommendation_context: bool = True,
        search_context: bool = True,
    ) -> str:
        """
        Enrich a RAG prompt with relevant context.

        Args:
            prompt: The original prompt
            user_id: Optional user ID
            session_id: Optional session ID
            entity_id: Optional entity ID
            entity_type: Optional entity type
            anomaly_context: Whether to include anomaly detection context
            recommendation_context: Whether to include recommendation context
            search_context: Whether to include search context

        Returns:
            Enriched prompt with context
        """
        if not self.initialized:
            await self.initialize()

        # Retrieve context for the prompt
        context_items = await self.retrieve_context(
            query=prompt,
            user_id=user_id,
            session_id=session_id,
            entity_id=entity_id,
            entity_type=entity_type,
        )

        # Filter context based on source flags
        filtered_context = []
        for item in context_items:
            source = item.get("source")

            if not anomaly_context and source == "anomaly_detection":
                continue

            if not recommendation_context and source == "recommendation":
                continue

            if not search_context and source == "search":
                continue

            filtered_context.append(item)

        # Build enriched prompt
        if not filtered_context:
            return prompt

        # Format context for inclusion in prompt
        context_section = "\n\nContextual Information:\n"

        for idx, item in enumerate(filtered_context):
            context_section += f"\n[Context {idx+1}]\n"
            context_section += f"Type: {item.get('type')}\n"
            context_section += f"Source: {item.get('source')}\n"

            # Add entity information if available
            if item.get("entity_type") and item.get("entity_id"):
                context_section += (
                    f"Entity: {item.get('entity_type')}/{item.get('entity_id')}\n"
                )

            # Add value based on type
            value = item.get("value")
            if isinstance(value, str):
                context_section += f"Content: {value}\n"
            elif isinstance(value, (list, dict)):
                try:
                    import json

                    context_section += f"Content: {json.dumps(value, indent=2)}\n"
                except:
                    context_section += f"Content: (Complex value)\n"
            else:
                context_section += f"Content: {str(value)}\n"

            # Add relevance info
            if "similarity" in item:
                context_section += f"Relevance: {item.get('similarity'):.2f}\n"

            context_section += "\n"

        # Combine with original prompt
        enriched_prompt = prompt + context_section

        return enriched_prompt
