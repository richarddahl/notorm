# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap
import datetime

from typing import Optional, ClassVar

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    Identity,
    func,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import ENUM, ARRAY

from uno.db.base import Base, str_26, str_255
from uno.db.mixins import BaseFieldMixin, DBObjectPKMixin
from uno.sql_emitters import RecordVersionAuditSQL
from uno.db.enums import SQLOperation
from uno.graphs import GraphNode, GraphEdge

from uno.obj.tables import ObjectType
from uno.obj.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertDBObjectFunctionSQL,
)

from uno.auth.sql_emitters import (
    ValidateGroupInsert,
    InsertGroupForTenant,
    DefaultGroupTenant,
)
from uno.auth.rls_sql_emitters import (
    RLSSQL,
    UserRLSSQL,
    TenantRLSSQL,
)
from uno.auth.enums import TenantType
from uno.auth.schemas import user_schemas
from uno.auth.graphs import tenant_node, tenant_edges, user_node, user_edges, group_node


class Tenant(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "tenant"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Application end-user tenants",
        },
    )
    display_name = "Tenant"
    display_name_plural = "Tenants"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertDBObjectFunctionSQL,
        InsertGroupForTenant,
    ]

    graph_node = tenant_node
    graph_edges = tenant_edges

    edges: ClassVar[list[GraphEdge]] = [
        GraphEdge(
            label="HAS_USER",
            start_node_label="Tenant",
            end_node_label="User",
            accessor="tenant_users",
        ),
    ]

    # Columns
    name: Mapped[str_255] = mapped_column(unique=True, doc="Tenant name")
    tenant_type: Mapped[TenantType] = mapped_column(
        ENUM(TenantType, name="tenanttype", create_type=True, schema="uno"),
        server_default=TenantType.INDIVIDUAL.name,
        doc="Tenant type",
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        back_populates="tenant",
        foreign_keys="User.tenant_id",
        doc="Users that belong to the tenant",
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="tenant",
        foreign_keys="Group.tenant_id",
        doc="Groups that belong to the tenant",
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Tenant {self.name}>"


class User(Base, DBObjectPKMixin):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            textwrap.dedent(
                """
                (is_superuser = 'false' AND default_group_id IS NOT NULL) OR 
                (is_superuser = 'true' AND default_group_id IS NULL) AND
                (is_superuser = 'false' AND is_tenant_admin = 'false') OR
                (is_superuser = 'true' AND is_tenant_admin = 'false') OR
                (is_superuser = 'false' AND is_tenant_admin = 'true') 
            """
            ),
            name="ck_user_is_superuser",
        ),
        {
            "schema": "uno",
            "comment": "Application users",
            "info": {"audit_type": "history"},
        },
    )
    display_name = "User"
    display_name_plural = "Users"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertDBObjectFunctionSQL,
        RecordVersionAuditSQL,
    ]
    schemas = user_schemas

    graph_node = user_node
    graph_edges = user_edges

    # Columns
    email: Mapped[str_255] = mapped_column(
        unique=True, index=True, doc="Email address, used as login ID"
    )
    handle: Mapped[str_255] = mapped_column(
        unique=True, index=True, doc="User's displayed name and alternate login ID"
    )
    full_name: Mapped[str_255] = mapped_column(doc="User's full name")
    tenant_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    default_group_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.group.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    is_superuser: Mapped[bool] = mapped_column(
        server_default=text("false"),
        index=True,
        doc="Superuser status",
    )
    is_tenant_admin: Mapped[bool] = mapped_column(
        server_default=text("false"),
        index=True,
        doc="Tenant admin status",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates if the record is active",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.current_timestamp(),
        doc="Time the record was created",
    )
    owner_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
    modified_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_LAST_MODIFIED_BY", "editable": False},
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
        info={"editable": False},
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "WAS_DELETED_BY", "editable": False},
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship(
        back_populates="tenant_users",
        foreign_keys=[tenant_id],
        doc="Tenant the user belongs to",
    )
    default_group: Mapped["Group"] = relationship(
        back_populates="users_default_group",
        foreign_keys=[default_group_id],
        doc="Default group for the user",
    )
    owner: Mapped["User"] = relationship(
        back_populates="owned_users",
        foreign_keys=[owner_id],
        doc="User that owns this user",
    )
    modified_by: Mapped["User"] = relationship(
        back_populates="modified_users",
        foreign_keys=[modified_by_id],
        doc="User that last modified this user",
    )
    deleted_by: Mapped["User"] = relationship(
        back_populates="deleted_users",
        foreign_keys=[deleted_by_id],
        doc="User that deleted this user",
    )

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Permission(Base):
    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint(
            "object_type_id",
            "operation",
            name="uq_objecttype_operation",
        ),
        {
            "comment": """
                Permissions for each table.
                Deleted automatically by the DB via the FK Constraints
                ondelete when a object_type is deleted.
            """,
            "schema": "uno",
        },
    )
    display_name = "Permission"
    display_name_plural = "Permissions"

    sql_emitters = []

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    object_type_id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="Table the permission is for",
        info={"edge": "PROVIDES_PERMISSION_FOR_OBJECT_TYPE"},
    )
    operation: Mapped[SQLOperation] = mapped_column(
        ENUM(
            SQLOperation,
            name="sqloperation",
            create_type=True,
            schema="uno",
        ),
        primary_key=True,
        doc="Operation that is permissible",
    )

    # Relationships
    object_type: Mapped[ObjectType] = relationship(
        back_populates="permissions",
    )

    def __str__(self) -> str:
        return f"{self.object_type} - {self.actions}"

    def __repr__(self) -> str:
        return f"<TablePermission {self.object_type} - {self.actions}>"


