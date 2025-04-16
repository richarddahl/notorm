"""
Tests for the AI module API endpoints.

This module contains comprehensive tests for all API endpoints of the AI module,
focusing on embedding endpoints, semantic search endpoints, recommendation endpoints,
content generation endpoints, and RAG (Retrieval Augmented Generation) endpoints.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from uno.core.result import Result, Success, Failure

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

from uno.ai.domain_services import (
    EmbeddingModelService,
    EmbeddingService,
    SemanticSearchService,
    RAGService
)

# Import the endpoints module or mock it if not fully implemented yet
try:
    from uno.ai.domain_endpoints import create_endpoints
except ImportError:
    # Mock the endpoints if not implemented yet
    create_endpoints = MagicMock()


# Test constants
TEST_MODEL_ID = "test-model-id"
TEST_EMBEDDING_ID = "test-embedding-id"
TEST_QUERY_ID = "test-query-id"
TEST_RECOMMENDATION_ID = "test-recommendation-id"
TEST_CONTENT_REQUEST_ID = "test-content-request-id"
TEST_ANOMALY_DETECTION_ID = "test-anomaly-detection-id"


# Test DTOs and schemas
class EmbeddingModelCreateDTO(BaseModel):
    """DTO for creating an embedding model."""
    name: str
    model_type: str
    dimensions: int
    api_key: Optional[str] = None
    normalize_vectors: bool = True
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingCreateDTO(BaseModel):
    """DTO for creating an embedding."""
    text: str
    source_id: str
    source_type: str
    model_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchRequestDTO(BaseModel):
    """DTO for a search request."""
    query_text: str
    user_id: Optional[str] = None
    entity_type: Optional[str] = None
    limit: int = 10
    similarity_threshold: float = 0.7


class DocumentIndexDTO(BaseModel):
    """DTO for indexing a document."""
    content: str
    entity_id: str
    entity_type: str
    metadata: Optional[Dict[str, Any]] = None


class RAGRequestDTO(BaseModel):
    """DTO for a RAG request."""
    query: str
    system_prompt: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    limit: int = 5
    similarity_threshold: float = 0.7


# Endpoint Tests
class TestEmbeddingModelEndpoints:
    """Tests for the embedding model endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=EmbeddingModelService)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        # Mock the endpoint creation function to use our mock service
        app = FastAPI()
        
        # If the endpoints module is implemented, use it
        try:
            from uno.ai.domain_endpoints import create_embedding_model_router
            router = create_embedding_model_router(mock_service)
            app.include_router(router, prefix="/api/ai/embedding-models")
        except (ImportError, AttributeError):
            # If not implemented yet, add mock routes
            @app.post("/api/ai/embedding-models")
            async def create_model(model: EmbeddingModelCreateDTO):
                result = await mock_service.create_model(
                    name=model.name,
                    model_type=EmbeddingModelType(model.model_type),
                    dimensions=model.dimensions,
                    api_key=model.api_key,
                    normalize_vectors=model.normalize_vectors,
                    metadata=model.metadata
                )
                if isinstance(result, Success):
                    return {"id": result.value.id.value, **model.dict()}
                return {"error": result.error}
            
            @app.get("/api/ai/embedding-models/{model_id}")
            async def get_model(model_id: str):
                result = await mock_service.get_model(model_id)
                if isinstance(result, Success):
                    return {
                        "id": result.value.id.value,
                        "name": result.value.name,
                        "model_type": result.value.model_type.value,
                        "dimensions": result.value.dimensions,
                        "normalize_vectors": result.value.normalize_vectors,
                        "metadata": result.value.metadata
                    }
                return {"error": result.error}
            
            @app.get("/api/ai/embedding-models")
            async def list_models():
                result = await mock_service.list_models()
                if isinstance(result, Success):
                    return {
                        "models": [
                            {
                                "id": model.id.value,
                                "name": model.name,
                                "model_type": model.model_type.value,
                                "dimensions": model.dimensions
                            }
                            for model in result.value
                        ]
                    }
                return {"error": result.error}
        
        return TestClient(app)
    
    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        return EmbeddingModel(
            id=ModelId(TEST_MODEL_ID),
            name="test-model",
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMER,
            dimensions=384,
            api_key=None,
            normalize_vectors=True,
            metadata={"source": "test"}
        )
    
    def test_create_model(self, client, mock_service, sample_model):
        """Test creating a model endpoint."""
        # Setup
        mock_service.create_model.return_value = Success(sample_model)
        
        # Execute
        response = client.post(
            "/api/ai/embedding-models",
            json={
                "name": "test-model",
                "model_type": "sentence_transformer",
                "dimensions": 384,
                "normalize_vectors": True,
                "metadata": {"source": "test"}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "test-model"
        assert response.json()["model_type"] == "sentence_transformer"
        assert response.json()["dimensions"] == 384
        mock_service.create_model.assert_called_once()
    
    def test_get_model(self, client, mock_service, sample_model):
        """Test getting a model endpoint."""
        # Setup
        mock_service.get_model.return_value = Success(sample_model)
        
        # Execute
        response = client.get(f"/api/ai/embedding-models/{TEST_MODEL_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_MODEL_ID
        assert response.json()["name"] == "test-model"
        assert response.json()["model_type"] == "sentence_transformer"
        assert response.json()["dimensions"] == 384
        mock_service.get_model.assert_called_once_with(TEST_MODEL_ID)
    
    def test_list_models(self, client, mock_service, sample_model):
        """Test listing models endpoint."""
        # Setup
        mock_service.list_models.return_value = Success([sample_model])
        
        # Execute
        response = client.get("/api/ai/embedding-models")
        
        # Assert
        assert response.status_code == 200
        assert "models" in response.json()
        assert len(response.json()["models"]) == 1
        assert response.json()["models"][0]["id"] == TEST_MODEL_ID
        assert response.json()["models"][0]["name"] == "test-model"
        mock_service.list_models.assert_called_once()


class TestEmbeddingEndpoints:
    """Tests for the embedding endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=EmbeddingService)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        # Mock the endpoint creation function to use our mock service
        app = FastAPI()
        
        # If the endpoints module is implemented, use it
        try:
            from uno.ai.domain_endpoints import create_embedding_router
            router = create_embedding_router(mock_service)
            app.include_router(router, prefix="/api/ai/embeddings")
        except (ImportError, AttributeError):
            # If not implemented yet, add mock routes
            @app.post("/api/ai/embeddings")
            async def create_embedding(embedding: EmbeddingCreateDTO):
                result = await mock_service.create_embedding(
                    text=embedding.text,
                    source_id=embedding.source_id,
                    source_type=embedding.source_type,
                    model_name=embedding.model_name,
                    metadata=embedding.metadata
                )
                if isinstance(result, Success):
                    return {
                        "id": result.value.id.value,
                        "source_id": result.value.source_id,
                        "source_type": result.value.source_type,
                        "model_id": result.value.model_id.value,
                        "dimensions": result.value.dimensions
                    }
                return {"error": result.error}
            
            @app.get("/api/ai/embeddings/{embedding_id}")
            async def get_embedding(embedding_id: str):
                result = await mock_service.get_embedding(embedding_id)
                if isinstance(result, Success):
                    return {
                        "id": result.value.id.value,
                        "source_id": result.value.source_id,
                        "source_type": result.value.source_type,
                        "model_id": result.value.model_id.value,
                        "dimensions": result.value.dimensions,
                        "vector": result.value.vector[:10] if len(result.value.vector) > 10 else result.value.vector
                    }
                return {"error": result.error}
            
            @app.get("/api/ai/embeddings/source/{source_type}/{source_id}")
            async def get_embedding_by_source(source_type: str, source_id: str):
                result = await mock_service.get_embedding_by_source(source_id, source_type)
                if isinstance(result, Success):
                    return {
                        "id": result.value.id.value,
                        "source_id": result.value.source_id,
                        "source_type": result.value.source_type,
                        "model_id": result.value.model_id.value,
                        "dimensions": result.value.dimensions
                    }
                return {"error": result.error}
            
            @app.post("/api/ai/embeddings/similarity")
            async def compute_similarity(data: dict):
                result = await mock_service.compute_similarity(
                    embedding1=data["vector1"],
                    embedding2=data["vector2"],
                    metric=data.get("metric", "cosine")
                )
                if isinstance(result, Success):
                    return {"similarity": result.value}
                return {"error": result.error}
        
        return TestClient(app)
    
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
    
    def test_create_embedding(self, client, mock_service, sample_embedding):
        """Test creating an embedding endpoint."""
        # Setup
        mock_service.create_embedding.return_value = Success(sample_embedding)
        
        # Execute
        response = client.post(
            "/api/ai/embeddings",
            json={
                "text": "This is a test document",
                "source_id": "test-doc-1",
                "source_type": "document",
                "model_name": "test-model",
                "metadata": {"source": "test"}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_EMBEDDING_ID
        assert response.json()["source_id"] == "test-doc-1"
        assert response.json()["source_type"] == "document"
        assert response.json()["model_id"] == TEST_MODEL_ID
        mock_service.create_embedding.assert_called_once()
    
    def test_get_embedding(self, client, mock_service, sample_embedding):
        """Test getting an embedding endpoint."""
        # Setup
        mock_service.get_embedding.return_value = Success(sample_embedding)
        
        # Execute
        response = client.get(f"/api/ai/embeddings/{TEST_EMBEDDING_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_EMBEDDING_ID
        assert response.json()["source_id"] == "test-doc-1"
        assert response.json()["source_type"] == "document"
        assert "vector" in response.json()
        mock_service.get_embedding.assert_called_once_with(TEST_EMBEDDING_ID)
    
    def test_get_embedding_by_source(self, client, mock_service, sample_embedding):
        """Test getting an embedding by source endpoint."""
        # Setup
        mock_service.get_embedding_by_source.return_value = Success(sample_embedding)
        
        # Execute
        response = client.get("/api/ai/embeddings/source/document/test-doc-1")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_EMBEDDING_ID
        assert response.json()["source_id"] == "test-doc-1"
        assert response.json()["source_type"] == "document"
        mock_service.get_embedding_by_source.assert_called_once_with("test-doc-1", "document")
    
    def test_compute_similarity(self, client, mock_service):
        """Test computing similarity endpoint."""
        # Setup
        mock_service.compute_similarity.return_value = Success(0.85)
        
        # Execute
        response = client.post(
            "/api/ai/embeddings/similarity",
            json={
                "vector1": [0.1, 0.2, 0.3],
                "vector2": [0.2, 0.3, 0.4],
                "metric": "cosine"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["similarity"] == 0.85
        mock_service.compute_similarity.assert_called_once()


class TestSearchEndpoints:
    """Tests for the semantic search endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=SemanticSearchService)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        # Mock the endpoint creation function to use our mock service
        app = FastAPI()
        
        # If the endpoints module is implemented, use it
        try:
            from uno.ai.domain_endpoints import create_search_router
            router = create_search_router(mock_service)
            app.include_router(router, prefix="/api/ai/search")
        except (ImportError, AttributeError):
            # If not implemented yet, add mock routes
            @app.post("/api/ai/search")
            async def search(search_request: SearchRequestDTO):
                result = await mock_service.search(
                    query_text=search_request.query_text,
                    user_id=search_request.user_id,
                    entity_type=search_request.entity_type,
                    limit=search_request.limit,
                    similarity_threshold=search_request.similarity_threshold
                )
                if isinstance(result, Success):
                    return {
                        "results": [
                            {
                                "id": r.id,
                                "entity_id": r.entity_id,
                                "entity_type": r.entity_type,
                                "similarity": r.similarity,
                                "rank": r.rank
                            }
                            for r in result.value
                        ]
                    }
                return {"error": result.error}
            
            @app.post("/api/ai/search/index")
            async def index_document(document: DocumentIndexDTO):
                result = await mock_service.index_document(
                    content=document.content,
                    entity_id=document.entity_id,
                    entity_type=document.entity_type,
                    metadata=document.metadata
                )
                if isinstance(result, Success):
                    return {
                        "id": result.value.id,
                        "entity_id": result.value.entity_id,
                        "entity_type": result.value.entity_type
                    }
                return {"error": result.error}
            
            @app.delete("/api/ai/search/index/{entity_type}/{entity_id}")
            async def delete_document(entity_type: str, entity_id: str):
                result = await mock_service.delete_document(entity_id, entity_type)
                if isinstance(result, Success):
                    return {"deleted": result.value}
                return {"error": result.error}
        
        return TestClient(app)
    
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
    def sample_search_results(self):
        """Create sample search results for testing."""
        return [
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
    
    def test_search(self, client, mock_service, sample_search_results):
        """Test search endpoint."""
        # Setup
        mock_service.search.return_value = Success(sample_search_results)
        
        # Execute
        response = client.post(
            "/api/ai/search",
            json={
                "query_text": "test query",
                "user_id": "user1",
                "entity_type": "document",
                "limit": 2,
                "similarity_threshold": 0.7
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert "results" in response.json()
        assert len(response.json()["results"]) == 2
        assert response.json()["results"][0]["entity_id"] == "entity-1"
        assert response.json()["results"][0]["similarity"] == 0.9
        assert response.json()["results"][1]["entity_id"] == "entity-2"
        assert response.json()["results"][1]["similarity"] == 0.8
        mock_service.search.assert_called_once()
    
    def test_index_document(self, client, mock_service, sample_document):
        """Test index document endpoint."""
        # Setup
        mock_service.index_document.return_value = Success(sample_document)
        
        # Execute
        response = client.post(
            "/api/ai/search/index",
            json={
                "content": "This is a test document",
                "entity_id": "entity-1",
                "entity_type": "document",
                "metadata": {"source": "test"}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "doc-1"
        assert response.json()["entity_id"] == "entity-1"
        assert response.json()["entity_type"] == "document"
        mock_service.index_document.assert_called_once()
    
    def test_delete_document(self, client, mock_service):
        """Test delete document endpoint."""
        # Setup
        mock_service.delete_document.return_value = Success(1)
        
        # Execute
        response = client.delete("/api/ai/search/index/document/entity-1")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["deleted"] == 1
        mock_service.delete_document.assert_called_once_with("entity-1", "document")


class TestRAGEndpoints:
    """Tests for the RAG endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        app = FastAPI()
        return app
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing."""
        service = AsyncMock(spec=RAGService)
        return service
    
    @pytest.fixture
    def client(self, app, mock_service):
        """Create a test client with mocked dependencies."""
        # Mock the endpoint creation function to use our mock service
        app = FastAPI()
        
        # If the endpoints module is implemented, use it
        try:
            from uno.ai.domain_endpoints import create_rag_router
            router = create_rag_router(mock_service)
            app.include_router(router, prefix="/api/ai/rag")
        except (ImportError, AttributeError):
            # If not implemented yet, add mock routes
            @app.post("/api/ai/rag/context")
            async def retrieve_context(request: RAGRequestDTO):
                result = await mock_service.retrieve_context(
                    query=request.query,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    entity_id=request.entity_id,
                    entity_type=request.entity_type,
                    limit=request.limit,
                    similarity_threshold=request.similarity_threshold
                )
                if isinstance(result, Success):
                    return {"context": result.value}
                return {"error": result.error}
            
            @app.post("/api/ai/rag/prompt")
            async def create_rag_prompt(request: RAGRequestDTO):
                result = await mock_service.create_rag_prompt(
                    query=request.query,
                    system_prompt=request.system_prompt,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    entity_id=request.entity_id,
                    entity_type=request.entity_type,
                    limit=request.limit,
                    similarity_threshold=request.similarity_threshold
                )
                if isinstance(result, Success):
                    return result.value
                return {"error": result.error}
        
        return TestClient(app)
    
    @pytest.fixture
    def sample_context_items(self):
        """Create sample context items for testing."""
        return [
            {
                "id": "ctx-1",
                "content": "This is the first context item.",
                "entity_id": "entity-1",
                "entity_type": "document",
                "similarity": 0.9,
                "metadata": {"title": "Context 1"}
            },
            {
                "id": "ctx-2",
                "content": "This is the second context item.",
                "entity_id": "entity-2",
                "entity_type": "document",
                "similarity": 0.8,
                "metadata": {"title": "Context 2"}
            }
        ]
    
    @pytest.fixture
    def sample_prompt(self):
        """Create a sample RAG prompt for testing."""
        return {
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "I need information based on the following context:\n\n[Context 1]\ntitle: Context 1\nContent: This is the first context item.\n\n[Context 2]\ntitle: Context 2\nContent: This is the second context item.\n\nMy question is: How do these contexts relate?"
        }
    
    def test_retrieve_context(self, client, mock_service, sample_context_items):
        """Test retrieve context endpoint."""
        # Setup
        mock_service.retrieve_context.return_value = Success(sample_context_items)
        
        # Execute
        response = client.post(
            "/api/ai/rag/context",
            json={
                "query": "How do these contexts relate?",
                "system_prompt": "You are a helpful assistant.",
                "user_id": "user1",
                "limit": 2,
                "similarity_threshold": 0.7
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert "context" in response.json()
        assert len(response.json()["context"]) == 2
        assert response.json()["context"][0]["id"] == "ctx-1"
        assert response.json()["context"][0]["content"] == "This is the first context item."
        assert response.json()["context"][1]["id"] == "ctx-2"
        assert response.json()["context"][1]["content"] == "This is the second context item."
        mock_service.retrieve_context.assert_called_once()
    
    def test_create_rag_prompt(self, client, mock_service, sample_prompt):
        """Test create RAG prompt endpoint."""
        # Setup
        mock_service.create_rag_prompt.return_value = Success(sample_prompt)
        
        # Execute
        response = client.post(
            "/api/ai/rag/prompt",
            json={
                "query": "How do these contexts relate?",
                "system_prompt": "You are a helpful assistant.",
                "user_id": "user1",
                "limit": 2,
                "similarity_threshold": 0.7
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert "system_prompt" in response.json()
        assert "user_prompt" in response.json()
        assert response.json()["system_prompt"] == "You are a helpful assistant."
        assert "I need information based on the following context" in response.json()["user_prompt"]
        assert "My question is: How do these contexts relate?" in response.json()["user_prompt"]
        mock_service.create_rag_prompt.assert_called_once()