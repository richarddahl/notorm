"""
FastAPI integration for CQRS and Read Model.

This module provides integration between FastAPI and the CQRS/Read Model system,
enabling automatic endpoint creation, WebSocket support, and authentication.
"""

import inspect
import logging
import asyncio
import json
from datetime import datetime, UTC
from typing import (
    Any, Dict, Generic, List, Optional, Set, Tuple, Type, TypeVar, Union, Callable,
    cast, get_type_hints
)
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from uno.core.cqrs import Command, Query, Mediator, CommandResult, QueryResult
from uno.domain.cqrs_read_model import (
    ReadModelQueryHandlerConfig, ReadModelCommandHandlerConfig,
    ReadModelIntegrationConfig
)
from uno.domain.events import DomainEvent, EventDispatcher
from uno.read_model.query_service import PaginatedResult

# Type variables
T = TypeVar('T')
TCommand = TypeVar('TCommand', bound=Command)
TQuery = TypeVar('TQuery', bound=Query)


class EndpointConfig(BaseModel):
    """
    Configuration for CQRS endpoints.
    
    Attributes:
        path_prefix: Prefix for endpoint paths
        include_docs: Whether to include documentation
        include_tags: Tags for OpenAPI documentation
        enable_audit: Whether to enable auditing
        enable_validation: Whether to enable additional validation
        enable_metrics: Whether to enable metrics
    """
    
    path_prefix: str = ""
    include_docs: bool = True
    include_tags: List[str] = Field(default_factory=list)
    enable_audit: bool = False
    enable_validation: bool = True
    enable_metrics: bool = True


class CommandEndpointConfig(EndpointConfig):
    """
    Configuration for command endpoints.
    
    Attributes:
        default_status_code: Default status code for successful responses
        require_authentication: Whether to require authentication
        authentication_scopes: Required scopes for authentication
    """
    
    default_status_code: int = 202  # Accepted
    require_authentication: bool = True
    authentication_scopes: List[str] = Field(default_factory=list)


class QueryEndpointConfig(EndpointConfig):
    """
    Configuration for query endpoints.
    
    Attributes:
        default_status_code: Default status code for successful responses
        require_authentication: Whether to require authentication
        authentication_scopes: Required scopes for authentication
        enable_caching: Whether to enable response caching
        cache_ttl: TTL for cached responses
    """
    
    default_status_code: int = 200  # OK
    require_authentication: bool = False
    authentication_scopes: List[str] = Field(default_factory=list)
    enable_caching: bool = True
    cache_ttl: int = 60  # seconds


class WebSocketConfig(BaseModel):
    """
    Configuration for WebSocket endpoints.
    
    Attributes:
        path: Path for the WebSocket endpoint
        require_authentication: Whether to require authentication
        authentication_scopes: Required scopes for authentication
        ping_interval: Interval for sending ping messages
        max_clients: Maximum number of connected clients
    """
    
    path: str
    require_authentication: bool = True
    authentication_scopes: List[str] = Field(default_factory=list)
    ping_interval: int = 30  # seconds
    max_clients: int = 100


class RequestMetrics(BaseModel):
    """
    Metrics for endpoint requests.
    
    Attributes:
        endpoint: The endpoint path
        method: The HTTP method
        status_code: The response status code
        duration_ms: Request duration in milliseconds
        timestamp: When the request occurred
        user_id: ID of the authenticated user
        command_id: ID of the command (for command endpoints)
        query_id: ID of the query (for query endpoints)
    """
    
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: Optional[str] = None
    command_id: Optional[str] = None
    query_id: Optional[str] = None


class AuditLog(BaseModel):
    """
    Audit log entry for command endpoints.
    
    Attributes:
        command_id: ID of the command
        command_type: Type of the command
        user_id: ID of the authenticated user
        timestamp: When the command was executed
        client_ip: IP address of the client
        request_path: Path of the request
        request_headers: Headers of the request
        request_body: Body of the request
        response_status: Status code of the response
    """
    
    command_id: str
    command_type: str
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    client_ip: Optional[str] = None
    request_path: str
    request_headers: Dict[str, str] = Field(default_factory=dict)
    request_body: Any = None
    response_status: int


