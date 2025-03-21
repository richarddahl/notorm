# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import ClassVar

from psycopg.sql import SQL, Identifier, Literal
from pydantic import computed_field

from uno.db.sql.sql_emitter import SQLEmitter, ADMIN_ROLE
from uno.utilities import convert_snake_to_camel, convert_snake_to_all_caps_snake


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
                {node_labels}
                {edge_labels}
            END $$;

            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                node_labels=SQL(self.create_node_labels()),
                edge_labels=SQL(self.create_edge_labels()),
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
        nodes = []
        if self.model:
            table = self.model.base.__table__
            filter_excludes = self.model.filter_excludes
        else:
            table = self.table
            filter_excludes = []
        for column_name, column in table.columns.items():
            if column_name in filter_excludes:
                continue
            if column.foreign_keys:
                label = convert_snake_to_camel(
                    list(column.foreign_keys)[0].column.table.name
                )
            else:
                label = convert_snake_to_camel(column_name)
            nodes.append({"column_name": column_name, "label": label})
        return nodes

    def create_node_labels(self) -> str:
        return "\n".join(
            [self.create_node_label_sql(node["label"]) for node in self.graph_nodes]
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
                        CREATE (v:{label} {{val: %s}})
                    ', quote_nullable(NEW.{val})
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
                        MATCH (v:{label} {{val: %s}})
                        SET v.val = %s
                    ', quote_nullable(OLD.{val}), quote_nullable(NEW.{val}));
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
        edges = []
        if self.model:
            table = self.model.base.__table__
            filter_excludes = self.model.filter_excludes
        else:
            table = self.table
            filter_excludes = []
        for column_name, column in table.columns.items():
            if column_name in filter_excludes:
                continue
            if column.foreign_keys:
                if self.model:
                    # This is a column from an UnoBase class
                    local_node_label = convert_snake_to_camel(self.table_name)
                    column_name_ = list(column.foreign_keys)[0].column.name

                    label = convert_snake_to_all_caps_snake(
                        column_name.replace("_id", "")
                    )
                    remote_node_label = convert_snake_to_camel(
                        list(column.foreign_keys)[0].column.table.name
                    )
                    remote_column_name = column_name
                else:
                    # This is a column from an Association Table
                    local_node_label = convert_snake_to_camel(
                        column_name.replace("_id", "")
                    )
                    column_name_ = column_name
                    for col_name, col in table.columns.items():
                        if col_name == column_name:
                            continue
                        label = convert_snake_to_all_caps_snake(
                            col_name.replace("_id", "")
                        )
                        remote_node_label = convert_snake_to_camel(
                            list(col.foreign_keys)[0].column.table.name
                        )
                        remote_column_name = col_name
            else:
                local_node_label = convert_snake_to_camel(self.table_name)
                label = convert_snake_to_all_caps_snake(column_name.replace("_id", ""))
                remote_column_name = column_name
                remote_node_label = convert_snake_to_camel(
                    column_name.replace("_id", "")
                )
                column_name_ = "id"

            # This is a fallback for when the edge label derived from the column name is not correct
            label = column.info.get("edge_label", label)
            edges.append(
                {
                    "local_node_label": local_node_label,
                    "column_name": column_name_,
                    "label": label,
                    "remote_column_name": remote_column_name,
                    "remote_node_label": remote_node_label,
                }
            )
        return edges

    def create_edge_labels(self) -> str:
        return "\n".join(
            [self.create_edge_label_sql(edge["label"]) for edge in self.graph_edges]
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
        local_node_label: str,
        column_name: str,
        label: str,
        remote_column_name: str,
        remote_node_label: str,
    ) -> str:
        return (
            SQL(
                """
                IF NEW.{remote_column_name} IS NOT NULL THEN
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{local_node_label} {{val: %s}})
                            MATCH (r:{remote_node_label} {{val: %s}})
                            CREATE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(NEW.{column_name}),
                        quote_nullable(NEW.{remote_column_name})
                    );
                END IF;
            """
            )
            .format(
                local_node_label=(SQL(local_node_label)),
                column_name=SQL(column_name),
                label=SQL(label),
                remote_node_label=SQL(remote_node_label),
                remote_column_name=SQL(remote_column_name),
            )
            .as_string()
        )

    def update_edge_sql(
        self,
        local_node_label: str,
        column_name: str,
        label: str,
        remote_column_name: str,
        remote_node_label: str,
    ) -> str:
        return (
            SQL(
                """
                IF OLD.{remote_column_name} != NEW.{remote_column_name} THEN
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{local_node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{val: %s}})
                            DELETE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(OLD.{column_name}),
                        quote_nullable(OLD.{remote_column_name})
                    ); 
                END IF;

                EXECUTE FORMAT('
                    SELECT * FROM cypher(''graph'', $$
                        MATCH (l:{local_node_label} {{id: %s}})
                        MATCH (r:{remote_node_label} {{val: %s}})
                        CREATE (l)-[e:{label}]->(r)
                    $$) AS (result agtype)',
                    quote_nullable(NEW.{column_name}),
                    quote_nullable(NEW.{remote_column_name})
                ); 
            """
            )
            .format(
                local_node_label=(SQL(local_node_label)),
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
                            self.insert_node_sql(
                                node["label"],
                                node["column_name"],
                            )
                            for node in self.graph_nodes
                        ]
                    ),
                ),
                edges=SQL(
                    "".join(
                        [
                            self.insert_edge_sql(
                                edge["local_node_label"],
                                edge["column_name"],
                                edge["label"],
                                edge["remote_column_name"],
                                edge["remote_node_label"],
                            )
                            for edge in self.graph_edges
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
                            self.update_node_sql(
                                node["label"],
                                node["column_name"],
                            )
                            for node in self.graph_nodes
                        ]
                    ),
                ),
                edges=SQL(
                    "".join(
                        [
                            self.update_edge_sql(
                                edge["local_node_label"],
                                edge["column_name"],
                                edge["label"],
                                edge["remote_column_name"],
                                edge["remote_node_label"],
                            )
                            for edge in self.graph_edges
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
                        MATCH (v:{local_node_label} {{id: %s}})
                        DELETE v
                    $graph$) AS (e agtype);, OLD.id);');

                    RETURN OLD;
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                local_node_label=SQL(self.table_node_label),
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
                        MATCH (v:{local_node_label})
                        DELETE v
                    $graph$) AS (e agtype);');
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                local_node_label=SQL(self.table_node_label),
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
