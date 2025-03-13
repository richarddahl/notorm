# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Literal
from pydantic import BaseModel

from uno.config import settings


class Filter(BaseModel):
    label: str
    accessor: str
    filter_type: Literal["Edge", "Property"] = "Property"
    lookups: list[str]
    remote_table_name: str = None
