# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Endpoint factory for creating FastAPI endpoints for domain models.

This module provides a factory for creating standardized FastAPI endpoints
for domain models, making it easy to expose model operations through a
RESTful API with consistent patterns and error handling.
"""

import logging
import inspect
import traceback
from typing import Dict, Type, List, Optional, Any, Union, Callable, Set

from pydantic import BaseModel
from fastapi import FastAPI, APIRouter

from uno.api.endpoint import (
    UnoEndpoint,
    CreateEndpoint,
    ViewEndpoint,
    ListEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
    ImportEndpoint,
)

# Configure logger
logger = logging.getLogger(__name__)


class EndpointCreationError(Exception):
    """Error raised when an endpoint cannot be created."""
    
    def __init__(self, endpoint_type: str, model_name: str, cause: Exception):
        """
        Initialize the error.
        
        Args:
            endpoint_type: Type of endpoint (Create, View, etc.)
            model_name: Name of the model
            cause: Original exception
        """
        self.endpoint_type = endpoint_type
        self.model_name = model_name
        self.cause = cause
        super().__init__(f"Error creating {endpoint_type} endpoint for {model_name}: {cause}")


class UnoEndpointFactory:
    """
    Factory for creating FastAPI endpoints for domain models.
    
    This class simplifies the creation of standardized API endpoints for
    domain models, ensuring consistent behavior and error handling across
    your API.
    """

    # Map of endpoint type names to endpoint classes
    ENDPOINT_TYPES = {
        "Create": CreateEndpoint,
        "View": ViewEndpoint,
        "List": ListEndpoint,
        "Update": UpdateEndpoint,
        "Delete": DeleteEndpoint,
        "Import": ImportEndpoint,
    }

    def __init__(self):
        """Initialize the endpoint factory."""
        pass

    def create_endpoints(
        self,
        app: Optional[FastAPI] = None,
        model_obj: Optional[Any] = None,
        repository: Optional[Any] = None,
        entity_type: Optional[Type] = None,
        schema_manager: Optional[Any] = None,
        endpoints: Optional[List[str]] = None,
        endpoint_tags: Optional[List[str]] = None,
        router: Optional[APIRouter] = None,
        path_prefix: Optional[str] = None,
        include_in_schema: bool = True,
        status_codes: Optional[Dict[str, int]] = None,
        dependencies: Optional[List[Depends]] = None,
    ) -> Dict[str, UnoEndpoint]:
        """
        Create endpoints for a model object or repository.

        Args:
            app: The FastAPI application
            model_obj: The model object to create endpoints for (legacy approach)
            repository: The repository to create endpoints for (DDD approach)
            entity_type: The entity type for the repository (required if repository is provided)
            schema_manager: The schema manager for the repository (required if repository is provided)
            endpoints: The types of endpoints to create (defaults to standard CRUD)
            endpoint_tags: The tags to apply to the endpoints
            router: Optional router to use instead of app directly
            path_prefix: Optional path prefix for all endpoints
            include_in_schema: Whether to include endpoints in OpenAPI schema
            status_codes: Optional mapping of endpoint types to status codes
            dependencies: Optional list of dependencies to add to all endpoints
            
        Returns:
            Dictionary mapping endpoint types to created endpoint instances
            
        Raises:
            EndpointCreationError: If an endpoint couldn't be created
            ValueError: If invalid arguments are provided
        """
        # Validate inputs
        if not app and not router:
            raise ValueError("Either app or router must be provided")
            
        # Check for repository or model
        if repository:
            # Domain-driven approach
            if not entity_type:
                raise ValueError("Entity type must be provided when using a repository")
                
            # Import the adapter here to avoid circular imports
            from uno.api.repository_adapter import RepositoryAdapter
            
            # Create a repository adapter
            adapter = RepositoryAdapter(
                repository=repository,
                entity_type=entity_type,
                schema_manager=schema_manager,
            )
            
            # Use the adapter as the model
            target_obj = adapter
            model_name = entity_type.__name__
        elif model_obj:
            # Legacy model class approach
            target_obj = model_obj
            model_name = getattr(model_obj, '__name__', model_obj.__class__.__name__)
        else:
            raise ValueError("Either model_obj or repository must be provided")
            
        # Use standard endpoints if none specified
        if endpoints is None:
            endpoints = ["Create", "View", "List", "Update", "Delete"]
        elif not endpoints:
            logger.info(f"No endpoints specified for {model_name}, skipping")
            return {}
        
        # Initialize result
        created_endpoints = {}
        
        # Prepare status codes and dependencies
        status_codes = status_codes or {}
        dependencies = dependencies or []
        
        # Keep track of failed endpoints
        failed_endpoints = []
        
        # Log endpoint creation start
        logger.info(f"Creating {len(endpoints)} endpoints for {model_name}: {', '.join(endpoints)}")
        
        # Create each endpoint
        for endpoint_type in endpoints:
            if endpoint_type not in self.ENDPOINT_TYPES:
                logger.warning(f"Unknown endpoint type '{endpoint_type}', skipping")
                continue

            endpoint_class = self.ENDPOINT_TYPES[endpoint_type]
            
            # Get status code if specified
            status_code = status_codes.get(endpoint_type)

            try:
                # Prepare endpoint parameters
                endpoint_params = {
                    "model": target_obj,
                    "app": app,
                    "router": router,
                    "include_in_schema": include_in_schema,
                    "dependencies": dependencies,
                }
                
                # Add optional parameters if provided
                if path_prefix:
                    endpoint_params["path_prefix"] = path_prefix
                    
                if endpoint_tags:
                    endpoint_params["tags"] = endpoint_tags
                    
                if status_code:
                    endpoint_params["status_code"] = status_code
                
                # Filter out parameters not accepted by the endpoint
                valid_params = self._filter_valid_params(endpoint_class, endpoint_params)
                
                # Create the endpoint
                endpoint = endpoint_class(**valid_params)
                
                # Add to result dictionary
                created_endpoints[endpoint_type] = endpoint
                
                logger.info(f"Created {endpoint_type} endpoint for {model_name}")
                
            except Exception as e:
                # Log the error but continue with other endpoints
                logger.error(
                    f"Error creating {endpoint_type} endpoint for {model_name}: {str(e)}"
                )
                logger.debug(traceback.format_exc())
                
                # Add to failed endpoints
                failed_endpoints.append(endpoint_type)
        
        # Log creation summary
        if failed_endpoints:
            logger.warning(
                f"Created {len(created_endpoints)}/{len(endpoints)} endpoints for {model_name}. "
                f"Failed endpoints: {', '.join(failed_endpoints)}"
            )
        else:
            logger.info(f"Successfully created {len(created_endpoints)} endpoints for {model_name}")
                
        return created_endpoints
    
    def _filter_valid_params(self, endpoint_class: Type[UnoEndpoint], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter parameters to include only those accepted by the endpoint class.
        
        Args:
            endpoint_class: The endpoint class
            params: Parameters dictionary
            
        Returns:
            Filtered parameters dictionary
        """
        if not hasattr(endpoint_class, '__init__'):
            return params
            
        init_signature = inspect.signature(endpoint_class.__init__)
        valid_params = {}
        
        for name, value in params.items():
            if name in init_signature.parameters or init_signature.parameters.get('kwargs'):
                valid_params[name] = value
                
        return valid_params
    
    def get_endpoint_class(self, endpoint_type: str) -> Optional[Type[UnoEndpoint]]:
        """
        Get the endpoint class for a given endpoint type.
        
        Args:
            endpoint_type: The endpoint type name
            
        Returns:
            The endpoint class or None if not found
        """
        return self.ENDPOINT_TYPES.get(endpoint_type)
    
    def register_endpoint_type(self, name: str, endpoint_class: Type[UnoEndpoint]) -> None:
        """
        Register a custom endpoint type.
        
        Args:
            name: The name of the endpoint type
            endpoint_class: The endpoint class
            
        Raises:
            ValueError: If an endpoint with the same name already exists
        """
        if name in self.ENDPOINT_TYPES:
            raise ValueError(f"Endpoint type '{name}' already registered")
            
        self.ENDPOINT_TYPES[name] = endpoint_class
        logger.info(f"Registered custom endpoint type: {name}")
    
    def get_available_endpoints(self) -> Set[str]:
        """
        Get the names of all available endpoint types.
        
        Returns:
            Set of endpoint type names
        """
        return set(self.ENDPOINT_TYPES.keys())
