"""
Documentation extraction tools for Uno applications.

This module provides tools for extracting documentation from Python source code,
including docstrings, type annotations, and more.
"""

import ast
import inspect
import os
import sys
import importlib
import pkgutil
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable


def extract_docstrings(
    target: Union[str, object],
    recursive: bool = True,
    include_private: bool = False,
    include_dunder: bool = False,
    include_modules: list[str] | None = None,
    exclude_modules: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Extract docstrings from a module, class, or function.

    Args:
        target: Module name, path, or object to extract docstrings from
        recursive: Whether to recursively extract from submodules and classes
        include_private: Whether to include private members (starting with _)
        include_dunder: Whether to include dunder methods (__method__)
        include_modules: Optional list of module names to include
        exclude_modules: Optional list of module names to exclude

    Returns:
        Dictionary of extracted docstrings and metadata
    """
    result = {}

    if include_modules is None:
        include_modules = []

    if exclude_modules is None:
        exclude_modules = []

    # Handle different types of targets
    if isinstance(target, str):
        # If target is a string, try to import it as a module
        if os.path.exists(target) and os.path.isfile(target):
            # Target is a file path
            module_name = os.path.basename(target)
            if module_name.endswith(".py"):
                module_name = module_name[:-3]

            # Add directory to path temporarily
            sys.path.insert(0, os.path.dirname(target))
            try:
                module = importlib.import_module(module_name)
                result = _extract_from_object(
                    module, recursive, include_private, include_dunder
                )
            except ImportError as e:
                print(f"Error importing module from file {target}: {e}")
            finally:
                sys.path.pop(0)
        else:
            # Target is a module name
            try:
                module = importlib.import_module(target)
                result = _extract_from_object(
                    module, recursive, include_private, include_dunder
                )
            except ImportError as e:
                print(f"Error importing module {target}: {e}")
    else:
        # Target is already an object
        result = _extract_from_object(
            target, recursive, include_private, include_dunder
        )

    # Filter results based on include/exclude modules
    if include_modules or exclude_modules:
        filtered_result = {}
        for key, value in result.items():
            # Extract module name from the key
            parts = key.split(".")
            module_name = parts[0] if parts else ""

            include_item = True

            # Check exclude list first
            if exclude_modules and module_name in exclude_modules:
                include_item = False

            # Check include list if not empty
            if include_modules and module_name not in include_modules:
                include_item = False

            if include_item:
                filtered_result[key] = value

        result = filtered_result

    return result


def _extract_from_object(
    obj: Any, recursive: bool, include_private: bool, include_dunder: bool
) -> dict[str, dict[str, Any]]:
    """
    Extract docstrings from an object.

    Args:
        obj: Object to extract docstrings from
        recursive: Whether to recursively extract
        include_private: Whether to include private members
        include_dunder: Whether to include dunder methods

    Returns:
        Dictionary of extracted docstrings and metadata
    """
    result = {}

    # Get the object's docstring
    obj_name = getattr(obj, "__name__", "Unknown")
    obj_module = getattr(obj, "__module__", "")

    # Determine the full qualified name
    if obj_module:
        if obj_module == "__main__":
            full_name = obj_name
        else:
            full_name = f"{obj_module}.{obj_name}"
    else:
        full_name = obj_name

    # Extract docstring
    doc = getattr(obj, "__doc__", "")
    if doc:
        result[full_name] = {
            "docstring": doc,
            "type": _get_object_type(obj),
            "qualified_name": full_name,
            "name": obj_name,
            "module": obj_module,
        }

        # Extract signature for callables
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                result[full_name]["signature"] = str(sig)
                result[full_name]["parameters"] = [
                    {
                        "name": name,
                        "annotation": (
                            str(param.annotation)
                            if param.annotation != inspect.Parameter.empty
                            else None
                        ),
                        "default": (
                            str(param.default)
                            if param.default != inspect.Parameter.empty
                            else None
                        ),
                        "kind": str(param.kind),
                    }
                    for name, param in sig.parameters.items()
                ]
                result[full_name]["return_annotation"] = (
                    str(sig.return_annotation)
                    if sig.return_annotation != inspect.Signature.empty
                    else None
                )
            except (ValueError, TypeError):
                # Some builtins don't support signature extraction
                pass

    # Recursively extract from members if requested
    if recursive:
        for name, member in inspect.getmembers(obj):
            # Skip items based on configuration
            if name.startswith("_"):
                if name.startswith("__") and name.endswith("__"):
                    if not include_dunder:
                        continue
                elif not include_private:
                    continue

            # Skip imported modules
            if inspect.ismodule(member):
                member_module = getattr(member, "__name__", "")
                if member_module != obj_module and (
                    not member_module.startswith(f"{obj_module}.")
                ):
                    continue

            # Extract from member
            member_results = _extract_from_object(
                member, recursive, include_private, include_dunder
            )
            result.update(member_results)

    return result


def _get_object_type(obj: Any) -> str:
    """
    Determine the type of an object.

    Args:
        obj: Object to determine type for

    Returns:
        String representing the object type
    """
    if inspect.ismodule(obj):
        return "module"
    elif inspect.isclass(obj):
        return "class"
    elif inspect.isfunction(obj):
        return "function"
    elif inspect.ismethod(obj):
        return "method"
    elif inspect.isgeneratorfunction(obj):
        return "generator"
    elif inspect.iscoroutinefunction(obj):
        return "coroutine"
    elif inspect.isabstract(obj):
        return "abstract class"
    elif inspect.isroutine(obj):
        return "routine"
    else:
        return type(obj).__name__
