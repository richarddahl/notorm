"""
Documentation renderers for the Uno framework.

This module provides renderers for converting extracted documentation into
various output formats such as Markdown, HTML, OpenAPI, and interactive playgrounds.
"""

import os
import json
import logging
import html
from typing import Dict, List, Optional, Any, Set, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseRenderer:
    """Base class for documentation renderers."""

    def __init__(self):
        """Initialize the renderer."""
        self.warnings: list[str] = []

    def render(
        self, data: dict[str, Any], output_dir: Union[str, Path]
    ) -> dict[str, str]:
        """
        Render documentation to the specified output format.

        Args:
            data: Documentation data to render
            output_dir: Output directory

        Returns:
            Dictionary of rendered files with filenames as keys and content as values
        """
        raise NotImplementedError("Subclasses must implement render")


class MarkdownRenderer(BaseRenderer):
    """Renderer for Markdown documentation."""

    def render(
        self, data: dict[str, Any], output_dir: Union[str, Path]
    ) -> dict[str, str]:
        """
        Render documentation to Markdown.

        Args:
            data: Documentation data to render
            output_dir: Output directory

        Returns:
            Dictionary of rendered files with filenames as keys and content as values
        """
        result = {}

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate index file
        index_content = self._render_index(data)
        result["index.md"] = index_content

        # Generate module documentation
        if "modules" in data:
            for module_data in data["modules"]:
                module_path = module_data["name"].replace(".", "/")
                module_dir = os.path.join(output_dir, module_path)
                os.makedirs(module_dir, exist_ok=True)

                # Generate module index
                module_index = self._render_module_index(module_data)
                result[f"{module_path}/index.md"] = module_index

                # Generate class documentation
                if "classes" in module_data:
                    for class_data in module_data["classes"]:
                        class_content = self._render_class(class_data)
                        result[f"{module_path}/{class_data['name']}.md"] = class_content

                # Generate function documentation
                if "functions" in module_data:
                    for function_data in module_data["functions"]:
                        function_content = self._render_function(function_data)
                        result[f"{module_path}/{function_data['name']}.md"] = (
                            function_content
                        )

        # Generate API endpoint documentation
        if "endpoints" in data:
            # Create API directory
            api_dir = os.path.join(output_dir, "api")
            os.makedirs(api_dir, exist_ok=True)

            # Generate API index
            api_index = self._render_api_index(data["endpoints"])
            result["api/index.md"] = api_index

            # Generate endpoint documentation
            for endpoint_data in data["endpoints"]:
                endpoint_content = self._render_endpoint(endpoint_data)
                endpoint_name = (
                    endpoint_data.get("name", "").replace("/", "_")
                    or f"endpoint_{len(result)}"
                )
                result[f"api/{endpoint_name}.md"] = endpoint_content

        # Generate model documentation
        if "models" in data:
            # Create models directory
            models_dir = os.path.join(output_dir, "models")
            os.makedirs(models_dir, exist_ok=True)

            # Generate models index
            models_index = self._render_models_index(data["models"])
            result["models/index.md"] = models_index

            # Generate model documentation
            for model_data in data["models"]:
                model_content = self._render_model(model_data)
                result[f"models/{model_data['name']}.md"] = model_content

        # Generate example documentation
        if "examples" in data:
            # Create examples directory
            examples_dir = os.path.join(output_dir, "examples")
            os.makedirs(examples_dir, exist_ok=True)

            # Generate examples index
            examples_index = self._render_examples_index(data["examples"])
            result["examples/index.md"] = examples_index

            # Generate example documentation
            for example_data in data["examples"]:
                example_content = self._render_example(example_data)
                example_name = (
                    example_data.get("name", "").replace("/", "_")
                    or f"example_{len(result)}"
                )
                result[f"examples/{example_name}.md"] = example_content

        # Create search index
        search_index = self._generate_search_index(data)
        result["search_index.json"] = json.dumps(search_index, indent=2)

        return result

    def _render_index(self, data: dict[str, Any]) -> str:
        """
        Render the documentation index.

        Args:
            data: Documentation data

        Returns:
            Rendered index content
        """
        lines = []
        lines.append(f"# {data.get('title', 'API Documentation')}")
        lines.append("")
        lines.append(data.get("description", ""))
        lines.append("")

        # Add sections
        sections = []

        if "modules" in data:
            sections.append(("Modules", "modules"))

        if "endpoints" in data:
            sections.append(("API Endpoints", "api"))

        if "models" in data:
            sections.append(("Data Models", "models"))

        if "examples" in data:
            sections.append(("Code Examples", "examples"))

        for title, path in sections:
            lines.append(f"## {title}")
            lines.append("")
            lines.append(f"[View {title} Documentation]({path}/index.md)")
            lines.append("")

        return "\n".join(lines)

    def _render_module_index(self, module_data: dict[str, Any]) -> str:
        """
        Render a module index.

        Args:
            module_data: Module data

        Returns:
            Rendered module index content
        """
        lines = []
        lines.append(f"# Module {module_data['name']}")
        lines.append("")

        if "description" in module_data:
            lines.append(module_data["description"])
            lines.append("")

        # Add classes
        if "classes" in module_data and module_data["classes"]:
            lines.append("## Classes")
            lines.append("")

            for class_data in module_data["classes"]:
                class_name = class_data["name"]
                class_desc = (
                    class_data.get("description", "").split(".")[0] + "."
                    if class_data.get("description")
                    else ""
                )

                lines.append(f"- [{class_name}]({class_name}.md): {class_desc}")

            lines.append("")

        # Add functions
        if "functions" in module_data and module_data["functions"]:
            lines.append("## Functions")
            lines.append("")

            for function_data in module_data["functions"]:
                function_name = function_data["name"]
                function_desc = (
                    function_data.get("description", "").split(".")[0] + "."
                    if function_data.get("description")
                    else ""
                )

                lines.append(
                    f"- [{function_name}]({function_name}.md): {function_desc}"
                )

            lines.append("")

        return "\n".join(lines)

    def _render_class(self, class_data: dict[str, Any]) -> str:
        """
        Render class documentation.

        Args:
            class_data: Class data

        Returns:
            Rendered class documentation content
        """
        lines = []
        lines.append(f"# {class_data['name']}")
        lines.append("")

        if "description" in class_data:
            lines.append(class_data["description"])
            lines.append("")

        if "long_description" in class_data and class_data["long_description"]:
            lines.append(class_data["long_description"])
            lines.append("")

        # Add inheritance
        if "bases" in class_data and class_data["bases"]:
            bases = ", ".join(class_data["bases"])
            lines.append(f"**Inherits from:** {bases}")
            lines.append("")

        # Add attributes
        if "attributes" in class_data and class_data["attributes"]:
            lines.append("## Attributes")
            lines.append("")

            for attr in class_data["attributes"]:
                attr_name = attr["name"]
                attr_type = attr.get("type", "")
                attr_desc = attr.get("description", "")

                if attr_type:
                    lines.append(f"### {attr_name}: {attr_type}")
                else:
                    lines.append(f"### {attr_name}")

                lines.append("")

                if attr_desc:
                    lines.append(attr_desc)
                    lines.append("")

        # Add methods
        if "methods" in class_data and class_data["methods"]:
            lines.append("## Methods")
            lines.append("")

            for method in class_data["methods"]:
                method_name = method["name"]
                method_sig = method.get("signature", "")
                method_desc = method.get("description", "")

                lines.append(f"### {method_name}{method_sig}")
                lines.append("")

                if method_desc:
                    lines.append(method_desc)
                    lines.append("")

                # Add parameters
                if "params" in method and method["params"]:
                    lines.append("**Parameters:**")
                    lines.append("")

                    for param in method["params"]:
                        param_name = param["name"]
                        param_type = param.get("type", "")
                        param_desc = param.get("description", "")

                        if param_type:
                            lines.append(
                                f"- `{param_name}` ({param_type}): {param_desc}"
                            )
                        else:
                            lines.append(f"- `{param_name}`: {param_desc}")

                    lines.append("")

                # Add return value
                if "returns" in method and method["returns"]:
                    return_type = method["returns"].get("type", "")
                    return_desc = method["returns"].get("description", "")

                    lines.append("**Returns:**")
                    lines.append("")

                    if return_type:
                        lines.append(f"- ({return_type}): {return_desc}")
                    else:
                        lines.append(f"- {return_desc}")

                    lines.append("")

                # Add exceptions
                if "raises" in method and method["raises"]:
                    lines.append("**Raises:**")
                    lines.append("")

                    for exception in method["raises"]:
                        exc_type = exception.get("type", "")
                        exc_desc = exception.get("description", "")

                        lines.append(f"- `{exc_type}`: {exc_desc}")

                    lines.append("")

        # Add examples
        if "examples" in class_data and class_data["examples"]:
            lines.append("## Examples")
            lines.append("")

            for example in class_data["examples"]:
                example_desc = example.get("description", "")

                if example_desc:
                    lines.append(example_desc)
                    lines.append("")

                if "source" in example:
                    lines.append("```python")
                    lines.append(example["source"])
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)

    def _render_function(self, function_data: dict[str, Any]) -> str:
        """
        Render function documentation.

        Args:
            function_data: Function data

        Returns:
            Rendered function documentation content
        """
        lines = []
        lines.append(f"# {function_data['name']}")
        lines.append("")

        # Add signature
        if "signature" in function_data:
            lines.append("```python")
            lines.append(f"def {function_data['name']}{function_data['signature']}")
            lines.append("```")
            lines.append("")

        if "description" in function_data:
            lines.append(function_data["description"])
            lines.append("")

        if "long_description" in function_data and function_data["long_description"]:
            lines.append(function_data["long_description"])
            lines.append("")

        # Add parameters
        if "params" in function_data and function_data["params"]:
            lines.append("## Parameters")
            lines.append("")

            for param in function_data["params"]:
                param_name = param["name"]
                param_type = param.get("type", "")
                param_desc = param.get("description", "")

                if param_type:
                    lines.append(f"- `{param_name}` ({param_type}): {param_desc}")
                else:
                    lines.append(f"- `{param_name}`: {param_desc}")

            lines.append("")

        # Add return value
        if "returns" in function_data and function_data["returns"]:
            lines.append("## Returns")
            lines.append("")

            return_type = function_data["returns"].get("type", "")
            return_desc = function_data["returns"].get("description", "")

            if return_type:
                lines.append(f"- ({return_type}): {return_desc}")
            else:
                lines.append(f"- {return_desc}")

            lines.append("")

        # Add exceptions
        if "raises" in function_data and function_data["raises"]:
            lines.append("## Raises")
            lines.append("")

            for exception in function_data["raises"]:
                exc_type = exception.get("type", "")
                exc_desc = exception.get("description", "")

                lines.append(f"- `{exc_type}`: {exc_desc}")

            lines.append("")

        # Add examples
        if "examples" in function_data and function_data["examples"]:
            lines.append("## Examples")
            lines.append("")

            for example in function_data["examples"]:
                example_desc = example.get("description", "")

                if example_desc:
                    lines.append(example_desc)
                    lines.append("")

                if "source" in example:
                    lines.append("```python")
                    lines.append(example["source"])
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)

    def _render_api_index(self, endpoints: list[dict[str, Any]]) -> str:
        """
        Render API endpoints index.

        Args:
            endpoints: List of endpoint data

        Returns:
            Rendered API index content
        """
        lines = []
        lines.append("# API Endpoints")
        lines.append("")
        lines.append("This section contains documentation for all API endpoints.")
        lines.append("")

        # Group endpoints by tags
        endpoints_by_tag = {}
        for endpoint in endpoints:
            tags = endpoint.get("tags", ["Default"])
            for tag in tags:
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)

        # Add endpoints by tag
        for tag, tag_endpoints in sorted(endpoints_by_tag.items()):
            lines.append(f"## {tag}")
            lines.append("")

            for endpoint in tag_endpoints:
                endpoint_name = (
                    endpoint.get("name", "").replace("/", "_")
                    or f"endpoint_{len(endpoints_by_tag)}"
                )
                methods = ", ".join(endpoint.get("methods", []))
                path = endpoint.get("path", "")
                desc = (
                    endpoint.get("description", "").split(".")[0] + "."
                    if endpoint.get("description")
                    else ""
                )

                lines.append(f"- [{methods} {path}]({endpoint_name}.md): {desc}")

            lines.append("")

        return "\n".join(lines)

    def _render_endpoint(self, endpoint_data: dict[str, Any]) -> str:
        """
        Render endpoint documentation.

        Args:
            endpoint_data: Endpoint data

        Returns:
            Rendered endpoint documentation content
        """
        lines = []

        # Title
        methods = ", ".join(endpoint_data.get("methods", []))
        path = endpoint_data.get("path", "")
        title = f"{methods} {path}"
        lines.append(f"# {title}")
        lines.append("")

        # Description
        if "description" in endpoint_data:
            lines.append(endpoint_data["description"])
            lines.append("")

        if "long_description" in endpoint_data and endpoint_data["long_description"]:
            lines.append(endpoint_data["long_description"])
            lines.append("")

        # Parameters
        if "parameters" in endpoint_data and endpoint_data["parameters"]:
            lines.append("## Parameters")
            lines.append("")

            lines.append("| Name | Type | Required | Description |")
            lines.append("| ---- | ---- | -------- | ----------- |")

            for param in endpoint_data["parameters"]:
                name = param["name"]
                type_name = param.get("type", "")
                required = "Yes" if param.get("required", False) else "No"
                desc = param.get("description", "")

                lines.append(f"| {name} | {type_name} | {required} | {desc} |")

            lines.append("")

        # Request body
        if "request_body" in endpoint_data:
            lines.append("## Request Body")
            lines.append("")

            request_body = endpoint_data["request_body"]
            content_type = request_body.get("content_type", "application/json")
            schema = request_body.get("schema", {})

            lines.append(f"**Content Type:** {content_type}")
            lines.append("")

            if schema:
                lines.append("**Schema:**")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(schema, indent=2))
                lines.append("```")
                lines.append("")

        # Responses
        if "responses" in endpoint_data and endpoint_data["responses"]:
            lines.append("## Responses")
            lines.append("")

            for status_code, response in endpoint_data["responses"].items():
                lines.append(f"### {status_code}")
                lines.append("")

                if "description" in response:
                    lines.append(response["description"])
                    lines.append("")

                if "content" in response:
                    content_type = list(response["content"].keys())[0]
                    schema = response["content"][content_type].get("schema", {})

                    lines.append(f"**Content Type:** {content_type}")
                    lines.append("")

                    if schema:
                        lines.append("**Schema:**")
                        lines.append("")
                        lines.append("```json")
                        lines.append(json.dumps(schema, indent=2))
                        lines.append("```")
                        lines.append("")

        # Examples
        if "examples" in endpoint_data and endpoint_data["examples"]:
            lines.append("## Examples")
            lines.append("")

            for example in endpoint_data["examples"]:
                example_name = example.get("name", "Example")
                lines.append(f"### {example_name}")
                lines.append("")

                if "description" in example:
                    lines.append(example["description"])
                    lines.append("")

                if "request" in example:
                    lines.append("**Request:**")
                    lines.append("")

                    if "headers" in example["request"]:
                        lines.append("Headers:")
                        lines.append("")
                        for header, value in example["request"]["headers"].items():
                            lines.append(f"- {header}: {value}")
                        lines.append("")

                    if "body" in example["request"]:
                        lines.append("Body:")
                        lines.append("")
                        lines.append("```json")
                        if isinstance(example["request"]["body"], dict):
                            lines.append(
                                json.dumps(example["request"]["body"], indent=2)
                            )
                        else:
                            lines.append(str(example["request"]["body"]))
                        lines.append("```")
                        lines.append("")

                if "response" in example:
                    lines.append("**Response:**")
                    lines.append("")

                    if "status_code" in example["response"]:
                        lines.append(
                            f"Status Code: {example['response']['status_code']}"
                        )
                        lines.append("")

                    if "headers" in example["response"]:
                        lines.append("Headers:")
                        lines.append("")
                        for header, value in example["response"]["headers"].items():
                            lines.append(f"- {header}: {value}")
                        lines.append("")

                    if "body" in example["response"]:
                        lines.append("Body:")
                        lines.append("")
                        lines.append("```json")
                        if isinstance(example["response"]["body"], dict):
                            lines.append(
                                json.dumps(example["response"]["body"], indent=2)
                            )
                        else:
                            lines.append(str(example["response"]["body"]))
                        lines.append("```")
                        lines.append("")

        return "\n".join(lines)

    def _render_models_index(self, models: list[dict[str, Any]]) -> str:
        """
        Render models index.

        Args:
            models: List of model data

        Returns:
            Rendered models index content
        """
        lines = []
        lines.append("# Data Models")
        lines.append("")
        lines.append("This section contains documentation for all data models.")
        lines.append("")

        # Group models by module
        models_by_module = {}
        for model in models:
            module = model.get("module", "Default")
            if module not in models_by_module:
                models_by_module[module] = []
            models_by_module[module].append(model)

        # Add models by module
        for module, module_models in sorted(models_by_module.items()):
            lines.append(f"## {module}")
            lines.append("")

            for model in module_models:
                model_name = model["name"]
                desc = (
                    model.get("description", "").split(".")[0] + "."
                    if model.get("description")
                    else ""
                )

                lines.append(f"- [{model_name}]({model_name}.md): {desc}")

            lines.append("")

        return "\n".join(lines)

    def _render_model(self, model_data: dict[str, Any]) -> str:
        """
        Render model documentation.

        Args:
            model_data: Model data

        Returns:
            Rendered model documentation content
        """
        lines = []
        lines.append(f"# {model_data['name']}")
        lines.append("")

        if "description" in model_data:
            lines.append(model_data["description"])
            lines.append("")

        if "long_description" in model_data and model_data["long_description"]:
            lines.append(model_data["long_description"])
            lines.append("")

        # Add table information
        if "tablename" in model_data:
            lines.append(f"**Table:** {model_data['tablename']}")

            if "schema" in model_data and model_data["schema"]:
                lines.append(f"**Schema:** {model_data['schema']}")

            lines.append("")

        # Add fields
        if "fields" in model_data and model_data["fields"]:
            lines.append("## Fields")
            lines.append("")

            lines.append("| Name | Type | Required | Description |")
            lines.append("| ---- | ---- | -------- | ----------- |")

            for field in model_data["fields"]:
                name = field["name"]
                type_name = field.get("type", "")
                required = (
                    "Yes"
                    if field.get("required", True) and not field.get("nullable", False)
                    else "No"
                )
                desc = field.get("description", "")

                lines.append(f"| {name} | {type_name} | {required} | {desc} |")

            lines.append("")

        # Add relationships
        if "relationships" in model_data and model_data["relationships"]:
            lines.append("## Relationships")
            lines.append("")

            lines.append("| Name | Target | Direction |")
            lines.append("| ---- | ------ | --------- |")

            for rel in model_data["relationships"]:
                name = rel["name"]
                target = rel.get("target", "")
                direction = rel.get("direction", "")

                lines.append(f"| {name} | {target} | {direction} |")

            lines.append("")

        # Add examples
        if "examples" in model_data and model_data["examples"]:
            lines.append("## Examples")
            lines.append("")

            for example in model_data["examples"]:
                example_desc = example.get("description", "")

                if example_desc:
                    lines.append(example_desc)
                    lines.append("")

                if "value" in example:
                    lines.append("```json")
                    lines.append(json.dumps(example["value"], indent=2))
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)

    def _render_examples_index(self, examples: list[dict[str, Any]]) -> str:
        """
        Render examples index.

        Args:
            examples: List of example data

        Returns:
            Rendered examples index content
        """
        lines = []
        lines.append("# Code Examples")
        lines.append("")
        lines.append("This section contains code examples and usage patterns.")
        lines.append("")

        # Group examples by module
        examples_by_module = {}
        for example in examples:
            module = example.get("module", "Default")
            if module not in examples_by_module:
                examples_by_module[module] = []
            examples_by_module[module].append(example)

        # Add examples by module
        for module, module_examples in sorted(examples_by_module.items()):
            lines.append(f"## {module}")
            lines.append("")

            for example in module_examples:
                example_name = (
                    example.get("name", "").replace("/", "_")
                    or f"example_{len(examples_by_module)}"
                )
                desc = (
                    example.get("description", "").split(".")[0] + "."
                    if example.get("description")
                    else ""
                )

                lines.append(f"- [{example_name}]({example_name}.md): {desc}")

            lines.append("")

        return "\n".join(lines)

    def _render_example(self, example_data: dict[str, Any]) -> str:
        """
        Render example documentation.

        Args:
            example_data: Example data

        Returns:
            Rendered example documentation content
        """
        lines = []
        example_name = example_data.get("name", "Example")

        lines.append(f"# {example_name}")
        lines.append("")

        if "description" in example_data:
            lines.append(example_data["description"])
            lines.append("")

        # Add examples
        if "examples" in example_data:
            for example in example_data["examples"]:
                example_desc = example.get("description", "")

                if example_desc:
                    lines.append(f"## {example_desc}")
                    lines.append("")

                if "source" in example:
                    lines.append("```python")
                    lines.append(example["source"])
                    lines.append("```")
                    lines.append("")
        elif "source" in example_data:
            lines.append("## Source Code")
            lines.append("")
            lines.append("```python")
            lines.append(example_data["source"])
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def _generate_search_index(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Generate search index.

        Args:
            data: Documentation data

        Returns:
            Search index
        """
        search_index = []

        # Index modules
        if "modules" in data:
            for module_data in data["modules"]:
                module_path = module_data["name"].replace(".", "/")

                search_index.append(
                    {
                        "type": "module",
                        "name": module_data["name"],
                        "path": f"{module_path}/index.md",
                        "description": module_data.get("description", ""),
                    }
                )

                # Index classes
                if "classes" in module_data:
                    for class_data in module_data["classes"]:
                        search_index.append(
                            {
                                "type": "class",
                                "name": class_data["name"],
                                "module": module_data["name"],
                                "path": f"{module_path}/{class_data['name']}.md",
                                "description": class_data.get("description", ""),
                            }
                        )

                # Index functions
                if "functions" in module_data:
                    for function_data in module_data["functions"]:
                        search_index.append(
                            {
                                "type": "function",
                                "name": function_data["name"],
                                "module": module_data["name"],
                                "path": f"{module_path}/{function_data['name']}.md",
                                "description": function_data.get("description", ""),
                            }
                        )

        # Index endpoints
        if "endpoints" in data:
            for endpoint_data in data["endpoints"]:
                endpoint_name = (
                    endpoint_data.get("name", "").replace("/", "_")
                    or f"endpoint_{len(search_index)}"
                )
                methods = ", ".join(endpoint_data.get("methods", []))
                path = endpoint_data.get("path", "")

                search_index.append(
                    {
                        "type": "endpoint",
                        "name": f"{methods} {path}",
                        "path": f"api/{endpoint_name}.md",
                        "description": endpoint_data.get("description", ""),
                    }
                )

        # Index models
        if "models" in data:
            for model_data in data["models"]:
                search_index.append(
                    {
                        "type": "model",
                        "name": model_data["name"],
                        "module": model_data.get("module", ""),
                        "path": f"models/{model_data['name']}.md",
                        "description": model_data.get("description", ""),
                    }
                )

        # Index examples
        if "examples" in data:
            for example_data in data["examples"]:
                example_name = (
                    example_data.get("name", "").replace("/", "_")
                    or f"example_{len(search_index)}"
                )

                search_index.append(
                    {
                        "type": "example",
                        "name": example_data.get("name", "Example"),
                        "module": example_data.get("module", ""),
                        "path": f"examples/{example_name}.md",
                        "description": example_data.get("description", ""),
                    }
                )

        return search_index


class OpenAPIRenderer(BaseRenderer):
    """Renderer for OpenAPI documentation."""

    def render(
        self, data: dict[str, Any], output_dir: Union[str, Path]
    ) -> dict[str, str]:
        """
        Render documentation to OpenAPI.

        Args:
            data: Documentation data to render
            output_dir: Output directory

        Returns:
            Dictionary of rendered files with filenames as keys and content as values
        """
        result = {}

        # Generate OpenAPI schema
        openapi_schema = self._generate_openapi_schema(data)

        # Save as JSON and YAML
        result["openapi.json"] = json.dumps(openapi_schema, indent=2)

        try:
            import yaml

            result["openapi.yaml"] = yaml.dump(openapi_schema, default_flow_style=False)
        except ImportError:
            self.warnings.append(
                "PyYAML is not installed, OpenAPI YAML output is disabled"
            )

        return result

    def _generate_openapi_schema(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate OpenAPI schema.

        Args:
            data: Documentation data

        Returns:
            OpenAPI schema
        """
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": data.get("title", "API Documentation"),
                "description": data.get("description", ""),
                "version": data.get("version", "1.0.0"),
            },
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {},
            },
        }

        # Add paths from endpoints
        if "endpoints" in data:
            for endpoint_data in data["endpoints"]:
                path = endpoint_data.get("path", "")
                if not path:
                    continue

                methods = [
                    method.lower() for method in endpoint_data.get("methods", [])
                ]

                if path not in schema["paths"]:
                    schema["paths"][path] = {}

                for method in methods:
                    schema["paths"][path][method] = self._convert_endpoint_to_openapi(
                        endpoint_data
                    )

        # Add schemas from models
        if "models" in data:
            for model_data in data["models"]:
                model_name = model_data["name"]
                schema["components"]["schemas"][model_name] = (
                    self._convert_model_to_openapi(model_data)
                )

        return schema

    def _convert_endpoint_to_openapi(
        self, endpoint_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Convert endpoint data to OpenAPI operation object.

        Args:
            endpoint_data: Endpoint data

        Returns:
            OpenAPI operation object
        """
        operation = {
            "summary": (
                endpoint_data.get("description", "").split(".")[0]
                if endpoint_data.get("description")
                else ""
            ),
            "description": endpoint_data.get("description", ""),
            "tags": endpoint_data.get("tags", []),
            "parameters": [],
            "responses": {},
        }

        # Add deprecated flag
        if endpoint_data.get("deprecated", False):
            operation["deprecated"] = True

        # Add parameters
        if "parameters" in endpoint_data:
            for param in endpoint_data["parameters"]:
                param_name = param["name"]
                param_in = (
                    "path"
                    if "{" + param_name + "}" in endpoint_data.get("path", "")
                    else "query"
                )

                openapi_param = {
                    "name": param_name,
                    "in": param_in,
                    "description": param.get("description", ""),
                    "required": param.get("required", False),
                }

                # Add schema
                if "type" in param:
                    openapi_param["schema"] = {
                        "type": self._convert_type_to_openapi(param["type"]),
                    }

                operation["parameters"].append(openapi_param)

        # Add request body
        if "request_body" in endpoint_data:
            request_body = endpoint_data["request_body"]
            content_type = request_body.get("content_type", "application/json")
            schema = request_body.get("schema", {})

            operation["requestBody"] = {
                "content": {
                    content_type: {
                        "schema": schema,
                    },
                },
            }

        # Add responses
        if "responses" in endpoint_data:
            operation["responses"] = endpoint_data["responses"]
        else:
            # Add default responses
            operation["responses"] = {
                "200": {
                    "description": "Successful operation",
                },
                "400": {
                    "description": "Bad request",
                },
                "401": {
                    "description": "Unauthorized",
                },
                "404": {
                    "description": "Not found",
                },
                "500": {
                    "description": "Internal server error",
                },
            }

        return operation

    def _convert_model_to_openapi(self, model_data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert model data to OpenAPI schema object.

        Args:
            model_data: Model data

        Returns:
            OpenAPI schema object
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        # Add description
        if "description" in model_data:
            schema["description"] = model_data["description"]

        # Add properties
        if "fields" in model_data:
            for field in model_data["fields"]:
                field_name = field["name"]
                field_type = field.get("type", "string")
                field_desc = field.get("description", "")
                field_required = field.get("required", True) and not field.get(
                    "nullable", False
                )

                schema["properties"][field_name] = {
                    "type": self._convert_type_to_openapi(field_type),
                    "description": field_desc,
                }

                if field_required:
                    schema["required"].append(field_name)

        return schema

    def _convert_type_to_openapi(self, type_str: str) -> str:
        """
        Convert Python type to OpenAPI type.

        Args:
            type_str: Python type string

        Returns:
            OpenAPI type string
        """
        # Handle basic types
        if type_str.lower() in ("str", "string"):
            return "string"
        elif type_str.lower() in ("int", "integer", "long"):
            return "integer"
        elif type_str.lower() in ("float", "double", "decimal"):
            return "number"
        elif type_str.lower() in ("bool", "boolean"):
            return "boolean"
        elif type_str.lower() in ("dict", "dictionary", "object"):
            return "object"
        elif type_str.lower() in ("list", "array"):
            return "array"

        # Handle complex types (very simplified)
        if "list" in type_str.lower() or "[]" in type_str:
            return "array"
        elif "dict" in type_str.lower() or "{" in type_str:
            return "object"

        # Default to string
        return "string"


class HTMLRenderer(BaseRenderer):
    """Renderer for HTML documentation."""

    def render(
        self, data: dict[str, Any], output_dir: Union[str, Path]
    ) -> dict[str, str]:
        """
        Render documentation to HTML.

        Args:
            data: Documentation data to render
            output_dir: Output directory

        Returns:
            Dictionary of rendered files with filenames as keys and content as values
        """
        result = {}

        # Generate HTML files using markdown and templates
        markdown_renderer = MarkdownRenderer()
        markdown_files = markdown_renderer.render(data, output_dir)

        # Convert markdown to HTML
        try:
            import markdown

            # Load templates
            index_template = self._load_template("index.html")
            page_template = self._load_template("page.html")

            # Convert each markdown file to HTML
            for filename, content in markdown_files.items():
                if filename.endswith(".json"):
                    # Skip JSON files (search index)
                    result[filename] = content
                    continue

                html_filename = filename.replace(".md", ".html")

                # Convert markdown to HTML
                html_content = markdown.markdown(
                    content,
                    extensions=["tables", "fenced_code", "codehilite"],
                )

                # Wrap in template
                template = index_template if filename == "index.md" else page_template

                page_title = self._extract_title(content)
                full_html = template.replace("{{title}}", page_title)
                full_html = full_html.replace("{{content}}", html_content)

                result[html_filename] = full_html

            # Generate CSS and JavaScript files
            result["css/style.css"] = self._generate_css()
            result["js/script.js"] = self._generate_js()

        except ImportError:
            self.warnings.append("markdown is not installed, HTML output is disabled")
            return {}

        return result

    def _load_template(self, template_name: str) -> str:
        """
        Load HTML template.

        Args:
            template_name: Template name

        Returns:
            Template content
        """
        # Basic templates
        templates = {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>API Documentation</h1>
            <div class="search-box">
                <input type="text" id="search" placeholder="Search...">
                <div id="search-results"></div>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="content">
            {{content}}
        </div>
    </div>
    <footer>
        <div class="container">
            <p>Generated by Uno Documentation Generator</p>
        </div>
    </footer>
    <script src="js/script.js"></script>
</body>
</html>""",
            "page.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1><a href="/">API Documentation</a></h1>
            <div class="search-box">
                <input type="text" id="search" placeholder="Search...">
                <div id="search-results"></div>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="content">
            {{content}}
        </div>
    </div>
    <footer>
        <div class="container">
            <p>Generated by Uno Documentation Generator</p>
        </div>
    </footer>
    <script src="/js/script.js"></script>
</body>
</html>""",
        }

        return templates.get(template_name, "")

    def _extract_title(self, markdown_content: str) -> str:
        """
        Extract title from Markdown content.

        Args:
            markdown_content: Markdown content

        Returns:
            Title
        """
        lines = markdown_content.split("\n")
        for line in lines:
            if line.startswith("# "):
                return line[2:].strip()

        return "API Documentation"

    def _generate_css(self) -> str:
        """
        Generate CSS for HTML documentation.

        Returns:
            CSS content
        """
        return """
/* Base styles */
:root {
    --primary-color: #0078d7;
    --primary-dark: #005a9e;
    --primary-light: #e6f2ff;
    --text-color: #333;
    --text-light: #666;
    --background-color: #f9f9f9;
    --border-color: #ddd;
    --code-background: #f5f5f5;
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
header {
    background-color: var(--primary-color);
    color: white;
    padding: 20px 0;
    margin-bottom: 20px;
}

header h1 {
    margin: 0;
}

header a {
    color: white;
    text-decoration: none;
}

/* Search */
.search-box {
    margin-top: 10px;
    position: relative;
}

#search {
    width: 100%;
    padding: 10px;
    border: none;
    border-radius: 4px;
    font-size: 16px;
}

#search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: white;
    border: 1px solid var(--border-color);
    border-top: none;
    border-radius: 0 0 4px 4px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 100;
    max-height: 300px;
    overflow-y: auto;
    display: none;
}

