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
            version INT DEFAULT 1,
            data JSONB NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indices for efficient querying
        CREATE INDEX IF NOT EXISTS idx_domain_events_event_type ON {schema}.domain_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_domain_events_aggregate_id ON {schema}.domain_events(aggregate_id);
        CREATE INDEX IF NOT EXISTS idx_domain_events_timestamp ON {schema}.domain_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_domain_events_aggregate_version ON {schema}.domain_events(aggregate_id, version);
        
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
                    'timestamp', NEW.timestamp,
                    'version', NEW.version
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


class CreateEventSnapshotsTable(SQLEmitter):
    """Emitter for creating the aggregate_snapshots table."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating the aggregate_snapshots table.

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
        
        -- Create aggregate snapshots table for event sourcing
        CREATE TABLE IF NOT EXISTS {schema}.aggregate_snapshots (
            aggregate_id VARCHAR(36) NOT NULL,
            aggregate_type VARCHAR(100) NOT NULL,
            version INT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            state JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Primary key combines ID and type
            PRIMARY KEY(aggregate_id, aggregate_type),
            
            -- Ensure version is positive
            CONSTRAINT snapshot_version_check CHECK (version > 0)
        );

        -- Create indices for efficient querying
        CREATE INDEX IF NOT EXISTS idx_snapshots_aggregate_type 
        ON {schema}.aggregate_snapshots(aggregate_type);
        
        CREATE INDEX IF NOT EXISTS idx_snapshots_version
        ON {schema}.aggregate_snapshots(aggregate_id, version);
        
        COMMENT ON TABLE {schema}.aggregate_snapshots IS 'Stores aggregate snapshots for optimized event sourcing';
        """

        # Add the create table statement to the list
        statements.append(
            SQLStatement(
                name="create_aggregate_snapshots_table",
                type=SQLStatementType.TABLE,
                sql=create_table_sql,
            )
        )

        # Generate the update timestamp function SQL
        update_timestamp_function_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a function to update the timestamp when a snapshot is updated
        CREATE OR REPLACE FUNCTION {schema}.update_snapshot_timestamp()
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
                name="create_update_snapshot_timestamp_function",
                type=SQLStatementType.FUNCTION,
                sql=update_timestamp_function_sql,
            )
        )

        # Generate the trigger SQL
        trigger_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a trigger to call the function before an update
        DROP TRIGGER IF EXISTS snapshot_update_timestamp_trigger ON {schema}.aggregate_snapshots;
        CREATE TRIGGER snapshot_update_timestamp_trigger
        BEFORE UPDATE ON {schema}.aggregate_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION {schema}.update_snapshot_timestamp();
        """

        # Add the trigger statement to the list
        statements.append(
            SQLStatement(
                name="create_snapshot_update_timestamp_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        # Generate the grant permissions SQL
        grant_permissions_sql = f"""
        SET ROLE {admin_role};
        
        -- Grant permissions
        GRANT SELECT, INSERT, UPDATE ON {schema}.aggregate_snapshots TO {writer_role};
        GRANT SELECT ON {schema}.aggregate_snapshots TO {reader_role};
        """

        # Add the grant permissions statement to the list
        statements.append(
            SQLStatement(
                name="grant_aggregate_snapshots_permissions",
                type=SQLStatementType.GRANT,
                sql=grant_permissions_sql,
            )
        )

        return statements


class CreateEventProjectionFunction(SQLEmitter):
    """Emitter for creating event projection functions."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating event projection functions.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate the create function SQL
        db_name = self.config.DB_NAME
        admin_role = f"{db_name}_admin"
        schema = self.config.DB_SCHEMA  # Use configured schema from settings
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"

        # Create the generic event projection function
        event_projection_function_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a function to handle event projections
        CREATE OR REPLACE FUNCTION {schema}.project_event(
            projection_name TEXT,
            event_data JSONB
        )
        RETURNS VOID AS $$
        DECLARE
            projection_schema_name TEXT;
            projection_table_name TEXT;
            event_type TEXT;
            aggregate_id TEXT;
            sql_statement TEXT;
            event_payload JSONB;
        BEGIN
            -- Extract event details
            event_type := event_data->>'event_type';
            aggregate_id := event_data->>'aggregate_id';
            
            -- Skip if no aggregate_id
            IF aggregate_id IS NULL THEN
                RETURN;
            END IF;
            
            -- Get projection schema and table names
            projection_schema_name := split_part(projection_name, '.', 1);
            IF projection_schema_name = projection_name THEN
                projection_schema_name := '{schema}';
            ELSE
                projection_table_name := split_part(projection_name, '.', 2);
            END IF;
            
            -- Check if the projection exists
            PERFORM 1
            FROM information_schema.tables
            WHERE table_schema = projection_schema_name
            AND table_name = COALESCE(projection_table_name, projection_name);
            
            IF NOT FOUND THEN
                RAISE NOTICE 'Projection table % does not exist', projection_name;
                RETURN;
            END IF;
            
            -- Process based on event type
            -- This is a simplistic example - real implementations would have 
            -- specific handling for different event types and projections
            IF event_type LIKE '%Created' OR event_type LIKE '%Updated' THEN
                -- For an insert or update event, call the projection's handler function if it exists
                IF EXISTS (
                    SELECT 1 FROM pg_proc 
                    WHERE proname = 'handle_' || lower(replace(event_type, '.', '_')) 
                    AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = projection_schema_name)
                ) THEN
                    -- Dynamic call to event handler function
                    sql_statement := 'SELECT ' || projection_schema_name || '.handle_' || 
                                    lower(replace(event_type, '.', '_')) || 
                                    '(' || quote_literal(event_data::text) || '::jsonb)';
                    EXECUTE sql_statement;
                ELSE
                    RAISE NOTICE 'No handler function for event type % in projection %', 
                             event_type, projection_name;
                END IF;
            END IF;
            
            -- Record that this event has been processed for this projection
            INSERT INTO {schema}.event_processors 
                (processor_id, last_processed_event_id, last_processed_timestamp, processor_type)
            VALUES 
                (
                    projection_name || ':' || event_type,
                    event_data->>'event_id',
                    (event_data->>'timestamp')::TIMESTAMP,
                    'projection'
                )
            ON CONFLICT (processor_id) 
            DO UPDATE SET
                last_processed_event_id = EXCLUDED.last_processed_event_id,
                last_processed_timestamp = EXCLUDED.last_processed_timestamp,
                updated_at = CURRENT_TIMESTAMP;
        END;
        $$ LANGUAGE plpgsql;
        """

        # Add the projection function statement to the list
        statements.append(
            SQLStatement(
                name="create_event_projection_function",
                type=SQLStatementType.FUNCTION,
                sql=event_projection_function_sql,
            )
        )

        # Generate the version check function for optimistic concurrency
        version_check_function_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a function to check event version for optimistic concurrency
        CREATE OR REPLACE FUNCTION {schema}.check_event_version()
        RETURNS TRIGGER AS $$
        DECLARE
            latest_version INT;
        BEGIN
            -- Skip check if no aggregate_id or version
            IF NEW.aggregate_id IS NULL OR NEW.version IS NULL THEN
                RETURN NEW;
            END IF;
            
            -- Get the latest version for this aggregate
            SELECT MAX(version) INTO latest_version
            FROM {schema}.domain_events
            WHERE aggregate_id = NEW.aggregate_id
            AND aggregate_type = NEW.aggregate_type;
            
            -- If first event for this aggregate, version should be 1
            IF latest_version IS NULL THEN
                IF NEW.version <> 1 THEN
                    RAISE EXCEPTION 'Invalid version for first event: expected 1, got %', NEW.version;
                END IF;
            -- Otherwise version should be exactly one more than the latest
            ELSIF NEW.version <> latest_version + 1 THEN
                RAISE EXCEPTION 'Concurrency conflict: expected version %, got %', 
                              latest_version + 1, NEW.version;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """

        # Add the version check function statement to the list
        statements.append(
            SQLStatement(
                name="create_event_version_check_function",
                type=SQLStatementType.FUNCTION,
                sql=version_check_function_sql,
            )
        )

        # Create the version check trigger
        version_check_trigger_sql = f"""
        SET ROLE {admin_role};
        
        -- Create a trigger to check event version before insert
        DROP TRIGGER IF EXISTS event_version_check_trigger ON {schema}.domain_events;
        CREATE TRIGGER event_version_check_trigger
        BEFORE INSERT ON {schema}.domain_events
        FOR EACH ROW
        EXECUTE FUNCTION {schema}.check_event_version();
        """

        # Add the version check trigger statement to the list
        statements.append(
            SQLStatement(
                name="create_event_version_check_trigger",
                type=SQLStatementType.TRIGGER,
                sql=version_check_trigger_sql,
            )
        )

        return statements