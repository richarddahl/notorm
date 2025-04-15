#!/usr/bin/env python3
"""
Script to standardize and maintain consistency in documentation files.

This script processes Markdown documentation files to ensure consistent
formatting, heading structure, and other style guidelines.
"""

import os
import re
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


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
    parser = argparse.ArgumentParser(description="Standardize documentation files")
    
    parser.add_argument(
        "--docs-dir", "-d",
        default="docs",
        help="Directory containing documentation files (default: docs)"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix issues instead of just reporting them"
    )
    
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="Check for broken links between documentation files"
    )
    
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Check for broken image references"
    )
    
    parser.add_argument(
        "--standardize-headings",
        action="store_true",
        help="Standardize heading levels and formats"
    )
    
    parser.add_argument(
        "--standardize-code-blocks",
        action="store_true",
        help="Standardize code block formatting"
    )
    
    parser.add_argument(
        "--add-frontmatter",
        action="store_true",
        help="Add YAML frontmatter to files that don't have it"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def find_markdown_files(docs_dir: str) -> List[Path]:
    """
    Find all Markdown files in the documentation directory.
    
    Args:
        docs_dir: Documentation directory path
        
    Returns:
        List of paths to Markdown files
    """
    docs_path = Path(docs_dir)
    markdown_files = []
    
    for path in docs_path.glob("**/*.md"):
        # Exclude files in hidden directories
        if not any(part.startswith(".") for part in path.parts):
            markdown_files.append(path)
    
    return markdown_files


def check_links(markdown_files: List[Path], docs_dir: Path) -> Dict[Path, List[str]]:
    """
    Check for broken links between documentation files.
    
    Args:
        markdown_files: List of Markdown file paths
        docs_dir: Documentation directory path
        
    Returns:
        Dictionary of files with broken links
    """
    logger = logging.getLogger("docs.links")
    issues = {}
    
    # Build set of valid targets
    valid_targets = set()
    for path in markdown_files:
        # Add file path relative to docs directory
        rel_path = path.relative_to(docs_dir)
        valid_targets.add(str(rel_path))
        
        # Add path without extension (for cleaner URLs)
        if rel_path.name != "index.md":
            valid_targets.add(str(rel_path.with_suffix("")))
        else:
            # For index.md, the parent directory is also a valid target
            valid_targets.add(str(rel_path.parent))
    
    # Check links in each file
    for path in markdown_files:
        with open(path, "r") as f:
            content = f.read()
        
        # Find all Markdown links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        broken_links = []
        
        for link_text, link_target in links:
            # Skip external links and anchors
            if link_target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            
            # Remove any anchor or query params
            link_target = link_target.split("#")[0].split("?")[0]
            
            # Handle relative links
            if not link_target.startswith("/"):
                # Relative to current file
                current_dir = path.parent.relative_to(docs_dir)
                link_path = current_dir / link_target
                normalized_path = str(link_path)
            else:
                # Root-relative link (remove leading slash)
                normalized_path = link_target[1:]
            
            # Check if target exists
            if normalized_path and normalized_path not in valid_targets:
                broken_links.append(f"{link_text} -> {link_target}")
        
        if broken_links:
            issues[path] = broken_links
            logger.warning(f"Found {len(broken_links)} broken links in {path}")
    
    return issues


def check_images(markdown_files: List[Path], docs_dir: Path) -> Dict[Path, List[str]]:
    """
    Check for broken image references.
    
    Args:
        markdown_files: List of Markdown file paths
        docs_dir: Documentation directory path
        
    Returns:
        Dictionary of files with broken image references
    """
    logger = logging.getLogger("docs.images")
    issues = {}
    
    # Build set of valid image paths
    valid_images = set()
    for ext in ["png", "jpg", "jpeg", "gif", "svg"]:
        for img_path in docs_dir.glob(f"**/*.{ext}"):
            # Skip images in hidden directories
            if not any(part.startswith(".") for part in img_path.parts):
                valid_images.add(str(img_path.relative_to(docs_dir)))
    
    # Check image references in each file
    for path in markdown_files:
        with open(path, "r") as f:
            content = f.read()
        
        # Find all image references
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        broken_images = []
        
        for alt_text, img_path in images:
            # Skip external images
            if img_path.startswith(("http:", "https:")):
                continue
            
            # Handle relative images
            if not img_path.startswith("/"):
                # Relative to current file
                current_dir = path.parent.relative_to(docs_dir)
                full_img_path = current_dir / img_path
                normalized_path = str(full_img_path)
            else:
                # Root-relative image (remove leading slash)
                normalized_path = img_path[1:]
            
            # Check if image exists
            if normalized_path and normalized_path not in valid_images:
                broken_images.append(f"{alt_text} -> {img_path}")
        
        if broken_images:
            issues[path] = broken_images
            logger.warning(f"Found {len(broken_images)} broken images in {path}")
    
    return issues


def standardize_headings(file_path: Path, fix: bool = False) -> List[str]:
    """
    Standardize heading levels and formats.
    
    Args:
        file_path: Path to Markdown file
        fix: Whether to fix issues
        
    Returns:
        List of issues found
    """
    logger = logging.getLogger("docs.headings")
    issues = []
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for proper heading hierarchy
    headings = re.findall(r'^(#+)\s+(.*?)(?:\s++#+)?$', content, re.MULTILINE)
    
    if headings:
        current_level = len(headings[0][0])
        
        # Check first heading is level 1
        if current_level != 1:
            issues.append(f"First heading should be level 1 (# Heading), found level {current_level}")
            
            if fix:
                # Fix heading levels
                new_content = content
                for heading_markers, heading_text in headings:
                    level = len(heading_markers)
                    if level > 1:
                        # Adjust heading levels
                        new_level = max(1, level - (current_level - 1))
                        new_markers = "#" * new_level
                        new_content = re.sub(
                            f"^{re.escape(heading_markers)}\\s+{re.escape(heading_text)}(?:\\s+#*)?$",
                            f"{new_markers} {heading_text}",
                            new_content,
                            flags=re.MULTILINE
                        )
                
                # Write fixed content
                with open(file_path, "w") as f:
                    f.write(new_content)
                
                logger.info(f"Fixed heading levels in {file_path}")
        
        # Check for skipped levels
        prev_level = current_level
        for markers, text in headings[1:]:
            level = len(markers)
            
            if level > prev_level + 1:
                issues.append(f"Skipped heading level: {prev_level} to {level} ({text})")
            
            prev_level = level
    
    # Check for consistent heading style (ATX vs Setext)
    setext_headings = re.findall(r'^(.+)\n([=\-]+)$', content, re.MULTILINE)
    if setext_headings:
        issues.append("Inconsistent heading style: found Setext headings (using === or ---)")
        
        if fix:
            # Convert Setext headings to ATX
            new_content = content
            for heading_text, heading_markers in setext_headings:
                level = 1 if heading_markers[0] == "=" else 2
                new_markers = "#" * level
                new_content = re.sub(
                    f"^{re.escape(heading_text)}\\n{re.escape(heading_markers)}$",
                    f"{new_markers} {heading_text.strip()}",
                    new_content,
                    flags=re.MULTILINE
                )
            
            # Write fixed content
            with open(file_path, "w") as f:
                f.write(new_content)
            
            logger.info(f"Converted Setext headings to ATX in {file_path}")
    
    return issues


def standardize_code_blocks(file_path: Path, fix: bool = False) -> List[str]:
    """
    Standardize code block formatting.
    
    Args:
        file_path: Path to Markdown file
        fix: Whether to fix issues
        
    Returns:
        List of issues found
    """
    logger = logging.getLogger("docs.codeblocks")
    issues = []
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for indented code blocks
    indented_blocks = re.findall(r'(?:^|\n)(?:    [^\n]+(?:\n+    [^\n]+)*)', content)
    if indented_blocks:
        issues.append(f"Found {len(indented_blocks)} indented code blocks, use fenced code blocks (```)")
        
        if fix:
            # Convert indented code blocks to fenced
            new_content = content
            for block in indented_blocks:
                # Skip if it's part of a list item (might be intentional indentation)
                if re.search(r'^\s*[*\-+]\s', block, re.MULTILINE):
                    continue
                    
                # Remove the 4-space indentation
                fixed_block = "\n".join(line[4:] for line in block.split("\n"))
                
                # Replace with fenced code block
                new_content = new_content.replace(
                    block, 
                    f"```\n{fixed_block}\n```"
                )
            
            # Write fixed content
            with open(file_path, "w") as f:
                f.write(new_content)
            
            logger.info(f"Converted indented code blocks to fenced in {file_path}")
    
    # Check for fenced code blocks without language
    fenced_blocks = re.findall(r'```\s*\n', content)
    if fenced_blocks:
        issues.append(f"Found {len(fenced_blocks)} code blocks without language specified")
    
    return issues


def add_frontmatter(file_path: Path, fix: bool = False) -> List[str]:
    """
    Add YAML frontmatter to files that don't have it.
    
    Args:
        file_path: Path to Markdown file
        fix: Whether to fix issues
        
    Returns:
        List of issues found
    """
    logger = logging.getLogger("docs.frontmatter")
    issues = []
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for existing frontmatter
    has_frontmatter = re.match(r'^---\n(?:.*\n)+?---\n', content, re.MULTILINE)
    
    if not has_frontmatter:
        issues.append("Missing YAML frontmatter")
        
        if fix:
            # Get title from first heading
            title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem.replace("_", " ").title()
            
            # Create frontmatter
            frontmatter = f"""---
title: {title}
description: Documentation for Uno framework
---

"""
            
            # Add frontmatter
            with open(file_path, "w") as f:
                f.write(frontmatter + content)
            
            logger.info(f"Added frontmatter to {file_path}")
    
    return issues


def main() -> int:
    """
    Main entry point for documentation standardization script.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger("docs.standardize")
    
    # Find Markdown files
    docs_dir = Path(args.docs_dir)
    markdown_files = find_markdown_files(args.docs_dir)
    logger.info(f"Found {len(markdown_files)} Markdown files in {args.docs_dir}")
    
    # Track issues
    all_issues = {}
    
    # Check links
    if args.check_links:
        logger.info("Checking for broken links...")
        link_issues = check_links(markdown_files, docs_dir)
        for file_path, issues in link_issues.items():
            if file_path not in all_issues:
                all_issues[file_path] = []
            all_issues[file_path].extend([f"Broken link: {issue}" for issue in issues])
    
    # Check images
    if args.check_images:
        logger.info("Checking for broken image references...")
        image_issues = check_images(markdown_files, docs_dir)
        for file_path, issues in image_issues.items():
            if file_path not in all_issues:
                all_issues[file_path] = []
            all_issues[file_path].extend([f"Broken image: {issue}" for issue in issues])
    
    # Process each file
    for file_path in markdown_files:
        file_issues = []
        
        # Standardize headings
        if args.standardize_headings:
            heading_issues = standardize_headings(file_path, args.fix)
            file_issues.extend(heading_issues)
        
        # Standardize code blocks
        if args.standardize_code_blocks:
            code_block_issues = standardize_code_blocks(file_path, args.fix)
            file_issues.extend(code_block_issues)
        
        # Add frontmatter
        if args.add_frontmatter:
            frontmatter_issues = add_frontmatter(file_path, args.fix)
            file_issues.extend(frontmatter_issues)
        
        # Add to all issues
        if file_issues:
            all_issues[file_path] = file_issues
    
    # Report issues
    total_issues = sum(len(issues) for issues in all_issues.values())
    logger.info(f"Found {total_issues} issues in {len(all_issues)} files")
    
    if total_issues > 0 and not args.fix:
        logger.info("Run with --fix to automatically fix issues")
        
        # Show detailed issues
        for file_path, issues in all_issues.items():
            print(f"\n{file_path}:")
            for issue in issues:
                print(f"  - {issue}")
    
    return 1 if total_issues > 0 and not args.fix else 0


if __name__ == "__main__":
    sys.exit(main())