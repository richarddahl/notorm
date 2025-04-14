#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Validate that error codes across all modules follow the standard format.

This script checks all error codes in the codebase to ensure they follow
the standardized format: MODULE-####, where MODULE is a module identifier
and #### is a four-digit number.
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def find_error_code_classes(src_dir: str) -> List[str]:
    """
    Find all error code classes in the source directory.
    
    Args:
        src_dir: The root source directory
        
    Returns:
        List of file paths containing error code classes
    """
    error_code_files = []
    
    for root, _, files in os.walk(os.path.join(src_dir, "src", "uno")):
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            
            # Skip __pycache__ directories
            if "__pycache__" in file_path:
                continue
                
            # Check if file contains "ErrorCode" class
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if re.search(r"class\s+\w*ErrorCode", content):
                        error_code_files.append(file_path)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
    return error_code_files


def extract_error_codes(file_path: str) -> List[Tuple[str, str]]:
    """
    Extract error codes from a file.
    
    Args:
        file_path: The file to process
        
    Returns:
        List of (code_name, code_value) tuples
    """
    error_codes = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
            # Find the ErrorCode class
            class_match = re.search(r"class\s+(\w+ErrorCode)", content)
            if not class_match:
                return []
                
            class_name = class_match.group(1)
            
            # Find the class content - everything between first { and closing }
            class_content_match = re.search(
                r"class\s+" + class_name + r".*?:(.*?)(?:class|def|\Z)", 
                content, 
                re.DOTALL
            )
            
            if not class_content_match:
                return []
                
            class_content = class_content_match.group(1)
            
            # Extract all constants
            for line in class_content.split("\n"):
                # Look for lines like: SOME_ERROR = "MODULE-####"
                match = re.search(r"\s+(\w+)\s*=\s*[\"']([A-Z0-9\-]+)[\"']", line)
                if match:
                    code_name = match.group(1)
                    code_value = match.group(2)
                    error_codes.append((code_name, code_value))
                    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return error_codes


def validate_error_code_format(error_codes: List[Tuple[str, str]]) -> List[str]:
    """
    Validate that error codes follow the standard format.
    
    Args:
        error_codes: List of (code_name, code_value) tuples
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for code_name, code_value in error_codes:
        # Check format: MODULE-####
        if not re.match(r"^[A-Z]+-\d{4}$", code_value):
            errors.append(f"Error code {code_name} = {code_value} has invalid format. Should be MODULE-####")
            
    return errors


def print_summary(error_code_files: List[str], all_codes: Dict[str, List[Tuple[str, str]]], validation_errors: Dict[str, List[str]]):
    """
    Print a summary of the findings.
    
    Args:
        error_code_files: List of files with error code classes
        all_codes: Dictionary of file path to list of error codes
        validation_errors: Dictionary of file path to list of validation errors
    """
    print(f"\nFound {len(error_code_files)} files with error code classes:")
    
    total_codes = sum(len(codes) for codes in all_codes.values())
    total_errors = sum(len(errors) for errors in validation_errors.values())
    
    for file_path in error_code_files:
        rel_path = os.path.relpath(file_path, project_root)
        code_count = len(all_codes.get(file_path, []))
        error_count = len(validation_errors.get(file_path, []))
        
        print(f"  - {rel_path}: {code_count} codes, {error_count} errors")
        
        # Print the errors for this file
        if file_path in validation_errors and validation_errors[file_path]:
            for error in validation_errors[file_path]:
                print(f"      - {error}")
                
    print(f"\nTotal: {total_codes} error codes, {total_errors} validation errors")
    
    # Print summary of error codes per module
    module_counts = {}
    
    for file_path, codes in all_codes.items():
        for _, code_value in codes:
            module = code_value.split("-")[0]
            module_counts[module] = module_counts.get(module, 0) + 1
            
    print("\nError codes by module:")
    for module, count in sorted(module_counts.items()):
        print(f"  - {module}: {count} codes")
        
    if total_errors == 0:
        print("\n✅ All error codes follow the standard format.")
    else:
        print(f"\n❌ Found {total_errors} error codes with invalid format.")


def main():
    """Main entry point."""
    src_dir = project_root
    
    print("Validating error code format...")
    
    error_code_files = find_error_code_classes(src_dir)
    all_codes = {}
    validation_errors = {}
    
    for file_path in error_code_files:
        error_codes = extract_error_codes(file_path)
        all_codes[file_path] = error_codes
        
        errors = validate_error_code_format(error_codes)
        if errors:
            validation_errors[file_path] = errors
            
    print_summary(error_code_files, all_codes, validation_errors)


if __name__ == "__main__":
    main()