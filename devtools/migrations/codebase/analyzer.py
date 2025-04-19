"""Code analyzer for migration assistance.

This module provides tools for analyzing Python code to identify
patterns that need migration, such as deprecated APIs, old patterns,
and version incompatibilities.
"""
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Pattern
import os
import re
import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
import importlib
import importlib.util

logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents an issue in the code that needs migration."""
    
    file_path: Path
    line_number: int
    issue_type: str
    description: str
    suggestion: str
    severity: str = "medium"  # low, medium, high, critical
    code_snippet: Optional[str] = None
    
    def __str__(self) -> str:
        """Format the issue as a string."""
        return (
            f"{self.file_path}:{self.line_number} - {self.issue_type} ({self.severity})\n"
            f"  {self.description}\n"
            f"  Suggestion: {self.suggestion}"
        )


@dataclass
class AnalysisResult:
    """Result of a code analysis."""
    
    issues: List[CodeIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue: CodeIssue) -> None:
        """Add an issue to the results."""
        self.issues.append(issue)
        
    def get_issues_by_severity(self, severity: str) -> List[CodeIssue]:
        """Get issues filtered by severity."""
        return [issue for issue in self.issues if issue.severity == severity]
        
    def get_issues_by_type(self, issue_type: str) -> List[CodeIssue]:
        """Get issues filtered by type."""
        return [issue for issue in self.issues if issue.issue_type == issue_type]
        
    def get_issues_by_file(self, file_path: Union[str, Path]) -> List[CodeIssue]:
        """Get issues for a specific file."""
        file_path = Path(file_path)
        return [issue for issue in self.issues if issue.file_path == file_path]
        
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(issue.severity == "critical" for issue in self.issues)
        
    def summary(self) -> str:
        """Get a summary of the analysis results."""
        severity_counts = {
            "critical": len(self.get_issues_by_severity("critical")),
            "high": len(self.get_issues_by_severity("high")),
            "medium": len(self.get_issues_by_severity("medium")),
            "low": len(self.get_issues_by_severity("low"))
        }
        
        type_counts = {}
        for issue in self.issues:
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
            
        file_counts = {}
        for issue in self.issues:
            file_path = str(issue.file_path)
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
            
        return (
            f"Analysis Summary:\n"
            f"  Total issues: {len(self.issues)}\n"
            f"  By severity: {severity_counts}\n"
            f"  By type: {type_counts}\n"
            f"  Files with issues: {len(file_counts)}\n"
            f"  Stats: {self.stats}"
        )
        
    def to_markdown(self) -> str:
        """Convert the analysis results to markdown format."""
        lines = ["# Code Analysis Results", "", "## Summary", ""]
        lines.append(self.summary().replace("\n", "\n\n"))
        
        if self.issues:
            lines.append("\n## Issues\n")
            
            # Group issues by file
            issues_by_file = {}
            for issue in self.issues:
                file_path = str(issue.file_path)
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)
                
            # Add issues grouped by file
            for file_path, issues in issues_by_file.items():
                lines.append(f"### {file_path}\n")
                
                for issue in issues:
                    lines.append(f"- **Line {issue.line_number}** - {issue.issue_type} ({issue.severity})")
                    lines.append(f"  - {issue.description}")
                    lines.append(f"  - Suggestion: {issue.suggestion}")
                    
                    if issue.code_snippet:
                        lines.append("  ```python")
                        lines.append(f"  {issue.code_snippet}")
                        lines.append("  ```")
                        
                    lines.append("")
                    
        return "\n".join(lines)


class CodeAnalyzer:
    """Analyzer for Python code to identify migration needs."""
    
    def __init__(self):
        """Initialize the code analyzer."""
        self.pattern_checkers = {
            "deprecated_apis": self._check_deprecated_apis,
            "python_version": self._check_python_version_compatibility,
            "uno_api_changes": self._check_uno_api_changes,
            "type_annotations": self._check_type_annotations,
            "error_handling": self._check_error_handling,
            "dependency_injection": self._check_dependency_injection,
            "async_patterns": self._check_async_patterns
        }
        
    def analyze_file(
        self, 
        file_path: Union[str, Path],
        patterns: Optional[List[str]] = None
    ) -> AnalysisResult:
        """Analyze a single Python file.
        
        Args:
            file_path: Path to the Python file
            patterns: List of patterns to check for (default: all)
            
        Returns:
            Analysis results
        """
        file_path = Path(file_path)
        result = AnalysisResult()
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return result
            
        if not file_path.suffix == '.py':
            logger.warning(f"Not a Python file: {file_path}")
            return result
            
        # Load file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse the file with ast
            tree = ast.parse(content)
            lines = content.splitlines()
            
            # Use all patterns or only specified ones
            patterns_to_check = patterns or list(self.pattern_checkers.keys())
            
            # Check each pattern
            for pattern in patterns_to_check:
                if pattern in self.pattern_checkers:
                    checker = self.pattern_checkers[pattern]
                    checker(file_path, tree, lines, content, result)
                else:
                    logger.warning(f"Unknown pattern: {pattern}")
                    
            # Add stats
            result.stats["file_size"] = len(content)
            result.stats["line_count"] = len(lines)
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            
        return result
        
    def analyze_directory(
        self, 
        directory: Union[str, Path],
        patterns: Optional[List[str]] = None,
        include_pattern: str = "*.py",
        exclude_dirs: Optional[List[str]] = None
    ) -> AnalysisResult:
        """Analyze all Python files in a directory.
        
        Args:
            directory: Path to the directory
            patterns: List of patterns to check for (default: all)
            include_pattern: Pattern for files to include
            exclude_dirs: List of directory names to exclude
            
        Returns:
            Analysis results
        """
        directory = Path(directory)
        result = AnalysisResult()
        
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory not found: {directory}")
            return result
            
        exclude_dirs = exclude_dirs or ["venv", ".venv", "env", ".env", ".git", "__pycache__"]
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
                    
        # Analyze each file
        for file_path in python_files:
            file_result = self.analyze_file(file_path, patterns)
            result.issues.extend(file_result.issues)
            
        # Update stats
        result.stats["file_count"] = len(python_files)
        result.stats["directory"] = str(directory)
        
        return result
        
    def _check_deprecated_apis(
        self, 
        file_path: Path, 
        tree: ast.AST, 
        lines: List[str],
        content: str,
        result: AnalysisResult
    ) -> None:
        """Check for deprecated APIs.
        
        This looks for imports and usages of deprecated modules, classes,
        and functions in the Python standard library and common packages.
        """
        # Example deprecated APIs to check
        deprecated_imports = {
            "imp": {
                "replacement": "importlib",
                "severity": "high",
                "description": "The 'imp' module is deprecated since Python 3.4"
            },
            "asyncio.coroutine": {
                "replacement": "async/await syntax",
                "severity": "medium",
                "description": "asyncio.coroutine is deprecated since Python 3.8"
            },
            "unittest.util.safe_repr": {
                "replacement": "reprlib.repr",
                "severity": "low",
                "description": "unittest.util.safe_repr is deprecated"
            }
        }
        
        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name in deprecated_imports:
                        info = deprecated_imports[name.name]
                        result.add_issue(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="deprecated_import",
                            description=info["description"],
                            suggestion=f"Replace with {info['replacement']}",
                            severity=info["severity"],
                            code_snippet=lines[node.lineno - 1]
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module in deprecated_imports:
                    info = deprecated_imports[node.module]
                    result.add_issue(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="deprecated_import",
                        description=info["description"],
                        suggestion=f"Replace with {info['replacement']}",
                        severity=info["severity"],
                        code_snippet=lines[node.lineno - 1]
                    ))
                else:
                    # Check for importing deprecated items from a module
                    for name in node.names:
                        full_name = f"{node.module}.{name.name}"
                        if full_name in deprecated_imports:
                            info = deprecated_imports[full_name]
                            result.add_issue(CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                issue_type="deprecated_import",
                                description=info["description"],
                                suggestion=f"Replace with {info['replacement']}",
                                severity=info["severity"],
                                code_snippet=lines[node.lineno - 1]
                            ))
    
    def _check_python_version_compatibility(
        self, 
        file_path: Path, 
        tree: ast.AST, 
        lines: List[str],
        content: str,
        result: AnalysisResult
    ) -> None:
        """Check for Python version incompatibilities.
        
        This looks for syntax and APIs that might be incompatible with
        the target Python version.
        """
        # For this example, we're checking for Python 3.9+ compatibility
        target_version = (3, 9)
        
        # Features not available in the target version
        for node in ast.walk(tree):
            # Pattern matching (Python 3.10+)
            if hasattr(ast, 'Match') and isinstance(node, ast.Match):
                result.add_issue(CodeIssue(
                    file_path=file_path,
                    line_number=node.lineno,
                    issue_type="version_incompatible",
                    description="Pattern matching requires Python 3.10+",
                    suggestion="Refactor to use if/elif/else statements",
                    severity="critical",
                    code_snippet=lines[node.lineno - 1]
                ))
                
            # Union type operator (Python 3.10+)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                if (isinstance(node.left, ast.Name) and isinstance(node.right, ast.Name) and
                    node.left.id.startswith(('int', 'str', 'list', 'dict', 'set', 'tuple', 'Union'))):
                    result.add_issue(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="version_incompatible",
                        description="Union type operator (|) requires Python 3.10+",
                        suggestion="Use Union from typing module",
                        severity="critical",
                        code_snippet=lines[node.lineno - 1]
                    ))
                    
            # Check for usage of modules or functions added in newer Python versions
            # This is a simplified check
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Example: zoneinfo module (Python 3.9+)
                for name in node.names:
                    if isinstance(node, ast.Import) and name.name == 'zoneinfo':
                        if target_version < (3, 9):
                            result.add_issue(CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                issue_type="version_incompatible",
                                description="zoneinfo module requires Python 3.9+",
                                suggestion="Use the pytz or dateutil.tz packages",
                                severity="high",
                                code_snippet=lines[node.lineno - 1]
                            ))
                    # other checks...
        
    def _check_uno_api_changes(
        self, 
        file_path: Path, 
        tree: ast.AST, 
        lines: List[str],
        content: str,
        result: AnalysisResult
    ) -> None:
        """Check for Uno API changes.
        
        This looks for usage of old Uno APIs that have been changed or deprecated.
        """
        # Map of old APIs to new ones
        api_changes = {
            # Example: method moved from one class to another
            "DomainService.validate_input": {
                "replacement": "UnoValidator.validate",
                "severity": "high",
                "description": "DomainService.validate_input has been moved to UnoValidator.validate"
            },
            # Example: function renamed
            "unodb.execute_query": {
                "replacement": "unodb.execute",
                "severity": "medium",
                "description": "unodb.execute_query has been renamed to unodb.execute"
            },
            # Example: module restructured
            "uno.util": {
                "replacement": "uno.core.utils",
                "severity": "medium",
                "description": "uno.util has been moved to uno.core.utils"
            }
        }
        
        # Patterns to find API usage
        api_patterns = {
            pattern: re.compile(fr"\b{re.escape(pattern)}\b") 
            for pattern in api_changes.keys()
        }
        
        # Check each line for API usage
        for i, line in enumerate(lines):
            for pattern_name, pattern in api_patterns.items():
                if pattern.search(line):
                    info = api_changes[pattern_name]
                    result.add_issue(CodeIssue(
                        file_path=file_path,
                        line_number=i + 1,
                        issue_type="api_change",
                        description=info["description"],
                        suggestion=f"Use {info['replacement']} instead",
                        severity=info["severity"],
                        code_snippet=line
                    ))
                    
        # Check for specific import patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "uno.util":
                    result.add_issue(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="api_change",
                        description="The uno.util module has been moved to uno.core.utils",
                        suggestion="Import from uno.core.utils instead",
                        severity="medium",
                        code_snippet=lines[node.lineno - 1]
                    ))
        
    def _check_type_annotations(
        self, 
        file_path: Path, 
        tree: ast.AST, 
        lines: List[str],
        content: str,
        result: AnalysisResult
    ) -> None:
        """Check for missing or incorrect type annotations.
        
        This looks for functions and variables that should have type annotations.
        """
        # Check function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check return annotation
                if not node.returns and not node.name.startswith('_'):
                    result.add_issue(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="missing_type_annotation",
                        description=f"Function {node.name} is missing return type annotation",
                        suggestion="Add return type annotation",
                        severity="medium",
                        code_snippet=lines[node.lineno - 1]
                    ))
                    
                # Check parameter annotations
                for arg in node.args.args:
                    if not arg.annotation and arg.arg != 'self' and arg.arg != 'cls':
                        result.add_issue(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="missing_type_annotation",
                            description=f"Parameter {arg.arg} in function {node.name} is missing type annotation",
                            suggestion=f"Add type annotation for parameter {arg.arg}",
                            severity="medium",
                            code_snippet=lines[node.lineno - 1]
                        ))
                
                # Check for old-style type annotations (comments)
                func_line = lines[node.lineno - 1]
                if "# type:" in func_line or "#type:" in func_line:
                    result.add_issue(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="old_style_type_annotation",
                        description=f"Function {node.name} uses comment-style type annotation",
                        suggestion="Convert to modern type annotation syntax",
                        severity="low",
                        code_snippet=lines[node.lineno - 1]
                    ))
        
    def _check_error_handling(
        self, 
        file_path: Path, 
        tree: ast.AST, 
        lines: List[str],
        content: str,
        result: AnalysisResult
    ) -> None:
        """Check for proper error handling.
        
        This looks for bare except blocks, re-raising exceptions without context,
        and other error handling issues.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check for bare except blocks
                for handler in node.handlers:
                    if handler.type is None:
                        result.add_issue(CodeIssue(
                            file_path=file_path,
                            line_number=handler.lineno,
                            issue_type="bare_except",
                            description="Bare except block found",
                            suggestion="Specify exception types to catch",
                            severity="high",
                            code_snippet=lines[handler.lineno - 1]
                        ))
                    # Check for catching Exception (too broad)
                    elif isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                        result.add_issue(CodeIssue(
                            file_path=file_path,
                            line_number=handler.lineno,
                            issue_type="broad_except",
                            description="Catching Exception is too broad",
                            suggestion="Catch specific exception types",
                            severity="medium",
                            code_snippet=lines[handler.lineno - 1]
                        ))
                        
                # Check for re-raising exceptions without context
                for handler in node.handlers:
                    if handler.body and isinstance(handler.body[-1], ast.Raise):
                        raise_node = handler.body[-1]
                        if raise_node.exc is None:
                            # Simple re-raise, which is fine
                            pass
                        elif isinstance(raise_node.exc, ast.Name) and raise_node.cause is None:
                            result.add_issue(CodeIssue(
                                file_path=file_path,
                                line_number=raise_node.lineno,
                                issue_type="context_loss",
                                description="Re-raising exception without preserving context",
                                suggestion="Use 'raise NewException() from original' syntax",
                                severity="medium",
                                code_snippet=lines[raise_node.lineno - 1]
                            ))
        
    def _check_dependency_injection(
        self, 
        file_path: Path, 
        tree: ast.AST, 
        lines: List[str],
        content: str,
        result: AnalysisResult
    ) -> None:
        """Check for dependency injection patterns.
        
        This looks for service locator patterns, global state, and other
        anti-patterns that should be replaced with dependency injection.
        """
        # Check for global service locator patterns
        service_locator_patterns = [
            r"get_service\(",
            r"ServiceLocator\.",
            r"Container\.",
            r"Registry\.get\(",
            r"UnoRegistry\.get\("
        ]
        
        for pattern in service_locator_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Find the line number for the match
                line_number = content[:match.start()].count('\n') + 1
                result.add_issue(CodeIssue(
                    file_path=file_path,
                    line_number=line_number,
                    issue_type="service_locator",
                    description="Service locator pattern detected",
                    suggestion="Use constructor dependency injection",
                    severity="medium",
                    code_snippet=lines[line_number - 1]
                ))
                
        # Check for class definitions with global state
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if the class has @inject decorators
                has_inject = any(
                    isinstance(decorator, ast.Name) and decorator.id == 'inject'
                    for decorator in node.decorator_list
                )
                
                # If the class has methods but no __init__ with dependencies, flag it
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                init_methods = [m for m in methods if m.name == '__init__']
                
                if methods and not init_methods and not has_inject:
                    # This is a rough heuristic - the class might be using some form of
                    # dependency injection, but it's not obvious from the structure
                    for method in methods:
                        # Look for access to global state in methods
                        for subnode in ast.walk(method):
                            if isinstance(subnode, ast.Attribute) and isinstance(subnode.value, ast.Name):
                                if subnode.value.id in ['config', 'settings', 'app', 'registry']:
                                    result.add_issue(CodeIssue(
                                        file_path=file_path,
                                        line_number=subnode.lineno,
                                        issue_type="global_state",
                                        description=f"Access to global state ({subnode.value.id})",
                                        suggestion="Inject dependencies in constructor",
                                        severity="medium",
                                        code_snippet=lines[subnode.lineno - 1]
                                    ))
        
    def _check_async_patterns(
        self, 
        file_path: Path, 
        tree: ast.AST, 
        lines: List[str],
        content: str,
        result: AnalysisResult
    ) -> None:
        """Check for proper async patterns.
        
        This looks for blocking operations in async functions, improper use of
        awaitables, and other async pattern issues.
        """
        # Find all async functions
        async_functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_functions[node.name] = node
                
                # Check for sync I/O operations in async functions
                blocking_calls = set([
                    'open', 'read', 'write', 'sleep', 'executes', 'connect',
                    'execute', 'dumps', 'loads'
                ])
                
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                        if subnode.func.id in blocking_calls:
                            result.add_issue(CodeIssue(
                                file_path=file_path,
                                line_number=subnode.lineno,
                                issue_type="blocking_in_async",
                                description=f"Potentially blocking call to {subnode.func.id} in async function",
                                suggestion=f"Use async version (a{subnode.func.id}) or run in executor",
                                severity="high",
                                code_snippet=lines[subnode.lineno - 1]
                            ))
                
                # Check for missing await on awaitable calls
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        # Check calls to other async functions
                        if isinstance(subnode.func, ast.Name) and subnode.func.id in async_functions:
                            # If this call is not in an Await node, flag it
                            if not any(
                                isinstance(parent, ast.Await) and parent.value == subnode
                                for parent in ast.iter_child_nodes(node)
                            ):
                                result.add_issue(CodeIssue(
                                    file_path=file_path,
                                    line_number=subnode.lineno,
                                    issue_type="missing_await",
                                    description=f"Missing await for async function {subnode.func.id}",
                                    suggestion=f"Add await before the call to {subnode.func.id}",
                                    severity="critical",
                                    code_snippet=lines[subnode.lineno - 1]
                                ))


def analyze_python_files(
    directory: Union[str, Path],
    patterns: Optional[List[str]] = None,
    output_format: str = "text"
) -> Union[AnalysisResult, str]:
    """Analyze Python files in a directory.
    
    Args:
        directory: Path to the directory
        patterns: List of patterns to check for (default: all)
        output_format: Format for the output ('text', 'markdown', or 'json')
        
    Returns:
        Analysis results or formatted output
    """
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_directory(directory, patterns)
    
    if output_format == "text":
        return result.summary()
    elif output_format == "markdown":
        return result.to_markdown()
    elif output_format == "json":
        import json
        # Convert to serializable format
        data = {
            "issues": [vars(issue) for issue in result.issues],
            "stats": result.stats
        }
        # Convert Path objects to strings
        for issue in data["issues"]:
            issue["file_path"] = str(issue["file_path"])
        return json.dumps(data, indent=2)
    else:
        return result