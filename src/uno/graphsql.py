# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import ClassVar
from typing_extensions import Self

from psycopg import sql
from pydantic import BaseModel, computed_field, ConfigDict, model_validator
from sqlalchemy import Column

from uno.sqlemitter import SQLEmitter, ADMIN_ROLE, READER_ROLE, WRITER_ROLE
from uno.utilities import snake_to_camel, snake_to_caps_snake


class ConvertProperty(SQLEmitter):
    """Cast the property to the correct data type for the graph database.

    This is needed as the graph database does not support all of the same data types
    as the relational database.  For example, a timestamp in PostgreSQL is a datetime
    in Python, but in the graph database it is a string.
    """

    def convert_property_function(self) -> str:
        function_string = (
            sql.SQL(
                """
            IF pg_typeof(column) = 'timestamp'::pg_catalog.timestamp THEN
                RETURN EXTRACT(EPOCH FROM column)::INT::TEXT
            END IF;

            """
            )
            .format(
                column_name=sql.SQL(self.column.name),
                target_data_type=sql.SQL(self.column.type.python_type.__name__),
            )
            .as_string()
        )

        return self.createsqlfunction(
            "convert_property",
            function_string,
            function_args="column ",
            return_type="TEXT",
        )


class GraphSQLEmitter(SQLEmitter):

    exclude_fields: ClassVar[list[str]] = ["table", "nodes", "edges"]
    nodes: list["Node"] = []
    edges: list["Edge"] = []

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        nodes = []
        # create the node that represents the table first
        if "id" in self.table.columns.keys():
            nodes.append(
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
                    label = snake_to_camel(
                        list(column.foreign_keys)[0].column.table.name
                    )
                    node_triggers = (
                        False  # FK nodes will be managed by thier source table triggers
                    )
                else:
                    label = snake_to_camel(column.name)
                nodes.append(
                    Node(
                        column=column,
                        label=label,
                        node_triggers=node_triggers,
                        target_data_type=column.type.python_type.__name__,
                    )
                )
            self.nodes = nodes
            return self

        # This is for Tables, edges are defined by nodes for Model.tables
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
        """Returns a sql.SQL script for creating labels for nodes and edges in Apache AGE.

        The method constructs a sql.SQL script that:
        - Sets the database role to the specified admin role.
        - Creates labels for nodes that are marked for creation.
        - Creates labels for edges.

        Returns:
            str: A formatted sql.SQL script as a string.
        """
        return textwrap.dedent(
            sql.SQL(
                """
            DO $$
            BEGIN
                SET ROLE {admin_role};
                {node_labels}
                {edges}
            END $$;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                node_labels=sql.SQL(
                    "\n".join([node.label_sql() for node in self.nodes])
                ),
                edges=sql.SQL("\n".join([edge.label_sql() for edge in self.edges])),
            )
            .as_string()
        )

    def function_string(self, operation: str) -> str:
        """Generates a sql.SQL string for performing a specified operation for nodes and edges.

        Args:
            operation (str): The type of operation to perform. Supported values are:
                - "insert_sql": Generates sql.SQL for creating or updating nodes and edges.
                - "update_sql": Generates sql.SQL for creating or updating nodes and edges.
                - "delete_sql": Generates sql.SQL for deleting nodes and edges.
                - "truncate_sql": Generates sql.SQL for truncating nodes and edges.

        Returns:
            str: A formatted sql.SQL string that includes the operation logic for nodes and edges,
            along with the appropriate return value ("OLD", "NULL", or "NEW") based on the operation.

        Notes:
            - The sql.SQL string includes placeholders for administrative roles, nodes, and edges,
              which are dynamically populated using the provided operation and the object's attributes.
            - The function assumes the existence of `self.nodes` and `self.edges`, which are iterated
              to generate operation-specific sql.SQL fragments.
            - The `ADMIN_ROLE` constant is used to set the role for executing the sql.SQL.
        """
        if operation == "delete_sql":
            return_value = "OLD"
        elif operation == "truncate_sql":
            return_value = "NULL"
        else:
            return_value = "NEW"
        return textwrap.dedent(
            sql.SQL(
                """
            DECLARE
                cypher_query TEXT;
                column_type TEXT;
                column_text TEXT;
                column_int BIGINT;
            BEGIN
                SET ROLE {admin_role};
                -- Execute the Cypher query to {operation} the nodes and thier associated edges, for Model tables
                {nodes}
                -- Execute the Cypher queries to {operation} the edges for association tables
                {edges}
                RETURN {return_value};
            END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                operation=sql.SQL(operation),
                nodes=sql.SQL(
                    "".join(
                        [
                            getattr(node, operation)()
                            for node in self.nodes
                            # if node.node_triggers
                        ]
                    )
                ),
                edges=sql.SQL(
                    "".join([getattr(edge, operation)() for edge in self.edges])
                ),
                return_value=sql.SQL(return_value),
            )
            .as_string()
        )

    @computed_field
    def create_insert_function(self) -> str:
        function_string = self.function_string("insert_sql")
        return self.createsqlfunction(
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
        return self.createsqlfunction(
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
        return self.createsqlfunction(
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
        return self.createsqlfunction(
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
    node_triggers: bool = True
    edges: list["Edge"] = []
    target_data_type: str

    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.column.info.get("graph_excludes", False):
            return self
        if self.column.foreign_keys:
            source_node_label = snake_to_camel(self.column.table.name)
            source_column = list(self.column.foreign_keys)[0].column.name
            target_node_label = snake_to_camel(
                list(self.column.foreign_keys)[0].column.table.name
            )
            target_column = self.column.name
            label = snake_to_caps_snake(
                self.column.info.get(
                    "edge",
                    self.column.name.replace("_id", ""),
                )
            )
            self.edges.append(
                Edge(
                    source_node_label=source_node_label,
                    source_column=source_column,
                    label=label,
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
            label = snake_to_caps_snake(self.column.name.replace("_id", ""))
            target_column = "id"
            target_node_label = snake_to_camel(self.column.name.replace("_id", ""))
            source_column = "id"
            # This is a fallback for when the edge label should not be derived from the column name
            label = snake_to_caps_snake(self.column.info.get("edge", label))
            self.edges.append(
                Edge(
                    source_node_label=source_node_label,
                    source_column=source_column,
                    label=label,
                    target_column=target_column,
                    target_node_label=target_node_label,
                    target_val_data_type=self.target_data_type,
                )
            )
        return self

    def label_sql(self) -> str:
        """Generates an sql.SQL string to create a vertex label in a graph database if it does not already exist.

        The sql.SQL string performs the following actions:
        - Checks if a label with the specified name exists in the `ag_catalog.ag_label` table.
        - If the label does not exist:
            - Creates a vertex label in the graph using `ag_catalog.create_vlabel`.
            - Creates an index on the `id` column of the label.
            - Creates a GIN index on the `properties` column of the label.
        - Includes additional sql.SQL for edge labels if applicable.

        Returns:
            str: The formatted sql.SQL string.
        """
        return (
            sql.SQL(
                """
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {label});
                    CREATE INDEX ON graph.{label_ident} (id);
                    CREATE INDEX ON graph.{label_ident} USING gin (properties);
                    GRANT SELECT ON graph.{label_ident} TO {reader_role};
                    GRANT SELECT, UPDATE, DELETE ON graph.{label_ident} TO {writer_role};
                END IF;
                {edges}
            """
            )
            .format(
                label=sql.Literal(self.label),
                label_ident=sql.Identifier(self.label),
                edges=sql.SQL("\n".join([edge.label_sql() for edge in self.edges])),
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
            )
            .as_string()
        )

    def insert_sql(self) -> str:

        return (
            sql.SQL(
                """
                -- MERGE must be used to ensure that the node is created only if it does not already exist
                -- This is required as some objects have multiple relationsihps to the same object, i.e. User

                IF NEW.{column_name} IS NOT NULL THEN
                    SELECT pg_typeof(NEW.{column_name}) INTO column_type;
                    -- As all graph propertsies are stored as text, 
                    -- We need to convert the column to text in a format
                    -- That can be used for comparision during search
                    CASE
                        WHEN column_type = 'bool' THEN
                            column_text := NEW.{column_name}::TEXT;
                        WHEN column_type = 'int' THEN
                            column_text := NEW.{column_name}::TEXT;
                        WHEN column_type = 'float' THEN
                            column_text := NEW.{column_name}::TEXT;
                        WHEN column_type = 'timestamp with time zone' THEN 
                            column_text := EXTRACT(EPOCH FROM NEW.{column_name})::BIGINT::TEXT;
                        ELSE column_text := NEW.{column_name}::TEXT;
                    END CASE;

                    cypher_query := FORMAT('
                        MERGE (v:{label} {{id: %s}})
                        SET v.val =  %s',
                        quote_nullable(NEW.id), quote_nullable(column_text)
                    );
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    {create_statements}
                END IF;
            """
            )
            .format(
                label=sql.SQL(self.label),
                column_name=sql.SQL(self.column.name),
                create_statements=sql.SQL(
                    "\n".join([edge.create_statement() for edge in self.edges])
                ),
            )
            .as_string()
        )

    def update_sql(self) -> str:
        """Generates a sql.SQL query string to handle updates to a graph database using Cypher queries.

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
            str: The generated sql.SQL query string to execute the necessary Cypher queries.

        Notes:
            - The method uses the `FORMAT` function to dynamically construct Cypher queries.
            - The `EXECUTE` statement is used to run the Cypher queries within the graph database.
            - The method assumes the existence of specific labels, column names, and edge labels
              defined in the class attributes (`label`, `column`, `edge`).

        Raises:
            Any exceptions related to sql.SQL execution or Cypher query formatting will propagate
            to the caller.
        """
        return (
            sql.SQL(
                """
                IF NEW.{column_name} IS NOT NULL AND NEW.{column_name} != OLD.{column_name} THEN
                    IF OLD.{column_name} IS NULL THEN 
                        -- The object previously did not have a value for this field
                        -- Construct the Cypher query to create the node
                        cypher_query := FORMAT('CREATE (v:{label} {{val: %s}})', quote_nullable(NEW.{column_name}));
                        -- Execute the Cypher query
                        EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                        -- Create the edge
                        {create_statements}
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
                        {delete_statements}
                        -- Create the edge
                        {create_statements}
                    END IF;
                ELSIF NEW.{column_name} IS NULL THEN
                    -- The object no longer has a value for this field, but previously did
                    -- Construct the Cypher query to delete the node
                    cypher_query := FORMAT('MATCH (v:{label} {{val: %s}}) DETACH DELETE v', quote_nullable(OLD.{column_name}));
                    -- Execute the Cypher query
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);
                    -- Delete the existing edge
                    {delete_statements}
                END IF;
            """
            )
            .format(
                label=sql.SQL(self.label),
                column_name=sql.SQL(self.column.name),
                delete_statements=sql.SQL(
                    "\n".join([edge.delete_statement() for edge in self.edges])
                ),
                create_statements=sql.SQL(
                    "\n".join([edge.create_statement() for edge in self.edges])
                ),
            )
            .as_string()
        )

    def delete_sql(self) -> str:
        """Generates a sql.SQL query string to delete a vertex from a graph database.

        The method constructs a sql.SQL query that uses the `cypher` function to match
        a vertex with a specific label and value, and then performs a `DETACH DELETE`
        operation on the matched vertex.

        Returns:
            str: The sql.SQL query string for deleting the specified vertex.
        """
        if self.column.name != "id":
            return ""
        return sql.SQL(
            """
                    /*
                    Match all of the nodes with the objects id and delete them
                    Detach delete ensures that all edges using the nodes are also deleted
                    All "local" nodes, those that are not foreign keys, 
                        as they have the same id property will be deleted
                    */
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        MATCH (v: {id: %s})
                        DETACH DELETE v
                    $graph$) AS (e agtype);', OLD.id);
            """
        ).as_string()

    def truncate_sql(self) -> str:
        """Generates a sql.SQL query string to truncate (delete) all nodes of a specific label
        in a graph database using the Cypher query language.

        Returns:
            str: A sql.SQL query string that deletes all nodes with the specified label
            if the column name is "id". Returns an empty string otherwise.  All node
        """
        return (
            sql.SQL(
                """
                    -- Detach delete ensures that all edges using the node are also deleted
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        MATCH (v:{label})
                        DETACH DELETE v
                    $graph$) AS (e agtype);');
            """
            )
            .format(label=sql.SQL(self.label))
            .as_string()
        )


class Edge(BaseModel):
    source_node_label: str
    source_column: str
    label: str
    target_column: str
    target_node_label: str
    target_val_data_type: str

    def label_sql(self) -> str:
        return (
            sql.SQL(
                """
                IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_elabel('graph', {label});
                    CREATE INDEX ON graph.{label_ident} (start_id, end_id);
                    GRANT SELECT ON graph.{label_ident} TO {reader_role};
                    GRANT SELECT, UPDATE, DELETE ON graph.{label_ident} TO {writer_role};
                END IF;
            """
            )
            .format(
                label=sql.Literal(self.label),
                label_ident=sql.Identifier(self.label),
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                # mock_edge=sql.SQL(self.mock_edge_for_filter()),
            )
            .as_string()
        )

    '''
    def mock_edge_for_filter(self) -> str:
        return (
            sql.SQL(
                """
                SELECT *
                FROM cypher('graph', $$
                    MATCH (s:{source_node_label})
                    MATCH (t:{target_node_label})
                    CREATE (s)-[e:{label}]->(t)
                $$) AS (result agtype)
                );
            """
            )
            .format(
                source_node_label=sql.SQL(self.source_node_label),
                label=sql.SQL(self.label),
                target_node_label=sql.SQL(self.target_node_label),
            )
            .as_string()
        )
    '''

    def create_statement(self) -> str:
        return (
            sql.SQL(
                """
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{source_node_label} {{id: %s}})
                            MATCH (r:{target_node_label} {{id: %s}})
                            CREATE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(NEW.{source_column}),
                        quote_nullable(NEW.{target_column})
                    );
            """
            )
            .format(
                source_node_label=(sql.SQL(self.source_node_label)),
                source_column=sql.SQL(self.source_column),
                label=sql.SQL(self.label),
                target_node_label=sql.SQL(self.target_node_label),
                target_column=sql.SQL(self.target_column),
            )
            .as_string()
        )

    def insert_sql(self) -> str:
        return (
            sql.SQL(
                """
                -- Insert graph edges for association tables
                IF NEW.{target_column} IS NOT NULL THEN
                    {create_statement}
                END IF;
            """
            )
            .format(
                target_column=sql.SQL(self.target_column),
                create_statement=sql.SQL(self.create_statement()),
            )
            .as_string()
        )

    def insert_sql_old(self) -> str:
        return (
            sql.SQL(
                """
                -- Insert graph edges for association tables
                IF NEW.{target_column} IS NOT NULL THEN
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{source_node_label} {{id: %s}})
                            MATCH (r:{target_node_label} {{id: %s}})
                            CREATE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(NEW.{source_column}),
                        quote_nullable(NEW.{target_column})
                    );
                END IF;
            """
            )
            .format(
                target_column=sql.SQL(self.target_column),
                source_node_label=(sql.SQL(self.source_node_label)),
                label=sql.SQL(self.label),
                source_column=sql.SQL(self.source_column),
                target_node_label=sql.SQL(self.target_node_label),
            )
            .as_string()
        )

    def delete_statement(self) -> str:
        return (
            sql.SQL(
                """
                        EXECUTE FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                MATCH (l:{source_node_label} {{id: %s}})
                                MATCH (r:{target_node_label} {{id: %s}})
                                MATCH (l)-[e:{label}]->(r)
                                DELETE e
                            $$) AS (result agtype)',
                            quote_nullable(OLD.{source_column}),
                            quote_nullable(OLD.{target_column})
                        ); 
            """
            )
            .format(
                source_node_label=(sql.SQL(self.source_node_label)),
                source_column=sql.SQL(self.source_column),
                label=sql.SQL(self.label),
                target_node_label=sql.SQL(self.target_node_label),
                target_column=sql.SQL(self.target_column),
            )
            .as_string()
        )

    def update_sql(self) -> str:
        return (
            sql.SQL(
                """
                -- Update graph edges for association tables
                IF NEW.{target_column} IS NOT NULL AND NEW.{target_column} != OLD.{target_column} THEN
                    IF OLD.{target_column} != NEW.{target_column} THEN
                        {delete_statement}
                    END IF;
                    IF NEW.{target_column} IS NOT NULL THEN
                        {create_statement}
                    END IF;
                END IF;
            """
            )
            .format(
                target_column=sql.SQL(self.target_column),
                delete_statement=sql.SQL(self.delete_statement()),
                create_statement=sql.SQL(self.create_statement()),
            )
            .as_string()
        )

    def delete_sql(self) -> str:
        return (
            sql.SQL(
                """
                -- Delete graph edges for association tables
                EXECUTE FORMAT('
                    SELECT * FROM cypher(''graph'', $$
                        MATCH (l:{source_node_label} {{id: %s}})
                        MATCH (r:{target_node_label} {{id: %s}})
                        MATCH (l)-[e:{label}]->(r)
                        DELETE e
                    $$) AS (result agtype)',
                    quote_nullable(OLD.{source_column}),
                    quote_nullable(OLD.{target_column})
                );
            """
            )
            .format(
                source_node_label=(sql.SQL(self.source_node_label)),
                target_node_label=sql.SQL(self.target_node_label),
                label=sql.SQL(self.label),
                source_column=sql.SQL(self.source_column),
                target_column=sql.SQL(self.target_column),
            )
            .as_string()
        )

    def truncate_sql(self) -> str:
        return (
            sql.SQL(
                """
                -- Truncate graph edges for association tables
                EXECUTE FORMAT('
                    SELECT * FROM cypher(''graph'', $$
                        MATCH [e:{label}]
                        DELETE e
                    $$) AS (result agtype)'
                );
            """
            )
            .format(
                source_node_label=(sql.SQL(self.source_node_label)),
                label=sql.SQL(self.label),
                target_node_label=sql.SQL(self.target_node_label),
            )
            .as_string()
        )
