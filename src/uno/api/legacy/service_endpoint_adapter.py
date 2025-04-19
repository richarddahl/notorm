"""
Domain service endpoint adapter for the uno framework API.

This module provides adapter classes that integrate domain services with the API endpoint system,
allowing endpoints to work with domain services in a consistent way.

DEPRECATED: This module is deprecated and will be removed in a future version.
Use the unified endpoint framework in `uno.api.endpoint` instead.
"""

import warnings

# Display deprecation warning
warnings.warn(
    "The uno.api.service_endpoint_adapter module is deprecated and will be removed in a future version. "
    "Use the unified endpoint framework in uno.api.endpoint instead.",
    DeprecationWarning,
    stacklevel=2,
)

import logging
import inspect
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Generic,
    Union,
    Protocol,
    Callable,
    Awaitable,
    cast,
    get_type_hints,
    get_origin,
    get_args,
)

from pydantic import BaseModel, create_model
from fastapi import HTTPException, status

from uno.core.errors.result import Result, Success, Failure
from uno.core.base.error import BaseError
from uno.domain.unified_services import (
    DomainService,
    ReadOnlyDomainService,
    EntityService,
    AggregateService,
    DomainServiceProtocol,
)


# Type variables
T = TypeVar("T")
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


def convert_to_pydantic_model(
    model_class: Type[Any], name: str = None
) -> Type[BaseModel]:
    """
    Convert a class to a Pydantic model if it's not already one.

    Args:
        model_class: The class to convert
        name: Optional name for the created model

    Returns:
        A Pydantic model class
    """
    if issubclass(model_class, BaseModel):
        return model_class

    # Get annotations and create a dynamic model
    annotations = get_type_hints(model_class)
    model_name = name or f"{model_class.__name__}Model"

    # Create a Pydantic model from the annotations
    return create_model(
        model_name, **{field: (typ, ...) for field, typ in annotations.items()}
    )


def get_service_io_models(
    service_class: Type[DomainServiceProtocol],
) -> tuple[Optional[Type], Optional[Type]]:
    """
    Extract input and output models from a domain service class.

    Args:
        service_class: The domain service class

    Returns:
        Tuple of (input_model, output_model) or (None, None) if not determinable
    """
    try:
        # Get generic type parameters
        if hasattr(service_class, "__orig_bases__"):
            for base in service_class.__orig_bases__:
                if get_origin(base) in {DomainService, ReadOnlyDomainService}:
                    type_args = get_args(base)
                    if len(type_args) >= 2:
                        input_model = type_args[0]
                        output_model = type_args[1]
                        return input_model, output_model

        # Try to get types from execute method
        hints = get_type_hints(service_class.execute)
        if "input_data" in hints and "return" in hints:
            input_model = hints["input_data"]

            # Extract output type from Result
            return_type = hints["return"]
            if get_origin(return_type) is Result:
                output_model = get_args(return_type)[0]
                return input_model, output_model

        # Couldn't determine types
        return None, None

    except Exception:
        return None, None


