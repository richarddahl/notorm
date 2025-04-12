#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: setup.sh
# Description: Set up Docker test environment for Uno
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./setup.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -c, --clean      Remove existing PostgreSQL test data volumes before starting
#   -p, --port PORT  PostgreSQL port to use (default: 5433)
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../../common/functions.sh"

# Default values
verbose=false
clean_data=false
pg_port=5433
container_name="pg16_uno_test"
compose_file="${PROJECT_ROOT}/docker/test/docker-compose.yaml"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Set up Docker test environment for Uno" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -c, --clean      Remove existing PostgreSQL test data volumes before starting
  -p, --port PORT  PostgreSQL port to use (default: 5433)"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -c|--clean)
            clean_data=true
            shift
            ;;
        -p|--port)
            pg_port="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Main script logic
log_section "Setting up Test Environment with Docker"

# Check if Docker is running
if ! docker_is_running; then
    exit 1
fi

# Create test environment .env file if it doesn't exist
env_file="${PROJECT_ROOT}/.env_test"
if [ ! -f "$env_file" ]; then
    log_info "Creating test environment configuration..."
    cat > "$env_file" << EOL
# GENERAL SETTINGS
SITE_NAME="Uno Test"
LOCALE="en_US"
ENV="test"
API_VERSION="v1.0"
DEBUG=True

# DATABASE SETTINGS
DB_HOST="localhost"
DB_PORT="${pg_port}"  # Different port than dev to allow both to run simultaneously
DB_SCHEMA="uno"
DB_NAME="uno_test"
DB_USER="postgres"
DB_USER_PW="postgreSQLR0ck%"
DB_SYNC_DRIVER="postgresql+psycopg"
DB_ASYNC_DRIVER="postgresql+asyncpg"

# DATABASE QUERY SETTINGS
DEFAULT_LIMIT=100
DEFAULT_OFFSET=0
DEFAULT_PAGE_SIZE=25

# SECURITY SETTINGS
TOKEN_EXPIRE_MINUTES=15
TOKEN_REFRESH_MINUTES=30
TOKEN_ALGORITHM="HS384"
TOKEN_SECRET="TEST_SECRET_KEY"
LOGIN_URL="/api/auth/login"
FORCE_RLS=True

# VECTOR SEARCH SETTINGS
VECTOR_DIMENSIONS=1536
VECTOR_INDEX_TYPE=hnsw
VECTOR_BATCH_SIZE=10
VECTOR_UPDATE_INTERVAL=1.0
VECTOR_AUTO_START=true
EOL
    log_success "Created .env_test configuration file"
fi

# Create test docker-compose file
test_dir="${PROJECT_ROOT}/docker/test"
mkdir -p "$test_dir"

if [ -f "$compose_file" ]; then
    log_info "Test Docker Compose file already exists"
else
    log_info "Creating test Docker Compose file..."
    cat > "$compose_file" << EOL
services:
  db_test:
    container_name: "${container_name}"
    build:
      context: ..
      dockerfile: Dockerfile
    restart: always
    environment:
      POSTGRES_PASSWORD: "postgreSQLR0ck%"
      # No PGDATA environment variable here - let PostgreSQL use default
    volumes:
      - pg_test_data:/var/lib/postgresql/data
    ports:
      - "${pg_port}:5432"  # Use a different port for testing
    user: postgres  # Explicitly set the user to postgres

volumes:
  pg_test_data:
    driver: local
EOL
    log_success "Created test Docker Compose file"
fi

# Handle clearing data if requested
if $clean_data; then
    log_info "Clearing test PostgreSQL data volumes..."
    cd "$test_dir"
    docker-compose down -v
    log_success "Test data cleared."
elif confirm "Do you want to clear existing test PostgreSQL data?" "n"; then
    log_info "Clearing test PostgreSQL data volumes..."
    cd "$test_dir"
    docker-compose down -v
    log_success "Test data cleared."
fi

# Start the test container
log_info "Starting test PostgreSQL container"
cd "$test_dir"
docker-compose down 2>/dev/null || true

# Build and start the test container
log_info "Building Docker test image..."
docker-compose build
log_info "Starting test container..."
docker-compose up -d

# Wait for PostgreSQL to start properly
log_info "Waiting for PostgreSQL to be ready..."
if ! docker_wait_for_postgres "$container_name" 15; then
    exit 1
fi

# Create the test database
log_info "Creating test database..."
docker exec "$container_name" psql -U postgres -c "DROP DATABASE IF EXISTS uno_test;"
docker exec "$container_name" psql -U postgres -c "CREATE DATABASE uno_test;"
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE SCHEMA IF NOT EXISTS uno;"

# Enable extensions in the database
log_info "Enabling PostgreSQL extensions..."
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS hstore;"
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS age;"
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS pgjwt;"
docker exec "$container_name" psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS supa_audit CASCADE;"

# Set up age graph
log_info "Setting up Age graph..."
docker exec "$container_name" psql -U postgres -d uno_test -c "SELECT * FROM ag_catalog.create_graph('graph');"

log_section "Test Environment Setup Complete"
log_success "Test database is now set up and ready for testing!"
log_info "You can run tests with: hatch run test:test"
log_info "For more information about the Docker setup, see docs/docker_setup.md"

exit 0