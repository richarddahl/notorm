"""
PostgreSQL-specific optimization strategies for the query optimizer.

This module provides specialized optimization strategies that leverage
PostgreSQL-specific features for improved performance.
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Set
import re
import json
import logging
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, AsyncConnection
from sqlalchemy.sql import Select, Executable

from uno.core.errors.result import Result as OpResult, Success, Failure
from uno.database.query_optimizer import (
    QueryComplexity,
    OptimizationLevel,
    IndexType,
    QueryPlan,
    IndexRecommendation,
    QueryRewrite,
    QueryOptimizer,
)


@dataclass
class PgIndexRecommendation(IndexRecommendation):
    """
    Extended index recommendation for PostgreSQL.
    
    Adds PostgreSQL-specific index features.
    """
    
    # PostgreSQL specific index options
    include_columns: List[str] = field(default_factory=list)
    is_unique: bool = False
    is_partial: bool = False
    where_clause: Optional[str] = None
    operator_class: Optional[str] = None
    index_tablespace: Optional[str] = None
    
    def get_creation_sql(self) -> str:
        """
        Get the SQL statement to create this index.
        
        Returns:
            SQL CREATE INDEX statement with PostgreSQL extensions
        """
        # Generate a name if not provided
        index_name = self.index_name
        if index_name is None:
            column_suffix = "_".join(self.column_names)
            index_name = f"idx_{self.table_name}_{column_suffix}"
        
        # Generate the CREATE INDEX statement
        sql_parts = []
        sql_parts.append("CREATE")
        
        if self.is_unique:
            sql_parts.append("UNIQUE")
            
        sql_parts.append("INDEX")
        sql_parts.append(index_name)
        sql_parts.append(f"ON {self.table_name}")
        
        if self.index_type != IndexType.BTREE:
            sql_parts.append(f"USING {self.index_type.value}")
        
        # Add columns with operator class if specified
        columns = []
        for col in self.column_names:
            if self.operator_class and col == self.column_names[0]:
                columns.append(f"{col} {self.operator_class}")
            else:
                columns.append(col)
                
        sql_parts.append(f"({', '.join(columns)})")
        
        # Add INCLUDE clause for covering indexes
        if self.include_columns:
            sql_parts.append(f"INCLUDE ({', '.join(self.include_columns)})")
        
        # Add WHERE clause for partial indexes
        if self.is_partial and self.where_clause:
            sql_parts.append(f"WHERE {self.where_clause}")
        
        # Add tablespace if specified
        if self.index_tablespace:
            sql_parts.append(f"TABLESPACE {self.index_tablespace}")
            
        return " ".join(sql_parts)


class PgOptimizationStrategies:
    """
    PostgreSQL-specific optimization strategies.
    
    Provides additional optimization techniques leveraging PostgreSQL features.
    """
    
    def __init__(self, optimizer: QueryOptimizer):
        """
        Initialize PostgreSQL optimization strategies.
        
        Args:
            optimizer: The query optimizer to extend
        """
        self.optimizer = optimizer
        self.logger = optimizer.logger
    
    async def analyze_table(self, table_name: str) -> OpResult[Dict[str, Any]]:
        """
        Run ANALYZE on a table to update statistics.
        
        Args:
            table_name: The name of the table to analyze
            
        Returns:
            Result with success message or error
        """
        if not self.optimizer.session and not self.optimizer.engine:
            return Failure("Either session or engine must be provided")
        
        try:
            analyze_sql = f"ANALYZE {table_name}"
            
            if self.optimizer.session:
                await self.optimizer.session.execute(text(analyze_sql))
                await self.optimizer.session.commit()
            else:
                async with self.optimizer.engine.connect() as connection:
                    await connection.execute(text(analyze_sql))
                    await connection.commit()
            
            return Success({"message": f"Successfully analyzed table {table_name}"})
            
        except Exception as e:
            error_msg = f"Error analyzing table {table_name}: {e}"
            self.logger.error(error_msg)
            return Failure(error_msg)
    
    async def get_table_statistics(self, table_name: str) -> OpResult[Dict[str, Any]]:
        """
        Get statistics for a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            Result with table statistics or error
        """
        if not self.optimizer.session and not self.optimizer.engine:
            return Failure("Either session or engine must be provided")
        
        try:
            stats_sql = f"""
            SELECT
                pg_class.relname AS table_name,
                pg_class.reltuples::bigint AS row_estimate,
                pg_class.relpages::bigint AS page_count,
                pg_total_relation_size(pg_class.oid) AS total_bytes,
                pg_relation_size(pg_class.oid) AS table_bytes,
                pg_indexes_size(pg_class.oid) AS index_bytes,
                pg_stat_get_numscans(pg_class.oid) AS seq_scan_count,
                pg_stat_get_tuples_returned(pg_class.oid) AS seq_scan_rows,
                pg_stat_get_tuples_fetched(pg_class.oid) AS seq_scan_rows_fetched
            FROM
                pg_class
            WHERE
                pg_class.relname = :table_name
            """
            
            # Column statistics
            col_stats_sql = f"""
            SELECT
                pg_attribute.attname AS column_name,
                pg_stats.n_distinct AS distinct_values,
                pg_stats.null_frac AS null_fraction,
                pg_stats.most_common_vals AS common_values,
                pg_stats.most_common_freqs AS common_freqs,
                pg_stats.correlation AS correlation
            FROM
                pg_stats
            JOIN
                pg_attribute ON pg_stats.attname = pg_attribute.attname
            JOIN
                pg_class ON pg_class.relname = pg_stats.tablename
            WHERE
                pg_stats.tablename = :table_name
                AND pg_attribute.attrelid = pg_class.oid
                AND pg_attribute.attnum > 0
            """
            
            if self.optimizer.session:
                stats_result = await self.optimizer.session.execute(
                    text(stats_sql), {"table_name": table_name}
                )
                stats_data = stats_result.mappings().first()
                
                col_stats_result = await self.optimizer.session.execute(
                    text(col_stats_sql), {"table_name": table_name}
                )
                column_stats = [dict(row) for row in col_stats_result.mappings()]
                
            else:
                async with self.optimizer.engine.connect() as connection:
                    stats_result = await connection.execute(
                        text(stats_sql), {"table_name": table_name}
                    )
                    stats_data = stats_result.mappings().first()
                    
                    col_stats_result = await connection.execute(
                        text(col_stats_sql), {"table_name": table_name}
                    )
                    column_stats = [dict(row) for row in col_stats_result.mappings()]
            
            if not stats_data:
                return Failure(f"Table {table_name} not found or no statistics available")
            
            # Convert to dict and add column stats
            stats = dict(stats_data)
            stats["columns"] = column_stats
            
            # Calculate some derived metrics
            if stats["row_estimate"] > 0:
                stats["avg_row_size"] = stats["table_bytes"] / stats["row_estimate"]
            else:
                stats["avg_row_size"] = 0
            
            # Format sizes for easier reading
            for size_key in ["total_bytes", "table_bytes", "index_bytes"]:
                bytes_value = stats[size_key]
                stats[f"{size_key}_human"] = self._format_bytes(bytes_value)
            
            return Success(stats)
            
        except Exception as e:
            error_msg = f"Error getting statistics for table {table_name}: {e}"
            self.logger.error(error_msg)
            return Failure(error_msg)
    
    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes to human-readable string"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    async def recommend_table_maintenance(
        self, table_name: str
    ) -> OpResult[Dict[str, Any]]:
        """
        Recommend maintenance operations for a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            Result with maintenance recommendations or error
        """
        # Get table statistics
        stats_result = await self.get_table_statistics(table_name)
        if stats_result.is_failure:
            return stats_result
        
        stats = stats_result.value
        
        # Initialize recommendations
        recommendations = []
        
        # Check for bloat (estimated)
        if "table_bytes" in stats and "row_estimate" in stats and "avg_row_size" in stats:
            estimated_size = stats["row_estimate"] * stats["avg_row_size"]
            actual_size = stats["table_bytes"]
            
            if actual_size > estimated_size * 1.3:  # 30% bloat
                bloat_percentage = (actual_size - estimated_size) / actual_size * 100
                recommendations.append({
                    "type": "VACUUM",
                    "reason": f"Table has approximately {bloat_percentage:.1f}% bloat",
                    "sql": f"VACUUM (FULL, ANALYZE) {table_name}",
                    "priority": "high" if bloat_percentage > 50 else "medium"
                })
        
        # Check for outdated statistics
        if "seq_scan_count" in stats and stats["seq_scan_count"] > 10:
            recommendations.append({
                "type": "ANALYZE",
                "reason": "Table has been scanned frequently, statistics may be outdated",
                "sql": f"ANALYZE {table_name}",
                "priority": "medium"
            })
        
        # Check for index to table size ratio
        if "index_bytes" in stats and "table_bytes" in stats and stats["table_bytes"] > 0:
            index_ratio = stats["index_bytes"] / stats["table_bytes"]
            if index_ratio > 2.0:
                recommendations.append({
                    "type": "REVIEW_INDEXES",
                    "reason": f"Index size ({stats['index_bytes_human']}) is {index_ratio:.1f}x larger than table size ({stats['table_bytes_human']})",
                    "sql": f"SELECT * FROM pg_indexes WHERE tablename = '{table_name}'",
                    "priority": "medium"
                })
        
        # Check correlation for ordering
        for col in stats.get("columns", []):
            if "correlation" in col and abs(col["correlation"]) < 0.5:
                recommendations.append({
                    "type": "CLUSTER",
                    "reason": f"Column {col['column_name']} has low correlation ({col['correlation']:.2f}), table might benefit from clustering",
                    "sql": f"CLUSTER {table_name} USING {table_name}_pkey",  # Assumes primary key index
                    "priority": "low"
                })
        
        return Success({
            "table_name": table_name,
            "statistics": stats,
            "recommendations": recommendations
        })
    
    def recommend_covering_index(
        self, query_plan: QueryPlan, query_text: str
    ) -> List[PgIndexRecommendation]:
        """
        Recommend covering indexes for a query.
        
        Args:
            query_plan: The query plan to analyze
            query_text: The original query text
            
        Returns:
            List of covering index recommendations
        """
        recommendations = []
        
        # Only proceed if we have sequential scans
        if not query_plan.has_sequential_scans:
            return recommendations
        
        # For each table with a sequential scan
        for table_name in query_plan.table_scans:
            # Check if table info is available
            if table_name not in self.optimizer._table_info:
                continue
            
            # Extract columns referenced in query for this table
            key_columns = self._extract_filter_columns(table_name, query_plan.operations)
            if not key_columns:
                continue
            
            # Extract columns used in SELECT and other clauses
            include_columns = self._extract_output_columns(table_name, query_text)
            
            # Remove key columns from include columns to avoid duplication
            include_columns = [col for col in include_columns if col not in key_columns]
            
            # Only create covering index if we have both key and include columns
            if key_columns and include_columns:
                rec = PgIndexRecommendation(
                    table_name=table_name,
                    column_names=key_columns,
                    include_columns=include_columns,
                    index_type=IndexType.BTREE,
                    estimated_improvement=0.4,  # Moderate improvement estimation
                    query_pattern=f"SELECT with filter on {', '.join(key_columns)}"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def recommend_partial_index(
        self, query_plan: QueryPlan, query_text: str
    ) -> List[PgIndexRecommendation]:
        """
        Recommend partial indexes for a query.
        
        Args:
            query_plan: The query plan to analyze
            query_text: The original query text
            
        Returns:
            List of partial index recommendations
        """
        recommendations = []
        
        # Extract WHERE clauses from the query
        where_clauses = self._extract_where_clauses(query_text)
        if not where_clauses:
            return recommendations
        
        # For each table with a sequential scan
        for table_name in query_plan.table_scans:
            # Check if table info is available
            if table_name not in self.optimizer._table_info:
                continue
            
            # Extract columns used in WHERE clause for this table
            filter_columns = self._extract_filter_columns(table_name, query_plan.operations)
            if not filter_columns:
                continue
            
            # Extract suitable where clause for partial index
            table_where_clause = self._extract_partial_index_condition(table_name, where_clauses)
            if not table_where_clause:
                continue
            
            # Create partial index recommendation
            rec = PgIndexRecommendation(
                table_name=table_name,
                column_names=filter_columns,
                index_type=IndexType.BTREE,
                is_partial=True,
                where_clause=table_where_clause,
                estimated_improvement=0.5,  # Good improvement for targeted queries
                query_pattern=f"WHERE {table_where_clause}"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def recommend_expression_index(
        self, query_plan: QueryPlan, query_text: str
    ) -> List[PgIndexRecommendation]:
        """
        Recommend expression indexes for a query.
        
        Args:
            query_plan: The query plan to analyze
            query_text: The original query text
            
        Returns:
            List of expression index recommendations
        """
        recommendations = []
        
        # Extract expressions from the query
        expressions = self._extract_expressions(query_text)
        if not expressions:
            return recommendations
        
        # For each expression that might benefit from an index
        for expr_info in expressions:
            table_name = expr_info["table"]
            expression = expr_info["expression"]
            columns = expr_info["columns"]
            
            # Check if table info is available
            if table_name not in self.optimizer._table_info:
                continue
            
            # Only proceed if this table had a sequential scan
            if table_name not in query_plan.table_scans:
                continue
            
            # Create an expression index recommendation
            # Note: For expression indexes, we store the expression in column_names
            rec = PgIndexRecommendation(
                table_name=table_name,
                column_names=[expression],  # The expression itself
                index_type=IndexType.BTREE,
                estimated_improvement=0.4,
                query_pattern=f"WHERE {expression}"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _extract_output_columns(self, table_name: str, query_text: str) -> List[str]:
        """
        Extract columns used in SELECT clause for a specific table.
        
        Args:
            table_name: The name of the table
            query_text: The query text to analyze
            
        Returns:
            List of column names
        """
        # This is a simplified implementation that would need more robust parsing
        # in a production environment
        
        columns = []
        
        # Match SELECT clause
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", query_text, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return columns
        
        select_clause = select_match.group(1)
        
        # Extract table alias if any
        alias_match = re.search(
            r"FROM\s+%s\s+(?:AS\s+)?(\w+)" % table_name,
            query_text,
            re.IGNORECASE
        )
        table_alias = alias_match.group(1) if alias_match else table_name
        
        # Look for columns with table prefix
        prefix_pattern = r"(?:%s|%s)\.([\w_]+)" % (table_name, table_alias)
        prefixed_columns = re.findall(prefix_pattern, select_clause, re.IGNORECASE)
        columns.extend(prefixed_columns)
        
        # Also look for columns without prefix if no other tables are involved
        if len(re.findall(r"FROM\s+(\w+)", query_text, re.IGNORECASE)) == 1:
            # Simple columns (no table prefix)
            simple_columns = re.findall(r"(?:^|,)\s*([\w_]+)\s*(?:,|$)", select_clause)
            columns.extend(simple_columns)
        
        return columns
    
    def _extract_where_clauses(self, query_text: str) -> List[str]:
        """
        Extract WHERE clauses from a query.
        
        Args:
            query_text: The query text to analyze
            
        Returns:
            List of WHERE conditions
        """
        where_match = re.search(r"WHERE\s+(.*?)(?:ORDER BY|GROUP BY|LIMIT|$)", 
                               query_text, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return []
        
        where_clause = where_match.group(1).strip()
        
        # Split on AND to get individual conditions
        # Note: This is simplified and doesn't handle OR or parentheses properly
        conditions = [c.strip() for c in where_clause.split("AND")]
        
        return conditions
    
    def _extract_partial_index_condition(
        self, table_name: str, where_clauses: List[str]
    ) -> Optional[str]:
        """
        Extract a condition suitable for a partial index.
        
        Args:
            table_name: The name of the table
            where_clauses: List of WHERE conditions
            
        Returns:
            Condition suitable for partial index or None
        """
        # Look for suitable clauses (equality on low-cardinality columns)
        for clause in where_clauses:
            # Check if clause is for this table
            if table_name in clause or "." not in clause:
                # Look for equality conditions on status-like columns
                for status_keyword in ["status", "type", "state", "is_", "active", "enabled"]:
                    if status_keyword in clause.lower() and "=" in clause:
                        return clause
        
        return None
    
    def _extract_expressions(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Extract expressions from a query that might benefit from expression indexes.
        
        Args:
            query_text: The query text to analyze
            
        Returns:
            List of expression information (table, expression, columns)
        """
        expressions = []
        
        # Look for common patterns that benefit from expression indexes
        
        # LOWER() function
        lower_matches = re.finditer(
            r"LOWER\(\s*(\w+)\.(\w+)\s*\)\s*=\s*['\"]([^'\"]+)['\"]",
            query_text,
            re.IGNORECASE
        )
        for match in lower_matches:
            table = match.group(1)
            column = match.group(2)
            expressions.append({
                "table": table,
                "expression": f"LOWER({column})",
                "columns": [column],
                "type": "function"
            })
        
        # Date extraction
        date_matches = re.finditer(
            r"EXTRACT\(\s*(\w+)\s+FROM\s+(\w+)\.(\w+)\s*\)",
            query_text,
            re.IGNORECASE
        )
        for match in date_matches:
            date_part = match.group(1)
            table = match.group(2)
            column = match.group(3)
            expressions.append({
                "table": table,
                "expression": f"EXTRACT({date_part} FROM {column})",
                "columns": [column],
                "type": "date_extract"
            })
        
        # String concatenation
        concat_matches = re.finditer(
            r"(\w+)\.(\w+)\s*\|\|\s*(\w+)\.(\w+)",
            query_text
        )
        for match in concat_matches:
            table1 = match.group(1)
            column1 = match.group(2)
            table2 = match.group(3)
            column2 = match.group(4)
            
            # Only if concatenating columns from the same table
            if table1 == table2:
                expressions.append({
                    "table": table1,
                    "expression": f"{column1} || {column2}",
                    "columns": [column1, column2],
                    "type": "concatenation"
                })
        
        return expressions
    
    async def rewrite_for_pg_features(
        self, query: str
    ) -> OpResult[QueryRewrite]:
        """
        Rewrite a query to leverage PostgreSQL-specific features.
        
        Args:
            query: The query to rewrite
            
        Returns:
            Result with QueryRewrite on success, error message on failure
        """
        # CTE optimization rewrite
        cte_result = self._rewrite_cte(query)
        if cte_result.is_success:
            return cte_result
        
        # LATERAL JOIN optimization
        lateral_result = self._rewrite_to_lateral(query)
        if lateral_result.is_success:
            return lateral_result
        
        # JSON functions optimization
        json_result = self._rewrite_json_functions(query)
        if json_result.is_success:
            return json_result
        
        # DISTINCT ON optimization
        distinct_result = self._rewrite_to_distinct_on(query)
        if distinct_result.is_success:
            return distinct_result
        
        # No applicable rewrites
        return Failure("No PostgreSQL-specific rewrites applicable")
    
    def _rewrite_cte(self, query: str) -> OpResult[QueryRewrite]:
        """
        Rewrite subqueries to use Common Table Expressions (CTEs).
        
        Args:
            query: The query to rewrite
            
        Returns:
            Result with QueryRewrite on success, error message on failure
        """
        # Look for subqueries
        subquery_pattern = r"\(\s*(SELECT\s+.*?)\s*\)\s+AS\s+(\w+)"
        matches = list(re.finditer(subquery_pattern, query, re.IGNORECASE | re.DOTALL))
        
        if not matches:
            return Failure("No subqueries found to convert to CTEs")
        
        # Construct the CTE query
        cte_parts = []
        main_query = query
        
        for i, match in enumerate(matches):
            subquery = match.group(1)
            alias = match.group(2)
            
            # Add the CTE
            cte_parts.append(f"{alias} AS (\n{subquery}\n)")
            
            # Replace the subquery in the main query
            main_query = main_query.replace(match.group(0), alias)
        
        # Construct the final CTE query
        cte_query = f"WITH {', '.join(cte_parts)}\n{main_query}"
        
        return Success(QueryRewrite(
            original_query=query,
            rewritten_query=cte_query,
            rewrite_type="cte_optimization",
            estimated_improvement=0.2,
            reason="Converted subqueries to Common Table Expressions (CTEs) for better readability and potential performance improvement"
        ))
    
    def _rewrite_to_lateral(self, query: str) -> OpResult[QueryRewrite]:
        """
        Rewrite certain JOIN patterns to use LATERAL JOIN.
        
        Args:
            query: The query to rewrite
            
        Returns:
            Result with QueryRewrite on success, error message on failure
        """
        # Look for joins where the right side depends on the left side
        # This is a simplified pattern and would need more robust parsing in production
        pattern = r"FROM\s+(\w+)\s+.*?JOIN\s+\(\s*SELECT\s+.*?WHERE\s+.*?(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)"
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return Failure("No suitable joins found for LATERAL optimization")
        
        # Analyze the match
        main_table = match.group(1)
        filter_table = match.group(2)
        filter_column = match.group(3)
        join_table = match.group(4)
        join_column = match.group(5)
        
        # Only proceed if the filter table is the same as the main table
        if filter_table != main_table:
            return Failure("Join filter doesn't reference the main table")
        
        # Extract the subquery
        subquery_pattern = r"JOIN\s+(\(\s*SELECT\s+.*?\))\s+AS\s+(\w+)"
        subquery_match = re.search(subquery_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not subquery_match:
            return Failure("Could not extract subquery for LATERAL join")
        
        subquery = subquery_match.group(1)
        subquery_alias = subquery_match.group(2)
        
        # Rewrite with LATERAL
        lateral_subquery = subquery.replace(
            f"{filter_table}.{filter_column} = {join_table}.{join_column}",
            f"{main_table}.{filter_column} = {join_table}.{join_column}"
        )
        
        rewritten = query.replace(
            f"JOIN {subquery} AS {subquery_alias}",
            f"CROSS JOIN LATERAL {lateral_subquery} AS {subquery_alias}"
        )
        
        return Success(QueryRewrite(
            original_query=query,
            rewritten_query=rewritten,
            rewrite_type="lateral_join_optimization",
            estimated_improvement=0.3,
            reason="Converted to LATERAL JOIN for better performance with correlated subqueries"
        ))
    
    def _rewrite_json_functions(self, query: str) -> OpResult[QueryRewrite]:
        """
        Optimize JSON operations using PostgreSQL-specific functions.
        
        Args:
            query: The query to rewrite
            
        Returns:
            Result with QueryRewrite on success, error message on failure
        """
        # Replace JSON_EXTRACT with PostgreSQL's -> operator
        json_extract_pattern = r"JSON_EXTRACT\(\s*(\w+)\.(\w+)\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
        
        if not re.search(json_extract_pattern, query, re.IGNORECASE):
            return Failure("No JSON_EXTRACT functions found to optimize")
        
        rewritten = re.sub(
            json_extract_pattern,
            lambda m: f"{m.group(1)}.{m.group(2)} -> '{m.group(3)}'",
            query,
            flags=re.IGNORECASE
        )
        
        # Replace JSON_EXTRACT_SCALAR with ->> operator for text output
        json_scalar_pattern = r"JSON_EXTRACT_SCALAR\(\s*(\w+)\.(\w+)\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
        
        if re.search(json_scalar_pattern, query, re.IGNORECASE):
            rewritten = re.sub(
                json_scalar_pattern,
                lambda m: f"{m.group(1)}.{m.group(2)} ->> '{m.group(3)}'",
                rewritten,
                flags=re.IGNORECASE
            )
        
        return Success(QueryRewrite(
            original_query=query,
            rewritten_query=rewritten,
            rewrite_type="json_function_optimization",
            estimated_improvement=0.25,
            reason="Replaced generic JSON functions with PostgreSQL-specific operators for better performance"
        ))
    
    def _rewrite_to_distinct_on(self, query: str) -> OpResult[QueryRewrite]:
        """
        Rewrite GROUP BY queries with first-value logic to use DISTINCT ON.
        
        Args:
            query: The query to rewrite
            
        Returns:
            Result with QueryRewrite on success, error message on failure
        """
        # Look for GROUP BY with aggregate functions getting the "first" value
        pattern = r"SELECT\s+(.*?)(?:,\s*)?(\w+\.\w+|\w+)\s+FROM\s+(.*?)\s+GROUP\s+BY\s+(.*?)\s+ORDER\s+BY\s+(.*?)(?:LIMIT|$)"
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return Failure("No suitable GROUP BY pattern found for DISTINCT ON optimization")
        
        select_clause = match.group(1)
        group_cols = match.group(4).split(",")
        order_cols = match.group(5).strip()
        
        # Only proceed if we're essentially taking the first row per group
        # This is a simplified check; a real implementation would be more robust
        if "MIN(" not in select_clause and "MAX(" not in select_clause:
            return Failure("No first-value aggregates found")
        
        # Rewrite to use DISTINCT ON
        distinct_cols = ", ".join(col.strip() for col in group_cols)
        
        # Replace aggregate functions with direct column references
        new_select = re.sub(
            r"(MIN|MAX)\(\s*(\w+\.\w+|\w+)\s*\)",
            r"\2",
            select_clause
        )
        
        rewritten = f"SELECT DISTINCT ON ({distinct_cols}) {new_select} FROM {match.group(3)} ORDER BY {distinct_cols}, {order_cols}"
        
        return Success(QueryRewrite(
            original_query=query,
            rewritten_query=rewritten,
            rewrite_type="distinct_on_optimization",
            estimated_improvement=0.3,
            reason="Replaced GROUP BY with first-value aggregates using DISTINCT ON for more efficient execution"
        ))


# Helper function to extend an optimizer with PostgreSQL strategies
def add_pg_strategies(optimizer: QueryOptimizer) -> PgOptimizationStrategies:
    """
    Add PostgreSQL-specific optimization strategies to a query optimizer.
    
    Args:
        optimizer: The query optimizer to extend
        
    Returns:
        The PostgreSQL optimization strategies object
    """
    return PgOptimizationStrategies(optimizer)


# Specialized version of the optimizer with PostgreSQL-specific strategies
class PgQueryOptimizer(QueryOptimizer):
    """
    PostgreSQL-specific query optimizer.
    
    Extends the base QueryOptimizer with PostgreSQL-specific optimizations.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the PostgreSQL query optimizer.
        
        Args:
            Same as QueryOptimizer
        """
        super().__init__(*args, **kwargs)
        self.pg_strategies = PgOptimizationStrategies(self)
    
    async def analyze_query(self, query, params=None):
        """
        Analyze a query, with PostgreSQL-specific details.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            
        Returns:
            Parsed query plan
        """
        # Get basic query plan from parent method
        plan = await super().analyze_query(query, params)
        
        # Add any PostgreSQL-specific analysis here
        
        return plan
    
    async def recommend_indexes(self, query_plan, query_text=None):
        """
        Recommend indexes for a query, including PostgreSQL-specific indexes.
        
        Args:
            query_plan: Query plan to analyze
            query_text: Original query text (optional)
            
        Returns:
            List of index recommendations
        """
        # Get basic recommendations from parent method
        recommendations = await super().recommend_indexes(query_plan)
        
        # Add PostgreSQL-specific recommendations if query_text was provided
        if query_text and self.config.recommend_indexes:
            # Add covering indexes
            covering_indexes = self.pg_strategies.recommend_covering_index(query_plan, query_text)
            recommendations.extend(covering_indexes)
            
            # Add partial indexes
            partial_indexes = self.pg_strategies.recommend_partial_index(query_plan, query_text)
            recommendations.extend(partial_indexes)
            
            # Add expression indexes
            expression_indexes = self.pg_strategies.recommend_expression_index(query_plan, query_text)
            recommendations.extend(expression_indexes)
        
        return recommendations
    
    async def rewrite_query(self, query, params=None):
        """
        Rewrite a query, including PostgreSQL-specific optimizations.
        
        Args:
            query: SQL query string or SQLAlchemy executable
            params: Optional query parameters
            
        Returns:
            Result containing QueryRewrite on success, error message on failure
        """
        # Try standard rewrites first
        result = await super().rewrite_query(query, params)
        if result.is_success:
            return result
        
        # If no standard rewrites applied, try PostgreSQL-specific rewrites
        if self.config.rewrite_queries:
            # Convert query to string if it's a SQLAlchemy executable
            query_str = query
            if not isinstance(query, str):
                if hasattr(query, "compile"):
                    compiled = query.compile(compile_kwargs={"literal_binds": True})
                    query_str = str(compiled)
                else:
                    query_str = str(query)
            
            return await self.pg_strategies.rewrite_for_pg_features(query_str)
        
        return result
    
    async def analyze_tables(self, table_names):
        """
        Run ANALYZE on specified tables to update statistics.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            Dictionary of table names to results
        """
        results = {}
        for table_name in table_names:
            result = await self.pg_strategies.analyze_table(table_name)
            results[table_name] = result
        
        return results
    
    async def get_maintenance_recommendations(self, table_names):
        """
        Get maintenance recommendations for specified tables.
        
        Args:
            table_names: List of table names to analyze
            
        Returns:
            Dictionary of table names to maintenance recommendations
        """
        recommendations = {}
        for table_name in table_names:
            result = await self.pg_strategies.recommend_table_maintenance(table_name)
            if result.is_success:
                recommendations[table_name] = result.value
            else:
                recommendations[table_name] = {"error": result.error}
        
        return recommendations


# Helper function to create a PostgreSQL-specific optimizer
def create_pg_optimizer(
    session=None,
    engine=None,
    config=None,
    logger=None,
):
    """
    Create a PostgreSQL-specific query optimizer.
    
    Args:
        session: Optional AsyncSession to use
        engine: Optional AsyncEngine to use
        config: Optional configuration
        logger: Optional logger instance
        
    Returns:
        PostgreSQL-specific query optimizer
    """
    return PgQueryOptimizer(
        session=session,
        engine=engine,
        config=config,
        logger=logger,
    )