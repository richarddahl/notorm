"""
Embedding models for AI capabilities.

This module provides a unified interface to different embedding models,
which convert text and other content into vector representations for
semantic operations like search and clustering.
"""

import os
import importlib.util
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Type

import numpy as np

# Set up logger
logger = logging.getLogger(__name__)


class EmbeddingModel(ABC):
    """Base class for embedding models that convert text to vector representations."""

    def __init__(self, model_name: str, dimensions: int):
        """
        Initialize the embedding model.

        Args:
            model_name: Name or identifier for the model
            dimensions: Number of dimensions in the embedding vectors
        """
        self.model_name = model_name
        self.dimensions = dimensions

    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """
        Convert text to a vector embedding.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as numpy array
        """
        pass

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Convert multiple texts to vector embeddings.

        Args:
            texts: List of texts to embed

        Returns:
            Array of vector embeddings
        """
        # Default implementation calls embed for each text
        # Subclasses should override for efficiency
        return np.vstack([self.embed(text) for text in texts])


class SentenceTransformerModel(EmbeddingModel):
    """Embedding model using sentence-transformers library."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the sentence-transformer model.

        Args:
            model_name: Name of the model to use
        """
        # Check if sentence-transformers is installed
        if not importlib.util.find_spec("sentence_transformers"):
            raise ImportError(
                "sentence-transformers package is required. "
                "Install it with: pip install sentence-transformers"
            )

        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        dimensions = self.model.get_sentence_embedding_dimension()

        super().__init__(model_name, dimensions)

    def embed(self, text: str) -> np.ndarray:
        """
        Embed text using the sentence transformer model.

        Args:
            text: Text to embed

        Returns:
            Vector embedding
        """
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Embed multiple texts efficiently using the sentence transformer model.

        Args:
            texts: List of texts to embed

        Returns:
            Array of vector embeddings
        """
        return self.model.encode(texts, convert_to_numpy=True)


class OpenAIEmbeddingModel(EmbeddingModel):
    """Embedding model using OpenAI's API."""

    def __init__(
        self,
        model_name: str = "text-embedding-ada-002",
        api_key: str | None = None,
        dimensions: Optional[int] = None,
    ):
        """
        Initialize the OpenAI embedding model.

        Args:
            model_name: Name of the OpenAI embedding model
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
            dimensions: Manually specify dimensions (optional)
        """
        # Check if openai is installed
        if not importlib.util.find_spec("openai"):
            raise ImportError(
                "openai package is required. " "Install it with: pip install openai"
            )

        import openai

        # Set API key from parameter or environment
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Provide it as a parameter "
                "or set the OPENAI_API_KEY environment variable."
            )

        openai.api_key = self.api_key
        self.client = openai.OpenAI()

        # Model dimensions based on model name
        dimensions_map = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }

        # Use provided dimensions or look up from map
        if dimensions is None:
            model_dimensions = dimensions_map.get(model_name, 1536)
        else:
            model_dimensions = dimensions

        super().__init__(model_name, model_dimensions)

    def embed(self, text: str) -> np.ndarray:
        """
        Embed text using OpenAI's API.

        Args:
            text: Text to embed

        Returns:
            Vector embedding
        """
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return np.array(response.data[0].embedding)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Embed multiple texts using OpenAI's API.

        Args:
            texts: List of texts to embed

        Returns:
            Array of vector embeddings
        """
        response = self.client.embeddings.create(model=self.model_name, input=texts)
        return np.array([data.embedding for data in response.data])


class EmbeddingRegistry:
    """Registry for managing embedding models."""

    def __init__(self):
        """Initialize the embedding registry."""
        self.models: Dict[str, EmbeddingModel] = {}

    def register(self, name: str, model: EmbeddingModel) -> None:
        """
        Register an embedding model.

        Args:
            name: Name to register the model under
            model: Embedding model instance
        """
        self.models[name] = model

    def get(self, name: str) -> EmbeddingModel:
        """
        Get a registered embedding model.

        Args:
            name: Name of the model to retrieve

        Returns:
            Embedding model instance

        Raises:
            ValueError: If model not found
        """
        if name not in self.models:
            raise ValueError(f"Embedding model '{name}' not found in registry")
        return self.models[name]

    def list_models(self) -> list[str]:
        """
        List all registered model names.

        Returns:
            List of model names
        """
        return list(self.models.keys())

    def create_and_register(
        self, name: str, model_type: str, **kwargs: Any
    ) -> EmbeddingModel:
        """
        Create and register a new embedding model.

        Args:
            name: Name to register the model under
            model_type: Type of model ("sentence_transformer" or "openai")
            **kwargs: Arguments to pass to the model constructor

        Returns:
            Created embedding model instance

        Raises:
            ValueError: For unknown model type
        """
        if model_type == "sentence_transformer":
            model = SentenceTransformerModel(**kwargs)
        elif model_type == "openai":
            model = OpenAIEmbeddingModel(**kwargs)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        self.register(name, model)
        return model


# Global embedding registry
embedding_registry = EmbeddingRegistry()

# Try to register default models
try:
    default_model = SentenceTransformerModel()
    embedding_registry.register("default", default_model)
    logger.info(f"Registered default embedding model: {default_model.model_name}")
except ImportError:
    logger.info(
        "Could not register default embedding model. Install sentence-transformers package for local embedding."
    )
except Exception as e:
    logger.warning(f"Error registering default embedding model: {str(e)}")


def get_embedding_model(name: str = "default") -> EmbeddingModel:
    """
    Get an embedding model from the registry.

    Args:
        name: Name of the registered model

    Returns:
        Embedding model instance
    """
    return embedding_registry.get(name)
