# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR

from uno.db.mixins import (
    UnoMixin,
    ColumnDef,
    RecordStatusMixin,
    InsertMetaRecordMixin,
)
from uno.db.sql.table_sql_emitters import RecordUserAuditFunction
from uno.auth.sql_emitters import UserRecordAuditFunction


class UserRecordUserAuditMixin(UnoMixin):
    sql_emitters = [UserRecordAuditFunction]

    column_defs = [
        ColumnDef(
            args=["created_by_id", VARCHAR(26)],
            kwargs={
                "index": True,
                "nullable": True,
            },
        ),
        ColumnDef(
            args=["modified_by_id", VARCHAR(26)],
            kwargs={
                "index": True,
                "nullable": True,
            },
        ),
        ColumnDef(
            args=["deleted_by_id", VARCHAR(26)],
            kwargs={
                "index": True,
                "nullable": True,
            },
        ),
    ]

    created_by_id: Optional[str] = None
    modified_by_id: Optional[str] = None
    deleted_by_id: Optional[str] = None


class UserMixin(InsertMetaRecordMixin, RecordStatusMixin, UserRecordUserAuditMixin):
    """Mixin for General Objects"""

    column_defs = []
    sql_emitters = []