class Role(Base, DBObjectPKMixin, BaseFieldMixin):
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
        },
    )
    display_name = "Role"
    display_name_plural = "Roles"

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

    # Relationships
    permissions: Mapped[list[Permission]] = relationship(
        back_populates="roles",
        secondary="uno.role__permission",
        doc="Permissions assigned to the role",
    )
    tenants: Mapped[list[Tenant]] = relationship(
        back_populates="roles",
        doc="Tenants that have this role",
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class RolePermission(Base):
    __tablename__ = "role__permission"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": "uno",
        },
    )
    display_name = "Role Permission"
    display_name_plural = "Role Permissions"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertDBObjectFunctionSQL,
    ]
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


class Group(Base, DBObjectPKMixin, BaseFieldMixin):
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
    display_name = "Group"
    display_name_plural = "Groups"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        ValidateGroupInsert,
        DefaultGroupTenant,
        InsertDBObjectFunctionSQL,
    ]

    graph_node = group_node

    # Columns
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "BELONGS_TO_TENANT"},
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")

    # Relationships
    users: Mapped[list["User"]] = relationship(
        back_populates="groups",
        secondary="uno.user__group_role",
        doc="Users that belong to the group",
    )
    default_group_users: Mapped[list["User"]] = relationship(
        back_populates="default_group",
        foreign_keys="user.default_group_id",
        doc="Users that have this group as their default group",
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Group {self.name}>"


class GroupRole(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "group_role"
    __table_args__ = (
        {
            "comment": "Assigned by admin users to assign roles to groups.",
            "schema": "uno",
        },
    )
    display_name = "Group Permission"
    display_name_plural = "Group Permissions"

    sql_emitters = []

    # Columns
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.group.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "HAS_GROUP"},
    )
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.role.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "HAS_ROLE"},
    )


class UserGroupRole(Base):
    __tablename__ = "user__group_role"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": "uno",
        },
    )
    display_name = "User Group Role"
    display_name_plural = "User Group Roles"
    # include_in_graph = False

    sql_emitters = []

    # Columns
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"edge": "HAS_USER"},
    )
    group_role_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.group_role.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"edge": "HAS_GROUP_ROLE"},
    )
