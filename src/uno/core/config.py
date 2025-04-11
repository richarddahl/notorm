"""
Configuration management for the Uno framework.

This module provides a flexible and extensible configuration system that
supports multiple sources, environments, and validation.
"""

import json
import os
import yaml
import logging
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic, Set, Callable, cast, Union, get_type_hints, get_origin

from uno.core.protocols import ConfigProvider


T = TypeVar('T')


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, path: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            message: The error message
            path: The configuration path where the error occurred
        """
        self.path = path
        message_with_path = f"{message} (path: {path})" if path else message
        super().__init__(message_with_path)


class ConfigSource:
    """Base class for configuration sources."""
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        raise NotImplementedError("Subclasses must implement get")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: The section name
            
        Returns:
            The configuration section
        """
        raise NotImplementedError("Subclasses must implement get_section")
    
    def reload(self) -> None:
        """Reload the configuration."""
        pass


class DictConfigSource(ConfigSource):
    """Configuration source backed by a dictionary."""
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the configuration source.
        
        Args:
            data: The configuration data
        """
        self._data = data
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key (supports dot notation)
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        parts = key.split('.')
        value = self._data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: The section name (supports dot notation)
            
        Returns:
            The configuration section
        """
        if not section:
            return self._data.copy()
        
        value = self.get(section)
        if isinstance(value, dict):
            return value.copy()
        return {}


class EnvironmentConfigSource(ConfigSource):
    """Configuration source backed by environment variables."""
    
    def __init__(self, prefix: str = "", separator: str = "__"):
        """
        Initialize the configuration source.
        
        Args:
            prefix: The prefix for environment variables
            separator: The separator for nested keys
        """
        self._prefix = prefix
        self._separator = separator
    
    def _env_to_dict(self) -> Dict[str, Any]:
        """
        Convert environment variables to a dictionary.
        
        Returns:
            The configuration dictionary
        """
        result: Dict[str, Any] = {}
        
        for key, value in os.environ.items():
            if self._prefix and not key.startswith(self._prefix):
                continue
            
            # Remove prefix
            if self._prefix:
                key = key[len(self._prefix):]
                if key.startswith(self._separator):
                    key = key[len(self._separator):]
            
            # Convert to nested dictionary
            parts = key.split(self._separator)
            current = result
            
            for i, part in enumerate(parts):
                part = part.lower()  # Normalize keys to lowercase
                
                if i == len(parts) - 1:
                    # Try to parse the value as a number or boolean
                    if value.lower() == "true":
                        current[part] = True
                    elif value.lower() == "false":
                        current[part] = False
                    else:
                        try:
                            current[part] = int(value)
                        except ValueError:
                            try:
                                current[part] = float(value)
                            except ValueError:
                                current[part] = value
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        return result
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key (supports dot notation)
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        # Try direct environment variable lookup
        env_key = key.replace('.', self._separator).upper()
        if self._prefix:
            env_key = f"{self._prefix}{self._separator}{env_key}"
        
        if env_key in os.environ:
            value = os.environ[env_key]
            
            # Try to parse the value as a number or boolean
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            else:
                try:
                    return int(value)
                except ValueError:
                    try:
                        return float(value)
                    except ValueError:
                        return value
        
        # Fall back to dictionary lookup
        data = self._env_to_dict()
        parts = key.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: The section name (supports dot notation)
            
        Returns:
            The configuration section
        """
        data = self._env_to_dict()
        
        if not section:
            return data
        
        parts = section.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return {}
        
        if isinstance(value, dict):
            return value.copy()
        return {}


class FileConfigSource(ConfigSource):
    """Configuration source backed by a file."""
    
    def __init__(self, file_path: str, auto_reload: bool = False):
        """
        Initialize the configuration source.
        
        Args:
            file_path: The path to the configuration file
            auto_reload: Whether to automatically reload the configuration
        """
        self._file_path = file_path
        self._auto_reload = auto_reload
        self._data: Dict[str, Any] = {}
        self._last_modified: Optional[float] = None
        self.reload()
    
    def reload(self) -> None:
        """Reload the configuration."""
        if not os.path.exists(self._file_path):
            self._data = {}
            return
        
        # Check if the file has changed
        modified_time = os.path.getmtime(self._file_path)
        if self._last_modified is not None and self._last_modified >= modified_time:
            return
        
        self._last_modified = modified_time
        
        # Load the file
        with open(self._file_path, 'r') as f:
            if self._file_path.endswith('.json'):
                self._data = json.load(f)
            elif self._file_path.endswith(('.yaml', '.yml')):
                self._data = yaml.safe_load(f)
            else:
                raise ConfigurationError(f"Unsupported file format: {self._file_path}")
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key (supports dot notation)
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        if self._auto_reload:
            self.reload()
        
        parts = key.split('.')
        value = self._data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: The section name (supports dot notation)
            
        Returns:
            The configuration section
        """
        if self._auto_reload:
            self.reload()
        
        if not section:
            return self._data.copy()
        
        value = self.get(section)
        if isinstance(value, dict):
            return value.copy()
        return {}


