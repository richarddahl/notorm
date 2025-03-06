# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, ClassVar

from sqlalchemy import Table, Column
from sqlalchemy.sql.expression import Join, join, Alias

from pydantic import BaseModel, computed_field, field_validator
from pydantic.fields import Field

from uno.record.obj import UnoRecord
from uno.record.enums import RelType
from uno.utilities import create_random_alias
from uno.config import settings


def set_local_column_alias(values: dict) -> Alias:
    local_table_alias = values["local_table_alias"]
    local_column_name = values["local_column_name"]
    local_column_alias = local_table_alias.columns[local_column_name]
    return local_column_alias


def set_remote_table(values: dict) -> Table:
    remote_table_name = values["remote_table_name"]
    local_table = values["local_table"]
    remote_table = local_table.metadata.tables[
        f"{settings.DB_SCHEMA}.{remote_table_name}"
    ]
    return remote_table


def set_remote_table_alias(values: dict) -> Alias:
    remote_table = values["remote_table"]
    remote_table_alias = create_random_alias(
        remote_table,
        prefix=remote_table.name,
    )
    return remote_table_alias


def set_remote_column_alias(values: dict) -> Alias:
    remote_table_alias = values["remote_table_alias"]
    remote_column_name = values["remote_column_name"]
    remote_column_alias = remote_table_alias.columns[remote_column_name]
    return remote_column_alias


class UnoRelObj(BaseModel):
    obj_class_name: str
    local_table: Table
    local_column_name: str
    local_table_alias: Alias
    local_column_alias: Alias = Field(default_factory=set_local_column_alias)

    remote_table_name: str
    remote_column_name: str

    remote_table: Table = Field(default_factory=set_remote_table)
    remote_table_alias: Alias = Field(default_factory=set_remote_table_alias)
    remote_column_alias: Alias = Field(default_factory=set_remote_column_alias)

    join_table: str = None
    # join_table_alias: Alias <-- This is a computed field
    join_table_column: str = None
    # join_table_column_alias: Alias <-- This is a computed field

    rel_type: RelType = RelType.ONE_TO_MANY
    pre_fetch: bool = True
    edge_label: Optional[str] = None

    # join: Join <-- this is a computed field

    model_config = {"arbitrary_types_allowed": True}

    @computed_field
    def join(self) -> Join:
        if self.rel_type == RelType.MANY_TO_MANY:
            pass
        return join(
            self.local_table_alias,
            self.remote_table_alias,
            onclause=self.local_column_alias == self.remote_column_alias,
            isouter=True,
        )


class GroupRelObj(UnoRelObj):
    local_column_name: str = "group_id"
    remote_table_name: str = "group"
    remote_column_name: str = "id"
    rel_type: RelType = RelType.ONE_TO_MANY
    edge_label: str = "IS_ASSIGNED_TO"


class TenantRelObj(UnoRelObj):
    local_column_name: str = "tenant_id"
    remote_table_name: str = "tenant"
    remote_column_name: str = "id"
    rel_type: RelType = RelType.ONE_TO_MANY
    edge_label: str = "IS_ASSIGNED_TO"


class CreatedByRelObj(UnoRelObj):
    local_column_name: str = "created_by_id"
    remote_table_name: str = "user"
    remote_column_name: str = "id"
    rel_type: RelType = RelType.ONE_TO_MANY
    edge_label: str = "CREATED_BY"


class ModifiedByRelObj(UnoRelObj):
    local_column_name: str = "modified_by_id"
    remote_table_name: str = "user"
    remote_column_name: str = "id"
    rel_type: RelType = RelType.ONE_TO_MANY
    edge_label: str = "MODIFIED_BY"


class DeletedByRelObj(UnoRelObj):
    local_column_name: str = "deleted_by_id"
    remote_table_name: str = "user"
    remote_column_name: str = "id"
    rel_type: RelType = RelType.ONE_TO_MANY
    edge_label: str = "DELETED_BY"


general_rel_objs = {
    "group_id": GroupRelObj,
    "tenant_id": TenantRelObj,
    "created_by_id": CreatedByRelObj,
    "modified_by_id": ModifiedByRelObj,
    "deleted_by_id": DeletedByRelObj,
}
