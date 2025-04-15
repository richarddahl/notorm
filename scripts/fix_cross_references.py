#!/usr/bin/env python3
"""
Script to fix cross-reference issues in MkDocs documentation files.
This script addresses the mkdocs_autorefs warnings by fixing the cross-reference targets.
"""

import os
from pathlib import Path
import re

# Define the docs directory
DOCS_DIR = Path("docs")

# Define files with cross-reference issues and their fixes
CROSS_REF_FIXES = {
    "testing.md": {
        "pattern": r"Could not find cross-reference target '0'",
        "replacement": "Could not find cross-reference target '[0]'",
    },
    "caching/multilevel.md": {
        "pattern": r"''local''|''distributed''|''overall''",
        "replacement": "`local`|`distributed`|`overall`",
    },
    "database/pg_optimizer.md": {
        "pattern": r"''total_bytes_human''",
        "replacement": "`total_bytes_human`",
    },
    "dependencies/overview.md": {
        "pattern": r'"id"|"name"',
        "replacement": "`id`|`name`",
    },
    "multitenancy/management.md": {
        "pattern": r'"analytics"',
        "replacement": "`analytics`",
    },
    "reports/tutorial.md": {
        "pattern": r'"monthly_spent"',
        "replacement": "`monthly_spent`",
    },
}


def fix_cross_references_in_file(file_path, fixes):
    """Fix cross-reference issues in a specific file."""
    if not file_path.exists():
        print(f"Warning: File {file_path} does not exist.")
        return

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    original_content = content

    # Apply fixes
    for pattern, replacement in fixes.items():
        # Convert pattern to regex if it's not already
        if not pattern.startswith("^") and not pattern.endswith("$"):
            pattern = re.compile(pattern)

        # Replace the pattern
        if isinstance(pattern, str):
            content = content.replace(pattern, replacement)
        else:  # It's a regex
            content = pattern.sub(replacement, content)

    # Write changes back if content was modified
    if content != original_content:
        print(f"Fixing cross-references in {file_path}")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)


def main():
    """Main function to fix cross-reference issues."""
    for file_name, fixes in CROSS_REF_FIXES.items():
        file_path = DOCS_DIR / file_name

        # Create a dictionary of pattern/replacement pairs
        fix_dict = {}
        if isinstance(fixes["pattern"], str):
            patterns = fixes["pattern"].split("|")
            replacements = fixes["replacement"].split("|")

            # If we have equal number of patterns and replacements, pair them
            if len(patterns) == len(replacements):
                for i, pattern in enumerate(patterns):
                    fix_dict[pattern] = replacements[i]
            else:
                # Otherwise, use the same replacement for all patterns
                for pattern in patterns:
                    fix_dict[pattern] = fixes["replacement"]
        else:
            # Single pattern/replacement
            fix_dict[fixes["pattern"]] = fixes["replacement"]

        fix_cross_references_in_file(file_path, fix_dict)

    print("Cross-reference fixing completed!")


if __name__ == "__main__":
    main()
