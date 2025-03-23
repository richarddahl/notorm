# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import ClassVar

from psycopg.sql import SQL, Identifier, Literal
from pydantic import BaseModel, computed_field, ConfigDict
from sqlalchemy import Column, Table

from uno.db.sql.sql_emitter import SQLEmitter, ADMIN_ROLE
from uno.utilities import convert_snake_to_camel, convert_snake_to_all_caps_snake


class GraphSQLEmitter(SQLEmitter):
    """
    GraphSQLEmitter is a specialized SQL emitter class designed to manage the lifecycle of
    graph nodes and edges, for a given database table.
    It provides methods to generate SQL functions and triggers for operations such as
    insert, update, delete, and truncate.

    Uno uses Apache AGE (https://age.apache.org/) as the graph database, which is built on
    top of PostgreSQL. The SQL functions and triggers generated by this class are designed
    to interact with Apache AGE's Cypher query language.

    Uno creates a node and edge for each column in the table, where the node represents
    the column's value and the edge represents the relationship between two nodes.

    Attributes:
        exclude_fields (ClassVar[list[str]]): A list of field names to exclude from the graph.
        table_name (str): The name of the table for which the graph is being generated.
        model (Optional[type[BaseModel]]): The model class for the table.
        table (Optional[Any]): The table object for the table.

    Computed Fields:
        - create_labels (str): Generates the SQL for creating graph structures, including node and edge labels.
        - nodes (list[Node]): Computes and returns a list of nodes based on the table.
        - edges (list[Edge]): Computes and returns a list of edges based on the table.
        - create_insert_function (str): Generates the SQL function for handling graph insertion operations.
        - create_update_function (str): Generates the SQL function for handling graph update operations.
        - create_delete_function (str): Generates the SQL function for handling graph deletion operations.
        - create_truncate_function (str): Generates the SQL function for handling graph truncation operations.

    Methods:
        - function_string(operation: str) -> str: Generates the SQL function body for a given operation
          (e.g., insert, update, delete, truncate).
    """

    exclude_fields: ClassVar[list[str]] = [
        "table",
        "table_name",
        "model",
        "nodes",
        "edges",
    ]
    # nodes: list[Node] = [] <- computed field
    # edges: list[Edge] = [] <- computed field

    @computed_field
    def create_labels(self) -> str:
        """Returns a SQL script for creating labels for nodes and edges in Apache AGE.

        The method constructs a SQL script that:
        - Sets the database role to the specified admin role.
        - Creates labels for nodes that are marked for creation.
        - Creates labels for edges.

        Returns:
            str: A formatted SQL script as a string.
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
                node_labels=SQL(
                    "\n".join(
                        [node.label_sql() for node in self.nodes if node.create_node]
                    )
                ),
                edge_labels=SQL("\n".join([edge.label_sql() for edge in self.edges])),
            )
            .as_string()
        )

    @computed_field
    def nodes(self) -> list["Node"]:
        """Returns a list of `Node` objects representing the columns of a database table.

        This method computes nodes for the table associated with the current instance.
        It creates a "table node" for the primary key column (if it exists) and additional
        nodes for each column in the table. Foreign key columns are handled differently,
        as their nodes are created by their source tables.

        Returns:
            list[Node]: A list of `Node` objects representing the table's columns.

        Notes:
            - If the `model` attribute is set, the table and filter excludes are derived
              from the model's base and filter_excludes attributes.
            - If the `model` attribute is not set, the table and filter excludes are
              derived from the `table` attribute and an empty list, respectively.
            - Columns listed in `filter_excludes` are skipped.
            - The "table node" is created for the primary key column (named "id").
            - Foreign key columns do not create standalone nodes, as their nodes are
              created by their source tables.
        """
        print("Computing nodes for", self.table_name)
        nodes = []
        if self.model:
            table = self.model.base.__table__
            filter_excludes = self.model.filter_excludes
        else:
            return nodes
            table = self.table
            filter_excludes = []

        # create the "table node" first
        if "id" in table.columns:
            nodes.append(
                Node(
                    column=table.columns["id"],
                    label=convert_snake_to_camel(self.table_name),
                    create_node=True,
                )
            )
        for column_name, column in table.columns.items():
            if column.name == "id":
                continue
            create_node = True
            if column_name in filter_excludes:
                continue
            if column.foreign_keys:
                label = convert_snake_to_camel(self.table_name)
                create_node = False  # FK nodes will be created by thier "source table"
            else:
                label = convert_snake_to_camel(column_name)
            nodes.append(
                Node(
                    column=column,
                    label=label,
                    create_node=create_node,
                )
            )
        return nodes

    @computed_field
    def edges(self) -> list["Edge"]:
        """Returns a list of `Edge` objects representing the columns of an association table.

        An edge represents a relationship between two nodes in a graph, where each
        node corresponds to a table or entity. The edges are derived from the foreign
        key relationships defined in the table's columns.

        Returns:
            list[Edge]: A list of `Edge` objects representing the relationships
            between nodes in the graph. Each `Edge` contains the following attributes:
                - source_node_label (str): The label of the source node derived from the column name.
                - column_name (str): The name of the column in the source table.
                - label (str): The label for the edge, derived from the column name or
                  overridden by the column's `edge_label` metadata.
                - destination_column_name (str): The name of the column in the destination table.
                - destination_node_label (str): The label of the destination node derived
                  from the foreign key's referenced table.

        Notes:
            - If the table has no nodes or no model, an empty list is returned.
            - The function assumes that column names ending with `_id` represent
              foreign key relationships.
            - The `convert_snake_to_camel` and `convert_snake_to_all_caps_snake`
              functions are used to transform column names into appropriate labels.
        """
        print("Computing edges for ", self.table_name)
        if self.model:
            return []  # Not an association table
        edges = []
        for column_name, column in self.table.columns.items():
            if column.foreign_keys:
                # This is a column from an Association Table
                source_node_label = convert_snake_to_camel(
                    column_name.replace("_id", "")
                )
                column_name_ = column_name
                for col_name, col in self.table.columns.items():
                    if col_name == column_name:
                        continue
                    label = convert_snake_to_all_caps_snake(col_name.replace("_id", ""))
                    destination_node_label = convert_snake_to_camel(
                        list(col.foreign_keys)[0].column.table.name
                    )
                    destination_column_name = col_name
                # This is a fallback for when the edge label derived from the column name is not correct
                label = column.info.get("edge_label", label)
                edges.append(
                    Edge(
                        source_node_label=source_node_label,
                        column_name=column_name_,
                        label=label,
                        destination_column_name=destination_column_name,
                        destination_node_label=destination_node_label,
                    )
                )
        return edges

    def function_string(self, operation: str) -> str:
        """Generates a SQL string for performing a specified operation for nodes and edges.

        Args:
            operation (str): The type of operation to perform. Supported values are:
                - "insert_sql": Generates SQL for creating or updating nodes and edges.
                - "update_sql": Generates SQL for creating or updating nodes and edges.
                - "delete_sql": Generates SQL for deleting nodes and edges.
                - "truncate_sql": Generates SQL for truncating nodes and edges.

        Returns:
            str: A formatted SQL string that includes the operation logic for nodes and edges,
            along with the appropriate return value ("OLD", "NULL", or "NEW") based on the operation.

        Notes:
            - The SQL string includes placeholders for administrative roles, nodes, and edges,
              which are dynamically populated using the provided operation and the object's attributes.
            - The function assumes the existence of `self.nodes` and `self.edges`, which are iterated
              to generate operation-specific SQL fragments.
            - The `ADMIN_ROLE` constant is used to set the role for executing the SQL.
        """
        if operation == "delete_sql":
            return_value = "OLD"
        elif operation == "truncate_sql":
            return_value = "NULL"
        else:
            return_value = "NEW"
        return textwrap.dedent(
            SQL(
                """
            DECLARE
                cypher_query text;
            BEGIN
                SET ROLE {admin_role};
                -- Execute the Cypher query to {operation} the nodes and thier associated edges, for Base tables
                {nodes}
                -- Execute the Cypher queries to {operation} the edges for association tables
                {edges}
                RETURN {return_value};
            END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                operation=SQL(operation),
                nodes=SQL("".join([getattr(node, operation)() for node in self.nodes])),
                edges=SQL("".join([getattr(edge, operation)() for edge in self.edges])),
                return_value=SQL(return_value),
            )
            .as_string()
        )

    @computed_field
    def create_insert_function(self) -> str:
        function_string = self.function_string("insert_sql")
        return self.create_sql_function(
            "insert_graph",
            function_string,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def create_update_function(self) -> str:
        function_string = self.function_string("update_sql")
        return self.create_sql_function(
            "update_graph",
            function_string,
            timing="AFTER",
            operation="UPDATE",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def create_delete_function(self) -> str:
        function_string = self.function_string("delete_sql")
        return self.create_sql_function(
            "delete_graph",
            function_string,
            timing="AFTER",
            operation="DELETE",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def create_truncate_function(self) -> str:
        function_string = self.function_string("truncate_sql")
        return self.create_sql_function(
            "truncate_graph",
            function_string,
            timing="BEFORE",
            operation="TRUNCATE",
            for_each="STATEMENT",
            include_trigger=True,
            db_function=False,
        )


class Node(BaseModel):
    column: Column
    label: str
    create_node: bool = True
    # edge: "Edge" <- computed field

    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def edge(self) -> "Edge":
        """Generates an `Edge` object representing a relationship between nodes in a graph.

        Returns:
            Edge: An object containing the source node label, column name, edge label,
                  destination column name, and destination node label.

        The method determines the source and destination node labels, column names, and
        edge label based on whether the column has foreign keys. If foreign keys are present,
        the edge is derived from the foreign key relationship. Otherwise, it is inferred
        from the column name. Additionally, a custom edge label can be provided via the
        column's `info` dictionary under the key "edge_label".
        """
        print("Computing edges for", self.column.name)
        if self.column.foreign_keys:
            source_node_label = convert_snake_to_camel(self.column.table.name)
            column_name_ = list(self.column.foreign_keys)[0].column.name
            label = convert_snake_to_all_caps_snake(self.column.name.replace("_id", ""))
            destination_node_label = convert_snake_to_camel(
                list(self.column.foreign_keys)[0].column.table.name
            )
            destination_column_name = self.column.name
        else:
            source_node_label = convert_snake_to_camel(self.column.table.name)
            label = convert_snake_to_all_caps_snake(self.column.name.replace("_id", ""))
            destination_column_name = self.column.name
            destination_node_label = convert_snake_to_camel(
                self.column.name.replace("_id", "")
            )
            column_name_ = "id"
        # This is a fallback for when the edge label should not be derived from the column name
        label = self.column.info.get("edge_label", label)
        return Edge(
            source_node_label=source_node_label,
            column_name=column_name_,
            label=label,
            destination_column_name=destination_column_name,
            destination_node_label=destination_node_label,
        )

    def label_sql(self) -> str:
        """Generates an SQL string to create a vertex label in a graph database if it does not already exist.

        The SQL string performs the following actions:
        - Checks if a label with the specified name exists in the `ag_catalog.ag_label` table.
        - If the label does not exist:
            - Creates a vertex label in the graph using `ag_catalog.create_vlabel`.
            - Creates an index on the `id` column of the label.
            - Creates a GIN index on the `properties` column of the label.
        - Includes additional SQL for edge labels if applicable.

        Returns:
            str: The formatted SQL string.
        """
        return (
            SQL(
                """
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {label});
                    CREATE INDEX ON graph.{label_ident} (id);
                    CREATE INDEX ON graph.{label_ident} USING gin (properties);
                END IF;
                {edge_label}
            """
            )
            .format(
                label=Literal(self.label),
                label_ident=Identifier(self.label),
                edge_label=SQL(self.edge.label_sql()),
            )
            .as_string()
        )

    def insert_sql(self) -> str:
        """Generates an SQL string for inserting data into a graph database using Cypher queries.

        This method constructs a series of Cypher queries to:
        1. Merge a vertex (node) with a specific label and properties.
        2. Create an edge (relationship) between two nodes if certain conditions are met.

        Returns:
            str: The generated SQL string containing the Cypher queries.

        Notes:
            - The method uses placeholders for dynamic values such as labels, column names,
              and node/edge properties, which are formatted using the `SQL` and `format` methods.
            - The generated SQL assumes the use of a graph database with Cypher query support.
            - The `NEW` keyword refers to the new row being inserted in a trigger context.
        """
        return (
            SQL(
                """
                IF NEW.{column_name} IS NOT NULL THEN
                    cypher_query := FORMAT('
                        MERGE (v:{label} {{id: %s, val: %s}})',
                        quote_nullable(NEW.id), quote_nullable(NEW.{column_name})
                    );
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{source_node_label} {{id: %s}})
                            MATCH (r:{destination_node_label} {{id: %s}})
                            CREATE (l)-[e:{edge_label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(NEW.id),
                        quote_nullable(NEW.id)
                    );
                END IF;
            """
            )
            .format(
                label=SQL(self.label),
                column_name=SQL(self.column.name),
                source_node_label=SQL(self.edge.source_node_label),
                source_column_name=SQL(self.edge.column_name),
                edge_label=SQL(self.edge.label),
                destination_node_label=SQL(self.edge.destination_node_label),
                destination_column_name=SQL(self.edge.destination_column_name),
            )
            .as_string()
        )

    def update_sql(self) -> str:
        """Generates a SQL query string to handle updates to a graph database using Cypher queries.

        This method constructs and executes Cypher queries to manage nodes and edges in a graph
        database based on changes to a specific column in a relational database. It handles the
        following scenarios:

        1. If the new value of the column is not null and differs from the old value:
           - If the old value was null, it creates a new node and an edge in the graph.
           - If the old value was not null, it updates the node's value, deletes the existing edge,
             and creates a new edge.

        2. If the new value of the column is null:
           - Deletes the corresponding node and its associated edge from the graph.

        Returns:
            str: The generated SQL query string to execute the necessary Cypher queries.

        Notes:
            - The method uses the `FORMAT` function to dynamically construct Cypher queries.
            - The `EXECUTE` statement is used to run the Cypher queries within the graph database.
            - The method assumes the existence of specific labels, column names, and edge labels
              defined in the class attributes (`label`, `column`, `edge`).

        Raises:
            Any exceptions related to SQL execution or Cypher query formatting will propagate
            to the caller.
        """
        return (
            SQL(
                """
                IF NEW.{column_name} IS NOT NULL AND NEW.{column_name} != OLD.{column_name} THEN
                    IF OLD.{column_name} IS NULL THEN 
                        -- The object previously did not have a value for this field
                        -- Construct the Cypher query to create the node
                        cypher_query := FORMAT('CREATE (v:{label} {{val: %s}})', quote_nullable(NEW.{column_name}));
                        -- Execute the Cypher query
                        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                        -- Create the edge
                        cypher_query := FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                MATCH (l:{source_node_label} {{val: %s}})
                                MATCH (r:{destination_node_label} {{val: %s}})
                                CREATE (l)-[e:{edge_label}]->(r)
                            $$) AS (result agtype)',
                            quote_nullable(NEW.{source_column_name}),
                            quote_nullable(NEW.{destination_column_name}));
                        -- Execute the Cypher query
                        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    ELSE
                        -- The object previously had a value for this field, but it has changed
                        -- Construct the Cypher query to update the node
                        cypher_query := FORMAT('
                            MATCH (v:{label} {{val: %s}})
                            SET v.val = %s
                        ', quote_nullable(OLD.{column_name}), quote_nullable(NEW.{column_name}));
                        -- Execute the Cypher query
                        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                        -- Delete the existing edge
                        cypher_query := FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                MATCH (l:{source_node_label} {{val: %s}})-[e:{edge_label}]->(r:{destination_node_label} {{val: %s}})
                                DELETE e
                            $$) AS (result agtype)',
                            quote_nullable(OLD.{source_column_name}),
                            quote_nullable(OLD.{destination_column_name}));
                        -- Execute the Cypher query
                        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                        -- Create the edge
                        cypher_query := FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                MATCH (l:{source_node_label} {{val: %s}})
                                MATCH (r:{destination_node_label} {{val: %s}})
                                CREATE (l)-[e:{edge_label}]->(r)
                            $$) AS (result agtype)',
                            quote_nullable(NEW.{source_column_name}),
                            quote_nullable(NEW.{destination_column_name}));
                        -- Execute the Cypher query
                        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    END IF;
                ELSIF NEW.{column_name} IS NULL THEN
                    -- The object no longer has a value for this field, but previously did
                    -- Construct the Cypher query to delete the node
                    cypher_query := FORMAT('MATCH (v:{label} {{val: %s}}) DETACH DELETE v', quote_nullable(OLD.{column_name}));
                    -- Execute the Cypher query
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    -- Delete the existing edge
                    cypher_query := FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{source_node_label} {{val: %s}})-[e:{edge_label}]->(r:{destination_node_label} {{val: %s}})
                            DELETE e
                        $$) AS (result agtype)',
                        quote_nullable(OLD.{source_column_name}),
                        quote_nullable(OLD.{destination_column_name}));
                    -- Execute the Cypher query
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query
                    );
                END IF;
            """
            )
            .format(
                label=SQL(self.label),
                val=SQL(self.column.name),
                column_name=SQL(self.column.name),
                source_node_label=SQL(self.edge.source_node_label),
                source_column_name=SQL(self.edge.column_name),
                edge_label=SQL(self.edge.label),
                destination_column_name=SQL(self.edge.destination_column_name),
                destination_node_label=SQL(self.edge.destination_node_label),
            )
            .as_string()
        )

    def delete_sql(self) -> str:
        """Generates a SQL query string to delete a vertex from a graph database.

        The method constructs a SQL query that uses the `cypher` function to match
        a vertex with a specific label and value, and then performs a `DETACH DELETE`
        operation on the matched vertex.

        Returns:
            str: The SQL query string for deleting the specified vertex.
        """
        return (
            SQL(
                """
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        MATCH (v:{label} {{val: %s}})
                        DETACH DELETE v
                    $graph$) AS (e agtype);, OLD.id);');
            """
            )
            .format(label=SQL(self.label))
            .as_string()
        )

    def truncate_sql(self) -> str:
        """Generates a SQL query string to truncate (delete) all nodes of a specific label
        from a graph database using the Cypher query language.

        Returns:
            str: A SQL query string that matches and deletes all nodes with the specified
            label in the graph database.
        """
        return (
            SQL(
                """
                    SELECT * FROM cypher('graph', $graph$
                        MATCH (v:{label})
                        DETACH DELETE v
                    $graph$) AS (e agtype);
            """
            )
            .format(label=SQL(self.label))
            .as_string()
        )


class Edge(BaseModel):
    source_node_label: str
    column_name: str
    label: str
    destination_column_name: str
    destination_node_label: str

    def label_sql(self) -> str:
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
                label=Literal(self.label),
                label_ident=Identifier(self.label),
            )
            .as_string()
        )

    def insert_sql(self) -> str:
        return (
            SQL(
                """
                IF NEW.{destination_column_name} IS NOT NULL THEN
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{source_node_label} {{val: %s}})
                            MATCH (r:{destination_node_label} {{val: %s}})
                            CREATE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(NEW.{column_name}),
                        quote_nullable(NEW.{destination_column_name})
                    );
                END IF;
            """
            )
            .format(
                source_node_label=(SQL(self.source_node_label)),
                column_name=SQL(self.column_name),
                label=SQL(self.label),
                destination_node_label=SQL(self.destination_node_label),
                destination_column_name=SQL(self.destination_column_name),
            )
            .as_string()
        )

    def update_sql(self) -> str:
        return (
            SQL(
                """
                IF NEW.{destination_column_name} IS NOT NULL AND NEW.{destination_column_name} != OLD.{destination_column_name} THEN
                    IF OLD.{destination_column_name} != NEW.{destination_column_name} THEN
                        EXECUTE FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                DELETE (l:{source_node_label} {{val: %s}})
                                DELETE (r:{destination_node_label} {{val: %s}})
                                DELETE (l)-[e:{label}]->(r)
                            $$) AS (result agtype)',
                            quote_nullable(OLD.{column_name}),
                            quote_nullable(OLD.{destination_column_name})
                        ); 
                    END IF;
                    IF NEW.{destination_column_name} IS NOT NULL THEN
                        -- MERGE must be used in order to prevent duplicate nodes
                        -- For situations where the node already exists, i.e. when they are the same
                        -- e.g. User.created_by_id = User.id
                        EXECUTE FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                MERGE (l:{source_node_label} {{val: %s}})
                                MERGE (r:{destination_node_label} {{val: %s}})
                                CREATE (l)-[e:{label}]->(r)
                            $$) AS (result agtype)',
                            quote_nullable(NEW.{column_name}),
                            quote_nullable(NEW.{destination_column_name})
                        ); 
                    END IF;
                END IF;
            """
            )
            .format(
                source_node_label=(SQL(self.source_node_label)),
                column_name=SQL(self.column_name),
                label=SQL(self.label),
                destination_node_label=SQL(self.destination_node_label),
                destination_column_name=SQL(self.destination_column_name),
            )
            .as_string()
        )

    def delete_sql(self) -> str:
        return (
            SQL(
                """
                EXECUTE FORMAT('
                    SELECT * FROM cypher(''graph'', $$
                        MATCH (l:{source_node_label} {{val: %s}})-[e:{label}]->()
                        DELETE e
                    $$) AS (result agtype)',
                    quote_nullable(OLD.{column_name}),
                    quote_nullable(OLD.{destination_column_name})
                );
            """
            )
            .format(
                source_node_label=(SQL(self.source_node_label)),
                label=SQL(self.label),
                column_name=SQL(self.column_name),
                destination_column_name=SQL(self.destination_column_name),
            )
            .as_string()
        )

    def truncate_sql(self) -> str:
        return (
            SQL(
                """
                SELECT * FROM cypher('graph', $$
                    MATCH [e:{label}]
                    DELETE e
                $$) AS (result agtype);
            """
            )
            .format(
                source_node_label=(SQL(self.source_node_label)),
                label=SQL(self.label),
                destination_node_label=SQL(self.destination_node_label),
            )
            .as_string()
        )
