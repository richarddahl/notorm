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

from uno.db.tables import (
    Base,
    RelatedObject,
    ObjectType,
    BaseTable,
    str_26,
    str_255,
)
from uno.db.enums import SQLOperation
from uno.db.sql_emitters import (
    RecordVersionAuditSQL,
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
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
from uno.auth.schemas import (
    user_schema_defs,
    tenant_schema_defs,
    group_schema_defs,
    role_schema_defs,
)


class GroupRole(RelatedObject):
    display_name = "Group Permission"
    display_name_plural = "Group Permissions"

    sql_emitters = []
    include_in_graph = False

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
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

    __tablename__ = "group_role"
    __table_args__ = (
        {
            "comment": "Assigned by admin users to assign roles to groups.",
            "schema": "uno",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "group_role",
        "inherit_condition": id == RelatedObject.id,
    }


class UserGroupRole(RelatedObject):
    display_name = "User Group Role"
    display_name_plural = "User Group Roles"

    sql_emitters = []

    include_in_graph = False

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    group_role_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.group_role.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    __tablename__ = "user__group_role"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": "uno",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "user__group_role",
        "inherit_condition": id == RelatedObject.id,
    }


class Tenant(RelatedObject):
    display_name = "Tenant"
    display_name_plural = "Tenants"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
        InsertGroupForTenant,
    ]
    schema_defs = tenant_schema_defs

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
        info={"edge": "BELONGS_TO_TENANT"},
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="tenant",
        foreign_keys="Group.tenant_id",
        doc="Groups that belong to the tenant",
        info={"edge": "BELONGS_TO_TENANT"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="tenant",
        foreign_keys="Role.tenant_id",
        doc="Roles that belong to the tenant",
        info={"edge": "BELONGS_TO_TENANT"},
    )

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

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Tenant {self.name}>"


class User(RelatedObject):
    display_name = "User"
    display_name_plural = "Users"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
        RecordVersionAuditSQL,
    ]
    schema_defs = user_schema_defs

    exclude_from_properties = ["is_superuser", "is_tenant_admin"]
    graph_properties = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    email: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        doc="Email address, used as login ID",
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
    )
    default_group_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.group.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="Default group for the user",
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

    # Relationships
    tenant: Mapped[Optional[Tenant]] = relationship(
        back_populates="users",
        foreign_keys=[tenant_id],
        doc="Tenant the user belongs to",
        info={"edge": "IS_OWNED_BY"},
    )
    default_group: Mapped[Optional["Group"]] = relationship(
        back_populates="default_group_users",
        foreign_keys=[default_group_id],
        doc="Default group for the user",
        info={"edge": "HAS_DEFAULT_GROUP"},
    )
    owned_objects: Mapped[list[RelatedObject]] = relationship(
        back_populates="owner",
        foreign_keys="RelatedObject.owner_id",
        primaryjoin="User.id == RelatedObject.owner_id",
        doc="The objects owned by the user",
        info={"edge": "OWNS"},
    )
    modified_objects: Mapped[list[RelatedObject]] = relationship(
        back_populates="modified_by",
        foreign_keys=[RelatedObject.modified_by_id],
        primaryjoin="RelatedObject.modified_by_id == RelatedObject.id",
        doc="The objects last modified by the user",
        info={"edge": "MODIFIED"},
    )
    deleted_objects: Mapped[list[RelatedObject]] = relationship(
        back_populates="deleted_by",
        foreign_keys=[RelatedObject.deleted_by_id],
        primaryjoin="RelatedObject.deleted_by_id == RelatedObject.id",
        doc="The objects delted by the user",
        info={"edge": "DELETED"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="users",
        secondary=UserGroupRole.__table__,
        doc="Roles assigned to the user",
        info={"edge": "IS_ASSIGNED"},
    )

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

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class RolePermission(Base):
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
    )
    permission_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.permission.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="Permission ID",
    )

    __tablename__ = "role__permission"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": "uno",
        },
    )


class Permission(Base):
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
    object_type_name: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.name", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="Table the permission is for",
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
        doc="Table the permission is for",
        info={"edge": "ALLOWS_ACCESS_TO"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="permissions",
        secondary=RolePermission.__table__,
        doc="Roles that have this permission",
        info={"edge": "ALLOWS_ACCESS_VIA"},
    )

    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint(
            "object_type_name",
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

    def __str__(self) -> str:
        return f"{self.object_type.name} - {self.actions}"


class Role(RelatedObject):
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
    )
    name: Mapped[str_255] = mapped_column(doc="Role name")
    description: Mapped[str] = mapped_column(doc="Role description")

    # Relationships
    permissions: Mapped[list[Permission]] = relationship(
        back_populates="roles",
        secondary=RolePermission.__table__,
        doc="Permissions assigned to the role",
        info={"edge": "ALLOWS_PERMISSION"},
    )
    tenant: Mapped[Tenant] = relationship(
        back_populates="roles",
        foreign_keys="Role.tenant_id",
        doc="Tenants that have this role",
        info={"edge": "BELONGS_TO_TENANT"},
    )
    users: Mapped[list["User"]] = relationship(
        back_populates="roles",
        secondary=UserGroupRole.__table__,
        doc="Users that have this role",
        info={"edge": "IS_ASSIGNED_TO"},
    )

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

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Group(RelatedObject):
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
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")

    # Relationships
    tenant: Mapped[Tenant] = relationship(
        back_populates="groups",
        foreign_keys="Group.tenant_id",
        doc="Tenant the group belongs to",
        info={"edge": "BELONGS_TO_TENANT"},
    )
    default_group_users: Mapped[list["User"]] = relationship(
        back_populates="default_group",
        foreign_keys="User.default_group_id",
        doc="Users that belong to the group",
        info={"edge": "HAS_DEFAULT_GROUP"},
    )

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

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Group {self.name}>"
