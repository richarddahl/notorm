"""
Tests for the developer documentation generator.

This module contains unit tests for the Uno developer documentation generator.
"""

import os
import tempfile
from pathlib import Path
import pytest
from typing import Dict, List, Any, Optional, Union

from uno.core.docs.generator import DocGeneratorConfig, DocFormat
from uno.devtools.docs.generator import DevToolsDocumentationGenerator, generate_dev_docs
from uno.devtools.docs.extractors import ExampleExtractor, TestExtractor, BenchmarkExtractor


class TestDevToolsDocumentationGenerator:
    """Tests for DevToolsDocumentationGenerator."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = DevToolsDocumentationGenerator()
        
        assert hasattr(generator, "config")
        assert hasattr(generator, "logger")
        assert hasattr(generator, "discovery")
        assert hasattr(generator, "example_extractor")
        assert hasattr(generator, "test_extractor")
        assert hasattr(generator, "benchmark_extractor")
        assert hasattr(generator, "playground_renderer")
        assert hasattr(generator, "tutorial_renderer")
        assert hasattr(generator, "dashboard_renderer")
    
    def test_default_config(self):
        """Test default configuration."""
        generator = DevToolsDocumentationGenerator()
        config = generator.config
        
        assert config.title == "Uno Developer Documentation"
        assert "developer" in config.description.lower()
        assert config.output_dir == "docs/dev"
        assert config.include_internal is True
        assert config.include_examples is True
        assert config.example_depth == 3
        assert config.include_deprecated is True
        assert config.include_beta is True
        assert config.include_alpha is True
        assert config.include_experimental is True
        assert "uno" in config.modules_to_document
    
    def test_custom_config(self):
        """Test with custom configuration."""
        custom_config = DocGeneratorConfig(
            title="Custom Developer Docs",
            description="Custom Description",
            output_dir="custom/dev/docs"
        )
        
        generator = DevToolsDocumentationGenerator(config=custom_config)
        config = generator.config
        
        assert config.title == "Custom Developer Docs"
        assert config.description == "Custom Description"
        assert config.output_dir == "custom/dev/docs"
    
    def test_setup_discovery(self):
        """Test discovery setup."""
        generator = DevToolsDocumentationGenerator()
        discovery = generator.discovery
        
        # Check that standard providers are registered
        assert "model" in discovery.providers
        assert "endpoint" in discovery.providers
        assert "schema" in discovery.providers
        
        # Check that additional providers are registered
        assert "example" in discovery.providers
        assert "test" in discovery.providers
        assert "benchmark" in discovery.providers


class TestGenerateDevDocs:
    """Tests for generate_dev_docs function."""
    
    def test_generate_dev_docs(self):
        """Test generating developer documentation."""
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure the generator
            config = DocGeneratorConfig(
                title="Test Developer Documentation",
                description="Test Description",
                version="1.0.0",
                formats=[DocFormat.MARKDOWN],
                output_dir=temp_dir,
                modules_to_document=[]
            )
            
            # Generate documentation (without real components)
            docs = generate_dev_docs(config)
            
            # Check the result
            assert isinstance(docs, dict)
            assert DocFormat.MARKDOWN.name in docs
            assert isinstance(docs[DocFormat.MARKDOWN.name], dict)


class TestDevExtractors:
    """Tests for specialized developer documentation extractors."""
    
    def test_example_extractor(self):
        """Test example extractor."""
        extractor = ExampleExtractor()
        
        # Check that it has an extract method
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)
    
    def test_test_extractor(self):
        """Test test extractor."""
        extractor = TestExtractor()
        
        # Check that it has an extract method
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)
    
    def test_benchmark_extractor(self):
        """Test benchmark extractor."""
        extractor = BenchmarkExtractor()
        
        # Check that it has an extract method
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)
        

class TestDevToolsIntegration:
    """Integration tests for the developer documentation generator."""
    
    def test_full_generation_process(self):
        """Test the full documentation generation process."""
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure the generator
            config = DocGeneratorConfig(
                title="Integration Test",
                description="Integration Test Description",
                version="1.0.0",
                formats=[DocFormat.MARKDOWN],
                output_dir=temp_dir,
                modules_to_document=[]
            )
            
            # Create generator
            generator = DevToolsDocumentationGenerator(config)
            
            # Generate documentation
            docs = generator.generate()
            
            # Check results
            assert isinstance(docs, dict)
            assert DocFormat.MARKDOWN.name in docs
            
            # Check that files were created
            output_dir = Path(temp_dir)
            assert (output_dir / DocFormat.MARKDOWN.name.lower()).exists()