#!/usr/bin/env python
"""
Protocol Validation Script

This script analyzes the UNO codebase to identify implementations of core protocols
and validates their compliance with the expected interface. It helps track the progress
of the architectural unification effort.

Usage:
    python validate_protocol_compliance.py [--report] [--details] [--protocol PROTOCOL]

Options:
    --report    Generate a summary report of protocol compliance
    --details   Show detailed information about non-compliant implementations
    --protocol  Limit analysis to a specific protocol (Repository, Service, etc.)
"""

import ast
import importlib
import inspect
import os
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Type, Any

# Core protocol interfaces to validate
PROTOCOLS = {
    "Repository": "uno.core.protocols.RepositoryProtocol",
    "Service": "uno.core.protocols.ServiceProtocol",
    "EventBus": "uno.core.protocols.EventBusProtocol",
    "Config": "uno.dependencies.interfaces.ConfigProtocol",
    "DatabaseProvider": "uno.dependencies.interfaces.DatabaseProviderProtocol",
    "Endpoint": "uno.api.EndpointProtocol",
    "Entity": "uno.domain.protocols.entity_protocols.EntityProtocol",
    "ValueObject": "uno.domain.protocols.value_object_protocols.ValueObjectProtocol",
    "Specification": "uno.domain.protocols.specification.SpecificationProtocol",
}

@dataclass
class ProtocolImplementation:
    """Details about a protocol implementation."""
    class_name: str
    module_path: str
    file_path: str
    compliant: bool
    missing_methods: List[str] = None
    is_imported: bool = False
    
    def __post_init__(self):
        if self.missing_methods is None:
            self.missing_methods = []


@dataclass
class ProtocolInfo:
    """Information about a protocol and its expected interface."""
    name: str
    import_path: str
    methods: Set[str] = None
    implementations: List[ProtocolImplementation] = None
    
    def __post_init__(self):
        if self.methods is None:
            self.methods = set()
        if self.implementations is None:
            self.implementations = []


def find_protocol_methods(protocol_path: str) -> Set[str]:
    """Extract method names from a protocol class."""
    try:
        module_path, class_name = protocol_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        protocol_class = getattr(module, class_name)
        
        # Get methods defined in the protocol
        methods = set()
        for name, member in inspect.getmembers(protocol_class):
            if not name.startswith('_') and inspect.isfunction(member):
                methods.add(name)
        return methods
    except (ImportError, AttributeError):
        print(f"Warning: Could not import protocol {protocol_path}")
        return set()


def find_class_methods(node: ast.ClassDef) -> Set[str]:
    """Extract method names from a class definition using AST."""
    methods = set()
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            if not item.name.startswith('_') or item.name in ('__init__',):
                methods.add(item.name)
    return methods


def get_base_classes(node: ast.ClassDef) -> List[str]:
    """Extract base class names from a class definition."""
    bases = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            # Handle qualified names like module.ClassName
            bases.append(base.attr)
    return bases


def find_imported_classes(module_node: ast.Module) -> Dict[str, str]:
    """Build a map of imported class names to their fully qualified names."""
    imported = {}
    
    for node in module_node.body:
        # Handle direct imports like: from module import Class
        if isinstance(node, ast.ImportFrom) and node.module:
            for name in node.names:
                if not name.name.startswith('_'):
                    imported[name.asname or name.name] = f"{node.module}.{name.name}"
        
        # Handle regular imports like: import module
        elif isinstance(node, ast.Import):
            for name in node.names:
                imported[name.asname or name.name] = name.name
                
    return imported


