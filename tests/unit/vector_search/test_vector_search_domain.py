"""
Tests for the Vector Search module domain components.

This module contains comprehensive tests for the Vector Search module domain entities,
repositories, and services to ensure proper functionality and compliance with 
domain-driven design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

from uno.core.result import Success, Failure
from uno.vector_search.entities import (
    VectorId, IndexId, EmbeddingId, SearchQueryId,
    VectorIndex, Embedding, SearchQuery, SearchResult,
    HybridSearchQuery, TypedSearchResult, RAGContext,
    IndexType, DistanceMetric, EmbeddingModel
)
from uno.vector_search.domain_repositories import (
    VectorIndexRepository, EmbeddingRepository, SearchRepository
)
from uno.vector_search.domain_services import (
    VectorIndexService, EmbeddingService, SearchService, RAGService, VectorSearchService
)

# Test Data
TEST_INDEX_ID = "test_index"
TEST_EMBEDDING_ID = "test_embedding"
TEST_QUERY_ID = "test_query"
TEST_SOURCE_ID = "test_source"
TEST_SOURCE_TYPE = "test_source_type"
TEST_VECTOR = [0.1, 0.2, 0.3, 0.4, 0.5]
TEST_DIMENSION = 5


class TestValueObjects:
    """Tests for the value objects."""

    def test_vector_id(self):
        """Test VectorId value object."""
        # Arrange
        value = "test_vector"
        
        # Act
        vector_id = VectorId(value)
        
        # Assert
        assert vector_id.value == value
        # Test immutability
        with pytest.raises(Exception):
            vector_id.value = "new_value"

    def test_index_id(self):
        """Test IndexId value object."""
        # Arrange
        value = TEST_INDEX_ID
        
        # Act
        index_id = IndexId(value)
        
        # Assert
        assert index_id.value == value
        # Test immutability
        with pytest.raises(Exception):
            index_id.value = "new_value"

    def test_embedding_id(self):
        """Test EmbeddingId value object."""
        # Arrange
        value = TEST_EMBEDDING_ID
        
        # Act
        embedding_id = EmbeddingId(value)
        
        # Assert
        assert embedding_id.value == value
        # Test immutability
        with pytest.raises(Exception):
            embedding_id.value = "new_value"

    def test_search_query_id(self):
        """Test SearchQueryId value object."""
        # Arrange
        value = TEST_QUERY_ID
        
        # Act
        query_id = SearchQueryId(value)
        
        # Assert
        assert query_id.value == value
        # Test immutability
        with pytest.raises(Exception):
            query_id.value = "new_value"


class TestVectorIndexEntity:
    """Tests for the VectorIndex domain entity."""

    def test_create_vector_index(self):
        """Test creating a vector index entity."""
        # Arrange
        index_id = IndexId(TEST_INDEX_ID)
        name = "Test Index"
        dimension = TEST_DIMENSION
        index_type = IndexType.HNSW
        distance_metric = DistanceMetric.COSINE
        
        # Act
        index = VectorIndex(
            id=index_id,
            name=name,
            dimension=dimension,
            index_type=index_type,
            distance_metric=distance_metric
        )
        
        # Assert
        assert index.id == index_id
        assert index.name == name
        assert index.dimension == dimension
        assert index.index_type == index_type
        assert index.distance_metric == distance_metric
        assert isinstance(index.created_at, datetime)
        assert isinstance(index.updated_at, datetime)
        assert index.metadata == {}

    def test_update_vector_index(self):
        """Test updating a vector index entity."""
        # Arrange
        index = VectorIndex(
            id=IndexId(TEST_INDEX_ID),
            name="Test Index",
            dimension=TEST_DIMENSION,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.COSINE
        )
        original_created_at = index.created_at
        original_updated_at = index.updated_at
        
        # Wait a moment to ensure updated_at will be different
        import time
        time.sleep(0.001)
        
        # Act
        index.update(
            name="Updated Index",
            distance_metric=DistanceMetric.L2,
            metadata={"key": "value"}
        )
        
        # Assert
        assert index.name == "Updated Index"
        assert index.distance_metric == DistanceMetric.L2
        assert index.metadata == {"key": "value"}
        assert index.created_at == original_created_at
        assert index.updated_at > original_updated_at


class TestEmbeddingEntity:
    """Tests for the Embedding domain entity."""

    def test_create_embedding(self):
        """Test creating an embedding entity."""
        # Arrange
        embedding_id = EmbeddingId(TEST_EMBEDDING_ID)
        vector = TEST_VECTOR
        source_id = TEST_SOURCE_ID
        source_type = TEST_SOURCE_TYPE
        model = EmbeddingModel.DEFAULT
        dimension = TEST_DIMENSION
        
        # Act
        embedding = Embedding(
            id=embedding_id,
            vector=vector,
            source_id=source_id,
            source_type=source_type,
            model=model,
            dimension=dimension
        )
        
        # Assert
        assert embedding.id == embedding_id
        assert embedding.vector == vector
        assert embedding.source_id == source_id
        assert embedding.source_type == source_type
        assert embedding.model == model
        assert embedding.dimension == dimension
        assert isinstance(embedding.created_at, datetime)
        assert embedding.metadata == {}

    def test_update_vector(self):
        """Test updating an embedding vector."""
        # Arrange
        embedding = Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=TEST_VECTOR,
            source_id=TEST_SOURCE_ID,
            source_type=TEST_SOURCE_TYPE,
            model=EmbeddingModel.DEFAULT,
            dimension=TEST_DIMENSION
        )
        new_vector = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        # Act
        embedding.update_vector(new_vector)
        
        # Assert
        assert embedding.vector == new_vector
        assert embedding.dimension == len(new_vector)


class TestSearchQueryEntity:
    """Tests for the SearchQuery domain entity."""

    def test_create_search_query(self):
        """Test creating a search query entity."""
        # Arrange
        query_id = SearchQueryId(TEST_QUERY_ID)
        query_text = "test query"
        query_vector = TEST_VECTOR
        filters = {"field": "value"}
        limit = 20
        threshold = 0.8
        
        # Act
        query = SearchQuery(
            id=query_id,
            query_text=query_text,
            query_vector=query_vector,
            filters=filters,
            limit=limit,
            threshold=threshold
        )
        
        # Assert
        assert query.id == query_id
        assert query.query_text == query_text
        assert query.query_vector == query_vector
        assert query.filters == filters
        assert query.limit == limit
        assert query.threshold == threshold
        assert query.metric == "cosine"
        assert query.index_id is None
        assert isinstance(query.created_at, datetime)
        assert query.metadata == {}


class TestHybridSearchQueryEntity:
    """Tests for the HybridSearchQuery domain entity."""

    def test_create_hybrid_search_query(self):
        """Test creating a hybrid search query entity."""
        # Arrange
        query_id = SearchQueryId(TEST_QUERY_ID)
        query_text = "test query"
        query_vector = TEST_VECTOR
        start_node_type = "User"
        start_filters = {"active": True}
        path_pattern = "(user)-[:CREATED]->(post)"
        
        # Act
        query = HybridSearchQuery(
            id=query_id,
            query_text=query_text,
            query_vector=query_vector,
            start_node_type=start_node_type,
            start_filters=start_filters,
            path_pattern=path_pattern,
            combine_method="intersect",
            graph_weight=0.6,
            vector_weight=0.4
        )
        
        # Assert
        assert query.id == query_id
        assert query.query_text == query_text
        assert query.query_vector == query_vector
        assert query.start_node_type == start_node_type
        assert query.start_filters == start_filters
        assert query.path_pattern == path_pattern
        assert query.combine_method == "intersect"
        assert query.graph_weight == 0.6
        assert query.vector_weight == 0.4


class TestSearchResultEntity:
    """Tests for the SearchResult domain entity."""

    def test_create_search_result(self):
        """Test creating a search result entity."""
        # Arrange
        result_id = str(uuid.uuid4())
        similarity = 0.95
        entity_id = "entity123"
        entity_type = "User"
        query_id = TEST_QUERY_ID
        rank = 1
        
        # Act
        result = SearchResult(
            id=result_id,
            similarity=similarity,
            entity_id=entity_id,
            entity_type=entity_type,
            query_id=query_id,
            rank=rank
        )
        
        # Assert
        assert result.id == result_id
        assert result.similarity == similarity
        assert result.entity_id == entity_id
        assert result.entity_type == entity_type
        assert result.query_id == query_id
        assert result.rank == rank
        assert result.metadata == {}
        assert isinstance(result.created_at, datetime)


class TestTypedSearchResultEntity:
    """Tests for the TypedSearchResult domain entity."""

    def test_create_typed_search_result(self):
        """Test creating a typed search result entity."""
        # Arrange
        result_id = str(uuid.uuid4())
        similarity = 0.95
        entity = {"id": "entity123", "name": "Test Entity"}
        rank = 1
        
        # Act
        result = TypedSearchResult(
            id=result_id,
            similarity=similarity,
            entity=entity,
            rank=rank
        )
        
        # Assert
        assert result.id == result_id
        assert result.similarity == similarity
        assert result.entity == entity
        assert result.rank == rank
        assert result.metadata == {}


class TestRAGContextEntity:
    """Tests for the RAGContext domain entity."""

    def test_create_rag_context(self):
        """Test creating a RAG context entity."""
        # Arrange
        query = "How do vector databases work?"
        system_prompt = "You are a helpful assistant."
        results = [
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.95,
                entity_id="entity1",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=1,
                metadata={"content": "Vector databases store and retrieve vectors efficiently."}
            ),
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.85,
                entity_id="entity2",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=2,
                metadata={"content": "Embeddings are high-dimensional vector representations."}
            )
        ]
        
        # Act
        context = RAGContext(
            query=query,
            system_prompt=system_prompt,
            results=results
        )
        
        # Assert
        assert context.query == query
        assert context.system_prompt == system_prompt
        assert context.results == results
        assert context.formatted_context is None
        assert context.metadata == {}
        assert isinstance(context.created_at, datetime)

    def test_format_context(self):
        """Test formatting the RAG context."""
        # Arrange
        context = RAGContext(
            query="How do vector databases work?",
            system_prompt="You are a helpful assistant.",
            results=[
                SearchResult(
                    id=str(uuid.uuid4()),
                    similarity=0.95,
                    entity_id="entity1",
                    entity_type="Document",
                    query_id=TEST_QUERY_ID,
                    rank=1,
                    metadata={"content": "Vector databases store and retrieve vectors efficiently."}
                ),
                SearchResult(
                    id=str(uuid.uuid4()),
                    similarity=0.85,
                    entity_id="entity2",
                    entity_type="Document",
                    query_id=TEST_QUERY_ID,
                    rank=2,
                    metadata={"content": "Embeddings are high-dimensional vector representations."}
                )
            ]
        )
        
        def format_results(results):
            """Simple formatter function."""
            return "\n".join([
                f"Document {i+1}: {r.metadata.get('content', '')}"
                for i, r in enumerate(results)
            ])
        
        # Act
        formatted = context.format_context(format_results)
        
        # Assert
        assert formatted == context.formatted_context
        assert "Vector databases store and retrieve vectors efficiently" in formatted
        assert "Embeddings are high-dimensional vector representations" in formatted

    def test_create_prompt(self):
        """Test creating a prompt from RAG context."""
        # Arrange
        context = RAGContext(
            query="How do vector databases work?",
            system_prompt="You are a helpful assistant.",
            results=[
                SearchResult(
                    id=str(uuid.uuid4()),
                    similarity=0.95,
                    entity_id="entity1",
                    entity_type="Document",
                    query_id=TEST_QUERY_ID,
                    rank=1,
                    metadata={"content": "Vector databases store and retrieve vectors efficiently."}
                )
            ]
        )
        
        # Format the context
        context.format_context(lambda results: "Vector databases use embeddings.")
        
        # Act
        prompt = context.create_prompt()
        
        # Assert
        assert prompt["system_prompt"] == "You are a helpful assistant."
        assert "Vector databases use embeddings." in prompt["user_prompt"]
        assert "How do vector databases work?" in prompt["user_prompt"]

    def test_create_prompt_without_formatting(self):
        """Test creating a prompt without formatting the context first."""
        # Arrange
        context = RAGContext(
            query="How do vector databases work?",
            system_prompt="You are a helpful assistant.",
            results=[]
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Context has not been formatted yet"):
            context.create_prompt()


# Repository Tests

class TestVectorIndexRepository:
    """Tests for the VectorIndexRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a VectorIndexRepository instance."""
        return VectorIndexRepository()

    @pytest.fixture
    def mock_result(self):
        """Create a mock SQL result."""
        result = AsyncMock()
        result.fetchone.return_value = Mock(
            id=TEST_INDEX_ID,
            name="Test Index",
            dimension=TEST_DIMENSION,
            index_type="hnsw",
            distance_metric="cosine",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            metadata={}
        )
        return result

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session, mock_result):
        """Test creating a vector index successfully."""
        # Arrange
        index = VectorIndex(
            id=IndexId(TEST_INDEX_ID),
            name="Test Index",
            dimension=TEST_DIMENSION,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.COSINE
        )
        
        # Mock the execute calls
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.create(index)
        
        # Assert
        assert result.is_success
        assert result.value.id.value == TEST_INDEX_ID
        assert result.value.name == "Test Index"
        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_name(self, repository, mock_session):
        """Test creating a vector index with a duplicate name."""
        # Arrange
        index = VectorIndex(
            id=IndexId(TEST_INDEX_ID),
            name="Test Index",
            dimension=TEST_DIMENSION,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.COSINE
        )
        
        # Mock the execute calls
        result_mock = AsyncMock()
        result_mock.fetchone.return_value = {"id": "existing_id"}  # Existing index
        mock_session.execute.return_value = result_mock
        
        # Act
        result = await repository.create(index)
        
        # Assert
        assert result.is_failure
        assert "already exists" in str(result.error)
        mock_session.commit.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_get_success(self, repository, mock_session, mock_result):
        """Test getting a vector index successfully."""
        # Arrange
        index_id = IndexId(TEST_INDEX_ID)
        
        # Mock the execute calls
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get(index_id)
        
        # Assert
        assert result.is_success
        assert result.value.id.value == TEST_INDEX_ID
        assert result.value.name == "Test Index"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(self, repository, mock_session):
        """Test getting a vector index when not found."""
        # Arrange
        index_id = IndexId("nonexistent")
        
        # Mock the execute calls
        result_mock = AsyncMock()
        result_mock.fetchone.return_value = None  # Not found
        mock_session.execute.return_value = result_mock
        
        # Act
        result = await repository.get(index_id)
        
        # Assert
        assert result.is_failure
        assert "not found" in str(result.error)

    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_session, mock_result):
        """Test updating a vector index successfully."""
        # Arrange
        index = VectorIndex(
            id=IndexId(TEST_INDEX_ID),
            name="Updated Index",
            dimension=TEST_DIMENSION,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.L2
        )
        
        # Mock the execute calls
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.update(index)
        
        # Assert
        assert result.is_success
        assert result.value.id.value == TEST_INDEX_ID
        assert result.value.name == "Updated Index"
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestEmbeddingRepository:
    """Tests for the EmbeddingRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create an EmbeddingRepository instance."""
        return EmbeddingRepository()

    @pytest.fixture
    def mock_result(self):
        """Create a mock SQL result."""
        result = AsyncMock()
        result.fetchone.return_value = Mock(
            id=TEST_EMBEDDING_ID,
            vector=TEST_VECTOR,
            source_id=TEST_SOURCE_ID,
            source_type=TEST_SOURCE_TYPE,
            model="default",
            dimension=TEST_DIMENSION,
            created_at=datetime.now(UTC),
            metadata={}
        )
        return result

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session, mock_result):
        """Test creating an embedding successfully."""
        # Arrange
        embedding = Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=TEST_VECTOR,
            source_id=TEST_SOURCE_ID,
            source_type=TEST_SOURCE_TYPE,
            model=EmbeddingModel.DEFAULT,
            dimension=TEST_DIMENSION
        )
        
        # Mock the execute calls
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.create(embedding)
        
        # Assert
        assert result.is_success
        assert result.value.id.value == TEST_EMBEDDING_ID
        assert result.value.vector == TEST_VECTOR
        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_source(self, repository, mock_session):
        """Test creating an embedding with a duplicate source."""
        # Arrange
        embedding = Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=TEST_VECTOR,
            source_id=TEST_SOURCE_ID,
            source_type=TEST_SOURCE_TYPE,
            model=EmbeddingModel.DEFAULT,
            dimension=TEST_DIMENSION
        )
        
        # Mock the execute calls
        result_mock = AsyncMock()
        result_mock.fetchone.return_value = {"id": "existing_id"}  # Existing embedding
        mock_session.execute.return_value = result_mock
        
        # Act
        result = await repository.create(embedding)
        
        # Assert
        assert result.is_failure
        assert "already exists" in str(result.error)
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_success(self, repository, mock_session, mock_result):
        """Test getting an embedding successfully."""
        # Arrange
        embedding_id = EmbeddingId(TEST_EMBEDDING_ID)
        
        # Mock the execute calls
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get(embedding_id)
        
        # Assert
        assert result.is_success
        assert result.value.id.value == TEST_EMBEDDING_ID
        assert result.value.vector == TEST_VECTOR
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_source_success(self, repository, mock_session, mock_result):
        """Test getting an embedding by source successfully."""
        # Arrange
        source_id = TEST_SOURCE_ID
        source_type = TEST_SOURCE_TYPE
        
        # Mock the execute calls
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get_by_source(source_id, source_type)
        
        # Assert
        assert result.is_success
        assert result.value.source_id == source_id
        assert result.value.source_type == source_type
        mock_session.execute.assert_called_once()


class TestSearchRepository:
    """Tests for the SearchRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a SearchRepository instance."""
        return SearchRepository()

    @pytest.mark.asyncio
    async def test_save_query_success(self, repository, mock_session):
        """Test saving a search query successfully."""
        # Arrange
        query = SearchQuery(
            id=SearchQueryId(TEST_QUERY_ID),
            query_text="test query",
            query_vector=TEST_VECTOR
        )
        
        # Mock the execute calls
        result_mock = AsyncMock()
        mock_session.execute.return_value = result_mock
        
        # Act
        with patch.object(repository, 'session', return_value=mock_session):
            result = await repository.save_query(query)
        
        # Assert
        assert result.is_success
        assert result.value.id.value == TEST_QUERY_ID
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_results_success(self, repository, mock_session):
        """Test saving search results successfully."""
        # Arrange
        results = [
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.95,
                entity_id="entity1",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=1
            ),
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.85,
                entity_id="entity2",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=2
            )
        ]
        
        # Mock the execute calls
        mock_session.execute_many.return_value = None
        
        # Act
        with patch.object(repository, 'session', return_value=mock_session):
            result = await repository.save_results(results)
        
        # Assert
        assert result.is_success
        assert result.value == results
        mock_session.execute_many.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_results_empty(self, repository, mock_session):
        """Test saving empty search results."""
        # Arrange
        results = []
        
        # Act
        with patch.object(repository, 'session', return_value=mock_session):
            result = await repository.save_results(results)
        
        # Assert
        assert result.is_success
        assert result.value == []
        mock_session.execute_many.assert_not_called()
        mock_session.commit.assert_not_called()


# Service Tests

class TestVectorIndexService:
    """Tests for the VectorIndexService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a VectorIndexService instance."""
        return VectorIndexService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_index_success(self, service, mock_repository):
        """Test creating a vector index successfully."""
        # Arrange
        index = VectorIndex(
            id=IndexId(TEST_INDEX_ID),
            name="Test Index",
            dimension=TEST_DIMENSION,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.COSINE
        )
        mock_repository.create.return_value = Success(index)
        
        # Act
        result = await service.create_index(
            name="Test Index",
            dimension=TEST_DIMENSION,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.COSINE
        )
        
        # Assert
        assert result.is_success
        assert result.value.name == "Test Index"
        assert result.value.dimension == TEST_DIMENSION
        assert result.value.index_type == IndexType.HNSW
        assert result.value.distance_metric == DistanceMetric.COSINE
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_index_success(self, service, mock_repository):
        """Test getting a vector index successfully."""
        # Arrange
        index_id = IndexId(TEST_INDEX_ID)
        index = VectorIndex(
            id=index_id,
            name="Test Index",
            dimension=TEST_DIMENSION,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.COSINE
        )
        mock_repository.get.return_value = Success(index)
        
        # Act
        result = await service.get_index(index_id)
        
        # Assert
        assert result.is_success
        assert result.value.id == index_id
        assert result.value.name == "Test Index"
        mock_repository.get.assert_called_once_with(index_id)

    @pytest.mark.asyncio
    async def test_list_indices_success(self, service, mock_repository):
        """Test listing vector indices successfully."""
        # Arrange
        indices = [
            VectorIndex(
                id=IndexId("index1"),
                name="Index 1",
                dimension=TEST_DIMENSION,
                index_type=IndexType.HNSW,
                distance_metric=DistanceMetric.COSINE
            ),
            VectorIndex(
                id=IndexId("index2"),
                name="Index 2",
                dimension=TEST_DIMENSION,
                index_type=IndexType.IVFFLAT,
                distance_metric=DistanceMetric.L2
            )
        ]
        mock_repository.list.return_value = Success(indices)
        
        # Act
        result = await service.list_indices()
        
        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert result.value[0].name == "Index 1"
        assert result.value[1].name == "Index 2"
        mock_repository.list.assert_called_once()


class TestEmbeddingService:
    """Tests for the EmbeddingService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create an EmbeddingService instance."""
        return EmbeddingService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_embedding_success(self, service, mock_repository):
        """Test creating an embedding successfully."""
        # Arrange
        embedding = Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=TEST_VECTOR,
            source_id=TEST_SOURCE_ID,
            source_type=TEST_SOURCE_TYPE,
            model=EmbeddingModel.DEFAULT,
            dimension=TEST_DIMENSION
        )
        mock_repository.create.return_value = Success(embedding)
        
        # Act
        result = await service.create_embedding(
            vector=TEST_VECTOR,
            source_id=TEST_SOURCE_ID,
            source_type=TEST_SOURCE_TYPE,
            model=EmbeddingModel.DEFAULT
        )
        
        # Assert
        assert result.is_success
        assert result.value.vector == TEST_VECTOR
        assert result.value.source_id == TEST_SOURCE_ID
        assert result.value.source_type == TEST_SOURCE_TYPE
        assert result.value.model == EmbeddingModel.DEFAULT
        assert result.value.dimension == TEST_DIMENSION
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embedding_success(self, service, mock_repository):
        """Test getting an embedding successfully."""
        # Arrange
        embedding_id = EmbeddingId(TEST_EMBEDDING_ID)
        embedding = Embedding(
            id=embedding_id,
            vector=TEST_VECTOR,
            source_id=TEST_SOURCE_ID,
            source_type=TEST_SOURCE_TYPE,
            model=EmbeddingModel.DEFAULT,
            dimension=TEST_DIMENSION
        )
        mock_repository.get.return_value = Success(embedding)
        
        # Act
        result = await service.get_embedding(embedding_id)
        
        # Assert
        assert result.is_success
        assert result.value.id == embedding_id
        assert result.value.vector == TEST_VECTOR
        mock_repository.get.assert_called_once_with(embedding_id)

    @pytest.mark.asyncio
    async def test_get_embedding_by_source_success(self, service, mock_repository):
        """Test getting an embedding by source successfully."""
        # Arrange
        source_id = TEST_SOURCE_ID
        source_type = TEST_SOURCE_TYPE
        embedding = Embedding(
            id=EmbeddingId(TEST_EMBEDDING_ID),
            vector=TEST_VECTOR,
            source_id=source_id,
            source_type=source_type,
            model=EmbeddingModel.DEFAULT,
            dimension=TEST_DIMENSION
        )
        mock_repository.get_by_source.return_value = Success(embedding)
        
        # Act
        result = await service.get_embedding_by_source(source_id, source_type)
        
        # Assert
        assert result.is_success
        assert result.value.source_id == source_id
        assert result.value.source_type == source_type
        mock_repository.get_by_source.assert_called_once_with(source_id, source_type)


class TestSearchService:
    """Tests for the SearchService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a SearchService instance."""
        return SearchService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_search_success(self, service, mock_repository):
        """Test performing a search successfully."""
        # Arrange
        query_text = "test query"
        query = SearchQuery(
            id=SearchQueryId(TEST_QUERY_ID),
            query_text=query_text,
            query_vector=TEST_VECTOR
        )
        results = [
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.95,
                entity_id="entity1",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=1
            ),
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.85,
                entity_id="entity2",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=2
            )
        ]
        mock_repository.search.return_value = Success(results)
        
        # Act
        result = await service.search(query_text=query_text)
        
        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert result.value[0].similarity == 0.95
        assert result.value[0].entity_id == "entity1"
        assert result.value[1].similarity == 0.85
        assert result.value[1].entity_id == "entity2"
        mock_repository.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_vector_success(self, service, mock_repository):
        """Test performing a vector search successfully."""
        # Arrange
        vector = TEST_VECTOR
        results = [
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.95,
                entity_id="entity1",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=1
            )
        ]
        mock_repository.search.return_value = Success(results)
        
        # Act
        result = await service.search_vector(vector=vector)
        
        # Assert
        assert result.is_success
        assert len(result.value) == 1
        assert result.value[0].similarity == 0.95
        assert result.value[0].entity_id == "entity1"
        mock_repository.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_hybrid_search_success(self, service, mock_repository):
        """Test performing a hybrid search successfully."""
        # Arrange
        query_text = "test query"
        start_node_type = "User"
        results = [
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.95,
                entity_id="entity1",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=1
            )
        ]
        mock_repository.hybrid_search.return_value = Success(results)
        
        # Act
        result = await service.hybrid_search(
            query_text=query_text,
            start_node_type=start_node_type
        )
        
        # Assert
        assert result.is_success
        assert len(result.value) == 1
        assert result.value[0].similarity == 0.95
        assert result.value[0].entity_id == "entity1"
        mock_repository.hybrid_search.assert_called_once()


class TestRAGService:
    """Tests for the RAGService."""

    @pytest.fixture
    def mock_search_service(self):
        """Create a mock search service."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_search_service):
        """Create a RAGService instance."""
        service = RAGService()
        service.search_service = mock_search_service
        return service

    @pytest.mark.asyncio
    async def test_generate_context_success(self, service, mock_search_service):
        """Test generating RAG context successfully."""
        # Arrange
        query = "How do vector databases work?"
        system_prompt = "You are a helpful assistant."
        results = [
            SearchResult(
                id=str(uuid.uuid4()),
                similarity=0.95,
                entity_id="entity1",
                entity_type="Document",
                query_id=TEST_QUERY_ID,
                rank=1,
                metadata={"content": "Vector databases store and retrieve vectors efficiently."}
            )
        ]
        mock_search_service.search.return_value = Success(results)
        
        # Act
        result = await service.generate_context(
            query=query,
            system_prompt=system_prompt
        )
        
        # Assert
        assert result.is_success
        assert result.value.query == query
        assert result.value.system_prompt == system_prompt
        assert result.value.results == results
        mock_search_service.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_format_context_success(self, service):
        """Test formatting RAG context successfully."""
        # Arrange
        context = RAGContext(
            query="How do vector databases work?",
            system_prompt="You are a helpful assistant.",
            results=[
                SearchResult(
                    id=str(uuid.uuid4()),
                    similarity=0.95,
                    entity_id="entity1",
                    entity_type="Document",
                    query_id=TEST_QUERY_ID,
                    rank=1,
                    metadata={"content": "Vector databases store and retrieve vectors efficiently."}
                )
            ]
        )
        
        # Act
        result = service.format_context(context)
        
        # Assert
        assert result.is_success
        assert result.value.formatted_context is not None
        assert "Vector databases" in result.value.formatted_context

    @pytest.mark.asyncio
    async def test_generate_prompt_success(self, service):
        """Test generating a prompt from RAG context successfully."""
        # Arrange
        context = RAGContext(
            query="How do vector databases work?",
            system_prompt="You are a helpful assistant.",
            results=[
                SearchResult(
                    id=str(uuid.uuid4()),
                    similarity=0.95,
                    entity_id="entity1",
                    entity_type="Document",
                    query_id=TEST_QUERY_ID,
                    rank=1,
                    metadata={"content": "Vector databases store and retrieve vectors efficiently."}
                )
            ]
        )
        
        # Format the context
        context.format_context(lambda results: "Vector databases use embeddings.")
        
        # Act
        result = service.generate_prompt(context)
        
        # Assert
        assert result.is_success
        assert "system_prompt" in result.value
        assert "user_prompt" in result.value
        assert result.value["system_prompt"] == "You are a helpful assistant."
        assert "Vector databases use embeddings." in result.value["user_prompt"]
        assert "How do vector databases work?" in result.value["user_prompt"]