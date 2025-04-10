# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for graph database integration."""

import textwrap
from typing import List, Optional, ClassVar
from typing_extensions import Self

from pydantic import BaseModel, model_validator, computed_field, ConfigDict
from sqlalchemy import Column, Table

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder
from uno.utilities import snake_to_camel, snake_to_caps_snake


class GraphSQLEmitter(SQLEmitter):
    """Emitter for graph database operations.

    This class generates SQL for creating graph labels, functions, and triggers
    that synchronize relational database operations with a graph database.

    Attributes:
        exclude_fields: Fields to exclude when generating SQL
        nodes: List of node definitions
        edges: List of edge definitions
    """

    exclude_fields: ClassVar[List[str]] = [
        "table",
        "nodes",
        "edges",
        "config",
        "connection_config",
        "logger",
        "engine_factory",
        "observers",
    ]
    nodes: List["Node"] = []
    edges: List["Edge"] = []

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        """Validate and populate nodes and edges based on table columns.

        For tables that have an "id" column, a node is created representing the table.
        Columns with foreign keys yield additional nodes and related edges.

        For association tables (no "id" column), edges are defined by nodes.

        Returns:
            Self with populated nodes and edges
        """
        if self.table is None:
            return self

        if "id" in self.table.columns:
            new_nodes = []
            # Create the main node representing the table using the "id" column.
            new_nodes.append(
                Node(
                    column=self.table.columns["id"],
                    label=snake_to_camel(self.table.name),
                    node_triggers=True,
                    target_data_type=self.table.columns["id"].type.python_type.__name__,
                    config=self.config,
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
                        config=self.config,
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
                            config=self.config,
                        )
                    )
        return self

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for graph database integration.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate create labels SQL
        node_labels_sql = "\n".join([node.label_sql() for node in self.nodes])
        edges_sql = "\n".join(
            [edge.label_sql(config=self.config) for edge in self.edges]
        )

        admin_role = f"{self.config.DB_NAME}_admin"
        create_labels_sql = textwrap.dedent(
            f"""
            DO $$
            BEGIN
                SET ROLE {admin_role};
                {node_labels_sql}
                {edges_sql}
            END $$;
            """
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_labels",
                type=SQLStatementType.FUNCTION,
                sql=create_labels_sql,
            )
        )

        # Generate insert function SQL
        insert_function_body = self.function_string("insert_sql")

        insert_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_insert_graph")
            .with_return_type("TRIGGER")
            .with_body(insert_function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_insert_function",
                type=SQLStatementType.FUNCTION,
                sql=insert_function_sql,
            )
        )

        # Generate insert trigger SQL
        insert_trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_insert_graph_trigger")
            .with_function(f"{self.table.name}_insert_graph")
            .with_timing("AFTER")
            .with_operation("INSERT")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_insert_trigger",
                type=SQLStatementType.TRIGGER,
                sql=insert_trigger_sql,
            )
        )

        # Generate update function SQL
        update_function_body = self.function_string("update_sql")

        update_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_update_graph")
            .with_return_type("TRIGGER")
            .with_body(update_function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_update_function",
                type=SQLStatementType.FUNCTION,
                sql=update_function_sql,
            )
        )

        # Generate update trigger SQL
        update_trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_update_graph_trigger")
            .with_function(f"{self.table.name}_update_graph")
            .with_timing("AFTER")
            .with_operation("UPDATE")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_update_trigger",
                type=SQLStatementType.TRIGGER,
                sql=update_trigger_sql,
            )
        )

        # Generate delete function SQL
        delete_function_body = self.function_string("delete_sql")

        delete_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_delete_graph")
            .with_return_type("TRIGGER")
            .with_body(delete_function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_delete_function",
                type=SQLStatementType.FUNCTION,
                sql=delete_function_sql,
            )
        )

        # Generate delete trigger SQL
        delete_trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_delete_graph_trigger")
            .with_function(f"{self.table.name}_delete_graph")
            .with_timing("AFTER")
            .with_operation("DELETE")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_delete_trigger",
                type=SQLStatementType.TRIGGER,
                sql=delete_trigger_sql,
            )
        )

        # Generate truncate function SQL
        truncate_function_body = self.function_string("truncate_sql")

        truncate_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_truncate_graph")
            .with_return_type("TRIGGER")
            .with_body(truncate_function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_truncate_function",
                type=SQLStatementType.FUNCTION,
                sql=truncate_function_sql,
            )
        )

        # Generate truncate trigger SQL
        truncate_trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_truncate_graph_trigger")
            .with_function(f"{self.table.name}_truncate_graph")
            .with_timing("BEFORE")
            .with_operation("TRUNCATE")
            .with_for_each("STATEMENT")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_truncate_trigger",
                type=SQLStatementType.TRIGGER,
                sql=truncate_trigger_sql,
            )
        )

        return statements

    def function_string(self, operation: str) -> str:
        """Generate a SQL function body for graph operations.

        Args:
            operation: One of "insert_sql", "update_sql", "delete_sql", or "truncate_sql"

        Returns:
            SQL function body
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


class Node(BaseModel):
    """Represents a node in the graph database.

    Attributes:
        column: Database column this node is based on
        label: Label for the node in the graph database
        node_triggers: Whether to generate triggers for this node
        edges: List of edges connected to this node
        target_data_type: Data type for the node's target value
        config: Configuration settings
    """

    column: Column
    label: str
    node_triggers: bool = True
    edges: List["Edge"] = []
    target_data_type: str
    config: Optional[BaseModel] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        """Validate the node and add associated edges if applicable.

        Returns:
            Self with populated edges
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
        """Generate SQL to create a vertex label if it does not exist.

        Returns:
            SQL statement for creating label
        """
        # Pass a dummy config to avoid None issues if self.config is None
        dummy_config = type("obj", (object,), {"DB_NAME": "app"})
        config_to_use = self.config if self.config is not None else dummy_config

        edges_sql = "\n".join(edge.label_sql(config_to_use) for edge in self.edges)
        db_name = config_to_use.DB_NAME
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"

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
        """Generate SQL for inserting a node.

        Returns:
            SQL statement for node insertion
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
                SET LOCAL search_path TO ag_catalog;
                EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                {create_statements}
            END IF;
            """
        )
        return sql_str

    def update_sql(self) -> str:
        """Generate SQL for updating a node.

        Returns:
            SQL statement for node update
        """
        delete_statements = "\n".join([edge.delete_statement() for edge in self.edges])
        create_statements = "\n".join([edge.create_statement() for edge in self.edges])

        sql_str = textwrap.dedent(
            f"""
            IF NEW.{self.column.name} IS NOT NULL AND NEW.{self.column.name} != OLD.{self.column.name} THEN
                IF OLD.{self.column.name} IS NULL THEN 
                    cypher_query := FORMAT('CREATE (v:{self.label} {{val: %s}})', quote_nullable(NEW.{self.column.name}));
                    SET LOCAL search_path TO ag_catalog;
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    {create_statements}
                ELSE
                    cypher_query := FORMAT(
                        'MATCH (v:{self.label} {{val: %s}}) SET v.val = %s',
                        quote_nullable(OLD.{self.column.name}), quote_nullable(NEW.{self.column.name})
                    );
                    SET LOCAL search_path TO ag_catalog;
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
        """Generate SQL for deleting a node.

        Returns:
            SQL statement for node deletion
        """
        if self.column.name != "id":
            return ""

        sql_str = textwrap.dedent(
            f"""
            /*
            Match and detach delete node using its id.
            */
            SET LOCAL search_path TO ag_catalog;
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v: {{id: %s}})
                DETACH DELETE v
            $graph$) AS (e agtype);', OLD.id);
            """
        )
        return sql_str

    def truncate_sql(self) -> str:
        """Generate SQL for truncating nodes with this label.

        Returns:
            SQL statement for node truncation
        """
        sql_str = textwrap.dedent(
            f"""
            SET LOCAL search_path TO ag_catalog;
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.label})
                DETACH DELETE v
            $graph$) AS (e agtype);');
            """
        )
        return sql_str


class Edge(BaseModel):
    """Represents an edge (relationship) in the graph database.

    Attributes:
        source_node_label: Label of the source node
        source_column: Column name in the source node
        label: Label for the edge in the graph database
        target_column: Column name in the target node
        target_node_label: Label of the target node
        target_val_data_type: Data type for the target value
        config: Configuration settings
    """

    source_node_label: str
    source_column: str
    label: str
    target_column: str
    target_node_label: str
    target_val_data_type: str
    config: Optional[BaseModel] = None

    def label_sql(self, config: Optional[BaseModel] = None) -> str:
        """Generate SQL for creating an edge label if it does not exist.

        Args:
            config: Configuration settings

        Returns:
            SQL statement for creating edge label
        """
        # Create a dummy config object if neither config nor self.config is available
        dummy_config = type("obj", (object,), {"DB_NAME": "app"})
        conf = (
            config
            if config is not None
            else (self.config if self.config is not None else dummy_config)
        )
        db_name = conf.DB_NAME
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"

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
        """Generate SQL for creating an edge between nodes.

        Returns:
            SQL statement for edge creation
        """
        sql_str = textwrap.dedent(
            f"""
            SET LOCAL search_path TO ag_catalog;
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
        """Generate SQL for inserting an edge.

        Returns:
            SQL statement for edge insertion
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
        """Generate SQL for deleting an edge.

        Returns:
            SQL statement for edge deletion
        """
        sql_str = textwrap.dedent(
            f"""
            SET LOCAL search_path TO ag_catalog;
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
        """Generate SQL for updating an edge.

        Returns:
            SQL statement for edge update
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
        """Generate SQL for deleting an edge.

        Returns:
            SQL statement for edge deletion
        """
        sql_str = textwrap.dedent(
            f"""
            SET LOCAL search_path TO ag_catalog;
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
        """Generate SQL for truncating all edges with this label.

        Returns:
            SQL statement for edge truncation
        """
        sql_str = textwrap.dedent(
            f"""
            SET LOCAL search_path TO ag_catalog;
            EXECUTE FORMAT('
                SELECT * FROM cypher(''graph'', $$
                    MATCH [e:{self.label}]
                    DELETE e
                $$) AS (result agtype)'
            );
            """
        )
        return sql_str
