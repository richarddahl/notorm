# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, List
from typing_extensions import Self

from uno.obj import UnoObj
from uno.schema import UnoSchemaConfig
from uno.meta.models import MetaTypeModel, MetaRecordModel


class MetaType(UnoObj[MetaTypeModel]):
    # Class variables
    model = MetaTypeModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
    }
    terminate_filters = True

    # Fields
    id: str

    def __str__(self) -> str:
        return self.name


class MetaRecord(UnoObj[MetaRecordModel]):
    # Class variables
    model = MetaRecordModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=["meta_type"],
        ),
    }
    terminate_filters = True

    # Fields
    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type.id if self.meta_type else 'Unknown'}: {self.id}"
