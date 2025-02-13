# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from dataclasses import dataclass
from datetime import datetime, date, time
from decimal import Decimal


from psycopg.sql import SQL, Identifier, Literal

from pydantic import ConfigDict, computed_field

from sqlalchemy import Column

from uno.grph.enums import (
    Lookup,
    related_lookups,
    numeric_lookups,
    string_lookups,
)
from uno.config import settings


ADMIN_ROLE = f"{settings.DB_NAME}_admin"


@dataclass
class GraphBase:
    def create_sql_trigger(
        self,
        function_name: str,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        db_function: bool = True,
    ) -> str:
        trigger_scope = (
            f"{self.schema_name}."
            if db_function
            else f"{self.schema_name}.{self.table_name}_"
        )
        return textwrap.dedent(
            f"""
            CREATE OR REPLACE TRIGGER {self.table_name}_{function_name}_trigger
                {timing} {operation}
                ON {self.schema_name}.{self.table_name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
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
            f"{self.schema_name}.{function_name}"
            if db_function
            else f"{self.schema_name}.{self.table_name}_{function_name}"
        )
        fnct_string = textwrap.dedent(
            f"""
            SET ROLE {settings.DB_NAME}_admin;
            CREATE OR REPLACE FUNCTION {full_function_name}({function_args})
            RETURNS {return_type}
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            {function_string}
            $$;
            """
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
        return f"{textwrap.dedent(fnct_string)}\n{textwrap.dedent(trggr_string)}"


class GraphProperty(GraphBase):
    # table_name: str <- GraphBase
    # schema_name: str <- GraphBase

    # accessor: str <- computed_field
    # lookups: Lookup <- computed_field

    column: Column

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def accessor(self) -> str:
        return self.column.name

    @computed_field
    def lookups(self) -> Lookup:
        if self.column.foreign_keys:
            return related_lookups
        if self.column.type.python_type in [
            int,
            float,
            Decimal,
            datetime,
            date,
            time,
        ]:
            return numeric_lookups
        return string_lookups

    @computed_field
    def label(self) -> str:
        return self.column.name.replace("_id", " ").replace("_", " ").title()


@dataclass
class GraphNode(GraphBase):
    table_name: str
    label: str
    schema_name: str = "uno"
    column_name: str = "id"
    properties: list[GraphProperty] = None

    def emit_sql(self) -> str:
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
        sql = self.create_node_label_and_record_sql()
        # sql += f"\n{self.insert_node_sql()}"
        # sql += f"\n{self.update_nodet_sql()}"
        # sql += f"\n{self.delete_nodet_sql()}"
        # sql += f"\n{self.truncate_nodet_sql()}"
        # sql += f"\n{self.create_filter_field_sql()}"
        return textwrap.dedent(sql)

    def create_node_label_and_record_sql(self) -> str:
        query = SQL(
            """
            DO $$
            DECLARE
                object_type_id INT;
            BEGIN
                SET ROLE {admin_role};
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label
                WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {label});
                    EXECUTE format('CREATE INDEX ON graph.{label_ident} (id);');
                END IF;

                SELECT id
                    FROM uno.object_type
                    WHERE schema_name = {schema_name} AND table_name = {table_name}
                    INTO object_type_id;
                
                IF object_type_id IS NULL THEN
                    RAISE EXCEPTION 'Object Type not found for table. Ensure the table is defined in uno.object_type.';
                END IF; 

                INSERT INTO uno.node (object_type_id, accessor, label)
                    VALUES (object_type_id, {table_name}, {label});
            END $$;
            """
        ).format(
            admin_role=Identifier(ADMIN_ROLE),
            label=Literal(self.label),
            label_ident=Identifier(self.label),
            schema_name=Literal(self.schema_name),
            table_name=Literal(self.table_name),
        )
        return query.as_string()

    def insert_node_sql(self) -> str:
        """
        Generates SQL code to create a function and trigger for inserting a new node record
        when a new relational table record is inserted.

        The function constructs the SQL statements required to:
        - Create a new node with the specified label and properties.
        - Create edges for the node if any are defined.

        Returns:
            str: The generated SQL code for the insert function and trigger.
        """
        prop_key_str = ""
        prop_val_str = ""
        edge_str = ""
        # if self.edges:
        #    edge_str = "\n".join([edge.insert_edge_sql() for edge in self.edges])

        if self.properties:
            prop_key_str = ", ".join(f"{prop}: %s" for prop in self.properties.keys())
            prop_val_str = ", ".join(
                [
                    f"quote_nullable(NEW.{prop.accessor})"
                    for prop in self.properties.values()
                ]
            )

        function_string = textwrap.dedent(
            f"""
            DECLARE 
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        CREATE (v:{self.label} {{{prop_key_str}}})
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
        function_string = f"""
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.label} {{id: %s}})
                    {prop_key_str}
                $graph$) AS (a agtype);', quote_nullable(NEW.id){prop_val_str});
            BEGIN
                EXECUTE _sql;
                {edge_str}
                RETURN NEW;
            END;
            """
        return textwrap.dedent(
            self.create_sql_function(
                "update_node",
                function_string,
                include_trigger=True,
                db_function=False,
            )
        )

    def delete_node_sql(self) -> str:
        """
        Generates SQL code for creating a function and trigger to delete a node record
        from a graph database when its corresponding relational table record is deleted.

        Returns:
            str: The SQL code for creating the delete function and trigger.
        """
        function_string = f"""
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.label} {{id: %s}})
                    DETACH DELETE v
                $graph$) AS (a agtype);', quote_nullable(OLD.id));
            BEGIN
                EXECUTE _sql;
                RETURN OLD;
            END;
            """
        return textwrap.dedent(
            self.create_sql_function(
                "delete_node",
                function_string,
                operation="DELETE",
                include_trigger=True,
                db_function=False,
            )
        )

    def truncate_node_sql(self) -> str:
        """
        Generates SQL function and trigger for truncating a relation table.

        This method creates a SQL function and trigger that deletes all corresponding
        vertices for a relation table when the table is truncated. The generated SQL
        function uses the `cypher` command to match and detach delete vertices with
        the specified label.

        Returns:
            str: The SQL string to create the function and trigger.
        """
        function_string = f"""
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.label})
                    DETACH DELETE v
                $graph$) AS (a agtype);');
            BEGIN
                EXECUTE _sql;
                RETURN OLD;
            END;
            """

        return textwrap.dedent(
            self.create_sql_function(
                "truncate_node",
                function_string,
                operation="TRUNCATE",
                for_each="STATEMENT",
                include_trigger=True,
                db_function=False,
            )
        )


