"""
SQL emitters for vector search functionality.

This module contains SQL emitters for creating vector columns, indexes, and related functions.
It also provides emitters for executing vector search operations like similarity search and
hybrid vector-graph search.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple, TypeVar, Generic, Protocol, Union

from sqlalchemy.engine import Connection
from sqlalchemy import text as sql_text

from uno.sql.emitter import SQLEmitter
from uno.database.session import DatabaseSessionProtocol
from uno.settings import uno_settings

T = TypeVar('T')

# Define a protocol for database connections that can execute queries
class ExecutableConnection(Protocol):
    async def execute(self, statement, *args, **kwargs): ...
    
# Type alias for connections that can be either SQLAlchemy Connection or DatabaseSessionProtocol
ConnectionType = Union[Connection, DatabaseSessionProtocol]
from uno.sql.statement import SQLStatement, SQLStatementType


class VectorSQLEmitter(SQLEmitter):
    """
    Emitter for creating pgvector extension and related database objects.
    
    This emitter creates the pgvector extension, helper functions for
    vector operations, and necessary permissions.
    """
    
    def generate_sql(self) -> List[SQLStatement]:
        """
        Generate SQL statements for setting up vector functionality.
        
        Returns:
            List of SQL statements with metadata
        """
        statements = []
        
        # Get config values safely
        if hasattr(self.config, "DB_SCHEMA") and hasattr(self.config, "DB_NAME"):
            db_schema = self.config.DB_SCHEMA
            db_name = self.config.DB_NAME
        else:
            from uno.settings import uno_settings
            db_schema = uno_settings.DB_SCHEMA
            db_name = uno_settings.DB_NAME
            
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"
        admin_role = f"{db_name}_admin"
        
        # SQL for creating pgvector extension
        create_vector_extension_sql = f"""
        -- Create the pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector;

        -- Set search path for the current session
        SET search_path TO {db_schema}, public;
        """
        
        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_vector_extension",
                type=SQLStatementType.EXTENSION,
                sql=create_vector_extension_sql,
            )
        )
        
        # SQL for creating vector helper functions
        create_vector_functions_sql = f"""
        -- Create helper functions for vector operations in the schema
        
        -- Function to create a vector embedding from text using the embedding system
        -- This is a placeholder that will be replaced by actual embedding logic
        CREATE OR REPLACE FUNCTION {db_schema}.generate_embedding(
            text_content TEXT,
            dimensions INT DEFAULT 1536
        ) RETURNS vector AS $$
        BEGIN
            -- This is a placeholder implementation
            -- In production, this would call an embedding service or use a local model
            -- For now, we return a random vector of the specified dimension
            RETURN (
                SELECT 
                    vector_agg(random()) 
                FROM 
                    generate_series(1, dimensions)
            );
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Grant execute permission on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.generate_embedding TO {admin_role}, {writer_role}, {reader_role};

        -- Function to calculate cosine similarity between two vectors
        CREATE OR REPLACE FUNCTION {db_schema}.cosine_similarity(
            a vector,
            b vector
        ) RETURNS float8 AS $$
        BEGIN
            -- Use pgvector's built-in operator for cosine similarity
            RETURN 1 - (a <=> b);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        
        -- Grant execute permission on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.cosine_similarity TO {admin_role}, {writer_role}, {reader_role};

        -- Function to create an embedding trigger for a table
        CREATE OR REPLACE FUNCTION {db_schema}.create_embedding_trigger(
            table_name TEXT,
            vector_column_name TEXT DEFAULT 'embedding',
            content_columns TEXT[] DEFAULT '{{"content"}}',
            dimensions INT DEFAULT 1536
        ) RETURNS void AS $$
        DECLARE
            trigger_name TEXT;
            function_name TEXT;
            content_expression TEXT;
            i INT;
        BEGIN
            -- Construct the content expression by concatenating columns with spaces
            content_expression := '';
            FOR i IN 1..array_length(content_columns, 1) LOOP
                IF i > 1 THEN
                    content_expression := content_expression || ' || '' '' || ';
                END IF;
                content_expression := content_expression || 'COALESCE(NEW.' || content_columns[i] || ', '''')';
            END LOOP;
            
            -- Create function name based on table name
            function_name := '{db_schema}.update_' || table_name || '_' || vector_column_name || '_trigger_fn';
            
            -- Create trigger name based on table name
            trigger_name := table_name || '_' || vector_column_name || '_trigger';

            -- Create or replace the trigger function
            EXECUTE format('
                CREATE OR REPLACE FUNCTION %s() RETURNS trigger AS $func$
                BEGIN
                    -- Generate embedding when content columns are updated
                    IF (TG_OP = ''INSERT'' OR 
                        (TG_OP = ''UPDATE'' AND (%s IS DISTINCT FROM %s))) THEN
                        NEW.%I := {db_schema}.generate_embedding(%s, %s);
                    END IF;
                    RETURN NEW;
                END;
                $func$ LANGUAGE plpgsql SECURITY DEFINER;',
                function_name,
                content_expression,
                content_expression,
                vector_column_name,
                content_expression,
                dimensions
            );
            
            -- Grant execute permission on the function
            EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO {admin_role}, {writer_role};', function_name);
            
            -- Create the trigger on the table
            EXECUTE format('
                DROP TRIGGER IF EXISTS %I ON {db_schema}.%I;
                CREATE TRIGGER %I
                BEFORE INSERT OR UPDATE ON {db_schema}.%I
                FOR EACH ROW
                EXECUTE FUNCTION %s();',
                trigger_name,
                table_name,
                trigger_name,
                table_name,
                function_name
            );
            
            -- Log the created trigger
            RAISE NOTICE 'Created embedding trigger % on table {db_schema}.%', trigger_name, table_name;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Grant execute permission on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.create_embedding_trigger TO {admin_role};
        """
        
        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_vector_functions",
                type=SQLStatementType.FUNCTION,
                sql=create_vector_functions_sql,
            )
        )
        
        # SQL for creating vector index management functions
        create_vector_index_functions_sql = f"""
        -- Create functions for managing vector indexes
        
        -- Function to create an HNSW index on a vector column
        CREATE OR REPLACE FUNCTION {db_schema}.create_hnsw_index(
            table_name TEXT,
            column_name TEXT DEFAULT 'embedding',
            m INT DEFAULT 16,          -- Max number of connections per layer
            ef_construction INT DEFAULT 64  -- Size of the dynamic candidate list for construction
        ) RETURNS void AS $$
        DECLARE
            index_name TEXT;
        BEGIN
            -- Create index name
            index_name := table_name || '_' || column_name || '_hnsw_idx';
            
            -- Create the HNSW index
            EXECUTE format('
                CREATE INDEX IF NOT EXISTS %I
                ON {db_schema}.%I USING hnsw (%I vector_cosine_ops)
                WITH (m = %s, ef_construction = %s);',
                index_name,
                table_name,
                column_name,
                m,
                ef_construction
            );
            
            RAISE NOTICE 'Created HNSW index % on {db_schema}.%.%', index_name, table_name, column_name;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Grant execute permission on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.create_hnsw_index TO {admin_role};
        
        -- Function to create an IVF-Flat index on a vector column
        CREATE OR REPLACE FUNCTION {db_schema}.create_ivfflat_index(
            table_name TEXT,
            column_name TEXT DEFAULT 'embedding',
            lists INT DEFAULT 100       -- Number of inverted lists
        ) RETURNS void AS $$
        DECLARE
            index_name TEXT;
        BEGIN
            -- Create index name
            index_name := table_name || '_' || column_name || '_ivfflat_idx';
            
            -- Create the IVF-Flat index
            EXECUTE format('
                CREATE INDEX IF NOT EXISTS %I
                ON {db_schema}.%I USING ivfflat (%I vector_cosine_ops)
                WITH (lists = %s);',
                index_name,
                table_name,
                column_name,
                lists
            );
            
            RAISE NOTICE 'Created IVF-Flat index % on {db_schema}.%.%', index_name, table_name, column_name;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Grant execute permission on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.create_ivfflat_index TO {admin_role};
        """
        
        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_vector_index_functions",
                type=SQLStatementType.FUNCTION,
                sql=create_vector_index_functions_sql,
            )
        )
        
        # SQL for creating vector search functions
        create_vector_search_functions_sql = f"""
        -- Create functions for vector similarity search
        
        -- Function to perform vector similarity search on a table
        CREATE OR REPLACE FUNCTION {db_schema}.vector_search(
            table_name TEXT,
            query_embedding vector,
            column_name TEXT DEFAULT 'embedding',
            limit_val INT DEFAULT 10,
            threshold FLOAT DEFAULT 0.7,
            where_clause TEXT DEFAULT NULL
        ) RETURNS TABLE (
            id TEXT,
            similarity FLOAT,
            row_data JSONB
        ) AS $$
        DECLARE
            query TEXT;
            where_part TEXT;
        BEGIN
            -- Build the where clause if provided
            IF where_clause IS NOT NULL AND where_clause != '' THEN
                where_part := ' AND ' || where_clause;
            ELSE
                where_part := '';
            END IF;
            
            -- Build and execute the query
            query := format('
                SELECT 
                    id::TEXT, 
                    (1 - (%I <=> $1)) AS similarity,
                    row_to_json({db_schema}.%I.*)::JSONB AS row_data
                FROM {db_schema}.%I
                WHERE (1 - (%I <=> $1)) >= $2 %s
                ORDER BY %I <=> $1
                LIMIT $3',
                column_name,
                table_name,
                table_name,
                column_name,
                where_part,
                column_name
            );
            
            RETURN QUERY EXECUTE query
            USING query_embedding, threshold, limit_val;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Grant execute permission on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.vector_search TO {admin_role}, {writer_role}, {reader_role};
        
        -- Function to perform hybrid vector and graph search
        CREATE OR REPLACE FUNCTION {db_schema}.hybrid_search(
            table_name TEXT,
            query_embedding vector,
            graph_traversal_query TEXT DEFAULT NULL,
            column_name TEXT DEFAULT 'embedding',
            limit_val INT DEFAULT 10,
            threshold FLOAT DEFAULT 0.7
        ) RETURNS TABLE (
            id TEXT,
            similarity FLOAT,
            row_data JSONB,
            graph_distance INT
        ) AS $$
        DECLARE
            query TEXT;
            has_graph BOOLEAN;
        BEGIN
            -- Check if graph traversal is requested
            has_graph := graph_traversal_query IS NOT NULL AND graph_traversal_query != '';
            
            IF has_graph THEN
                -- Hybrid search with graph traversal and vector similarity
                query := format('
                    WITH graph_results AS (
                        %s
                    ),
                    vector_results AS (
                        SELECT 
                            id::TEXT, 
                            (1 - (%I <=> $1)) AS similarity,
                            row_to_json({db_schema}.%I.*)::JSONB AS row_data
                        FROM {db_schema}.%I
                        WHERE (1 - (%I <=> $1)) >= $2
                    )
                    SELECT 
                        v.id,
                        v.similarity,
                        v.row_data,
                        COALESCE(g.distance, 999999) AS graph_distance
                    FROM 
                        vector_results v
                    LEFT JOIN 
                        graph_results g ON v.id = g.id
                    ORDER BY 
                        -- Prefer items with both graph connection and vector similarity
                        CASE WHEN g.id IS NOT NULL THEN 0 ELSE 1 END,
                        -- Then by graph distance (if available)
                        COALESCE(g.distance, 999999),
                        -- Then by vector similarity
                        v.similarity DESC
                    LIMIT $3',
                    graph_traversal_query,
                    column_name,
                    table_name,
                    table_name,
                    column_name
                );
            ELSE
                -- Plain vector search
                query := format('
                    SELECT 
                        id::TEXT, 
                        (1 - (%I <=> $1)) AS similarity,
                        row_to_json({db_schema}.%I.*)::JSONB AS row_data,
                        999999 AS graph_distance
                    FROM {db_schema}.%I
                    WHERE (1 - (%I <=> $1)) >= $2
                    ORDER BY %I <=> $1
                    LIMIT $3',
                    column_name,
                    table_name,
                    table_name,
                    column_name,
                    column_name
                );
            END IF;
            
            RETURN QUERY EXECUTE query
            USING query_embedding, threshold, limit_val;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Grant execute permission on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.hybrid_search TO {admin_role}, {writer_role}, {reader_role};
        """
        
        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_vector_search_functions",
                type=SQLStatementType.FUNCTION,
                sql=create_vector_search_functions_sql,
            )
        )
        
        return statements


class VectorIntegrationEmitter(SQLEmitter):
    """
    Emitter for integrating vector search with other database features.
    
    This emitter creates functions and procedures that integrate vector search
    with other database features like graph database capabilities.
    """
    
    def generate_sql(self) -> List[SQLStatement]:
        """
        Generate SQL statements for vector integration.
        
        Returns:
            List of SQL statements with metadata
        """
        statements = []
        
        # Get config values safely
        if hasattr(self.config, "DB_SCHEMA") and hasattr(self.config, "DB_NAME"):
            db_schema = self.config.DB_SCHEMA
            db_name = self.config.DB_NAME
        else:
            from uno.settings import uno_settings
            db_schema = uno_settings.DB_SCHEMA
            db_name = uno_settings.DB_NAME
            
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"
        admin_role = f"{db_name}_admin"
        
        # SQL for integrating vector search with graph database
        integration_sql = f"""
        -- Function to perform hybrid vector and graph search
        CREATE OR REPLACE FUNCTION {db_schema}.hybrid_graph_search(
            vertex_label TEXT,            -- The vertex label to search
            query_embedding vector,       -- The query embedding vector
            start_id TEXT DEFAULT NULL,   -- Optional start vertex for graph traversal
            max_hops INT DEFAULT 2,       -- Maximum number of hops in graph traversal
            limit_val INT DEFAULT 10,     -- Maximum number of results to return
            threshold FLOAT DEFAULT 0.7   -- Minimum similarity threshold
        ) RETURNS TABLE (
            id TEXT,
            similarity FLOAT,
            vertex_data JSONB,
            graph_distance INT
        ) AS $$
        DECLARE
            graph_query TEXT;
            combined_query TEXT;
        BEGIN
            -- Build the graph traversal query if a start_id is provided
            IF start_id IS NOT NULL THEN
                graph_query := format('
                    SELECT 
                        v.id::TEXT,
                        p.distance
                    FROM
                        ag_catalog.cypher(''graph'', ''
                            MATCH p = (start)-[*1..%s]->(v)
                            WHERE id(start) = $1
                            RETURN id(v) AS id, length(p) AS distance
                            ORDER BY distance
                        '', %L)
                        AS (id TEXT, distance INT)
                    ', 
                    max_hops,
                    start_id
                );
            ELSE
                -- If no start_id, use a simple graph query to get all vertices of the given label
                graph_query := format('
                    SELECT 
                        v.id::TEXT,
                        0 AS distance
                    FROM
                        graph.%I v
                    ', 
                    vertex_label
                );
            END IF;
            
            -- Build the combined query for hybrid search
            combined_query := format('
                WITH graph_results AS (
                    %s
                ),
                vector_results AS (
                    SELECT 
                        v.id::TEXT, 
                        (1 - (v.embedding <=> $1)) AS similarity,
                        to_jsonb(v.*) AS vertex_data
                    FROM 
                        graph.%I v
                    WHERE 
                        (1 - (v.embedding <=> $1)) >= $2
                )
                SELECT 
                    v.id,
                    v.similarity,
                    v.vertex_data,
                    COALESCE(g.distance, 999999) AS graph_distance
                FROM 
                    vector_results v
                LEFT JOIN 
                    graph_results g ON v.id = g.id
                ORDER BY 
                    -- Prefer items with both graph connection and vector similarity
                    CASE WHEN g.id IS NOT NULL THEN 0 ELSE 1 END,
                    -- Then by graph distance (if available)
                    COALESCE(g.distance, 999999),
                    -- Then by vector similarity
                    v.similarity DESC
                LIMIT $3
            ',
            graph_query,
            vertex_label
            );
            
            RETURN QUERY EXECUTE combined_query
            USING query_embedding, threshold, limit_val;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Grant permissions on the function
        GRANT EXECUTE ON FUNCTION {db_schema}.hybrid_graph_search TO {admin_role}, {writer_role}, {reader_role};
        """
        
        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_hybrid_graph_search",
                type=SQLStatementType.FUNCTION,
                sql=integration_sql,
            )
        )
        
        return statements


class CreateVectorTables(SQLEmitter):
    """
    Emitter for creating standard vector-enabled tables.
    
    This emitter creates a standard set of tables for vector search capabilities
    like a documents table for RAG.
    """
    
    def generate_sql(self) -> List[SQLStatement]:
        """
        Generate SQL statements for creating vector-enabled tables.
        
        Returns:
            List of SQL statements with metadata
        """
        statements = []
        
        # Get config values safely
        if hasattr(self.config, "DB_SCHEMA") and hasattr(self.config, "DB_NAME"):
            db_schema = self.config.DB_SCHEMA
            db_name = self.config.DB_NAME
        else:
            from uno.settings import uno_settings
            db_schema = uno_settings.DB_SCHEMA
            db_name = uno_settings.DB_NAME
            
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"
        admin_role = f"{db_name}_admin"
        
        # SQL for creating a documents table for RAG
        create_documents_table_sql = f"""
        -- Create a documents table for RAG (Retrieval-Augmented Generation)
        CREATE TABLE IF NOT EXISTS {db_schema}.documents (
            id TEXT PRIMARY KEY DEFAULT {db_schema}.gen_ulid(),
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{{}}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            embedding vector(1536)  -- Default to 1536 dimensions (OpenAI Ada 2)
        );
        
        -- Set up table permissions
        ALTER TABLE {db_schema}.documents OWNER TO {admin_role};
        GRANT SELECT ON {db_schema}.documents TO {reader_role};
        GRANT SELECT, INSERT, UPDATE, DELETE ON {db_schema}.documents TO {writer_role}, {admin_role};
        
        -- Create timestamp trigger
        CREATE OR REPLACE FUNCTION {db_schema}.documents_update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Create trigger for timestamps
        DROP TRIGGER IF EXISTS documents_timestamp_trigger ON {db_schema}.documents;
        CREATE TRIGGER documents_timestamp_trigger
        BEFORE UPDATE ON {db_schema}.documents
        FOR EACH ROW
        EXECUTE FUNCTION {db_schema}.documents_update_timestamp();
        
        -- Create embedding trigger
        SELECT {db_schema}.create_embedding_trigger(
            'documents',  -- table name
            'embedding',  -- vector column
            ARRAY['title', 'content'],  -- content columns
            1536  -- dimensions
        );
        
        -- Create HNSW index
        SELECT {db_schema}.create_hnsw_index('documents', 'embedding');
        """
        
        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_documents_table",
                type=SQLStatementType.TABLE,
                sql=create_documents_table_sql,
            )
        )
        
        # SQL for creating a vector config table
        create_vector_config_table_sql = f"""
        -- Create a vector configuration table to manage entity embedding configs
        CREATE TABLE IF NOT EXISTS {db_schema}.vector_config (
            entity_type TEXT PRIMARY KEY,
            dimensions INTEGER NOT NULL DEFAULT 1536,
            content_fields TEXT[] NOT NULL,
            index_type TEXT NOT NULL DEFAULT 'hnsw',
            index_options JSONB DEFAULT '{{}}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Set up table permissions
        ALTER TABLE {db_schema}.vector_config OWNER TO {admin_role};
        GRANT SELECT ON {db_schema}.vector_config TO {reader_role};
        GRANT SELECT, INSERT, UPDATE, DELETE ON {db_schema}.vector_config TO {writer_role}, {admin_role};
        
        -- Create timestamp trigger
        CREATE OR REPLACE FUNCTION {db_schema}.vector_config_update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Create trigger for timestamps
        DROP TRIGGER IF EXISTS vector_config_timestamp_trigger ON {db_schema}.vector_config;
        CREATE TRIGGER vector_config_timestamp_trigger
        BEFORE UPDATE ON {db_schema}.vector_config
        FOR EACH ROW
        EXECUTE FUNCTION {db_schema}.vector_config_update_timestamp();
        
        -- Insert default configuration for documents
        INSERT INTO {db_schema}.vector_config 
            (entity_type, dimensions, content_fields, index_type, index_options)
        VALUES 
            ('documents', 1536, ARRAY['title', 'content'], 'hnsw', '{{"m": 16, "ef_construction": 64}}')
        ON CONFLICT (entity_type) DO NOTHING;
        """
        
        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_vector_config_table",
                type=SQLStatementType.TABLE,
                sql=create_vector_config_table_sql,
            )
        )
        
        return statements


class VectorSearchEmitter(SQLEmitter):
    """
    Emitter for vector search operations.
    
    This emitter provides methods for executing vector similarity search,
    hybrid vector-graph search, and embedding generation.
    """
    
    def __init__(
        self,
        table_name: str,
        column_name: str = "embedding",
        schema: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize vector search emitter.
        
        Args:
            table_name: The database table name containing embeddings
            column_name: The column name containing embeddings (default: "embedding")
            schema: Optional database schema name (defaults to settings.DB_SCHEMA)
            **kwargs: Additional arguments to pass to SQLEmitter
        """
        super().__init__(**kwargs)
        self.table_name = table_name
        self.column_name = column_name
        
        # Get schema safely
        if schema:
            self._schema = schema
        elif hasattr(self.config, "DB_SCHEMA"):
            self._schema = self.config.DB_SCHEMA
        else:
            from uno.settings import uno_settings
            self._schema = uno_settings.DB_SCHEMA
    
    def search_sql(
        self,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.7,
        metric: str = "cosine",
        where_clause: Optional[str] = None
    ) -> str:
        """
        Generate SQL for vector similarity search.
        
        Args:
            query_text: The text to search for
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
            metric: Distance metric to use (cosine, l2, dot)
            where_clause: Optional WHERE clause for filtering
            
        Returns:
            SQL query for the search operation
        """
        # Get schema
        schema = self._schema
        
        # Determine operator based on metric
        op = "<->" if metric == "l2" else "<#>" if metric == "dot" else "<=>"
        
        # Build the where clause
        where_conditions = []
        if threshold > 0:
            # Convert threshold to distance based on metric
            if metric == "cosine":
                where_conditions.append(f"(1 - ({self.column_name} {op} {schema}.generate_embedding(:query_text))) >= :threshold")
            elif metric == "l2":
                where_conditions.append(f"({self.column_name} {op} {schema}.generate_embedding(:query_text)) <= :threshold")
            elif metric == "dot":
                where_conditions.append(f"({self.column_name} {op} {schema}.generate_embedding(:query_text)) >= :threshold")
        
        # Add custom where clause if provided
        if where_clause:
            where_conditions.append(where_clause)
        
        # Build the complete where clause
        where_part = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        # Build similarity expression based on metric
        if metric == "cosine":
            similarity_expr = f"(1 - ({self.column_name} {op} {schema}.generate_embedding(:query_text))) AS similarity"
        elif metric == "l2":
            similarity_expr = f"1.0 / (1.0 + ({self.column_name} {op} {schema}.generate_embedding(:query_text))) AS similarity"
        elif metric == "dot":
            similarity_expr = f"({self.column_name} {op} {schema}.generate_embedding(:query_text)) AS similarity"
        else:
            similarity_expr = f"(1 - ({self.column_name} {op} {schema}.generate_embedding(:query_text))) AS similarity"
        
        # Build the order by clause
        if metric == "cosine" or metric == "dot":
            order_by = f"ORDER BY {self.column_name} {op} {schema}.generate_embedding(:query_text) DESC"
        else:
            order_by = f"ORDER BY {self.column_name} {op} {schema}.generate_embedding(:query_text) ASC"
        
        sql = f"""
        SELECT 
            id::TEXT, 
            {similarity_expr},
            row_to_json({schema}.{self.table_name}.*)::JSONB AS row_data
        FROM {schema}.{self.table_name}
        {where_part}
        {order_by}
        LIMIT :limit
        """
        
        return sql
    
    def hybrid_search_sql(
        self,
        query_text: str,
        graph_query: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> str:
        """
        Generate SQL for hybrid vector-graph search.
        
        Args:
            query_text: The text to search for
            graph_query: Optional graph query for hybrid search
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            SQL query for the hybrid search operation
        """
        # Get schema
        schema = self._schema
        
        # Determine if we have a graph query
        has_graph = graph_query is not None and graph_query.strip() != ""
        
        # Basic vector search CTE (common table expression)
        vector_cte = f"""
        vector_results AS (
            SELECT 
                id::TEXT, 
                (1 - ({self.column_name} <=> {schema}.generate_embedding(:query_text))) AS similarity,
                row_to_json({schema}.{self.table_name}.*)::JSONB AS row_data
            FROM {schema}.{self.table_name}
            WHERE (1 - ({self.column_name} <=> {schema}.generate_embedding(:query_text))) >= :threshold
        )
        """
        
        if has_graph:
            # Full hybrid search
            sql = f"""
            WITH
            graph_results AS (
                {graph_query}
            ),
            {vector_cte}
            SELECT 
                v.id,
                v.similarity,
                v.row_data,
                COALESCE(g.distance, 999999) AS graph_distance
            FROM 
                vector_results v
            LEFT JOIN 
                graph_results g ON v.id = g.id
            ORDER BY 
                -- Prefer items with both graph connection and vector similarity
                CASE WHEN g.id IS NOT NULL THEN 0 ELSE 1 END,
                -- Then by graph distance (if available)
                COALESCE(g.distance, 999999),
                -- Then by vector similarity
                v.similarity DESC
            LIMIT :limit
            """
        else:
            # Plain vector search with graph compatible output
            sql = f"""
            WITH
            {vector_cte}
            SELECT 
                id::TEXT, 
                similarity,
                row_data,
                999999 AS graph_distance
            FROM vector_results
            ORDER BY similarity DESC
            LIMIT :limit
            """
        
        return sql
    
    def generate_embedding_sql(self, text: str) -> str:
        """
        Generate SQL for embedding text.
        
        Args:
            text: The text to embed
            
        Returns:
            SQL query for generating an embedding
        """
        schema = self._schema
        return f"SELECT {schema}.generate_embedding(:text) AS embedding"
    
    async def execute_search(
        self,
        connection: ConnectionType,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.7,
        metric: str = "cosine",
        where_clause: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a vector similarity search.
        
        Args:
            connection: Database connection
            query_text: The text to search for
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
            metric: Distance metric to use (cosine, l2, dot)
            where_clause: Optional WHERE clause for filtering
            
        Returns:
            List of search results
        """
        sql = self.search_sql(
            query_text=query_text,
            limit=limit,
            threshold=threshold,
            metric=metric,
            where_clause=where_clause
        )
        
        params = {
            "query_text": query_text,
            "limit": limit,
            "threshold": threshold
        }
        
        result = await connection.execute(sql_text(sql), params)
        rows = result.fetchall()
        
        # Convert rows to result dictionaries
        search_results = []
        for row in rows:
            if hasattr(row, "_mapping"):
                search_results.append(dict(row._mapping))
            else:
                # Fall back for compatibility
                search_results.append({
                    "id": row[0],
                    "similarity": row[1],
                    "row_data": row[2]
                })
                
        return search_results
    
    async def execute_hybrid_search(
        self,
        connection: ConnectionType,
        query_text: str,
        graph_query: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Execute a hybrid vector-graph search.
        
        Args:
            connection: Database connection
            query_text: The text to search for
            graph_query: Optional graph query for hybrid search
            limit: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of search results
        """
        sql = self.hybrid_search_sql(
            query_text=query_text,
            graph_query=graph_query,
            limit=limit,
            threshold=threshold
        )
        
        params = {
            "query_text": query_text,
            "limit": limit,
            "threshold": threshold
        }
        
        result = await connection.execute(sql_text(sql), params)
        rows = result.fetchall()
        
        # Convert rows to result dictionaries
        search_results = []
        for row in rows:
            if hasattr(row, "_mapping"):
                search_results.append(dict(row._mapping))
            else:
                # Fall back for compatibility
                search_results.append({
                    "id": row[0],
                    "similarity": row[1],
                    "row_data": row[2],
                    "graph_distance": row[3]
                })
                
        return search_results
    
    async def execute_generate_embedding(
        self,
        connection: ConnectionType,
        text: str
    ) -> List[float]:
        """
        Generate an embedding vector for text.
        
        Args:
            connection: Database connection
            text: The text to embed
            
        Returns:
            Embedding vector as a list of floats
        """
        sql = self.generate_embedding_sql(text)
        
        result = await connection.execute(sql_text(sql), {"text": text})
        row = result.fetchone()
        
        if row and row.embedding:
            # Convert from postgres vector type to list of floats
            embedding_str = row.embedding.replace('[', '').replace(']', '')
            return [float(val) for val in embedding_str.split(',')]
        
        return []


class VectorBatchEmitter(SQLEmitter):
    """
    Emitter for batch vector operations.
    
    This emitter provides methods for batch vector operations such as
    updating embeddings for multiple entities at once.
    """
    
    def __init__(
        self,
        entity_type: str,
        content_fields: List[str],
        schema: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize vector batch emitter.
        
        Args:
            entity_type: Type of entities to process
            content_fields: Fields containing content to embed
            schema: Optional database schema name (defaults to settings.DB_SCHEMA)
            **kwargs: Additional arguments to pass to SQLEmitter
        """
        super().__init__(**kwargs)
        self.entity_type = entity_type
        self.table_name = entity_type.lower()
        self.content_fields = content_fields
        
        # Get schema safely
        if schema:
            self._schema = schema
        elif hasattr(self.config, "DB_SCHEMA"):
            self._schema = self.config.DB_SCHEMA
        else:
            from uno.settings import uno_settings
            self._schema = uno_settings.DB_SCHEMA
    
    def get_entity_count_sql(self) -> str:
        """
        Generate SQL to count entities.
        
        Returns:
            SQL query to count entities
        """
        schema = self._schema
        return f"SELECT COUNT(*) FROM {schema}.{self.table_name}"
    
    def get_batch_sql(self, limit: int, offset: int) -> str:
        """
        Generate SQL to get a batch of entities.
        
        Args:
            limit: Maximum number of entities to retrieve
            offset: Number of entities to skip
            
        Returns:
            SQL query to get a batch of entities
        """
        schema = self._schema
        select_fields = ["id"] + self.content_fields
        fields_str = ", ".join(select_fields)
        
        return f"""
        SELECT {fields_str}
        FROM {schema}.{self.table_name}
        ORDER BY id
        LIMIT :limit OFFSET :offset
        """
    
    def get_entities_by_ids_sql(self, entity_ids: List[str]) -> str:
        """
        Generate SQL to get entities by IDs.
        
        Args:
            entity_ids: List of entity IDs to retrieve
            
        Returns:
            SQL query to get entities by IDs
        """
        schema = self._schema
        select_fields = ["id"] + self.content_fields
        fields_str = ", ".join(select_fields)
        
        return f"""
        SELECT {fields_str}
        FROM {schema}.{self.table_name}
        WHERE id IN :ids
        """
    
    async def execute_get_count(self, connection: ConnectionType) -> int:
        """
        Execute a query to count entities.
        
        Args:
            connection: Database connection
            
        Returns:
            Entity count
        """
        sql = self.get_entity_count_sql()
        result = await connection.execute(sql_text(sql))
        return result.scalar() or 0
    
    async def execute_get_batch(
        self,
        connection: ConnectionType,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """
        Execute a query to get a batch of entities.
        
        Args:
            connection: Database connection
            limit: Maximum number of entities to retrieve
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        sql = self.get_batch_sql(limit, offset)
        result = await connection.execute(
            sql_text(sql),
            {"limit": limit, "offset": offset}
        )
        
        rows = result.fetchall()
        entities = []
        
        for row in rows:
            if hasattr(row, "_mapping"):
                entities.append(dict(row._mapping))
            else:
                # Fall back for compatibility
                entity = {"id": row[0]}
                for i, field in enumerate(self.content_fields, 1):
                    if i < len(row):
                        entity[field] = row[i]
                entities.append(entity)
        
        return entities
    
    async def execute_get_entities_by_ids(
        self,
        connection: ConnectionType,
        entity_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute a query to get entities by IDs.
        
        Args:
            connection: Database connection
            entity_ids: List of entity IDs to retrieve
            
        Returns:
            List of entities
        """
        if not entity_ids:
            return []
            
        sql = self.get_entities_by_ids_sql(entity_ids)
        result = await connection.execute(
            sql_text(sql),
            {"ids": tuple(entity_ids)}
        )
        
        rows = result.fetchall()
        entities = []
        
        for row in rows:
            if hasattr(row, "_mapping"):
                entities.append(dict(row._mapping))
            else:
                # Fall back for compatibility
                entity = {"id": row[0]}
                for i, field in enumerate(self.content_fields, 1):
                    if i < len(row):
                        entity[field] = row[i]
                entities.append(entity)
        
        return entities