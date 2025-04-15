#!/usr/bin/env python3
"""
Script to generate placeholder files for missing documentation.
This script creates basic placeholder files for documentation referenced in the navigation
but not found in the docs directory.
"""

import os
from pathlib import Path
import yaml

# Define the docs directory and mkdocs config file
DOCS_DIR = Path("docs")
MKDOCS_CONFIG = Path("mkdocs.yml")


def extract_nav_paths(nav_item, paths=None):
    """Recursively extract all file paths from the navigation structure."""
    if paths is None:
        paths = []

    if isinstance(nav_item, dict):
        for _, value in nav_item.items():
            extract_nav_paths(value, paths)
    elif isinstance(nav_item, list):
        for item in nav_item:
            extract_nav_paths(item, paths)
    elif isinstance(nav_item, str) and not nav_item.startswith("http"):
        paths.append(nav_item)

    return paths


def generate_placeholder(file_path):
    """Generate a placeholder markdown file with basic structure."""
    # Create directory if it doesn't exist
    os.makedirs(file_path.parent, exist_ok=True)

    # Generate title from filename
    title = file_path.stem.replace("_", " ").replace("-", " ").title()

    # Create content
    content = f"""# {title}

## Overview

This is a placeholder document for {file_path.name}.

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

```python
# Example code
def example_function():
    return "This is an example"
```

## Related Documentation

- [Documentation Home](../index.md)

"""

    # Write the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Created placeholder file: {file_path}")


def main():
    """Main function to generate placeholder files."""
    # Load the MkDocs configuration
    with open(MKDOCS_CONFIG, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Extract all file paths from the navigation
    nav_paths = extract_nav_paths(config.get("nav", []))

    # Generate placeholders for missing files
    for path in nav_paths:
        file_path = DOCS_DIR / path
        if not file_path.exists():
            generate_placeholder(file_path)

    print("Placeholder generation completed!")


if __name__ == "__main__":
    main()
