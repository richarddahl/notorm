"""Restoration utilities for database and code migrations.

This module provides tools for restoring backups of databases
and code after failed migrations.
"""
from typing import Dict, List, Optional, Union, Any
import os
import shutil
import tempfile
import logging
import subprocess
import json
import gzip
import tarfile
from pathlib import Path

logger = logging.getLogger(__name__)

def restore_file(
    backup_path: Union[str, Path],
    target_path: Optional[Union[str, Path]] = None,
    force: bool = False
) -> Path:
    """Restore a file from a backup.
    
    Args:
        backup_path: Path to the backup file
        target_path: Path to restore to (default: derived from backup filename)
        force: Whether to overwrite existing files
        
    Returns:
        Path to the restored file
    """
    backup_path = Path(backup_path)
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
    # Determine target path if not specified
    if not target_path:
        # Try to derive from filename (assumes .bak suffix with optional timestamp)
        filename = backup_path.name
        if filename.endswith(".bak"):
            # Remove .bak suffix
            filename = filename[:-4]
            
            # Remove timestamp if present
            parts = filename.split(".")
            if len(parts) > 1 and parts[-1].isdigit() and len(parts[-1]) >= 8:
                # Timestamp likely found, remove it
                filename = ".".join(parts[:-1])
                
            # Use the derived filename in the same directory as the backup
            target_path = backup_path.parent / filename
        else:
            # Can't determine original filename, use backup with "restored_" prefix
            target_path = backup_path.parent / f"restored_{backup_path.name}"
    else:
        target_path = Path(target_path)
        
    # Check if target exists
    if target_path.exists() and not force:
        raise FileExistsError(f"Target file exists, use force=True to overwrite: {target_path}")
        
    # Copy the file
    shutil.copy2(backup_path, target_path)
    logger.info(f"Restored file from {backup_path} to {target_path}")
    
    return target_path


def restore_directory(
    backup_path: Union[str, Path],
    target_dir: Union[str, Path],
    force: bool = False
) -> Path:
    """Restore a directory from a backup archive.
    
    Args:
        backup_path: Path to the backup archive (.tar or .tar.gz)
        target_dir: Directory to restore to
        force: Whether to overwrite existing files
        
    Returns:
        Path to the restored directory
    """
    backup_path = Path(backup_path)
    target_dir = Path(target_dir)
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup archive not found: {backup_path}")
        
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Check if the target directory is empty or force is True
    if not force and any(target_dir.iterdir()):
        raise FileExistsError(f"Target directory is not empty, use force=True to overwrite: {target_dir}")
        
    # Extract the archive
    if backup_path.name.endswith(".tar.gz") or backup_path.name.endswith(".tgz"):
        with tarfile.open(backup_path, "r:gz") as tar:
            # Get the top-level directory in the archive
            top_dirs = [m for m in tar.getmembers() if m.isdir() and "/" not in m.name]
            
            if top_dirs:
                # Extract to a temporary directory first
                with tempfile.TemporaryDirectory() as temp_dir:
                    tar.extractall(path=temp_dir)
                    
                    # Get the extracted directory
                    extracted_dir = Path(temp_dir) / top_dirs[0].name
                    
                    # Copy contents to target directory
                    for item in extracted_dir.iterdir():
                        item_target = target_dir / item.name
                        
                        if item.is_dir():
                            shutil.copytree(item, item_target, dirs_exist_ok=force)
                        else:
                            if force or not item_target.exists():
                                shutil.copy2(item, item_target)
            else:
                # No top-level directory, extract directly
                tar.extractall(path=target_dir)
    elif backup_path.name.endswith(".tar"):
        with tarfile.open(backup_path, "r") as tar:
            # Get the top-level directory in the archive
            top_dirs = [m for m in tar.getmembers() if m.isdir() and "/" not in m.name]
            
            if top_dirs:
                # Extract to a temporary directory first
                with tempfile.TemporaryDirectory() as temp_dir:
                    tar.extractall(path=temp_dir)
                    
                    # Get the extracted directory
                    extracted_dir = Path(temp_dir) / top_dirs[0].name
                    
                    # Copy contents to target directory
                    for item in extracted_dir.iterdir():
                        item_target = target_dir / item.name
                        
                        if item.is_dir():
                            shutil.copytree(item, item_target, dirs_exist_ok=force)
                        else:
                            if force or not item_target.exists():
                                shutil.copy2(item, item_target)
            else:
                # No top-level directory, extract directly
                tar.extractall(path=target_dir)
    else:
        raise ValueError(f"Unsupported archive format: {backup_path}")
        
    logger.info(f"Restored directory from {backup_path} to {target_dir}")
    return target_dir


