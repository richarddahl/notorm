#!/usr/bin/env python3
"""
Script to modernize async patterns in the codebase.

This script updates deprecated asyncio patterns:
1. Replaces direct event loop access (asyncio.get_event_loop()) with modern alternatives
2. Updates transaction management to use context managers consistently
3. Standardizes task creation and management
"""

import os
import re
from pathlib import Path
import sys
import argparse
from typing import List, Tuple, Dict

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Define patterns to replace
patterns = [
    # Replace direct event loop access with modern alternatives
    (
        r'loop\s*=\s*asyncio\.get_event_loop\(\)',
        '# Using asyncio.create_task() instead of direct event loop access'
    ),
    
    # Replace loop.add_signal_handler with modern signal handling
    (
        r'loop\.add_signal_handler\(\s*([^,]+),\s*lambda\s+(?:s=\1)?\s*:\s*asyncio\.create_task\(([^)]+)\)\s*\)',
        'asyncio.create_task(self._setup_signal_handler(\\1, \\2))'
    ),
    
    # Replace asyncio.get_running_loop().time() with asyncio.get_running_loop().time()
    (
        r'(?:loop|asyncio\.get_event_loop\(\))\.time\(\)',
        'asyncio.get_running_loop().time()'
    ),
    
    # Replace raw time extraction (when using cached event loop)
    (
        r'now\s*=\s*(?:self\.)?(?:_)?loop\.time\(\)',
        'now = asyncio.get_running_loop().time()'
    ),
    
    # Update AsyncCache.get method with get_running_loop
    (
        r'now\s*=\s*asyncio\.get_event_loop\(\)\.time\(\)',
        'now = asyncio.get_running_loop().time()'
    ),
]

# Files to exclude from processing
exclude_patterns = [
    r'.*\.git/.*',
    r'.*\.pyc$',
    r'.*\.pyo$',
    r'.*__pycache__/.*',
    r'.*venv/.*',
    r'.*/env/.*',
    r'.*/.tox/.*',
    r'.*/.idea/.*',
    r'.*\.egg-info/.*',
    r'.*\.pytest_cache/.*',
    r'.*\btest_.*\.py$',  # Exclude test files to avoid breaking tests
]

def should_process_file(file_path: str) -> bool:
    """Check if the file should be processed based on exclusion patterns."""
    for pattern in exclude_patterns:
        if re.match(pattern, file_path):
            return False
    return True

def update_file(file_path: str, dry_run: bool = False) -> List[Tuple[str, str, int]]:
    """
    Update a file with the defined patterns.
    
    Args:
        file_path: Path to the file to update
        dry_run: If True, don't write changes to the file
        
    Returns:
        List of tuples containing (pattern, replacement, count)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping binary file: {file_path}")
        return []
    
    changes = []
    modified = False
    
    # Apply all patterns
    for pattern, replacement in patterns:
        # Compile the regex pattern
        regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
        
        # Count matches before replacement
        matches_count = len(regex.findall(content))
        
        if matches_count > 0:
            # Replace the pattern
            new_content = regex.sub(replacement, content)
            
            if new_content != content:
                content = new_content
                modified = True
                changes.append((pattern, replacement, matches_count))
    
    # Write the changes if the file was modified and this is not a dry run
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes

def process_directory(directory: str, dry_run: bool = False) -> Dict[str, List[Tuple[str, str, int]]]:
    """
    Process all Python files in a directory and its subdirectories.
    
    Args:
        directory: Directory to process
        dry_run: If True, don't write changes to files
        
    Returns:
        Dictionary mapping file paths to lists of changes
    """
    results = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Skip files that match exclusion patterns
                if not should_process_file(file_path):
                    continue
                
                changes = update_file(file_path, dry_run)
                
                if changes:
                    results[file_path] = changes
    
    return results

def print_results(results: Dict[str, List[Tuple[str, str, int]]]) -> None:
    """Print the results of the modernization process."""
    if not results:
        print("No files were modified.")
        return
    
    print(f"Modified {len(results)} files:")
    
    for file_path, changes in results.items():
        print(f"\n{file_path}:")
        
        for pattern, replacement, count in changes:
            print(f"  - Replaced {count} occurrences of pattern:")
            print(f"    {pattern}")
            print(f"    with:")
            print(f"    {replacement}")

def create_async_helper_function():
    """Create a new helper function file for the modern async patterns."""
    helper_file = Path("src/uno/core/async/helpers.py")
    
    # Create the directory if it doesn't exist
    helper_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Only create the file if it doesn't exist
    if not helper_file.exists():
        content = """\"\"\"
