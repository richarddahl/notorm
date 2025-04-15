# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for complex SQL generation scenarios.

This module contains tests for more complex SQL generation scenarios, including:
- Complex conditional SQL generation
- Dynamic SQL statement construction
- Composition of multiple SQL statements with dependencies
- Advanced SQL syntax handling (CTEs, window functions, etc.)
- Performance-optimized SQL generation
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy import (
    Table, Column, String, Integer, Boolean, ForeignKey, MetaData, DateTime,
    func, select, and_, or_, not_, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.database.config import ConnectionConfig
from uno.sql.builders.function import SQLFunctionBuilder
from uno.sql.builders.trigger import SQLTriggerBuilder
from uno.core.errors import UnoError


# Mock settings for testing
class MockSettings:
    """Mock settings for testing."""
    
    DB_NAME = "test_db"
    DB_SCHEMA = "test_schema"
    DB_USER_PW = "test_password"
    UNO_ROOT = "/test/path"
    DB_SYNC_DRIVER = "psycopg2"
    DB_ASYNC_DRIVER = "asyncpg"
    DB_HOST = "localhost"
    DB_PORT = 5432


# Test fixtures
@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return MockSettings()


@pytest.fixture
def mock_tables():
    """Create a set of mock SQLAlchemy tables with relationships for testing."""
    metadata = MetaData()
    
    # Create user table
    users = Table(
        "users",
        metadata,
        Column("id", UUID, primary_key=True),
        Column("username", String(50), nullable=False, unique=True),
        Column("email", String(100), nullable=False, unique=True),
        Column("password_hash", String(255), nullable=False),
        Column("is_active", Boolean, nullable=False, default=True),
        Column("created_at", DateTime, nullable=False, default=func.now()),
        Column("updated_at", DateTime, nullable=False, default=func.now(), onupdate=func.now()),
        Column("last_login", DateTime),
        Column("profile", JSONB)
    )
    
    # Create posts table
    posts = Table(
        "posts",
        metadata,
        Column("id", UUID, primary_key=True),
        Column("user_id", UUID, ForeignKey("users.id"), nullable=False),
        Column("title", String(200), nullable=False),
        Column("content", String, nullable=False),
        Column("published", Boolean, nullable=False, default=False),
        Column("view_count", Integer, nullable=False, default=0),
        Column("created_at", DateTime, nullable=False, default=func.now()),
        Column("updated_at", DateTime, nullable=False, default=func.now(), onupdate=func.now()),
        Column("metadata", JSONB)
    )
    
    # Create comments table
    comments = Table(
        "comments",
        metadata,
        Column("id", UUID, primary_key=True),
        Column("post_id", UUID, ForeignKey("posts.id"), nullable=False),
        Column("user_id", UUID, ForeignKey("users.id"), nullable=False),
        Column("content", String, nullable=False),
        Column("created_at", DateTime, nullable=False, default=func.now()),
        Column("updated_at", DateTime, nullable=False, default=func.now(), onupdate=func.now()),
        Column("parent_id", UUID, ForeignKey("comments.id")),
        Column("metadata", JSONB)
    )
    
    # Create tags table
    tags = Table(
        "tags",
        metadata,
        Column("id", UUID, primary_key=True),
        Column("name", String(50), nullable=False, unique=True),
        Column("description", String(255)),
        Column("created_at", DateTime, nullable=False, default=func.now())
    )
    
    # Create post_tags table for many-to-many relationship
    post_tags = Table(
        "post_tags",
        metadata,
        Column("post_id", UUID, ForeignKey("posts.id"), primary_key=True),
        Column("tag_id", UUID, ForeignKey("tags.id"), primary_key=True),
        Column("created_at", DateTime, nullable=False, default=func.now())
    )
    
    return {
        "users": users,
        "posts": posts,
        "comments": comments,
        "tags": tags,
        "post_tags": post_tags
    }


# Custom emitters for testing complex SQL scenarios
class AdvancedAnalyticsFunction(SQLEmitter):
    """Emitter for advanced analytics function with window functions and CTEs."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate a complex SQL function for user and post analytics."""
        # Format the schema name
        schema_name = self.connection_config.db_schema if self.connection_config else "public"
        db_name = self.connection_config.db_name if self.connection_config else "test_db"
        
        # CTE-based analytics function with window functions for post engagement metrics
        function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.user_post_analytics(
            p_user_id UUID,
            p_start_date TIMESTAMP,
            p_end_date TIMESTAMP
        ) RETURNS TABLE(
            user_id UUID,
            username TEXT,
            total_posts INTEGER,
            total_views INTEGER,
            total_comments INTEGER,
            avg_comments_per_post NUMERIC,
            engagement_score NUMERIC,
            most_popular_post_id UUID,
            most_popular_post_title TEXT,
            most_commented_post_id UUID,
            most_commented_post_title TEXT,
            most_used_tags TEXT[]
        ) AS $$
        BEGIN
            SET ROLE {db_name}_reader;
            
            RETURN QUERY
            WITH post_stats AS (
                SELECT 
                    p.id AS post_id,
                    p.user_id,
                    p.title,
                    p.view_count,
                    COUNT(c.id) AS comment_count
                FROM 
                    {schema_name}.posts p
                LEFT JOIN 
                    {schema_name}.comments c ON p.id = c.post_id
                WHERE 
                    (p.user_id = p_user_id OR p_user_id IS NULL)
                    AND p.created_at BETWEEN p_start_date AND p_end_date
                GROUP BY 
                    p.id, p.user_id, p.title, p.view_count
            ),
            user_stats AS (
                SELECT 
                    u.id AS user_id,
                    u.username,
                    COUNT(DISTINCT ps.post_id) AS total_posts,
                    SUM(ps.view_count) AS total_views,
                    SUM(ps.comment_count) AS total_comments,
                    CASE WHEN COUNT(DISTINCT ps.post_id) > 0 
                        THEN SUM(ps.comment_count)::NUMERIC / COUNT(DISTINCT ps.post_id) 
                        ELSE 0 
                    END AS avg_comments_per_post,
                    CASE WHEN COUNT(DISTINCT ps.post_id) > 0 
                        THEN (SUM(ps.view_count) + SUM(ps.comment_count) * 5)::NUMERIC / COUNT(DISTINCT ps.post_id) 
                        ELSE 0 
                    END AS engagement_score
                FROM 
                    {schema_name}.users u
                LEFT JOIN 
                    post_stats ps ON u.id = ps.user_id
                WHERE 
                    (u.id = p_user_id OR p_user_id IS NULL)
                GROUP BY 
                    u.id, u.username
            ),
            popular_posts AS (
                SELECT 
                    ps.user_id,
                    FIRST_VALUE(ps.post_id) OVER (PARTITION BY ps.user_id ORDER BY ps.view_count DESC) AS most_viewed_post_id,
                    FIRST_VALUE(ps.title) OVER (PARTITION BY ps.user_id ORDER BY ps.view_count DESC) AS most_viewed_post_title,
                    FIRST_VALUE(ps.post_id) OVER (PARTITION BY ps.user_id ORDER BY ps.comment_count DESC) AS most_commented_post_id,
                    FIRST_VALUE(ps.title) OVER (PARTITION BY ps.user_id ORDER BY ps.comment_count DESC) AS most_commented_post_title
                FROM 
                    post_stats ps
            ),
            user_tags AS (
                SELECT 
                    p.user_id,
                    ARRAY_AGG(DISTINCT t.name ORDER BY COUNT(*) DESC) FILTER (WHERE t.name IS NOT NULL) AS tags
                FROM 
                    {schema_name}.posts p
                JOIN 
                    {schema_name}.post_tags pt ON p.id = pt.post_id
                JOIN 
                    {schema_name}.tags t ON pt.tag_id = t.id
                WHERE 
                    (p.user_id = p_user_id OR p_user_id IS NULL)
                    AND p.created_at BETWEEN p_start_date AND p_end_date
                GROUP BY 
                    p.user_id
            )
            SELECT 
                us.user_id,
                us.username,
                us.total_posts,
                us.total_views,
                us.total_comments,
                us.avg_comments_per_post,
                us.engagement_score,
                pp.most_viewed_post_id,
                pp.most_viewed_post_title,
                pp.most_commented_post_id,
                pp.most_commented_post_title,
                ut.tags
            FROM 
                user_stats us
            LEFT JOIN 
                (SELECT DISTINCT ON (user_id) * FROM popular_posts) pp ON us.user_id = pp.user_id
            LEFT JOIN
                user_tags ut ON us.user_id = ut.user_id
            ORDER BY 
                us.engagement_score DESC;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create the SQL statement
        return [
            SQLStatement(
                name="user_post_analytics_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql
            )
        ]


class RecursiveCommentTreeFunction(SQLEmitter):
    """Emitter for recursive comment tree function using PostgreSQL recursive CTEs."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate a complex SQL function for retrieving comment trees recursively."""
        # Format the schema name
        schema_name = self.connection_config.db_schema if self.connection_config else "public"
        db_name = self.connection_config.db_name if self.connection_config else "test_db"
        
        # Recursive CTE function for building comment trees
        function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.get_comment_tree(
            p_post_id UUID,
            p_max_depth INTEGER DEFAULT 10
        ) RETURNS TABLE(
            id UUID,
            post_id UUID,
            user_id UUID,
            username TEXT,
            content TEXT,
            created_at TIMESTAMP,
            parent_id UUID,
            depth INTEGER,
            path UUID[],
            reply_count INTEGER
        ) AS $$
        BEGIN
            SET ROLE {db_name}_reader;
            
            RETURN QUERY
            WITH RECURSIVE comment_tree AS (
                -- Base case: Top-level comments
                SELECT 
                    c.id,
                    c.post_id,
                    c.user_id,
                    u.username,
                    c.content,
                    c.created_at,
                    c.parent_id,
                    1 AS depth,
                    ARRAY[c.id] AS path,
                    (SELECT COUNT(*) FROM {schema_name}.comments WHERE parent_id = c.id) AS reply_count
                FROM 
                    {schema_name}.comments c
                JOIN 
                    {schema_name}.users u ON c.user_id = u.id
                WHERE 
                    c.post_id = p_post_id 
                    AND c.parent_id IS NULL
                
                UNION ALL
                
                -- Recursive case: Child comments up to max depth
                SELECT 
                    c.id,
                    c.post_id,
                    c.user_id,
                    u.username,
                    c.content,
                    c.created_at,
                    c.parent_id,
                    ct.depth + 1,
                    ct.path || c.id,
                    (SELECT COUNT(*) FROM {schema_name}.comments WHERE parent_id = c.id) AS reply_count
                FROM 
                    {schema_name}.comments c
                JOIN 
                    {schema_name}.users u ON c.user_id = u.id
                JOIN 
                    comment_tree ct ON c.parent_id = ct.id
                WHERE 
                    ct.depth < p_max_depth
            )
            SELECT * FROM comment_tree
            ORDER BY path;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create the SQL statement
        return [
            SQLStatement(
                name="comment_tree_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql
            )
        ]


class FullTextSearchFunction(SQLEmitter):
    """Emitter for full-text search function across posts and comments."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate a complex SQL function for full-text search."""
        # Format the schema name
        schema_name = self.connection_config.db_schema if self.connection_config else "public"
        db_name = self.connection_config.db_name if self.connection_config else "test_db"
        
        # Create function with tsvector indexing and ranking
        function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.search_content(
            p_query TEXT,
            p_limit INTEGER DEFAULT 20,
            p_offset INTEGER DEFAULT 0
        ) RETURNS TABLE(
            id UUID,
            content_type TEXT,
            title TEXT,
            content TEXT,
            username TEXT,
            created_at TIMESTAMP,
            parent_id UUID,
            rank FLOAT,
            highlight TEXT
        ) AS $$
        DECLARE
            query_tokens TEXT;
            ts_query TSQUERY;
        BEGIN
            -- Set role to reader
            SET ROLE {db_name}_reader;
            
            -- Create tokens for highlighting
            query_tokens := string_agg(lexeme, ' | ') FROM unnest(regexp_split_to_array(p_query, '\\s+')) lexeme;
            ts_query := to_tsquery('english', query_tokens);
            
            RETURN QUERY
            -- Search in posts
            SELECT 
                p.id::UUID,
                'post'::TEXT AS content_type,
                p.title,
                p.content,
                u.username,
                p.created_at,
                NULL::UUID AS parent_id,
                ts_rank_cd(
                    setweight(to_tsvector('english', COALESCE(p.title, '')), 'A') || 
                    setweight(to_tsvector('english', COALESCE(p.content, '')), 'B'),
                    ts_query
                ) AS rank,
                ts_headline('english', p.content, ts_query, 'StartSel=<em>, StopSel=</em>, MaxWords=35, MinWords=15') AS highlight
            FROM 
                {schema_name}.posts p
            JOIN 
                {schema_name}.users u ON p.user_id = u.id
            WHERE 
                p.published = TRUE
                AND (
                    to_tsvector('english', COALESCE(p.title, '')) @@ ts_query
                    OR to_tsvector('english', COALESCE(p.content, '')) @@ ts_query
                )
                
            UNION ALL
            
            -- Search in comments
            SELECT 
                c.id::UUID,
                'comment'::TEXT AS content_type,
                '' AS title,
                c.content,
                u.username,
                c.created_at,
                c.post_id AS parent_id,
                ts_rank_cd(
                    to_tsvector('english', COALESCE(c.content, '')),
                    ts_query
                ) AS rank,
                ts_headline('english', c.content, ts_query, 'StartSel=<em>, StopSel=</em>, MaxWords=35, MinWords=15') AS highlight
            FROM 
                {schema_name}.comments c
            JOIN 
                {schema_name}.users u ON c.user_id = u.id
            JOIN 
                {schema_name}.posts p ON c.post_id = p.id
            WHERE 
                p.published = TRUE
                AND to_tsvector('english', COALESCE(c.content, '')) @@ ts_query
                
            ORDER BY 
                rank DESC
            LIMIT p_limit
            OFFSET p_offset;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create the SQL statement
        return [
            SQLStatement(
                name="full_text_search_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql
            )
        ]


class AuditTrailTriggerSetup(SQLEmitter):
    """Emitter for complete audit trail system with function, trigger, and table."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for a complete audit trail system."""
        # Format the schema name
        schema_name = self.connection_config.db_schema if self.connection_config else "public"
        db_name = self.connection_config.db_name if self.connection_config else "test_db"
        
        # Create audit table
        create_audit_table = f"""
        SET ROLE {db_name}_admin;
        
        CREATE TABLE IF NOT EXISTS {schema_name}.audit_trail (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            table_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            user_id UUID,
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            old_data JSONB,
            new_data JSONB,
            query TEXT,
            ip_address INET,
            session_id TEXT,
            application_name TEXT
        );
        
        -- Add comments for documentation
        COMMENT ON TABLE {schema_name}.audit_trail IS 'Stores audit records for all tracked tables';
        COMMENT ON COLUMN {schema_name}.audit_trail.id IS 'Unique identifier for the audit record';
        COMMENT ON COLUMN {schema_name}.audit_trail.table_name IS 'Name of the audited table';
        COMMENT ON COLUMN {schema_name}.audit_trail.operation IS 'Operation type (INSERT, UPDATE, DELETE)';
        COMMENT ON COLUMN {schema_name}.audit_trail.user_id IS 'User who performed the operation';
        COMMENT ON COLUMN {schema_name}.audit_trail.timestamp IS 'When the operation occurred';
        COMMENT ON COLUMN {schema_name}.audit_trail.old_data IS 'Previous state of the record (for UPDATE, DELETE)';
        COMMENT ON COLUMN {schema_name}.audit_trail.new_data IS 'New state of the record (for INSERT, UPDATE)';
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_audit_trail_table_name ON {schema_name}.audit_trail(table_name);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_user_id ON {schema_name}.audit_trail(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON {schema_name}.audit_trail(timestamp);
        
        -- Create GIN indexes for JSONB fields
        CREATE INDEX IF NOT EXISTS idx_audit_trail_old_data ON {schema_name}.audit_trail USING GIN (old_data);
        CREATE INDEX IF NOT EXISTS idx_audit_trail_new_data ON {schema_name}.audit_trail USING GIN (new_data);
        
        -- Set permissions
        GRANT SELECT ON {schema_name}.audit_trail TO {db_name}_reader;
        GRANT INSERT ON {schema_name}.audit_trail TO {db_name}_writer;
        """
        
        # Create audit function
        create_audit_function = f"""
        SET ROLE {db_name}_admin;
        
        CREATE OR REPLACE FUNCTION {schema_name}.audit_trail_trigger()
        RETURNS TRIGGER AS $$
        DECLARE
            current_user_id UUID;
            client_ip INET;
            app_name TEXT;
            session_id TEXT;
            excluded_cols TEXT[] := ARRAY['created_at', 'updated_at'];
            should_record BOOLEAN := TRUE;
            record_old_data JSONB;
            record_new_data JSONB;
        BEGIN
            -- Try to get current user ID from session variables
            BEGIN
                current_user_id := NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID;
            EXCEPTION WHEN OTHERS THEN
                current_user_id := NULL;
            END;
            
            -- Try to get client IP from session variables
            BEGIN
                client_ip := NULLIF(current_setting('app.client_ip', TRUE), '')::INET;
            EXCEPTION WHEN OTHERS THEN
                client_ip := NULL;
            END;
            
            -- Try to get application name from session variables
            BEGIN
                app_name := NULLIF(current_setting('app.application_name', TRUE), '');
            EXCEPTION WHEN OTHERS THEN
                app_name := current_setting('application_name');
            END;
            
            -- Try to get session ID from session variables
            BEGIN
                session_id := NULLIF(current_setting('app.session_id', TRUE), '');
            EXCEPTION WHEN OTHERS THEN
                session_id := NULL;
            END;
            
            -- For DELETE operations, store the old record, for others use converted JSON from record
            IF (TG_OP = 'DELETE') THEN
                record_old_data := row_to_json(OLD)::JSONB;
                record_new_data := NULL;
            ELSIF (TG_OP = 'UPDATE') THEN
                record_old_data := row_to_json(OLD)::JSONB;
                record_new_data := row_to_json(NEW)::JSONB;
                
                -- Check if any meaningful columns changed (excluding excluded_cols)
                should_record := FALSE;
                FOR i IN SELECT * FROM jsonb_object_keys(record_old_data) LOOP
                    IF NOT (i = ANY(excluded_cols)) AND record_old_data->i IS DISTINCT FROM record_new_data->i THEN
                        should_record := TRUE;
                        EXIT;
                    END IF;
                END LOOP;
            ELSE -- INSERT
                record_old_data := NULL;
                record_new_data := row_to_json(NEW)::JSONB;
            END IF;
            
            -- Insert audit record if meaningful changes were made
            IF should_record THEN
                SET ROLE {db_name}_writer;
                
                INSERT INTO {schema_name}.audit_trail (
                    table_name,
                    operation,
                    user_id,
                    timestamp,
                    old_data,
                    new_data,
                    query,
                    ip_address,
                    session_id,
                    application_name
                ) VALUES (
                    TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
                    TG_OP,
                    current_user_id,
                    NOW(),
                    record_old_data,
                    record_new_data,
                    current_query(),
                    client_ip,
                    session_id,
                    app_name
                );
                
                SET ROLE {db_name}_admin;
            END IF;
            
            RETURN NULL; -- result is ignored since this is an AFTER trigger
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Add comment for documentation
        COMMENT ON FUNCTION {schema_name}.audit_trail_trigger() IS 'Function for tracking changes to audited tables';
        
        -- Set permissions
        REVOKE ALL ON FUNCTION {schema_name}.audit_trail_trigger() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION {schema_name}.audit_trail_trigger() TO {db_name}_writer;
        """
        
        # Create helper function for adding audit triggers
        create_helper_function = f"""
        SET ROLE {db_name}_admin;
        
        CREATE OR REPLACE FUNCTION {schema_name}.add_audit_trigger(p_table_name TEXT)
        RETURNS VOID AS $$
        DECLARE
            trigger_name TEXT;
            schema_name TEXT;
            table_only TEXT;
        BEGIN
            -- Extract schema and table name
            IF p_table_name LIKE '%.%' THEN
                schema_name := split_part(p_table_name, '.', 1);
                table_only := split_part(p_table_name, '.', 2);
            ELSE
                schema_name := '{schema_name}';
                table_only := p_table_name;
            END IF;
            
            -- Generate trigger name
            trigger_name := table_only || '_audit_trigger';
            
            -- Create the trigger
            EXECUTE format('
                DROP TRIGGER IF EXISTS %I ON %I.%I;
                CREATE TRIGGER %I
                AFTER INSERT OR UPDATE OR DELETE ON %I.%I
                FOR EACH ROW EXECUTE FUNCTION {schema_name}.audit_trail_trigger();
            ', trigger_name, schema_name, table_only, trigger_name, schema_name, table_only);
            
            -- Log the trigger creation
            RAISE NOTICE 'Audit trigger added to %.%', schema_name, table_only;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Add comment for documentation
        COMMENT ON FUNCTION {schema_name}.add_audit_trigger(TEXT) IS 'Helper function for adding audit triggers to tables';
        
        -- Set permissions
        REVOKE ALL ON FUNCTION {schema_name}.add_audit_trigger(TEXT) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION {schema_name}.add_audit_trigger(TEXT) TO {db_name}_admin;
        """
        
        # Create statements
        return [
            SQLStatement(
                name="create_audit_table",
                type=SQLStatementType.TABLE,
                sql=create_audit_table
            ),
            SQLStatement(
                name="create_audit_function",
                type=SQLStatementType.FUNCTION,
                sql=create_audit_function,
                depends_on=["create_audit_table"]
            ),
            SQLStatement(
                name="create_audit_helper",
                type=SQLStatementType.FUNCTION,
                sql=create_helper_function,
                depends_on=["create_audit_function"]
            )
        ]


class DynamicQueryBuilder(SQLEmitter):
    """Emitter that builds SQL queries dynamically based on configuration."""
    
    # Filter configuration for dynamic SQL generation
    filter_config: Dict[str, Any] = {
        "condition": "AND",
        "filters": [
            {"field": "users.is_active", "operator": "=", "value": True},
            {
                "condition": "OR",
                "filters": [
                    {"field": "posts.published", "operator": "=", "value": True},
                    {"field": "posts.user_id", "operator": "=", "value": "{user_id}"}
                ]
            },
            {
                "condition": "AND",
                "filters": [
                    {"field": "posts.created_at", "operator": ">=", "value": "{start_date}"},
                    {"field": "posts.created_at", "operator": "<=", "value": "{end_date}"}
                ]
            }
        ]
    }
    
    # Sorting configuration
    sort_config: List[Dict[str, str]] = [
        {"field": "posts.created_at", "direction": "DESC"},
        {"field": "posts.view_count", "direction": "DESC"}
    ]
    
    # Fields to select
    select_fields: List[str] = [
        "posts.id", "posts.title", "posts.content", "posts.created_at", 
        "users.id AS user_id", "users.username",
        "COUNT(comments.id) AS comment_count"
    ]
    
    # Join tables
    joins: List[Dict[str, str]] = [
        {"type": "JOIN", "table": "users", "on": "posts.user_id = users.id"},
        {"type": "LEFT JOIN", "table": "comments", "on": "posts.id = comments.post_id"}
    ]
    
    def _build_where_clause(self, filters: Dict[str, Any], params: Dict[str, Any] = None) -> str:
        """Recursively build a WHERE clause from filter config."""
        if params is None:
            params = {}
        
        # Handle leaf node (actual filter)
        if "field" in filters:
            field = filters["field"]
            operator = filters["operator"]
            value = filters["value"]
            
            # Handle parameterized values
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                param_name = value[1:-1]
                if param_name in params:
                    if isinstance(params[param_name], str):
                        value = f"'{params[param_name]}'"
                    else:
                        value = str(params[param_name])
                else:
                    value = "NULL"
            elif isinstance(value, str):
                value = f"'{value}'"
            elif value is None:
                value = "NULL"
                if operator == "=":
                    operator = "IS"
                elif operator == "!=":
                    operator = "IS NOT"
            else:
                value = str(value)
            
            return f"{field} {operator} {value}"
        
        # Handle condition node (AND/OR group)
        if "condition" in filters and "filters" in filters:
            condition = filters["condition"]
            sub_filters = filters["filters"]
            
            # Build each sub-filter
            sub_clauses = []
            for sub_filter in sub_filters:
                sub_clause = self._build_where_clause(sub_filter, params)
                if sub_clause:
                    sub_clauses.append(sub_clause)
            
            # Join with the condition
            if sub_clauses:
                joined = f" {condition} ".join(sub_clauses)
                return f"({joined})"
        
        return ""
    
    def _build_sort_clause(self, sort_config: List[Dict[str, str]]) -> str:
        """Build an ORDER BY clause from sort config."""
        if not sort_config:
            return ""
        
        sort_terms = []
        for sort_item in sort_config:
            field = sort_item["field"]
            direction = sort_item["direction"]
            sort_terms.append(f"{field} {direction}")
        
        return "ORDER BY " + ", ".join(sort_terms)
    
    def _build_join_clause(self, joins: List[Dict[str, str]], schema_name: str) -> str:
        """Build JOIN clauses from join config."""
        if not joins:
            return ""
        
        join_clauses = []
        for join in joins:
            join_type = join["type"]
            table = join["table"]
            on = join["on"]
            join_clauses.append(f"{join_type} {schema_name}.{table} ON {on}")
        
        return " ".join(join_clauses)
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate dynamic SQL function for post search."""
        # Get schema name
        schema_name = self.connection_config.db_schema if self.connection_config else "public"
        db_name = self.connection_config.db_name if self.connection_config else "test_db"
        
        # Example parameter values for demonstration
        params = {
            "user_id": "current_user()",
            "start_date": "NOW() - INTERVAL '30 days'",
            "end_date": "NOW()"
        }
        
        # Build the dynamic query parts
        where_clause = self._build_where_clause(self.filter_config, params)
        sort_clause = self._build_sort_clause(self.sort_config)
        select_clause = ", ".join(self.select_fields)
        join_clause = self._build_join_clause(self.joins, schema_name)
        
        # Create the dynamic search function
        function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.search_posts(
            p_user_id UUID,
            p_start_date TIMESTAMP,
            p_end_date TIMESTAMP,
            p_limit INTEGER DEFAULT 20,
            p_offset INTEGER DEFAULT 0
        ) RETURNS TABLE(
            post_id UUID,
            title TEXT,
            content TEXT,
            created_at TIMESTAMP,
            user_id UUID,
            username TEXT,
            comment_count BIGINT
        ) AS $$
        BEGIN
            SET ROLE {db_name}_reader;
            
            RETURN QUERY EXECUTE '
                SELECT 
                    posts.id AS post_id,
                    posts.title,
                    posts.content,
                    posts.created_at,
                    users.id AS user_id,
                    users.username,
                    COUNT(comments.id) AS comment_count
                FROM 
                    {schema_name}.posts
                {join_clause}
                WHERE 
                    {where_clause}
                GROUP BY
                    posts.id, posts.title, posts.content, posts.created_at,
                    users.id, users.username
                {sort_clause}
                LIMIT $1
                OFFSET $2
            ' USING p_limit, p_offset;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create the SQL statement
        return [
            SQLStatement(
                name="dynamic_post_search_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql
            )
        ]


# Test cases
class TestComplexSQLGeneration:
    """Tests for complex SQL generation scenarios."""
    
    def test_advanced_analytics_function(self, mock_config):
        """Test creation of advanced analytics function with window functions and CTEs."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create the emitter
        emitter = AdvancedAnalyticsFunction(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Verify the result
        assert len(statements) == 1
        assert statements[0].name == "user_post_analytics_function"
        assert statements[0].type == SQLStatementType.FUNCTION
        
        # Check for key SQL features in the generated function
        sql = statements[0].sql
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "RETURNS TABLE" in sql
        assert "WITH RECURSIVE" not in sql  # Not using recursion in this function
        assert "WITH post_stats AS" in sql  # Using CTEs
        assert "user_stats AS" in sql  # Multiple CTEs
        assert "popular_posts AS" in sql  # More CTEs
        assert "FIRST_VALUE" in sql  # Window function
        assert "PARTITION BY" in sql  # Window function partitioning
        assert "ORDER BY" in sql  # Window function ordering
        assert "OVER" in sql  # Window function syntax
        
        # Check that the function uses proper role management
        assert f"SET ROLE {mock_config.DB_NAME}_reader;" in sql
    
    def test_recursive_comment_tree_function(self, mock_config):
        """Test creation of recursive comment tree function using CTEs."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create the emitter
        emitter = RecursiveCommentTreeFunction(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Verify the result
        assert len(statements) == 1
        assert statements[0].name == "comment_tree_function"
        assert statements[0].type == SQLStatementType.FUNCTION
        
        # Check for key SQL features in the generated function
        sql = statements[0].sql
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "RETURNS TABLE" in sql
        assert "WITH RECURSIVE comment_tree AS" in sql  # Using recursive CTE
        assert "UNION ALL" in sql  # Recursive CTE union
        assert "-- Base case:" in sql  # Base case for recursion
        assert "-- Recursive case:" in sql  # Recursive case
        assert "ORDER BY path;" in sql  # Ordering by path array
        
        # Check proper role management
        assert f"SET ROLE {mock_config.DB_NAME}_reader;" in sql
    
    def test_full_text_search_function(self, mock_config):
        """Test creation of full-text search function with tsvector and ranking."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create the emitter
        emitter = FullTextSearchFunction(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Verify the result
        assert len(statements) == 1
        assert statements[0].name == "full_text_search_function"
        assert statements[0].type == SQLStatementType.FUNCTION
        
        # Check for key SQL features in the generated function
        sql = statements[0].sql
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "RETURNS TABLE" in sql
        assert "to_tsquery" in sql  # Full-text search query
        assert "to_tsvector" in sql  # Full-text search vector
        assert "ts_rank_cd" in sql  # Full-text search ranking
        assert "setweight" in sql  # Weighting for different fields
        assert "ts_headline" in sql  # Highlighting results
        assert "UNION ALL" in sql  # Combining results
        assert "ORDER BY rank DESC" in sql  # Ordering by rank
        
        # Check proper role management
        assert f"SET ROLE {mock_config.DB_NAME}_reader;" in sql
    
    def test_audit_trail_setup(self, mock_config):
        """Test creation of complete audit trail system with dependencies."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create the emitter
        emitter = AuditTrailTriggerSetup(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Verify the result
        assert len(statements) == 3
        assert statements[0].name == "create_audit_table"
        assert statements[0].type == SQLStatementType.TABLE
        assert statements[1].name == "create_audit_function"
        assert statements[1].type == SQLStatementType.FUNCTION
        assert statements[2].name == "create_audit_helper"
        assert statements[2].type == SQLStatementType.FUNCTION
        
        # Check dependencies are correctly set
        assert statements[1].depends_on == ["create_audit_table"]
        assert statements[2].depends_on == ["create_audit_function"]
        
        # Check for key SQL features in the table creation
        table_sql = statements[0].sql
        assert "CREATE TABLE IF NOT EXISTS" in table_sql
        assert "audit_trail" in table_sql
        assert "PRIMARY KEY" in table_sql
        assert "CREATE INDEX" in table_sql
        assert "GIN" in table_sql  # GIN index for JSONB
        assert "COMMENT ON TABLE" in table_sql  # SQL comments
        assert "GRANT SELECT" in table_sql  # Permissions
        
        # Check for key SQL features in the function creation
        function_sql = statements[1].sql
        assert "CREATE OR REPLACE FUNCTION" in function_sql
        assert "RETURNS TRIGGER" in function_sql
        assert "DECLARE" in function_sql  # Variable declarations
        assert "BEGIN" in function_sql
        assert "EXCEPTION" in function_sql  # Exception handling
        assert "WHEN OTHERS THEN" in function_sql
        assert "INSERT INTO" in function_sql
        assert "jsonb_set" in function_sql  # JSONB operations
        assert "SECURITY DEFINER" in function_sql  # Function security
        
        # Check for key SQL features in the helper function
        helper_sql = statements[2].sql
        assert "CREATE OR REPLACE FUNCTION" in helper_sql
        assert "RETURNS VOID" in helper_sql
        assert "EXECUTE format" in helper_sql  # Dynamic SQL execution
        assert "RAISE NOTICE" in helper_sql  # Notifications
    
    def test_dynamic_query_builder(self, mock_config):
        """Test dynamic SQL generation based on configuration."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create the emitter
        emitter = DynamicQueryBuilder(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Verify the result
        assert len(statements) == 1
        assert statements[0].name == "dynamic_post_search_function"
        assert statements[0].type == SQLStatementType.FUNCTION
        
        # Check for key SQL features in the generated function
        sql = statements[0].sql
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "RETURNS TABLE" in sql
        assert "EXECUTE '" in sql  # Dynamic SQL execution
        assert "posts.is_active" not in sql  # Parameterized value, not hardcoded
        assert "USING p_limit, p_offset" in sql  # Using parameters
        
        # Check for proper SQL structure elements in the dynamically built query
        assert "FROM" in sql
        assert "WHERE" in sql
        assert "GROUP BY" in sql
        assert "ORDER BY" in sql
        
        # Check proper role management
        assert f"SET ROLE {mock_config.DB_NAME}_reader;" in sql
        
        # Test the internal utility functions directly
        where_clause = emitter._build_where_clause(emitter.filter_config, {"user_id": "123", "start_date": "2023-01-01", "end_date": "2023-12-31"})
        assert "users.is_active = True" in where_clause
        assert "posts.user_id = '123'" in where_clause
        assert "posts.created_at >= '2023-01-01'" in where_clause
        assert "posts.created_at <= '2023-12-31'" in where_clause
        
        sort_clause = emitter._build_sort_clause(emitter.sort_config)
        assert "ORDER BY" in sort_clause
        assert "posts.created_at DESC" in sort_clause
        assert "posts.view_count DESC" in sort_clause
        
        join_clause = emitter._build_join_clause(emitter.joins, "test_schema")
        assert "JOIN test_schema.users ON" in join_clause
        assert "LEFT JOIN test_schema.comments ON" in join_clause


class TestSQLEmitterCompositionAndDependencies:
    """Tests for SQL emitter composition and dependencies."""
    
    def test_emitter_composition(self, mock_config, mock_tables):
        """Test composition of multiple SQL emitters with dependencies."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create emitters
        audit_emitter = AuditTrailTriggerSetup(
            config=mock_config,
            connection_config=conn_config
        )
        
        analytics_emitter = AdvancedAnalyticsFunction(
            config=mock_config,
            connection_config=conn_config
        )
        
        search_emitter = FullTextSearchFunction(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate statements from all emitters
        all_statements = []
        all_statements.extend(audit_emitter.generate_sql())
        all_statements.extend(analytics_emitter.generate_sql())
        all_statements.extend(search_emitter.generate_sql())
        
        # Add post-processing or metadata enhancement
        for statement in all_statements:
            # Add documentation
            if statement.type == SQLStatementType.FUNCTION:
                # Append documentation comment
                statement.sql += f"\n\n-- Function automatically generated by SQL Emitter on {datetime.now().strftime('%Y-%m-%d')}"
            
            # Add execution environment info
            statement.sql += f"\n\n-- Generated for schema: {mock_config.DB_SCHEMA}, database: {mock_config.DB_NAME}"
        
        # Verify composition
        assert len(all_statements) == 5  # 3 from audit, 1 from analytics, 1 from search
        
        # Create composed statement indexes for testing
        statements_by_name = {stmt.name: stmt for stmt in all_statements}
        
        # Test proper composition
        for statement in all_statements:
            # Check that all statements have documentation and environment info
            assert "Generated for schema" in statement.sql
            
            # Check that functions have function-specific documentation
            if statement.type == SQLStatementType.FUNCTION:
                assert "Function automatically generated" in statement.sql
        
        # Verify audit trail dependencies are maintained
        assert "create_audit_function" in statements_by_name
        assert "create_audit_helper" in statements_by_name
        assert statements_by_name["create_audit_function"].depends_on == ["create_audit_table"]
        assert statements_by_name["create_audit_helper"].depends_on == ["create_audit_function"]
    
    def test_dependency_ordering(self, mock_config):
        """Test proper dependency ordering for SQL statements."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create the emitter with statements that have dependencies
        emitter = AuditTrailTriggerSetup(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Define dependency ordering function
        def order_by_dependencies(statements: List[SQLStatement]) -> List[SQLStatement]:
            """Order statements by dependencies (topological sort)."""
            # Build dependency graph
            dependency_graph = {stmt.name: set(stmt.depends_on) for stmt in statements}
            
            # Initialize result list
            ordered_statements = []
            unprocessed = {stmt.name: stmt for stmt in statements}
            
            # Process until all statements are ordered
            while unprocessed:
                # Find statements with no unprocessed dependencies
                ready = [
                    name for name, deps in dependency_graph.items()
                    if name in unprocessed and all(dep not in unprocessed for dep in deps)
                ]
                
                # If no statements are ready, we have a circular dependency
                if not ready:
                    raise ValueError("Circular dependency detected in SQL statements")
                
                # Add ready statements to the result and remove from unprocessed
                for name in ready:
                    ordered_statements.append(unprocessed[name])
                    del unprocessed[name]
            
            return ordered_statements
        
        # Order the statements
        ordered_statements = order_by_dependencies(statements)
        
        # Verify ordering
        assert len(ordered_statements) == 3
        assert ordered_statements[0].name == "create_audit_table"
        assert ordered_statements[1].name == "create_audit_function"
        assert ordered_statements[2].name == "create_audit_helper"
        
        # Verify invalid dependencies are caught
        # Create a circular dependency
        circular_statements = statements.copy()
        circular_statements[0].depends_on = ["create_audit_helper"]  # This creates a cycle
        
        # Test circular dependency detection
        with pytest.raises(ValueError, match="Circular dependency detected"):
            order_by_dependencies(circular_statements)


class TestSQLOptimizationTechniques:
    """Tests for SQL optimization techniques."""
    
    def test_optimized_indexes_creation(self, mock_config):
        """Test creation of optimized indexes based on query patterns."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create a custom emitter for optimized indexes
        class OptimizedIndexEmitter(SQLEmitter):
            """Emitter for creating optimized indexes based on query patterns."""
            
            # Query patterns to optimize for
            query_patterns = [
                {
                    "description": "User posts by date range",
                    "table": "posts",
                    "where_columns": ["user_id", "created_at"],
                    "order_columns": ["created_at DESC"],
                    "frequency": "high"
                },
                {
                    "description": "Post search by title/content",
                    "table": "posts",
                    "where_columns": ["published"],
                    "using": "GIN",
                    "expression": "to_tsvector('english', title || ' ' || content)",
                    "frequency": "medium"
                },
                {
                    "description": "Comments by post",
                    "table": "comments",
                    "where_columns": ["post_id"],
                    "order_columns": ["created_at DESC"],
                    "frequency": "high"
                },
                {
                    "description": "User activity history",
                    "table": "users",
                    "where_columns": ["username", "is_active"],
                    "frequency": "low"
                }
            ]
            
            def generate_sql(self) -> List[SQLStatement]:
                """Generate optimized indexes based on query patterns."""
                schema_name = self.connection_config.db_schema if self.connection_config else "public"
                db_name = self.connection_config.db_name if self.connection_config else "test_db"
                
                statements = []
                
                # SQL header
                header = f"""
                SET ROLE {db_name}_admin;
                
                -- Optimized indexes based on query pattern analysis
                -- Generated on {datetime.now().strftime('%Y-%m-%d')}
                """
                
                # Generate optimized indexes
                index_sql = header
                
                # Process each query pattern
                for pattern in self.query_patterns:
                    table = pattern["table"]
                    description = pattern["description"]
                    frequency = pattern["frequency"]
                    
                    # Add a comment explaining the index
                    index_sql += f"\n\n-- Index for: {description} (query frequency: {frequency})\n"
                    
                    # Generate index name
                    if "using" in pattern and pattern["using"] == "GIN" and "expression" in pattern:
                        # GIN index for full-text search
                        expression = pattern["expression"]
                        index_name = f"idx_{table}_tsvector"
                        
                        index_sql += f"""
                        DROP INDEX IF EXISTS {schema_name}.{index_name};
                        CREATE INDEX {index_name} ON {schema_name}.{table} USING GIN ({expression});
                        """
                        
                        # Add comment
                        index_sql += f"COMMENT ON INDEX {schema_name}.{index_name} IS 'Full-text search index for {table}';\n"
                    else:
                        # Regular B-tree index for WHERE and ORDER BY
                        where_columns = pattern.get("where_columns", [])
                        order_columns = pattern.get("order_columns", [])
                        
                        # Build column list - use compound index if multiple columns are frequently used together
                        if where_columns and order_columns:
                            # Create a covering index for both WHERE and ORDER BY
                            include_columns = [col.split()[0] for col in order_columns]  # Strip DESC/ASC if present
                            where_col_str = ", ".join(where_columns)
                            index_name = f"idx_{table}_{'_'.join(where_columns)}"
                            
                            index_sql += f"""
                            DROP INDEX IF EXISTS {schema_name}.{index_name};
                            CREATE INDEX {index_name} ON {schema_name}.{table} ({where_col_str}) INCLUDE ({', '.join(include_columns)});
                            """
                        elif where_columns:
                            # Create index for WHERE clause only
                            if len(where_columns) == 1:
                                # Single column index
                                index_name = f"idx_{table}_{where_columns[0]}"
                                index_sql += f"""
                                DROP INDEX IF EXISTS {schema_name}.{index_name};
                                CREATE INDEX {index_name} ON {schema_name}.{table} ({where_columns[0]});
                                """
                            else:
                                # Multi-column index
                                index_name = f"idx_{table}_{'_'.join(where_columns)}"
                                where_col_str = ", ".join(where_columns)
                                index_sql += f"""
                                DROP INDEX IF EXISTS {schema_name}.{index_name};
                                CREATE INDEX {index_name} ON {schema_name}.{table} ({where_col_str});
                                """
                        
                        # Add comment
                        index_sql += f"COMMENT ON INDEX {schema_name}.{index_name} IS 'Index for {description}';\n"
                    
                    # Add index statistics hint if high frequency query
                    if frequency == "high":
                        index_sql += f"""
                        -- Collect statistics for high-frequency query pattern
                        ANALYZE {schema_name}.{table};
                        """
                
                statements.append(
                    SQLStatement(
                        name="create_optimized_indexes",
                        type=SQLStatementType.INDEX,
                        sql=index_sql
                    )
                )
                
                # For high-frequency tables, add autovacuum tuning
                vacuum_sql = f"""
                SET ROLE {db_name}_admin;
                
                -- Customize autovacuum for high-write tables
                
                -- Posts table (high write frequency)
                ALTER TABLE {schema_name}.posts SET (
                    autovacuum_vacuum_scale_factor = 0.05,  -- Vacuum when 5% of tuples are dead
                    autovacuum_analyze_scale_factor = 0.05, -- Analyze when 5% of tuples are modified
                    autovacuum_vacuum_cost_limit = 1000     -- Allow more work per vacuum
                );
                
                -- Comments table (high write frequency)
                ALTER TABLE {schema_name}.comments SET (
                    autovacuum_vacuum_scale_factor = 0.05,
                    autovacuum_analyze_scale_factor = 0.05,
                    autovacuum_vacuum_cost_limit = 1000
                );
                """
                
                statements.append(
                    SQLStatement(
                        name="tune_autovacuum",
                        type=SQLStatementType.TABLE,
                        sql=vacuum_sql
                    )
                )
                
                return statements
        
        # Create the emitter
        emitter = OptimizedIndexEmitter(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Verify the result
        assert len(statements) == 2
        assert statements[0].name == "create_optimized_indexes"
        assert statements[0].type == SQLStatementType.INDEX
        assert statements[1].name == "tune_autovacuum"
        assert statements[1].type == SQLStatementType.TABLE
        
        # Check for key optimization techniques
        index_sql = statements[0].sql
        assert "USING GIN" in index_sql  # GIN index for full-text search
        assert "INCLUDE" in index_sql  # Covering index for performance
        assert "ANALYZE" in index_sql  # Statistics collection
        
        vacuum_sql = statements[1].sql
        assert "autovacuum_vacuum_scale_factor" in vacuum_sql  # Autovacuum tuning
        assert "autovacuum_analyze_scale_factor" in vacuum_sql
        assert "autovacuum_vacuum_cost_limit" in vacuum_sql
    
    def test_query_optimization_techniques(self, mock_config):
        """Test SQL query optimization techniques."""
        # Set up connection config
        conn_config = ConnectionConfig(
            db_name=mock_config.DB_NAME,
            db_schema=mock_config.DB_SCHEMA,
            db_user_pw=mock_config.DB_USER_PW,
            db_driver=mock_config.DB_SYNC_DRIVER
        )
        
        # Create a custom emitter with optimization techniques
        class OptimizedQueryEmitter(SQLEmitter):
            """Emitter that demonstrates SQL query optimization techniques."""
            
            def generate_sql(self) -> List[SQLStatement]:
                """Generate optimized SQL queries."""
                schema_name = self.connection_config.db_schema if self.connection_config else "public"
                db_name = self.connection_config.db_name if self.connection_config else "test_db"
                
                statements = []
                
                # Optimization 1: Use CTEs for complex calculations instead of subqueries
                cte_optimization = f"""
                -- OPTIMIZATION TECHNIQUE: Common Table Expressions (CTEs)
                -- Using CTEs instead of multiple subqueries improves readability and often performance
                
                -- Original query with subqueries (less optimal):
                /*
                SELECT
                    u.id, u.username,
                    (SELECT COUNT(*) FROM {schema_name}.posts p WHERE p.user_id = u.id) AS post_count,
                    (SELECT COUNT(*) FROM {schema_name}.comments c WHERE c.user_id = u.id) AS comment_count,
                    (SELECT MAX(p2.created_at) FROM {schema_name}.posts p2 WHERE p2.user_id = u.id) AS last_post_date
                FROM
                    {schema_name}.users u
                WHERE
                    u.is_active = true
                */
                
                -- Optimized query with CTEs:
                SET ROLE {db_name}_reader;
                WITH user_posts AS (
                    SELECT 
                        user_id,
                        COUNT(*) AS post_count,
                        MAX(created_at) AS last_post_date
                    FROM 
                        {schema_name}.posts
                    GROUP BY 
                        user_id
                ),
                user_comments AS (
                    SELECT 
                        user_id,
                        COUNT(*) AS comment_count
                    FROM 
                        {schema_name}.comments
                    GROUP BY 
                        user_id
                )
                SELECT
                    u.id, u.username,
                    COALESCE(up.post_count, 0) AS post_count,
                    COALESCE(uc.comment_count, 0) AS comment_count,
                    up.last_post_date
                FROM
                    {schema_name}.users u
                LEFT JOIN
                    user_posts up ON u.id = up.user_id
                LEFT JOIN
                    user_comments uc ON u.id = uc.user_id
                WHERE
                    u.is_active = true;
                """
                
                statements.append(
                    SQLStatement(
                        name="cte_optimization",
                        type=SQLStatementType.FUNCTION,
                        sql=cte_optimization
                    )
                )
                
                # Optimization 2: Use LATERAL joins for correlated subqueries
                lateral_optimization = f"""
                -- OPTIMIZATION TECHNIQUE: LATERAL joins 
                -- Using LATERAL joins for row-by-row processing that depends on the main query row
                
                -- Original query with correlated subqueries (less optimal):
                /*
                SELECT 
                    p.id, p.title,
                    (SELECT c.id FROM {schema_name}.comments c 
                     WHERE c.post_id = p.id 
                     ORDER BY c.created_at DESC LIMIT 1) AS latest_comment_id,
                    (SELECT c.content FROM {schema_name}.comments c 
                     WHERE c.post_id = p.id 
                     ORDER BY c.created_at DESC LIMIT 1) AS latest_comment,
                    (SELECT u.username FROM {schema_name}.users u 
                     JOIN {schema_name}.comments c ON u.id = c.user_id
                     WHERE c.post_id = p.id 
                     ORDER BY c.created_at DESC LIMIT 1) AS latest_commenter
                FROM 
                    {schema_name}.posts p
                WHERE 
                    p.published = true
                */
                
                -- Optimized query with LATERAL joins:
                SET ROLE {db_name}_reader;
                SELECT 
                    p.id, p.title,
                    latest_comment.id AS latest_comment_id,
                    latest_comment.content AS latest_comment,
                    latest_comment.username AS latest_commenter
                FROM 
                    {schema_name}.posts p
                LEFT JOIN LATERAL (
                    SELECT 
                        c.id,
                        c.content,
                        u.username
                    FROM 
                        {schema_name}.comments c
                    JOIN 
                        {schema_name}.users u ON c.user_id = u.id
                    WHERE 
                        c.post_id = p.id
                    ORDER BY 
                        c.created_at DESC
                    LIMIT 1
                ) latest_comment ON true
                WHERE 
                    p.published = true;
                """
                
                statements.append(
                    SQLStatement(
                        name="lateral_optimization",
                        type=SQLStatementType.FUNCTION,
                        sql=lateral_optimization
                    )
                )
                
                # Optimization 3: Use JSONB_AGG for parent-child data hierarchies
                jsonb_optimization = f"""
                -- OPTIMIZATION TECHNIQUE: JSONB_AGG for hierarchical data 
                -- Using JSONB_AGG to create hierarchical data structures in a single query
                
                -- Original approach with multiple queries (less optimal):
                /*
                -- First query: Get posts
                SELECT id, title, content FROM {schema_name}.posts WHERE user_id = 'some_user_id';
                
                -- Then for each post, query its comments:
                SELECT id, content FROM {schema_name}.comments WHERE post_id = 'post_id_1';
                SELECT id, content FROM {schema_name}.comments WHERE post_id = 'post_id_2';
                -- ...etc.
                */
                
                -- Optimized query with JSONB_AGG:
                SET ROLE {db_name}_reader;
                SELECT 
                    p.id,
                    p.title,
                    p.content,
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'id', c.id,
                            'content', c.content,
                            'username', u.username,
                            'created_at', c.created_at
                        ) ORDER BY c.created_at DESC
                    ) FILTER (WHERE c.id IS NOT NULL) AS comments
                FROM 
                    {schema_name}.posts p
                LEFT JOIN 
                    {schema_name}.comments c ON p.id = c.post_id
                LEFT JOIN 
                    {schema_name}.users u ON c.user_id = u.id
                WHERE 
                    p.user_id = '00000000-0000-0000-0000-000000000001'
                GROUP BY 
                    p.id, p.title, p.content;
                """
                
                statements.append(
                    SQLStatement(
                        name="jsonb_optimization",
                        type=SQLStatementType.FUNCTION,
                        sql=jsonb_optimization
                    )
                )
                
                # Optimization 4: Use function-based indexes for complex conditions
                function_index_optimization = f"""
                -- OPTIMIZATION TECHNIQUE: Function-based indexes 
                -- Using indexes on expressions for better query performance
                
                -- Create function-based index for date range queries
                SET ROLE {db_name}_admin;
                
                -- Create function-based index for case-insensitive search
                DROP INDEX IF EXISTS {schema_name}.idx_users_username_lower;
                CREATE INDEX idx_users_username_lower ON {schema_name}.users (LOWER(username));
                
                -- Create function-based index for date range queries
                DROP INDEX IF EXISTS {schema_name}.idx_posts_year_month;
                CREATE INDEX idx_posts_year_month ON {schema_name}.posts (EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at));
                
                -- Create function-based index for JSON data
                DROP INDEX IF EXISTS {schema_name}.idx_posts_metadata_published;
                CREATE INDEX idx_posts_metadata_published ON {schema_name}.posts ((metadata->>'published')::boolean);
                
                -- Example query using these indexes:
                SET ROLE {db_name}_reader;
                
                -- This query can use the LOWER index:
                SELECT * FROM {schema_name}.users WHERE LOWER(username) = LOWER('UserName');
                
                -- This query can use the date extraction index:
                SELECT * FROM {schema_name}.posts 
                WHERE EXTRACT(YEAR FROM created_at) = 2023 AND EXTRACT(MONTH FROM created_at) = 6;
                
                -- This query can use the JSON index:
                SELECT * FROM {schema_name}.posts WHERE (metadata->>'published')::boolean = true;
                """
                
                statements.append(
                    SQLStatement(
                        name="function_index_optimization",
                        type=SQLStatementType.INDEX,
                        sql=function_index_optimization
                    )
                )
                
                # Optimization 5: Using MATERIALIZED VIEWS for complex reporting queries
                materialized_view_optimization = f"""
                -- OPTIMIZATION TECHNIQUE: MATERIALIZED VIEWS 
                -- Using materialized views for complex reporting queries
                
                SET ROLE {db_name}_admin;
                
                -- Create materialized view for user activity reports
                DROP MATERIALIZED VIEW IF EXISTS {schema_name}.user_activity_report;
                CREATE MATERIALIZED VIEW {schema_name}.user_activity_report AS
                SELECT 
                    u.id AS user_id,
                    u.username,
                    COUNT(DISTINCT p.id) AS post_count,
                    COUNT(DISTINCT c.id) AS comment_count,
                    MAX(p.created_at) AS last_post_date,
                    MAX(c.created_at) AS last_comment_date,
                    SUM(p.view_count) AS total_views,
                    (COUNT(DISTINCT c.id)::float / NULLIF(COUNT(DISTINCT p.id), 0)) AS comments_per_post
                FROM 
                    {schema_name}.users u
                LEFT JOIN 
                    {schema_name}.posts p ON u.id = p.user_id
                LEFT JOIN 
                    {schema_name}.comments c ON u.id = c.user_id
                WHERE 
                    u.is_active = true
                GROUP BY 
                    u.id, u.username;
                
                -- Create index on materialized view
                CREATE UNIQUE INDEX idx_user_activity_report_user_id ON {schema_name}.user_activity_report(user_id);
                
                -- Grant permissions
                GRANT SELECT ON {schema_name}.user_activity_report TO {db_name}_reader;
                
                -- Function to refresh the materialized view
                CREATE OR REPLACE FUNCTION {schema_name}.refresh_activity_report() 
                RETURNS VOID AS $$
                BEGIN
                    REFRESH MATERIALIZED VIEW CONCURRENTLY {schema_name}.user_activity_report;
                END;
                $$ LANGUAGE plpgsql;
                
                -- Grant permissions to refresh function
                GRANT EXECUTE ON FUNCTION {schema_name}.refresh_activity_report() TO {db_name}_writer;
                
                -- Example query using the materialized view:
                SET ROLE {db_name}_reader;
                SELECT * FROM {schema_name}.user_activity_report WHERE post_count > 0 ORDER BY total_views DESC;
                """
                
                statements.append(
                    SQLStatement(
                        name="materialized_view_optimization",
                        type=SQLStatementType.VIEW,
                        sql=materialized_view_optimization
                    )
                )
                
                return statements
        
        # Create the emitter
        emitter = OptimizedQueryEmitter(
            config=mock_config,
            connection_config=conn_config
        )
        
        # Generate SQL statements
        statements = emitter.generate_sql()
        
        # Verify the result
        assert len(statements) == 5
        
        # Check for optimization techniques
        optimization_types = [stmt.name for stmt in statements]
        assert "cte_optimization" in optimization_types
        assert "lateral_optimization" in optimization_types
        assert "jsonb_optimization" in optimization_types
        assert "function_index_optimization" in optimization_types
        assert "materialized_view_optimization" in optimization_types
        
        # Check for specific optimization keywords
        assert "WITH" in statements[0].sql  # CTEs
        assert "LATERAL" in statements[1].sql  # LATERAL joins
        assert "JSONB_AGG" in statements[2].sql  # JSON aggregation
        assert "CREATE INDEX" in statements[3].sql  # Function-based indexes
        assert "MATERIALIZED VIEW" in statements[4].sql  # Materialized views