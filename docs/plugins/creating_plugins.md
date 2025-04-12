# Creating Plugins

This guide walks you through the process of creating a plugin for the Uno framework, from basic structure to advanced features.

## Plugin Structure

Every plugin consists of these core elements:

1. **Plugin Class**: Extends the `Plugin` base class
2. **Plugin Info**: Provides metadata about the plugin
3. **Plugin Config**: Defines configuration options
4. **Lifecycle Methods**: Handles loading, enabling, disabling, and unloading

## Basic Plugin Template

Here's a minimal plugin implementation:

```python
from uno.core.plugins.plugin import (
    Plugin, create_plugin_info, create_plugin_config, PluginType
)

class MyPlugin(Plugin):
    """My custom plugin."""
    
    def __init__(self):
        """Initialize the plugin."""
        # Create plugin info
        info = create_plugin_info(
            id="my_plugin",
            name="My Plugin",
            version="1.0.0",
            description="A simple example plugin",
            author="Your Name",
            plugin_type=PluginType.UTILITY
        )
        
        # Create plugin config
        config = create_plugin_config(
            schema={
                "setting": {
                    "type": "string",
                    "description": "An example setting",
                    "default": "default value"
                }
            },
            defaults={
                "setting": "default value"
            }
        )
        
        # Initialize the plugin
        super().__init__(info, config)
    
    async def load(self) -> None:
        """Load the plugin."""
        self.logger.info(f"Loading {self.name}...")
        # Perform initialization
    
    async def unload(self) -> None:
        """Unload the plugin."""
        self.logger.info(f"Unloading {self.name}...")
        # Clean up resources
    
    async def enable(self) -> None:
        """Enable the plugin."""
        self.logger.info(f"Enabling {self.name}...")
        # Activate functionality
    
    async def disable(self) -> None:
        """Disable the plugin."""
        self.logger.info(f"Disabling {self.name}...")
        # Deactivate functionality
```

## Plugin Information

The `PluginInfo` class contains metadata about your plugin:

```python
from uno.core.plugins.plugin import PluginInfo, PluginType, PluginDependency

info = PluginInfo(
    id="my_plugin",              # Unique identifier
    name="My Plugin",            # Human-readable name
    version="1.0.0",             # Version using semantic versioning
    description="Description",   # Detailed description
    author="Your Name",          # Plugin author
    website="https://example.com",  # Optional website URL
    license="MIT",               # Optional license
    plugin_type=PluginType.UTILITY,  # Plugin type
    requires_restart=False,      # Whether app needs restart after enabling/disabling
    dependencies=[               # Plugin dependencies
        PluginDependency(plugin_id="other_plugin", min_version="1.0.0"),
        PluginDependency(plugin_id="optional_plugin", optional=True)
    ],
    tags=["example", "utility"],  # Tags for categorizing the plugin
    min_app_version="1.0.0",     # Minimum application version required
    max_app_version="2.0.0",     # Maximum application version supported
    python_dependencies=["requests>=2.25.0"]  # Python package dependencies
)
```

You can also use the helper function:

```python
from uno.core.plugins.plugin import create_plugin_info

info = create_plugin_info(
    id="my_plugin",
    name="My Plugin",
    version="1.0.0",
    description="Description",
    author="Your Name",
    plugin_type=PluginType.UTILITY
)
```

## Plugin Configuration

The `PluginConfig` class defines configuration options for your plugin:

```python
from uno.core.plugins.plugin import PluginConfig

config = PluginConfig(
    schema={
        "api_key": {
            "type": "string",
            "description": "API key for the service",
            "required": True
        },
        "timeout": {
            "type": "integer",
            "description": "Request timeout in seconds",
            "default": 30,
            "minimum": 1,
            "maximum": 300
        },
        "debug": {
            "type": "boolean",
            "description": "Enable debug mode",
            "default": False
        }
    },
    defaults={
        "timeout": 30,
        "debug": False
    }
)
```

Or use the helper function:

```python
from uno.core.plugins.plugin import create_plugin_config

config = create_plugin_config(
    schema={
        "api_key": {
            "type": "string",
            "description": "API key for the service",
            "required": True
        },
        "timeout": {
            "type": "integer",
            "description": "Request timeout in seconds",
            "default": 30
        }
    },
    defaults={
        "timeout": 30
    }
)
```

