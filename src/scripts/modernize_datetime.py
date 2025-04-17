#!/usr/bin/env python3
"""
Modernize datetime usage in the codebase.

This script updates outdated datetime patterns to follow modern Python standards:
- Replace datetime.utcnow() with datetime.now(datetime.UTC)
"""

import os
import re
from pathlib import Path
import sys
import cli_utils

# Shared logger
logger = cli_utils.setup_logger(__name__)


def update_file(file_path: Path) -> tuple[int, list[str]]:
    """
    Update datetime.utcnow() to datetime.now(datetime.UTC) in a file.
    
    Args:
        file_path: Path to the file to update
        
    Returns:
        Tuple of (count of replacements, list of modified lines)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add UTC import if needed
    imports_updated = False
    if 'datetime.utcnow' in content:
        # Check if datetime is imported
        if re.search(r'import\s+datetime', content) or re.search(r'from\s+datetime\s+import', content):
            # Make sure UTC is imported if we're replacing utcnow
            if 'datetime.UTC' not in content and 'UTC' not in content:
                # Find the datetime import
                match = re.search(r'(from\s+datetime\s+import\s+[^()]*?)(?=\s*$|\s*#|\s*from|\s*import)', content, re.MULTILINE)
                if match:
                    # Add UTC to the existing import
                    old_import = match.group(1)
                    if old_import.strip().endswith(','):
                        new_import = f"{old_import} UTC,"
                    else:
                        new_import = f"{old_import}, UTC"
                    
                    content = content.replace(old_import, new_import)
                    imports_updated = True
                else:
                    # Add a separate import for UTC if regular pattern not found
                    simple_match = re.search(r'(from\s+datetime\s+import\s+datetime)', content)
                    if simple_match:
                        old_import = simple_match.group(1)
                        new_import = f"{old_import}, UTC"
                        content = content.replace(old_import, new_import)
                        imports_updated = True
    
    # Replace patterns
    patterns = [
        # Handle onupdate= pattern (must be before basic pattern)
        (r'onupdate=datetime\.utcnow', r'onupdate=lambda: datetime.now(datetime.UTC)'),
        
        # Basic pattern: datetime.utcnow()
        (r'datetime\.utcnow\(\)', r'datetime.now(datetime.UTC)'),
        
        # Field default factory pattern
        (r'default_factory=datetime\.utcnow', r'default_factory=lambda: datetime.now(datetime.UTC)'),
        
        # Imported datetime pattern: from datetime import datetime; datetime.utcnow()
        (r'(?<!\.)datetime\.utcnow\(\)', r'datetime.now(UTC)'),
        
        # More general pattern for any variable based on context
        (r'([^\.a-zA-Z0-9_])datetime\.utcnow\(\)', r'\1datetime.now(datetime.UTC)'),
        
        # Handle specific case in scheduler.py and other files (whitespace before datetime)
        (r'\s+datetime\.utcnow\(\)', r' datetime.now(datetime.UTC)'),
        
        # Handle datetime.datetime.utcnow pattern (fully qualified)
        (r'datetime\.datetime\.utcnow', r'datetime.datetime.now(datetime.UTC)'),
        
        # Handle default= pattern in models
        (r'default=datetime\.utcnow', r'default=lambda: datetime.now(datetime.UTC)'),
        
        # Variation of default= pattern
        (r'default=datetime\.datetime\.utcnow', r'default=lambda: datetime.datetime.now(datetime.UTC)'),
        
        # Variation of onupdate= pattern
        (r'onupdate=datetime\.datetime\.utcnow', r'onupdate=lambda: datetime.datetime.now(datetime.UTC)'),
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
    
    if count > 0 or imports_updated:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return count, modified_lines


def main() -> int:
    """Update datetime usage in the codebase."""
    project_root = Path(__file__).parent.parent.parent
    # Parse optional path argument
    target_arg = cli_utils.parse_path_arg(
        "Update datetime usage in the codebase"
    )
    if target_arg:
        target_path = Path(target_arg)
        if not target_path.is_absolute():
            target_path = project_root / target_path
    else:
        target_path = project_root / 'src'
    
    py_files = []
    if target_path.is_file() and target_path.suffix == '.py':
        py_files = [target_path]
    else:
        py_files = list(target_path.glob('**/*.py'))
    
    logger.info(f"Scanning {len(py_files)} Python files...")
    
    total_replacements = 0
    modified_files = 0
    
    # Exclude this script itself to avoid recursion
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
            logger.info(f"\nUpdated {rel_path} ({count} replacements):")
            for line in modified_lines[:5]:  # Show at most 5 modifications per file
                logger.info(f"  {line}")
            if len(modified_lines) > 5:
                logger.info(f"  ... and {len(modified_lines) - 5} more modifications")
    
    logger.info(f"\nSummary: Updated {total_replacements} occurrences in {modified_files} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())