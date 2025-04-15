"""
Query optimizer for database operations.

This module provides a query optimization system that analyzes
and improves SQL queries for better performance, with automatic
indexing recommendations and query rewriting.

Features:
- Query plan analysis
- Index recommendations
- Automatic query rewriting
- Performance statistics tracking
- Query execution monitoring
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union, Type, cast
import asyncio
import dataclasses
import enum
import json
import logging
import re
import time
from dataclasses import dataclass, field

from sqlalchemy import text, select, inspect, Table, Column, func
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, AsyncConnection
from sqlalchemy.sql import Select, Executable
from sqlalchemy.orm import DeclarativeMeta, joinedload, selectinload

from uno.core.errors.result import Result as OpResult, Success, Failure


class QueryComplexity(enum.Enum):
    """
    Complexity levels for database queries.
    
    Used to categorize queries for optimization strategies.
    """
    
    SIMPLE = "simple"           # Simple queries with no joins or aggregations
    MODERATE = "moderate"       # Queries with simple joins or basic aggregations
    COMPLEX = "complex"         # Queries with multiple joins or complex aggregations
    VERY_COMPLEX = "very_complex"  # Queries with multiple joins and complex aggregations


class OptimizationLevel(enum.Enum):
    """
    Optimization levels for query optimization.
    
    Controls how aggressively to optimize queries.
    """
    
    NONE = "none"               # No optimization
    BASIC = "basic"             # Basic optimizations only
    STANDARD = "standard"       # Standard optimization level (default)
    AGGRESSIVE = "aggressive"   # Aggressive optimization (might alter query behavior)


class IndexType(enum.Enum):
    """
    Types of database indexes.
    
    Different index types for different query patterns.
    """
    
    BTREE = "btree"             # Standard B-tree index
    HASH = "hash"               # Hash index for equality comparisons
    GIN = "gin"                 # GIN index for full-text search
    GIST = "gist"               # GiST index for geometric and custom data types
    BRIN = "brin"               # BRIN index for large tables with natural ordering
    VECTOR = "vector"           # Vector index for vector search


@dataclass
class QueryPlan:
    """
    Parsed database query execution plan.
    
    Extracted and structured from database EXPLAIN output.
    """
    
    # Basic plan info
    plan_type: str
    estimated_cost: float
    estimated_rows: int
    
    # Plan details
    operations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Analysis
    table_scans: List[str] = field(default_factory=list)
    index_usage: Dict[str, str] = field(default_factory=dict)
    join_types: List[str] = field(default_factory=list)
    
    # Metrics
    total_cost: float = 0.0
    execution_time: Optional[float] = None
    
    @property
    def has_sequential_scans(self) -> bool:
        """Check if the plan contains sequential table scans."""
        return bool(self.table_scans)
    
    @property
    def has_nested_loops(self) -> bool:
        """Check if the plan contains nested loop joins."""
        return "Nested Loop" in self.join_types
    
    @property
    def complexity(self) -> QueryComplexity:
        """Determine the complexity of the query from the plan."""
        if not self.join_types and not self.operations:
            return QueryComplexity.SIMPLE
        
        if len(self.join_types) <= 1 and len(self.operations) <= 3:
            return QueryComplexity.MODERATE
        
        if len(self.join_types) <= 3 and len(self.operations) <= 10:
            return QueryComplexity.COMPLEX
        
        return QueryComplexity.VERY_COMPLEX


@dataclass
class IndexRecommendation:
    """
    Recommendation for a database index to improve query performance.
    
    Contains all information needed to create the index.
    """
    
    # Index details
    table_name: str
    column_names: List[str]
    index_type: IndexType = IndexType.BTREE
    index_name: Optional[str] = None
    
    # Context
    query_pattern: Optional[str] = None
    estimated_improvement: Optional[float] = None
    
    # Status
    implemented: bool = False
    implementation_time: Optional[float] = None
    
    # Creation SQL
    _creation_sql: Optional[str] = None
    
    def get_creation_sql(self) -> str:
        """
        Get the SQL statement to create this index.
        
        Returns:
            SQL CREATE INDEX statement
        """
        if self._creation_sql is not None:
            return self._creation_sql
        
        # Generate a name if not provided
        index_name = self.index_name
        if index_name is None:
            column_suffix = "_".join(self.column_names)
            index_name = f"idx_{self.table_name}_{column_suffix}"
        
        # Generate the CREATE INDEX statement
        columns = ", ".join(self.column_names)
        
        index_method = ""
        if self.index_type != IndexType.BTREE:
            index_method = f" USING {self.index_type.value}"
        
        sql = f"CREATE INDEX {index_name} ON {self.table_name}{index_method} ({columns})"
        
        self._creation_sql = sql
        return sql
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with index recommendation details
        """
        return {
            "table_name": self.table_name,
            "column_names": self.column_names,
            "index_type": self.index_type.value,
            "index_name": self.index_name,
            "query_pattern": self.query_pattern,
            "estimated_improvement": self.estimated_improvement,
            "implemented": self.implemented,
            "implementation_time": self.implementation_time,
            "creation_sql": self.get_creation_sql(),
        }


