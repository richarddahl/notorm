"""
Domain repositories for the DevTools module.

This module defines repository interfaces and implementations for the DevTools module,
providing data access for debugging tools, profiling sessions, code generation templates,
and documentation assets.
"""

from abc import ABC, abstractmethod
from datetime import datetime, UTC
from pathlib import Path
import json
import os
from typing import Dict, List, Optional, Protocol, Union, cast

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.devtools.entities import (
    ProfilerSession, ProfilerSessionId, ProfileMetric, MemoryProfilerSession,
    CodegenTemplate, CodegenTemplateId, GeneratedCodeResult,
    DocumentationAsset, DocumentationId, DiagramSpecification
)


# Repository Protocols

class ProfilerSessionRepositoryProtocol(Protocol):
    """Repository protocol for profiler sessions."""
    
    def save(self, session: ProfilerSession) -> Result[ProfilerSession, ErrorDetails]:
        """Save a profiler session."""
        ...
    
    def get_by_id(self, session_id: ProfilerSessionId) -> Result[ProfilerSession, ErrorDetails]:
        """Get a profiler session by ID."""
        ...
    
    def list_sessions(self, limit: int = 100) -> Result[List[ProfilerSession], ErrorDetails]:
        """List recent profiler sessions."""
        ...
    
    def delete(self, session_id: ProfilerSessionId) -> Result[None, ErrorDetails]:
        """Delete a profiler session by ID."""
        ...


class MemoryProfilerSessionRepositoryProtocol(Protocol):
    """Repository protocol for memory profiler sessions."""
    
    def save(self, session: MemoryProfilerSession) -> Result[MemoryProfilerSession, ErrorDetails]:
        """Save a memory profiler session."""
        ...
    
    def get_by_id(self, session_id: ProfilerSessionId) -> Result[MemoryProfilerSession, ErrorDetails]:
        """Get a memory profiler session by ID."""
        ...
    
    def list_sessions(self, limit: int = 100) -> Result[List[MemoryProfilerSession], ErrorDetails]:
        """List recent memory profiler sessions."""
        ...
    
    def delete(self, session_id: ProfilerSessionId) -> Result[None, ErrorDetails]:
        """Delete a memory profiler session by ID."""
        ...


class CodegenTemplateRepositoryProtocol(Protocol):
    """Repository protocol for code generation templates."""
    
    def save(self, template: CodegenTemplate) -> Result[CodegenTemplate, ErrorDetails]:
        """Save a code generation template."""
        ...
    
    def get_by_id(self, template_id: CodegenTemplateId) -> Result[CodegenTemplate, ErrorDetails]:
        """Get a code generation template by ID."""
        ...
    
    def list_templates(self) -> Result[List[CodegenTemplate], ErrorDetails]:
        """List all code generation templates."""
        ...
    
    def delete(self, template_id: CodegenTemplateId) -> Result[None, ErrorDetails]:
        """Delete a code generation template by ID."""
        ...


class GeneratedCodeRepositoryProtocol(Protocol):
    """Repository protocol for generated code results."""
    
    def save(self, result: GeneratedCodeResult) -> Result[GeneratedCodeResult, ErrorDetails]:
        """Save a generated code result."""
        ...
    
    def list_by_model_name(self, model_name: str) -> Result[List[GeneratedCodeResult], ErrorDetails]:
        """List generated code results by model name."""
        ...


class DocumentationAssetRepositoryProtocol(Protocol):
    """Repository protocol for documentation assets."""
    
    def save(self, asset: DocumentationAsset) -> Result[DocumentationAsset, ErrorDetails]:
        """Save a documentation asset."""
        ...
    
    def get_by_id(self, asset_id: DocumentationId) -> Result[DocumentationAsset, ErrorDetails]:
        """Get a documentation asset by ID."""
        ...
    
    def list_assets(self) -> Result[List[DocumentationAsset], ErrorDetails]:
        """List all documentation assets."""
        ...
    
    def delete(self, asset_id: DocumentationId) -> Result[None, ErrorDetails]:
        """Delete a documentation asset by ID."""
        ...


# In-Memory Repository Implementations

