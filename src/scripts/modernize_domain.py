#!/usr/bin/env python
"""
Script to modernize the domain model code in the uno framework.

This script:
1. Identifies all files using legacy domain model patterns
2. Updates imports to use new domain model classes
3. Updates class definitions to extend new base classes
4. Updates method calls to match new interfaces
5. Updates tests to use the new model classes

Since uno is a new library, we completely replace legacy patterns with
modern implementations without maintaining compatibility or adapters.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set, Pattern
import argparse


# Define patterns to find and replace
LEGACY_PATTERNS = [
    # Legacy imports
    (
        r"from uno\.domain\.core import Entity",
        "from uno.domain.models import Entity"
    ),
    (
        r"from uno\.domain\.core import (.*Entity.*)",
        r"from uno.domain.models import \1"
    ),
    (
        r"from uno\.domain\.core import (.+)",
        r"from uno.domain.models import \1"
    ),
    (
        r"from uno\.domain import core",
        "from uno.domain import models"
    ),
    # Legacy class usage with import renaming
    (
        r"class\s+(\w+)\s*\(\s*core\.Entity\s*(\[\s*.*\s*\])?\s*\)",
        r"class \1(models.Entity\2)"
    ),
    # Legacy value object usage
    (
        r"class\s+(\w+)\s*\(\s*core\.ValueObject\s*\)",
        r"class \1(models.ValueObject)"
    ),
    # Legacy aggregate root usage
    (
        r"class\s+(\w+)\s*\(\s*core\.AggregateRoot\s*(\[\s*.*\s*\])?\s*\)",
        r"class \1(models.AggregateRoot\2)"
    ),
    # Legacy domain event usage
    (
        r"class\s+(\w+)\s*\(\s*core\.DomainEvent\s*\)",
        r"class \1(models.DomainEvent)"
    ),
    # Direct class usage (already imported)
    (
        r"class\s+(\w+)\s*\(\s*Entity\s*(\[\s*.*\s*\])?\s*\)",
        r"class \1(Entity\2)"
    ),
    # Legacy method calls
    (
        r"\.register_domain_event\(",
        ".register_event("
    ),
    (
        r"\.get_domain_events\(",
        ".clear_events("
    ),
    # Legacy factory pattern
    (
        r"@classmethod\s+def\s+create\(\s*cls\s*,\s*(.*)\)\s*:\s*\n\s+.*\n\s+return\s+cls\((.*)\)",
        r"@classmethod\n    def create(cls, \1):\n        return cls(\2)"
    ),
]

# Define file patterns to exclude
EXCLUDE_PATTERNS = [
    r".*\.git/.*",
    r".*venv/.*",
    r".*__pycache__/.*",
    r".*\.pyc$",
    r".*\.pyo$",
    r".*\.pyd$",
    r".*\.so$",
    r".*\.dylib$",
    r".*\.dll$",
    r".*\.egg-info/.*",
    r".*dist/.*",
    r".*build/.*",
    r".*\.pytest_cache/.*",
    r".*\.mypy_cache/.*",
    r".*\.tox/.*",
    r".*\.coverage.*",
    r".*htmlcov/.*",
    r".*\.benchmarks/.*",
    r".*benchmarks/venv/.*",
]

# Ignore list for specific files we don't want to modify
IGNORE_LIST = [
    "src/uno/domain/models.py",
    "src/uno/domain/protocols.py",
    "src/uno/domain/specifications.py",
    "src/uno/domain/factories.py",
    "src/scripts/modernize_domain.py",
]


def should_exclude(file_path: str) -> bool:
    """Check if file should be excluded from processing."""
    # Check exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if re.match(pattern, file_path):
            return True
    
    # Check ignore list
    for ignored in IGNORE_LIST:
        if ignored in file_path:
            return True
    
    return False


def process_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Process a single file, applying pattern replacements.
    
    Args:
        file_path: Path to the file to process
        dry_run: If True, only report changes but don't modify files
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Track if any changes were made
        modified = False
        new_content = content
        
        # Apply patterns
        for pattern, replacement in LEGACY_PATTERNS:
            compiled_pattern = re.compile(pattern, re.MULTILINE)
            if re.search(compiled_pattern, new_content):
                new_content = re.sub(compiled_pattern, replacement, new_content)
                modified = True
        
        if modified:
            print(f"Modified: {file_path}")
            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def find_python_files(base_dir: str) -> List[str]:
    """
    Find all Python files in the given directory.
    
    Args:
        base_dir: The directory to search for Python files
        
    Returns:
        List of Python file paths
    """
    python_files = []
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if not should_exclude(file_path):
                    python_files.append(file_path)
    
    return python_files


def find_legacy_domain_usage(files: List[str]) -> Dict[str, List[str]]:
    """
    Find files with legacy domain model usage.
    
    Args:
        files: List of Python file paths
        
    Returns:
        Dictionary mapping file paths to lists of legacy patterns found
    """
    legacy_usage = {}
    
    # Compile legacy pattern regexes for faster matching
    compiled_patterns = [(re.compile(pattern, re.MULTILINE), replacement) 
                         for pattern, replacement in LEGACY_PATTERNS]
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            matches = []
            for pattern, _ in compiled_patterns:
                if re.search(pattern, content):
                    matches.append(pattern.pattern)
            
            if matches:
                legacy_usage[file_path] = matches
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
    
    return legacy_usage


def main():
    """Main function to run the modernization script."""
    parser = argparse.ArgumentParser(description="Modernize domain model code in uno framework")
    parser.add_argument("--scan", action="store_true", help="Only scan for legacy patterns without modifying files")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without modifying files")
    parser.add_argument("--dir", default=".", help="Base directory to process")
    args = parser.parse_args()
    
    # Get all Python files
    python_files = find_python_files(args.dir)
    print(f"Found {len(python_files)} Python files to analyze")
    
    if args.scan:
        # Just scan for legacy patterns
        legacy_usage = find_legacy_domain_usage(python_files)
        
        if legacy_usage:
            print(f"\nFound {len(legacy_usage)} files with legacy domain model usage:")
            for file_path, patterns in legacy_usage.items():
                print(f"\n{file_path}:")
                for pattern in patterns:
                    print(f"  - {pattern}")
        else:
            print("No legacy domain model usage found!")
        
        return
    
    # Process files
    modified_count = 0
    for file_path in python_files:
        if process_file(file_path, args.dry_run):
            modified_count += 1
    
    if args.dry_run:
        print(f"\nWould modify {modified_count} files (dry run)")
    else:
        print(f"\nModified {modified_count} files")


if __name__ == "__main__":
    main()