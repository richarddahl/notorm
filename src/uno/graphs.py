# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from dataclasses import dataclass, field
from datetime import datetime, date, time
from decimal import Decimal
from typing import Any


from psycopg.sql import SQL, Identifier, Literal

from pydantic import BaseModel, ConfigDict, computed_field


from uno.fltr.enums import (
    DataType,
    Lookup,
    related_lookups,
    numeric_lookups,
    string_lookups,
)
from uno.config import settings
from uno.utilities import convert_snake_to_title

ADMIN_ROLE = f"{settings.DB_NAME}_admin"


class GraphEdgeDef(BaseModel):
    name: str
    destination_table_name: str
    accessor: str
    secondary_table_name: str = None


class GraphBase(BaseModel):
    klass: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    def table_name(self) -> str:
        return self.klass.__tablename__

    @computed_field
    def schema_name(self) -> str:
        return self.klass.__table__.schema

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
    # table_name: str <- from GraphBase
    # schema_name: str <- from GraphBase
    # name: str <- from GraphBase
    accessor: str
    data_type: str

    @computed_field
    def display(self) -> str:
        return convert_snake_to_title(self.name)

    @computed_field
    def lookups(self) -> Lookup:
        if self.data_type in [
            "int",
            "float",
            "Decimal",
            "datetime",
            "date",
            "time",
        ]:
            return numeric_lookups
        return string_lookups

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
        sql = self.create_filter_record_sql()
        return textwrap.dedent(sql)

    def create_filter_record_sql(self) -> str:
        """ """
        return (
            SQL(
                """
                DO $$
                BEGIN
                    INSERT INTO uno.filter(filter_type, data_type, table_name, name, accessor, lookups)
                        VALUES ({filter_type}, {data_type}, {table_name}, {name}, {accessor}, {lookups});
                END $$;
                """
            )
            .format(
                admin_role=Identifier(ADMIN_ROLE),
                filter_type=Literal("PROPERTY"),
                data_type=Literal(self.data_type),
                table_name=Literal(self.table_name),
                name=Literal(self.name),
                label_ident=Identifier(self.name),
                accessor=Literal(self.accessor),
                lookups=Literal(self.lookups),
            )
            .as_string()
        )


class GraphNode(GraphBase):
    # table_name: str <- from GraphBase
    # schema_name: str <- from GraphBase
    # name: str <- from GraphBase

    @computed_field
    def properties(self) -> dict[str, GraphProperty]:
        from uno.db.tables import Base

        klass = Base.registry.get(self.table_name)
        return klass.graph_properties

    def emit_sql(self) -> str:
        """
        Generates a complete SQL script by combining various SQL
        components.

        This method constructs a SQL script by sequentially appending
        the results of several helper methods that generate specific
        parts of the SQL script.
        The final script includes SQL for creating labels, insert
        functions and triggers, update functions and triggers,
        delete functions and triggers, truncate functions and
        triggers, and filter fields.

        Returns:
            str: The complete SQL script as a single string.
        """
        sql = self.create_node_label()
        # sql += f"\n{self.insert_node_sql()}"
        # sql += f"\n{self.update_nodet_sql()}"
        # sql += f"\n{self.delete_nodet_sql()}"
        # sql += f"\n{self.truncate_nodet_sql()}"
        # sql += f"\n{self.create_filter_field_sql()}"
        return textwrap.dedent(sql)

    def create_node_label(self) -> str:
        query = SQL(
            """
            DO $$
            BEGIN
                SET ROLE {admin_role};
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label
                WHERE name = {name}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {name});
                    EXECUTE format('CREATE INDEX ON graph.{label_ident} (id);');
                END IF;
            END $$;
            """
        ).format(
            admin_role=Identifier(ADMIN_ROLE),
            name=Literal(self.name),
            label_ident=Identifier(self.name),
            schema_name=Literal(self.schema_name),
            table_name=Literal(self.table_name),
        )
        return query.as_string()

    def insert_node_sql(self) -> str:
        """
        Generates SQL code to create a function and trigger for inserting a new node record
        when a new relational table record is inserted.

        The function constructs the SQL statements required to:
        - Create a new node with the specified name and properties.
        - Create edges for the node if any are defined.

        Returns:
            str: The generated SQL code for the insert function and trigger.
        """
        prop_key_str = ""
        prop_val_str = ""

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
                        CREATE (v:{self.name} {{{prop_key_str}}})
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
                    MATCH (v:{self.name} {{id: %s}})
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
                    MATCH (v:{self.name} {{id: %s}})
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
        the specified name.

        Returns:
            str: The SQL string to create the function and trigger.
        """
        function_string = f"""
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


