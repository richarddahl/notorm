# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json
import textwrap

from typing import Any, ClassVar

from psycopg.sql import SQL, Identifier, Literal

from pydantic import BaseModel, computed_field

from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

from uno.db.sql.sql_emitter import (
    SQLEmitter,
    DB_SCHEMA,
    ADMIN_ROLE,
    WRITER_ROLE,
)
from uno.apps.val.enums import (
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


class GraphSQLEmitter(SQLEmitter):

    @computed_field
    def source_meta_type(self) -> str:
        return self.obj_class.table.name


class PropertySQLEmitter(GraphSQLEmitter):
    # obj_class: type[DeclarativeBase] <- from GraphBase
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

    @computed_field
    def emit_sql(self) -> str:
        return
        return (
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
                schema_name=DB_SCHEMA,
                display=Literal(self.display),
                data_type=Literal(self.data_type),
                source_meta_type=Literal(self.source_meta_type),
                destination_meta_type=Literal(self.destination_meta_type),
                accessor=Literal(self.accessor),
                lookups=Literal(self.lookups),
            )
            .as_string()
        )


class NodeSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = ["table_name", "label", "properties"]

    properties: dict[str, Any] = {}

    @computed_field
    def label(self) -> str:
        return convert_snake_to_camel(self.table_name)

    # @computed_field
    # def properties(self) -> dict[str, PropertySQLEmitter]:
    #    return self.node.properties

    @computed_field
    def create_vlabel(self) -> str:
        return textwrap.dedent(
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

    @computed_field
    def insert_node(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                cypher_query text;
                properties hstore;
                properties_str text;
            BEGIN
                -- Convert the NEW record to hstore to get column names and values
                properties := hstore(NEW);

                -- Construct the properties string
                properties_str := array_to_string(array(
                    SELECT FORMAT('%I: %L', key, value) FROM EACH(properties)
                ), ', ');

                -- Construct the Cypher query dynamically
                cypher_query := format(
                    'CREATE (v:%s {{%s}})',
                    {label},
                    properties_str
                );

                -- Execute the Cypher query
                EXECUTE FORMAT('SELECT * FROM cypher(''graph'', %L) AS (result agtype)', cypher_query);
                RETURN NEW;
            END;
        """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=Literal(self.label),
            )
            .as_string()
        )

        function_string_old = (
            SQL(
                """
                DECLARE
                    cypher_query text;
                    properties hstore;
                    properties_str text;
                BEGIN
                    -- Convert the NEW record to hstore to get column names and values
                    properties := hstore(NEW);


                    -- Construct the properties string
                    properties_str := array_to_string(array(
                        SELECT FORMAT('%I: %L', key, value) FROM EACH(properties)
                    ), ', ');

                    -- Construct the Cypher query dynamically
                    cypher_query := format(
                        'CREATE (v:{label} {{%s}})',
                        properties_str
                    );

                    -- Execute the Cypher query
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', %L) AS (result agtype)', cypher_query);
                    RETURN NEW;
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=SQL(self.label),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_node",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    # @computed_field
    def insert_node_old(self) -> str:
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
            function_string_ = SQL(
                """
                DECLARE 
                    insert_node_sql TEXT := FORMAT('SELECT * FROM cypher(''graph'',
                        $g$
                        CREATE (v:{label} {{{prop_key_str}}})
                        $g$) AS (a agtype);', {prop_val_str}
                    ');
                BEGIN
                    SET ROLE {admin_role};
                    EXECUTE insert_node_sql;
                    {edge_str}
                    RETURN NEW;
                END;
                """
            )
        else:
            function_string_ = SQL(
                """
                DECLARE 
                    insert_node_sql TEXT := FORMAT('SELECT * FROM cypher(''graph'',
                        $g$
                            CREATE (v:{label})
                        $g$) AS (a agtype);
                    ');
                BEGIN
                    SET ROLE {admin_role};
                    EXECUTE insert_node_sql;
                    {edge_str}
                    RETURN NEW;
                END;
                """
            )
        function_string = function_string_.format(
            graph=Literal("graph"),
            admin_role=ADMIN_ROLE,
            label=SQL(self.label),
            prop_key_str=SQL(prop_key_str),
            prop_val_str=SQL(prop_val_str),
            edge_str=SQL(edge_str),
        ).as_string()

        return self.create_sql_function(
            "insert_node",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
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


class EdgeSQLEmitter(SQLEmitter):
    edge: BaseModel = None

    """
    @computed_field
    def properties(self) -> dict[str, PropertySQLEmitter]:
        if not isinstance(self.secondary, Table):
            return {}
        props = {}
        for column in self.secondary.columns:
            if column.foreign_keys and column.primary_key:
                continue
            data_type = column.type.python_type.__name__
            for base in self.obj_class.registry.mappers:
                if base.class_.__tablename__ == self.secondary.name:
                    obj_class = base.class_
                    break
            props.update(
                {
                    column.name: PropertySQLEmitter(
                        obj_class=obj_class,
                        accessor=column.name,
                        data_type=data_type,
                    )
                }
            )
        return props
    """

    @computed_field
    def emit_sql(self) -> str:
        self.create_edge_label()
        # self.create_filter_field()

    def create_edge_label(self) -> str:
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
                END $$;
                """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=Literal(self.edge.label),
                label_ident=Identifier(self.edge.label),
            )
            .as_string()
        )

    def create_filter_field(self) -> str:
        return
        return (
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
                schema_name=DB_SCHEMA,
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
