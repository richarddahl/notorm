# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.model.model import UnoModel
from uno.db.sql.table_sql_emitters import AlterGrants, InsertPermission


class MetaType(UnoModel):
    # Class variables
    table_name = "meta_type"
    sql_emitters = [AlterGrants, InsertPermission]

    id: str
    name: str

    def __str__(self) -> str:
        return f"{self.id}"


class MetaBase(UnoModel):
    # Class variables
    table_name = "meta"
    sql_emitters = [AlterGrants]

    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type_id}: {self.id}"