@dataclass
class QueryRewrite:
    """
    Rewritten query for better performance.
    
    Contains both original and rewritten query with improvement metrics.
    """
    
    # Query info
    original_query: str
    rewritten_query: str
    rewrite_type: str
    
    # Improvement metrics
    estimated_improvement: Optional[float] = None
    actual_improvement: Optional[float] = None
    
    # Context
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with query rewrite details
        """
        return {
            "original_query": self.original_query,
            "rewritten_query": self.rewritten_query,
            "rewrite_type": self.rewrite_type,
            "estimated_improvement": self.estimated_improvement,
            "actual_improvement": self.actual_improvement,
            "reason": self.reason,
        }


@dataclass
class QueryStatistics:
    """
    Performance statistics for a query.
    
    Tracks execution time and other metrics over time.
    """
    
    # Query info
    query_hash: str
    query_text: str
    
    # Execution stats
    execution_count: int = 0
    total_execution_time: float = 0.0
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    
    # Result stats
    avg_result_size: float = 0.0
    
    # Timeline
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    
    # Query plan
    latest_plan: Optional[QueryPlan] = None
    
    def record_execution(self, execution_time: float, result_size: int) -> None:
        """
        Record a query execution.
        
        Args:
            execution_time: Time taken to execute the query in seconds
            result_size: Size of the result set (row count)
        """
        self.execution_count += 1
        self.total_execution_time += execution_time
        self.last_seen = time.time()
        
        # Update min/max execution time
        if self.min_execution_time is None or execution_time < self.min_execution_time:
            self.min_execution_time = execution_time
        
        if self.max_execution_time is None or execution_time > self.max_execution_time:
            self.max_execution_time = execution_time
        
        # Update average result size
        new_avg = ((self.avg_result_size * (self.execution_count - 1)) + result_size) / self.execution_count
        self.avg_result_size = new_avg
    
    @property
    def avg_execution_time(self) -> float:
        """Get the average execution time in seconds."""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count
    
    @property
    def frequency(self) -> float:
        """Get the execution frequency (executions per hour)."""
        elapsed_time = self.last_seen - self.first_seen
        if elapsed_time <= 0:
            return 0.0
        
        hours = elapsed_time / 3600.0
        if hours <= 0:
            return float(self.execution_count)
        
        return self.execution_count / hours
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with query statistics
        """
        return {
            "query_hash": self.query_hash,
            "query_text": self.query_text,
            "execution_count": self.execution_count,
            "avg_execution_time": self.avg_execution_time,
            "min_execution_time": self.min_execution_time,
            "max_execution_time": self.max_execution_time,
            "total_execution_time": self.total_execution_time,
            "avg_result_size": self.avg_result_size,
            "frequency": self.frequency,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


@dataclass
class OptimizationConfig:
    """
    Configuration for the query optimizer.
    
    Controls optimization behavior and settings.
    """
    
    # General settings
    enabled: bool = True
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    
    # Analysis settings
    analyze_queries: bool = True
    collect_statistics: bool = True
    
    # Rewrite settings
    rewrite_queries: bool = True
    safe_rewrites_only: bool = True
    
    # Index settings
    recommend_indexes: bool = True
    auto_implement_indexes: bool = False
    index_creation_threshold: float = 0.5  # 50% estimated improvement threshold
    
    # Performance thresholds
    slow_query_threshold: float = 1.0  # 1 second
    very_slow_query_threshold: float = 5.0  # 5 seconds
    
    # Logging
    log_recommendations: bool = True
    log_rewrites: bool = True
    log_slow_queries: bool = True
    
    # Advanced settings
    max_recommendations_per_query: int = 3
    min_query_frequency_for_index: float = 10.0  # 10 executions per hour


class QueryOptimizer:
    """
    Optimizer for database queries.
    
    Analyzes, optimizes, and tracks queries for improved performance.
    """
    
    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        engine: Optional[AsyncEngine] = None,
        config: Optional[OptimizationConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the query optimizer.
        
        Args:
            session: Optional AsyncSession to use
            engine: Optional AsyncEngine to use
            config: Optional configuration
            logger: Optional logger instance
        """
        self.session = session
        self.engine = engine
        self.config = config or OptimizationConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # Query statistics
        self._query_stats: Dict[str, QueryStatistics] = {}
        
        # Index recommendations
        self._index_recommendations: List[IndexRecommendation] = []
        
        # Query rewrites
        self._query_rewrites: Dict[str, QueryRewrite] = {}
        
        # Schema information
        self._table_info: Dict[str, Dict[str, Any]] = {}
        self._existing_indexes: Dict[str, List[Dict[str, Any]]] = {}
    
    async def analyze_query(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryPlan:
        """
        Analyze a query and extract its execution plan.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            
        Returns:
            Parsed query plan
            
        Raises:
            ValueError: If neither session nor engine is available
        """
        if not self.session and not self.engine:
            raise ValueError("Either session or engine must be provided")
        
        # Convert query to string if it's a SQLAlchemy executable
        query_str = query
        if not isinstance(query, str):
            if hasattr(query, "compile"):
                compiled = query.compile(compile_kwargs={"literal_binds": True})
                query_str = str(compiled)
            else:
                query_str = str(query)
        
        # Build EXPLAIN query
        explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query_str}"
        
        # Execute the EXPLAIN query
        connection = None
        try:
            if self.session:
                result = await self.session.execute(text(explain_query), params or {})
                plan_json = await result.scalar()
            else:
                async with self.engine.connect() as connection:
                    result = await connection.execute(text(explain_query), params or {})
                    plan_json = await result.scalar()
            
            # Parse the JSON plan
            if isinstance(plan_json, str):
                plan_data = json.loads(plan_json)
            else:
                plan_data = plan_json
            
            # Extract plan information
            if isinstance(plan_data, list) and len(plan_data) > 0:
                plan_details = plan_data[0]
            else:
                plan_details = plan_data
            
            # Extract the plan node
            if "Plan" in plan_details:
                plan_node = plan_details["Plan"]
            else:
                plan_node = plan_details
            
            # Create QueryPlan object
            plan = QueryPlan(
                plan_type=plan_node.get("Node Type", "Unknown"),
                estimated_cost=float(plan_node.get("Total Cost", 0.0)),
                estimated_rows=int(plan_node.get("Plan Rows", 0)),
                total_cost=float(plan_node.get("Total Cost", 0.0)),
                execution_time=float(plan_details.get("Execution Time", 0.0)) / 1000.0,
            )
            
            # Extract operations
            plan.operations = self._extract_operations(plan_node)
            
            # Extract table scans
            plan.table_scans = self._extract_table_scans(plan_node)
            
            # Extract index usage
            plan.index_usage = self._extract_index_usage(plan_node)
            
            # Extract join types
            plan.join_types = self._extract_join_types(plan_node)
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            # Return a simple plan with default values
            return QueryPlan(
                plan_type="Unknown",
                estimated_cost=0.0,
                estimated_rows=0,
            )
    
    def _extract_operations(self, plan_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract operations from a plan node recursively.
        
        Args:
            plan_node: Plan node to extract operations from
            
        Returns:
            List of operations in the plan
        """
        operations = []
        
        # Add the current node
        operations.append({
            "type": plan_node.get("Node Type", "Unknown"),
            "cost": float(plan_node.get("Total Cost", 0.0)),
            "rows": int(plan_node.get("Plan Rows", 0)),
            "width": int(plan_node.get("Plan Width", 0)),
        })
        
        # Recursively process child nodes
        for child_key in ["Plans", "Child"]:
            if child_key in plan_node:
                child_nodes = plan_node[child_key]
                if not isinstance(child_nodes, list):
                    child_nodes = [child_nodes]
                
                for child in child_nodes:
                    operations.extend(self._extract_operations(child))
        
        return operations
    
    def _extract_table_scans(self, plan_node: Dict[str, Any]) -> List[str]:
        """
        Extract sequential table scans from a plan node.
        
        Args:
            plan_node: Plan node to extract scans from
            
        Returns:
            List of table names with sequential scans
        """
        scans = []
        
        # Check if this node is a sequential scan
        if plan_node.get("Node Type") == "Seq Scan":
            relation = plan_node.get("Relation Name")
            if relation:
                scans.append(relation)
        
        # Recursively process child nodes
        for child_key in ["Plans", "Child"]:
            if child_key in plan_node:
                child_nodes = plan_node[child_key]
                if not isinstance(child_nodes, list):
                    child_nodes = [child_nodes]
                
                for child in child_nodes:
                    scans.extend(self._extract_table_scans(child))
        
        return scans
    
    def _extract_index_usage(self, plan_node: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract index usage from a plan node.
        
        Args:
            plan_node: Plan node to extract index usage from
            
        Returns:
            Dictionary mapping table names to used indexes
        """
        index_usage = {}
        
        # Check if this node is an index scan or index only scan
        if plan_node.get("Node Type") in ["Index Scan", "Index Only Scan"]:
            relation = plan_node.get("Relation Name")
            index = plan_node.get("Index Name")
            
            if relation and index:
                index_usage[relation] = index
        
        # Recursively process child nodes
        for child_key in ["Plans", "Child"]:
            if child_key in plan_node:
                child_nodes = plan_node[child_key]
                if not isinstance(child_nodes, list):
                    child_nodes = [child_nodes]
                
                for child in child_nodes:
                    child_usage = self._extract_index_usage(child)
                    index_usage.update(child_usage)
        
        return index_usage
    
    def _extract_join_types(self, plan_node: Dict[str, Any]) -> List[str]:
        """
        Extract join types from a plan node.
        
        Args:
            plan_node: Plan node to extract join types from
            
        Returns:
            List of join types in the plan
        """
        join_types = []
        
        # Check if this node is a join
        node_type = plan_node.get("Node Type", "")
        if "Join" in node_type:
            join_types.append(node_type)
        
        # Recursively process child nodes
        for child_key in ["Plans", "Child"]:
            if child_key in plan_node:
                child_nodes = plan_node[child_key]
                if not isinstance(child_nodes, list):
                    child_nodes = [child_nodes]
                
                for child in child_nodes:
                    join_types.extend(self._extract_join_types(child))
        
        return join_types
    
    def recommend_indexes(self, query_plan: QueryPlan) -> List[IndexRecommendation]:
        """
        Recommend indexes based on a query plan.
        
        Args:
            query_plan: Query plan to analyze
            
        Returns:
            List of index recommendations
        """
        if not self.config.recommend_indexes:
            return []
        
        recommendations = []
        
        # Look for sequential scans with filters
        for table_name in query_plan.table_scans:
            # Only recommend if we have schema information
            if table_name in self._table_info:
                table_info = self._table_info[table_name]
                
                # Analyze operations to find filter conditions
                filter_columns = self._extract_filter_columns(table_name, query_plan.operations)
                
                if filter_columns:
                    # Check if an index already exists for these columns
                    if not self._has_matching_index(table_name, filter_columns):
                        # Create an index recommendation
                        rec = IndexRecommendation(
                            table_name=table_name,
                            column_names=filter_columns,
                            index_type=IndexType.BTREE,
                            estimated_improvement=self._estimate_index_improvement(query_plan),
                        )
                        
                        # Only include if estimated improvement is significant
                        if rec.estimated_improvement and rec.estimated_improvement >= self.config.index_creation_threshold:
                            recommendations.append(rec)
        
        # Sort by estimated improvement
        recommendations.sort(key=lambda r: r.estimated_improvement or 0.0, reverse=True)
        
        # Limit to max recommendations
        return recommendations[:self.config.max_recommendations_per_query]
    
    def _extract_filter_columns(self, table_name: str, operations: List[Dict[str, Any]]) -> List[str]:
        """
        Extract filter columns for a table from operations.
        
        This is a simplified analysis - in a real implementation,
        this would parse the actual conditions from the plan.
        
        Args:
            table_name: Table to extract filter columns for
            operations: List of operations in the plan
            
        Returns:
            List of column names to index
        """
        # This is a placeholder implementation
        # In a real system, this would analyze the filter conditions in the plan
        filter_columns = []
        
        # Look for filter operations
        for op in operations:
            if op["type"] in ["Seq Scan", "Filter", "Index Scan"]:
                # In a real implementation, we would extract column names from filter conditions
                # For this example, we'll return a placeholder
                filter_columns = ["id", "status"]
        
        return filter_columns
    
    def _has_matching_index(self, table_name: str, columns: List[str]) -> bool:
        """
        Check if a table already has an index on the specified columns.
        
        Args:
            table_name: Table name to check
            columns: List of column names
            
        Returns:
            True if an index exists, False otherwise
        """
        # Get existing indexes for the table
        existing_indexes = self._existing_indexes.get(table_name, [])
        
        # Check if any existing index covers these columns
        for index in existing_indexes:
            index_columns = index.get("columns", [])
            
            # Check if index columns match or start with our columns
            if len(index_columns) >= len(columns):
                matches = True
                for i, col in enumerate(columns):
                    if i >= len(index_columns) or index_columns[i] != col:
                        matches = False
                        break
                
                if matches:
                    return True
        
        return False
    
    def _estimate_index_improvement(self, query_plan: QueryPlan) -> float:
        """
        Estimate the improvement from adding an index.
        
        Args:
            query_plan: Query plan to analyze
            
        Returns:
            Estimated improvement factor (0.0-1.0)
        """
        # This is a simplified estimation
        # In a real implementation, this would use the plan details to estimate improvement
        
        # If no sequential scans, no improvement expected
        if not query_plan.has_sequential_scans:
            return 0.0
        
        # Simple heuristic: more sequential scans = more improvement potential
        scan_count = len(query_plan.table_scans)
        
        if scan_count == 1:
            return 0.3  # 30% improvement
        elif scan_count == 2:
            return 0.5  # 50% improvement
        else:
            return 0.7  # 70% improvement
    
    async def rewrite_query(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
    ) -> OpResult[QueryRewrite]:
        """
        Rewrite a query for better performance.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            
        Returns:
            Result containing QueryRewrite on success, error message on failure
        """
        if not self.config.rewrite_queries:
            return Failure("Query rewriting is disabled")
        
        # Convert query to string if it's a SQLAlchemy executable
        query_str = query
        if not isinstance(query, str):
            if hasattr(query, "compile"):
                compiled = query.compile(compile_kwargs={"literal_binds": True})
                query_str = str(compiled)
            else:
                query_str = str(query)
        
        # Apply rewrite rules
        for rule_func in [
            self._rewrite_unnecessary_distinct,
            self._rewrite_count_star,
            self._rewrite_or_to_union,
            self._rewrite_in_clause,
        ]:
            result = rule_func(query_str)
            if result.is_success:
                rewrite = result.value
                
                # Log the rewrite if enabled
                if self.config.log_rewrites:
                    self.logger.info(
                        f"Rewrote query with {rewrite.rewrite_type}: "
                        f"Estimated improvement: {rewrite.estimated_improvement or 0.0:.2f}"
                    )
                
                # Store the rewrite
                query_hash = self._hash_query(query_str)
                self._query_rewrites[query_hash] = rewrite
                
                return Success(rewrite)
        
        # No rewrites applied
        return Failure("No applicable rewrites found")
    
    def _rewrite_unnecessary_distinct(self, query: str) -> OpResult[QueryRewrite]:
        """
        Remove unnecessary DISTINCT clauses.
        
        Args:
            query: SQL query string
            
        Returns:
            Result containing QueryRewrite on success, error message on failure
        """
        # Look for DISTINCT on primary key or unique columns
        pattern = r"SELECT\s+DISTINCT(.*?)\s+FROM\s+(\w+)"
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return Failure("No DISTINCT clause found")
        
        columns = match.group(1).strip()
        table = match.group(2).strip()
        
        # Check if columns include primary key or unique columns
        # This is a simplified check - in real implementation, would use schema information
        if "id" in columns.lower() or "uuid" in columns.lower():
            # Rewrite by removing DISTINCT
            rewritten = query.replace(
                f"SELECT DISTINCT{match.group(1)}",
                f"SELECT{match.group(1)}"
            )
            
            return Success(QueryRewrite(
                original_query=query,
                rewritten_query=rewritten,
                rewrite_type="remove_unnecessary_distinct",
                estimated_improvement=0.2,  # 20% improvement
                reason="DISTINCT is unnecessary when selecting primary key or unique columns",
            ))
        
        return Failure("DISTINCT may be necessary")
    
    def _rewrite_count_star(self, query: str) -> OpResult[QueryRewrite]:
        """
        Optimize COUNT(*) queries.
        
        Args:
            query: SQL query string
            
        Returns:
            Result containing QueryRewrite on success, error message on failure
        """
        # Look for COUNT(*) without WHERE clause
        pattern = r"SELECT\s+COUNT\(\*\)\s+FROM\s+(\w+)(?:\s+WHERE\s+.+)?$"
        match = re.search(pattern, query, re.IGNORECASE)
        
        if not match:
            return Failure("Not a COUNT(*) query")
        
        table = match.group(1).strip()
        
        # Check if there's a WHERE clause
        has_where = "WHERE" in query.upper()
        
        if not has_where:
            # For tables with primary key, COUNT(1) is slightly faster
            rewritten = query.replace("COUNT(*)", "COUNT(1)")
            
            return Success(QueryRewrite(
                original_query=query,
                rewritten_query=rewritten,
                rewrite_type="optimize_count",
                estimated_improvement=0.1,  # 10% improvement
                reason="COUNT(1) is slightly faster than COUNT(*) for simple counts",
            ))
        
        return Failure("Query already has WHERE clause, COUNT(*) optimization not applicable")
    
    def _rewrite_or_to_union(self, query: str) -> OpResult[QueryRewrite]:
        """
        Rewrite OR conditions to UNION for better index usage.
        
        Args:
            query: SQL query string
            
        Returns:
            Result containing QueryRewrite on success, error message on failure
        """
        # Only apply if in aggressive mode
        if self.config.optimization_level != OptimizationLevel.AGGRESSIVE:
            return Failure("OR to UNION rewrite requires aggressive optimization")
        
        # Look for OR conditions on different columns
        pattern = r"WHERE\s+(.+?)\s+OR\s+(.+?)(?:\s+ORDER BY|\s+GROUP BY|\s+LIMIT|\s*$)"
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return Failure("No suitable OR conditions found")
        
        left_condition = match.group(1).strip()
        right_condition = match.group(2).strip()
        
        # Check if conditions are on different columns
        left_column = left_condition.split("=")[0].strip() if "=" in left_condition else ""
        right_column = right_condition.split("=")[0].strip() if "=" in right_condition else ""
        
        if left_column and right_column and left_column != right_column:
            # Extract the parts before and after the WHERE clause
            before_where = query[:match.start()].strip()
            after_where = query[match.end():].strip()
            
            # Create UNION query
            rewritten = (
                f"{before_where} WHERE {left_condition} "
                f"UNION ALL "
                f"{before_where} WHERE {right_condition} "
            )
            
            if after_where:
                rewritten += f" {after_where}"
            
            return Success(QueryRewrite(
                original_query=query,
                rewritten_query=rewritten,
                rewrite_type="or_to_union",
                estimated_improvement=0.4,  # 40% improvement
                reason="Splitting OR conditions on different columns into UNION can improve index usage",
            ))
        
        return Failure("OR conditions not suitable for UNION rewrite")
    
    def _rewrite_in_clause(self, query: str) -> OpResult[QueryRewrite]:
        """
        Optimize large IN clauses.
        
        Args:
            query: SQL query string
            
        Returns:
            Result containing QueryRewrite on success, error message on failure
        """
        # Look for large IN clauses
        pattern = r"WHERE\s+(\w+)\s+IN\s+\(([^)]+)\)"
        match = re.search(pattern, query, re.IGNORECASE)
        
        if not match:
            return Failure("No IN clause found")
        
        column = match.group(1).strip()
        values = match.group(2).strip().split(",")
        
        # Only optimize large IN clauses
        if len(values) <= 5:
            return Failure("IN clause not large enough to optimize")
        
        # For very large IN clauses, use a temporary table
        if len(values) > 100:
            # In a real implementation, we would create a temporary table
            # For this example, we'll use a VALUES clause
            temp_table = "temp_in_values"
            values_clause = ", ".join(f"({v.strip()})" for v in values)
            
            # Rewrite query to use JOIN
            original_in_clause = f"{column} IN ({match.group(2)})"
            rewritten_in_clause = f"{column} IN (SELECT value FROM {temp_table})"
            
            # Create WITH clause
            rewritten = (
                f"WITH {temp_table} (value) AS (VALUES {values_clause}) "
                f"{query.replace(original_in_clause, rewritten_in_clause)}"
            )
            
            return Success(QueryRewrite(
                original_query=query,
                rewritten_query=rewritten,
                rewrite_type="optimize_large_in",
                estimated_improvement=0.3,  # 30% improvement
                reason="Large IN clauses perform better with temporary tables",
            ))
        
        return Failure("IN clause optimization not applicable")
    
    def _hash_query(self, query: str) -> str:
        """
        Generate a hash for a query.
        
        Args:
            query: SQL query string
            
        Returns:
            Hash string for the query
        """
        import hashlib
        
        # Normalize the query (remove whitespace, convert to lowercase)
        normalized = " ".join(query.lower().split())
        
        # Create a hash
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()
    
    async def execute_optimized_query(
        self,
        query: Union[str, Executable],
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a query with optimization.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            
        Returns:
            Query result
            
        Raises:
            ValueError: If session is not provided
        """
        if not self.session:
            raise ValueError("Session must be provided for execute_optimized_query")
        
        if not self.config.enabled:
            # If optimization is disabled, execute directly
            return await self.session.execute(query, params or {})
        
        # Convert query to string if it's a SQLAlchemy executable
        query_str = query
        if not isinstance(query, str):
            if hasattr(query, "compile"):
                compiled = query.compile(compile_kwargs={"literal_binds": True})
                query_str = str(compiled)
            else:
                query_str = str(query)
        
        # Get query hash
        query_hash = self._hash_query(query_str)
        
        # Check if we have a rewrite for this query
        if query_hash in self._query_rewrites and self.config.rewrite_queries:
            rewrite = self._query_rewrites[query_hash]
            query_to_execute = rewrite.rewritten_query
        else:
            # Try to rewrite the query
            rewrite_result = await self.rewrite_query(query_str, params)
            
            if rewrite_result.is_success:
                rewrite = rewrite_result.value
                query_to_execute = rewrite.rewritten_query
            else:
                query_to_execute = query_str
        
        # Record start time
        start_time = time.time()
        
        # Execute the query
        result = await self.session.execute(text(query_to_execute), params or {})
        
        # Record execution time
        execution_time = time.time() - start_time
        
        # Convert result to a list to get size
        rows = list(result)
        result_size = len(rows)
        
        # Update query statistics
        if self.config.collect_statistics:
            if query_hash not in self._query_stats:
                self._query_stats[query_hash] = QueryStatistics(
                    query_hash=query_hash,
                    query_text=query_str,
                )
            
            self._query_stats[query_hash].record_execution(execution_time, result_size)
            
            # Get query plan for slow queries
            if execution_time >= self.config.slow_query_threshold:
                plan = await self.analyze_query(query_str, params)
                self._query_stats[query_hash].latest_plan = plan
                
                # Log slow query
                if self.config.log_slow_queries:
                    self.logger.warning(
                        f"Slow query detected ({execution_time:.2f}s): {query_str[:100]}..."
                    )
                
                # Generate index recommendations for very slow queries
                if execution_time >= self.config.very_slow_query_threshold:
                    recommendations = self.recommend_indexes(plan)
                    
                    if recommendations and self.config.log_recommendations:
                        for rec in recommendations:
                            self.logger.info(
                                f"Index recommendation for table {rec.table_name}: "
                                f"{rec.get_creation_sql()}"
                            )
                    
                    # Add to recommendations list
                    self._index_recommendations.extend(recommendations)
        
        # Return rows
        return rows
    
    async def load_schema_information(self) -> None:
        """
        Load schema information for better optimization.
        
        This includes table structure and existing indexes.
        
        Raises:
            ValueError: If neither session nor engine is available
        """
        if not self.session and not self.engine:
            raise ValueError("Either session or engine must be provided")
        
        # Get tables information
        tables_query = """
        SELECT
            table_name,
            table_schema
        FROM
            information_schema.tables
        WHERE
            table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE';
        """
        
        # Get table columns
        columns_query = """
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM
            information_schema.columns
        WHERE
            table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY
            table_name,
            ordinal_position;
        """
        
        # Get existing indexes
        indexes_query = """
        SELECT
            t.relname AS table_name,
            i.relname AS index_name,
            a.attname AS column_name,
            ix.indisunique AS is_unique,
            am.amname AS index_type
        FROM
            pg_index ix
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            JOIN pg_am am ON am.oid = i.relam
            JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE
            n.nspname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY
            t.relname,
            i.relname,
            a.attnum;
        """
        
        try:
            # Execute queries
            if self.session:
                tables_result = await self.session.execute(text(tables_query))
                columns_result = await self.session.execute(text(columns_query))
                indexes_result = await self.session.execute(text(indexes_query))
            else:
                async with self.engine.connect() as connection:
                    tables_result = await connection.execute(text(tables_query))
                    columns_result = await connection.execute(text(columns_query))
                    indexes_result = await connection.execute(text(indexes_query))
            
            # Process tables and columns
            tables = {row.table_name: {"schema": row.table_schema, "columns": []} for row in tables_result}
            
            for row in columns_result:
                if row.table_name in tables:
                    tables[row.table_name]["columns"].append({
                        "name": row.column_name,
                        "type": row.data_type,
                        "nullable": row.is_nullable == "YES",
                        "default": row.column_default,
                    })
            
            # Store table information
            self._table_info = tables
            
            # Process indexes
            indexes = {}
            
            for row in indexes_result:
                table_name = row.table_name
                index_name = row.index_name
                column_name = row.column_name
                
                if table_name not in indexes:
                    indexes[table_name] = []
                
                # Find the index if it already exists
                index = None
                for idx in indexes[table_name]:
                    if idx["name"] == index_name:
                        index = idx
                        break
                
                if index is None:
                    index = {
                        "name": index_name,
                        "columns": [],
                        "unique": row.is_unique,
                        "type": row.index_type,
                    }
                    indexes[table_name].append(index)
                
                # Add column to index
                index["columns"].append(column_name)
            
            # Store indexes
            self._existing_indexes = indexes
            
            self.logger.info(
                f"Loaded schema information: {len(tables)} tables, "
                f"{sum(len(idxs) for idxs in indexes.values())} indexes"
            )
            
        except Exception as e:
            self.logger.error(f"Error loading schema information: {e}")
    
    def get_statistics(self) -> Dict[str, QueryStatistics]:
        """
        Get collected query statistics.
        
        Returns:
            Dictionary mapping query hashes to statistics
        """
        return dict(self._query_stats)
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[QueryStatistics]:
        """
        Get statistics for slow queries.
        
        Args:
            threshold: Optional threshold in seconds (default: config.slow_query_threshold)
            
        Returns:
            List of query statistics for slow queries, sorted by execution time
        """
        if threshold is None:
            threshold = self.config.slow_query_threshold
        
        slow_queries = [
            stats for stats in self._query_stats.values()
            if stats.avg_execution_time >= threshold
        ]
        
        # Sort by average execution time
        slow_queries.sort(key=lambda s: s.avg_execution_time, reverse=True)
        
        return slow_queries
    
    def get_frequent_queries(self, min_frequency: Optional[float] = None) -> List[QueryStatistics]:
        """
        Get statistics for frequently executed queries.
        
        Args:
            min_frequency: Optional minimum frequency in queries per hour
                (default: config.min_query_frequency_for_index)
            
        Returns:
            List of query statistics for frequent queries, sorted by frequency
        """
        if min_frequency is None:
            min_frequency = self.config.min_query_frequency_for_index
        
        frequent_queries = [
            stats for stats in self._query_stats.values()
            if stats.frequency >= min_frequency
        ]
        
        # Sort by frequency
        frequent_queries.sort(key=lambda s: s.frequency, reverse=True)
        
        return frequent_queries
    
    def get_index_recommendations(self) -> List[IndexRecommendation]:
        """
        Get all index recommendations.
        
        Returns:
            List of index recommendations
        """
        return list(self._index_recommendations)
    
    async def implement_index(self, recommendation: IndexRecommendation) -> bool:
        """
        Implement an index recommendation.
        
        Args:
            recommendation: Index recommendation to implement
            
        Returns:
            True if implementation was successful, False otherwise
            
        Raises:
            ValueError: If neither session nor engine is available
            ValueError: If auto_implement_indexes is disabled
        """
        if not self.config.auto_implement_indexes:
            raise ValueError("Auto implement indexes is disabled")
        
        if not self.session and not self.engine:
            raise ValueError("Either session or engine must be provided")
        
        # Get the SQL statement
        sql = recommendation.get_creation_sql()
        
        try:
            # Execute the SQL
            if self.session:
                await self.session.execute(text(sql))
                await self.session.commit()
            else:
                async with self.engine.connect() as connection:
                    await connection.execute(text(sql))
                    await connection.commit()
            
            # Update the recommendation
            recommendation.implemented = True
            recommendation.implementation_time = time.time()
            
            # Update existing indexes
            if recommendation.table_name in self._existing_indexes:
                self._existing_indexes[recommendation.table_name].append({
                    "name": recommendation.index_name or f"idx_{recommendation.table_name}_{recommendation.column_names[0]}",
                    "columns": recommendation.column_names,
                    "unique": False,
                    "type": recommendation.index_type.value,
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error implementing index: {e}")
            return False


# Helper functions

async def optimize_query(
    query: Union[str, Executable],
    params: Optional[Dict[str, Any]] = None,
    session: Optional[AsyncSession] = None,
    engine: Optional[AsyncEngine] = None,
    config: Optional[OptimizationConfig] = None,
) -> Tuple[Union[str, Executable], Optional[List[IndexRecommendation]]]:
    """
    Optimize a query and provide recommendations.
    
    Args:
        query: SQL query string or SQLAlchemy executable
        params: Optional query parameters
        session: Optional AsyncSession to use
        engine: Optional AsyncEngine to use
        config: Optional configuration
        
    Returns:
        Tuple of (optimized query, index recommendations)
        
    Raises:
        ValueError: If neither session nor engine is provided
    """
    if not session and not engine:
        raise ValueError("Either session or engine must be provided")
    
    # Create optimizer
    optimizer = QueryOptimizer(
        session=session,
        engine=engine,
        config=config,
    )
    
    # Try to rewrite the query
    rewrite_result = await optimizer.rewrite_query(query, params)
    
    if rewrite_result.is_success:
        rewrite = rewrite_result.value
        optimized_query = rewrite.rewritten_query
    else:
        optimized_query = query
    
    # Analyze the query
    query_plan = await optimizer.analyze_query(query, params)
    
    # Get index recommendations
    recommendations = optimizer.recommend_indexes(query_plan)
    
    return optimized_query, recommendations


def optimized_query(
    config: Optional[OptimizationConfig] = None,
):
    """
    Decorator to optimize a query function.
    
    Args:
        config: Optional optimization configuration
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract session from args or kwargs
            session = None
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break
            
            if session is None and "session" in kwargs:
                session = kwargs["session"]
            
            if session is None:
                # No session found, can't optimize
                return await func(*args, **kwargs)
            
            # Try to extract the query
            # This would require inspecting the function source
            # For this example, we'll execute the function normally
            
            # Create optimizer
            optimizer = QueryOptimizer(
                session=session,
                config=config,
            )
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # For demonstration purposes, add some logging
            if hasattr(result, "statement"):
                query_str = str(result.statement)
                query_hash = optimizer._hash_query(query_str)
                
                # Only log once per query
                if query_hash not in optimizer._query_stats:
                    optimizer.logger.info(f"Executing optimized query: {query_str[:100]}...")
            
            return result
            
        return wrapper
    
    return decorator