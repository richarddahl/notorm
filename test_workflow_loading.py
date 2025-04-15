#!/usr/bin/env python3

"""
Test script to validate workflow module loading.
"""

import inject
import logging


# Configure a basic injector to prevent initialization errors
def config(binder):
    binder.bind(logging.Logger, logging.getLogger("test"))


# Configure the injector
inject.clear_and_configure(config)

# Now try to import the workflows module
print("Starting import...")
try:
    import uno.workflows
except Exception as e:
    print(f"Import failed: {e}")
