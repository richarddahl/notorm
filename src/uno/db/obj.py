# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar, Any

from sqlalchemy import MetaData, Table
from sqlalchemy.engine import Connection

from pydantic import BaseModel, ConfigDict

from uno.db.sql.sql_emitter import SQLEmitter
from uno.db.sql.table_sql_emitters import AlterGrants
from uno.db.graph import GraphEdge
from uno.db.sql.table_sql_emitters import InsertMetaTypeRecord
from uno.db.graph import GraphNode
from uno.db.db import UnoDB
from uno.errors import UnoRegistryError
from uno.utilities import convert_snake_to_title
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
    table_name: str
    meta_data: MetaData
    args: list[Any] = []
    kwargs: dict[str, Any] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UnoObj(BaseModel):
    """Base class for all database tables"""

    table_def: ClassVar[UnoTableDef]
    table: ClassVar[Table]

    db: ClassVar[UnoDB] = None
    table_name: ClassVar[str] = ""

    include_in_api_docs: ClassVar[bool] = True

    registry: ClassVar[dict[str, "UnoObj"]] = {}
    class_name_map: ClassVar[dict[str, str]] = {}

    display_name: ClassVar[str] = None
    display_name_plural: ClassVar[str] = None

    related_objects: ClassVar[dict[str, BaseModel]] = {}

    # SQL attributes
    sql_emitters: ClassVar[list[SQLEmitter]] = [
        AlterGrants,
        InsertMetaTypeRecord,
    ]

    # Graph attributes
    graph_node: ClassVar[GraphNode] = None
    graph_edges: ClassVar[dict[str, GraphEdge]] = {}
    exclude_from_properties: ClassVar[list[str]] = []
    filters: ClassVar[dict[str, dict[str, str]]] = {}

    # schema attributes
    schema_defs: ClassVar[list[BaseModel]] = []
    insert_schema: ClassVar[BaseModel] = None
    list_schema: ClassVar[BaseModel] = None
    select_schema: ClassVar[BaseModel] = None
    update_schema: ClassVar[BaseModel] = None
    delete_schema: ClassVar[BaseModel] = None
    import_schema: ClassVar[BaseModel] = None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        # Don't add the UnoObj class to the registry
        if cls is UnoObj:
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

        from uno.app.app import app

        cls.app = app

        # Create the table
        cls.table = Table(
            cls.table_def.table_name,
            cls.table_def.meta_data,
            *cls.table_def.args,
            **cls.table_def.kwargs,
        )

        # Initialize the uno_db
        cls.db = UnoDB(obj_class=cls)

        cls.display_name = (
            convert_snake_to_title(cls.table.name)
            if cls.display_name is None
            else cls.display_name
        )
        cls.display_name_plural = (
            f"{convert_snake_to_title(cls.table.name)}s"
            if cls.display_name_plural is None
            else cls.display_name_plural
        )

        # Add the subclass to the model_name_registry if it is not there (shouldn't be there, but just in case)
        if cls.__name__ not in cls.class_name_map:
            cls.class_name_map.update({cls.__name__: cls})
        else:
            raise UnoRegistryError(
                f"A class with the table name {cls.table_name} already exists.",
                "MODEL_NAME_EXISTS_IN_REGISTRY",
            )
        # Add the subclass to the table_name_registry
        if cls.table.name not in cls.registry:
            cls.registry.update({cls.table.name: cls})
        else:
            # Raise an error if a class with the same table name already exists in the registry
            raise UnoRegistryError(
                f"A class with the table name {cls.table.name} already exists.",
                "TABLE_NAME_EXISTS_IN_REGISTRY",
            )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.configure_related_objects()

    @classmethod
    def create_schemas(cls) -> None:
        for schema_def in cls.schema_defs:
            schema_def.create_schema(cls, cls.app)

    @classmethod
    def configure_obj(cls) -> None:
        cls.create_schemas()
        cls.set_graph()
        cls.set_fields()

    def configure_related_objects(self) -> None:
        for name, rel_obj in self.related_objects.items():
            edge = GraphEdge(
                obj_class=self,
                source_table=self.table.name,
                source_column=rel_obj.column,
                destination_column=rel_obj.remote_column,
                label=rel_obj.edge_label,
            )
            self.graph_edges.update({name: edge})
            with self.db.sync_connection() as conn:
                edge._emit_sql(conn)
                conn.commit()
                conn.close()

    @classmethod
    def set_graph(cls) -> None:
        cls.graph_node = GraphNode(obj_class=cls)
        with cls.db.sync_connection() as conn:
            cls.graph_node._emit_sql(conn)
            conn.commit()
            conn.close()
        cls.set_edges()

    @classmethod
    def set_edges(cls) -> None:
        cls.graph_edges = {}
        if not cls.graph_node:
            return
        # for rel in cls.relationships():
        #    if not rel.mapper.class_.graph_node:
        #        continue
        #    edge = EdgeSQLEmitter(
        #        obj_class=cls,
        #        destination_meta_type=rel.mapper.class_.table.name,
        #        label=rel.info.get("edge"),
        #        secondary=rel.secondary,
        #        accessor=rel.key,
        #    )
        #    cls.graph_edges[rel.key] = edge

    @classmethod
    def set_filters(cls) -> None:
        cls.filters = {}
        if not cls.graph_node:
            return
        for property in cls.graph_properties:
            cls.filters[property.display] = {
                "data_type": property.data_type,
                "name": property.name,
                # "accessor": property.accessor,
                "lookups": property.lookups,
            }
        for edge in cls.graph_edges:
            cls.filters[edge.display] = {
                # "table_name": edge.table_name,
                # "filter_type": "EDGE",
                "data_type": "record",
                "name": edge.name,
                # "destination_table_name": edge.destination_table_name,
                # "accessor": edge.accessor,
                "lookups": edge.lookups,
            }

    @classmethod
    def set_fields(cls) -> None:
        pass

    @classmethod
    def _emit_sql(cls, conn: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(obj_class=cls)._emit_sql(conn)

    def save(self) -> None:
        schema = self.insert_schema(**self.model_dump())
        self.db.insert(schema)

    # DB methods
    @classmethod
    def select(cls, id: str) -> bool | None:
        return cls.db.select(id)

    @classmethod
    def sync_select(cls, id: str) -> bool | None:
        return cls.db.sync_select(id)
