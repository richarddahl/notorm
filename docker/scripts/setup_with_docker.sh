#!/bin/bash
# This script sets up the Docker environment and creates the database

set -e  # Exit on error

echo "===== Setting up Uno with Docker and Vector Search ====="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo ""
echo "Step 1: Building and starting Docker container"
cd ..

# First ensure any existing containers are stopped
docker-compose down 2>/dev/null || true

# Check if this is a non-interactive run
if [ -t 0 ]; then
    # Running interactively
    read -p "Do you want to clear existing PostgreSQL data? (y/N): " clear_data
    if [[ $clear_data == "y" || $clear_data == "Y" ]]; then
        echo "Clearing PostgreSQL data volumes..."
        docker-compose down -v
        echo "Data cleared."
    fi
else
    # Non-interactive run
    echo "Non-interactive mode detected. Keeping existing data."
fi

# Build and start the containers
echo "Building Docker image..."
docker-compose build

echo "Starting containers..."
docker-compose up -d

# Wait for PostgreSQL to start properly
echo ""
echo "Step 2: Waiting for PostgreSQL to be ready..."
sleep 5  # Give PostgreSQL some time to initialize

# Check if PostgreSQL is accepting connections
max_attempts=15
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker exec pg16_uno pg_isready -U postgres > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi
    
    echo "Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)..."
    sleep 2
    attempt=$((attempt + 1))
    
    if [ $attempt -gt $max_attempts ]; then
        echo "PostgreSQL did not become ready in time. Check Docker logs:"
        docker logs pg16_uno
        exit 1
    fi
done

echo ""
echo "Step 3: Creating database with vector search capabilities..."
cd ..
echo "Creating database directly in the Docker container..."
docker exec pg16_uno psql -U postgres -c "DROP DATABASE IF EXISTS uno_dev;"
docker exec pg16_uno psql -U postgres -c "CREATE DATABASE uno_dev;"
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE SCHEMA IF NOT EXISTS uno;"

# Enable extensions in the database
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS hstore;"
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS age;"
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS pgjwt;"
docker exec pg16_uno psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS supa_audit CASCADE;"

# Set up age graph
docker exec pg16_uno psql -U postgres -d uno_dev -c "SELECT * FROM ag_catalog.create_graph('graph');"

if [ $? -eq 0 ]; then
    echo ""
    echo "===== Setup Complete ====="
    echo "Vector search is now set up and ready to use!"
    echo ""
    echo "To use the database, set:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: uno_dev"
    echo "  User: postgres"
    echo "  Password: postgreSQLR0ck%"
    echo ""
    echo "To run the application:"
    echo "  hatch run dev:main"
    echo ""
    echo "For more information about the Docker setup, see docs/docker_setup.md"
else
    echo ""
    echo "===== Setup Failed ====="
    echo "Check the error messages above for details."
    echo ""
    echo "For troubleshooting, see docs/docker_setup.md"
    echo ""
fi