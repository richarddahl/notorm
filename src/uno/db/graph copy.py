# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import ClassVar, Type

from datetime import datetime, date, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field
from pydantic.dataclasses import dataclass, Field

from sqlalchemy import Table, Column

from uno.utilities import convert_snake_to_capital_word
from uno.fltrs.enums import (
    GraphType,
    EdgeDirection,
    Lookup,
    related_lookups,
    numeric_lookups,
    string_lookups,
)
from uno.db.sql_emitters import SQLEmitter


class Property(BaseModel):
    # accessor: str <- computed_field
    # data_type: str <- computed_field
    # lookups: Lookup <- computed_field
    # label: str <- computed_field

    column: Column

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def accessor(self) -> str:
        return self.column.name

    @computed_field
    def data_type(self) -> str:
        """Get the column type for a given column"""
        return f"quote_nullable(NEW.{self.accessor})"

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

    def create_filter_field_sql(self) -> str:
        """
        Generates the SQL statement to create a filter field and its associated table type.

        This method constructs and returns a SQL statement that performs the following operation:
        1. Inserts a new filter field into the `uno.filter_field` table with the specified attributes.
           - If a conflict occurs on the combination of `label` and `graph_type`, the insertion is ignored.
        2. Inserts a relationship between the filter field and a table type into the `uno.filter_field_ObjectType` table.
           - The relationship is defined by the `filterfield_id`, `object_type_id`, and `direction`.
           - If a conflict occurs, the insertion is ignored.

        Returns:
            str: The SQL statement for creating the filter field and its associated table type.
        """
        return textwrap.dedent(
            f"""
            -- Create the filter field
            INSERT INTO uno.filter_field (
                accessor,
                label,
                data_type,
                graph_type,
                lookups
            )
            VALUES (
                '{self.accessor}',
                '{self.label}',
                '{self.column.type}',
                '{GraphType.PROPERTY.name}',
                ARRAY{self.lookups}::uno.lookup[]
            ) ON CONFLICT (label, graph_type) DO NOTHING;

            INSERT INTO uno.filter_field_ObjectType (
                filterfield_id,
                object_type_id,
                direction
            )
            SELECT f.id, t.id, '{EdgeDirection.FROM.name}'
            FROM uno.filter_field f
            JOIN uno.object_type t
            ON f.label = '{self.label}'
            AND f.graph_type = '{GraphType.PROPERTY.name}'
            AND t.name = '{self.table_name}'
            AND t.schema = '{self.schema}'
            ON CONFLICT DO NOTHING;
            """
        )


class GraphLabelSQL(SQLEmitter):
    # label: str <- computed_field

    @computed_field
    def label(self) -> str:
        return convert_snake_to_capital_word(self.table_name)

    def emit_sql(self) -> str:
        """
        Generates SQL code to create a vertex label and its corresponding index
        in the AgensGraph database if it does not already exist.

        Returns:
            str: The SQL code to create the vertex label and index.
        """
        self.label = convert_snake_to_capital_word(self.table_name)
        return textwrap.dedent(
            f"""
            -- Create the vertex label and index
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label
                WHERE name = '{self.label}') THEN
                    PERFORM ag_catalog.create_vlabel('graph', '{self.label}');
                    CREATE INDEX ON graph."{self.label}" (id);
                END IF;
            END $$;
            """
        )


