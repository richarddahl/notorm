"""
OpenAPI documentation utilities for the unified endpoint framework.

This module provides utilities for enhancing FastAPI's OpenAPI schema generation,
including response examples, security documentation, and schema customization.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union

from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

__all__ = [
    "ApiDocumentation",
    "ResponseExample",
    "add_response_example",
    "add_security_schema",
    "add_operation_id",
    "document_operation",
    "OpenApiEnhancer",
]


class ResponseExample:
    """
    A response example for OpenAPI documentation.

    This class stores example data for specific response codes and content types.
    """

    def __init__(
        self,
        status_code: Union[int, str],
        content_type: str = "application/json",
        example: Optional[Dict[str, Any]] = None,
        description: str | None = None,
    ):
        """
        Initialize a new response example.

        Args:
            status_code: HTTP status code or string code (e.g., "200" or "2XX").
            content_type: Media type of the response.
            example: Example data for the response.
            description: Optional description of the response.
        """
        self.status_code = str(status_code)
        self.content_type = content_type
        self.example = example or {}
        self.description = description


def add_response_example(
    app: FastAPI,
    path: str,
    method: str,
    example: ResponseExample,
) -> None:
    """
    Add a response example to a FastAPI operation.

    Args:
        app: The FastAPI application.
        path: The path of the operation.
        method: The HTTP method of the operation.
        example: The example to add.
    """
    if not hasattr(app, "openapi_schema"):
        # Generate the schema first
        app.openapi()

    schema = app.openapi_schema
    if schema is None:
        return

    # Ensure the path and method exist in the schema
    if path not in schema["paths"]:
        return
    if method.lower() not in schema["paths"][path]:
        return

    operation = schema["paths"][path][method.lower()]

    # Ensure the responses section exists
    if "responses" not in operation:
        operation["responses"] = {}

    # Add or update the response for this status code
    if example.status_code not in operation["responses"]:
        operation["responses"][example.status_code] = {}

    response = operation["responses"][example.status_code]

    # Add or update description
    if example.description:
        response["description"] = example.description
    elif "description" not in response:
        response["description"] = f"Response with status code {example.status_code}"

    # Add or update content
    if "content" not in response:
        response["content"] = {}

    if example.content_type not in response["content"]:
        response["content"][example.content_type] = {}

    content = response["content"][example.content_type]

    # Add example
    if "examples" not in content:
        content["examples"] = {}

    example_key = f"example_{len(content['examples']) + 1}"
    content["examples"][example_key] = {"value": example.example}


def add_security_schema(
    app: FastAPI,
    schema_name: str,
    schema_type: str,
    schema_data: Dict[str, Any],
) -> None:
    """
    Add a security schema to a FastAPI application.

    Args:
        app: The FastAPI application.
        schema_name: The name of the security schema.
        schema_type: The type of the security schema (e.g., "http", "apiKey").
        schema_data: Additional data for the security schema.
    """
    if not hasattr(app, "openapi_schema"):
        # Generate the schema first
        app.openapi()

    schema = app.openapi_schema
    if schema is None:
        return

    # Ensure security schemes exist
    if "components" not in schema:
        schema["components"] = {}

    if "securitySchemes" not in schema["components"]:
        schema["components"]["securitySchemes"] = {}

    # Add the security schema
    schema["components"]["securitySchemes"][schema_name] = {
        "type": schema_type,
        **schema_data,
    }


def add_operation_id(
    app: FastAPI,
    path: str,
    method: str,
    operation_id: str,
) -> None:
    """
    Add an operationId to a FastAPI operation.

    Args:
        app: The FastAPI application.
        path: The path of the operation.
        method: The HTTP method of the operation.
        operation_id: The operation ID to add.
    """
    if not hasattr(app, "openapi_schema"):
        # Generate the schema first
        app.openapi()

    schema = app.openapi_schema
    if schema is None:
        return

    # Ensure the path and method exist in the schema
    if path not in schema["paths"]:
        return
    if method.lower() not in schema["paths"][path]:
        return

    operation = schema["paths"][path][method.lower()]

    # Add or update the operationId
    operation["operationId"] = operation_id


def document_operation(
    app: FastAPI,
    path: str,
    method: str,
    *,
    summary: str | None = None,
    description: str | None = None,
    operation_id: str | None = None,
    tags: list[str] | None = None,
    deprecated: Optional[bool] = None,
    responses: Optional[Dict[str, ResponseExample]] = None,
    security: Optional[list[dict[str, list[str]]]] = None,
) -> None:
    """
    Add comprehensive documentation to a FastAPI operation.

    Args:
        app: The FastAPI application.
        path: The path of the operation.
        method: The HTTP method of the operation.
        summary: Optional summary of the operation.
        description: Optional description of the operation.
        operation_id: Optional operation ID.
        tags: Optional tags for the operation.
        deprecated: Whether the operation is deprecated.
        responses: Optional examples for different response codes.
        security: Optional security requirements for the operation.
    """
    if not hasattr(app, "openapi_schema"):
        # Generate the schema first
        app.openapi()

    schema = app.openapi_schema
    if schema is None:
        return

    # Ensure the path and method exist in the schema
    if path not in schema["paths"]:
        return
    if method.lower() not in schema["paths"][path]:
        return

    operation = schema["paths"][path][method.lower()]

    # Update operation documentation
    if summary:
        operation["summary"] = summary

    if description:
        operation["description"] = description

    if operation_id:
        operation["operationId"] = operation_id

    if tags:
        operation["tags"] = tags

    if deprecated is not None:
        operation["deprecated"] = deprecated

    if security:
        operation["security"] = security

    # Add response examples
    if responses:
        for status_code, example in responses.items():
            add_response_example(app, path, method, example)


class ApiDocumentation:
    """
    API documentation container class.

    This class stores documentation metadata for API endpoints and provides
    methods for registering that documentation with a FastAPI application.
    """

    def __init__(
        self,
        *,
        title: str,
        description: str | None = None,
        version: str = "0.1.0",
        openapi_tags: Optional[list[dict[str, str]]] = None,
        contact: Optional[Dict[str, str]] = None,
        license_info: Optional[Dict[str, str]] = None,
        security_schemas: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """
        Initialize a new API documentation container.

        Args:
            title: The title of the API.
            description: Optional description of the API.
            version: The version of the API.
            openapi_tags: Optional tags for the OpenAPI schema.
            contact: Optional contact information.
            license_info: Optional license information.
            security_schemas: Optional security schemas.
        """
        self.title = title
        self.description = description
        self.version = version
        self.openapi_tags = openapi_tags or []
        self.contact = contact
        self.license_info = license_info
        self.security_schemas = security_schemas or {}
        self.operation_docs: Dict[str, Dict[str, Any]] = {}

    def document_operation(
        self,
        path: str,
        method: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        operation_id: str | None = None,
        tags: list[str] | None = None,
        deprecated: Optional[bool] = None,
        responses: Optional[Dict[str, ResponseExample]] = None,
        security: Optional[list[dict[str, list[str]]]] = None,
    ) -> None:
        """
        Add documentation to an operation.

        Args:
            path: The path of the operation.
            method: The HTTP method of the operation.
            summary: Optional summary of the operation.
            description: Optional description of the operation.
            operation_id: Optional operation ID.
            tags: Optional tags for the operation.
            deprecated: Whether the operation is deprecated.
            responses: Optional examples for different response codes.
            security: Optional security requirements for the operation.
        """
        key = f"{method.lower()}:{path}"
        self.operation_docs[key] = {
            "path": path,
            "method": method,
            "summary": summary,
            "description": description,
            "operation_id": operation_id,
            "tags": tags,
            "deprecated": deprecated,
            "responses": responses,
            "security": security,
        }

    def add_security_schema(
        self,
        schema_name: str,
        schema_type: str,
        schema_data: Dict[str, Any],
    ) -> None:
        """
        Add a security schema.

        Args:
            schema_name: The name of the security schema.
            schema_type: The type of the security schema.
            schema_data: Additional data for the security schema.
        """
        self.security_schemas[schema_name] = {
            "type": schema_type,
            **schema_data,
        }

    def add_tag(
        self,
        name: str,
        description: str | None = None,
        external_docs: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add a tag with detailed description.

        Args:
            name: The name of the tag.
            description: Optional description of the tag.
            external_docs: Optional external documentation URL.
        """
        tag = {"name": name}
        if description:
            tag["description"] = description
        if external_docs:
            tag["externalDocs"] = external_docs

        self.openapi_tags.append(tag)

    def register_with_app(self, app: FastAPI) -> None:
        """
        Register all documentation with a FastAPI application.

        Args:
            app: The FastAPI application.
        """

        # Override the OpenAPI schema generator
        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema

            # Generate the default schema
            openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                description=self.description,
                routes=app.routes,
            )

            # Add custom components
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}

            # Add security schemas
            if self.security_schemas:
                if "securitySchemes" not in openapi_schema["components"]:
                    openapi_schema["components"]["securitySchemes"] = {}

                for name, schema in self.security_schemas.items():
                    openapi_schema["components"]["securitySchemes"][name] = schema

            # Add tags
            if self.openapi_tags:
                openapi_schema["tags"] = self.openapi_tags

            # Add contact information
            if self.contact:
                if "info" not in openapi_schema:
                    openapi_schema["info"] = {}
                openapi_schema["info"]["contact"] = self.contact

            # Add license information
            if self.license_info:
                if "info" not in openapi_schema:
                    openapi_schema["info"] = {}
                openapi_schema["info"]["license"] = self.license_info

            # Set the schema
            app.openapi_schema = openapi_schema

            # Apply operation-specific documentation
            for doc in self.operation_docs.values():
                document_operation(
                    app,
                    doc["path"],
                    doc["method"],
                    summary=doc["summary"],
                    description=doc["description"],
                    operation_id=doc["operation_id"],
                    tags=doc["tags"],
                    deprecated=doc["deprecated"],
                    responses=doc["responses"],
                    security=doc["security"],
                )

            return app.openapi_schema

        # Set the custom OpenAPI schema generator
        app.openapi = custom_openapi