class InMemoryProfilerSessionRepository:
    """In-memory implementation of the profiler session repository."""
    
    def __init__(self):
        self._sessions: Dict[str, ProfilerSession] = {}
    
    def save(self, session: ProfilerSession) -> Result[ProfilerSession, ErrorDetails]:
        """Save a profiler session."""
        self._sessions[str(session.id)] = session
        return Success(session)
    
    def get_by_id(self, session_id: ProfilerSessionId) -> Result[ProfilerSession, ErrorDetails]:
        """Get a profiler session by ID."""
        session = self._sessions.get(str(session_id))
        if session is None:
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_NOT_FOUND",
                message=f"Profiler session with ID {session_id} not found"
            ))
        return Success(session)
    
    def list_sessions(self, limit: int = 100) -> Result[List[ProfilerSession], ErrorDetails]:
        """List recent profiler sessions."""
        sessions = list(self._sessions.values())
        # Sort by start time, most recent first
        sessions.sort(key=lambda s: s.start_time, reverse=True)
        return Success(sessions[:limit])
    
    def delete(self, session_id: ProfilerSessionId) -> Result[None, ErrorDetails]:
        """Delete a profiler session by ID."""
        if str(session_id) not in self._sessions:
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_NOT_FOUND",
                message=f"Profiler session with ID {session_id} not found"
            ))
        del self._sessions[str(session_id)]
        return Success(None)


class InMemoryMemoryProfilerSessionRepository:
    """In-memory implementation of the memory profiler session repository."""
    
    def __init__(self):
        self._sessions: Dict[str, MemoryProfilerSession] = {}
    
    def save(self, session: MemoryProfilerSession) -> Result[MemoryProfilerSession, ErrorDetails]:
        """Save a memory profiler session."""
        self._sessions[str(session.id)] = session
        return Success(session)
    
    def get_by_id(self, session_id: ProfilerSessionId) -> Result[MemoryProfilerSession, ErrorDetails]:
        """Get a memory profiler session by ID."""
        session = self._sessions.get(str(session_id))
        if session is None:
            return Failure(ErrorDetails(
                code="MEMORY_PROFILER_SESSION_NOT_FOUND",
                message=f"Memory profiler session with ID {session_id} not found"
            ))
        return Success(session)
    
    def list_sessions(self, limit: int = 100) -> Result[List[MemoryProfilerSession], ErrorDetails]:
        """List recent memory profiler sessions."""
        sessions = list(self._sessions.values())
        # Sort by start time, most recent first
        sessions.sort(key=lambda s: s.start_time, reverse=True)
        return Success(sessions[:limit])
    
    def delete(self, session_id: ProfilerSessionId) -> Result[None, ErrorDetails]:
        """Delete a memory profiler session by ID."""
        if str(session_id) not in self._sessions:
            return Failure(ErrorDetails(
                code="MEMORY_PROFILER_SESSION_NOT_FOUND",
                message=f"Memory profiler session with ID {session_id} not found"
            ))
        del self._sessions[str(session_id)]
        return Success(None)


class InMemoryCodegenTemplateRepository:
    """In-memory implementation of the code generation template repository."""
    
    def __init__(self):
        self._templates: Dict[str, CodegenTemplate] = {}
    
    def save(self, template: CodegenTemplate) -> Result[CodegenTemplate, ErrorDetails]:
        """Save a code generation template."""
        self._templates[str(template.id)] = template
        return Success(template)
    
    def get_by_id(self, template_id: CodegenTemplateId) -> Result[CodegenTemplate, ErrorDetails]:
        """Get a code generation template by ID."""
        template = self._templates.get(str(template_id))
        if template is None:
            return Failure(ErrorDetails(
                code="CODEGEN_TEMPLATE_NOT_FOUND",
                message=f"Code generation template with ID {template_id} not found"
            ))
        return Success(template)
    
    def list_templates(self) -> Result[List[CodegenTemplate], ErrorDetails]:
        """List all code generation templates."""
        return Success(list(self._templates.values()))
    
    def delete(self, template_id: CodegenTemplateId) -> Result[None, ErrorDetails]:
        """Delete a code generation template by ID."""
        if str(template_id) not in self._templates:
            return Failure(ErrorDetails(
                code="CODEGEN_TEMPLATE_NOT_FOUND",
                message=f"Code generation template with ID {template_id} not found"
            ))
        del self._templates[str(template_id)]
        return Success(None)


class InMemoryGeneratedCodeRepository:
    """In-memory implementation of the generated code result repository."""
    
    def __init__(self):
        self._results: List[GeneratedCodeResult] = []
    
    def save(self, result: GeneratedCodeResult) -> Result[GeneratedCodeResult, ErrorDetails]:
        """Save a generated code result."""
        self._results.append(result)
        return Success(result)
    
    def list_by_model_name(self, model_name: str) -> Result[List[GeneratedCodeResult], ErrorDetails]:
        """List generated code results by model name."""
        results = [r for r in self._results if r.model_name == model_name]
        return Success(results)


