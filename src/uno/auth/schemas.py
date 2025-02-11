# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional
from pydantic import BaseModel

from uno.db.enums import SQLOperation

from uno.objs.tables import ObjectType

from uno.auth.enums import TenantType


class TenantSchema(BaseModel):
    name: str
    tenant_type: TenantType

    tenant_users: list["UserSchema"]


class UserSchema(BaseModel):
    email: str
    handle: str
    full_name: str
    tenant_id: Optional[str]
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool
    created_at: datetime.datetime
    owner_id: Optional[str]
    modified_at: datetime.datetime
    modified_by_id: str
    deleted_at: Optional[datetime.datetime]
    deleted_by_id: Optional[str]

    tenant: Optional[TenantSchema]
    default_group: Optional["GroupSchema"]


class PermissionSchema(BaseModel):
    object_type_id: ObjectType
    operations: list[SQLOperation]


class RoleSchema(BaseModel):
    tenant_id: str
    name: str
    description: str


class RolePermissionSchema(BaseModel):
    role_id: str
    permission_id: str


class GroupSchema(BaseModel):
    tenant_id: str
    name: str
    users_default_group: list["UserSchema"]


class UserGroupSchema(BaseModel):
    user_id: str
    group_id: str
    role_id: str
