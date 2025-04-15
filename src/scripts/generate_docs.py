#!/usr/bin/env python3
"""
Command-line script for generating documentation.

This script provides a command-line interface for generating documentation
for the Uno framework using the documentation generation system.
"""

import argparse
import logging
import os
import sys
import shutil
import subprocess
from typing import List, Optional, Dict, Union, Any
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from uno.core.docs.generator import DocGeneratorConfig, DocFormat, generate_docs
from uno.devtools.docs.generator import generate_dev_docs

# Check for required dependencies
try:
    import docstring_parser
except ImportError:
    print("Warning: docstring_parser not installed. Run: pip install docstring-parser")

try:
    import markdown
    import pygments
except ImportError:
    print("Warning: markdown or pygments not installed. Run: pip install markdown pygments")

try:
    import jinja2
except ImportError:
    print("Warning: jinja2 not installed. Run: pip install jinja2")

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not installed. Run: pip install pyyaml")


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Generate documentation for Uno framework")
    
    parser.add_argument(
        "--modules", "-m",
        nargs="+",
        default=["uno"],
        help="Modules to document (default: uno)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="docs/api",
        help="Output directory for documentation (default: docs/api)"
    )
    
    parser.add_argument(
        "--formats", "-f",
        nargs="+",
        choices=[f.name.lower() for f in DocFormat],
        default=["markdown", "openapi"],
        help="Documentation formats to generate (default: markdown, openapi)"
    )
    
    parser.add_argument(
        "--title", "-t",
        default="Uno API Documentation",
        help="Documentation title (default: Uno API Documentation)"
    )
    
    parser.add_argument(
        "--description", "-d",
        default="API documentation for the Uno framework",
        help="Documentation description"
    )
    
    parser.add_argument(
        "--version", "-v",
        default=None,
        help="API version (default: auto-detect from package version)"
    )
    
    parser.add_argument(
        "--include-internal",
        action="store_true",
        help="Include internal components (prefixed with _)"
    )
    
    parser.add_argument(
        "--exclude-deprecated",
        action="store_true",
        help="Exclude deprecated components"
    )
    
    parser.add_argument(
        "--include-examples",
        action="store_true",
        default=True,
        help="Include code examples (default: True)"
    )
    
    parser.add_argument(
        "--include-source-links",
        action="store_true",
        default=True,
        help="Include links to source code (default: True)"
    )
    
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Generate developer documentation with additional features"
    )
    
    parser.add_argument(
        "--playground",
        action="store_true",
        help="Include interactive code playgrounds (only with HTML format and --dev)"
    )
    
    parser.add_argument(
        "--mkdocs",
        action="store_true",
        help="Generate MkDocs site from the documentation"
    )
    
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Serve the MkDocs site after generation (implies --mkdocs)"
    )
    
    parser.add_argument(
        "--check-dependencies",
        action="store_true",
        help="Check for missing dependencies and install them"
    )
    
    parser.add_argument(
        "--consistency-check",
        action="store_true",
        help="Check documentation for consistency issues"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate documentation coverage report"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def create_config_from_args(args: argparse.Namespace) -> DocGeneratorConfig:
    """
    Create generator configuration from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Documentation generator configuration
    """
    # Convert format strings to enum values
    formats = []
    for fmt_str in args.formats:
        for fmt in DocFormat:
            if fmt.name.lower() == fmt_str.lower():
                formats.append(fmt)
                break
    
    # Auto-detect version if not specified
    version = args.version
    if version is None:
        try:
            from uno import __about__
            version = __about__.__version__
        except (ImportError, AttributeError):
            version = "0.1.0"  # Default if can't detect
    
    # Create configuration
    config = DocGeneratorConfig(
        title=args.title,
        description=args.description,
        version=version,
        formats=formats,
        output_dir=args.output,
        include_internal=args.include_internal,
        include_deprecated=not args.exclude_deprecated,
        include_examples=args.include_examples,
        include_source_links=args.include_source_links,
        modules_to_document=args.modules
    )
    
    return config


def setup_mkdocs(config: DocGeneratorConfig) -> Path:
    """
    Set up MkDocs directory for documentation.
    
    Args:
        config: Documentation generator configuration
        
    Returns:
        Path to the MkDocs directory
    """
    logger = logging.getLogger("uno.docs")
    
    # Create mkdocs directory
    mkdocs_dir = Path(config.output_dir) / "site"
    mkdocs_dir.mkdir(exist_ok=True, parents=True)
    
    # Set up docs directory structure
    docs_dir = mkdocs_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Copy existing mkdocs.yml if it exists, otherwise create a new one
    project_root = Path(__file__).resolve().parent.parent.parent
    mkdocs_yml_src = project_root / "mkdocs.yml"
    mkdocs_yml_dst = mkdocs_dir / "mkdocs.yml"
    
    if mkdocs_yml_src.exists():
        logger.info(f"Copying existing mkdocs.yml from {mkdocs_yml_src}")
        shutil.copy(mkdocs_yml_src, mkdocs_yml_dst)
    else:
        logger.info("Creating new mkdocs.yml")
        with open(mkdocs_yml_dst, "w") as f:
            yaml.dump({
                "site_name": config.title,
                "site_description": config.description,
                "theme": {
                    "name": "material",
                    "palette": {
                        "primary": "blue",
                        "accent": "indigo"
                    },
                    "features": [
                        "navigation.tabs",
                        "navigation.sections",
                        "toc.integrate",
                        "search.suggest",
                        "search.highlight"
                    ]
                },
                "plugins": [
                    "search",
                    "mkdocstrings"
                ],
                "markdown_extensions": [
                    "admonition",
                    "pymdownx.highlight",
                    "pymdownx.superfences",
                    "pymdownx.tabbed",
                    "pymdownx.details",
                    {"toc": {"permalink": True}}
                ]
            }, f)
    
    return mkdocs_dir

def build_mkdocs(mkdocs_dir: Path) -> bool:
    """
    Build MkDocs site.
    
    Args:
        mkdocs_dir: Path to MkDocs directory
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger("uno.docs")
    
    try:
        logger.info("Building MkDocs site")
        subprocess.run(["mkdocs", "build"], cwd=mkdocs_dir, check=True)
        logger.info(f"MkDocs site built successfully in {mkdocs_dir}/site")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error building MkDocs site: {e}")
        return False
    except FileNotFoundError:
        logger.error("MkDocs not found. Please install with: pip install mkdocs mkdocs-material mkdocstrings")
        return False

def generate_openapi_spec(config: DocGeneratorConfig) -> str:
    """
    Generate OpenAPI specification.
    
    Args:
        config: Documentation generator configuration
        
    Returns:
        Path to the generated OpenAPI specification
    """
    logger = logging.getLogger("uno.docs")
    
    try:
        # Import FastAPI-related modules here to avoid dependency issues
        from fastapi.openapi.utils import get_openapi
        from fastapi import FastAPI
        
        # Create a temporary FastAPI app
        app = FastAPI(title=config.title, description=config.description, version=config.version)
        
        # Generate OpenAPI spec
        openapi_spec = get_openapi(
            title=config.title,
            description=config.description,
            version=config.version,
            routes=app.routes,
        )
        
        # Write to file
        spec_path = os.path.join(config.output_dir, "openapi", "openapi.json")
        os.makedirs(os.path.dirname(spec_path), exist_ok=True)
        
        with open(spec_path, "w") as f:
            import json
            json.dump(openapi_spec, f, indent=2)
        
        logger.info(f"Generated OpenAPI specification: {spec_path}")
        return spec_path
    except ImportError:
        logger.warning("FastAPI not installed. Skipping OpenAPI spec generation.")
        return ""

def check_dependencies(install: bool = False) -> bool:
    """
    Check for required dependencies and optionally install them.
    
    Args:
        install: Whether to install missing dependencies
        
    Returns:
        True if all dependencies are present, False otherwise
    """
    logger = logging.getLogger("uno.docs")
    
    # List of required dependencies
    dependencies = [
        ("docstring_parser", "docstring-parser"),
        ("markdown", "markdown"),
        ("pygments", "pygments"),
        ("jinja2", "jinja2"),
        ("pyyaml", "pyyaml"),
        ("mkdocs", "mkdocs"),
        ("mkdocs.material", "mkdocs-material"),
        ("mkdocstrings", "mkdocstrings"),
    ]
    
    missing = []
    
    # Check for dependencies
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            logger.debug(f"Dependency {module_name} is installed")
        except ImportError:
            logger.warning(f"Dependency {module_name} is missing")
            missing.append((module_name, package_name))
    
    # Install missing dependencies if requested
    if install and missing:
        logger.info("Installing missing dependencies...")
        try:
            import pip
            for _, package_name in missing:
                logger.info(f"Installing {package_name}...")
                pip.main(["install", package_name])
            
            # Check if installation was successful
            still_missing = []
            for module_name, package_name in missing:
                try:
                    __import__(module_name)
                    logger.info(f"Successfully installed {package_name}")
                except ImportError:
                    logger.error(f"Failed to install {package_name}")
                    still_missing.append((module_name, package_name))
            
            missing = still_missing
        except ImportError:
            logger.error("Could not import pip to install dependencies")
    
    return not missing

def check_documentation_consistency(modules: List[str]) -> Dict[str, List[str]]:
    """
    Check documentation for consistency issues.
    
    Args:
        modules: List of modules to check
        
    Returns:
        Dictionary of issues by category
    """
    logger = logging.getLogger("uno.docs")
    
    issues = {
        "missing_docstrings": [],
        "empty_docstrings": [],
        "missing_params": [],
        "missing_returns": [],
        "missing_raises": [],
        "deprecated_no_alternative": [],
    }
    
    # Import modules
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            logger.info(f"Checking documentation consistency for {module_name}")
            
            # Get all members recursively
            members = _get_module_members(module)
            
            # Check each member
            for name, obj in members:
                if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.isclass(obj):
                    doc = inspect.getdoc(obj)
                    
                    # Check for missing docstrings
                    if doc is None:
                        issues["missing_docstrings"].append(f"{name}")
                        continue
                    
                    # Check for empty docstrings
                    if not doc.strip():
                        issues["empty_docstrings"].append(f"{name}")
                        continue
                    
                    # Check for deprecated without alternative
                    if "Deprecated" in doc or "deprecated" in doc:
                        if "Use" not in doc and "use" not in doc:
                            issues["deprecated_no_alternative"].append(f"{name}")
                    
                    # For functions and methods, check params, returns, raises
                    if inspect.isfunction(obj) or inspect.ismethod(obj):
                        sig = inspect.signature(obj)
                        
                        # Check for missing parameter docs
                        for param_name in sig.parameters:
                            if param_name not in ["self", "cls"] and f"{param_name}:" not in doc and f"{param_name} " not in doc:
                                issues["missing_params"].append(f"{name} - {param_name}")
                        
                        # Check for missing returns docs
                        if sig.return_annotation != inspect.Signature.empty and sig.return_annotation != None:
                            if "return" not in doc.lower() and "returns" not in doc.lower():
                                issues["missing_returns"].append(f"{name}")
                        
                        # Check for missing raises docs
                        # This is a heuristic - look for raise statements in the code
                        source = inspect.getsource(obj)
                        if "raise" in source and "raises" not in doc.lower() and "raise" not in doc.lower():
                            issues["missing_raises"].append(f"{name}")
            
        except ImportError as e:
            logger.error(f"Could not import module {module_name}: {e}")
    
    # Log summary
    total_issues = sum(len(issues[category]) for category in issues)
    logger.info(f"Found {total_issues} documentation consistency issues")
    for category, category_issues in issues.items():
        if category_issues:
            logger.info(f"  {category}: {len(category_issues)} issues")
    
    return issues

def _get_module_members(module, prefix=""):
    """Recursively get all members of a module."""
    members = []
    
    for name, obj in inspect.getmembers(module):
        # Skip private members
        if name.startswith("_"):
            continue
        
        # Skip imported modules
        if inspect.ismodule(obj):
            # Only include submodules of the original module
            if hasattr(obj, "__name__") and obj.__name__.startswith(module.__name__):
                submembers = _get_module_members(obj, prefix=f"{prefix}{name}.")
                members.extend(submembers)
        else:
            # Include other members
            members.append((f"{prefix}{name}", obj))
    
    return members

def generate_coverage_report(modules: List[str], output_dir: str) -> None:
    """
    Generate a documentation coverage report.
    
    Args:
        modules: List of modules to check
        output_dir: Output directory for the report
    """
    logger = logging.getLogger("uno.docs")
    
    # Check documentation consistency
    issues = check_documentation_consistency(modules)
    
    # Calculate coverage metrics
    total_items = 0
    documented_items = 0
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            
            # Get all members recursively
            members = _get_module_members(module)
            
            for name, obj in members:
                if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.isclass(obj):
                    total_items += 1
                    
                    # Check if documented
                    doc = inspect.getdoc(obj)
                    if doc and doc.strip():
                        documented_items += 1
        
        except ImportError as e:
            logger.error(f"Could not import module {module_name}: {e}")
    
    # Calculate overall coverage
    coverage = documented_items / total_items if total_items > 0 else 0
    
    # Generate report
    report = {
        "coverage": coverage,
        "documented_items": documented_items,
        "total_items": total_items,
        "issues": issues
    }
    
    # Write report to file
    report_path = os.path.join(output_dir, "coverage_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w") as f:
        import json
        json.dump(report, f, indent=2)
    
    logger.info(f"Documentation coverage: {coverage:.2%} ({documented_items}/{total_items})")
    logger.info(f"Coverage report saved to {report_path}")

def main() -> int:
    """
    Main entry point for documentation generator CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger("uno.docs")
    
    # Check for dependencies if requested
    if args.check_dependencies:
        logger.info("Checking dependencies...")
        if not check_dependencies(install=True):
            logger.error("Missing dependencies. Please install them before proceeding.")
            return 1
    
    # Check documentation consistency if requested
    if args.consistency_check:
        logger.info("Checking documentation consistency...")
        issues = check_documentation_consistency(args.modules)
        return 0 if sum(len(issues[category]) for category in issues) == 0 else 1
    
    # Generate coverage report if requested
    if args.coverage:
        logger.info("Generating documentation coverage report...")
        generate_coverage_report(args.modules, args.output)
        return 0
    
    # Generate documentation
    logger.info(f"Generating documentation for modules: {', '.join(args.modules)}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Formats: {', '.join(args.formats)}")
    
    # Create configuration
    config = create_config_from_args(args)
    
    try:
        # Generate documentation
        if args.dev:
            # If --playground is specified, add HTML format if not already included
            if args.playground and DocFormat.HTML not in config.formats:
                config.formats.append(DocFormat.HTML)
            
            logger.info("Generating developer documentation")
            docs = generate_dev_docs(config)
        else:
            logger.info("Generating API documentation")
            docs = generate_docs(config)
        
        # Log results
        total_files = sum(len(files) for files in docs.values())
        logger.info(f"Generated {total_files} documentation files")
        for fmt, files in docs.items():
            logger.info(f"  {fmt}: {len(files)} files")
        
        # Copy files to output directory
        for format_name, files in docs.items():
            format_dir = os.path.join(config.output_dir, format_name.lower())
            os.makedirs(format_dir, exist_ok=True)
            
            for filename, content in files.items():
                filepath = os.path.join(format_dir, filename)
                
                # Create parent directories if needed
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Write file
                with open(filepath, "w") as f:
                    f.write(content)
                
                logger.debug(f"Wrote file: {filepath}")
        
        # Generate OpenAPI spec if requested
        if DocFormat.OPENAPI in config.formats:
            generate_openapi_spec(config)
        
        # Set up and build MkDocs if requested
        if args.mkdocs or args.serve:
            mkdocs_dir = setup_mkdocs(config)
            # Copy Markdown docs to mkdocs directory
            if DocFormat.MARKDOWN in config.formats:
                markdown_dir = os.path.join(config.output_dir, "markdown")
                mkdocs_docs_dir = os.path.join(mkdocs_dir, "docs")
                
                # Copy all markdown files
                for root, dirs, files in os.walk(markdown_dir):
                    for file in files:
                        if file.endswith(".md"):
                            src_path = os.path.join(root, file)
                            rel_path = os.path.relpath(src_path, markdown_dir)
                            dst_path = os.path.join(mkdocs_docs_dir, rel_path)
                            
                            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                            shutil.copy(src_path, dst_path)
                
                # Build MkDocs site
                if build_mkdocs(mkdocs_dir):
                    logger.info(f"MkDocs site built successfully in {mkdocs_dir}/site")
                    
                    # Serve MkDocs site if requested
                    if args.serve:
                        logger.info("Serving MkDocs site...")
                        try:
                            subprocess.run(["mkdocs", "serve"], cwd=mkdocs_dir, check=True)
                        except subprocess.CalledProcessError as e:
                            logger.error(f"Error serving MkDocs site: {e}")
                            return 1
                        except FileNotFoundError:
                            logger.error("MkDocs not found. Please install with: pip install mkdocs")
                            return 1
                else:
                    logger.error("Failed to build MkDocs site")
                    return 1
        
        logger.info(f"Documentation generated successfully in {config.output_dir}")
        return 0
    except Exception as e:
        logger.error(f"Error generating documentation: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())