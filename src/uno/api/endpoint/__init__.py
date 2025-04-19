"""
Unified Endpoint Framework for UNO API.

This module provides a standardized approach to creating HTTP endpoints
that integrate seamlessly with the domain entity framework.
"""

from typing import Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar, Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel

from uno.core.errors.result import Result
from uno.domain.entity.service import ApplicationService, CrudService, DomainService

__all__ = [
    "EndpointProtocol",
    "ResponseModel",
    "RequestModel",
    "IdType",
    "EntityType"
]

# Type variables for endpoint generics
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
RequestModel = TypeVar("RequestModel", bound=BaseModel)
IdType = TypeVar("IdType")
EntityType = TypeVar("EntityType")


class EndpointProtocol(Protocol, Generic[RequestModel, ResponseModel, IdType]):
    """Protocol defining the interface for API endpoints."""
    
    router: APIRouter
    
    def register(self, app: FastAPI, prefix: str = "") -> None:
        """Register this endpoint with a FastAPI application."""
        ...
    
    def get_router(self) -> APIRouter:
        """Get the router for this endpoint."""
        ...