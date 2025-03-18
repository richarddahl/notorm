# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Literal, Optional
from typing_extensions import Self
from pydantic import BaseModel, model_validator

from uno.db.enums import SQLOperation

from uno.apps.fltr.bases import FilterBase
from uno.apps.val.enums import DataType
from uno.errors import UnoRegistryError
from uno.config import settings


class Filter(BaseModel):
    source_model: type[BaseModel] = None
    remote_model: type[BaseModel] = None
    label: str
    data_type: str = "str"
    source_table_name: str
    remote_table_name: str
    accessor: str
    filter_type: Literal["Edge", "Property"] = "Property"
    lookups: list[str]
    children: Optional[list["Filter"]] = []

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        print(f"Source: {self.source_table_name} Filter: {self.label}")
        if self.filter_type == "Edge":
            for filter in self.remote_model.filters.values():
                print(
                    f"(v:{self.source_model.__name__})-[:{self.accessor}]-(:{self.remote_model.__name__} {{{filter.accessor}}})"
                )
        print("")
        return self
