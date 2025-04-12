"""
Extractors for documentation components.

This module provides extractors that analyze code components and extract
documentation information from them, such as descriptions, types, and examples.
"""

import inspect
import re
import ast
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type, Union, get_type_hints
from dataclasses import dataclass

from uno.core.docs.schema import (
    EndpointDoc, ParameterDoc, ModelDoc, FieldDoc, ExampleDoc,
    ParameterLocation, DocStatus
)


class DocExtractor(ABC):
    """Base class for documentation extractors."""
    
    @abstractmethod
    def extract(self, components: List[Any], config: Any) -> List[Any]:
        """
        Extract documentation from components.
        
        Args:
            components: List of components to extract documentation from
            config: Configuration for extraction
            
        Returns:
            List of extracted documentation objects
        """
        pass


class ModelExtractor(DocExtractor):
    """Extractor for data models."""
    
    def extract(self, models: List[Type], config: Any) -> List[ModelDoc]:
        """
        Extract documentation from data models.
        
        Args:
            models: List of model classes to extract documentation from
            config: Configuration for extraction
            
        Returns:
            List of ModelDoc objects
        """
        result = []
        
        for model in models:
            # Skip if internal and not including internal
            if model.__name__.startswith('_') and not config.include_internal:
                continue
                
            # Extract model documentation
            doc_str = inspect.getdoc(model) or ""
            
            # Parse docstring to get description
            description = self._parse_docstring(doc_str)
            
            # Get fields from model
            fields = self._extract_fields(model, config)
            
            # Get examples if available
            examples = self._extract_examples(model, config)
            
            # Check if deprecated
            deprecated = hasattr(model, "__deprecated__") or ".. deprecated::" in doc_str
            
            # Determine status
            status = self._determine_status(model, doc_str)
            
            # Get source file
            source_file = None
            try:
                source_file = inspect.getsourcefile(model)
            except (TypeError, OSError):
                pass
                
            # Get inherited classes
            inherits_from = []
            for base in model.__bases__:
                if base.__name__ != 'object':
                    inherits_from.append(base.__name__)
            
            # Create model doc
            model_doc = ModelDoc(
                name=model.__name__,
                description=description,
                fields=fields,
                examples=examples,
                tags=getattr(model, "__tags__", []),
                deprecated=deprecated,
                status=status,
                version=getattr(model, "__version__", None),
                source_file=source_file,
                inherits_from=inherits_from,
                metadata=getattr(model, "__metadata__", {})
            )
            
            result.append(model_doc)
            
        return result
    
    def _parse_docstring(self, doc_str: str) -> str:
        """Parse docstring to extract description."""
        if not doc_str:
            return ""
            
        # Split by sections and take the first part as description
        sections = re.split(r'\n\s*\n', doc_str)
        description = sections[0].strip()
        
        return description
    
    def _extract_fields(self, model: Type, config: Any) -> List[FieldDoc]:
        """Extract field documentation from a model."""
        fields = []
        
        # Get annotations
        try:
            annotations = get_type_hints(model)
        except (TypeError, NameError):
            annotations = getattr(model, "__annotations__", {})
        
        # Get default values
        defaults = {}
        for name, value in inspect.getmembers(model):
            if not name.startswith('_') and not inspect.ismethod(value) and not inspect.isfunction(value):
                defaults[name] = value
        
        # Add fields from dataclass if applicable
        dataclass_fields = getattr(model, "__dataclass_fields__", {})
        
        # Process each field
        for name, type_hint in annotations.items():
            if name.startswith('_') and not config.include_internal:
                continue
                
            # Get field description
            description = ""
            if hasattr(model, f"__{name}_description__"):
                description = getattr(model, f"__{name}_description__")
            else:
                # Try to find description in docstring
                doc_str = inspect.getdoc(model) or ""
                field_pattern = rf":param {name}:\s*([^\n]+)"
                match = re.search(field_pattern, doc_str)
                if match:
                    description = match.group(1).strip()
            
            # Get field properties
            field_properties = {}
            
            # Check if field is in dataclass fields
            if name in dataclass_fields:
                field_info = dataclass_fields[name]
                
                # Check if required
                field_properties["required"] = not field_info.default_factory and field_info.default is inspect.Parameter.empty
                
                # Get default value
                if field_info.default is not inspect.Parameter.empty:
                    field_properties["default"] = field_info.default
                elif field_info.default_factory is not inspect.Parameter.empty:
                    # We can't call the factory here, just note it has a default
                    field_properties["default"] = "..."
            else:
                # For non-dataclass fields, check if there's a default value
                field_properties["required"] = name not in defaults
                if name in defaults:
                    field_properties["default"] = defaults[name]
            
            # Check for validator methods to extract constraints
            validator_name = f"validate_{name}"
            if hasattr(model, validator_name):
                validator = getattr(model, validator_name)
                validator_source = inspect.getsource(validator)
                
                # Extract pattern
                pattern_match = re.search(r'match\s*\(\s*[\'"](.*?)[\'"]\s*,', validator_source)
                if pattern_match:
                    field_properties["pattern"] = pattern_match.group(1)
                
                # Extract min/max values
                min_match = re.search(r'([<>]=?)\s*(\d+)', validator_source)
                if min_match:
                    op, val = min_match.groups()
                    if op in ('>', '>='):
                        field_properties["min_value"] = int(val)
                    elif op in ('<', '<='):
                        field_properties["max_value"] = int(val)
            
            # Check if deprecated
            field_properties["deprecated"] = (
                hasattr(model, f"__{name}_deprecated__") or 
                (hasattr(model, "__deprecated_fields__") and name in getattr(model, "__deprecated_fields__"))
            )
            
            # Extract type as string
            type_str = self._type_to_string(type_hint)
            
            # Check for enum values
            enum_values = None
            if hasattr(model, f"__{name}_choices__"):
                enum_values = getattr(model, f"__{name}_choices__")
            
            # Check for examples
            example = None
            if hasattr(model, f"__{name}_example__"):
                example = getattr(model, f"__{name}_example__")
            
            # Create field doc
            field_doc = FieldDoc(
                name=name,
                description=description,
                type=type_str,
                required=field_properties.get("required", True),
                default=field_properties.get("default"),
                enum_values=enum_values,
                deprecated=field_properties.get("deprecated", False),
                pattern=field_properties.get("pattern"),
                min_value=field_properties.get("min_value"),
                max_value=field_properties.get("max_value"),
                example=example,
                metadata=getattr(model, f"__{name}_metadata__", {})
            )
            
            fields.append(field_doc)
        
        return fields
    
    def _extract_examples(self, model: Type, config: Any) -> List[ExampleDoc]:
        """Extract examples from a model."""
        examples = []
        
        # Check for class-level examples
        if hasattr(model, "__examples__"):
            model_examples = getattr(model, "__examples__")
            
            for i, example in enumerate(model_examples):
                name = f"Example {i+1}"
                if isinstance(example, dict) and "name" in example and "value" in example:
                    name = example["name"]
                    value = example["value"]
                    description = example.get("description", f"Example {i+1}")
                else:
                    value = example
                    description = f"Example {i+1}"
                
                example_doc = ExampleDoc(
                    name=name,
                    description=description,
                    value=value
                )
                
                examples.append(example_doc)
        
        return examples
    
    def _determine_status(self, model: Type, doc_str: str) -> DocStatus:
        """Determine the documentation status of a model."""
        if hasattr(model, "__status__"):
            status_str = getattr(model, "__status__").upper()
            if status_str == "STABLE":
                return DocStatus.STABLE
            elif status_str == "BETA":
                return DocStatus.BETA
            elif status_str == "ALPHA":
                return DocStatus.ALPHA
            elif status_str == "DEPRECATED":
                return DocStatus.DEPRECATED
            elif status_str == "EXPERIMENTAL":
                return DocStatus.EXPERIMENTAL
        
        # Check docstring for status indicators
        if ".. deprecated::" in doc_str:
            return DocStatus.DEPRECATED
        elif ".. warning:: This is an experimental API" in doc_str:
            return DocStatus.EXPERIMENTAL
        elif ".. note:: This API is in alpha" in doc_str:
            return DocStatus.ALPHA
        elif ".. note:: This API is in beta" in doc_str:
            return DocStatus.BETA
            
        # Default to stable
        return DocStatus.STABLE
    
    def _type_to_string(self, type_hint: Any) -> str:
        """Convert a type hint to a string representation."""
        if hasattr(type_hint, "__origin__"):
            # Handle generic types like List[str], Dict[str, int], etc.
            origin = type_hint.__origin__
            args = type_hint.__args__
            
            if origin == list:
                return f"List[{self._type_to_string(args[0])}]"
            elif origin == dict:
                return f"Dict[{self._type_to_string(args[0])}, {self._type_to_string(args[1])}]"
            elif origin == set:
                return f"Set[{self._type_to_string(args[0])}]"
            elif origin == tuple:
                if len(args) == 2 and args[1] == Ellipsis:
                    return f"Tuple[{self._type_to_string(args[0])}, ...]"
                else:
                    return f"Tuple[{', '.join(self._type_to_string(arg) for arg in args)}]"
            elif origin == Union:
                if len(args) == 2 and args[1] == type(None):
                    return f"Optional[{self._type_to_string(args[0])}]"
                else:
                    return f"Union[{', '.join(self._type_to_string(arg) for arg in args)}]"
            else:
                return str(type_hint)
        else:
            # Handle simple types
            return getattr(type_hint, "__name__", str(type_hint))


