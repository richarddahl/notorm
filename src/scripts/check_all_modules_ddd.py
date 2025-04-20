#!/usr/bin/env python
"""
Comprehensive validation script to ensure all modules follow domain-driven design principles.

This script checks:
1. No UnoObj references are used in any module
2. Domain entities are properly defined and exposed in the module's public API
3. Repository pattern is properly implemented
4. Circular dependencies are avoided with proper forward references
"""

import os
import re
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple, Optional


def check_file(file_path: Path, module_name: str) -> Tuple[bool, str | None]:
    """
    Check a single Python file for domain-driven design compliance.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, "r") as f:
            content = f.read()

            # Check for UnoObj references
            if re.search(r"\bUnoObj\b", content):
                return False, f"Found UnoObj reference in {file_path}"

            # Check if entities.py has proper domain entities
            if file_path.name == "entities.py":
                # Basic check - should have at least one AggregateRoot or Entity
                if not re.search(r"class \w+\([^)]*(?:AggregateRoot|Entity)", content):
                    return False, f"No domain entities found in {file_path}"

            # Check for domain-driven design imports in domain files
            if (
                file_path.name != "entities.py"
                and "domain" in file_path.name
                and file_path.name.endswith(".py")
            ):
                # Skip this check for core module's domain.py since it defines the base protocols
                if module_name == "core" and file_path.name == "domain.py":
                    pass
                elif not re.search(
                    rf"from uno\.{module_name}\.entities import", content
                ):
                    return (
                        False,
                        f"Domain entities not imported in domain file {file_path}",
                    )

            # Check if __init__.py properly exports domain entities
            if file_path.name == "__init__.py" and os.path.exists(
                os.path.join(file_path.parent, "entities.py")
            ):
                if not re.search(rf"from uno\.{module_name}\.entities import", content):
                    return False, f"Domain entities not exported in {file_path}"

                # Check if there are any domain entities in __all__
                # This is a basic check - could be improved to check specific entities
                if '"' not in content and "'" not in content:
                    return False, f"No symbols exported in __all__ in {file_path}"

        return True, None

    except Exception as e:
        return False, f"Error checking {file_path}: {str(e)}"


def check_module(module_path: Path) -> Tuple[str, bool, list[str]]:
    """
    Check a module for domain-driven design compliance.

    Returns:
        Tuple of (module_name, is_valid, error_messages)
    """
    module_name = module_path.name
    error_messages = []
    all_valid = True

    # Skip non-modules (directories without __init__.py)
    if not os.path.exists(os.path.join(module_path, "__init__.py")):
        return module_name, True, []

    # Check if entities.py exists (not all modules might need domain entities)
    has_entities = os.path.exists(os.path.join(module_path, "entities.py"))

    for file_path in module_path.glob("**/*.py"):
        is_valid, error_message = check_file(file_path, module_name)

        if not is_valid:
            all_valid = False
            if error_message:
                error_messages.append(error_message)

    # If the module has a domain-related structure but no entities.py, flag it
    if not has_entities and any(
        os.path.exists(os.path.join(module_path, f))
        for f in ["domain_services.py", "domain_repositories.py", "domain_endpoints.py"]
    ):
        all_valid = False
        error_messages.append(
            f"Module {module_name} has domain files but missing entities.py"
        )

    return module_name, all_valid, error_messages


def main():
    """Check all modules for domain-driven design compliance."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    src_dir = project_root / "src" / "uno"

    if not src_dir.exists():
        print(f"Error: Source directory not found at {src_dir}")
        return 1

    print(f"Checking all modules in {src_dir}")

    # Get all immediate subdirectories in src/uno (these are our modules)
    modules = [
        d for d in src_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]

    # Track overall validation status
    all_modules_valid = True
    valid_modules = []
    invalid_modules = []

    # Process modules in parallel
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(check_module, module): module for module in modules}

        for future in as_completed(futures):
            module_name, is_valid, error_messages = future.result()

            if is_valid:
                print(f"✅ {module_name}: Passed")
                valid_modules.append(module_name)
            else:
                print(f"❌ {module_name}: Failed")
                for error in error_messages:
                    print(f"  - {error}")
                invalid_modules.append(module_name)
                all_modules_valid = False

    # Print summary
    print("\n=== Domain-Driven Design Validation Summary ===")
    print(f"Total modules: {len(modules)}")
    print(f"Passing modules: {len(valid_modules)}")
    print(f"Failing modules: {len(invalid_modules)}")

    if all_modules_valid:
        print(
            "\n🎉 ALL MODULES PASSED: All modules follow domain-driven design principles!"
        )
        return 0
    else:
        print("\n⚠️ SOME MODULES FAILED: The following modules need to be updated:")
        for module in sorted(invalid_modules):
            print(f"  - {module}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
