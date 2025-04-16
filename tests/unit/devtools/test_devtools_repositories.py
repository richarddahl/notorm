"""
Tests for the DevTools module domain repositories.

This module contains tests for the repository implementations in the DevTools module,
ensuring correct data access patterns for profiler sessions, templates, and documentation.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, UTC
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.devtools.entities import (
    ProfilerSessionId,
    CodegenTemplateId,
    DocumentationId,
    ProfilerType,
    CodegenType,
    ProfilerConfiguration,
    ProfileMetric,
    ProfilerSession,
    MemoryMetric,
    MemoryProfilerSession,
    CodegenTemplate,
    GeneratedCodeResult,
    DocumentationAsset
)
from uno.devtools.domain_repositories import (
    InMemoryProfilerSessionRepository,
    InMemoryMemoryProfilerSessionRepository,
    InMemoryCodegenTemplateRepository,
    InMemoryGeneratedCodeRepository,
    InMemoryDocumentationAssetRepository
)


class TestInMemoryProfilerSessionRepository:
    """Tests for the InMemoryProfilerSessionRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository for testing."""
        return InMemoryProfilerSessionRepository()
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample profiler session for testing."""
        session_id = ProfilerSessionId("test-session")
        config = ProfilerConfiguration(type=ProfilerType.FUNCTION)
        
        session = ProfilerSession(
            id=session_id,
            start_time=datetime.now(UTC),
            configuration=config
        )
        
        # Add a metric
        metric = ProfileMetric(
            name="test_func",
            calls=1,
            total_time=0.1,
            own_time=0.1,
            avg_time=0.1,
            max_time=0.1,
            min_time=0.1
        )
        session.add_metric(metric)
        
        return session
    
    def test_save(self, repository, sample_session):
        """Test saving a profiler session."""
        result = repository.save(sample_session)
        
        assert isinstance(result, Success)
        assert result.value == sample_session
        assert sample_session.id in repository.sessions
    
    def test_get_by_id(self, repository, sample_session):
        """Test getting a profiler session by ID."""
        # First save a session
        repository.save(sample_session)
        
        # Then retrieve it
        result = repository.get_by_id(sample_session.id)
        
        assert isinstance(result, Success)
        assert result.value == sample_session
    
    def test_get_by_id_not_found(self, repository):
        """Test getting a non-existent profiler session by ID."""
        result = repository.get_by_id(ProfilerSessionId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "SESSION_NOT_FOUND"
    
    def test_list(self, repository, sample_session):
        """Test listing all profiler sessions."""
        # First save a session
        repository.save(sample_session)
        
        # Then list all sessions
        result = repository.list()
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_session
    
    def test_delete(self, repository, sample_session):
        """Test deleting a profiler session."""
        # First save a session
        repository.save(sample_session)
        
        # Then delete it
        result = repository.delete(sample_session.id)
        
        assert isinstance(result, Success)
        assert result.value is True
        assert sample_session.id not in repository.sessions
    
    def test_delete_not_found(self, repository):
        """Test deleting a non-existent profiler session."""
        result = repository.delete(ProfilerSessionId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "SESSION_NOT_FOUND"


class TestInMemoryMemoryProfilerSessionRepository:
    """Tests for the InMemoryMemoryProfilerSessionRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository for testing."""
        return InMemoryMemoryProfilerSessionRepository()
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample memory profiler session for testing."""
        session_id = ProfilerSessionId("test-session")
        config = ProfilerConfiguration(type=ProfilerType.MEMORY)
        
        session = MemoryProfilerSession(
            id=session_id,
            start_time=datetime.now(UTC),
            configuration=config
        )
        
        # Add a metric
        metric = MemoryMetric(
            name="test_func",
            allocations=100,
            bytes_allocated=10240,
            peak_memory=20480
        )
        session.add_metric(metric)
        
        return session
    
    def test_save(self, repository, sample_session):
        """Test saving a memory profiler session."""
        result = repository.save(sample_session)
        
        assert isinstance(result, Success)
        assert result.value == sample_session
        assert sample_session.id in repository.sessions
    
    def test_get_by_id(self, repository, sample_session):
        """Test getting a memory profiler session by ID."""
        # First save a session
        repository.save(sample_session)
        
        # Then retrieve it
        result = repository.get_by_id(sample_session.id)
        
        assert isinstance(result, Success)
        assert result.value == sample_session
    
    def test_get_by_id_not_found(self, repository):
        """Test getting a non-existent memory profiler session by ID."""
        result = repository.get_by_id(ProfilerSessionId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "SESSION_NOT_FOUND"
    
    def test_list(self, repository, sample_session):
        """Test listing all memory profiler sessions."""
        # First save a session
        repository.save(sample_session)
        
        # Then list all sessions
        result = repository.list()
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_session
    
    def test_delete(self, repository, sample_session):
        """Test deleting a memory profiler session."""
        # First save a session
        repository.save(sample_session)
        
        # Then delete it
        result = repository.delete(sample_session.id)
        
        assert isinstance(result, Success)
        assert result.value is True
        assert sample_session.id not in repository.sessions
    
    def test_delete_not_found(self, repository):
        """Test deleting a non-existent memory profiler session."""
        result = repository.delete(ProfilerSessionId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "SESSION_NOT_FOUND"


class TestInMemoryCodegenTemplateRepository:
    """Tests for the InMemoryCodegenTemplateRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository for testing."""
        return InMemoryCodegenTemplateRepository()
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample code generation template for testing."""
        template_id = CodegenTemplateId("test-template")
        
        template = CodegenTemplate(
            id=template_id,
            name="Test Template",
            type=CodegenType.MODEL,
            template_path=Path("/templates/test.jinja2"),
            description="A test template"
        )
        
        return template
    
    def test_save(self, repository, sample_template):
        """Test saving a code generation template."""
        result = repository.save(sample_template)
        
        assert isinstance(result, Success)
        assert result.value == sample_template
        assert sample_template.id in repository.templates
    
    def test_get_by_id(self, repository, sample_template):
        """Test getting a template by ID."""
        # First save a template
        repository.save(sample_template)
        
        # Then retrieve it
        result = repository.get_by_id(sample_template.id)
        
        assert isinstance(result, Success)
        assert result.value == sample_template
    
    def test_get_by_id_not_found(self, repository):
        """Test getting a non-existent template by ID."""
        result = repository.get_by_id(CodegenTemplateId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "TEMPLATE_NOT_FOUND"
    
    def test_list_templates(self, repository, sample_template):
        """Test listing all templates."""
        # First save a template
        repository.save(sample_template)
        
        # Then list all templates
        result = repository.list_templates()
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_template
    
    def test_list_templates_by_type(self, repository, sample_template):
        """Test listing templates by type."""
        # First save a template
        repository.save(sample_template)
        
        # Also save a template of a different type
        other_template = CodegenTemplate(
            id=CodegenTemplateId("other-template"),
            name="Other Template",
            type=CodegenType.REPOSITORY,
            template_path=Path("/templates/other.jinja2")
        )
        repository.save(other_template)
        
        # Then list templates by type
        result = repository.list_templates_by_type(CodegenType.MODEL)
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_template
    
    def test_delete(self, repository, sample_template):
        """Test deleting a template."""
        # First save a template
        repository.save(sample_template)
        
        # Then delete it
        result = repository.delete(sample_template.id)
        
        assert isinstance(result, Success)
        assert result.value is True
        assert sample_template.id not in repository.templates
    
    def test_delete_not_found(self, repository):
        """Test deleting a non-existent template."""
        result = repository.delete(CodegenTemplateId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "TEMPLATE_NOT_FOUND"


class TestInMemoryGeneratedCodeRepository:
    """Tests for the InMemoryGeneratedCodeRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository for testing."""
        return InMemoryGeneratedCodeRepository()
    
    @pytest.fixture
    def sample_result(self):
        """Create a sample generated code result for testing."""
        template_id = CodegenTemplateId("test-template")
        
        result = GeneratedCodeResult(
            template_id=template_id,
            output_path=Path("/output/test.py"),
            generated_code="class Test:\n    pass\n",
            model_name="Test"
        )
        
        return result
    
    def test_save(self, repository, sample_result):
        """Test saving a generated code result."""
        result = repository.save(sample_result)
        
        assert isinstance(result, Success)
        assert result.value == sample_result
        assert len(repository.results) == 1
    
    def test_list(self, repository, sample_result):
        """Test listing all generated code results."""
        # First save a result
        repository.save(sample_result)
        
        # Then list all results
        result = repository.list()
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_result
    
    def test_list_by_model_name(self, repository, sample_result):
        """Test listing generated code results by model name."""
        # First save a result
        repository.save(sample_result)
        
        # Also save a result for a different model
        other_result = GeneratedCodeResult(
            template_id=CodegenTemplateId("other-template"),
            output_path=Path("/output/other.py"),
            generated_code="class Other:\n    pass\n",
            model_name="Other"
        )
        repository.save(other_result)
        
        # Then list results by model name
        result = repository.list_by_model_name("Test")
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_result
    
    def test_list_by_template_id(self, repository, sample_result):
        """Test listing generated code results by template ID."""
        # First save a result
        repository.save(sample_result)
        
        # Then list results by template ID
        result = repository.list_by_template_id(sample_result.template_id)
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_result


class TestInMemoryDocumentationAssetRepository:
    """Tests for the InMemoryDocumentationAssetRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository for testing."""
        return InMemoryDocumentationAssetRepository()
    
    @pytest.fixture
    def sample_asset(self):
        """Create a sample documentation asset for testing."""
        doc_id = DocumentationId("test-doc")
        
        asset = DocumentationAsset(
            id=doc_id,
            title="Test Documentation",
            content="# Test\n\nThis is a test documentation asset.",
            path=Path("/docs/test.md"),
            format="markdown"
        )
        
        return asset
    
    def test_save(self, repository, sample_asset):
        """Test saving a documentation asset."""
        result = repository.save(sample_asset)
        
        assert isinstance(result, Success)
        assert result.value == sample_asset
        assert sample_asset.id in repository.assets
    
    def test_get_by_id(self, repository, sample_asset):
        """Test getting a documentation asset by ID."""
        # First save an asset
        repository.save(sample_asset)
        
        # Then retrieve it
        result = repository.get_by_id(sample_asset.id)
        
        assert isinstance(result, Success)
        assert result.value == sample_asset
    
    def test_get_by_id_not_found(self, repository):
        """Test getting a non-existent documentation asset by ID."""
        result = repository.get_by_id(DocumentationId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "DOCUMENTATION_ASSET_NOT_FOUND"
    
    def test_list(self, repository, sample_asset):
        """Test listing all documentation assets."""
        # First save an asset
        repository.save(sample_asset)
        
        # Then list all assets
        result = repository.list()
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_asset
    
    def test_search_by_title(self, repository, sample_asset):
        """Test searching documentation assets by title."""
        # First save an asset
        repository.save(sample_asset)
        
        # Also save an asset with a different title
        other_asset = DocumentationAsset(
            id=DocumentationId("other-doc"),
            title="Other Documentation",
            content="# Other\n\nThis is another documentation asset.",
            path=Path("/docs/other.md"),
            format="markdown"
        )
        repository.save(other_asset)
        
        # Then search for assets by title
        result = repository.search_by_title("Test")
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == sample_asset
    
    def test_delete(self, repository, sample_asset):
        """Test deleting a documentation asset."""
        # First save an asset
        repository.save(sample_asset)
        
        # Then delete it
        result = repository.delete(sample_asset.id)
        
        assert isinstance(result, Success)
        assert result.value is True
        assert sample_asset.id not in repository.assets
    
    def test_delete_not_found(self, repository):
        """Test deleting a non-existent documentation asset."""
        result = repository.delete(DocumentationId("nonexistent"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "DOCUMENTATION_ASSET_NOT_FOUND"