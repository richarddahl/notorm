"""
SQL emitters for vector search functionality.

This module contains SQL emitters for creating vector columns, indexes, and related functions.
"""

import logging
from typing import List, Optional, Dict, Any

from uno.sql.emitter import SQLEmitter
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
        
        # Get config values
        db_schema = self.config.DB_SCHEMA
        db_name = self.config.DB_NAME
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
        
        # Get config values
        db_schema = self.config.DB_SCHEMA
        db_name = self.config.DB_NAME
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
        
        # Get config values
        db_schema = self.config.DB_SCHEMA
        db_name = self.config.DB_NAME
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