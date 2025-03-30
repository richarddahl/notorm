# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

import datetime

from typing import Optional, Any
from typing_extensions import Self
from psycopg import sql
from pydantic import BaseModel, model_validator

from uno.utilities import snake_to_title
from uno.config import settings


class UnoFilter(BaseModel):
    source_node: Optional[str] = None
    label_string: Optional[str] = None
    label: Optional[str] = None
    target_node: Optional[str] = None
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
        # self.source_path = f"(:{self.source_node})-[:{self.label}]->"
        self.source_path = f"(s:{self.source_node})-[e:{self.label}]"
        # self.destination_path = f"(:{self.target_node} {{val: %s}})"
        self.destination_path = f"(d:{self.target_node})"
        return self

    def __str__(self) -> str:
        return f"{self.source_node}-{self.label}->{self.target_node}"

    def __repr__(self) -> str:
        return f"<UnoFilter: {self.source_path}->{self.destination_path}>"

    def path(self) -> str:
        return f"{self.source_path}->{self.destination_path}"

    def cypher_query_string(self, value: Any) -> str:
        if not isinstance(value, self.raw_data_type):
            raise TypeError(f"Value {value} is not of type {self.raw_data_type}")

        if self.data_type == "bool":
            val = str(value).lower()
        elif self.data_type == "datetime":
            val = round(value.timestamp())
        else:
            val = str(value)

        print(f"Cypher Query String: {self.path()} {val}")
        return (
            sql.SQL(
                """
        (SELECT * FROM cypher('graph', $subq$
            MATCH {path}
            WHERE d.val = '{value}'
            RETURN DISTINCT s.id
        $subq$) AS (id TEXT))
        """
            )
            .format(
                path=sql.SQL(self.path()),
                value=sql.SQL(str(val)),
            )
            .as_string()
        )
