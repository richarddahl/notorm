#!/bin/bash
# Script to completely rebuild the Docker container and recreate the database

set -e  # Exit on error

echo "===== REBUILDING DOCKER CONTAINERS ====="

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Ask if the user wants to clear existing data
read -p "Do you want to clear existing PostgreSQL data? (y/N): " clear_data
if [[ $clear_data == "y" || $clear_data == "Y" ]]; then
    echo "Clearing PostgreSQL data..."
    docker-compose down -v  # This removes named volumes
    echo "Data cleared."
fi

# Rebuild the Docker image without cache
echo "Rebuilding Docker image..."
docker-compose build --no-cache

# Start the containers
echo "Starting containers..."
docker-compose up -d

# Wait for PostgreSQL to start
echo "Waiting for PostgreSQL to start..."
sleep 5

echo "===== REBUILD COMPLETE ====="
echo ""
echo "PostgreSQL is now running on localhost:5432"
echo "Username: postgres"
echo "Password: postgreSQLR0ck%"
echo ""
echo "To create the Uno database, run:"
echo "export ENV=dev"
echo "python src/scripts/createdb.py"
echo ""