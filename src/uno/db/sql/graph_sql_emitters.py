# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json

from psycopg.sql import SQL, Identifier, Literal, Placeholder

from pydantic import computed_field

from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from uno.db.sql.sql_emitter import (
    TableSQLEmitter,
    DB_SCHEMA,
    ADMIN_ROLE,
    WRITER_ROLE,
)
from uno.val.enums import (
    Lookup,
    numeric_lookups,
    text_lookups,
    object_lookups,
    boolean_lookups,
)
from uno.utilities import (
    convert_snake_to_camel,
    convert_snake_to_title,
)


class GraphSQLEmitter(TableSQLEmitter):

    @computed_field
    def source_meta_type(self) -> str:
        return self.klass.__tablename__


class PropertySQLEmitter(GraphSQLEmitter):
    # klass: type[DeclarativeBase] <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    accessor: str
    data_type: str
    # display: str <- computed_field
    # destination_meta_type: str <- computed_field
    # lookups: Lookup <- computed_field

    @computed_field
    def display(self) -> str:
        return convert_snake_to_title(self.accessor)

    @computed_field
    def destination_meta_type(self) -> str:
        return self.source_meta_type

    @computed_field
    def lookups(self) -> Lookup:
        if self.data_type in [
            "datetime",
            "date",
            "Decimal",
            "int",
            "time",
        ]:
            return numeric_lookups
        if self.data_type in ["str"]:
            return text_lookups
        if self.data_type in ["bool"]:
            return boolean_lookups
        return object_lookups

    def emit_sql(self, conn: Connection) -> None:
        return
        conn.execute(
            text(
                SQL(
                    """
            DO $$
            BEGIN
                SET ROLE {admin_role};
                INSERT INTO filter (
                    display,
                    data_type,
                    source_meta_type,
                    destination_meta_type,
                    accessor,
                    lookups
                )
                VALUES (
                    {display},
                    {data_type},
                    {source_meta_type},
                    {destination_meta_type},
                    {accessor},
                    {lookups}
                )
                RETURNING id;
            END $$;
            """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    db_schema=DB_SCHEMA,
                    display=Literal(self.display),
                    data_type=Literal(self.data_type),
                    source_meta_type=Literal(self.source_meta_type),
                    destination_meta_type=Literal(self.destination_meta_type),
                    accessor=Literal(self.accessor),
                    lookups=Literal(self.lookups),
                )
                .as_string()
            )
        )


