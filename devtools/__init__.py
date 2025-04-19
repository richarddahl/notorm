"""
Uno Developer Tools package.

This package provides a collection of tools to enhance the developer experience when working
with the Uno framework, including debugging aids, profiling tools, code generators,
and interactive documentation utilities.

The DevTools module follows a domain-driven design approach, providing interfaces for
debugging, profiling, code generation, and documentation functionalities.
"""

__version__ = "0.1.0"

# Domain-driven design implementation
from uno.devtools.entities import (
    DebugConfiguration, DebugLevel,
    ProfilerConfiguration, ProfilerType, ProfilerSessionId, ProfileMetric,
    MemoryProfilerSession, MemoryMetric,
    CodegenTemplate, CodegenTemplateId, CodegenType, GeneratedCodeResult,
    DocumentationAsset, DocumentationId, DiagramSpecification,
)
from uno.devtools.domain_repositories import (
    ProfilerSessionRepositoryProtocol,
    MemoryProfilerSessionRepositoryProtocol,
    CodegenTemplateRepositoryProtocol,
    GeneratedCodeRepositoryProtocol,
    DocumentationAssetRepositoryProtocol,
)
from uno.devtools.domain_services import (
    DebugServiceProtocol,
    ProfilerServiceProtocol,
    MemoryProfilerServiceProtocol,
    CodegenServiceProtocol,
    DocumentationServiceProtocol,
)
from uno.devtools.domain_provider import DevToolsProvider, TestingDevToolsProvider
from uno.devtools.domain_endpoints import router as devtools_router

# Legacy compatibility imports
from uno.devtools.debugging import setup_debugger, DebugMiddleware, trace_function
from uno.devtools.profiling import Profiler, profile, ProfilerMiddleware
from uno.devtools.codegen import generate_model, generate_repository, generate_api
from uno.devtools.docs import DocGenerator
from uno.devtools.cli import cli

__all__ = [
    # Domain-driven design exports
    "DebugConfiguration", "DebugLevel",
    "ProfilerConfiguration", "ProfilerType", "ProfilerSessionId", "ProfileMetric",
    "MemoryProfilerSession", "MemoryMetric",
    "CodegenTemplate", "CodegenTemplateId", "CodegenType", "GeneratedCodeResult",
    "DocumentationAsset", "DocumentationId", "DiagramSpecification",
    
    "ProfilerSessionRepositoryProtocol",
    "MemoryProfilerSessionRepositoryProtocol",
    "CodegenTemplateRepositoryProtocol",
    "GeneratedCodeRepositoryProtocol",
    "DocumentationAssetRepositoryProtocol",
    
    "DebugServiceProtocol",
    "ProfilerServiceProtocol",
    "MemoryProfilerServiceProtocol",
    "CodegenServiceProtocol",
    "DocumentationServiceProtocol",
    
    "DevToolsProvider",
    "TestingDevToolsProvider",
    "devtools_router",
    
    # Legacy exports
    "setup_debugger",
    "DebugMiddleware", 
    "trace_function",
    "Profiler",
    "profile",
    "ProfilerMiddleware",
    "generate_model",
    "generate_repository", 
    "generate_api",
    "DocGenerator",
    "cli",
]