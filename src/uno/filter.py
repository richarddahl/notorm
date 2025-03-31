# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

import datetime
import decimal

from typing import Optional, Any
from typing_extensions import Self
from psycopg import sql
from pydantic import BaseModel, model_validator

from uno.enums import (
    GraphLookup,
    graph_boolean_comparison_operators,
    graph_numeric_comparison_operators,
    graph_text_comparison_operators,
)
from uno.utilities import snake_to_title
from uno.config import settings


class UnoFilter(BaseModel):
    source_node: Optional[str] = None
    label_string: Optional[str] = None
    label: Optional[str] = None
    target_node: Optional[str] = None
    data_type: str = "str"
    raw_data_type: type = str
    comparison_operators: list[str]
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

    def cypher_query_string(
        self, value: Any, comparison_operator: str = "EQUAL"
    ) -> str:

        print(type(comparison_operator))
        graph_comparison_operator = GraphLookup.__members__.get(comparison_operator)

        if self.data_type == "bool":
            val = str(value).lower()
            if not val in ["true", "false", "t", "f", "t"]:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            if not comparison_operator in graph_boolean_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for boolean data type."
                )
        elif self.data_type in ["datetime", "date", "time"]:
            try:
                val = round(value.timestamp())
            except AttributeError:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            if not comparison_operator in graph_numeric_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for datetime data type."
                )
        elif self.data_type == "decimal":
            try:
                val = decimal.Decimal(value)
            except AttributeError:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            if not comparison_operator in graph_numeric_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for decimal data type."
                )
        elif self.data_type == "int":
            try:
                val = int(value)
            except AttributeError:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            if not comparison_operator in graph_numeric_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for int data type."
                )
        elif self.data_type == "float":
            try:
                val = float(value)
            except AttributeError:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            if not comparison_operator in graph_numeric_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for float data type."
                )
        else:
            val = str(value)
            if not comparison_operator in graph_text_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for {self.data_type} data type."
                )

        if comparison_operator == "NULL":
            comparison = "IS NULL"
        elif comparison_operator == "NOTNULL":
            comparison = "IS NOT NULL"
        else:
            comparison = f"{graph_comparison_operator.value} '{val}'"

        return (
            sql.SQL(
                """
        (SELECT * FROM cypher('graph', $subq$
            MATCH {path}
            WHERE d.val {comparison}
            RETURN DISTINCT s.id
        $subq$) AS (id TEXT))
        """
            )
            .format(
                path=sql.SQL(self.path()),
                comparison=sql.SQL(comparison),
                value=sql.SQL(str(val)),
            )
            .as_string()
        )
