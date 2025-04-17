"""
Unit tests for read model query service.

This module contains tests for the ReadModelQueryService and EnhancedQueryService
implementations, verifying their functionality for querying read models.
"""

import pytest
import asyncio
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Type
from unittest.mock import MagicMock, AsyncMock, patch

from uno.read_model.read_model import ReadModel, ReadModelRepository
from uno.read_model.query_service import (
    ReadModelQueryService, EnhancedQueryService, 
    GetByIdQuery, FindByQuery, PaginatedQuery, 
    SearchQuery, AggregateQuery, GraphQuery, HybridQuery,
    PaginatedResult, QueryMetrics
)


# Define a test read model
class TestReadModel(ReadModel):
    """Test read model for query service tests."""
    name: str
    value: int
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


# Mock repository
class MockReadModelRepository(ReadModelRepository[TestReadModel]):
    """Mock repository for testing query services."""
    
    def __init__(self):
        super().__init__(TestReadModel)
        self.models: Dict[str, TestReadModel] = {}
    
    async def get(self, id: str) -> Optional[TestReadModel]:
        """Get a model by ID."""
        return self.models.get(id)
    
    async def find(self, query: Dict[str, Any]) -> List[TestReadModel]:
        """Find models matching query criteria."""
        results = []
        
        for model in self.models.values():
            # Simple property matching
            matches = True
            for key, value in query.items():
                if not hasattr(model, key) or getattr(model, key) != value:
                    matches = False
                    break
            
            if matches:
                results.append(model)
        
        return results
    
    async def save(self, model: TestReadModel) -> TestReadModel:
        """Save a model."""
        self.models[model.id] = model
        return model
    
    async def delete(self, id: str) -> bool:
        """Delete a model."""
        if id in self.models:
            del self.models[id]
            return True
        return False
    
    def add_test_models(self, models: List[TestReadModel]) -> None:
        """Helper to add multiple test models."""
        for model in models:
            self.models[model.id] = model


# Mock graph service
class MockGraphService:
    """Mock graph service for testing."""
    
    async def query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a graph query."""
        # Return a list of node IDs and scores
        return [
            {"id": "model1", "score": 0.9},
            {"id": "model2", "score": 0.8},
            {"id": "model3", "score": 0.7}
        ]


# Mock vector service
class MockVectorService:
    """Mock vector service for testing."""
    
    async def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a vector search."""
        # Return a list of node IDs and scores
        return [
            {"id": "model1", "score": 0.95},
            {"id": "model3", "score": 0.85},
            {"id": "model4", "score": 0.75}
        ]


# Test fixtures
@pytest.fixture
def test_models() -> List[TestReadModel]:
    """Create test models for query testing."""
    return [
        TestReadModel(id="model1", name="Test Model 1", value=100, tags=["tag1", "tag2"]),
        TestReadModel(id="model2", name="Test Model 2", value=200, tags=["tag2", "tag3"]),
        TestReadModel(id="model3", name="Another Test", value=150, tags=["tag1", "tag3"]),
        TestReadModel(id="model4", name="Final Test", value=300, tags=["tag4"]),
    ]


@pytest.fixture
def mock_repository(test_models: List[TestReadModel]) -> MockReadModelRepository:
    """Create a mock repository with test models."""
    repo = MockReadModelRepository()
    repo.add_test_models(test_models)
    return repo


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Create a mock cache."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def query_service(mock_repository: MockReadModelRepository, mock_cache: AsyncMock) -> ReadModelQueryService[TestReadModel]:
    """Create a query service with mock dependencies."""
    return ReadModelQueryService(
        repository=mock_repository,
        model_type=TestReadModel,
        cache=mock_cache
    )


@pytest.fixture
def mock_graph_service() -> MockGraphService:
    """Create a mock graph service."""
    return MockGraphService()


@pytest.fixture
def mock_vector_service() -> MockVectorService:
    """Create a mock vector service."""
    return MockVectorService()


@pytest.fixture
def enhanced_query_service(
    mock_repository: MockReadModelRepository,
    mock_cache: AsyncMock,
    mock_graph_service: MockGraphService,
    mock_vector_service: MockVectorService
) -> EnhancedQueryService[TestReadModel]:
    """Create an enhanced query service with mock dependencies."""
    return EnhancedQueryService(
        repository=mock_repository,
        model_type=TestReadModel,
        cache=mock_cache,
        graph_service=mock_graph_service,
        vector_service=mock_vector_service
    )


# Test basic query service
@pytest.mark.asyncio
async def test_get_by_id(query_service: ReadModelQueryService[TestReadModel]):
    """Test getting a read model by ID."""
    # Get existing model
    model = await query_service.get_by_id("model1")
    assert model is not None
    assert model.id == "model1"
    assert model.name == "Test Model 1"
    
    # Get non-existent model
    model = await query_service.get_by_id("non-existent")
    assert model is None


