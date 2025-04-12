"""
Command-line interface for documentation generation.

This module provides a command-line tool for generating documentation
using the Uno documentation generation framework.
"""

import argparse
import logging
import os
import sys
from typing import List, Optional

from uno.core.docs.generator import DocGeneratorConfig, DocFormat, generate_docs


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate documentation for Uno components"
    )
    
    parser.add_argument(
        "--title",
        type=str,
        default="API Documentation",
        help="Title for the documentation"
    )
    
    parser.add_argument(
        "--description",
        type=str,
        default="Generated API documentation",
        help="Description for the documentation"
    )
    
    parser.add_argument(
        "--version",
        type=str,
        default="1.0.0",
        help="Version for the documentation"
    )
    
    parser.add_argument(
        "--formats",
        type=str,
        nargs="+",
        choices=[f.name.lower() for f in DocFormat],
        default=["markdown", "openapi"],
        help="Output formats for the documentation"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/api",
        help="Output directory for the documentation"
    )
    
    parser.add_argument(
        "--include-source-links",
        action="store_true",
        default=True,
        help="Include links to source code in the documentation"
    )
    
    parser.add_argument(
        "--include-examples",
        action="store_true",
        default=True,
        help="Include examples in the documentation"
    )
    
    parser.add_argument(
        "--example-depth",
        type=int,
        default=2,
        help="Depth of examples to include"
    )
    
    parser.add_argument(
        "--include-internal",
        action="store_true",
        default=False,
        help="Include internal components in the documentation"
    )
    
    parser.add_argument(
        "--include-deprecated",
        action="store_true",
        default=True,
        help="Include deprecated components in the documentation"
    )
    
    parser.add_argument(
        "--include-beta",
        action="store_true",
        default=True,
        help="Include beta components in the documentation"
    )
    
    parser.add_argument(
        "--include-alpha",
        action="store_true",
        default=True,
        help="Include alpha components in the documentation"
    )
    
    parser.add_argument(
        "--include-experimental",
        action="store_true",
        default=True,
        help="Include experimental components in the documentation"
    )
    
    parser.add_argument(
        "--modules",
        type=str,
        nargs="+",
        required=True,
        help="Modules to document"
    )
    
    parser.add_argument(
        "--url-base",
        type=str,
        default=None,
        help="Base URL for the documentation"
    )
    
    parser.add_argument(
        "--logo-url",
        type=str,
        default=None,
        help="URL for the logo to use in the documentation"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level"
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the documentation generator CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parsed_args = parse_args(args)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, parsed_args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Convert format strings to DocFormat enum values
    formats = [DocFormat[f.upper()] for f in parsed_args.formats]
    
    # Create generator config
    config = DocGeneratorConfig(
        title=parsed_args.title,
        description=parsed_args.description,
        version=parsed_args.version,
        formats=formats,
        output_dir=parsed_args.output_dir,
        include_source_links=parsed_args.include_source_links,
        include_examples=parsed_args.include_examples,
        example_depth=parsed_args.example_depth,
        include_internal=parsed_args.include_internal,
        include_deprecated=parsed_args.include_deprecated,
        include_beta=parsed_args.include_beta,
        include_alpha=parsed_args.include_alpha,
        include_experimental=parsed_args.include_experimental,
        modules_to_document=parsed_args.modules,
        url_base=parsed_args.url_base,
        logo_url=parsed_args.logo_url
    )
    
    try:
        # Generate documentation
        result = generate_docs(config)
        
        # Log success
        logging.info(f"Documentation generated in {parsed_args.output_dir}")
        
        for format_name, files in result.items():
            logging.info(f"{format_name} documentation: {len(files)} files")
        
        return 0
    except Exception as e:
        logging.error(f"Error generating documentation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())