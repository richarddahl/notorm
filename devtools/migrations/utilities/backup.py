"""Backup utilities for database and code migrations.

This module provides tools for creating backups of databases
and code before applying migrations.
"""

from typing import Dict, List, Optional, Union, Any
import os
import shutil
import tempfile
import datetime
import logging
import subprocess
from pathlib import Path
import json
import gzip

logger = logging.getLogger(__name__)


def backup_file(
    file_path: Union[str, Path],
    backup_dir: Optional[Union[str, Path]] = None,
    backup_suffix: str = ".bak",
    timestamp: bool = True,
) -> Path:
    """Create a backup of a single file.

    Args:
        file_path: Path to the file to back up
        backup_dir: Directory to store the backup (default: same as file)
        backup_suffix: Suffix to add to the backup file
        timestamp: Whether to include a timestamp in the backup filename

    Returns:
        Path to the backup file
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine backup directory
    if backup_dir:
        backup_dir = Path(backup_dir)
        os.makedirs(backup_dir, exist_ok=True)
    else:
        backup_dir = file_path.parent

    # Generate backup filename with optional timestamp
    filename = file_path.name
    timestamp_str = ""

    if timestamp:
        timestamp_str = f".{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    backup_filename = f"{filename}{timestamp_str}{backup_suffix}"
    backup_path = backup_dir / backup_filename

    # Copy the file
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup of {file_path} at {backup_path}")

    return backup_path


def backup_directory(
    directory: Union[str, Path],
    backup_dir: Optional[Union[str, Path]] = None,
    exclude_patterns: list[str] | None = None,
    compress: bool = False,
) -> Path:
    """Create a backup of a directory.

    Args:
        directory: Path to the directory to back up
        backup_dir: Directory to store the backup (default: parent of directory)
        exclude_patterns: Patterns of files to exclude
        compress: Whether to compress the backup

    Returns:
        Path to the backup archive
    """
    directory = Path(directory)

    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # Determine backup directory
    if backup_dir:
        backup_dir = Path(backup_dir)
        os.makedirs(backup_dir, exist_ok=True)
    else:
        backup_dir = directory.parent

    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_name = f"{directory.name}_backup_{timestamp}"

    # Create a temporary directory for copying files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / backup_name
        temp_path.mkdir()

        # Copy files, excluding patterns
        exclude_patterns = exclude_patterns or [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            ".DS_Store",
        ]

        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    d == pat or d.endswith(pat.rstrip("*"))
                    for pat in exclude_patterns
                    if not pat.startswith("*")
                )
            ]

            # Create corresponding directories in the temp path
            rel_path = Path(root).relative_to(directory)
            (temp_path / rel_path).mkdir(exist_ok=True)

            # Copy files, excluding patterns
            for file in files:
                if not any(
                    file == pat
                    or (pat.startswith("*") and file.endswith(pat[1:]))
                    or (pat.endswith("*") and file.startswith(pat[:-1]))
                    for pat in exclude_patterns
                ):
                    src_file = Path(root) / file
                    dst_file = temp_path / rel_path / file
                    shutil.copy2(src_file, dst_file)

        # Create the backup archive
        if compress:
            backup_path = backup_dir / f"{backup_name}.tar.gz"
            shutil.make_archive(
                str(backup_path).rstrip(".gz"), "gztar", temp_dir, backup_name
            )
        else:
            backup_path = backup_dir / f"{backup_name}.tar"
            shutil.make_archive(
                str(backup_path).rstrip(".tar"), "tar", temp_dir, backup_name
            )

    logger.info(f"Created backup of {directory} at {backup_path}")
    return backup_path


def backup_database(
    connection_string: str,
    output_file: Union[str, Path],
    compress: bool = True,
    pg_dump_path: str | None = None,
    schema: str | None = None,
    tables: list[str] | None = None,
) -> Path:
    """Create a backup of a PostgreSQL database.

    Args:
        connection_string: Database connection string or URL
        output_file: Path to the output file
        compress: Whether to compress the backup
        pg_dump_path: Path to the pg_dump executable
        schema: Schema to back up (default: public)
        tables: List of tables to back up (default: all)

    Returns:
        Path to the backup file
    """
    output_file = Path(output_file)

    # Ensure the output directory exists
    os.makedirs(output_file.parent, exist_ok=True)

    # Find pg_dump executable
    if not pg_dump_path:
        pg_dump_path = "pg_dump"

    # Build pg_dump command
    cmd = [pg_dump_path, "--format=custom"]

    # Add connection string
    if "://" in connection_string:
        # Extract database name from URL
        from urllib.parse import urlparse

        parsed_url = urlparse(connection_string)
        db_name = parsed_url.path.lstrip("/")

        # Use connection string directly
        cmd.extend(["--dbname", connection_string])
    else:
        # Treat as a database name
        cmd.extend(["--dbname", connection_string])

    # Add schema if specified
    if schema:
        cmd.extend(["--schema", schema])

    # Add tables if specified
    if tables:
        for table in tables:
            cmd.extend(["--table", table])

    # Run the command
    if compress:
        # Use gzip compression
        with gzip.open(str(output_file) + ".gz", "wb") as f:
            process = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
            )
            f.write(process.stdout)
        backup_path = Path(str(output_file) + ".gz")
    else:
        # Write directly to file
        with open(output_file, "wb") as f:
            process = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
        backup_path = output_file

    logger.info(f"Created database backup at {backup_path}")
    return backup_path


def save_migration_metadata(
    backup_path: Union[str, Path], metadata: dict[str, Any]
) -> Path:
    """Save metadata about a backup for future reference.

    Args:
        backup_path: Path to the backup file
        metadata: Dictionary of metadata to save

    Returns:
        Path to the metadata file
    """
    backup_path = Path(backup_path)
    metadata_path = backup_path.with_suffix(backup_path.suffix + ".meta.json")

    # Add timestamp if not present
    if "timestamp" not in metadata:
        metadata["timestamp"] = datetime.datetime.now().isoformat()

    # Add backup file info
    metadata["backup_file"] = {
        "path": str(backup_path),
        "size": backup_path.stat().st_size,
        "created": datetime.datetime.fromtimestamp(
            backup_path.stat().st_ctime
        ).isoformat(),
    }

    # Write metadata to file
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved backup metadata to {metadata_path}")
    return metadata_path


def backup_before_migration(
    files_or_dirs: list[Union[str, Path]],
    output_dir: Union[str, Path],
    metadata: dict[str, Any] | None = None,
    compress: bool = True,
) -> dict[str, Path]:
    """Create backups of files or directories before migration.

    Args:
        files_or_dirs: List of files or directories to back up
        output_dir: Directory to store the backups
        metadata: Additional metadata to save with the backups
        compress: Whether to compress the backups

    Returns:
        Dictionary mapping input paths to backup paths
    """
    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Initialize metadata
    metadata = metadata or {}
    metadata["migration_info"] = {
        "started_at": datetime.datetime.now().isoformat(),
        "backup_count": len(files_or_dirs),
    }

    # Create backups
    backups = {}

    for path_str in files_or_dirs:
        path = Path(path_str)

        if not path.exists():
            logger.warning(f"Path not found, skipping backup: {path}")
            continue

        try:
            if path.is_file():
                backup_path = backup_file(path, output_dir, timestamp=True)
            elif path.is_dir():
                backup_path = backup_directory(path, output_dir, compress=compress)
            else:
                logger.warning(f"Unsupported path type, skipping backup: {path}")
                continue

            backups[str(path)] = backup_path

        except Exception as e:
            logger.error(f"Error backing up {path}: {e}")

    # Save metadata
    metadata["backups"] = {
        str(path): {
            "original_path": str(path),
            "backup_path": str(backup_path),
            "is_directory": Path(path).is_dir(),
        }
        for path, backup_path in backups.items()
    }

    metadata_path = (
        output_dir
        / f"migration_backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.meta.json"
    )
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Created {len(backups)} backups in {output_dir}")
    return backups
