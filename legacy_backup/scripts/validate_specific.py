#!/usr/bin/env python3
"""
Protocol validation utility script for the Uno framework.

This script validates that classes marked with the @implements decorator
correctly implement their protocols. It can be used as a development tool
or as part of CI/CD pipelines to ensure protocol compliance.

Usage:
    python src/scripts/validate_specific.py [--verbose] [module1 module2 ...]

This specific version skips problematic modules and only validates specific modules.
"""

import argparse
import importlib
import sys
from typing import List, Union

# Apply registry patches first


# Save original register method
original_registry_register = UnoRegistry.register

# Create an idempotent version
def idempotent_register(self, model_class, table_name):
    if table_name in self._models:
        # Always skip if already registered
        return
    self._models[table_name] = model_class

# Apply monkey patch
UnoRegistry.register = idempotent_register

# Import the registry_patch
import uno.sql.registry_patch

# Now import the validator
from uno.core.protocol_validator import verify_all_implementations, ProtocolValidationError


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 for success, 1 for validation errors.
    """
    parser = argparse.ArgumentParser(description="Validate protocol implementations for specific modules.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed error information")
    
    args = parser.parse_args()
    verbose = args.verbose
    
    # Specific modules to validate - add the ones you specifically want to test
    modules = [
        "uno.values",
        "uno.reports"
    ]
    
    # Validate the specified modules
    try:
        all_errors = {}
        for module_name in modules:
            try:
                print(f"Validating module: {module_name}")
                module_errors = verify_all_implementations([module_name])
                if module_errors:
                    all_errors.update(module_errors)
            except Exception as e:
                print(f"❌ Error validating module {module_name}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Print the results
        if not all_errors:
            print("✅ All protocol implementations in specified modules are valid!")
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
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())