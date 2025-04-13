# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Business logic layer objects for the Uno framework.

This module provides the UnoObj class, which serves as the business logic layer
for models in the Uno framework. It handles object lifecycle, data validation,
and business logic operations.
"""

import inspect
from typing import (
    Dict,
    Type,
    List,
    Optional,
    ClassVar,
    TypeVar,
    Generic,
    Any,
    get_origin,
    Union,
    cast,
    Tuple,
)

from pydantic import BaseModel, ConfigDict, Field, model_validator

from uno.core.types import FilterParam  # Use the core types to avoid circular import
from uno.model import UnoModel
from uno.schema.schema import UnoSchemaConfig
from uno.errors import UnoError, ValidationContext, ValidationError
from uno.utilities import snake_to_title
from uno.registry import get_registry
from uno.api.endpoint_factory import UnoEndpointFactory

# Import necessary protocols from core protocols
from uno.core.protocols import (
    SchemaManagerProtocol,
    FilterManagerProtocol,
    DBClientProtocol,
)

# Use deferred imports for implementations to avoid circular dependencies
def get_schema_manager() -> SchemaManagerProtocol:
    """Get the schema manager instance."""
    from uno.schema.schema_manager import UnoSchemaManager
    return UnoSchemaManager()

def get_filter_manager() -> FilterManagerProtocol:
    """Get the filter manager instance."""
    from uno.queries.filter_manager import UnoFilterManager
    return UnoFilterManager()

def get_db_factory(obj: Type[Any]) -> Any:
    """Get the database factory instance."""
    from uno.database.db_manager import UnoDBFactory
    return UnoDBFactory(obj=obj)


# Type variable for the UnoModel
T = TypeVar("T", bound=UnoModel)


class UnoObj(BaseModel, Generic[T]):
    """
    Business logic layer object for the Uno framework.

    This class provides business logic operations for models, including data validation,
    object lifecycle management, and integration with the web application.

    When subclassing UnoObj, you must explicitly set the 'model' class variable to your model class.
    For example:

        class MyObj(UnoObj[MyModel]):
            model = MyModel
            # ... rest of class definition
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    # Class variables
    model: ClassVar[Type[T]]  # Must be explicitly set in subclasses
    exclude_from_filters: ClassVar[bool] = False
    terminate_filters: ClassVar[bool] = False
    display_name: ClassVar[str] = None
    display_name_plural: ClassVar[str] = None
    schema_configs: ClassVar[Dict[str, UnoSchemaConfig]] = {}
    endpoints: ClassVar[List[str]] = [
        "Create",
        "View",
        "List",
        "Update",
        "Delete",
        "Import",
    ]
    endpoint_tags: ClassVar[List[str]] = []
    terminate_field_filters: ClassVar[List[str]] = []

    # Instance variables - these will be populated with values from the model
    id: Optional[str] = Field(None, description="Unique identifier for the object")

    # Runtime components - initialized in __init__
    db: DBClientProtocol = Field(None, exclude=True)
    schema_manager: SchemaManagerProtocol = Field(None, exclude=True)
    filter_manager: FilterManagerProtocol = Field(None, exclude=True)

    def __init__(self, **data: Any):
        """
        Initialize a UnoObj instance.

        Args:
            **data: The data to initialize the object with
        """
        super().__init__(**data)

        # Initialize the db factory using the deferred import
        self.db = get_db_factory(obj=self.__class__)

        # Initialize the schema manager using the deferred import
        schema_manager = get_schema_manager()
        # Add schema configs if available
        if hasattr(self.__class__, "schema_configs"):
            schema_manager.schema_configs = self.__class__.schema_configs
        self.schema_manager = schema_manager

        # Initialize the filter manager using the deferred import
        self.filter_manager = get_filter_manager()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize a UnoObj subclass.

        This method is called when a subclass of UnoObj is created. It registers
        the subclass in the registry and sets up display names. It also validates
        that the model class variable is explicitly set.

        Args:
            **kwargs: Additional keyword arguments
        """
        super().__init_subclass__(**kwargs)

        # Skip initialization for UnoObj itself
        if cls is UnoObj:
            return

        # Check if the class name contains brackets, which suggests it's a generic class
        # created by Pydantic's machinery rather than a user-defined class
        if "[" in cls.__name__:
            return

        # Check if model is explicitly set
        if not hasattr(cls, "model") or cls.model is None:
            raise TypeError(
                f"Class {cls.__name__} must specify a model class "
                f"as a class variable (model = ModelClass)"
            )

        # Set display names if not already set
        cls._set_display_names()

        # Register the class in the registry
        registry = get_registry()
        try:
            registry.register(cls, cls.model.__tablename__)
        except AttributeError:
            # Handle case where model or __tablename__ might not be available
            registry.register(cls, cls.__name__)

    @classmethod
    def _set_display_names(cls) -> None:
        """
        Set display names for the class if not already set.

        This method sets the display_name and display_name_plural class variables
        based on the model's table name if they are not already set.
        """
        try:
            table_name = cls.model.__table__.name
        except (AttributeError, TypeError):
            table_name = cls.__name__

        cls.display_name = (
            snake_to_title(table_name) if cls.display_name is None else cls.display_name
        )

        cls.display_name_plural = (
            f"{snake_to_title(table_name)}s"
            if cls.display_name_plural is None
            else cls.display_name_plural
        )

    def validate(self, schema_name: str) -> ValidationContext:
        """
        Validate the UnoObj instance against a schema.
        
        Args:
            schema_name: The name of the schema to validate against
            
        Returns:
            A validation context with any validation errors
            
        Raises:
            UnoError: If the schema is not found
        """
        # Ensure schemas are created
        self._ensure_schemas_created()
        
        # Get the schema
        schema_class = self.schema_manager.get_schema(schema_name)
        if not schema_class:
            raise UnoError(
                f"Schema {schema_name} not found in {self.__class__.__name__}",
                "SCHEMA_NOT_FOUND",
            )
        
        # Create a validation context
        context = ValidationContext(self.__class__.__name__)
        
        try:
            # Convert to schema to validate
            schema_class(**self.model_dump())
        except ValidationError as e:
            # Add any validation errors to the context
            for error in getattr(e, "validation_errors", []):
                context.add_error(
                    error.get("field", ""),
                    error.get("message", "Validation error"),
                    error.get("error_code", "VALIDATION_ERROR"),
                    error.get("value")
                )
        except Exception as e:
            # Add any other exceptions as validation errors
            context.add_error(
                "",
                str(e),
                getattr(e, "error_code", "VALIDATION_ERROR")
            )
        
        return context

    def to_model(self, schema_name: str) -> T:
        """
        Convert the UnoObj instance to a model instance using a schema.

        Args:
            schema_name: The name of the schema to use for conversion

        Returns:
            A model instance

        Raises:
            UnoError: If the schema is not found
            ValidationError: If validation fails
        """
        # Ensure schemas are created
        self._ensure_schemas_created()

        # Get the schema
        schema_class = self.schema_manager.get_schema(schema_name)
        if not schema_class:
            raise UnoError(
                f"Schema {schema_name} not found in {self.__class__.__name__}",
                "SCHEMA_NOT_FOUND",
            )

        # Validate first
        validation_context = self.validate(schema_name)
        validation_context.raise_if_errors()

        # Convert to schema
        schema = schema_class(**self.model_dump())

        # Convert to model
        return self.__class__.model(**schema.model_dump())

    def _ensure_schemas_created(self) -> None:
        """
        Ensure that schemas have been created.

        This method creates all schemas for the class if they haven't been created yet.
        """
        if not self.schema_manager.get_schema("edit_schema"):
            self.schema_manager.create_all_schemas(self.__class__)

    async def merge(self, **kwargs: Any) -> Tuple[T, str]:
        """
        Merge the current object with an existing one in the database.

        This method attempts to merge the current object with an existing one in the database.
        If no matching object is found, a new one is created.

        Args:
            **kwargs: Additional filter parameters

        Returns:
            A tuple of (model, action) where action is "insert" or "update"
            
        Raises:
            ValidationError: If validation fails
        """
        self._ensure_schemas_created()

        # Get the edit schema
        edit_schema = self.schema_manager.get_schema("edit_schema")
        if not edit_schema:
            raise UnoError(
                "Edit schema not found",
                "SCHEMA_NOT_FOUND",
            )

        # Validate first
        validation_context = self.validate("edit_schema")
        validation_context.raise_if_errors()

        # Convert to schema
        schema = edit_schema(**self.model_dump())

        # Merge
        result = await self.db.merge(schema.model_dump())

        # Get the action
        action = result[0].pop("_action")

        # Convert to model
        return self.__class__.model(**result[0]), action

    async def save(self, importing: bool = False) -> T:
        """
        Save the current object to the database.

        This method creates or updates the object in the database.

        Args:
            importing: Whether the object is being imported

        Returns:
            The saved model
            
        Raises:
            ValidationError: If validation fails
        """
        self._ensure_schemas_created()

        if importing:
            schema_name = "view_schema"
        else:
            schema_name = "edit_schema"

        # Validate first
        validation_context = self.validate(schema_name)
        validation_context.raise_if_errors()

        model = self.to_model(schema_name=schema_name)

        if self.id:
            # Update
            return await self.db.update(to_db_model=model)
        else:
            # Create
            result = await self.db.create(schema=model)
            return result[0]

    async def delete(self) -> None:
        """
        Delete the current object from the database.

        Returns:
            None
        """
        self._ensure_schemas_created()

        model = self.to_model(schema_name="edit_schema")
        await self.db.delete(model)

    @classmethod
    async def get(cls, **kwargs: Any) -> "UnoObj":
        """
        Get an object from the database.

        Args:
            **kwargs: Filter parameters

        Returns:
            A UnoObj instance
        """
        # Create the database factory using the deferred import
        db = get_db_factory(obj=cls)

        # Get the model from the database
        model = await db.get(**kwargs)

        # Convert to UnoObj
        return cls(**model)

    @classmethod
    async def filter(
        cls, 
        filters: Optional[FilterParam] = None
    ) -> List["UnoObj"]:
        """
        Filter objects from the database.

        Args:
            filters: Filter parameters

        Returns:
            A list of UnoObj instances
        """
        # Create the database factory using the deferred import
        db = get_db_factory(obj=cls)

        # Filter models from the database
        models = await db.filter(filters=filters)

        # Convert to UnoObj instances
        return [cls(**model) for model in models]

    @classmethod
    def configure(cls, app: Any) -> None:
        """
        Configure the UnoObj class for use with a web application.

        This method sets up filters, schemas, and endpoints for the class.

        Args:
            app: The web application to configure (typically a FastAPI instance)
        """
        # Setup filter manager using the deferred import
        filter_manager = get_filter_manager()
        filter_manager.create_filters_from_table(
            cls.model,
            cls.exclude_from_filters,
            cls.terminate_field_filters,
        )

        # Create and attach schema_manager to the model class using the deferred import
        schema_manager = get_schema_manager()
        schema_manager.create_all_schemas(cls)
        cls.schema_manager = schema_manager  # attach schema manager to the class

        # Setup endpoints
        endpoint_factory = UnoEndpointFactory()
        endpoint_factory.create_endpoints(
            app,
            cls,
            cls.endpoints,
            cls.endpoint_tags,
        )

    @classmethod
    def create_filter_params(cls) -> Type[FilterParam]:
        """
        Create a filter parameters model for the class.

        Returns:
            A Pydantic model class for filter parameters
        """
        # Setup filter manager using the deferred import
        filter_manager = get_filter_manager()
        filter_manager.create_filters_from_table(
            cls.model,
            cls.exclude_from_filters,
            cls.terminate_field_filters,
        )

        # Create filter parameters
        filter_params = filter_manager.create_filter_params(cls)
        return cast(Type[FilterParam], filter_params)

    @classmethod
    def validate_filter_params(cls, filter_params: FilterParam) -> List[Any]:
        """
        Validate filter parameters.

        Args:
            filter_params: The filter parameters to validate

        Returns:
            A list of validated filter tuples

        Raises:
            ValidationError: If validation fails
        """
        # Setup filter manager using the deferred import
        filter_manager = get_filter_manager()
        filter_manager.create_filters_from_table(
            cls.model,
            cls.exclude_from_filters,
            cls.terminate_field_filters,
        )

        # Create validation context
        context = ValidationContext(f"{cls.__name__}FilterParams")
        
        # Validate filter parameters
        try:
            return filter_manager.validate_filter_params(filter_params, cls)
        except ValidationError as e:
            # Re-raise ValidationError
            raise e
        except Exception as e:
            # Wrap any other exceptions in ValidationError
            context.add_error(
                "", 
                str(e),
                getattr(e, "error_code", "FILTER_VALIDATION_ERROR")
            )
            context.raise_if_errors()
            # This line should never be reached due to raise_if_errors() above
            return []