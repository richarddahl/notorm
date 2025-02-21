# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json

from typing import Any

from psycopg.sql import SQL, Identifier, Literal

from pydantic import BaseModel, ConfigDict, computed_field

from sqlalchemy import Table
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text
from sqlalchemy.types import NullType

from uno.db.sql_emitters import DB_SCHEMA, ADMIN_ROLE
from uno.val.enums import (
    Lookup,
    numeric_lookups,
    text_lookups,
    object_lookups,
    boolean_lookups,
)
from uno.config import settings
from uno.utilities import convert_snake_to_camel, convert_snake_to_title


class GraphBase(BaseModel):
    klass: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def source_meta_type(self) -> str:
        return self.klass.__tablename__

    def create_sql_trigger(
        self,
        function_name: str,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        db_function: bool = True,
    ) -> str:
        trigger_scope = (
            f"{settings.DB_SCHEMA}."
            if db_function
            else f"{settings.DB_SCHEMA}.{self.source_meta_type}_"
        )
        return (
            SQL(
                """
            CREATE OR REPLACE TRIGGER {source_meta_type}_{function_name}_trigger
                {timing} {operation}
                ON {db_schema}.{source_meta_type}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
            )
            .format(
                source_meta_type=SQL(self.source_meta_type),
                function_name=SQL(function_name),
                timing=SQL(timing),
                operation=SQL(operation),
                for_each=SQL(for_each),
                db_schema=SQL(settings.DB_SCHEMA),
                trigger_scope=SQL(trigger_scope),
            )
            .as_string()
        )

    def create_sql_function(
        self,
        function_name: str,
        function_string: str,
        function_args: str = "",
        db_function: bool = True,
        return_type: str = "TRIGGER",
        volatile: str = "VOLATILE",
        include_trigger: bool = False,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        security_definer: str = "SECURITY DEFINER",
    ) -> str:
        if function_args and include_trigger is True:
            raise ValueError(
                "Function arguments cannot be used when creating a trigger function."
            )
        full_function_name = (
            f"{settings.DB_SCHEMA}.{function_name}"
            if db_function
            else f"{settings.DB_SCHEMA}.{self.source_meta_type}_{function_name}"
        )
        fnct_string = (
            SQL(
                """
            SET ROLE {admin};
            CREATE OR REPLACE FUNCTION {full_function_name}({function_args})
            RETURNS {return_type}
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            {function_string}
            $$;
            """
            )
            .format(
                admin=ADMIN_ROLE,
                full_function_name=SQL(full_function_name),
                function_args=SQL(function_args),
                return_type=SQL(return_type),
                function_string=SQL(function_string),
            )
            .as_string()
        )

        if not include_trigger:
            return fnct_string
        trggr_string = self.create_sql_trigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return f"{SQL(fnct_string)}\n{SQL(trggr_string)}"


class GraphProperty(GraphBase):
    # klass: Any <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    accessor: str
    data_type: str
    # display: str <- computed_field
    # destination_meta_type: str <- computed_field
    # lookups: Lookup <- computed_field

    @computed_field
    def display(self) -> str:
        return convert_snake_to_title(self.accessor)

    @computed_field
    def destination_meta_type(self) -> str:
        return self.source_meta_type

    @computed_field
    def lookups(self) -> Lookup:
        if self.data_type in [
            "int",
            "Decimal",
            "datetime",
            "date",
            "time",
        ]:
            return numeric_lookups
        if self.data_type in ["str"]:
            return text_lookups
        if self.data_type in ["bool"]:
            return boolean_lookups
        return object_lookups

    def emit_sql(self, conn: Engine) -> None:
        """
        Generates a complete SQL script by combining various SQL components.

        This method constructs a SQL script by sequentially appending the results
        of several helper methods that generate specific parts of the SQL script.
        The final script includes SQL for creating labels, insert functions and
        triggers, update functions and triggers, delete functions and triggers,
        truncate functions and triggers, and filter fields.

        Returns:
            str: The complete SQL script as a single string.
        """
        conn.execute(
            text(
                SQL(
                    """
            DO $$
            BEGIN
                SET ROLE {writer_role};
                INSERT INTO {db_schema}.filter (
                    display,
                    data_type,
                    source_meta_type,
                    destination_meta_type,
                    accessor,
                    lookups
                )
                VALUES (
                    {display},
                    {data_type},
                    {source_meta_type},
                    {destination_meta_type},
                    {accessor},
                    {lookups}
                );
            END $$;
            """
                )
                .format(
                    writer_role=ADMIN_ROLE,
                    db_schema=DB_SCHEMA,
                    display=Literal(self.display),
                    data_type=Literal(self.data_type),
                    source_meta_type=Literal(self.source_meta_type),
                    destination_meta_type=Literal(self.destination_meta_type),
                    accessor=Literal(self.accessor),
                    lookups=Literal(self.lookups),
                )
                .as_string()
            )
        )


class GraphNode(GraphBase):
    # klass: Any <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    # properties: dict[str, GraphProperty] <- computed_field
    # name: str <- computed_field

    @computed_field
    def properties(self) -> dict[str, GraphProperty]:
        return self.klass.graph_properties

    @computed_field
    def name(self) -> str:
        return convert_snake_to_camel(self.source_meta_type)

    def emit_sql(self, conn: Engine) -> None:
        """
        Generates a complete SQL script by combining various SQL
        components.

        This method constructs a SQL script by sequentially appending
        the results of several helper methods that generate specific
        parts of the SQL script.
        The final script includes SQL for creating labels, insert
        functions and triggers, update functions and triggers,
        delete functions and triggers, truncate functions and
        triggers, and filter fields.

        Returns:
            str: The complete SQL script as a single string.
        """
        sql = self.create_node_label()
        # sql += f"\n{self.insert_node_sql()}"
        # sql += f"\n{self.update_nodet_sql()}"
        # sql += f"\n{self.delete_nodet_sql()}"
        # sql += f"\n{self.truncate_nodet_sql()}"
        # sql += f"\n{self.create_filter_field_sql()}"
        conn.execute(text(SQL(sql).as_string()))

    def create_node_label(self) -> str:
        query = SQL(
            """
            DO $$
            BEGIN
                SET ROLE {admin};
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label
                WHERE name = {name}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {name});
                    EXECUTE format('CREATE INDEX ON graph.{name_ident} (id);');
                END IF;
            END $$;
            """
        ).format(
            admin=ADMIN_ROLE,
            name=Literal(self.name),
            name_ident=Identifier(self.name),
        )
        return query.as_string()

    def insert_node_sql(self) -> str:
        """
        Generates SQL code to create a function and trigger for inserting a new node record
        when a new relational table record is inserted.

        The function constructs the SQL statements required to:
        - Create a new node with the specified name and properties.
        - Create edges for the node if any are defined.

        Returns:
            str: The generated SQL code for the insert function and trigger.
        """
        prop_key_str = ""
        prop_val_str = ""

        if self.properties:
            prop_key_str = ", ".join(f"{prop}: %s" for prop in self.properties.keys())
            prop_val_str = ", ".join(
                [
                    f"quote_nullable(NEW.{prop.accessor})"
                    for prop in self.properties.values()
                ]
            )

        function_string = SQL(
            """
            DECLARE 
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        CREATE (v:{self.name} {{{prop_key_str}}})
                    $graph$) AS (a agtype);', {prop_val_str});
            BEGIN
                EXECUTE _sql;
                {edge_str}
                RETURN NEW;
            END;
            """
        )

        return self.create_sql_function(
            "insert_node",
            function_string,
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )

    def update_node_sql(self) -> str:
        """
        Generates SQL code for creating an update function and trigger for a node record.

        This method constructs the SQL code necessary to update an existing node record
        in a graph database when its corresponding relational table record is updated. The
        generated SQL includes the necessary property updates and edge updates if they exist.

        Returns:
            str: The generated SQL code as a string.
        """
        prop_key_str = ""
        prop_val_str = ""
        edge_str = ""
        if self.edges:
            edge_str = "\n".join([edge.update_edge_sql() for edge in self.edges])
        if self.properties:
            prop_key_str = "SET " + ", ".join(
                f"v.{prop.accessor} = %s" for prop in self.properties
            )
            prop_val_str = ", " + ", ".join(
                [prop.data_type for prop in self.properties]
            )
        function_string = SQL(
            """
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.name} {{id: %s}})
                    {prop_key_str}
                $graph$) AS (a agtype);', quote_nullable(NEW.id){prop_val_str});
            BEGIN
                EXECUTE _sql;
                {edge_str}
                RETURN NEW;
            END;
            """
        ).format(
            prop_key_str=SQL(prop_key_str),
            prop_val_str=SQL(prop_val_str),
            edge_str=SQL(edge_str),
        )
        return self.create_sql_function(
            "update_node",
            function_string,
            include_trigger=True,
            db_function=False,
        )

    def delete_node_sql(self) -> str:
        """
        Generates SQL code for creating a function and trigger to delete a node record
        from a graph database when its corresponding relational table record is deleted.

        Returns:
            str: The SQL code for creating the delete function and trigger.
        """
        function_string = """
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.name} {{id: %s}})
                    DETACH DELETE v
                $graph$) AS (a agtype);', quote_nullable(OLD.id));
            BEGIN
                EXECUTE _sql;
                RETURN OLD;
            END;
            """
        return self.create_sql_function(
            "delete_node",
            function_string,
            operation="DELETE",
            include_trigger=True,
            db_function=False,
        )

    def truncate_node_sql(self) -> str:
        """
        Generates SQL function and trigger for truncating a relation table.

        This method creates a SQL function and trigger that deletes all corresponding
        vertices for a relation table when the table is truncated. The generated SQL
        function uses the `cypher` command to match and detach delete vertices with
        the specified name.

        Returns:
            str: The SQL string to create the function and trigger.
        """
        function_string = """
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.name})
                    DETACH DELETE v
                $graph$) AS (a agtype);');
            BEGIN
                EXECUTE _sql;
                RETURN OLD;
            END;
            """

        return self.create_sql_function(
            "truncate_node",
            function_string,
            operation="TRUNCATE",
            for_each="STATEMENT",
            include_trigger=True,
            db_function=False,
        )


class GraphEdge(GraphBase):
    label: str
    destination_meta_type: str
    accessor: str
    secondary: Table | None
    lookups: list[Lookup] = object_lookups
    # properties: dict[str, GraphProperty]
    # display: str <- computed_field
    # nullable: bool = False <- computed_field

    @computed_field
    def display(self) -> str:
        return f"{convert_snake_to_title(self.accessor)} ({convert_snake_to_title(self.destination_meta_type)})"

    @computed_field
    def source_meta_type(self) -> str:
        return self.klass.__table__.name

    @computed_field
    def properties(self) -> dict[str, GraphProperty]:
        if not isinstance(self.secondary, Table):
            return {}
        props = {}
        for column in self.secondary.columns:
            if column.foreign_keys and column.primary_key:
                continue

            if type(column.type) == NullType:
                data_type = "str"
            else:
                data_type = column.type.python_type.__name__
            from uno.db.base import Base

            for base in Base.registry.mappers:
                if base.class_.__tablename__ == self.secondary.name:
                    klass = base.class_
                    break
            props.update(
                {
                    column.name: GraphProperty(
                        klass=klass,
                        accessor=column.name,
                        data_type=data_type,
                    )
                }
            )
        return props

    def emit_sql(self, conn: Engine) -> None:
        sql = self.create_edge_label_and_filter_record_sql()
        conn.execute(text(sql))

    def create_edge_label_and_filter_record_sql(self) -> str:
        return (
            SQL(
                """
                DO $$
                BEGIN
                    SET ROLE {admin_role};
                    IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label
                        WHERE name = {label}) THEN
                            PERFORM ag_catalog.create_elabel('graph', {label});
                            CREATE INDEX ON graph.{label_ident} (start_id, end_id);
                    END IF;

                    INSERT INTO {db_schema}.filter (
                        data_type,
                        source_meta_type,
                        destination_meta_type,
                        accessor,
                        display,
                        lookups,
                        properties
                    )
                    VALUES (
                        {data_type},
                        {source_meta_type},
                        {destination_meta_type},
                        {accessor},
                        {display},
                        {lookups},
                        {properties}

                    );
                END $$;
                """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=Literal(self.label),
                label_ident=Identifier(self.label),
                db_schema=DB_SCHEMA,
                data_type=Literal("object"),
                source_meta_type=Literal(self.source_meta_type),
                destination_meta_type=Literal(self.destination_meta_type),
                display=Literal(self.display),
                accessor=Literal(self.accessor),
                lookups=Literal(self.lookups),
                properties=json.dumps(list(self.properties.keys())),
            )
            .as_string()
        )

    def insert_edge_sql(self) -> str:
        """
        Generates an SQL string to create a function and trigger for inserting
        a relationship between two vertices in a graph database.

        The generated SQL uses the `cypher` function to match the start and end
        vertices by their IDs and creates a relationship between them with the
        specified name and properties.

        Returns:
            str: The generated SQL string.
        """
        prop_key_str = ", ".join(f"{prop.accessor}: %s" for prop in self.properties)
        prop_val_str = ", ".join([prop.data_type for prop in self.properties])
        function_string = SQL(
            """
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.start_node.name} {{id: %s}})
                    MATCH (w:{self.end_node.name} {{id: %s}})
                    CREATE (v)-[e:{self.name} {{{prop_key_str}}}]->(w)
                $graph$) AS (a agtype);', quote_nullable(NEW.id), quote_nullable(NEW.id){prop_val_str});
            BEGIN
                EXECUTE _sql;
                RETURN NEW;
            END;
            """
        ).format(
            prop_key_str=SQL(prop_key_str),
            prop_val_str=SQL(prop_val_str),
        )
        return function_string

    def update_edge_sql(self) -> str:
        """
        Generates the SQL string for creating an update function and trigger in a graph database.

        This function constructs a SQL query that:
        - Matches a start node and an end node based on their labels and IDs.
        - Deletes an existing relationship between the vertices.
        - Creates a new relationship between the vertices with updated properties.

        Returns:
            str: The formatted SQL string for the update function and trigger.
        """

        prop_key_str = ""
        prop_val_str = ""
        if self.properties:
            prop_key_str = "SET " + ", ".join(
                f"v.{prop.accessor} = %s" for prop in self.properties
            )
            prop_val_str = ", " + ", ".join(
                [prop.data_type for prop in self.properties]
            )
        function_string = """
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
                DELETE o
                CREATE (v)-[e:{self.name}] ->(w)
                {prop_key_str}
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type}{prop_val_str});
            """
        return SQL(function_string)

        return SQL(
            self.create_sql_function(
                "update_edge",
                function_string,
                operation="UPDATE",
                include_trigger=True,
                db_function=False,
            )
        )

    def delete_edge_sql(self) -> str:
        """
        Generates the SQL string for creating a delete function and trigger.

        This function constructs an SQL command that uses the `cypher` function to
        delete a relationship between two vertices in a graph database. The vertices
        and the relationship are specified by the attributes of the class instance.

        Returns:
            str: The formatted SQL string for deleting the specified relationship.
        """
        function_string = """
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type});
            """
        return SQL(function_string)

        return self.create_sql_function(
            "delete_edge",
            function_string,
            operation="UPDATE",
            include_trigger=True,
            db_function=False,
        )

    def truncate_edge_sql(self) -> str:
        """
        Generates the SQL command to create a function and trigger for truncating
        relationships in a graph database.

        This method constructs a SQL string that uses the `cypher` function to
        match and delete a relationship between two vertices in a graph. The
        vertices and relationship are specified by the `start_node`,
        `end_node`, and `name` attributes of the class instance.

        Returns:
            str: The formatted SQL command string.
        """
        function_string = """
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type});
            """

        return self.create_sql_function(
            "truncate_edge",
            function_string,
            operation="UPDATE",
            include_trigger=True,
            for_each="STATEMENT",
            db_function=False,
        )