class GraphEdge(GraphBase):
    # table_name: str <- from GraphBase
    # schema_name: str <- from GraphBase
    # name: str <- from GraphBase
    destination_table_name: str
    accessor: str
    secondary_table_name: str = None
    lookups: list[Lookup] = related_lookups
    # display: str <- computed_field
    # properties: dict[str, GraphProperty] <- computed_field
    # nullable: bool = False <- computed_field

    @computed_field
    def display(self) -> str:
        return f"{convert_snake_to_title(self.name)} ({convert_snake_to_title(self.destination_table_name)})"

    @computed_field
    def properties(self) -> dict[str, GraphProperty]:
        if not self.secondary_table_name:
            return {}
        from uno.db.tables import Base

        table = Base.metadata.tables[self.secondary_table_name]
        props = {}
        for column in table.columns:
            if column.foreign_keys and not column.primary_key:
                continue
            props.update(
                {
                    column.name: GraphProperty(
                        table_name=self.table_name,
                        name=convert_snake_to_title(column.name),
                        accessor=column.name,
                        data_type=column.type.python_type.__name__,
                    )
                }
            )
        return props

    def emit_sql(self) -> str:
        sql = self.create_edge_label_and_filter_record_sql()
        return textwrap.dedent(sql)

    def create_edge_label_and_filter_record_sql(self) -> str:
        return (
            SQL(
                """
                DO $$
                BEGIN
                    SET ROLE {admin_role};
                    IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_label
                        WHERE name = {name}) THEN
                            PERFORM ag_catalog.create_elabel('graph', {name});
                            CREATE INDEX ON graph.{label_ident} (start_id, end_id);
                    END IF;
                
                    INSERT INTO uno.filter(filter_type, data_type, table_name, name, destination_table_name, accessor, lookups)
                        VALUES ({filter_type}, {data_type}, {table_name}, {name}, {destination_table_name}, {accessor}, {lookups});
                END $$;
                """
            )
            .format(
                admin_role=Identifier(ADMIN_ROLE),
                filter_type=Literal("EDGE"),
                data_type=Literal("object"),
                table_name=Literal(self.table_name),
                name=Literal(self.name),
                destination_table_name=Literal(self.destination_table_name),
                label_ident=Identifier(self.name),
                accessor=Literal(self.accessor),
                lookups=Literal(self.lookups),
            )
            .as_string()
        )

    def insert_edge_sql(self) -> str:
        """
        Generates an SQL string to create a function and trigger for inserting
        a relationship between two vertices in a graph database.

        The generated SQL uses the `cypher` function to match the start and end
        vertices by their IDs and creates a relationship between them with the
        specified name and properties.

        Returns:
            str: The generated SQL string.
        """
        prop_key_str = ", ".join(f"{prop.accessor}: %s" for prop in self.properties)
        prop_val_str = ", ".join([prop.data_type for prop in self.properties])
        function_string = f"""
            DECLARE
                _sql TEXT := FORMAT('SELECT * FROM cypher(''graph'', $graph$
                    MATCH (v:{self.start_node.name} {{id: %s}})
                    MATCH (w:{self.end_node.name} {{id: %s}})
                    CREATE (v)-[e:{self.name} {{{prop_key_str}}}]->(w)
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
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
                DELETE o
                CREATE (v)-[e:{self.name}] ->(w)
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
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
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
        `end_node`, and `name` attributes of the class instance.

        Returns:
            str: The formatted SQL command string.
        """
        function_string = f"""
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
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
