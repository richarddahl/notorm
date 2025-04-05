# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.object import UnoObj
from uno.schema import UnoSchemaConfig
from uno.meta.objects import MetaTypeModel, MetaRecordModel


class MetaType(UnoObj):
    # Class variables
    model = MetaTypeModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(),
    }
    endpoints = ["List"]

    id: str

    def __str__(self) -> str:
        return f"{self.id}"


class MetaRecord(UnoObj):
    # Class variables
    model = MetaRecordModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(),
    }
    endpoints = ["List"]

    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type_id}: {self.id}"
