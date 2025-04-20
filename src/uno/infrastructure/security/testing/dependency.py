# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Dependency scanner for Uno applications.

This module provides a dependency scanner for Uno applications,
which checks for known vulnerabilities in dependencies.
"""

import logging
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from uno.security.config import SecurityTestingConfig
from uno.security.testing.scanner import Vulnerability


class DependencyScanner:
    """
    Dependency scanner for Uno applications.

    This class scans dependencies for known vulnerabilities.
    """

    def __init__(
        self,
        config: SecurityTestingConfig,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the dependency scanner.

        Args:
            config: Security testing configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.testing.dependency")

    def scan(self, target: str) -> list[Vulnerability]:
        """
        Scan dependencies for known vulnerabilities.

        Args:
            target: Target to scan (file or directory)

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        # Scan Python dependencies with Safety
        vulnerabilities.extend(self._scan_python_dependencies(target))

        # Scan JavaScript dependencies (if applicable)
        if os.path.exists(os.path.join(target, "package.json")):
            vulnerabilities.extend(self._scan_javascript_dependencies(target))

        return vulnerabilities

    def _scan_python_dependencies(self, target: str) -> list[Vulnerability]:
        """
        Scan Python dependencies with Safety.

        Args:
            target: Target to scan

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        try:
            # Check if Safety is installed
            try:
                subprocess.run(["safety", "--version"], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.warning("Safety not installed, trying to install it")
                subprocess.run(["pip", "install", "safety"], check=True)

            # Run Safety
            result = subprocess.run(
                ["safety", "check", "--json", "-r", "requirements.txt"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse the output
            if result.returncode != 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for vuln in data:
                        package = vuln[0]
                        installed_version = vuln[2]
                        vulnerability_id = vuln[4]
                        description = vuln[3]

                        vulnerabilities.append(
                            Vulnerability(
                                id=vulnerability_id,
                                title=f"Vulnerable dependency: {package} {installed_version}",
                                description=description,
                                severity="high",  # Safety doesn't provide severity
                                scanner="safety",
                                file_path="requirements.txt",
                                recommendation=f"Update {package} to a non-vulnerable version",
                            )
                        )
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse Safety output")
        except Exception as e:
            self.logger.error(f"Error running Safety: {str(e)}")

        return vulnerabilities

    def _scan_javascript_dependencies(self, target: str) -> list[Vulnerability]:
        """
        Scan JavaScript dependencies with npm audit.

        Args:
            target: Target to scan

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        try:
            # Run npm audit
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse the output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)

                    if "vulnerabilities" in data:
                        for vuln_name, vuln_data in data["vulnerabilities"].items():
                            severity = vuln_data.get("severity", "").lower()
                            via = vuln_data.get("via", [])

                            # Get the vulnerability details
                            if isinstance(via, list) and via:
                                if isinstance(via[0], dict):
                                    vuln_id = via[0].get("url", "").split("/")[-1]
                                    vuln_title = via[0].get(
                                        "title", f"Vulnerability in {vuln_name}"
                                    )
                                    vuln_description = via[0].get(
                                        "description", "No description available"
                                    )
                                else:
                                    vuln_id = vuln_name
                                    vuln_title = f"Vulnerability in {vuln_name}"
                                    vuln_description = "No description available"
                            else:
                                vuln_id = vuln_name
                                vuln_title = f"Vulnerability in {vuln_name}"
                                vuln_description = "No description available"

                            vulnerabilities.append(
                                Vulnerability(
                                    id=vuln_id,
                                    title=vuln_title,
                                    description=vuln_description,
                                    severity=severity,
                                    scanner="npm-audit",
                                    file_path="package.json",
                                    recommendation=vuln_data.get(
                                        "recommendation",
                                        "Update to a non-vulnerable version",
                                    ),
                                )
                            )
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse npm audit output")
        except Exception as e:
            self.logger.error(f"Error running npm audit: {str(e)}")

        return vulnerabilities
