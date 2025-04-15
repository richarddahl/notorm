# Documentation Extractors

Extractors are responsible for analyzing code components and extracting documentation information from them, such as descriptions, types, and examples.

## Overview

The Uno documentation framework uses extractors to gather information from different types of components:

- **ModelExtractor**: Extracts documentation from data models
- **EndpointExtractor**: Extracts documentation from API endpoints
- **SchemaExtractor**: Extracts documentation from API schemas

Each extractor implements the `DocExtractor` interface and provides an `extract` method that takes a list of components and returns a list of documentation objects.

## How Extractors Work

Extractors use various techniques to gather documentation information:

1. **Parse docstrings** to extract descriptions and parameter details
2. **Analyze type annotations** to determine parameter and return types
3. **Inspect class attributes** for special documentation attributes
4. **Examine method signatures** to identify parameters and their properties
5. **Look for decorators** to identify API endpoints and their routes

## Built-in Extractors

### ModelExtractor

Extracts documentation from data model classes:

```python
from uno.core.docs.extractors import ModelExtractor

# Create model extractor
extractor = ModelExtractor()

# Extract documentation from model classes
model_docs = extractor.extract(model_classes, config)
```

The `ModelExtractor` looks for:

- **Class docstrings** for model descriptions
- **Field annotations** for field types
- **Special attributes** like `__field_description__`, `__field_example__`, etc.
- **Validator methods** to extract constraints
- **Dataclass fields** or Pydantic fields
- **Examples** defined in special attributes

### EndpointExtractor

Extracts documentation from API endpoint functions or classes:

```python
from uno.core.docs.extractors import EndpointExtractor

# Create endpoint extractor
extractor = EndpointExtractor()

# Extract documentation from endpoint functions or classes
endpoint_docs = extractor.extract(endpoints, config)
```

The `EndpointExtractor` looks for:

- **Function docstrings** for endpoint descriptions
- **Decorator information** to determine paths and HTTP methods
- **Parameter annotations** for parameter types
- **Parameter descriptions** in docstrings
- **Response information** in docstrings
- **Error information** in docstrings

### SchemaExtractor

Extracts documentation from API schemas:

```python
from uno.core.docs.extractors import SchemaExtractor

# Create schema extractor
extractor = SchemaExtractor()

# Extract documentation from API schemas
schema_docs = extractor.extract(schemas, config)
```

## Custom Extractors

You can create custom extractors by implementing the `DocExtractor` interface:

```python
from abc import ABC, abstractmethod
from typing import Any, List
from uno.core.docs.extractors import DocExtractor

class CustomExtractor(DocExtractor):```

"""Custom extractor for specialized components."""
``````

```
```

def extract(self, components: List[Any], config: Any) -> List[Any]:```

"""
Extract documentation from components.
``````

```
```

Args:
    components: List of components to extract documentation from
    config: Configuration for extraction
    
Returns:
    List of extracted documentation objects
"""
result = []
``````

```
```

for component in components:
    # Extract information from the component
    # ...
    
    # Create documentation object
    doc = {
        "name": component.__name__,
        "description": "..."
        # ...
    }
    
    result.append(doc)
``````

```
```

return result
```
```
```

## Registering Extractors

To use a custom extractor, register it with the `DocGenerator`:

```python
from uno.core.docs.generator import DocGenerator, DocGeneratorConfig

# Create config and generator
config = DocGeneratorConfig(...)
generator = DocGenerator(config)

# Register custom extractor
generator.register_extractor("custom", CustomExtractor())

# Generate documentation
generator.generate()
```

## Extraction Techniques

### Docstring Parsing

Extractors parse docstrings to get descriptions and parameter information:

```python
def _parse_docstring(self, doc_str: str) -> str:```

"""Parse docstring to extract description."""
if not doc_str:```

return ""
```
    
# Split by sections and take the first part as description
sections = re.split(r'\n\s*\n', doc_str)
description = sections[0].strip()
``````

```
```

return description
```
```

### Type Extraction

Extractors convert type annotations to string representations:

```python
def _type_to_string(self, type_hint: Any) -> str:```

"""Convert a type hint to a string representation."""
if hasattr(type_hint, "__origin__"):```

# Handle generic types like List[str], Dict[str, int], etc.
origin = type_hint.__origin__
args = type_hint.__args__
``````

```
```

if origin == list:
    return f"List[{self._type_to_string(args[0])}]"
# ...
```
else:```

# Handle simple types
return getattr(type_hint, "__name__", str(type_hint))
```
```
```

### Parameter Extraction

Extractors analyze function signatures to extract parameter information:

```python
def _extract_parameters_from_function(self, func: Any, doc_str: str) -> List[ParameterDoc]:```

"""Extract parameters from a function."""
parameters = []
``````

```
```

# Get signature parameters
try:```

sig = inspect.signature(func)
```
except (ValueError, TypeError):```

return parameters
```
``````

```
```

for name, param in sig.parameters.items():```

if name == "self" or name == "cls":
    continue
    
# Get parameter type
param_type = param.annotation
if param_type == inspect.Parameter.empty:
    param_type = "Any"
``````

```
```

# Get parameter description from docstring
description = ""
param_pattern = rf":param {name}:\s*([^\n]+)"
match = re.search(param_pattern, doc_str)
if match:
    description = match.group(1).strip()
``````

```
```

# Create parameter doc
param_doc = ParameterDoc(
    name=name,
    description=description,
    type=self._type_to_string(param_type),
    # ...
)
``````

```
```

parameters.append(param_doc)
```
``````

```
```

return parameters
```
```

## Best Practices

1. **Comprehensive Docstrings**: Write clear, detailed docstrings for classes and functions
2. **Parameter Documentation**: Document all parameters with descriptions
3. **Return Documentation**: Document return values with descriptions
4. **Error Documentation**: Document potential errors with `:raises` sections
5. **Type Annotations**: Use type annotations for all parameters and return values
6. **Examples**: Provide examples for models and endpoints
7. **Validator Methods**: Implement validator methods to document constraints

## Next Steps

- Learn how to customize renderers to output documentation in different formats
- Explore the command-line interface for generating documentation (`src/scripts/generate_docs.py`)
- See practical examples of documentation generation in the source code