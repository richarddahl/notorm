"""
OpenAPI extensions for endpoint classes.

This module provides extension classes that add OpenAPI documentation capabilities
to the existing endpoint framework classes.
"""

from typing import Any, Dict, List, Optional, Type, Union, get_type_hints

from fastapi import FastAPI
from pydantic import BaseModel

from uno.domain.entity.service import ApplicationService, CrudService, DomainService

from .base import BaseEndpoint, CommandEndpoint, CrudEndpoint, QueryEndpoint
from .cqrs import CqrsEndpoint
from .filter.endpoints import FilterableCrudEndpoint, FilterableCqrsEndpoint
from .openapi import OpenApiEnhancer, ResponseExample

__all__ = [
    "DocumentedBaseEndpoint",
    "DocumentedCrudEndpoint",
    "DocumentedQueryEndpoint",
    "DocumentedCommandEndpoint",
    "DocumentedCqrsEndpoint",
    "DocumentedFilterableCrudEndpoint",
    "DocumentedFilterableCqrsEndpoint",
]


class DocumentedBaseEndpoint(BaseEndpoint):
    """
    Base endpoint with OpenAPI documentation support.

    This class extends BaseEndpoint with methods for generating and customizing
    OpenAPI documentation for the endpoint.
    """

    def __init__(
        self,
        *,
        router=None,
        tags=None,
        summary: str | None = None,
        description: str | None = None,
    ):
        """
        Initialize a new documented endpoint instance.

        Args:
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            summary: Optional summary of the endpoint.
            description: Optional description of the endpoint.
        """
        super().__init__(router=router, tags=tags)
        self.summary = summary
        self.description = description
        self.operation_docs: dict[str, dict[str, Any]] = {}

    def register(self, app: FastAPI, prefix: str = "") -> None:
        """
        Register this endpoint with a FastAPI application.

        This method registers the endpoint routes and documentation with the application.

        Args:
            app: The FastAPI application to register with.
            prefix: An optional URL prefix to add to all routes.
        """
        # Register routes
        super().register(app, prefix)

        # Register documentation
        enhancer = OpenApiEnhancer(app)

        for path, method, doc in self._get_operations():
            full_path = f"{prefix}{path}"
            enhancer.document_operation(full_path, method, **doc)

    def _get_operations(self) -> list[tuple]:
        """
        Get the operations defined by this endpoint.

        Returns:
            A list of tuples (path, method, docs) for each operation.
        """
        return []

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
        responses: Optional[dict[str, ResponseExample]] = None,
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
            "summary": summary,
            "description": description,
            "operation_id": operation_id,
            "tags": tags or self.tags,
            "deprecated": deprecated,
            "responses": responses,
            "security": security,
        }