Helper functions for modern async patterns.

This module provides utility functions for modern async patterns, including:
- Signal handling without direct event loop access
- TaskGroup for structured concurrency
- Transaction context manager
\"\"\"

import asyncio
import signal
import contextlib
from typing import Any, Awaitable, Callable, TypeVar, List, Set, Optional
import logging

T = TypeVar('T')


async def setup_signal_handler(
    sig: signal.Signals,
    handler: Callable[[signal.Signals], Awaitable[None]],
) -> None:
    \"\"\"
    Set up a signal handler using modern patterns.
    
    Args:
        sig: Signal to handle
        handler: Async handler function
    \"\"\"
    loop = asyncio.get_running_loop()
    
    def _handler():
        asyncio.create_task(handler(sig))
    
    loop.add_signal_handler(sig, _handler)


@contextlib.asynccontextmanager
async def transaction(session: Any) -> None:
    \"\"\"
    Context manager for database transactions.
    
    Args:
        session: Database session
        
    Yields:
        None
    \"\"\"
    try:
        yield
        await session.commit()
    except Exception:
        await session.rollback()
        raise


class TaskGroup:
    \"\"\"
    TaskGroup for structured concurrency.
    
    This class provides a way to manage multiple tasks as a group, similar to
    Python 3.11's asyncio.TaskGroup but with additional features.
    \"\"\"
    
    def __init__(self, name: Optional[str] = None, logger: Optional[logging.Logger] = None):
        \"\"\"
        Initialize the task group.
        
        Args:
            name: Optional name for the task group
            logger: Optional logger instance
        \"\"\"
        self.name = name or f"TaskGroup_{id(self):x}"
        self.logger = logger or logging.getLogger(__name__)
        self.tasks: Set[asyncio.Task] = set()
        self._entered = False
        self._exited = False
    
    async def __aenter__(self) -> 'TaskGroup':
        \"\"\"Enter the async context, enabling task creation.\"\"\"
        self._entered = True
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        \"\"\"Exit the async context, cancelling all tasks.\"\"\"
        if self._exited:
            return
        
        self._exited = True
        
        if not self.tasks:
            return
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Raise any exceptions from tasks
        for task in self.tasks:
            if task.done() and not task.cancelled():
                exc = task.exception()
                if exc is not None and exc_type is None:
                    raise exc
    
    def create_task(self, coro: Awaitable[T], name: Optional[str] = None) -> asyncio.Task[T]:
        \"\"\"
        Create a task in this group.
        
        Args:
            coro: Coroutine to run as a task
            name: Optional name for the task
            
        Returns:
            The created task
        \"\"\"
        if not self._entered or self._exited:
            raise RuntimeError("TaskGroup not active")
        
        task_name = name or f"{self.name}_{len(self.tasks)}"
        task = asyncio.create_task(coro, name=task_name)
        self.tasks.add(task)
        
        # Remove the task from the set when it's done
        task.add_done_callback(self.tasks.discard)
        
        return task
    
    @property
    def active_tasks(self) -> List[asyncio.Task]:
        \"\"\"Get the list of active (unfinished) tasks.\"\"\"
        return [task for task in self.tasks if not task.done()]
    
    @property
    def completed_tasks(self) -> List[asyncio.Task]:
        \"\"\"Get the list of completed tasks.\"\"\"
        return [task for task in self.tasks if task.done() and not task.cancelled()]
    
    @property
    def cancelled_tasks(self) -> List[asyncio.Task]:
        \"\"\"Get the list of cancelled tasks.\"\"\"
        return [task for task in self.tasks if task.cancelled()]
    
    async def cancel_all(self) -> None:
        \"\"\"Cancel all tasks in the group.\"\"\"
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
"""
        
        with open(helper_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created helper file: {helper_file}")
        
        # Create an __init__.py to make it a proper package
        init_file = helper_file.parent / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('"""Async utilities package."""\n')
            print(f"Created init file: {init_file}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Modernize async patterns in the codebase")
    parser.add_argument("--dir", "-d", default="src", help="Directory to process")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Don't write changes to files")
    parser.add_argument("--create-helpers", "-c", action="store_true", help="Create helper functions")
    args = parser.parse_args()
    
    if args.create_helpers:
        create_async_helper_function()
    
    print(f"Processing directory: {args.dir}")
    print(f"Dry run: {args.dry_run}")
    
    results = process_directory(args.dir, args.dry_run)
    print_results(results)


if __name__ == "__main__":
    main()