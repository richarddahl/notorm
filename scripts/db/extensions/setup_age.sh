#!/bin/bash
set -e

# This script sets up Apache AGE extension for PostgreSQL
# It should be run from the project root

# Source common functions
source scripts/common/functions.sh

echo_info "Setting up Apache AGE extension..."

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Get container ID of the PostgreSQL container
PG_CONTAINER=$(docker ps --filter name=pg16_uno -q)

if [ -z "$PG_CONTAINER" ]; then
    echo_error "PostgreSQL container not found. Make sure it is running."
    exit 1
fi

# Check if AGE extension is already installed
echo_info "Checking if AGE extension is already installed..."
AGE_INSTALLED=$(docker exec -it "$PG_CONTAINER" psql -U postgres -d postgres -t -c "SELECT count(*) FROM pg_extension WHERE extname = 'age';")

if [ "$AGE_INSTALLED" -gt 0 ]; then
    echo_success "Apache AGE extension is already installed."
else
    echo_info "Installing Apache AGE extension..."
    
    # Install AGE extension
    docker exec -it "$PG_CONTAINER" psql -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS age;"
    
    if [ $? -eq 0 ]; then
        echo_success "Apache AGE extension installed successfully."
    else
        echo_error "Failed to install Apache AGE extension."
        exit 1
    fi
fi

# Create test graph if it doesn't exist already
echo_info "Creating test graph..."
docker exec -it "$PG_CONTAINER" psql -U postgres -d postgres -c "LOAD 'age'; SELECT * FROM ag_catalog.create_graph('graph');"

if [ $? -eq 0 ]; then
    echo_success "Test graph created or already exists."
else
    echo_warning "Could not create test graph. This is normal if it already exists."
fi

# Set up AGE schema objects
echo_info "Setting up AGE schema objects..."
docker exec -it "$PG_CONTAINER" psql -U postgres -d postgres -c "
    LOAD 'age';
    SET search_path = ag_catalog, '$user', public;
    
    -- Create helper function for graph traversal if it doesn't exist
    CREATE OR REPLACE FUNCTION graph_traverse(
        start_label TEXT, 
        start_filters JSONB, 
        path_pattern TEXT
    ) RETURNS TABLE (id TEXT, distance INTEGER) AS \$\$
    DECLARE
        cypher_query TEXT;
    BEGIN
        cypher_query := 'MATCH path = (start:' || start_label || ')-' || path_pattern || 
                      'WHERE ';
        
        -- Add filters for the start node
        FOR key_value IN SELECT * FROM jsonb_each(start_filters)
        LOOP
            cypher_query := cypher_query || 'start.' || key_value.key || 
                          ' = ''' || key_value.value::TEXT || ''' AND ';
        END LOOP;
        
        -- Remove trailing 'AND' if filters were added
        IF start_filters != '{}'::JSONB THEN
            cypher_query := substring(cypher_query, 1, length(cypher_query) - 5);
        ELSE
            -- Remove 'WHERE' if no filters
            cypher_query := substring(cypher_query, 1, length(cypher_query) - 6);
        END IF;
        
        cypher_query := cypher_query || 
                      'RETURN end.id AS id, length(path) AS distance';
                      
        -- Execute Cypher query
        RETURN QUERY
        SELECT 
            (row->>'id')::TEXT,
            (row->>'distance')::INTEGER
        FROM
            cypher('graph', cypher_query, {}, true) AS (row agtype);
    END;
    \$\$ LANGUAGE plpgsql;
    
    -- Grant permissions to public
    GRANT EXECUTE ON FUNCTION graph_traverse TO PUBLIC;
"

if [ $? -eq 0 ]; then
    echo_success "AGE schema objects set up successfully."
else
    echo_error "Failed to set up AGE schema objects."
    exit 1
fi

echo_success "Apache AGE extension setup complete!"