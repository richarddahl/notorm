# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import copy


from uno.db.rel_obj import (
    UnoRelObj,
    GroupRelObj,
    TenantRelObj,
    CreatedByRelObj,
    ModifiedByRelObj,
    DeletedByRelObj,
    general_rel_objs,
)
from uno.db.enums import RelType


class UserDefaultGroupRelObj(UnoRelObj):
    local_column_name: str = "default_group_id"
    remote_table_name: str = "group"
    remote_column_name: str = "id"
    rel_type: RelType = RelType.ONE_TO_MANY
    edge_label: str = "IS_ASSIGNED_TO"


user_rel_objs = {
    "tenant_id": TenantRelObj,
    "default_group_id": UserDefaultGroupRelObj,
    "created_by_id": CreatedByRelObj,
    "modified_by_id": ModifiedByRelObj,
    "deleted_by_id": DeletedByRelObj,
}
"""
user_rel_objs.update(
    {
        "created_objects": UnoRelObj(
            column="created_by_id",
            populates="created_objects",
            remote_column="user.id",
            edge_label="CREATED",
            multiple=True,
            rel_type="ONE_TO_MANY",
        ),
        "modified_objects": UnoRelObj(
            column="modified_by_id",
            populates="modified_objects",
            remote_column="user.id",
            edge_label="MODIFIED",
            multiple=True,
            rel_type="ONE_TO_MANY",
        ),
        "deleted_objects": UnoRelObj(
            column="deleted_by_id",
            populates="deleted_objects",
            remote_column="user.id",
            edge_label="DELETED",
            multiple=True,
            rel_type="ONE_TO_MANY",
        ),
    }
)
"""

group_rel_objs = copy.deepcopy(general_rel_objs)
"""
group_rel_objs.update(
    {
        "members": UnoRelObj(
            column="id",
            populates="members",
            remote_column="user.id",
            edge_label="HAS_MEMBER",
            multiple=True,
            join_table="user__group__role",
            join_column="group_id",
            join_remote_column="user_id",
            rel_type="MANY_TO_MANY",
        ),
        "roles": UnoRelObj(
            column="id",
            populates="roles",
            remote_column="role.id",
            edge_label="HAS_ROLE",
            multiple=True,
            join_table="user__group__role",
            join_column="group_id",
            join_remote_column="role_id",
            rel_type="MANY_TO_MANY",
        ),
    },
)
"""

role_rel_objs = copy.deepcopy(general_rel_objs)
"""
role_rel_objs.update(
    {
        "tenant": UnoRelObj(
            column="tenant_id",
            populates="tenant",
            remote_column="tenant.id",
            edge_label="BELONGS_TO",
            multiple=False,
            rel_type="ONE_TO_MANY",
        )
    }
)
"""
