# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.table_sql_emitters import (
    AlterGrants,
    InsertMetaType,
)
from uno.db.sql.db_sql_emitters import (
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.db.sql.sql_config import SQLConfig, TableSQLConfig
from uno.db.sql.graph_sql_emitters import TableGraphSQLEmitter
from uno.db.sql.graph_sql_emitters import NodeSQLEmitter
from uno.apps.fltr.models import Filter, FilterValue, Query


class FilterSQLConfig(SQLConfig):
    table_name = "filter"
    model = Filter
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        NodeSQLEmitter,
    ]


class FilterValueSQLConfig(SQLConfig):
    table_name = "filter_value"
    model = FilterValue
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        NodeSQLEmitter,
    ]


class QuerySQLConfig(SQLConfig):
    table_name = "query"
    model = Query
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        NodeSQLEmitter,
    ]


"""


class RolePermisionSQLConfig(TableSQLConfig):
    table_name = "role__permission"
    sql_emitters = [
        TableGraphSQLEmitter(
            local_node_label="Role",
            column_name="role_id",
            label="HAS_PERMISSIONS",
            remote_table_name="permission",
            remote_column_name="permission_id",
            remote_node_label="Permission",
        ),
        TableGraphSQLEmitter(
            local_node_label="Permission",
            column_name="permission_id",
            label="HAS_PERMISSIONS_FROM",
            remote_table_name="role",
            remote_column_name="role_id",
            remote_node_label="Role",
        ),
    ]


"""
