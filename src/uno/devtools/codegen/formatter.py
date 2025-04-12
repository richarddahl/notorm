"""
Code formatting utilities for code generation.

This module provides utilities for formatting generated code.
"""

import re
import logging
from typing import Optional, List

try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False


logger = logging.getLogger("uno.codegen")


def format_code(code: str, line_length: int = 88) -> str:
    """Format Python code using black if available, or basic formatting otherwise.
    
    Args:
        code: The code to format
        line_length: Maximum line length
        
    Returns:
        Formatted code
    """
    # Try using black if available
    if BLACK_AVAILABLE:
        try:
            mode = black.Mode(
                line_length=line_length,
                string_normalization=True,
                preview=True,
            )
            return black.format_str(code, mode=mode)
        except Exception as e:
            logger.warning(f"Error formatting code with black: {str(e)}")
            # Fall back to basic formatting
    
    # Basic formatting
    return _basic_format(code)


def _basic_format(code: str) -> str:
    """Apply basic formatting to Python code.
    
    Args:
        code: The code to format
        
    Returns:
        Formatted code
    """
    # Remove extra blank lines (more than 2 in a row)
    code = re.sub(r'\n{3,}', '\n\n', code)
    
    # Ensure proper spacing around operators
    code = re.sub(r'([^\s=!<>])([=!<>]+)([^\s=])', r'\1 \2 \3', code)
    
    # Ensure proper spacing after commas
    code = re.sub(r',([^\s])', r', \1', code)
    
    # Remove trailing whitespace
    code = re.sub(r' +$', '', code, flags=re.MULTILINE)
    
    # Ensure file ends with a newline
    if not code.endswith('\n'):
        code += '\n'
    
    return code


def strip_docstrings(code: str) -> str:
    """Remove docstrings from Python code.
    
    Args:
        code: The code to process
        
    Returns:
        Code with docstrings removed
    """
    # Simple regex to remove docstrings (not perfect, but good enough for generated code)
    code = re.sub(r'""".*?"""', '""""""', code, flags=re.DOTALL)
    return code


def strip_comments(code: str) -> str:
    """Remove comments from Python code.
    
    Args:
        code: The code to process
        
    Returns:
        Code with comments removed
    """
    # Remove single-line comments
    code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    return code


def minify_code(code: str) -> str:
    """Minify Python code by removing docstrings, comments, and unnecessary whitespace.
    
    Args:
        code: The code to minify
        
    Returns:
        Minified code
    """
    # Remove docstrings and comments
    code = strip_docstrings(code)
    code = strip_comments(code)
    
    # Remove blank lines
    code = re.sub(r'\n\s*\n', '\n', code)
    
    # Remove trailing whitespace
    code = re.sub(r' +$', '', code, flags=re.MULTILINE)
    
    return code