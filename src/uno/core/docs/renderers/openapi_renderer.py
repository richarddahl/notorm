"""
OpenAPI renderer for documentation.

This module provides a renderer that transforms documentation schemas into
OpenAPI specification format for use with Swagger, ReDoc, or other OpenAPI tools.
"""

import json
import re
import yaml
from typing import Dict, List, Any, Optional

from uno.core.docs.schema import (
    DocSchema, EndpointDoc, ModelDoc, ParameterDoc, ParameterLocation
)
from uno.core.docs.renderers.base import DocRenderer


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
        
        # Create HTML page that embeds Swagger UI
        html_content = self._create_swagger_ui_page(schema, config)
        
        return {
            "openapi.yaml": yaml_content,
            "openapi.json": json_content,
            "swagger-ui.html": html_content
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
    
    def _render_field_schema(self, field) -> Dict[str, Any]:
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
    
    def _render_schema_type_from_field(self, field) -> Dict[str, Any]:
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
    
    def _create_swagger_ui_page(self, schema: DocSchema, config: Any) -> str:
        """Create an HTML page with embedded Swagger UI."""
        title = schema.title
        version = schema.version
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        
        *,
        *:before,
        *:after {{
            box-sizing: inherit;
        }}
        
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        
        .swagger-ui .topbar {{
            background-color: #333;
        }}
        
        .swagger-ui .info {{
            margin: 20px 0;
        }}
        
        .swagger-ui .info hgroup.main h2.title {{
            font-weight: bold;
        }}
        
        .swagger-ui .scheme-container {{
            box-shadow: none;
            padding: 15px 0;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    
    <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: "openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout",
                supportedSubmitMethods: ["get", "post", "put", "delete", "patch", "options", "head"],
                validatorUrl: null
            }});
            
            window.ui = ui;
        }};
    </script>
</body>
</html>
"""
        return html