#search-results ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

#search-results li {
    padding: 10px;
    border-bottom: 1px solid var(--border-color);
}

#search-results li:last-child {
    border-bottom: none;
}

#search-results a {
    color: var(--primary-color);
    text-decoration: none;
}

#search-results a:hover {
    text-decoration: underline;
}

/* Content */
.content {
    background-color: white;
    padding: 20px;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: var(--primary-color);
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 {
    font-size: 2rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.3em;
}

h2 {
    font-size: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.3em;
}

a {
    color: var(--primary-color);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

p {
    margin-bottom: 1em;
}

/* Code */
pre {
    background-color: var(--code-background);
    padding: 16px;
    border-radius: 4px;
    overflow-x: auto;
    margin-bottom: 1em;
}

code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    background-color: var(--code-background);
    padding: 0.2em 0.4em;
    border-radius: 4px;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1em;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background-color: var(--code-background);
    font-weight: 600;
}

/* Lists */
ul, ol {
    margin-bottom: 1em;
    padding-left: 2em;
}

/* Footer */
footer {
    color: var(--text-light);
    padding: 20px 0;
    text-align: center;
    margin-top: 20px;
    border-top: 1px solid var(--border-color);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    :root {
        --primary-color: #0078d7;
        --primary-dark: #005a9e;
        --primary-light: #e6f2ff;
        --text-color: #e0e0e0;
        --text-light: #a0a0a0;
        --background-color: #1e1e1e;
        --border-color: #444;
        --code-background: #2d2d2d;
    }
    
    body {
        color: var(--text-color);
        background-color: var(--background-color);
    }
    
    .content {
        background-color: #252525;
    }
    
    #search-results {
        background-color: #252525;
    }
}
"""

    def _generate_js(self) -> str:
        """
        Generate JavaScript for HTML documentation.

        Returns:
            JavaScript content
        """
        return """
