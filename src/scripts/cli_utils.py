#!/usr/bin/env python3
"""
Shared CLI utilities for scripts: logging setup and argument parsing.
"""
import logging
import sys

def setup_logger(name: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger that writes to stdout with a standard format.
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(level)
    # Avoid adding multiple handlers if already configured
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

def parse_path_arg(description: str) -> str:
    """
    Parse a single optional positional argument for a file or directory path.
    Returns the path string or None if omitted.
    """
    import argparse

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Specific file or directory to process (default=src/)",
    )
    args = parser.parse_args()
    return args.target