"""
Tests for the modeler module analyzer.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from uno.devtools.modeler.analyzer import AnalyzeCodebase, ModelType


class TestAnalyzer:
    """Tests for the AnalyzeCodebase class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = AnalyzeCodebase(temp_dir)
            assert analyzer.project_path == Path(temp_dir)

    def test_initialization_invalid_path(self):
        """Test analyzer initialization with invalid path."""
        with pytest.raises(ValueError):
            AnalyzeCodebase("/path/that/does/not/exist")

    @patch("uno.devtools.modeler.analyzer.AnalyzeCodebase._analyze_entities")
    def test_analyze_entity_type(self, mock_analyze_entities):
        """Test analyzing with entity model type."""
        mock_analyze_entities.return_value = ([], [])

        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = AnalyzeCodebase(temp_dir)
            result = analyzer.analyze(ModelType.ENTITY)

            # Check that the right analysis method was called
            mock_analyze_entities.assert_called_once()

            # Check result structure
            assert "entities" in result
            assert "relationships" in result
            assert isinstance(result["entities"], list)
            assert isinstance(result["relationships"], list)

    @patch("uno.devtools.modeler.analyzer.AnalyzeCodebase._find_domain_dirs")
    @patch("uno.devtools.modeler.analyzer.AnalyzeCodebase._analyze_domain_dir")
    @patch("uno.devtools.modeler.analyzer.AnalyzeCodebase._extract_relationships")
    def test_analyze_entities(
        self, mock_extract_relationships, mock_analyze_domain, mock_find_domains
    ):
        """Test _analyze_entities method."""
        # Setup mocks
        mock_domain1 = MagicMock()
        mock_domain2 = MagicMock()
        mock_find_domains.return_value = [mock_domain1, mock_domain2]

        # Mock entity objects with id attributes
        mock_entity1 = MagicMock()
        mock_entity1.id = "entity1_id"
        mock_entity1.name = "Entity1"

        mock_entity2 = MagicMock()
        mock_entity2.id = "entity2_id"
        mock_entity2.name = "Entity2"

        # Mock domain analysis results
        mock_analyze_domain.return_value = ([mock_entity1], [])
        mock_extract_relationships.return_value = [MagicMock()]

        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = AnalyzeCodebase(temp_dir)
            entities, relationships = analyzer._analyze_entities()

            # Check method calls
            assert mock_find_domains.call_count == 1
            assert mock_analyze_domain.call_count == 2
            assert mock_extract_relationships.call_count == 2

            # Check results
            assert len(entities) == 2  # One entity per domain
            assert len(relationships) == 2  # One relationship per domain

    def test_extract_entity_from_file(self):
        """Test extracting entity from Python file."""
        # Create a temporary test file with entity class
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(
                """
from typing import Optional
from pydantic import BaseModel

class TestEntity(BaseModel):
                            
    __test__ = False  # Prevent pytest from collecting this class as a test
    id: str
    name: str
    description: Optional[str] = None
    active: bool = True
"""
            )
            temp_file_path = temp_file.name

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                analyzer = AnalyzeCodebase(temp_dir)
                entity = analyzer._extract_entity_from_file(Path(temp_file_path))

                # Check extracted entity
                assert entity is not None
                assert entity.name == "TestEntity"
                assert len(entity.fields) == 4

                # Check field names
                field_names = [field.name for field in entity.fields]
                assert "id" in field_names
                assert "name" in field_names
                assert "description" in field_names
                assert "active" in field_names

                # Check primary key
                id_field = next(field for field in entity.fields if field.name == "id")
                assert id_field.primaryKey is True
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    def test_extract_subscript_type(self):
        """Test extracting type from subscript annotation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = AnalyzeCodebase(temp_dir)

            # Create mock AST subscript nodes
            mock_list_str = MagicMock()
            mock_list_str.value = MagicMock()
            mock_list_str.value.id = "List"
            mock_list_str.slice = MagicMock()
            mock_list_str.slice.id = "str"

            result = analyzer._extract_subscript_type(mock_list_str)
            assert result == "List[str]"
