# Developer Tools

This document provides an overview of the Developer Tools available in the Uno framework. These tools are designed to improve the developer experience by providing debugging utilities, profiling tools, code generation capabilities, interactive modeling, and comprehensive documentation.

## Overview

The Developer Tools module is organized into several key components:

1. **Project Scaffolding**: Tools for creating new projects and features with standardized structure and best practices.
2. **Visual Data Modeling**: Interactive entity modeling and code generation with a browser-based interface.
3. **Migration Assistance**: Tools for database schema migrations and codebase transformations.
4. **Debugging Tools**: Utilities for debugging application code, including middleware for request/response inspection, function tracing, and SQL query analysis.
5. **Profiling Tools**: Performance and memory profiling utilities to identify bottlenecks and optimization opportunities.
6. **Code Generation**: Tools for generating code templates for models, repositories, and API endpoints.
7. **Documentation Tools**: Utilities for automatically generating documentation from code.
8. **CLI Tools**: Command-line interface for accessing all developer tools.

## Installation

The Developer Tools are included in the main Uno package. To ensure you have all optional dependencies for the best experience, install with:

```bash
pip install uno[devtools]
```

## Command Line Interface

The central entry point for all developer tools is the CLI module:

```bash
python -m uno.devtools.cli.main [COMMAND] [OPTIONS]
```

### Global Options

All commands support these options:

- `--help`: Show help information
- `--verbose`: Enable verbose output
- `--quiet`: Suppress non-essential output

## Scaffolding

The scaffolding system allows you to quickly create projects and components:

```bash
# Create a new project
python -m uno.devtools.cli.main scaffold new my_project --template standard --database postgresql

# Scaffold a complete feature
python -m uno.devtools.cli.main scaffold feature product --domain ecommerce
```

<!-- TODO: Create scaffolding documentation -->
<!-- See [Scaffolding Guide](developer_tools/scaffolding.md) for complete documentation. -->

## Visual Data Modeling

The visual data modeling tool provides an interactive browser-based interface for designing entity models with comprehensive unit tests:

```bash
# Start the visual modeler using the CLI
python -m uno.devtools.cli.main modeler start

# Or use the convenience script
./scripts/launch_modeler.sh

# Analyze an existing project and extract its model
python -m uno.devtools.cli.main modeler analyze /path/to/project
```

The modeler allows you to:
- Create entities with fields and proper data types
- Position entities in a visual canvas
- Save your model as JSON
- Generate code for entities, repositories, and services

See [Visual Modeler Guide](/docs/developer_tools/visual_modeler.md) for complete documentation.

## Migration Assistance

The migration assistance tools help with database schema migrations and codebase transformations:

```bash
# Compare SQLAlchemy models to database schema
python -m uno.devtools.cli.main migrations diff-schema --connection postgresql://user:password@localhost/dbname --models my_project.models

# Generate a migration script
python -m uno.devtools.cli.main migrations generate-migration --connection postgresql://user:password@localhost/dbname --models my_project.models --output-dir migrations --message "Add user table"

# Apply a migration script
python -m uno.devtools.cli.main migrations apply-migration path/to/migration_script.py --connection postgresql://user:password@localhost/dbname

# Analyze code for migration needs
python -m uno.devtools.cli.main migrations analyze-code path/to/your/code

# Transform code to fix identified issues
python -m uno.devtools.cli.main migrations transform-code path/to/your/code --no-dry-run
```

See [Migration Assistance Guide](/docs/developer_tools/migrations.md) for complete documentation.

## Debugging Tools

### Debug Middleware

The Debug Middleware integrates with FastAPI to provide detailed information about requests, responses, SQL queries, and errors.

```python
from fastapi import FastAPI
from uno.devtools.debugging.middleware import DebugMiddleware

app = FastAPI()
app.add_middleware(```

DebugMiddleware,
enabled=True,
log_requests=True,
log_responses=True,
log_sql=True,
log_errors=True,
log_level="DEBUG"
```
)
```

### Function Tracer

The Function Tracer provides detailed logging of function execution, including arguments, return values, and execution time.

