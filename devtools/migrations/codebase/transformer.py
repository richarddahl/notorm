"""Code transformer for migration assistance.

This module provides tools for transforming Python code to
migrate APIs, patterns, and syntax to newer versions.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Pattern, Callable
import os
import re
import ast
import logging

# Use our local astor implementation
from uno.devtools.migrations.codebase import astor
from pathlib import Path
import importlib
import importlib.util
from dataclasses import dataclass, field

from uno.devtools.migrations.codebase.analyzer import CodeIssue, AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class TransformationResult:
    """Result of a code transformation."""

    file_path: Path
    original_content: str
    transformed_content: str
    issues_fixed: list[CodeIssue] = field(default_factory=list)
    issues_remaining: list[CodeIssue] = field(default_factory=list)
    success: bool = True
    error: str | None = None

    @property
    def has_changes(self) -> bool:
        """Check if the transformation resulted in any changes."""
        return self.original_content != self.transformed_content

    @property
    def diff(self) -> str:
        """Get a diff of the changes."""
        import difflib

        if not self.has_changes:
            return "No changes"

        original_lines = self.original_content.splitlines(True)
        transformed_lines = self.transformed_content.splitlines(True)

        diff = difflib.unified_diff(
            original_lines,
            transformed_lines,
            fromfile=f"{self.file_path}.orig",
            tofile=str(self.file_path),
            n=3,
        )

        return "".join(diff)


class CodeTransformer:
    """Transformer for Python code to migrate APIs and patterns."""

    def __init__(self):
        """Initialize the code transformer."""
        self.transformers = {
            "deprecated_apis": self._transform_deprecated_apis,
            "type_annotations": self._transform_type_annotations,
            "error_handling": self._transform_error_handling,
            "dependency_injection": self._transform_dependency_injection,
            "async_patterns": self._transform_async_patterns,
            "uno_api_changes": self._transform_uno_api_changes,
        }

    def transform_file(
        self,
        file_path: Union[str, Path],
        transformations: list[str] | None = None,
        analysis_result: Optional[AnalysisResult] = None,
        dry_run: bool = False,
    ) -> TransformationResult:
        """Transform a single Python file to fix migration issues.

        Args:
            file_path: Path to the Python file
            transformations: List of transformations to apply (default: all)
            analysis_result: Optional pre-computed analysis result
            dry_run: Whether to actually modify the file or just generate a diff

        Returns:
            Transformation results
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return TransformationResult(
                file_path=file_path,
                original_content="",
                transformed_content="",
                success=False,
                error=f"File not found: {file_path}",
            )

        if not file_path.suffix == ".py":
            return TransformationResult(
                file_path=file_path,
                original_content="",
                transformed_content="",
                success=False,
                error=f"Not a Python file: {file_path}",
            )

        # Read the file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Run analysis if not provided
            if analysis_result is None:
                from uno.devtools.migrations.codebase.analyzer import CodeAnalyzer

                analyzer = CodeAnalyzer()
                analysis_result = analyzer.analyze_file(file_path)

            # Filter issues for this file
            file_issues = [
                issue
                for issue in analysis_result.issues
                if issue.file_path == file_path
            ]

            # Apply transformations
            transformations_to_apply = transformations or list(self.transformers.keys())

            transformed_content = content
            fixed_issues = []

            for transformation in transformations_to_apply:
                if transformation in self.transformers:
                    transformer = self.transformers[transformation]

                    # Get issues for this transformation
                    issues = [
                        issue
                        for issue in file_issues
                        if issue.issue_type in transformation
                        or issue.issue_type == transformation
                    ]

                    # Apply transformation
                    try:
                        transformed_content, fixed = transformer(
                            transformed_content, issues, file_path
                        )
                        fixed_issues.extend(fixed)
                    except Exception as e:
                        logger.error(
                            f"Error applying transformation {transformation} to {file_path}: {e}"
                        )
                else:
                    logger.warning(f"Unknown transformation: {transformation}")

            # Determine remaining issues
            remaining_issues = [
                issue for issue in file_issues if issue not in fixed_issues
            ]

            # Write file if not dry run and there are changes
            if not dry_run and transformed_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(transformed_content)

            return TransformationResult(
                file_path=file_path,
                original_content=content,
                transformed_content=transformed_content,
                issues_fixed=fixed_issues,
                issues_remaining=remaining_issues,
            )

        except Exception as e:
            logger.error(f"Error transforming file {file_path}: {e}")
            return TransformationResult(
                file_path=file_path,
                original_content=content if "content" in locals() else "",
                transformed_content=content if "content" in locals() else "",
                success=False,
                error=str(e),
            )

    def transform_directory(
        self,
        directory: Union[str, Path],
        transformations: list[str] | None = None,
        include_pattern: str = "*.py",
        exclude_dirs: list[str] | None = None,
        dry_run: bool = False,
    ) -> list[TransformationResult]:
        """Transform all Python files in a directory.

        Args:
            directory: Path to the directory
            transformations: List of transformations to apply (default: all)
            include_pattern: Pattern for files to include
            exclude_dirs: List of directory names to exclude
            dry_run: Whether to actually modify files or just generate diffs

        Returns:
            List of transformation results
        """
        directory = Path(directory)
        results = []

        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory not found: {directory}")
            return results

        exclude_dirs = exclude_dirs or [
            "venv",
            ".venv",
            "env",
            ".env",
            ".git",
            "__pycache__",
        ]

        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        # Analyze all files first
        from uno.devtools.migrations.codebase.analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer()
        analysis_result = analyzer.analyze_directory(directory)

        # Transform each file
        for file_path in python_files:
            result = self.transform_file(
                file_path, transformations, analysis_result, dry_run
            )
            results.append(result)

        return results

    def _transform_deprecated_apis(
        self, content: str, issues: list[CodeIssue], file_path: Path
    ) -> Tuple[str, list[CodeIssue]]:
        """Transform deprecated APIs.

        This transforms imports and usages of deprecated modules, classes,
        and functions to their modern equivalents.
        """
        # Group issues by line number for efficient processing
        issues_by_line = {}
        for issue in issues:
            if issue.issue_type == "deprecated_import":
                issues_by_line.setdefault(issue.line_number, []).append(issue)

        if not issues_by_line:
            return content, []

        # Parse the content
        try:
            tree = ast.parse(content)

            class ImportTransformer(ast.NodeTransformer):
                def __init__(self, issues_by_line):
                    self.issues_by_line = issues_by_line
                    self.fixed_issues = []

                def visit_Import(self, node):
                    if node.lineno in self.issues_by_line:
                        # Found an issue on this line
                        issues = self.issues_by_line[node.lineno]

                        # Create a new list of import names
                        new_names = []
                        for name in node.names:
                            found = False
                            for issue in issues:
                                if name.name == issue.issue_type:
                                    # Replace with suggested import
                                    replacement = issue.suggestion.replace(
                                        "Replace with ", ""
                                    )
                                    new_names.append(
                                        ast.alias(name=replacement, asname=name.asname)
                                    )
                                    self.fixed_issues.append(issue)
                                    found = True
                                    break

                            if not found:
                                new_names.append(name)

                        # Create a new Import node if needed
                        if new_names:
                            node.names = new_names
                            return node
                        else:
                            return None

                    return node

                def visit_ImportFrom(self, node):
                    if node.lineno in self.issues_by_line:
                        # Found an issue on this line
                        issues = self.issues_by_line[node.lineno]

                        for issue in issues:
                            if node.module == issue.description.replace(
                                "The '", ""
                            ).replace("' module is deprecated", ""):
                                # Replace with suggested import
                                replacement = issue.suggestion.replace(
                                    "Replace with ", ""
                                )
                                new_node = ast.ImportFrom(
                                    module=replacement,
                                    names=node.names,
                                    level=node.level,
                                )
                                self.fixed_issues.append(issue)
                                return new_node

                    return node

            # Apply the transformer
            transformer = ImportTransformer(issues_by_line)
            new_tree = transformer.visit(tree)

            # Generate new code
            new_content = astor.to_source(new_tree)

            return new_content, transformer.fixed_issues

        except Exception as e:
            logger.error(f"Error transforming deprecated APIs in {file_path}: {e}")
            return content, []

    def _transform_type_annotations(
        self, content: str, issues: list[CodeIssue], file_path: Path
    ) -> Tuple[str, list[CodeIssue]]:
        """Transform type annotations.

        This adds missing type annotations and converts comment-style
        annotations to modern syntax.
        """
        # For simplicity, this implementation just handles old-style type annotations
        fixed_issues = []
        new_content = content

        for issue in issues:
            if issue.issue_type == "old_style_type_annotation":
                # Extract the type annotation from the comment
                line = issue.code_snippet
                match = re.search(r"#\s*type:\s*(.+)$", line)

                if match:
                    type_annotation = match.group(1).strip()

                    # Remove the comment and add proper annotation
                    if "def " in line:
                        # Function definition
                        new_line = line.split("#")[0].rstrip()
                        if "-> " not in new_line:
                            if new_line.endswith(":"):
                                new_line = new_line[:-1] + f" -> {type_annotation}:"
                            else:
                                new_line = new_line + f" -> {type_annotation}"

                        new_content = new_content.replace(line, new_line)
                        fixed_issues.append(issue)

        return new_content, fixed_issues

    def _transform_error_handling(
        self, content: str, issues: list[CodeIssue], file_path: Path
    ) -> Tuple[str, list[CodeIssue]]:
        """Transform error handling patterns.

        This fixes bare except blocks, improves exception re-raising,
        and addresses other error handling issues.
        """
        # For now, just handle bare excepts
        fixed_issues = []

        for issue in issues:
            if issue.issue_type == "bare_except":
                # Replace bare except with except Exception
                line = issue.code_snippet
                if "except:" in line:
                    new_line = line.replace("except:", "except Exception:")
                    new_content = content.replace(line, new_line)
                    content = new_content
                    fixed_issues.append(issue)

        return content, fixed_issues

    def _transform_dependency_injection(
        self, content: str, issues: list[CodeIssue], file_path: Path
    ) -> Tuple[str, list[CodeIssue]]:
        """Transform dependency injection patterns.

        This transforms service locator and global state patterns
        to use dependency injection.
        """
        # This is a complex transformation that would need
        # a deeper understanding of the codebase
        # For this example, we'll just add a note about DI
        fixed_issues = []

        # Add imports if needed
        if (
            "service_locator" in [i.issue_type for i in issues]
            and "import inject" not in content
        ):
            new_content = "import inject\n" + content
            content = new_content

        # The full implementation would analyze the class structure
        # and add proper constructor injection

        return content, fixed_issues

    def _transform_async_patterns(
        self, content: str, issues: list[CodeIssue], file_path: Path
    ) -> Tuple[str, list[CodeIssue]]:
        """Transform async patterns.

        This adds missing awaits, replaces blocking calls with async versions,
        and addresses other async pattern issues.
        """
        # For now, just handle missing awaits
        fixed_issues = []
        new_content = content

        for issue in issues:
            if issue.issue_type == "missing_await":
                line = issue.code_snippet
                func_name = issue.description.split("async function ")[1]

                # Add await before the function call
                # This is a simplified approach that may not handle all cases
                pattern = re.compile(rf"\b{func_name}\(")
                new_line = pattern.sub(f"await {func_name}(", line)

                new_content = new_content.replace(line, new_line)
                fixed_issues.append(issue)

        return new_content, fixed_issues

    def _transform_uno_api_changes(
        self, content: str, issues: list[CodeIssue], file_path: Path
    ) -> Tuple[str, list[CodeIssue]]:
        """Transform Uno API changes.

        This updates old Uno APIs to their modern equivalents.
        """
        fixed_issues = []
        new_content = content

        for issue in issues:
            if issue.issue_type == "api_change":
                # Get the old and new API names
                old_api = issue.description.split(" has been ")[0]
                new_api = issue.suggestion.replace("Use ", "").replace(" instead", "")

                # Replace in the content
                new_content = new_content.replace(old_api, new_api)
                fixed_issues.append(issue)

        return new_content, fixed_issues


