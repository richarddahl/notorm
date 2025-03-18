# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import ClassVar

from psycopg.sql import SQL, Identifier, Literal
from pydantic import BaseModel, computed_field
from sqlalchemy.sql import text
from sqlalchemy.engine import Connection

from uno.db.sql.sql_emitter import SQLEmitter, ADMIN_ROLE
from uno.utilities import convert_snake_to_camel, convert_snake_to_all_caps_snake


class TableGraphSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = [
        "table_name",
        "model",
        "node_label",
        "table",
        "column_name",
        "label",
        "remote_node_label",
        "remote_column_name",
        "local_node_label",
    ]
    column_name: str
    label: str
    remote_node_label: str
    remote_column_name: str
    local_node_label: str = None

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


class NodeSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = [
        "table_name",
        "table_node_label",
        "model",
        "graph_edges",
        "graph_nodes",
        "update_edges",
        "table",
    ]

    @computed_field
    def table_node_label(self) -> str:
        """Return the node label for the model, excluded from the SQL"""
        return convert_snake_to_camel(self.table_name)

    @computed_field
    def create_graph(self) -> str:
        """Generate SQL to create a graph structure in the database.

        This method produces a SQL statement that creates both node and edge labels
        for a graph structure. The generated SQL is wrapped in a DO block that
        executes with admin role privileges.

        Returns:
            str: A SQL statement for creating the graph structure with node and edge labels.
        """
        return textwrap.dedent(
            SQL(
                """
            DO $$
            BEGIN
                SET ROLE {admin_role};
                {edge_labels}
                {node_labels}
            END $$;

            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                edge_labels=SQL(self.create_edge_labels()),
                node_labels=SQL(self.create_node_labels()),
            )
            .as_string()
        )

    # Node related fields and methods
    @computed_field
    def graph_nodes(self) -> str:
        """Generate SQL statements for inserting nodes into the graph database.

        This method creates a dictionary mapping node labels to their corresponding INSERT SQL
        statements. It begins by adding an SQL statement for the primary node label (the table), then
        analyzes the table's columns to generate additional node insertion statements.

        During processing, it:
        - Skips columns found in the model's filter_excludes list
        - Ignores columns that represent foreign keys
        - Converts snake_case column names to CamelCase for node labels

        Returns:
            dict: A dictionary where keys are node labels and values are SQL statements
                  for inserting those nodes into the graph database.
        """
        nodes = {}
        nodes.update(
            {
                self.table_node_label: {
                    "column_name": "id",
                    "label": self.table_node_label,
                    "sql": self.create_node_label_sql(label=self.table_node_label),
                }
            }
        )
        for column_name, column in self.model.base.__table__.columns.items():
            if column_name in self.model.filter_excludes:
                continue
            if column.foreign_keys:
                continue
            label = convert_snake_to_camel(column_name)
            if label is not None:
                nodes.update({label: {"column_name": column_name, "label": label}})
        return nodes

    def create_node_labels(self) -> str:
        return "\n".join(
            [
                self.create_node_label_sql(node_label)
                for node_label in self.graph_nodes.keys()
            ]
        )

    def create_node_label_sql(self, label: str = None) -> str:
        """Generates SQL to create a vertex label (node) in the graph if it doesn't already exist.

        This method generates PostgreSQL/AGE compatible SQL that checks if a vertex label exists
        in the graph database and creates it if it doesn't. It also creates an index on the 'id'
        column of the vertex label for improved query performance.

        Args:
            label (str, optional): The name of the vertex label to create. Defaults to None.

        Returns:
            str: SQL statement string to create the vertex label, or an empty string if label is None.

        """

        return (
            SQL(
                """
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {label});
                    EXECUTE format('CREATE INDEX ON graph.{label_ident} (id);');
                END IF;
            """
            )
            .format(
                label=Literal(label),
                label_ident=Identifier(label),
            )
            .as_string()
        )

    def insert_node_sql(self, label: str, val: str) -> str:
        return (
            SQL(
                """
                IF NEW.{val} IS NOT NULL THEN
                    cypher_query := FORMAT('
                        CREATE (v:{label} {{id: %s, val: %s}})
                    ', quote_nullable(NEW.id), quote_nullable(NEW.{val})
                    );
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                END IF; 
            """
            )
            .format(label=SQL(label), val=SQL(val))
            .as_string()
        )

    def update_node_sql(self, label: str, val: str) -> str:
        return (
            SQL(
                """
                IF OLD.{val} != NEW.{val} THEN
                    -- Construct the Cypher query dynamically
                    cypher_query := FORMAT('
                        MATCH (v:{label} {{id: %s}})
                        SET v.val = %s
                    ', quote_nullable(OLD.id), quote_nullable(NEW.{val}));
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                END IF;
            """
            )
            .format(label=SQL(label), val=SQL(val))
            .as_string()
        )

    # Edge related fields and methods
    @computed_field
    def graph_edges(self) -> str:
        """
        Generates SQL statements for inserting edges based on the model's relationships and columns.

        This method processes the relationships and columns of the model to create SQL statements
        for inserting edges into the database. It handles both relationships defined in the model
        and columns that are not foreign keys or excluded by filters.

        Returns:
            str: A dictionary where the keys are edge labels and the values are the corresponding
             SQL insert statements.
        """
        edges = {}
        for relationship in self.model.relationships():
            if not relationship.info.get("edge"):
                continue
            if relationship.secondary is not None:
                continue
            column_name = relationship.info.get("column")
            label = relationship.info.get("edge")
            remote_node_label = convert_snake_to_camel(
                relationship.mapper.class_.__tablename__
            )
            remote_column_name = relationship.info.get("remote_column")
            edges.update(
                {
                    label: {
                        "column_name": column_name,
                        "label": label,
                        "remote_column_name": remote_column_name,
                        "remote_node_label": remote_node_label,
                    }
                }
            )
        for column_name, column in self.model.base.__table__.columns.items():
            if column_name in self.model.filter_excludes:
                continue
            if column.foreign_keys:
                continue
            label = convert_snake_to_all_caps_snake(column_name)
            edges.update(
                {
                    label: {
                        "column_name": "id",
                        "label": label,
                        "remote_column_name": "id",
                        "remote_node_label": convert_snake_to_camel(column_name),
                    }
                }
            )
        return edges

    def create_edge_labels(self) -> str:
        return "\n".join(
            [
                self.create_edge_label_sql(edge_label)
                for edge_label in self.graph_edges.keys()
            ]
        )

    def create_edge_label_sql(self, label: str) -> str:
        return (
            SQL(
                """
                IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_elabel('graph', {label});
                    CREATE INDEX ON graph.{label_ident} (start_id, end_id);
                END IF;
                """
            )
            .format(
                label=Literal(label),
                label_ident=Identifier(label),
            )
            .as_string()
        )

    def insert_edge_sql(
        self,
        column_name: str,
        label: str,
        remote_column_name: str,
        remote_node_label: str,
        local_node_label: str = None,
    ) -> str:
        return (
            SQL(
                """
                IF NEW.{column_name} IS NOT NULL THEN
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{id: %s}})
                            CREATE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(NEW.{column_name}),
                        quote_nullable(NEW.{remote_column_name})
                    );
                END IF;
            """
            )
            .format(
                node_label=(
                    SQL(self.table_node_label)
                    if local_node_label is None
                    else SQL(local_node_label)
                ),
                column_name=SQL(column_name),
                label=SQL(label),
                remote_node_label=SQL(remote_node_label),
                remote_column_name=SQL(remote_column_name),
            )
            .as_string()
        )

    def update_edge_sql(
        self,
        column_name: str,
        label: str,
        remote_column_name: str,
        remote_node_label: str,
        local_node_label: str = None,
    ) -> str:
        return (
            SQL(
                """
                IF OLD.{remote_column_name} != NEW.{remote_column_name} THEN
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{id: %s}})
                            DELETE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(OLD.{column_name}),
                        quote_nullable(OLD.{remote_column_name})
                    ); 
                END IF;

                EXECUTE FORMAT('
                    SELECT * FROM cypher(''graph'', $$
                        MATCH (l:{node_label} {{id: %s}})
                        MATCH (r:{remote_node_label} {{id: %s}})
                        CREATE (l)-[e:{label}]->(r)
                    $$) AS (result agtype)',
                    quote_nullable(NEW.{column_name}),
                    quote_nullable(NEW.{remote_column_name})
                ); 
            """
            )
            .format(
                node_label=(
                    SQL(self.table_node_label)
                    if local_node_label is None
                    else SQL(local_node_label)
                ),
                column_name=SQL(column_name),
                label=SQL(label),
                remote_node_label=SQL(remote_node_label),
                remote_column_name=SQL(remote_column_name),
            )
            .as_string()
        )

    @computed_field
    def insert_graph(self) -> str:
        function_string = textwrap.dedent(
            SQL(
                """
            DECLARE
                cypher_query text;
            BEGIN
                SET ROLE {admin_role};
                -- Execute the Cypher query to insert the nodes
                {nodes}
                -- Execute the Cypher queries to insert the edges
                {edges}
                RETURN NEW;
            END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                nodes=SQL(
                    "".join(
                        [
                            self.insert_node_sql(node_label, node["column_name"])
                            for node_label, node in self.graph_nodes.items()
                        ]
                    ),
                ),
                edges=SQL(
                    "".join(
                        [
                            self.insert_edge_sql(
                                edge["column_name"],
                                edge["label"],
                                edge["remote_column_name"],
                                edge["remote_node_label"],
                            )
                            for edge_label, edge in self.graph_edges.items()
                        ]
                    ),
                ),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_graph",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def update_graph(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                cypher_query text;
            BEGIN
                SET ROLE {admin_role};
                -- Execute the Cypher query to insert the nodes
                {nodes}
                -- Execute the Cypher queries to insert the edges
                {edges}
                RETURN NEW;
            END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                nodes=SQL(
                    "".join(
                        [
                            self.update_node_sql(node_label, node["column_name"])
                            for node_label, node in self.graph_nodes.items()
                        ]
                    ),
                ),
                edges=SQL(
                    "".join(
                        [
                            self.update_edge_sql(
                                edge["column_name"],
                                edge["label"],
                                edge["remote_column_name"],
                                edge["remote_node_label"],
                            )
                            for edge_label, edge in self.graph_edges.items()
                        ]
                    ),
                ),
            )
            .as_string()
        )

        return self.create_sql_function(
            "update_graph",
            function_string,
            operation="UPDATE",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def delete_graph(self) -> str:
        function_string = (
            SQL(
                """
                BEGIN
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        MATCH (v:{node_label} {{id: %s}})
                        DELETE v
                    $graph$) AS (e agtype);, OLD.id);');

                    RETURN OLD;
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                node_label=SQL(self.table_node_label),
            )
            .as_string()
        )

        return self.create_sql_function(
            "delete_graph",
            function_string,
            timing="AFTER",
            operation="DELETE",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def truncate_graph(self) -> str:
        function_string = (
            SQL(
                """
                BEGIN
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        MATCH (v:{node_label})
                        DELETE v
                    $graph$) AS (e agtype);');
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                node_label=SQL(self.table_node_label),
            )
            .as_string()
        )

        return self.create_sql_function(
            "truncate_graph",
            function_string,
            operation="TRUNCATE",
            timing="BEFORE",
            include_trigger=True,
            for_each="STATEMENT",
            db_function=False,
        )
