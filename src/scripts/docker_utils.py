"""
Docker utility functions for managing container environments.

This module provides utilities for:
- Setting up test and development environments
- Managing container lifecycle
- Initializing databases
- Installing and configuring extensions
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple, Callable


class DockerUtilsError(Exception):
    """Base exception for docker utilities errors."""

    pass


def run_command(
    command: Union[str, list[str]],
    check: bool = True,
    shell: bool = True,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """
    Run a shell command and handle errors.

    Args:
        command: Command to run (string or list of arguments)
        check: Whether to raise an exception on non-zero exit code
        shell: Whether to run the command through the shell
        capture_output: Whether to capture stdout and stderr
        env: Optional environment variables to set

    Returns:
        CompletedProcess instance with command results

    Raises:
        DockerUtilsError: If command fails and check is True
    """
    try:
        current_env = os.environ.copy()
        if env:
            current_env.update(env)

        result = subprocess.run(
            command,
            shell=shell,
            check=False,  # We'll handle this ourselves
            capture_output=capture_output,
            text=True,
            env=current_env,
        )

        if check and result.returncode != 0:
            error_message = (
                f"Command failed with exit code {result.returncode}:\n{command}"
            )
            if capture_output and result.stderr:
                error_message += f"\nError output:\n{result.stderr}"
            raise DockerUtilsError(error_message)

        return result
    except Exception as e:
        if not isinstance(e, DockerUtilsError):
            raise DockerUtilsError(f"Error running command: {e}")
        raise


def is_docker_running() -> bool:
    """
    Check if Docker is running.

    Returns:
        True if Docker is running, False otherwise
    """
    try:
        result = run_command("docker info", check=False, capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


def ensure_docker_running() -> None:
    """
    Ensure Docker is running or raise an error.

    Raises:
        DockerUtilsError: If Docker is not running
    """
    if not is_docker_running():
        raise DockerUtilsError(
            "Docker is not running. Please start Docker and try again."
        )


def get_project_root() -> Path:
    """
    Get the absolute path to the project root.

    Returns:
        Path to project root directory
    """
    # Assuming this script is in src/scripts
    return Path(__file__).resolve().parent.parent.parent


def create_test_env_file(overwrite: bool = False) -> Path:
    """
    Create a test environment configuration file.

    Args:
        overwrite: Whether to overwrite an existing file

    Returns:
        Path to the created file

    Raises:
        DockerUtilsError: If file exists and overwrite is False
    """
    project_root = get_project_root()
    env_file = project_root / ".env_test"

    if env_file.exists() and not overwrite:
        print(f"Test environment file already exists: {env_file}")
        return env_file

    env_content = """# GENERAL SETTINGS
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
"""

    try:
        with open(env_file, "w") as f:
            f.write(env_content)
        print(f"Created test environment file: {env_file}")
        return env_file
    except Exception as e:
        raise DockerUtilsError(f"Failed to create test environment file: {e}")


def create_test_compose_file(overwrite: bool = False) -> Path:
    """
    Create a docker-compose file for testing.

    Args:
        overwrite: Whether to overwrite an existing file

    Returns:
        Path to the created file

    Raises:
        DockerUtilsError: If file exists and overwrite is False
    """
    project_root = get_project_root()
    docker_test_dir = project_root / "docker" / "test"
    docker_test_dir.mkdir(parents=True, exist_ok=True)

    compose_file = docker_test_dir / "docker-compose.yaml"

    if compose_file.exists() and not overwrite:
        print(f"Test docker-compose file already exists: {compose_file}")
        return compose_file

    compose_content = """services:
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
"""

    try:
        with open(compose_file, "w") as f:
            f.write(compose_content)
        print(f"Created test docker-compose file: {compose_file}")
        return compose_file
    except Exception as e:
        raise DockerUtilsError(f"Failed to create test docker-compose file: {e}")


def wait_for_postgres(
    container_name: str, max_attempts: int = 15, delay: int = 2
) -> bool:
    """
    Wait for PostgreSQL to become ready in a container.

    Args:
        container_name: Name of the Docker container
        max_attempts: Maximum number of connection attempts
        delay: Delay in seconds between attempts

    Returns:
        True if PostgreSQL became ready, False otherwise
    """
    attempt = 1
    while attempt <= max_attempts:
        try:
            result = run_command(
                f"docker exec {container_name} pg_isready -U postgres",
                check=False,
                capture_output=True,
            )
            if result.returncode == 0:
                print(f"PostgreSQL instance in {container_name} is ready!")
                return True
        except Exception:
            pass

        print(
            f"Waiting for PostgreSQL to be ready (attempt {attempt}/{max_attempts})..."
        )
        time.sleep(delay)
        attempt += 1

    print(f"PostgreSQL did not become ready in time. Check Docker logs:")
    run_command(f"docker logs {container_name}")
    return False


def setup_test_database(container_name: str = "pg16_uno_test") -> bool:
    """
    Create and initialize the test database with required extensions.

    Args:
        container_name: Name of the Docker container

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create database
        run_command(
            f'docker exec {container_name} psql -U postgres -c "DROP DATABASE IF EXISTS uno_test;"'
        )
        run_command(
            f'docker exec {container_name} psql -U postgres -c "CREATE DATABASE uno_test;"'
        )
        run_command(
            f'docker exec {container_name} psql -U postgres -d uno_test -c "CREATE SCHEMA IF NOT EXISTS uno;"'
        )

        # Enable extensions
        extensions = [
            "btree_gist",
            "hstore",
            "pgcrypto",
            "vector",
            "age",
            "pgjwt",
            "supa_audit CASCADE",
        ]

        for ext in extensions:
            run_command(
                f"docker exec {container_name} psql -U postgres -d uno_test -c "
                f'"CREATE EXTENSION IF NOT EXISTS {ext};"'
            )

        # Set up age graph
        run_command(
            f"docker exec {container_name} psql -U postgres -d uno_test -c "
            f"\"SELECT * FROM ag_catalog.create_graph('graph');\""
        )

        return True
    except Exception as e:
        print(f"Error setting up test database: {e}")
        return False


