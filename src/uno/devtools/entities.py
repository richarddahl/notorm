"""
Domain entities for the DevTools module.

This module defines the domain entities, value objects, and aggregates for the DevTools module,
focusing on the various development tools provided by Uno including debugging, profiling,
code generation, and documentation.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, Protocol, TypeVar, Generic
from pathlib import Path
import uuid

from pydantic import BaseModel, Field

from uno.core.errors.result import Result, Success, Failure, ErrorDetails


# Value Objects

class ToolId(str):
    """Value object representing a unique identifier for a development tool."""
    
    def __init__(self, id_value: str):
        if not id_value:
            raise ValueError("ToolId cannot be empty")
        super().__init__()


class ProfilerSessionId(str):
    """Value object representing a unique identifier for a profiler session."""
    
    def __init__(self, id_value: str):
        if not id_value:
            raise ValueError("ProfilerSessionId cannot be empty")
        super().__init__()
    
    @classmethod
    def generate(cls) -> 'ProfilerSessionId':
        """Generate a new unique profiler session ID."""
        return cls(str(uuid.uuid4()))


class CodegenTemplateId(str):
    """Value object representing a unique identifier for a code generation template."""
    
    def __init__(self, id_value: str):
        if not id_value:
            raise ValueError("CodegenTemplateId cannot be empty")
        super().__init__()


class DocumentationId(str):
    """Value object representing a unique identifier for a documentation asset."""
    
    def __init__(self, id_value: str):
        if not id_value:
            raise ValueError("DocumentationId cannot be empty")
        super().__init__()


# Enums

class DebugLevel(Enum):
    """Debug level enum for controlling the verbosity of debugging output."""
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    DEBUG = auto()
    TRACE = auto()


class ProfilerType(Enum):
    """Type of profiler to use."""
    FUNCTION = auto()
    MEMORY = auto()
    SQL = auto()
    API = auto()
    FULL = auto()


class CodegenType(Enum):
    """Type of code to generate."""
    MODEL = auto()
    REPOSITORY = auto()
    SERVICE = auto()
    API = auto()
    CRUD = auto()
    PROJECT = auto()
    MODULE = auto()


# Domain Entities

@dataclass(frozen=True)
class DebugConfiguration:
    """Configuration settings for the debugger."""
    level: DebugLevel = DebugLevel.INFO
    trace_sql: bool = False
    trace_repository: bool = False
    enhance_errors: bool = True
    log_file: Optional[Path] = None
    
    def with_level(self, level: DebugLevel) -> 'DebugConfiguration':
        """Create a new configuration with an updated debug level."""
        return DebugConfiguration(
            level=level,
            trace_sql=self.trace_sql,
            trace_repository=self.trace_repository,
            enhance_errors=self.enhance_errors,
            log_file=self.log_file
        )
    
    def with_sql_tracing(self, enabled: bool) -> 'DebugConfiguration':
        """Create a new configuration with SQL tracing enabled or disabled."""
        return DebugConfiguration(
            level=self.level,
            trace_sql=enabled,
            trace_repository=self.trace_repository,
            enhance_errors=self.enhance_errors,
            log_file=self.log_file
        )


@dataclass
class ProfilerConfiguration:
    """Configuration settings for the profiler."""
    type: ProfilerType = ProfilerType.FUNCTION
    sample_rate: int = 100
    output_format: str = "html"
    output_path: Optional[Path] = None
    include_modules: List[str] = field(default_factory=list)
    exclude_modules: List[str] = field(default_factory=list)
    
    def with_type(self, profile_type: ProfilerType) -> 'ProfilerConfiguration':
        """Create a new configuration with an updated profiler type."""
        return ProfilerConfiguration(
            type=profile_type,
            sample_rate=self.sample_rate,
            output_format=self.output_format,
            output_path=self.output_path,
            include_modules=self.include_modules,
            exclude_modules=self.exclude_modules
        )


@dataclass
class ProfileMetric:
    """A single profiling metric for a function or component."""
    name: str
    calls: int
    total_time: float
    own_time: float
    avg_time: float
    max_time: float
    min_time: float
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    
    @property
    def is_hotspot(self) -> bool:
        """Determine if this metric represents a performance hotspot."""
        # Simple heuristic - if own_time is more than 10% of total time and
        # more than 100ms, consider it a hotspot
        return self.own_time > 0.1 and self.own_time > 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary representation."""
        return {
            "name": self.name,
            "calls": self.calls,
            "total_time": self.total_time,
            "own_time": self.own_time,
            "avg_time": self.avg_time,
            "max_time": self.max_time,
            "min_time": self.min_time,
            "parent": self.parent,
            "children": self.children,
            "is_hotspot": self.is_hotspot
        }


