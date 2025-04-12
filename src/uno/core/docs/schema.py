"""
Schema definitions for documentation generation.

This module defines the data structures that represent documentation
components such as endpoints, parameters, models, fields, and examples.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union, Set


class DocStatus(Enum):
    """Status of documentation component."""
    STABLE = auto()
    BETA = auto()
    ALPHA = auto()
    DEPRECATED = auto()
    EXPERIMENTAL = auto()


class ParameterLocation(Enum):
    """Locations where parameters can be specified."""
    PATH = auto()
    QUERY = auto()
    HEADER = auto()
    COOKIE = auto()
    BODY = auto()


@dataclass
class ExampleDoc:
    """Documentation for an example request or response."""
    name: str
    description: str
    value: Any
    format: Optional[str] = None
    is_response: bool = False


@dataclass
class ParameterDoc:
    """Documentation for an API endpoint parameter."""
    name: str
    description: str
    type: str
    location: ParameterLocation
    required: bool = True
    default: Any = None
    enum_values: Optional[List[Any]] = None
    deprecated: bool = False
    pattern: Optional[str] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    format: Optional[str] = None
    example: Optional[Any] = None
    examples: List[ExampleDoc] = field(default_factory=list)
    references: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResponseDoc:
    """Documentation for an API endpoint response."""
    status_code: int
    description: str
    content_type: str
    schema: Optional[str] = None
    examples: List[ExampleDoc] = field(default_factory=list)
    headers: Dict[str, ParameterDoc] = field(default_factory=dict)


@dataclass
class EndpointDoc:
    """Documentation for an API endpoint."""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[ParameterDoc] = field(default_factory=list)
    request_body: Optional[ParameterDoc] = None
    responses: Dict[int, ResponseDoc] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    operation_id: Optional[str] = None
    examples: List[ExampleDoc] = field(default_factory=list)
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    status: DocStatus = DocStatus.STABLE
    handlers: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldDoc:
    """Documentation for a model field."""
    name: str
    description: str
    type: str
    required: bool = True
    default: Any = None
    enum_values: Optional[List[Any]] = None
    deprecated: bool = False
    pattern: Optional[str] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    format: Optional[str] = None
    example: Optional[Any] = None
    examples: List[ExampleDoc] = field(default_factory=list)
    references: Dict[str, str] = field(default_factory=dict)
    nullable: bool = False
    read_only: bool = False
    write_only: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelDoc:
    """Documentation for a data model."""
    name: str
    description: str
    fields: List[FieldDoc] = field(default_factory=list)
    examples: List[ExampleDoc] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    status: DocStatus = DocStatus.STABLE
    version: Optional[str] = None
    source_file: Optional[str] = None
    inherits_from: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TagDoc:
    """Documentation for a tag used to group endpoints."""
    name: str
    description: str
    external_docs: Optional[Dict[str, str]] = None


@dataclass
class SecuritySchemeDoc:
    """Documentation for a security scheme."""
    name: str
    type: str
    description: str
    scheme: Optional[str] = None
    bearer_format: Optional[str] = None
    flows: Optional[Dict[str, Any]] = None
    open_id_connect_url: Optional[str] = None
    in_param: Optional[ParameterLocation] = None


@dataclass
class DocSchema:
    """Complete schema for API documentation."""
    title: str
    description: str
    version: str
    endpoints: List[EndpointDoc] = field(default_factory=list)
    models: List[ModelDoc] = field(default_factory=list)
    tags: List[TagDoc] = field(default_factory=list)
    security_schemes: List[SecuritySchemeDoc] = field(default_factory=list)
    servers: Optional[List[Dict[str, str]]] = None
    contact: Optional[Dict[str, str]] = None
    license: Optional[Dict[str, str]] = None
    terms_of_service: Optional[str] = None
    external_docs: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentReference:
    """Reference to a documentation component."""
    type: str  # "model", "endpoint", "parameter", "field", "example", etc.
    id: str
    path: Optional[str] = None