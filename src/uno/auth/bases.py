# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    CheckConstraint,
    ForeignKey,
    UniqueConstraint,
    Identity,
    text,
    Table,
    Column,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    ENUM,
    VARCHAR,
    BIGINT,
)

from uno.db import UnoBase, str_26, str_255, str_63
from uno.mixins import BaseMixin
from uno.auth.mixins import RecordAuditBaseMixin
from uno.enums import SQLOperation, TenantType
from uno.config import settings

user__group = Table(
    "user__group",
    UnoBase.metadata,
    Column(
        "user_id",
        VARCHAR(26),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "GROUPS"},
    ),
    Column(
        "group_id",
        VARCHAR(26),
        ForeignKey("group.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "USERS"},
    ),
    Index(
        "ix_user_group_user_id_group_id",
        "user_id",
        "group_id",
    ),
)


user__role = Table(
    "user__role",
    UnoBase.metadata,
    Column(
        "user_id",
        VARCHAR(26),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "ROLES"},
    ),
    Column(
        "role_id",
        VARCHAR(26),
        ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "USERS"},
    ),
    Index(
        "ix_user_role_user_id_role_id",
        "user_id",
        "role_id",
    ),
)


role__permission = Table(
    "role__permission",
    UnoBase.metadata,
    Column(
        "role_id",
        VARCHAR(26),
        ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "PERMISSIONS"},
    ),
    Column(
        "permission_id",
        BIGINT,
        ForeignKey("permission.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "ROLES"},
    ),
    Index(
        "ix_role_permission_role_id_permission_id",
        "role_id",
        "permission_id",
    ),
)


class UserBase(BaseMixin, RecordAuditBaseMixin, UnoBase):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            """
                is_superuser = 'false' AND default_group_id IS NOT NULL OR 
                is_superuser = 'true' AND default_group_id IS NULL
                --is_superuser = 'false' AND is_tenant_admin = 'false' OR
                --is_superuser = 'true' AND is_tenant_admin = 'false' OR
                --is_superuser = 'false' AND is_tenant_admin = 'true'
            """,
            name="ck_user_is_superuser",
        ),
        {"comment": "Application users"},
    )

    # Columns
    email: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
        doc="Email address, used as login ID",
    )
    handle: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
        doc="User's displayed name and alternate login ID",
    )
    full_name: Mapped[str_255] = mapped_column(
        nullable=False,
        doc="User's full name",
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        doc="The Tenant to which the user is assigned",
        info={
            "edge": "TENANT",
            "reverse_edge": "USERS",
        },
    )
    default_group_id: Mapped[str_26] = mapped_column(
        ForeignKey("group.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User's default group, used as default for creating new objects",
        info={
            "edge": "DEFAULT_GROUP",
            "reverse_edge": "DEFAULT_GROUP_USERS",
        },
    )
    is_superuser: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the user is a Superuser",
    )

    # Relationships
    tenant: Mapped["TenantBase"] = relationship(
        foreign_keys=[tenant_id],
        doc="Tenant to which the user is assigned",
    )
    default_group: Mapped["GroupBase"] = relationship(
        foreign_keys=[default_group_id],
        doc="User's default group, used as default for creating new objects",
    )
    groups: Mapped[list["GroupBase"]] = relationship(
        secondary=user__group,
        back_populates="users",
        doc="Groups to which the user is assigned",
    )
    roles: Mapped[list["RoleBase"]] = relationship(
        secondary=user__role,
        back_populates="users",
        doc="Roles assigned to the user",
    )


class GroupBase(BaseMixin, UnoBase, RecordAuditBaseMixin):
    __tablename__ = "group"
    __table_args__ = (
        Index("ix_group_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": "Application end-user groups",
        },
    )

    # Columns
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The Tenant that owns the group",
        info={
            "edge": "TENANT",
            "reverse_edge": "GROUPS",
        },
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")

    # Relationships
    tenant: Mapped[list["TenantBase"]] = relationship(
        viewonly=True,
        doc="Customer to which the group belongs",
    )
    default_group_users: Mapped[list[UserBase]] = relationship(
        viewonly=True,
        foreign_keys=[UserBase.default_group_id],
        doc="Users assigned to the group",
    )
    users: Mapped[list[UserBase]] = relationship(
        secondary=user__group,
        back_populates="groups",
        doc="Users assigned to the group",
    )


