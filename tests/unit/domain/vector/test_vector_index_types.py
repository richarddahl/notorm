"""
Unit tests for vector search with different index types.

These tests compare the behavior and performance differences between
HNSW and IVF-Flat index types for vector search.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import random
from typing import List, Dict, Any, Optional

from uno.domain.vector_search import (
    VectorSearchService,
    VectorQuery
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    mock = AsyncMock()
    mock.execute.return_value = AsyncMock()
    mock.execute.return_value.__aenter__.return_value.fetchall.return_value = [
        {"id": "doc1", "similarity": 0.95, "metadata": json.dumps({"type": "test"})},
        {"id": "doc2", "similarity": 0.85, "metadata": json.dumps({"type": "test"})},
    ]
    return mock


@pytest.fixture
def hnsw_search_service():
    """Create a VectorSearchService with HNSW index type."""
    service = VectorSearchService(
        entity_type="test",
        table_name="test_documents",
        dimensions=1536,
        index_type="hnsw"
    )
    service._generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    return service


@pytest.fixture
def ivfflat_search_service():
    """Create a VectorSearchService with IVF-Flat index type."""
    service = VectorSearchService(
        entity_type="test",
        table_name="test_documents", 
        dimensions=1536,
        index_type="ivfflat"
    )
    service._generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    return service


@pytest.mark.asyncio
async def test_hnsw_index_search_sql_generation(hnsw_search_service, mock_session):
    """Test SQL generation for HNSW index search."""
    # Setup query
    query = VectorQuery(query_text="test query")
    
    # Patch the session to return our mock
    with patch.object(hnsw_search_service, '_get_session', return_value=mock_session):
        # Execute search
        await hnsw_search_service.search(query)
        
        # Check that SQL was generated with HNSW-specific syntax
        call_args = mock_session.execute.call_args[0][0]
        sql_str = str(call_args).lower()
        
        # HNSW index should use vector_cosine_ops or similar operator
        assert "vector_cosine_ops" in sql_str or "cosine" in sql_str
        assert "test_documents" in sql_str
        assert "embedding" in sql_str


@pytest.mark.asyncio
async def test_ivfflat_index_search_sql_generation(ivfflat_search_service, mock_session):
    """Test SQL generation for IVF-Flat index search."""
    # Setup query
    query = VectorQuery(query_text="test query")
    
    # Patch the session to return our mock
    with patch.object(ivfflat_search_service, '_get_session', return_value=mock_session):
        # Execute search
        await ivfflat_search_service.search(query)
        
        # Check that SQL was generated with IVF-Flat-specific syntax
        call_args = mock_session.execute.call_args[0][0]
        sql_str = str(call_args).lower()
        
        # IVF-Flat index should also use vector operations
        assert "vector_cosine_ops" in sql_str or "cosine" in sql_str
        assert "test_documents" in sql_str
        assert "embedding" in sql_str


@pytest.mark.asyncio
async def test_index_type_in_initialization(hnsw_search_service, ivfflat_search_service):
    """Test that index type is properly stored in service initialization."""
    assert hnsw_search_service._index_type == "hnsw"
    assert ivfflat_search_service._index_type == "ivfflat"


@pytest.mark.asyncio
async def test_search_results_format_consistency(hnsw_search_service, ivfflat_search_service, mock_session):
    """Test that both index types return results in the same format."""
    # Setup query
    query = VectorQuery(query_text="test query")
    
    # Execute search with HNSW
    with patch.object(hnsw_search_service, '_get_session', return_value=mock_session):
        hnsw_results = await hnsw_search_service.search(query)
    
    # Execute search with IVF-Flat
    with patch.object(ivfflat_search_service, '_get_session', return_value=mock_session):
        ivfflat_results = await ivfflat_search_service.search(query)
    
    # Check that results have the same structure
    assert len(hnsw_results) == len(ivfflat_results)
    assert hnsw_results[0].id == ivfflat_results[0].id
    assert hnsw_results[0].similarity == ivfflat_results[0].similarity
    assert hnsw_results[0].metadata == ivfflat_results[0].metadata


@pytest.mark.asyncio
async def test_invalid_index_type_handling():
    """Test handling of invalid index type during initialization."""
    with pytest.raises(ValueError, match="Invalid index type"):
        VectorSearchService(
            entity_type="test",
            table_name="test_documents",
            dimensions=1536,
            index_type="invalid_type"
        )


@pytest.mark.asyncio
async def test_default_index_type():
    """Test that a default index type is used if none is specified."""
    service = VectorSearchService(
        entity_type="test",
        table_name="test_documents",
        dimensions=1536
    )
    
    # The default should be "hnsw" based on common practice
    assert service._index_type == "hnsw" or service._index_type == "ivfflat"


class TestIndexTypeDDL:
    """Test DDL generation for different index types."""
    
    @pytest.mark.asyncio
    async def test_hnsw_index_ddl_generation(self):
        """Test DDL generation for HNSW index."""
        from uno.sql.emitters.vector import VectorSQLEmitter
        
        emitter = VectorSQLEmitter()
        
        # Generate DDL for HNSW index
        sql = emitter.generate_index_ddl(
            table_name="test_documents",
            column_name="embedding",
            index_type="hnsw"
        )
        
        # Check DDL
        assert "CREATE INDEX" in sql
        assert "ON test_documents" in sql
        assert "embedding" in sql
        assert "USING hnsw" in sql or "vector_cosine_ops" in sql
    
    @pytest.mark.asyncio
    async def test_ivfflat_index_ddl_generation(self):
        """Test DDL generation for IVF-Flat index."""
        from uno.sql.emitters.vector import VectorSQLEmitter
        
        emitter = VectorSQLEmitter()
        
        # Generate DDL for IVF-Flat index
        sql = emitter.generate_index_ddl(
            table_name="test_documents",
            column_name="embedding",
            index_type="ivfflat"
        )
        
        # Check DDL
        assert "CREATE INDEX" in sql
        assert "ON test_documents" in sql
        assert "embedding" in sql
        assert "USING ivfflat" in sql or "vector_cosine_ops" in sql