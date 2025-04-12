"""
Admin interfaces for tenant configuration management.

This module provides API routes for managing tenant-specific configuration settings,
including retrieving, updating, and resetting configuration values.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Request
from pydantic import BaseModel, validator

from uno.core.multitenancy.config import TenantConfig, TenantConfigService, TenantConfigError
from uno.core.multitenancy.utils import tenant_admin_required, get_tenant_id_from_request
from uno.core.multitenancy.repository import TenantAwareRepository
from uno.core.multitenancy.models import TenantSettings
from uno.database.session import get_session


# Request/response models for the admin API
class ConfigValueRequest(BaseModel):
    """Request model for setting a configuration value."""
    value: Any


class ConfigSettingResponse(BaseModel):
    """Response model for a configuration setting."""
    key: str
    value: Any
    is_default: bool
    type: str
    description: str
    options: List[Any] = []
    validation: Dict[str, Any] = {}


class ConfigKeyResponse(BaseModel):
    """Response model for a configuration key listing."""
    key: str
    type: str
    description: str


def create_tenant_config_router(
    default_config: Dict[str, Any],
    schema: Optional[Dict[str, Dict[str, Any]]] = None
) -> APIRouter:
    """
    Create an API router for tenant configuration management.
    
    Args:
        default_config: Default configuration values
        schema: Optional schema for configuration validation
        
    Returns:
        A FastAPI router with tenant configuration endpoints
    """
    router = APIRouter(prefix="/admin/config", tags=["Tenant Configuration"])
    
    # Dependency for getting the tenant config service
    async def get_tenant_config_service():
        session = await get_session()
        
        # Create a repository for tenant settings
        settings_repo = TenantAwareRepository(
            session, TenantSettings
        )
        
        # Create the tenant config manager
        tenant_config = TenantConfig(
            default_config=default_config,
            settings_repo=settings_repo
        )
        
        # Create the tenant config service
        return TenantConfigService(
            tenant_config=tenant_config,
            schema=schema
        )
    
    # --- Tenant configuration endpoints ---
    
    @router.get(
        "/",
        response_model=Dict[str, Any],
        dependencies=[Depends(tenant_admin_required())]
    )
    async def get_tenant_config(
        flatten: bool = Query(False, description="Flatten nested dictionaries with dot notation"),
        config_service: TenantConfigService = Depends(get_tenant_config_service)
    ):
        """Get the configuration for the current tenant."""
        try:
            return await config_service.get_config(flatten=flatten)
        except TenantConfigError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.get(
        "/keys",
        response_model=List[ConfigKeyResponse],
        dependencies=[Depends(tenant_admin_required())]
    )
    async def list_config_keys():
        """List all available configuration keys with metadata."""
        keys = []
        
        if schema:
            for key, info in schema.items():
                keys.append({
                    "key": key,
                    "type": info.get("type", "any"),
                    "description": info.get("description", "")
                })
        else:
            # If no schema is provided, extract keys from default_config
            for key in _extract_keys(default_config):
                keys.append({
                    "key": key,
                    "type": "any",
                    "description": ""
                })
        
        return sorted(keys, key=lambda k: k["key"])
    
    @router.get(
        "/{key}",
        response_model=ConfigSettingResponse,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def get_config_value(
        key: str = Path(..., description="Configuration key"),
        config_service: TenantConfigService = Depends(get_tenant_config_service)
    ):
        """Get a specific configuration value."""
        try:
            return await config_service.get_setting(key)
        except TenantConfigError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
    
    @router.put(
        "/{key}",
        response_model=ConfigSettingResponse,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def set_config_value(
        key: str,
        config_value: ConfigValueRequest,
        config_service: TenantConfigService = Depends(get_tenant_config_service)
    ):
        """Set a specific configuration value."""
        try:
            return await config_service.set_setting(key, config_value.value)
        except TenantConfigError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.delete(
        "/{key}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def delete_config_value(
        key: str,
        config_service: TenantConfigService = Depends(get_tenant_config_service)
    ):
        """Delete a specific configuration value, resetting it to the default."""
        try:
            success = await config_service.delete_setting(key)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Configuration key '{key}' not found"
                )
            return None
        except TenantConfigError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.post(
        "/reset",
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def reset_tenant_config(
        config_service: TenantConfigService = Depends(get_tenant_config_service)
    ):
        """Reset all configuration values to defaults."""
        try:
            count = await config_service.reset_config()
            return {"reset_count": count}
        except TenantConfigError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    return router


def _extract_keys(config: Dict[str, Any], prefix: str = "") -> List[str]:
    """
    Extract all keys from a nested dictionary, with dot notation for nested keys.
    
    Args:
        config: Configuration dictionary
        prefix: Prefix for nested keys
        
    Returns:
        List of all keys in the dictionary
    """
    keys = []
    
    for key, value in config.items():
        full_key = f"{prefix}.{key}" if prefix else key
        keys.append(full_key)
        
        if isinstance(value, dict):
            keys.extend(_extract_keys(value, full_key))
    
    return keys


# Example default configuration
DEFAULT_CONFIG = {
    "appearance": {
        "theme": "light",
        "logo_url": "/assets/logo.png",
        "primary_color": "#3498db",
        "accent_color": "#2ecc71"
    },
    "features": {
        "advanced_search": True,
        "export": True,
        "import": True,
        "analytics": False,
        "custom_reports": False
    },
    "security": {
        "password_policy": {
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special": True
        },
        "session_timeout": 30,  # minutes
        "max_login_attempts": 5
    },
    "integrations": {
        "email": {
            "enabled": True,
            "provider": "smtp",
            "from_email": "noreply@example.com"
        },
        "slack": {
            "enabled": False,
            "webhook_url": ""
        },
        "webhooks": {
            "enabled": False,
            "endpoints": []
        }
    },
    "notifications": {
        "email": True,
        "in_app": True,
        "push": False
    },
    "defaults": {
        "page_size": 20,
        "date_format": "YYYY-MM-DD",
        "time_format": "HH:mm:ss",
        "timezone": "UTC",
        "language": "en"
    }
}

# Example configuration schema
CONFIG_SCHEMA = {
    "appearance.theme": {
        "type": "string",
        "description": "Application theme",
        "options": ["light", "dark", "auto"],
        "validation": {
            "minLength": 1,
            "maxLength": 50
        }
    },
    "appearance.logo_url": {
        "type": "string",
        "description": "URL for the tenant's logo",
        "validation": {
            "minLength": 1,
            "maxLength": 500
        }
    },
    "appearance.primary_color": {
        "type": "string",
        "description": "Primary brand color (hex)",
        "validation": {
            "pattern": "^#[0-9A-Fa-f]{6}$"
        }
    },
    "appearance.accent_color": {
        "type": "string",
        "description": "Accent color (hex)",
        "validation": {
            "pattern": "^#[0-9A-Fa-f]{6}$"
        }
    },
    "features.advanced_search": {
        "type": "boolean",
        "description": "Enable advanced search features"
    },
    "features.export": {
        "type": "boolean",
        "description": "Enable data export"
    },
    "features.import": {
        "type": "boolean",
        "description": "Enable data import"
    },
    "features.analytics": {
        "type": "boolean",
        "description": "Enable analytics dashboard"
    },
    "features.custom_reports": {
        "type": "boolean",
        "description": "Enable custom reports"
    },
    "security.password_policy.min_length": {
        "type": "number",
        "description": "Minimum password length",
        "validation": {
            "minimum": 6,
            "maximum": 72
        }
    },
    "security.password_policy.require_uppercase": {
        "type": "boolean",
        "description": "Require uppercase letters in passwords"
    },
    "security.password_policy.require_lowercase": {
        "type": "boolean",
        "description": "Require lowercase letters in passwords"
    },
    "security.password_policy.require_numbers": {
        "type": "boolean",
        "description": "Require numbers in passwords"
    },
    "security.password_policy.require_special": {
        "type": "boolean",
        "description": "Require special characters in passwords"
    },
    "security.session_timeout": {
        "type": "number",
        "description": "Session timeout in minutes",
        "validation": {
            "minimum": 5,
            "maximum": 1440
        }
    },
    "security.max_login_attempts": {
        "type": "number",
        "description": "Maximum failed login attempts before lockout",
        "validation": {
            "minimum": 1,
            "maximum": 20
        }
    },
    "integrations.email.enabled": {
        "type": "boolean",
        "description": "Enable email integration"
    },
    "integrations.email.provider": {
        "type": "string",
        "description": "Email provider",
        "options": ["smtp", "sendgrid", "mailgun", "ses"]
    },
    "integrations.email.from_email": {
        "type": "string",
        "description": "From email address",
        "validation": {
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        }
    },
    "integrations.slack.enabled": {
        "type": "boolean",
        "description": "Enable Slack integration"
    },
    "integrations.slack.webhook_url": {
        "type": "string",
        "description": "Slack webhook URL"
    },
    "integrations.webhooks.enabled": {
        "type": "boolean",
        "description": "Enable webhooks"
    },
    "integrations.webhooks.endpoints": {
        "type": "array",
        "description": "Webhook endpoints",
        "validation": {
            "maxItems": 10
        }
    },
    "notifications.email": {
        "type": "boolean",
        "description": "Enable email notifications"
    },
    "notifications.in_app": {
        "type": "boolean",
        "description": "Enable in-app notifications"
    },
    "notifications.push": {
        "type": "boolean",
        "description": "Enable push notifications"
    },
    "defaults.page_size": {
        "type": "number",
        "description": "Default page size for lists",
        "validation": {
            "minimum": 5,
            "maximum": 100
        }
    },
    "defaults.date_format": {
        "type": "string",
        "description": "Default date format",
        "options": ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"]
    },
    "defaults.time_format": {
        "type": "string",
        "description": "Default time format",
        "options": ["HH:mm:ss", "HH:mm", "hh:mm:ss a", "hh:mm a"]
    },
    "defaults.timezone": {
        "type": "string",
        "description": "Default timezone",
        "options": ["UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific", "Europe/London", "Europe/Paris"]
    },
    "defaults.language": {
        "type": "string",
        "description": "Default language",
        "options": ["en", "es", "fr", "de", "it", "pt", "ja", "zh"]
    }
}


# Default tenant configuration router
default_tenant_config_router = create_tenant_config_router(
    default_config=DEFAULT_CONFIG,
    schema=CONFIG_SCHEMA
)