class WebSocketMessage(BaseModel):
    """
    Message for WebSocket communication.
    
    Attributes:
        type: Type of message (event, query, command, error, etc.)
        payload: Message payload
        correlation_id: Correlation ID for request-response patterns
        timestamp: When the message was created
    """
    
    type: str
    payload: Any
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CQRSEndpointFactory:
    """
    Factory for creating CQRS-based FastAPI endpoints.
    
    This factory creates REST endpoints for commands and queries,
    automatically mapping them to the CQRS system.
    """
    
    def __init__(
        self,
        mediator: Mediator,
        oauth2_scheme: Optional[OAuth2PasswordBearer] = None,
        get_current_user: Optional[Callable] = None,
        metrics_handler: Optional[Callable[[RequestMetrics], None]] = None,
        audit_handler: Optional[Callable[[AuditLog], None]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the endpoint factory.
        
        Args:
            mediator: The CQRS mediator for executing commands and queries
            oauth2_scheme: Optional OAuth2 scheme for authentication
            get_current_user: Optional function to get the current user
            metrics_handler: Optional handler for request metrics
            audit_handler: Optional handler for audit logs
            logger: Optional logger for diagnostics
        """
        self.mediator = mediator
        self.oauth2_scheme = oauth2_scheme
        self.get_current_user = get_current_user
        self.metrics_handler = metrics_handler
        self.audit_handler = audit_handler
        self.logger = logger or logging.getLogger(__name__)
    
    def create_command_endpoint(
        self,
        router: APIRouter,
        command_type: Type[Command],
        path: str,
        response_model: Optional[Type] = None,
        config: Optional[CommandEndpointConfig] = None,
        **kwargs
    ):
        """
        Create an endpoint that executes a command.
        
        Args:
            router: The FastAPI router to add the endpoint to
            command_type: The type of command to execute
            path: The endpoint path
            response_model: The response model for the endpoint
            config: Optional endpoint configuration
            **kwargs: Additional arguments for the endpoint decorator
        """
        # Create default config if not provided
        config = config or CommandEndpointConfig()
        
        # Determine full path
        full_path = f"{config.path_prefix}{path}"
        
        # Build endpoint arguments
        endpoint_args = {
            "response_model": response_model,
            "status_code": config.default_status_code,
        }
        
        # Add tags if specified
        if config.include_tags:
            endpoint_args["tags"] = config.include_tags
        
        # Add documentation if enabled
        if config.include_docs:
            # Extract command attributes for documentation
            command_fields = command_type.__annotations__ if hasattr(command_type, "__annotations__") else {}
            command_docs = inspect.getdoc(command_type) or ""
            
            endpoint_args["summary"] = f"Execute {command_type.__name__}"
            endpoint_args["description"] = command_docs
        
        # Add authentication if required
        dependencies = []
        if config.require_authentication and self.oauth2_scheme:
            if config.authentication_scopes:
                # Require specific scopes
                dependencies.append(Depends(self._get_auth_dependency(config.authentication_scopes)))
            else:
                # Just require authentication
                dependencies.append(Depends(self.oauth2_scheme))
        
        if dependencies:
            endpoint_args["dependencies"] = dependencies
        
        # Add any additional arguments
        endpoint_args.update(kwargs)
        
        # Create the endpoint
        @router.post(full_path, **endpoint_args)
        async def endpoint(
            command_data: command_type,
            user: Optional[Any] = Depends(self.get_current_user) if self.get_current_user else None
        ):
            # Start timing
            start_time = datetime.now(UTC)
            
            try:
                # Set command ID if not already set
                if not getattr(command_data, "command_id", None):
                    command_data.command_id = str(uuid4())
                
                # Attach user ID if authenticated
                if user and hasattr(user, "id") and hasattr(command_data, "user_id"):
                    command_data.user_id = user.id
                
                # Perform additional validation if enabled
                if config.enable_validation:
                    self._validate_command(command_data)
                
                # Execute the command
                result = await self.mediator.execute_command(command_data)
                
                # Record metrics
                if config.enable_metrics and self.metrics_handler:
                    end_time = datetime.now(UTC)
                    duration_ms = (end_time - start_time).total_seconds() * 1000
                    
                    metrics = RequestMetrics(
                        endpoint=full_path,
                        method="POST",
                        status_code=config.default_status_code,
                        duration_ms=duration_ms,
                        user_id=user.id if user and hasattr(user, "id") else None,
                        command_id=command_data.command_id
                    )
                    
                    self.metrics_handler(metrics)
                
                # Create audit log if enabled
                if config.enable_audit and self.audit_handler:
                    # Get client IP and headers from request context if available
                    client_ip = None
                    request_headers = {}
                    request_path = full_path
                    
                    # Create audit log entry
                    audit_log = AuditLog(
                        command_id=command_data.command_id,
                        command_type=command_type.__name__,
                        user_id=user.id if user and hasattr(user, "id") else None,
                        client_ip=client_ip,
                        request_path=request_path,
                        request_headers=request_headers,
                        request_body=command_data.model_dump(),
                        response_status=config.default_status_code
                    )
                    
                    self.audit_handler(audit_log)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error executing command {command_type.__name__}: {str(e)}")
                
                # Get appropriate status code and error message
                status_code, error_message = self._handle_command_error(e)
                
                # Record metrics for error
                if config.enable_metrics and self.metrics_handler:
                    end_time = datetime.now(UTC)
                    duration_ms = (end_time - start_time).total_seconds() * 1000
                    
                    metrics = RequestMetrics(
                        endpoint=full_path,
                        method="POST",
                        status_code=status_code,
                        duration_ms=duration_ms,
                        user_id=user.id if user and hasattr(user, "id") else None,
                        command_id=getattr(command_data, "command_id", None)
                    )
                    
                    self.metrics_handler(metrics)
                
                # Create audit log for error if enabled
                if config.enable_audit and self.audit_handler:
                    # Get client IP and headers from request context if available
                    client_ip = None
                    request_headers = {}
                    request_path = full_path
                    
                    # Create audit log entry
                    audit_log = AuditLog(
                        command_id=getattr(command_data, "command_id", str(uuid4())),
                        command_type=command_type.__name__,
                        user_id=user.id if user and hasattr(user, "id") else None,
                        client_ip=client_ip,
                        request_path=request_path,
                        request_headers=request_headers,
                        request_body=command_data.model_dump(),
                        response_status=status_code
                    )
                    
                    self.audit_handler(audit_log)
                
                # Raise HTTP exception
                raise HTTPException(status_code=status_code, detail=error_message)
    
    def create_query_endpoint(
        self,
        router: APIRouter,
        query_type: Type[Query],
        path: str,
        response_model: Optional[Type] = None,
        config: Optional[QueryEndpointConfig] = None,
        **kwargs
    ):
        """
        Create an endpoint that executes a query.
        
        Args:
            router: The FastAPI router to add the endpoint to
            query_type: The type of query to execute
            path: The endpoint path
            response_model: The response model for the endpoint
            config: Optional endpoint configuration
            **kwargs: Additional arguments for the endpoint decorator
        """
        # Create default config if not provided
        config = config or QueryEndpointConfig()
        
        # Determine full path
        full_path = f"{config.path_prefix}{path}"
        
        # Build endpoint arguments
        endpoint_args = {
            "response_model": response_model,
            "status_code": config.default_status_code,
        }
        
        # Add tags if specified
        if config.include_tags:
            endpoint_args["tags"] = config.include_tags
        
        # Add documentation if enabled
        if config.include_docs:
            # Extract query attributes for documentation
            query_fields = query_type.__annotations__ if hasattr(query_type, "__annotations__") else {}
            query_docs = inspect.getdoc(query_type) or ""
            
            endpoint_args["summary"] = f"Execute {query_type.__name__}"
            endpoint_args["description"] = query_docs
        
        # Add caching headers if enabled
        response_headers = {}
        if config.enable_caching:
            response_headers["Cache-Control"] = f"max-age={config.cache_ttl}"
        
        if response_headers:
            endpoint_args["response_headers"] = response_headers
        
        # Add authentication if required
        dependencies = []
        if config.require_authentication and self.oauth2_scheme:
            if config.authentication_scopes:
                # Require specific scopes
                dependencies.append(Depends(self._get_auth_dependency(config.authentication_scopes)))
            else:
                # Just require authentication
                dependencies.append(Depends(self.oauth2_scheme))
        
        if dependencies:
            endpoint_args["dependencies"] = dependencies
        
        # Add any additional arguments
        endpoint_args.update(kwargs)
        
        # Determine if query should use GET or POST based on complexity
        query_field_count = len(query_type.__annotations__.keys()) if hasattr(query_type, "__annotations__") else 0
        use_get = query_field_count <= 5
        
        if use_get:
            # For simpler queries, use GET with query parameters
            @router.get(full_path, **endpoint_args)
            async def get_endpoint(
                query_params: query_type = Depends(),
                user: Optional[Any] = Depends(self.get_current_user) if self.get_current_user else None
            ):
                # Start timing
                start_time = datetime.now(UTC)
                
                try:
                    # Set query ID if not already set
                    if not getattr(query_params, "query_id", None):
                        query_params.query_id = str(uuid4())
                    
                    # Attach user ID if authenticated
                    if user and hasattr(user, "id") and hasattr(query_params, "user_id"):
                        query_params.user_id = user.id
                    
                    # Perform additional validation if enabled
                    if config.enable_validation:
                        self._validate_query(query_params)
                    
                    # Execute the query
                    result = await self.mediator.execute_query(query_params)
                    
                    # Record metrics
                    if config.enable_metrics and self.metrics_handler:
                        end_time = datetime.now(UTC)
                        duration_ms = (end_time - start_time).total_seconds() * 1000
                        
                        metrics = RequestMetrics(
                            endpoint=full_path,
                            method="GET",
                            status_code=config.default_status_code,
                            duration_ms=duration_ms,
                            user_id=user.id if user and hasattr(user, "id") else None,
                            query_id=query_params.query_id
                        )
                        
                        self.metrics_handler(metrics)
                    
                    return result
                    
                except Exception as e:
                    self.logger.error(f"Error executing query {query_type.__name__}: {str(e)}")
                    
                    # Get appropriate status code and error message
                    status_code, error_message = self._handle_query_error(e)
                    
                    # Record metrics for error
                    if config.enable_metrics and self.metrics_handler:
                        end_time = datetime.now(UTC)
                        duration_ms = (end_time - start_time).total_seconds() * 1000
                        
                        metrics = RequestMetrics(
                            endpoint=full_path,
                            method="GET",
                            status_code=status_code,
                            duration_ms=duration_ms,
                            user_id=user.id if user and hasattr(user, "id") else None,
                            query_id=getattr(query_params, "query_id", None)
                        )
                        
                        self.metrics_handler(metrics)
                    
                    # Raise HTTP exception
                    raise HTTPException(status_code=status_code, detail=error_message)
        else:
            # For more complex queries, use POST with request body
            @router.post(full_path, **endpoint_args)
            async def post_endpoint(
                query_data: query_type,
                user: Optional[Any] = Depends(self.get_current_user) if self.get_current_user else None
            ):
                # Start timing
                start_time = datetime.now(UTC)
                
                try:
                    # Set query ID if not already set
                    if not getattr(query_data, "query_id", None):
                        query_data.query_id = str(uuid4())
                    
                    # Attach user ID if authenticated
                    if user and hasattr(user, "id") and hasattr(query_data, "user_id"):
                        query_data.user_id = user.id
                    
                    # Perform additional validation if enabled
                    if config.enable_validation:
                        self._validate_query(query_data)
                    
                    # Execute the query
                    result = await self.mediator.execute_query(query_data)
                    
                    # Record metrics
                    if config.enable_metrics and self.metrics_handler:
                        end_time = datetime.now(UTC)
                        duration_ms = (end_time - start_time).total_seconds() * 1000
                        
                        metrics = RequestMetrics(
                            endpoint=full_path,
                            method="POST",
                            status_code=config.default_status_code,
                            duration_ms=duration_ms,
                            user_id=user.id if user and hasattr(user, "id") else None,
                            query_id=query_data.query_id
                        )
                        
                        self.metrics_handler(metrics)
                    
                    return result
                    
                except Exception as e:
                    self.logger.error(f"Error executing query {query_type.__name__}: {str(e)}")
                    
                    # Get appropriate status code and error message
                    status_code, error_message = self._handle_query_error(e)
                    
                    # Record metrics for error
                    if config.enable_metrics and self.metrics_handler:
                        end_time = datetime.now(UTC)
                        duration_ms = (end_time - start_time).total_seconds() * 1000
                        
                        metrics = RequestMetrics(
                            endpoint=full_path,
                            method="POST",
                            status_code=status_code,
                            duration_ms=duration_ms,
                            user_id=user.id if user and hasattr(user, "id") else None,
                            query_id=getattr(query_data, "query_id", None)
                        )
                        
                        self.metrics_handler(metrics)
                    
                    # Raise HTTP exception
                    raise HTTPException(status_code=status_code, detail=error_message)
    
    def create_websocket_endpoint(
        self,
        router: APIRouter,
        event_dispatcher: EventDispatcher,
        config: WebSocketConfig
    ):
        """
        Create a WebSocket endpoint for real-time updates.
        
        Args:
            router: The FastAPI router to add the endpoint to
            event_dispatcher: Event dispatcher for subscribing to events
            config: WebSocket configuration
        """
        active_connections: Set[WebSocket] = set()
        
        @router.websocket(config.path)
        async def websocket_endpoint(websocket: WebSocket):
            # Authenticate if required
            if config.require_authentication:
                # Get authentication token from query string
                token = websocket.query_params.get("token")
                if not token:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return
                
                # Verify token (simplified example)
                user = None
                try:
                    # Use the token to get the user
                    if self.get_current_user:
                        user = await self.get_current_user(token)
                    
                    if not user:
                        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                        return
                    
                    # Check scopes if required
                    if config.authentication_scopes:
                        # This is a simplified example
                        # Actual scope checking would depend on your auth system
                        has_required_scopes = True
                        if not has_required_scopes:
                            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                            return
                    
                except Exception:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return
            
            # Check max clients
            if len(active_connections) >= config.max_clients:
                await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
                return
            
            # Accept connection
            await websocket.accept()
            active_connections.add(websocket)
            
            try:
                # Create a queue for events
                event_queue = asyncio.Queue()
                
                # Create event handler
                async def event_handler(event: DomainEvent):
                    # Create WebSocket message
                    message = WebSocketMessage(
                        type="event",
                        payload={
                            "type": event.__class__.__name__,
                            "data": event.model_dump()
                        }
                    )
                    
                    # Add to queue
                    await event_queue.put(message)
                
                # Register event handler with dispatcher
                event_dispatcher.subscribe("*", event_handler)
                
                # Create ping task
                async def send_pings():
                    while True:
                        try:
                            await asyncio.sleep(config.ping_interval)
                            await websocket.send_text('{"type":"ping"}')
                        except:
                            break
                
                ping_task = asyncio.create_task(send_pings())
                
                # Process incoming messages and send events
                while True:
                    # Check for incoming messages (non-blocking)
                    message_task = asyncio.create_task(websocket.receive_text())
                    event_task = asyncio.create_task(event_queue.get())
                    
                    # Wait for either a message or an event
                    done, pending = await asyncio.wait(
                        [message_task, event_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                    
                    # Handle message if received
                    if message_task in done:
                        try:
                            # Parse message
                            text = message_task.result()
                            if not text:
                                continue
                            
                            data = json.loads(text)
                            
                            # Handle different message types
                            if data.get("type") == "pong":
                                # Ping-pong response
                                pass
                            elif data.get("type") == "query":
                                # Handle query
                                payload = data.get("payload", {})
                                correlation_id = data.get("correlation_id")
                                
                                # Execute query
                                if payload.get("query_type") and payload.get("data"):
                                    # This is simplified - in reality you would
                                    # use a query registry to find the query type
                                    # and instantiate it from the data
                                    try:
                                        # Execute query (simplified example)
                                        result = {"result": "query_result"}
                                        
                                        # Send response
                                        response = WebSocketMessage(
                                            type="query_result",
                                            payload=result,
                                            correlation_id=correlation_id
                                        )
                                        
                                        await websocket.send_json(response.model_dump())
                                        
                                    except Exception as e:
                                        # Send error response
                                        error = WebSocketMessage(
                                            type="error",
                                            payload={"message": str(e)},
                                            correlation_id=correlation_id
                                        )
                                        
                                        await websocket.send_json(error.model_dump())
                            
                            elif data.get("type") == "command":
                                # Handle command
                                # This would be similar to query handling
                                pass
                            
                        except json.JSONDecodeError:
                            # Invalid JSON
                            continue
                        except Exception as e:
                            # General error
                            self.logger.error(f"WebSocket error: {str(e)}")
                            continue
                    
                    # Handle event if received
                    if event_task in done:
                        try:
                            # Get event message
                            event_message = event_task.result()
                            
                            # Send to client
                            await websocket.send_json(event_message.model_dump())
                            
                        except Exception as e:
                            # Error sending event
                            self.logger.error(f"Error sending event: {str(e)}")
                
            except WebSocketDisconnect:
                # Client disconnected
                pass
            except Exception as e:
                # Other error
                self.logger.error(f"WebSocket error: {str(e)}")
            finally:
                # Clean up
                active_connections.remove(websocket)
                event_dispatcher.unsubscribe("*", event_handler)
                
                # Cancel ping task
                ping_task.cancel()
                
                # Close if not already closed
                try:
                    await websocket.close()
                except:
                    pass
    
    def _get_auth_dependency(self, scopes: List[str]) -> Callable:
        """
        Get a dependency function for checking authentication scopes.
        
        Args:
            scopes: Required scopes
            
        Returns:
            A dependency function
        """
        async def check_scopes(token: str = Depends(self.oauth2_scheme)):
            # This is a simplified example
            # Actual scope checking would depend on your auth system
            return token
        
        return check_scopes
    
    def _validate_command(self, command: Command) -> None:
        """
        Perform additional validation on a command.
        
        Args:
            command: The command to validate
        """
        # Simplified example - actual validation would be more complex
        pass
    
    def _validate_query(self, query: Query) -> None:
        """
        Perform additional validation on a query.
        
        Args:
            query: The query to validate
        """
        # Simplified example - actual validation would be more complex
        pass
    
    def _handle_command_error(self, error: Exception) -> Tuple[int, str]:
        """
        Handle a command error.
        
        Args:
            error: The exception
            
        Returns:
            Tuple of (status_code, error_message)
        """
        # Handle common error types with appropriate status codes
        # This is a simplified example - actual error handling would be more comprehensive
        return 500, str(error)
    
    def _handle_query_error(self, error: Exception) -> Tuple[int, str]:
        """
        Handle a query error.
        
        Args:
            error: The exception
            
        Returns:
            Tuple of (status_code, error_message)
        """
        # Handle common error types with appropriate status codes
        # This is a simplified example - actual error handling would be more comprehensive
        return 500, str(error)


def create_crud_endpoints(
    router: APIRouter,
    mediator: Mediator,
    entity_name: str,
    get_command_type: Type[Command],
    list_command_type: Type[Command],
    create_command_type: Type[Command],
    update_command_type: Type[Command],
    delete_command_type: Type[Command],
    entity_model: Type,
    entity_list_model: Type,
    path_prefix: str = "",
    tags: List[str] = None,
    auth_required: bool = True,
    oauth2_scheme: Optional[OAuth2PasswordBearer] = None,
    get_current_user: Optional[Callable] = None
) -> None:
    """
    Create CRUD endpoints for an entity.
    
    Args:
        router: The FastAPI router to add the endpoints to
        mediator: The CQRS mediator
        entity_name: Name of the entity (for path and documentation)
        get_command_type: Command type for getting an entity
        list_command_type: Command type for listing entities
        create_command_type: Command type for creating an entity
        update_command_type: Command type for updating an entity
        delete_command_type: Command type for deleting an entity
        entity_model: Model for entity responses
        entity_list_model: Model for entity list responses
        path_prefix: Prefix for endpoint paths
        tags: Tags for OpenAPI documentation
        auth_required: Whether authentication is required
        oauth2_scheme: OAuth2 scheme for authentication
        get_current_user: Function to get the current user
    """
    # Create endpoint factory
    factory = CQRSEndpointFactory(
        mediator=mediator,
        oauth2_scheme=oauth2_scheme,
        get_current_user=get_current_user
    )
    
    # Base path
    base_path = f"{path_prefix}/{entity_name.lower()}"
    
    # Create configurations
    command_config = CommandEndpointConfig(
        require_authentication=auth_required,
        include_tags=tags or [entity_name]
    )
    
    query_config = QueryEndpointConfig(
        require_authentication=auth_required,
        include_tags=tags or [entity_name],
        enable_caching=True
    )
    
    # Create endpoints
    
    # GET /entity - List entities
    factory.create_query_endpoint(
        router=router,
        query_type=list_command_type,
        path=base_path,
        response_model=entity_list_model,
        config=query_config
    )
    
    # GET /entity/{id} - Get entity by ID
    factory.create_query_endpoint(
        router=router,
        query_type=get_command_type,
        path=f"{base_path}/{{id}}",
        response_model=entity_model,
        config=query_config
    )
    
    # POST /entity - Create entity
    factory.create_command_endpoint(
        router=router,
        command_type=create_command_type,
        path=base_path,
        response_model=entity_model,
        config=command_config,
        status_code=201  # Created
    )
    
    # PUT /entity/{id} - Update entity
    factory.create_command_endpoint(
        router=router,
        command_type=update_command_type,
        path=f"{base_path}/{{id}}",
        response_model=entity_model,
        config=command_config
    )
    
    # DELETE /entity/{id} - Delete entity
    factory.create_command_endpoint(
        router=router,
        command_type=delete_command_type,
        path=f"{base_path}/{{id}}",
        response_model=None,
        config=command_config,
        status_code=204  # No Content
    )