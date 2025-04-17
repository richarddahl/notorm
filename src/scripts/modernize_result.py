#!/usr/bin/env python3
"""
Modernize Result API usage in the codebase.

This script updates outdated Result API patterns to follow modern standards:
- Replace result.unwrap() with result.value
- Replace result.unwrap_err() with result.error
- Replace result.is_ok() with result.is_success
- Replace result.is_err() with result.is_failure
"""

import os
import re
from pathlib import Path
import sys


def update_file(file_path: Path) -> tuple[int, list[str]]:
    """
    Update Result pattern methods in a file.
    
    Args:
        file_path: Path to the file to update
        
    Returns:
        Tuple of (count of replacements, list of modified lines)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace patterns
    patterns = [
        # Replace unwrap()
        (r'\.unwrap\(\)', r'.value'),
        
        # Replace unwrap_err()
        (r'\.unwrap_err\(\)', r'.error'),
        
        # Replace is_ok()
        (r'\.is_ok\(\)', r'.is_success'),
        
        # Replace is_err()
        (r'\.is_err\(\)', r'.is_failure'),
    ]
    
    count = 0
    modified_lines = []
    
    for pattern, replacement in patterns:
        prev_content = content
        content = re.sub(pattern, replacement, content)
        if content != prev_content:
            # Find modified lines for reporting
            original_lines = prev_content.splitlines()
            updated_lines = content.splitlines()
            for i, (old, new) in enumerate(zip(original_lines, updated_lines)):
                if old != new:
                    modified_lines.append(f"Line {i+1}: {old} -> {new}")
            
            # More reliable way to count replacements
            replacement_count = len(re.findall(pattern, prev_content))
            count += replacement_count
    
    if count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return count, modified_lines


def main():
    """Update Result API usage in the codebase."""
    # Get the project root directory (2 levels up from the script)
    project_root = Path(__file__).parent.parent.parent
    
    if len(sys.argv) > 1:
        # Allow specifying a specific file or directory
        target_path = Path(sys.argv[1])
        if not target_path.is_absolute():
            target_path = project_root / target_path
    else:
        # Default to scanning the src directory
        target_path = project_root / 'src'
    
    py_files = []
    if target_path.is_file() and target_path.suffix == '.py':
        py_files = [target_path]
    else:
        py_files = list(target_path.glob('**/*.py'))
    
    print(f"Scanning {len(py_files)} Python files...")
    
    total_replacements = 0
    modified_files = 0
    
    # Exclude this script to avoid recursion
    script_path = Path(__file__).resolve()
    
    for file_path in py_files:
        # Skip this script itself
        if file_path.resolve() == script_path:
            continue
            
        count, modified_lines = update_file(file_path)
        if count > 0:
            modified_files += 1
            total_replacements += count
            rel_path = file_path.relative_to(project_root) if project_root in file_path.parents else file_path
            print(f"\nUpdated {rel_path} ({count} replacements):")
            for line in modified_lines[:5]:  # Show at most 5 modifications per file
                print(f"  {line}")
            if len(modified_lines) > 5:
                print(f"  ... and {len(modified_lines) - 5} more modifications")
    
    print(f"\nSummary: Updated {total_replacements} occurrences in {modified_files} files.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())