```python
from uno.devtools.debugging.tracer import trace_function, trace_class

@trace_function
def my_function(arg1, arg2):```

# Function code here
return result
```

# Or trace an entire class
@trace_class
class MyClass:```

def __init__(self):```

pass
```
``````

```
```

def my_method(self, arg):```

return arg
```
```
```

### SQL Query Debugger

The SQL Query Debugger tracks SQL queries, analyzes patterns, and detects issues like N+1 query problems.

```python
from uno.devtools.debugging.sql_debug import capture_sql_queries, analyze_query_patterns

# Capture and analyze SQL queries
with capture_sql_queries() as queries:```

# Database operations here
results = repository.get_all_users()
```

# Analyze the queries for patterns and issues
analysis = analyze_query_patterns(queries)
print(f"Slow queries: {len(analysis['slow_queries'])}")
print(f"Similar queries: {len(analysis['similar_queries'])}")
```

### Error Enhancer

The Error Enhancer provides additional context for exceptions, including source code information and variable values.

```python
from uno.devtools.debugging.error_enhancer import enhance_errors

@enhance_errors
def function_that_might_fail():```

# Function code here
raise ValueError("Something went wrong")
```
```

## Profiling Tools

### Performance Profiler

The Performance Profiler measures function execution time and identifies performance bottlenecks.

```python
from uno.devtools.profiling.profiler import profile, Profiler

# As a decorator
@profile
def function_to_profile():```

# Function code here
return result
```

# Or as a context manager
with Profiler("operation_name") as profiler:```

# Code to profile
result = perform_operation()
```
```

### Memory Profiler

The Memory Profiler tracks memory usage and helps identify memory leaks.

```python
from uno.devtools.profiling.memory import track_memory, MemoryTracker, MemoryLeakDetector

# As a decorator
@track_memory
def memory_intensive_function():```

# Function code here
return result
```

# Or as a context manager
with MemoryTracker("operation_name") as snapshot:```

# Code to track
result = perform_operation()
```

# Or to detect memory leaks
detector = MemoryLeakDetector()
detector.snapshot()  # Take initial snapshot
# Perform operations that might leak memory
leaks = detector.check_leaks()
```

## Code Generation

### Model Generator

The Model Generator creates UnoModel and UnoSchema classes from field definitions.

```python
from uno.devtools.codegen.model import ModelGenerator, ModelDefinition, FieldDefinition

# Define a model
model_def = ModelDefinition(```

name="User",
table_name="users",
fields=[```

FieldDefinition(name="id", field_type="int", primary_key=True),
FieldDefinition(name="name", field_type="str", nullable=False),
FieldDefinition(name="email", field_type="str", unique=True)
```
]
```
)

# Generate the model code
generator = ModelGenerator()
model_code = generator.generate_model(model_def)
schema_code = generator.generate_schema(model_def)

# Or generate from database schema
models = generator.generate_from_database(tables=["users", "orders"])
```

### Repository Generator

The Repository Generator creates repository classes for Uno models.

```python
from uno.devtools.codegen.repository import RepositoryGenerator, RepositoryDefinition

# Define a repository
repo_def = RepositoryDefinition(```

name="UserRepository",
model_name="User",
table_name="users"
```
)

# Generate the repository code
generator = RepositoryGenerator()
repo_code = generator.generate_repository(repo_def)

# Or generate from a model class
from myapp.models import User
repo_code = generator.generate_from_model(User)
```

### API Generator

The API Generator creates FastAPI endpoints for Uno models.

```python
from uno.devtools.codegen.api import ApiGenerator, ApiDefinition, EndpointDefinition, EndpointType

# Define an API
api_def = ApiDefinition(```

name="UserApi",
model_name="User",
schema_name="UserSchema",
repository_name="UserRepository",
route_prefix="/users",
endpoints=[```

EndpointDefinition(type=EndpointType.GET_ALL, include_pagination=True),
EndpointDefinition(type=EndpointType.GET_BY_ID),
EndpointDefinition(type=EndpointType.CREATE, include_validation=True),
EndpointDefinition(type=EndpointType.UPDATE, include_validation=True),
EndpointDefinition(type=EndpointType.DELETE)
```
]
```
)

# Generate the API code
generator = ApiGenerator()
api_code = generator.generate_api(api_def)
```

