"""
Tests for the Queries module domain components.

This module contains comprehensive tests for the Queries module domain entities,
repositories, and services to ensure proper functionality and compliance with 
domain-driven design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any, Optional

from uno.core.result import Success, Failure
from uno.enums import Include, Match
from uno.queries.entities import QueryPath, QueryValue, Query
from uno.queries.domain_repositories import (
    QueryPathRepository, QueryValueRepository, QueryRepository
)
from uno.queries.domain_services import (
    QueryPathService, QueryValueService, QueryService
)

# Test Data
TEST_QUERY_PATH_ID = "test_query_path"
TEST_QUERY_VALUE_ID = "test_query_value"
TEST_QUERY_ID = "test_query"
TEST_SOURCE_META_TYPE_ID = "source_meta_type"
TEST_TARGET_META_TYPE_ID = "target_meta_type"
TEST_CYPHER_PATH = "MATCH (s:SourceType)-[r:RELATES_TO]->(t:TargetType)"
TEST_DATA_TYPE = "string"
TEST_QUERY_NAME = "Test Query"


class TestQueryPathEntity:
    """Tests for the QueryPath domain entity."""

    def test_create_query_path(self):
        """Test creating a query path entity."""
        # Arrange
        path_id = TEST_QUERY_PATH_ID
        source_meta_type_id = TEST_SOURCE_META_TYPE_ID
        target_meta_type_id = TEST_TARGET_META_TYPE_ID
        cypher_path = TEST_CYPHER_PATH
        data_type = TEST_DATA_TYPE
        
        # Act
        query_path = QueryPath(
            id=path_id,
            source_meta_type_id=source_meta_type_id,
            target_meta_type_id=target_meta_type_id,
            cypher_path=cypher_path,
            data_type=data_type
        )
        
        # Assert
        assert query_path.id == path_id
        assert query_path.source_meta_type_id == source_meta_type_id
        assert query_path.target_meta_type_id == target_meta_type_id
        assert query_path.cypher_path == cypher_path
        assert query_path.data_type == data_type
        assert query_path.source_meta_type is None
        assert query_path.target_meta_type is None
        assert query_path.__uno_model__ == "QueryPathModel"

    def test_validate_query_path_valid(self):
        """Test validation with a valid query path."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        
        # Act & Assert
        query_path.validate()  # Should not raise an exception

    def test_validate_query_path_invalid_empty_source_meta_type_id(self):
        """Test validation with empty source meta type ID."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id="",  # Empty source meta type ID
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Source meta type ID cannot be empty"):
            query_path.validate()

    def test_validate_query_path_invalid_empty_target_meta_type_id(self):
        """Test validation with empty target meta type ID."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id="",  # Empty target meta type ID
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Target meta type ID cannot be empty"):
            query_path.validate()

    def test_validate_query_path_invalid_empty_cypher_path(self):
        """Test validation with empty cypher path."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path="",  # Empty cypher path
            data_type=TEST_DATA_TYPE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cypher path cannot be empty"):
            query_path.validate()

    def test_validate_query_path_invalid_empty_data_type(self):
        """Test validation with empty data type."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=""  # Empty data type
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Data type cannot be empty"):
            query_path.validate()

    def test_string_representation(self):
        """Test string representation of query path."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        
        # Act & Assert
        assert str(query_path) == TEST_CYPHER_PATH


class TestQueryValueEntity:
    """Tests for the QueryValue domain entity."""

    def test_create_query_value(self):
        """Test creating a query value entity."""
        # Arrange
        value_id = TEST_QUERY_VALUE_ID
        query_path_id = TEST_QUERY_PATH_ID
        include = Include.INCLUDE
        match = Match.AND
        lookup = "equal"
        
        # Act
        query_value = QueryValue(
            id=value_id,
            query_path_id=query_path_id,
            include=include,
            match=match,
            lookup=lookup
        )
        
        # Assert
        assert query_value.id == value_id
        assert query_value.query_path_id == query_path_id
        assert query_value.include == include
        assert query_value.match == match
        assert query_value.lookup == lookup
        assert query_value.query_path is None
        assert query_value.values == []
        assert query_value.queries == []
        assert query_value.__uno_model__ == "QueryValueModel"

    def test_validate_query_value_valid(self):
        """Test validation with a valid query value with values."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID,
            include=Include.INCLUDE,
            match=Match.AND,
            lookup="equal"
        )
        query_value.add_value("test_value")
        
        # Act & Assert
        query_value.validate()  # Should not raise an exception

    def test_validate_query_value_valid_with_queries(self):
        """Test validation with a valid query value with queries."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID,
            include=Include.INCLUDE,
            match=Match.AND,
            lookup="equal"
        )
        
        # Add a query to the query value
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        query_value.add_query(query)
        
        # Act & Assert
        query_value.validate()  # Should not raise an exception

    def test_validate_query_value_invalid_empty_query_path_id(self):
        """Test validation with empty query path ID."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id="",  # Empty query path ID
            include=Include.INCLUDE,
            match=Match.AND,
            lookup="equal"
        )
        query_value.add_value("test_value")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Query path ID cannot be empty"):
            query_value.validate()

    def test_validate_query_value_invalid_include(self):
        """Test validation with invalid include value."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID,
            include="INVALID",  # Invalid include value
            match=Match.AND,
            lookup="equal"
        )
        query_value.add_value("test_value")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid include value"):
            query_value.validate()

    def test_validate_query_value_invalid_match(self):
        """Test validation with invalid match value."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID,
            include=Include.INCLUDE,
            match="INVALID",  # Invalid match value
            lookup="equal"
        )
        query_value.add_value("test_value")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid match value"):
            query_value.validate()

    def test_validate_query_value_invalid_no_values_or_queries(self):
        """Test validation with no values or queries."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID,
            include=Include.INCLUDE,
            match=Match.AND,
            lookup="equal"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Query value must have either values or queries"):
            query_value.validate()

    def test_add_value(self):
        """Test adding a value to a query value."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        value = "test_value"
        
        # Act
        query_value.add_value(value)
        
        # Assert
        assert value in query_value.values
        assert len(query_value.values) == 1
        
        # Adding the same value again should not duplicate
        query_value.add_value(value)
        assert len(query_value.values) == 1

    def test_remove_value(self):
        """Test removing a value from a query value."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        value = "test_value"
        query_value.add_value(value)
        assert value in query_value.values
        
        # Act
        query_value.remove_value(value)
        
        # Assert
        assert value not in query_value.values
        assert len(query_value.values) == 0
        
        # Removing a value that's not in the list should not raise an error
        query_value.remove_value(value)

    def test_add_query(self):
        """Test adding a query to a query value."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        
        # Act
        query_value.add_query(query)
        
        # Assert
        assert query in query_value.queries
        assert len(query_value.queries) == 1
        
        # Adding the same query again should not duplicate
        query_value.add_query(query)
        assert len(query_value.queries) == 1

    def test_remove_query(self):
        """Test removing a query from a query value."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        query_value.add_query(query)
        assert query in query_value.queries
        
        # Act
        query_value.remove_query(query)
        
        # Assert
        assert query not in query_value.queries
        assert len(query_value.queries) == 0
        
        # Removing a query that's not in the list should not raise an error
        query_value.remove_query(query)


class TestQueryEntity:
    """Tests for the Query domain entity."""

    def test_create_query(self):
        """Test creating a query entity."""
        # Arrange
        query_id = TEST_QUERY_ID
        name = TEST_QUERY_NAME
        query_meta_type_id = TEST_SOURCE_META_TYPE_ID
        
        # Act
        query = Query(
            id=query_id,
            name=name,
            query_meta_type_id=query_meta_type_id
        )
        
        # Assert
        assert query.id == query_id
        assert query.name == name
        assert query.query_meta_type_id == query_meta_type_id
        assert query.description is None
        assert query.include_values == Include.INCLUDE
        assert query.match_values == Match.AND
        assert query.include_queries == Include.INCLUDE
        assert query.match_queries == Match.AND
        assert query.query_meta_type is None
        assert query.query_values == []
        assert query.sub_queries == []
        assert query.__uno_model__ == "QueryModel"

    def test_validate_query_valid(self):
        """Test validation with a valid query."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            include_values=Include.INCLUDE,
            match_values=Match.AND,
            include_queries=Include.INCLUDE,
            match_queries=Match.AND
        )
        
        # Act & Assert
        query.validate()  # Should not raise an exception

    def test_validate_query_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name="",  # Empty name
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Name cannot be empty"):
            query.validate()

    def test_validate_query_invalid_empty_query_meta_type_id(self):
        """Test validation with empty query meta type ID."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=""  # Empty query meta type ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Query meta type ID cannot be empty"):
            query.validate()

    def test_validate_query_invalid_include_values(self):
        """Test validation with invalid include_values."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            include_values="INVALID"  # Invalid include_values
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid include_values"):
            query.validate()

    def test_validate_query_invalid_match_values(self):
        """Test validation with invalid match_values."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            match_values="INVALID"  # Invalid match_values
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid match_values"):
            query.validate()

    def test_validate_query_invalid_include_queries(self):
        """Test validation with invalid include_queries."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            include_queries="INVALID"  # Invalid include_queries
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid include_queries"):
            query.validate()

    def test_validate_query_invalid_match_queries(self):
        """Test validation with invalid match_queries."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            match_queries="INVALID"  # Invalid match_queries
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid match_queries"):
            query.validate()

    def test_string_representation(self):
        """Test string representation of query."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        
        # Act & Assert
        assert str(query) == TEST_QUERY_NAME

    def test_add_query_value(self):
        """Test adding a query value to a query."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        
        # Act
        query.add_query_value(query_value)
        
        # Assert
        assert query_value in query.query_values
        assert query in query_value.queries
        assert len(query.query_values) == 1
        
        # Adding the same query value again should not duplicate
        query.add_query_value(query_value)
        assert len(query.query_values) == 1

    def test_remove_query_value(self):
        """Test removing a query value from a query."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        query.add_query_value(query_value)
        assert query_value in query.query_values
        assert query in query_value.queries
        
        # Act
        query.remove_query_value(query_value)
        
        # Assert
        assert query_value not in query.query_values
        assert query not in query_value.queries
        assert len(query.query_values) == 0
        
        # Removing a query value that's not in the list should not raise an error
        query.remove_query_value(query_value)

    def test_add_sub_query(self):
        """Test adding a sub-query to a query."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        sub_query = Query(
            id="sub_query",
            name="Sub Query",
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        
        # Act
        query.add_sub_query(sub_query)
        
        # Assert
        assert sub_query in query.sub_queries
        assert len(query.sub_queries) == 1
        
        # Adding the same sub-query again should not duplicate
        query.add_sub_query(sub_query)
        assert len(query.sub_queries) == 1

    def test_add_sub_query_circular_reference(self):
        """Test adding a query as its own sub-query."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot add query as its own sub-query"):
            query.add_sub_query(query)

    def test_remove_sub_query(self):
        """Test removing a sub-query from a query."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        sub_query = Query(
            id="sub_query",
            name="Sub Query",
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        query.add_sub_query(sub_query)
        assert sub_query in query.sub_queries
        
        # Act
        query.remove_sub_query(sub_query)
        
        # Assert
        assert sub_query not in query.sub_queries
        assert len(query.sub_queries) == 0
        
        # Removing a sub-query that's not in the list should not raise an error
        query.remove_sub_query(sub_query)


# Repository Tests

class TestQueryPathRepository:
    """Tests for the QueryPathRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a QueryPathRepository instance."""
        return QueryPathRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting a query path by ID successfully."""
        # Arrange
        query_path_id = TEST_QUERY_PATH_ID
        mock_session.get.return_value = QueryPath(
            id=query_path_id,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )

        # Act
        result = await repository.get_by_id(query_path_id, mock_session)

        # Assert
        assert result.is_success
        query_path = result.value
        assert query_path.id == query_path_id
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_attribute_id(self, repository, mock_session):
        """Test finding query paths by attribute ID."""
        # Arrange
        attribute_id = "test_attribute"
        query_paths = [
            QueryPath(
                id="path1",
                source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
                target_meta_type_id=TEST_TARGET_META_TYPE_ID,
                cypher_path=TEST_CYPHER_PATH,
                data_type=TEST_DATA_TYPE
            ),
            QueryPath(
                id="path2",
                source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
                target_meta_type_id="another_target",
                cypher_path="Another path",
                data_type=TEST_DATA_TYPE
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = query_paths

        # Act
        result = await repository.find_by_attribute_id(attribute_id, mock_session)

        # Assert
        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_meta_type_id(self, repository, mock_session):
        """Test finding query paths by meta type ID."""
        # Arrange
        meta_type_id = TEST_SOURCE_META_TYPE_ID
        query_paths = [
            QueryPath(
                id="path1",
                source_meta_type_id=meta_type_id,
                target_meta_type_id=TEST_TARGET_META_TYPE_ID,
                cypher_path=TEST_CYPHER_PATH,
                data_type=TEST_DATA_TYPE
            ),
            QueryPath(
                id="path2",
                source_meta_type_id=meta_type_id,
                target_meta_type_id="another_target",
                cypher_path="Another path",
                data_type=TEST_DATA_TYPE
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = query_paths

        # Act
        result = await repository.find_by_meta_type_id(meta_type_id, mock_session)

        # Assert
        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_path_name(self, repository, mock_session):
        """Test finding query paths by path name."""
        # Arrange
        path_name = "test_path"
        query_paths = [
            QueryPath(
                id="path1",
                source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
                target_meta_type_id=TEST_TARGET_META_TYPE_ID,
                cypher_path=path_name,
                data_type=TEST_DATA_TYPE
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = query_paths

        # Act
        result = await repository.find_by_path_name(path_name, mock_session)

        # Assert
        assert len(result) == 1
        mock_session.execute.assert_called_once()


class TestQueryValueRepository:
    """Tests for the QueryValueRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a QueryValueRepository instance."""
        return QueryValueRepository()

    @pytest.mark.asyncio
    async def test_find_by_query_id(self, repository, mock_session):
        """Test finding query values by query ID."""
        # Arrange
        query_id = TEST_QUERY_ID
        query_values = [
            QueryValue(
                id="value1",
                query_path_id=TEST_QUERY_PATH_ID
            ),
            QueryValue(
                id="value2",
                query_path_id="another_path"
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = query_values

        # Act
        result = await repository.find_by_query_id(query_id, mock_session)

        # Assert
        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_query_path_id(self, repository, mock_session):
        """Test finding query values by query path ID."""
        # Arrange
        query_path_id = TEST_QUERY_PATH_ID
        query_values = [
            QueryValue(
                id="value1",
                query_path_id=query_path_id
            ),
            QueryValue(
                id="value2",
                query_path_id=query_path_id
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = query_values

        # Act
        result = await repository.find_by_query_path_id(query_path_id, mock_session)

        # Assert
        assert len(result) == 2
        assert all(qv.query_path_id == query_path_id for qv in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_for_query(self, repository, mock_session):
        """Test deleting query values for a query."""
        # Arrange
        query_id = TEST_QUERY_ID
        
        # Act
        await repository.delete_for_query(query_id, mock_session)
        
        # Assert
        mock_session.execute.assert_called_once()


class TestQueryRepository:
    """Tests for the QueryRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a QueryRepository instance."""
        return QueryRepository()

    @pytest.mark.asyncio
    async def test_find_by_name(self, repository, mock_session):
        """Test finding queries by name."""
        # Arrange
        name = TEST_QUERY_NAME
        queries = [
            Query(
                id=TEST_QUERY_ID,
                name=name,
                query_meta_type_id=TEST_SOURCE_META_TYPE_ID
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = queries

        # Act
        result = await repository.find_by_name(name, mock_session)

        # Assert
        assert len(result) == 1
        assert result[0].name == name
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_meta_type_id(self, repository, mock_session):
        """Test finding queries by meta type ID."""
        # Arrange
        meta_type_id = TEST_SOURCE_META_TYPE_ID
        queries = [
            Query(
                id="query1",
                name="Query 1",
                query_meta_type_id=meta_type_id
            ),
            Query(
                id="query2",
                name="Query 2",
                query_meta_type_id=meta_type_id
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = queries

        # Act
        result = await repository.find_by_meta_type_id(meta_type_id, mock_session)

        # Assert
        assert len(result) == 2
        assert all(q.query_meta_type_id == meta_type_id for q in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_with_values(self, repository, mock_session):
        """Test finding a query with its values."""
        # Arrange
        query_id = TEST_QUERY_ID
        query = Query(
            id=query_id,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        
        # Mock DB models as needed
        mock_session.get.return_value = query
        
        # Mock joined load execution
        mock_query = AsyncMock()
        mock_session.execute.return_value.scalar.return_value = query
        
        # Act
        result = await repository.find_with_values(query_id, mock_session)
        
        # Assert
        assert result.id == query_id
        assert result.name == TEST_QUERY_NAME
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_all_with_values(self, repository, mock_session):
        """Test finding all queries with their values."""
        # Arrange
        queries = [
            Query(
                id="query1",
                name="Query 1",
                query_meta_type_id=TEST_SOURCE_META_TYPE_ID
            ),
            Query(
                id="query2",
                name="Query 2",
                query_meta_type_id=TEST_SOURCE_META_TYPE_ID
            )
        ]
        mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = queries
        
        # Act
        result = await repository.find_all_with_values(mock_session)
        
        # Assert
        assert len(result) == 2
        mock_session.execute.assert_called_once()


# Service Tests

class TestQueryPathService:
    """Tests for the QueryPathService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=QueryPathRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create a QueryPathService instance."""
        return QueryPathService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_query_path_success(self, service, mock_repository):
        """Test creating a query path successfully."""
        # Arrange
        query_path = QueryPath(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )
        mock_repository.save.return_value = Success(query_path)

        # Act
        result = await service.create(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_QUERY_PATH_ID
        assert result.value.source_meta_type_id == TEST_SOURCE_META_TYPE_ID
        assert result.value.target_meta_type_id == TEST_TARGET_META_TYPE_ID
        assert result.value.cypher_path == TEST_CYPHER_PATH
        assert result.value.data_type == TEST_DATA_TYPE
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_query_path_validation_error(self, service):
        """Test creating a query path with validation error."""
        # Act - Missing required source_meta_type_id
        result = await service.create(
            id=TEST_QUERY_PATH_ID,
            source_meta_type_id="",  # Empty source meta type ID
            target_meta_type_id=TEST_TARGET_META_TYPE_ID,
            cypher_path=TEST_CYPHER_PATH,
            data_type=TEST_DATA_TYPE
        )

        # Assert
        assert result.is_failure
        assert "Source meta type ID cannot be empty" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_meta_type_id_success(self, service, mock_repository):
        """Test finding query paths by meta type ID successfully."""
        # Arrange
        meta_type_id = TEST_SOURCE_META_TYPE_ID
        query_paths = [
            QueryPath(
                id="path1",
                source_meta_type_id=meta_type_id,
                target_meta_type_id=TEST_TARGET_META_TYPE_ID,
                cypher_path=TEST_CYPHER_PATH,
                data_type=TEST_DATA_TYPE
            ),
            QueryPath(
                id="path2",
                source_meta_type_id=meta_type_id,
                target_meta_type_id="another_target",
                cypher_path="Another path",
                data_type=TEST_DATA_TYPE
            )
        ]
        mock_repository.find_by_meta_type_id.return_value = query_paths

        # Act
        result = await service.find_by_meta_type_id(meta_type_id)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(qp.source_meta_type_id == meta_type_id for qp in result.value)
        mock_repository.find_by_meta_type_id.assert_called_once_with(meta_type_id, None)


class TestQueryValueService:
    """Tests for the QueryValueService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=QueryValueRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create a QueryValueService instance."""
        return QueryValueService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_query_value_success(self, service, mock_repository):
        """Test creating a query value successfully."""
        # Arrange
        query_value = QueryValue(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID
        )
        query_value.add_value("test_value")
        mock_repository.save.return_value = Success(query_value)

        # Act
        result = await service.create(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID,
            values=["test_value"]
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_QUERY_VALUE_ID
        assert result.value.query_path_id == TEST_QUERY_PATH_ID
        assert "test_value" in result.value.values
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_query_value_validation_error(self, service):
        """Test creating a query value with validation error."""
        # Act - Missing required values/queries
        result = await service.create(
            id=TEST_QUERY_VALUE_ID,
            query_path_id=TEST_QUERY_PATH_ID,
            values=[]  # Empty values list
        )

        # Assert
        assert result.is_failure
        assert "Query value must have either values or queries" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_query_id_success(self, service, mock_repository):
        """Test finding query values by query ID successfully."""
        # Arrange
        query_id = TEST_QUERY_ID
        query_values = [
            QueryValue(
                id="value1",
                query_path_id=TEST_QUERY_PATH_ID
            ),
            QueryValue(
                id="value2",
                query_path_id="another_path"
            )
        ]
        # Add values to each query value to satisfy validation
        for qv in query_values:
            qv.add_value("test_value")
            
        mock_repository.find_by_query_id.return_value = query_values

        # Act
        result = await service.find_by_query_id(query_id)

        # Assert
        assert result.is_success
        assert len(result.value) == 2
        mock_repository.find_by_query_id.assert_called_once_with(query_id, None)


class TestQueryService:
    """Tests for the QueryService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=QueryRepository)

    @pytest.fixture
    def mock_value_repository(self):
        """Create a mock query value repository."""
        return AsyncMock(spec=QueryValueRepository)

    @pytest.fixture
    def service(self, mock_repository, mock_value_repository):
        """Create a QueryService instance."""
        service = QueryService(repository=mock_repository)
        service.value_repository = mock_value_repository
        return service

    @pytest.mark.asyncio
    async def test_create_query_success(self, service, mock_repository):
        """Test creating a query successfully."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_repository.save.return_value = Success(query)

        # Act
        result = await service.create(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_QUERY_ID
        assert result.value.name == TEST_QUERY_NAME
        assert result.value.query_meta_type_id == TEST_SOURCE_META_TYPE_ID
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_query_validation_error(self, service):
        """Test creating a query with validation error."""
        # Act - Missing required name
        result = await service.create(
            id=TEST_QUERY_ID,
            name="",  # Empty name
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )

        # Assert
        assert result.is_failure
        assert "Name cannot be empty" in str(result.error)

    @pytest.mark.asyncio
    async def test_find_by_name_success(self, service, mock_repository):
        """Test finding queries by name successfully."""
        # Arrange
        name = TEST_QUERY_NAME
        queries = [
            Query(
                id=TEST_QUERY_ID,
                name=name,
                query_meta_type_id=TEST_SOURCE_META_TYPE_ID
            )
        ]
        mock_repository.find_by_name.return_value = queries

        # Act
        result = await service.find_by_name(name)

        # Assert
        assert result.is_success
        assert len(result.value) == 1
        assert result.value[0].name == name
        mock_repository.find_by_name.assert_called_once_with(name, None)

    @pytest.mark.asyncio
    async def test_get_with_values_success(self, service, mock_repository):
        """Test getting a query with its values successfully."""
        # Arrange
        query_id = TEST_QUERY_ID
        query = Query(
            id=query_id,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_repository.find_with_values.return_value = query

        # Act
        result = await service.get_with_values(query_id)

        # Assert
        assert result.is_success
        assert result.value.id == query_id
        assert result.value.name == TEST_QUERY_NAME
        mock_repository.find_with_values.assert_called_once_with(query_id, None)

    @pytest.mark.asyncio
    async def test_get_with_values_not_found(self, service, mock_repository):
        """Test getting a query with its values when not found."""
        # Arrange
        query_id = "nonexistent"
        mock_repository.find_with_values.return_value = None

        # Act
        result = await service.get_with_values(query_id)

        # Assert
        assert result.is_failure
        assert f"Query {query_id} not found" in str(result.error)
        mock_repository.find_with_values.assert_called_once_with(query_id, None)

    @pytest.mark.asyncio
    async def test_create_with_values_success(self, service, mock_repository, mock_value_repository):
        """Test creating a query with values successfully."""
        # Arrange
        query = Query(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_repository.save.return_value = Success(query)
        
        # Data for query values
        query_values_data = [
            {
                "id": "value1",
                "query_path_id": TEST_QUERY_PATH_ID,
                "values": ["test_value"]
            }
        ]
        
        # Mock the save method for query values
        mock_value_repository.save.return_value = Success(
            QueryValue(
                id="value1",
                query_path_id=TEST_QUERY_PATH_ID
            )
        )

        # Act
        result = await service.create_with_values(
            id=TEST_QUERY_ID,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID,
            query_values=query_values_data
        )

        # Assert
        assert result.is_success
        assert result.value.id == TEST_QUERY_ID
        assert result.value.name == TEST_QUERY_NAME
        mock_repository.save.assert_called_once()
        mock_value_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_with_values_success(self, service, mock_repository, mock_value_repository):
        """Test deleting a query with its values successfully."""
        # Arrange
        query_id = TEST_QUERY_ID
        query = Query(
            id=query_id,
            name=TEST_QUERY_NAME,
            query_meta_type_id=TEST_SOURCE_META_TYPE_ID
        )
        mock_repository.get_by_id.return_value = Success(query)
        mock_repository.delete.return_value = Success(query)

        # Act
        result = await service.delete_with_values(query_id)

        # Assert
        assert result.is_success
        assert result.value.id == query_id
        mock_repository.get_by_id.assert_called_once_with(query_id, None)
        mock_value_repository.delete_for_query.assert_called_once_with(query_id, None)
        mock_repository.delete.assert_called_once()