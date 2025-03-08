# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.model.model import UnoModel


class MetaType(UnoModel):
    # Class variables
    table_name = "meta_type"

    id: str
    name: str

    def __str__(self) -> str:
        return f"{self.id}"


class MetaBase(UnoModel):
    # Class variables
    table_name = "meta"

    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type_id}: {self.id}"
