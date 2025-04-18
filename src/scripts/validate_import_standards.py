#!/usr/bin/env python3
"""
Script to validate adherence to Uno framework import standards and identify legacy code.

This script scans the codebase for:
1. Usage of legacy class names that should be replaced with Base-prefixed versions
2. Imports from deprecated modules that should use the standardized paths
3. Files that may still contain backward compatibility layers

Usage:
    python -m src.scripts.validate_import_standards

Returns:
    A report of violations and suggestions for fixing them
"""

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ImportViolation:
    """Represents a violation of import standards."""

    file_path: str
    line_number: int
    line: str
    violation_type: str
    suggestion: str


class ImportStandardsValidator:
    """Validates import standards in the Uno framework codebase."""

    LEGACY_CLASS_PATTERNS = [
        (r"\bUnoModel\b", "BaseModel", "uno.domain.base.model"),
        (r"\bUnoRepository\b", "BaseRepository", "uno.core.base.repository"),
        (r"\bUnoService\b", "BaseService", "uno.core.base.service"),
        (r"\bBaseDTO\b", "BaseDTO", "uno.core.base.dto"),
        (r"\bUnoError\b", "BaseError", "uno.core.base.error"),
    ]

    DEPRECATED_IMPORT_PATTERNS = [
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
    ]

    BACKWARD_COMPAT_PATTERNS = [
        r"# For backward compatibility",
        r"# Legacy alias",
        r"# Deprecated",
        r"DeprecationWarning",
        r"warnings\.warn\(",
    ]

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.violations: List[ImportViolation] = []

    def validate_file(self, file_path: Path) -> None:
        """Validate a single file for import standard violations."""
        if not file_path.is_file() or file_path.suffix != ".py":
            return

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        rel_path = file_path.relative_to(self.base_dir)

        for i, line in enumerate(lines, 1):
            # Check for legacy class patterns
            for pattern, replacement, import_path in self.LEGACY_CLASS_PATTERNS:
                if re.search(pattern, line):
                    # Skip if the line is defining the alias itself
                    clean_pattern = pattern.replace("\\b", "")
                    alias_pattern = f"{replacement} = {clean_pattern}"
                    if re.search(alias_pattern, line):
                        continue

                    # Skip if it's in a comment
                    if line.strip().startswith("#"):
                        continue

                    suggestion = (
                        f"Replace with {replacement} and import from {import_path}"
                    )
                    self.violations.append(
                        ImportViolation(
                            file_path=str(rel_path),
                            line_number=i,
                            line=line.strip(),
                            violation_type="Legacy Class Name",
                            suggestion=suggestion,
                        )
                    )

            # Check for deprecated import patterns
            for pattern, replacement in self.DEPRECATED_IMPORT_PATTERNS:
                if re.search(pattern, line):
                    # Skip if it's in a comment
                    if line.strip().startswith("#"):
                        continue

                    suggestion = f"Use {replacement}"
                    self.violations.append(
                        ImportViolation(
                            file_path=str(rel_path),
                            line_number=i,
                            line=line.strip(),
                            violation_type="Deprecated Import",
                            suggestion=suggestion,
                        )
                    )

            # Check for backward compatibility layers
            for pattern in self.BACKWARD_COMPAT_PATTERNS:
                if re.search(pattern, line):
                    # Skip certain specific cases
                    if "validate_import_standards.py" in str(file_path):
                        continue

                    suggestion = (
                        "Potential backward compatibility layer - consider removing"
                    )
                    self.violations.append(
                        ImportViolation(
                            file_path=str(rel_path),
                            line_number=i,
                            line=line.strip(),
                            violation_type="Backward Compatibility",
                            suggestion=suggestion,
                        )
                    )

    def validate_directory(self, directory: Optional[Path] = None) -> None:
        """Recursively validate all files in a directory."""
        directory = directory or self.base_dir / "src" / "uno"

        if not directory.exists():
            print(f"Directory not found: {directory}")
            return

        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".py":
                self.validate_file(item)
            elif item.is_dir() and not item.name.startswith("."):
                self.validate_directory(item)

    def generate_report(self) -> str:
        """Generate a readable report of all violations."""
        if not self.violations:
            return "No violations found! The codebase follows the import standards."

        report = ["# Import Standards Validation Report", ""]

        # Group by file path for better organization
        violations_by_file: Dict[str, List[ImportViolation]] = {}
        for violation in self.violations:
            if violation.file_path not in violations_by_file:
                violations_by_file[violation.file_path] = []
            violations_by_file[violation.file_path].append(violation)

        # Sort files by violation count (most violations first)
        sorted_files = sorted(
            violations_by_file.items(), key=lambda x: len(x[1]), reverse=True
        )

        # Add summary
        total_violations = len(self.violations)
        total_files = len(violations_by_file)
        report.append(
            f"Found {total_violations} violations across {total_files} files.\n"
        )

        # Add list of files with violation counts
        report.append("## Files with violations (sorted by count):")
        for file_path, file_violations in sorted_files:
            report.append(f"- {file_path}: {len(file_violations)} violations")
        report.append("")

        # Add detailed report for each file
        report.append("## Detailed Report")
        for file_path, file_violations in sorted_files:
            report.append(f"\n### {file_path}")

            # Group by violation type for better organization
            by_type: Dict[str, List[ImportViolation]] = {}
            for v in file_violations:
                if v.violation_type not in by_type:
                    by_type[v.violation_type] = []
                by_type[v.violation_type].append(v)

            for violation_type, violations in by_type.items():
                report.append(f"\n#### {violation_type} ({len(violations)})")
                for v in violations:
                    report.append(f"- Line {v.line_number}: `{v.line}`")
                    report.append(f"  - Suggestion: {v.suggestion}")

        return "\n".join(report)

    def generate_fix_guide(self) -> str:
        """Generate a guide with specific changes to fix violations."""
        if not self.violations:
            return "No fixes needed! The codebase follows the import standards."

        guide = ["# Import Standards Fix Guide", ""]

        # Group by file path
        violations_by_file: Dict[str, List[ImportViolation]] = {}
        for violation in self.violations:
            if violation.file_path not in violations_by_file:
                violations_by_file[violation.file_path] = []
            violations_by_file[violation.file_path].append(violation)

        # Sort files alphabetically
        sorted_files = sorted(violations_by_file.items(), key=lambda x: x[0])

        # Add summary
        total_violations = len(self.violations)
        total_files = len(violations_by_file)
        guide.append(
            f"This guide provides specific fixes for {total_violations} violations across {total_files} files.\n"
        )

        # Generate fixes for each file
        for file_path, file_violations in sorted_files:
            guide.append(f"## {file_path}")

            # Sort violations by line number (ascending)
            sorted_violations = sorted(file_violations, key=lambda v: v.line_number)

            # Group consecutive violations for the same pattern
            i = 0
            while i < len(sorted_violations):
                current = sorted_violations[i]

                # If it's a Legacy Class Name, recommend also adding the import
                if current.violation_type == "Legacy Class Name":
                    pattern = None
                    for p, replacement, import_path in self.LEGACY_CLASS_PATTERNS:
                        if re.search(p, current.line):
                            pattern = p.replace("\\b", "")
                            guide.append(f"\n### Replace {pattern} with {replacement}")
                            guide.append(
                                f"1. Add import: `from {import_path} import {replacement}`"
                            )
                            guide.append(
                                f"2. Replace all occurrences of `{pattern}` with `{replacement}`"
                            )
                            break

                # If it's a Deprecated Import, provide the specific change
                elif current.violation_type == "Deprecated Import":
                    guide.append(f"\n### Fix import on line {current.line_number}")
                    guide.append(f"Change from:")
                    guide.append(f"```python\n{current.line}\n```")

                    # Extract the target pattern and replacement
                    for pattern, replacement in self.DEPRECATED_IMPORT_PATTERNS:
                        if re.search(pattern, current.line):
                            # Create the replacement by substituting the pattern
                            new_import = re.sub(pattern, replacement, current.line)
                            guide.append(f"To:")
                            guide.append(f"```python\n{new_import}\n```")
                            break

                # If it's a Backward Compatibility layer, provide context
                elif current.violation_type == "Backward Compatibility":
                    guide.append(
                        f"\n### Evaluate backward compatibility on line {current.line_number}"
                    )
                    guide.append(f"Code: `{current.line}`")
                    guide.append(
                        "If this is a backward compatibility layer, consider removing it completely if not needed."
                    )
                    guide.append(
                        "If this is a deprecation warning, ensure it directs users to the correct standardized imports."
                    )

                i += 1

            guide.append("\n---\n")

        return "\n".join(guide)

    def run(self) -> Tuple[str, str]:
        """Run the validation and return reports."""
        self.validate_directory()
        return self.generate_report(), self.generate_fix_guide()


def main():
    base_dir = Path(__file__).parent.parent.parent
    validator = ImportStandardsValidator(base_dir)
    report, fix_guide = validator.run()

    # Create reports directory if it doesn't exist
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Write reports to files
    with open(reports_dir / "import_validation_report.md", "w") as f:
        f.write(report)

    with open(reports_dir / "import_fix_guide.md", "w") as f:
        f.write(fix_guide)

    print(
        f"Reports written to:\n{reports_dir / 'import_validation_report.md'}\n{reports_dir / 'import_fix_guide.md'}"
    )
    print("\nSummary:")

    # Print just the summary section of the report
    summary_lines = []
    in_summary = False
    for line in report.split("\n"):
        if line.startswith("Found "):
            in_summary = True
            summary_lines.append(line)
        elif in_summary and line.startswith("## Files with violations"):
            # Continue printing the file list
            summary_lines.append(line)
        elif in_summary and line.startswith("## Detailed Report"):
            in_summary = False
        elif in_summary:
            summary_lines.append(line)

    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