class InMemoryDocumentationAssetRepository:
    """In-memory implementation of the documentation asset repository."""
    
    def __init__(self):
        self._assets: Dict[str, DocumentationAsset] = {}
    
    def save(self, asset: DocumentationAsset) -> Result[DocumentationAsset, ErrorDetails]:
        """Save a documentation asset."""
        self._assets[str(asset.id)] = asset
        return Success(asset)
    
    def get_by_id(self, asset_id: DocumentationId) -> Result[DocumentationAsset, ErrorDetails]:
        """Get a documentation asset by ID."""
        asset = self._assets.get(str(asset_id))
        if asset is None:
            return Failure(ErrorDetails(
                code="DOCUMENTATION_ASSET_NOT_FOUND",
                message=f"Documentation asset with ID {asset_id} not found"
            ))
        return Success(asset)
    
    def list_assets(self) -> Result[List[DocumentationAsset], ErrorDetails]:
        """List all documentation assets."""
        return Success(list(self._assets.values()))
    
    def delete(self, asset_id: DocumentationId) -> Result[None, ErrorDetails]:
        """Delete a documentation asset by ID."""
        if str(asset_id) not in self._assets:
            return Failure(ErrorDetails(
                code="DOCUMENTATION_ASSET_NOT_FOUND",
                message=f"Documentation asset with ID {asset_id} not found"
            ))
        del self._assets[str(asset_id)]
        return Success(None)


# File-Based Repository Implementations

class FileProfilerSessionRepository:
    """File-based implementation of the profiler session repository."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.sessions_path = base_path / "profiler_sessions"
        os.makedirs(self.sessions_path, exist_ok=True)
    
    def _session_to_dict(self, session: ProfilerSession) -> Dict:
        """Convert a profiler session to a dictionary for serialization."""
        return {
            "id": str(session.id),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "configuration": {
                "type": session.configuration.type.name,
                "sample_rate": session.configuration.sample_rate,
                "output_format": session.configuration.output_format,
                "output_path": str(session.configuration.output_path) if session.configuration.output_path else None,
                "include_modules": session.configuration.include_modules,
                "exclude_modules": session.configuration.exclude_modules
            },
            "metrics": [metric.to_dict() for metric in session.metrics]
        }
    
    def save(self, session: ProfilerSession) -> Result[ProfilerSession, ErrorDetails]:
        """Save a profiler session."""
        try:
            file_path = self.sessions_path / f"{session.id}.json"
            with open(file_path, 'w') as f:
                json.dump(self._session_to_dict(session), f, indent=2)
            return Success(session)
        except Exception as e:
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_SAVE_ERROR",
                message=f"Error saving profiler session: {str(e)}"
            ))
    
    def get_by_id(self, session_id: ProfilerSessionId) -> Result[ProfilerSession, ErrorDetails]:
        """Get a profiler session by ID."""
        file_path = self.sessions_path / f"{session_id}.json"
        if not file_path.exists():
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_NOT_FOUND",
                message=f"Profiler session with ID {session_id} not found"
            ))
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # This is a simplified deserialization - a full implementation would need
            # to properly reconstruct the session from the JSON data
            # In a real implementation, we would deserialize the JSON back to the correct objects
            return Failure(ErrorDetails(
                code="NOT_IMPLEMENTED",
                message="Deserialization of profiler sessions from file is not yet implemented"
            ))
        except Exception as e:
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_LOAD_ERROR",
                message=f"Error loading profiler session: {str(e)}"
            ))
    
    def list_sessions(self, limit: int = 100) -> Result[List[ProfilerSession], ErrorDetails]:
        """List recent profiler sessions."""
        try:
            session_files = list(self.sessions_path.glob("*.json"))
            # Sort by modification time, most recent first
            session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            sessions = []
            for file_path in session_files[:limit]:
                # In a real implementation, we would deserialize the JSON to ProfilerSession objects
                # This is simplified for illustration
                pass
            
            # Since we're not fully implementing the deserialization, return a failure
            return Failure(ErrorDetails(
                code="NOT_IMPLEMENTED",
                message="Listing profiler sessions from file is not yet implemented"
            ))
        except Exception as e:
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_LIST_ERROR",
                message=f"Error listing profiler sessions: {str(e)}"
            ))
    
    def delete(self, session_id: ProfilerSessionId) -> Result[None, ErrorDetails]:
        """Delete a profiler session by ID."""
        file_path = self.sessions_path / f"{session_id}.json"
        if not file_path.exists():
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_NOT_FOUND",
                message=f"Profiler session with ID {session_id} not found"
            ))
        
        try:
            os.remove(file_path)
            return Success(None)
        except Exception as e:
            return Failure(ErrorDetails(
                code="PROFILER_SESSION_DELETE_ERROR",
                message=f"Error deleting profiler session: {str(e)}"
            ))


class FileCodegenTemplateRepository:
    """File-based implementation of the code generation template repository."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.templates_path = base_path / "codegen_templates"
        os.makedirs(self.templates_path, exist_ok=True)
    
    def save(self, template: CodegenTemplate) -> Result[CodegenTemplate, ErrorDetails]:
        """Save a code generation template."""
        try:
            file_path = self.templates_path / f"{template.id}.json"
            with open(file_path, 'w') as f:
                json.dump(template.to_dict(), f, indent=2)
            return Success(template)
        except Exception as e:
            return Failure(ErrorDetails(
                code="CODEGEN_TEMPLATE_SAVE_ERROR",
                message=f"Error saving code generation template: {str(e)}"
            ))
    
    def get_by_id(self, template_id: CodegenTemplateId) -> Result[CodegenTemplate, ErrorDetails]:
        """Get a code generation template by ID."""
        # Implementation would deserialize from JSON to CodegenTemplate
        # This is simplified for illustration
        return Failure(ErrorDetails(
            code="NOT_IMPLEMENTED",
            message="Getting code generation templates from file is not yet implemented"
        ))
    
    def list_templates(self) -> Result[List[CodegenTemplate], ErrorDetails]:
        """List all code generation templates."""
        # Implementation would list and deserialize all templates
        # This is simplified for illustration
        return Failure(ErrorDetails(
            code="NOT_IMPLEMENTED",
            message="Listing code generation templates from file is not yet implemented"
        ))
    
    def delete(self, template_id: CodegenTemplateId) -> Result[None, ErrorDetails]:
        """Delete a code generation template by ID."""
        file_path = self.templates_path / f"{template_id}.json"
        if not file_path.exists():
            return Failure(ErrorDetails(
                code="CODEGEN_TEMPLATE_NOT_FOUND",
                message=f"Code generation template with ID {template_id} not found"
            ))
        
        try:
            os.remove(file_path)
            return Success(None)
        except Exception as e:
            return Failure(ErrorDetails(
                code="CODEGEN_TEMPLATE_DELETE_ERROR",
                message=f"Error deleting code generation template: {str(e)}"
            ))


