"""
Selective graph updater for efficient graph synchronization.

This module provides a selective graph update mechanism that reduces
the need for full graph rebuilds when making changes to relational data.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime

from sqlalchemy import text
from uno.database.session import async_session
from sqlalchemy.exc import SQLAlchemyError

from uno.utilities import snake_to_camel


from uno.core.events.event import Event
from typing import Optional, Set, Any


class GraphChangeEvent(Event):
    """
    Represents a change event for graph updates.
    Inherits all canonical event metadata fields from Event.
    These events are used to track changes to entities that should be
    reflected in the graph database.
    """

    CREATE: str = "create"
    UPDATE: str = "update"
    DELETE: str = "delete"

    entity_type: str
    entity_id: str
    change_type: str
    data: dict[str, Any] = {}
    previous_data: dict[str, Any] = {}
    changed_fields: Set[str] = set()

    @property
    def node_label(self) -> str:
        """Get the node label for this entity type."""
        from uno.utilities import snake_to_camel

        return snake_to_camel(self.entity_type)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        d = super().dict()
        d.update(
            {
                "entity_type": self.entity_type,
                "entity_id": self.entity_id,
                "change_type": self.change_type,
                "data": self.data,
                "previous_data": self.previous_data,
                "changed_fields": list(self.changed_fields),
                "node_label": self.node_label,
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphChangeEvent":
        """Create from dictionary representation."""
        changed_fields = set(data.get("changed_fields", []))
        return cls(
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            change_type=data["change_type"],
            data=data.get("data", {}),
            previous_data=data.get("previous_data", {}),
            changed_fields=changed_fields,
        )


class SelectiveGraphUpdater:
    """
    Updates only affected parts of the graph based on entity changes.

    This class provides more efficient graph updates by avoiding complete
    rebuilds of the graph when only small parts of the data have changed.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the selective graph updater.

        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self.batch_size = 100
        self.relationship_cache: Dict[str, list[dict[str, Any]]] = {}

    async def handle_entity_change(self, event: GraphChangeEvent) -> None:
        """
        Handle a specific entity change event.

        Args:
            event: The change event to process
        """
        try:
            if event.change_type == GraphChangeEvent.CREATE:
                await self.create_node_and_relationships(event)
            elif event.change_type == GraphChangeEvent.UPDATE:
                await self.update_node_and_relationships(event)
            elif event.change_type == GraphChangeEvent.DELETE:
                await self.delete_node_and_relationships(event)
            else:
                self.logger.warning(f"Unknown change type: {event.change_type}")
        except Exception as e:
            self.logger.error(f"Error handling entity change: {e}")

    async def create_node_and_relationships(self, event: GraphChangeEvent) -> None:
        """
        Create a node and its relationships in the graph.

        Args:
            event: The creation event
        """
        try:
            # Create the node
            node_props = self._prepare_node_properties(event.data)

            cypher_query = f"""
            CREATE (n:{event.node_label} {{id: $id, properties: $properties}})
            RETURN n
            """

            params = {"id": event.entity_id, "properties": json.dumps(node_props)}

            await self._execute_cypher(cypher_query, params)

            # Create relationships
            await self._create_relationships(event)

        except Exception as e:
            self.logger.error(f"Error creating node: {e}")
            raise

    async def update_node_and_relationships(self, event: GraphChangeEvent) -> None:
        """
        Update a node and its relationships in the graph.

        Args:
            event: The update event
        """
        try:
            # Update the node properties
            node_props = self._prepare_node_properties(event.data)

            cypher_query = f"""
            MATCH (n:{event.node_label} {{id: $id}})
            SET n.properties = $properties
            RETURN n
            """

            params = {"id": event.entity_id, "properties": json.dumps(node_props)}

            await self._execute_cypher(cypher_query, params)

            # Handle relationships only if relevant fields changed
            relationship_fields = await self._get_relationship_fields(event.entity_type)

            if any(field in event.changed_fields for field in relationship_fields):
                # First, remove old relationships
                await self._delete_relationships(event)

                # Then create new ones
                await self._create_relationships(event)

        except Exception as e:
            self.logger.error(f"Error updating node: {e}")
            raise

    async def delete_node_and_relationships(self, event: GraphChangeEvent) -> None:
        """
        Delete a node and its relationships from the graph.

        Args:
            event: The deletion event
        """
        try:
            # Delete the node and all its relationships
            cypher_query = f"""
            MATCH (n:{event.node_label} {{id: $id}})
            DETACH DELETE n
            """

            params = {"id": event.entity_id}

            await self._execute_cypher(cypher_query, params)

        except Exception as e:
            self.logger.error(f"Error deleting node: {e}")
            raise

    async def _create_relationships(self, event: GraphChangeEvent) -> None:
        """
        Create relationships for an entity in the graph.

        Args:
            event: The entity change event
        """
        relationships = await self._get_entity_relationships(
            event.entity_type, event.entity_id
        )

        for rel in relationships:
            source_label = snake_to_camel(rel["source_table"])
            target_label = snake_to_camel(rel["target_table"])
            rel_type = rel["relationship_name"]

            cypher_query = f"""
            MATCH (a:{source_label} {{id: $source_id}}), (b:{target_label} {{id: $target_id}})
            CREATE (a)-[r:{rel_type}]->(b)
            RETURN r
            """

            params = {"source_id": rel["source_id"], "target_id": rel["target_id"]}

            await self._execute_cypher(cypher_query, params)

    async def _delete_relationships(self, event: GraphChangeEvent) -> None:
        """
        Delete relationships for an entity from the graph.

        Args:
            event: The entity change event
        """
        cypher_query = f"""
        MATCH (n:{event.node_label} {{id: $id}})-[r]-()
        DELETE r
        """

        params = {"id": event.entity_id}

        await self._execute_cypher(cypher_query, params)

    async def _get_relationship_fields(self, entity_type: str) -> list[str]:
        """
        Get field names that represent relationships for an entity type.

        Args:
            entity_type: The type of entity

        Returns:
            List of field names that represent relationships
        """
        # Cache in the instance to avoid repeated queries
        cache_key = f"rel_fields:{entity_type}"

        if cache_key in self.relationship_cache:
            return self.relationship_cache[cache_key]

        try:
            async with async_session() as session:
                # Query for foreign key columns
                query = """
                SELECT column_name 
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = :table_name
                """

                result = await session.execute(text(query), {"table_name": entity_type})
                fields = [row[0] for row in result.fetchall()]

                # Cache the result
                self.relationship_cache[cache_key] = fields

                return fields

        except SQLAlchemyError as e:
            self.logger.error(f"Error getting relationship fields: {e}")
            return []

    async def _get_entity_relationships(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        """
        Get relationships for a specific entity.

        Args:
            entity_type: The type of entity
            entity_id: The entity ID

        Returns:
            List of relationship definitions
        """
        try:
            relationships = []
            rel_fields = await self._get_relationship_fields(entity_type)

            if not rel_fields:
                return []

            # Get the entity data
            async with async_session() as session:
                query = f"SELECT * FROM {entity_type} WHERE id = :id"
                result = await session.execute(text(query), {"id": entity_id})
                entity = result.fetchone()

                if not entity:
                    return []

                # Check each foreign key for relationships
                for field in rel_fields:
                    if entity[field] is not None:
                        # Get the target table name
                        fk_query = """
                        SELECT ccu.table_name AS target_table, kcu.column_name AS fk_column
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage ccu 
                        ON tc.constraint_name = ccu.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND tc.table_name = :table_name 
                        AND kcu.column_name = :column_name
                        """

                        fk_result = await session.execute(
                            text(fk_query),
                            {"table_name": entity_type, "column_name": field},
                        )
                        fk_info = fk_result.fetchone()

                        if fk_info:
                            # Add the relationship
                            relationships.append(
                                {
                                    "source_table": entity_type,
                                    "source_id": entity_id,
                                    "target_table": fk_info.target_table,
                                    "target_id": entity[field],
                                    "relationship_name": field.upper(),
                                    "source_field": "id",
                                    "target_field": "id",
                                }
                            )

            return relationships

        except SQLAlchemyError as e:
            self.logger.error(f"Error getting entity relationships: {e}")
            return []

    def _prepare_node_properties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare node properties for storage in the graph.

        Args:
            data: Raw entity data

        Returns:
            Processed properties suitable for graph storage
        """
        # Make a copy to avoid modifying the original
        props = data.copy()

        # Remove ID as it's stored separately
        if "id" in props:
            del props["id"]

        # Handle special types (dates, etc.)
        for key, value in props.items():
            if isinstance(value, datetime):
                props[key] = value.isoformat()

        return props

    async def _execute_cypher(
        self, query: str, params: Dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a cypher query against the graph database.

        Args:
            query: The cypher query to execute
            params: Optional parameters for the query

        Returns:
            Results from the query
        """
        try:
            async with async_session() as session:
                # Convert params to JSON if provided
                params_json = json.dumps(params) if params else None

                # Construct the full query
                full_query = f"""
                SELECT * FROM cypher('graph', $$ {query} $$, $${params_json}$$) AS (result agtype)
                """

                result = await session.execute(text(full_query))
                return [dict(row) for row in result.fetchall()]

        except SQLAlchemyError as e:
            self.logger.error(f"Error executing cypher query: {e}")
            raise


class GraphSynchronizer:
    """
    Manages synchronization between relational and graph databases.

    This class coordinates change detection and selective updates
    to keep the graph database in sync with the relational database.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the graph synchronizer.

        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self.updater = SelectiveGraphUpdater(logger=logger)
        self.pending_events: list[GraphChangeEvent] = []

    def queue_change_event(self, event: GraphChangeEvent) -> None:
        """
        Queue a change event for processing.

        Args:
            event: The change event to queue
        """
        self.pending_events.append(event)

    async def process_pending_events(self, batch_size: int = 100) -> int:
        """
        Process pending change events.

        Args:
            batch_size: Maximum number of events to process in this batch

        Returns:
            Number of events processed
        """
        if not self.pending_events:
            return 0

        # Process events in batches
        events_to_process = self.pending_events[:batch_size]
        self.pending_events = self.pending_events[batch_size:]

        processed_count = 0

        for event in events_to_process:
            try:
                await self.updater.handle_entity_change(event)
                processed_count += 1
            except Exception as e:
                self.logger.error(f"Error processing change event: {e}")

        return processed_count

    async def create_change_detector_triggers(self, table_names: list[str]) -> None:
        """
        Create database triggers that detect changes and generate events.

        Args:
            table_names: List of table names to monitor for changes
        """
        try:
            async with async_session() as session:
                for table_name in table_names:
                    # Create the function that will handle changes
                    function_sql = f"""
                    CREATE OR REPLACE FUNCTION {table_name}_change_event()
                    RETURNS TRIGGER AS $$
                    DECLARE
                        change_type TEXT;
                        entity_id TEXT;
                        data JSONB;
                        prev_data JSONB;
                        changed_fields TEXT[];
                    BEGIN
                        -- Determine the change type
                        IF TG_OP = 'INSERT' THEN
                            change_type := 'create';
                            entity_id := NEW.id;
                            data := row_to_json(NEW)::JSONB;
                            prev_data := NULL;
                            changed_fields := NULL;
                        ELSIF TG_OP = 'UPDATE' THEN
                            change_type := 'update';
                            entity_id := NEW.id;
                            data := row_to_json(NEW)::JSONB;
                            prev_data := row_to_json(OLD)::JSONB;
                            -- Calculate changed fields
                            changed_fields := ARRAY(
                                SELECT key 
                                FROM jsonb_object_keys(data) k(key)
                                WHERE data->key IS DISTINCT FROM prev_data->key
                            );
                        ELSIF TG_OP = 'DELETE' THEN
                            change_type := 'delete';
                            entity_id := OLD.id;
                            data := NULL;
                            prev_data := row_to_json(OLD)::JSONB;
                            changed_fields := NULL;
                        END IF;
                        
                        -- Insert into event queue table
                        INSERT INTO graph_change_events (
                            entity_type, entity_id, change_type, 
                            data, previous_data, changed_fields, created_at
                        ) VALUES (
                            '{table_name}', entity_id, change_type,
                            data, prev_data, changed_fields, NOW()
                        );
                        
                        -- Return appropriate record
                        IF TG_OP = 'DELETE' THEN
                            RETURN OLD;
                        ELSE
                            RETURN NEW;
                        END IF;
                    END;
                    $$ LANGUAGE plpgsql;
                    """

                    await session.execute(text(function_sql))

                    # Create triggers for INSERT, UPDATE, DELETE
                    for op in ["INSERT", "UPDATE", "DELETE"]:
                        trigger_sql = f"""
                        DROP TRIGGER IF EXISTS {table_name}_{op.lower()}_event_trigger ON {table_name};
                        CREATE TRIGGER {table_name}_{op.lower()}_event_trigger
                        AFTER {op} ON {table_name}
                        FOR EACH ROW EXECUTE FUNCTION {table_name}_change_event();
                        """

                        await session.execute(text(trigger_sql))

                    self.logger.info(
                        f"Created change detection triggers for {table_name}"
                    )

                await session.commit()

        except SQLAlchemyError as e:
            self.logger.error(f"Error creating change detector triggers: {e}")
            raise

    async def create_event_queue_table(self) -> None:
        """Create the table used to store change events."""
        try:
            async with async_session() as session:
                # Create the table for event queue
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS graph_change_events (
                    id SERIAL PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    data JSONB,
                    previous_data JSONB,
                    changed_fields TEXT[],
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    processed_at TIMESTAMP,
                    error TEXT,
                    retries INTEGER NOT NULL DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_graph_change_events_processed 
                ON graph_change_events(processed_at) 
                WHERE processed_at IS NULL;
                """

                await session.execute(text(create_table_sql))
                await session.commit()

                self.logger.info("Created graph change events table")

        except SQLAlchemyError as e:
            self.logger.error(f"Error creating event queue table: {e}")
            raise

    async def process_events_from_queue(self, limit: int = 100) -> int:
        """
        Process events from the database queue.

        Args:
            limit: Maximum number of events to process

        Returns:
            Number of events processed
        """
        try:
            async with async_session() as session:
                # Get events to process
                query = """
                UPDATE graph_change_events
                SET processed_at = NOW()
                WHERE id IN (
                    SELECT id FROM graph_change_events
                    WHERE processed_at IS NULL
                    ORDER BY created_at
                    LIMIT :limit
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, entity_type, entity_id, change_type, data, 
                          previous_data, changed_fields, created_at
                """

                result = await session.execute(text(query), {"limit": limit})
                events = result.fetchall()

                if not events:
                    return 0

                # Process each event
                processed_count = 0
                for event_row in events:
                    try:
                        # Convert to GraphChangeEvent
                        changed_fields = set(event_row.changed_fields or [])

                        event = GraphChangeEvent(
                            entity_type=event_row.entity_type,
                            entity_id=event_row.entity_id,
                            change_type=event_row.change_type,
                            data=event_row.data,
                            previous_data=event_row.previous_data,
                            changed_fields=changed_fields,
                            timestamp=event_row.created_at,
                        )

                        # Process the event
                        await self.updater.handle_entity_change(event)
                        processed_count += 1

                        # Mark as successfully processed
                        await session.execute(
                            text(
                                "UPDATE graph_change_events SET error = NULL WHERE id = :id"
                            ),
                            {"id": event_row.id},
                        )

                    except Exception as e:
                        # Mark as failed
                        error_msg = str(e)[:500]  # Limit error message length
                        await session.execute(
                            text(
                                """
                            UPDATE graph_change_events 
                            SET error = :error, retries = retries + 1
                            WHERE id = :id
                            """
                            ),
                            {"id": event_row.id, "error": error_msg},
                        )
                        self.logger.error(
                            f"Error processing event {event_row.id}: {error_msg}"
                        )

                await session.commit()
                return processed_count

        except SQLAlchemyError as e:
            self.logger.error(f"Error processing events from queue: {e}")
            return 0
