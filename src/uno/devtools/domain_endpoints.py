"""
Domain endpoints for the DevTools module.

This module defines FastAPI endpoints for the DevTools module, providing HTTP API
access to debugging, profiling, code generation, and documentation functionalities.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from uno.core.errors.result import Result, Success, Failure
from uno.devtools.entities import (
    DebugConfiguration, DebugLevel,
    ProfilerConfiguration, ProfilerType, ProfilerSessionId, ProfileMetric,
    MemoryProfilerSession, MemoryMetric,
    CodegenTemplate, CodegenTemplateId, CodegenType, GeneratedCodeResult,
    DocumentationAsset, DocumentationId, DiagramSpecification,
    # Request/Response Models
    DebugConfigurationRequest, ProfilerConfigurationRequest,
    CodegenRequest, DiagramRequest
)
from uno.devtools.domain_services import (
    DebugServiceProtocol,
    ProfilerServiceProtocol,
    MemoryProfilerServiceProtocol,
    CodegenServiceProtocol,
    DocumentationServiceProtocol,
)
from uno.devtools.domain_provider import DevToolsProvider


# Response Models

class ProfilerSessionResponse(BaseModel):
    """Response model for a profiler session."""
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    profile_type: str
    metrics_count: int


class ProfileMetricResponse(BaseModel):
    """Response model for a profiler metric."""
    name: str
    calls: int
    total_time: float
    own_time: float
    avg_time: float
    max_time: float
    min_time: float
    is_hotspot: bool


class MemoryProfilerSessionResponse(BaseModel):
    """Response model for a memory profiler session."""
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics_count: int


class MemoryMetricResponse(BaseModel):
    """Response model for a memory metric."""
    name: str
    allocations: int
    bytes_allocated: int
    peak_memory: int
    leak_count: int


class CodegenTemplateResponse(BaseModel):
    """Response model for a code generation template."""
    id: str
    name: str
    type: str
    description: str


class GeneratedCodeResultResponse(BaseModel):
    """Response model for a generated code result."""
    template_id: str
    output_path: str
    model_name: str
    timestamp: datetime


class DocumentationAssetResponse(BaseModel):
    """Response model for a documentation asset."""
    id: str
    title: str
    path: str
    format: str
    timestamp: datetime


class DiagramSpecificationResponse(BaseModel):
    """Response model for a diagram specification."""
    title: str
    diagram_type: str
    include_modules: List[str]
    exclude_modules: List[str]
    output_format: str
    output_path: Optional[str] = None


# Helper Functions

def get_debug_service() -> DebugServiceProtocol:
    """Dependency injection for the debug service."""
    return DevToolsProvider.get_debug_service()


def get_profiler_service() -> ProfilerServiceProtocol:
    """Dependency injection for the profiler service."""
    return DevToolsProvider.get_profiler_service()


def get_memory_profiler_service() -> MemoryProfilerServiceProtocol:
    """Dependency injection for the memory profiler service."""
    return DevToolsProvider.get_memory_profiler_service()


def get_codegen_service() -> CodegenServiceProtocol:
    """Dependency injection for the code generation service."""
    return DevToolsProvider.get_codegen_service()


def get_documentation_service() -> DocumentationServiceProtocol:
    """Dependency injection for the documentation service."""
    return DevToolsProvider.get_documentation_service()


# Router

router = APIRouter(prefix="/api/devtools", tags=["DevTools"])


# Debug Endpoints

@router.get("/debug/config", response_model=DebugConfiguration)
def get_debug_config(
    debug_service: DebugServiceProtocol = Depends(get_debug_service)
) -> Dict[str, Any]:
    """Get the current debug configuration."""
    result = debug_service.get_configuration()
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting debug configuration: {result.error.message}"
        )
    
    return {
        "level": result.value.level.name,
        "trace_sql": result.value.trace_sql,
        "trace_repository": result.value.trace_repository,
        "enhance_errors": result.value.enhance_errors,
        "log_file": str(result.value.log_file) if result.value.log_file else None
    }


@router.post("/debug/config", response_model=DebugConfiguration)
def set_debug_config(
    config: DebugConfigurationRequest,
    debug_service: DebugServiceProtocol = Depends(get_debug_service)
) -> Dict[str, Any]:
    """Set the debug configuration."""
    # Convert string level to enum
    try:
        level = DebugLevel[config.level]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid debug level: {config.level}"
        )
    
    # Create the configuration object
    debug_config = DebugConfiguration(
        level=level,
        trace_sql=config.trace_sql,
        trace_repository=config.trace_repository,
        enhance_errors=config.enhance_errors,
        log_file=Path(config.log_file) if config.log_file else None
    )
    
    # Apply the configuration
    result = debug_service.configure(debug_config)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting debug configuration: {result.error.message}"
        )
    
    return {
        "level": result.value.level.name,
        "trace_sql": result.value.trace_sql,
        "trace_repository": result.value.trace_repository,
        "enhance_errors": result.value.enhance_errors,
        "log_file": str(result.value.log_file) if result.value.log_file else None
    }


@router.post("/debug/sql")
def set_sql_debugging(
    enabled: bool,
    debug_service: DebugServiceProtocol = Depends(get_debug_service)
) -> Dict[str, Any]:
    """Enable or disable SQL debugging."""
    result = debug_service.setup_sql_debugging(enabled)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting SQL debugging: {result.error.message}"
        )
    
    return {"status": "success", "sql_debugging": enabled}


@router.post("/debug/repository")
def set_repository_debugging(
    enabled: bool,
    debug_service: DebugServiceProtocol = Depends(get_debug_service)
) -> Dict[str, Any]:
    """Enable or disable repository debugging."""
    result = debug_service.setup_repository_debugging(enabled)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting repository debugging: {result.error.message}"
        )
    
    return {"status": "success", "repository_debugging": enabled}


# Profiler Endpoints

@router.post("/profiler/sessions", response_model=Dict[str, str])
def start_profiler_session(
    config: ProfilerConfigurationRequest,
    profiler_service: ProfilerServiceProtocol = Depends(get_profiler_service)
) -> Dict[str, str]:
    """Start a new profiling session."""
    # Convert string type to enum
    try:
        profile_type = ProfilerType[config.type]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profiler type: {config.type}"
        )
    
    # Create the configuration object
    profiler_config = ProfilerConfiguration(
        type=profile_type,
        sample_rate=config.sample_rate,
        output_format=config.output_format,
        output_path=Path(config.output_path) if config.output_path else None,
        include_modules=config.include_modules,
        exclude_modules=config.exclude_modules
    )
    
    # Start the session
    result = profiler_service.start_session(profiler_config)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting profiler session: {result.error.message}"
        )
    
    return {"session_id": str(result.value)}


@router.post("/profiler/sessions/{session_id}/end", response_model=ProfilerSessionResponse)
def end_profiler_session(
    session_id: str,
    profiler_service: ProfilerServiceProtocol = Depends(get_profiler_service)
) -> ProfilerSessionResponse:
    """End a profiling session."""
    result = profiler_service.end_session(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ending profiler session: {result.error.message}"
        )
    
    session = result.value
    return ProfilerSessionResponse(
        id=str(session.id),
        start_time=session.start_time,
        end_time=session.end_time,
        duration=session.duration,
        profile_type=session.configuration.type.name,
        metrics_count=len(session.metrics)
    )


@router.get("/profiler/sessions/{session_id}", response_model=ProfilerSessionResponse)
def get_profiler_session(
    session_id: str,
    profiler_service: ProfilerServiceProtocol = Depends(get_profiler_service)
) -> ProfilerSessionResponse:
    """Get a profiling session by ID."""
    result = profiler_service.get_session(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profiler session not found: {result.error.message}"
        )
    
    session = result.value
    return ProfilerSessionResponse(
        id=str(session.id),
        start_time=session.start_time,
        end_time=session.end_time,
        duration=session.duration,
        profile_type=session.configuration.type.name,
        metrics_count=len(session.metrics)
    )


@router.get("/profiler/sessions/{session_id}/metrics", response_model=List[ProfileMetricResponse])
def get_profiler_session_metrics(
    session_id: str,
    profiler_service: ProfilerServiceProtocol = Depends(get_profiler_service)
) -> List[ProfileMetricResponse]:
    """Get the metrics for a profiling session."""
    result = profiler_service.get_session(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profiler session not found: {result.error.message}"
        )
    
    session = result.value
    return [
        ProfileMetricResponse(
            name=metric.name,
            calls=metric.calls,
            total_time=metric.total_time,
            own_time=metric.own_time,
            avg_time=metric.avg_time,
            max_time=metric.max_time,
            min_time=metric.min_time,
            is_hotspot=metric.is_hotspot
        )
        for metric in session.metrics
    ]


@router.get("/profiler/sessions/{session_id}/hotspots", response_model=List[ProfileMetricResponse])
def get_profiler_session_hotspots(
    session_id: str,
    profiler_service: ProfilerServiceProtocol = Depends(get_profiler_service)
) -> List[ProfileMetricResponse]:
    """Get the hotspots for a profiling session."""
    result = profiler_service.analyze_hotspots(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing hotspots: {result.error.message}"
        )
    
    return [
        ProfileMetricResponse(
            name=metric.name,
            calls=metric.calls,
            total_time=metric.total_time,
            own_time=metric.own_time,
            avg_time=metric.avg_time,
            max_time=metric.max_time,
            min_time=metric.min_time,
            is_hotspot=metric.is_hotspot
        )
        for metric in result.value
    ]


@router.post("/profiler/sessions/{session_id}/export", response_model=Dict[str, str])
def export_profiler_session(
    session_id: str,
    format: str,
    profiler_service: ProfilerServiceProtocol = Depends(get_profiler_service)
) -> Dict[str, str]:
    """Export a profiling session to a file."""
    if format not in ["json", "html"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}"
        )
    
    result = profiler_service.export_session(ProfilerSessionId(session_id), format)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting profiler session: {result.error.message}"
        )
    
    return {"file_path": str(result.value)}


# Memory Profiler Endpoints

@router.post("/memory-profiler/sessions", response_model=Dict[str, str])
def start_memory_profiler_session(
    config: ProfilerConfigurationRequest,
    memory_profiler_service: MemoryProfilerServiceProtocol = Depends(get_memory_profiler_service)
) -> Dict[str, str]:
    """Start a new memory profiling session."""
    # Convert string type to enum (using the same ProfilerType enum)
    try:
        profile_type = ProfilerType[config.type]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profiler type: {config.type}"
        )
    
    # Create the configuration object
    profiler_config = ProfilerConfiguration(
        type=profile_type,
        sample_rate=config.sample_rate,
        output_format=config.output_format,
        output_path=Path(config.output_path) if config.output_path else None,
        include_modules=config.include_modules,
        exclude_modules=config.exclude_modules
    )
    
    # Start the session
    result = memory_profiler_service.start_session(profiler_config)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting memory profiler session: {result.error.message}"
        )
    
    return {"session_id": str(result.value)}


@router.post("/memory-profiler/sessions/{session_id}/end", response_model=MemoryProfilerSessionResponse)
def end_memory_profiler_session(
    session_id: str,
    memory_profiler_service: MemoryProfilerServiceProtocol = Depends(get_memory_profiler_service)
) -> MemoryProfilerSessionResponse:
    """End a memory profiling session."""
    result = memory_profiler_service.end_session(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ending memory profiler session: {result.error.message}"
        )
    
    session = result.value
    return MemoryProfilerSessionResponse(
        id=str(session.id),
        start_time=session.start_time,
        end_time=session.end_time,
        metrics_count=len(session.metrics)
    )


@router.get("/memory-profiler/sessions/{session_id}", response_model=MemoryProfilerSessionResponse)
def get_memory_profiler_session(
    session_id: str,
    memory_profiler_service: MemoryProfilerServiceProtocol = Depends(get_memory_profiler_service)
) -> MemoryProfilerSessionResponse:
    """Get a memory profiling session by ID."""
    result = memory_profiler_service.get_session(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory profiler session not found: {result.error.message}"
        )
    
    session = result.value
    return MemoryProfilerSessionResponse(
        id=str(session.id),
        start_time=session.start_time,
        end_time=session.end_time,
        metrics_count=len(session.metrics)
    )


@router.get("/memory-profiler/sessions/{session_id}/metrics", response_model=List[MemoryMetricResponse])
def get_memory_profiler_session_metrics(
    session_id: str,
    memory_profiler_service: MemoryProfilerServiceProtocol = Depends(get_memory_profiler_service)
) -> List[MemoryMetricResponse]:
    """Get the metrics for a memory profiling session."""
    result = memory_profiler_service.get_session(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory profiler session not found: {result.error.message}"
        )
    
    session = result.value
    return [
        MemoryMetricResponse(
            name=metric.name,
            allocations=metric.allocations,
            bytes_allocated=metric.bytes_allocated,
            peak_memory=metric.peak_memory,
            leak_count=metric.leak_count
        )
        for metric in session.metrics
    ]


@router.get("/memory-profiler/sessions/{session_id}/leaks", response_model=List[MemoryMetricResponse])
def get_memory_profiler_session_leaks(
    session_id: str,
    memory_profiler_service: MemoryProfilerServiceProtocol = Depends(get_memory_profiler_service)
) -> List[MemoryMetricResponse]:
    """Get the potential memory leaks for a memory profiling session."""
    result = memory_profiler_service.analyze_leaks(ProfilerSessionId(session_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing memory leaks: {result.error.message}"
        )
    
    return [
        MemoryMetricResponse(
            name=metric.name,
            allocations=metric.allocations,
            bytes_allocated=metric.bytes_allocated,
            peak_memory=metric.peak_memory,
            leak_count=metric.leak_count
        )
        for metric in result.value
    ]


# Code Generation Endpoints

@router.get("/codegen/templates", response_model=List[CodegenTemplateResponse])
def list_codegen_templates(
    codegen_service: CodegenServiceProtocol = Depends(get_codegen_service)
) -> List[CodegenTemplateResponse]:
    """List all code generation templates."""
    result = codegen_service.list_templates()
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing code generation templates: {result.error.message}"
        )
    
    return [
        CodegenTemplateResponse(
            id=str(template.id),
            name=template.name,
            type=template.type.name,
            description=template.description
        )
        for template in result.value
    ]


@router.post("/codegen/templates/{template_id}", response_model=CodegenTemplateResponse)
def get_codegen_template(
    template_id: str,
    codegen_service: CodegenServiceProtocol = Depends(get_codegen_service)
) -> CodegenTemplateResponse:
    """Get a code generation template by ID."""
    result = codegen_service.get_template(CodegenTemplateId(template_id))
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Code generation template not found: {result.error.message}"
        )
    
    template = result.value
    return CodegenTemplateResponse(
        id=str(template.id),
        name=template.name,
        type=template.type.name,
        description=template.description
    )


@router.post("/codegen/generate", response_model=GeneratedCodeResultResponse)
def generate_code(
    request: CodegenRequest,
    codegen_service: CodegenServiceProtocol = Depends(get_codegen_service)
) -> GeneratedCodeResultResponse:
    """Generate code based on a template."""
    # Convert string type to enum
    try:
        codegen_type = CodegenType[request.type]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code generation type: {request.type}"
        )
    
    # Call the appropriate service method based on the type
    if codegen_type == CodegenType.MODEL:
        result = codegen_service.generate_model(
            request.name,
            request.fields,
            Path(request.output_path)
        )
    elif codegen_type == CodegenType.REPOSITORY:
        result = codegen_service.generate_repository(
            request.name,
            Path(request.output_path)
        )
    elif codegen_type == CodegenType.SERVICE:
        result = codegen_service.generate_service(
            request.name,
            Path(request.output_path)
        )
    elif codegen_type == CodegenType.API:
        result = codegen_service.generate_api(
            request.name,
            Path(request.output_path)
        )
    elif codegen_type == CodegenType.CRUD:
        result = codegen_service.generate_crud(
            request.name,
            Path(request.output_path)
        )
    elif codegen_type == CodegenType.PROJECT:
        # Projects are handled differently and not returned as GeneratedCodeResult
        project_result = codegen_service.create_project(
            request.name,
            Path(request.output_path),
            request.options
        )
        
        if isinstance(project_result, Failure):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating project: {project_result.error.message}"
            )
        
        # Return a simplified response for projects
        return GeneratedCodeResultResponse(
            template_id="project",
            output_path=str(project_result.value),
            model_name=request.name,
            timestamp=datetime.now()
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported code generation type: {request.type}"
        )
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating code: {result.error.message}"
        )
    
    generated_code = result.value
    return GeneratedCodeResultResponse(
        template_id=str(generated_code.template_id),
        output_path=str(generated_code.output_path),
        model_name=generated_code.model_name,
        timestamp=generated_code.timestamp
    )


# Documentation Endpoints

@router.post("/docs/generate", response_model=DocumentationAssetResponse)
def generate_documentation(
    module_path: str,
    documentation_service: DocumentationServiceProtocol = Depends(get_documentation_service)
) -> DocumentationAssetResponse:
    """Generate documentation for a module."""
    result = documentation_service.generate_documentation(module_path)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating documentation: {result.error.message}"
        )
    
    asset = result.value
    return DocumentationAssetResponse(
        id=str(asset.id),
        title=asset.title,
        path=str(asset.path),
        format=asset.format,
        timestamp=asset.timestamp
    )


@router.post("/docs/diagram", response_model=Dict[str, str])
def generate_diagram(
    request: DiagramRequest,
    documentation_service: DocumentationServiceProtocol = Depends(get_documentation_service)
) -> Dict[str, str]:
    """Generate a diagram based on a specification."""
    spec = DiagramSpecification(
        title=request.title,
        diagram_type=request.diagram_type,
        include_modules=request.include_modules,
        exclude_modules=request.exclude_modules,
        output_format=request.output_format,
        output_path=Path(request.output_path) if request.output_path else None
    )
    
    result = documentation_service.generate_diagram(spec)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating diagram: {result.error.message}"
        )
    
    return {"diagram_path": str(result.value)}


@router.get("/docs/extract", response_model=Dict[str, str])
def extract_docstrings(
    module_path: str,
    documentation_service: DocumentationServiceProtocol = Depends(get_documentation_service)
) -> Dict[str, str]:
    """Extract docstrings from a module."""
    result = documentation_service.extract_docstrings(module_path)
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting docstrings: {result.error.message}"
        )
    
    return result.value