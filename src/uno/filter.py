# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Optional
from typing_extensions import Self
from pydantic import BaseModel, model_validator

from uno.utilities import snake_to_title
from uno.config import settings


class UnoFilter(BaseModel):
    source_node: Optional[str] = None
    label_string: Optional[str] = None
    label: Optional[str] = None
    destination_node: Optional[str] = None
    data_type: str = "str"
    raw_data_type: type = str
    lookups: list[str]
    display: Optional[str] = None
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    id: Optional[int] = None

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        self.display = snake_to_title(self.label)
        self.source_path = f"(:{self.source_node})-[:{self.label}]->"
        self.destination_path = f"(:{self.destination_node} {{val: %s}})"
        return self

    def __str__(self) -> str:
        return f"{self.source_node}-{self.label}->{self.destination_node}"

    def __repr__(self) -> str:
        return f"<UnoFilter: {self.source_path}->{self.destination_path}>"
