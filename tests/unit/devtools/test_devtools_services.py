"""
Tests for the DevTools module domain services.

This module contains tests for all domain services in the DevTools module,
focusing on the business logic for debugging, profiling, code generation, and documentation.
"""

import pytest
import uuid
import json
import time
import os
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
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
from uno.devtools.domain_repositories import (
    ProfilerSessionRepositoryProtocol,
    MemoryProfilerSessionRepositoryProtocol,
    CodegenTemplateRepositoryProtocol,
    GeneratedCodeRepositoryProtocol,
    DocumentationAssetRepositoryProtocol
)
from uno.devtools.domain_services import (
    DebugService,
    ProfilerService,
    MemoryProfilerService,
    CodegenService,
    DocumentationService
)


class TestDebugService:
    """Tests for the DebugService."""
    
    def test_configure(self):
        """Test configuring the debug service."""
        service = DebugService()
        config = DebugConfiguration(level=DebugLevel.DEBUG, trace_sql=True)
        
        result = service.configure(config)
        
        assert isinstance(result, Success)
        assert result.value == config
        assert service._config == config
    
    def test_get_configuration(self):
        """Test getting the current debug configuration."""
        service = DebugService()
        config = DebugConfiguration(level=DebugLevel.DEBUG, trace_sql=True)
        
        # Configure the service first
        service.configure(config)
        
        # Then get the configuration
        result = service.get_configuration()
        
        assert isinstance(result, Success)
        assert result.value == config
    
    def test_trace_function(self):
        """Test the trace_function decorator."""
        service = DebugService()
        
        # Set up a high level to enable tracing
        config = DebugConfiguration(level=DebugLevel.TRACE)
        service.configure(config)
        
        # Define a function to be traced
        def test_func():
            return "test"
        
        # Apply the decorator
        traced_func = service.trace_function(test_func)
        
        # Call the traced function with stdout capture
        with patch('builtins.print') as mock_print:
            result = traced_func()
            
            # Check the result is correct
            assert result == "test"
            
            # Check that tracing occurred
            mock_print.assert_called()
            
            # Specifically check that the first call contains the entry message
            args, _ = mock_print.call_args_list[0]
            assert "TRACE: Entering test_func" in args[0]
    
    def test_setup_sql_debugging(self):
        """Test setting up SQL debugging."""
        service = DebugService()
        
        # Enable SQL debugging
        result = service.setup_sql_debugging(True)
        
        assert isinstance(result, Success)
        assert service._config.trace_sql is True
        
        # Disable SQL debugging
        result = service.setup_sql_debugging(False)
        
        assert isinstance(result, Success)
        assert service._config.trace_sql is False
    
    def test_setup_repository_debugging(self):
        """Test setting up repository debugging."""
        service = DebugService()
        
        # This method is a stub in the implementation
        result = service.setup_repository_debugging(True)
        
        assert isinstance(result, Success)
    
    def test_enhance_error_information_enabled(self):
        """Test enhancing error information when enabled."""
        service = DebugService()
        config = DebugConfiguration(enhance_errors=True)
        service.configure(config)
        
        # Create a sample error
        try:
            raise ValueError("Test error")
        except ValueError as e:
            error = e
        
        # Enhance the error information
        result = service.enhance_error_information(error)
        
        assert isinstance(result, Success)
        enhanced_info = result.value
        
        assert enhanced_info["error_type"] == "ValueError"
        assert enhanced_info["message"] == "Test error"
        assert "traceback" in enhanced_info
        assert "timestamp" in enhanced_info
    
    def test_enhance_error_information_disabled(self):
        """Test enhancing error information when disabled."""
        service = DebugService()
        config = DebugConfiguration(enhance_errors=False)
        service.configure(config)
        
        # Create a sample error
        error = ValueError("Test error")
        
        # Try to enhance the error information
        result = service.enhance_error_information(error)
        
        assert isinstance(result, Failure)
        assert result.error.code == "ERROR_ENHANCEMENT_DISABLED"