@dataclass
class InsertVertexSQL(SQLEmitter):
    edges: list["Edge"] = Field(default_factory=list)
    properties: list["Property"] = Field(default_factory=list)

    def emit_sql(self) -> str:
        """
        Generates SQL code to create a function and trigger for inserting a new vertex record
        when a new relational table record is inserted.

        The function constructs the SQL statements required to:
        - Create a new vertex with the specified label and properties.
        - Create edges for the vertex if any are defined.

        Returns:
            str: The generated SQL code for the insert function and trigger.
        """
        self.label = convert_snake_to_capital_word(self.table_name)
        prop_key_str = ""
        prop_val_str = ""
        edge_str = ""
        if self.edges:
            edge_str = "\n".join(
                [edge.create_insert_function_and_trigger_sql() for edge in self.edges]
            )

        if self.properties:
            prop_key_str = ", ".join(f"{prop.accessor}: %s" for prop in self.properties)
            prop_val_str = ", " + ", ".join(
                [prop.data_type for prop in self.properties]
            )
        sql = textwrap.dedent(
            f"""
            -- Create the insert vertex function and trigger
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                CREATE (v:{self.label} {{{prop_key_str}}})
            $$) AS (a agtype);'{prop_val_str});
            -- Create the edges for the vertex on insert
            {edge_str}
            RETURN NEW;
            """
        )
        return textwrap.dedent(
            self.create_sql_function(
                "insert_vertex",
                sql,
                operation="INSERT",
                include_trigger=True,
                db_function=False,
            )
        )


