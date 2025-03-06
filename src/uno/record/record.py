# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT


from typing import ClassVar, Any

from sqlalchemy import MetaData, Table, Column
from sqlalchemy.sql.expression import Alias
from sqlalchemy.engine import Connection

from pydantic import BaseModel, ConfigDict, AliasGenerator

from uno.storage.sql.sql_emitter import SQLEmitter
from uno.storage.sql.table_sql_emitters import AlterGrants
from uno.storage.graph import GraphEdge
from uno.storage.sql.table_sql_emitters import InsertMetaTypeRecord
from uno.storage.graph import GraphNode

# from uno.storage.db_back import UnoDB
from uno.api.endpoint import UnoEndpoint, UnoModel
from uno.errors import UnoRegistryError
from uno.utilities import convert_snake_to_title, create_random_alias
from uno.config import settings


# configures the naming convention for the database implicit constraints and indexes
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


meta_data = MetaData(
    naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION,
    schema=settings.DB_SCHEMA,
)


class UnoTableDef(BaseModel):
    """Table definition class for UnoRecord classes.

    The UnoTableDef class is a subclass of the Pydantic BaseModel class and is
    used to define the table that corresponds to a UnoRecord class.  It enables
    the ini_subclass method of the UnoRecord class to create the table and
    add it to the database using mixins.

    The args and kwargs are simply passed through to the SQLAlchemy Table class
    when the table is created.

    """

    table_name: str
    meta_data: MetaData
    args: list[Any] = []
    kwargs: dict[str, Any] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UnoRecord(BaseModel):
    """Records are the data persistence layer of the Uno framework.

    They are the classes that represent the tables in the database.
    Each record class is a subclass of the UnoRecord class and has a corresponding table in the database.
    The UnoRecord class is a subclass of the Pydantic BaseModel class and has a
    class variable called table_def that is an instance of the UnoTableDef class.
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=None,
            serialization_alias=convert_snake_to_title,
        ),
        validate_assignment=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    table_def: ClassVar[UnoTableDef]
    table: ClassVar[Table]
    table_name: ClassVar[str] = ""
    table_alias: ClassVar[Alias]  # Alias is a SQLAlchemy class used in joins

    registry: ClassVar[dict[str, "UnoRecord"]] = {}

    related_object_defs: ClassVar[dict[str, BaseModel]] = {}
    related_objects: ClassVar[dict[str, BaseModel]] = {}

    # SQL attributes
    sql_emitters: ClassVar[list[SQLEmitter]] = [
        AlterGrants,
        InsertMetaTypeRecord,
    ]

    # Graph attributes
    graph_node: ClassVar[GraphNode] = None
    graph_edges: ClassVar[dict[str, GraphEdge]] = {}
    filters: ClassVar[dict[str, dict[str, str]]] = {}

    # SETUP METHODS BEGIN
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        # Don't add the UnoRecord class to the registry
        if cls is UnoRecord:
            return

        sql_emitters = []
        column_defs = []
        constraint_defs = []
        for kls in cls.mro():
            if hasattr(kls, "column_defs"):
                for column_def in kls.column_defs:
                    if column_def not in column_defs:
                        column_defs.append(column_def)

            if hasattr(kls, "constraint_defs"):
                for constraint_def in kls.constraint_defs:
                    if constraint_def not in constraint_defs:
                        constraint_defs.append(constraint_def)

            if hasattr(kls, "sql_emitters"):
                for sql_emitter in kls.sql_emitters:
                    if sql_emitter not in sql_emitters:
                        sql_emitters.append(sql_emitter)

        cls.column_defs = column_defs
        cls.constraint_defs = constraint_defs
        cls.table_def.args.extend(
            [column_def.create_column() for column_def in column_defs]
        )
        cls.table_def.args.extend(
            [constraint_def.create_constraint() for constraint_def in constraint_defs]
        )
        cls.sql_emitters = sql_emitters

        # Create the table
        cls.table = Table(
            cls.table_def.table_name,
            cls.table_def.meta_data,
            *cls.table_def.args,
            **cls.table_def.kwargs,
        )
        cls.table_alias = create_random_alias(cls.table, prefix=cls.table.name)

        # Add the subclass to the table_name_registry
        if cls.table.name not in cls.registry:
            cls.registry.update({cls.__name__: cls})
        else:
            # Raise an error if a class with the same table name already exists in the registry
            raise UnoRegistryError(
                f"A Record class with the name {cls.__name__} already exists in the registry.",
                "RECORD_CLASS_EXISTS_IN_REGISTRY",
            )

    # End of __init_subclass__

    @classmethod
    def _emit_sql(cls, conn: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(obj_class=cls)._emit_sql(conn)

    @classmethod
    def configure(cls, alter_db: bool = False) -> None:
        """Configures the class variables that are not set during class creation
        Theses variables are set after the class is created to avoid circular
        dependencies and to allow for all UnoRecord classes to be created before the
        related objects, dependent on other UnoObjs, are created.
        """

        cls.set_node(alter_db=alter_db)
        cls.set_related_objects()

    @classmethod
    def set_node(cls, alter_db=False) -> None:
        cls.graph_node = GraphNode(obj_class=cls)

    @classmethod
    def set_related_objects(cls) -> dict[str, BaseModel]:
        rel_objs = {}
        for rel_obj_name, rel_obJ_def in cls.related_object_defs.items():
            rel_obj = rel_obJ_def(
                obj_class_name=cls.__name__,
                local_table=cls.table,
                local_table_alias=cls.table_alias,
            )
            rel_objs.update({rel_obj_name: rel_obj})

            edge = GraphEdge(
                obj_class=cls,
                source_table=cls.table.name,
                source_column_name=rel_obj.local_column_name,
                destination_column_name=rel_obj.remote_column_name,
                label=rel_obj.edge_label,
            )
            cls.graph_edges.update({rel_obj_name: edge})
            with cls.db.sync_connection() as conn:
                edge._emit_sql(conn)
            rel_objs.update({rel_obj.local_column_name: rel_obj})
        cls.related_objects = rel_objs

    # SETUP METHODS COMPLETE
