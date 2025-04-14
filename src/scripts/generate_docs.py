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
from typing import List, Optional
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from uno.core.docs.generator import DocGeneratorConfig, DocFormat, generate_docs
from uno.devtools.docs.generator import generate_dev_docs


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
        
        logger.info(f"Documentation generated successfully in {config.output_dir}")
        return 0
    except Exception as e:
        logger.error(f"Error generating documentation: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())