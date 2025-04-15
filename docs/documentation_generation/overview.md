# Documentation Generation

The uno framework includes a powerful documentation generation system that automatically creates comprehensive API documentation from your code.

## Overview

The documentation generation system analyzes your codebase to extract information about:

- API endpoints and their parameters
- Data models and their fields
- Security schemes
- Examples and use cases

This information is then rendered into various formats, such as Markdown, OpenAPI (Swagger), HTML, and AsciiDoc.

## Key Features

- **Code-Driven Documentation**: Documentation is generated directly from your code, keeping it in sync with your implementation
- **Multiple Output Formats**: Generate documentation in Markdown, OpenAPI, HTML, and AsciiDoc
- **Automatic Component Discovery**: Automatically finds and documents models, endpoints, and other components
- **Customizable**: Configure what components to include and how to render them
- **Extensible**: Add custom extractors and renderers for specialized components

## Basic Usage

To generate documentation for your application:

```python
from uno.core.docs.generator import DocGeneratorConfig, DocFormat, generate_docs

# Configure the documentation generator
config = DocGeneratorConfig(
    title="My API Documentation",
    description="Documentation for my API",
    version="1.0.0",
    formats=[DocFormat.MARKDOWN, DocFormat.OPENAPI],
    output_dir="docs/api",
    modules_to_document=["my_app.api", "my_app.models"]
)

# Generate documentation
generate_docs(config)
```

## Command-Line Interface

The documentation generator can be used from the command line in two ways:

### Core CLI

For standard API documentation:

```bash
python -m uno.core.docs.cli --title "My API" --modules my_app.api my_app.models
```

### Developer Documentation CLI

For comprehensive developer documentation with additional features:

```bash
python -m src.scripts.generate_docs --dev --playground --include-internal --modules my_app
```

This enhanced CLI provides:
- Interactive code playgrounds (when used with HTML format)
- Documentation for tests and benchmarks
- More detailed internal component documentation
- Support for additional formats and renderers

## Documentation Sources

The documentation generator extracts information from:

### Class and Function Docstrings

```python
def get_user(user_id: str) -> Dict[str, Any]:```

"""
Retrieve a user by ID.
``````

```
```

This endpoint returns the user information for the specified user ID.
``````

```
```

:param user_id: The ID of the user to retrieve
:return: User information
:raises UserNotFoundError: If the user does not exist
"""
# Implementation
```
```

### Type Annotations

```python
def create_user(```

name: str,
email: str,
roles: List[str] = [],
is_active: bool = True
```
) -> Dict[str, Any]:```

# Implementation
```
```

### Special Attributes

```python
class UserModel:```

# Field documentation
__email_description__ = "Email address of the user"
``````

```
```

# Field examples
__email_example__ = "user@example.com"
``````

```
```

# Field choices
__roles_choices__ = ["admin", "user", "guest"]
``````

```
```

# Model status
__status__ = "beta"
``````

```
```

# Model examples
__examples__ = [```

{
    "name": "Example User",
    "value": {"id": "usr_123", "name": "Test User"}
}
```
]
```
```

## Component Discovery

The documentation generator automatically discovers components to document:

- **Models**: Classes with dataclass decorators, Pydantic models, or classes with "Model", "Schema", "DTO", or "Entity" in their name
- **Endpoints**: Functions decorated with FastAPI/Flask decorators or classes with HTTP method handlers
- **Security Schemes**: Security configurations in your API setup

## Documentation Structure

The generated documentation is organized as follows:

- **Index**: Overview of all documented components
- **Endpoints**: Grouped by tag or module
- **Models**: Grouped by first letter or module
- **Security**: Authentication and authorization methods

## Next Steps

- Learn how to [configure the documentation generator](configuration.md)
- Explore documentation [extractors](extractors.md) for customized information extraction
- Customize documentation with different output formats
- See practical examples of documentation generation in the codebase