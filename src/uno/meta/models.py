# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.model import UnoModel
from uno.schema import UnoSchemaConfig
from uno.meta.bases import MetaTypeBase, MetaBase


class MetaType(UnoModel):
    # Class variables
    base = MetaTypeBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(),
    }
    endpoints = ["List"]

    id: str

    def __str__(self) -> str:
        return f"{self.id}"


class Meta(UnoModel):
    # Class variables
    base = MetaBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(),
    }
    endpoints = ["List"]

    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type_id}: {self.id}"