## AI Integration

All developer tools integrate with Uno's AI capabilities:

- **Smart Template Completion**: AI-enhanced template completion
- **Code Generation**: Intelligent code suggestions
- **Documentation**: Automated documentation generation
- **Entity Analysis**: AI-assisted entity relationship detection
- **Best Practices**: Suggestions for architectural improvements

## Documentation Tools

### Documentation Generator

The Documentation Generator extracts documentation from Python modules, classes, and functions, and generates markdown or HTML documentation.

```python
from uno.devtools.docs.generator import DocGenerator

# Generate documentation for a package
generator = DocGenerator()
generator.generate_docs_for_package("myapp", output_dir="docs")

# Or for a specific module
from myapp import users
module_doc = generator.extract_module_doc(users)
markdown = generator.generate_markdown(module_doc)
```

## Integration with FastAPI

The Developer Tools integrate seamlessly with FastAPI:

```python
from fastapi import FastAPI, Depends
from uno.devtools.debugging.middleware import DebugMiddleware
from uno.devtools.profiling.middleware import ProfilerMiddleware

app = FastAPI()

# Add debugging middleware
app.add_middleware(DebugMiddleware, enabled=True)

# Add profiling middleware
app.add_middleware(ProfilerMiddleware, enabled=True)

# Route-specific debugging
@app.get("/debug_example")
def debug_example(debug=Depends(DebugMiddleware.debug_dependency)):```

# This route will have detailed debugging
return {"message": "Debug example"}
```
```

## Configuration

The Developer Tools can be configured through environment variables or a configuration file:

```python
from uno.devtools.config import DevToolsConfig

config = DevToolsConfig(```

debug=True,
profiling=True,
log_level="DEBUG",
output_dir="./devtools_output"
```
)
```

Or use environment variables:

```bash
export UNO_DEVTOOLS_DEBUG=True
export UNO_DEVTOOLS_PROFILING=True
export UNO_DEVTOOLS_LOG_LEVEL=DEBUG
export UNO_DEVTOOLS_OUTPUT_DIR=./devtools_output
```

## Best Practices

1. **Use Scaffolding**: Start new projects and features with the scaffolding system for consistent structure
2. **Visual Modeling**: Design entity models visually before implementation for better architecture
3. **Selective Profiling**: Focus profiling on specific operations rather than the entire application
4. **Code Generation as Starting Points**: Use generated code as a starting point, then customize as needed
5. **Documentation Updates**: Regenerate documentation when making significant code changes
6. **CLI for Automation**: Use the CLI tools in automation scripts and CI/CD pipelines
7. **Debug in Development**: Enable debugging only in development environments, not in production

## Extending Developer Tools

You can extend the developer tooling system with custom:

- Project templates
- Component templates
- Code generators
- Analysis tools

## Troubleshooting

### Common Issues

1. **High Memory Usage**: When using memory profiling, be aware that it can increase memory usage significantly. Use selectively.
2. **Performance Impact**: Debugging and profiling tools add overhead. Use selectively in performance-sensitive code.
3. **Generated Code Conflicts**: Generated code might conflict with existing files. Use the `--force` flag to overwrite, or specify a different output path.
4. **Visual Modeler Issues**: If the visual modeler doesn't start, check for port conflicts or missing dependencies (FastAPI, Uvicorn, Jinja2).
5. **JavaScript Requirements**: The visual modeler requires a modern browser with JavaScript ES6+ support.
6. **Network Access**: Some tools may require network access for features like API documentation fetching or template updates.

### Getting Help

For more help with the Developer Tools, use the built-in help command:

```bash
python -m uno.devtools.cli.main --help
python -m uno.devtools.cli.main <command> --help
```

## Conclusion

The Developer Tools provide a comprehensive suite of utilities to enhance your development experience with the Uno framework. From scaffolding and visual modeling to debugging, profiling, code generation and documentation, these tools are designed to make your development workflow more efficient and productive.