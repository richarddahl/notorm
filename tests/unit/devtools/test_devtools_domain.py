"""
Tests for the DevTools module domain entities.

This module contains tests for all domain entities, value objects, and enums in the DevTools module,
ensuring they meet the business requirements and behave as expected.
"""

import pytest
import uuid
from datetime import datetime, timedelta, UTC
from pathlib import Path
import io
import sys
from typing import Dict, List, Any, Optional

from uno.devtools.entities import (
    ToolId,
    ProfilerSessionId,
    CodegenTemplateId,
    DocumentationId,
    DebugLevel,
    ProfilerType,
    CodegenType,
    DebugConfiguration,
    ProfilerConfiguration,
    ProfileMetric,
    ProfilerSession,
    MemoryMetric,
    MemoryProfilerSession,
    CodegenTemplate,
    GeneratedCodeResult,
    DocumentationAsset,
    DiagramSpecification
)


class TestValueObjects:
    """Tests for value objects in the DevTools domain."""
    
    def test_tool_id(self):
        """Test the ToolId value object."""
        id_value = "test-tool-id"
        tool_id = ToolId(id_value)
        
        assert tool_id == id_value
        
        # Test validation
        with pytest.raises(ValueError):
            ToolId("")
    
    def test_profiler_session_id(self):
        """Test the ProfilerSessionId value object."""
        id_value = str(uuid.uuid4())
        session_id = ProfilerSessionId(id_value)
        
        assert session_id == id_value
        
        # Test validation
        with pytest.raises(ValueError):
            ProfilerSessionId("")
        
        # Test generation
        generated_id = ProfilerSessionId.generate()
        assert isinstance(generated_id, ProfilerSessionId)
        assert len(str(generated_id)) > 0
    
    def test_codegen_template_id(self):
        """Test the CodegenTemplateId value object."""
        id_value = "template-id"
        template_id = CodegenTemplateId(id_value)
        
        assert template_id == id_value
        
        # Test validation
        with pytest.raises(ValueError):
            CodegenTemplateId("")
    
    def test_documentation_id(self):
        """Test the DocumentationId value object."""
        id_value = "doc-id"
        doc_id = DocumentationId(id_value)
        
        assert doc_id == id_value
        
        # Test validation
        with pytest.raises(ValueError):
            DocumentationId("")


class TestEnums:
    """Tests for enums in the DevTools domain."""
    
    def test_debug_level(self):
        """Test the DebugLevel enum."""
        # Verify expected members and order
        assert list(DebugLevel) == [
            DebugLevel.ERROR,
            DebugLevel.WARNING,
            DebugLevel.INFO,
            DebugLevel.DEBUG,
            DebugLevel.TRACE
        ]
        
        # Verify increasing values
        assert DebugLevel.ERROR.value < DebugLevel.WARNING.value
        assert DebugLevel.WARNING.value < DebugLevel.INFO.value
        assert DebugLevel.INFO.value < DebugLevel.DEBUG.value
        assert DebugLevel.DEBUG.value < DebugLevel.TRACE.value
    
    def test_profiler_type(self):
        """Test the ProfilerType enum."""
        # Verify expected members
        assert set(ProfilerType) == {
            ProfilerType.FUNCTION,
            ProfilerType.MEMORY,
            ProfilerType.SQL,
            ProfilerType.API,
            ProfilerType.FULL
        }
    
    def test_codegen_type(self):
        """Test the CodegenType enum."""
        # Verify expected members
        assert set(CodegenType) == {
            CodegenType.MODEL,
            CodegenType.REPOSITORY,
            CodegenType.SERVICE,
            CodegenType.API,
            CodegenType.CRUD,
            CodegenType.PROJECT,
            CodegenType.MODULE
        }