class DocumentedCrudEndpoint(CrudEndpoint, DocumentedBaseEndpoint):
    """
    CRUD endpoint with OpenAPI documentation support.

    This class extends CrudEndpoint with methods for generating and customizing
    OpenAPI documentation for CRUD operations.
    """

    def __init__(
        self,
        *,
        service: CrudService,
        create_model: Type,
        response_model: Type,
        update_model: Optional[Type] = None,
        router=None,
        tags=None,
        path: str = "",
        id_field: str = "id",
        summary: str | None = None,
        description: str | None = None,
        operation_examples: Optional[dict[str, dict[str, Any]]] = None,
    ):
        """
        Initialize a new documented CRUD endpoint instance.

        Args:
            service: The CrudService to use for operations.
            create_model: The Pydantic model for creation requests.
            response_model: The Pydantic model for responses.
            update_model: Optional separate model for update requests.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            path: The base path for routes, defaults to "".
            id_field: The name of the ID field in the entity.
            summary: Optional summary of the endpoint.
            description: Optional description of the endpoint.
            operation_examples: Optional examples for operations.
        """
        CrudEndpoint.__init__(
            self,
            service=service,
            create_model=create_model,
            response_model=response_model,
            update_model=update_model,
            router=router,
            tags=tags,
            path=path,
            id_field=id_field,
        )

        self.summary = summary
        self.description = description
        self.operation_docs = {}
        self.operation_examples = operation_examples or {}

        # Add default documentation for CRUD operations
        self._add_default_documentation()

    def _add_default_documentation(self) -> None:
        """Add default documentation for CRUD operations."""
        entity_name = self.response_model.__name__.replace("DTO", "").replace(
            "Response", ""
        )

        # Create operation
        self.document_operation(
            self.path,
            "post",
            summary=f"Create a new {entity_name}",
            description=f"Creates a new {entity_name} with the provided data.",
            operation_id=f"create{entity_name}",
            responses=self._get_operation_examples("create"),
        )

        # Get operation
        self.document_operation(
            f"{self.path}/{{id}}",
            "get",
            summary=f"Get a {entity_name} by ID",
            description=f"Retrieves a {entity_name} by its unique identifier.",
            operation_id=f"get{entity_name}ById",
            responses=self._get_operation_examples("get"),
        )

        # List operation
        self.document_operation(
            self.path,
            "get",
            summary=f"List all {entity_name}s",
            description=f"Retrieves a list of all {entity_name}s.",
            operation_id=f"list{entity_name}s",
            responses=self._get_operation_examples("list"),
        )

        # Update operation
        self.document_operation(
            f"{self.path}/{{id}}",
            "put",
            summary=f"Update a {entity_name}",
            description=f"Updates an existing {entity_name} with the provided data.",
            operation_id=f"update{entity_name}",
            responses=self._get_operation_examples("update"),
        )

        # Delete operation
        self.document_operation(
            f"{self.path}/{{id}}",
            "delete",
            summary=f"Delete a {entity_name}",
            description=f"Deletes an existing {entity_name}.",
            operation_id=f"delete{entity_name}",
            responses=self._get_operation_examples("delete"),
        )

    def _get_operation_examples(self, operation: str) -> dict[str, ResponseExample]:
        """
        Get examples for a specific operation.

        Args:
            operation: The operation name (create, get, list, update, delete).

        Returns:
            A dictionary of response examples for different status codes.
        """
        examples = {}

        if operation in self.operation_examples:
            operation_examples = self.operation_examples[operation]

            # Process examples for different status codes
            for status_code, data in operation_examples.items():
                if (
                    isinstance(data, dict)
                    and "content" in data
                    and "description" in data
                ):
                    # Example is already in the correct format
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data["content"],
                        description=data["description"],
                    )
                else:
                    # Example is just the content
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data,
                    )

        # Add default examples if none provided
        if not examples:
            entity_name = self.response_model.__name__.replace("DTO", "").replace(
                "Response", ""
            )

            if operation == "create":
                examples["201"] = ResponseExample(
                    status_code=201,
                    example={"id": "123", "name": f"Example {entity_name}"},
                    description=f"The {entity_name} was created successfully.",
                )
                examples["400"] = ResponseExample(
                    status_code=400,
                    example={
                        "message": "Invalid input data",
                        "code": "VALIDATION_ERROR",
                    },
                    description="The request data was invalid.",
                )

            elif operation == "get":
                examples["200"] = ResponseExample(
                    status_code=200,
                    example={"id": "123", "name": f"Example {entity_name}"},
                    description=f"The {entity_name} was retrieved successfully.",
                )
                examples["404"] = ResponseExample(
                    status_code=404,
                    example={
                        "message": f"{entity_name} not found",
                        "code": "NOT_FOUND",
                    },
                    description=f"The requested {entity_name} does not exist.",
                )

            elif operation == "list":
                examples["200"] = ResponseExample(
                    status_code=200,
                    example=[{"id": "123", "name": f"Example {entity_name}"}],
                    description=f"A list of {entity_name}s was retrieved successfully.",
                )

            elif operation == "update":
                examples["200"] = ResponseExample(
                    status_code=200,
                    example={"id": "123", "name": f"Updated {entity_name}"},
                    description=f"The {entity_name} was updated successfully.",
                )
                examples["404"] = ResponseExample(
                    status_code=404,
                    example={
                        "message": f"{entity_name} not found",
                        "code": "NOT_FOUND",
                    },
                    description=f"The requested {entity_name} does not exist.",
                )
                examples["400"] = ResponseExample(
                    status_code=400,
                    example={
                        "message": "Invalid input data",
                        "code": "VALIDATION_ERROR",
                    },
                    description="The request data was invalid.",
                )

            elif operation == "delete":
                examples["204"] = ResponseExample(
                    status_code=204,
                    example=None,
                    description=f"The {entity_name} was deleted successfully.",
                )
                examples["404"] = ResponseExample(
                    status_code=404,
                    example={
                        "message": f"{entity_name} not found",
                        "code": "NOT_FOUND",
                    },
                    description=f"The requested {entity_name} does not exist.",
                )

        return examples

    def _get_operations(self) -> list[tuple]:
        """
        Get the operations defined by this endpoint.

        Returns:
            A list of tuples (path, method, docs) for each operation.
        """
        operations = []

        # Create operation
        if f"post:{self.path}" in self.operation_docs:
            operations.append(
                (self.path, "post", self.operation_docs[f"post:{self.path}"])
            )

        # Get operation
        if f"get:{self.path}/{{id}}" in self.operation_docs:
            operations.append(
                (
                    f"{self.path}/{{id}}",
                    "get",
                    self.operation_docs[f"get:{self.path}/{{id}}"],
                )
            )

        # List operation
        if f"get:{self.path}" in self.operation_docs:
            operations.append(
                (self.path, "get", self.operation_docs[f"get:{self.path}"])
            )

        # Update operation
        if f"put:{self.path}/{{id}}" in self.operation_docs:
            operations.append(
                (
                    f"{self.path}/{{id}}",
                    "put",
                    self.operation_docs[f"put:{self.path}/{{id}}"],
                )
            )

        # Delete operation
        if f"delete:{self.path}/{{id}}" in self.operation_docs:
            operations.append(
                (
                    f"{self.path}/{{id}}",
                    "delete",
                    self.operation_docs[f"delete:{self.path}/{{id}}"],
                )
            )

        return operations


