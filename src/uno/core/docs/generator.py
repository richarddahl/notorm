"""
Documentation generator for Uno components.

This module provides the core functionality for discovering, extracting,
and rendering documentation for various components in the Uno framework.
"""

import os
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Type, Union

from uno.core.docs.schema import DocSchema
from uno.core.docs.extractors import DocExtractor
from uno.core.docs.renderers import DocRenderer
from uno.core.docs.discovery import DocDiscovery


class DocFormat(Enum):
    """Supported documentation formats."""
    MARKDOWN = auto()
    OPENAPI = auto()
    HTML = auto()
    ASCIIDOC = auto()
    JSON = auto()


@dataclass
class DocGeneratorConfig:
    """Configuration for documentation generator."""
    title: str = "API Documentation"
    description: str = "Generated API documentation"
    version: str = "1.0.0"
    formats: List[DocFormat] = field(default_factory=lambda: [DocFormat.MARKDOWN, DocFormat.OPENAPI])
    output_dir: str = "docs/api"
    include_source_links: bool = True
    include_examples: bool = True
    example_depth: int = 2
    include_internal: bool = False
    include_deprecated: bool = True
    include_beta: bool = True
    include_alpha: bool = True
    include_experimental: bool = True
    modules_to_document: List[str] = field(default_factory=list)
    url_base: Optional[str] = None
    logo_url: Optional[str] = None
    css_urls: List[str] = field(default_factory=list)
    js_urls: List[str] = field(default_factory=list)
    extra_templates: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocGenerator:
    """
    Generator for comprehensive API documentation.
    
    This class orchestrates the process of discovering components,
    extracting documentation, and rendering it in various formats.
    """
    
    def __init__(self, config: DocGeneratorConfig):
        """
        Initialize the documentation generator.
        
        Args:
            config: Configuration for the documentation generator
        """
        self.config = config
        self.logger = logging.getLogger("uno.docs.generator")
        self.discovery = DocDiscovery()
        self.extractors: Dict[str, DocExtractor] = {}
        self.renderers: Dict[DocFormat, DocRenderer] = {}
        
    def register_extractor(self, component_type: str, extractor: DocExtractor) -> None:
        """
        Register an extractor for a specific component type.
        
        Args:
            component_type: Type of component (e.g., "model", "endpoint")
            extractor: Extractor instance for the component type
        """
        self.extractors[component_type] = extractor
        
    def register_renderer(self, format: DocFormat, renderer: DocRenderer) -> None:
        """
        Register a renderer for a specific documentation format.
        
        Args:
            format: Format to render (e.g., MARKDOWN, OPENAPI)
            renderer: Renderer instance for the format
        """
        self.renderers[format] = renderer
    
    def discover(self) -> Dict[str, List[Any]]:
        """
        Discover components to document.
        
        Returns:
            Dictionary of discovered components by type
        """
        return self.discovery.discover(self.config.modules_to_document)
    
    def extract(self, discovered_components: Dict[str, List[Any]]) -> DocSchema:
        """
        Extract documentation from discovered components.
        
        Args:
            discovered_components: Components discovered by the discovery process
            
        Returns:
            Completed documentation schema
        """
        schema = DocSchema(
            title=self.config.title,
            description=self.config.description,
            version=self.config.version
        )
        
        for component_type, components in discovered_components.items():
            if component_type not in self.extractors:
                self.logger.warning(f"No extractor registered for component type: {component_type}")
                continue
                
            extractor = self.extractors[component_type]
            extracted_docs = extractor.extract(components, self.config)
            
            if component_type == "endpoint":
                schema.endpoints.extend(extracted_docs)
            elif component_type == "model":
                schema.models.extend(extracted_docs)
            elif component_type == "tag":
                schema.tags.extend(extracted_docs)
            elif component_type == "security_scheme":
                schema.security_schemes.extend(extracted_docs)
        
        return schema
    
    def render(self, schema: DocSchema) -> Dict[str, Dict[str, str]]:
        """
        Render documentation in all configured formats.
        
        Args:
            schema: Documentation schema to render
            
        Returns:
            Dictionary of rendered documentation by format and filename
        """
        results = {}
        
        for format in self.config.formats:
            if format not in self.renderers:
                self.logger.warning(f"No renderer registered for format: {format}")
                continue
                
            renderer = self.renderers[format]
            rendered_docs = renderer.render(schema, self.config)
            results[format.name] = rendered_docs
            
        return results
    
    def save(self, rendered_docs: Dict[str, Dict[str, str]]) -> None:
        """
        Save rendered documentation to the output directory.
        
        Args:
            rendered_docs: Rendered documentation by format and filename
        """
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        for format_name, docs in rendered_docs.items():
            format_dir = os.path.join(self.config.output_dir, format_name.lower())
            os.makedirs(format_dir, exist_ok=True)
            
            for filename, content in docs.items():
                filepath = os.path.join(format_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, "w") as f:
                    f.write(content)
                    
                self.logger.info(f"Saved documentation to: {filepath}")
    
    def generate(self) -> Dict[str, Dict[str, str]]:
        """
        Generate documentation for discovered components.
        
        Returns:
            Dictionary of rendered documentation by format and filename
        """
        discovered_components = self.discover()
        self.logger.info(f"Discovered components: {', '.join(f'{k}: {len(v)}' for k, v in discovered_components.items())}")
        
        schema = self.extract(discovered_components)
        self.logger.info(f"Extracted documentation: {len(schema.endpoints)} endpoints, {len(schema.models)} models")
        
        rendered_docs = self.render(schema)
        self.logger.info(f"Rendered documentation in formats: {', '.join(rendered_docs.keys())}")
        
        self.save(rendered_docs)
        
        return rendered_docs


def generate_docs(config: DocGeneratorConfig) -> Dict[str, Dict[str, str]]:
    """
    Generate documentation based on the provided configuration.
    
    This is a convenience function that sets up a properly configured
    DocGenerator with default extractors and renderers.
    
    Args:
        config: Configuration for documentation generation
        
    Returns:
        Dictionary of rendered documentation by format and filename
    """
    from uno.core.docs.extractors import (
        ModelExtractor, EndpointExtractor, SchemaExtractor
    )
    from uno.core.docs.renderers import (
        MarkdownRenderer, OpenApiRenderer, HtmlRenderer, AsciiDocRenderer
    )
    
    generator = DocGenerator(config)
    
    # Register extractors
    generator.register_extractor("model", ModelExtractor())
    generator.register_extractor("endpoint", EndpointExtractor())
    generator.register_extractor("schema", SchemaExtractor())
    
    # Register renderers
    generator.register_renderer(DocFormat.MARKDOWN, MarkdownRenderer())
    generator.register_renderer(DocFormat.OPENAPI, OpenApiRenderer())
    generator.register_renderer(DocFormat.HTML, HtmlRenderer())
    generator.register_renderer(DocFormat.ASCIIDOC, AsciiDocRenderer())
    
    return generator.generate()