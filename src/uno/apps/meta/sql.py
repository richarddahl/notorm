# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sql_emitter import UnoSQL
from uno.db.sql.table_sql_emitters import AlterGrants, InsertPermission


class MetaTypeSQL(UnoSQL):
    sql_emitters = [AlterGrants, InsertPermission]
    table_name = "meta_type"


class MetaBaseSQL(UnoSQL):
    sql_emitters = [AlterGrants]
    table_name = "meta"
