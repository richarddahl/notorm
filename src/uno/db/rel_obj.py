# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import enum

from typing import Optional, ClassVar

from sqlalchemy import Table, Column
from sqlalchemy.sql.expression import Join, join

from pydantic import BaseModel, computed_field, field_validator

from uno.db.obj import UnoObj
from uno.db.enums import RelType
from uno.config import settings


class UnoRelObj(BaseModel):
    column: ClassVar[str]
    remote_column: ClassVar[str]
    join_table: ClassVar[str] = None
    edge_label: ClassVar[Optional[str]] = None
    rel_type: ClassVar[RelType] = RelType.ONE_TO_MANY
    join: ClassVar[Join] = None
    table: ClassVar[Optional[Table]] = None
    pre_fetch: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @classmethod
    def create_join(cls) -> Join:
        local_column = cls.table.columns[cls.column]
        remote_table = cls.table.metadata.tables[
            f"{settings.DB_SCHEMA}.{cls.remote_column.split('.')[0]}"
        ]
        remote_column = remote_table.columns[cls.remote_column.split(".")[1]]
        if cls.rel_type == RelType.MANY_TO_MANY:
            cls.join = join(
                cls.table,
                remote_table,
                onclause=local_column == remote_column,
            )
        cls.join = join(
            cls.table,
            remote_table,
            onclause=local_column == remote_column,
        )

    def _emit_sql(self, table_name: str) -> str:
        if self.rel_type == RelType.ONE_TO_ONE:
            return f"JOIN {self.obj.table_name} ON {table_name}.{self.column} = {self.obj.table_name}.{self.remote_column}"
        elif self.rel_type == RelType.ONE_TO_MANY:
            return f"JOIN {self.obj.table_name} ON {table_name}.{self.column} = {self.obj.table_name}.{self.remote_column}"
        elif self.rel_type == RelType.MANY_TO_ONE:
            return f"JOIN {self.obj.table_name} ON {table_name}.{self.column} = {self.obj.table_name}.{self.remote_column}"
        elif self.rel_type == RelType.MANY_TO_MANY:
            return f"JOIN {self.join_table} ON {table_name}.{self.column} = {self.join_table}.{self.join_column} JOIN {self.obj.table_name} ON {self.join_table}.{self.join_remote_column} = {self.obj.table_name}.{self.remote_column}"
        else:
            raise ValueError(f"Invalid rel_type: {self.rel_type}")


class GroupRelObj(UnoRelObj):
    column = "group_id"
    remote_column = "group.id"
    edge_label = "IS_ASSIGNED_TO"
    rel_type = RelType.ONE_TO_MANY


class TenantRelObj(UnoRelObj):
    column = "tenant_id"
    remote_column = "tenant.id"
    edge_label = "IS_ASSIGNED_TO"
    rel_type = RelType.ONE_TO_MANY


class CreatedByRelObj(UnoRelObj):
    column = "created_by_id"
    remote_column = "user.id"
    edge_label = "CREATED_BY"
    rel_type = RelType.ONE_TO_MANY


class ModifiedByRelObj(UnoRelObj):
    column = "modified_by_id"
    remote_column = "user.id"
    edge_label = "MODIFIED_BY"
    rel_type = RelType.ONE_TO_MANY


class DeletedByRelObj(UnoRelObj):
    column = "deleted_by_id"
    remote_column = "user.id"
    edge_label = "DELETED_BY"
    rel_type = RelType.ONE_TO_MANY


general_rel_objs = {
    "group_id": GroupRelObj,
    "tenant_id": TenantRelObj,
    "created_by_id": CreatedByRelObj,
    "modified_by_id": ModifiedByRelObj,
    "deleted_by_id": DeletedByRelObj,
}