class DocumentedQueryEndpoint(QueryEndpoint, DocumentedBaseEndpoint):
    """
    Query endpoint with OpenAPI documentation support.

    This class extends QueryEndpoint with methods for generating and customizing
    OpenAPI documentation for query operations.
    """

    def __init__(
        self,
        *,
        service: Union[ApplicationService, DomainService],
        response_model: Type,
        query_model: Optional[Type] = None,
        router=None,
        tags=None,
        path: str = "",
        method: str = "get",
        summary: str | None = None,
        description: str | None = None,
        operation_examples: Optional[dict[str, dict[str, Any]]] = None,
    ):
        """
        Initialize a new documented query endpoint instance.

        Args:
            service: The service to use for query operations.
            response_model: The Pydantic model for responses.
            query_model: Optional model for query parameters.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            path: The path for the query endpoint.
            method: The HTTP method to use (default: "get").
            summary: Optional summary of the endpoint.
            description: Optional description of the endpoint.
            operation_examples: Optional examples for operations.
        """
        QueryEndpoint.__init__(
            self,
            service=service,
            response_model=response_model,
            query_model=query_model,
            router=router,
            tags=tags,
            path=path,
            method=method,
        )

        self.summary = summary
        self.description = description
        self.operation_docs = {}
        self.operation_examples = operation_examples or {}

        # Add default documentation for query operation
        self._add_default_documentation()

    def _add_default_documentation(self) -> None:
        """Add default documentation for query operation."""
        operation_name = self.service.__class__.__name__.replace("Service", "").replace(
            "Query", ""
        )

        self.document_operation(
            self.path,
            self.method,
            summary=f"Execute {operation_name} query",
            description=self.description
            or f"Executes the {operation_name} query and returns the results.",
            operation_id=f"query{operation_name}",
            responses=self._get_operation_examples(),
        )

    def _get_operation_examples(self) -> dict[str, ResponseExample]:
        """
        Get examples for the query operation.

        Returns:
            A dictionary of response examples for different status codes.
        """
        examples = {}

        if "query" in self.operation_examples:
            operation_examples = self.operation_examples["query"]

            # Process examples for different status codes
            for status_code, data in operation_examples.items():
                if (
                    isinstance(data, dict)
                    and "content" in data
                    and "description" in data
                ):
                    # Example is already in the correct format
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data["content"],
                        description=data["description"],
                    )
                else:
                    # Example is just the content
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data,
                    )

        # Add default examples if none provided
        if not examples:
            operation_name = self.service.__class__.__name__.replace(
                "Service", ""
            ).replace("Query", "")

            examples["200"] = ResponseExample(
                status_code=200,
                example={"result": "Example query result"},
                description=f"The {operation_name} query was executed successfully.",
            )
            examples["400"] = ResponseExample(
                status_code=400,
                example={
                    "message": "Invalid query parameters",
                    "code": "VALIDATION_ERROR",
                },
                description="The query parameters were invalid.",
            )

        return examples

    def _get_operations(self) -> list[tuple]:
        """
        Get the operations defined by this endpoint.

        Returns:
            A list of tuples (path, method, docs) for each operation.
        """
        operations = []

        # Query operation
        key = f"{self.method}:{self.path}"
        if key in self.operation_docs:
            operations.append((self.path, self.method, self.operation_docs[key]))

        return operations


