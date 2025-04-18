#!/usr/bin/env python
"""
Generate Architecture Documentation

This script generates markdown documentation from Python source code
for the unified architecture, focusing on protocol definitions and
base implementations.

Usage:
    python generate_architecture_docs.py [--output-dir OUTPUT_DIR]

Options:
    --output-dir    Directory to write documentation files (default: docs/reference)
"""

import argparse
import ast
import inspect
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def extract_docstring(node: ast.AST) -> Optional[str]:
    """Extract docstring from an AST node."""
    if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    
    if not node.body:
        return None
    
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Str):
        return first.value.s
    return None


def extract_class_info(node: ast.ClassDef, module_path: str) -> Dict:
    """Extract information about a class from its AST node."""
    docstring = extract_docstring(node)
    bases = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            bases.append(f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr)
    
    methods = []
    properties = []
    
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_docstring = extract_docstring(item)
            is_property = any(
                isinstance(d, ast.Name) and d.id == "property"
                for d in item.decorator_list
            )
            
            if is_property:
                properties.append({
                    "name": item.name,
                    "docstring": method_docstring,
                    "async": isinstance(item, ast.AsyncFunctionDef),
                })
            else:
                methods.append({
                    "name": item.name,
                    "docstring": method_docstring,
                    "async": isinstance(item, ast.AsyncFunctionDef),
                    "is_abstractmethod": any(
                        isinstance(d, ast.Name) and d.id == "abstractmethod" 
                        for d in item.decorator_list
                    ),
                })
    
    return {
        "name": node.name,
        "docstring": docstring,
        "bases": bases,
        "methods": methods,
        "properties": properties,
        "module_path": module_path,
    }


def extract_module_info(file_path: str) -> Dict:
    """Extract information about a module from its file path."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        print(f"Syntax error in {file_path}, skipping")
        return {"classes": [], "docstring": None, "path": file_path}
    
    docstring = extract_docstring(tree)
    classes = []
    
    # Convert file path to module path
    parts = Path(file_path).parts
    try:
        uno_index = parts.index('uno')
        module_path = '.'.join(parts[uno_index:]).replace('.py', '')
    except ValueError:
        module_path = os.path.basename(file_path).replace('.py', '')
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(extract_class_info(node, module_path))
    
    return {
        "path": file_path,
        "docstring": docstring,
        "classes": classes,
    }


def generate_class_docs(class_info: Dict) -> str:
    """Generate markdown documentation for a class."""
    lines = []
    name = class_info["name"]
    
    # Class header
    lines.append(f"## {name}")
    lines.append("")
    
    # Module path
    lines.append(f"*Defined in `{class_info['module_path']}`*")
    lines.append("")
    
    # Base classes
    if class_info["bases"]:
        lines.append("**Inherits from:** " + ", ".join(f"`{base}`" for base in class_info["bases"]))
        lines.append("")
    
    # Class docstring
    if class_info["docstring"]:
        lines.append(class_info["docstring"])
        lines.append("")
    
    # Properties
    if class_info["properties"]:
        lines.append("### Properties")
        lines.append("")
        
        for prop in class_info["properties"]:
            lines.append(f"#### `{prop['name']}`")
            lines.append("")
            if prop["docstring"]:
                lines.append(prop["docstring"])
                lines.append("")
    
    # Methods
    if class_info["methods"]:
        lines.append("### Methods")
        lines.append("")
        
        for method in class_info["methods"]:
            # Skip private methods
            if method["name"].startswith("_") and method["name"] != "__init__":
                continue
                
            prefix = "async " if method["async"] else ""
            lines.append(f"#### `{prefix}{method['name']}()`")
            lines.append("")
            
            if method["is_abstractmethod"]:
                lines.append("*Abstract method*")
                lines.append("")
                
            if method["docstring"]:
                lines.append(method["docstring"])
                lines.append("")
    
    return "\n".join(lines)


def generate_module_docs(module_info: Dict) -> str:
    """Generate markdown documentation for a module."""
    lines = []
    module_name = os.path.basename(module_info["path"]).replace(".py", "")
    
    # Module header
    lines.append(f"# {module_name.capitalize()}")
    lines.append("")
    
    # Module path
    lines.append(f"*Defined in `{module_info['path']}`*")
    lines.append("")
    
    # Module docstring
    if module_info["docstring"]:
        lines.append(module_info["docstring"])
        lines.append("")
    
    # Classes
    for class_info in module_info["classes"]:
        lines.append(generate_class_docs(class_info))
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate architecture documentation")
    parser.add_argument("--output-dir", default="docs/reference", help="Output directory for documentation files")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Files to process - focusing on the core architecture
    # This would be expanded as more files are implemented
    core_protocols = [
        "src/uno/core/protocols/repository.py",
        "src/uno/core/protocols/service.py",
        "src/uno/core/protocols/event.py",
        "src/uno/core/protocols/entity.py",
    ]
    core_errors = [
        "src/uno/core/errors/result.py",
        "src/uno/core/errors/catalog.py",
    ]
    domain_base = [
        "src/uno/domain/common/entities/base_entity.py",
        "src/uno/domain/common/value_objects/base_value_object.py",
    ]
    
    files_to_process = []
    
    # Check which files exist and add them to the processing list
    for file_list in [core_protocols, core_errors, domain_base]:
        for file_path in file_list:
            if os.path.exists(file_path):
                files_to_process.append(file_path)
            else:
                print(f"Warning: {file_path} does not exist, skipping")
    
    # Process files
    for file_path in files_to_process:
        print(f"Processing {file_path}...")
        module_info = extract_module_info(file_path)
        markdown = generate_module_docs(module_info)
        
        # Determine output path
        path_parts = Path(file_path).parts
        try:
            # Get the path after src/uno
            uno_index = path_parts.index('uno')
            relative_path = Path(*path_parts[uno_index+1:])
            
            # Create output directory
            output_dir = Path(args.output_dir) / relative_path.parent
            os.makedirs(output_dir, exist_ok=True)
            
            # Create output file
            output_file = output_dir / f"{relative_path.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
                
            print(f"Generated {output_file}")
        except ValueError:
            print(f"Could not determine output path for {file_path}, skipping")
    
    print("Documentation generation complete!")


if __name__ == "__main__":
    main()