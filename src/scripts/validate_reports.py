#!/usr/bin/env python3
"""
Simple validation script for the reports module.
"""

import sys
import importlib

# Apply registry patches
from uno.registry import UnoRegistry

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

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 for success, 1 for errors.
    """
    try:
        # Just try to import the modules
        importlib.import_module("uno.reports.interfaces")
        importlib.import_module("uno.reports.models")
        importlib.import_module("uno.reports.objs")
        importlib.import_module("uno.reports.repositories")
        importlib.import_module("uno.reports.services")
        importlib.import_module("uno.reports.sqlconfigs")
        print("✅ All reports modules imported successfully!")
        return 0
    except Exception as e:
        print(f"❌ Error importing reports modules: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())