class TestProfilerService:
    """Tests for the ProfilerService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock profiler session repository."""
        repository = MagicMock(spec=ProfilerSessionRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a profiler service with a mock repository."""
        return ProfilerService(repository=mock_repository)
    
    def test_start_session(self, service):
        """Test starting a profiler session."""
        config = ProfilerConfiguration()
        
        result = service.start_session(config)
        
        assert isinstance(result, Success)
        assert isinstance(result.value, ProfilerSessionId)
        assert str(result.value) in service.active_sessions
        assert service.active_sessions[str(result.value)].configuration == config
    
    def test_end_session(self, service, mock_repository):
        """Test ending a profiler session."""
        # Start a session first
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        
        # Set up the repository to return success
        mock_repository.save.return_value = Success(service.active_sessions[str(session_id)])
        
        # End the session
        result = service.end_session(session_id)
        
        assert isinstance(result, Success)
        assert result.value.id == session_id
        assert result.value.end_time is not None
        assert str(session_id) not in service.active_sessions
        mock_repository.save.assert_called_once()
    
    def test_end_session_not_found(self, service):
        """Test ending a non-existent profiler session."""
        session_id = ProfilerSessionId("nonexistent")
        
        result = service.end_session(session_id)
        
        assert isinstance(result, Failure)
        assert result.error.code == "PROFILER_SESSION_NOT_FOUND"
    
    def test_profile_function(self, service):
        """Test profiling a function."""
        # Start a session
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session = service.active_sessions[str(session_id_result.value)]
        
        # Define a function to profile
        def test_func():
            time.sleep(0.01)  # Small delay for measurable execution time
            return "test"
        
        # Apply the decorator
        profiled_func = service.profile_function(test_func)
        
        # Call the profiled function
        result = profiled_func()
        
        # Check the result is correct
        assert result == "test"
        
        # Check that a metric was added to the session
        assert len(session.metrics) == 1
        metric = session.metrics[0]
        assert metric.name == "test_func"
        assert metric.calls == 1
        assert metric.total_time > 0
    
    def test_profile_function_with_exception(self, service):
        """Test profiling a function that raises an exception."""
        # Start a session
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session = service.active_sessions[str(session_id_result.value)]
        
        # Define a function that raises an exception
        def failing_func():
            time.sleep(0.01)  # Small delay for measurable execution time
            raise ValueError("Test error")
        
        # Apply the decorator
        profiled_func = service.profile_function(failing_func)
        
        # Call the profiled function and expect an exception
        with pytest.raises(ValueError):
            profiled_func()
        
        # Check that a metric was still added to the session
        assert len(session.metrics) == 1
        metric = session.metrics[0]
        assert metric.name == "failing_func"
        assert metric.calls == 1
        assert metric.total_time > 0
    
    def test_get_session_active(self, service):
        """Test getting an active profiler session."""
        # Start a session
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        
        # Get the session
        result = service.get_session(session_id)
        
        assert isinstance(result, Success)
        assert result.value.id == session_id
    
    def test_get_session_from_repository(self, service, mock_repository):
        """Test getting a profiler session from the repository."""
        session_id = ProfilerSessionId("saved-session")
        saved_session = ProfilerSession(
            id=session_id,
            start_time=datetime.now(UTC)
        )
        
        # Set up the repository to return the session
        mock_repository.get_by_id.return_value = Success(saved_session)
        
        # Get the session
        result = service.get_session(session_id)
        
        assert isinstance(result, Success)
        assert result.value == saved_session
        mock_repository.get_by_id.assert_called_once_with(session_id)
    
    def test_analyze_hotspots(self, service):
        """Test analyzing hotspots in a profiler session."""
        # Start a session
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        session = service.active_sessions[str(session_id)]
        
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
        
        # Analyze hotspots
        result = service.analyze_hotspots(session_id)
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == hotspot
    
    def test_export_session_json(self, service, mock_repository, tmp_path):
        """Test exporting a profiler session to JSON."""
        # Start a session
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        session = service.active_sessions[str(session_id)]
        
        # Add some metrics
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
        
        # Complete the session
        session.complete()
        
        # Export to JSON
        export_path = tmp_path / "profile.json"
        result = service.export_session(session_id, "json", export_path)
        
        assert isinstance(result, Success)
        assert result.value == export_path
        assert export_path.exists()
        
        # Verify the exported JSON
        with open(export_path, 'r') as f:
            data = json.load(f)
            assert data["id"] == str(session_id)
            assert "start_time" in data
            assert "end_time" in data
            assert "metrics" in data
            assert len(data["metrics"]) == 1
    
    def test_export_session_html(self, service, mock_repository, tmp_path):
        """Test exporting a profiler session to HTML."""
        # Start a session
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        session = service.active_sessions[str(session_id)]
        
        # Add some metrics
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
        
        # Complete the session
        session.complete()
        
        # Export to HTML
        export_path = tmp_path / "profile.html"
        result = service.export_session(session_id, "html", export_path)
        
        assert isinstance(result, Success)
        assert result.value == export_path
        assert export_path.exists()
        
        # Verify the exported HTML contains expected content
        with open(export_path, 'r') as f:
            content = f.read()
            assert f"<h1>Profiler Session {session_id}</h1>" in content
            assert "<table" in content
            assert "test_function" in content
    
    def test_export_session_unsupported_format(self, service):
        """Test exporting a profiler session to an unsupported format."""
        # Start a session
        config = ProfilerConfiguration()
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        
        # Export to unsupported format
        result = service.export_session(session_id, "invalid", Path("output.invalid"))
        
        assert isinstance(result, Failure)
        assert result.error.code == "UNSUPPORTED_FORMAT"


class TestMemoryProfilerService:
    """Tests for the MemoryProfilerService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock memory profiler session repository."""
        repository = MagicMock(spec=MemoryProfilerSessionRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a memory profiler service with a mock repository."""
        return MemoryProfilerService(repository=mock_repository)
    
    def test_start_session(self, service):
        """Test starting a memory profiler session."""
        config = ProfilerConfiguration(type=ProfilerType.MEMORY)
        
        result = service.start_session(config)
        
        assert isinstance(result, Success)
        assert isinstance(result.value, ProfilerSessionId)
        assert str(result.value) in service.active_sessions
        assert service.active_sessions[str(result.value)].configuration == config
    
    def test_end_session(self, service, mock_repository):
        """Test ending a memory profiler session."""
        # Start a session first
        config = ProfilerConfiguration(type=ProfilerType.MEMORY)
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        
        # Set up the repository to return success
        mock_repository.save.return_value = Success(service.active_sessions[str(session_id)])
        
        # End the session
        result = service.end_session(session_id)
        
        assert isinstance(result, Success)
        assert result.value.id == session_id
        assert result.value.end_time is not None
        assert str(session_id) not in service.active_sessions
        mock_repository.save.assert_called_once()
    
    def test_end_session_not_found(self, service):
        """Test ending a non-existent memory profiler session."""
        session_id = ProfilerSessionId("nonexistent")
        
        result = service.end_session(session_id)
        
        assert isinstance(result, Failure)
        assert result.error.code == "MEMORY_PROFILER_SESSION_NOT_FOUND"
    
    def test_profile_memory_usage(self, service):
        """Test profiling memory usage of a function."""
        # Start a session
        config = ProfilerConfiguration(type=ProfilerType.MEMORY)
        session_id_result = service.start_session(config)
        session = service.active_sessions[str(session_id_result.value)]
        
        # Define a function to profile
        def test_func():
            # Allocate some memory (though this won't be tracked in the simplified implementation)
            x = [0] * 1000000
            return len(x)
        
        # Apply the decorator
        profiled_func = service.profile_memory_usage(test_func)
        
        # Call the profiled function
        result = profiled_func()
        
        # Check the result is correct
        assert result == 1000000
        
        # Check that a metric was added to the session
        assert len(session.metrics) == 1
        metric = session.metrics[0]
        assert metric.name == "test_func"
        assert metric.allocations == 1
    
    def test_get_session_active(self, service):
        """Test getting an active memory profiler session."""
        # Start a session
        config = ProfilerConfiguration(type=ProfilerType.MEMORY)
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        
        # Get the session
        result = service.get_session(session_id)
        
        assert isinstance(result, Success)
        assert result.value.id == session_id
    
    def test_get_session_from_repository(self, service, mock_repository):
        """Test getting a memory profiler session from the repository."""
        session_id = ProfilerSessionId("saved-session")
        saved_session = MemoryProfilerSession(
            id=session_id,
            start_time=datetime.now(UTC)
        )
        
        # Set up the repository to return the session
        mock_repository.get_by_id.return_value = Success(saved_session)
        
        # Get the session
        result = service.get_session(session_id)
        
        assert isinstance(result, Success)
        assert result.value == saved_session
        mock_repository.get_by_id.assert_called_once_with(session_id)
    
    def test_analyze_leaks(self, service):
        """Test analyzing memory leaks in a profiler session."""
        # Start a session
        config = ProfilerConfiguration(type=ProfilerType.MEMORY)
        session_id_result = service.start_session(config)
        session_id = session_id_result.value
        session = service.active_sessions[str(session_id)]
        
        # Add metrics with and without leaks
        leaky_metric = MemoryMetric(
            name="leaky_function",
            allocations=10,
            bytes_allocated=1024000,
            peak_memory=2048000,
            leak_count=5
        )
        session.add_metric(leaky_metric)
        
        clean_metric = MemoryMetric(
            name="clean_function",
            allocations=10,
            bytes_allocated=1024000,
            peak_memory=2048000,
            leak_count=0
        )
        session.add_metric(clean_metric)
        
        # Analyze leaks
        result = service.analyze_leaks(session_id)
        
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert result.value[0] == leaky_metric


class TestCodegenService:
    """Tests for the CodegenService."""
    
    @pytest.fixture
    def mock_template_repository(self):
        """Create a mock template repository."""
        repository = MagicMock(spec=CodegenTemplateRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def mock_generated_code_repository(self):
        """Create a mock generated code repository."""
        repository = MagicMock(spec=GeneratedCodeRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_template_repository, mock_generated_code_repository):
        """Create a codegen service with mock repositories."""
        return CodegenService(
            template_repository=mock_template_repository,
            generated_code_repository=mock_generated_code_repository
        )
    
    def test_register_template(self, service, mock_template_repository):
        """Test registering a code generation template."""
        template = CodegenTemplate(
            id=CodegenTemplateId("template-id"),
            name="Model Template",
            type=CodegenType.MODEL,
            template_path=Path("/templates/model.jinja2")
        )
        
        mock_template_repository.save.return_value = Success(template)
        
        result = service.register_template(template)
        
        assert isinstance(result, Success)
        assert result.value == template
        mock_template_repository.save.assert_called_once_with(template)
    
    def test_get_template(self, service, mock_template_repository):
        """Test getting a template by ID."""
        template_id = CodegenTemplateId("template-id")
        template = CodegenTemplate(
            id=template_id,
            name="Model Template",
            type=CodegenType.MODEL,
            template_path=Path("/templates/model.jinja2")
        )
        
        mock_template_repository.get_by_id.return_value = Success(template)
        
        result = service.get_template(template_id)
        
        assert isinstance(result, Success)
        assert result.value == template
        mock_template_repository.get_by_id.assert_called_once_with(template_id)
    
    def test_list_templates(self, service, mock_template_repository):
        """Test listing all templates."""
        templates = [
            CodegenTemplate(
                id=CodegenTemplateId("template-1"),
                name="Model Template",
                type=CodegenType.MODEL,
                template_path=Path("/templates/model.jinja2")
            ),
            CodegenTemplate(
                id=CodegenTemplateId("template-2"),
                name="Repository Template",
                type=CodegenType.REPOSITORY,
                template_path=Path("/templates/repository.jinja2")
            )
        ]
        
        mock_template_repository.list_templates.return_value = Success(templates)
        
        result = service.list_templates()
        
        assert isinstance(result, Success)
        assert result.value == templates
        mock_template_repository.list_templates.assert_called_once()
    
    def test_generate_model(self, service, mock_template_repository, mock_generated_code_repository, tmp_path):
        """Test generating a model."""
        # Setup
        template = CodegenTemplate(
            id=CodegenTemplateId("model-template"),
            name="Model Template",
            type=CodegenType.MODEL,
            template_path=Path("/templates/model.jinja2")
        )
        
        mock_template_repository.list_templates.return_value = Success([template])
        
        fields = {
            "id": "str",
            "name": "str",
            "age": "int",
            "email": "str"
        }
        
        output_path = tmp_path / "user.py"
        
        # Mock the save method to return success
        def mock_save(result):
            return Success(result)
        
        mock_generated_code_repository.save.side_effect = mock_save
        
        # Execute
        result = service.generate_model("User", fields, output_path)
        
        # Assert
        assert isinstance(result, Success)
        assert result.value.template_id == template.id
        assert result.value.output_path == output_path
        assert result.value.model_name == "User"
        assert "class User" in result.value.generated_code
        assert "id: str" in result.value.generated_code
        assert "name: str" in result.value.generated_code
        assert "age: int" in result.value.generated_code
        assert "email: str" in result.value.generated_code
        assert "created_at" in result.value.generated_code
        assert "updated_at" in result.value.generated_code
        assert "to_dict" in result.value.generated_code
        
        # Check that the file was created
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
            assert "class User" in content
    
    def test_generate_model_no_template(self, service, mock_template_repository):
        """Test generating a model when no template is available."""
        # Setup - empty template list
        mock_template_repository.list_templates.return_value = Success([])
        
        fields = {"id": "str", "name": "str"}
        output_path = Path("/output/user.py")
        
        # Execute
        result = service.generate_model("User", fields, output_path)
        
        # Assert
        assert isinstance(result, Failure)
        assert result.error.code == "NO_MODEL_TEMPLATE"
    
    def test_not_implemented_methods(self, service):
        """Test methods that are not yet implemented."""
        # These methods return a NOT_IMPLEMENTED error in the current implementation
        
        # generate_repository
        result = service.generate_repository("User", Path("/output/user_repository.py"))
        assert isinstance(result, Failure)
        assert result.error.code == "NOT_IMPLEMENTED"
        
        # generate_service
        result = service.generate_service("User", Path("/output/user_service.py"))
        assert isinstance(result, Failure)
        assert result.error.code == "NOT_IMPLEMENTED"
        
        # generate_api
        result = service.generate_api("User", Path("/output/user_api.py"))
        assert isinstance(result, Failure)
        assert result.error.code == "NOT_IMPLEMENTED"
        
        # generate_crud
        result = service.generate_crud("User", Path("/output/user_crud.py"))
        assert isinstance(result, Failure)
        assert result.error.code == "NOT_IMPLEMENTED"
        
        # create_project
        result = service.create_project("MyProject", Path("/output/myproject"), {})
        assert isinstance(result, Failure)
        assert result.error.code == "NOT_IMPLEMENTED"


class TestDocumentationService:
    """Tests for the DocumentationService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock documentation asset repository."""
        repository = MagicMock(spec=DocumentationAssetRepositoryProtocol)
        return repository
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create a documentation service with a mock repository."""
        return DocumentationService(repository=mock_repository)
    
    @pytest.mark.skip(reason="This test requires importing a real module, which might not be available")
    def test_generate_documentation(self, service, mock_repository):
        """Test generating documentation for a module."""
        # This test is skipped because it requires importing a real module
        # In a real test suite, you would use a test module or mock the importlib module
        pass
    
    def test_generate_documentation_module_not_found(self, service):
        """Test generating documentation for a non-existent module."""
        result = service.generate_documentation("nonexistent.module")
        
        assert isinstance(result, Failure)
        assert result.error.code == "MODULE_NOT_FOUND"
    
    def test_generate_diagram(self, service, tmp_path):
        """Test generating a diagram."""
        spec = DiagramSpecification(
            title="Module Dependencies",
            diagram_type="dependency",
            include_modules=["uno.core", "uno.database"],
            exclude_modules=[],
            output_path=tmp_path / "diagram.svg"
        )
        
        result = service.generate_diagram(spec)
        
        assert isinstance(result, Success)
        assert result.value == spec.output_path
        assert spec.output_path.exists()
        
        # Check the content of the generated diagram
        with open(spec.output_path, 'r') as f:
            content = f.read()
            assert "Diagram: Module Dependencies" in content
            assert "Type: dependency" in content
            assert "Include modules:" in content
            assert "- uno.core" in content
            assert "- uno.database" in content
    
    def test_generate_diagram_without_output_path(self, service):
        """Test generating a diagram without specifying an output path."""
        spec = DiagramSpecification(
            title="Module Dependencies",
            diagram_type="dependency"
        )
        
        result = service.generate_diagram(spec)
        
        assert isinstance(result, Success)
        assert result.value == Path("module_dependencies.svg")
        assert result.value.exists()
        
        # Clean up the generated file
        os.remove(result.value)
    
    @pytest.mark.skip(reason="This test requires importing a real module, which might not be available")
    def test_extract_docstrings(self, service):
        """Test extracting docstrings from a module."""
        # This test is skipped because it requires importing a real module
        # In a real test suite, you would use a test module or mock the importlib module
        pass
    
    def test_extract_docstrings_module_not_found(self, service):
        """Test extracting docstrings from a non-existent module."""
        result = service.extract_docstrings("nonexistent.module")
        
        assert isinstance(result, Failure)
        assert result.error.code == "MODULE_NOT_FOUND"
    
    def test_serve_documentation(self, service):
        """Test serving documentation."""
        # This method is not implemented in the current implementation
        result = service.serve_documentation()
        
        assert isinstance(result, Failure)
        assert result.error.code == "NOT_IMPLEMENTED"