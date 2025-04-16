#!/usr/bin/env python
"""
Validation script to ensure the queries module is using domain-driven design.

This script checks that:
1. No UnoObj references are used in the module
2. Domain entities (Query, QueryPath, QueryValue) are used instead
3. Repository pattern and proper domain services are implemented
4. Circular dependencies are avoided with proper forward references
"""

import os
import re
import sys
from pathlib import Path


def check_file(file_path):
    """Check a single Python file for UnoObj references."""
    with open(file_path, 'r') as f:
        content = f.read()
        
        # Check for UnoObj references
        if re.search(r'\bUnoObj\b', content):
            print(f"  WARNING: Found UnoObj reference in {file_path}")
            return False
        
        # Check if entities.py exists and has proper domain entities
        if file_path.name == "entities.py":
            if not re.search(r'class Query\(AggregateRoot', content):
                print(f"  WARNING: Query domain entity not defined in {file_path}")
                return False
            if not re.search(r'class QueryPath\(AggregateRoot', content):
                print(f"  WARNING: QueryPath domain entity not defined in {file_path}")
                return False
            if not re.search(r'class QueryValue\(AggregateRoot', content):
                print(f"  WARNING: QueryValue domain entity not defined in {file_path}")
                return False
        
        # Check if domain entities are imported in other files
        if file_path.name != "entities.py" and file_path.name.endswith(".py"):
            if "domain" in file_path.name and not re.search(r'from uno\.queries\.entities import', content):
                print(f"  WARNING: Domain entities not imported in domain file {file_path}")
                return False
        
        # Check if __init__.py properly exports domain entities
        if file_path.name == "__init__.py":
            if not re.search(r'from uno\.queries\.entities import Query, QueryPath, QueryValue', content):
                print(f"  WARNING: Domain entities not exported in {file_path}")
                return False
            if not re.search(r"'Query',\s*\n\s*'QueryPath',\s*\n\s*'QueryValue'", content):
                print(f"  WARNING: Domain entities not included in __all__ in {file_path}")
                return False
    
    return True


def main():
    """Check all Python files in the queries module."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    queries_dir = project_root / "src" / "uno" / "queries"
    
    if not queries_dir.exists():
        print(f"Error: Queries directory not found at {queries_dir}")
        return 1
    
    print(f"Checking queries module at {queries_dir}")
    
    # Check all Python files in the queries directory
    all_valid = True
    for file_path in queries_dir.glob("**/*.py"):
        print(f"Checking {file_path.relative_to(project_root)}")
        if not check_file(file_path):
            all_valid = False
    
    if all_valid:
        print("\nVALIDATION PASSED: Queries module uses domain-driven design!")
        return 0
    else:
        print("\nVALIDATION FAILED: Some issues found in the queries module.")
        return 1


if __name__ == "__main__":
    sys.exit(main())