class TestDebugConfiguration:
    """Tests for the DebugConfiguration entity."""
    
    def test_debug_configuration_default(self):
        """Test creating a DebugConfiguration with default values."""
        config = DebugConfiguration()
        
        assert config.level == DebugLevel.INFO
        assert config.trace_sql is False
        assert config.trace_repository is False
        assert config.enhance_errors is True
        assert config.log_file is None
    
    def test_debug_configuration_custom(self):
        """Test creating a DebugConfiguration with custom values."""
        log_file = Path("/tmp/debug.log")
        config = DebugConfiguration(
            level=DebugLevel.DEBUG,
            trace_sql=True,
            trace_repository=True,
            enhance_errors=False,
            log_file=log_file
        )
        
        assert config.level == DebugLevel.DEBUG
        assert config.trace_sql is True
        assert config.trace_repository is True
        assert config.enhance_errors is False
        assert config.log_file == log_file
    
    def test_with_level(self):
        """Test updating the debug level."""
        config = DebugConfiguration()
        new_config = config.with_level(DebugLevel.TRACE)
        
        # Original config should be unchanged (immutability)
        assert config.level == DebugLevel.INFO
        
        # New config should have updated level
        assert new_config.level == DebugLevel.TRACE
        
        # Other fields should remain the same
        assert new_config.trace_sql == config.trace_sql
        assert new_config.trace_repository == config.trace_repository
        assert new_config.enhance_errors == config.enhance_errors
        assert new_config.log_file == config.log_file
    
    def test_with_sql_tracing(self):
        """Test updating the SQL tracing flag."""
        config = DebugConfiguration(trace_sql=False)
        new_config = config.with_sql_tracing(True)
        
        # Original config should be unchanged (immutability)
        assert config.trace_sql is False
        
        # New config should have updated trace_sql
        assert new_config.trace_sql is True
        
        # Other fields should remain the same
        assert new_config.level == config.level
        assert new_config.trace_repository == config.trace_repository
        assert new_config.enhance_errors == config.enhance_errors
        assert new_config.log_file == config.log_file


class TestProfilerConfiguration:
    """Tests for the ProfilerConfiguration entity."""
    
    def test_profiler_configuration_default(self):
        """Test creating a ProfilerConfiguration with default values."""
        config = ProfilerConfiguration()
        
        assert config.type == ProfilerType.FUNCTION
        assert config.sample_rate == 100
        assert config.output_format == "html"
        assert config.output_path is None
        assert config.include_modules == []
        assert config.exclude_modules == []
    
    def test_profiler_configuration_custom(self):
        """Test creating a ProfilerConfiguration with custom values."""
        output_path = Path("/tmp/profile.html")
        config = ProfilerConfiguration(
            type=ProfilerType.MEMORY,
            sample_rate=50,
            output_format="json",
            output_path=output_path,
            include_modules=["uno.core", "uno.database"],
            exclude_modules=["uno.tests"]
        )
        
        assert config.type == ProfilerType.MEMORY
        assert config.sample_rate == 50
        assert config.output_format == "json"
        assert config.output_path == output_path
        assert config.include_modules == ["uno.core", "uno.database"]
        assert config.exclude_modules == ["uno.tests"]
    
    def test_with_type(self):
        """Test updating the profiler type."""
        config = ProfilerConfiguration()
        new_config = config.with_type(ProfilerType.SQL)
        
        # Original config should be unchanged
        assert config.type == ProfilerType.FUNCTION
        
        # New config should have updated type
        assert new_config.type == ProfilerType.SQL
        
        # Other fields should remain the same
        assert new_config.sample_rate == config.sample_rate
        assert new_config.output_format == config.output_format
        assert new_config.output_path == config.output_path
        assert new_config.include_modules == config.include_modules
        assert new_config.exclude_modules == config.exclude_modules


