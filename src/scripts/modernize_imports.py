#!/usr/bin/env python3
"""
Script to modernize imports in the Uno framework codebase.

This script automatically updates:
1. Legacy class names to their Base-prefixed versions
2. Deprecated module imports to the standardized paths
3. Optionally removes backward compatibility layers

Usage:
    python -m src.scripts.modernize_imports [--remove-compat] [--path=PATH]

Options:
    --remove-compat    Also remove backward compatibility layers (use with caution)
    --path=PATH        Process only files in the specified path (relative to project root)
    --dry-run          Show changes without applying them
    --auto-fix         Apply all changes without confirmation (use with caution)

Example:
    python -m src.scripts.modernize_imports --path=src/uno/api
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ImportModernizer:
    """Tool to modernize imports in the Uno framework codebase."""

    # Mapping of legacy class names to their modern replacements with import paths
    LEGACY_CLASS_REPLACEMENTS = [
        # (legacy_pattern, replacement, import_path)
        (r"\bUnoModel\b", "BaseModel", "uno.domain.base.model"),
        (r"\bUnoRepository\b", "BaseRepository", "uno.core.base.repository"),
        (r"\bUnoService\b", "BaseService", "uno.core.base.service"),
        (r"\bBaseDTO\b", "BaseDTO", "uno.core.base.dto"),
        (r"\bUnoError\b", "BaseError", "uno.core.base.error"),
        (r"\bRepositoryResults\b", "RepositoryResult", "uno.core.base.repository"),
    ]

    # Mapping of deprecated import patterns to their modern replacements
    DEPRECATED_IMPORT_REPLACEMENTS = [
        # (deprecated_pattern, replacement)
        (r"from uno\.model import", "from uno.domain.base.model import"),
        (r"from uno\.repository import", "from uno.core.base.repository import"),
        (r"from uno\.service import", "from uno.core.base.service import"),
        (r"from uno\.dto\.schema import", "from uno.core.base.dto import"),
        (r"from uno\.errors import", "from uno.core.base.error import"),
        (r"from uno\.async_manager import", "from uno.core.async.task_manager import"),
        (
            r"from uno\.core\.async_manager import",
            "from uno.core.async.task_manager import",
        ),
        (r"from uno\.dataloader import", "from uno.core.async.helpers import"),
        (r"from uno\.core\.dataloader import", "from uno.core.async.helpers import"),
        (
            r"from uno\.domain\.repository import",
            "from uno.core.base.repository import",
        ),
        (
            r"from uno\.domain\.repository_results import",
            "from uno.core.base.repository import",
        ),
        (
            r"import uno\.domain\.repository_results",
            "from uno.core.base.repository import RepositoryResult",
        ),
    ]

    # Patterns that identify backward compatibility layers
    BACKWARD_COMPAT_PATTERNS = [
        r"# For backward compatibility",
        r"# Legacy alias",
        r"# Deprecated",
        r"# Aliases for backward compatibility",
        r"# Legacy imports",
    ]

    def __init__(
        self,
        base_dir: str,
        remove_compat: bool = False,
        dry_run: bool = False,
        auto_fix: bool = False,
    ):
        self.base_dir = Path(base_dir)
        self.remove_compat = remove_compat
        self.dry_run = dry_run
        self.auto_fix = auto_fix
        self.files_processed = 0
        self.files_modified = 0
        self.import_lines_added = []

    def process_file(self, file_path: Path) -> bool:
        """Process a single file to modernize imports and class names."""
        if not file_path.is_file() or file_path.suffix != ".py":
            return False

        self.files_processed += 1
        rel_path = file_path.relative_to(self.base_dir)
        print(f"Processing: {rel_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        modified_content = original_content
        needs_imports = set()

        # Replace legacy class names
        for pattern, replacement, import_path in self.LEGACY_CLASS_REPLACEMENTS:
            if re.search(pattern, modified_content):
                # Skip replacements in alias definitions or comments
                lines = modified_content.split("\n")
                clean_pattern = pattern.replace("\\b", "")

                # First scan to find imports needed
                for i, line in enumerate(lines):
                    # Skip if the line is a comment
                    if line.strip().startswith("#"):
                        continue

                    # Skip if it's an alias definition like "BaseModel = BaseModel"
                    if re.search(f"{clean_pattern} = {replacement}", line):
                        continue

                    # Skip if it's a backward compatibility line like "BaseModel = BaseModel"
                    if re.search(f"{replacement} = {clean_pattern}", line):
                        continue

                    # If it contains the pattern and isn't one of the above, we need the import
                    if re.search(pattern, line):
                        print(f"  Found legacy class: {clean_pattern} on line {i+1}")
                        needs_imports.add((replacement, import_path))

                # Do the actual replacement, preserving alias definitions and comments
                lines = modified_content.split("\n")
                for i, line in enumerate(lines):
                    # Skip if the line is a comment
                    if line.strip().startswith("#"):
                        continue

                    # Skip if it's an alias definition in either direction
                    if re.search(f"{clean_pattern} = {replacement}", line) or re.search(
                        f"{replacement} = {clean_pattern}", line
                    ):
                        continue

                    # Replace the pattern otherwise
                    if re.search(pattern, line):
                        lines[i] = re.sub(pattern, replacement, line)
                modified_content = "\n".join(lines)

        # Replace deprecated imports
        for pattern, replacement in self.DEPRECATED_IMPORT_REPLACEMENTS:
            if re.search(pattern, modified_content):
                print(f"  Found deprecated import: {pattern}")
                modified_content = re.sub(pattern, replacement, modified_content)

        # Add needed imports if we have replacements
        if needs_imports and modified_content != original_content:
            import_statements = []
            for class_name, import_path in needs_imports:
                import_statement = f"from {import_path} import {class_name}"
                if import_statement not in modified_content:
                    import_statements.append(import_statement)

            if import_statements:
                # Find the best place to add imports (after existing imports)
                lines = modified_content.split("\n")

                # Find the last import statement position
                last_import_pos = 0
                for i, line in enumerate(lines):
                    if re.match(r"^import |^from ", line):
                        last_import_pos = i

                # Add the new imports after the last import, or at the top if no imports
                insert_pos = last_import_pos + 1 if last_import_pos > 0 else 0

                # If there are docstrings, make sure we insert after them
                for i, line in enumerate(lines):
                    if i <= insert_pos:
                        if re.match(r'^"""', line) or re.match(r"^'''", line):
                            # Find the end of the docstring
                            for j in range(i + 1, len(lines)):
                                if re.search(r'"""$', lines[j]) or re.search(
                                    r"'''$", lines[j]
                                ):
                                    insert_pos = j + 1
                                    break

                # Insert the new imports
                for import_statement in import_statements:
                    print(f"  Adding import: {import_statement}")
                    self.import_lines_added.append(import_statement)
                    lines.insert(insert_pos, import_statement)
                    insert_pos += 1

                modified_content = "\n".join(lines)

        # Remove backward compatibility layers if requested
        if self.remove_compat:
            lines = modified_content.split("\n")
            filtered_lines = []
            i = 0

            while i < len(lines):
                line = lines[i]
                skip_line = False

                # Check if the line contains a backward compatibility pattern
                for pattern in self.BACKWARD_COMPAT_PATTERNS:
                    if re.search(pattern, line):
                        print(f"  Found backward compatibility layer: {line.strip()}")
                        skip_line = True

                        # If the line is an alias assignment, skip it
                        if re.match(r"^[A-Za-z0-9_]+ = [A-Za-z0-9_]+", line.strip()):
                            print(f"    Removing alias: {line.strip()}")
                            i += 1
                            continue

                        # If the next line is an alias assignment, skip both
                        if i + 1 < len(lines) and re.match(
                            r"^[A-Za-z0-9_]+ = [A-Za-z0-9_]+", lines[i + 1].strip()
                        ):
                            print(
                                f"    Removing alias with comment: {lines[i+1].strip()}"
                            )
                            i += 2
                            continue

                if not skip_line:
                    filtered_lines.append(line)

                i += 1

            modified_content = "\n".join(filtered_lines)

        # Write the changes if there are any
        if modified_content != original_content:
            print(f"  Changes needed for {rel_path}")

            if self.dry_run:
                print("  Dry run - no changes applied")
                return True

            if not self.auto_fix:
                response = input("  Apply changes? (y/n): ").strip().lower()
                if response != "y":
                    print("  Changes skipped")
                    return False

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)

            self.files_modified += 1
            print(f"  Updated {rel_path}")
            return True

        return False

    def process_directory(self, directory: Optional[Path] = None) -> None:
        """Recursively process all files in a directory."""
        directory = directory or self.base_dir / "src" / "uno"

        if not directory.exists():
            print(f"Directory not found: {directory}")
            return

        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".py":
                self.process_file(item)
            elif (
                item.is_dir()
                and not item.name.startswith(".")
                and item.name != "__pycache__"
            ):
                self.process_directory(item)

    def run(self, path: Optional[str] = None) -> None:
        """Run the modernizer."""
        if path:
            target_path = self.base_dir / path
            if target_path.is_file():
                self.process_file(target_path)
            elif target_path.is_dir():
                self.process_directory(target_path)
            else:
                print(f"Path not found: {target_path}")
                return
        else:
            self.process_directory()

        # Print summary
        mode = "dry run" if self.dry_run else "modernization"
        print(f"\nImport {mode} summary:")
        print(f"Files processed: {self.files_processed}")
        print(f"Files with changes: {self.files_modified}")

        if self.import_lines_added:
            print("\nNew imports added:")
            for import_line in sorted(set(self.import_lines_added)):
                print(f"  {import_line}")


def main():
    parser = argparse.ArgumentParser(
        description="Modernize imports in the Uno framework"
    )
    parser.add_argument(
        "--remove-compat",
        action="store_true",
        help="Remove backward compatibility layers",
    )
    parser.add_argument("--path", help="Process only files in the specified path")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying them"
    )
    parser.add_argument(
        "--auto-fix", action="store_true", help="Apply all changes without confirmation"
    )

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent
    modernizer = ImportModernizer(
        base_dir,
        remove_compat=args.remove_compat,
        dry_run=args.dry_run,
        auto_fix=args.auto_fix,
    )

    modernizer.run(args.path)


if __name__ == "__main__":
    main()
