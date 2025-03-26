# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import EmailStr

from uno.db.enums import SQLOperation
from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.pkgs.auth.enums import TenantType
from uno.pkgs.auth.bases import (
    UserBase,
    GroupBase,
    RoleBase,
    TenantBase,
    PermissionBase,
)
from uno.pkgs.auth.mixins import RecordAuditMixin
from uno.config import settings


class User(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = UserBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
                "default_group",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "email",
                "handle",
                "full_name",
                "tenant_id",
                "default_group_id",
                "is_superuser",
            ],
        ),
    }
    terminate_filters = True
    endpoint_tags = ["Authorization"]

    # Fields
    email: EmailStr = None
    handle: str = None
    full_name: str = None
    tenant: Optional["Tenant"] = None
    tenant_id: Optional[str] = None
    default_group: Optional["Group"] = None
    default_group_id: Optional[str] = None
    is_superuser: bool = False

    # roles: Optional[list["Role"]] = None
    # created_objects: Optional[list[MetaBase]] = None
    # modified_objects: Optional[list[MetaBase]] = None
    # deleted_objects: Optional[list[MetaBase]] = None

    def __str__(self) -> str:
        return self.handle


class Group(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = GroupBase

    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "tenant_id",
            ],
        ),
    }
    terminate_filters = True
    endpoint_tags = ["Authorization"]

    # Fields
    id: Optional[str]
    name: str
    tenant_id: Optional[str]
    tenant: Optional["Tenant"]

    # roles: list["Role"] = []
    # default_users: list[User] = []
    # members: list[User] = []

    def __str__(self) -> str:
        return self.name


class Role(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = RoleBase

    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
            ],
        ),
    }
    terminate_filters = True
    endpoint_tags = ["Authorization"]

    # Fields
    id: Optional[str]
    name: str
    description: Optional[str]
    tenant_id: Optional[str]
    tenant: Optional["Tenant"]

    def __str__(self) -> str:
        return self.name


class Tenant(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = TenantBase

    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "tenant_type",
            ],
        ),
    }
    terminate_filters = True
    endpoint_tags = ["Authorization"]

    # Fields
    id: Optional[str]
    name: str
    tenant_type: TenantType

    # users: list["User"] = []
    # groups: list["Group"] = []
    # roles: list["Role"] = []

    def __str__(self) -> str:
        return self.name


class Permission(UnoModel):
    # Class variables
    base = PermissionBase
    endpoints = []
    schema_configs = {}
    terminate_filters = True
    endpoint_tags = ["Authorization"]

    # Fields
    id: Optional[int]
    meta_type_id: str
    operation: SQLOperation

    def __str__(self) -> str:
        return f"{self.meta_type.id}:  {self.operation}"