class DocumentedCommandEndpoint(CommandEndpoint, DocumentedBaseEndpoint):
    """
    Command endpoint with OpenAPI documentation support.

    This class extends CommandEndpoint with methods for generating and customizing
    OpenAPI documentation for command operations.
    """

    def __init__(
        self,
        *,
        service: Union[ApplicationService, DomainService],
        command_model: Type,
        response_model: Optional[Type] = None,
        router=None,
        tags=None,
        path: str = "",
        method: str = "post",
        summary: str | None = None,
        description: str | None = None,
        operation_examples: Optional[dict[str, dict[str, Any]]] = None,
    ):
        """
        Initialize a new documented command endpoint instance.

        Args:
            service: The service to use for command operations.
            command_model: The Pydantic model for command data.
            response_model: Optional model for command responses.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            path: The path for the command endpoint.
            method: The HTTP method to use (default: "post").
            summary: Optional summary of the endpoint.
            description: Optional description of the endpoint.
            operation_examples: Optional examples for operations.
        """
        CommandEndpoint.__init__(
            self,
            service=service,
            command_model=command_model,
            response_model=response_model,
            router=router,
            tags=tags,
            path=path,
            method=method,
        )

        self.summary = summary
        self.description = description
        self.operation_docs = {}
        self.operation_examples = operation_examples or {}

        # Add default documentation for command operation
        self._add_default_documentation()

    def _add_default_documentation(self) -> None:
        """Add default documentation for command operation."""
        operation_name = self.service.__class__.__name__.replace("Service", "").replace(
            "Command", ""
        )

        self.document_operation(
            self.path,
            self.method,
            summary=f"Execute {operation_name} command",
            description=self.description
            or f"Executes the {operation_name} command with the provided data.",
            operation_id=f"command{operation_name}",
            responses=self._get_operation_examples(),
        )

    def _get_operation_examples(self) -> dict[str, ResponseExample]:
        """
        Get examples for the command operation.

        Returns:
            A dictionary of response examples for different status codes.
        """
        examples = {}

        if "command" in self.operation_examples:
            operation_examples = self.operation_examples["command"]

            # Process examples for different status codes
            for status_code, data in operation_examples.items():
                if (
                    isinstance(data, dict)
                    and "content" in data
                    and "description" in data
                ):
                    # Example is already in the correct format
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data["content"],
                        description=data["description"],
                    )
                else:
                    # Example is just the content
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data,
                    )

        # Add default examples if none provided
        if not examples:
            operation_name = self.service.__class__.__name__.replace(
                "Service", ""
            ).replace("Command", "")

            if self.response_model:
                examples["201"] = ResponseExample(
                    status_code=201,
                    example={"result": "Example command result"},
                    description=f"The {operation_name} command was executed successfully.",
                )
            else:
                examples["204"] = ResponseExample(
                    status_code=204,
                    example=None,
                    description=f"The {operation_name} command was executed successfully.",
                )

            examples["400"] = ResponseExample(
                status_code=400,
                example={"message": "Invalid command data", "code": "VALIDATION_ERROR"},
                description="The command data was invalid.",
            )

        return examples

    def _get_operations(self) -> list[tuple]:
        """
        Get the operations defined by this endpoint.

        Returns:
            A list of tuples (path, method, docs) for each operation.
        """
        operations = []

        # Command operation
        key = f"{self.method}:{self.path}"
        if key in self.operation_docs:
            operations.append((self.path, self.method, self.operation_docs[key]))

        return operations


