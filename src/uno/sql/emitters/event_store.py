# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for event store operations."""

import logging
from typing import List, Optional

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType


class CreateDomainEventsTable(SQLEmitter):
    """Emitter for creating the domain_events table and related objects."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating the domain_events table.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate the create table SQL
        db_name = self.config.DB_NAME
        admin_role = f"{db_name}_admin"
        schema = self.config.DB_SCHEMA  # Use configured schema from settings
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"

        create_table_sql = f"""
        SET ROLE {admin_role};
        
        -- Create domain events table for event sourcing
        CREATE TABLE IF NOT EXISTS {schema}.domain_events (
            event_id VARCHAR(36) PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            aggregate_id VARCHAR(36),
            aggregate_type VARCHAR(100),
            timestamp TIMESTAMP NOT NULL,
            data JSONB NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indices for efficient querying
        CREATE INDEX IF NOT EXISTS idx_domain_events_event_type ON {schema}.domain_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_domain_events_aggregate_id ON {schema}.domain_events(aggregate_id);
        CREATE INDEX IF NOT EXISTS idx_domain_events_timestamp ON {schema}.domain_events(timestamp);
        
        COMMENT ON TABLE {schema}.domain_events IS 'Stores domain events for event sourcing and event-driven architecture';
        """

        # Add the create table statement to the list
        statements.append(
            SQLStatement(
                name="create_domain_events_table",
                type=SQLStatementType.TABLE,
                sql=create_table_sql,
            )
        )

        # Generate the notification function SQL
        notification_function_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a function to publish events to Postgres NOTIFY when events are inserted
        CREATE OR REPLACE FUNCTION {schema}.notify_domain_event()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Publish a notification with the event_type and aggregate_id
            PERFORM pg_notify(
                'domain_events',
                json_build_object(
                    'event_id', NEW.event_id,
                    'event_type', NEW.event_type,
                    'aggregate_id', NEW.aggregate_id,
                    'aggregate_type', NEW.aggregate_type,
                    'timestamp', NEW.timestamp
                )::text
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """

        # Add the notification function statement to the list
        statements.append(
            SQLStatement(
                name="create_notify_domain_event_function",
                type=SQLStatementType.FUNCTION,
                sql=notification_function_sql,
            )
        )

        # Generate the trigger SQL
        trigger_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a trigger to call the function after an event is inserted
        DROP TRIGGER IF EXISTS domain_event_notify_trigger ON {schema}.domain_events;
        CREATE TRIGGER domain_event_notify_trigger
        AFTER INSERT ON {schema}.domain_events
        FOR EACH ROW
        EXECUTE FUNCTION {schema}.notify_domain_event();
        """

        # Add the trigger statement to the list
        statements.append(
            SQLStatement(
                name="create_domain_event_notify_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        # Generate the grant permissions SQL
        grant_permissions_sql = f"""
        SET ROLE {admin_role};
        
        -- Grant permissions
        GRANT SELECT, INSERT ON {schema}.domain_events TO {writer_role};
        GRANT SELECT ON {schema}.domain_events TO {reader_role};
        """

        # Add the grant permissions statement to the list
        statements.append(
            SQLStatement(
                name="grant_domain_events_permissions",
                type=SQLStatementType.GRANT,
                sql=grant_permissions_sql,
            )
        )

        return statements


class CreateEventProcessorsTable(SQLEmitter):
    """Emitter for creating the event_processors table for tracking consumers."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating the event_processors table.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate the create table SQL
        db_name = self.config.DB_NAME
        admin_role = f"{db_name}_admin"
        schema = self.config.DB_SCHEMA  # Use configured schema from settings
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"

        create_table_sql = f"""
        SET ROLE {admin_role};
        
        -- Create event processors table for tracking event consumers
        CREATE TABLE IF NOT EXISTS {schema}.event_processors (
            processor_id VARCHAR(100) PRIMARY KEY,
            last_processed_event_id VARCHAR(36),
            last_processed_timestamp TIMESTAMP,
            processor_type VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indices for efficient querying
        CREATE INDEX IF NOT EXISTS idx_event_processors_status ON {schema}.event_processors(status);
        CREATE INDEX IF NOT EXISTS idx_event_processors_type ON {schema}.event_processors(processor_type);
        
        COMMENT ON TABLE {schema}.event_processors IS 'Tracks event processors and their progress for exactly-once processing';
        """

        # Add the create table statement to the list
        statements.append(
            SQLStatement(
                name="create_event_processors_table",
                type=SQLStatementType.TABLE,
                sql=create_table_sql,
            )
        )

        # Generate the update timestamp function SQL
        update_timestamp_function_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a function to update the timestamp when a processor is updated
        CREATE OR REPLACE FUNCTION {schema}.update_event_processor_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """

        # Add the update timestamp function statement to the list
        statements.append(
            SQLStatement(
                name="create_update_event_processor_timestamp_function",
                type=SQLStatementType.FUNCTION,
                sql=update_timestamp_function_sql,
            )
        )

        # Generate the trigger SQL
        trigger_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a trigger to call the function before an update
        DROP TRIGGER IF EXISTS event_processor_update_timestamp_trigger ON {schema}.event_processors;
        CREATE TRIGGER event_processor_update_timestamp_trigger
        BEFORE UPDATE ON {schema}.event_processors
        FOR EACH ROW
        EXECUTE FUNCTION {schema}.update_event_processor_timestamp();
        """

        # Add the trigger statement to the list
        statements.append(
            SQLStatement(
                name="create_event_processor_update_timestamp_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        # Generate the grant permissions SQL
        grant_permissions_sql = f"""
        SET ROLE {admin_role};
        
        -- Grant permissions
        GRANT SELECT, INSERT, UPDATE ON {schema}.event_processors TO {writer_role};
        GRANT SELECT ON {schema}.event_processors TO {reader_role};
        """

        # Add the grant permissions statement to the list
        statements.append(
            SQLStatement(
                name="grant_event_processors_permissions",
                type=SQLStatementType.GRANT,
                sql=grant_permissions_sql,
            )
        )

        return statements