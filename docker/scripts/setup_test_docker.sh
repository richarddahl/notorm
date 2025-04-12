#!/bin/bash
# This script sets up the Docker environment for testing

set -e  # Exit on error

echo "===== Setting up Test Environment with Docker ====="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create test environment .env file if it doesn't exist
if [ ! -f "../../.env_test" ]; then
    echo "Creating test environment configuration..."
    cat > ../../.env_test << EOL
# GENERAL SETTINGS
SITE_NAME="Uno Test"
LOCALE="en_US"
ENV="test"
API_VERSION="v1.0"
DEBUG=True

# DATABASE SETTINGS
DB_HOST="localhost"
DB_PORT="5433"  # Different port than dev to allow both to run simultaneously
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
    echo "Created .env_test configuration file"
fi

# Create test docker-compose file
mkdir -p ../test
cat > ../test/docker-compose.yaml << EOL
services:
  db_test:
    container_name: "pg16_uno_test"
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
      - "5433:5432"  # Use a different port for testing
    user: postgres  # Explicitly set the user to postgres

volumes:
  pg_test_data:
    driver: local
EOL

echo ""
echo "Step 1: Setting up test Docker environment"

# Check if this is a non-interactive run
if [ -t 0 ]; then
    # Running interactively
    read -p "Do you want to clear existing test PostgreSQL data? (y/N): " clear_data
    if [[ $clear_data == "y" || $clear_data == "Y" ]]; then
        echo "Clearing test PostgreSQL data volumes..."
        cd ../test
        docker-compose down -v
        cd ../scripts
        echo "Test data cleared."
    fi
else
    # Non-interactive run
    echo "Non-interactive mode detected. Keeping existing test data."
fi

echo ""
echo "Step 2: Starting test PostgreSQL container"
cd ../test
docker-compose down 2>/dev/null || true

# Build and start the test container
echo "Building Docker test image..."
docker-compose build
echo "Starting test container..."
docker-compose up -d

# Wait for PostgreSQL to start properly
echo ""
echo "Step 3: Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is accepting connections
max_attempts=15
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker exec pg16_uno_test pg_isready -U postgres > /dev/null 2>&1; then
        echo "PostgreSQL test instance is ready!"
        break
    fi
    
    echo "Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)..."
    sleep 2
    attempt=$((attempt + 1))
    
    if [ $attempt -gt $max_attempts ]; then
        echo "PostgreSQL did not become ready in time. Check Docker logs:"
        docker logs pg16_uno_test
        exit 1
    fi
done

echo ""
echo "Step 4: Creating test database..."
cd ../../
echo "Creating test database directly in the Docker container..."
docker exec pg16_uno_test psql -U postgres -c "DROP DATABASE IF EXISTS uno_test;"
docker exec pg16_uno_test psql -U postgres -c "CREATE DATABASE uno_test;"
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE SCHEMA IF NOT EXISTS uno;"

# Enable extensions in the database
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS hstore;"
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS age;"
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS pgjwt;"
docker exec pg16_uno_test psql -U postgres -d uno_test -c "CREATE EXTENSION IF NOT EXISTS supa_audit CASCADE;"

# Set up age graph
docker exec pg16_uno_test psql -U postgres -d uno_test -c "SELECT * FROM ag_catalog.create_graph('graph');"

if [ $? -eq 0 ]; then
    echo ""
    echo "===== Test Environment Setup Complete ====="
    echo "Test database is now set up and ready for testing!"
    echo ""
    echo "You can run tests with:"
    echo "  hatch run test:test"
    echo ""
    echo "For more information about the Docker setup, see docs/docker_setup.md"
else
    echo ""
    echo "===== Test Environment Setup Failed ====="
    echo "Check the error messages above for details."
    echo ""
    echo "For troubleshooting, see docs/docker_setup.md"
    echo ""
fi