# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import ClassVar

from psycopg.sql import SQL, Identifier, Literal
from pydantic import BaseModel, computed_field
from sqlalchemy.sql import text
from sqlalchemy.engine import Connection

from uno.db.sql.sql_emitter import SQLEmitter, ADMIN_ROLE
from uno.utilities import convert_snake_to_camel


class TableGraphSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = [
        "table_name",
        "model",
        "node_label",
        "table",
        "column_name",
        "label",
        "remote_node_label",
        "remote_column_name",
        "local_node_label",
    ]
    column_name: str
    label: str
    remote_node_label: str
    remote_column_name: str
    local_node_label: str = None

    @computed_field
    def node_label(self) -> str:
        return convert_snake_to_camel(self.table_name)

    @computed_field
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
                label=Literal(self.label),
                label_ident=Identifier(self.label),
            )
            .as_string()
        )


'''
class EdgeSQLEmitter(SQLEmitter):

    @computed_field
    def insert_graph(self) -> str:
        function_string = (
            SQL(
                """
            BEGIN
                SET ROLE {admin_role};
                {edges}
                RETURN NEW;
            END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                edges=SQL(
                    "\n".join(
                        [
                            self.insert_edge_sql(edge_config)
                            for edge_config in self.edge_configs
                        ]
                    ),
                ),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_graph",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )
'''


class NodeSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = [
        "table_name",
        "node_label",
        "model",
        "insert_edges",
        "update_edges",
        "table",
    ]

    @computed_field
    def node_label(self) -> str:
        return convert_snake_to_camel(self.table_name)

    @computed_field
    def create_node_label(self) -> str:
        return textwrap.dedent(
            SQL(
                """
            DO $$
            BEGIN
                SET ROLE {admin_role};
                IF NOT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = {label}) THEN
                    PERFORM ag_catalog.create_vlabel('graph', {label});
                    EXECUTE format('CREATE INDEX ON graph.{label_ident} (id);');
                END IF;

                {edge_labels}

            END $$;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=Literal(self.node_label),
                label_ident=Identifier(self.node_label),
                edge_labels=SQL(self.create_edge_labels()),
            )
            .as_string()
        )

    @computed_field
    def insert_edges(self) -> str:
        edges = {}
        for relationship in self.model.relationships():
            if not relationship.info.get("edge"):
                continue
            if relationship.secondary is not None:
                continue
            print(f"Processing relationship: {relationship}")
            column_name = relationship.info.get("column")
            label = relationship.info.get("edge")
            remote_node_label = convert_snake_to_camel(
                relationship.mapper.class_.__tablename__
            )
            remote_column_name = relationship.info.get("remote_column")
            edges.update(
                {
                    label: self.insert_edge_sql(
                        column_name=column_name,
                        label=label,
                        remote_column_name=remote_column_name,
                        remote_node_label=remote_node_label,
                    )
                }
            )
        return edges

    @computed_field
    def update_edges(self) -> str:
        edges = {}
        for relationship in self.model.relationships():
            if not relationship.info.get("edge"):
                continue
            if relationship.secondary is not None:
                continue
            print(f"Processing relationship: {relationship}")
            column_name = relationship.info.get("column")
            label = relationship.info.get("edge")
            remote_node_label = convert_snake_to_camel(
                relationship.mapper.class_.__tablename__
            )
            remote_column_name = relationship.info.get("remote_column")
            edges.update(
                {
                    label: self.update_edge_sql(
                        column_name=column_name,
                        label=label,
                        remote_column_name=remote_column_name,
                        remote_node_label=remote_node_label,
                    )
                }
            )
        return edges

    def create_edge_labels(self) -> str:
        return "\n".join(
            [
                self.create_edge_label_sql(edge_label)
                for edge_label in self.insert_edges.keys()
            ]
        )

    def create_edge_label_sql(self, label: str) -> str:
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
                admin_role=ADMIN_ROLE,
                label=Literal(label),
                label_ident=Identifier(label),
            )
            .as_string()
        )

    def insert_edge_sql(
        self,
        column_name: str,
        label: str,
        remote_node_label: str,
        remote_column_name: str,
        local_node_label: str = None,
    ) -> str:
        return (
            SQL(
                """
                    IF NEW.{column_name} IS NOT NULL THEN
                        EXECUTE FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                MATCH (l:{node_label} {{id: %s}})
                                MATCH (r:{remote_node_label} {{id: %s}})
                                CREATE (l)-[e:{label}]->(r)
                            $$) AS (result agtype)',
                            quote_nullable(NEW.{column_name}),
                            quote_nullable(NEW.{remote_column_name})
                        );
                    END IF;
            """
            )
            .format(
                node_label=(
                    SQL(self.node_label)
                    if local_node_label is None
                    else SQL(self.local_node_label)
                ),
                column_name=Identifier(column_name),
                label=SQL(label),
                remote_node_label=SQL(remote_node_label),
                remote_column_name=Identifier(remote_column_name),
            )
            .as_string()
        )

    @computed_field
    def insert_graph(self) -> str:
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
                    properties_str := array_to_string(
                        array(SELECT FORMAT('%s: %L', key, 
                            COALESCE(value, 'NULL')) 
                            FROM EACH(properties)),', ');

                    -- Construct the Cypher query dynamically
                    cypher_query := format('
                        CREATE (v:{label} {{%s}})', properties_str
                    );

                    -- Execute the Cypher query
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', cypher_query);

                    -- Execute the Cypher queries to insert the edges
                    {edges}

                    RETURN NEW;

                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=SQL(self.node_label),
                edges=SQL(
                    "\n".join([edge for edge in self.insert_edges.values()]),
                ),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_graph",
            function_string,
            operation="INSERT",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    def update_edge_sql(
        self,
        column_name: str,
        label: str,
        remote_node_label: str,
        remote_column_name: str,
        local_node_label: str = None,
    ) -> str:
        return (
            SQL(
                """
                    IF OLD.{column_name} IS NOT NULL THEN
                        EXECUTE FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                                MATCH (l:{node_label} {{id: %s}})
                                MATCH (r:{remote_node_label} {{id: %s}})
                                DELETE (l)-[e:{label}]->(r)
                            $$) AS (result agtype)',
                            quote_nullable(OLD.{column_name}),
                            quote_nullable(OLD.{remote_column_name})
                        ); 
                    END IF;

                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{id: %s}})
                            CREATE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(NEW.{column_name}),
                        quote_nullable(NEW.{remote_column_name})
                    ); 
            """
            )
            .format(
                node_label=(
                    SQL(self.node_label)
                    if local_node_label is None
                    else SQL(self.local_node_label)
                ),
                column_name=Identifier(column_name),
                label=SQL(label),
                remote_node_label=SQL(remote_node_label),
                remote_column_name=Identifier(remote_column_name),
            )
            .as_string()
        )

    @computed_field
    def update_graph(self) -> str:
        function_string = (
            SQL(
                """
                DECLARE
                    update_node_query text;
                    properties hstore;
                    set_properties_str text;
                BEGIN
                    -- Convert the NEW record to hstore to get column names and values
                    properties := uno.hstore(NEW);

                    -- Construct the properties string
                    set_properties_str := array_to_string(
                        array(SELECT FORMAT('SET v.%s = %L', key, COALESCE(value, 'NULL')) FROM EACH(properties)),', ');

                    -- Construct the Cypher query dynamically
                    update_node_query := format('
                        MATCH (v:{label} {{id: %s}})
                        set_properties_str
                        ', OLD.id);

                    -- Execute the Cypher query
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $$%s$$) AS (result agtype)', update_node_query);

                    -- Execute the Cypher queries to insert the edges
                    {edges}

                    RETURN NEW;

                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                label=SQL(self.node_label),
                edges=SQL(
                    "\n".join([edge for edge in self.update_edges.values()]),
                ),
            )
            .as_string()
        )

        return self.create_sql_function(
            "update_graph",
            function_string,
            operation="UPDATE",
            timing="AFTER",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def delete_graph(self) -> str:
        function_string = (
            SQL(
                """
                BEGIN
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        MATCH (v:{node_label} {{id: %s}})
                        DELETE v
                    $graph$) AS (e agtype);, OLD.id);');

                    RETURN OLD;
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                node_label=SQL(self.node_label),
            )
            .as_string()
        )

        return self.create_sql_function(
            "delete_graph",
            function_string,
            timing="AFTER",
            operation="DELETE",
            include_trigger=True,
            db_function=False,
        )

    @computed_field
    def truncate_graph(self) -> str:
        function_string = (
            SQL(
                """
                BEGIN
                    SET ROLE {admin_role};
                    EXECUTE FORMAT('SELECT * FROM cypher(''graph'', $graph$
                        MATCH (v:{node_label})
                        DELETE v
                    $graph$) AS (e agtype);');
                END;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                node_label=SQL(self.node_label),
            )
            .as_string()
        )

        return self.create_sql_function(
            "truncate_graph",
            function_string,
            operation="TRUNCATE",
            timing="BEFORE",
            include_trigger=True,
            for_each="STATEMENT",
            db_function=False,
        )
