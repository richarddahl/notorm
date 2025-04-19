#!/usr/bin/env python3
"""
Protocol validation utility script for the UNO framework.

This script validates that classes marked with the @implements decorator
correctly implement their protocols and finds all implementations of protocols
in the codebase. It can be used as a development tool or as part of 
CI/CD pipelines to ensure protocol compliance.

Usage:
    python -m src.scripts.validate_protocols [--verbose] [--find-all] [--test-suite] [module1 module2 ...]

Arguments:
    --verbose: Show detailed error information
    --find-all: Find all implementations of protocols, not just those marked with @implements
    --test-suite: Generate a test suite for all protocol implementations
    module1, module2, ...: Modules to validate (defaults to 'src.uno' if not specified)
"""

import argparse
import importlib
import inspect
import sys
import unittest
from typing import List, Dict, Type, Any

from uno.core.protocol_validator import (
    verify_all_implementations, 
    find_protocol_implementations,
    ProtocolValidationError,
)
from uno.core.protocol_testing import create_protocol_test_suite, all_protocol_implementations


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 for success, 1 for validation errors.
    """
    parser = argparse.ArgumentParser(description="Validate protocol implementations in the UNO framework.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed error information")
    parser.add_argument("--find-all", "-f", action="store_true", help="Find all implementations of protocols")
    parser.add_argument("--test-suite", "-t", action="store_true", help="Generate a test suite for protocol implementations")
    parser.add_argument("modules", nargs="*", default=["src.uno"], help="Modules to validate")
    
    args = parser.parse_args()
    verbose = args.verbose
    find_all = args.find_all
    test_suite = args.test_suite
    modules = args.modules
    
    if test_suite:
        return run_test_suite(modules, verbose)
    elif find_all:
        return find_all_implementations(modules, verbose)
    else:
        return validate_implementations(modules, verbose)


def validate_implementations(modules: List[str], verbose: bool) -> int:
    """
    Validate implementations marked with @implements.
    
    Args:
        modules: List of modules to validate
        verbose: Whether to show detailed error information
        
    Returns:
        0 for success, 1 for validation errors
    """
    # Validate implementations marked with @implements
    all_errors = verify_all_implementations(modules)
    
    # Print the results
    if not all_errors:
        print("✅ All protocol implementations are valid!")
        return 0
    
    # There are validation errors
    error_count = sum(len(errors) for errors in all_errors.values())
    print(f"❌ Found {error_count} protocol validation errors in {len(all_errors)} classes:")
    
    for class_name, errors in all_errors.items():
        print(f"\n{class_name}:")
        for i, error in enumerate(errors, 1):
            if verbose:
                print(f"  {i}. {error}")
            else:
                # Print a more concise error message
                protocol_name = error.protocol.__name__
                if error.missing_attributes:
                    attrs = ", ".join(error.missing_attributes)
                    print(f"  {i}. Missing attributes for {protocol_name}: {attrs}")
                if error.type_mismatches:
                    mismatches = ", ".join(f"{attr}" for attr in error.type_mismatches.keys())
                    print(f"  {i}. Type mismatches for {protocol_name}: {mismatches}")
    
    return 1


def find_all_implementations(modules: List[str], verbose: bool) -> int:
    """
    Find all implementations of protocols in the specified modules.
    
    Args:
        modules: List of modules to search
        verbose: Whether to show detailed information
        
    Returns:
        0 for success
    """
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            print(f"\nSearching for protocol implementations in {module_name}...")
            
            # Find all protocols in the module
            protocols = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    hasattr(obj, '_is_protocol') and obj._is_protocol):
                    protocols.append(obj)
            
            if not protocols:
                print(f"No protocols found in {module_name}")
                continue
            
            print(f"Found {len(protocols)} protocols in {module_name}")
            if verbose:
                for protocol in protocols:
                    print(f"  - {protocol.__name__}")
            
            # Find implementations for each protocol
            print("\nImplementations found:")
            implementation_count = 0
            
            for protocol in protocols:
                impls = find_protocol_implementations(module, protocol)
                if impls:
                    implementation_count += len(impls)
                    print(f"\n{protocol.__name__} ({len(impls)} implementations):")
                    for impl in impls:
                        marked = " ✓" if hasattr(impl, '__implemented_protocols__') else ""
                        print(f"  - {impl.__name__}{marked}")
            
            print(f"\nTotal: {implementation_count} implementations found")
            
        except ImportError as e:
            print(f"Error importing module {module_name}: {e}")
    
    return 0


def run_test_suite(modules: List[str], verbose: bool) -> int:
    """
    Generate and run a test suite for all protocol implementations.
    
    Args:
        modules: List of modules to test
        verbose: Whether to use verbose test output
        
    Returns:
        0 for success, 1 for test failures
    """
    print("Generating test suite for protocol implementations...")
    
    # Create a test suite for each module
    suite = unittest.TestSuite()
    for module_name in modules:
        try:
            print(f"Adding tests for {module_name}...")
            module_suite = create_protocol_test_suite(module_name)
            suite.addTest(module_suite)
        except ImportError as e:
            print(f"Error importing module {module_name}: {e}")
    
    # Run the tests
    print("\nRunning protocol implementation tests...")
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All protocol implementation tests passed!")
        return 0
    else:
        print(f"\n❌ {len(result.failures)} test failures, {len(result.errors)} errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())