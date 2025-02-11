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


class Permission(Base, RelatedObjectPKMixin):
    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint(
            "object_type_id",
            "operations",
            name="uq_ObjectType_operations",
        ),
        {
            "schema": "uno",
            "comment": """
                Permissions for each table.
                Created automatically by the DB via a trigger when a Table using role access is created.
                Records are created for each table with the following combinations of permissions:
                    [SELECT]
                    [SELECT, INSERT]
                    [SELECT, UPDATE]
                    [SELECT, INSERT, UPDATE]
                    [SELECT, INSERT, UPDATE, DELETE]
                Deleted automatically by the DB via the FK Constraints ondelete when a object_type is deleted.
            """,
            "info": {"rls_policy": "superuser", "vertex": False},
        },
    )
    verbose_name = "Permission"
    verbose_name_plural = "Permissions"
    # include_in_graph = False

    sql_emitters = [InsertObjectTypeRecordSQL]

    object_type_id: Mapped[ObjectType] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "HAS_ObjectType"},
    )
    operations: Mapped[list[SQLOperation]] = mapped_column(
        ARRAY(
            ENUM(
                SQLOperation,
                name="sqloperation",
                create_type=True,
                schema="uno",
            )
        ),
        doc="Operations that are permissible",
    )

    def __str__(self) -> str:
        return f"{self.object_type} - {self.actions}"

    def __repr__(self) -> str:
        return f"<TablePermission {self.object_type} - {self.actions}>"


class Role(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "role"
    __table_args__ = (
        Index("ix_role_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": """
                Roles, created by end user group admins, enable assignment of group_permissions
                by functionality, department, etc... to users.
            """,
            "schema": "uno",
            "info": {"rls_policy": "admin", "vertex": False},
        },
    )
    verbose_name = "Role"
    verbose_name_plural = "Roles"
    # include_in_graph = False

    sql_emitters = [InsertObjectTypeRecordSQL]

    # Columns
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant the role belongs to",
        info={"edge": "BELONGS_TO_TENANT"},
    )
    name: Mapped[str_255] = mapped_column(doc="Role name")
    description: Mapped[str] = mapped_column(doc="Role description")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class RolePermission(Base):
    __tablename__ = "role_permission"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": "uno",
            "info": {"rls_policy": "none"},
        },
    )
    verbose_name = "Role Permission"
    verbose_name_plural = "Role Permissions"
    include_in_graph = False

    # Columns
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.role.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="Role ID",
        info={"edge": "HAS_ROLE"},
    )
    permission_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.permission.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="Permission ID",
        info={"edge": "HAS_PERMISSION"},
    )

    def __str__(self) -> str:
        return f"{self.role_id} - {self.permission_id}"

    def __repr__(self) -> str:
        return f"<RolePermission {self.role_id} - {self.permission_id}>"


class Group(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "group"
    __table_args__ = (
        Index("ix_group_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": "Application end-user groups",
            "schema": "uno",
            "info": {"rls_policy": "admin"},
        },
    )
    verbose_name = "Group"
    verbose_name_plural = "Groups"
    # include_in_graph = False

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        ValidateGroupInsert,
        DefaultGroupTenant,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns

    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "BELONGS_TO_TENANT"},
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")

    # Relationships
    users_default_group: Mapped[list["User"]] = relationship(
        back_populates="default_group",
        foreign_keys="User.default_group_id",
        doc="Users that have this group as their default group",
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Group {self.name}>"


class UserGroup(Base):
    __tablename__ = "user__group__role"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": "uno",
            "info": {"rls_policy": "admin", "vertex": False},
        },
    )
    verbose_name = "User Group Role"
    verbose_name_plural = "User Group Roles"
    include_in_graph = False

    sql_emitters = [InsertObjectTypeRecordSQL]

    # Columns
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"edge": "HAS_USER"},
    )
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.group.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"edge": "HAS_GROUP"},
    )
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.role.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"property": True},
    )
