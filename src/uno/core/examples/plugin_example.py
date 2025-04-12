"""
Example showing how to use the plugin system.

This module demonstrates how to create, register, and use plugins in the Uno framework.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from uno.core.plugins.plugin import (
    Plugin, PluginInfo, PluginConfig, PluginType, PluginStatus, 
    create_plugin_info, create_plugin_config
)
from uno.core.plugins.registry import register_plugin, get_plugin, get_plugins
from uno.core.plugins.manager import init_plugins, enable_plugin, disable_plugin
from uno.core.plugins.extension import (
    ExtensionPoint, register_extension_point, register_extension,
    get_extensions, create_extension_point
)
from uno.core.plugins.hooks import register_hook, call_hook


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("uno.example.plugins")


# Example Extension Point Interface
class GreeterExtension:
    """Interface for greeter extensions."""
    
    def get_greeting(self, name: str) -> str:
        """
        Get a greeting message.
        
        Args:
            name: Name to greet
            
        Returns:
            Greeting message
        """
        raise NotImplementedError("Subclasses must implement get_greeting")


# Example Plugin 1: Simple Greeter
class SimpleGreeterPlugin(Plugin):
    """A simple greeter plugin that provides a basic greeting."""
    
    def __init__(self):
        """Initialize the plugin."""
        info = create_plugin_info(
            id="simple_greeter",
            name="Simple Greeter",
            version="1.0.0",
            description="A simple greeter plugin that provides a basic greeting",
            author="Uno Framework",
            plugin_type=PluginType.UTILITY
        )
        
        config = create_plugin_config(
            schema={
                "greeting": {
                    "type": "string",
                    "description": "Greeting to use",
                    "default": "Hello"
                }
            },
            defaults={
                "greeting": "Hello"
            }
        )
        
        super().__init__(info, config)
    
    async def load(self) -> None:
        """Load the plugin."""
        logger.info(f"Loading {self.name}...")
    
    async def unload(self) -> None:
        """Unload the plugin."""
        logger.info(f"Unloading {self.name}...")
    
    async def enable(self) -> None:
        """Enable the plugin."""
        logger.info(f"Enabling {self.name}...")
        
        # Register greeter extension
        class SimpleGreeter(GreeterExtension):
            def __init__(self, plugin: SimpleGreeterPlugin):
                self.plugin = plugin
            
            def get_greeting(self, name: str) -> str:
                greeting = self.plugin.config.get("greeting", "Hello")
                return f"{greeting}, {name}!"
        
        register_extension(
            extension_point_id="greeter",
            extension_id="simple_greeter",
            extension=SimpleGreeter(self)
        )
    
    async def disable(self) -> None:
        """Disable the plugin."""
        logger.info(f"Disabling {self.name}...")


# Example Plugin 2: Fancy Greeter
class FancyGreeterPlugin(Plugin):
    """A fancy greeter plugin that provides a more elaborate greeting."""
    
    def __init__(self):
        """Initialize the plugin."""
        info = create_plugin_info(
            id="fancy_greeter",
            name="Fancy Greeter",
            version="1.0.0",
            description="A fancy greeter plugin that provides a more elaborate greeting",
            author="Uno Framework",
            plugin_type=PluginType.UTILITY
        )
        
        config = create_plugin_config(
            schema={
                "pre_greeting": {
                    "type": "string",
                    "description": "Text before the name",
                    "default": "Greetings, esteemed"
                },
                "post_greeting": {
                    "type": "string",
                    "description": "Text after the name",
                    "default": "Welcome to our application!"
                }
            },
            defaults={
                "pre_greeting": "Greetings, esteemed",
                "post_greeting": "Welcome to our application!"
            }
        )
        
        super().__init__(info, config)
    
    async def load(self) -> None:
        """Load the plugin."""
        logger.info(f"Loading {self.name}...")
    
    async def unload(self) -> None:
        """Unload the plugin."""
        logger.info(f"Unloading {self.name}...")
    
    async def enable(self) -> None:
        """Enable the plugin."""
        logger.info(f"Enabling {self.name}...")
        
        # Register greeter extension
        class FancyGreeter(GreeterExtension):
            def __init__(self, plugin: FancyGreeterPlugin):
                self.plugin = plugin
            
            def get_greeting(self, name: str) -> str:
                pre = self.plugin.config.get("pre_greeting", "Greetings, esteemed")
                post = self.plugin.config.get("post_greeting", "Welcome to our application!")
                return f"{pre} {name}! {post}"
        
        register_extension(
            extension_point_id="greeter",
            extension_id="fancy_greeter",
            extension=FancyGreeter(self)
        )
    
    async def disable(self) -> None:
        """Disable the plugin."""
        logger.info(f"Disabling {self.name}...")


# Example application using plugins
class GreeterApp:
    """Example application that uses greeter plugins."""
    
    def __init__(self):
        """Initialize the application."""
        self.logger = logging.getLogger("uno.example.greeter_app")
    
    async def setup(self) -> None:
        """Set up the application."""
        # Register extension point for greeters
        greeter_extension_point = create_extension_point(
            id="greeter",
            name="Greeter",
            description="Extension point for greeting providers",
            interface=GreeterExtension
        )
        
        register_extension_point(greeter_extension_point)
        
        # Register plugin lifecycle hook
        register_hook(
            "plugin_enabled",
            self.on_plugin_enabled
        )
    
    async def on_plugin_enabled(self, plugin: Plugin) -> None:
        """
        Hook called when a plugin is enabled.
        
        Args:
            plugin: Plugin that was enabled
        """
        self.logger.info(f"Plugin enabled: {plugin.name} ({plugin.id})")
    
    async def greet(self, name: str) -> List[str]:
        """
        Get greetings from all enabled greeter plugins.
        
        Args:
            name: Name to greet
            
        Returns:
            List of greeting messages
        """
        greetings = []
        
        # Get all greeter extensions
        greeter_extensions = get_extensions("greeter")
        
        for ext_id, ext_data in greeter_extensions.items():
            extension = ext_data["extension"]
            try:
                greeting = extension.get_greeting(name)
                greetings.append(f"[{ext_id}] {greeting}")
            except Exception as e:
                self.logger.error(f"Error getting greeting from {ext_id}: {str(e)}")
        
        return greetings


async def run_example():
    """Run the plugin system example."""
    # Create the greeter application
    app = GreeterApp()
    await app.setup()
    
    # Create and register plugins
    simple_greeter = SimpleGreeterPlugin()
    fancy_greeter = FancyGreeterPlugin()
    
    register_plugin(simple_greeter)
    register_plugin(fancy_greeter)
    
    # Print registered plugins
    plugins = get_plugins()
    logger.info(f"Registered {len(plugins)} plugins:")
    for plugin in plugins:
        logger.info(f"  - {plugin.name} ({plugin.id}) v{plugin.version}")
    
    # Initialize plugins
    total, loaded, enabled = await init_plugins(app_version="1.0.0")
    logger.info(f"Initialized {total} plugins: {loaded} loaded, {enabled} enabled")
    
    # Enable plugins
    await enable_plugin(simple_greeter)
    await enable_plugin(fancy_greeter)
    
    # Try the greeter application
    name = "User"
    greetings = await app.greet(name)
    
    logger.info(f"Greetings for {name}:")
    for greeting in greetings:
        logger.info(f"  {greeting}")
    
    # Update plugin configuration
    await simple_greeter.update_config({"greeting": "Hi there"})
    await fancy_greeter.update_config({
        "pre_greeting": "Most cordial salutations,",
        "post_greeting": "We're absolutely delighted to have you with us!"
    })
    
    # Try the greeter application again with updated config
    greetings = await app.greet(name)
    
    logger.info(f"Greetings after config update:")
    for greeting in greetings:
        logger.info(f"  {greeting}")
    
    # Disable a plugin
    await disable_plugin(fancy_greeter)
    
    # Try the greeter application with only one plugin
    greetings = await app.greet(name)
    
    logger.info(f"Greetings after disabling fancy_greeter:")
    for greeting in greetings:
        logger.info(f"  {greeting}")


def main():
    """Run the plugin example."""
    asyncio.run(run_example())


if __name__ == "__main__":
    main()