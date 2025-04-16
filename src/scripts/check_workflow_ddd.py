#!/usr/bin/env python3
"""
Scan the workflows module for UnoObj references and check entity imports.
"""

import os
import sys
import glob
import re

# Add src directory to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def check_file(file_path):
    """Check a single Python file for UnoObj references."""
    print(f"Checking file: {file_path}")
    with open(file_path, 'r') as f:
        content = f.read()
        
        # Check for UnoObj references
        if re.search(r'\bUnoObj\b', content):
            print(f"  WARNING: Found UnoObj reference in {file_path}")
        
        # Check if domain entities are imported
        if re.search(r'from uno\.workflows\.entities import', content):
            print(f"  OK: Domain entities are imported")
        else:
            # Check if domain entities might be used without import
            domain_entities = [
                r'\bWorkflowDef\b', 
                r'\bWorkflowTrigger\b',
                r'\bWorkflowCondition\b', 
                r'\bWorkflowAction\b',
                r'\bWorkflowRecipient\b', 
                r'\bWorkflowExecutionRecord\b',
                r'\bUser\b'
            ]
            
            for entity in domain_entities:
                # Check if the entity is used but not imported properly, ignoring type hints with quotes
                if (re.search(entity, content) 
                    and not re.search(r'from uno\.workflows\.entities import.*' + entity[2:-2], content)
                    and not re.search(r'List\["' + entity[2:-2] + r'"\]', content)
                    and not re.search(r'Optional\["' + entity[2:-2] + r'"\]', content) 
                    and not re.search(r'class\s+' + entity[2:-2] + r'\b', content)
                    and not re.search(r'def.*condition: "' + entity[2:-2] + r'"', content)):
                    print(f"  WARNING: {entity[2:-2]} might be used without proper import")

def main():
    """Scan the workflows module for UnoObj references."""
    workflows_dir = os.path.join(src_path, 'uno', 'workflows')
    
    # Scan all Python files in the workflows directory
    for py_file in glob.glob(os.path.join(workflows_dir, '*.py')):
        check_file(py_file)
    
    # Scan subdirectories
    for subdir in glob.glob(os.path.join(workflows_dir, '*/')):
        for py_file in glob.glob(os.path.join(subdir, '*.py')):
            check_file(py_file)

if __name__ == "__main__":
    main()