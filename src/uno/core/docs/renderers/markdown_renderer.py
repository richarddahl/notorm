"""
Markdown renderer for documentation.

This module provides a renderer that transforms documentation schemas into
Markdown format for use in documentation sites.
"""

import json
import re
from typing import Dict, List, Any

from uno.core.docs.schema import (
    DocSchema, EndpointDoc, ModelDoc, TagDoc, DocStatus
)
from uno.core.docs.renderers.base import DocRenderer


class MarkdownRenderer(DocRenderer):
    """Renderer for Markdown documentation."""
    
    def render(self, schema: DocSchema, config: Any) -> Dict[str, str]:
        """
        Render documentation schema as Markdown.
        
        Args:
            schema: Documentation schema to render
            config: Configuration for rendering
            
        Returns:
            Dictionary of filenames to rendered content
        """
        result = {}
        
        # Render index page
        index_content = self._render_index(schema, config)
        result["index.md"] = index_content
        
        # Render endpoints by tag
        endpoints_by_tag = self._group_endpoints_by_tag(schema.endpoints)
        
        for tag, endpoints in endpoints_by_tag.items():
            tag_filename = f"endpoints/{self._slugify(tag)}.md"
            tag_content = self._render_tag_endpoints(tag, endpoints, schema, config)
            result[tag_filename] = tag_content
        
        # Render models by first letter
        models_by_letter = self._group_models_by_letter(schema.models)
        
        for letter, models in models_by_letter.items():
            letter_filename = f"models/{letter.lower()}.md"
            letter_content = self._render_letter_models(letter, models, schema, config)
            result[letter_filename] = letter_content
        
        return result
    
    def _render_index(self, schema: DocSchema, config: Any) -> str:
        """Render index page."""
        lines = [
            f"# {schema.title}",
            "",
            schema.description,
            "",
            f"API Version: {schema.version}",
            "",
            "## Endpoints",
            ""
        ]
        
        # Group endpoints by tag
        endpoints_by_tag = self._group_endpoints_by_tag(schema.endpoints)
        
        for tag in sorted(endpoints_by_tag.keys()):
            tag_slug = self._slugify(tag)
            tag_endpoints = endpoints_by_tag[tag]
            lines.append(f"- [{tag}](endpoints/{tag_slug}.md) ({len(tag_endpoints)} endpoints)")
        
        lines.extend([
            "",
            "## Models",
            ""
        ])
        
        # Group models by first letter
        models_by_letter = self._group_models_by_letter(schema.models)
        
        for letter in sorted(models_by_letter.keys()):
            letter_models = models_by_letter[letter]
            lines.append(f"- [{letter}](models/{letter.lower()}.md) ({len(letter_models)} models)")
        
        return "\n".join(lines)
    
    def _render_tag_endpoints(self, tag: str, endpoints: List[EndpointDoc], schema: DocSchema, config: Any) -> str:
        """Render endpoints for a tag."""
        lines = [
            f"# {tag} Endpoints",
            ""
        ]
        
        # Get tag description if available
        tag_obj = next((t for t in schema.tags if t.name == tag), None)
        if tag_obj and tag_obj.description:
            lines.extend([tag_obj.description, ""])
        
        lines.append("## Endpoints")
        
        # Sort endpoints by path
        sorted_endpoints = sorted(endpoints, key=lambda e: e.path)
        
        for endpoint in sorted_endpoints:
            status_badge = self._status_badge(endpoint.status)
            deprecated_badge = "![Deprecated](https://img.shields.io/badge/-Deprecated-red)" if endpoint.deprecated else ""
            
            badges = " ".join(filter(None, [status_badge, deprecated_badge]))
            if badges:
                badges = f" {badges}"
            
            lines.extend([
                "",
                f"### {endpoint.method} {endpoint.path}{badges}",
                "",
                endpoint.description,
                "",
                "**Operation ID:** " + (endpoint.operation_id or "N/A"),
                ""
            ])
            
            if endpoint.parameters:
                lines.extend([
                    "#### Parameters",
                    "",
                    "| Name | Type | Location | Required | Description |",
                    "| ---- | ---- | -------- | -------- | ----------- |"
                ])
                
                for param in endpoint.parameters:
                    required = "Yes" if param.required else "No"
                    lines.append(f"| {param.name} | {param.type} | {param.location.name} | {required} | {param.description} |")
                
                lines.append("")
            
            if endpoint.responses:
                lines.extend([
                    "#### Responses",
                    "",
                    "| Status | Description | Content Type |",
                    "| ------ | ----------- | ------------ |"
                ])
                
                for status_code, response in endpoint.responses.items():
                    lines.append(f"| {status_code} | {response['description']} | {response['content_type']} |")
                
                lines.append("")
            
            if endpoint.examples:
                lines.extend([
                    "#### Examples",
                    ""
                ])
                
                for example in endpoint.examples:
                    lines.extend([
                        f"##### {example.name}",
                        "",
                        example.description,
                        "",
                        "```json",
                        json.dumps(example.value, indent=2),
                        "```",
                        ""
                    ])
        
        return "\n".join(lines)
    
    def _render_letter_models(self, letter: str, models: List[ModelDoc], schema: DocSchema, config: Any) -> str:
        """Render models for a letter."""
        lines = [
            f"# Models - {letter}",
            ""
        ]
        
        # Sort models by name
        sorted_models = sorted(models, key=lambda m: m.name)
        
        for model in sorted_models:
            status_badge = self._status_badge(model.status)
            deprecated_badge = "![Deprecated](https://img.shields.io/badge/-Deprecated-red)" if model.deprecated else ""
            
            badges = " ".join(filter(None, [status_badge, deprecated_badge]))
            if badges:
                badges = f" {badges}"
            
            lines.extend([
                f"## {model.name}{badges}",
                "",
                model.description,
                ""
            ])
            
            if model.inherits_from:
                lines.extend([
                    "**Inherits from:** " + ", ".join(model.inherits_from),
                    ""
                ])
            
            if model.version:
                lines.extend([
                    f"**Version:** {model.version}",
                    ""
                ])
            
            if model.fields:
                lines.extend([
                    "### Fields",
                    "",
                    "| Name | Type | Required | Description |",
                    "| ---- | ---- | -------- | ----------- |"
                ])
                
                for field in model.fields:
                    required = "Yes" if field.required else "No"
                    lines.append(f"| {field.name} | {field.type} | {required} | {field.description} |")
                
                lines.append("")
            
            if model.examples:
                lines.extend([
                    "### Examples",
                    ""
                ])
                
                for example in model.examples:
                    lines.extend([
                        f"#### {example.name}",
                        "",
                        example.description,
                        "",
                        "```json",
                        json.dumps(example.value, indent=2),
                        "```",
                        ""
                    ])
        
        return "\n".join(lines)
    
    def _group_endpoints_by_tag(self, endpoints: List[EndpointDoc]) -> Dict[str, List[EndpointDoc]]:
        """Group endpoints by tag."""
        result = {}
        
        for endpoint in endpoints:
            # Use first tag, or "Default" if no tags
            tag = endpoint.tags[0] if endpoint.tags else "Default"
            
            if tag not in result:
                result[tag] = []
                
            result[tag].append(endpoint)
        
        return result
    
    def _group_models_by_letter(self, models: List[ModelDoc]) -> Dict[str, List[ModelDoc]]:
        """Group models by first letter."""
        result = {}
        
        for model in models:
            letter = model.name[0].upper()
            
            if letter not in result:
                result[letter] = []
                
            result[letter].append(model)
        
        return result
    
    def _slugify(self, text: str) -> str:
        """Convert text to slug format."""
        return text.lower().replace(" ", "-").replace("_", "-")
    
    def _status_badge(self, status: DocStatus) -> str:
        """Generate status badge."""
        if status == DocStatus.STABLE:
            return "![Stable](https://img.shields.io/badge/-Stable-brightgreen)"
        elif status == DocStatus.BETA:
            return "![Beta](https://img.shields.io/badge/-Beta-blue)"
        elif status == DocStatus.ALPHA:
            return "![Alpha](https://img.shields.io/badge/-Alpha-yellow)"
        elif status == DocStatus.DEPRECATED:
            return "![Deprecated](https://img.shields.io/badge/-Deprecated-red)"
        elif status == DocStatus.EXPERIMENTAL:
            return "![Experimental](https://img.shields.io/badge/-Experimental-orange)"
        return ""