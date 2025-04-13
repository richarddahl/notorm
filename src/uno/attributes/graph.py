# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Graph database integration for the attributes module.

This module provides utilities for querying objects based on their attributes
using the graph database.
"""

from typing import Any, Dict, List, Optional, Union
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result, Ok, Err
from uno.database.engine import async_connection
from uno.database.enhanced_session import enhanced_async_session
from uno.enums import Include, Match
from uno.queries.models import QueryPathModel
from uno.attributes.objs import AttributeType


class AttributeGraphError(Exception):
    """Base error class for attribute graph operations."""
    pass


class AttributeGraphQuery:
    """
    Utilities for attribute-based graph queries.
    
    This class provides methods for creating and executing attribute-based
    graph queries.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the attribute graph query utilities.
        
        Args:
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger(__name__)
    
    async def register_attribute_query_paths(
        self,
        attribute_type: AttributeType,
        session: Optional[AsyncSession] = None
    ) -> Result[List[str], AttributeGraphError]:
        """
        Register query paths for an attribute type.
        
        This creates query paths in the database that can be used for
        attribute-based queries.
        
        Args:
            attribute_type: The attribute type to register paths for
            session: Optional database session
            
        Returns:
            Result containing the IDs of created query paths
        """
        try:
            path_ids = []
            
            # For each meta type the attribute type describes
            for meta_type in attribute_type.describes:
                # For each value type the attribute can have
                for value_type in attribute_type.value_types:
                    # Create a query path
                    if session:
                        path_id = await self._create_attribute_query_path(
                            attribute_type=attribute_type,
                            source_meta_type_id=meta_type.id,
                            target_meta_type_id=value_type.id,
                            session=session
                        )
                    else:
                        async with enhanced_async_session() as s:
                            path_id = await self._create_attribute_query_path(
                                attribute_type=attribute_type,
                                source_meta_type_id=meta_type.id,
                                target_meta_type_id=value_type.id,
                                session=s
                            )
                    
                    path_ids.append(path_id)
            
            return Ok(path_ids)
            
        except Exception as e:
            self.logger.error(f"Error registering attribute query paths: {e}")
            return Err(AttributeGraphError(f"Error registering attribute query paths: {str(e)}"))
    
    async def _create_attribute_query_path(
        self,
        attribute_type: AttributeType,
        source_meta_type_id: str,
        target_meta_type_id: str,
        session: AsyncSession
    ) -> str:
        """
        Create a query path for an attribute type.
        
        Args:
            attribute_type: The attribute type
            source_meta_type_id: The source meta type ID
            target_meta_type_id: The target meta type ID
            session: Database session
            
        Returns:
            The ID of the created query path
        """
        # Construct the cypher path
        cypher_path = f"""(s:{source_meta_type_id})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->
        (at:AttributeType {{name: '{attribute_type.name}'}}),
        (a)-[:HAS_VALUE]->(t:{target_meta_type_id})"""
        
        # Check if path already exists
        query = text("""
        SELECT id FROM query_path
        WHERE source_meta_type_id = :source_meta_type_id
        AND target_meta_type_id = :target_meta_type_id
        AND cypher_path = :cypher_path
        """)
        
        result = await session.execute(
            query,
            {
                "source_meta_type_id": source_meta_type_id,
                "target_meta_type_id": target_meta_type_id,
                "cypher_path": cypher_path
            }
        )
        
        existing_path = result.fetchone()
        
        if existing_path:
            return existing_path[0]
        
        # Create the query path
        path = QueryPathModel(
            source_meta_type_id=source_meta_type_id,
            target_meta_type_id=target_meta_type_id,
            cypher_path=cypher_path,
            data_type="str"  # Use string data type for attribute values
        )
        
        session.add(path)
        await session.flush()
        
        return path.id
    
    async def find_objects_by_attribute(
        self,
        object_type: str,
        attribute_type: str,
        value: Any,
        session: Optional[AsyncSession] = None
    ) -> Result[List[str], AttributeGraphError]:
        """
        Find objects with a specific attribute type and value.
        
        Args:
            object_type: The type of object to search
            attribute_type: The attribute type name
            value: The attribute value
            session: Optional database session
            
        Returns:
            Result containing a list of object IDs matching the criteria
        """
        try:
            # Construct the cypher query
            cypher_query = f"""
            MATCH (o:{object_type})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType),
                  (a)-[:HAS_VALUE]->(v)
            WHERE at.name = $attribute_type AND v.value = $value
            RETURN DISTINCT o.id
            """
            
            # Execute the query
            if session:
                result = await self._execute_cypher_query(
                    cypher_query,
                    {"attribute_type": attribute_type, "value": str(value)},
                    session
                )
            else:
                async with enhanced_async_session() as s:
                    result = await self._execute_cypher_query(
                        cypher_query,
                        {"attribute_type": attribute_type, "value": str(value)},
                        s
                    )
            
            return Ok(result)
            
        except Exception as e:
            self.logger.error(f"Error finding objects by attribute: {e}")
            return Err(AttributeGraphError(f"Error finding objects by attribute: {str(e)}"))
    
    async def find_objects_with_attributes(
        self,
        object_type: str,
        conditions: List[Dict[str, Any]],
        logic: str = "AND",
        session: Optional[AsyncSession] = None
    ) -> Result[List[str], AttributeGraphError]:
        """
        Find objects with multiple attribute conditions.
        
        Args:
            object_type: The type of object to search
            conditions: List of attribute conditions, each with 'attribute_type' and 'value'
            logic: Logic operator to combine conditions ('AND' or 'OR')
            session: Optional database session
            
        Returns:
            Result containing a list of object IDs matching the criteria
        """
        try:
            # Validate logic operator
            if logic not in ["AND", "OR"]:
                return Err(AttributeGraphError(f"Invalid logic operator: {logic}. Must be 'AND' or 'OR'"))
            
            # Construct the cypher query
            cypher_query = f"""
            MATCH (o:{object_type})
            WHERE 
            """
            
            # Add conditions
            condition_parts = []
            params = {}
            
            for i, condition in enumerate(conditions):
                attribute_type = condition.get("attribute_type")
                value = condition.get("value")
                
                if not attribute_type or value is None:
                    return Err(AttributeGraphError(f"Invalid condition: {condition}. Must include 'attribute_type' and 'value'"))
                
                # Add condition
                condition_parts.append(f"""
                EXISTS {{
                    MATCH (o)-[:HAS_ATTRIBUTE]->(a{i}:Attribute)-[:ATTRIBUTE_TYPE]->(at{i}:AttributeType),
                          (a{i})-[:HAS_VALUE]->(v{i})
                    WHERE at{i}.name = $attribute_type{i} AND v{i}.value = $value{i}
                }}
                """)
                
                # Add parameters
                params[f"attribute_type{i}"] = attribute_type
                params[f"value{i}"] = str(value)
            
            # Combine conditions with the specified logic
            cypher_query += f" {logic} ".join(condition_parts)
            cypher_query += " RETURN DISTINCT o.id"
            
            # Execute the query
            if session:
                result = await self._execute_cypher_query(cypher_query, params, session)
            else:
                async with enhanced_async_session() as s:
                    result = await self._execute_cypher_query(cypher_query, params, s)
            
            return Ok(result)
            
        except Exception as e:
            self.logger.error(f"Error finding objects with attributes: {e}")
            return Err(AttributeGraphError(f"Error finding objects with attributes: {str(e)}"))
    
    async def find_objects_by_attribute_range(
        self,
        object_type: str,
        attribute_type: str,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        session: Optional[AsyncSession] = None
    ) -> Result[List[str], AttributeGraphError]:
        """
        Find objects with an attribute value in a range.
        
        Args:
            object_type: The type of object to search
            attribute_type: The attribute type name
            min_value: Optional minimum value (inclusive)
            max_value: Optional maximum value (inclusive)
            session: Optional database session
            
        Returns:
            Result containing a list of object IDs matching the criteria
        """
        try:
            # Validate parameters
            if min_value is None and max_value is None:
                return Err(AttributeGraphError("At least one of min_value or max_value must be provided"))
            
            # Construct the cypher query
            cypher_query = f"""
            MATCH (o:{object_type})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType),
                  (a)-[:HAS_VALUE]->(v)
            WHERE at.name = $attribute_type
            """
            
            params = {"attribute_type": attribute_type}
            
            # Add range conditions
            if min_value is not None:
                cypher_query += " AND v.value >= $min_value"
                params["min_value"] = str(min_value)
            
            if max_value is not None:
                cypher_query += " AND v.value <= $max_value"
                params["max_value"] = str(max_value)
            
            cypher_query += " RETURN DISTINCT o.id"
            
            # Execute the query
            if session:
                result = await self._execute_cypher_query(cypher_query, params, session)
            else:
                async with enhanced_async_session() as s:
                    result = await self._execute_cypher_query(cypher_query, params, s)
            
            return Ok(result)
            
        except Exception as e:
            self.logger.error(f"Error finding objects by attribute range: {e}")
            return Err(AttributeGraphError(f"Error finding objects by attribute range: {str(e)}"))
    
    async def count_objects_with_attribute(
        self,
        object_type: str,
        attribute_type: str,
        value: Optional[Any] = None,
        session: Optional[AsyncSession] = None
    ) -> Result[int, AttributeGraphError]:
        """
        Count objects with a specific attribute type and optionally a value.
        
        Args:
            object_type: The type of object to count
            attribute_type: The attribute type name
            value: Optional attribute value to match
            session: Optional database session
            
        Returns:
            Result containing the count of matching objects
        """
        try:
            # Construct the cypher query
            cypher_query = f"""
            MATCH (o:{object_type})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:ATTRIBUTE_TYPE]->(at:AttributeType)
            WHERE at.name = $attribute_type
            """
            
            params = {"attribute_type": attribute_type}
            
            # Add value condition if provided
            if value is not None:
                cypher_query += """
                MATCH (a)-[:HAS_VALUE]->(v)
                WHERE v.value = $value
                """
                params["value"] = str(value)
            
            cypher_query += " RETURN COUNT(DISTINCT o) as count"
            
            # Execute the query
            if session:
                result = await session.execute(
                    text(f"""
                    SELECT COUNT(*) FROM cypher('graph', $cypher_query$
                        {cypher_query}
                    $cypher_query$, $params$:=$cypher_params$) AS (count BIGINT)
                    """),
                    {"cypher_params": params}
                )
                count = result.scalar() or 0
            else:
                async with enhanced_async_session() as s:
                    result = await s.execute(
                        text(f"""
                        SELECT COUNT(*) FROM cypher('graph', $cypher_query$
                            {cypher_query}
                        $cypher_query$, $params$:=$cypher_params$) AS (count BIGINT)
                        """),
                        {"cypher_params": params}
                    )
                    count = result.scalar() or 0
            
            return Ok(count)
            
        except Exception as e:
            self.logger.error(f"Error counting objects with attribute: {e}")
            return Err(AttributeGraphError(f"Error counting objects with attribute: {str(e)}"))
    
    async def _execute_cypher_query(
        self,
        cypher_query: str,
        params: Dict[str, Any],
        session: AsyncSession
    ) -> List[str]:
        """
        Execute a cypher query and return the results.
        
        Args:
            cypher_query: The cypher query to execute
            params: Query parameters
            session: Database session
            
        Returns:
            List of object IDs from the query results
        """
        result = await session.execute(
            text(f"""
            SELECT id FROM cypher('graph', $cypher_query$
                {cypher_query}
            $cypher_query$, $params$:=$cypher_params$) AS (id TEXT)
            """),
            {"cypher_params": params}
        )
        
        return [row[0] for row in result.fetchall()]


# Create singleton instance
attribute_graph_query = AttributeGraphQuery()


def get_attribute_graph_query() -> AttributeGraphQuery:
    """
    Get the attribute graph query singleton instance.
    
    Returns:
        The attribute graph query instance
    """
    return attribute_graph_query