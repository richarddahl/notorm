# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import Type
from dataclasses import dataclass
from datetime import datetime, date, time
from decimal import Decimal


from psycopg.sql import SQL, Identifier, Literal, Placeholder, quote

from pydantic import BaseModel, ConfigDict, computed_field

from sqlalchemy import Table, Column

from uno.fltrs.enums import (
    FilterType,
    Lookup,
    related_lookups,
    numeric_lookups,
    string_lookups,
)
from uno.utilities import convert_snake_to_capital_word
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


class PropertyDef(GraphBase):
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
class VertexDef(GraphBase):
    table_name: str
    label: str
    schema_name: str = "uno"
    column_name: str = "id"
    properties: list[PropertyDef] = None
    # lookups: list[Lookup] = related_lookups

    # def label(self) -> str:
    #    return convert_snake_to_capital_word(self.table.name)
    #
    #    def column(self) -> Column:
    #        return self.table.columns[self.column_name]

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
        sql = self.create_vertex_label_sql()
        # sql += f"\n{self.insert_vertex_sql()}"
        # sql += f"\n{self.update_vertext_sql()}"
        # sql += f"\n{self.delete_vertext_sql()}"
        # sql += f"\n{self.truncate_vertext_sql()}"
        # sql += f"\n{self.create_filter_field_sql()}"
        return textwrap.dedent(sql)

    def create_vertex_label_sql(self) -> str:
        query = SQL(
            """
            DO $$
            BEGIN
                SET ROLE {};
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label
                WHERE name = {}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {});
                    EXECUTE format('CREATE INDEX ON graph.{} (id);');
                END IF;
            END $$;
            """
        ).format(
            Identifier(ADMIN_ROLE),
            Literal(self.label),
            Literal(self.label),
            Identifier(self.label),
        )
        return query.as_string()

    def insert_vertex_sql(self) -> str:
        """
        Generates SQL code to create a function and trigger for inserting a new vertex record
        when a new relational table record is inserted.

        The function constructs the SQL statements required to:
        - Create a new vertex with the specified label and properties.
        - Create edges for the vertex if any are defined.

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
            "insert_vertex",
            function_string,
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )

    def update_vertext_sql(self) -> str:
        """
        Generates SQL code for creating an update function and trigger for a vertex record.

        This method constructs the SQL code necessary to update an existing vertex record
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
                "update_vertex",
                function_string,
                include_trigger=True,
                db_function=False,
            )
        )

    def delete_vertext_sql(self) -> str:
        """
        Generates SQL code for creating a function and trigger to delete a vertex record
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
                "delete_vertex",
                function_string,
                operation="DELETE",
                include_trigger=True,
                db_function=False,
            )
        )

    def truncate_vertext_sql(self) -> str:
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
                "truncate_vertex",
                function_string,
                operation="TRUNCATE",
                for_each="STATEMENT",
                include_trigger=True,
                db_function=False,
            )
        )


class EdgeDef(GraphBase):
    label: str
    table: Table
    to_column: Column
    start_vertex_label: str
    end_vertex_label: str
    lookups: list[Lookup] = related_lookups
    in_vertex: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def accessor(self) -> str:
        return self.to_column.name

    def properties(self) -> list[PropertyDef]:
        """
        Retrieves a list of PropertySqlEmitter objects for the current table.

        Returns:
            list[PropertySqlEmitter]: A list of PropertySqlEmitter objects representing
            the properties of the table's columns that are not foreign keys.
        """
        props = []
        if not self.in_vertex:
            for column in self.table.columns:
                if not column.foreign_keys:
                    props.append(PropertyDef(table=self.table, column=column))
        return props

    def create_label_sql(self) -> str:
        """
        Generates a SQL statement to create a label in the AgensGraph database if it does not already exist.

        Returns:
            str: A SQL statement that checks for the existence of a label in the ag_catalog.ag_label table.
                 If the label does not exist, it creates the label and an index on the 'graph' schema_name.
        """
        return textwrap.dedent(
            f"""
            DO $$
            BEGIN
                SET ROLE {settings.DB_NAME}_admin;
                IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label
                    WHERE name = '{self.label}') THEN
                        PERFORM ag_catalog.create_elabel('graph', '{self.label}');
                        CREATE INDEX ON graph."{self.label}" (start_id, end_id);
                END IF;
            END $$;
            """
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
                    MATCH (v:{self.start_vertex.label} {{id: %s}})
                    MATCH (w:{self.end_vertex.label} {{id: %s}})
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
        - Matches a start vertex and an end vertex based on their labels and IDs.
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
                MATCH (v:{self.start_vertex.label} {{id: %s}})
                MATCH (w:{self.end_vertex.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
                CREATE (v)-[e:{self.label}] ->(w)
                {prop_key_str}
            $graph$) AS (e agtype);', {self.start_vertex.data_type}, {self.end_vertex.data_type}{prop_val_str});
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
                MATCH (v:{self.start_vertex.label} {{id: %s}})
                MATCH (w:{self.end_vertex.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_vertex.data_type}, {self.end_vertex.data_type});
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
        vertices and relationship are specified by the `start_vertex`,
        `end_vertex`, and `label` attributes of the class instance.

        Returns:
            str: The formatted SQL command string.
        """
        function_string = f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_vertex.label} {{id: %s}})
                MATCH (w:{self.end_vertex.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_vertex.data_type}, {self.end_vertex.data_type});
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
#    from_vertex: Vertex
#    edge: Edge
#    to_vertex: Vertex
#    parent_path: "Path"
#
#    model_config = ConfigDict(arbitrary_types_allowed=True)
