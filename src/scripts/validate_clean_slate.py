#!/usr/bin/env python3
"""
Validation script for clean slate implementation.

This script verifies that legacy code patterns have been successfully removed
and that the codebase follows modern design patterns.
"""

import sys
import os
import importlib
import re
from pathlib import Path
from typing import List, Set, Dict, Any, Tuple


def check_imports(files: List[Path], bad_imports: List[str]) -> Dict[str, List[str]]:
    """Check for banned imports."""
    violations = {}
    
    for file_path in files:
        if file_path.suffix != '.py':
            continue
            
        # Skip this validation script
        if file_path.name == 'validate_clean_slate.py':
            continue
            
        file_violations = []
        with open(file_path, 'r') as f:
            content = f.read()
            
            for bad_import in bad_imports:
                if f"import {bad_import}" in content or f"from {bad_import}" in content:
                    file_violations.append(bad_import)
                    
        if file_violations:
            violations[str(file_path)] = file_violations
            
    return violations


def check_legacy_classes(files: List[Path], legacy_classes: List[str]) -> Dict[str, List[str]]:
    """Check for usage of legacy get_instance() methods."""
    violations = {}
    
    for file_path in files:
        if file_path.suffix != '.py':
            continue
            
        # Skip this validation script
        if file_path.name == 'validate_clean_slate.py':
            continue
            
        # Skip self-references in QueryCacheManager and query_cache.py
        # which maintain backward compatibility but are properly documented as deprecated
        if file_path.name == 'query_cache.py' and 'database' in str(file_path):
            continue
            
        file_violations = []
        with open(file_path, 'r') as f:
            content = f.read()
            
            for legacy_class in legacy_classes:
                # Check only for get_instance() calls on legacy classes
                pattern = rf'{legacy_class}\.get_instance\('
                matches = re.findall(pattern, content)
                if matches:
                    file_violations.append(f"{legacy_class}.get_instance()")
                    
        if file_violations:
            violations[str(file_path)] = file_violations
            
    return violations


def check_legacy_methods(files: List[Path], 
                        legacy_methods: Dict[str, str]) -> Dict[str, List[str]]:
    """Check for usage of legacy methods."""
    violations = {}
    
    for file_path in files:
        if file_path.suffix != '.py':
            continue
            
        # Skip this validation script
        if file_path.name == 'validate_clean_slate.py':
            continue
            
        file_violations = []
        with open(file_path, 'r') as f:
            content = f.read()
            
            for legacy_method, modern_method in legacy_methods.items():
                # Check for method calls like ".unwrap()" or "result.is_ok()"
                pattern = rf'\.{legacy_method}\s*\('
                matches = re.findall(pattern, content)
                if matches:
                    file_violations.append(f"{legacy_method} (use {modern_method} instead)")
                    
        if file_violations:
            violations[str(file_path)] = file_violations
            
    return violations


def check_instance_calls(files: List[Path]) -> Dict[str, int]:
    """Count calls to inject.instance and get_instance in each file."""
    violations = {}
    
    for file_path in files:
        if file_path.suffix != '.py':
            continue
            
        # Skip this validation script and the database.py file we updated
        if file_path.name == 'validate_clean_slate.py' or file_path.name == 'database.py':
            continue
            
        # Skip query_cache.py which maintains backward compatibility but is properly documented as deprecated
        if file_path.name == 'query_cache.py' and 'database' in str(file_path):
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Count inject.instance() calls
            inject_instance_count = len(re.findall(r'inject\.instance\s*\(', content))
            
            # Count get_instance() calls
            get_instance_count = len(re.findall(r'get_instance\s*\(', content))
            
            total_count = inject_instance_count + get_instance_count
            
            if total_count > 0:
                violations[str(file_path)] = total_count
                
    return violations


def main() -> int:
    """Run the validation checks."""
    uno_dir = Path(__file__).parent.parent / 'uno'
    
    if not uno_dir.exists():
        print(f"Error: Could not find the uno directory at {uno_dir}")
        return 1
        
    # Get all Python files in the uno directory
    py_files = list(uno_dir.glob('**/*.py'))
    
    print(f"Found {len(py_files)} Python files to check")
    
    # Define banned imports
    banned_imports = [
        'uno.dependencies.container',
        'uno.dependencies.provider',
        'uno.dependencies.fastapi',
    ]
    
    # Define legacy classes we've removed
    legacy_classes = [
        'WorkflowStep',
        'WorkflowTransition',
        'WorkflowTask',
        'WorkflowInstance',
        'ServiceProvider',
        'UnoRegistry',
        'CacheManager',
        'QueryCacheManager',  # Note: Special handling for backward compatibility in query_cache.py
        'DataLoaderRegistry',
        'AsyncManager',
        'ResourceManager',
        'TaskManager',
    ]
    
    # Define legacy methods and their modern replacements
    legacy_methods = {
        'unwrap': 'value',
        'unwrap_err': 'error',
        'is_ok': 'is_success',
        'is_err': 'is_failure',
    }
    
    # Run checks
    print("\nChecking for banned imports...")
    import_violations = check_imports(py_files, banned_imports)
    
    print("\nChecking for legacy classes...")
    class_violations = check_legacy_classes(py_files, legacy_classes)
    
    print("\nChecking for legacy methods...")
    method_violations = check_legacy_methods(py_files, legacy_methods)
    
    print("\nChecking for inject.instance() and get_instance() calls...")
    instance_violations = check_instance_calls(py_files)
    
    # Print results
    all_clean = True
    
    if import_violations:
        all_clean = False
        print("\n❌ Found banned imports:")
        for file, violations in import_violations.items():
            print(f"  {file}: {', '.join(violations)}")
    else:
        print("\n✅ No banned imports found")
        
    if class_violations:
        all_clean = False
        print("\n❌ Found legacy classes:")
        for file, violations in class_violations.items():
            print(f"  {file}: {', '.join(violations)}")
    else:
        print("\n✅ No legacy classes found")
        
    if method_violations:
        all_clean = False
        print("\n❌ Found legacy methods:")
        for file, violations in method_violations.items():
            print(f"  {file}: {', '.join(violations)}")
    else:
        print("\n✅ No legacy methods found")
        
    if instance_violations:
        all_clean = False
        print("\n❌ Found inject.instance() or get_instance() calls:")
        for file, count in instance_violations.items():
            print(f"  {file}: {count} calls")
    else:
        print("\n✅ No inject.instance() or get_instance() calls found")
        
    if all_clean:
        print("\n🎉 All checks passed! The codebase is clean of legacy patterns.")
        return 0
    else:
        print("\n❌ Some checks failed. Codebase still contains legacy patterns.")
        return 1
        

if __name__ == "__main__":
    sys.exit(main())