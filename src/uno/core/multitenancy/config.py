"""
Tenant-specific configuration management.

This module provides utilities for managing tenant-specific configuration settings,
including defaults, overrides, and inheritance.
"""

import copy
from typing import Dict, Any, Optional, List, Set, Tuple, Union
import logging

from uno.core.multitenancy.models import Tenant, TenantSettings
from uno.core.multitenancy.repository import TenantAwareRepository
from uno.core.multitenancy.context import get_current_tenant_context


class TenantConfigError(Exception):
    """Error raised for tenant configuration issues."""
    pass


class TenantConfig:
    """
    Tenant-specific configuration manager.
    
    This class provides methods for managing tenant-specific configuration settings,
    with support for defaults, inheritance, and validation.
    """
    
    def __init__(
        self,
        default_config: Dict[str, Any],
        settings_repo: Optional[TenantAwareRepository] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the tenant configuration manager.
        
        Args:
            default_config: Default configuration values
            settings_repo: Repository for tenant settings
            logger: Optional logger instance
        """
        self.default_config = default_config
        self.settings_repo = settings_repo
        self._tenant_configs: Dict[str, Dict[str, Any]] = {}
        self.logger = logger or logging.getLogger(__name__)
    
    async def get_tenant_config(
        self, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the configuration for a specific tenant.
        
        This method merges the default configuration with tenant-specific settings.
        If no tenant_id is provided, it uses the current tenant from the context.
        
        Args:
            tenant_id: Optional tenant ID to get configuration for
            
        Returns:
            The merged configuration dictionary
        """
        # Use the current tenant context if no tenant_id is provided
        if tenant_id is None:
            tenant_id = get_current_tenant_context()
            if not tenant_id:
                return copy.deepcopy(self.default_config)
        
        # Use cached config if available
        if tenant_id in self._tenant_configs:
            return copy.deepcopy(self._tenant_configs[tenant_id])
        
        # Get tenant settings from repository
        tenant_config = copy.deepcopy(self.default_config)
        
        if self.settings_repo:
            # Get all settings for the tenant
            settings = await self.settings_repo.find_by(tenant_id=tenant_id)
            
            # Apply tenant-specific settings
            for setting in settings:
                self._set_nested_value(
                    tenant_config, setting.key.split('.'), setting.value
                )
        
        # Cache the result
        self._tenant_configs[tenant_id] = tenant_config
        
        return copy.deepcopy(tenant_config)
    
    async def set_tenant_config(
        self, key: str, value: Any, tenant_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> TenantSettings:
        """
        Set a configuration value for a tenant.
        
        Args:
            key: Configuration key (dot notation supported)
            value: Configuration value
            tenant_id: Optional tenant ID (defaults to current tenant)
            description: Optional description of the setting
            
        Returns:
            The created or updated tenant setting
            
        Raises:
            TenantConfigError: If no tenant is specified and no current tenant context
            ValueError: If the settings repository is not available
        """
        # Use the current tenant context if no tenant_id is provided
        if tenant_id is None:
            tenant_id = get_current_tenant_context()
            if not tenant_id:
                raise TenantConfigError("No tenant specified and no current tenant context")
        
        if not self.settings_repo:
            raise ValueError("Cannot set tenant config: settings repository not available")
        
        # Check if setting already exists
        settings = await self.settings_repo.find_by(tenant_id=tenant_id, key=key)
        
        if settings:
            # Update existing setting
            setting = settings[0]
            updated = await self.settings_repo.update(
                setting.id, {"value": value, "description": description}
            )
            
            # Update cache if it exists
            if tenant_id in self._tenant_configs:
                self._set_nested_value(
                    self._tenant_configs[tenant_id], key.split('.'), value
                )
            
            return updated
        else:
            # Create new setting
            new_setting = TenantSettings(
                tenant_id=tenant_id,
                key=key,
                value=value,
                description=description
            )
            created = await self.settings_repo.create(new_setting.model_dump())
            
            # Update cache if it exists
            if tenant_id in self._tenant_configs:
                self._set_nested_value(
                    self._tenant_configs[tenant_id], key.split('.'), value
                )
            
            return created
    
    async def delete_tenant_config(
        self, key: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete a configuration value for a tenant.
        
        Args:
            key: Configuration key to delete
            tenant_id: Optional tenant ID (defaults to current tenant)
            
        Returns:
            True if the setting was deleted, False otherwise
            
        Raises:
            TenantConfigError: If no tenant is specified and no current tenant context
            ValueError: If the settings repository is not available
        """
        # Use the current tenant context if no tenant_id is provided
        if tenant_id is None:
            tenant_id = get_current_tenant_context()
            if not tenant_id:
                raise TenantConfigError("No tenant specified and no current tenant context")
        
        if not self.settings_repo:
            raise ValueError("Cannot delete tenant config: settings repository not available")
        
        # Find the setting
        settings = await self.settings_repo.find_by(tenant_id=tenant_id, key=key)
        
        if not settings:
            return False
        
        # Delete the setting
        setting = settings[0]
        success = await self.settings_repo.delete(setting.id)
        
        # Update cache if it exists
        if success and tenant_id in self._tenant_configs:
            self._delete_nested_value(self._tenant_configs[tenant_id], key.split('.'))
        
        return success
    
    async def reset_tenant_config(self, tenant_id: Optional[str] = None) -> int:
        """
        Reset all configuration values for a tenant to defaults.
        
        Args:
            tenant_id: Optional tenant ID (defaults to current tenant)
            
        Returns:
            Number of settings deleted
            
        Raises:
            TenantConfigError: If no tenant is specified and no current tenant context
            ValueError: If the settings repository is not available
        """
        # Use the current tenant context if no tenant_id is provided
        if tenant_id is None:
            tenant_id = get_current_tenant_context()
            if not tenant_id:
                raise TenantConfigError("No tenant specified and no current tenant context")
        
        if not self.settings_repo:
            raise ValueError("Cannot reset tenant config: settings repository not available")
        
        # Delete all settings for the tenant
        settings = await self.settings_repo.find_by(tenant_id=tenant_id)
        count = 0
        
        for setting in settings:
            success = await self.settings_repo.delete(setting.id)
            if success:
                count += 1
        
        # Clear the cache for this tenant
        if tenant_id in self._tenant_configs:
            del self._tenant_configs[tenant_id]
        
        return count
    
    async def get_tenant_setting(
        self, key: str, tenant_id: Optional[str] = None
    ) -> Tuple[Any, bool]:
        """
        Get a specific setting value for a tenant.
        
        Args:
            key: Configuration key
            tenant_id: Optional tenant ID (defaults to current tenant)
            
        Returns:
            Tuple of (value, is_default) where is_default indicates if the value is the default
            
        Raises:
            TenantConfigError: If the key doesn't exist in the default config
        """
        # Get the current config
        config = await self.get_tenant_config(tenant_id)
        
        # Get the value from the config
        try:
            value = self._get_nested_value(config, key.split('.'))
            
            # Check if it's the default value
            default_value = self._get_nested_value(self.default_config, key.split('.'))
            is_default = value == default_value
            
            return value, is_default
        except KeyError:
            # If the key doesn't exist in the config, it doesn't exist in the default config
            raise TenantConfigError(f"Configuration key '{key}' not found")
    
    def invalidate_cache(self, tenant_id: Optional[str] = None) -> None:
        """
        Invalidate the configuration cache for a tenant.
        
        Args:
            tenant_id: Optional tenant ID (defaults to all tenants)
        """
        if tenant_id:
            if tenant_id in self._tenant_configs:
                del self._tenant_configs[tenant_id]
        else:
            self._tenant_configs.clear()
    
    def _get_nested_value(self, config: Dict[str, Any], keys: List[str]) -> Any:
        """
        Get a nested value from a dictionary using a list of keys.
        
        Args:
            config: Dictionary to get value from
            keys: List of keys to traverse
            
        Returns:
            The value at the specified path
            
        Raises:
            KeyError: If the path doesn't exist
        """
        current = config
        for key in keys:
            current = current[key]
        return current
    
    def _set_nested_value(
        self, config: Dict[str, Any], keys: List[str], value: Any
    ) -> None:
        """
        Set a nested value in a dictionary using a list of keys.
        
        Args:
            config: Dictionary to set value in
            keys: List of keys to traverse
            value: Value to set
        """
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def _delete_nested_value(self, config: Dict[str, Any], keys: List[str]) -> None:
        """
        Delete a nested value from a dictionary using a list of keys.
        
        Args:
            config: Dictionary to delete value from
            keys: List of keys to traverse
        """
        current = config
        for key in keys[:-1]:
            if key not in current:
                # Path doesn't exist, nothing to delete
                return
            current = current[key]
        
        if keys[-1] in current:
            del current[keys[-1]]


class TenantConfigService:
    """
    Service for managing tenant configuration settings.
    
    This service provides high-level methods for managing tenant-specific
    configuration settings, with validation and schema support.
    """
    
    def __init__(
        self,
        tenant_config: TenantConfig,
        schema: Optional[Dict[str, Dict[str, Any]]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the tenant configuration service.
        
        Args:
            tenant_config: Tenant configuration manager
            schema: Optional schema for configuration validation
            logger: Optional logger instance
        """
        self.tenant_config = tenant_config
        self.schema = schema or {}
        self.logger = logger or logging.getLogger(__name__)
    
    async def get_config(
        self, tenant_id: Optional[str] = None, flatten: bool = False
    ) -> Dict[str, Any]:
        """
        Get the configuration for a tenant.
        
        Args:
            tenant_id: Optional tenant ID
            flatten: Whether to flatten nested dictionaries with dot notation
            
        Returns:
            The tenant configuration
        """
        config = await self.tenant_config.get_tenant_config(tenant_id)
        
        if flatten:
            return self._flatten_dict(config)
        else:
            return config
    
    async def get_setting(
        self, key: str, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a specific setting with metadata.
        
        Args:
            key: Configuration key
            tenant_id: Optional tenant ID
            
        Returns:
            Dictionary with the setting value and metadata
            
        Raises:
            TenantConfigError: If the key doesn't exist
        """
        value, is_default = await self.tenant_config.get_tenant_setting(key, tenant_id)
        
        # Get schema info if available
        schema_info = self.schema.get(key, {})
        
        return {
            "key": key,
            "value": value,
            "is_default": is_default,
            "type": schema_info.get("type", type(value).__name__),
            "description": schema_info.get("description", ""),
            "options": schema_info.get("options", []),
            "validation": schema_info.get("validation", {})
        }
    
    async def set_setting(
        self, key: str, value: Any, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set a specific setting.
        
        Args:
            key: Configuration key
            value: Configuration value
            tenant_id: Optional tenant ID
            
        Returns:
            Dictionary with the updated setting
            
        Raises:
            TenantConfigError: If validation fails
        """
        # Validate the value if schema is available
        if key in self.schema:
            self._validate_value(key, value)
        
        # Set the value
        description = self.schema.get(key, {}).get("description", "")
        await self.tenant_config.set_tenant_config(key, value, tenant_id, description)
        
        # Return the updated setting
        return await self.get_setting(key, tenant_id)
    
    async def delete_setting(
        self, key: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete a specific setting.
        
        Args:
            key: Configuration key
            tenant_id: Optional tenant ID
            
        Returns:
            True if the setting was deleted, False otherwise
        """
        return await self.tenant_config.delete_tenant_config(key, tenant_id)
    
    async def reset_config(
        self, tenant_id: Optional[str] = None
    ) -> int:
        """
        Reset all settings to defaults.
        
        Args:
            tenant_id: Optional tenant ID
            
        Returns:
            Number of settings reset
        """
        return await self.tenant_config.reset_tenant_config(tenant_id)
    
    def _validate_value(self, key: str, value: Any) -> None:
        """
        Validate a configuration value against the schema.
        
        Args:
            key: Configuration key
            value: Value to validate
            
        Raises:
            TenantConfigError: If validation fails
        """
        schema = self.schema.get(key, {})
        
        # Check type
        expected_type = schema.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(value, str):
                raise TenantConfigError(f"Value for '{key}' must be a string")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                raise TenantConfigError(f"Value for '{key}' must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                raise TenantConfigError(f"Value for '{key}' must be a boolean")
            elif expected_type == "array" and not isinstance(value, list):
                raise TenantConfigError(f"Value for '{key}' must be an array")
            elif expected_type == "object" and not isinstance(value, dict):
                raise TenantConfigError(f"Value for '{key}' must be an object")
        
        # Check options
        options = schema.get("options")
        if options and value not in options:
            raise TenantConfigError(
                f"Value for '{key}' must be one of: {', '.join(str(o) for o in options)}"
            )
        
        # Check validation rules
        validation = schema.get("validation", {})
        
        # String validation
        if isinstance(value, str):
            min_length = validation.get("minLength")
            max_length = validation.get("maxLength")
            pattern = validation.get("pattern")
            
            if min_length is not None and len(value) < min_length:
                raise TenantConfigError(
                    f"Value for '{key}' must be at least {min_length} characters"
                )
            if max_length is not None and len(value) > max_length:
                raise TenantConfigError(
                    f"Value for '{key}' must be at most {max_length} characters"
                )
            if pattern and not re.match(pattern, value):
                raise TenantConfigError(
                    f"Value for '{key}' must match pattern: {pattern}"
                )
        
        # Number validation
        if isinstance(value, (int, float)):
            minimum = validation.get("minimum")
            maximum = validation.get("maximum")
            
            if minimum is not None and value < minimum:
                raise TenantConfigError(
                    f"Value for '{key}' must be at least {minimum}"
                )
            if maximum is not None and value > maximum:
                raise TenantConfigError(
                    f"Value for '{key}' must be at most {maximum}"
                )
        
        # Array validation
        if isinstance(value, list):
            min_items = validation.get("minItems")
            max_items = validation.get("maxItems")
            unique_items = validation.get("uniqueItems")
            
            if min_items is not None and len(value) < min_items:
                raise TenantConfigError(
                    f"Value for '{key}' must have at least {min_items} items"
                )
            if max_items is not None and len(value) > max_items:
                raise TenantConfigError(
                    f"Value for '{key}' must have at most {max_items} items"
                )
            if unique_items and len(value) != len(set(value)):
                raise TenantConfigError(
                    f"Value for '{key}' must have unique items"
                )
    
    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """
        Flatten a nested dictionary with dot notation.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for recursion
            sep: Separator for keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)