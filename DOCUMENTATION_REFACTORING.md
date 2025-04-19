# Documentation Refactoring

This document explains the documentation refactoring process for the Uno framework.

## Overview

The Uno framework documentation has been completely refactored to provide a modern, consistent, and comprehensive guide to using the framework. The refactoring focuses on organizing the documentation around key architectural components and providing clear guidance on using the modern, unified approach implemented in the framework.

## Key Changes

1. **Consistent Structure**: Documentation now follows a consistent structure across all components
2. **Modern Focus**: All documentation focuses on the modern, unified approach without legacy references
3. **Comprehensive Coverage**: Essential components are now fully documented
4. **Clear Navigation**: Documentation is organized in a logical hierarchy for easy navigation
5. **Practical Examples**: Each component includes practical code examples
6. **Migration Guides**: New guides for migrating from Django and SQLAlchemy
7. **Complete Architecture Documentation**: Detailed explanations of the architecture and design principles

## Documentation Structure

The documentation is now organized into the following main sections:

- **Home**: Introduction and overview
- **Getting Started**: Installation and initial setup
- **Tutorials**: Step-by-step guides and migration tutorials
- **Architecture**: Design principles and architectural patterns
- **Core**: Core framework components (events, unit of work, errors)
- **Domain**: Domain-driven design implementation
- **API**: Endpoint framework and API design
- **Database**: Database access and PostgreSQL integration
- **Infrastructure**: Technical implementations (repositories, security, caching)
- **Application**: Application layer components (DTOs, queries, workflows, jobs)
- **Features**: Specific framework features
- **Developer Tools**: Development utilities
- **Deployment**: Deployment guidance
- **Reference**: Command and API references

## Documentation Standards

All documentation now follows these standards:

1. **File Naming**: Consistent lowercase with underscores (`file_name.md`)
2. **Directory Structure**: Logical hierarchy of components
3. **Document Structure**: Clear headings, introductions, and sections
4. **Code Examples**: Complete, runnable examples with imports
5. **Markdown Syntax**: Properly formatted markdown with tables, code blocks, and admonitions

## Next Steps

This refactoring is the first phase of a comprehensive documentation improvement project. Future phases include:

1. **Component Documentation**: Complete documentation for all remaining components
2. **Interactive Examples**: Add interactive tutorials and playgrounds
3. **Video Tutorials**: Create video walkthroughs of key concepts
4. **API Reference**: Generate comprehensive API reference documentation
5. **Case Studies**: Real-world examples of Uno applications

## Contributing to Documentation

A comprehensive guide for contributing to documentation has been created at [Project Documentation Guide](docs/project/documentation_guide.md). This guide explains:

1. Documentation standards and formatting
2. How to add new documentation
3. Documentation templates and examples
4. Best practices for documentation

## Migration Tutorials

Special focus has been placed on providing comprehensive migration guides:

1. **[Migrating from SQLAlchemy](docs/tutorial/migrating_from_sqlalchemy.md)**: Guide for converting SQLAlchemy applications to Uno
2. **[Migrating from Django](docs/tutorial/migrating_from_django.md)**: Steps for migrating Django applications to Uno

These guides provide step-by-step instructions for converting existing applications to use the Uno framework's modern architecture.

## Key Documentation Files

The following key documentation files have been created or updated:

1. **[Index](docs/index.md)**: Main entry point and overview
2. **[Getting Started](docs/getting_started.md)**: Installation and setup guide
3. **[Architecture Overview](docs/architecture/overview.md)**: Architectural principles and patterns
4. **[Domain Guide](docs/domain/guide.md)**: Domain-driven design implementation
5. **[API Endpoint Overview](docs/api/endpoint/overview.md)**: API endpoint framework
6. **[Event System](docs/core/events/index.md)**: Event system documentation
7. **[Unit of Work](docs/core/uow/index.md)**: Transaction management documentation
8. **[Error Handling](docs/core/errors/overview.md)**: Error handling framework
9. **[Database Overview](docs/database/overview.md)**: Database framework documentation

## Building Documentation

The documentation can be built using MkDocs:

```bash
# Install MkDocs and required plugins
pip install mkdocs mkdocs-material mkdocstrings pymdown-extensions

# Serve the documentation (for development)
mkdocs serve

# Build the documentation (for production)
mkdocs build
```

The built documentation will be available in the `site` directory.

## Conclusion

This documentation refactoring provides a solid foundation for understanding and using the Uno framework. It focuses on the modern, unified approach implemented in the framework and provides clear guidance for developing applications with domain-driven design, event-driven architecture, and clean separation of concerns.