class OpenApiEnhancer:
    """
    Utility class for enhancing the OpenAPI schema of FastAPI applications.

    This class provides methods for customizing the OpenAPI schema with
    additional information, examples, and security requirements.
    """

    def __init__(self, app: FastAPI):
        """
        Initialize a new OpenAPI enhancer.

        Args:
            app: The FastAPI application to enhance.
        """
        self.app = app

        # Create documentation if it doesn't exist
        if not hasattr(self.app, "_api_documentation"):
            self.app._api_documentation = ApiDocumentation(
                title=self.app.title,
                description=self.app.description,
                version=self.app.version,
            )

    @property
    def documentation(self) -> ApiDocumentation:
        """Get the API documentation container."""
        return self.app._api_documentation

    def add_security_schema(
        self,
        schema_name: str,
        schema_type: str,
        schema_data: Dict[str, Any],
    ) -> None:
        """
        Add a security schema to the OpenAPI documentation.

        Args:
            schema_name: The name of the security schema.
            schema_type: The type of the security schema.
            schema_data: Additional data for the security schema.
        """
        self.documentation.add_security_schema(schema_name, schema_type, schema_data)

    def add_tag(
        self,
        name: str,
        description: str | None = None,
        external_docs: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add a tag with detailed description to the OpenAPI documentation.

        Args:
            name: The name of the tag.
            description: Optional description of the tag.
            external_docs: Optional external documentation URL.
        """
        self.documentation.add_tag(name, description, external_docs)

    def document_operation(
        self,
        path: str,
        method: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        operation_id: str | None = None,
        tags: list[str] | None = None,
        deprecated: Optional[bool] = None,
        responses: Optional[Dict[str, ResponseExample]] = None,
        security: Optional[list[dict[str, list[str]]]] = None,
    ) -> None:
        """
        Add comprehensive documentation to an operation.

        Args:
            path: The path of the operation.
            method: The HTTP method of the operation.
            summary: Optional summary of the operation.
            description: Optional description of the operation.
            operation_id: Optional operation ID.
            tags: Optional tags for the operation.
            deprecated: Whether the operation is deprecated.
            responses: Optional examples for different response codes.
            security: Optional security requirements for the operation.
        """
        self.documentation.document_operation(
            path,
            method,
            summary=summary,
            description=description,
            operation_id=operation_id,
            tags=tags,
            deprecated=deprecated,
            responses=responses,
            security=security,
        )

    def setup_jwt_auth(
        self,
        *,
        description: str = "JWT authentication",
        scheme_name: str = "BearerAuth",
    ) -> None:
        """
        Set up JWT authentication in the OpenAPI documentation.

        Args:
            description: Optional description of the authentication scheme.
            scheme_name: Optional name for the security scheme.
        """
        self.add_security_schema(
            scheme_name,
            "http",
            {
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": description,
            },
        )

    def setup_api_key_auth(
        self,
        *,
        name: str = "api_key",
        location: str = "header",
        description: str = "API key authentication",
        scheme_name: str = "ApiKeyAuth",
    ) -> None:
        """
        Set up API key authentication in the OpenAPI documentation.

        Args:
            name: The name of the API key parameter.
            location: The location of the API key (header, query, cookie).
            description: Optional description of the authentication scheme.
            scheme_name: Optional name for the security scheme.
        """
        self.add_security_schema(
            scheme_name,
            "apiKey",
            {
                "name": name,
                "in": location,
                "description": description,
            },
        )

    def apply(self) -> None:
        """Apply all enhancements to the FastAPI application."""
        self.documentation.register_with_app(self.app)
