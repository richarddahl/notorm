"""
Docker container rebuild and database reset utilities.

This module provides tools for:
- Completely rebuilding Docker containers
- Resetting PostgreSQL data
- Managing Docker environment for development and testing
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple


class DockerRebuildError(Exception):
    """Base exception for Docker rebuild errors."""

    pass


def run_command(
    command: Union[str, list[str]],
    check: bool = True,
    shell: bool = True,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    """
    Run a shell command and handle errors.

    Args:
        command: Command to run (string or list of arguments)
        check: Whether to raise an exception on non-zero exit code
        shell: Whether to run the command through the shell
        capture_output: Whether to capture stdout and stderr
        env: Optional environment variables to set
        cwd: Optional working directory

    Returns:
        CompletedProcess instance with command results

    Raises:
        DockerRebuildError: If command fails and check is True
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
            cwd=cwd,
        )

        if check and result.returncode != 0:
            error_message = (
                f"Command failed with exit code {result.returncode}:\n{command}"
            )
            if capture_output and result.stderr:
                error_message += f"\nError output:\n{result.stderr}"
            raise DockerRebuildError(error_message)

        return result
    except Exception as e:
        if not isinstance(e, DockerRebuildError):
            raise DockerRebuildError(f"Error running command: {e}")
        raise


def get_project_root() -> Path:
    """
    Get the absolute path to the project root.

    Returns:
        Path to project root directory
    """
    # Assuming this script is in src/scripts
    return Path(__file__).resolve().parent.parent.parent


def get_docker_compose_path(env: str = "dev") -> Path:
    """
    Get the path to the docker-compose.yaml file for the specified environment.

    Args:
        env: Environment name (dev, test)

    Returns:
        Path to docker-compose.yaml
    """
    project_root = get_project_root()

    if env == "test":
        return project_root / "docker" / "test" / "docker-compose.yaml"
    else:
        return project_root / "docker" / "docker-compose.yaml"


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """
    Prompt the user for a yes/no answer.

    Args:
        question: The question to ask
        default: Default value if no input is provided

    Returns:
        True for yes, False for no
    """
    default_prompt = "(Y/n)" if default else "(y/N)"
    try:
        response = input(f"{question} {default_prompt}: ").strip().lower()
        if not response:
            return default
        return response[0] == "y"
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive mode
        print(f"Non-interactive mode, using default: {default}")
        return default


def rebuild_containers(
    env: str = "dev",
    clear_data: Optional[bool] = None,
    no_cache: bool = True,
    non_interactive: bool = False,
) -> bool:
    """
    Rebuild Docker containers and optionally clear data.

    Args:
        env: Environment name (dev, test)
        clear_data: Whether to clear existing PostgreSQL data (None = prompt user)
        no_cache: Whether to use --no-cache when building
        non_interactive: Whether to run in non-interactive mode

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"===== REBUILDING DOCKER CONTAINERS ({env.upper()}) =====")

        # Get docker-compose path
        compose_path = get_docker_compose_path(env)
        if not compose_path.exists():
            raise DockerRebuildError(f"Docker compose file not found: {compose_path}")

        compose_dir = compose_path.parent

        # Stop existing containers
        print("Stopping existing containers...")
        run_command(f"cd {compose_dir} && docker-compose down", check=False)

        # Determine whether to clear data
        should_clear_data = clear_data
        if should_clear_data is None and not non_interactive:
            should_clear_data = prompt_yes_no(
                "Do you want to clear existing PostgreSQL data?", default=False
            )

        if should_clear_data:
            print("Clearing PostgreSQL data...")
            run_command(f"cd {compose_dir} && docker-compose down -v")
            print("Data cleared.")

        # Rebuild the Docker image
        print("Rebuilding Docker image...")
        cache_arg = "--no-cache" if no_cache else ""
        run_command(f"cd {compose_dir} && docker-compose build {cache_arg}")

        # Start the containers
        print("Starting containers...")
        run_command(f"cd {compose_dir} && docker-compose up -d")

        # Wait for PostgreSQL to start
        print("Waiting for PostgreSQL to start...")
        time.sleep(5)

        container_name = "pg16_uno_test" if env == "test" else "pg16_uno"
        port = "5433" if env == "test" else "5432"

        print(f"===== REBUILD COMPLETE ({env.upper()}) =====")
        print("")
        print(f"PostgreSQL is now running on localhost:{port}")
        print("Username: postgres")
        print("Password: postgreSQLR0ck%")
        print("")

        if env == "dev":
            print("To create the Uno database, run:")
            print("export ENV=dev")
            print("python src/scripts/createdb.py")
        else:
            print("Test database has been created")
            print("You can run tests with:")
            print("hatch run test:test")

        print("")

        return True
    except DockerRebuildError as e:
        print(f"\n===== REBUILD FAILED =====")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n===== REBUILD FAILED =====")
        print(f"Unexpected error: {e}")
        return False


def main() -> int:
    """
    Main entry point for Docker container rebuild utility.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Docker container rebuild utility")
    parser.add_argument(
        "--env",
        choices=["dev", "test"],
        default="dev",
        help="Environment (dev or test)",
    )
    parser.add_argument(
        "--clear-data", action="store_true", help="Clear existing PostgreSQL data"
    )
    parser.add_argument(
        "--keep-data", action="store_true", help="Keep existing PostgreSQL data"
    )
    parser.add_argument(
        "--use-cache", action="store_true", help="Use Docker build cache"
    )
    parser.add_argument(
        "--non-interactive", action="store_true", help="Run in non-interactive mode"
    )

    args = parser.parse_args()

    # Handle clear data logic
    clear_data = None  # Default: ask user
    if args.clear_data:
        clear_data = True
    elif args.keep_data:
        clear_data = False

    success = rebuild_containers(
        env=args.env,
        clear_data=clear_data,
        no_cache=not args.use_cache,
        non_interactive=args.non_interactive,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
