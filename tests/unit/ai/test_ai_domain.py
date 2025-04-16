"""
Tests for the AI module domain entities, repositories, and services.

This module contains comprehensive tests for all domain components of the AI module,
focusing on value objects, entities, repositories, and domain services related to
embeddings, semantic search, RAG, recommendations, content generation, and anomaly detection.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

import numpy as np

from uno.core.result import Result, Success, Failure
from uno.domain.core import ValueObject

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
    RecommendationMethod,
    SimilarityMetric
)

from uno.ai.domain_repositories import (
    EmbeddingModelRepositoryProtocol,
    EmbeddingRepositoryProtocol,
    SearchRepositoryProtocol,
    RecommendationRepositoryProtocol,
    ContentGenerationRepositoryProtocol,
    AnomalyDetectionRepositoryProtocol,
    AIContextRepositoryProtocol,
    EmbeddingModelRepository,
    EmbeddingRepository,
    SearchRepository
)

from uno.ai.domain_services import (
    EmbeddingModelService,
    EmbeddingService,
    SemanticSearchService,
    RAGService
)


# Test constants
TEST_MODEL_ID = "test-model-id"
TEST_EMBEDDING_ID = "test-embedding-id"
TEST_QUERY_ID = "test-query-id"
TEST_RECOMMENDATION_ID = "test-recommendation-id"
TEST_CONTENT_REQUEST_ID = "test-content-request-id"
TEST_ANOMALY_DETECTION_ID = "test-anomaly-detection-id"


# Value Object Tests
class TestValueObjects:
    """Tests for value objects in the AI domain."""

    def test_embedding_id(self):
        """Test EmbeddingId value object."""
        id_value = str(uuid.uuid4())
        embedding_id = EmbeddingId(id_value)
        
        assert embedding_id.value == id_value
        assert isinstance(embedding_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            embedding_id.value = "new-value"
            
        # Test equality
        same_id = EmbeddingId(id_value)
        different_id = EmbeddingId(str(uuid.uuid4()))
        
        assert embedding_id == same_id
        assert embedding_id != different_id
        assert hash(embedding_id) == hash(same_id)

    def test_search_query_id(self):
        """Test SearchQueryId value object."""
        id_value = str(uuid.uuid4())
        query_id = SearchQueryId(id_value)
        
        assert query_id.value == id_value
        assert isinstance(query_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            query_id.value = "new-value"
            
        # Test equality
        same_id = SearchQueryId(id_value)
        different_id = SearchQueryId(str(uuid.uuid4()))
        
        assert query_id == same_id
        assert query_id != different_id
        assert hash(query_id) == hash(same_id)

    def test_recommendation_id(self):
        """Test RecommendationId value object."""
        id_value = str(uuid.uuid4())
        recommendation_id = RecommendationId(id_value)
        
        assert recommendation_id.value == id_value
        assert isinstance(recommendation_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            recommendation_id.value = "new-value"
            
        # Test equality
        same_id = RecommendationId(id_value)
        different_id = RecommendationId(str(uuid.uuid4()))
        
        assert recommendation_id == same_id
        assert recommendation_id != different_id
        assert hash(recommendation_id) == hash(same_id)

    def test_content_request_id(self):
        """Test ContentRequestId value object."""
        id_value = str(uuid.uuid4())
        content_request_id = ContentRequestId(id_value)
        
        assert content_request_id.value == id_value
        assert isinstance(content_request_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            content_request_id.value = "new-value"
            
        # Test equality
        same_id = ContentRequestId(id_value)
        different_id = ContentRequestId(str(uuid.uuid4()))
        
        assert content_request_id == same_id
        assert content_request_id != different_id
        assert hash(content_request_id) == hash(same_id)

    def test_anomaly_detection_id(self):
        """Test AnomalyDetectionId value object."""
        id_value = str(uuid.uuid4())
        anomaly_detection_id = AnomalyDetectionId(id_value)
        
        assert anomaly_detection_id.value == id_value
        assert isinstance(anomaly_detection_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            anomaly_detection_id.value = "new-value"
            
        # Test equality
        same_id = AnomalyDetectionId(id_value)
        different_id = AnomalyDetectionId(str(uuid.uuid4()))
        
        assert anomaly_detection_id == same_id
        assert anomaly_detection_id != different_id
        assert hash(anomaly_detection_id) == hash(same_id)

    def test_model_id(self):
        """Test ModelId value object."""
        id_value = str(uuid.uuid4())
        model_id = ModelId(id_value)
        
        assert model_id.value == id_value
        assert isinstance(model_id, ValueObject)
        
        # Test immutability
        with pytest.raises(Exception):
            model_id.value = "new-value"
            
        # Test equality
        same_id = ModelId(id_value)
        different_id = ModelId(str(uuid.uuid4()))
        
        assert model_id == same_id
        assert model_id != different_id
        assert hash(model_id) == hash(same_id)


# Entity Tests
class TestEmbeddingModelEntity:
    """Tests for the EmbeddingModel entity."""
    
    def test_create_embedding_model(self):
        """Test creating an embedding model entity."""
        model = EmbeddingModel(
            id=ModelId(TEST_MODEL_ID),
            name="test-model",
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMER,
            dimensions=384,
            api_key="test-api-key",
            normalize_vectors=True,
            metadata={"source": "test"}
        )
        
        assert model.id.value == TEST_MODEL_ID
        assert model.name == "test-model"
        assert model.model_type == EmbeddingModelType.SENTENCE_TRANSFORMER
        assert model.dimensions == 384
        assert model.api_key == "test-api-key"
        assert model.normalize_vectors is True
        assert model.metadata == {"source": "test"}
        assert isinstance(model.created_at, datetime)

    def test_embedding_model_type_enum(self):
        """Test the EmbeddingModelType enum."""
        assert EmbeddingModelType.SENTENCE_TRANSFORMER.value == "sentence_transformer"
        assert EmbeddingModelType.HUGGINGFACE.value == "huggingface"
        assert EmbeddingModelType.OPENAI.value == "openai"
        assert EmbeddingModelType.CUSTOM.value == "custom"


class TestEmbeddingEntity:
    """Tests for the Embedding entity."""
    
    def test_create_embedding(self):
        """Test creating an embedding entity."""
        embedding = Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=[0.1, 0.2, 0.3, 0.4],
            model_id=ModelId(TEST_MODEL_ID),
            source_id="test-doc-1",
            source_type="document",
            dimensions=4,
            metadata={"source": "test"}
        )
        
        assert embedding.id.value == TEST_EMBEDDING_ID
        assert embedding.vector == [0.1, 0.2, 0.3, 0.4]
        assert embedding.model_id.value == TEST_MODEL_ID
        assert embedding.source_id == "test-doc-1"
        assert embedding.source_type == "document"
        assert embedding.dimensions == 4
        assert embedding.metadata == {"source": "test"}
        assert isinstance(embedding.created_at, datetime)


class TestSearchQueryEntity:
    """Tests for the SearchQuery entity."""
    
    def test_create_search_query(self):
        """Test creating a search query entity."""
        query = SearchQuery(
            id=SearchQueryId(TEST_QUERY_ID),
            query_text="test query",
            user_id="user1",
            entity_type="document",
            metadata={"source": "test"}
        )
        
        assert query.id.value == TEST_QUERY_ID
        assert query.query_text == "test query"
        assert query.user_id == "user1"
        assert query.entity_type == "document"
        assert query.metadata == {"source": "test"}
        assert isinstance(query.created_at, datetime)
    
    def test_get_query_vector(self):
        """Test get_query_vector method."""
        query = SearchQuery(
            id=SearchQueryId(TEST_QUERY_ID),
            query_text="test query"
        )
        
        # Mock the embedding service
        embedding_service = MagicMock()
        embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # This method is a placeholder in the entity, so we're just testing it returns an empty list
        vector = query.get_query_vector(embedding_service)
        assert isinstance(vector, list)


class TestSearchResultEntity:
    """Tests for the SearchResult entity."""
    
    def test_create_search_result(self):
        """Test creating a search result entity."""
        result = SearchResult(
            id="result-1",
            query_id=SearchQueryId(TEST_QUERY_ID),
            entity_id="doc-1",
            entity_type="document",
            similarity=0.85,
            rank=1,
            metadata={"highlight": "text snippet"}
        )
        
        assert result.id == "result-1"
        assert result.query_id.value == TEST_QUERY_ID
        assert result.entity_id == "doc-1"
        assert result.entity_type == "document"
        assert result.similarity == 0.85
        assert result.rank == 1
        assert result.metadata == {"highlight": "text snippet"}
        assert isinstance(result.created_at, datetime)


class TestDocumentIndexEntity:
    """Tests for the DocumentIndex entity."""
    
    def test_create_document_index(self):
        """Test creating a document index entity."""
        doc = DocumentIndex(
            id="doc-1",
            content="This is a test document",
            entity_id="entity-1",
            entity_type="document",
            embedding_id=EmbeddingId(TEST_EMBEDDING_ID),
            metadata={"source": "test"}
        )
        
        assert doc.id == "doc-1"
        assert doc.content == "This is a test document"
        assert doc.entity_id == "entity-1"
        assert doc.entity_type == "document"
        assert doc.embedding_id.value == TEST_EMBEDDING_ID
        assert doc.metadata == {"source": "test"}
        assert isinstance(doc.created_at, datetime)
        assert isinstance(doc.updated_at, datetime)


class TestRAGQueryEntity:
    """Tests for the RAGQuery entity."""
    
    def test_create_rag_query(self):
        """Test creating a RAG query entity."""
        query = RAGQuery(
            id="rag-1",
            query_text="How do vectors work?",
            system_prompt="You are a helpful assistant.",
            user_id="user-1",
            session_id="session-1",
            metadata={"source": "test"}
        )
        
        assert query.id == "rag-1"
        assert query.query_text == "How do vectors work?"
        assert query.system_prompt == "You are a helpful assistant."
        assert query.user_id == "user-1"
        assert query.session_id == "session-1"
        assert query.metadata == {"source": "test"}
        assert isinstance(query.created_at, datetime)
    
    def test_create_prompt(self):
        """Test create_prompt method."""
        query = RAGQuery(
            id="rag-1",
            query_text="How do vectors work?",
            system_prompt="You are a helpful assistant."
        )
        
        context_items = [
            {
                "content": "Vectors are mathematical objects with magnitude and direction.",
                "entity_id": "doc-1",
                "entity_type": "document",
                "title": "Vector basics"
            },
            {
                "content": "In machine learning, vectors represent points in a high-dimensional space.",
                "entity_id": "doc-2",
                "entity_type": "document",
                "title": "ML vectors"
            }
        ]
        
        prompt = query.create_prompt(context_items)
        
        assert "system_prompt" in prompt
        assert "user_prompt" in prompt
        assert prompt["system_prompt"] == "You are a helpful assistant."
        assert "How do vectors work?" in prompt["user_prompt"]
        assert "Vector basics" in prompt["user_prompt"]
        assert "ML vectors" in prompt["user_prompt"]
        assert "Vectors are mathematical objects" in prompt["user_prompt"]
        assert "In machine learning, vectors represent" in prompt["user_prompt"]


# Repository Tests
class TestEmbeddingModelRepository:
    """Tests for the EmbeddingModelRepository."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        mock_session = MagicMock()
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        return mock_session_context
    
    @pytest.fixture
    def repository(self, mock_session):
        """Create a repository with a mock session for testing."""
        repository = EmbeddingModelRepository()
        repository.session = MagicMock(return_value=mock_session)
        return repository
    
    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        return EmbeddingModel(
            id=ModelId(TEST_MODEL_ID),
            name="test-model",
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMER,
            dimensions=384,
            api_key="test-api-key",
            normalize_vectors=True,
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_create(self, repository, mock_session, sample_model):
        """Test creating a model."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.create(sample_model)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_model
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_duplicate_name(self, repository, mock_session, sample_model):
        """Test creating a model with a duplicate name."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = {"id": "existing-id"}
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.create(sample_model)
        
        # Assert
        assert isinstance(result, Failure)
        assert "already exists" in result.error
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get(self, repository, mock_session, sample_model):
        """Test getting a model by ID."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = MagicMock(
            id=TEST_MODEL_ID,
            name="test-model",
            model_type="sentence_transformer",
            dimensions=384,
            api_key="test-api-key",
            normalize_vectors=True,
            metadata={"source": "test"},
            created_at=datetime.now(UTC)
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.get(ModelId(TEST_MODEL_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_MODEL_ID
        assert result.value.name == "test-model"
        assert result.value.model_type == EmbeddingModelType.SENTENCE_TRANSFORMER
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, repository, mock_session):
        """Test getting a model that doesn't exist."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.get(ModelId(TEST_MODEL_ID))
        
        # Assert
        assert isinstance(result, Failure)
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_get_by_name(self, repository, mock_session, sample_model):
        """Test getting a model by name."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = MagicMock(
            id=TEST_MODEL_ID,
            name="test-model",
            model_type="sentence_transformer",
            dimensions=384,
            api_key="test-api-key",
            normalize_vectors=True,
            metadata={"source": "test"},
            created_at=datetime.now(UTC)
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.get_by_name("test-model")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_MODEL_ID
        assert result.value.name == "test-model"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update(self, repository, mock_session, sample_model):
        """Test updating a model."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = {"id": TEST_MODEL_ID}
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.update(sample_model)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_model
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_session, sample_model):
        """Test updating a model that doesn't exist."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.update(sample_model)
        
        # Assert
        assert isinstance(result, Failure)
        assert "not found" in result.error
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete(self, repository, mock_session):
        """Test deleting a model."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = {"id": TEST_MODEL_ID}
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.delete(ModelId(TEST_MODEL_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value is True
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_session):
        """Test deleting a model that doesn't exist."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.delete(ModelId(TEST_MODEL_ID))
        
        # Assert
        assert isinstance(result, Failure)
        assert "not found" in result.error
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_list(self, repository, mock_session):
        """Test listing all models."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id=TEST_MODEL_ID,
                name="test-model",
                model_type="sentence_transformer",
                dimensions=384,
                api_key="test-api-key",
                normalize_vectors=True,
                metadata={"source": "test"},
                created_at=datetime.now(UTC)
            ),
            MagicMock(
                id="model-2",
                name="other-model",
                model_type="openai",
                dimensions=1536,
                api_key="other-api-key",
                normalize_vectors=True,
                metadata={"source": "other"},
                created_at=datetime.now(UTC)
            )
        ]
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.list()
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].id.value == TEST_MODEL_ID
        assert result.value[0].name == "test-model"
        assert result.value[1].id.value == "model-2"
        assert result.value[1].name == "other-model"
        mock_db_session.execute.assert_called_once()