@pytest.mark.asyncio
async def test_get_by_id_with_cache(
    query_service: ReadModelQueryService[TestReadModel],
    mock_cache: AsyncMock,
    test_models: List[TestReadModel]
):
    """Test getting a read model by ID with cache hit."""
    # Set up cache to return a model
    mock_cache.get.return_value = test_models[0]
    
    # Get model (should come from cache)
    model = await query_service.get_by_id("model1")
    
    assert model is not None
    assert model.id == "model1"
    
    # Verify cache was checked
    mock_cache.get.assert_called_once_with("model1")
    # Verify no save to cache (since it was already cached)
    mock_cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_find(query_service: ReadModelQueryService[TestReadModel]):
    """Test finding read models by criteria."""
    # Find by value
    models = await query_service.find({"value": 100})
    assert len(models) == 1
    assert models[0].id == "model1"
    
    # Find by tag
    models = await query_service.find({"tags": ["tag1", "tag2"]})
    assert len(models) == 1
    assert models[0].id == "model1"
    
    # Find with no match
    models = await query_service.find({"name": "Non-existent"})
    assert len(models) == 0


@pytest.mark.asyncio
async def test_paginate(query_service: ReadModelQueryService[TestReadModel]):
    """Test paginating query results."""
    # Create a paginated query
    query = PaginatedQuery(page=1, page_size=2, sort_by="value", sort_direction="asc")
    
    # Execute the query
    result = await query_service.paginate(query)
    
    # Check result
    assert isinstance(result, PaginatedResult)
    assert result.page == 1
    assert result.page_size == 2
    assert result.total == 4
    assert result.pages == 2
    assert len(result.items) == 2
    
    # Check sorting (ascending by value)
    assert result.items[0].value == 100  # model1
    assert result.items[1].value == 150  # model3
    
    # Test next page
    query = PaginatedQuery(page=2, page_size=2, sort_by="value", sort_direction="asc")
    result = await query_service.paginate(query)
    
    assert result.page == 2
    assert len(result.items) == 2
    assert result.items[0].value == 200  # model2
    assert result.items[1].value == 300  # model4
    
    # Test descending sort
    query = PaginatedQuery(page=1, page_size=2, sort_by="value", sort_direction="desc")
    result = await query_service.paginate(query)
    
    assert result.items[0].value == 300  # model4
    assert result.items[1].value == 200  # model2


@pytest.mark.asyncio
async def test_handle_query(query_service: ReadModelQueryService[TestReadModel]):
    """Test generic query handling."""
    # Test GetByIdQuery
    get_query = GetByIdQuery(id="model1")
    result = await query_service.handle_query(get_query)
    assert result is not None
    assert result.id == "model1"
    
    # Test FindByQuery
    find_query = FindByQuery(criteria={"value": 200})
    result = await query_service.handle_query(find_query)
    assert len(result) == 1
    assert result[0].id == "model2"
    
    # Test PaginatedQuery
    paginated_query = PaginatedQuery(page=1, page_size=2)
    result = await query_service.handle_query(paginated_query)
    assert isinstance(result, PaginatedResult)
    assert len(result.items) == 2
    
    # Test unsupported query type
    with pytest.raises(ValueError):
        await query_service.handle_query(MagicMock())


@pytest.mark.asyncio
async def test_metrics_collection(query_service: ReadModelQueryService[TestReadModel]):
    """Test that query metrics are collected."""
    # Enable metrics collection
    query_service.metrics_enabled = True
    
    # Execute a query
    await query_service.get_by_id("model1")
    
    # Check metrics
    metrics = query_service.get_recent_metrics()
    assert len(metrics) == 1
    assert metrics[0]["query_type"] == "get_by_id"
    assert metrics[0]["result_count"] == 1
    assert metrics[0]["duration_ms"] is not None
    
    # Execute another query
    await query_service.find({"value": 200})
    
    # Check updated metrics
    metrics = query_service.get_recent_metrics()
    assert len(metrics) == 2
    assert metrics[1]["query_type"] == "find"
    assert metrics[1]["result_count"] == 1


