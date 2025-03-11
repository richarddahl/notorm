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


class EdgeConfig(BaseModel):
    table_name: str
    column_name: str
    label: str
    remote_table_name: str
    remote_column_name: str
    remote_node_label: str
    secondary_table_name: str = None
    secondary_column_name: str = None
    secondary_remote_column_name: str = None

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


class GraphSQLEmitter(SQLEmitter):
    exclude_fields: ClassVar[list[str]] = ["table_name", "node_label"]
    edge_configs: ClassVar[list[EdgeConfig]] = []

    def emit_sql(self, connection: Connection) -> None:
        for edge_config in self.edge_configs:
            for statement_name, sql_statement in (
                edge_config(table_name=self.table_name)
                .model_dump(include=["create_edge_label"])
                .items()
            ):
                print(f"Executing {statement_name}...")
                connection.execute(text(sql_statement))
        for statement_name, sql_statement in self.model_dump(
            exclude=self.exclude_fields
        ).items():
            print(f"Executing {statement_name}...")
            connection.execute(text(sql_statement))

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
                label=Literal(self.node_label),
                label_ident=Identifier(self.node_label),
            )
            .as_string()
        )

    def insert_edge_sql(self, edge_config: EdgeConfig) -> str:
        return (
            SQL(
                """
                    IF NEW.{column_name} IS NOT NULL THEN
                        EXECUTE FORMAT('
                            SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{id: %s}})
                            CREATE (l)-[e:{label}]->(r)$$) AS (result agtype)',
                            quote_nullable(NEW.{column_name}),
                            quote_nullable(NEW.{remote_column_name})
                        );
                    END IF;
            """
            )
            .format(
                node_label=SQL(edge_config.node_label),
                column_name=Identifier(edge_config.column_name),
                label=SQL(edge_config.label),
                remote_node_label=SQL(edge_config.remote_node_label),
                remote_column_name=Identifier(edge_config.remote_column_name),
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
                        array(SELECT FORMAT('%s: %L', key, COALESCE(value, 'NULL')) FROM EACH(properties)),', ');

                    -- Construct the Cypher query dynamically
                    cypher_query := format('CREATE (v:{label} {{%s}})', properties_str);

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
                    "\n".join(
                        [
                            self.insert_edge_sql(
                                edge_config(table_name=self.table_name)
                            )
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

    def update_edge_sql(self, edge_config: EdgeConfig) -> str:

        return (
            SQL(
                """
                    EXECUTE FORMAT('
                        SELECT * FROM cypher(''graph'', $$
                            MATCH (l:{node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{id: %s}})
                            DELETE (l)-[e:{label}]->(r)
                            MATCH (l:{node_label} {{id: %s}})
                            MATCH (r:{remote_node_label} {{id: %s}})
                            CREATE (l)-[e:{label}]->(r)
                        $$) AS (result agtype)',
                        quote_nullable(OLD.{column_name}),
                        quote_nullable(OLD.{remote_column_name}),
                        quote_nullable(NEW.{column_name}),
                        quote_nullable(NEW.{remote_column_name})
                    ); 
            """
            )
            .format(
                node_label=SQL(edge_config.node_label),
                column_name=Identifier(edge_config.column_name),
                label=SQL(edge_config.label),
                remote_node_label=SQL(edge_config.remote_node_label),
                remote_column_name=Identifier(edge_config.remote_column_name),
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
                    "\n".join(
                        [
                            self.update_edge_sql(
                                edge_config(table_name=self.table_name)
                            )
                            for edge_config in self.edge_configs
                        ]
                    ),
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
