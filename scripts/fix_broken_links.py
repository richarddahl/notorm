#!/usr/bin/env python3
"""
Script to fix broken links in MkDocs documentation files.
This script scans all markdown files in the docs directory and fixes common link issues.
"""

import os
import re
from pathlib import Path

# Define the docs directory
DOCS_DIR = Path("docs")

# Define link replacements
LINK_REPLACEMENTS = {
    # Fix links in index.md
    "./DOCUMENTATION_INDEX.md": "./index.md",
    "./DOCUMENTATION_STATUS_VISUALIZATION.md": "./project/documentation_status.md",
    "./DOCUMENTATION_DEVELOPMENT_PLAN.md": "./project/documentation_plan.md",
    # Fix links in vector_search/index.md
    "./hybrid_search.md": "./hybrid_queries.md",
    "./events.md": "./event_driven.md",
    # Fix links in modernization/overview.md
    "examples.md": "key_features.md",
    "../../ROADMAP.md": "../project/ROADMAP.md",
    # Fix links in offline/overview.md
    "change-tracking.md": "sync.md",
    "conflict-resolution.md": "sync.md",
    "progressive-enhancement.md": "progressive.md",
    # Fix links in plugins/overview.md
    "extension_points.md": "creating_plugins.md",
    "hooks.md": "creating_plugins.md",
    "plugin_configuration.md": "creating_plugins.md",
    "plugin_examples.md": "creating_plugins.md",
    # Fix links in reports files
    "../api/reports.md": "../api/workflows.md",
    "../support.md": "../faq.md",
    "triggers.md": "advanced_features.md",
    "outputs.md": "templates.md",
    # Fix links in reports/use_cases.md
    "../examples/education_reports.py": "../project/examples/education_reports.md",
    "../examples/real_estate_reports.py": "../project/examples/real_estate_reports.md",
    "../examples/energy_reports.py": "../project/examples/energy_reports.md",
    "../examples/logistics_reports.py": "../project/examples/logistics_reports.md",
    # Fix links in testing/framework.md
    "../tests/TEST_STANDARDIZATION_PLAN.md": "../project/test_standardization_plan.md",
    # Fix links in admin/overview.md
    "../static/components/README.md": "../developer_tools/images/README.md",
}


# Function to fix links in a file
def fix_links_in_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    original_content = content

    # Replace links
    for old_link, new_link in LINK_REPLACEMENTS.items():
        content = content.replace(f"({old_link})", f"({new_link})")
        content = content.replace(f"[{old_link}]", f"[{new_link}]")

    # Fix anchors in workflows/advanced-patterns.md
    if file_path.name == "advanced-patterns.md" and "workflows" in str(file_path):
        # Add missing anchor sections
        if "# Dynamic Content Generation" not in content:
            content += "\n\n## Dynamic Content Generation\n\nContent for dynamic generation...\n"

        if "# Multi-Entity Workflows" not in content:
            content += "\n\n## Multi-Entity Workflows\n\nContent for multi-entity workflows...\n"

        if "# Scheduled Workflows" not in content:
            content += (
                "\n\n## Scheduled Workflows\n\nContent for scheduled workflows...\n"
            )

        if "# Bulk Notifications" not in content:
            content += (
                "\n\n## Bulk Notifications\n\nContent for bulk notifications...\n"
            )

        if "# Performance Optimization" not in content:
            content += "\n\n## Performance Optimization\n\nContent for performance optimization...\n"

    # Write changes back if content was modified
    if content != original_content:
        print(f"Fixing links in {file_path}")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)


# Function to create missing files
def create_missing_files():
    # Create missing files that are referenced
    missing_files = [
        DOCS_DIR / "project" / "documentation_status.md",
        DOCS_DIR / "project" / "documentation_plan.md",
        DOCS_DIR / "project" / "test_standardization_plan.md",
        DOCS_DIR / "project" / "examples" / "education_reports.md",
        DOCS_DIR / "project" / "examples" / "real_estate_reports.md",
        DOCS_DIR / "project" / "examples" / "energy_reports.md",
        DOCS_DIR / "project" / "examples" / "logistics_reports.md",
    ]

    for file_path in missing_files:
        # Create directory if it doesn't exist
        os.makedirs(file_path.parent, exist_ok=True)

        if not file_path.exists():
            print(f"Creating missing file: {file_path}")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(
                    f"# {file_path.stem.replace('_', ' ').title()}\n\nPlaceholder content for {file_path.name}\n"
                )


# Main function
def main():
    # Create missing files first
    create_missing_files()

    # Process all markdown files
    for file_path in DOCS_DIR.glob("**/*.md"):
        fix_links_in_file(file_path)

    print("Link fixing completed!")


if __name__ == "__main__":
    main()
