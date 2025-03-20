# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Optional
from typing_extensions import Self
from pydantic import model_validator

from uno.db.enums import SQLOperation
from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.apps.auth.mixins import RecordAuditMixin
from uno.apps.fltr.bases import FilterBase
from uno.apps.fltr.enums import FilterType
from uno.utilities import convert_snake_to_title, convert_snake_to_camel
from uno.acronyms import acronyms
from uno.config import settings


class Filter(UnoModel):
    # Class variables
    base = FilterBase
    table_name = "filter"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=["prepend_path", "append_path", "path", "display"]
        ),
        "edit_schema": UnoSchemaConfig(exclude_fields=["label_string"]),
    }
    endpoints = ["List"]
    exclude_from_filters = True

    # Fields
    source_meta_type_id: Optional[str] = None
    label_string: Optional[str] = None
    remote_meta_type_id: Optional[str] = None
    data_type: str = "str"
    lookups: list[str]
    display: Optional[str] = None
    path: Optional[str] = None
    prepend_path: Optional[str] = None
    append_path: Optional[str] = None
    id: Optional[int] = None

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        self.display = acronyms.get(
            self.label_string, convert_snake_to_title(self.label_string)
        )
        source_node = convert_snake_to_camel(self.source_meta_type_id)
        remote_node = convert_snake_to_camel(self.remote_meta_type_id)
        label = convert_snake_to_title(self.label_string)
        self.path = f"{source_node}-[:{label}]->(:{remote_node} {{val: %s}})"
        self.prepend_path = f"{source_node}-[:{label}]->(:{remote_node})"
        self.append_path = f"-[:{label}]->(:{remote_node} {{val: %s}})"
        return self

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"<Filter: {self.path} >"

    async def edit_data(self) -> dict:
        return FilterBase(**self.edit_schema(**self.model_dump()).model_dump())


"""
class UnoFilterValue(UnoModel, GeneralModelMixin, RecordAuditMixin):
    base = FilterBase
    table_name = "filter_value"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "filter",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "filter_id",
                "value",
                "label",
                "is_default",
                "is_active",
                "order",
            ],
        ),
    }
    filter_id: int
    value: str
    label: str
    is_default: bool = False
    is_active: bool = True
    order: int = 0
    # python_type: Any = str
    # filter: Filter

"""