def setup_test_environment(
    clear_data: bool = False, non_interactive: bool = False
) -> bool:
    """
    Set up the Docker environment for testing.

    Args:
        clear_data: Whether to clear existing PostgreSQL data
        non_interactive: Whether to run in non-interactive mode

    Returns:
        True if setup was successful, False otherwise
    """
    try:
        print("===== Setting up Test Environment with Docker =====")

        # Check if Docker is running
        ensure_docker_running()

        # Create configuration files
        create_test_env_file()
        compose_file = create_test_compose_file()

        print("\nStep 1: Setting up test Docker environment")

        # Handle data clearing
        if not non_interactive and not clear_data:
            try:
                user_input = input(
                    "Do you want to clear existing test PostgreSQL data? (y/N): "
                )
                clear_data = user_input.lower() in ("y", "yes")
            except EOFError:
                # Handle the case where input() can't get user input (non-interactive)
                clear_data = False
                print("Non-interactive mode detected. Keeping existing test data.")

        if clear_data:
            print("Clearing test PostgreSQL data volumes...")
            run_command(f"cd {compose_file.parent} && docker-compose down -v")
            print("Test data cleared.")

        print("\nStep 2: Starting test PostgreSQL container")

        # Stop any existing containers
        run_command(
            f"cd {compose_file.parent} && docker-compose down 2>/dev/null || true",
            check=False,
        )

        # Build and start the container
        print("Building Docker test image...")
        run_command(f"cd {compose_file.parent} && docker-compose build")

        print("Starting test container...")
        run_command(f"cd {compose_file.parent} && docker-compose up -d")

        # Wait for PostgreSQL to start
        print("\nStep 3: Waiting for PostgreSQL to be ready...")
        time.sleep(5)

        if not wait_for_postgres("pg16_uno_test"):
            return False

        # Create and set up database
        print("\nStep 4: Creating test database...")
        if not setup_test_database("pg16_uno_test"):
            return False

        print("\n===== Test Environment Setup Complete =====")
        print("Test database is now set up and ready for testing!")
        print("\nYou can run tests with:")
        print("  hatch run test:test")
        print("\nFor more information about the Docker setup, see docs/docker_setup.md")

        return True
    except DockerUtilsError as e:
        print(f"\n===== Test Environment Setup Failed =====")
        print(f"Error: {e}")
        print("\nFor troubleshooting, see docs/docker_setup.md")
        return False
    except Exception as e:
        print(f"\n===== Test Environment Setup Failed =====")
        print(f"Unexpected error: {e}")
        print("\nFor troubleshooting, see docs/docker_setup.md")
        return False


def main() -> int:
    """
    Main entry point for Docker utilities command line interface.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Docker utilities for uno framework")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Setup test environment command
    setup_test_parser = subparsers.add_parser(
        "setup-test", help="Set up the test environment"
    )
    setup_test_parser.add_argument(
        "--clear-data", action="store_true", help="Clear existing PostgreSQL data"
    )
    setup_test_parser.add_argument(
        "--non-interactive", action="store_true", help="Run in non-interactive mode"
    )

    # Parse arguments
    args = parser.parse_args()

    if args.command == "setup-test":
        success = setup_test_environment(
            clear_data=args.clear_data, non_interactive=args.non_interactive
        )
        return 0 if success else 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