class NodeSQLEmitter(GraphSQLEmitter):
    # klass: type[DeclarativeBase] <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    # properties: dict[str, PropertySQLEmitter] <- computed_field
    # label: str <- computed_field

    @computed_field
    def properties(self) -> dict[str, PropertySQLEmitter]:
        return self.klass.graph_properties

    @computed_field
    def label(self) -> str:
        return convert_snake_to_camel(self.source_meta_type)

    def emit_sql(self, conn: Connection) -> None:
        self.create_node_label(conn)
        self.insert_node(conn)
        # self.update_node(conn)
        # self.delete_node(conn)
        # self.truncate_node(conn)
        # self.create_filter_field(conn)

    def create_node_label(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            DO $$
            BEGIN
                SET ROLE {admin_role};
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label
                WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {label});
                    EXECUTE format('CREATE INDEX ON graph.{label_ident} (id);');
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
        )

    def insert_node(self, conn: Connection) -> None:
        return
        prop_str = " ".join(
            SQL('{accessor}: "NEW".{value}')
            .format(
                accessor=Literal(prop.accessor),
                value=Literal(prop.accessor),
            )
            .as_string()
            for prop in self.properties.values()
        )

        function_string = (
            SQL(
                """
            BEGIN
                SELECT * FROM cypher('graph', $graph$
                    CREATE (v:{label} {{{prop_str}}})
                $graph$) AS (a agtype);
                RETURN NEW; 
            END;
            """
            )
            .format(label=SQL(self.label), prop_str=SQL(prop_str))
            .as_string()
        )

        conn.execute(
            text(
                self.create_sql_function(
                    "insert_node",
                    function_string,
                    operation="INSERT",
                    include_trigger=True,
                    db_function=False,
                )
            )
        )

    def update_node(self) -> None:
        """
        Generates SQL code for creating an update function and trigger for a graph_node record.

        This method constructs the SQL code necessary to update an existing graph_node record
        in a graph database when its corresponding relational table record is updated. The
        generated SQL includes the necessary property updates and edge updates if they exist.

        Returns:
            str: The generated SQL code as a string.
        """
        prop_key_str = ""
        prop_val_str = ""
        edge_str = ""
        if self.graph_edges:
            edge_str = "\n".join([edge.update_edge_sql() for edge in self.graph_edges])
        if self.properties:
            prop_key_str = "SET " + ", ".join(
                f"v.{prop.accessor} = %s" for prop in self.properties
            )
            prop_val_str = ", " + ", ".join(
                [prop.data_type for prop in self.properties]
            )
        function_string = SQL(
            """
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
        ).format(
            prop_key_str=SQL(prop_key_str),
            prop_val_str=SQL(prop_val_str),
            edge_str=SQL(edge_str),
        )
        return self.create_sql_function(
            "update_node",
            function_string,
            include_trigger=True,
            db_function=False,
        )

    def delete_node(self) -> None:
        """
        Generates SQL code for creating a function and trigger to delete a graph_node record
        from a graph database when its corresponding relational table record is deleted.

        Returns:
            str: The SQL code for creating the delete function and trigger.
        """
        function_string = """
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
        return self.create_sql_function(
            "delete_node",
            function_string,
            operation="DELETE",
            include_trigger=True,
            db_function=False,
        )

    def truncate_node(self) -> None:
        """
        Generates SQL function and trigger for truncating a relation table.

        This method creates a SQL function and trigger that deletes all corresponding
        vertices for a relation table when the table is truncated. The generated SQL
        function uses the `cypher` command to match and detach delete vertices with
        the specified name.

        Returns:
            str: The SQL string to create the function and trigger.
        """
        function_string = """
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

        return self.create_sql_function(
            "truncate_node",
            function_string,
            operation="TRUNCATE",
            for_each="STATEMENT",
            include_trigger=True,
            db_function=False,
        )


class EdgeSQLEmitter(GraphSQLEmitter):
    # klass: type[DeclarativeBase] <- from GraphBase
    # source_meta_type: str <- computed_field from GraphBase
    label: str
    destination_meta_type: str
    accessor: str
    secondary: Table | None
    lookups: list[Lookup] = object_lookups
    # properties: dict[str, PropertySQLEmitter] <- computed_field
    # display: str <- computed_field
    # nullable: bool = False <- computed_field

    @computed_field
    def display(self) -> str:
        return f"{convert_snake_to_title(self.accessor)} ({convert_snake_to_title(self.destination_meta_type)})"

    @computed_field
    def source_meta_type(self) -> str:
        return self.klass.__table__.name

    @computed_field
    def properties(self) -> dict[str, PropertySQLEmitter]:
        if not isinstance(self.secondary, Table):
            return {}
        props = {}
        for column in self.secondary.columns:
            if column.foreign_keys and column.primary_key:
                continue
            data_type = column.type.python_type.__name__
            for base in self.klass.registry.mappers:
                if base.class_.__tablename__ == self.secondary.name:
                    klass = base.class_
                    break
            props.update(
                {
                    column.name: PropertySQLEmitter(
                        klass=klass,
                        accessor=column.name,
                        data_type=data_type,
                    )
                }
            )
        return props

    def emit_sql(self, conn: Connection) -> None:
        self.create_edge_label(conn)
        self.create_filter_field(conn)

    def create_edge_label(self, conn: Connection) -> None:
        conn.execute(
            text(
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
        )

    def create_filter_field(self, conn: Connection) -> None:
        return
        conn.execute(
            text(
                SQL(
                    """
                DO $$
                DECLARE
                    filter_id VARCHAR(26);
                BEGIN
                    SET ROLE {admin_role};
                    INSERT INTO filter (
                        data_type,
                        source_meta_type,
                        destination_meta_type,
                        accessor,
                        display,
                        lookups,
                        properties
                    )
                    VALUES (
                        {data_type},
                        {source_meta_type},
                        {destination_meta_type},
                        {accessor},
                        {display},
                        {lookups},
                        {properties}

                    ) RETURNING id INTO filter_id;

                END $$;
                """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    label=Literal(self.label),
                    label_ident=Identifier(self.label),
                    db_schema=DB_SCHEMA,
                    data_type=Literal("object"),
                    source_meta_type=Literal(self.source_meta_type),
                    destination_meta_type=Literal(self.destination_meta_type),
                    display=Literal(self.display),
                    accessor=Literal(self.accessor),
                    lookups=Literal(self.lookups),
                    properties=json.dumps(list(self.properties.keys())),
                )
                .as_string()
            )
        )

    def insert_edge_sql(self) -> None:
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
        function_string = SQL(
            """
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
        ).format(
            prop_key_str=SQL(prop_key_str),
            prop_val_str=SQL(prop_val_str),
        )
        return function_string

    def update_edge_sql(self) -> None:
        """
        Generates the SQL string for creating an update function and trigger in a graph database.

        This function constructs a SQL query that:
        - Matches a start graph_node and an end graph_node based on their labels and IDs.
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
        function_string = """
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
                DELETE o
                CREATE (v)-[e:{self.name}] ->(w)
                {prop_key_str}
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type}{prop_val_str});
            """
        return SQL(function_string)

        return SQL(
            self.create_sql_function(
                "update_edge",
                function_string,
                operation="UPDATE",
                include_trigger=True,
                db_function=False,
            )
        )

    def delete_edge_sql(self) -> None:
        """
        Generates the SQL string for creating a delete function and trigger.

        This function constructs an SQL command that uses the `cypher` function to
        delete a relationship between two vertices in a graph database. The vertices
        and the relationship are specified by the attributes of the class instance.

        Returns:
            str: The formatted SQL string for deleting the specified relationship.
        """
        function_string = """
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type});
            """
        return SQL(function_string)

        return self.create_sql_function(
            "delete_edge",
            function_string,
            operation="UPDATE",
            include_trigger=True,
            db_function=False,
        )

    def truncate_edge_sql(self) -> None:
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
        function_string = """
            EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                MATCH (v:{self.start_node.name} {{id: %s}})
                MATCH (w:{self.end_node.name} {{id: %s}})
                MATCH (v)-[o:{self.name}] ->(w)
                DELETE o
            $graph$) AS (e agtype);', {self.start_node.data_type}, {self.end_node.data_type});
            """

        return self.create_sql_function(
            "truncate_edge",
            function_string,
            operation="UPDATE",
            include_trigger=True,
            for_each="STATEMENT",
            db_function=False,
        )
