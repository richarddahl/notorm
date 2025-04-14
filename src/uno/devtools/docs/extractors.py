"""
Documentation extractors for the Uno framework.

This module provides specialized extractors for extracting documentation from
various sources, including code, docstrings, examples, and more.
"""

import inspect
import re
import ast
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Type, get_type_hints
from dataclasses import dataclass, field

from uno.core.docs.schema import DocSchema


logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of a documentation extraction."""
    content: Dict[str, Any]
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    warnings: List[str] = field(default_factory=list)


class BaseExtractor:
    """Base class for documentation extractors."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.warnings: List[str] = []
    
    def extract_from_module(self, module_name: str) -> List[ExtractionResult]:
        """
        Extract documentation from a module.
        
        Args:
            module_name: Name of the module to extract documentation from
            
        Returns:
            List of extraction results
        """
        try:
            module = importlib.import_module(module_name)
            return self.extract_from_object(module)
        except ImportError as e:
            self.warnings.append(f"Failed to import module {module_name}: {e}")
            return []
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract documentation from an object.
        
        Args:
            obj: Object to extract documentation from
            
        Returns:
            List of extraction results
        """
        raise NotImplementedError("Subclasses must implement extract_from_object")
    
    def extract_docstring(self, obj: Any) -> Dict[str, Any]:
        """
        Extract structured information from a docstring.
        
        Args:
            obj: Object with docstring
            
        Returns:
            Dictionary with extracted information
        """
        docstring = inspect.getdoc(obj)
        if not docstring:
            return {}
        
        # Parse the docstring
        return self._parse_docstring(docstring)
    
    def _parse_docstring(self, docstring: str) -> Dict[str, Any]:
        """
        Parse a docstring into structured information.
        
        Args:
            docstring: Docstring to parse
            
        Returns:
            Dictionary with extracted information
        """
        try:
            from docstring_parser import parse
            doc = parse(docstring)
            
            result = {
                "description": doc.short_description,
                "long_description": doc.long_description,
                "params": [],
                "returns": None,
                "raises": [],
                "examples": [],
                "notes": [],
                "warnings": [],
            }
            
            # Process parameters
            for param in doc.params:
                result["params"].append({
                    "name": param.arg_name,
                    "description": param.description,
                    "type": param.type_name,
                    "is_optional": param.is_optional,
                    "default": param.default,
                })
            
            # Process return value
            if doc.returns:
                result["returns"] = {
                    "description": doc.returns.description,
                    "type": doc.returns.type_name,
                }
            
            # Process exceptions
            for exception in doc.raises:
                result["raises"].append({
                    "type": exception.type_name,
                    "description": exception.description,
                })
            
            # Process examples and other metadata
            for meta in doc.meta:
                if meta.args[0].lower() == "example":
                    result["examples"].append({
                        "description": meta.description,
                    })
                elif meta.args[0].lower() == "note":
                    result["notes"].append(meta.description)
                elif meta.args[0].lower() == "warning":
                    result["warnings"].append(meta.description)
            
            return result
        except ImportError:
            # Fallback to simple parsing
            lines = docstring.split("\n")
            description = []
            current_section = "description"
            result = {
                "description": "",
                "params": [],
                "returns": None,
                "raises": [],
                "examples": [],
                "notes": [],
                "warnings": [],
            }
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                param_match = re.match(r"(?:Args|Parameters):", line)
                return_match = re.match(r"(?:Returns|Return):", line)
                raises_match = re.match(r"(?:Raises|Exceptions):", line)
                example_match = re.match(r"(?:Examples?|Usage):", line)
                note_match = re.match(r"(?:Notes?):", line)
                warning_match = re.match(r"(?:Warnings?):", line)
                
                if param_match:
                    current_section = "params"
                elif return_match:
                    current_section = "returns"
                elif raises_match:
                    current_section = "raises"
                elif example_match:
                    current_section = "examples"
                elif note_match:
                    current_section = "notes"
                elif warning_match:
                    current_section = "warnings"
                else:
                    # Add content to the current section
                    if current_section == "description":
                        description.append(line)
                    elif current_section == "params" and line.strip().startswith("- "):
                        # Parse parameter
                        param_line = line.strip()[2:].strip()
                        param_name_match = re.match(r"(\w+)(?:\s+\(([^)]+)\))?:\s*(.*)", param_line)
                        if param_name_match:
                            name, type_name, desc = param_name_match.groups()
                            result["params"].append({
                                "name": name,
                                "description": desc,
                                "type": type_name,
                                "is_optional": False,
                                "default": None,
                            })
                    elif current_section == "returns":
                        result["returns"] = {
                            "description": line,
                            "type": None,
                        }
                    elif current_section == "raises" and line.strip().startswith("- "):
                        # Parse exception
                        exception_line = line.strip()[2:].strip()
                        exception_match = re.match(r"(\w+)(?:\s*:\s*(.*))?\s*", exception_line)
                        if exception_match:
                            type_name, desc = exception_match.groups()
                            result["raises"].append({
                                "type": type_name,
                                "description": desc or "",
                            })
                    elif current_section == "examples":
                        result["examples"].append({
                            "description": line,
                        })
                    elif current_section == "notes":
                        result["notes"].append(line)
                    elif current_section == "warnings":
                        result["warnings"].append(line)
            
            # Set description
            result["description"] = "\n".join(description).strip()
            return result


class ClassExtractor(BaseExtractor):
    """Extractor for class documentation."""
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract documentation from a class.
        
        Args:
            obj: Class to extract documentation from
            
        Returns:
            List of extraction results
        """
        if not inspect.isclass(obj):
            return []
        
        # Get basic class information
        class_info = {
            "name": obj.__name__,
            "module": obj.__module__,
            "bases": [base.__name__ for base in obj.__bases__ if base != object],
            "is_dataclass": hasattr(obj, "__dataclass_fields__"),
            "is_enum": issubclass(obj, (object,)) and hasattr(obj, "__members__"),
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(obj)
        class_info.update(docstring_info)
        
        # Get type hints
        try:
            type_hints = get_type_hints(obj)
            class_info["type_hints"] = {name: str(hint) for name, hint in type_hints.items()}
        except (NameError, TypeError):
            class_info["type_hints"] = {}
        
        # Get attributes and methods
        class_info["attributes"] = []
        class_info["methods"] = []
        
        for name, member in inspect.getmembers(obj):
            # Skip private members
            if name.startswith("_") and name != "__init__":
                continue
            
            # Handle methods
            if inspect.isfunction(member):
                method_info = {
                    "name": name,
                    "signature": str(inspect.signature(member)),
                }
                
                # Get docstring information
                method_docstring = self.extract_docstring(member)
                method_info.update(method_docstring)
                
                # Get type hints
                try:
                    method_type_hints = get_type_hints(member)
                    method_info["type_hints"] = {name: str(hint) for name, hint in method_type_hints.items()}
                except (NameError, TypeError):
                    method_info["type_hints"] = {}
                
                class_info["methods"].append(method_info)
            
            # Handle attributes (class variables)
            elif not callable(member) and not name.startswith("__"):
                attr_info = {
                    "name": name,
                    "value": repr(member),
                    "type": type(member).__name__,
                }
                
                # Check for docstring in class variables
                attr_doc = getattr(obj, f"__{name}_description__", None)
                if attr_doc:
                    attr_info["description"] = attr_doc
                
                class_info["attributes"].append(attr_info)
        
        # Get source file and line number
        try:
            source_file = inspect.getsourcefile(obj)
            source_line = inspect.getsourcelines(obj)[1]
        except (TypeError, OSError):
            source_file = None
            source_line = None
        
        return [ExtractionResult(content=class_info, source_file=source_file, source_line=source_line)]


class FunctionExtractor(BaseExtractor):
    """Extractor for function documentation."""
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract documentation from a function.
        
        Args:
            obj: Function to extract documentation from
            
        Returns:
            List of extraction results
        """
        if not inspect.isfunction(obj):
            return []
        
        # Get basic function information
        function_info = {
            "name": obj.__name__,
            "module": obj.__module__,
            "signature": str(inspect.signature(obj)),
            "is_async": inspect.iscoroutinefunction(obj),
            "is_generator": inspect.isgeneratorfunction(obj),
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(obj)
        function_info.update(docstring_info)
        
        # Get type hints
        try:
            type_hints = get_type_hints(obj)
            function_info["type_hints"] = {name: str(hint) for name, hint in type_hints.items()}
        except (NameError, TypeError):
            function_info["type_hints"] = {}
        
        # Get source file and line number
        try:
            source_file = inspect.getsourcefile(obj)
            source_line = inspect.getsourcelines(obj)[1]
        except (TypeError, OSError):
            source_file = None
            source_line = None
        
        return [ExtractionResult(content=function_info, source_file=source_file, source_line=source_line)]


class ModuleExtractor(BaseExtractor):
    """Extractor for module documentation."""
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract documentation from a module.
        
        Args:
            obj: Module to extract documentation from
            
        Returns:
            List of extraction results
        """
        if not inspect.ismodule(obj):
            return []
        
        # Get basic module information
        module_info = {
            "name": obj.__name__,
            "file": getattr(obj, "__file__", None),
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(obj)
        module_info.update(docstring_info)
        
        # Get all module members
        module_info["classes"] = []
        module_info["functions"] = []
        module_info["variables"] = []
        
        for name, member in inspect.getmembers(obj):
            # Skip private members
            if name.startswith("_"):
                continue
            
            # Skip imported members
            if hasattr(member, "__module__") and member.__module__ != obj.__name__:
                continue
            
            # Handle classes
            if inspect.isclass(member):
                module_info["classes"].append(name)
            
            # Handle functions
            elif inspect.isfunction(member):
                module_info["functions"].append(name)
            
            # Handle variables
            elif not inspect.ismodule(member) and not callable(member):
                module_info["variables"].append({
                    "name": name,
                    "value": repr(member),
                    "type": type(member).__name__,
                })
        
        # Get source file
        source_file = getattr(obj, "__file__", None)
        
        return [ExtractionResult(content=module_info, source_file=source_file, source_line=1)]


class ExampleExtractor(BaseExtractor):
    """Extractor for code examples."""
    
    def __init__(self, examples_dir: Optional[str] = None):
        """
        Initialize the example extractor.
        
        Args:
            examples_dir: Directory containing code examples
        """
        super().__init__()
        self.examples_dir = examples_dir or "examples"
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract code examples related to an object.
        
        Args:
            obj: Object to extract examples for
            
        Returns:
            List of extraction results
        """
        # Only process modules
        if not inspect.ismodule(obj):
            return []
        
        # Check for example objects
        examples = []
        for name, member in inspect.getmembers(obj):
            if name.endswith("_example") and inspect.isfunction(member):
                # This is an example function
                example_info = self._extract_example_from_function(member)
                examples.append(example_info)
        
        # Check for example files
        example_files = self._find_example_files(obj.__name__)
        for file_path in example_files:
            example_info = self._extract_example_from_file(file_path, obj.__name__)
            examples.append(example_info)
        
        # Combine all examples
        if not examples:
            return []
        
        result = {
            "name": obj.__name__,
            "examples": examples,
        }
        
        return [ExtractionResult(content=result, source_file=None, source_line=None)]
    
    def _extract_example_from_function(self, func: Any) -> Dict[str, Any]:
        """
        Extract example information from a function.
        
        Args:
            func: Function to extract example from
            
        Returns:
            Dictionary with example information
        """
        # Get docstring and source
        docstring = inspect.getdoc(func) or ""
        try:
            source = inspect.getsource(func)
        except (OSError, TypeError):
            source = ""
        
        result = {
            "name": func.__name__,
            "description": docstring,
            "source": source,
            "type": "function",
        }
        
        return result
    
    def _find_example_files(self, module_name: str) -> List[str]:
        """
        Find example files for a module.
        
        Args:
            module_name: Module name
            
        Returns:
            List of example file paths
        """
        if not self.examples_dir:
            return []
        
        # Convert module name to path
        module_path = module_name.replace(".", "/")
        examples_path = Path(self.examples_dir) / module_path
        
        # Look for example files
        example_files = []
        if examples_path.exists():
            for file_path in examples_path.glob("*.py"):
                if file_path.name.endswith("_example.py") or "example" in file_path.name:
                    example_files.append(str(file_path))
        
        return example_files
    
    def _extract_example_from_file(self, file_path: str, module_name: str) -> Dict[str, Any]:
        """
        Extract example information from a file.
        
        Args:
            file_path: Path to the example file
            module_name: Related module name
            
        Returns:
            Dictionary with example information
        """
        # Read the file
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except OSError:
            return {
                "name": Path(file_path).stem,
                "description": f"Could not read example file: {file_path}",
                "source": "",
                "type": "file",
            }
        
        # Parse the file to extract docstring
        try:
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree) or ""
        except SyntaxError:
            docstring = ""
        
        result = {
            "name": Path(file_path).stem,
            "description": docstring,
            "source": content,
            "type": "file",
            "file_path": file_path,
        }
        
        return result


class APIEndpointExtractor(BaseExtractor):
    """Extractor for API endpoints."""
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract documentation from API endpoints.
        
        Args:
            obj: Object to extract endpoints from
            
        Returns:
            List of extraction results
        """
        results = []
        
        # Check for FastAPI router or app
        if hasattr(obj, "routes"):
            for route in obj.routes:
                endpoint_info = self._extract_endpoint_from_route(route)
                if endpoint_info:
                    source_file = None
                    source_line = None
                    
                    if hasattr(route, "endpoint"):
                        try:
                            source_file = inspect.getsourcefile(route.endpoint)
                            source_line = inspect.getsourcelines(route.endpoint)[1]
                        except (TypeError, OSError):
                            pass
                    
                    results.append(ExtractionResult(
                        content=endpoint_info,
                        source_file=source_file,
                        source_line=source_line
                    ))
        
        # Check for Uno endpoint classes
        elif inspect.isclass(obj) and any(base.__name__ == "UnoEndpoint" for base in obj.__mro__):
            endpoint_info = self._extract_endpoint_from_class(obj)
            if endpoint_info:
                try:
                    source_file = inspect.getsourcefile(obj)
                    source_line = inspect.getsourcelines(obj)[1]
                except (TypeError, OSError):
                    source_file = None
                    source_line = None
                
                results.append(ExtractionResult(
                    content=endpoint_info,
                    source_file=source_file,
                    source_line=source_line
                ))
        
        # Check for endpoint functions (with decorators)
        elif inspect.isfunction(obj) and hasattr(obj, "__endpoint__"):
            endpoint_info = self._extract_endpoint_from_function(obj)
            if endpoint_info:
                try:
                    source_file = inspect.getsourcefile(obj)
                    source_line = inspect.getsourcelines(obj)[1]
                except (TypeError, OSError):
                    source_file = None
                    source_line = None
                
                results.append(ExtractionResult(
                    content=endpoint_info,
                    source_file=source_file,
                    source_line=source_line
                ))
        
        return results
    
    def _extract_endpoint_from_route(self, route: Any) -> Optional[Dict[str, Any]]:
        """
        Extract endpoint information from a route.
        
        Args:
            route: FastAPI route
            
        Returns:
            Dictionary with endpoint information
        """
        if not hasattr(route, "endpoint") or not callable(route.endpoint):
            return None
        
        # Get basic endpoint information
        endpoint_info = {
            "name": route.name or "",
            "path": getattr(route, "path", ""),
            "methods": getattr(route, "methods", []),
            "description": "",
            "tags": getattr(route, "tags", []),
            "parameters": [],
            "responses": {},
            "deprecated": getattr(route, "deprecated", False),
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(route.endpoint)
        endpoint_info["description"] = docstring_info.get("description", "")
        endpoint_info["long_description"] = docstring_info.get("long_description", "")
        
        # Get parameters from signature
        try:
            sig = inspect.signature(route.endpoint)
            for name, param in sig.parameters.items():
                if name in ("self", "cls"):
                    continue
                
                param_info = {
                    "name": name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                    "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                    "required": param.default == inspect.Parameter.empty,
                }
                
                # Add description from docstring if available
                for doc_param in docstring_info.get("params", []):
                    if doc_param["name"] == name:
                        param_info["description"] = doc_param["description"]
                        break
                
                endpoint_info["parameters"].append(param_info)
        except ValueError:
            pass
        
        # Get return type
        try:
            sig = inspect.signature(route.endpoint)
            if sig.return_annotation != inspect.Signature.empty:
                endpoint_info["return_type"] = str(sig.return_annotation)
        except ValueError:
            pass
        
        # Get OpenAPI schema if available
        if hasattr(route, "openapi_schema"):
            schema = route.openapi_schema
            endpoint_info["openapi_schema"] = schema
            
            # Extract responses
            if "responses" in schema:
                endpoint_info["responses"] = schema["responses"]
        
        return endpoint_info
    
    def _extract_endpoint_from_class(self, cls: Any) -> Optional[Dict[str, Any]]:
        """
        Extract endpoint information from a class.
        
        Args:
            cls: Endpoint class
            
        Returns:
            Dictionary with endpoint information
        """
        # Get basic endpoint information
        endpoint_info = {
            "name": cls.__name__,
            "path": getattr(cls, "path", "") or getattr(cls, "__path__", ""),
            "methods": getattr(cls, "methods", []) or getattr(cls, "__methods__", []),
            "description": "",
            "tags": getattr(cls, "tags", []) or getattr(cls, "__tags__", []),
            "parameters": [],
            "responses": {},
            "deprecated": getattr(cls, "deprecated", False) or getattr(cls, "__deprecated__", False),
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(cls)
        endpoint_info["description"] = docstring_info.get("description", "")
        endpoint_info["long_description"] = docstring_info.get("long_description", "")
        
        # Look for HTTP methods
        for method_name in ("get", "post", "put", "delete", "patch", "options", "head"):
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                method_info = self._extract_endpoint_method(method)
                
                if method_name not in endpoint_info["methods"]:
                    endpoint_info["methods"].append(method_name.upper())
                
                # Merge method parameters
                for param in method_info.get("parameters", []):
                    if not any(p["name"] == param["name"] for p in endpoint_info["parameters"]):
                        endpoint_info["parameters"].append(param)
        
        return endpoint_info
    
    def _extract_endpoint_method(self, method: Any) -> Dict[str, Any]:
        """
        Extract endpoint information from a method.
        
        Args:
            method: Endpoint method
            
        Returns:
            Dictionary with method information
        """
        method_info = {
            "parameters": [],
            "responses": {},
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(method)
        
        # Get parameters from signature
        try:
            sig = inspect.signature(method)
            for name, param in sig.parameters.items():
                if name in ("self", "cls"):
                    continue
                
                param_info = {
                    "name": name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                    "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                    "required": param.default == inspect.Parameter.empty,
                }
                
                # Add description from docstring if available
                for doc_param in docstring_info.get("params", []):
                    if doc_param["name"] == name:
                        param_info["description"] = doc_param["description"]
                        break
                
                method_info["parameters"].append(param_info)
        except ValueError:
            pass
        
        return method_info
    
    def _extract_endpoint_from_function(self, func: Any) -> Optional[Dict[str, Any]]:
        """
        Extract endpoint information from a function.
        
        Args:
            func: Endpoint function
            
        Returns:
            Dictionary with endpoint information
        """
        # Get endpoint metadata
        endpoint_metadata = getattr(func, "__endpoint__", {})
        
        # Get basic endpoint information
        endpoint_info = {
            "name": func.__name__,
            "path": endpoint_metadata.get("path", ""),
            "methods": endpoint_metadata.get("methods", []),
            "description": "",
            "tags": endpoint_metadata.get("tags", []),
            "parameters": [],
            "responses": endpoint_metadata.get("responses", {}),
            "deprecated": endpoint_metadata.get("deprecated", False),
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(func)
        endpoint_info["description"] = docstring_info.get("description", "")
        endpoint_info["long_description"] = docstring_info.get("long_description", "")
        
        # Get parameters from signature
        try:
            sig = inspect.signature(func)
            for name, param in sig.parameters.items():
                if name in ("self", "cls"):
                    continue
                
                param_info = {
                    "name": name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                    "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                    "required": param.default == inspect.Parameter.empty,
                }
                
                # Add description from docstring if available
                for doc_param in docstring_info.get("params", []):
                    if doc_param["name"] == name:
                        param_info["description"] = doc_param["description"]
                        break
                
                endpoint_info["parameters"].append(param_info)
        except ValueError:
            pass
        
        # Get return type
        try:
            sig = inspect.signature(func)
            if sig.return_annotation != inspect.Signature.empty:
                endpoint_info["return_type"] = str(sig.return_annotation)
        except ValueError:
            pass
        
        return endpoint_info


class SQLExtractor(BaseExtractor):
    """Extractor for SQL-related documentation."""
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract SQL-related documentation.
        
        Args:
            obj: Object to extract SQL documentation from
            
        Returns:
            List of extraction results
        """
        results = []
        
        # Check for SQL emitter classes
        if inspect.isclass(obj) and any(hasattr(obj, attr) for attr in ("emit_sql", "generate_sql", "to_sql")):
            sql_info = self._extract_sql_from_class(obj)
            if sql_info:
                try:
                    source_file = inspect.getsourcefile(obj)
                    source_line = inspect.getsourcelines(obj)[1]
                except (TypeError, OSError):
                    source_file = None
                    source_line = None
                
                results.append(ExtractionResult(
                    content=sql_info,
                    source_file=source_file,
                    source_line=source_line
                ))
        
        # Check for SQL generation functions
        elif inspect.isfunction(obj) and any(name in obj.__name__.lower() for name in ("sql", "query", "statement")):
            sql_info = self._extract_sql_from_function(obj)
            if sql_info:
                try:
                    source_file = inspect.getsourcefile(obj)
                    source_line = inspect.getsourcelines(obj)[1]
                except (TypeError, OSError):
                    source_file = None
                    source_line = None
                
                results.append(ExtractionResult(
                    content=sql_info,
                    source_file=source_file,
                    source_line=source_line
                ))
        
        return results
    
    def _extract_sql_from_class(self, cls: Any) -> Dict[str, Any]:
        """
        Extract SQL information from a class.
        
        Args:
            cls: SQL-related class
            
        Returns:
            Dictionary with SQL information
        """
        # Get basic SQL information
        sql_info = {
            "name": cls.__name__,
            "type": "class",
            "sql_methods": [],
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(cls)
        sql_info.update(docstring_info)
        
        # Look for SQL-related methods
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if any(term in name.lower() for term in ("sql", "query", "statement")):
                method_info = {
                    "name": name,
                    "signature": str(inspect.signature(method)),
                }
                
                # Get docstring information
                method_docstring = self.extract_docstring(method)
                method_info.update(method_docstring)
                
                sql_info["sql_methods"].append(method_info)
        
        return sql_info
    
    def _extract_sql_from_function(self, func: Any) -> Dict[str, Any]:
        """
        Extract SQL information from a function.
        
        Args:
            func: SQL-related function
            
        Returns:
            Dictionary with SQL information
        """
        # Get basic SQL information
        sql_info = {
            "name": func.__name__,
            "type": "function",
            "signature": str(inspect.signature(func)),
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(func)
        sql_info.update(docstring_info)
        
        return sql_info


class ModelExtractor(BaseExtractor):
    """Extractor for model documentation."""
    
    def extract_from_object(self, obj: Any) -> List[ExtractionResult]:
        """
        Extract documentation from a model.
        
        Args:
            obj: Model to extract documentation from
            
        Returns:
            List of extraction results
        """
        if not inspect.isclass(obj):
            return []
        
        # Check if this is a model class
        is_model = (
            any(base.__name__ in ("UnoModel", "BaseModel", "Model") for base in obj.__mro__) or
            "model" in obj.__name__.lower() or
            hasattr(obj, "__tablename__") or
            hasattr(obj, "__table__")
        )
        
        if not is_model:
            return []
        
        # Get basic model information
        model_info = {
            "name": obj.__name__,
            "module": obj.__module__,
            "fields": [],
            "relationships": [],
            "methods": [],
        }
        
        # Get docstring information
        docstring_info = self.extract_docstring(obj)
        model_info.update(docstring_info)
        
        # Get SQLAlchemy table information
        if hasattr(obj, "__table__"):
            table = obj.__table__
            model_info["tablename"] = table.name
            model_info["schema"] = table.schema
            
            # Get columns
            for column in table.columns:
                field_info = {
                    "name": column.name,
                    "type": str(column.type),
                    "primary_key": column.primary_key,
                    "nullable": column.nullable,
                    "default": str(column.default) if column.default is not None else None,
                }
                
                # Get field docstring if available
                field_doc = getattr(obj, f"__{column.name}_description__", None)
                if field_doc:
                    field_info["description"] = field_doc
                
                model_info["fields"].append(field_info)
        
        # Get Pydantic fields
        elif hasattr(obj, "__fields__"):
            fields = obj.__fields__
            for name, field in fields.items():
                field_info = {
                    "name": name,
                    "type": str(field.type_),
                    "required": field.required,
                    "default": str(field.default) if field.default is not None else None,
                }
                
                # Get field docstring if available
                field_doc = getattr(obj, f"__{name}_description__", None)
                if field_doc:
                    field_info["description"] = field_doc
                
                model_info["fields"].append(field_info)
        
        # Get attributes using introspection
        else:
            for name, attr in inspect.getmembers(obj):
                # Skip private attrs, methods, and special attributes
                if name.startswith("_") or callable(attr) or name.isupper():
                    continue
                
                field_info = {
                    "name": name,
                    "type": type(attr).__name__,
                }
                
                # Get field docstring if available
                field_doc = getattr(obj, f"__{name}_description__", None)
                if field_doc:
                    field_info["description"] = field_doc
                
                model_info["fields"].append(field_info)
        
        # Get relationships (SQLAlchemy)
        if hasattr(obj, "__mapper__") and hasattr(obj.__mapper__, "relationships"):
            for name, rel in obj.__mapper__.relationships.items():
                rel_info = {
                    "name": name,
                    "target": rel.target.name,
                    "direction": str(rel.direction),
                }
                
                model_info["relationships"].append(rel_info)
        
        # Get source file and line number
        try:
            source_file = inspect.getsourcefile(obj)
            source_line = inspect.getsourcelines(obj)[1]
        except (TypeError, OSError):
            source_file = None
            source_line = None
        
        return [ExtractionResult(content=model_info, source_file=source_file, source_line=source_line)]