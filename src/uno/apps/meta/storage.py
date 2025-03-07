# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import BaseModel

from uno.storage.storage import UnoStorage
from uno.storage.sql.table_sql_emitters import (
    AlterGrants,
    InsertPermission,
)
from uno.config import settings


class MetaTypeStorage(UnoStorage):
    table_name: Optional[str] = "meta_type"
    sql_emitters: list[BaseModel] = [AlterGrants, InsertPermission]


class MetaStorage(UnoStorage):
    table_name: Optional[str] = "meta"
    sql_emitters: list[BaseModel] = [AlterGrants]
