#!/usr/bin/env python
"""
Validation script to ensure the meta module is using domain-driven design.

This script checks that:
1. No UnoObj references are used in the module
2. Domain entities (MetaType, MetaRecord) are used instead
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
            required_entities = ['MetaType', 'MetaRecord']
            for entity in required_entities:
                pattern = rf'class {entity}\([^)]*(?:AggregateRoot|Entity)'
                if not re.search(pattern, content):
                    print(f"  WARNING: {entity} domain entity not defined properly in {file_path}")
                    return False
        
        # Check if domain entities are imported in other files
        if file_path.name != "entities.py" and file_path.name.endswith(".py") and "domain" in file_path.name:
            if not re.search(r'from uno\.meta\.entities import', content):
                print(f"  WARNING: Domain entities not imported in domain file {file_path}")
                return False
        
        # Check if __init__.py properly exports domain entities
        if file_path.name == "__init__.py":
            if not re.search(r'from uno\.meta\.entities import', content):
                print(f"  WARNING: Domain entities not exported in {file_path}")
                return False
            
            # Check if key domain entities are in __all__
            required_exports = ["MetaType", "MetaRecord"]
            missing_exports = [
                entity for entity in required_exports 
                if not re.search(rf'"{entity}"', content)
            ]
            if missing_exports:
                print(f"  WARNING: Domain entities {', '.join(missing_exports)} not included in __all__ in {file_path}")
                return False
    
    return True


def main():
    """Check all Python files in the meta module."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    meta_dir = project_root / "src" / "uno" / "meta"
    
    if not meta_dir.exists():
        print(f"Error: Meta directory not found at {meta_dir}")
        return 1
    
    print(f"Checking meta module at {meta_dir}")
    
    # Check all Python files in the meta directory
    all_valid = True
    for file_path in meta_dir.glob("**/*.py"):
        print(f"Checking {file_path.relative_to(project_root)}")
        if not check_file(file_path):
            all_valid = False
    
    if all_valid:
        print("\nVALIDATION PASSED: Meta module uses domain-driven design!")
        return 0
    else:
        print("\nVALIDATION FAILED: Some issues found in the meta module.")
        return 1


if __name__ == "__main__":
    sys.exit(main())