document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.getElementById('search');
    const searchResults = document.getElementById('search-results');
    
    if (searchInput && searchResults) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            if (query.length < 2) {
                searchResults.style.display = 'none';
                return;
            }
            
            // Fetch search index
            fetch('/search_index.json')
                .then(response => response.json())
                .then(searchIndex => {
                    // Filter results
                    const results = searchIndex.filter(item => {
                        return item.name.toLowerCase().includes(query) || 
                               item.description.toLowerCase().includes(query);
                    });
                    
                    // Display results
                    if (results.length === 0) {
                        searchResults.innerHTML = '<p>No results found</p>';
                    } else {
                        let html = '<ul>';
                        for (const result of results.slice(0, 10)) {
                            html += `<li><a href="/${result.path.replace('.md', '.html')}">`;
                            html += `${result.name} <small>(${result.type})</small></a>`;
                            
                            if (result.description) {
                                const shortDesc = result.description.split('.')[0] + '.';
                                html += `<p>${shortDesc}</p>`;
                            }
                            
                            html += '</li>';
                        }
                        html += '</ul>';
                        
                        searchResults.innerHTML = html;
                    }
                    
                    searchResults.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error loading search index:', error);
                    searchResults.innerHTML = '<p>Error loading search index</p>';
                    searchResults.style.display = 'block';
                });
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', function(event) {
            if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
                searchResults.style.display = 'none';
            }
        });
    }
    
    // Code highlighting
    const codeBlocks = document.querySelectorAll('pre code');
    if (window.hljs && codeBlocks.length > 0) {
        codeBlocks.forEach(block => {
            hljs.highlightBlock(block);
        });
    }
});
"""


class PlaygroundRenderer(BaseRenderer):
    """Renderer for interactive code playgrounds."""

    def render(
        self, data: dict[str, Any], output_dir: Union[str, Path]
    ) -> dict[str, str]:
        """
        Render documentation with interactive code playgrounds.

        Args:
            data: Documentation data to render
            output_dir: Output directory

        Returns:
            Dictionary of rendered files with filenames as keys and content as values
        """
        # First, generate HTML documentation
        html_renderer = HTMLRenderer()
        html_files = html_renderer.render(data, output_dir)

        # Add interactive playground functionality
        result = html_files.copy()

        # Add playground CSS and JavaScript
        result["css/playground.css"] = self._generate_playground_css()
        result["js/playground.js"] = self._generate_playground_js()

        # Modify HTML files to include playground functionality
        for filename, content in html_files.items():
            if not filename.endswith(".html"):
                continue

            # Add playground scripts and styles
            modified_content = content.replace(
                "</head>", '<link rel="stylesheet" href="/css/playground.css">\n</head>'
            )

            modified_content = modified_content.replace(
                "</body>", '<script src="/js/playground.js"></script>\n</body>'
            )

            # Add playground containers to code blocks
            modified_content = self._add_playground_containers(modified_content)

            result[filename] = modified_content

        return result

    def _add_playground_containers(self, html_content: str) -> str:
        """
        Add playground containers to code blocks.

        Args:
            html_content: HTML content

        Returns:
            Modified HTML content
        """
        # Simple regex-based approach (not robust for all HTML, but works for our generated HTML)
        import re

        # Find code blocks
        code_block_pattern = r'<pre><code class="language-python">(.*?)</code></pre>'

        def replace_code_block(match):
            code = match.group(1)
            code_escaped = html.escape(html.unescape(code))

            # Create playground container
            result = '<div class="playground">\n'
            result += '<div class="playground-header">\n'
            result += '<button class="playground-run">Run</button>\n'
            result += '<button class="playground-reset">Reset</button>\n'
            result += "</div>\n"
            result += f'<pre><code class="language-python">{code}</code></pre>\n'
            result += '<div class="playground-output hidden"></div>\n'
            result += "</div>\n"

            return result

        # Replace code blocks with playground containers
        modified_content = re.sub(
            code_block_pattern, replace_code_block, html_content, flags=re.DOTALL
        )

        return modified_content

    def _generate_playground_css(self) -> str:
        """
        Generate CSS for code playgrounds.

        Returns:
            CSS content
        """
        return """