## Lifecycle Methods

Every plugin must implement four lifecycle methods:

### load()

Called when the plugin is being loaded, before it's enabled:

```python
async def load(self) -> None:
    """Load the plugin."""
    self.logger.info(f"Loading {self.name}...")
    
    # Initialize resources
    self.resource = await self.initialize_resource()
    
    # Load any necessary data
    self.data = await self.load_data()
```

### enable()

Called when the plugin is being enabled after loading:

```python
async def enable(self) -> None:
    """Enable the plugin."""
    self.logger.info(f"Enabling {self.name}...")
    
    # Register extensions
    register_extension(
        extension_point_id="my_extension_point",
        extension_id=f"{self.id}_extension",
        extension=MyExtension(self)
    )
    
    # Register hooks
    register_hook(
        hook_type="app_event",
        callback=self.on_app_event
    )
    
    # Start any background tasks
    self.task = asyncio.create_task(self.background_task())
```

### disable()

Called when the plugin is being disabled:

```python
async def disable(self) -> None:
    """Disable the plugin."""
    self.logger.info(f"Disabling {self.name}...")
    
    # Unregister extensions and hooks
    # (this happens automatically, but you may need to clean up)
    
    # Cancel any background tasks
    if hasattr(self, 'task') and self.task:
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
```

### unload()

Called when the plugin is being unloaded after being disabled:

```python
async def unload(self) -> None:
    """Unload the plugin."""
    self.logger.info(f"Unloading {self.name}...")
    
    # Release any resources
    if hasattr(self, 'resource') and self.resource:
        await self.resource.close()
    
    # Clear any cached data
    if hasattr(self, 'data'):
        self.data = None
```

## Working with Plugin Configuration

Use the configuration in your plugin:

```python
def get_timeout(self) -> int:
    """Get the configured timeout."""
    return self.config.get("timeout", 30)
```

Apply configuration changes:

```python
async def apply_config(self) -> None:
    """Apply configuration changes."""
    if hasattr(self, 'client'):
        # Update client timeout from config
        self.client.timeout = self.config.get("timeout", 30)
        
        # Apply debug mode
        self.client.debug = self.config.get("debug", False)
```

## Providing Extensions

Plugins can provide extensions for extension points:

```python
from uno.core.plugins.extension import register_extension

# Define an extension class
class MyAuthProvider:
    def __init__(self, plugin):
        self.plugin = plugin
    
    async def authenticate(self, username, password):
        # Implementation
        api_key = self.plugin.config.get("api_key")
        # Use the API key for authentication
        return result

# In your plugin's enable method
async def enable(self) -> None:
    # Register the extension
    register_extension(
        extension_point_id="auth_provider",
        extension_id=f"{self.id}_auth",
        extension=MyAuthProvider(self)
    )
```

## Registering Hooks

Plugins can register hooks for framework events:

```python
from uno.core.plugins.hooks import register_hook

# In your plugin's enable method
async def enable(self) -> None:
    # Register hooks
    register_hook(
        hook_type="user_created",
        callback=self.on_user_created
    )
    
    register_hook(
        hook_type="request_started",
        callback=self.on_request_started,
        priority=50  # Lower numbers run first
    )

# Hook handler methods
async def on_user_created(self, user):
    self.logger.info(f"User created: {user.username}")
    
    # Do something with the event
    await self.send_welcome_email(user)

async def on_request_started(self, request):
    self.logger.debug(f"Request started: {request.method} {request.url}")
    
    # Add something to the request
    request.start_time = time.time()
```

## Creating Core Plugins

Core plugins extend the framework's basic functionality:

```python
from uno.core.plugins.plugin import CorePlugin

class MyCorePlugin(CorePlugin):
    """A core plugin that extends framework functionality."""
    
    # ... init and lifecycle methods ...
    
    async def register_components(self) -> None:
        """Register components with the framework."""
        # Register components with the framework
        self.framework.register_component("my_component", MyComponent())
    
    async def unregister_components(self) -> None:
        """Unregister components from the framework."""
        # Unregister components from the framework
        self.framework.unregister_component("my_component")
```

## Plugin File Structure

For simple plugins, a single file is often sufficient:

