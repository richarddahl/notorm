#!/usr/bin/env python3
"""
Script to modernize error handling in the Uno framework codebase.

This script:
1. Renames UnoError to BaseError
2. Updates imports to use the standardized error module paths
3. Updates error subclasses to follow the standard pattern

Usage:
    python -m src.scripts.modernize_error_classes [--dry-run] [--auto-fix]

Options:
    --dry-run     Show changes without applying them
    --auto-fix    Apply all changes without confirmation
"""

import argparse
import os
import sys
from pathlib import Path

from src.scripts.modernize_imports import ImportModernizer


def main():
    parser = argparse.ArgumentParser(description="Modernize error handling in the Uno framework")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying them")
    parser.add_argument("--auto-fix", action="store_true", help="Apply all changes without confirmation")
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent.parent
    
    # Error directories to modernize
    error_paths = [
        "src/uno/core/errors",
        "src/uno/infrastructure/database",
        "src/uno/attributes",
        "src/uno/values",
        "src/uno/application/queries",
        "src/uno/application/workflows",
        "src/uno/infrastructure/sql"
    ]
    
    # Create a modernizer instance
    modernizer = ImportModernizer(
        base_dir, 
        remove_compat=False,
        dry_run=args.dry_run,
        auto_fix=args.auto_fix
    )
    
    # Process each path
    for path in error_paths:
        print(f"\n{'-' * 40}")
        print(f"Processing error classes in: {path}")
        print(f"{'-' * 40}")
        modernizer.run(path)
    
    # Print summary
    print("\nError classes modernization complete!")
    print(f"Total files processed: {modernizer.files_processed}")
    print(f"Files with changes: {modernizer.files_modified}")


if __name__ == "__main__":
    main()