class Vertex(BaseModel):
    # label: str <- computed_field
    # accessor: str <- computed_field
    # data_type: str <- computed_field
    # properties: list[PropertySqlEmitter] | None <- computed_field
    # edges: list[EdgeSqlEmitter] | None <- computed_field

    sql_emitters: ClassVar[list[str, Type[SQLEmitter]]] = [
        GraphLabelSQL,
        InsertVertexSQL,
    ]

    table: Table
    column_name: str
    # lookups: list[Lookup] = related_lookups

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def label(self) -> str:
        return convert_snake_to_capital_word(self.table.name)

    @computed_field
    def accessor(self) -> str:
        return self.table.name

    @computed_field
    def column(self) -> Column:
        return self.table.columns[self.column_name]

    @computed_field
    def data_type(self) -> str:
        """
        Generates a string representing a SQL expression to cast a column to its specified type.

        Returns:
            str: A SQL expression string in the format "quote_nullable(NEW.<column_name>::<column_type>)".
        """
        return f"quote_nullable(NEW.{self.column.name}::{self.column.type})"

    @computed_field
    def properties(self) -> list[Property] | None:
        """
        Generates a list of PropertySqlEmitter instances for each column in the table.

        Returns:
            list[PropertySqlEmitter] | None: A list of PropertySqlEmitter instances or None if no columns are present.
        """
        props = []
        for column in self.table.columns:
            props.append(Property(table=self.table, column=column))
        return props

    @computed_field
    def edges(self) -> list["Edge"] | None:
        """
        Generates a list of EdgeSqlEmitter objects representing the foreign key relationships
        of the table associated with this instance.

        Returns:
            list[EdgeSqlEmitter] | None: A list of EdgeSqlEmitter objects if foreign keys are present,
            otherwise None.
        """
        edges = []
        for fk in self.table.foreign_keys:
            edges.append(
                Edge(
                    table=self.table,
                    to_column=fk.parent,
                    start_vertex=self,
                    end_vertex=Vertex(
                        table=fk.column.table,
                        column=fk.parent,
                    ),
                )
            )
        return edges

    # Functions to generate sql statements

    def create_sql(self) -> str:
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
        sql = self.create_label_sql()
        # sql += f"\n{self.create_insert_function_and_trigger_sql()}"
        # sql += f"\n{self.create_update_function_and_trigger_sql()}"
        # sql += f"\n{self.create_delete_function_and_trigger_sql()}"
        # sql += f"\n{self.create_truncate_function_and_trigger_sql()}"
        # sql += f"\n{self.create_filter_field_sql()}"
        return textwrap.dedent(sql)

    def create_filter_field_sql(self) -> str:
        """
        Generates the SQL statement to create a filter field and associate it with a table type.

        The SQL statement performs the following operations:
        1. Inserts a new filter field into the `uno.filter_field` table with the specified attributes.
           - If a conflict occurs on the combination of `label` and `graph_type`, the insertion is ignored.
        2. Inserts a new association between the filter field and a table type into the `uno.filter_field_ObjectType` table.
           - The association includes the filter field ID, table type ID, and direction.
           - If a conflict occurs, the insertion is ignored.

        Returns:
            str: The generated SQL statement.
        """
        return textwrap.dedent(
            f"""
            -- Create the filter field
            INSERT INTO uno.filter_field (
                accessor,
                label,
                data_type,
                graph_type,
                lookups
            )
            VALUES (
                '{self.accessor}',
                '{self.label}',
                '{self.column.type}',
                '{GraphType.VERTEX.name}',
                ARRAY{self.lookups}::uno.lookup[]
            ) ON CONFLICT (label, graph_type) DO NOTHING;

            INSERT INTO uno.filter_field_ObjectType (
                filterfield_id,
                object_type_id,
                direction
            )
            SELECT f.id, t.id, '{EdgeDirection.FROM.name}'
            FROM uno.filter_field f
            JOIN uno.object_type t
            ON f.label = '{self.label}'
            AND f.graph_type = '{GraphType.VERTEX.name}'
            AND t.name = '{self.table_name}'
            AND t.schema = '{self.schema}'
            ON CONFLICT DO NOTHING;
            """
        )

    def create_update_function_and_trigger_sql(self) -> str:
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
            edge_str = "\n".join(
                [edge.create_update_function_and_trigger_sql() for edge in self.edges]
            )
        if self.properties:
            prop_key_str = "SET " + ", ".join(
                f"v.{prop.accessor} = %s" for prop in self.properties
            )
            prop_val_str = ", " + ", ".join(
                [prop.data_type for prop in self.properties]
            )
        sql = textwrap.dedent(
            f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                MATCH (v:{self.label} {{id: %s}})
                {prop_key_str}
            $$) AS (a agtype);', quote_nullable(NEW.id){prop_val_str});
            {edge_str}
            RETURN NEW;
            """
        )
        return textwrap.dedent(
            self.create_sql_function(
                "update_vertex",
                sql,
                include_trigger=True,
            )
        )

    def create_delete_function_and_trigger_sql(self) -> str:
        """
        Generates SQL code for creating a function and trigger to delete a vertex record
        from a graph database when its corresponding relational table record is deleted.

        Returns:
            str: The SQL code for creating the delete function and trigger.
        """
        sql = textwrap.dedent(
            f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                MATCH (v:{self.label} {{id: %s}})
                DETACH DELETE v
            $$) AS (a agtype);', quote_nullable(OLD.id));
            RETURN OLD;
            """
        )
        return textwrap.dedent(
            self.create_sql_function(
                "delete_vertex",
                sql,
                operation="DELETE",
                include_trigger=True,
            )
        )

    def create_truncate_function_and_trigger_sql(self) -> str:
        """
        Generates SQL function and trigger for truncating a relation table.

        This method creates a SQL function and trigger that deletes all corresponding
        vertices for a relation table when the table is truncated. The generated SQL
        function uses the `cypher` command to match and detach delete vertices with
        the specified label.

        Returns:
            str: The SQL string to create the function and trigger.
        """
        sql = textwrap.dedent(
            f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                MATCH (v:{self.label})
                DETACH DELETE v
            $$) AS (a agtype);');
            RETURN OLD;
            """
        )
        return textwrap.dedent(
            self.create_sql_function(
                "truncate_vertex",
                sql,
                operation="truncate",
                for_each="STATEMENT",
                include_trigger=True,
            )
        )


class Edge(BaseModel):
    """
    EdgeSqlEmitter is a class that represents the schema for an edge in a graph database. It extends the TableManager class and includes additional attributes and methods specific to edges.
    Attributes:
        table (Table): The table associated with the edge.
        to_column (Column): The column representing the edge.
        start_vertex (VertexSqlEmitter): The schema of the start vertex.
        end_vertex (VertexSqlEmitter): The schema of the end vertex.
        lookups (list[Lookup]): A list of related lookups.
        in_vertex (bool): A flag indicating if the edge is in a vertex. Defaults to True.
        model_config (dict): Configuration for the model, allowing arbitrary types.
    Methods:
        label() -> str:
            Computes and returns the label for the edge.
        accessor() -> str:
            Computes and returns the accessor for the edge.
        properties() -> list["PropertySqlEmitter"]:
        create_sql() -> str:
        create_filter_field_sql() -> str:
            Returns the SQL to insert the edge as a filter field and creates the filterfield_ObjectType records for the edge.
        create_label_sql() -> str:
        create_insert_function_and_trigger_sql() -> str:
            Generates an SQL string to create a function and trigger for inserting a relationship between two vertices in a graph database.
        create_update_function_and_trigger_sql() -> str:
        create_delete_function_and_trigger_sql() -> str:
        create_truncate_function_and_trigger_sql() -> str:
            Generates the SQL command to create a function and trigger for truncating relationships in a graph database.
    """

    # label: str <- computed_field
    # accessor: str <- computed_field
    # properties: list[PropertySqlEmitter] <- computed_field

    table: Table
    to_column: Column
    start_vertex: Vertex
    end_vertex: Vertex
    lookups: list[Lookup] = related_lookups
    in_vertex: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def label(self) -> str:
        return self.to_column.info.get("edge")

    @computed_field
    def accessor(self) -> str:
        return self.to_column.name

    @computed_field
    def properties(self) -> list[Property]:
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
                    props.append(Property(table=self.table, column=column))
        return props

    # Functions to generate sql statements

    def create_sql(self) -> str:
        """
        Generates the complete SQL string for creating various SQL functions and triggers.

        This method constructs SQL statements for creating label SQL, insert, update, delete,
        and truncate functions and their respective triggers. It also includes SQL for
        filtering fields. The generated SQL is dedented before being returned.

        Returns:
            str: The complete SQL string for creating the necessary functions and triggers.
        """
        sql = self.create_label_sql()
        sql += self.create_sql_function(
            "insert_edge",
            self.create_insert_function_and_trigger_sql(),
            operation="INSERT",
            for_each="ROW",
            include_trigger=True,
        )
        sql += self.create_sql_function(
            "update_edge",
            self.create_update_function_and_trigger_sql(),
            operation="UPDATE",
            for_each="ROW",
            include_trigger=True,
        )
        sql += self.create_sql_function(
            "delete_edge",
            self.create_delete_function_and_trigger_sql(),
            operation="DELETE",
            for_each="ROW",
            include_trigger=True,
        )
        sql += self.create_sql_function(
            "truncate_edge",
            self.create_truncate_function_and_trigger_sql(),
            operation="TRUNCATE",
            for_each="STATEMENT",
            include_trigger=True,
        )
        sql += self.create_filter_field_sql()
        return textwrap.dedent(sql)

    def create_filter_field_sql(self) -> str:
        """Returns the sql to insert the Edge as a filter field

        Additionally, it creates the filterfield_ObjectType records for the edge
        for both the start and end vertices.
        """
        return textwrap.dedent(
            f"""
            -- Create the filter field
            INSERT INTO uno.filter_field (
                accessor,
                label,
                data_type,
                graph_type,
                lookups
            )
            VALUES (
                '{self.accessor}',
                '{self.label}',
                '{self.to_column.type}',
                '{GraphType.EDGE.name}',
                ARRAY{self.lookups}::uno.lookup[]
            ) ON CONFLICT (label, graph_type) DO NOTHING;

            INSERT INTO uno.filter_field_ObjectType (
                filterfield_id,
                object_type_id,
                direction
            )
            SELECT f.id, t.id, '{EdgeDirection.FROM.name}'
            FROM uno.filter_field f
            JOIN uno.object_type t
            ON f.label = '{self.label}'
            AND f.graph_type = '{GraphType.EDGE.name}'
            AND t.name = '{self.table_name}'
            AND t.schema = '{self.schema}'
            ON CONFLICT DO NOTHING;
    
            INSERT INTO uno.filter_field_ObjectType (
                filterfield_id,
                object_type_id,
                direction
            )
            SELECT f.id, t.id, '{EdgeDirection.TO.name}'
            FROM uno.filter_field f
            JOIN uno.object_type t
            ON f.label = '{self.label}'
            AND f.graph_type = '{GraphType.EDGE.name}'
            AND t.name = '{self.end_vertex.table.name}'
            AND t.schema = '{self.end_vertex.table.schema}'
            ON CONFLICT DO NOTHING;
            """
        )

    def create_label_sql(self) -> str:
        """
        Generates a SQL statement to create a label in the AgensGraph database if it does not already exist.

        Returns:
            str: A SQL statement that checks for the existence of a label in the ag_catalog.ag_label table.
                 If the label does not exist, it creates the label and an index on the 'graph' schema.
        """
        return textwrap.dedent(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label WHERE name = '{self.label}') THEN
                    PERFORM ag_catalog.create_elabel('graph', '{self.label}');
                    CREATE INDEX ON graph."{self.label}" (start_id, end_id);
                END IF;
            END $$;
            """
        )

    def create_insert_function_and_trigger_sql(self) -> str:
        """
        Generates an SQL string to create a function and trigger for inserting
        a relationship between two vertices in a graph database.

        The generated SQL uses the `cypher` function to match the start and end
        vertices by their IDs and creates a relationship between them with the
        specified label and properties.

        Returns:
            str: The generated SQL string.
        """
        prop_key_str = ""
        prop_val_str = ""
        if self.properties:
            prop_key_str = ", ".join(f"{prop.accessor}: %s" for prop in self.properties)
            prop_val_str = ", " + ", ".join(
                [prop.data_type for prop in self.properties]
            )
        sql = f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                MATCH (v:{self.start_vertex.label} {{id: %s}})
                MATCH (w:{self.end_vertex.label} {{id: %s}})
                CREATE (v)-[e:{self.label} {{{prop_key_str}}}] ->(w)
            $$) AS (e agtype);', {self.start_vertex.data_type}, {self.end_vertex.data_type}{prop_val_str});
            """
        # if not self.in_vertex:
        #    sql += "\nRETURN NEW;"
        return textwrap.dedent(sql)

    def create_update_function_and_trigger_sql(self) -> str:
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
        return textwrap.dedent(
            f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                MATCH (v:{self.start_vertex.label} {{id: %s}})
                MATCH (w:{self.end_vertex.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
                CREATE (v)-[e:{self.label}] ->(w)
                {prop_key_str}
            $$) AS (e agtype);', {self.start_vertex.data_type}, {self.end_vertex.data_type}{prop_val_str});
            """
        )

    def create_delete_function_and_trigger_sql(self) -> str:
        """
        Generates the SQL string for creating a delete function and trigger.

        This function constructs an SQL command that uses the `cypher` function to
        delete a relationship between two vertices in a graph database. The vertices
        and the relationship are specified by the attributes of the class instance.

        Returns:
            str: The formatted SQL string for deleting the specified relationship.
        """
        return textwrap.dedent(
            f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                MATCH (v:{self.start_vertex.label} {{id: %s}})
                MATCH (w:{self.end_vertex.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
            $$) AS (e agtype);', {self.start_vertex.data_type}, {self.end_vertex.data_type});
            """
        )

    def create_truncate_function_and_trigger_sql(self) -> str:
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
        return textwrap.dedent(
            f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$
                MATCH (v:{self.start_vertex.label} {{id: %s}})
                MATCH (w:{self.end_vertex.label} {{id: %s}})
                MATCH (v)-[o:{self.label}] ->(w)
                DELETE o
            $$) AS (e agtype);', {self.start_vertex.data_type}, {self.end_vertex.data_type});
            """
        )
