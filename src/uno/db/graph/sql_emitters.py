# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json
import textwrap

from typing import Any, ClassVar

from psycopg.sql import SQL, Identifier, Literal

from pydantic import BaseModel, computed_field

from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from uno.db.sql.sql_emitter import (
    SQLEmitter,
    DB_SCHEMA,
    ADMIN_ROLE,
    WRITER_ROLE,
)
from uno.apps.val.enums import (
    Lookup,
    numeric_lookups,
    text_lookups,
    object_lookups,
    boolean_lookups,
)
from uno.utilities import convert_snake_to_camel


class NodeSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = ["table_name", "label"]

    @computed_field
    def label(self) -> str:
        return convert_snake_to_camel(self.table_name)

    @computed_field
    def create_node_label(self) -> str:
        return textwrap.dedent(
            SQL(
                """
            DO $$
            BEGIN
                SET ROLE {admin_role};
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label
                WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {label});
                    EXECUTE format('CREATE INDEX ON graph.{label_ident} (id);');
                END IF;
            END $$;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=Literal(self.label),
                label_ident=Identifier(self.label),
            )
            .as_string()
        )

    @computed_field
    def insert_node(self) -> str:
        function_string = (
            SQL(
                """
                DECLARE
                    cypher_query text;
                    properties hstore;
                    properties_str text;
                BEGIN
                    -- Convert the NEW record to hstore to get column names and values
                    properties := hstore(NEW);

                    -- Construct the properties string
                    properties_str := array_to_string(
                        array(SELECT FORMAT('%s: %L', key, COALESCE(value, 'NULL')) FROM EACH(properties)),', ');

                    -- Construct the Cypher query dynamically
                    cypher_query := format('CREATE (v:{label} {{%s}})', properties_str);

                    -- Execute the Cypher query
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    RETURN NEW;
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=SQL(self.label),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_node",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    def update_node(self) -> None:
        """
        Generates SQL code for creating an update function and trigger for a graph_node record.

        This method constructs the SQL code necessary to update an existing graph_node record
        in a graph database when its corresponding relational table record is updated. The
        generated SQL includes the necessary property updates and edge updates if they exist.

        Returns:
            str: The generated SQL code as a string.
        """
        prop_key_str = ""
        prop_val_str = ""
        edge_str = ""
        if self.graph_edges:
            edge_str = "\n".join([edge.update_edge_sql() for edge in self.graph_edges])
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

    def delete_node(self) -> None:
        """
        Generates SQL code for creating a function and trigger to delete a graph_node record
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

    def truncate_node(self) -> None:
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


class EdgeConfig(BaseModel):
    table_name: str
    column_name: str
    label: str
    remote_table_name: str
    remote_column_name: str
    remote_node_label: str
    secondary_table_name: str = None
    secondary_column_name: str = None
    secondary_remote_column_name: str = None

    @computed_field
    def node_label(self) -> str:
        return convert_snake_to_camel(self.table_name)

    @computed_field
    def create_edge_label(self) -> str:
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
                END $$;
                """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=Literal(self.label),
                label_ident=Identifier(self.label),
            )
            .as_string()
        )


class EdgeSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = ["table_name"]
    edge_configs: ClassVar[list[EdgeConfig]] = []

    def insert_edge_sql(self, edge_config: EdgeConfig) -> str:
        return (
            SQL(
                """
                    IF NEW.{column_name} IS NOT NULL THEN
                        EXECUTE FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{id: %s}})
                            CREATE (l)-[e:{label}]->(r)$$) AS (result agtype)',
                            quote_nullable(NEW.{column_name}),
                            quote_nullable(NEW.{remote_column_name})
                        );
                    END IF;
            """
            )
            .format(
                node_label=SQL(edge_config.node_label),
                column_name=Identifier(edge_config.column_name),
                label=SQL(edge_config.label),
                remote_node_label=SQL(edge_config.remote_node_label),
                remote_column_name=Identifier(edge_config.remote_column_name),
            )
            .as_string()
        )

    @computed_field
    def insert_edge(self) -> str:
        function_string = (
            SQL(
                """
                BEGIN

                    -- Execute the Cypher queries to insert the edges
                    SET ROLE {admin_role};
                    {edges}
                    RETURN NEW;

                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                edges=SQL(
                    "\n".join(
                        [
                            self.insert_edge_sql(
                                edge_config(table_name=self.table_name)
                            )
                            for edge_config in self.edge_configs
                        ]
                    ),
                ),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_edges",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    def old_insert_edge(self) -> str:
        function_string = (
            SQL(
                """
                DECLARE
                    cypher_query text;
                    properties hstore;
                    properties_str text;
                BEGIN
                    -- Convert the NEW record to hstore to get column names and values
                    properties := hstore(NEW);

                    -- Construct the properties string
                    properties_str := array_to_string(
                        array(SELECT FORMAT('%s: %L', key, value) FROM EACH(properties)),', ');

                    -- Construct the Cypher query dynamically
                    cypher_query := format('
                        MATCH (v:{node_label} {{id: %s}})
                        MATCH (w:{remote_node_label} {{id: %s}})
                        CREATE (v)-[e:{label} {{%s}}]->(w)',
                        quote_nullable(NEW.{column_name}),
                        quote_nullable(NEW.{remote_column_name}),
                        properties_str
                    );

                    -- Execute the Cypher query
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    RETURN NEW;
                END;
            """
            )
            .format(
                node_label=SQL(self.node_label),
                column_name=SQL(self.column_name),
                label=SQL(self.label),
                remote_node_label=SQL(self.remote_node_label),
                remote_column_name=SQL(self.remote_column_name),
                admin_role=ADMIN_ROLE,
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_edges",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    def update_edge_sql(self) -> None:
        """
        Generates the SQL string for creating an update function and trigger in a graph database.

        This function constructs a SQL query that:
        - Matches a start graph_node and an end graph_node based on their labels and IDs.
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

    def delete_edge_sql(self) -> None:
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

    def truncate_edge_sql(self) -> None:
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
