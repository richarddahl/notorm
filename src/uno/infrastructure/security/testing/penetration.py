# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Penetration testing tools for Uno applications.

This module provides penetration testing tools for Uno applications.
"""

import logging
import json
import os
import subprocess
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from uno.security.config import SecurityTestingConfig
from uno.security.testing.scanner import Vulnerability


class PenetrationTester:
    """
    Penetration tester for Uno applications.
    
    This class provides tools for penetration testing of web applications.
    """
    
    def __init__(
        self,
        config: SecurityTestingConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the penetration tester.
        
        Args:
            config: Security testing configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.testing.penetration")
    
    def scan(self, target: str) -> List[Vulnerability]:
        """
        Scan a web application for security vulnerabilities.
        
        Args:
            target: Target URL to scan
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        # Check if the target is a URL
        parsed_url = urlparse(target)
        if not parsed_url.scheme or not parsed_url.netloc:
            self.logger.warning(f"Target {target} is not a valid URL, skipping penetration testing")
            return vulnerabilities
        
        # Run OWASP ZAP scan (if available)
        vulnerabilities.extend(self._run_zap_scan(target))
        
        # Run Nikto scan (if available)
        vulnerabilities.extend(self._run_nikto_scan(target))
        
        return vulnerabilities
    
    def _run_zap_scan(self, target: str) -> List[Vulnerability]:
        """
        Run an OWASP ZAP scan.
        
        Args:
            target: Target URL to scan
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        try:
            # Check if ZAP is available
            zap_path = os.environ.get("ZAP_PATH")
            if not zap_path:
                zap_path = "/opt/zaproxy/zap.sh"  # Default path on Linux
                if not os.path.exists(zap_path):
                    zap_path = "zap"  # Try PATH
            
            # Run ZAP scan
            result = subprocess.run(
                [
                    zap_path,
                    "-cmd",
                    "-quickurl", target,
                    "-quickout", "zap_report.json"
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.security_scan_timeout
            )
            
            # Check if the report was generated
            if os.path.exists("zap_report.json"):
                try:
                    with open("zap_report.json", "r") as f:
                        data = json.load(f)
                    
                    for site in data.get("site", []):
                        site_url = site.get("@name", "")
                        for alert in site.get("alerts", []):
                            alert_name = alert.get("name", "")
                            risk = alert.get("riskdesc", "").split(" ")[0].lower()
                            
                            # Map ZAP risk to severity
                            severity = "info"
                            if risk == "high":
                                severity = "high"
                            elif risk == "medium":
                                severity = "medium"
                            elif risk == "low":
                                severity = "low"
                            
                            for instance in alert.get("instances", []):
                                url = instance.get("uri", "")
                                
                                vulnerabilities.append(Vulnerability(
                                    id=f"zap-{alert_name.lower().replace(' ', '-')}",
                                    title=alert_name,
                                    description=alert.get("desc", ""),
                                    severity=severity,
                                    scanner="owasp-zap",
                                    file_path=url,
                                    recommendation=alert.get("solution", "")
                                ))
                    
                    # Clean up the report file
                    os.remove("zap_report.json")
                except (json.JSONDecodeError, IOError):
                    self.logger.error("Failed to parse ZAP report")
        except (subprocess.SubprocessError, FileNotFoundError):
            self.logger.warning("OWASP ZAP not available or timed out")
        except Exception as e:
            self.logger.error(f"Error running OWASP ZAP: {str(e)}")
        
        return vulnerabilities
    
    def _run_nikto_scan(self, target: str) -> List[Vulnerability]:
        """
        Run a Nikto scan.
        
        Args:
            target: Target URL to scan
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        try:
            # Check if Nikto is available
            try:
                subprocess.run(["nikto", "-Version"], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.warning("Nikto not available")
                return vulnerabilities
            
            # Run Nikto scan
            result = subprocess.run(
                [
                    "nikto",
                    "-h", target,
                    "-Format", "json",
                    "-output", "nikto_report.json"
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.security_scan_timeout
            )
            
            # Check if the report was generated
            if os.path.exists("nikto_report.json"):
                try:
                    with open("nikto_report.json", "r") as f:
                        data = json.load(f)
                    
                    for vuln in data.get("vulnerabilities", []):
                        osvdb_id = vuln.get("OSVDB", "")
                        
                        vulnerabilities.append(Vulnerability(
                            id=f"nikto-osvdb-{osvdb_id}" if osvdb_id else f"nikto-{len(vulnerabilities) + 1}",
                            title=vuln.get("msg", "Nikto finding"),
                            description=vuln.get("msg", ""),
                            severity="medium",  # Nikto doesn't provide severity
                            scanner="nikto",
                            file_path=vuln.get("url", target)
                        ))
                    
                    # Clean up the report file
                    os.remove("nikto_report.json")
                except (json.JSONDecodeError, IOError):
                    self.logger.error("Failed to parse Nikto report")
        except (subprocess.SubprocessError, FileNotFoundError):
            self.logger.warning("Nikto not available or timed out")
        except Exception as e:
            self.logger.error(f"Error running Nikto: {str(e)}")
        
        return vulnerabilities