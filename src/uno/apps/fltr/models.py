# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Literal, Optional, Type
from pydantic import BaseModel

from uno.db.enums import SQLOperation

from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.apps.auth.mixins import RecordAuditMixin
from uno.apps.fltr.bases import FilterBase
from uno.config import settings


class Filter(BaseModel):
    source_model: type[BaseModel] = None
    remote_model: type[BaseModel] = None
    id: int = None
    label: str
    data_type: str = "str"
    source_table_name: str
    remote_table_name: str
    accessor: str
    filter_type: Literal["Edge", "Property"] = "Property"
    lookups: list[str]
    children: Optional[list["Filter"]] = []


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