class TestProfileMetric:
    """Tests for the ProfileMetric entity."""
    
    def test_profile_metric_creation(self):
        """Test creating a ProfileMetric entity."""
        metric = ProfileMetric(
            name="test_function",
            calls=10,
            total_time=0.5,
            own_time=0.4,
            avg_time=0.05,
            max_time=0.1,
            min_time=0.01,
            parent="parent_function",
            children=["child_function1", "child_function2"]
        )
        
        assert metric.name == "test_function"
        assert metric.calls == 10
        assert metric.total_time == 0.5
        assert metric.own_time == 0.4
        assert metric.avg_time == 0.05
        assert metric.max_time == 0.1
        assert metric.min_time == 0.01
        assert metric.parent == "parent_function"
        assert metric.children == ["child_function1", "child_function2"]
    
    def test_is_hotspot(self):
        """Test the is_hotspot property."""
        # Hotspot criteria: own_time > 0.1 and own_time > 0.1
        
        # Should be a hotspot
        hotspot_metric = ProfileMetric(
            name="slow_function",
            calls=1,
            total_time=1.0,
            own_time=0.9,  # Significant portion of own time
            avg_time=0.9,
            max_time=0.9,
            min_time=0.9
        )
        assert hotspot_metric.is_hotspot is True
        
        # Should not be a hotspot (low own_time)
        non_hotspot_metric = ProfileMetric(
            name="fast_function",
            calls=1,
            total_time=1.0,
            own_time=0.09,  # Low own time
            avg_time=0.09,
            max_time=0.09,
            min_time=0.09
        )
        assert non_hotspot_metric.is_hotspot is False
    
    def test_to_dict(self):
        """Test converting a ProfileMetric to a dictionary."""
        metric = ProfileMetric(
            name="test_function",
            calls=10,
            total_time=0.5,
            own_time=0.4,
            avg_time=0.05,
            max_time=0.1,
            min_time=0.01
        )
        
        result = metric.to_dict()
        
        assert result["name"] == "test_function"
        assert result["calls"] == 10
        assert result["total_time"] == 0.5
        assert result["own_time"] == 0.4
        assert result["avg_time"] == 0.05
        assert result["max_time"] == 0.1
        assert result["min_time"] == 0.01
        assert result["parent"] is None
        assert result["children"] == []
        assert "is_hotspot" in result


class TestProfilerSession:
    """Tests for the ProfilerSession entity."""
    
    def test_create_profiler_session(self):
        """Test creating a ProfilerSession using the factory method."""
        config = ProfilerConfiguration()
        session = ProfilerSession.create(config)
        
        assert isinstance(session.id, ProfilerSessionId)
        assert isinstance(session.start_time, datetime)
        assert session.end_time is None
        assert session.configuration == config
        assert session.metrics == []
    
    def test_add_metric(self):
        """Test adding a metric to a profiler session."""
        session = ProfilerSession(
            id=ProfilerSessionId("test-session"),
            start_time=datetime.now(UTC)
        )
        
        metric = ProfileMetric(
            name="test_function",
            calls=1,
            total_time=0.1,
            own_time=0.1,
            avg_time=0.1,
            max_time=0.1,
            min_time=0.1
        )
        
        session.add_metric(metric)
        
        assert len(session.metrics) == 1
        assert session.metrics[0] == metric
    
    def test_complete(self):
        """Test completing a profiler session."""
        session = ProfilerSession(
            id=ProfilerSessionId("test-session"),
            start_time=datetime.now(UTC) - timedelta(seconds=5)
        )
        
        assert session.end_time is None
        
        session.complete()
        
        assert isinstance(session.end_time, datetime)
    
    def test_duration(self):
        """Test calculating the duration of a profiler session."""
        start_time = datetime.now(UTC) - timedelta(seconds=5)
        end_time = datetime.now(UTC)
        
        # Incomplete session
        incomplete_session = ProfilerSession(
            id=ProfilerSessionId("incomplete"),
            start_time=start_time
        )
        assert incomplete_session.duration is None
        
        # Complete session
        complete_session = ProfilerSession(
            id=ProfilerSessionId("complete"),
            start_time=start_time,
            end_time=end_time
        )
        assert complete_session.duration is not None
        assert 4.9 <= complete_session.duration <= 5.1  # Allow for small time differences
    
    def test_find_hotspots(self):
        """Test finding hotspots in a profiler session."""
        session = ProfilerSession(
            id=ProfilerSessionId("test-session"),
            start_time=datetime.now(UTC)
        )
        
        # Add a hotspot metric
        hotspot = ProfileMetric(
            name="slow_function",
            calls=1,
            total_time=1.0,
            own_time=0.9,
            avg_time=0.9,
            max_time=0.9,
            min_time=0.9
        )
        session.add_metric(hotspot)
        
        # Add a non-hotspot metric
        non_hotspot = ProfileMetric(
            name="fast_function",
            calls=1,
            total_time=1.0,
            own_time=0.09,
            avg_time=0.09,
            max_time=0.09,
            min_time=0.09
        )
        session.add_metric(non_hotspot)
        
        hotspots = session.find_hotspots()
        
        assert len(hotspots) == 1
        assert hotspots[0] == hotspot


