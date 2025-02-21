# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional, ClassVar, Any

from psycopg.sql import SQL

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    Identity,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    declared_attr,
)
from sqlalchemy.dialects.postgresql import ENUM, ARRAY

from uno.db.base import Base, str_26, str_255
from uno.db.tables import (
    MetaRecord,
    MetaType,
    MetaObjectMixin,
    RecordAuditMixin,
    RecordVersionAuditMixin,
    HistoryTableAuditMixin,
)
from uno.db.enums import SQLOperation
from uno.db.sql.sql_emitter import SQLEmitter

from uno.auth.sql_emitters import (
    ValidateGroupInsert,
    InsertGroupForTenant,
    DefaultGroupTenant,
    UserRecordAuditFunction,
)

# from uno.auth.rls_sql_emitters import (
#    RowLevelSecurity,
#    UserRowLevelSecurity,
#    TenantRowLevelSecurity,
# )
from uno.msg.tables import Message, MessageAddressedTo, MessageCopiedTo
from uno.auth.enums import TenantType
from uno.auth.schemas import (
    user_schema_defs,
    tenant_schema_defs,
    group_schema_defs,
    role_schema_defs,
)

from uno.config import settings


class UserRecordAuditMixin:
    """Mixin for auditing actions on records

    Documents both the timestamps of when and user ids  of who created,
    modified, and deleted a record

    """

    sql_emitters: ClassVar[list[SQLEmitter]] = [UserRecordAuditFunction]

    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates if the record is active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates if the record has been deleted",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was created",
    )

    @declared_attr
    def created_by_id(cls) -> Mapped[Optional[str_26]]:
        return mapped_column(
            ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
            index=True,
        )

    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
    )

    @declared_attr
    def modified_by_id(cls) -> Mapped[Optional[str_26]]:
        return mapped_column(
            ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
            index=True,
        )

    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
    )

    @declared_attr
    def deleted_by_id(cls) -> Mapped[Optional[str_26]]:
        return mapped_column(
            ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
            index=True,
        )


class UserGroupRole(Base):
    __tablename__ = "user__group__role"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The relationship between users, groups, and roles.",
        },
    )
    display_name: ClassVar[str] = "User Group Role"
    display_name_plural: ClassVar[str] = "User Group Roles"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    include_in_graph = False

    # Columns
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.group.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.role.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Tenant(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
):
    __tablename__ = "tenant"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Application end-user tenants",
        },
    )
    display_name: ClassVar[str] = "Tenant"
    display_name_plural: ClassVar[str] = "Tenants"

    sql_emitters: ClassVar[list[SQLEmitter]] = [InsertGroupForTenant]

    schema_defs = tenant_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
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
        info={"edge": "BELONGS_TO"},
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="tenant",
        foreign_keys="Group.tenant_id",
        doc="Groups that belong to the tenant",
        info={"edge": "BELONGS_TO"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="tenant",
        foreign_keys="Role.tenant_id",
        doc="Roles that belong to the tenant",
        info={"edge": "BELONGS_TO"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "tenant",
        "inherit_condition": id == MetaRecord.id,
    }

    def __str__(self) -> str:
        return self.name


class User(
    MetaRecord,
    MetaObjectMixin,
    UserRecordAuditMixin,
    HistoryTableAuditMixin,
):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            SQL(
                """
                (is_superuser = 'false' AND default_group_id IS NOT NULL) OR 
                (is_superuser = 'true' AND default_group_id IS NULL)
            """
            ).as_string(),
            name="ck_user_is_superuser",
        ),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Application users",
        },
    )
    display_name: ClassVar[str] = "User"
    display_name_plural: ClassVar[str] = "Users"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    schema_defs = user_schema_defs

    exclude_from_properties = ["is_superuser"]
    graph_properties = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    email: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        doc="Email address, used as login ID",
    )
    handle: Mapped[str_255] = mapped_column(
        unique=True, index=True, doc="User's displayed name and alternate login ID"
    )
    full_name: Mapped[Optional[str_255]] = mapped_column(doc="User's full name")
    tenant_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.tenant.id", ondelete="CASCADE"),
        index=True,
        doc="Tenant to which the user belongs.",
    )
    default_group_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.group.id", ondelete="SET NULL"),
        index=True,
        doc="Default group for the user",
    )
    is_superuser: Mapped[bool] = mapped_column(
        server_default=text("false"),
        index=True,
        doc="Superuser status",
    )
    tenant: Mapped[Optional[Tenant]] = relationship(
        back_populates="users",
        foreign_keys=[tenant_id],
        doc="Tenant the user belongs to",
        info={"edge": "IS_OWNED_BY"},
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="users",
        secondary=UserGroupRole.__table__,
        foreign_keys="UserGroupRole.user_id",
        primaryjoin="and_(User.id == UserGroupRole.user_id, UserGroupRole.role_id == None)",
        secondaryjoin="and_(User.id == UserGroupRole.user_id, UserGroupRole.role_id == None)",
        doc="Groups of which the user is a member.",
        info={"edge": "IS_MEMBER_OF"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="users",
        secondary=UserGroupRole.__table__,
        foreign_keys="UserGroupRole.user_id",
        primaryjoin="and_(User.id == UserGroupRole.user_id, UserGroupRole.group_id == None)",
        secondaryjoin="and_(User.id == UserGroupRole.user_id, UserGroupRole.group_id == None)",
        doc="Roles assigned to the user",
        info={"edge": "IS_ASSIGNED"},
    )
    default_group: Mapped[Optional["Group"]] = relationship(
        back_populates="default_users",
        foreign_keys=[default_group_id],
        doc="Default group for the user.",
        info={"edge": "HAS_DEFAULT_GROUP"},
    )
    messages_sent: Mapped[list["Message"]] = relationship(
        back_populates="sender",
        foreign_keys=[Message.sender_id],
        doc="Messages sent by the user",
        info={"edge": "SENT"},
    )
    messages_recieved: Mapped[list["Message"]] = relationship(
        back_populates="addressed_to",
        secondary=MessageAddressedTo.__table__,
        doc="Messages received by the user",
        info={"edge": "RECEIVED"},
    )
    copied_messages: Mapped[list["Message"]] = relationship(
        back_populates="copied_to",
        secondary=MessageCopiedTo.__table__,
        doc="Messages copied to the user",
        info={"edge": "COPIED_ON"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "inherit_condition": id == MetaRecord.id,
    }

    def __str__(self) -> str:
        return self.email


class RolePermission(Base, RecordVersionAuditMixin):
    __tablename__ = "role__permission"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The relationship between roles and permissions.",
        },
    )
    display_name: ClassVar[str] = "Role Permission"
    display_name_plural: ClassVar[str] = "Role Permissions"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    include_in_graph = False

    # Columns
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.role.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Role ID",
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.permission.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Permission ID",
    )


