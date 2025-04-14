"""
Tests for the modeler module generator.
"""

import pytest
from unittest.mock import patch, MagicMock

from uno.devtools.modeler.generator import CodeGenerator
from uno.devtools.modeler.analyzer import Entity, EntityField

class TestCodeGenerator:
    """Tests for the CodeGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a CodeGenerator instance."""
        return CodeGenerator("TestProject")
    
    @patch('uno.devtools.modeler.generator.Environment')
    def test_initialization(self, mock_env):
        """Test generator initialization."""
        # Setup mock
        mock_env_instance = MagicMock()
        mock_env.return_value = mock_env_instance
        
        # Create generator
        generator = CodeGenerator("TestProject")
        
        # Check initialization
        assert generator.project_name == "TestProject"
        assert mock_env.called
        
        # Check filters
        assert mock_env_instance.filters['snake_case'] == generator._to_snake_case
        assert mock_env_instance.filters['camel_case'] == generator._to_camel_case
        assert mock_env_instance.filters['pascal_case'] == generator._to_pascal_case
    
    @patch('uno.devtools.modeler.generator.Environment')
    def test_generate(self, mock_env, generator):
        """Test code generation with entities and relationships."""
        # Setup mock template
        mock_template = MagicMock()
        mock_template.render.return_value = "Generated code"
        
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance
        
        # Create test entities
        entity1 = MagicMock()
        entity1.id = "entity1_id"
        entity1.name = "User"
        
        entity2 = MagicMock()
        entity2.id = "entity2_id"
        entity2.name = "Product"
        
        # Create test relationship
        relationship = MagicMock()
        relationship.source = "entity1_id"
        relationship.target = "entity2_id"
        relationship.type = "one-to-many"
        
        # Generate code
        generator = CodeGenerator("TestProject")
        result = generator.generate([entity1, entity2], [relationship])
        
        # Check result structure
        assert "entities" in result
        assert "repositories" in result
        assert "services" in result
        
        # Check entity code generation
        assert "User" in result["entities"]
        assert "Product" in result["entities"]
        
        # Check template calls
        assert mock_env_instance.get_template.call_count == 6  # 2 entities x 3 templates
    
    def test_find_entity_relationships(self, generator):
        """Test finding relationships for an entity."""
        # Create test entities
        entity1 = MagicMock()
        entity1.id = "entity1_id"
        entity1.name = "User"
        
        entity2 = MagicMock()
        entity2.id = "entity2_id"
        entity2.name = "Product"
        
        # Create entity map
        entity_map = {
            "entity1_id": entity1,
            "entity2_id": entity2
        }
        
        # Create test relationships
        relationships = [
            # User has many Products
            MagicMock(source="entity1_id", target="entity2_id", type="one-to-many"),
            # Product belongs to User
            MagicMock(source="entity2_id", target="entity1_id", type="many-to-one")
        ]
        
        # Find relationships for User
        user_relationships = generator._find_entity_relationships(entity1, relationships, entity_map)
        
        # Check results
        assert len(user_relationships) == 2
        
        # Check first relationship (User has many Products)
        assert user_relationships[0]["entity_id"] == "entity1_id"
        assert user_relationships[0]["related_id"] == "entity2_id"
        assert user_relationships[0]["related_name"] == "Product"
        assert user_relationships[0]["is_source"] is True
        assert user_relationships[0]["is_target"] is False
        assert user_relationships[0]["is_many"] is True
        
        # Check second relationship (User is referenced by Product)
        assert user_relationships[1]["entity_id"] == "entity1_id"
        assert user_relationships[1]["related_id"] == "entity2_id"
        assert user_relationships[1]["related_name"] == "Product"
        assert user_relationships[1]["is_source"] is False
        assert user_relationships[1]["is_target"] is True
        assert user_relationships[1]["is_many"] is False
    
    def test_string_case_conversions(self, generator):
        """Test string case conversion methods."""
        # Test snake_case
        assert generator._to_snake_case("HelloWorld") == "hello_world"
        assert generator._to_snake_case("helloWorld") == "hello_world"
        assert generator._to_snake_case("hello_world") == "hello_world"
        
        # Test camel_case
        assert generator._to_camel_case("hello_world") == "helloWorld"
        assert generator._to_camel_case("HelloWorld") == "HelloWorld"
        assert generator._to_camel_case("hello_world_example") == "helloWorldExample"
        
        # Test pascal_case
        assert generator._to_pascal_case("hello_world") == "HelloWorld"
        assert generator._to_pascal_case("helloWorld") == "HelloWorld"
        assert generator._to_pascal_case("hello_world_example") == "HelloWorldExample"