class ConfigurationService(ConfigProvider):
    """Configuration service that combines multiple sources."""
    
    def __init__(self, sources: Optional[List[ConfigSource]] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the configuration service.
        
        Args:
            sources: The configuration sources
            logger: Optional logger
        """
        self._sources = sources or []
        self._logger = logger or logging.getLogger(__name__)
    
    def add_source(self, source: ConfigSource, priority: int = 0) -> None:
        """
        Add a configuration source.
        
        Sources are checked in reverse order of addition (last added, first checked).
        
        Args:
            source: The configuration source
            priority: The priority of the source (higher = checked first)
        """
        self._sources.insert(priority, source)
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        for source in self._sources:
            value = source.get(key, None)
            if value is not None:
                return value
        
        return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: The section name
            
        Returns:
            The configuration section
        """
        result: Dict[str, Any] = {}
        
        # Process sources in reverse order, so later sources override earlier ones
        for source in reversed(self._sources):
            section_data = source.get_section(section)
            result.update(section_data)
        
        return result
    
    def reload(self) -> None:
        """Reload all configuration sources."""
        for source in self._sources:
            try:
                source.reload()
            except Exception as e:
                self._logger.error(f"Error reloading configuration source {source}: {e}")
    
    def validate(self, model_type: Type[BaseModel], section: str = "") -> BaseModel:
        """
        Validate configuration against a Pydantic model.
        
        Args:
            model_type: The Pydantic model type
            section: The configuration section to validate
            
        Returns:
            The validated configuration model
            
        Raises:
            ConfigurationError: If validation fails
        """
        data = self.get_section(section)
        
        try:
            return model_type(**data)
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e}", section)
    
    @classmethod
    def create_default(cls, app_name: str, env_var_prefix: str = "") -> 'ConfigurationService':
        """
        Create a default configuration service.
        
        This method creates a configuration service with the following sources (in order of precedence):
        1. Environment variables
        2. app_name.{environment}.yaml in the current directory
        3. app_name.yaml in the current directory
        
        Args:
            app_name: The application name
            env_var_prefix: The prefix for environment variables
            
        Returns:
            The configuration service
        """
        service = cls()
        
        # Add environment variable source (highest precedence)
        service.add_source(EnvironmentConfigSource(prefix=env_var_prefix), priority=10)
        
        # Add environment-specific file source
        env = os.environ.get('ENV', 'development')
        env_file = f"{app_name}.{env}.yaml"
        if os.path.exists(env_file):
            service.add_source(FileConfigSource(env_file, auto_reload=True), priority=5)
        
        # Add default file source (lowest precedence)
        default_file = f"{app_name}.yaml"
        if os.path.exists(default_file):
            service.add_source(FileConfigSource(default_file, auto_reload=True), priority=0)
        
        return service


@dataclass
class ConfigurationOptions:
    """Base class for strongly-typed configuration options."""
    
    @classmethod
    def from_config(cls, config: ConfigProvider, section: str = "") -> 'ConfigurationOptions':
        """
        Create configuration options from a configuration provider.
        
        Args:
            config: The configuration provider
            section: The configuration section
            
        Returns:
            The configuration options
        """
        data = config.get_section(section)
        hints = get_type_hints(cls)
        args = {}
        
        for field_name, field_type in hints.items():
            if field_name.startswith('_'):
                continue
            
            default = getattr(cls, field_name, None)
            value = data.get(field_name, default)
            
            # Convert the value to the expected type
            if value is not None:
                # Handle Optional types
                if get_origin(field_type) == Union:
                    # Get the first non-None type
                    for arg in field_type.__args__:
                        if arg is not type(None):
                            field_type = arg
                            break
                
                # Try to convert the value
                try:
                    if field_type == bool and isinstance(value, str):
                        value = value.lower() == 'true'
                    elif field_type in (int, float, str):
                        value = field_type(value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(
                        f"Invalid value for {field_name}: {value} (expected {field_type.__name__})",
                        section
                    )
            
            args[field_name] = value
        
        return cls(**args)