class ResponsibilityRoleBase(BaseMixin, UnoBase, RecordAuditBaseMixin):
    __tablename__ = "responsibility_role"
    __table_args__ = {"comment": "Application process responsibility"}

    # Columns
    name: Mapped[str_255] = mapped_column(
        index=True,
        nullable=False,
    )
    description: Mapped[str_255] = mapped_column(
        nullable=False,
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The Tenant that owns the group",
        info={
            "edge": "TENANT",
            "reverse_edge": "GROUPS",
        },
    )
    # Relationships
    tenant: Mapped[list["TenantBase"]] = relationship(
        viewonly=True,
        doc="Customer to which the group belongs",
    )


class RoleBase(BaseMixin, UnoBase, RecordAuditBaseMixin):
    __tablename__ = "role"
    __table_args__ = (
        Index("ix_role_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {"comment": "Application roles"},
    )

    # Columns
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The Tenant that owns the role",
        info={
            "edge": "TENANT",
            "reverse_edge": "ROLES",
        },
    )
    name: Mapped[str_255] = mapped_column(
        index=True,
        nullable=False,
        doc="Role name",
    )
    description: Mapped[str_255] = mapped_column(
        nullable=False,
        doc="Role description",
    )
    responsibility_role_id: Mapped[str_26] = mapped_column(
        ForeignKey("responsibility_role.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The Responsibility that the role's assigned user performs",
        info={
            "edge": "RESPONSIBILITY_ROLE",
            "reverse_edge": "RESPONSIBLITY_ROLES",
        },
    )

    # Relationships
    tenant: Mapped[list["TenantBase"]] = relationship(
        viewonly=True,
        doc="Customer to which the role belongs",
    )
    permissions: Mapped[list["PermissionBase"]] = relationship(
        viewonly=True,
        secondary=role__permission,
        doc="Permissions assigned to the role",
    )
    users: Mapped[list[UserBase]] = relationship(
        secondary=user__role,
        back_populates="roles",
        doc="Users assigned to the role",
    )
    responsibility: Mapped["ResponsibilityRoleBase"] = relationship(
        doc="The Responsibility that the role's assigned user performs",
    )


class TenantBase(BaseMixin, UnoBase, RecordAuditBaseMixin):
    __tablename__ = "tenant"
    __table_args__ = (
        Index("ix_tenant_name", "name"),
        UniqueConstraint("name"),
        {"comment": "Application tenants"},
    )

    # Columns
    name: Mapped[str_255] = mapped_column(
        index=True,
        nullable=False,
        doc="Role name",
    )
    tenant_type: Mapped[TenantType] = mapped_column(
        ENUM(
            TenantType,
            name="tenanttype",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        server_default=TenantType.INDIVIDUAL.name,
        nullable=False,
        doc="Tenant type",
    )

    # Relationships
    users: Mapped[list[UserBase]] = relationship(
        viewonly=True,
        foreign_keys=[UserBase.tenant_id],
        doc="Users assigned to the tenant",
    )
    groups: Mapped[list[GroupBase]] = relationship(
        viewonly=True,
        foreign_keys=[GroupBase.tenant_id],
        doc="Groups assigned to the tenant",
    )
    roles: Mapped[list[RoleBase]] = relationship(
        viewonly=True,
        foreign_keys=[RoleBase.tenant_id],
        doc="Roles assigned to the tenant",
    )


class PermissionBase(UnoBase):
    __tablename__ = "permission"
    __table_args__ = (
        Index("ix_permission_meta_type_id_operation", "meta_type_id", "operation"),
        UniqueConstraint("meta_type_id", "operation"),
        {"comment": "Application permissions"},
    )

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(start=1, cycle=True),
        primary_key=True,
        index=True,
        nullable=False,
        doc="Primary Key",
    )
    meta_type_id: Mapped[str_63] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Foreign Key to MetaRecord Type",
        info={
            "edge": "META_TYPE",
            "reverse_edge": "PERMISSIONS",
        },
    )
    operation: Mapped[SQLOperation] = mapped_column(
        ENUM(
            SQLOperation,
            name="sqloperation",
            create_type=True,
        ),
        doc="sql.SQL Operation",
    )
