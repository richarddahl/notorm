"""Simple script to identify import issues"""

try:
    from uno.testing.integration import *
    print("Imported successfully!")
except ImportError as e:
    print(f"Import error: {e}")
    # Print the full error with traceback
    import traceback
    traceback.print_exc()