# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Static analyzer for Uno applications.

This module provides a static analyzer for Uno applications,
which checks for security issues in the code.
"""

import logging
import json
import os
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from uno.security.config import SecurityTestingConfig
from uno.security.testing.scanner import Vulnerability


class StaticAnalyzer:
    """
    Static analyzer for Uno applications.

    This class analyzes source code for security issues.
    """

    def __init__(
        self,
        config: SecurityTestingConfig,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the static analyzer.

        Args:
            config: Security testing configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.testing.static")

    def scan(self, target: str) -> list[Vulnerability]:
        """
        Scan source code for security issues.

        Args:
            target: Target to scan (file or directory)

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        # Scan Python code with Bandit
        vulnerabilities.extend(self._scan_python_code(target))

        # Scan JavaScript code with ESLint (if applicable)
        if self._has_javascript_files(target):
            vulnerabilities.extend(self._scan_javascript_code(target))

        return vulnerabilities

    def _scan_python_code(self, target: str) -> list[Vulnerability]:
        """
        Scan Python code with Bandit.

        Args:
            target: Target to scan

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        try:
            # Check if Bandit is installed
            try:
                subprocess.run(["bandit", "--version"], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.warning("Bandit not installed, trying to install it")
                subprocess.run(["pip", "install", "bandit"], check=True)

            # Run Bandit
            result = subprocess.run(
                ["bandit", "-r", "-f", "json", target],
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse the output
            if result.returncode != 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)

                    for result in data.get("results", []):
                        vuln_id = result.get("test_id", "")
                        severity = result.get("issue_severity", "").lower()
                        confidence = result.get("issue_confidence", "").lower()
                        file_path = result.get("filename", "")
                        line = result.get("line_number", 0)

                        vulnerabilities.append(
                            Vulnerability(
                                id=vuln_id,
                                title=result.get("test_name", "Security issue"),
                                description=result.get("issue_text", ""),
                                severity=severity,
                                scanner="bandit",
                                file_path=file_path,
                                line=line,
                                recommendation=f"Review the code at {file_path}:{line}",
                            )
                        )
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse Bandit output")
        except Exception as e:
            self.logger.error(f"Error running Bandit: {str(e)}")

        return vulnerabilities

    def _scan_javascript_code(self, target: str) -> list[Vulnerability]:
        """
        Scan JavaScript code with ESLint.

        Args:
            target: Target to scan

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        try:
            # Check if ESLint is installed
            try:
                subprocess.run(["eslint", "--version"], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.warning("ESLint not installed or not found in PATH")
                return vulnerabilities

            # Check if eslint-plugin-security is available
            eslintrc_path = os.path.join(target, ".eslintrc.js")
            if not os.path.exists(eslintrc_path):
                # Create a temporary ESLint config
                with open(eslintrc_path, "w") as f:
                    f.write(
                        """module.exports = {
  plugins: ['security'],
  extends: ['plugin:security/recommended'],
};
"""
                    )

            # Run ESLint
            result = subprocess.run(
                ["eslint", ".", "-f", "json"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse the output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)

                    for file_result in data:
                        file_path = file_result.get("filePath", "")
                        for message in file_result.get("messages", []):
                            rule_id = message.get("ruleId", "")

                            # Only include security-related rules
                            if rule_id.startswith("security/"):
                                severity_value = message.get("severity", 0)
                                severity = (
                                    "high"
                                    if severity_value == 2
                                    else "medium" if severity_value == 1 else "low"
                                )
                                line = message.get("line", 0)

                                vulnerabilities.append(
                                    Vulnerability(
                                        id=rule_id,
                                        title=f"JavaScript security issue: {rule_id}",
                                        description=message.get("message", ""),
                                        severity=severity,
                                        scanner="eslint",
                                        file_path=file_path,
                                        line=line,
                                        recommendation=f"Review the code at {file_path}:{line}",
                                    )
                                )
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse ESLint output")
        except Exception as e:
            self.logger.error(f"Error running ESLint: {str(e)}")

        return vulnerabilities

    def _has_javascript_files(self, target: str) -> bool:
        """
        Check if the target has JavaScript files.

        Args:
            target: Target to check

        Returns:
            True if the target has JavaScript files, False otherwise
        """
        if os.path.isfile(target):
            return (
                target.endswith(".js")
                or target.endswith(".jsx")
                or target.endswith(".ts")
                or target.endswith(".tsx")
            )

        for root, _, files in os.walk(target):
            for file in files:
                if (
                    file.endswith(".js")
                    or file.endswith(".jsx")
                    or file.endswith(".ts")
                    or file.endswith(".tsx")
                ):
                    return True

        return False