@dataclass
class GraphEdge(GraphBase):
    label: str
    start_node_label: str
    end_node_label: str
    accessor: str
    # properties: list[GraphProperty] = None

    def properties(self) -> list[GraphProperty]:
        """
        Retrieves a list of PropertySqlEmitter objects for the current table.

        Returns:
            list[PropertySqlEmitter]: A list of PropertySqlEmitter objects representing
            the properties of the table's columns that are not foreign keys.
        """
        props = []
        if not self.in_node:
            for column in self.table.columns:
                if not column.foreign_keys:
                    props.append(GraphProperty(table=self.table, column=column))
        return props

    def emit_sql(self) -> str:
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
        sql = self.create_edge_label_and_filter_record_sql()
        return textwrap.dedent(sql)

    def create_edge_label_and_filter_record_sql(self) -> str:
        """
        Generates a SQL statement to create a label in the AgensGraph database if it does not already exist.

        Returns:
            str: A SQL statement that checks for the existence of a label in the ag_catalog.ag_label table.
                 If the label does not exist, it creates the label and an index on the 'graph' schema_name.
        """
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

                INSERT INTO uno.edge (start_node_label, label, end_node_label, accessor)
                    VALUES ({start_node_label}, {label}, {end_node_label}, {accessor});
            END $$;
            """
            )
            .format(
                admin_role=Identifier(ADMIN_ROLE),
                label=Literal(self.label),
                label_ident=Identifier(self.label),
                start_node_label=Literal(self.start_node_label),
                end_node_label=Literal(self.end_node_label),
                accessor=Literal(self.accessor),
            )
            .as_string()
        )

    def insert_edge_sql(self) -> str:
        """
        Generates an SQL string to create a function and trigger for inserting
        a relationship between two vertices in a graph database.

        The generated SQL uses the `cypher` function to match the start and end
        vertices by their IDs and creates a relationship between them with the
        specified label and properties.

        Returns:
            str: The generated SQL string.
        """
        prop_key_str = ", ".join(f"{prop.accessor}: %s" for prop in self.properties)
        prop_val_str = ", ".join([prop.data_type for prop in self.properties])
        function_string = f"""
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.start_node.label} {{id: %s}})
                    MATCH (w:{self.end_node.label} {{id: %s}})
                    CREATE (v)-[e:{self.label} {{{prop_key_str}}}]->(w)
                $graph$) AS (a agtype);', quote_nullable(NEW.id), quote_nullable(NEW.id){prop_val_str});
            BEGIN
                EXECUTE _sql;
                RETURN NEW;
            END;
            """
        return textwrap.dedent(function_string)

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
        function_string = f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.label} {{id: %s}})
                MATCH (w:{self.end_node.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
                CREATE (v)-[e:{self.label}] ->(w)
                {prop_key_str}
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type}{prop_val_str});
            """
        return textwrap.dedent(function_string)

        return textwrap.dedent(
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
        function_string = f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.label} {{id: %s}})
                MATCH (w:{self.end_node.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type});
            """
        return textwrap.dedent(function_string)

        return textwrap.dedent(
            self.create_sql_function(
                "delete_edge",
                function_string,
                operation="UPDATE",
                include_trigger=True,
                db_function=False,
            )
        )

    def truncate_edge_sql(self) -> str:
        """
        Generates the SQL command to create a function and trigger for truncating
        relationships in a graph database.

        This method constructs a SQL string that uses the `cypher` function to
        match and delete a relationship between two vertices in a graph. The
        vertices and relationship are specified by the `start_node`,
        `end_node`, and `label` attributes of the class instance.

        Returns:
            str: The formatted SQL command string.
        """
        function_string = f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.label} {{id: %s}})
                MATCH (w:{self.end_node.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type});
            """

        return textwrap.dedent(
            self.create_sql_function(
                "truncate_edge",
                function_string,
                operation="UPDATE",
                include_trigger=True,
                for_each="STATEMENT",
                db_function=False,
            )
        )


# class Path(GraphBase):
#    from_node: Node
#    edge: Edge
#    to_node: Node
#    parent_path: "Path"
#
#    model_config = ConfigDict(arbitrary_types_allowed=True)
