# Plugin Architecture

The Uno framework includes a powerful plugin system that allows extending the framework's functionality without modifying core code.

## Overview

The plugin architecture provides a flexible way to add new features, customize behavior, and integrate with external systems. Key features include:

- **Plugin Lifecycle Management**: Load, enable, disable, and unload plugins dynamically
- **Extension Points**: Well-defined points where plugins can extend functionality
- **Dependency Management**: Handle plugin dependencies and version compatibility
- **Configuration System**: Configure plugins without code changes
- **Hook System**: Register callbacks for framework events
- **Discovery Mechanism**: Automatically discover plugins from different sources

## Key Concepts

### Plugins

A plugin is a self-contained module that adds functionality to the framework. Each plugin:

- Has a unique identifier and metadata
- Defines its lifecycle methods (load, enable, disable, unload)
- Can provide extensions for specific extension points
- Can register hooks for framework events
- Can have its own configuration

### Extension Points

Extension points are well-defined interfaces where plugins can provide implementations to extend functionality. Examples include:

- Authentication providers
- Template renderers
- API handlers
- Custom UI components

### Hooks

Hooks are callback points in the framework where plugins can register functions to be called when specific events occur, such as:

- Application startup and shutdown
- Request processing
- User authentication
- Plugin lifecycle events

## Plugin Lifecycle

Plugins go through several states during their lifecycle:

1. **Registered**: The plugin is registered with the system but not loaded
2. **Loaded**: The plugin is loaded but not active
3. **Enabled**: The plugin is active and its functionality is available
4. **Disabled**: The plugin is loaded but its functionality is not active
5. **Unloaded**: The plugin is no longer loaded

## Creating Plugins

### Basic Plugin Structure

```python
from uno.core.plugins.plugin import Plugin, PluginInfo, PluginConfig, PluginType

class MyPlugin(Plugin):```

"""A simple example plugin."""
``````

```
```

def __init__(self):```

"""Initialize the plugin."""
info = PluginInfo(
    id="my_plugin",
    name="My Plugin",
    version="1.0.0",
    description="An example plugin",
    author="Your Name",
    plugin_type=PluginType.UTILITY
)
``````

```
```

config = PluginConfig(
    schema={
        "option1": {
            "type": "string",
            "description": "An example option",
            "default": "default value"
        }
    },
    defaults={
        "option1": "default value"
    }
)
``````

```
```

super().__init__(info, config)
```
``````

```
```

async def load(self) -> None:```

"""Load the plugin."""
self.logger.info(f"Loading {self.name}...")
```
``````

```
```

async def unload(self) -> None:```

"""Unload the plugin."""
self.logger.info(f"Unloading {self.name}...")
```
``````

```
```

async def enable(self) -> None:```

"""Enable the plugin."""
self.logger.info(f"Enabling {self.name}...")
# Register extensions, hooks, etc.
```
``````

```
```

async def disable(self) -> None:```

"""Disable the plugin."""
self.logger.info(f"Disabling {self.name}...")
# Unregister extensions, hooks, etc.
```
```
```

### Providing Extensions

To extend a specific part of the framework, plugins can provide extensions:

```python
from uno.core.plugins.extension import register_extension

# In your plugin's enable method
async def enable(self) -> None:```

# Create and register an extension
register_extension(```

extension_point_id="authentication_provider",
extension_id="my_auth_provider",
extension=MyAuthProvider(),
config={"priority": 100}
```
)
```
```

### Registering Hooks

Plugins can register hooks to be notified of framework events:

```python
from uno.core.plugins.hooks import register_hook

# In your plugin's enable method
async def enable(self) -> None:```

# Register a hook
register_hook(```

hook_type="request_started",
callback=self.on_request_started,
priority=100
```
)
```

async def on_request_started(self, request):```

self.logger.info(f"Request started: {request.url}")
```
```

## Using Plugins

### Loading Plugins

```python
from uno.core.plugins.discovery import load_plugins_from_directory
from uno.core.plugins.manager import init_plugins

# Load plugins from a directory
plugins = await load_plugins_from_directory("/path/to/plugins")

# Initialize all registered plugins
total, loaded, enabled = await init_plugins()
```

### Getting Extensions

```python
from uno.core.plugins.extension import get_extensions

# Get all extensions for an extension point
auth_providers = get_extensions("authentication_provider")

# Use extensions
for provider_id, provider_data in auth_providers.items():```

provider = provider_data["extension"]
result = provider.authenticate(username, password)
```
```

### Calling Hooks

```python
from uno.core.plugins.hooks import call_hook

# Call all registered hooks for an event
results = await call_hook("request_started", request)
```

## Plugin Configuration

Plugins can be configured through their `PluginConfig` object:

```python
# Getting configuration
value = plugin.config.get("option1")

# Setting configuration
await plugin.update_config({"option1": "new value"})

# Validating configuration
errors = await plugin.validate_config({"option1": "new value"})
if not errors:```

# Configuration is valid
pass
```
```

## Plugin Dependencies

Plugins can specify dependencies on other plugins:

```python
from uno.core.plugins.plugin import PluginInfo, PluginDependency

info = PluginInfo(```

id="my_plugin",
name="My Plugin",
version="1.0.0",
description="An example plugin",
author="Your Name",
dependencies=[```

PluginDependency(plugin_id="other_plugin", min_version="1.0.0"),
PluginDependency(plugin_id="optional_plugin", optional=True)
```
]
```
)
```

The plugin system will automatically ensure that dependencies are loaded and enabled in the correct order.

## Core vs. Custom Plugins

The framework distinguishes between two types of plugins:

- **Core Plugins**: Extend core framework functionality and are tightly integrated
- **Custom Plugins**: Add new features, integrations, or behaviors on top of the framework

Core plugins have additional responsibilities and capabilities, such as registering components with the framework:

```python
from uno.core.plugins.plugin import CorePlugin

class MyCorePlugin(CorePlugin):```

"""A core plugin that extends framework functionality."""
``````

```
```

# ...
``````

```
```

async def register_components(self) -> None:```

"""Register components with the framework."""
# Register components
pass
```
``````

```
```

async def unregister_components(self) -> None:```

"""Unregister components from the framework."""
# Unregister components
pass
```
```
```

## Best Practices

1. **Unique IDs**: Use clear, namespaced identifiers for plugins and extensions
2. **Version Compatibility**: Specify application version compatibility in your plugin info
3. **Clean Lifecycle**: Ensure your plugin cleans up after itself when disabled or unloaded
4. **Dependency Management**: Keep dependencies minimal and clearly specify version requirements
5. **Configuration Validation**: Validate configuration options thoroughly
6. **Error Handling**: Handle errors gracefully in all plugin operations
7. **Documentation**: Document your plugin's features, extensions, hooks, and configuration options

## Next Steps

- Learn how to [create your first plugin](creating_plugins.md)
- Explore available [extension points](extension_points.md)
- Understand the [hook system](hooks.md)
- Create [configuration schemas](plugin_configuration.md)
- See [plugin examples](plugin_examples.md)