# Test enhanced query service
@pytest.mark.asyncio
async def test_search(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test search functionality with vector service."""
    # Create a search query
    query = SearchQuery(
        text="test",
        fields=["name"],
        page=1,
        page_size=10
    )
    
    # Execute the query
    result = await enhanced_query_service.search(query)
    
    # Check result
    assert isinstance(result, PaginatedResult)
    assert len(result.items) == 3  # model1, model3, model4 from mock vector service


@pytest.mark.asyncio
async def test_search_fallback(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test search fallback when vector service is not available."""
    # Remove vector service
    enhanced_query_service.vector_service = None
    
    # Create a search query
    query = SearchQuery(
        text="Test",
        fields=["name"],
        page=1,
        page_size=10
    )
    
    # Execute the query
    result = await enhanced_query_service.search(query)
    
    # Check result - should use basic text search
    assert isinstance(result, PaginatedResult)
    assert len(result.items) == 3  # Should find models with "Test" in name


@pytest.mark.asyncio
async def test_aggregate(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test aggregation functionality."""
    # Create an aggregate query
    query = AggregateQuery(
        group_by=["tags"],
        aggregates={"value": "sum"}
    )
    
    # Execute the query
    # Note: This is a simplified test since our mock repository doesn't fully
    # support the complex grouping logic required by aggregate
    with patch.object(enhanced_query_service.repository, 'find', return_value=[
        TestReadModel(id="1", name="Test 1", value=100, tags=["tag1"]),
        TestReadModel(id="2", name="Test 2", value=200, tags=["tag1"]), 
        TestReadModel(id="3", name="Test 3", value=300, tags=["tag2"])
    ]):
        results = await enhanced_query_service.aggregate(query)
    
    # Check results
    assert len(results) > 0
    # The exact structure depends on the implementation details
    # But we should expect aggregated values


@pytest.mark.asyncio
async def test_graph_query(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test graph query functionality."""
    # Create a graph query
    query = GraphQuery(
        start_node="model1",
        path_pattern="(a)-[:RELATES_TO]->(b)",
        max_depth=2
    )
    
    # Execute the query
    results = await enhanced_query_service.graph_query(query)
    
    # Check results
    assert len(results) == 3  # model1, model2, model3 from mock graph service


@pytest.mark.asyncio
async def test_graph_query_no_service(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test graph query when graph service is not available."""
    # Remove graph service
    enhanced_query_service.graph_service = None
    
    # Create a graph query
    query = GraphQuery(
        start_node="model1",
        path_pattern="(a)-[:RELATES_TO]->(b)",
        max_depth=2
    )
    
    # Execute the query
    results = await enhanced_query_service.graph_query(query)
    
    # Check results
    assert len(results) == 0  # Should return empty list when no service


@pytest.mark.asyncio
async def test_hybrid_query(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test hybrid query functionality combining vector and graph."""
    # Create a hybrid query
    query = HybridQuery(
        text="test",
        path_pattern="(a)-[:RELATES_TO]->(b)",
        vector_weight=0.6,
        graph_weight=0.4,
        page=1,
        page_size=10
    )
    
    # Execute the query
    result = await enhanced_query_service.hybrid_query(query)
    
    # Check result
    assert isinstance(result, PaginatedResult)
    # Should contain a blend of results from both services
    assert len(result.items) > 0


@pytest.mark.asyncio
async def test_hybrid_query_fallback(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test hybrid query fallback when vector service is not available."""
    # Remove vector service
    enhanced_query_service.vector_service = None
    
    # Create a hybrid query
    query = HybridQuery(
        text="test",
        path_pattern="(a)-[:RELATES_TO]->(b)",
        page=1,
        page_size=10
    )
    
    # Execute the query
    result = await enhanced_query_service.hybrid_query(query)
    
    # Check result - should fall back to basic search
    assert isinstance(result, PaginatedResult)
    assert len(result.items) > 0


@pytest.mark.asyncio
async def test_enhanced_handle_query(enhanced_query_service: EnhancedQueryService[TestReadModel]):
    """Test enhanced query handling."""
    # Test SearchQuery
    search_query = SearchQuery(text="test")
    with patch.object(enhanced_query_service, 'search', return_value=PaginatedResult(
        items=[TestReadModel(id="1", name="Test", value=100)],
        total=1,
        page=1,
        page_size=10
    )):
        result = await enhanced_query_service.handle_query(search_query)
        assert isinstance(result, PaginatedResult)
    
    # Test AggregateQuery
    agg_query = AggregateQuery(group_by=["tags"], aggregates={"value": "sum"})
    with patch.object(enhanced_query_service, 'aggregate', return_value=[{"tags": "tag1", "sum_value": 300}]):
        result = await enhanced_query_service.handle_query(agg_query)
        assert isinstance(result, list)
    
    # Test GraphQuery
    graph_query = GraphQuery(start_node="model1", path_pattern="(a)-[]->(b)")
    with patch.object(enhanced_query_service, 'graph_query', return_value=[TestReadModel(id="1", name="Test", value=100)]):
        result = await enhanced_query_service.handle_query(graph_query)
        assert isinstance(result, list)
    
    # Test HybridQuery
    hybrid_query = HybridQuery(text="test")
    with patch.object(enhanced_query_service, 'hybrid_query', return_value=PaginatedResult(
        items=[TestReadModel(id="1", name="Test", value=100)],
        total=1,
        page=1,
        page_size=10
    )):
        result = await enhanced_query_service.handle_query(hybrid_query)
        assert isinstance(result, PaginatedResult)
    
    # Test fallback to base handler
    with patch.object(ReadModelQueryService, 'handle_query', return_value="base_result"):
        base_query = GetByIdQuery(id="model1")
        result = await enhanced_query_service.handle_query(base_query)
        assert result == "base_result"