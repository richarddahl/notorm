# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sql_config import SQLConfig
from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaType
from uno.db.sql.db_sql_emitters import InsertPermission


class MetaTypeSQLConfig(SQLConfig):
    table_name = "meta_type"
    sql_emitters = [AlterGrants, InsertPermission, InsertMetaType]


class MetaSQLConfig(SQLConfig):
    table_name = "meta"
    sql_emitters = [AlterGrants]
