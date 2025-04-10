# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Endpoint factory component for UnoObj models.

This module provides functionality for creating FastAPI endpoints for UnoObj models.
"""

from typing import Dict, Type, List, Optional, Any

from pydantic import BaseModel
from fastapi import FastAPI

from uno.api.endpoint import (
    CreateEndpoint,
    ViewEndpoint,
    ListEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
    ImportEndpoint,
)


class UnoEndpointFactory:
    """
    Factory for creating FastAPI endpoints for UnoObj models.

    This class handles the creation of FastAPI endpoints for UnoObj models.
    """

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
        app: FastAPI,
        model_obj: Any,
        endpoints: List[str] = None,
        endpoint_tags: List[str] = None,
    ) -> None:
        """
        Create endpoints for a model object.

        Args:
            app: The FastAPI application
            model_obj: The model object to create endpoints for
            endpoints: The types of endpoints to create (defaults to all)
            endpoint_tags: The tags to apply to the endpoints
        """
        endpoints = endpoints or [
            "Create",
            "View",
            "List",
            "Update",
            "Delete",
            "Import",
        ]

        for endpoint_type in endpoints:
            if endpoint_type not in self.ENDPOINT_TYPES:
                continue

            endpoint_class = self.ENDPOINT_TYPES[endpoint_type]

            try:
                endpoint_class(
                    model=model_obj,
                    app=app,
                )
            except Exception as e:
                # Log the error but continue with other endpoints
                print(
                    f"Error creating {endpoint_type} endpoint for {model_obj.__class__.__name__}: {e}"
                )