def apply_transformations(
    directory_or_file: Union[str, Path],
    transformations: list[str] | None = None,
    dry_run: bool = True,
    output_format: str = "text",
) -> Union[list[TransformationResult], str]:
    """Apply code transformations to a file or directory.

    Args:
        directory_or_file: Path to the file or directory
        transformations: List of transformations to apply
        dry_run: Whether to actually modify files or just generate diffs
        output_format: Format for the output ('text', 'diff', or 'json')

    Returns:
        Transformation results or formatted output
    """
    path = Path(directory_or_file)
    transformer = CodeTransformer()

    if path.is_file():
        results = [transformer.transform_file(path, transformations, dry_run=dry_run)]
    elif path.is_dir():
        results = transformer.transform_directory(
            path, transformations, dry_run=dry_run
        )
    else:
        raise ValueError(f"Path does not exist: {path}")

    if output_format == "text":
        # Generate a text summary
        summary = []
        summary.append(f"Transformation Summary:")
        summary.append(f"  Files processed: {len(results)}")
        summary.append(f"  Files changed: {sum(1 for r in results if r.has_changes)}")
        summary.append(f"  Issues fixed: {sum(len(r.issues_fixed) for r in results)}")
        summary.append(
            f"  Issues remaining: {sum(len(r.issues_remaining) for r in results)}"
        )

        if not dry_run:
            summary.append(f"\nFiles have been modified.")
        else:
            summary.append(f"\nThis was a dry run. No files were modified.")

        return "\n".join(summary)

    elif output_format == "diff":
        # Generate diffs for all changed files
        diffs = []
        for result in results:
            if result.has_changes:
                diffs.append(f"--- {result.file_path} ---")
                diffs.append(result.diff)
                diffs.append("")

        if not diffs:
            return "No changes"

        return "\n".join(diffs)

    elif output_format == "json":
        import json

        # Convert to serializable format
        data = []
        for result in results:
            result_dict = {
                "file_path": str(result.file_path),
                "has_changes": result.has_changes,
                "issues_fixed": len(result.issues_fixed),
                "issues_remaining": len(result.issues_remaining),
                "success": result.success,
            }

            if not result.success:
                result_dict["error"] = result.error

            data.append(result_dict)

        return json.dumps(data, indent=2)

    return results
