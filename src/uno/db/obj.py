# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar, Any

from sqlalchemy import MetaData, Table, Column
from sqlalchemy.sql.expression import Alias
from sqlalchemy.engine import Connection

from pydantic import BaseModel, ConfigDict, AliasGenerator

from uno.db.sql.sql_emitter import SQLEmitter
from uno.db.sql.table_sql_emitters import AlterGrants
from uno.db.graph import GraphEdge
from uno.db.sql.table_sql_emitters import InsertMetaTypeRecord
from uno.db.graph import GraphNode
from uno.db.db import UnoDB
from uno.app.endpoint import UnoEndpoint, UnoModel
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
    table_name: str
    meta_data: MetaData
    args: list[Any] = []
    kwargs: dict[str, Any] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UnoObj(BaseModel):
    """Base class for all database tables"""

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
    table_alias: ClassVar[Alias]  # Alias is a SQLAlchemy class used in joins

    db: ClassVar[UnoDB] = None
    table_name: ClassVar[str] = ""

    include_in_api_docs: ClassVar[bool] = True

    registry: ClassVar[dict[str, "UnoObj"]] = {}
    class_name_map: ClassVar[dict[str, str]] = {}

    display_name: ClassVar[str] = None
    display_name_plural: ClassVar[str] = None

    endpoints: ClassVar[list[UnoEndpoint]] = []
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
    exclude_from_properties: ClassVar[list[str]] = []
    filters: ClassVar[dict[str, dict[str, str]]] = {}

    # Resposne Model attributes
    # schema_defs: ClassVar[list[BaseModel]] = []
    import_model: ClassVar[UnoModel] = None
    view_model: ClassVar[UnoModel] = None
    edit_model: ClassVar[UnoModel] = None
    summary_model: ClassVar[UnoModel] = None

    # SETUP METHODS BEGIN
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

        # Create the table
        cls.table = Table(
            cls.table_def.table_name,
            cls.table_def.meta_data,
            *cls.table_def.args,
            **cls.table_def.kwargs,
        )
        cls.table_alias = create_random_alias(cls.table, prefix=cls.table.name)

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
        cls.db = UnoDB(obj_class=cls)

        from uno.app.app import app

        cls.app = app
        cls.set_endpoints()

    # End of __init_subclass__

    @classmethod
    def _emit_sql(cls, conn: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(obj_class=cls)._emit_sql(conn)

    @classmethod
    def configure(cls) -> None:
        """Configures the class variables that are not set during class creation
        Theses variables are set after the class is created to avoid circular
        dependencies and to allow for all UnoObj classes to be created before the
        related objects, dependent on other UnoObjs, are created.
        """

        cls.set_related_objects()

    @classmethod
    def set_endpoints(cls) -> None:
        for endpoint in cls.endpoints:
            e = endpoint(app=cls.app, obj_class=cls)
            if hasattr(e, e.response_model.modelname) is False:
                setattr(
                    cls,
                    e.response_model.modelname,
                    e.response_model,
                )
            if e.body_model and hasattr(e, e.body_model.modelname) is False:
                setattr(
                    cls,
                    e.body_model.modelname,
                    e.body_model,
                )

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

            # edge = GraphEdge(
            #    obj_class=self,
            #    source_table=self.table.name,
            #    source_column=rel_obj.column,
            #    destination_column=rel_obj.remote_column,
            #    label=rel_obj.edge_label,
            # )
            # self.graph_edges.update({name: edge})
            # with self.db.sync_connection() as conn:
            #    edge._emit_sql(conn)
            # rel_objs.update({rel_obj.local_column_name: rel_obj})
        cls.related_objects = rel_objs

    # SETUP METHODS COMPLETE

    # UTILITY METHODS BEGIN

    def refresh(self, fields: dict[str, Any]) -> None:
        field_names = self.model_fields.keys()
        for field_name in fields.keys():
            if field_name in field_names:
                setattr(self, field_name, fields[field_name])

    @classmethod
    def query_columns(cls, response_model: BaseModel) -> list[Column]:
        local_columns = []
        related_columns = []
        for column_name in response_model.model_fields.keys():
            if column_name in cls.related_objects.keys():
                rel_obj = cls.related_objects.get(column_name)
                rel_obj_class = cls.registry.get(rel_obj.remote_table_name)
                rel_obj_model = getattr(rel_obj_class, "summary_model")
                for col_name in rel_obj_model.model_fields.keys():
                    related_columns.append(
                        rel_obj.remote_table_alias.columns.get(col_name).label(
                            f"{column_name}__{col_name}"
                        )
                    )
            else:
                local_columns.append(cls.table_alias.columns.get(column_name))
        return local_columns + related_columns

    @classmethod
    def corellate_data(cls, data: dict[str:Any]) -> BaseModel:
        model_dict = {}
        for key, value in data.items():
            # Check if the key is a related object field (__ delimiter)
            if "__" in key:
                rel_name, field_name = key.split("__")
                if rel_name not in model_dict:
                    model_dict[rel_name] = {}
                model_dict[rel_name].update({field_name: value})
            else:
                model_dict.update({key: value})
        return model_dict

    @classmethod
    def construct_response_schema(cls, data) -> dict[str, BaseModel]:

        model_dict = {}
        corellated_data = cls.corellate_data(data)
        for key, val in corellated_data.items():
            # The key is a field_name and the val is either a value or a dictionary
            # If the value is a dictionary, it is a related object
            if type(val) is dict:
                # Check if the related object is empty and skip it
                # The returned value will be null
                if "id" in val and val.get("id") is None:
                    continue
                rel_obj = cls.related_objects.get(key)
                rel_obj_class = cls.registry.get(rel_obj.remote_table_name)
                rel_obj_model = rel_obj_class.summary_model
                model_dict.update({key: rel_obj_model(**val)})
            else:
                model_dict.update({key: val})
        return model_dict

    # UTILITY METHODS END

    # DB METHODS BEGIN
    @classmethod
    async def select(
        cls,
        response_model: BaseModel = None,
        id: str = None,
    ) -> BaseModel:
        if not response_model:
            response_model = getattr(cls, "view_model")
        columns = cls.query_columns(response_model)
        result = await cls.db.select(response_model, columns, id=id)
        if not id:
            results = [
                response_model(**cls.construct_response_schema(row)) for row in result
            ]
            return results
        result_model = response_model(**cls.construct_response_schema(result))
        return result_model

    async def save(self) -> BaseModel:
        if not self.id:
            body_model = self.edit_model(**self.model_dump())
            result = await self.db.insert(body_model)
        else:
            body_model = self.edit_model(**self.model_dump())
            result = await self.db.update(body_model)
        self.refresh(result)
        return self