class TestMemoryMetric:
    """Tests for the MemoryMetric entity."""
    
    def test_memory_metric_creation(self):
        """Test creating a MemoryMetric entity."""
        metric = MemoryMetric(
            name="test_function",
            allocations=100,
            bytes_allocated=10240,
            peak_memory=12288,
            leak_count=2
        )
        
        assert metric.name == "test_function"
        assert metric.allocations == 100
        assert metric.bytes_allocated == 10240
        assert metric.peak_memory == 12288
        assert metric.leak_count == 2
    
    def test_to_dict(self):
        """Test converting a MemoryMetric to a dictionary."""
        metric = MemoryMetric(
            name="test_function",
            allocations=100,
            bytes_allocated=10240,
            peak_memory=12288,
            leak_count=2
        )
        
        result = metric.to_dict()
        
        assert result["name"] == "test_function"
        assert result["allocations"] == 100
        assert result["bytes_allocated"] == 10240
        assert result["peak_memory"] == 12288
        assert result["leak_count"] == 2


class TestMemoryProfilerSession:
    """Tests for the MemoryProfilerSession entity."""
    
    def test_create_memory_profiler_session(self):
        """Test creating a MemoryProfilerSession using the factory method."""
        config = ProfilerConfiguration(type=ProfilerType.MEMORY)
        session = MemoryProfilerSession.create(config)
        
        assert isinstance(session.id, ProfilerSessionId)
        assert isinstance(session.start_time, datetime)
        assert session.end_time is None
        assert session.configuration == config
        assert session.metrics == []
    
    def test_add_metric(self):
        """Test adding a metric to a memory profiler session."""
        session = MemoryProfilerSession(
            id=ProfilerSessionId("test-session"),
            start_time=datetime.now(UTC)
        )
        
        metric = MemoryMetric(
            name="test_function",
            allocations=100,
            bytes_allocated=10240,
            peak_memory=12288
        )
        
        session.add_metric(metric)
        
        assert len(session.metrics) == 1
        assert session.metrics[0] == metric
    
    def test_complete(self):
        """Test completing a memory profiler session."""
        session = MemoryProfilerSession(
            id=ProfilerSessionId("test-session"),
            start_time=datetime.now(UTC) - timedelta(seconds=5)
        )
        
        assert session.end_time is None
        
        session.complete()
        
        assert isinstance(session.end_time, datetime)


class TestCodegenTemplate:
    """Tests for the CodegenTemplate entity."""
    
    def test_codegen_template_creation(self):
        """Test creating a CodegenTemplate entity."""
        template_id = CodegenTemplateId("template-id")
        template_path = Path("/templates/model.jinja2")
        
        template = CodegenTemplate(
            id=template_id,
            name="Model Template",
            type=CodegenType.MODEL,
            template_path=template_path,
            description="A template for generating model classes"
        )
        
        assert template.id == template_id
        assert template.name == "Model Template"
        assert template.type == CodegenType.MODEL
        assert template.template_path == template_path
        assert template.description == "A template for generating model classes"
    
    def test_to_dict(self):
        """Test converting a CodegenTemplate to a dictionary."""
        template_id = CodegenTemplateId("template-id")
        template_path = Path("/templates/model.jinja2")
        
        template = CodegenTemplate(
            id=template_id,
            name="Model Template",
            type=CodegenType.MODEL,
            template_path=template_path,
            description="A template for generating model classes"
        )
        
        result = template.to_dict()
        
        assert result["id"] == "template-id"
        assert result["name"] == "Model Template"
        assert result["type"] == "MODEL"
        assert result["template_path"] == "/templates/model.jinja2"
        assert result["description"] == "A template for generating model classes"


