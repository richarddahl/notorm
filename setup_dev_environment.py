#!/usr/bin/env python3
"""
Development Environment Setup Script for Uno

This script performs a complete reset and setup of the development environment:
1. Drops the existing dev database and roles if they exist
2. Recreates the database structure with all necessary schemas and extensions
3. Creates all functions, triggers, and tables
4. Runs all SQL emitters to set up database objects
5. Runs Alembic migrations
6. Starts the main application

Usage:
    python setup_dev_environment.py [--no-app]

Options:
    --no-app    Set up the environment but don't start the application
"""

import os
import sys
import time
import argparse
import logging
import subprocess
from pathlib import Path


def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("setup_dev")


def run_command(logger, cmd, description, check=True, env=None):
    """
    Run a shell command and log the output.
    
    Args:
        logger: Logger instance
        cmd: Command to run (list or string)
        description: Description of the command for logging
        check: Whether to check for return code (default: True)
        env: Environment variables to use (default: None)
        
    Returns:
        subprocess.CompletedProcess instance
    """
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
        
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=False,  # Always capture result, even on error
            text=True,
            capture_output=True,
            env=env
        )
        
        if result.stdout.strip():
            logger.debug(f"Output: {result.stdout}")
            
        if result.returncode == 0:
            logger.info(f"Successfully completed: {description}")
        else:
            logger.error(f"Failed: {description}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
            
        # Only raise exception if check is True and return code is not 0
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, 
                                               result.stdout, result.stderr)
            
        return result
    except Exception as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Error: {e}")
        if check:
            raise
        return None


def check_docker(logger):
    """Check if Docker is running and if the PostgreSQL container is available."""
    try:
        run_command(
            logger, 
            "docker ps | grep postgres", 
            "Checking if PostgreSQL Docker container is running",
            check=False
        )
        logger.info("Docker and PostgreSQL container appear to be running")
    except subprocess.CalledProcessError:
        logger.error("PostgreSQL Docker container doesn't seem to be running")
        logger.info("Setting up Docker containers...")
        run_command(
            logger,
            "./setup_with_docker.sh",
            "Setting up Docker containers"
        )
        # Wait for containers to be ready
        logger.info("Waiting for Docker containers to be ready...")
        time.sleep(10)


def recreate_database(logger):
    """Drop and recreate the database using createdb.py."""
    logger.info("Dropping and recreating database...")
    
    # Import in function scope to avoid import errors before environment is ready
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from src.scripts.createdb import init_db_manager
        
        # Drop database (if exists)
        try:
            init_db_manager.drop_db()
            logger.info("Successfully dropped existing database")
        except Exception as e:
            logger.warning(f"Error dropping database (may not exist yet): {e}")
        
        # Create database
        init_db_manager.create_db()
        logger.info("Successfully created database structure")
        
    except ImportError as e:
        logger.error(f"ImportError: {e}")
        logger.error("Falling back to command-line approach")
        run_command(
            logger,
            [sys.executable, "src/scripts/createdb.py"],
            "Recreating database structure"
        )


def run_migrations(logger):
    """Run all Alembic migrations."""
    logger.info("Running database migrations...")
    
    try:
        run_command(
            logger,
            [sys.executable, "src/scripts/migrations.py", "upgrade"],
            "Running Alembic migrations"
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration error: {e}")
        logger.info("Attempting to initialize migrations first...")
        
        # Try initializing migrations first, then upgrade
        run_command(
            logger,
            [sys.executable, "src/scripts/migrations.py", "init"],
            "Initializing migrations",
            check=False
        )
        
        run_command(
            logger,
            [sys.executable, "src/scripts/migrations.py", "upgrade"],
            "Running Alembic migrations again after initialization"
        )


def create_event_store(logger):
    """Create the event store for the application."""
    logger.info("Creating event store...")
    
    try:
        # Run the eventstore.py script which creates the event store schema
        cmd = [sys.executable, "src/scripts/eventstore.py"]
        if logger.level <= logging.DEBUG:
            cmd.append("--verbose")
            
        result = run_command(
            logger,
            cmd,
            "Creating event store",
            check=False  # Don't error out if this fails
        )
        
        # Check if the command was successful by looking for error messages in output
        if result.returncode == 0 and "ERROR" not in result.stderr and "Error" not in result.stdout:
            logger.info("Event store created successfully")
            return True
        else:
            if result.stderr:
                logger.warning(f"Event store creation failed with error: {result.stderr}")
            if "Error" in result.stdout:
                logger.warning(f"Event store error in output: {result.stdout}")
            logger.warning("Continuing without event store - some functionality may be limited")
            return False
    except Exception as e:
        logger.warning(f"Event store creation failed: {e}")
        logger.warning("Continuing without event store - some functionality may be limited")
        return False


def start_application(logger):
    """Start the main application."""
    logger.info("Starting main application...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent)
    
    try:
        # Use exec form to replace the current process with the app
        os.execle(sys.executable, sys.executable, "main.py", env)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Set up development environment for Uno")
    parser.add_argument(
        "--no-app",
        action="store_true",
        help="Set up the environment but don't start the application"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--skip-event-store",
        action="store_true",
        help="Skip event store creation"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Ensure base directory is set correctly
        os.chdir(Path(__file__).parent)
        
        # Check if Docker is running with PostgreSQL
        check_docker(logger)
        
        # Drop and recreate database
        recreate_database(logger)
        
        # Run migrations
        run_migrations(logger)
        
        # Create event store (unless skipped)
        if not args.skip_event_store:
            event_store_success = create_event_store(logger)
            if not event_store_success:
                logger.warning("Event store creation was skipped or failed")
        else:
            logger.info("Skipping event store creation as requested")
        
        # Start application if requested
        if not args.no_app:
            logger.info("All database setup steps completed successfully")
            start_application(logger)
        else:
            logger.info("Environment setup complete. Use 'python main.py' to start the application.")
    
    except Exception as e:
        logger.error(f"Error setting up development environment: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()