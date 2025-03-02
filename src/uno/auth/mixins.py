# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import VARCHAR

from pydantic import BaseModel
from pydantic.fields import Field

from uno.db.rel_obj import UnoRelObj
from uno.db.mixins import (
    UnoMixin,
    RecordStatusMixin,
    InsertMetaRecordMixin,
    ColumnDef,
    UnoMixinFKConstraint,
    UnoMixinCKConstraint,
    UnoMixinUQConstraint,
)
from uno.auth.sql_emitters import UserRecordAuditFunction


class UserRecordUserAuditMixin(UnoMixin):
    sql_emitters = [UserRecordAuditFunction]

    column_defs = [
        ColumnDef(
            args=["created_by_id", VARCHAR(26)],
            kwargs={
                "nullable": False,
                "doc": "User that created the record",
            },
        ),
        ColumnDef(
            args=["modified_by_id", VARCHAR(26)],
            kwargs={
                "nullable": False,
                "doc": "User that last modified the record",
            },
        ),
        ColumnDef(
            args=["deleted_by_id", VARCHAR(26)],
            kwargs={
                "nullable": True,
                "doc": "User that deleted the record",
            },
        ),
    ]

    constraint_defs = [
        UnoMixinFKConstraint(
            columns=["created_by_id"],
            ref_columns=["user.id"],
            name="fk_created_by_id",
        ),
        UnoMixinFKConstraint(
            columns=["modified_by_id"],
            ref_columns=["user.id"],
            name="fk_modified_by_id",
        ),
        UnoMixinFKConstraint(
            columns=["deleted_by_id"],
            ref_columns=["user.id"],
            name="fk_deleted_by_id",
        ),
        UnoMixinCKConstraint(
            sqltext="""
                is_superuser = 'true'  OR
                is_superuser = 'false' AND
                default_group_id IS NOT NULL AND
               tenant_id IS NOT NULL AND
                created_by_id IS NOT NULL AND
                modified_by_id IS NOT NULL
             """,
            name="ck_user_is_superuser",
        ),
    ]

    created_by_id: Optional[str | BaseModel] = Field(
        None, serialization_alias="Created By"
    )
    modified_by_id: Optional[str | BaseModel] = Field(
        None, serialization_alias="Modified By"
    )
    deleted_by_id: Optional[str | BaseModel] = Field(
        None, serialization_alias="Deleted By"
    )


class UserMixin(
    InsertMetaRecordMixin,
    RecordStatusMixin,
    UserRecordUserAuditMixin,
):
    """Mixin for User Objects"""