class TestGeneratedCodeResult:
    """Tests for the GeneratedCodeResult entity."""
    
    def test_generated_code_result_creation(self):
        """Test creating a GeneratedCodeResult entity."""
        template_id = CodegenTemplateId("template-id")
        output_path = Path("/output/user.py")
        
        result = GeneratedCodeResult(
            template_id=template_id,
            output_path=output_path,
            generated_code="class User:\n    pass\n",
            model_name="User"
        )
        
        assert result.template_id == template_id
        assert result.output_path == output_path
        assert result.generated_code == "class User:\n    pass\n"
        assert result.model_name == "User"
        assert isinstance(result.timestamp, datetime)
    
    def test_to_dict(self):
        """Test converting a GeneratedCodeResult to a dictionary."""
        template_id = CodegenTemplateId("template-id")
        output_path = Path("/output/user.py")
        
        result = GeneratedCodeResult(
            template_id=template_id,
            output_path=output_path,
            generated_code="class User:\n    pass\n",
            model_name="User"
        )
        
        dict_result = result.to_dict()
        
        assert dict_result["template_id"] == "template-id"
        assert dict_result["output_path"] == "/output/user.py"
        assert dict_result["model_name"] == "User"
        assert "timestamp" in dict_result


class TestDocumentationAsset:
    """Tests for the DocumentationAsset entity."""
    
    def test_documentation_asset_creation(self):
        """Test creating a DocumentationAsset entity."""
        doc_id = DocumentationId("doc-id")
        path = Path("/docs/module.md")
        
        asset = DocumentationAsset(
            id=doc_id,
            title="Module Documentation",
            content="# Module\n\nThis is the documentation for the module.",
            path=path,
            format="markdown"
        )
        
        assert asset.id == doc_id
        assert asset.title == "Module Documentation"
        assert asset.content == "# Module\n\nThis is the documentation for the module."
        assert asset.path == path
        assert asset.format == "markdown"
        assert isinstance(asset.timestamp, datetime)
    
    def test_to_dict(self):
        """Test converting a DocumentationAsset to a dictionary."""
        doc_id = DocumentationId("doc-id")
        path = Path("/docs/module.md")
        
        asset = DocumentationAsset(
            id=doc_id,
            title="Module Documentation",
            content="# Module\n\nThis is the documentation for the module.",
            path=path,
            format="markdown"
        )
        
        result = asset.to_dict()
        
        assert result["id"] == "doc-id"
        assert result["title"] == "Module Documentation"
        assert result["path"] == "/docs/module.md"
        assert result["format"] == "markdown"
        assert "timestamp" in result


class TestDiagramSpecification:
    """Tests for the DiagramSpecification entity."""
    
    def test_diagram_specification_creation(self):
        """Test creating a DiagramSpecification entity."""
        output_path = Path("/diagrams/module-dependencies.svg")
        
        spec = DiagramSpecification(
            title="Module Dependencies",
            diagram_type="dependency",
            include_modules=["uno.core", "uno.database"],
            exclude_modules=["uno.tests"],
            output_format="svg",
            output_path=output_path
        )
        
        assert spec.title == "Module Dependencies"
        assert spec.diagram_type == "dependency"
        assert spec.include_modules == ["uno.core", "uno.database"]
        assert spec.exclude_modules == ["uno.tests"]
        assert spec.output_format == "svg"
        assert spec.output_path == output_path
    
    def test_diagram_specification_defaults(self):
        """Test creating a DiagramSpecification with default values."""
        spec = DiagramSpecification(
            title="Module Dependencies",
            diagram_type="dependency"
        )
        
        assert spec.title == "Module Dependencies"
        assert spec.diagram_type == "dependency"
        assert spec.include_modules == []
        assert spec.exclude_modules == []
        assert spec.output_format == "svg"
        assert spec.output_path is None
    
    def test_to_dict(self):
        """Test converting a DiagramSpecification to a dictionary."""
        output_path = Path("/diagrams/module-dependencies.svg")
        
        spec = DiagramSpecification(
            title="Module Dependencies",
            diagram_type="dependency",
            include_modules=["uno.core", "uno.database"],
            exclude_modules=["uno.tests"],
            output_format="svg",
            output_path=output_path
        )
        
        result = spec.to_dict()
        
        assert result["title"] == "Module Dependencies"
        assert result["diagram_type"] == "dependency"
        assert result["include_modules"] == ["uno.core", "uno.database"]
        assert result["exclude_modules"] == ["uno.tests"]
        assert result["output_format"] == "svg"
        assert result["output_path"] == "/diagrams/module-dependencies.svg"