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
    Table,
    Column,
    Integer,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import ENUM, ARRAY

from uno.db.base import Base, RelatedObject, str_26, str_255
from uno.db.mixins import BaseFieldMixin, RelatedObjectPKMixin
from uno.db.sql_emitters import RecordVersionAuditSQL
from uno.db.enums import SQLOperation

# from uno.obj.tables import ObjectType
from uno.glbl.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
)
from uno.db.mixins import RelatedObjectPKMixin, BaseFieldMixin
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
from uno.auth.schemas import (
    user_schema_defs,
    tenant_schema_defs,
    group_schema_defs,
    role_schema_defs,
)
from uno.auth.graphs import tenant_edge_defs, user_edge_defs


class GroupRole(Base, BaseFieldMixin):
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
    include_in_graph = False

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the Group Role.",
    )
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.group.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.role.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )


class UserGroupRole(Base, BaseFieldMixin):
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

    sql_emitters = []

    include_in_graph = False

    # Columns
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
    )
    group_role_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.group_role.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
    )


class Tenant(RelatedObject):
    __tablename__ = "tenant"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Application end-user tenants",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "tenant",
        "inherit_condition": id == RelatedObject.id,
    }

    display_name = "Tenant"
    display_name_plural = "Tenants"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
        InsertGroupForTenant,
    ]
    schema_defs = tenant_schema_defs

    graph_edge_defs = tenant_edge_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
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
    roles: Mapped[list["Role"]] = relationship(
        back_populates="tenant",
        foreign_keys="Role.tenant_id",
        doc="Roles that belong to the tenant",
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Tenant {self.name}>"


class User(RelatedObject):
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
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "user",
        "inherit_condition": id == RelatedObject.id,
    }

    display_name = "User"
    display_name_plural = "Users"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
        RecordVersionAuditSQL,
    ]
    schema_defs = user_schema_defs

    graph_edge_defs = user_edge_defs
    exclude_from_properties = ["is_superuser", "is_tenant_admin"]
    graph_properties = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
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
        doc="Tenant to which the user belongs.",
        info={"edge": {"name": "WORKS_FOR", "accessor": "tenant"}},
    )
    default_group_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.group.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="Default group for the user",
        info={"edge": {"name": "HAS_DEFAULT_GROUP", "accessor": "default_group"}},
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
        doc="User that owns this user.",
        info={"edge": {"name": "HAS_OWNER", "accessor": "owner"}},
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
    modified_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        doc="User that last modified this user",
        info={"edge": {"name": "WAS_LAST_MODIFIED_BY", "accessor": "modified_by"}},
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        doc="User that deleted this user",
        info={"edge": {"name": "WAS_DELETED_BY", "accessor": "deleted_by"}},
    )

    # Relationships
    tenant: Mapped[Optional[Tenant]] = relationship(
        back_populates="users",
        foreign_keys=[tenant_id],
        doc="Tenant the user belongs to",
    )
    default_group: Mapped[Optional["Group"]] = relationship(
        back_populates="default_group_users",
        foreign_keys=[default_group_id],
        doc="Default group for the user",
    )

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Permission(Base):
    __tablename__ = "permission"
    __table_args__ = (
        # UniqueConstraint(
        #    "object_type_id",
        #    "operation",
        #    name="uq_objecttype_operation",
        # ),
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
    include_in_graph = False

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    """
    object_type_id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="Table the permission is for",
        info={"edge": "PROVIDES_PERMISSION_FOR_OBJECT_TYPE"},
    )
    """
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
    # object_type: Mapped[ObjectType] = relationship(
    #    back_populates="permissions",
    # )

    def __str__(self) -> str:
        return f"{self.object_type} - {self.actions}"

    def __repr__(self) -> str:
        return f"<TablePermission {self.object_type} - {self.actions}>"


class Role(RelatedObject):
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
    __mapper_args__ = {
        "polymorphic_identity": "role",
        "inherit_condition": id == RelatedObject.id,
    }

    display_name = "Role"
    display_name_plural = "Roles"

    sql_emitters = [InsertObjectTypeRecordSQL]
    schema_defs = role_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
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
    # permissions: Mapped[list[Permission]] = relationship(
    #    back_populates="roles",
    #    secondary="uno.role__permission",
    #    doc="Permissions assigned to the role",
    # )
    tenant: Mapped[Tenant] = relationship(
        back_populates="roles",
        foreign_keys="Role.tenant_id",
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
        InsertRelatedObjectFunctionSQL,
    ]

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


class Group(RelatedObject):
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
    __mapper_args__ = {
        "polymorphic_identity": "group",
        "inherit_condition": id == RelatedObject.id,
    }

    display_name = "Group"
    display_name_plural = "Groups"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        ValidateGroupInsert,
        DefaultGroupTenant,
        InsertRelatedObjectFunctionSQL,
    ]
    schema_defs = group_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "BELONGS_TO_TENANT"},
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")

    # Relationships
    tenant: Mapped[Tenant] = relationship(
        back_populates="groups",
        foreign_keys="Group.tenant_id",
        doc="Tenant the group belongs to",
    )
    default_group_users: Mapped[list["User"]] = relationship(
        back_populates="default_group",
        foreign_keys="User.default_group_id",
        doc="Users that belong to the group",
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Group {self.name}>"