def analyze_file(file_path: str, protocols: Dict[str, ProtocolInfo]) -> List[ProtocolImplementation]:
    """Analyze a Python file for protocol implementations."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError:
            print(f"Syntax error in {file_path}, skipping")
            return []
    
    implementations = []
    imports = find_imported_classes(tree)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check class name for protocol implementation indicators
            class_name = node.name
            
            # Skip test classes and base classes
            if class_name.startswith(('Test', 'Mock', 'Base')):
                continue
                
            for protocol_name, protocol_info in protocols.items():
                is_potential_impl = False
                
                # Check if class name indicates it might implement the protocol
                if protocol_name in class_name:
                    is_potential_impl = True
                
                # Check base classes
                base_classes = get_base_classes(node)
                for base in base_classes:
                    if protocol_name in base or base in ('Base' + protocol_name, protocol_name + 'Base'):
                        is_potential_impl = True
                        break
                    
                    # Check if it inherits from an imported protocol
                    if base in imports and protocol_name in imports[base]:
                        is_potential_impl = True
                        break
                
                if is_potential_impl:
                    # Check method compliance
                    class_methods = find_class_methods(node)
                    missing_methods = protocol_info.methods - class_methods
                    
                    # Determine compliance
                    is_compliant = len(missing_methods) == 0
                    
                    implementations.append(ProtocolImplementation(
                        class_name=class_name,
                        module_path=file_path_to_module_path(file_path),
                        file_path=file_path,
                        compliant=is_compliant,
                        missing_methods=list(missing_methods),
                        is_imported=any(base in imports for base in base_classes)
                    ))
    
    return implementations


def file_path_to_module_path(file_path: str) -> str:
    """Convert a file path to a Python module path."""
    parts = Path(file_path).parts
    
    # Find the src/uno index
    try:
        uno_index = parts.index('uno')
        src_index = parts.index('src')
        if src_index < uno_index:
            # Build module path from src directory
            module_parts = parts[src_index:]
        else:
            module_parts = parts[uno_index:]
    except ValueError:
        # If no src/uno, just use the file path
        module_parts = parts
    
    # Create module path and remove .py extension
    module_path = '.'.join(module_parts)
    if module_path.endswith('.py'):
        module_path = module_path[:-3]
    
    return module_path


def find_python_files(start_dir: str = 'src') -> List[str]:
    """Recursively find all Python files in a directory."""
    python_files = []
    for root, _, files in os.walk(start_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    return python_files


def initialize_protocols() -> Dict[str, ProtocolInfo]:
    """Initialize protocol information with expected methods."""
    protocol_info = {}
    
    for name, path in PROTOCOLS.items():
        methods = find_protocol_methods(path)
        protocol_info[name] = ProtocolInfo(
            name=name,
            import_path=path,
            methods=methods
        )
    
    return protocol_info


def analyze_codebase(protocols: Dict[str, ProtocolInfo], specific_protocol: Optional[str] = None) -> Dict[str, ProtocolInfo]:
    """Analyze the entire codebase for protocol implementations."""
    python_files = find_python_files()
    
    # Filter protocols if a specific one is requested
    if specific_protocol:
        if specific_protocol in protocols:
            filtered_protocols = {specific_protocol: protocols[specific_protocol]}
        else:
            print(f"Protocol {specific_protocol} not found.")
            return {}
    else:
        filtered_protocols = protocols
    
    # Analyze each file
    for file_path in python_files:
        impls = analyze_file(file_path, filtered_protocols)
        
        # Add implementations to respective protocols
        for impl in impls:
            for protocol_name, protocol_info in filtered_protocols.items():
                if protocol_name in impl.class_name:
                    protocol_info.implementations.append(impl)
    
    return filtered_protocols


def generate_report(protocols: Dict[str, ProtocolInfo], show_details: bool = False) -> None:
    """Generate a report of protocol compliance."""
    print("\nProtocol Compliance Report")
    print("=========================\n")
    
    for name, info in protocols.items():
        if not info.implementations:
            print(f"{name}: No implementations found")
            continue
        
        compliant = sum(1 for impl in info.implementations if impl.compliant)
        total = len(info.implementations)
        percentage = (compliant / total) * 100 if total > 0 else 0
        
        print(f"{name}: {compliant}/{total} implementations ({percentage:.1f}%)")
        
        if show_details and total > 0:
            print("\nImplementations:")
            for impl in info.implementations:
                status = "✓ Compliant" if impl.compliant else "✗ Non-compliant"
                print(f"  - {impl.class_name} ({impl.module_path}): {status}")
                
                if not impl.compliant and impl.missing_methods:
                    print(f"    Missing methods: {', '.join(impl.missing_methods)}")
            
            print("")  # Extra line for readability
    
    # Overall summary
    all_impls = sum(len(info.implementations) for info in protocols.values())
    all_compliant = sum(sum(1 for impl in info.implementations if impl.compliant) for info in protocols.values())
    overall_percentage = (all_compliant / all_impls) * 100 if all_impls > 0 else 0
    
    print("\nOverall Compliance:")
    print(f"{all_compliant}/{all_impls} implementations ({overall_percentage:.1f}%)")


def main() -> None:
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate protocol compliance in the UNO codebase")
    parser.add_argument("--report", action="store_true", help="Generate a summary report")
    parser.add_argument("--details", action="store_true", help="Show detailed information")
    parser.add_argument("--protocol", help="Limit analysis to a specific protocol")
    
    args = parser.parse_args()
    
    # Initialize protocols
    protocols = initialize_protocols()
    
    # Analyze codebase
    results = analyze_codebase(protocols, args.protocol)
    
    # Generate report
    if args.report or True:  # Always show report for now
        generate_report(results, args.details)


if __name__ == "__main__":
    main()