class TestEmbeddingRepository:
    """Tests for the EmbeddingRepository."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        mock_session = MagicMock()
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        return mock_session_context
    
    @pytest.fixture
    def repository(self, mock_session):
        """Create a repository with a mock session for testing."""
        repository = EmbeddingRepository()
        repository.session = MagicMock(return_value=mock_session)
        return repository
    
    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding for testing."""
        return Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=[0.1, 0.2, 0.3, 0.4],
            model_id=ModelId(TEST_MODEL_ID),
            source_id="test-doc-1",
            source_type="document",
            dimensions=4,
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_create(self, repository, mock_session, sample_embedding):
        """Test creating an embedding."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.create(sample_embedding)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_embedding
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get(self, repository, mock_session, sample_embedding):
        """Test getting an embedding by ID."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = MagicMock(
            id=TEST_EMBEDDING_ID,
            vector=[0.1, 0.2, 0.3, 0.4],
            model_id=TEST_MODEL_ID,
            source_id="test-doc-1",
            source_type="document",
            dimensions=4,
            metadata={"source": "test"},
            created_at=datetime.now(UTC)
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.get(EmbeddingId(TEST_EMBEDDING_ID))
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_EMBEDDING_ID
        assert result.value.vector == [0.1, 0.2, 0.3, 0.4]
        assert result.value.model_id.value == TEST_MODEL_ID
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_source(self, repository, mock_session, sample_embedding):
        """Test getting an embedding by source."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = MagicMock(
            id=TEST_EMBEDDING_ID,
            vector=[0.1, 0.2, 0.3, 0.4],
            model_id=TEST_MODEL_ID,
            source_id="test-doc-1",
            source_type="document",
            dimensions=4,
            metadata={"source": "test"},
            created_at=datetime.now(UTC)
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.get_by_source("test-doc-1", "document")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_EMBEDDING_ID
        assert result.value.source_id == "test-doc-1"
        assert result.value.source_type == "document"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_create(self, repository, mock_session):
        """Test batch creating embeddings."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        
        embeddings = [
            Embedding(
                id=EmbeddingId(TEST_EMBEDDING_ID),
                vector=[0.1, 0.2, 0.3, 0.4],
                model_id=ModelId(TEST_MODEL_ID),
                source_id="test-doc-1",
                source_type="document",
                dimensions=4,
                metadata={"source": "test"}
            ),
            Embedding(
                id=EmbeddingId("embedding-2"),
                vector=[0.5, 0.6, 0.7, 0.8],
                model_id=ModelId(TEST_MODEL_ID),
                source_id="test-doc-2",
                source_type="document",
                dimensions=4,
                metadata={"source": "test"}
            )
        ]
        
        # Execute
        result = await repository.batch_create(embeddings)
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].id.value == TEST_EMBEDDING_ID
        assert result.value[1].id.value == "embedding-2"
        mock_db_session.execute_many.assert_called_once()
        mock_db_session.commit.assert_called_once()


