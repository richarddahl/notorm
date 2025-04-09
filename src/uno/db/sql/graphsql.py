#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap
from typing import ClassVar, List
from typing_extensions import Self

from pydantic import BaseModel, computed_field, ConfigDict, model_validator
from pydantic_settings import BaseSettings
from sqlalchemy import Column

from uno.db.sql.classes import SQLEmitter
from uno.utilities import snake_to_camel, snake_to_caps_snake
from uno.settings import uno_settings


class ConvertProperty(SQLEmitter):
    """
    Cast the property to the correct data type for the graph database.

    The graph database may not support all the same data types as the relational database.
    For example, a timestamp in PostgreSQL is a datetime in Python, but in the graph database it is stored as text.
    """

    def convert_property_function(self) -> str:
        """
        Generate a SQL function for converting a property.

        Returns:
            str: The generated SQL function as a string.
        """
        function_body = textwrap.dedent(
            """
            IF pg_typeof(column) = 'timestamp'::pg_catalog.timestamp THEN
                RETURN EXTRACT(EPOCH FROM column)::INT::TEXT;
            END IF;
            """
        )
        return self.create_sql_function(
            "convert_property",
            function_body,
            function_args="column ",
            return_type="TEXT",
        )


class GraphSQLEmitter(SQLEmitter):
    """
    Generate SQL for creating graph labels, functions, and triggers.

    This class builds on SQLEmitter and uses internal SQL generation functions
    to handle nodes and edges in a graph database.
    """

    exclude_fields: ClassVar[List[str]] = [
        "table",
        "nodes",
        "edges",
        "config",
        "connection_config",
        "logger",
    ]
    nodes: List["Node"] = []
    edges: List["Edge"] = []

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        """
        Validate and populate nodes and edges based on table columns.

        For tables that have an "id" column, a node is created representing the table.
        Columns with foreign keys yield additional nodes and related edges.

        For association tables (no "id" column), edges are defined by nodes.
        """
        if "id" in self.table.columns:
            new_nodes = []
            # Create the main node representing the table using the "id" column.
            new_nodes.append(
                Node(
                    column=self.table.columns["id"],
                    label=snake_to_camel(self.table.name),
                    node_triggers=True,
                    target_data_type=self.table.columns["id"].type.python_type.__name__,
                )
            )
            for column in self.table.columns.values():
                if column.name == "id" or column.info.get("graph_excludes", False):
                    continue
                node_triggers = True
                if column.foreign_keys:
                    # Foreign key nodes are managed by their source table triggers.
                    label = snake_to_camel(
                        list(column.foreign_keys)[0].column.table.name
                    )
                    node_triggers = False
                else:
                    label = snake_to_camel(column.name)
                new_nodes.append(
                    Node(
                        column=column,
                        label=label,
                        node_triggers=node_triggers,
                        target_data_type=column.type.python_type.__name__,
                    )
                )
            self.nodes = new_nodes
        else:
            # For association tables, edges are defined directly from nodes.
            for column in self.table.columns.values():
                if column.foreign_keys:
                    source_node_label = snake_to_camel(column.name.replace("_id", ""))
                    source_column = column.name
                    label = snake_to_caps_snake(
                        column.info.get("edge", column.name.replace("_id", ""))
                    )
                    target_node_label = snake_to_camel(
                        list(column.foreign_keys)[0].column.table.name
                    )
                    # Determine target_column from the table's columns.
                    target_column = ""
                    for col in column.table.columns:
                        if col.name == column.name:
                            continue
                        target_column = col.name
                    self.edges.append(
                        Edge(
                            source_node_label=source_node_label,
                            source_column=source_column,
                            label=label,
                            target_column=target_column,
                            target_node_label=target_node_label,
                            target_val_data_type=col.type.python_type.__name__,
                        )
                    )
        return self

    @computed_field
    def create_labels(self) -> str:
        """
        Returns a SQL script for creating labels for nodes and edges in the graph database.

        The script sets the role to the admin role, then creates vertex and edge labels.
        """
        node_labels_sql = "\n".join([node.label_sql() for node in self.nodes])
        edges_sql = "\n".join(
            [edge.label_sql(config=self.config) for edge in self.edges]
        )

        admin_role = f"{self.config.DB_NAME}_admin"
        sql_script = textwrap.dedent(
            f"""
        DO $$
        BEGIN
            SET ROLE {admin_role};
            {node_labels_sql}
            {edges_sql}
        END $$;
        """
        )
        return sql_script

    def function_string(self, operation: str) -> str:
        """
        Generate an SQL string for an operation on nodes and edges in the graph database.

        Args:
            operation (str): One of "insert_sql", "update_sql", "delete_sql", or "truncate_sql".

        Returns:
            str: The formatted SQL string.
        """
        return_value = (
            "OLD"
            if operation == "delete_sql"
            else "NULL" if operation == "truncate_sql" else "NEW"
        )

        nodes_sql = "".join([getattr(node, operation)() for node in self.nodes])
        edges_sql = "".join([getattr(edge, operation)() for edge in self.edges])

        admin_role = f"{self.config.DB_NAME}_admin"
        function_sql = textwrap.dedent(
            f"""
        DECLARE
            cypher_query TEXT;
            column_type TEXT;
            column_text TEXT;
            column_int BIGINT;
        BEGIN
            SET ROLE {admin_role};
            -- Execute the Cypher query to {operation} nodes
            {nodes_sql}
            -- Execute the Cypher query to {operation} edges
            {edges_sql}
            RETURN {return_value};
        END;
        """
        )
        return function_sql

    @computed_field
    def create_insert_function(self) -> str:
        function_sql = self.function_string("insert_sql")
        return self.create_sql_function(
            "insert_graph",
            function_sql,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def create_update_function(self) -> str:
        function_sql = self.function_string("update_sql")
        return self.create_sql_function(
            "update_graph",
            function_sql,
            timing="AFTER",
            operation="UPDATE",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def create_delete_function(self) -> str:
        function_sql = self.function_string("delete_sql")
        return self.create_sql_function(
            "delete_graph",
            function_sql,
            timing="AFTER",
            operation="DELETE",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def create_truncate_function(self) -> str:
        function_sql = self.function_string("truncate_sql")
        return self.create_sql_function(
            "truncate_graph",
            function_sql,
            timing="BEFORE",
            operation="TRUNCATE",
            for_each="STATEMENT",
            include_trigger=True,
            db_function=False,
        )


class Node(BaseModel):
    """
    Represents a node in the graph database associated with a specific database column.
    """

    column: Column
    label: str
    node_triggers: bool = True
    edges: List["Edge"] = []
    target_data_type: str
    config: BaseSettings = uno_settings

    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        """
        Validate the node and add associated edges if applicable.
        """
        if self.column.info.get("graph_excludes", False):
            return self

        if self.column.foreign_keys:
            source_node_label = snake_to_camel(self.column.table.name)
            source_column = list(self.column.foreign_keys)[0].column.name
            target_node_label = snake_to_camel(
                list(self.column.foreign_keys)[0].column.table.name
            )
            target_column = self.column.name
            edge_label = snake_to_caps_snake(
                self.column.info.get("edge", self.column.name.replace("_id", ""))
            )
            self.edges.append(
                Edge(
                    source_node_label=source_node_label,
                    source_column=source_column,
                    label=edge_label,
                    target_column=target_column,
                    target_node_label=target_node_label,
                    target_val_data_type=self.target_data_type,
                )
            )
            if self.column.info.get("reverse_edge", False):
                self.edges.append(
                    Edge(
                        source_node_label=target_node_label,
                        source_column=target_column,
                        label=snake_to_caps_snake(self.column.info["reverse_edge"]),
                        target_column=source_column,
                        target_node_label=snake_to_camel(source_node_label),
                        target_val_data_type=self.target_data_type,
                    )
                )
        else:
            source_node_label = snake_to_camel(self.column.table.name)
            default_label = snake_to_caps_snake(self.column.name.replace("_id", ""))
            target_column = "id"
            target_node_label = snake_to_camel(self.column.name.replace("_id", ""))
            source_column = "id"
            edge_label = snake_to_caps_snake(
                self.column.info.get("edge", default_label)
            )
            self.edges.append(
                Edge(
                    source_node_label=source_node_label,
                    source_column=source_column,
                    label=edge_label,
                    target_column=target_column,
                    target_node_label=target_node_label,
                    target_val_data_type=self.target_data_type,
                )
            )
        return self

    def label_sql(self) -> str:
        """
        Generate an SQL string to create a vertex label if it does not exist.
        """
        edges_sql = "\n".join(edge.label_sql(self.config) for edge in self.edges)
        reader_role = f"{self.config.DB_NAME}_reader"
        writer_role = f"{self.config.DB_NAME}_writer"
        sql_str = textwrap.dedent(
            f"""
        IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = '{self.label}') THEN
            PERFORM ag_catalog.create_vlabel('graph', '{self.label}');
            CREATE INDEX ON graph."{self.label}" (id);
            CREATE INDEX ON graph."{self.label}" USING gin (properties);
            GRANT SELECT ON graph."{self.label}" TO {reader_role};
            GRANT SELECT, UPDATE, DELETE ON graph."{self.label}" TO {writer_role};
        END IF;
        {edges_sql}
        """
        )
        return sql_str

    def insert_sql(self) -> str:
        """
        Generate an SQL query for inserting a node.
        """
        create_statements = "\n".join([edge.create_statement() for edge in self.edges])
        sql_str = textwrap.dedent(
            f"""
        IF NEW.{self.column.name} IS NOT NULL THEN
            SELECT pg_typeof(NEW.{self.column.name}) INTO column_type;
            CASE
                WHEN column_type = 'bool' THEN
                    column_text := NEW.{self.column.name}::TEXT;
                WHEN column_type = 'int' THEN
                    column_text := NEW.{self.column.name}::TEXT;
                WHEN column_type = 'float' THEN
                    column_text := NEW.{self.column.name}::TEXT;
                WHEN column_type = 'timestamp with time zone' THEN 
                    column_text := EXTRACT(EPOCH FROM NEW.{self.column.name})::BIGINT::TEXT;
                ELSE 
                    column_text := NEW.{self.column.name}::TEXT;
            END CASE;
            cypher_query := FORMAT(
                'MERGE (v:{self.label} {{id: %s}}) SET v.val = %s',
                quote_nullable(NEW.id), quote_nullable(column_text)
            );
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
            {create_statements}
        END IF;
        """
        )
        return sql_str

    def update_sql(self) -> str:
        """
        Generate an SQL query for updating a node.
        """
        delete_statements = "\n".join([edge.delete_statement() for edge in self.edges])
        create_statements = "\n".join([edge.create_statement() for edge in self.edges])
        sql_str = textwrap.dedent(
            f"""
        IF NEW.{self.column.name} IS NOT NULL AND NEW.{self.column.name} != OLD.{self.column.name} THEN
            IF OLD.{self.column.name} IS NULL THEN 
                cypher_query := FORMAT('CREATE (v:{self.label} {{val: %s}})', quote_nullable(NEW.{self.column.name}));
                EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                {create_statements}
            ELSE
                cypher_query := FORMAT(
                    'MATCH (v:{self.label} {{val: %s}}) SET v.val = %s',
                    quote_nullable(OLD.{self.column.name}), quote_nullable(NEW.{self.column.name})
                );
                EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                {delete_statements}
                {create_statements}
            END IF;
        ELSIF NEW.{self.column.name} IS NULL THEN
            cypher_query := FORMAT('MATCH (v:{self.label} {{val: %s}}) DETACH DELETE v', quote_nullable(OLD.{self.column.name}));
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
            {delete_statements}
        END IF;
        """
        )
        return sql_str

    def delete_sql(self) -> str:
        """
        Generate an SQL query for deleting a node.
        """
        if self.column.name != "id":
            return ""
        sql_str = textwrap.dedent(
            f"""
        /*
        Match and detach delete node using its id.
        */
        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
            MATCH (v: {{id: %s}})
            DETACH DELETE v
        $graph$) AS (e agtype);', OLD.id);
        """
        )
        return sql_str

    def truncate_sql(self) -> str:
        """
        Generate an SQL query for truncating nodes with the specified label.
        """
        sql_str = textwrap.dedent(
            f"""
        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
            MATCH (v:{self.label})
            DETACH DELETE v
        $graph$) AS (e agtype);');
        """
        )
        return sql_str


class Edge(BaseModel):
    """
    Represents an edge (relationship) in the graph database between two nodes.
    """

    source_node_label: str
    source_column: str
    label: str
    target_column: str
    target_node_label: str
    target_val_data_type: str
    config: BaseSettings = uno_settings

    def label_sql(self, config: BaseSettings) -> str:
        """
        Generate an SQL string to create an edge label if it does not exist.
        """
        reader_role = f"{config.DB_NAME}_reader"
        writer_role = f"{config.DB_NAME}_writer"
        sql_str = textwrap.dedent(
            f"""
        IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label WHERE name = '{self.label}') THEN
            PERFORM ag_catalog.create_elabel('graph', '{self.label}');
            CREATE INDEX ON graph."{self.label}" (start_id, end_id);
            GRANT SELECT ON graph."{self.label}" TO {reader_role};
            GRANT SELECT, UPDATE, DELETE ON graph."{self.label}" TO {writer_role};
        END IF;
        """
        )
        return sql_str

    def create_statement(self) -> str:
        """
        Generate an SQL statement to create an edge between two nodes.
        """
        sql_str = textwrap.dedent(
            f"""
        EXECUTE FORMAT('
            SELECT * FROM cypher(''graph'', $$
                MATCH (l:{self.source_node_label} {{id: %s}})
                MATCH (r:{self.target_node_label} {{id: %s}})
                CREATE (l)-[e:{self.label}]->(r)
            $$) AS (result agtype)',
            quote_nullable(NEW.{self.source_column}),
            quote_nullable(NEW.{self.target_column})
        );
        """
        )
        return sql_str

    def insert_sql(self) -> str:
        """
        Generate an SQL string to insert an edge for association tables.
        """
        sql_str = textwrap.dedent(
            f"""
        IF NEW.{self.target_column} IS NOT NULL THEN
            {self.create_statement()}
        END IF;
        """
        )
        return sql_str

    def delete_statement(self) -> str:
        """
        Generate an SQL statement to delete an edge.
        """
        sql_str = textwrap.dedent(
            f"""
        EXECUTE FORMAT('
            SELECT * FROM cypher(''graph'', $$
                MATCH (l:{self.source_node_label} {{id: %s}})
                MATCH (r:{self.target_node_label} {{id: %s}})
                MATCH (l)-[e:{self.label}]->(r)
                DELETE e
            $$) AS (result agtype)',
            quote_nullable(OLD.{self.source_column}),
            quote_nullable(OLD.{self.target_column})
        );
        """
        )
        return sql_str

    def update_sql(self) -> str:
        """
        Generate an SQL string to update an edge.
        """
        delete_stmt = self.delete_statement()
        create_stmt = self.create_statement()
        sql_str = textwrap.dedent(
            f"""
        IF NEW.{self.target_column} IS NOT NULL AND NEW.{self.target_column} != OLD.{self.target_column} THEN
            IF OLD.{self.target_column} != NEW.{self.target_column} THEN
                {delete_stmt}
            END IF;
            IF NEW.{self.target_column} IS NOT NULL THEN
                {create_stmt}
            END IF;
        END IF;
        """
        )
        return sql_str

    def delete_sql(self) -> str:
        """
        Generate an SQL string to delete an edge.
        """
        sql_str = textwrap.dedent(
            f"""
        EXECUTE FORMAT('
            SELECT * FROM cypher(''graph'', $$
                MATCH (l:{self.source_node_label} {{id: %s}})
                MATCH (r:{self.target_node_label} {{id: %s}})
                MATCH (l)-[e:{self.label}]->(r)
                DELETE e
            $$) AS (result agtype)',
            quote_nullable(OLD.{self.source_column}),
            quote_nullable(OLD.{self.target_column})
        );
        """
        )
        return sql_str

    def truncate_sql(self) -> str:
        """
        Generate an SQL string to truncate (delete) all edges with this label.
        """
        sql_str = textwrap.dedent(
            f"""
        EXECUTE FORMAT('
            SELECT * FROM cypher(''graph'', $$
                MATCH [e:{self.label}]
                DELETE e
            $$) AS (result agtype)'
        );
        """
        )
        return sql_str
