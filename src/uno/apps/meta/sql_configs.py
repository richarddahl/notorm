# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sql_config import SQLConfig
from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaType
from uno.db.sql.db_sql_emitters import InsertPermission
from uno.db.sql.graph_sql_emitters import NodeSQLEmitter
from uno.apps.meta.models import MetaType, Meta


class MetaTypeSQLConfig(SQLConfig):
    table_name = "meta_type"
    model = MetaType
    sql_emitters = [
        AlterGrants,
        InsertPermission,
        InsertMetaType,
        # NodeSQLEmitter,
    ]


class MetaSQLConfig(SQLConfig):
    table_name = "meta"
    model = Meta
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        # NodeSQLEmitter,
    ]
