# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Business logic layer objects for the Uno framework.

This module provides the UnoObj class, which serves as the business logic layer
for models in the Uno framework. It handles object lifecycle, data validation,
and business logic operations.
"""

import datetime
from typing import Dict, Type, List, Optional, Any, ClassVar, TypeVar, Generic

from pydantic import BaseModel, ConfigDict, Field

from uno.db.db import UnoDBFactory, FilterParam
from uno.model import UnoModel
from uno.schema import UnoSchemaConfig
from uno.errors import UnoError
from uno.utilities import snake_to_title
from uno.registry import UnoRegistry
from uno.schema_manager import UnoSchemaManager
from uno.filter_manager import UnoFilterManager
from uno.endpoint_factory import UnoEndpointFactory


T = TypeVar("T", bound=UnoModel)


class UnoObj(BaseModel, Generic[T]):
    """
    Business logic layer object for the Uno framework.

    This class provides business logic operations for models, including data validation,
    object lifecycle management, and integration with the web application.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    # Class variables
    model: ClassVar[Type[T]]
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
    db: Any = Field(None, exclude=True)
    registry: UnoRegistry = Field(None, exclude=True)
    schema_manager: UnoSchemaManager = Field(None, exclude=True)
    filter_manager: UnoFilterManager = Field(None, exclude=True)

    def __init__(self, **data: Any):
        """
        Initialize a UnoObj instance.

        Args:
            **data: The data to initialize the object with
        """
        super().__init__(**data)

        # Initialize the db factory
        self.db = UnoDBFactory(obj=self.__class__)

        # Get the registry instance
        self.registry = UnoRegistry.get_instance()

        # Initialize the schema manager
        self.schema_manager = UnoSchemaManager(self.__class__.schema_configs)

        # Initialize the filter manager
        self.filter_manager = UnoFilterManager()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize a UnoObj subclass.

        This method is called when a subclass of UnoObj is created. It registers
        the subclass in the registry and sets up display names. It also extracts
        the model from the Generic type parameter if not explicitly set.

        Args:
            **kwargs: Additional keyword arguments
        """
        super().__init_subclass__(**kwargs)

        # Don't register the UnoObj class itself
        if cls.__name__ == "UnoObj":
            return

        # Try to get the model from the Generic type parameter if not explicitly set
        if not hasattr(cls, "model") or cls.model is None:
            from typing import get_origin, get_args

            # Get the bases of the class
            for base in cls.__orig_bases__:
                # Check if this is a UnoObj with type parameters
                origin = get_origin(base)
                if origin is UnoObj:
                    args = get_args(base)
                    if args and len(args) > 0:
                        cls.model = args[0]
                        break

            # If still no model, raise an error
            if not hasattr(cls, "model") or cls.model is None:
                raise TypeError(
                    f"Class {cls.__name__} must specify a model class either "
                    f"as a type parameter (UnoObj[ModelClass]) or as a class variable (model = ModelClass)"
                )

        # Set display names if not already set
        cls._set_display_names()

        # Register the class in the registry
        registry = UnoRegistry.get_instance()
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

    def to_model(self, schema_name: str) -> T:
        """
        Convert the UnoObj instance to a model instance using a schema.

        Args:
            schema_name: The name of the schema to use for conversion

        Returns:
            A model instance

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

        # Convert to schema
        schema = schema_class(**self.model_dump())

        # Convert to model
        return self.__class__.model(**schema.model_dump())

    def _ensure_schemas_created(self) -> None:
        """
        Ensure that schemas have been created.

        This method creates all schemas for the class if they haven't been created yet.
        """
        if not self.schema_manager.schemas:
            self.schema_manager.create_all_schemas(self.__class__)

    async def merge(self, **kwargs: Any) -> tuple[T, str]:
        """
        Merge the current object with an existing one in the database.

        This method attempts to merge the current object with an existing one in the database.
        If no matching object is found, a new one is created.

        Args:
            **kwargs: Additional filter parameters

        Returns:
            A tuple of (model, action) where action is "insert" or "update"
        """
        self._ensure_schemas_created()

        # Get the edit schema
        edit_schema = self.schema_manager.get_schema("edit_schema")
        if not edit_schema:
            raise UnoError(
                "Edit schema not found",
                "SCHEMA_NOT_FOUND",
            )

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
        """
        self._ensure_schemas_created()

        if importing:
            schema_name = "view_schema"
        else:
            schema_name = "edit_schema"

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
        # Create the database factory
        db = UnoDBFactory(obj=cls)

        # Get the model from the database
        model = await db.get(**kwargs)

        # Convert to UnoObj
        return cls(**model)

    @classmethod
    async def filter(cls, filters: FilterParam = None) -> List["UnoObj"]:
        """
        Filter objects from the database.

        Args:
            filters: Filter parameters

        Returns:
            A list of UnoObj instances
        """
        # Create the database factory
        db = UnoDBFactory(obj=cls)

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
        # Setup filter manager
        filter_manager = UnoFilterManager()
        filter_manager.create_filters_from_table(
            cls.model,
            cls.exclude_from_filters,
            cls.terminate_field_filters,
        )

        # Setup schema manager
        schema_manager = UnoSchemaManager(cls.schema_configs)
        schema_manager.create_all_schemas(cls)

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
        # Setup filter manager
        filter_manager = UnoFilterManager()
        filter_manager.create_filters_from_table(
            cls.model,
            cls.exclude_from_filters,
            cls.terminate_field_filters,
        )

        # Create filter parameters
        return filter_manager.create_filter_params(cls)

    @classmethod
    def validate_filter_params(cls, filter_params: FilterParam) -> List[Any]:
        """
        Validate filter parameters.

        Args:
            filter_params: The filter parameters to validate

        Returns:
            A list of validated filter tuples

        Raises:
            UnoError: If validation fails
        """
        # Setup filter manager
        filter_manager = UnoFilterManager()
        filter_manager.create_filters_from_table(
            cls.model,
            cls.exclude_from_filters,
            cls.terminate_field_filters,
        )

        # Validate filter parameters
        try:
            return filter_manager.validate_filter_params(filter_params, cls)
        except Exception as e:
            # Wrap any exceptions in UnoError
            raise UnoError(
                str(e),
                getattr(e, "error_code", "FILTER_VALIDATION_ERROR"),
            ) from e
