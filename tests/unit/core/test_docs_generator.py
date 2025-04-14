"""
Tests for the documentation generator.

This module contains unit tests for the Uno documentation generator.
"""

import os
import tempfile
from pathlib import Path
import pytest
from typing import Dict, List, Any, Optional, Union

from uno.core.docs.generator import DocGeneratorConfig, DocFormat, DocGenerator, generate_docs
from uno.core.docs.extractors import ModelExtractor, EndpointExtractor, SchemaExtractor
from uno.core.docs.renderers import MarkdownRenderer, OpenApiRenderer
from uno.core.docs.schema import DocSchema


class TestDocGeneratorConfig:
    """Tests for DocGeneratorConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = DocGeneratorConfig()
        
        assert config.title == "API Documentation"
        assert config.description == "Generated API documentation"
        assert config.version == "1.0.0"
        assert DocFormat.MARKDOWN in config.formats
        assert DocFormat.OPENAPI in config.formats
        assert config.output_dir == "docs/api"
        assert config.include_source_links is True
        assert config.include_examples is True
        assert config.example_depth == 2
        assert config.include_internal is False
        assert config.include_deprecated is True
        assert config.include_beta is True
        assert config.include_alpha is True
        assert config.include_experimental is True
        assert config.modules_to_document == []
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = DocGeneratorConfig(
            title="Custom Title",
            description="Custom Description",
            version="2.0.0",
            formats=[DocFormat.MARKDOWN],
            output_dir="custom/output",
            include_source_links=False,
            include_examples=False,
            example_depth=3,
            include_internal=True,
            include_deprecated=False,
            include_beta=False,
            include_alpha=False,
            include_experimental=False,
            modules_to_document=["module1", "module2"],
            url_base="https://example.com",
            logo_url="https://example.com/logo.png"
        )
        
        assert config.title == "Custom Title"
        assert config.description == "Custom Description"
        assert config.version == "2.0.0"
        assert config.formats == [DocFormat.MARKDOWN]
        assert config.output_dir == "custom/output"
        assert config.include_source_links is False
        assert config.include_examples is False
        assert config.example_depth == 3
        assert config.include_internal is True
        assert config.include_deprecated is False
        assert config.include_beta is False
        assert config.include_alpha is False
        assert config.include_experimental is False
        assert config.modules_to_document == ["module1", "module2"]
        assert config.url_base == "https://example.com"
        assert config.logo_url == "https://example.com/logo.png"


class TestDocGenerator:
    """Tests for DocGenerator."""
    
    def test_initialization(self):
        """Test generator initialization."""
        config = DocGeneratorConfig()
        generator = DocGenerator(config)
        
        assert generator.config == config
        assert hasattr(generator, "logger")
        assert hasattr(generator, "discovery")
        assert hasattr(generator, "extractors")
        assert hasattr(generator, "renderers")
    
    def test_register_extractor(self):
        """Test registering an extractor."""
        config = DocGeneratorConfig()
        generator = DocGenerator(config)
        
        # Create a mock extractor
        class MockExtractor:
            def extract(self, components, config):
                return []
        
        # Register the extractor
        mock_extractor = MockExtractor()
        generator.register_extractor("mock", mock_extractor)
        
        # Check if extractor was registered
        assert "mock" in generator.extractors
        assert generator.extractors["mock"] == mock_extractor
    
    def test_register_renderer(self):
        """Test registering a renderer."""
        config = DocGeneratorConfig()
        generator = DocGenerator(config)
        
        # Create a mock renderer
        class MockRenderer:
            def render(self, schema, config):
                return {}
        
        # Register the renderer
        mock_renderer = MockRenderer()
        generator.register_renderer(DocFormat.MARKDOWN, mock_renderer)
        
        # Check if renderer was registered
        assert DocFormat.MARKDOWN in generator.renderers
        assert generator.renderers[DocFormat.MARKDOWN] == mock_renderer


class TestGenerateDocs:
    """Tests for generate_docs function."""
    
    def test_generate_docs(self):
        """Test generating documentation."""
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure the generator
            config = DocGeneratorConfig(
                title="Test Documentation",
                description="Test Description",
                version="1.0.0",
                formats=[DocFormat.MARKDOWN],
                output_dir=temp_dir,
                modules_to_document=[]
            )
            
            # Generate documentation (without real components)
            docs = generate_docs(config)
            
            # Check the result
            assert isinstance(docs, dict)
            assert DocFormat.MARKDOWN.name in docs
            assert isinstance(docs[DocFormat.MARKDOWN.name], dict)


class TestDocSchema:
    """Tests for DocSchema."""
    
    def test_schema_creation(self):
        """Test creating a documentation schema."""
        schema = DocSchema(
            title="Test Schema",
            description="Test Description",
            version="1.0.0"
        )
        
        assert schema.title == "Test Schema"
        assert schema.description == "Test Description"
        assert schema.version == "1.0.0"
        assert schema.endpoints == []
        assert schema.models == []
        assert schema.tags == []
        assert schema.security_schemes == []


class TestExtractors:
    """Tests for documentation extractors."""
    
    def test_model_extractor(self):
        """Test model extractor."""
        extractor = ModelExtractor()
        
        # Check that it has an extract method
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)
    
    def test_endpoint_extractor(self):
        """Test endpoint extractor."""
        extractor = EndpointExtractor()
        
        # Check that it has an extract method
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)
    
    def test_schema_extractor(self):
        """Test schema extractor."""
        extractor = SchemaExtractor()
        
        # Check that it has an extract method
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)


class TestRenderers:
    """Tests for documentation renderers."""
    
    def test_markdown_renderer(self):
        """Test Markdown renderer."""
        renderer = MarkdownRenderer()
        
        # Check that it has a render method
        assert hasattr(renderer, "render")
        assert callable(renderer.render)
    
    def test_openapi_renderer(self):
        """Test OpenAPI renderer."""
        renderer = OpenApiRenderer()
        
        # Check that it has a render method
        assert hasattr(renderer, "render")
        assert callable(renderer.render)


class TestIntegration:
    """Integration tests for the documentation generator."""
    
    def test_full_generation_process(self):
        """Test the full documentation generation process."""
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure the generator
            config = DocGeneratorConfig(
                title="Integration Test",
                description="Integration Test Description",
                version="1.0.0",
                formats=[DocFormat.MARKDOWN, DocFormat.OPENAPI],
                output_dir=temp_dir,
                modules_to_document=[]
            )
            
            # Create generator
            generator = DocGenerator(config)
            
            # Register extractors and renderers
            generator.register_extractor("model", ModelExtractor())
            generator.register_extractor("endpoint", EndpointExtractor())
            generator.register_extractor("schema", SchemaExtractor())
            
            generator.register_renderer(DocFormat.MARKDOWN, MarkdownRenderer())
            generator.register_renderer(DocFormat.OPENAPI, OpenApiRenderer())
            
            # Generate documentation
            docs = generator.generate()
            
            # Check results
            assert isinstance(docs, dict)
            assert DocFormat.MARKDOWN.name in docs
            assert DocFormat.OPENAPI.name in docs
            
            # Check that files were created
            output_dir = Path(temp_dir)
            assert (output_dir / DocFormat.MARKDOWN.name.lower()).exists()
            assert (output_dir / DocFormat.OPENAPI.name.lower()).exists()