@dataclass
class ProfilerSession:
    """A profiling session containing performance metrics."""
    id: ProfilerSessionId
    start_time: datetime
    end_time: Optional[datetime] = None
    configuration: ProfilerConfiguration = field(default_factory=ProfilerConfiguration)
    metrics: List[ProfileMetric] = field(default_factory=list)
    
    @classmethod
    def create(cls, config: ProfilerConfiguration) -> 'ProfilerSession':
        """Create a new profiling session with the specified configuration."""
        return cls(
            id=ProfilerSessionId.generate(),
            start_time=datetime.now(UTC),
            configuration=config
        )
    
    def add_metric(self, metric: ProfileMetric) -> None:
        """Add a metric to this profiling session."""
        self.metrics.append(metric)
    
    def complete(self) -> None:
        """Mark the profiling session as complete."""
        self.end_time = datetime.now(UTC)
    
    @property
    def duration(self) -> Optional[float]:
        """Get the duration of the profiling session in seconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    def find_hotspots(self) -> List[ProfileMetric]:
        """Find performance hotspots in the profiling data."""
        return [metric for metric in self.metrics if metric.is_hotspot]


@dataclass
class MemoryMetric:
    """Memory usage metrics for a component or function."""
    name: str
    allocations: int
    bytes_allocated: int
    peak_memory: int
    leak_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary representation."""
        return {
            "name": self.name,
            "allocations": self.allocations,
            "bytes_allocated": self.bytes_allocated,
            "peak_memory": self.peak_memory,
            "leak_count": self.leak_count
        }


@dataclass
class MemoryProfilerSession:
    """A memory profiling session containing memory usage metrics."""
    id: ProfilerSessionId
    start_time: datetime
    end_time: Optional[datetime] = None
    configuration: ProfilerConfiguration = field(default_factory=ProfilerConfiguration)
    metrics: List[MemoryMetric] = field(default_factory=list)
    
    @classmethod
    def create(cls, config: ProfilerConfiguration) -> 'MemoryProfilerSession':
        """Create a new memory profiling session with the specified configuration."""
        return cls(
            id=ProfilerSessionId.generate(),
            start_time=datetime.now(UTC),
            configuration=config
        )
    
    def add_metric(self, metric: MemoryMetric) -> None:
        """Add a memory metric to this profiling session."""
        self.metrics.append(metric)
    
    def complete(self) -> None:
        """Mark the memory profiling session as complete."""
        self.end_time = datetime.now(UTC)


@dataclass
class CodegenTemplate:
    """A template for code generation."""
    id: CodegenTemplateId
    name: str
    type: CodegenType
    template_path: Path
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type.name,
            "template_path": str(self.template_path),
            "description": self.description
        }


@dataclass
class GeneratedCodeResult:
    """Result of a code generation operation."""
    template_id: CodegenTemplateId
    output_path: Path
    generated_code: str
    model_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary representation."""
        return {
            "template_id": str(self.template_id),
            "output_path": str(self.output_path),
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DocumentationAsset:
    """A documentation asset generated by the documentation tools."""
    id: DocumentationId
    title: str
    content: str
    path: Path
    format: str = "markdown"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the asset to a dictionary representation."""
        return {
            "id": str(self.id),
            "title": self.title,
            "path": str(self.path),
            "format": self.format,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DiagramSpecification:
    """Specification for generating a diagram."""
    title: str
    diagram_type: str
    include_modules: List[str] = field(default_factory=list)
    exclude_modules: List[str] = field(default_factory=list)
    output_format: str = "svg"
    output_path: Optional[Path] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the specification to a dictionary representation."""
        return {
            "title": self.title,
            "diagram_type": self.diagram_type,
            "include_modules": self.include_modules,
            "exclude_modules": self.exclude_modules,
            "output_format": self.output_format,
            "output_path": str(self.output_path) if self.output_path else None
        }


# Request/Response Models for API

class DebugConfigurationRequest(BaseModel):
    """Request model for configuring the debugger."""
    level: str = Field(default="INFO")
    trace_sql: bool = Field(default=False)
    trace_repository: bool = Field(default=False)
    enhance_errors: bool = Field(default=True)
    log_file: Optional[str] = Field(default=None)


class ProfilerConfigurationRequest(BaseModel):
    """Request model for configuring a profiler session."""
    type: str = Field(default="FUNCTION")
    sample_rate: int = Field(default=100, ge=1, le=1000)
    output_format: str = Field(default="html")
    output_path: Optional[str] = Field(default=None)
    include_modules: List[str] = Field(default_factory=list)
    exclude_modules: List[str] = Field(default_factory=list)


class CodegenRequest(BaseModel):
    """Request model for code generation."""
    type: str = Field(...)
    name: str = Field(...)
    output_path: str = Field(...)
    fields: Dict[str, str] = Field(default_factory=dict)
    template_id: Optional[str] = Field(default=None)
    options: Dict[str, Any] = Field(default_factory=dict)


class DiagramRequest(BaseModel):
    """Request model for diagram generation."""
    title: str = Field(...)
    diagram_type: str = Field(...)
    include_modules: List[str] = Field(default_factory=list)
    exclude_modules: List[str] = Field(default_factory=list)
    output_format: str = Field(default="svg")
    output_path: Optional[str] = Field(default=None)