class TestSearchRepository:
    """Tests for the SearchRepository."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        mock_session = MagicMock()
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        return mock_session_context
    
    @pytest.fixture
    def repository(self, mock_session):
        """Create a repository with a mock session for testing."""
        repository = SearchRepository()
        repository.session = MagicMock(return_value=mock_session)
        return repository
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return DocumentIndex(
            id="doc-1",
            content="This is a test document",
            entity_id="entity-1",
            entity_type="document",
            embedding_id=EmbeddingId(TEST_EMBEDDING_ID),
            metadata={"source": "test"}
        )
    
    @pytest.fixture
    def sample_query(self):
        """Create a sample search query for testing."""
        return SearchQuery(
            id=SearchQueryId(TEST_QUERY_ID),
            query_text="test query",
            user_id="user1",
            entity_type="document",
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_index_document(self, repository, mock_session, sample_document):
        """Test indexing a document."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.index_document(sample_document)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_document
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_index(self, repository, mock_session):
        """Test batch indexing documents."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        
        documents = [
            DocumentIndex(
                id="doc-1",
                content="This is the first test document",
                entity_id="entity-1",
                entity_type="document",
                embedding_id=EmbeddingId(TEST_EMBEDDING_ID),
                metadata={"source": "test"}
            ),
            DocumentIndex(
                id="doc-2",
                content="This is the second test document",
                entity_id="entity-2",
                entity_type="document",
                embedding_id=EmbeddingId("embedding-2"),
                metadata={"source": "test"}
            )
        ]
        
        # Execute
        result = await repository.batch_index(documents)
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].id == "doc-1"
        assert result.value[1].id == "doc-2"
        mock_db_session.execute_many.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("uno.sql.emitters.vector.VectorSearchEmitter")
    async def test_search(self, mock_emitter_class, repository, mock_session, sample_query):
        """Test performing a search."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_emitter = MagicMock()
        mock_emitter_class.return_value = mock_emitter
        
        mock_emitter.execute_search.return_value = [
            {"entity_id": "entity-1", "entity_type": "document", "similarity": 0.9, "metadata": {}},
            {"entity_id": "entity-2", "entity_type": "document", "similarity": 0.8, "metadata": {}}
        ]
        
        # Execute
        with patch("uuid.uuid4", return_value=uuid.UUID("00000000-0000-0000-0000-000000000000")):
            result = await repository.search(sample_query, limit=2, similarity_threshold=0.7)
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].entity_id == "entity-1"
        assert result.value[0].similarity == 0.9
        assert result.value[0].rank == 1
        assert result.value[1].entity_id == "entity-2"
        assert result.value[1].similarity == 0.8
        assert result.value[1].rank == 2
        mock_db_session.execute.assert_called()  # For logging the query
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("uno.sql.emitters.vector.VectorSearchEmitter")
    async def test_search_by_vector(self, mock_emitter_class, repository, mock_session):
        """Test performing a search by vector."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_emitter = MagicMock()
        mock_emitter_class.return_value = mock_emitter
        
        query_vector = [0.1, 0.2, 0.3]
        
        mock_emitter.execute_search.return_value = [
            {"entity_id": "entity-1", "entity_type": "document", "similarity": 0.9, "metadata": {}},
            {"entity_id": "entity-2", "entity_type": "document", "similarity": 0.8, "metadata": {}}
        ]
        
        # Execute
        with patch("uuid.uuid4", return_value=uuid.UUID("00000000-0000-0000-0000-000000000000")):
            result = await repository.search_by_vector(query_vector, entity_type="document", limit=2)
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].entity_id == "entity-1"
        assert result.value[0].similarity == 0.9
        assert result.value[0].rank == 1
        assert result.value[1].entity_id == "entity-2"
        assert result.value[1].similarity == 0.8
        assert result.value[1].rank == 2
        mock_emitter.execute_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_document(self, repository, mock_session):
        """Test deleting a document from the index."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = [{"id": "doc-1"}]
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.delete_document("entity-1", "document")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == 1
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_document(self, repository, mock_session, sample_document):
        """Test getting a document from the index."""
        # Setup
        mock_db_session = await mock_session.__aenter__()
        mock_result = AsyncMock()
        mock_result.fetchone.return_value = MagicMock(
            id="doc-1",
            content="This is a test document",
            entity_id="entity-1",
            entity_type="document",
            embedding_id=TEST_EMBEDDING_ID,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            metadata={"source": "test"}
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute
        result = await repository.get_document("entity-1", "document")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id == "doc-1"
        assert result.value.content == "This is a test document"
        assert result.value.entity_id == "entity-1"
        assert result.value.entity_type == "document"
        assert result.value.embedding_id.value == TEST_EMBEDDING_ID
        mock_db_session.execute.assert_called_once()


# Service Tests
class TestEmbeddingModelService:
    """Tests for the EmbeddingModelService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=EmbeddingModelRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with a mock repository for testing."""
        return EmbeddingModelService(model_repository=mock_repository)
    
    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        return EmbeddingModel(
            id=ModelId(TEST_MODEL_ID),
            name="test-model",
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMER,
            dimensions=384,
            api_key="test-api-key",
            normalize_vectors=True,
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_create_model(self, service, mock_repository, sample_model):
        """Test creating a model."""
        # Setup
        mock_repository.get_by_name.return_value = Failure("Not found")
        mock_repository.create.return_value = Success(sample_model)
        
        # Execute
        result = await service.create_model(
            name="test-model",
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMER,
            dimensions=384,
            api_key="test-api-key",
            normalize_vectors=True,
            metadata={"source": "test"}
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.name == "test-model"
        assert result.value.model_type == EmbeddingModelType.SENTENCE_TRANSFORMER
        mock_repository.get_by_name.assert_called_once_with("test-model")
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_model_already_exists(self, service, mock_repository, sample_model):
        """Test creating a model that already exists."""
        # Setup
        mock_repository.get_by_name.return_value = Success(sample_model)
        
        # Execute
        result = await service.create_model(
            name="test-model",
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMER,
            dimensions=384
        )
        
        # Assert
        assert isinstance(result, Failure)
        assert "already exists" in result.error
        mock_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_model(self, service, mock_repository, sample_model):
        """Test getting a model by ID."""
        # Setup
        mock_repository.get.return_value = Success(sample_model)
        
        # Execute
        result = await service.get_model(TEST_MODEL_ID)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_model
        mock_repository.get.assert_called_once_with(ModelId(TEST_MODEL_ID))
    
    @pytest.mark.asyncio
    async def test_get_model_by_name(self, service, mock_repository, sample_model):
        """Test getting a model by name."""
        # Setup
        mock_repository.get_by_name.return_value = Success(sample_model)
        
        # Execute
        result = await service.get_model_by_name("test-model")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_model
        mock_repository.get_by_name.assert_called_once_with("test-model")
    
    @pytest.mark.asyncio
    async def test_update_model(self, service, mock_repository, sample_model):
        """Test updating a model."""
        # Setup
        mock_repository.get.return_value = Success(sample_model)
        updated_model = sample_model
        updated_model.name = "updated-model"
        mock_repository.update.return_value = Success(updated_model)
        
        # Execute
        result = await service.update_model(
            model_id=TEST_MODEL_ID,
            name="updated-model"
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.name == "updated-model"
        mock_repository.get.assert_called_once()
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_model(self, service, mock_repository):
        """Test deleting a model."""
        # Setup
        mock_repository.delete.return_value = Success(True)
        
        # Execute
        result = await service.delete_model(TEST_MODEL_ID)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value is True
        mock_repository.delete.assert_called_once_with(ModelId(TEST_MODEL_ID))
    
    @pytest.mark.asyncio
    async def test_list_models(self, service, mock_repository, sample_model):
        """Test listing all models."""
        # Setup
        mock_repository.list.return_value = Success([sample_model])
        
        # Execute
        result = await service.list_models()
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_model
        mock_repository.list.assert_called_once()


class TestEmbeddingService:
    """Tests for the EmbeddingService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=EmbeddingRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def mock_model_service(self):
        """Create a mock model service for testing."""
        service = AsyncMock()
        return service
    
    @pytest.fixture
    def service(self, mock_repository, mock_model_service):
        """Create a service with mock dependencies for testing."""
        return EmbeddingService(
            embedding_repository=mock_repository,
            model_service=mock_model_service
        )
    
    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        return EmbeddingModel(
            id=ModelId(TEST_MODEL_ID),
            name="test-model",
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMER,
            dimensions=384,
            api_key="test-api-key",
            normalize_vectors=True,
            metadata={"source": "test"}
        )
    
    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding for testing."""
        return Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=[0.1, 0.2, 0.3, 0.4],
            model_id=ModelId(TEST_MODEL_ID),
            source_id="test-doc-1",
            source_type="document",
            dimensions=4,
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    @patch("uuid.uuid4", return_value=uuid.UUID(TEST_EMBEDDING_ID))
    async def test_create_embedding(self, mock_uuid, service, mock_repository, mock_model_service, sample_model):
        """Test creating an embedding."""
        # Setup
        mock_model_service.get_model_by_name.return_value = Success(sample_model)
        service._get_or_load_model = AsyncMock(return_value="mock_model")
        service._embed_with_sentence_transformer = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        mock_repository.create.return_value = Success(Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=[0.1, 0.2, 0.3, 0.4],
            model_id=ModelId(TEST_MODEL_ID),
            source_id="test-doc-1",
            source_type="document",
            dimensions=4,
            metadata={"source": "test"}
        ))
        
        # Execute
        result = await service.create_embedding(
            text="This is a test document",
            source_id="test-doc-1",
            source_type="document",
            model_name="test-model",
            metadata={"source": "test"}
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id.value == TEST_EMBEDDING_ID
        assert result.value.vector == [0.1, 0.2, 0.3, 0.4]
        assert result.value.source_id == "test-doc-1"
        assert result.value.source_type == "document"
        mock_model_service.get_model_by_name.assert_called_once_with("test-model")
        service._get_or_load_model.assert_called_once()
        service._embed_with_sentence_transformer.assert_called_once()
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_embedding(self, service, mock_repository, sample_embedding):
        """Test getting an embedding by ID."""
        # Setup
        mock_repository.get.return_value = Success(sample_embedding)
        
        # Execute
        result = await service.get_embedding(TEST_EMBEDDING_ID)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_embedding
        mock_repository.get.assert_called_once_with(EmbeddingId(TEST_EMBEDDING_ID))
    
    @pytest.mark.asyncio
    async def test_get_embedding_by_source(self, service, mock_repository, sample_embedding):
        """Test getting an embedding by source."""
        # Setup
        mock_repository.get_by_source.return_value = Success(sample_embedding)
        
        # Execute
        result = await service.get_embedding_by_source("test-doc-1", "document")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == sample_embedding
        mock_repository.get_by_source.assert_called_once_with("test-doc-1", "document")
    
    @pytest.mark.asyncio
    async def test_compute_similarity_cosine(self, service):
        """Test computing cosine similarity between two vectors."""
        # Setup
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [0.0, 1.0, 0.0]
        vector3 = [1.0, 0.0, 0.0]
        
        # Execute
        result1 = await service.compute_similarity(vector1, vector2, "cosine")
        result2 = await service.compute_similarity(vector1, vector3, "cosine")
        
        # Assert
        assert isinstance(result1, Success)
        assert isinstance(result2, Success)
        assert result1.value == 0.0  # Perpendicular vectors have cosine similarity of 0
        assert result2.value == 1.0  # Identical vectors have cosine similarity of 1
    
    @pytest.mark.asyncio
    async def test_compute_similarity_euclidean(self, service):
        """Test computing euclidean similarity between two vectors."""
        # Setup
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [0.0, 1.0, 0.0]
        vector3 = [1.0, 0.0, 0.0]
        
        # Execute
        result1 = await service.compute_similarity(vector1, vector2, "euclidean")
        result2 = await service.compute_similarity(vector1, vector3, "euclidean")
        
        # Assert
        assert isinstance(result1, Success)
        assert isinstance(result2, Success)
        # Euclidean similarity is 1/(1+distance), so further vectors have lower similarity
        assert result1.value < result2.value
        assert result2.value == 1.0  # Identical vectors have euclidean similarity of 1
    
    @pytest.mark.asyncio
    async def test_compute_similarity_dot_product(self, service):
        """Test computing dot product similarity between two vectors."""
        # Setup
        vector1 = [1.0, 2.0, 3.0]
        vector2 = [4.0, 5.0, 6.0]
        
        # Execute
        result = await service.compute_similarity(vector1, vector2, "dot_product")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == 32.0  # Dot product: 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32


class TestSemanticSearchService:
    """Tests for the SemanticSearchService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repository = AsyncMock(spec=SearchRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service for testing."""
        service = AsyncMock()
        return service
    
    @pytest.fixture
    def service(self, mock_repository, mock_embedding_service):
        """Create a service with mock dependencies for testing."""
        return SemanticSearchService(
            search_repository=mock_repository,
            embedding_service=mock_embedding_service
        )
    
    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding for testing."""
        return Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=[0.1, 0.2, 0.3, 0.4],
            model_id=ModelId(TEST_MODEL_ID),
            source_id="entity-1",
            source_type="document",
            dimensions=4,
            metadata={"source": "test"}
        )
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return DocumentIndex(
            id="doc-1",
            content="This is a test document",
            entity_id="entity-1",
            entity_type="document",
            embedding_id=EmbeddingId(TEST_EMBEDDING_ID),
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    @patch("uuid.uuid4", return_value=uuid.UUID("doc-1"))
    async def test_index_document(self, mock_uuid, service, mock_repository, mock_embedding_service, sample_embedding):
        """Test indexing a document."""
        # Setup
        mock_embedding_service.create_embedding.return_value = Success(sample_embedding)
        mock_repository.index_document.return_value = Success(DocumentIndex(
            id="doc-1",
            content="This is a test document",
            entity_id="entity-1",
            entity_type="document",
            embedding_id=EmbeddingId(TEST_EMBEDDING_ID),
            metadata={"source": "test"}
        ))
        
        # Execute
        result = await service.index_document(
            content="This is a test document",
            entity_id="entity-1",
            entity_type="document",
            metadata={"source": "test"}
        )
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.id == "doc-1"
        assert result.value.content == "This is a test document"
        assert result.value.entity_id == "entity-1"
        assert result.value.entity_type == "document"
        assert result.value.embedding_id.value == TEST_EMBEDDING_ID
        mock_embedding_service.create_embedding.assert_called_once_with(
            text="This is a test document",
            source_id="entity-1",
            source_type="document",
            metadata={"source": "test"}
        )
        mock_repository.index_document.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("uuid.uuid4", return_value=uuid.UUID(TEST_QUERY_ID))
    async def test_search(self, mock_uuid, service, mock_repository):
        """Test performing a search."""
        # Setup
        search_results = [
            SearchResult(
                id="result-1",
                query_id=SearchQueryId(TEST_QUERY_ID),
                entity_id="entity-1",
                entity_type="document",
                similarity=0.9,
                rank=1
            ),
            SearchResult(
                id="result-2",
                query_id=SearchQueryId(TEST_QUERY_ID),
                entity_id="entity-2",
                entity_type="document",
                similarity=0.8,
                rank=2
            )
        ]
        mock_repository.search.return_value = Success(search_results)
        
        # Execute
        result = await service.search(
            query_text="test query",
            user_id="user1",
            entity_type="document",
            limit=2,
            similarity_threshold=0.7
        )
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].entity_id == "entity-1"
        assert result.value[0].similarity == 0.9
        assert result.value[1].entity_id == "entity-2"
        assert result.value[1].similarity == 0.8
        mock_repository.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_vector(self, service, mock_repository):
        """Test performing a search by vector."""
        # Setup
        search_results = [
            SearchResult(
                id="result-1",
                query_id=SearchQueryId(TEST_QUERY_ID),
                entity_id="entity-1",
                entity_type="document",
                similarity=0.9,
                rank=1
            ),
            SearchResult(
                id="result-2",
                query_id=SearchQueryId(TEST_QUERY_ID),
                entity_id="entity-2",
                entity_type="document",
                similarity=0.8,
                rank=2
            )
        ]
        mock_repository.search_by_vector.return_value = Success(search_results)
        query_vector = [0.1, 0.2, 0.3]
        
        # Execute
        result = await service.search_by_vector(
            vector=query_vector,
            entity_type="document",
            limit=2,
            similarity_threshold=0.7
        )
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert result.value[0].entity_id == "entity-1"
        assert result.value[0].similarity == 0.9
        assert result.value[1].entity_id == "entity-2"
        assert result.value[1].similarity == 0.8
        mock_repository.search_by_vector.assert_called_once_with(
            query_vector, "document", 2, 0.7
        )
    
    @pytest.mark.asyncio
    async def test_delete_document(self, service, mock_repository):
        """Test deleting a document from the index."""
        # Setup
        mock_repository.delete_document.return_value = Success(1)
        
        # Execute
        result = await service.delete_document("entity-1", "document")
        
        # Assert
        assert isinstance(result, Success)
        assert result.value == 1
        mock_repository.delete_document.assert_called_once_with("entity-1", "document")


class TestRAGService:
    """Tests for the RAGService."""
    
    @pytest.fixture
    def mock_search_service(self):
        """Create a mock search service for testing."""
        search_service = AsyncMock()
        search_service.search_repository = AsyncMock()
        return search_service
    
    @pytest.fixture
    def mock_context_repository(self):
        """Create a mock context repository for testing."""
        repository = AsyncMock(spec=AIContextRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_search_service, mock_context_repository):
        """Create a service with mock dependencies for testing."""
        return RAGService(
            search_service=mock_search_service,
            context_repository=mock_context_repository
        )
    
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results for testing."""
        return [
            SearchResult(
                id="result-1",
                query_id=SearchQueryId(TEST_QUERY_ID),
                entity_id="entity-1",
                entity_type="document",
                similarity=0.9,
                rank=1,
                metadata={"title": "Document 1"}
            ),
            SearchResult(
                id="result-2",
                query_id=SearchQueryId(TEST_QUERY_ID),
                entity_id="entity-2",
                entity_type="document",
                similarity=0.8,
                rank=2,
                metadata={"title": "Document 2"}
            )
        ]
    
    @pytest.fixture
    def sample_document_1(self):
        """Create a sample document for testing."""
        return DocumentIndex(
            id="doc-1",
            content="This is the first test document",
            entity_id="entity-1",
            entity_type="document",
            embedding_id=EmbeddingId(TEST_EMBEDDING_ID),
            metadata={"title": "Document 1"}
        )
    
    @pytest.fixture
    def sample_document_2(self):
        """Create a sample document for testing."""
        return DocumentIndex(
            id="doc-2",
            content="This is the second test document",
            entity_id="entity-2",
            entity_type="document",
            embedding_id=EmbeddingId("embedding-2"),
            metadata={"title": "Document 2"}
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_context(
        self, service, mock_search_service, mock_context_repository, 
        sample_search_results, sample_document_1, sample_document_2
    ):
        """Test retrieving context for a query."""
        # Setup
        mock_search_service.search.return_value = Success(sample_search_results)
        mock_search_service.search_repository.get_document.side_effect = [
            Success(sample_document_1),
            Success(sample_document_2)
        ]
        
        user_contexts = [
            AIContext(
                id="context-1",
                user_id="user1",
                context_type="preference",
                context_source="profile",
                value={"interest": "machine learning"},
                metadata={}
            )
        ]
        mock_context_repository.get_user_context.return_value = Success(user_contexts)
        
        # Execute
        result = await service.retrieve_context(
            query="test query",
            user_id="user1",
            entity_type="document"
        )
        
        # Assert
        assert isinstance(result, Success)
        assert len(result.value) == 3  # 2 search results + 1 user context
        assert result.value[0]["content"] == "This is the first test document"
        assert result.value[0]["entity_id"] == "entity-1"
        assert result.value[0]["similarity"] == 0.9
        assert result.value[1]["content"] == "This is the second test document"
        assert result.value[1]["entity_id"] == "entity-2"
        assert result.value[1]["similarity"] == 0.8
        assert result.value[2]["context_type"] == "preference"
        mock_search_service.search.assert_called_once()
        mock_search_service.search_repository.get_document.assert_called()
        mock_context_repository.get_user_context.assert_called_once_with("user1", limit=3)
    
    @pytest.mark.asyncio
    @patch("uuid.uuid4", return_value=uuid.UUID("rag-query-id"))
    async def test_create_rag_prompt(self, mock_uuid, service):
        """Test creating a RAG prompt with retrieved context."""
        # Setup
        context_items = [
            {
                "content": "Vectors are mathematical objects with magnitude and direction.",
                "entity_id": "doc-1",
                "entity_type": "document",
                "similarity": 0.9,
                "metadata": {"title": "Vector basics"}
            },
            {
                "content": "In machine learning, vectors represent points in high-dimensional space.",
                "entity_id": "doc-2",
                "entity_type": "document",
                "similarity": 0.8,
                "metadata": {"title": "ML vectors"}
            }
        ]
        
        # Mock the retrieve_context method to return these items
        service.retrieve_context = AsyncMock(return_value=Success(context_items))
        
        # Execute
        result = await service.create_rag_prompt(
            query="How do vectors work?",
            system_prompt="You are a helpful assistant.",
            user_id="user1"
        )
        
        # Assert
        assert isinstance(result, Success)
        assert "system_prompt" in result.value
        assert "user_prompt" in result.value
        assert result.value["system_prompt"] == "You are a helpful assistant."
        assert "How do vectors work?" in result.value["user_prompt"]
        assert "Vector basics" in result.value["user_prompt"]
        assert "ML vectors" in result.value["user_prompt"]
        assert "Vectors are mathematical objects" in result.value["user_prompt"]
        assert "In machine learning, vectors represent" in result.value["user_prompt"]
        service.retrieve_context.assert_called_once_with(
            query="How do vectors work?",
            user_id="user1",
            session_id=None,
            entity_id=None,
            entity_type=None,
            limit=5,
            similarity_threshold=0.7
        )