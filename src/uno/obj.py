# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

import decimal
import datetime

from collections import namedtuple, OrderedDict
from typing import ClassVar, Literal, List, Annotated
from pydantic import BaseModel, ConfigDict, create_model

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import Column

from uno.model import UnoDBFactory, FilterParam
from uno.model import UnoModel
from uno.schema import UnoSchemaConfig
from uno.endpoint import (
    CreateEndpoint,
    ViewEndpoint,
    ListEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
    ImportEndpoint,
)
from uno.errors import UnoRegistryError
from uno.utilities import (
    snake_to_title,
    snake_to_camel,
    snake_to_caps_snake,
)
from uno.filter import (
    UnoFilter,
    boolean_lookups,
    numeric_lookups,
    datetime_lookups,
    text_lookups,
)
from uno.config import settings


class UnoObj(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    registry: ClassVar[dict[str, "UnoObj"]] = {}
    db: ClassVar["UnoDB"]
    model: ClassVar[type[UnoModel]]
    exclude_from_filters: ClassVar[bool] = False
    terminate_filters: ClassVar[bool] = False
    display_name: ClassVar[str] = None
    display_name_plural: ClassVar[str] = None
    schema_configs: ClassVar[dict[str, "UnoSchemaConfig"]] = {}
    endpoints: ClassVar[list[str]] = [
        "Create",
        "View",
        "List",
        "Update",
        "Delete",
        "Import",
    ]
    endpoint_tags: ClassVar[list[str]] = []
    filters: ClassVar[dict[str, UnoFilter]] = {}
    terminate_field_filters: ClassVar[list[str]] = []

    def __init_subclass__(cls, **kwargs) -> None:

        super().__init_subclass__(**kwargs)
        # Don't add the UnoObj class itself to the registry
        if cls is UnoObj:
            return
        # Add the subclass to the registry if it is not already there
        if cls.model.__tablename__ not in cls.registry:
            cls.registry.update({cls.model.__tablename__: cls})
        else:
            raise UnoRegistryError(
                f"A Model class with the table name {cls.model.__tablename__} already exists in the registry.",
                "DUPLICATE_MODEL",
            )
        cls.set_display_names()
        cls.db = UnoDBFactory(obj=cls)

    # End of __init_subclass__

    # Active Record style methods
    async def get_or_create(
        self,
        **kwargs,
    ) -> "UnoObj":
        """
        Asynchronously retrieves an existing record or creates a new one in the database.

        This method attempts to find a record in the database that matches the provided
        keyword arguments. If no such record exists, it creates a new one using the
        specified schema.

        Returns:
            UnoObj: The retrieved or newly created model instance.

        Raises:
            Exception: If there is an issue with the database operation.

        Keyword Args:
            **kwargs: Arbitrary keyword arguments used to filter or create the record,
            the combination of which must form a unique key in the database.
        """
        return await self.db.get_or_create(self.to_model(schema_name="edit_schema"))

    # End of get_or_create

    async def save(self, importing: bool = False) -> "UnoObj":
        """
        Save the current UnoObj instance to the database.

        This method handles both creating and updating the model in the database,
        depending on the state of the instance and the `importing` flag.

        Args:
            importing (bool): If True, the model is being imported and will be
                              created in the database using the "view_schema".
                              Defaults to False.

        Returns:
            UnoObj: The saved UnoObj instance.

        Behavior:
            - If `importing` is True, the model is created using the "view_schema".
            - If the instance has an `id`, it is created using the "edit_schema".
            - Otherwise, the model is updated using the "edit_schema".
        """
        if importing:
            return await self.db.create(self.to_model(schema_name="view_schema"))
        if self.id:
            return self.db.update(self.to_model(schema_name="edit_schema"))
        return await self.db.create(
            to_db_model=self.to_model(schema_name="edit_schema")
        )

    # End of save

    async def delete(self) -> None:
        """
        Delete the current UnoObj instance from the database.

        This method removes the instance from the database using the "edit_schema".

        Returns:
            None: The method does not return anything.

        Raises:
            Exception: If there is an issue with the database operation.
        """
        await self.db.delete(self.to_model(schema_name="edit_schema"))

    # End of delete

    @classmethod
    async def get(cls, **kwargs) -> "UnoObj":
        return await cls.db.get(**kwargs)

    # End of get

    @classmethod
    async def filter(cls, filters: FilterParam | None = None) -> list["UnoObj"]:
        return await cls.db.filter(filters=filters)

    # End of filter

    def to_model(self, schema_name: str) -> dict:
        self.set_schemas()
        if not hasattr(self, schema_name):
            raise UnoRegistryError(
                f"Schema {schema_name} not found in {self.__class__.__name__}",
                "SCHEMA_NOT_FOUND",
            )
        schema_ = getattr(self, schema_name)
        schema = schema_(**self.model_dump())
        return self.model(**schema.model_dump())

    # End of to_model

    @classmethod
    def configure(cls, app: FastAPI) -> None:
        """Configure the UnoObj class"""
        cls.set_filters()
        cls.set_schemas()
        cls.set_endpoints(app)

    # End of configure

    @classmethod
    def set_display_names(cls) -> None:
        cls.display_name = (
            snake_to_title(cls.model.__table__.name)
            if cls.display_name is None
            else cls.display_name
        )
        cls.display_name_plural = (
            f"{snake_to_title(cls.model.__table__.name)}s"
            if cls.display_name_plural is None
            else cls.display_name_plural
        )

    # End of set_display_names

    @classmethod
    def set_schemas(cls) -> None:
        for schema_name, schema_config in cls.schema_configs.items():
            setattr(
                cls,
                schema_name,
                schema_config.create_schema(
                    schema_name=schema_name,
                    model=cls,
                ),
            )

    # End of set_schemas

    @classmethod
    def set_endpoints(cls, app: FastAPI) -> None:
        for endpoint in cls.endpoints:
            if endpoint == "Create":
                CreateEndpoint(model=cls, app=app)
            elif endpoint == "View":
                ViewEndpoint(model=cls, app=app)
            elif endpoint == "List":
                ListEndpoint(model=cls, app=app)
            elif endpoint == "Update":
                UpdateEndpoint(model=cls, app=app)
            elif endpoint == "Delete":
                DeleteEndpoint(model=cls, app=app)
            elif endpoint == "Import":
                ImportEndpoint(model=cls, app=app)

    # End of set_endpoints

    @classmethod
    def set_filters(cls) -> None:
        """
        Sets up filters for the class based on its database table columns.

        This method iterates through the columns of the class's associated database table
        and generates `UnoFilter` objects for each column. These filters are stored in the
        `filters` attribute of the class, allowing for dynamic filtering based on the table's
        schema and relationships.

        The filters are constructed using the `create_filter` function, which determines
        the appropriate metadata, comparison operators, and relationships for each column.

            - Models with `exclude_from_filters` set to `True` will not have filters created.
            - Columns with foreign keys are treated as relationships, and the source and
              target node labels are derived from the foreign key relationships.
            - The `edge` label is derived from the column's `info` metadata or defaults to
              the column name.
            - The `source_path_fragment`, `middle_path_fragment`, and `target_path_fragment`
              are constructed based on the source and target node labels, allowing for
              flexible query generation.
            - The `lookups` are determined based on the column's data type, allowing for
              appropriate filtering options (e.g., boolean, numeric, datetime, text).
            - The `documentation` for each filter is derived from the column's docstring
              or the label, providing context for API documentation.
            - Filters are created for each column in the table, excluding those marked
              with `exclude_from_filters` or `graph_excludes`.
            - The `filters` attribute is a dictionary where keys are filter labels and
              values are `UnoFilter` objects.
            - The `create_filter` function is responsible for generating the filter
              objects based on the column properties.
            - Columns marked with `graph_excludes` in their `info` metadata are skipped.
            - Filters are keyed by their label, ensuring uniqueness.

        Attributes:
            filters (dict): A dictionary where keys are filter labels and values are
            `UnoFilter` objects representing the filtering configuration for each column.
        """

        def create_filter(column: Column) -> UnoFilter:
            """
            Creates a filter object for a given database column.

            This function generates a `UnoFilter` object based on the properties of the
            provided SQLAlchemy `Column`. It determines the appropriate comparison operators
            and constructs metadata for source and target nodes, as well as the relationship
            label between them.

            Args:
                column (Column): The SQLAlchemy `Column` object for which the filter is created.

            Returns:
                UnoFilter: An object containing metadata and configuration for filtering
                based on the provided column.

            Notes:
                - If the column has foreign keys, the source and target node labels and
                  metadata are derived from the foreign key relationships.
                - If the column does not have foreign keys, the source and target node
                  labels and metadata are derived from the column and table names.
                - The function determines the data type of the column and assigns the
                  appropriate comparison operators (boolean, numeric, or text).
            """

            # Determine the lookups based on the column type
            if column.type.python_type == bool:
                lookups = boolean_lookups
            elif column.type.python_type in [
                int,
                decimal.Decimal,
                float,
            ]:
                lookups = numeric_lookups
            elif column.type.python_type in [
                datetime.date,
                datetime.datetime,
                datetime.time,
            ]:
                lookups = datetime_lookups
            else:
                lookups = text_lookups

            # Get the edge label from the column info or use the column name
            edge = column.info.get("edge", column.name)

            # Determine the source and target node labels and meta_types
            if column.foreign_keys:
                # If the column has foreign keys, use the foreign key to determine the
                # source and target node labels and meta_types
                source_node_label = snake_to_camel(column.table.name)
                source_meta_type_id = column.table.name
                target_node_label = snake_to_camel(
                    list(column.foreign_keys)[0].column.table.name
                )
                target_meta_type_id = list(column.foreign_keys)[0].column.table.name
                label = snake_to_caps_snake(
                    column.info.get(edge, column.name.replace("_id", ""))
                )
            else:
                # If the column does not have foreign keys, use the column name to determine
                # the source and target node labels and meta_types
                source_node_label = snake_to_camel(table.name)
                source_meta_type_id = table.name
                target_node_label = snake_to_camel(column.name)
                target_meta_type_id = source_meta_type_id
                label = snake_to_caps_snake(
                    column.info.get(edge, column.name.replace("_id", ""))
                )

            return UnoFilter(
                source_node_label=source_node_label,
                source_meta_type_id=source_meta_type_id,
                label=label,
                target_node_label=target_node_label,
                target_meta_type_id=target_meta_type_id,
                data_type=column.type.python_type.__name__,
                raw_data_type=column.type.python_type,
                lookups=lookups,
                source_path_fragment=f"(s:{source_node_label})-[:{label}]",
                middle_path_fragment=f"(:{source_node_label})-[:{label}]",
                target_path_fragment=f"(t:{target_node_label})",
                documentation=column.doc or label,
            )

        if cls.exclude_from_filters:
            return
        filters = {}
        table = cls.model.__table__
        for column in table.columns.values():
            if column.info.get("graph_excludes", False):
                continue
            if fltr := create_filter(column):
                filter_key = fltr.label
                if filter_key not in filters.keys():
                    filters[filter_key] = fltr
        cls.filters = filters

    # End of set_filters

    @classmethod
    def create_filter_params(cls) -> "FilterParam":
        """
        Generate a Pydantic model for filter parameters based on the class's filters and model fields.

        This method dynamically creates a dictionary of filter parameters, including:
        - Pagination parameters (`limit` and `offset`).
        - Sorting parameters (`order_by`, `order_by.asc`, and `order_by.desc`).
        - Filters for each field in the model, including lookup-specific filters.

        The generated model is used to validate and document query parameters for filtering
        and sorting in API endpoints.

        Returns:
            FilterParam: A dynamically created Pydantic model subclassed from `FilterParam`.

        Notes:
            - The `order_by.asc` and `order_by.desc` fields are excluded from the schema
              for API documentation purposes.
            - Lookup-specific filters (e.g., `field.in`, `field.notin`) are also excluded
              from the schema for API documentation.
        """

        filter_names = list(cls.filters.keys())
        filter_names.sort()
        order_by_choices = [name for name in cls.model_fields.keys()]

        # Create a dictionary of filter parameters
        # Start with the filter parameters for limit, offset, and order_by
        # and then add the filters for each field in the model
        model_filter_dict = OrderedDict(
            {
                "limit": (Annotated[int | None, Query()], None),
                "offset": (Annotated[int | None, Query()], None),
                "order_by": (
                    Annotated[
                        Literal[*order_by_choices] | None,
                        Query(
                            description="Order by field",
                        ),
                    ],
                    None,
                ),
            }
        )
        # Add the order_by.asc and order_by.desc "lookup" fields, which are
        # excluded from the schema for the app documentation
        for direction in ["asc", "desc"]:
            model_filter_dict.update(
                {
                    f"order_by.{direction}": (
                        Annotated[
                            Literal[*order_by_choices] | None,
                            Query(
                                description="Order by field",
                                include_in_schema=False,
                            ),
                        ],
                        None,
                    )
                }
            )
        for name in filter_names:
            fltr = cls.filters[name]
            label = fltr.label.lower()
            # Add the base filter for the field, included in the schema for the app documentation
            model_filter_dict.update(
                {label: (Annotated[fltr.raw_data_type | None, Query()], None)}
            )
            # Add the filters for each lookup, excluded from the schema for the app documentation
            for lookup in fltr.lookups:
                if lookup in ["IN", "NOTIN"]:
                    data_type = List[fltr.raw_data_type] | None
                else:
                    data_type = fltr.raw_data_type | None
                label_ = f"{label}.{lookup.lower()}"
                model_filter_dict.update(
                    {
                        label_: (
                            Annotated[
                                data_type | None,
                                Query(include_in_schema=False),
                            ],
                            None,
                        )
                    }
                )
        return create_model(
            f"{cls.__name__}FilterParam",
            **model_filter_dict,
            __base__=FilterParam,
        )

    # End of create_filter_params

    @classmethod
    def validate_filter_params(cls, filter_params: FilterParam) -> dict:
        """
        Validates and processes filter parameters for a query.

        This method checks the provided filter parameters against the expected
        parameters defined in the class. It ensures that all parameters are valid,
        and raises an HTTPException if any unexpected or invalid parameters are found.
        Additionally, it constructs a list of filters to be applied to the query.

        Args:
            filter_params (FilterParam): An object containing the filter parameters
                to validate and process.

        Returns:
            dict: A list of named tuples representing the validated filters. Each
                tuple contains the filter's label, value, and lookup type.

        Raises:
            HTTPException: If any of the following conditions are met:
                - Unexpected query parameters are provided.
                - An invalid `order_by` value is specified.
                - An invalid `order` value is specified.
                - A non-positive integer is provided for `limit` or `offset`.
                - An invalid filter key or lookup is specified.
        """
        filter_tuple = namedtuple("UnoFilterTuple", ["label", "val", "lookup"])
        filters: list = []
        # Check for unexpected parameters
        # Get the expected parameters from the filters
        # and add the limit and offset keys
        # to the expected parameters
        expected_params = set([key.lower() for key in cls.filters.keys()])
        expected_params.update(["limit", "offset", "order_by"])
        unexpected_params = (
            set([key.split(".")[0] for key in filter_params.model_fields])
            - expected_params
        )
        if unexpected_params:
            unexpected_param_list = ", ".join(unexpected_params)
            raise HTTPException(
                status_code=400,
                detail=f"Unexpected query parameter(s): {unexpected_param_list}. Check spelling and case.",
            )
        for key, val in filter_params.model_dump().items():
            # Check if the filter is valid
            if val is None:
                continue
            filter_component_list = key.split(".")
            edge = filter_component_list[0]
            if edge in ["limit", "offset", "order_by"]:
                if edge == "order_by":
                    order_by_choices = [
                        name for name in cls.view_schema.model_fields.keys()
                    ]
                    if val not in order_by_choices:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid order_by value: {val}. Must be one of {order_by_choices}.",
                        )
                    if filter_component_list[1] == "asc":
                        filters.append(filter_tuple(edge, val, "asc"))
                    elif filter_component_list[1] == "desc":
                        filters.append(filter_tuple(edge, val, "desc"))
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid order_by value: {val}. Must be 'asc' or 'desc'.",
                        )
                if edge == "limit":
                    if not isinstance(val, int) or val < 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid limit value: {val}. Must be a positive integer.",
                        )
                    filters.append(filter_tuple(edge, val, "limit"))
                if edge == "offset":
                    if not isinstance(val, int) or val < 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid offset value: {val}. Must be a positive integer.",
                        )
                    filters.append(filter_tuple(edge, val, "offset"))
                continue
            edge_upper = edge.upper()
            if edge_upper not in cls.filters.keys():
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filter key: {key}",
                )
            lookup = (
                filter_component_list[1] if len(filter_component_list) > 1 else "equal"
            )
            if lookup not in cls.filters[edge_upper].lookups:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filter lookup: {lookup}",
                )
            filters.append(filter_tuple(edge_upper, val, lookup))
        return filters

    # End of validate_filter_params
