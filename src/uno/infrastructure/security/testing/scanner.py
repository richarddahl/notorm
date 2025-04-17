# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Security scanner for Uno applications.

This module provides a security scanner for Uno applications,
which coordinates different types of security testing.
"""

import logging
import json
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from uno.security.config import SecurityTestingConfig


class Vulnerability:
    """Class representing a security vulnerability."""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        severity: str,
        scanner: str,
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        cvss_score: Optional[float] = None,
        recommendation: Optional[str] = None,
        external_references: Optional[List[str]] = None,
    ):
        """
        Initialize a vulnerability.
        
        Args:
            id: Vulnerability ID
            title: Vulnerability title
            description: Vulnerability description
            severity: Vulnerability severity (critical, high, medium, low, info)
            scanner: Scanner that detected the vulnerability
            file_path: File where the vulnerability was found
            line: Line number where the vulnerability was found
            cvss_score: CVSS score (0.0-10.0)
            recommendation: Recommendation for fixing the vulnerability
            external_references: External references (e.g., CVE, CWE)
        """
        self.id = id
        self.title = title
        self.description = description
        self.severity = severity
        self.scanner = scanner
        self.file_path = file_path
        self.line = line
        self.cvss_score = cvss_score
        self.recommendation = recommendation
        self.external_references = external_references or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the vulnerability to a dictionary.
        
        Returns:
            Dictionary representation of the vulnerability
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "scanner": self.scanner,
            "file_path": self.file_path,
            "line": self.line,
            "cvss_score": self.cvss_score,
            "recommendation": self.recommendation,
            "external_references": self.external_references
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vulnerability":
        """
        Create a vulnerability from a dictionary.
        
        Args:
            data: Dictionary representation of the vulnerability
            
        Returns:
            Vulnerability instance
        """
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            severity=data["severity"],
            scanner=data["scanner"],
            file_path=data.get("file_path"),
            line=data.get("line"),
            cvss_score=data.get("cvss_score"),
            recommendation=data.get("recommendation"),
            external_references=data.get("external_references")
        )


class SecurityScanner:
    """
    Security scanner for Uno applications.
    
    This class coordinates different types of security testing,
    including dependency scanning, static analysis, and penetration testing.
    """
    
    def __init__(
        self,
        config: SecurityTestingConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the security scanner.
        
        Args:
            config: Security testing configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.testing")
        self.scanners = {}
        
        # Initialize scanners
        self._initialize_scanners()
    
    def _initialize_scanners(self) -> None:
        """Initialize security scanners."""
        if self.config.enable_dependency_scanning:
            from uno.security.testing.dependency import DependencyScanner
            self.scanners["dependency"] = DependencyScanner(self.config, self.logger)
        
        if self.config.enable_static_analysis:
            from uno.security.testing.static import StaticAnalyzer
            self.scanners["static"] = StaticAnalyzer(self.config, self.logger)
        
        if self.config.enable_dynamic_analysis:
            try:
                from uno.security.testing.dynamic import DynamicAnalyzer
                self.scanners["dynamic"] = DynamicAnalyzer(self.config, self.logger)
            except ImportError:
                self.logger.warning("Dynamic analysis not available")
        
        if self.config.enable_penetration_testing:
            try:
                from uno.security.testing.penetration import PenetrationTester
                self.scanners["penetration"] = PenetrationTester(self.config, self.logger)
            except ImportError:
                self.logger.warning("Penetration testing not available")
    
    def scan(self, target: str) -> Dict[str, Any]:
        """
        Scan a target for security vulnerabilities.
        
        Args:
            target: Target to scan (file, directory, or URL)
            
        Returns:
            Scan results
        """
        start_time = time.time()
        vulnerabilities = []
        
        # Run all enabled scanners
        for scanner_name, scanner in self.scanners.items():
            try:
                self.logger.info(f"Running {scanner_name} scanner...")
                scanner_vulnerabilities = scanner.scan(target)
                vulnerabilities.extend(scanner_vulnerabilities)
                self.logger.info(f"Found {len(scanner_vulnerabilities)} vulnerabilities with {scanner_name} scanner")
            except Exception as e:
                self.logger.error(f"Error running {scanner_name} scanner: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Count vulnerabilities by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for vulnerability in vulnerabilities:
            severity = vulnerability.severity.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Check if the scan should fail based on configuration
        fail_conditions = []
        if self.config.fail_build_on_critical and severity_counts["critical"] > 0:
            fail_conditions.append(f"Found {severity_counts['critical']} critical vulnerabilities")
        if self.config.fail_build_on_high and severity_counts["high"] > 0:
            fail_conditions.append(f"Found {severity_counts['high']} high vulnerabilities")
        if self.config.fail_build_on_medium and severity_counts["medium"] > 0:
            fail_conditions.append(f"Found {severity_counts['medium']} medium vulnerabilities")
        
        return {
            "target": target,
            "vulnerabilities": [v.to_dict() for v in vulnerabilities],
            "summary": {
                "total": len(vulnerabilities),
                "severity_counts": severity_counts,
                "duration": duration
            },
            "fail_conditions": fail_conditions,
            "should_fail": len(fail_conditions) > 0
        }
    
    def save_report(self, results: Dict[str, Any], filename: str) -> None:
        """
        Save scan results to a file.
        
        Args:
            results: Scan results
            filename: Filename for the report
        """
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
    
    def check_allowed_vulnerabilities(self, vulnerability: Vulnerability) -> bool:
        """
        Check if a vulnerability is in the allowed list.
        
        Args:
            vulnerability: Vulnerability to check
            
        Returns:
            True if the vulnerability is allowed, False otherwise
        """
        return vulnerability.id in self.config.allowed_vulnerabilities