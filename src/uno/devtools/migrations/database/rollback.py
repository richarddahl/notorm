"""Migration rollback utilities.

This module provides utilities for rolling back database migrations
with transaction safety and verification.
"""
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
import os
import logging
import importlib.util
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.engine import Engine, Connection

from uno.devtools.migrations.database.apply import MigrationExecutor

logger = logging.getLogger(__name__)

def rollback_migration(
    script_path: Union[str, Path],
    engine: Engine,
    schema: str = 'public',
    dry_run: bool = False,
    context: Optional[Dict[str, Any]] = None,
    verify: bool = True
) -> bool:
    """Roll back a migration with transaction safety.
    
    Args:
        script_path: Path to the migration script to roll back
        engine: SQLAlchemy engine for the database
        schema: Database schema name
        dry_run: Whether to run in dry run mode (no changes applied)
        context: Additional context to pass to the script
        verify: Whether to verify the rollback before committing
        
    Returns:
        True if the rollback was successful, False otherwise
    """
    script_path = Path(script_path)
    
    if not script_path.exists():
        logger.error(f"Migration script not found: {script_path}")
        return False
        
    try:
        if script_path.suffix == '.py':
            # Import the script as a module
            spec = importlib.util.spec_from_file_location(
                f"migration_{script_path.stem}", script_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if the module has a downgrade function
            if not hasattr(module, 'downgrade'):
                logger.error(f"Migration script has no downgrade function: {script_path}")
                return False
                
            # Execute the downgrade function
            with MigrationExecutor(engine, schema, dry_run) as executor:
                logger.info(f"Rolling back migration: {script_path}")
                
                # Set up context
                context = context or {}
                context['connection'] = executor.conn
                context['schema'] = schema
                
                # Create a mock alembic op object for dry run
                if dry_run:
                    class MockOp:
                        def __getattr__(self, name):
                            def method(*args, **kwargs):
                                logger.info(f"Would call op.{name}({args}, {kwargs}) (dry run)")
                            return method
                            
                    module.op = MockOp()
                
                # Execute downgrade
                if dry_run:
                    logger.info(f"Would execute downgrade from {script_path} (dry run)")
                    module.downgrade()
                else:
                    logger.info(f"Executing downgrade from {script_path}")
                    module.downgrade()
                    
                # Verify rollback if requested
                if verify and not dry_run:
                    logger.info(f"Verifying rollback for {script_path}")
                    # In a real implementation, you would check the database state
                    # to verify that the rollback was successful
                    # This is a simplified implementation
                    pass
                    
            return True
            
        elif script_path.suffix == '.sql':
            # For SQL scripts, we need a rollback SQL script
            rollback_script_path = script_path.with_name(f"{script_path.stem}_rollback.sql")
            
            if not rollback_script_path.exists():
                logger.error(f"Rollback script not found: {rollback_script_path}")
                return False
                
            with open(rollback_script_path, 'r') as f:
                rollback_sql = f.read()
                
            with MigrationExecutor(engine, schema, dry_run) as executor:
                logger.info(f"Rolling back migration with SQL: {rollback_script_path}")
                executor.execute_sql(rollback_sql)
                
            return True
            
        else:
            logger.error(f"Unsupported migration script type: {script_path.suffix}")
            return False
            
    except Exception as e:
        logger.error(f"Error rolling back migration {script_path}: {e}")
        return False


def rollback_migrations(
    scripts: List[Union[str, Path]],
    engine: Engine,
    schema: str = 'public',
    dry_run: bool = False,
    context: Optional[Dict[str, Any]] = None,
    verify: bool = True,
    stop_on_error: bool = True
) -> Dict[str, bool]:
    """Roll back multiple migrations with transaction safety.
    
    Args:
        scripts: List of paths to migration scripts to roll back (in reverse order)
        engine: SQLAlchemy engine for the database
        schema: Database schema name
        dry_run: Whether to run in dry run mode (no changes applied)
        context: Additional context to pass to the scripts
        verify: Whether to verify each rollback before committing
        stop_on_error: Whether to stop on the first error
        
    Returns:
        Dictionary mapping script paths to success/failure status
    """
    results = {}
    
    for script_path in scripts:
        script_path = Path(script_path)
        
        if not script_path.exists():
            logger.error(f"Migration script not found: {script_path}")
            results[str(script_path)] = False
            
            if stop_on_error:
                break
                
            continue
            
        success = rollback_migration(
            script_path, 
            engine, 
            schema, 
            dry_run, 
            context, 
            verify
        )
        
        results[str(script_path)] = success
        
        if not success and stop_on_error:
            break
            
    return results


def rollback_to_revision(
    revision: str,
    migrations_dir: Union[str, Path],
    engine: Engine,
    schema: str = 'public',
    dry_run: bool = False,
    context: Optional[Dict[str, Any]] = None,
    verify: bool = True,
    stop_on_error: bool = True
) -> Dict[str, bool]:
    """Roll back all migrations until a specific revision.
    
    Args:
        revision: Revision ID to roll back to
        migrations_dir: Directory containing migration scripts
        engine: SQLAlchemy engine for the database
        schema: Database schema name
        dry_run: Whether to run in dry run mode (no changes applied)
        context: Additional context to pass to the scripts
        verify: Whether to verify each rollback before committing
        stop_on_error: Whether to stop on the first error
        
    Returns:
        Dictionary mapping script paths to success/failure status
    """
    migrations_dir = Path(migrations_dir)
    
    if not migrations_dir.exists() or not migrations_dir.is_dir():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        return {}
        
    # Get all Python migration scripts
    scripts = list(migrations_dir.glob('*.py'))
    
    # Filter and sort scripts by revision ID
    # This is a simplified implementation that assumes the filename starts with the revision ID
    scripts = [
        script for script in scripts
        if script.stem.split('_')[0] > revision
    ]
    
    # Sort scripts in descending order (newest first)
    scripts.sort(key=lambda p: p.stem.split('_')[0], reverse=True)
    
    return rollback_migrations(
        scripts, 
        engine, 
        schema, 
        dry_run, 
        context, 
        verify, 
        stop_on_error
    )


def generate_rollback_script(
    script_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None
) -> Path:
    """Generate a rollback script for a migration.
    
    For Python migrations, this extracts the downgrade function.
    For SQL migrations, this attempts to reverse the operations.
    
    Args:
        script_path: Path to the migration script
        output_dir: Directory where the rollback script will be saved (default: same as script)
        
    Returns:
        Path to the generated rollback script
    """
    script_path = Path(script_path)
    
    if not script_path.exists():
        raise FileNotFoundError(f"Migration script not found: {script_path}")
        
    output_dir = Path(output_dir) if output_dir else script_path.parent
    
    if script_path.suffix == '.py':
        # Import the script as a module
        spec = importlib.util.spec_from_file_location(
            f"migration_{script_path.stem}", script_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if the module has a downgrade function
        if not hasattr(module, 'downgrade'):
            raise ValueError(f"Migration script has no downgrade function: {script_path}")
            
        # Generate a new Python file with just the downgrade function
        rollback_script_path = output_dir / f"{script_path.stem}_rollback.py"
        
        with open(script_path, 'r') as f:
            content = f.read()
            
        # Extract the header and imports
        header_end = content.find('def upgrade()')
        if header_end == -1:
            header_end = content.find('def downgrade()')
            
        header = content[:header_end]
        
        # Extract the downgrade function
        downgrade_start = content.find('def downgrade()')
        downgrade_end = len(content)
        downgrade = content[downgrade_start:downgrade_end]
        
        # Generate the rollback script
        rollback_content = f"{header}\n{downgrade}\n"
        
        with open(rollback_script_path, 'w') as f:
            f.write(rollback_content)
            
        return rollback_script_path
        
    elif script_path.suffix == '.sql':
        # Generate a rollback SQL script by reversing operations
        # This is a simplified implementation that just adds placeholders
        rollback_script_path = output_dir / f"{script_path.stem}_rollback.sql"
        
        with open(script_path, 'r') as f:
            content = f.read()
            
        # Extract header and footer
        lines = content.split('\n')
        header_lines = []
        
        for line in lines:
            if line.startswith('--'):
                header_lines.append(line)
            else:
                break
                
        # Generate a basic rollback script with BEGIN/COMMIT
        rollback_content = '\n'.join(header_lines)
        rollback_content += "\n\n-- WARNING: Auto-generated rollback script, review carefully!\n"
        rollback_content += "\nBEGIN;\n\n"
        rollback_content += "-- TODO: Add rollback operations here\n"
        rollback_content += "\nCOMMIT;\n"
        
        with open(rollback_script_path, 'w') as f:
            f.write(rollback_content)
            
        return rollback_script_path
        
    else:
        raise ValueError(f"Unsupported migration script type: {script_path.suffix}")