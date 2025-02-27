# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import enum

from typing import Optional

from pydantic import BaseModel, computed_field

from uno.db.obj import UnoObj


class RelType(str, enum.Enum):
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"


class UnoRelObj(BaseModel):
    column: str
    remote_column: str
    populates: str
    edge_label: Optional[str] = None
    multiple: bool = False
    join_table: Optional[str] = None
    join_column: Optional[str] = None
    join_remote_column: Optional[str] = None
    rel_type: RelType = RelType.ONE_TO_MANY
    pre_fetch: bool = False
    # obj: UnoObj <- computed_field

    @computed_field
    def obj(self) -> UnoObj:

        return UnoObj.registry[self.populates]


general_rel_objs = {
    "meta_record": UnoRelObj(
        column="id",
        remote_column="meta_record.id",
        populates="meta_record",
        edge_label="IS_META_RECORD",
        rel_type=RelType.ONE_TO_ONE,
    ),
    "group": UnoRelObj(
        column="group_id",
        populates="group",
        remote_column="group.id",
        edge_label="IS_ASSIGNED_TO",
        rel_type=RelType.ONE_TO_MANY,
    ),
    "tenant": UnoRelObj(
        column="tenant_id",
        populates="tenant",
        remote_column="tenant.id",
        edge_label="IS_ASSIGNED_TO",
        rel_type=RelType.ONE_TO_MANY,
    ),
    "created_by": UnoRelObj(
        column="created_by_id",
        remote_column="user.id",
        populates="created_by",
        edge_label="CREATED_BY",
        rel_type=RelType.ONE_TO_MANY,
        pre_fetch=True,
    ),
    "modified_by": UnoRelObj(
        column="modified_by_id",
        remote_column="user.id",
        populates="modified_by",
        edge_label="MODIFIED_BY",
        rel_type=RelType.ONE_TO_MANY,
        pre_fetch=True,
    ),
    "deleted_by": UnoRelObj(
        column="deleted_by_id",
        remote_column="user.id",
        populates="deleted_by",
        edge_label="DELETED_BY",
        rel_type=RelType.ONE_TO_MANY,
        pre_fetch=True,
    ),
}
