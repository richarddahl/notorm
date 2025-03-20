# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Literal, Optional
from typing_extensions import Self
from pydantic import BaseModel, model_validator, computed_field

from uno.db.enums import SQLOperation

# from uno.apps.fltr.bases import FilterBase
from uno.apps.val.enums import DataType
from uno.errors import UnoRegistryError
from uno.utilities import convert_snake_to_title
from uno.config import settings


class Filter(BaseModel):
    source_node: str
    label: str
    remote_node: str
    data_type: str = "str"
    filter_type: Literal["Column", "Relationship"] = "Column"
    lookups: list[str]
    parent: Optional["Filter"] = None
    display: Optional[str] = None
    path: Optional[str] = None

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        if self.filter_type == "Relationship":
            if self.parent is None:
                self.display = f"{self.source_node} {convert_snake_to_title(self.label)} (:{self.remote_node} {{id: %s, val: %s}})"
                self.path = f"(:{self.source_node})-[:{self.label}]->(:{self.remote_node} {{id: %s, val: %s}})"
            else:
                self.display = f"{self.parent.display} {convert_snake_to_title(self.label)} (:{self.remote_node}  {{id: %s, val: %s}})"
                self.path = f"{self.parent.path}-[:{self.label}]->(:{self.remote_node})"
        else:
            if self.parent is None:
                self.display = (
                    f"{self.source_node} {convert_snake_to_title(self.label)}"
                )
                self.path = f"(:{self.source_node})-[:{self.label}]->(:{self.remote_node} {{id: %s, val: %s}})"
            else:
                self.display = (
                    f"{self.parent.display} {convert_snake_to_title(self.label)}"
                )
                self.path = f"{self.parent.path}-[:{self.label}]->(:{self.remote_node} {{id: %s, val: %s}})"
        return self

    def get_parents(self):
        parents = []
        if self.parent:
            parents.append(self.parent)
            parents.extend(self.parent.get_parents())
        return parents