/* Playground styles */
.playground {
    margin-bottom: 1.5em;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    overflow: hidden;
}

.playground-header {
    background-color: #f0f0f0;
    padding: 8px;
    display: flex;
    justify-content: flex-end;
}

.playground button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    margin-left: 8px;
    cursor: pointer;
    font-size: 14px;
}

.playground button:hover {
    background-color: var(--primary-dark);
}

.playground-output {
    background-color: #f8f8f8;
    border-top: 1px solid var(--border-color);
    padding: 12px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    white-space: pre-wrap;
    overflow-x: auto;
}

.playground-output.hidden {
    display: none;
}

.playground-output.error {
    background-color: #fee;
    color: #c00;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    .playground-header {
        background-color: #333;
    }
    
    .playground-output {
        background-color: #2a2a2a;
    }
    
    .playground-output.error {
        background-color: #422;
        color: #f66;
    }
}
"""

    def _generate_playground_js(self) -> str:
        """
        Generate JavaScript for code playgrounds.

        Returns:
            JavaScript content
        """
        return """
document.addEventListener('DOMContentLoaded', function() {
    // Initialize playgrounds
    const playgrounds = document.querySelectorAll('.playground');
    
    playgrounds.forEach(playground => {
        const runButton = playground.querySelector('.playground-run');
        const resetButton = playground.querySelector('.playground-reset');
        const codeBlock = playground.querySelector('code');
        const output = playground.querySelector('.playground-output');
        
        // Store the original code
        const originalCode = codeBlock.textContent;
        
        // Run button
        if (runButton) {
            runButton.addEventListener('click', function() {
                const code = codeBlock.textContent;
                
                // Show output
                output.classList.remove('hidden');
                output.classList.remove('error');
                output.textContent = 'Running...';
                
                // Execute code in a web worker or send to a server
                executeCode(code)
                    .then(result => {
                        output.textContent = result;
                    })
                    .catch(error => {
                        output.classList.add('error');
                        output.textContent = `Error: ${error.message}`;
                    });
            });
        }
        
        // Reset button
        if (resetButton) {
            resetButton.addEventListener('click', function() {
                codeBlock.textContent = originalCode;
                output.classList.add('hidden');
                
                // Re-apply syntax highlighting if available
                if (window.hljs) {
                    hljs.highlightBlock(codeBlock);
                }
            });
        }
        
        // Make code block editable
        if (codeBlock) {
            codeBlock.contentEditable = 'true';
            codeBlock.spellcheck = false;
        }
    });
    
    // Function to execute code (placeholder - would need a backend service)
    async function executeCode(code) {
        // In a real implementation, this would send the code to a server
        // For this demo, we'll just return a message
        return 'Code execution is not available in this preview.\n\nIn a real implementation, this would execute the code and return the result.';
    }
});
"""
