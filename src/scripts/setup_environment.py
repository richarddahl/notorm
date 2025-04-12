"""
Environment setup utilities for the uno framework.

This module provides tools for:
- Setting up development and test environments
- Creating and initializing databases
- Installing and configuring Docker containers
- Managing PostgreSQL extensions
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple

# Import Docker utilities
from src.scripts.docker_utils import (
    run_command, 
    ensure_docker_running, 
    wait_for_postgres, 
    DockerUtilsError
)


def get_project_root() -> Path:
    """
    Get the absolute path to the project root.
    
    Returns:
        Path to project root directory
    """
    # Assuming this script is in src/scripts
    return Path(__file__).resolve().parent.parent.parent


def create_env_dev_file(overwrite: bool = False) -> Path:
    """
    Create a development environment configuration file.
    
    Args:
        overwrite: Whether to overwrite an existing file
        
    Returns:
        Path to the created file
        
    Raises:
        DockerUtilsError: If file exists and overwrite is False
    """
    project_root = get_project_root()
    env_file = project_root / ".env_dev"
    
    if env_file.exists() and not overwrite:
        print(f"Development environment file already exists: {env_file}")
        return env_file
    
    env_content = """# GENERAL SETTINGS
SITE_NAME="Uno Development"
LOCALE="en_US"
ENV="dev"
API_VERSION="v1.0"
DEBUG=True

# DATABASE SETTINGS
DB_HOST="localhost"
DB_PORT="5432"
DB_SCHEMA="uno"
DB_NAME="uno_dev"
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
TOKEN_SECRET="DEVELOPMENT_SECRET_KEY"
LOGIN_URL="/api/auth/login"
FORCE_RLS=True

# VECTOR SEARCH SETTINGS
VECTOR_DIMENSIONS=1536
VECTOR_INDEX_TYPE=hnsw
VECTOR_BATCH_SIZE=10
VECTOR_UPDATE_INTERVAL=1.0
VECTOR_AUTO_START=true
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"Created development environment file: {env_file}")
        return env_file
    except Exception as e:
        raise DockerUtilsError(f"Failed to create development environment file: {e}")


def setup_database(
    container_name: str, 
    db_name: str,
    schema_name: str = "uno"
) -> bool:
    """
    Create and initialize a database with required extensions.
    
    Args:
        container_name: Name of the Docker container
        db_name: Name of the database to create
        schema_name: Name of the schema to create
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create database
        run_command(
            f'docker exec {container_name} psql -U postgres -c "DROP DATABASE IF EXISTS {db_name};"'
        )
        run_command(
            f'docker exec {container_name} psql -U postgres -c "CREATE DATABASE {db_name};"'
        )
        run_command(
            f'docker exec {container_name} psql -U postgres -d {db_name} -c "CREATE SCHEMA IF NOT EXISTS {schema_name};"'
        )
        
        # Enable extensions
        extensions = [
            "btree_gist",
            "hstore",
            "pgcrypto",
            "vector",
            "age",
            "pgjwt",
            "supa_audit CASCADE"
        ]
        
        for ext in extensions:
            run_command(
                f'docker exec {container_name} psql -U postgres -d {db_name} -c '
                f'"CREATE EXTENSION IF NOT EXISTS {ext};"'
            )
        
        # Set up age graph
        run_command(
            f'docker exec {container_name} psql -U postgres -d {db_name} -c '
            f'"SELECT * FROM ag_catalog.create_graph(\'graph\');"'
        )
        
        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False


def setup_development_environment(
    clear_data: bool = False, 
    non_interactive: bool = False,
    rebuild_image: bool = True
) -> bool:
    """
    Set up the Docker environment for development.
    
    Args:
        clear_data: Whether to clear existing PostgreSQL data
        non_interactive: Whether to run in non-interactive mode
        rebuild_image: Whether to rebuild the Docker image
        
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        print("===== Setting up Uno with Docker and Vector Search =====")
        
        # Check if Docker is running
        ensure_docker_running()
        
        # Create configuration files
        create_env_dev_file()
        
        project_root = get_project_root()
        docker_dir = project_root / "docker"
        
        print("\nStep 1: Building and starting Docker container")
        
        # Stop any existing containers
        run_command(f"cd {docker_dir} && docker-compose down 2>/dev/null || true", check=False)
        
        # Handle data clearing
        if not non_interactive and not clear_data:
            try:
                user_input = input("Do you want to clear existing PostgreSQL data? (y/N): ")
                clear_data = user_input.lower() in ('y', 'yes')
            except EOFError:
                # Handle the case where input() can't get user input (non-interactive)
                clear_data = False
                print("Non-interactive mode detected. Keeping existing data.")
        
        if clear_data:
            print("Clearing PostgreSQL data volumes...")
            run_command(f"cd {docker_dir} && docker-compose down -v")
            print("Data cleared.")
        
        # Build if requested
        if rebuild_image:
            print("Building Docker image...")
            run_command(f"cd {docker_dir} && docker-compose build")
        
        # Start the containers
        print("Starting containers...")
        run_command(f"cd {docker_dir} && docker-compose up -d")
        
        # Wait for PostgreSQL to start
        print("\nStep 2: Waiting for PostgreSQL to be ready...")
        time.sleep(5)
        
        if not wait_for_postgres("pg16_uno"):
            return False
        
        # Create and set up database
        print("\nStep 3: Creating database with vector search capabilities...")
        if not setup_database("pg16_uno", "uno_dev", "uno"):
            return False
        
        print("\n===== Setup Complete =====")
        print("Vector search is now set up and ready to use!")
        print("")
        print("To use the database, set:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Database: uno_dev")
        print("  User: postgres")
        print("  Password: postgreSQLR0ck%")
        print("")
        print("To run the application:")
        print("  hatch run dev:main")
        print("")
        print("For more information about the Docker setup, see docs/docker_setup.md")
        
        return True
    except DockerUtilsError as e:
        print(f"\n===== Setup Failed =====")
        print(f"Error: {e}")
        print("\nFor troubleshooting, see docs/docker_setup.md")
        return False
    except Exception as e:
        print(f"\n===== Setup Failed =====")
        print(f"Unexpected error: {e}")
        print("\nFor troubleshooting, see docs/docker_setup.md")
        return False


def main() -> int:
    """
    Main entry point for environment setup utility.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Environment setup utility for uno framework")
    parser.add_argument(
        "--clear-data", 
        action="store_true", 
        help="Clear existing PostgreSQL data"
    )
    parser.add_argument(
        "--no-rebuild", 
        action="store_true", 
        help="Skip rebuilding the Docker image"
    )
    parser.add_argument(
        "--non-interactive", 
        action="store_true", 
        help="Run in non-interactive mode"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "test"],
        default="dev",
        help="Environment to set up (dev or test)"
    )
    
    args = parser.parse_args()
    
    if args.env == "test":
        # Import here to avoid circular imports
        from src.scripts.docker_utils import setup_test_environment
        success = setup_test_environment(
            clear_data=args.clear_data,
            non_interactive=args.non_interactive
        )
    else:
        success = setup_development_environment(
            clear_data=args.clear_data,
            non_interactive=args.non_interactive,
            rebuild_image=not args.no_rebuild
        )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())