class DocumentedCqrsEndpoint(CqrsEndpoint, DocumentedBaseEndpoint):
    """
    CQRS endpoint with OpenAPI documentation support.

    This class extends CqrsEndpoint with methods for generating and customizing
    OpenAPI documentation for CQRS operations.
    """

    def __init__(self, **kwargs):
        """
        Initialize a new documented CQRS endpoint instance.

        Args:
            **kwargs: Arguments to pass to CqrsEndpoint.__init__
        """
        # Extract documentation-specific parameters
        summary = kwargs.pop("summary", None)
        description = kwargs.pop("description", None)
        operation_examples = kwargs.pop("operation_examples", {})

        # Initialize base classes
        CqrsEndpoint.__init__(self, **kwargs)

        self.summary = summary
        self.description = description
        self.operation_docs = {}
        self.operation_examples = operation_examples

        # Add default documentation for operations
        self._add_default_documentation()

    def _add_default_documentation(self) -> None:
        """Add default documentation for CQRS operations."""
        # Documentation for queries
        for i, query_handler in enumerate(self.queries):
            path = f"{query_handler.path}"
            method = query_handler.method
            operation_name = getattr(query_handler, "name", f"Query{i+1}")

            self.document_operation(
                path,
                method,
                summary=f"Execute {operation_name} query",
                description=f"Executes the {operation_name} query and returns the results.",
                operation_id=f"query{operation_name}",
                responses=self._get_operation_examples(f"query_{operation_name}"),
            )

        # Documentation for commands
        for i, command_handler in enumerate(self.commands):
            path = f"{command_handler.path}"
            method = command_handler.method
            operation_name = getattr(command_handler, "name", f"Command{i+1}")

            self.document_operation(
                path,
                method,
                summary=f"Execute {operation_name} command",
                description=f"Executes the {operation_name} command with the provided data.",
                operation_id=f"command{operation_name}",
                responses=self._get_operation_examples(f"command_{operation_name}"),
            )

    def _get_operation_examples(self, operation_key: str) -> dict[str, ResponseExample]:
        """
        Get examples for a specific operation.

        Args:
            operation_key: The key for the operation examples.

        Returns:
            A dictionary of response examples for different status codes.
        """
        examples = {}

        if operation_key in self.operation_examples:
            operation_examples = self.operation_examples[operation_key]

            # Process examples for different status codes
            for status_code, data in operation_examples.items():
                if (
                    isinstance(data, dict)
                    and "content" in data
                    and "description" in data
                ):
                    # Example is already in the correct format
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data["content"],
                        description=data["description"],
                    )
                else:
                    # Example is just the content
                    examples[status_code] = ResponseExample(
                        status_code=status_code,
                        example=data,
                    )

        # Add default examples if none provided
        if not examples:
            is_query = operation_key.startswith("query_")
            operation_name = (
                operation_key.split("_", 1)[1]
                if "_" in operation_key
                else operation_key
            )

            if is_query:
                examples["200"] = ResponseExample(
                    status_code=200,
                    example={"result": "Example query result"},
                    description=f"The {operation_name} query was executed successfully.",
                )
                examples["400"] = ResponseExample(
                    status_code=400,
                    example={
                        "message": "Invalid query parameters",
                        "code": "VALIDATION_ERROR",
                    },
                    description="The query parameters were invalid.",
                )
            else:
                examples["201"] = ResponseExample(
                    status_code=201,
                    example={"result": "Example command result"},
                    description=f"The {operation_name} command was executed successfully.",
                )
                examples["400"] = ResponseExample(
                    status_code=400,
                    example={
                        "message": "Invalid command data",
                        "code": "VALIDATION_ERROR",
                    },
                    description="The command data was invalid.",
                )

        return examples

    def _get_operations(self) -> list[tuple]:
        """
        Get the operations defined by this endpoint.

        Returns:
            A list of tuples (path, method, docs) for each operation.
        """
        operations = []

        # Collect all operation docs
        for key, doc in self.operation_docs.items():
            method, path = key.split(":", 1)
            operations.append((path, method, doc))

        return operations