```
my_plugin.py
```

For more complex plugins, use a module structure:

```
my_plugin/
  __init__.py       # Exports the plugin class
  plugin.py         # Plugin implementation
  extensions.py     # Extension implementations
  utils.py          # Utility functions
  models.py         # Data models
  templates/        # Templates or other resources
  static/           # Static assets
```

The `__init__.py` should export the plugin class:

```python
from .plugin import MyPlugin

__all__ = ["MyPlugin"]
```

## Distribution and Installation

Plugins can be distributed as Python packages:

```
my_plugin/
  setup.py
  README.md
  my_plugin/
    __init__.py
    plugin.py
    ...
```

With entry points in `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name="my-plugin",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "uno.plugins": [
            "my_plugin=my_plugin:MyPlugin",
        ],
    },
)
```

## Advanced Features

### Background Tasks

Run background tasks in your plugin:

```python
import asyncio

async def enable(self) -> None:
    """Enable the plugin."""
    # Start background task
    self.running = True
    self.task = asyncio.create_task(self.background_task())

async def disable(self) -> None:
    """Disable the plugin."""
    # Stop background task
    self.running = False
    if hasattr(self, 'task') and self.task:
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

async def background_task(self) -> None:
    """Background task that runs periodically."""
    try:
        while self.running:
            # Do something periodically
            await self.perform_periodic_operation()
            
            # Wait for a while
            await asyncio.sleep(60)  # Run every minute
    except asyncio.CancelledError:
        # Handle cancellation
        self.logger.info("Background task cancelled")
        raise
    except Exception as e:
        # Handle other exceptions
        self.logger.error(f"Error in background task: {str(e)}")
```

### Plugin Settings UI

Define a schema for a settings UI:

```python
# In your plugin's __init__ method
self.settings_schema = {
    "type": "object",
    "properties": {
        "api_key": {
            "type": "string",
            "title": "API Key",
            "description": "Your API key for the service"
        },
        "timeout": {
            "type": "integer",
            "title": "Timeout",
            "description": "Request timeout in seconds",
            "minimum": 1,
            "maximum": 300
        },
        "features": {
            "type": "object",
            "title": "Features",
            "properties": {
                "feature1": {
                    "type": "boolean",
                    "title": "Feature 1",
                    "default": true
                },
                "feature2": {
                    "type": "boolean",
                    "title": "Feature 2",
                    "default": false
                }
            }
        }
    },
    "required": ["api_key"]
}
```

### Plugin Storage

Manage persistent storage for your plugin:

```python
import os
import json

class MyPlugin(Plugin):
    # ...
    
    async def load(self) -> None:
        """Load the plugin."""
        # Load saved data
        await self.load_data()
    
    async def unload(self) -> None:
        """Unload the plugin."""
        # Save data before unloading
        await self.save_data()
    
    async def load_data(self) -> None:
        """Load plugin data from storage."""
        data_file = os.path.join(self.get_data_dir(), "data.json")
        
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading data: {str(e)}")
                self.data = {}
        else:
            self.data = {}
    
    async def save_data(self) -> None:
        """Save plugin data to storage."""
        data_file = os.path.join(self.get_data_dir(), "data.json")
        
        try:
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            with open(data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
    
    def get_data_dir(self) -> str:
        """Get the plugin data directory."""
        return os.path.join(os.path.expanduser("~"), ".uno", "plugins", self.id)
```

## Best Practices

1. **Clean Initialization**: Initialize resources in `load()`, not `__init__()`
2. **Clean Shutdown**: Properly clean up resources in `disable()` and `unload()`
3. **Error Handling**: Catch and handle exceptions to prevent plugin failures from affecting the application
4. **Configuration Validation**: Always validate configuration before using it
5. **Default Values**: Provide sensible defaults for all configuration options
6. **Documentation**: Document your plugin's features, configuration, and usage
7. **Dependency Declaration**: Clearly specify all plugin dependencies
8. **Separation of Concerns**: Keep plugin functionality modular and focused
9. **Logging**: Use the provided logger for meaningful log messages
10. **Testing**: Write tests for your plugin to ensure it works as expected

By following these guidelines, you can create robust, maintainable plugins that enhance the Uno framework in powerful ways.