class FileDocumentationAssetRepository:
    """File-based implementation of the documentation asset repository."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.assets_path = base_path / "documentation_assets"
        os.makedirs(self.assets_path, exist_ok=True)
    
    def save(self, asset: DocumentationAsset) -> Result[DocumentationAsset, ErrorDetails]:
        """Save a documentation asset."""
        try:
            # Save metadata
            metadata_path = self.assets_path / f"{asset.id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(asset.to_dict(), f, indent=2)
            
            # Save content
            content_path = self.assets_path / f"{asset.id}.{asset.format}"
            with open(content_path, 'w') as f:
                f.write(asset.content)
            
            return Success(asset)
        except Exception as e:
            return Failure(ErrorDetails(
                code="DOCUMENTATION_ASSET_SAVE_ERROR",
                message=f"Error saving documentation asset: {str(e)}"
            ))
    
    def get_by_id(self, asset_id: DocumentationId) -> Result[DocumentationAsset, ErrorDetails]:
        """Get a documentation asset by ID."""
        # Implementation would load metadata and content from files
        # This is simplified for illustration
        return Failure(ErrorDetails(
            code="NOT_IMPLEMENTED",
            message="Getting documentation assets from file is not yet implemented"
        ))
    
    def list_assets(self) -> Result[List[DocumentationAsset], ErrorDetails]:
        """List all documentation assets."""
        # Implementation would list and load all assets
        # This is simplified for illustration
        return Failure(ErrorDetails(
            code="NOT_IMPLEMENTED",
            message="Listing documentation assets from file is not yet implemented"
        ))
    
    def delete(self, asset_id: DocumentationId) -> Result[None, ErrorDetails]:
        """Delete a documentation asset by ID."""
        metadata_path = self.assets_path / f"{asset_id}.json"
        if not metadata_path.exists():
            return Failure(ErrorDetails(
                code="DOCUMENTATION_ASSET_NOT_FOUND",
                message=f"Documentation asset with ID {asset_id} not found"
            ))
        
        try:
            # Need to determine the format to delete the content file
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            content_path = self.assets_path / f"{asset_id}.{metadata.get('format', 'md')}"
            
            # Delete both files
            if metadata_path.exists():
                os.remove(metadata_path)
            if content_path.exists():
                os.remove(content_path)
            
            return Success(None)
        except Exception as e:
            return Failure(ErrorDetails(
                code="DOCUMENTATION_ASSET_DELETE_ERROR",
                message=f"Error deleting documentation asset: {str(e)}"
            ))