class DocumentedFilterableCrudEndpoint(FilterableCrudEndpoint, DocumentedCrudEndpoint):
    """
    Filterable CRUD endpoint with OpenAPI documentation support.

    This class extends FilterableCrudEndpoint with methods for generating and customizing
    OpenAPI documentation for filterable CRUD operations.
    """

    def __init__(self, **kwargs):
        """
        Initialize a new documented filterable CRUD endpoint instance.

        Args:
            **kwargs: Arguments to pass to FilterableCrudEndpoint.__init__
        """
        # Extract documentation-specific parameters
        summary = kwargs.pop("summary", None)
        description = kwargs.pop("description", None)
        operation_examples = kwargs.pop("operation_examples", {})

        # Initialize base classes
        FilterableCrudEndpoint.__init__(self, **kwargs)

        self.summary = summary
        self.description = description
        self.operation_docs = {}
        self.operation_examples = operation_examples

        # Add default documentation for operations
        self._add_default_documentation()
        self._add_filter_documentation()

    def _add_filter_documentation(self) -> None:
        """Add documentation for filtering capabilities."""
        entity_name = self.response_model.__name__.replace("DTO", "").replace(
            "Response", ""
        )

        # Update the list operation to include filtering
        self.document_operation(
            self.path,
            "get",
            summary=f"List and filter {entity_name}s",
            description=(
                f"Retrieves a list of {entity_name}s that match the specified filters.\n\n"
                f"## Filtering Capabilities\n\n"
                f"- **Field filtering**: Filter by field values using query parameters (e.g., `?name=John`)\n"
                f"- **Operator filtering**: Use operators for more complex filtering (e.g., `?name__contains=John`)\n"
                f"- **Multiple filters**: Combine multiple filters (e.g., `?name__contains=John&age__gt=30`)\n"
                f"- **Pagination**: Use `limit` and `offset` parameters for pagination\n"
                f"- **Sorting**: Use `sort` parameter for sorting (e.g., `?sort=name`, `?sort=-age` for descending)"
            ),
            operation_id=f"filter{entity_name}s",
            responses=self._get_operation_examples("list"),
        )


class DocumentedFilterableCqrsEndpoint(FilterableCqrsEndpoint, DocumentedCqrsEndpoint):
    """
    Filterable CQRS endpoint with OpenAPI documentation support.

    This class extends FilterableCqrsEndpoint with methods for generating and customizing
    OpenAPI documentation for filterable CQRS operations.
    """

    def __init__(self, **kwargs):
        """
        Initialize a new documented filterable CQRS endpoint instance.

        Args:
            **kwargs: Arguments to pass to FilterableCqrsEndpoint.__init__
        """
        # Extract documentation-specific parameters
        summary = kwargs.pop("summary", None)
        description = kwargs.pop("description", None)
        operation_examples = kwargs.pop("operation_examples", {})

        # Initialize base classes
        FilterableCqrsEndpoint.__init__(self, **kwargs)

        self.summary = summary
        self.description = description
        self.operation_docs = {}
        self.operation_examples = operation_examples

        # Add default documentation for operations
        self._add_default_documentation()
        self._add_filter_documentation()

    def _add_filter_documentation(self) -> None:
        """Add documentation for filtering capabilities."""
        # Update query operations that support filtering
        for i, query_handler in enumerate(self.queries):
            if (
                hasattr(query_handler, "supports_filtering")
                and query_handler.supports_filtering
            ):
                path = f"{query_handler.path}"
                method = query_handler.method
                operation_name = getattr(query_handler, "name", f"Query{i+1}")

                self.document_operation(
                    path,
                    method,
                    summary=f"Execute {operation_name} query with filtering",
                    description=(
                        f"Executes the {operation_name} query with filtering capabilities.\n\n"
                        f"## Filtering Capabilities\n\n"
                        f"- **Field filtering**: Filter by field values using query parameters (e.g., `?name=John`)\n"
                        f"- **Operator filtering**: Use operators for more complex filtering (e.g., `?name__contains=John`)\n"
                        f"- **Multiple filters**: Combine multiple filters (e.g., `?name__contains=John&age__gt=30`)\n"
                        f"- **Pagination**: Use `limit` and `offset` parameters for pagination\n"
                        f"- **Sorting**: Use `sort` parameter for sorting (e.g., `?sort=name`, `?sort=-age` for descending)"
                    ),
                    operation_id=f"query{operation_name}WithFilters",
                    responses=self._get_operation_examples(f"query_{operation_name}"),
                )
