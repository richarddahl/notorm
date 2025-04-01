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
    ComparisonOperator,
    boolean_comparison_operators,
    numeric_comparison_operators,
    text_comparison_operators,
)
from uno.utilities import snake_to_title
from uno.config import settings


class UnoFilter(BaseModel):
    source_node_label: str
    label: str
    target_node_label: str
    data_type: str
    raw_data_type: type
    comparison_operators: list[str]
    source_path: str
    destination_path: str

    def __str__(self) -> str:
        return f"{self.source_node_label}-{self.label}->{self.target_node_label}"

    def __repr__(self) -> str:
        return f"<UnoFilter: {self.source_path}->{self.destination_path}>"

    def path(self) -> str:
        return f"{self.source_path}->{self.destination_path}"

    def cypher_query_string(
        self, value: Any, comparison_operator: str = "EQUAL"
    ) -> str:

        graph_comparison_operator = ComparisonOperator.__members__.get(
            comparison_operator
        )

        if self.data_type == "bool":
            val = str(value).lower()
            if not val in ["true", "false", "t", "f", "t"]:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            if not comparison_operator in boolean_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for boolean data type"
                )
        elif self.data_type in ["datetime", "date", "time"]:
            try:
                if self.data_type == "datetime":
                    val = datetime.datetime.fromisoformat(value)
                elif self.data_type == "date":
                    val = datetime.date.fromisoformat(value)
                elif self.data_type == "time":
                    val = datetime.time.fromisoformat(value)
                val = round(val.timestamp())
            except AttributeError:
                raise TypeError(f"Value {value} is not of type {self.raw_data_type}")
            if not comparison_operator in numeric_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for datetime data type"
                )
        else:
            val = str(value)
            if not comparison_operator in text_comparison_operators:
                raise TypeError(
                    f"ComparisonOperator {comparison_operator} is not valid for {self.data_type} data type"
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
