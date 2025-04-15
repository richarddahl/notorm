"""
Integration tests for vector search with typed results.

This module tests the vector search functionality with typed results,
ensuring that vector search operations correctly return typed entities.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any, TypeVar

from uno.domain.core import Entity
from uno.domain.repository import Repository
from uno.domain.vector_search import (
    VectorSearchService,
    VectorQuery,
    VectorSearchResult,
    TypedVectorSearchResult,
    TypedVectorSearchResponse
)


# Define a test entity class
class ProductEntity(Entity):
    """Test product entity for vector search."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        price: float,
        categories: List[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        """Initialize product entity."""
        super().__init__(id)
        self.name = name
        self.description = description
        self.price = price
        self.categories = categories or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()


# Define a mock repository for testing
class MockProductRepository(Repository[ProductEntity]):
    """Mock repository for product entities."""

    def __init__(self):
        """Initialize mock repository with test data."""
        self.products = {
            "1": ProductEntity(
                id="1",
                name="Laptop",
                description="Powerful laptop with high-performance specs",
                price=999.99,
                categories=["electronics", "computers"]
            ),
            "2": ProductEntity(
                id="2",
                name="Smartphone",
                description="Latest smartphone with advanced camera",
                price=699.99,
                categories=["electronics", "phones"]
            ),
            "3": ProductEntity(
                id="3",
                name="Headphones",
                description="Noise-cancelling wireless headphones",
                price=199.99,
                categories=["electronics", "audio"]
            ),
            "4": ProductEntity(
                id="4",
                name="Coffee Maker",
                description="Automatic coffee maker with built-in grinder",
                price=149.99,
                categories=["kitchen", "appliances"]
            ),
            "5": ProductEntity(
                id="5",
                name="Fitness Tracker",
                description="Track your activity with this smart fitness wearable",
                price=89.99,
                categories=["electronics", "wearables", "fitness"]
            )
        }

    async def get(self, id: str) -> Optional[ProductEntity]:
        """Get entity by ID."""
        return self.products.get(id)

    async def get_many(self, ids: List[str]) -> List[ProductEntity]:
        """Get multiple entities by IDs."""
        return [self.products[id] for id in ids if id in self.products]

    async def create(self, entity: ProductEntity) -> ProductEntity:
        """Create entity (not used in tests)."""
        self.products[entity.id] = entity
        return entity

    async def update(self, entity: ProductEntity) -> ProductEntity:
        """Update entity (not used in tests)."""
        self.products[entity.id] = entity
        return entity

    async def delete(self, id: str) -> bool:
        """Delete entity (not used in tests)."""
        if id in self.products:
            del self.products[id]
            return True
        return False


# Create a mock vector search service that doesn't actually use DB
class MockVectorSearchService(VectorSearchService[ProductEntity]):
    """Mock vector search service for testing typed results."""

    def __init__(self, repository: Repository[ProductEntity]):
        """Initialize with repository but don't create real DB emitter."""
        self.entity_type = ProductEntity
        self.table_name = "products"
        self.repository = repository
        self.schema = "public"

    async def search(self, query: VectorQuery) -> List[VectorSearchResult]:
        """Mock vector search that returns hardcoded results."""
        # Mock similarity search based on query text
        results = []
        
        if "laptop" in query.query_text.lower():
            results.append(VectorSearchResult(id="1", similarity=0.95))
        
        if "phone" in query.query_text.lower() or "smartphone" in query.query_text.lower():
            results.append(VectorSearchResult(id="2", similarity=0.92))
        
        if "headphone" in query.query_text.lower() or "audio" in query.query_text.lower():
            results.append(VectorSearchResult(id="3", similarity=0.88))
        
        if "coffee" in query.query_text.lower() or "kitchen" in query.query_text.lower():
            results.append(VectorSearchResult(id="4", similarity=0.85))
        
        if "fitness" in query.query_text.lower() or "wearable" in query.query_text.lower():
            results.append(VectorSearchResult(id="5", similarity=0.82))
        
        # If no specific matches, return generic results with lower similarity
        if not results:
            results = [
                VectorSearchResult(id="1", similarity=0.65),
                VectorSearchResult(id="2", similarity=0.63),
                VectorSearchResult(id="3", similarity=0.61)
            ]
        
        # Limit results
        results = results[:query.limit]
        
        # Load entities if repository is available
        if self.repository:
            for result in results:
                entity = await self.repository.get(result.id)
                if entity:
                    result.entity = entity
        
        return results


@pytest.fixture
def product_repository():
    """Create a mock product repository."""
    return MockProductRepository()


@pytest.fixture
def vector_service(product_repository):
    """Create a mock vector search service."""
    return MockVectorSearchService(product_repository)


@pytest.mark.asyncio
async def test_vector_search_with_typed_results(vector_service):
    """Test vector search with typed results."""
    # Create a query
    query = VectorQuery(
        query_text="I need a new laptop",
        limit=3,
        threshold=0.5
    )
    
    # Perform search with typed results
    response = await vector_service.search_typed(query)
    
    # Check response type
    assert isinstance(response, TypedVectorSearchResponse)
    
    # Check results
    assert len(response.results) > 0
    assert isinstance(response.results[0], TypedVectorSearchResult)
    assert isinstance(response.results[0].entity, ProductEntity)
    
    # Get entities directly
    entities = response.get_entities()
    assert len(entities) > 0
    assert all(isinstance(entity, ProductEntity) for entity in entities)
    
    # Test filtering
    best_match = response.get_best_match()
    assert best_match is not None
    assert best_match.id == "1"  # Laptop should be the best match
    
    # Test entity access
    assert best_match.entity.name == "Laptop"
    assert "computers" in best_match.entity.categories


@pytest.mark.asyncio
async def test_vector_search_filtering(vector_service):
    """Test vector search with filtering by similarity."""
    # Create a query
    query = VectorQuery(
        query_text="electronics devices",
        limit=5,
        threshold=0.5
    )
    
    # Perform search with typed results
    response = await vector_service.search_typed(query)
    
    # Filter by similarity
    high_similarity = response.filter_by_similarity(0.8)
    assert len(high_similarity) <= len(response.results)
    
    # Filter to specific product type
    for result in response.results:
        result.metadata["product_type"] = result.entity.categories[0]
    
    # Filter by metadata
    electronics = response.filter_by_metadata("product_type", "electronics")
    assert len(electronics) > 0
    assert all("electronics" in result.entity.categories for result in electronics)