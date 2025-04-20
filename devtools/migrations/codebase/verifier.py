"""Transformation verifier for migration assistance.

This module provides tools for verifying that code transformations
have been applied correctly and don't introduce new issues.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
import os
import re
import ast
import logging
import importlib
import subprocess
from pathlib import Path
from dataclasses import dataclass, field

from uno.devtools.migrations.codebase.analyzer import CodeIssue, AnalysisResult
from uno.devtools.migrations.codebase.transformer import TransformationResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of a code transformation verification."""

    file_path: Path
    syntax_valid: bool
    tests_pass: bool
    lint_pass: bool
    issues_introduced: list[CodeIssue] = field(default_factory=list)
    success: bool = True
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        """Check if the transformed code is valid."""
        return (
            self.syntax_valid
            and self.tests_pass
            and self.lint_pass
            and not self.issues_introduced
        )


class TransformationVerifier:
    """Verifier for code transformations."""

    def __init__(
        self,
        run_syntax_check: bool = True,
        run_tests: bool = False,
        run_lint: bool = False,
        check_new_issues: bool = True,
    ):
        """Initialize the transformation verifier.

        Args:
            run_syntax_check: Whether to check syntax validity
            run_tests: Whether to run tests for modified files
            run_lint: Whether to run linters on modified files
            check_new_issues: Whether to check for newly introduced issues
        """
        self.run_syntax_check = run_syntax_check
        self.run_tests = run_tests
        self.run_lint = run_lint
        self.check_new_issues = check_new_issues

    def verify_transformation(
        self,
        transformation_result: TransformationResult,
        test_command: str | None = None,
        lint_command: str | None = None,
        original_analysis: Optional[AnalysisResult] = None,
    ) -> VerificationResult:
        """Verify a code transformation.

        Args:
            transformation_result: Result of a code transformation
            test_command: Command to run tests (default: pytest {file_path})
            lint_command: Command to run linters (default: flake8 {file_path})
            original_analysis: Optional pre-computed analysis of original code

        Returns:
            Verification result
        """
        file_path = transformation_result.file_path

        # Initialize result
        result = VerificationResult(
            file_path=file_path, syntax_valid=True, tests_pass=True, lint_pass=True
        )

        # Skip verification if transformation failed
        if not transformation_result.success:
            result.success = False
            result.error = f"Transformation failed: {transformation_result.error}"
            return result

        # Skip verification if no changes were made
        if not transformation_result.has_changes:
            return result

        # Check syntax validity
        if self.run_syntax_check:
            try:
                ast.parse(transformation_result.transformed_content)
            except SyntaxError as e:
                result.syntax_valid = False
                result.success = False
                result.error = f"Syntax error: {e}"
                return result

        # Check for newly introduced issues
        if self.check_new_issues and original_analysis is not None:
            from uno.devtools.migrations.codebase.analyzer import CodeAnalyzer

            # Create a temporary file with the transformed content
            temp_file = file_path.with_suffix(".transformed.py")
            try:
                with open(temp_file, "w") as f:
                    f.write(transformation_result.transformed_content)

                # Analyze the transformed code
                analyzer = CodeAnalyzer()
                new_analysis = analyzer.analyze_file(temp_file)

                # Get issues from the original code
                original_issues = [
                    issue
                    for issue in original_analysis.issues
                    if issue.file_path == file_path
                ]

                # Get issues from the transformed code
                new_issues = [
                    issue
                    for issue in new_analysis.issues
                    if issue.file_path == temp_file
                ]

                # Find issues that were introduced by the transformation
                # (i.e., issues in the transformed code that weren't in the original)
                original_issue_types = {
                    (issue.issue_type, issue.line_number) for issue in original_issues
                }

                for issue in new_issues:
                    if (
                        issue.issue_type,
                        issue.line_number,
                    ) not in original_issue_types:
                        # This is a new issue introduced by the transformation
                        # Update the file path to point to the original file
                        issue.file_path = file_path
                        result.issues_introduced.append(issue)

            finally:
                # Clean up the temporary file
                if temp_file.exists():
                    temp_file.unlink()

        # Run tests if requested
        if self.run_tests and test_command:
            try:
                # Substitute file path in the command
                cmd = test_command.format(file_path=file_path)

                # Run the command
                process = subprocess.run(
                    cmd,
                    shell=True,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                if process.returncode != 0:
                    result.tests_pass = False
                    result.error = f"Tests failed: {process.stderr}"

            except Exception as e:
                result.tests_pass = False
                result.error = f"Error running tests: {e}"

        # Run linter if requested
        if self.run_lint and lint_command:
            try:
                # Substitute file path in the command
                cmd = lint_command.format(file_path=file_path)

                # Run the command
                process = subprocess.run(
                    cmd,
                    shell=True,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                if process.returncode != 0:
                    result.lint_pass = False
                    result.error = f"Lint failed: {process.stdout or process.stderr}"

            except Exception as e:
                result.lint_pass = False
                result.error = f"Error running linter: {e}"

        # Update success flag
        result.success = result.syntax_valid and result.tests_pass and result.lint_pass

        return result

    def verify_transformations(
        self,
        transformation_results: list[TransformationResult],
        test_command: str | None = None,
        lint_command: str | None = None,
        analysis_results: Optional[AnalysisResult] = None,
        fail_fast: bool = False,
    ) -> list[VerificationResult]:
        """Verify multiple code transformations.

        Args:
            transformation_results: Results of code transformations
            test_command: Command to run tests (default: pytest {file_path})
            lint_command: Command to run linters (default: flake8 {file_path})
            analysis_results: Optional pre-computed analysis of original code
            fail_fast: Whether to stop on the first failure

        Returns:
            List of verification results
        """
        results = []

        for transformation_result in transformation_results:
            result = self.verify_transformation(
                transformation_result, test_command, lint_command, analysis_results
            )

            results.append(result)

            if fail_fast and not result.success:
                break

        return results

    def generate_verification_report(
        self, verification_results: list[VerificationResult], format: str = "text"
    ) -> str:
        """Generate a report of verification results.

        Args:
            verification_results: List of verification results
            format: Format of the report ('text', 'markdown', or 'json')

        Returns:
            Verification report
        """
        if format == "text":
            # Generate a text summary
            summary = []
            summary.append(f"Verification Summary:")
            summary.append(f"  Files processed: {len(verification_results)}")
            summary.append(
                f"  Files valid: {sum(1 for r in verification_results if r.is_valid)}"
            )
            summary.append(
                f"  Files with syntax errors: {sum(1 for r in verification_results if not r.syntax_valid)}"
            )
            summary.append(
                f"  Files with test failures: {sum(1 for r in verification_results if not r.tests_pass)}"
            )
            summary.append(
                f"  Files with lint errors: {sum(1 for r in verification_results if not r.lint_pass)}"
            )
            summary.append(
                f"  Files with new issues: {sum(1 for r in verification_results if r.issues_introduced)}"
            )

            # Add details for files with errors
            invalid_results = [r for r in verification_results if not r.is_valid]
            if invalid_results:
                summary.append("\nFiles with issues:")

                for result in invalid_results:
                    summary.append(f"  {result.file_path}:")

                    if not result.syntax_valid:
                        summary.append(f"    - Syntax error: {result.error}")

                    if not result.tests_pass:
                        summary.append(f"    - Test failures")

                    if not result.lint_pass:
                        summary.append(f"    - Lint errors")

                    if result.issues_introduced:
                        summary.append(
                            f"    - New issues introduced: {len(result.issues_introduced)}"
                        )
                        for issue in result.issues_introduced:
                            summary.append(
                                f"      - Line {issue.line_number}: {issue.description}"
                            )

            return "\n".join(summary)

        elif format == "markdown":
            # Generate a markdown report
            lines = ["# Verification Report", "", "## Summary", ""]

            lines.append(f"- **Files processed:** {len(verification_results)}")
            lines.append(
                f"- **Files valid:** {sum(1 for r in verification_results if r.is_valid)}"
            )
            lines.append(
                f"- **Files with syntax errors:** {sum(1 for r in verification_results if not r.syntax_valid)}"
            )
            lines.append(
                f"- **Files with test failures:** {sum(1 for r in verification_results if not r.tests_pass)}"
            )
            lines.append(
                f"- **Files with lint errors:** {sum(1 for r in verification_results if not r.lint_pass)}"
            )
            lines.append(
                f"- **Files with new issues:** {sum(1 for r in verification_results if r.issues_introduced)}"
            )

            # Add details for files with errors
            invalid_results = [r for r in verification_results if not r.is_valid]
            if invalid_results:
                lines.append("\n## Files with Issues\n")

                for result in invalid_results:
                    lines.append(f"### {result.file_path}")

                    if not result.syntax_valid:
                        lines.append(f"- **Syntax error:** {result.error}")

                    if not result.tests_pass:
                        lines.append(f"- **Test failures**")

                    if not result.lint_pass:
                        lines.append(f"- **Lint errors**")

                    if result.issues_introduced:
                        lines.append(
                            f"- **New issues introduced:** {len(result.issues_introduced)}"
                        )
                        lines.append(
                            "  - "
                            + "\n  - ".join(
                                f"Line {issue.line_number}: {issue.description}"
                                for issue in result.issues_introduced
                            )
                        )

                    lines.append("")

            return "\n".join(lines)

        elif format == "json":
            import json

            # Convert to serializable format
            data = []
            for result in verification_results:
                result_dict = {
                    "file_path": str(result.file_path),
                    "valid": result.is_valid,
                    "syntax_valid": result.syntax_valid,
                    "tests_pass": result.tests_pass,
                    "lint_pass": result.lint_pass,
                    "success": result.success,
                    "issues_introduced": len(result.issues_introduced),
                }

                if result.error:
                    result_dict["error"] = result.error

                if result.issues_introduced:
                    result_dict["new_issues"] = [
                        {
                            "line": issue.line_number,
                            "type": issue.issue_type,
                            "description": issue.description,
                            "suggestion": issue.suggestion,
                        }
                        for issue in result.issues_introduced
                    ]

                data.append(result_dict)

            return json.dumps(data, indent=2)

        return f"Unknown format: {format}"


def verify_transformations(
    transformation_results: list[TransformationResult],
    run_syntax_check: bool = True,
    run_tests: bool = False,
    run_lint: bool = False,
    check_new_issues: bool = True,
    test_command: str | None = None,
    lint_command: str | None = None,
    output_format: str = "text",
    fail_fast: bool = False,
) -> Union[list[VerificationResult], str]:
    """Verify multiple code transformations.

    Args:
        transformation_results: Results of code transformations
        run_syntax_check: Whether to check syntax validity
        run_tests: Whether to run tests for modified files
        run_lint: Whether to run linters on modified files
        check_new_issues: Whether to check for newly introduced issues
        test_command: Command to run tests (default: pytest {file_path})
        lint_command: Command to run linters (default: flake8 {file_path})
        output_format: Format for the output ('text', 'markdown', or 'json')
        fail_fast: Whether to stop on the first failure

    Returns:
        Verification results or formatted output
    """
    verifier = TransformationVerifier(
        run_syntax_check=run_syntax_check,
        run_tests=run_tests,
        run_lint=run_lint,
        check_new_issues=check_new_issues,
    )

    results = verifier.verify_transformations(
        transformation_results, test_command, lint_command, fail_fast=fail_fast
    )

    if output_format in ["text", "markdown", "json"]:
        return verifier.generate_verification_report(results, output_format)

    return results
