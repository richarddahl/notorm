# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from uno.db.mixins import (
    UnoMixin,
    RecordStatusMixin,
    InsertMetaRecordMixin,
)
from uno.auth.sql_emitters import UserRecordAuditFunction


class UserRecordUserAuditMixin(UnoMixin):
    sql_emitters = [UserRecordAuditFunction]

    created_by_id: Optional[str] = None
    modified_by_id: Optional[str] = None
    deleted_by_id: Optional[str] = None


class UserMixin(
    InsertMetaRecordMixin,
    RecordStatusMixin,
    UserRecordUserAuditMixin,
):
    """Mixin for General Objects"""

    column_defs = []
    sql_emitters = []
