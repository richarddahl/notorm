#!/bin/bash
set -e

# This script is run when the PostgreSQL container starts up
# It ensures all the required extensions are enabled

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable extensions
    CREATE EXTENSION IF NOT EXISTS btree_gist;
    CREATE EXTENSION IF NOT EXISTS hstore;
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE EXTENSION IF NOT EXISTS pgjwt;
    CREATE EXTENSION IF NOT EXISTS supa_audit CASCADE;
    
    -- Enable vector extension for similarity search
    CREATE EXTENSION IF NOT EXISTS vector;
    
    -- Enable age extension for graph database
    CREATE EXTENSION IF NOT EXISTS age;
    
    -- Set up age graph
    SELECT * FROM ag_catalog.create_graph('graph');
EOSQL

echo "Initialized PostgreSQL with extensions: btree_gist, hstore, pgcrypto, pgjwt, supa_audit, vector, age"