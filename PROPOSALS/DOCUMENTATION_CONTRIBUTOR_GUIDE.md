# Documentation Contributor Guide

This guide is designed to help contributors create and update documentation for uno. Following these guidelines will help ensure that documentation is consistent, accurate, and easy to understand.

## Getting Started

### Documentation Structure

The uno documentation is organized into several key sections:

1. **Overview Pages**: High-level introductions to major components
2. **API References**: Detailed documentation of classes, methods, and functions
3. **Tutorials**: Step-by-step guides for common tasks
4. **Examples**: Practical code examples demonstrating usage
5. **Concepts**: Explanations of core concepts and architecture

Documentation files are stored in the `/docs` directory, organized by component:

```
/docs/
  ├── architecture/     # System architecture documentation
  ├── api/              # API reference documentation
  ├── database/         # Database component documentation
  ├── business_logic/   # Business logic layer documentation
  ├── queries/          # Query system documentation
  ├── workflows/        # Workflow system documentation
  ├── ...
```

### Documentation Format

All documentation is written in Markdown with the following conventions:

- Use ATX-style headers (`#` for H1, `##` for H2, etc.)
- Use fenced code blocks with language identifiers
- Use relative links for cross-references to other documentation files
- Use absolute paths starting with `/docs/` for cross-component references
- Include alt text for all images

## Writing Standards

### Style Guidelines

1. **Voice and Tone**
   - Use a clear, direct, and professional tone
   - Address the reader directly using "you" rather than "the user"
   - Use present tense and active voice where possible

2. **Structure**
   - Begin each document with a clear introduction that states its purpose
   - Use descriptive headings to organize content
   - Include a "Related Documentation" section at the end
   - Keep paragraphs focused on a single idea

3. **Language**
   - Define technical terms when first introduced
   - Use consistent terminology throughout
   - Avoid jargon or overly complex language
   - Provide examples to clarify complex concepts

### Example Quality Standards

All code examples should:

1. **Be Complete**: Include necessary imports and context
2. **Be Correct**: Verified to work with the current version
3. **Follow Best Practices**: Demonstrate recommended patterns
4. **Include Comments**: Explain key parts of the code
5. **Handle Errors**: Show proper error handling when relevant

```python
# Good example
from uno.queries import Filter, FilterItem

# Create a filter for active products with price > 100
filter = Filter()
filter.add(FilterItem("status", "eq", "active"))
filter.add(FilterItem("price", "gt", 100))

# Apply the filter to get matching products
products = await product_repository.list(filter=filter)
```

## Document Types

### Component Overview

Overview documents introduce a component and its key features:

```markdown
# Component Name

A brief (1-2 sentence) description of what this component does.

## Key Features

- Feature 1: Brief description
- Feature 2: Brief description
- Feature 3: Brief description

## Key Concepts

Explain the main concepts necessary to understand this component.

## Getting Started

Simple example showing basic usage.

## Related Documentation

- [Detailed Guide](example-link-detailed-guide.md)
- [API Reference](example-link-api-reference.md)
```

### API Reference

API reference documents should:

1. Clearly document all parameters, return values, and exceptions
2. Include type information
3. Provide usage examples
4. Explain any constraints or special considerations

```markdown
# ClassName

Brief description of the class's purpose.

## Constructor

```python
ClassName(param1: Type1, param2: Type2 = default_value)
```

Creates a new instance of ClassName.

### Parameters
- `param1` (Type1): Description of parameter 1.
- `param2` (Type2, optional): Description of parameter 2. Default: `default_value`.

### Raises
- `ExceptionType`: Circumstances under which this exception is raised.

## Methods

### method_name

```python
def method_name(param1: Type1) -> ReturnType:
```

Description of what the method does.

### Parameters
- `param1` (Type1): Description of parameter.

### Returns
- `ReturnType`: Description of return value.

### Example

```python
# Example of using the method
```
```

### Tutorial

Tutorials should:

1. Have a clear goal stated at the beginning
2. Include all steps necessary to complete the task
3. Explain why each step is necessary
4. Show expected output or results

```markdown
# How to Accomplish X

This tutorial will guide you through the process of X, which is useful for [purpose].

## Prerequisites

- List prerequisite knowledge
- List required components or setup

## Step 1: Initial Setup

Explanation of first step.

```python
# Code for first step
```

## Step 2: Configure Component

Explanation of configuration.

```python
# Configuration code
```

## Step 3: Use the Component

Explanation of usage.

```python
# Usage code
```

## Expected Results

Description of what should happen when the tutorial is complete.

## Troubleshooting

Common issues and their solutions.
```

## Contributing Documentation

### Creating New Documentation

1. **Identify the Need**: Determine what documentation is missing or needs improvement
2. **Check the Standards**: Review this guide and existing documentation for examples
3. **Create a Draft**: Write a draft following the appropriate template
4. **Review and Revise**: Self-review for clarity, completeness, and correctness
5. **Submit for Review**: Submit as a PR for review

### Improving Existing Documentation

When improving existing documentation:

1. **Maintain Structure**: Keep the existing document structure unless you're explicitly reorganizing
2. **Respect Style**: Match the style of the existing document
3. **Document Changes**: Explain your changes in the PR description
4. **Update Related Docs**: Update any related documents that reference the changed content

### Documentation Review Process

All documentation changes go through a review process:

1. **Technical Accuracy**: Verified by component owners
2. **Style and Clarity**: Checked against documentation standards
3. **Cross-References**: Ensure cross-references remain valid
4. **Examples**: Verify that examples work correctly

## Documentation Tools

### Standardization Script

Use the `standardize_docs.py` script to check documentation for formatting issues and broken links:

```bash
# Check for issues
python src/scripts/standardize_docs.py --check-links

# Fix standard formatting issues
python src/scripts/standardize_docs.py --fix
```

### Documentation Generation

For extracting documentation from code comments:

```bash
# Generate documentation for a package
python src/scripts/generate_docs.py --module uno.package_name
```

## Best Practices

1. **Keep Documentation Close to Code**: Update documentation when changing code
2. **Use TODOs**: Mark areas needing improvement with `<!-- TODO: description -->`
3. **Avoid Duplication**: Link to existing documentation rather than duplicating
4. **Test Examples**: Always verify code examples work correctly
5. **Consider the Audience**: Write for the appropriate knowledge level
6. **Document Whys, Not Just Hows**: Explain why things are done a certain way
7. **Maintain a Link Discipline**: Use proper relative or absolute paths consistently

## Documentation Roadmap

See [DOCUMENTATION_DEVELOPMENT_PLAN.md](./DOCUMENTATION_DEVELOPMENT_PLAN.md) for:

- Current documentation priorities
- Schedule for documentation improvements
- Documentation quality goals
- Planned tooling improvements

## Getting Help

If you need help with documentation:

1. Check this guide and existing documentation for examples
2. Review the [DOCUMENTATION_UPDATE_PROCESS.md](./DOCUMENTATION_UPDATE_PROCESS.md)
3. Ask for guidance in the #documentation channel
4. Request a review of early drafts before finalizing

Remember, good documentation is a key part of uno. Your contributions help make the framework more accessible and easier to use for everyone.