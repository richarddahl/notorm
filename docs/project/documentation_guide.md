# Documentation Guide

This guide explains how to contribute to and maintain the Uno Framework documentation.

## Documentation Structure

The Uno Framework documentation follows a structured organization:

1. **Home Page**: Introduction and high-level overview (`index.md`)
2. **Getting Started**: Quick setup guide (`getting_started.md`)
3. **Tutorials**: Step-by-step guides for specific tasks
4. **Architecture**: System design and architectural concepts
5. **Core**: Core framework components 
6. **Domain**: Domain-driven design implementation
7. **API**: API endpoint framework
8. **Database**: Database access and management
9. **Vector Search**: Vector search capabilities
10. **Infrastructure**: Technical implementations
11. **Application**: Application layer components
12. **Features**: Specific features
13. **Developer Tools**: Development utilities
14. **Deployment**: Deployment guidance
15. **Reference**: Command and API references
16. **Project**: Project information

## Documentation Standards

All documentation should follow these standards:

### File Naming and Structure

1. **File Names**: Use lowercase with underscores (`file_name.md`)
2. **Directory Structure**:
   - Primary categories are top-level directories
   - Subcategories are subdirectories
   - Example: `core/events/index.md`

### Content Guidelines

1. **Document Structure**:
   - Start with H1 title (`# Title`)
   - Include a brief description
   - Use H2 headings (`## Section`) for main sections
   - Use H3 headings (`### Subsection`) for subsections

2. **Code Examples**:
   - Include language identifier (```python)
   - Include imports
   - Add comments for clarity
   - Keep examples concise but complete

3. **Markdown Syntax**:
   - Use proper Markdown syntax
   - Use bullet points and numbered lists appropriately
   - Use code blocks for code examples
   - Use admonitions for notes, warnings, etc.

### Example Document Template

```markdown
# Component Name

Brief description of the component and its purpose.

## Overview

Detailed description of the component, its role in the framework, and key concepts.

## Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Usage

Basic usage example:

```python
from uno.module import Component

# Create a component
component = Component()

# Use the component
result = component.method()
```

## Implementation Details

Explanation of how the component is implemented.

### Subcomponent 1

Details about subcomponent 1.

### Subcomponent 2

Details about subcomponent 2.

## API Reference

### `Component` class

```python
class Component:
    """Component docstring."""
    
    def method(self, arg1: str, arg2: int) -> Result[str, Error]:
        """Method docstring.
        
        Args:
            arg1: Description of arg1
            arg2: Description of arg2
            
        Returns:
            Result with successful operation or error
        """
```

## Examples

### Basic Example

```python
# Basic example
```

### Advanced Example

```python
# Advanced example
```

## Best Practices

1. Best practice 1
2. Best practice 2
3. Best practice 3

## Common Pitfalls

- Pitfall 1: How to avoid it
- Pitfall 2: How to avoid it

## Related Components

- [Related Component 1](../related/component1.md)
- [Related Component 2](../related/component2.md)
```

## Adding New Documentation

### 1. Create the Markdown File

Create the new Markdown file in the appropriate directory:

```bash
mkdir -p docs/category/subcategory
touch docs/category/subcategory/new_document.md
```

### 2. Update mkdocs.yml

Add the new document to the navigation structure in `mkdocs.yml`:

```yaml
nav:
  - Category:
      - Subcategory:
          - Document Title: category/subcategory/new_document.md
```

### 3. Link from Other Documents

Add links to the new document from related documents:

```markdown
For more information, see [Document Title](../category/subcategory/new_document.md).
```

## Updating Existing Documentation

When updating existing documentation:

1. Ensure the document follows the standard structure
2. Maintain the existing heading hierarchy
3. Update code examples to use the latest syntax
4. Verify links to other documents still work
5. Add new sections at the appropriate position in the document

## Using Admonitions

Use admonitions to highlight important information:

```markdown
!!! note
    This is a note admonition.

!!! warning
    This is a warning admonition.

!!! tip
    This is a tip admonition.

!!! example
    This is an example admonition.
```

These will render as:

!!! note
    This is a note admonition.

!!! warning
    This is a warning admonition.

!!! tip
    This is a tip admonition.

!!! example
    This is an example admonition.

## Adding Images

Store images in the `docs/assets/images/` directory and reference them:

```markdown
![Image Alt Text](../assets/images/image_name.png)
```

## Building the Documentation

To build and preview the documentation locally:

```bash
# Install MkDocs and required plugins
pip install mkdocs mkdocs-material mkdocstrings pymdown-extensions

# Serve the documentation
mkdocs serve

# Build the documentation
mkdocs build
```

## Documentation Priorities

When adding new documentation, prioritize these areas:

1. Core components (events, unit of work, error handling)
2. Domain modeling (entities, repositories, services)
3. API endpoint framework
4. Database integration
5. Vector search capabilities
6. Tutorials and migration guides

## Maintaining Consistent Terminology

Use consistent terminology throughout the documentation:

- **Entity**: Domain model object with identity
- **Value Object**: Immutable object defined by its attributes
- **Repository**: Data access abstraction
- **Service**: Business logic component
- **Unit of Work**: Transaction management
- **Event**: Domain event
- **Endpoint**: HTTP API endpoint
- **DTO**: Data Transfer Object
- **Result**: Success/failure container

## Documentation Checklist

Use this checklist before submitting documentation changes:

- [ ] Document follows standard structure
- [ ] Code examples are complete and correct
- [ ] Links to other documents work
- [ ] Terminology is consistent
- [ ] Document is added to mkdocs.yml
- [ ] Images are properly referenced
- [ ] Admonitions are used appropriately
- [ ] Document builds without errors

## Conclusion

Following these guidelines will help maintain a consistent, high-quality documentation suite for the Uno Framework. For questions or assistance, please reach out to the documentation team.