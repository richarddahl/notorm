# DevTools API

The Uno DevTools module provides a comprehensive set of tools for enhancing developer experience when working with the Uno framework. The module follows a domain-driven design approach, providing interfaces for debugging, profiling, code generation, and documentation functionalities.

## Key Features

- **Debugging Tools**: Configure debug levels, trace function execution, debug SQL queries, and enhance error information
- **Profiling**: Profile function execution time and memory usage to identify performance bottlenecks
- **Code Generation**: Generate models, repositories, services, and API endpoints based on templates
- **Documentation**: Generate documentation from docstrings, create diagrams, and serve interactive documentation

## Getting Started

### Configuring the DevTools Provider

```python
from uno.devtools import DevToolsProvider

# Configure with in-memory repositories (default)
provider = DevToolsProvider()
provider.configure()

# Configure with file-based repositories
from pathlib import Path
provider = DevToolsProvider(
    storage_path=Path("./devtools_data"),
    use_file_storage=True
)
provider.configure()
```

### Debugging

```python
from uno.devtools import DevToolsProvider, DebugConfiguration, DebugLevel

# Get the debug service
debug_service = DevToolsProvider.get_debug_service()

# Configure debugging
config = DebugConfiguration(
    level=DebugLevel.DEBUG,
    trace_sql=True,
    trace_repository=True,
    enhance_errors=True
)
debug_service.configure(config)

# Decorate functions for tracing
@debug_service.trace_function
def my_function():
    # Function code here
    pass

# Enhance error information
try:
    # Code that might raise an exception
    raise ValueError("Example error")
except Exception as e:
    enhanced_info = debug_service.enhance_error_information(e)
    if enhanced_info.is_success:
        print(enhanced_info.value)
```

### Profiling

```python
from uno.devtools import DevToolsProvider, ProfilerConfiguration, ProfilerType

# Get the profiler service
profiler_service = DevToolsProvider.get_profiler_service()

# Start a profiling session
config = ProfilerConfiguration(
    type=ProfilerType.FUNCTION,
    sample_rate=100,
    output_format="html"
)
session_id_result = profiler_service.start_session(config)

if session_id_result.is_success:
    session_id = session_id_result.value
    
    # Decorate functions for profiling
    @profiler_service.profile_function
    def my_function():
        # Function code here
        pass
    
    # Call the function
    my_function()
    
    # End the session
    session_result = profiler_service.end_session(session_id)
    
    if session_result.is_success:
        session = session_result.value
        
        # Analyze hotspots
        hotspots_result = profiler_service.analyze_hotspots(session_id)
        
        if hotspots_result.is_success:
            hotspots = hotspots_result.value
            for hotspot in hotspots:
                print(f"Hotspot: {hotspot.name}, {hotspot.own_time:.6f}s")
        
        # Export the session
        export_result = profiler_service.export_session(session_id, "html")
        
        if export_result.is_success:
            print(f"Profile exported to: {export_result.value}")
```

### Memory Profiling

```python
from uno.devtools import DevToolsProvider, ProfilerConfiguration, ProfilerType

# Get the memory profiler service
memory_profiler_service = DevToolsProvider.get_memory_profiler_service()

# Start a memory profiling session
config = ProfilerConfiguration(
    type=ProfilerType.MEMORY,
    sample_rate=100
)
session_id_result = memory_profiler_service.start_session(config)

if session_id_result.is_success:
    session_id = session_id_result.value
    
    # Decorate functions for memory profiling
    @memory_profiler_service.profile_memory_usage
    def my_function():
        # Function code here
        data = [i for i in range(1000000)]
        return data
    
    # Call the function
    my_function()
    
    # End the session
    session_result = memory_profiler_service.end_session(session_id)
    
    if session_result.is_success:
        session = session_result.value
        
        # Analyze potential memory leaks
        leaks_result = memory_profiler_service.analyze_leaks(session_id)
        
        if leaks_result.is_success:
            leaks = leaks_result.value
            for leak in leaks:
                print(f"Potential leak: {leak.name}, {leak.bytes_allocated} bytes")
```

### Code Generation

```python
from pathlib import Path
from uno.devtools import DevToolsProvider, CodegenTemplate, CodegenTemplateId, CodegenType

# Get the code generation service
codegen_service = DevToolsProvider.get_codegen_service()

# Register a custom template
template = CodegenTemplate(
    id=CodegenTemplateId("my-model-template"),
    name="Custom Model Template",
    type=CodegenType.MODEL,
    template_path=Path("./templates/model.j2"),
    description="A custom model template with additional fields"
)
codegen_service.register_template(template)

# Generate a model
fields = {
    "id": "str",
    "name": "str",
    "description": "Optional[str]",
    "created_at": "datetime",
    "updated_at": "datetime"
}
result = codegen_service.generate_model(
    name="Product",
    fields=fields,
    output_path=Path("./app/models/product.py")
)

if result.is_success:
    print(f"Model generated at: {result.value.output_path}")

# Generate a repository for the model
result = codegen_service.generate_repository(
    model_name="Product",
    output_path=Path("./app/repositories/product_repository.py")
)

if result.is_success:
    print(f"Repository generated at: {result.value.output_path}")
```

### Documentation