def restore_database(
    backup_path: Union[str, Path],
    connection_string: str,
    pg_restore_path: Optional[str] = None,
    schema: Optional[str] = None,
    clean: bool = False
) -> bool:
    """Restore a PostgreSQL database from a backup.
    
    Args:
        backup_path: Path to the backup file
        connection_string: Database connection string or URL
        pg_restore_path: Path to the pg_restore executable
        schema: Schema to restore to (default: public)
        clean: Whether to clean (drop) objects before restoring
        
    Returns:
        True if the restoration was successful
    """
    backup_path = Path(backup_path)
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
    # Find pg_restore executable
    if not pg_restore_path:
        pg_restore_path = "pg_restore"
        
    # Build pg_restore command
    cmd = [pg_restore_path, "--no-owner"]
    
    if clean:
        cmd.append("--clean")
        
    # Add schema if specified
    if schema:
        cmd.extend(["--schema", schema])
        
    # Add connection string
    if "://" in connection_string:
        # Use connection string directly
        cmd.extend(["--dbname", connection_string])
    else:
        # Treat as a database name
        cmd.extend(["--dbname", connection_string])
        
    # Check if the backup is compressed
    if backup_path.name.endswith(".gz"):
        # For compressed backups, pipe through gunzip
        with gzip.open(backup_path, "rb") as f:
            process = subprocess.run(
                cmd,
                input=f.read(),
                stderr=subprocess.PIPE,
                check=False
            )
    else:
        # For uncompressed backups, read directly
        cmd.append(str(backup_path))
        process = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            check=False
        )
        
    # Check the result
    if process.returncode != 0:
        logger.error(f"Error restoring database: {process.stderr.decode()}")
        return False
        
    logger.info(f"Successfully restored database from {backup_path}")
    return True


def restore_from_metadata(
    metadata_path: Union[str, Path],
    target_dir: Optional[Union[str, Path]] = None,
    force: bool = False
) -> Dict[str, Union[Path, bool]]:
    """Restore files and directories from a migration backup metadata file.
    
    Args:
        metadata_path: Path to the backup metadata file
        target_dir: Base directory to restore to (default: use original paths)
        force: Whether to overwrite existing files
        
    Returns:
        Dictionary mapping backup paths to restoration results
    """
    metadata_path = Path(metadata_path)
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
    # Load metadata
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        
    # Check if this is a valid backup metadata file
    if "backups" not in metadata:
        raise ValueError(f"Invalid backup metadata file: {metadata_path}")
        
    # Restore each backup
    results = {}
    
    for path_str, info in metadata["backups"].items():
        backup_path = Path(info["backup_path"])
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            results[path_str] = False
            continue
            
        # Determine target path
        if target_dir:
            target_base = Path(target_dir)
            # Use relative path from original path
            original_path = Path(path_str)
            if "original_path" in info:
                original_path = Path(info["original_path"])
                
            # Create target path
            target_path = target_base / original_path.name
        else:
            # Restore to original path
            target_path = Path(path_str)
            if "original_path" in info:
                target_path = Path(info["original_path"])
                
        try:
            # Restore based on type
            if info.get("is_directory", False):
                restored_path = restore_directory(backup_path, target_path, force)
            else:
                restored_path = restore_file(backup_path, target_path, force)
                
            results[path_str] = restored_path
            
        except Exception as e:
            logger.error(f"Error restoring {path_str}: {e}")
            results[path_str] = False
            
    return results


def undo_migration(
    backups_dir: Union[str, Path],
    force: bool = False
) -> Dict[str, Any]:
    """Undo a migration by restoring all backups in a directory.
    
    Args:
        backups_dir: Directory containing backup files and metadata
        force: Whether to overwrite existing files
        
    Returns:
        Dictionary with restoration results
    """
    backups_dir = Path(backups_dir)
    
    if not backups_dir.exists() or not backups_dir.is_dir():
        raise FileNotFoundError(f"Backups directory not found: {backups_dir}")
        
    # Find the most recent metadata file
    metadata_files = list(backups_dir.glob("migration_backup_*.meta.json"))
    
    if not metadata_files:
        raise FileNotFoundError(f"No backup metadata files found in {backups_dir}")
        
    # Sort by modification time (most recent first)
    metadata_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    metadata_path = metadata_files[0]
    
    # Restore from the metadata
    results = restore_from_metadata(metadata_path, force=force)
    
    # Build a summary
    summary = {
        "metadata_file": str(metadata_path),
        "restore_count": len(results),
        "successful": sum(1 for r in results.values() if r is not False),
        "failed": sum(1 for r in results.values() if r is False),
        "results": {
            path: str(result) if result is not False else False
            for path, result in results.items()
        }
    }
    
    return summary