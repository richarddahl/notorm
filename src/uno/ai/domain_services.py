"""
Domain services for the AI module.

This module defines the core domain services for the AI module,
implementing business logic for AI features like embeddings, semantic search,
recommendations, content generation, and anomaly detection.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union, TypeVar, Type, Generic
from datetime import datetime, UTC

from uno.core.result import Result, Success, Failure
from uno.domain.service import DomainService

from uno.ai.entities import (
    EmbeddingId,
    SearchQueryId,
    RecommendationId,
    ContentRequestId,
    AnomalyDetectionId,
    ModelId,
    EmbeddingModel,
    Embedding,
    SearchQuery,
    SearchResult,
    DocumentIndex,
    RecommendationProfile,
    RecommendationRequest,
    Recommendation,
    ContentRequest,
    GeneratedContent,
    AnomalyDetectionConfig,
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    AIContext,
    RAGQuery,
    EmbeddingModelType,
    ContentGenerationType,
    AnomalyDetectionMethod,
    RecommendationMethod
)
from uno.ai.domain_repositories import (
    EmbeddingModelRepositoryProtocol,
    EmbeddingRepositoryProtocol,
    SearchRepositoryProtocol,
    RecommendationRepositoryProtocol,
    ContentGenerationRepositoryProtocol,
    AnomalyDetectionRepositoryProtocol,
    AIContextRepositoryProtocol
)


class EmbeddingModelService(DomainService):
    """Service for managing embedding models."""
    
    def __init__(
        self,
        model_repository: EmbeddingModelRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the embedding model service.
        
        Args:
            model_repository: Repository for embedding models
            logger: Optional logger
        """
        self.model_repository = model_repository
        self.logger = logger or logging.getLogger("uno.ai.embedding_model")
    
    async def create_model(
        self,
        name: str,
        model_type: EmbeddingModelType,
        dimensions: int,
        api_key: Optional[str] = None,
        normalize_vectors: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[EmbeddingModel]:
        """
        Create a new embedding model.
        
        Args:
            name: Model name
            model_type: Type of model
            dimensions: Number of dimensions
            api_key: Optional API key
            normalize_vectors: Whether to normalize vectors
            metadata: Optional metadata
            
        Returns:
            Result containing the created model or an error
        """
        try:
            # Check if model already exists
            existing_result = await self.model_repository.get_by_name(name)
            if isinstance(existing_result, Success):
                return Result.failure(f"Model '{name}' already exists")
            
            # Create model entity
            model = EmbeddingModel(
                id=ModelId(str(uuid.uuid4())),
                name=name,
                model_type=model_type,
                dimensions=dimensions,
                api_key=api_key,
                normalize_vectors=normalize_vectors,
                metadata=metadata or {}
            )
            
            # Save to repository
            return await self.model_repository.create(model)
        except Exception as e:
            self.logger.error(f"Failed to create model: {str(e)}")
            return Result.failure(f"Failed to create model: {str(e)}")
    
    async def get_model(self, model_id: Union[str, ModelId]) -> Result[EmbeddingModel]:
        """
        Get an embedding model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Result containing the model or an error if not found
        """
        try:
            if isinstance(model_id, str):
                model_id = ModelId(model_id)
            
            return await self.model_repository.get(model_id)
        except Exception as e:
            self.logger.error(f"Failed to get model: {str(e)}")
            return Result.failure(f"Failed to get model: {str(e)}")
    
    async def get_model_by_name(self, name: str) -> Result[EmbeddingModel]:
        """
        Get an embedding model by name.
        
        Args:
            name: Model name
            
        Returns:
            Result containing the model or an error if not found
        """
        try:
            return await self.model_repository.get_by_name(name)
        except Exception as e:
            self.logger.error(f"Failed to get model by name: {str(e)}")
            return Result.failure(f"Failed to get model by name: {str(e)}")
    
    async def update_model(
        self,
        model_id: Union[str, ModelId],
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        normalize_vectors: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[EmbeddingModel]:
        """
        Update an embedding model.
        
        Args:
            model_id: Model ID
            name: New name (optional)
            api_key: New API key (optional)
            normalize_vectors: New normalization setting (optional)
            metadata: New metadata (optional)
            
        Returns:
            Result containing the updated model or an error
        """
        try:
            if isinstance(model_id, str):
                model_id = ModelId(model_id)
            
            # Get existing model
            model_result = await self.model_repository.get(model_id)
            if isinstance(model_result, Failure):
                return model_result
            
            model = model_result.value
            
            # Update fields
            if name is not None:
                model.name = name
            if api_key is not None:
                model.api_key = api_key
            if normalize_vectors is not None:
                model.normalize_vectors = normalize_vectors
            if metadata is not None:
                model.metadata.update(metadata)
            
            # Save to repository
            return await self.model_repository.update(model)
        except Exception as e:
            self.logger.error(f"Failed to update model: {str(e)}")
            return Result.failure(f"Failed to update model: {str(e)}")
    
    async def delete_model(self, model_id: Union[str, ModelId]) -> Result[bool]:
        """
        Delete an embedding model.
        
        Args:
            model_id: Model ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            if isinstance(model_id, str):
                model_id = ModelId(model_id)
            
            return await self.model_repository.delete(model_id)
        except Exception as e:
            self.logger.error(f"Failed to delete model: {str(e)}")
            return Result.failure(f"Failed to delete model: {str(e)}")
    
    async def list_models(self) -> Result[List[EmbeddingModel]]:
        """
        List all embedding models.
        
        Returns:
            Result containing a list of models or an error
        """
        try:
            return await self.model_repository.list()
        except Exception as e:
            self.logger.error(f"Failed to list models: {str(e)}")
            return Result.failure(f"Failed to list models: {str(e)}")


class EmbeddingService(DomainService):
    """Service for generating and managing embeddings."""
    
    def __init__(
        self,
        embedding_repository: EmbeddingRepositoryProtocol,
        model_service: EmbeddingModelService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            embedding_repository: Repository for embeddings
            model_service: Service for embedding models
            logger: Optional logger
        """
        self.embedding_repository = embedding_repository
        self.model_service = model_service
        self.logger = logger or logging.getLogger("uno.ai.embedding")
        self.models = {}  # Cache for loaded models
    
    async def generate_embedding(
        self,
        text: str,
        model_name: Optional[str] = None
    ) -> Result[List[float]]:
        """
        Generate an embedding vector for text.
        
        Args:
            text: Text to embed
            model_name: Optional model name to use
            
        Returns:
            Result containing the embedding vector or an error
        """
        try:
            # Get the model (default if not specified)
            if not model_name:
                model_name = "default"
            
            model_result = await self.model_service.get_model_by_name(model_name)
            if isinstance(model_result, Failure):
                return Result.failure(f"Model '{model_name}' not found")
            
            model = model_result.value
            
            # Load the model if not cached
            embedding_model = await self._get_or_load_model(model)
            
            # Generate embedding
            if model.model_type == EmbeddingModelType.SENTENCE_TRANSFORMER:
                vector = await self._embed_with_sentence_transformer(embedding_model, text, model)
            elif model.model_type == EmbeddingModelType.OPENAI:
                vector = await self._embed_with_openai(embedding_model, text, model)
            elif model.model_type == EmbeddingModelType.HUGGINGFACE:
                vector = await self._embed_with_huggingface(embedding_model, text, model)
            else:
                return Result.failure(f"Unsupported model type: {model.model_type}")
            
            # Normalize if needed
            if model.normalize_vectors:
                import numpy as np
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = (vector / norm).tolist()
            
            return Result.success(vector)
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {str(e)}")
            return Result.failure(f"Failed to generate embedding: {str(e)}")
    
    async def create_embedding(
        self,
        text: str,
        source_id: str,
        source_type: str,
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[Embedding]:
        """
        Create and store an embedding for text.
        
        Args:
            text: Text to embed
            source_id: Source ID
            source_type: Source type
            model_name: Optional model name to use
            metadata: Optional metadata
            
        Returns:
            Result containing the created embedding or an error
        """
        try:
            # Generate the embedding vector
            vector_result = await self.generate_embedding(text, model_name)
            if isinstance(vector_result, Failure):
                return vector_result
            
            vector = vector_result.value
            
            # Get the model
            if not model_name:
                model_name = "default"
            
            model_result = await self.model_service.get_model_by_name(model_name)
            if isinstance(model_result, Failure):
                return Result.failure(f"Model '{model_name}' not found")
            
            model = model_result.value
            
            # Create embedding entity
            embedding = Embedding(
                id=EmbeddingId(str(uuid.uuid4())),
                vector=vector,
                model_id=model.id,
                source_id=source_id,
                source_type=source_type,
                dimensions=len(vector),
                metadata=metadata or {}
            )
            
            # Save to repository
            return await self.embedding_repository.create(embedding)
        except Exception as e:
            self.logger.error(f"Failed to create embedding: {str(e)}")
            return Result.failure(f"Failed to create embedding: {str(e)}")
    
    async def get_embedding(self, embedding_id: Union[str, EmbeddingId]) -> Result[Embedding]:
        """
        Get an embedding by ID.
        
        Args:
            embedding_id: Embedding ID
            
        Returns:
            Result containing the embedding or an error if not found
        """
        try:
            if isinstance(embedding_id, str):
                embedding_id = EmbeddingId(embedding_id)
            
            return await self.embedding_repository.get(embedding_id)
        except Exception as e:
            self.logger.error(f"Failed to get embedding: {str(e)}")
            return Result.failure(f"Failed to get embedding: {str(e)}")
    
    async def get_embedding_by_source(self, source_id: str, source_type: str) -> Result[Embedding]:
        """
        Get an embedding by source.
        
        Args:
            source_id: Source ID
            source_type: Source type
            
        Returns:
            Result containing the embedding or an error if not found
        """
        try:
            return await self.embedding_repository.get_by_source(source_id, source_type)
        except Exception as e:
            self.logger.error(f"Failed to get embedding by source: {str(e)}")
            return Result.failure(f"Failed to get embedding by source: {str(e)}")
    
    async def batch_create_embeddings(
        self,
        texts: List[str],
        source_ids: List[str],
        source_type: str,
        model_name: Optional[str] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> Result[List[Embedding]]:
        """
        Batch create embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            source_ids: List of corresponding source IDs
            source_type: Source type
            model_name: Optional model name to use
            metadata_list: Optional list of metadata dictionaries
            
        Returns:
            Result containing the created embeddings or an error
        """
        try:
            if len(texts) != len(source_ids):
                return Result.failure("Number of texts and source IDs must match")
            
            if metadata_list and len(metadata_list) != len(texts):
                return Result.failure("Number of metadata items must match number of texts")
            
            # Get the model
            if not model_name:
                model_name = "default"
            
            model_result = await self.model_service.get_model_by_name(model_name)
            if isinstance(model_result, Failure):
                return Result.failure(f"Model '{model_name}' not found")
            
            model = model_result.value
            
            # Load the model
            embedding_model = await self._get_or_load_model(model)
            
            # Generate embeddings in batch
            vectors = []
            if model.model_type == EmbeddingModelType.SENTENCE_TRANSFORMER:
                vectors = await self._embed_batch_with_sentence_transformer(embedding_model, texts, model)
            elif model.model_type == EmbeddingModelType.OPENAI:
                vectors = await self._embed_batch_with_openai(embedding_model, texts, model)
            elif model.model_type == EmbeddingModelType.HUGGINGFACE:
                vectors = await self._embed_batch_with_huggingface(embedding_model, texts, model)
            else:
                return Result.failure(f"Unsupported model type: {model.model_type}")
            
            # Normalize if needed
            if model.normalize_vectors:
                import numpy as np
                for i, vector in enumerate(vectors):
                    norm = np.linalg.norm(vector)
                    if norm > 0:
                        vectors[i] = (vector / norm).tolist()
            
            # Create embedding entities
            embeddings = []
            for i, (vector, source_id) in enumerate(zip(vectors, source_ids)):
                metadata = metadata_list[i] if metadata_list else {}
                
                embedding = Embedding(
                    id=EmbeddingId(str(uuid.uuid4())),
                    vector=vector,
                    model_id=model.id,
                    source_id=source_id,
                    source_type=source_type,
                    dimensions=len(vector),
                    metadata=metadata
                )
                
                embeddings.append(embedding)
            
            # Save to repository
            return await self.embedding_repository.batch_create(embeddings)
        except Exception as e:
            self.logger.error(f"Failed to batch create embeddings: {str(e)}")
            return Result.failure(f"Failed to batch create embeddings: {str(e)}")
    
    async def compute_similarity(
        self,
        embedding1: Union[List[float], Embedding],
        embedding2: Union[List[float], Embedding],
        metric: str = "cosine"
    ) -> Result[float]:
        """
        Compute similarity between two embeddings.
        
        Args:
            embedding1: First embedding or vector
            embedding2: Second embedding or vector
            metric: Similarity metric to use
            
        Returns:
            Result containing the similarity score or an error
        """
        try:
            # Extract vectors if needed
            vector1 = embedding1.vector if isinstance(embedding1, Embedding) else embedding1
            vector2 = embedding2.vector if isinstance(embedding2, Embedding) else embedding2
            
            # Compute similarity
            import numpy as np
            if metric == "cosine":
                # Cosine similarity
                vec1 = np.array(vector1)
                vec2 = np.array(vector2)
                
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 == 0 or norm2 == 0:
                    return Result.success(0.0)
                
                similarity = np.dot(vec1, vec2) / (norm1 * norm2)
                return Result.success(float(similarity))
            
            elif metric == "euclidean":
                # Euclidean distance converted to similarity
                vec1 = np.array(vector1)
                vec2 = np.array(vector2)
                
                distance = np.linalg.norm(vec1 - vec2)
                # Convert to similarity (0-1 range, higher is more similar)
                similarity = 1.0 / (1.0 + distance)
                return Result.success(float(similarity))
            
            elif metric == "dot_product":
                # Dot product
                vec1 = np.array(vector1)
                vec2 = np.array(vector2)
                
                similarity = np.dot(vec1, vec2)
                return Result.success(float(similarity))
            
            else:
                return Result.failure(f"Unsupported similarity metric: {metric}")
        except Exception as e:
            self.logger.error(f"Failed to compute similarity: {str(e)}")
            return Result.failure(f"Failed to compute similarity: {str(e)}")
    
    async def _get_or_load_model(self, model: EmbeddingModel) -> Any:
        """
        Get a loaded model or load it if not cached.
        
        Args:
            model: The model configuration
            
        Returns:
            Loaded model instance
        """
        # Check if model is already loaded
        if model.id.value in self.models:
            return self.models[model.id.value]
        
        # Load model based on type
        if model.model_type == EmbeddingModelType.SENTENCE_TRANSFORMER:
            try:
                import sentence_transformers
                
                # Load model
                model_instance = sentence_transformers.SentenceTransformer(model.name)
                self.models[model.id.value] = model_instance
                return model_instance
            except ImportError:
                raise ImportError("sentence-transformers is not installed")
        
        elif model.model_type == EmbeddingModelType.OPENAI:
            try:
                import openai
                
                # Create client
                if model.api_key:
                    client = openai.Client(api_key=model.api_key)
                else:
                    client = openai.Client()
                
                self.models[model.id.value] = client
                return client
            except ImportError:
                raise ImportError("openai is not installed")
        
        elif model.model_type == EmbeddingModelType.HUGGINGFACE:
            try:
                import torch
                from transformers import AutoTokenizer, AutoModel
                
                # Load tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(model.name)
                model_instance = AutoModel.from_pretrained(model.name)
                
                self.models[model.id.value] = (model_instance, tokenizer)
                return (model_instance, tokenizer)
            except ImportError:
                raise ImportError("transformers is not installed")
        
        else:
            raise ValueError(f"Unsupported model type: {model.model_type}")
    
    async def _embed_with_sentence_transformer(
        self,
        model,
        text: str,
        config: EmbeddingModel
    ) -> List[float]:
        """
        Generate embedding with SentenceTransformer.
        
        Args:
            model: SentenceTransformer model
            text: Text to embed
            config: Model configuration
            
        Returns:
            Embedding vector
        """
        import asyncio
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, model.encode, text)
        
        return embedding.tolist()
    
    async def _embed_with_openai(
        self,
        client,
        text: str,
        config: EmbeddingModel
    ) -> List[float]:
        """
        Generate embedding with OpenAI.
        
        Args:
            client: OpenAI client
            text: Text to embed
            config: Model configuration
            
        Returns:
            Embedding vector
        """
        # Call OpenAI API
        response = await client.embeddings.create(
            model=config.name, 
            input=text
        )
        
        return response.data[0].embedding
    
    async def _embed_with_huggingface(
        self,
        model_tuple,
        text: str,
        config: EmbeddingModel
    ) -> List[float]:
        """
        Generate embedding with Hugging Face model.
        
        Args:
            model_tuple: (Model, Tokenizer) tuple
            text: Text to embed
            config: Model configuration
            
        Returns:
            Embedding vector
        """
        import torch
        import asyncio
        
        model, tokenizer = model_tuple
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Define encoding function
        def encode():
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Use [CLS] token or mean pooling
            if config.metadata.get("pooling_strategy") == "cls":
                embedding = outputs.last_hidden_state[:, 0].numpy()
            else:
                # Mean pooling
                attention_mask = inputs["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                embedding = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
                    input_mask_expanded.sum(1), min=1e-9
                ).numpy()
            
            return embedding[0].tolist()
        
        # Execute encoding
        embedding = await loop.run_in_executor(None, encode)
        
        return embedding
    
    async def _embed_batch_with_sentence_transformer(
        self,
        model,
        texts: List[str],
        config: EmbeddingModel
    ) -> List[List[float]]:
        """
        Generate embeddings in batch with SentenceTransformer.
        
        Args:
            model: SentenceTransformer model
            texts: Texts to embed
            config: Model configuration
            
        Returns:
            List of embedding vectors
        """
        import asyncio
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, model.encode, texts)
        
        return [embedding.tolist() for embedding in embeddings]
    
    async def _embed_batch_with_openai(
        self,
        client,
        texts: List[str],
        config: EmbeddingModel
    ) -> List[List[float]]:
        """
        Generate embeddings in batch with OpenAI.
        
        Args:
            client: OpenAI client
            texts: Texts to embed
            config: Model configuration
            
        Returns:
            List of embedding vectors
        """
        # Call OpenAI API
        response = await client.embeddings.create(
            model=config.name, 
            input=texts
        )
        
        # Sort results by index
        embeddings = [None] * len(texts)
        for embedding_data in response.data:
            embeddings[embedding_data.index] = embedding_data.embedding
        
        return embeddings
    
    async def _embed_batch_with_huggingface(
        self,
        model_tuple,
        texts: List[str],
        config: EmbeddingModel
    ) -> List[List[float]]:
        """
        Generate embeddings in batch with Hugging Face model.
        
        Args:
            model_tuple: (Model, Tokenizer) tuple
            texts: Texts to embed
            config: Model configuration
            
        Returns:
            List of embedding vectors
        """
        import torch
        import asyncio
        
        model, tokenizer = model_tuple
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Define batch encoding function
        def encode_batch():
            # Tokenize
            inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Use [CLS] token or mean pooling
            embeddings = []
            if config.metadata.get("pooling_strategy") == "cls":
                batch_embeddings = outputs.last_hidden_state[:, 0].numpy()
                embeddings = [embedding.tolist() for embedding in batch_embeddings]
            else:
                # Mean pooling
                attention_mask = inputs["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                batch_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
                    input_mask_expanded.sum(1), min=1e-9
                ).numpy()
                
                embeddings = [embedding.tolist() for embedding in batch_embeddings]
            
            return embeddings
        
        # Execute batch encoding
        embeddings = await loop.run_in_executor(None, encode_batch)
        
        return embeddings


class SemanticSearchService(DomainService):
    """Service for semantic search operations."""
    
    def __init__(
        self,
        search_repository: SearchRepositoryProtocol,
        embedding_service: EmbeddingService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the semantic search service.
        
        Args:
            search_repository: Repository for search operations
            embedding_service: Service for generating embeddings
            logger: Optional logger
        """
        self.search_repository = search_repository
        self.embedding_service = embedding_service
        self.logger = logger or logging.getLogger("uno.ai.semantic_search")
    
    async def index_document(
        self,
        content: str,
        entity_id: str,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[DocumentIndex]:
        """
        Index a document for semantic search.
        
        Args:
            content: Document content
            entity_id: Entity ID
            entity_type: Entity type
            metadata: Optional metadata
            
        Returns:
            Result containing the indexed document or an error
        """
        try:
            # Generate embedding for the document
            embedding_result = await self.embedding_service.create_embedding(
                text=content,
                source_id=entity_id,
                source_type=entity_type,
                metadata=metadata
            )
            
            if isinstance(embedding_result, Failure):
                return Result.failure(f"Failed to create embedding: {embedding_result.error}")
            
            embedding = embedding_result.value
            
            # Create document index entity
            document = DocumentIndex(
                id=str(uuid.uuid4()),
                content=content,
                entity_id=entity_id,
                entity_type=entity_type,
                embedding_id=embedding.id,
                metadata=metadata or {}
            )
            
            # Save to repository
            return await self.search_repository.index_document(document)
        except Exception as e:
            self.logger.error(f"Failed to index document: {str(e)}")
            return Result.failure(f"Failed to index document: {str(e)}")
    
    async def batch_index(
        self,
        contents: List[str],
        entity_ids: List[str],
        entity_type: str,
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> Result[List[DocumentIndex]]:
        """
        Batch index documents.
        
        Args:
            contents: Document contents
            entity_ids: Entity IDs
            entity_type: Entity type
            metadata_list: Optional list of metadata
            
        Returns:
            Result containing the indexed documents or an error
        """
        try:
            if len(contents) != len(entity_ids):
                return Result.failure("Number of contents and entity IDs must match")
            
            if metadata_list and len(metadata_list) != len(contents):
                return Result.failure("Number of metadata items must match number of contents")
            
            # Generate embeddings in batch
            embeddings_result = await self.embedding_service.batch_create_embeddings(
                texts=contents,
                source_ids=entity_ids,
                source_type=entity_type,
                metadata_list=metadata_list
            )
            
            if isinstance(embeddings_result, Failure):
                return Result.failure(f"Failed to create embeddings: {embeddings_result.error}")
            
            embeddings = embeddings_result.value
            
            # Create document index entities
            documents = []
            for i, (content, entity_id, embedding) in enumerate(zip(contents, entity_ids, embeddings)):
                metadata = metadata_list[i] if metadata_list else {}
                
                document = DocumentIndex(
                    id=str(uuid.uuid4()),
                    content=content,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    embedding_id=embedding.id,
                    metadata=metadata
                )
                
                documents.append(document)
            
            # Save to repository
            return await self.search_repository.batch_index(documents)
        except Exception as e:
            self.logger.error(f"Failed to batch index documents: {str(e)}")
            return Result.failure(f"Failed to batch index documents: {str(e)}")
    
    async def search(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> Result[List[SearchResult]]:
        """
        Perform a semantic search.
        
        Args:
            query_text: Search query text
            user_id: Optional user ID
            entity_type: Optional entity type filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            # Create search query entity
            query = SearchQuery(
                id=SearchQueryId(str(uuid.uuid4())),
                query_text=query_text,
                user_id=user_id,
                entity_type=entity_type
            )
            
            # Execute search
            return await self.search_repository.search(
                query,
                limit,
                similarity_threshold
            )
        except Exception as e:
            self.logger.error(f"Failed to search: {str(e)}")
            return Result.failure(f"Failed to search: {str(e)}")
    
    async def search_by_vector(
        self,
        vector: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> Result[List[SearchResult]]:
        """
        Perform a search using a vector.
        
        Args:
            vector: Query vector
            entity_type: Optional entity type filter
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            return await self.search_repository.search_by_vector(
                vector,
                entity_type,
                limit,
                similarity_threshold
            )
        except Exception as e:
            self.logger.error(f"Failed to search by vector: {str(e)}")
            return Result.failure(f"Failed to search by vector: {str(e)}")
    
    async def delete_document(
        self,
        entity_id: str,
        entity_type: Optional[str] = None
    ) -> Result[int]:
        """
        Delete document from the index.
        
        Args:
            entity_id: Entity ID
            entity_type: Optional entity type filter
            
        Returns:
            Result containing the count of deleted documents or an error
        """
        try:
            return await self.search_repository.delete_document(entity_id, entity_type)
        except Exception as e:
            self.logger.error(f"Failed to delete document: {str(e)}")
            return Result.failure(f"Failed to delete document: {str(e)}")


class RAGService(DomainService):
    """Service for Retrieval Augmented Generation operations."""
    
    def __init__(
        self,
        search_service: SemanticSearchService,
        context_repository: Optional[AIContextRepositoryProtocol] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the RAG service.
        
        Args:
            search_service: Service for semantic search
            context_repository: Optional repository for AI context
            logger: Optional logger
        """
        self.search_service = search_service
        self.context_repository = context_repository
        self.logger = logger or logging.getLogger("uno.ai.rag")
    
    async def retrieve_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> Result[List[Dict[str, Any]]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The query text
            user_id: Optional user ID
            session_id: Optional session ID
            entity_id: Optional entity ID
            entity_type: Optional entity type
            limit: Maximum number of results to retrieve
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Result containing a list of context items or an error
        """
        try:
            # Search for relevant documents
            search_result = await self.search_service.search(
                query_text=query,
                user_id=user_id,
                entity_type=entity_type,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            if isinstance(search_result, Failure):
                return search_result
            
            search_results = search_result.value
            
            # Convert results to context items
            context_items = []
            for result in search_results:
                # Get the document
                document_result = await self.search_service.search_repository.get_document(
                    result.entity_id,
                    result.entity_type
                )
                
                if isinstance(document_result, Success):
                    document = document_result.value
                    context_items.append({
                        "id": result.id,
                        "content": document.content,
                        "entity_id": result.entity_id,
                        "entity_type": result.entity_type,
                        "similarity": result.similarity,
                        "metadata": {**document.metadata, **result.metadata}
                    })
            
            # Add user context if available
            if self.context_repository and user_id:
                user_context_result = await self.context_repository.get_user_context(user_id, limit=3)
                if isinstance(user_context_result, Success):
                    for context in user_context_result.value:
                        context_items.append({
                            "id": context.id,
                            "content": context.value if isinstance(context.value, str) else str(context.value),
                            "entity_id": context.entity_id or "",
                            "entity_type": context.entity_type or "",
                            "context_type": context.context_type,
                            "context_source": context.context_source,
                            "metadata": context.metadata
                        })
            
            # Add session context if available
            if self.context_repository and session_id:
                session_context_result = await self.context_repository.get_session_context(session_id, limit=3)
                if isinstance(session_context_result, Success):
                    for context in session_context_result.value:
                        context_items.append({
                            "id": context.id,
                            "content": context.value if isinstance(context.value, str) else str(context.value),
                            "entity_id": context.entity_id or "",
                            "entity_type": context.entity_type or "",
                            "context_type": context.context_type,
                            "context_source": context.context_source,
                            "metadata": context.metadata
                        })
            
            # Sort by similarity (if available)
            context_items.sort(
                key=lambda x: x.get("similarity", 0.0) if "similarity" in x else 0.5,
                reverse=True
            )
            
            # Apply final limit
            if len(context_items) > limit:
                context_items = context_items[:limit]
            
            return Result.success(context_items)
        except Exception as e:
            self.logger.error(f"Failed to retrieve context: {str(e)}")
            return Result.failure(f"Failed to retrieve context: {str(e)}")
    
    async def create_rag_prompt(
        self,
        query: str,
        system_prompt: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> Result[Dict[str, str]]:
        """
        Create a RAG prompt with retrieved context.
        
        Args:
            query: The user's query
            system_prompt: The system prompt
            user_id: Optional user ID
            session_id: Optional session ID
            entity_id: Optional entity ID
            entity_type: Optional entity type
            limit: Maximum number of results to retrieve
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Result containing a dict with system_prompt and user_prompt or an error
        """
        try:
            # Create RAG query entity
            rag_query = RAGQuery(
                id=str(uuid.uuid4()),
                query_text=query,
                system_prompt=system_prompt,
                user_id=user_id,
                session_id=session_id,
                entity_id=entity_id,
                entity_type=entity_type
            )
            
            # Retrieve context
            context_result = await self.retrieve_context(
                query=query,
                user_id=user_id,
                session_id=session_id,
                entity_id=entity_id,
                entity_type=entity_type,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            if isinstance(context_result, Failure):
                return context_result
            
            context_items = context_result.value
            
            # Create prompt
            prompt = rag_query.create_prompt(context_items)
            
            return Result.success(prompt)
        except Exception as e:
            self.logger.error(f"Failed to create RAG prompt: {str(e)}")
            return Result.failure(f"Failed to create RAG prompt: {str(e)}")


# Other services would follow a similar pattern
# For brevity, we'll implement them as needed.