```python
from uno.devtools import DevToolsProvider, DiagramSpecification

# Get the documentation service
docs_service = DevToolsProvider.get_documentation_service()

# Generate documentation for a module
result = docs_service.generate_documentation("app.models.product")

if result.is_success:
    asset = result.value
    print(f"Documentation generated at: {asset.path}")

# Generate a diagram
spec = DiagramSpecification(
    title="Product Domain Model",
    diagram_type="class",
    include_modules=["app.models", "app.repositories"],
    exclude_modules=["app.models.legacy"],
    output_format="svg"
)
result = docs_service.generate_diagram(spec)

if result.is_success:
    print(f"Diagram generated at: {result.value}")

# Extract docstrings from a module
result = docs_service.extract_docstrings("app.models.product")

if result.is_success:
    docstrings = result.value
    for key, value in docstrings.items():
        print(f"{key}: {value}")
```

## API Reference

### Entities

#### Debug

- `DebugConfiguration`: Configuration settings for debugging
- `DebugLevel`: Enum for debug verbosity levels (ERROR, WARNING, INFO, DEBUG, TRACE)

#### Profiling

- `ProfilerConfiguration`: Configuration for profiling sessions
- `ProfilerType`: Enum for profiler types (FUNCTION, MEMORY, SQL, API, FULL)
- `ProfilerSession`: A profiling session containing performance metrics
- `ProfilerSessionId`: Unique identifier for profiling sessions
- `ProfileMetric`: A single performance metric for a function
- `MemoryProfilerSession`: A memory profiling session
- `MemoryMetric`: Memory usage metrics for a component or function

#### Code Generation

- `CodegenTemplate`: A template for code generation
- `CodegenTemplateId`: Unique identifier for code generation templates
- `CodegenType`: Enum for code generation types (MODEL, REPOSITORY, SERVICE, API, CRUD, PROJECT, MODULE)
- `GeneratedCodeResult`: Result of a code generation operation

#### Documentation

- `DocumentationAsset`: A documentation asset generated by documentation tools
- `DocumentationId`: Unique identifier for documentation assets
- `DiagramSpecification`: Specification for generating a diagram

### Repositories

- `ProfilerSessionRepositoryProtocol`: Interface for profiler session repositories
- `MemoryProfilerSessionRepositoryProtocol`: Interface for memory profiler session repositories
- `CodegenTemplateRepositoryProtocol`: Interface for code generation template repositories
- `GeneratedCodeRepositoryProtocol`: Interface for generated code result repositories
- `DocumentationAssetRepositoryProtocol`: Interface for documentation asset repositories

### Services

- `DebugServiceProtocol`: Interface for debugging functionality
- `ProfilerServiceProtocol`: Interface for profiling functionality
- `MemoryProfilerServiceProtocol`: Interface for memory profiling functionality
- `CodegenServiceProtocol`: Interface for code generation functionality
- `DocumentationServiceProtocol`: Interface for documentation functionality

### HTTP API Endpoints

The DevTools module provides a FastAPI router with endpoints for all functionality:

```python
from fastapi import FastAPI
from uno.devtools import devtools_router

app = FastAPI()
app.include_router(devtools_router)
```

#### Debug Endpoints

- `GET /api/devtools/debug/config`: Get the current debug configuration
- `POST /api/devtools/debug/config`: Set the debug configuration
- `POST /api/devtools/debug/sql`: Enable or disable SQL debugging
- `POST /api/devtools/debug/repository`: Enable or disable repository debugging

#### Profiler Endpoints

- `POST /api/devtools/profiler/sessions`: Start a new profiling session
- `POST /api/devtools/profiler/sessions/{session_id}/end`: End a profiling session
- `GET /api/devtools/profiler/sessions/{session_id}`: Get a profiling session by ID
- `GET /api/devtools/profiler/sessions/{session_id}/metrics`: Get metrics for a profiling session
- `GET /api/devtools/profiler/sessions/{session_id}/hotspots`: Get hotspots for a profiling session
- `POST /api/devtools/profiler/sessions/{session_id}/export`: Export a profiling session

#### Memory Profiler Endpoints

- `POST /api/devtools/memory-profiler/sessions`: Start a new memory profiling session
- `POST /api/devtools/memory-profiler/sessions/{session_id}/end`: End a memory profiling session
- `GET /api/devtools/memory-profiler/sessions/{session_id}`: Get a memory profiling session by ID
- `GET /api/devtools/memory-profiler/sessions/{session_id}/metrics`: Get metrics for a memory profiling session
- `GET /api/devtools/memory-profiler/sessions/{session_id}/leaks`: Get potential memory leaks for a session

#### Code Generation Endpoints

- `GET /api/devtools/codegen/templates`: List all code generation templates
- `POST /api/devtools/codegen/templates/{template_id}`: Get a code generation template by ID
- `POST /api/devtools/codegen/generate`: Generate code based on a template

#### Documentation Endpoints

- `POST /api/devtools/docs/generate`: Generate documentation for a module
- `POST /api/devtools/docs/diagram`: Generate a diagram based on a specification
- `GET /api/devtools/docs/extract`: Extract docstrings from a module

## Testing

The DevTools module provides a `TestingDevToolsProvider` class for testing:

```python
from uno.devtools import TestingDevToolsProvider

# Configure with mock services
class MockDebugService:
    # Implementation of DebugServiceProtocol for testing
    pass

TestingDevToolsProvider.configure_with_mocks(debug_service=MockDebugService())

# Use the services in tests
debug_service = DevToolsProvider.get_debug_service()
assert isinstance(debug_service, MockDebugService)

# Clean up after tests
TestingDevToolsProvider.cleanup()
```