class EndpointExtractor(DocExtractor):
    """Extractor for API endpoints."""
    
    def extract(self, endpoints: List[Any], config: Any) -> List[EndpointDoc]:
        """
        Extract documentation from API endpoints.
        
        Args:
            endpoints: List of endpoint functions or classes to extract documentation from
            config: Configuration for extraction
            
        Returns:
            List of EndpointDoc objects
        """
        result = []
        
        for endpoint in endpoints:
            # Skip if internal and not including internal
            if endpoint.__name__.startswith('_') and not config.include_internal:
                continue
            
            # Handle different endpoint types
            if inspect.isfunction(endpoint):
                endpoint_docs = self._extract_from_function(endpoint, config)
                result.extend(endpoint_docs)
            elif inspect.isclass(endpoint):
                endpoint_docs = self._extract_from_class(endpoint, config)
                result.extend(endpoint_docs)
        
        return result
    
    def _extract_from_function(self, func: Any, config: Any) -> List[EndpointDoc]:
        """Extract documentation from a function-based endpoint."""
        results = []
        
        # Get decorator information
        path = "/"
        methods = ["GET"]
        
        # Try to extract path and methods from decorators
        source = inspect.getsource(func)
        
        # Look for FastAPI/Flask style decorators
        path_match = re.search(r'@\w+\.(?:get|post|put|delete|patch|options|head)\s*\(\s*[\'"]([^\'"]+)[\'"]', source)
        if path_match:
            path = path_match.group(1)
            
        method_match = re.search(r'@\w+\.(\w+)\s*\(', source)
        if method_match:
            method = method_match.group(1).upper()
            if method in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
                methods = [method]
        
        # Extract docstring
        doc_str = inspect.getdoc(func) or ""
        description = self._parse_docstring(doc_str)
        
        # Extract parameters
        parameters = self._extract_parameters_from_function(func, doc_str)
        
        # Extract responses
        responses = self._extract_responses_from_docstring(doc_str)
        
        # Check if deprecated
        deprecated = ".. deprecated::" in doc_str
        
        # Determine status
        status = self._determine_status(func, doc_str)
        
        # Get source file
        source_file = None
        try:
            source_file = inspect.getsourcefile(func)
        except (TypeError, OSError):
            pass
        
        # Create an endpoint doc for each HTTP method
        for method in methods:
            endpoint_doc = EndpointDoc(
                path=path,
                method=method,
                summary=description.split('\n')[0] if description else func.__name__,
                description=description,
                parameters=parameters,
                responses=responses,
                deprecated=deprecated,
                operation_id=func.__name__,
                handlers=[func.__name__],
                source_file=source_file,
                status=status
            )
            
            results.append(endpoint_doc)
        
        return results
    
    def _extract_from_class(self, cls: Any, config: Any) -> List[EndpointDoc]:
        """Extract documentation from a class-based endpoint."""
        results = []
        
        # Get base path from class if available
        base_path = getattr(cls, "__path__", "/")
        
        # Extract class-level docstring
        class_doc = inspect.getdoc(cls) or ""
        class_description = self._parse_docstring(class_doc)
        
        # Find HTTP method handlers
        http_methods = {"get", "post", "put", "delete", "patch", "options", "head"}
        
        for method_name, method in inspect.getmembers(cls, inspect.isfunction):
            if method_name.lower() in http_methods:
                # This is an HTTP method handler
                http_method = method_name.upper()
                
                # Extract docstring
                doc_str = inspect.getdoc(method) or ""
                description = self._parse_docstring(doc_str) or class_description
                
                # Extract parameters
                parameters = self._extract_parameters_from_function(method, doc_str)
                
                # Extract responses
                responses = self._extract_responses_from_docstring(doc_str)
                
                # Check if deprecated
                deprecated = ".. deprecated::" in doc_str or ".. deprecated::" in class_doc
                
                # Determine status
                status = self._determine_status(method, doc_str)
                if status == DocStatus.STABLE and ".. deprecated::" in class_doc:
                    status = DocStatus.DEPRECATED
                
                # Get source file
                source_file = None
                try:
                    source_file = inspect.getsourcefile(method)
                except (TypeError, OSError):
                    pass
                
                # Create endpoint doc
                endpoint_doc = EndpointDoc(
                    path=base_path,
                    method=http_method,
                    summary=description.split('\n')[0] if description else method.__name__,
                    description=description,
                    parameters=parameters,
                    responses=responses,
                    deprecated=deprecated,
                    operation_id=f"{cls.__name__}_{method.__name__}",
                    handlers=[f"{cls.__name__}.{method.__name__}"],
                    source_file=source_file,
                    status=status
                )
                
                results.append(endpoint_doc)
        
        return results
    
    def _parse_docstring(self, doc_str: str) -> str:
        """Parse docstring to extract description."""
        if not doc_str:
            return ""
            
        # Split by sections and take the first part as description
        sections = re.split(r'\n\s*\n', doc_str)
        description = sections[0].strip()
        
        return description
    
    def _extract_parameters_from_function(self, func: Any, doc_str: str) -> List[ParameterDoc]:
        """Extract parameters from a function."""
        parameters = []
        
        # Get signature parameters
        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            return parameters
        
        # Skip self/cls parameter
        skip_params = {"self", "cls"}
        
        for name, param in sig.parameters.items():
            if name in skip_params:
                continue
                
            # Get parameter type
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                param_type = "Any"
            
            # Get parameter description from docstring
            description = ""
            param_pattern = rf":param {name}:\s*([^\n]+)"
            match = re.search(param_pattern, doc_str)
            if match:
                description = match.group(1).strip()
            
            # Determine parameter location
            location = ParameterLocation.QUERY  # Default
            if "path" in name.lower() or name == "id":
                location = ParameterLocation.PATH
            elif "header" in name.lower() or name.lower().endswith("_header"):
                location = ParameterLocation.HEADER
            elif "cookie" in name.lower():
                location = ParameterLocation.COOKIE
            elif "body" in name.lower() or param_type.__name__ in ["dict", "list", "Dict", "List"]:
                location = ParameterLocation.BODY
            
            # Determine if required
            required = param.default == inspect.Parameter.empty
            
            # Get default value
            default = None
            if param.default != inspect.Parameter.empty:
                default = param.default
            
            # Create parameter doc
            param_doc = ParameterDoc(
                name=name,
                description=description,
                type=self._type_to_string(param_type),
                location=location,
                required=required,
                default=default
            )
            
            parameters.append(param_doc)
        
        return parameters
    
    def _extract_responses_from_docstring(self, doc_str: str) -> Dict[int, Any]:
        """Extract response information from docstring."""
        responses = {}
        
        # Look for response descriptions
        return_match = re.search(r':return:\s*([^\n]+)', doc_str)
        if return_match:
            description = return_match.group(1).strip()
            responses[200] = {
                "description": description,
                "content_type": "application/json"
            }
        
        # Look for error responses
        error_pattern = r':raises\s+(\w+):\s*([^\n]+)'
        for error_match in re.finditer(error_pattern, doc_str):
            error_class = error_match.group(1)
            error_desc = error_match.group(2).strip()
            
            status_code = 500  # Default for exceptions
            if "NotFound" in error_class:
                status_code = 404
            elif "Unauthorized" in error_class or "Permission" in error_class:
                status_code = 403
            elif "BadRequest" in error_class or "Validation" in error_class:
                status_code = 400
            
            responses[status_code] = {
                "description": f"{error_class}: {error_desc}",
                "content_type": "application/json"
            }
        
        return responses
    
    def _determine_status(self, func: Any, doc_str: str) -> DocStatus:
        """Determine the documentation status of an endpoint."""
        # Check for status indicators in docstring
        if ".. deprecated::" in doc_str:
            return DocStatus.DEPRECATED
        elif ".. warning:: This is an experimental API" in doc_str:
            return DocStatus.EXPERIMENTAL
        elif ".. note:: This API is in alpha" in doc_str:
            return DocStatus.ALPHA
        elif ".. note:: This API is in beta" in doc_str:
            return DocStatus.BETA
            
        # Default to stable
        return DocStatus.STABLE
    
    def _type_to_string(self, type_hint: Any) -> str:
        """Convert a type hint to a string representation."""
        if hasattr(type_hint, "__origin__"):
            # Handle generic types like List[str], Dict[str, int], etc.
            origin = type_hint.__origin__
            args = type_hint.__args__
            
            if origin == list:
                return f"List[{self._type_to_string(args[0])}]"
            elif origin == dict:
                return f"Dict[{self._type_to_string(args[0])}, {self._type_to_string(args[1])}]"
            elif origin == set:
                return f"Set[{self._type_to_string(args[0])}]"
            elif origin == tuple:
                if len(args) == 2 and args[1] == Ellipsis:
                    return f"Tuple[{self._type_to_string(args[0])}, ...]"
                else:
                    return f"Tuple[{', '.join(self._type_to_string(arg) for arg in args)}]"
            elif origin == Union:
                if len(args) == 2 and args[1] == type(None):
                    return f"Optional[{self._type_to_string(args[0])}]"
                else:
                    return f"Union[{', '.join(self._type_to_string(arg) for arg in args)}]"
            else:
                return str(type_hint)
        else:
            # Handle simple types
            return getattr(type_hint, "__name__", str(type_hint))


class SchemaExtractor(DocExtractor):
    """Extractor for API schemas."""
    
    def extract(self, schemas: List[Any], config: Any) -> List[Any]:
        """
        Extract documentation from API schemas.
        
        Args:
            schemas: List of schema objects to extract documentation from
            config: Configuration for extraction
            
        Returns:
            List of extracted schema documentation objects
        """
        # This is a placeholder implementation
        # The actual implementation would depend on the schema format
        return []