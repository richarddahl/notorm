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

from uno.model import UnoModel, PostgresTypes
from uno.mixins import ModelMixin
from uno.authorization.mixins import RecordAuditModelMixin
from uno.enums import SQLOperation, TenantType
from uno.settings import uno_settings

user__group = Table(
    "user__group",
    UnoModel.metadata,
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
    UnoModel.metadata,
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
    UnoModel.metadata,
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


class UserModel(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            """
                is_superuser = 'false' AND default_group_id IS NOT NULL OR 
                is_superuser = 'true' AND default_group_id IS NULL
            """,
            name="ck_user_is_superuser",
        ),
        UniqueConstraint("handle", "tenant_id", name="uq_user_handle_tenant_id"),
        {"comment": "Application users"},
    )

    # Columns
    email: Mapped[PostgresTypes.String255] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
        doc="Email address, used as login ID",
    )
    handle: Mapped[PostgresTypes.String255] = mapped_column(
        index=True,
        nullable=False,
        doc="User's displayed name and alternate login ID",
    )
    full_name: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        doc="User's full name",
    )
    tenant_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        doc="The Tenant to which the user is assigned",
        info={
            "edge": "TENANT",
            "reverse_edge": "USERS",
        },
    )
    default_group_id: Mapped[PostgresTypes.String26] = mapped_column(
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
    tenant: Mapped["TenantModel"] = relationship(
        foreign_keys=[tenant_id],
        doc="Tenant to which the user is assigned",
    )
    default_group: Mapped["GroupModel"] = relationship(
        foreign_keys=[default_group_id],
        doc="User's default group, used as default for creating new objects",
    )
    groups: Mapped[list["GroupModel"]] = relationship(
        secondary=user__group,
        back_populates="users",
        doc="Groups to which the user is assigned",
    )
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary=user__role,
        back_populates="users",
        doc="Roles assigned to the user",
    )
    messages: Mapped[list["MessageUserModel"]] = relationship(
        back_populates="user",
        doc="Messages associated with the user",
    )

    def __str__(self) -> str:
        return self.email


class GroupModel(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "group"
    __table_args__ = (
        Index("ix_group_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": "Application end-user groups",
        },
    )

    # Columns
    tenant_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The Tenant that owns the group",
        info={
            "edge": "TENANT",
            "reverse_edge": "GROUPS",
        },
    )
    name: Mapped[PostgresTypes.String255] = mapped_column(doc="Group name")

    # Relationships
    tenant: Mapped[list["TenantModel"]] = relationship(
        viewonly=True,
        doc="Customer to which the group belongs",
    )
    default_group_users: Mapped[list[UserModel]] = relationship(
        viewonly=True,
        foreign_keys=[UserModel.default_group_id],
        doc="Users assigned to the group",
    )
    users: Mapped[list[UserModel]] = relationship(
        secondary=user__group,
        back_populates="groups",
        doc="Users assigned to the group",
    )


class ResponsibilityRoleModel(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "responsibility_role"
    __table_args__ = {"comment": "Application process responsibility"}

    # Columns
    name: Mapped[PostgresTypes.String255] = mapped_column(
        index=True,
        nullable=False,
    )
    description: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
    )
    tenant_id: Mapped[PostgresTypes.String26] = mapped_column(
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
    tenant: Mapped[list["TenantModel"]] = relationship(
        viewonly=True,
        doc="Customer to which the group belongs",
    )


class RoleModel(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "role"
    __table_args__ = (
        Index("ix_role_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {"comment": "Application roles"},
    )

    # Columns
    tenant_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The Tenant that owns the role",
        info={
            "edge": "TENANT",
            "reverse_edge": "ROLES",
        },
    )
    name: Mapped[PostgresTypes.String255] = mapped_column(
        index=True,
        nullable=False,
        doc="Role name",
    )
    description: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        doc="Role description",
    )
    responsibility_role_id: Mapped[PostgresTypes.String26] = mapped_column(
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
    tenant: Mapped[list["TenantModel"]] = relationship(
        viewonly=True,
        doc="Customer to which the role belongs",
    )
    permissions: Mapped[list["PermissionModel"]] = relationship(
        viewonly=True,
        secondary=role__permission,
        doc="Permissions assigned to the role",
    )
    users: Mapped[list[UserModel]] = relationship(
        secondary=user__role,
        back_populates="roles",
        doc="Users assigned to the role",
    )
    responsibility: Mapped["ResponsibilityRoleModel"] = relationship(
        doc="The Responsibility that the role's assigned user performs",
    )


class TenantModel(ModelMixin, UnoModel, RecordAuditModelMixin):
    __tablename__ = "tenant"
    __table_args__ = (
        Index("ix_tenant_name", "name"),
        UniqueConstraint("name"),
        {"comment": "Application tenants"},
    )

    # Columns
    name: Mapped[PostgresTypes.String255] = mapped_column(
        index=True,
        nullable=False,
        doc="Role name",
    )
    tenant_type: Mapped[TenantType] = mapped_column(
        ENUM(
            TenantType,
            name="tenanttype",
            create_type=True,
            schema=uno_settings.DB_SCHEMA,
        ),
        server_default=TenantType.INDIVIDUAL.name,
        nullable=False,
        doc="Tenant type",
    )

    # Relationships
    users: Mapped[list[UserModel]] = relationship(
        viewonly=True,
        foreign_keys=[UserModel.tenant_id],
        doc="Users assigned to the tenant",
    )
    groups: Mapped[list[GroupModel]] = relationship(
        viewonly=True,
        foreign_keys=[GroupModel.tenant_id],
        doc="Groups assigned to the tenant",
    )
    roles: Mapped[list[RoleModel]] = relationship(
        viewonly=True,
        foreign_keys=[RoleModel.tenant_id],
        doc="Roles assigned to the tenant",
    )


class PermissionModel(UnoModel):
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
    meta_type_id: Mapped[PostgresTypes.String63] = mapped_column(
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
