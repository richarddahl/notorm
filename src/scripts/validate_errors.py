#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Validate that the error handling modernization was successful.

This script checks for direct imports from uno.errors.
"""

import os
import sys
import re
from pathlib import Path

def check_direct_imports(root_dir: str) -> dict:
    """
    Check for direct imports from uno.errors.
    
    Args:
        root_dir: Root directory to start searching
        
    Returns:
        Dictionary of file paths to lines with direct imports
    """
    violations = {}
    
    for root, dirs, files in os.walk(root_dir):
        if "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        import_lines = []
                        
                        for line in lines:
                            # Check for direct imports from uno.errors
                            if re.search(r"(from uno\.errors import|import uno\.errors)", line.strip()):
                                import_lines.append(line.strip())
                                
                        if import_lines:
                            violations[file_path] = import_lines
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                        
    return violations


def main():
    """Main entry point."""
    print("Validating error handling modernization...")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    src_dir = os.path.join(project_root, "src")
    
    direct_imports = check_direct_imports(src_dir)
    
    if direct_imports:
        print("\n❌ The following files still import directly from uno.errors:")
        for file_path, lines in direct_imports.items():
            rel_path = os.path.relpath(file_path, project_root)
            print(f"  - {rel_path}")
            for line in lines:
                print(f"      {line}")
    else:
        print("\n✅ No direct imports from uno.errors found")
            
    return 0


if __name__ == "__main__":
    sys.exit(main())