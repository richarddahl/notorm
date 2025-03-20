# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.model.model import UnoModel
from uno.apps.meta.bases import MetaTypeBase, MetaBase


class MetaType(UnoModel):
    # Class variables
    base = MetaTypeBase
    table_name = "meta_type"
    # exclude_from_filters = True

    id: str

    def __str__(self) -> str:
        return f"{self.id}"


class MetaBase(UnoModel):
    # Class variables
    base = MetaBase
    table_name = "meta"
    exclude_from_filters = True

    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type_id}: {self.id}"
