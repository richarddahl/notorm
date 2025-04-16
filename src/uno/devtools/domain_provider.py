"""
Domain provider for the DevTools module.

This module contains the dependency injection configuration for the DevTools module,
wiring up repositories and services according to the domain-driven design approach.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Type, cast

import inject

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.devtools.entities import (
    ProfilerSession, ProfilerSessionId, ProfileMetric,
    MemoryProfilerSession, MemoryMetric,
    CodegenTemplate, CodegenTemplateId, GeneratedCodeResult,
    DocumentationAsset, DocumentationId
)
from uno.devtools.domain_repositories import (
    # Protocols
    ProfilerSessionRepositoryProtocol,
    MemoryProfilerSessionRepositoryProtocol,
    CodegenTemplateRepositoryProtocol,
    GeneratedCodeRepositoryProtocol,
    DocumentationAssetRepositoryProtocol,
    
    # Implementations
    InMemoryProfilerSessionRepository,
    InMemoryMemoryProfilerSessionRepository,
    InMemoryCodegenTemplateRepository,
    InMemoryGeneratedCodeRepository,
    InMemoryDocumentationAssetRepository,
    FileProfilerSessionRepository,
    FileCodegenTemplateRepository,
    FileDocumentationAssetRepository
)
from uno.devtools.domain_services import (
    # Protocols
    DebugServiceProtocol,
    ProfilerServiceProtocol,
    MemoryProfilerServiceProtocol,
    CodegenServiceProtocol,
    DocumentationServiceProtocol,
    
    # Implementations
    DebugService,
    ProfilerService,
    MemoryProfilerService,
    CodegenService,
    DocumentationService
)


class DevToolsProvider:
    """Dependency provider for the DevTools module."""
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        use_file_storage: bool = False
    ):
        """Initialize with configuration options.
        
        Args:
            storage_path: Path where file-based repositories will store data
            use_file_storage: Whether to use file-based repositories instead of in-memory
        """
        self.storage_path = storage_path or Path.home() / ".uno" / "devtools"
        self.use_file_storage = use_file_storage
        
        # Create the storage path if it doesn't exist and we're using file storage
        if use_file_storage and storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)
    
    def configure(self) -> None:
        """Configure dependency injection for DevTools module."""
        def config(binder: inject.Binder) -> None:
            # Configure repositories
            if self.use_file_storage:
                binder.bind(
                    ProfilerSessionRepositoryProtocol,
                    FileProfilerSessionRepository(self.storage_path)
                )
                binder.bind(
                    CodegenTemplateRepositoryProtocol,
                    FileCodegenTemplateRepository(self.storage_path)
                )
                binder.bind(
                    DocumentationAssetRepositoryProtocol,
                    FileDocumentationAssetRepository(self.storage_path)
                )
                
                # These don't have file-based implementations, so use in-memory
                binder.bind(
                    MemoryProfilerSessionRepositoryProtocol,
                    InMemoryMemoryProfilerSessionRepository()
                )
                binder.bind(
                    GeneratedCodeRepositoryProtocol,
                    InMemoryGeneratedCodeRepository()
                )
            else:
                # Use in-memory repositories
                binder.bind(
                    ProfilerSessionRepositoryProtocol,
                    InMemoryProfilerSessionRepository()
                )
                binder.bind(
                    MemoryProfilerSessionRepositoryProtocol,
                    InMemoryMemoryProfilerSessionRepository()
                )
                binder.bind(
                    CodegenTemplateRepositoryProtocol,
                    InMemoryCodegenTemplateRepository()
                )
                binder.bind(
                    GeneratedCodeRepositoryProtocol,
                    InMemoryGeneratedCodeRepository()
                )
                binder.bind(
                    DocumentationAssetRepositoryProtocol,
                    InMemoryDocumentationAssetRepository()
                )
            
            # Configure services
            binder.bind(DebugServiceProtocol, DebugService())
            binder.bind(
                ProfilerServiceProtocol,
                ProfilerService(inject.instance(ProfilerSessionRepositoryProtocol))
            )
            binder.bind(
                MemoryProfilerServiceProtocol,
                MemoryProfilerService(inject.instance(MemoryProfilerSessionRepositoryProtocol))
            )
            binder.bind(
                CodegenServiceProtocol,
                CodegenService(
                    inject.instance(CodegenTemplateRepositoryProtocol),
                    inject.instance(GeneratedCodeRepositoryProtocol)
                )
            )
            binder.bind(
                DocumentationServiceProtocol,
                DocumentationService(inject.instance(DocumentationAssetRepositoryProtocol))
            )
        
        inject.configure(config)
    
    @staticmethod
    def get_debug_service() -> DebugServiceProtocol:
        """Get the debug service instance."""
        return inject.instance(DebugServiceProtocol)
    
    @staticmethod
    def get_profiler_service() -> ProfilerServiceProtocol:
        """Get the profiler service instance."""
        return inject.instance(ProfilerServiceProtocol)
    
    @staticmethod
    def get_memory_profiler_service() -> MemoryProfilerServiceProtocol:
        """Get the memory profiler service instance."""
        return inject.instance(MemoryProfilerServiceProtocol)
    
    @staticmethod
    def get_codegen_service() -> CodegenServiceProtocol:
        """Get the code generation service instance."""
        return inject.instance(CodegenServiceProtocol)
    
    @staticmethod
    def get_documentation_service() -> DocumentationServiceProtocol:
        """Get the documentation service instance."""
        return inject.instance(DocumentationServiceProtocol)


class TestingDevToolsProvider:
    """Testing provider for the DevTools module."""
    
    @staticmethod
    def configure_with_mocks(
        debug_service: Optional[DebugServiceProtocol] = None,
        profiler_service: Optional[ProfilerServiceProtocol] = None,
        memory_profiler_service: Optional[MemoryProfilerServiceProtocol] = None,
        codegen_service: Optional[CodegenServiceProtocol] = None,
        documentation_service: Optional[DocumentationServiceProtocol] = None
    ) -> None:
        """Configure the DevTools module with mock implementations for testing.
        
        Args:
            debug_service: Mock debug service implementation
            profiler_service: Mock profiler service implementation
            memory_profiler_service: Mock memory profiler service implementation
            codegen_service: Mock code generation service implementation
            documentation_service: Mock documentation service implementation
        """
        def config(binder: inject.Binder) -> None:
            # Bind mock services if provided, otherwise bind real implementations with in-memory repositories
            if debug_service:
                binder.bind(DebugServiceProtocol, debug_service)
            else:
                binder.bind(DebugServiceProtocol, DebugService())
            
            if profiler_service:
                binder.bind(ProfilerServiceProtocol, profiler_service)
            else:
                binder.bind(
                    ProfilerSessionRepositoryProtocol,
                    InMemoryProfilerSessionRepository()
                )
                binder.bind(
                    ProfilerServiceProtocol,
                    ProfilerService(inject.instance(ProfilerSessionRepositoryProtocol))
                )
            
            if memory_profiler_service:
                binder.bind(MemoryProfilerServiceProtocol, memory_profiler_service)
            else:
                binder.bind(
                    MemoryProfilerSessionRepositoryProtocol,
                    InMemoryMemoryProfilerSessionRepository()
                )
                binder.bind(
                    MemoryProfilerServiceProtocol,
                    MemoryProfilerService(inject.instance(MemoryProfilerSessionRepositoryProtocol))
                )
            
            if codegen_service:
                binder.bind(CodegenServiceProtocol, codegen_service)
            else:
                binder.bind(
                    CodegenTemplateRepositoryProtocol,
                    InMemoryCodegenTemplateRepository()
                )
                binder.bind(
                    GeneratedCodeRepositoryProtocol,
                    InMemoryGeneratedCodeRepository()
                )
                binder.bind(
                    CodegenServiceProtocol,
                    CodegenService(
                        inject.instance(CodegenTemplateRepositoryProtocol),
                        inject.instance(GeneratedCodeRepositoryProtocol)
                    )
                )
            
            if documentation_service:
                binder.bind(DocumentationServiceProtocol, documentation_service)
            else:
                binder.bind(
                    DocumentationAssetRepositoryProtocol,
                    InMemoryDocumentationAssetRepository()
                )
                binder.bind(
                    DocumentationServiceProtocol,
                    DocumentationService(inject.instance(DocumentationAssetRepositoryProtocol))
                )
        
        inject.configure(config)
    
    @staticmethod
    def cleanup() -> None:
        """Clean up the testing configuration."""
        inject.clear()