class Permission(Base, RecordVersionAuditMixin):
    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint(
            "meta_type_name",
            "operation",
            name="uq_meta_type_operation",
        ),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Permissions for each table.",
        },
    )
    display_name: ClassVar[str] = "Permission"
    display_name_plural: ClassVar[str] = "Permissions"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    include_in_graph = False

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        doc="The id of the node.",
    )
    meta_type_name: Mapped[int] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        primary_key=True,
        doc="Table to which the permission provides access.",
    )
    operation: Mapped[SQLOperation] = mapped_column(
        ENUM(
            SQLOperation,
            name="sqloperation",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        primary_key=True,
        doc="Database operation that is permissible.",
    )

    # Relationships
    meta_type: Mapped[MetaType] = relationship(
        # back_populates="permissions",
        doc="Table the permission is for",
        info={"edge": "ALLOWS_ACCESS_TO"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="permissions",
        secondary=RolePermission.__table__,
        doc="Roles that have this permission",
        info={"edge": "ALLOWS_ACCESS_VIA"},
    )

    def __str__(self) -> str:
        return f"{self.meta_type.name} - {self.actions}"


class Role(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
):
    __tablename__ = "role"
    __table_args__ = (
        Index("ix_role_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": "Roles define collections of permissions necessary to accomplish businness objectives.",
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name: ClassVar[str] = "Role"
    display_name_plural: ClassVar[str] = "Roles"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    schema_defs = role_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.tenant.id", ondelete="CASCADE"),
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
        info={"edge": "BELONGS_TO"},
    )
    users: Mapped[list[User]] = relationship(
        back_populates="roles",
        secondary=UserGroupRole.__table__,
        foreign_keys="UserGroupRole.role_id",
        primaryjoin="and_(Role.id == UserGroupRole.role_id, UserGroupRole.group_id == None)",
        secondaryjoin="and_(Role.id == UserGroupRole.role_id, UserGroupRole.group_id == None)",
        doc="Users that have this role",
        info={"edge": "IS_ASSIGNED_TO"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "role",
        "inherit_condition": id == MetaRecord.id,
    }

    def __str__(self) -> str:
        return self.name


class Group(
    MetaRecord,
    MetaObjectMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
):
    __tablename__ = "group"
    __table_args__ = (
        Index("ix_group_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Application user groups",
        },
    )
    display_name: ClassVar[str] = "Group"
    display_name_plural: ClassVar[str] = "Groups"

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        ValidateGroupInsert,
        DefaultGroupTenant,
    ]
    schema_defs = group_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.tenant.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")

    # Relationships
    tenant: Mapped[Tenant] = relationship(
        back_populates="groups",
        foreign_keys="Group.tenant_id",
        doc="Tenant the group belongs to",
        info={"edge": "BELONGS_TO"},
    )
    users: Mapped[list[User]] = relationship(
        back_populates="groups",
        secondary=UserGroupRole.__table__,
        foreign_keys="UserGroupRole.group_id",
        primaryjoin="and_(Group.id == UserGroupRole.group_id, UserGroupRole.role_id == None)",
        secondaryjoin="and_(Group.id == UserGroupRole.group_id, UserGroupRole.role_id == None)",
        doc="Users that belong to the group",
        info={"edge": "IS_MEMBER_OF"},
    )
    default_users: Mapped[list[User]] = relationship(
        back_populates="default_group",
        foreign_keys="User.default_group_id",
        doc="Users that belong to the group",
        info={"edge": "HAS_DEFAULT_GROUP"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "group",
        "inherit_condition": id == MetaRecord.id,
    }

    def __str__(self) -> str:
        return self.name
