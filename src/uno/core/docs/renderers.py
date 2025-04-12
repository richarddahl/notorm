"""
Renderers for documentation formats.

This module provides renderers that transform documentation schemas
into various formats such as Markdown, OpenAPI, HTML, and AsciiDoc.
"""

import os
import json
import yaml
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from uno.core.docs.schema import (
    DocSchema, EndpointDoc, ModelDoc, TagDoc, SecuritySchemeDoc,
    ParameterDoc, FieldDoc, ExampleDoc, DocStatus, ParameterLocation
)


class DocRenderer(ABC):
    """Base class for documentation renderers."""
    
    @abstractmethod
    def render(self, schema: DocSchema, config: Any) -> Dict[str, str]:
        """
        Render documentation schema into the target format.
        
        Args:
            schema: Documentation schema to render
            config: Configuration for rendering
            
        Returns:
            Dictionary of filenames to rendered content
        """
        pass


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


class OpenApiRenderer(DocRenderer):
    """Renderer for OpenAPI documentation."""
    
    def render(self, schema: DocSchema, config: Any) -> Dict[str, str]:
        """
        Render documentation schema as OpenAPI specification.
        
        Args:
            schema: Documentation schema to render
            config: Configuration for rendering
            
        Returns:
            Dictionary of filenames to rendered content
        """
        openapi = {
            "openapi": "3.0.3",
            "info": {
                "title": schema.title,
                "description": schema.description,
                "version": schema.version
            },
            "paths": self._render_paths(schema),
            "components": {
                "schemas": self._render_schemas(schema),
                "securitySchemes": self._render_security_schemes(schema)
            }
        }
        
        # Add contact info if available
        if schema.contact:
            openapi["info"]["contact"] = schema.contact
        
        # Add license info if available
        if schema.license:
            openapi["info"]["license"] = schema.license
        
        # Add terms of service if available
        if schema.terms_of_service:
            openapi["info"]["termsOfService"] = schema.terms_of_service
        
        # Add servers if available
        if schema.servers:
            openapi["servers"] = schema.servers
        
        # Add tags with descriptions
        if schema.tags:
            openapi["tags"] = [
                {"name": tag.name, "description": tag.description}
                for tag in schema.tags
            ]
        
        # Render as YAML and JSON
        yaml_content = yaml.dump(openapi, sort_keys=False)
        json_content = json.dumps(openapi, indent=2)
        
        return {
            "openapi.yaml": yaml_content,
            "openapi.json": json_content
        }
    
    def _render_paths(self, schema: DocSchema) -> Dict[str, Any]:
        """Render paths section of OpenAPI spec."""
        paths = {}
        
        for endpoint in schema.endpoints:
            # Initialize path if not exists
            if endpoint.path not in paths:
                paths[endpoint.path] = {}
            
            # Convert to lowercase method name
            method = endpoint.method.lower()
            
            # Create operation object
            operation = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "responses": self._render_responses(endpoint)
            }
            
            # Add operation ID if available
            if endpoint.operation_id:
                operation["operationId"] = endpoint.operation_id
            
            # Add tags if available
            if endpoint.tags:
                operation["tags"] = endpoint.tags
            
            # Add deprecated flag if true
            if endpoint.deprecated:
                operation["deprecated"] = True
            
            # Add parameters
            path_params = []
            query_params = []
            header_params = []
            cookie_params = []
            
            for param in endpoint.parameters:
                if param.location == ParameterLocation.BODY:
                    # Handle request body
                    operation["requestBody"] = self._render_request_body(param)
                else:
                    # Handle other parameter types
                    openapi_param = self._render_parameter(param)
                    
                    if param.location == ParameterLocation.PATH:
                        path_params.append(openapi_param)
                    elif param.location == ParameterLocation.QUERY:
                        query_params.append(openapi_param)
                    elif param.location == ParameterLocation.HEADER:
                        header_params.append(openapi_param)
                    elif param.location == ParameterLocation.COOKIE:
                        cookie_params.append(openapi_param)
            
            # Combine all parameters
            all_params = path_params + query_params + header_params + cookie_params
            if all_params:
                operation["parameters"] = all_params
            
            # Add security if available
            if endpoint.security:
                operation["security"] = endpoint.security
            
            # Add the operation to the path
            paths[endpoint.path][method] = operation
        
        return paths
    
    def _render_parameter(self, param: ParameterDoc) -> Dict[str, Any]:
        """Render parameter for OpenAPI spec."""
        result = {
            "name": param.name,
            "in": param.location.name.lower(),
            "description": param.description,
            "required": param.required,
            "schema": self._render_schema_type(param)
        }
        
        # Add deprecated flag if true
        if param.deprecated:
            result["deprecated"] = True
        
        # Add example if available
        if param.example is not None:
            result["example"] = param.example
        
        # Add examples if available
        if param.examples:
            result["examples"] = {
                example.name: {
                    "value": example.value,
                    "summary": example.description
                }
                for example in param.examples
            }
        
        return result
    
    def _render_request_body(self, param: ParameterDoc) -> Dict[str, Any]:
        """Render request body for OpenAPI spec."""
        result = {
            "description": param.description,
            "required": param.required,
            "content": {
                "application/json": {
                    "schema": self._render_schema_type(param)
                }
            }
        }
        
        # Add example if available
        if param.example is not None:
            result["content"]["application/json"]["example"] = param.example
        
        # Add examples if available
        if param.examples:
            result["content"]["application/json"]["examples"] = {
                example.name: {
                    "value": example.value,
                    "summary": example.description
                }
                for example in param.examples
            }
        
        return result
    
    def _render_responses(self, endpoint: EndpointDoc) -> Dict[str, Any]:
        """Render responses for OpenAPI spec."""
        result = {}
        
        # Ensure at least a 200 response is present
        if not endpoint.responses or 200 not in endpoint.responses:
            result["200"] = {
                "description": "Successful response"
            }
        
        # Add endpoint responses
        for status_code, response_info in endpoint.responses.items():
            result[str(status_code)] = {
                "description": response_info["description"],
                "content": {
                    response_info["content_type"]: {}
                }
            }
            
            # Add schema if available
            if "schema" in response_info and response_info["schema"]:
                result[str(status_code)]["content"][response_info["content_type"]]["schema"] = {
                    "$ref": f"#/components/schemas/{response_info['schema']}"
                }
        
        return result
    
    def _render_schemas(self, schema: DocSchema) -> Dict[str, Any]:
        """Render schemas section of OpenAPI spec."""
        result = {}
        
        for model in schema.models:
            result[model.name] = self._render_model_schema(model)
        
        return result
    
    def _render_model_schema(self, model: ModelDoc) -> Dict[str, Any]:
        """Render model schema for OpenAPI spec."""
        result = {
            "type": "object",
            "description": model.description,
            "properties": {}
        }
        
        # Add required fields
        required_fields = [field.name for field in model.fields if field.required]
        if required_fields:
            result["required"] = required_fields
        
        # Add deprecation flag if needed
        if model.deprecated:
            result["deprecated"] = True
        
        # Process fields
        for field in model.fields:
            result["properties"][field.name] = self._render_field_schema(field)
        
        # Add examples if available
        if model.examples:
            result["examples"] = [example.value for example in model.examples]
        
        return result
    
    def _render_field_schema(self, field: FieldDoc) -> Dict[str, Any]:
        """Render field schema for OpenAPI spec."""
        result = self._render_schema_type_from_field(field)
        
        # Add description
        result["description"] = field.description
        
        # Add default if available
        if field.default is not None:
            result["default"] = field.default
        
        # Add enum values if available
        if field.enum_values:
            result["enum"] = field.enum_values
        
        # Add deprecation flag if needed
        if field.deprecated:
            result["deprecated"] = True
        
        # Add pattern if available
        if field.pattern:
            result["pattern"] = field.pattern
        
        # Add min/max values if available
        if field.min_value is not None:
            if isinstance(field.min_value, int):
                result["minimum"] = field.min_value
            else:
                result["minLength"] = field.min_value
        
        if field.max_value is not None:
            if isinstance(field.max_value, int):
                result["maximum"] = field.max_value
            else:
                result["maxLength"] = field.max_value
        
        # Add format if available
        if field.format:
            result["format"] = field.format
        
        # Add example if available
        if field.example is not None:
            result["example"] = field.example
        
        # Add nullable flag if needed
        if field.nullable:
            result["nullable"] = True
        
        # Add read-only/write-only flags if needed
        if field.read_only:
            result["readOnly"] = True
        
        if field.write_only:
            result["writeOnly"] = True
        
        return result
    
    def _render_schema_type(self, param: ParameterDoc) -> Dict[str, Any]:
        """Render schema type for OpenAPI spec."""
        result = {
            "type": self._type_to_openapi_type(param.type)
        }
        
        # Handle array and object types
        if result["type"] == "array":
            result["items"] = {
                "type": "string"  # Default, should be overridden based on actual type
            }
            
            # Try to extract item type from param.type (e.g., List[str])
            match = re.search(r"List\[(.*?)\]", param.type)
            if match:
                item_type = match.group(1)
                result["items"]["type"] = self._type_to_openapi_type(item_type)
        
        # Add enum values if available
        if param.enum_values:
            result["enum"] = param.enum_values
        
        # Add pattern if available
        if param.pattern:
            result["pattern"] = param.pattern
        
        # Add min/max values if available
        if param.min_value is not None:
            if isinstance(param.min_value, int):
                result["minimum"] = param.min_value
            else:
                result["minLength"] = param.min_value
        
        if param.max_value is not None:
            if isinstance(param.max_value, int):
                result["maximum"] = param.max_value
            else:
                result["maxLength"] = param.max_value
        
        # Add format if available
        if param.format:
            result["format"] = param.format
        
        return result
    
    def _render_schema_type_from_field(self, field: FieldDoc) -> Dict[str, Any]:
        """Render schema type for OpenAPI spec from field."""
        result = {
            "type": self._type_to_openapi_type(field.type)
        }
        
        # Handle array and object types
        if result["type"] == "array":
            result["items"] = {
                "type": "string"  # Default, should be overridden based on actual type
            }
            
            # Try to extract item type from field.type (e.g., List[str])
            match = re.search(r"List\[(.*?)\]", field.type)
            if match:
                item_type = match.group(1)
                result["items"]["type"] = self._type_to_openapi_type(item_type)
        
        return result
    
    def _type_to_openapi_type(self, type_str: str) -> str:
        """Convert Python type string to OpenAPI type."""
        if type_str.startswith("int") or type_str.startswith("float"):
            return "number"
        elif type_str.startswith("str"):
            return "string"
        elif type_str.startswith("bool"):
            return "boolean"
        elif type_str.startswith("List") or type_str.startswith("list"):
            return "array"
        elif type_str.startswith("Dict") or type_str.startswith("dict"):
            return "object"
        elif type_str.startswith("Optional"):
            # Extract the inner type
            match = re.search(r"Optional\[(.*?)\]", type_str)
            if match:
                return self._type_to_openapi_type(match.group(1))
        elif type_str.startswith("Union"):
            # For union types, use string as a fallback
            return "string"
        elif type_str == "Any" or type_str == "any":
            return "object"
        else:
            # For custom types, use object as fallback
            return "object"
    
    def _render_security_schemes(self, schema: DocSchema) -> Dict[str, Any]:
        """Render security schemes for OpenAPI spec."""
        result = {}
        
        for security_scheme in schema.security_schemes:
            scheme_spec = {
                "type": security_scheme.type,
                "description": security_scheme.description
            }
            
            # Add scheme-specific properties
            if security_scheme.type == "http":
                scheme_spec["scheme"] = security_scheme.scheme
                if security_scheme.bearer_format:
                    scheme_spec["bearerFormat"] = security_scheme.bearer_format
            elif security_scheme.type == "apiKey":
                scheme_spec["in"] = security_scheme.in_param.name.lower()
                scheme_spec["name"] = security_scheme.name
            elif security_scheme.type == "oauth2":
                scheme_spec["flows"] = security_scheme.flows
            elif security_scheme.type == "openIdConnect":
                scheme_spec["openIdConnectUrl"] = security_scheme.open_id_connect_url
            
            result[security_scheme.name] = scheme_spec
        
        return result


class HtmlRenderer(DocRenderer):
    """Renderer for HTML documentation."""
    
    def render(self, schema: DocSchema, config: Any) -> Dict[str, str]:
        """
        Render documentation schema as HTML.
        
        Args:
            schema: Documentation schema to render
            config: Configuration for rendering
            
        Returns:
            Dictionary of filenames to rendered content
        """
        # This is a placeholder implementation
        # A complete implementation would generate HTML documentation
        
        result = {
            "index.html": "<html><body><h1>API Documentation</h1><p>HTML documentation coming soon.</p></body></html>"
        }
        
        return result


class AsciiDocRenderer(DocRenderer):
    """Renderer for AsciiDoc documentation."""
    
    def render(self, schema: DocSchema, config: Any) -> Dict[str, str]:
        """
        Render documentation schema as AsciiDoc.
        
        Args:
            schema: Documentation schema to render
            config: Configuration for rendering
            
        Returns:
            Dictionary of filenames to rendered content
        """
        # This is a placeholder implementation
        # A complete implementation would generate AsciiDoc documentation
        
        result = {
            "index.adoc": "= API Documentation\n\nAsciiDoc documentation coming soon."
        }
        
        return result