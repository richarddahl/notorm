# Security Testing

The Uno Security Framework includes a comprehensive security testing suite designed to identify vulnerabilities, enforce secure coding practices, and maintain a strong security posture. This document describes the security testing tools and methodologies available in the framework.

## Overview

Security testing in Uno provides:

- Automated vulnerability scanning of dependencies
- Static code analysis for security issues
- Penetration testing tools
- Security regression testing
- Compliance validation

## Core Components

### Dependency Scanner

The `DependencyScanner` identifies vulnerabilities in project dependencies:

```python
from uno.security.testing import DependencyScanner

# Create scanner instance
scanner = DependencyScanner()

# Scan project dependencies
vulnerabilities = scanner.scan_dependencies()

# Generate vulnerability report
report = scanner.generate_report(vulnerabilities)
print(f"Found {len(vulnerabilities)} vulnerabilities")

# Remediation recommendations
for vuln in vulnerabilities:```

print(f"Package: {vuln.package_name} (v{vuln.version})")
print(f"Severity: {vuln.severity}")
print(f"Description: {vuln.description}")
print(f"Recommendation: {vuln.recommendation}")
print()
```
```

### Static Analysis

The `StaticAnalyzer` scans source code for security issues:

```python
from uno.security.testing import StaticAnalyzer

# Create analyzer instance
analyzer = StaticAnalyzer()

# Analyze specific files or directories
issues = analyzer.analyze("src/uno")

# Generate report
report = analyzer.generate_report(issues)
print(f"Found {len(issues)} security issues")

# Review issues
for issue in issues:```

print(f"File: {issue.file_path}:{issue.line_number}")
print(f"Type: {issue.issue_type}")
print(f"Severity: {issue.severity}")
print(f"Description: {issue.description}")
print(f"Recommendation: {issue.recommendation}")
print()
```
```

### Penetration Testing

The `PenetrationTester` helps identify security weaknesses in applications:

```python
from uno.security.testing import PenetrationTester

# Create tester instance
pen_tester = PenetrationTester(```

target_url="https://myapp.example.com",
api_endpoints=["/api/login", "/api/users", "/api/data"]
```
)

# Run specific tests
results = pen_tester.run_tests(```

categories=["injection", "authentication", "authorization"]
```
)

# Generate report
report = pen_tester.generate_report(results)
print(f"Found {len(results)} security vulnerabilities")
```

## Integration with CI/CD

### GitHub Actions Integration

Example GitHub Actions workflow for security testing:

```yaml
name: Security Testing

on:
  push:```

branches: [ main ]
```
  pull_request:```

branches: [ main ]
```
  schedule:
    - cron: '0 0 * * 0'  # Weekly scan

jobs:
  security-testing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          
      - name: Scan dependencies
        run: python -m uno.security.testing.cli scan-dependencies
        
      - name: Run static analysis
        run: python -m uno.security.testing.cli static-analysis
        
      - name: Upload security reports
        uses: actions/upload-artifact@v2
        with:
          name: security-reports
          path: |
            reports/dependency-scan.json
            reports/static-analysis.json
```

## Configuration

Configure security testing through the `SecurityConfig`:

```python
from uno.security.config import SecurityConfig

config = SecurityConfig(```

testing={```

"dependency_scanning": {
    "enabled": True,
    "scan_frequency": "daily",
    "severity_threshold": "medium",  # Fail on medium or higher
    "ignore_vulnerabilities": [
        "CVE-2023-12345",  # Specific CVEs to ignore
    ],
},
"static_analysis": {
    "enabled": True,
    "paths": ["src/", "tests/"],
    "exclude_paths": ["src/vendor/"],
    "rules": ["all"],
    "exclude_rules": ["rule1", "rule2"],
    "max_issues": 0,  # Zero tolerance policy
},
"penetration_testing": {
    "enabled": True,
    "target_url": "https://staging.example.com",
    "auth": {
        "username": "${ENV_USERNAME}",
        "password": "${ENV_PASSWORD}",
    },
    "tests": ["injection", "authentication", "authorization"],
}
```
}
```
)
```

## Best Practices

1. **Regular scanning**: Run dependency scans at least weekly to identify new vulnerabilities.

2. **CI/CD integration**: Integrate security testing into your continuous integration pipeline.

3. **Zero tolerance for high severity issues**: Block merges and deployments when high severity issues are detected.

4. **Comprehensive test coverage**: Test all API endpoints, authentication flows, and data operations.

5. **Multiple testing approaches**: Combine dependency scanning, static analysis, and penetration testing for comprehensive coverage.

6. **Keep tools updated**: Regularly update security testing tools to detect the latest vulnerability patterns.

7. **Security testing for third-party integrations**: Extend testing to third-party APIs and services used by your application.

## Security Testing CLI

The security testing module includes a command-line interface for running tests:

```bash
# Scan dependencies
python -m uno.security.testing.cli scan-dependencies

# Run static analysis
python -m uno.security.testing.cli static-analysis

# Run penetration tests
python -m uno.security.testing.cli pen-test --target https://myapp.example.com

# Run all security tests
python -m uno.security.testing.cli run-all
```

## Example Usage

### Pre-Commit Setup

Integrate security testing into pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: security-dependency-check
        name: Security Dependency Check
        entry: python -m uno.security.testing.cli scan-dependencies
        language: system
        pass_filenames: false
        
      - id: security-static-analysis
        name: Security Static Analysis
        entry: python -m uno.security.testing.cli static-analysis
        language: system
        files: \.(py|js|ts)$
```

### Combining Multiple Security Tests

```python
from uno.security.testing import SecurityTestSuite

# Create a comprehensive test suite
suite = SecurityTestSuite()

# Run all security tests
results = suite.run_all()

# Generate comprehensive report
report = suite.generate_report(results)

# Check if any critical issues were found
if any(issue.severity == "critical" for issue in results.all_issues()):```

print("Critical security issues found!")
exit(1)
```
```

### Continuous Monitoring

```python
from uno.security.testing import SecurityMonitor
import schedule
import time

# Create security monitor
monitor = SecurityMonitor()

# Schedule regular scans
schedule.every().day.at("02:00").do(monitor.scan_dependencies)
schedule.every().week.do(monitor.run_static_analysis)
schedule.every().month.do(monitor.run_penetration_tests)

# Run monitoring loop
while True:```

schedule.run_pending()
time.sleep(1)
```
```

## Troubleshooting

### Common Issues

1. **False positives**: Review and configure rules to reduce false positives in static analysis.

2. **Scan performance**: For large codebases, configure incremental scanning to focus on changed files.

3. **Dependency conflicts**: Resolve conflicts between security requirements and functional requirements through careful version management.

### Debugging

Enable debug logging for the security testing system:

```python
import logging

# Set security testing logging to debug level
logging.getLogger("uno.security.testing").setLevel(logging.DEBUG)
```