class DomainServiceAdapter(Generic[InputT, OutputT]):
    """
    Adapter to bridge domain services with API endpoints.

    This class wraps a domain service, providing methods with signatures
    compatible with the API endpoint system while using domain-driven practices underneath.

    Type Parameters:
        InputT: The input model type
        OutputT: The output model type
    """

    def __init__(
        self,
        service: DomainServiceProtocol,
        input_model: Optional[Type[InputT]] = None,
        output_model: Optional[Type[OutputT]] = None,
        error_handler: Optional[Callable[[Result], None]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the service adapter.

        Args:
            service: The domain service to adapt
            input_model: The input model type (will be inferred if not provided)
            output_model: The output model type (will be inferred if not provided)
            error_handler: Optional custom error handler
            logger: Optional logger for diagnostic output
        """
        self.service = service
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = error_handler or self._default_error_handler

        # Try to infer input and output models if not provided
        if input_model is None or output_model is None:
            inferred_input, inferred_output = get_service_io_models(service.__class__)
            self.input_model = input_model or inferred_input
            self.output_model = output_model or inferred_output
        else:
            self.input_model = input_model
            self.output_model = output_model

        # Ensure we have Pydantic models for FastAPI
        if self.input_model and not issubclass(self.input_model, BaseModel):
            self.input_model = convert_to_pydantic_model(
                self.input_model, f"{service.__class__.__name__}Input"
            )

        if self.output_model and not issubclass(self.output_model, BaseModel):
            self.output_model = convert_to_pydantic_model(
                self.output_model, f"{service.__class__.__name__}Output"
            )

    async def execute(self, input_data: Union[Dict[str, Any], BaseModel]) -> Any:
        """
        Execute the domain service operation.

        Args:
            input_data: The input data for the operation

        Returns:
            The operation result

        Raises:
            HTTPException: If the operation fails
        """
        try:
            # Convert to input model if needed
            if isinstance(input_data, dict) and self.input_model:
                input_obj = self.input_model(**input_data)
            elif isinstance(input_data, BaseModel) and self.input_model:
                # Convert between Pydantic models if needed
                if not isinstance(input_data, self.input_model):
                    input_obj = self.input_model(**input_data.model_dump())
                else:
                    input_obj = input_data
            else:
                input_obj = input_data

            # Execute the service operation
            result = await self.service.execute(input_obj)

            # Handle errors
            self.error_handler(result)

            # Return the result value
            return result.value

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log and wrap other exceptions
            self.logger.error(f"Error executing domain service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "INTERNAL_ERROR", "message": str(e)},
            )

    def _default_error_handler(self, result: Result) -> None:
        """
        Default error handler for Result objects.

        Args:
            result: The Result object to check for errors

        Raises:
            HTTPException: If the Result contains an error
        """
        if not result.is_success:
            error = result.error
            status_code = status.HTTP_400_BAD_REQUEST
            error_dict = {"message": str(error)}

            # Extract more information if it's a BaseError
            if isinstance(error, BaseError):
                error_dict["error"] = error.error_code or "ERROR"
                error_dict["detail"] = error.context

                # Map error codes to status codes
                if hasattr(error, "error_code"):
                    if error.error_code in {
                        "NOT_FOUND",
                        "ENTITY_NOT_FOUND",
                        "RESOURCE_NOT_FOUND",
                    }:
                        status_code = status.HTTP_404_NOT_FOUND
                    elif error.error_code in {"UNAUTHORIZED", "UNAUTHENTICATED"}:
                        status_code = status.HTTP_401_UNAUTHORIZED
                    elif error.error_code in {
                        "FORBIDDEN",
                        "ACCESS_DENIED",
                        "PERMISSION_DENIED",
                    }:
                        status_code = status.HTTP_403_FORBIDDEN
                    elif error.error_code in {"VALIDATION_ERROR", "INVALID_INPUT"}:
                        status_code = status.HTTP_400_BAD_REQUEST
                    elif error.error_code in {"INTERNAL_ERROR", "SYSTEM_ERROR"}:
                        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    elif error.error_code in {
                        "CONFLICT",
                        "ALREADY_EXISTS",
                        "DUPLICATE",
                    }:
                        status_code = status.HTTP_409_CONFLICT

            raise HTTPException(status_code=status_code, detail=error_dict)


class EntityServiceAdapter(Generic[T]):
    """
    Adapter to bridge entity services with API endpoints.

    This class wraps an EntityService to provide CRUD operations for API endpoints.

    Type Parameters:
        T: The entity type
    """

    def __init__(
        self,
        service: EntityService[T],
        entity_type: Type[T],
        input_model: Optional[Type[BaseModel]] = None,
        output_model: Optional[Type[BaseModel]] = None,
        error_handler: Optional[Callable[[Result], None]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the entity service adapter.

        Args:
            service: The entity service to adapt
            entity_type: The entity type
            input_model: Optional input model for creating/updating entities
            output_model: Optional output model for entity responses
            error_handler: Optional custom error handler
            logger: Optional logger for diagnostic output
        """
        self.service = service
        self.entity_type = entity_type
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = error_handler or self._default_error_handler

        # Use provided models or create them dynamically
        self.input_model = input_model or convert_to_pydantic_model(
            entity_type, f"{entity_type.__name__}Input"
        )
        self.output_model = output_model or convert_to_pydantic_model(
            entity_type, f"{entity_type.__name__}Output"
        )

        # Set names for OpenAPI docs
        entity_name = getattr(entity_type, "__name__", "Entity")
        self.display_name = getattr(entity_type, "display_name", entity_name)
        self.display_name_plural = getattr(
            entity_type, "display_name_plural", f"{self.display_name}s"
        )

    async def get(self, id: str, **kwargs) -> Any:
        """
        Get an entity by ID.

        Args:
            id: The entity ID
            **kwargs: Additional parameters

        Returns:
            The entity if found

        Raises:
            HTTPException: If the entity is not found or another error occurs
        """
        result = await self.service.get_by_id(id)
        self.error_handler(result)

        entity = result.value
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ENTITY_NOT_FOUND",
                    "message": f"{self.display_name} with ID {id} not found",
                },
            )

        return entity

    async def filter(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50,
        **kwargs,
    ) -> Union[List[T], Dict[str, Any]]:
        """
        Filter entities based on criteria.

        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            **kwargs: Additional parameters

        Returns:
            List of entities or paginated result
        """
        # Apply ordering if specified
        order_by = None
        if "order_by" in kwargs:
            order_by = [kwargs["order_by"]]
            if "order_direction" in kwargs and kwargs["order_direction"] == "desc":
                order_by = [f"-{field}" for field in order_by]

        # Calculate offset for pagination
        offset = (page - 1) * page_size if page > 0 else 0

        # Get entities
        result = await self.service.find(filters or {})
        self.error_handler(result)
        entities = result.value

        # Get total count for pagination
        count_result = await self.service.count(filters or {})
        self.error_handler(count_result)
        total = count_result.value

        # Check if we need to return paginated results
        if kwargs.get("paginated", True):
            return {
                "items": entities,
                "page": page,
                "page_size": page_size,
                "total": total,
            }

        return entities

    async def save(self, data: Union[Dict[str, Any], BaseModel], **kwargs) -> T:
        """
        Create or update an entity.

        Args:
            data: The entity data
            **kwargs: Additional parameters

        Returns:
            The created or updated entity
        """
        # Convert to dict if it's a Pydantic model
        if isinstance(data, BaseModel):
            data_dict = data.model_dump()
        else:
            data_dict = data

        # Check if this is an update (has ID) or create
        entity_id = data_dict.get("id")

        if entity_id:
            # Update
            result = await self.service.update(entity_id, data_dict)
            self.error_handler(result)
            return result.value
        else:
            # Create
            result = await self.service.create(data_dict)
            self.error_handler(result)
            return result.value

    async def delete_(self, id: str, **kwargs) -> bool:
        """
        Delete an entity.

        Args:
            id: The entity ID
            **kwargs: Additional parameters

        Returns:
            True if successful
        """
        result = await self.service.delete(id)
        self.error_handler(result)
        return result.value

    def _default_error_handler(self, result: Result) -> None:
        """
        Default error handler for Result objects.

        Args:
            result: The Result object to check for errors

        Raises:
            HTTPException: If the Result contains an error
        """
        if not result.is_success:
            error = result.error
            status_code = status.HTTP_400_BAD_REQUEST
            error_dict = {"message": str(error)}

            # Extract more information if it's a BaseError
            if isinstance(error, BaseError):
                error_dict["error"] = error.error_code or "ERROR"
                error_dict["detail"] = error.context

                # Map error codes to status codes
                if hasattr(error, "error_code"):
                    if error.error_code in {
                        "NOT_FOUND",
                        "ENTITY_NOT_FOUND",
                        "RESOURCE_NOT_FOUND",
                    }:
                        status_code = status.HTTP_404_NOT_FOUND
                    elif error.error_code in {"UNAUTHORIZED", "UNAUTHENTICATED"}:
                        status_code = status.HTTP_401_UNAUTHORIZED
                    elif error.error_code in {
                        "FORBIDDEN",
                        "ACCESS_DENIED",
                        "PERMISSION_DENIED",
                    }:
                        status_code = status.HTTP_403_FORBIDDEN
                    elif error.error_code in {"VALIDATION_ERROR", "INVALID_INPUT"}:
                        status_code = status.HTTP_400_BAD_REQUEST
                    elif error.error_code in {"INTERNAL_ERROR", "SYSTEM_ERROR"}:
                        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    elif error.error_code in {
                        "CONFLICT",
                        "ALREADY_EXISTS",
                        "DUPLICATE",
                    }:
                        status_code = status.HTTP_409_CONFLICT

            raise HTTPException(status_code=status_code, detail=error_dict)
