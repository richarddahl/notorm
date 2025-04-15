"""
Custom endpoint behaviors example.

This module demonstrates how to create custom endpoint behaviors by extending
the UnoEndpoint framework. It shows how to create custom endpoints with
specialized behavior, advanced response formats, and integration with external services.
"""

import enum
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Type, Callable, Set, Annotated
from decimal import Decimal

from fastapi import FastAPI, status, APIRouter, HTTPException, Response, Request, Body, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator, ConfigDict, create_model, computed_field

from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.api.endpoint import UnoEndpoint, UnoRouter, CreateEndpoint, ViewEndpoint, ListEndpoint, UpdateEndpoint, DeleteEndpoint
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.schema import UnoSchemaConfig
from uno.core.errors import ValidationContext, UnoError, ErrorCode


# Set up logging
logger = logging.getLogger(__name__)


# ===== EXAMPLE MODEL =====

class ProductModel(UnoModel):
    """Example product model for demonstrating custom endpoints."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    sku: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, unique=True)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


# ===== CUSTOM ROUTER TYPES =====

class HealthCheckRouter(UnoRouter):
    """Router for system health checks."""
    
    path_suffix: str = "/health"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Get health status for {self.model.display_name_plural} service"
    
    @property
    def description(self) -> str:
        return f"""
            Get health status for the {self.model.display_name_plural} service.
            This endpoint checks database connectivity, model availability,
            and overall system health.
            
            Returns a health status object with:
            - status: 'healthy', 'degraded', or 'unhealthy'
            - details: Specific health information for various components
            - timestamp: When the health check was performed
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any, List
        
        class HealthStatus(BaseModel):
            status: str
            details: Dict[str, Any]
            timestamp: datetime
        
        async def endpoint(self) -> HealthStatus:
            details = {}
            overall_status = "healthy"
            
            # Check database connectivity
            try:
                # Try to query the database
                count = await self.model.count()
                details["database"] = {
                    "status": "healthy",
                    "count": count,
                    "message": "Database connection successful"
                }
            except Exception as e:
                details["database"] = {
                    "status": "unhealthy",
                    "message": f"Database connection failed: {str(e)}"
                }
                overall_status = "unhealthy"
            
            # Check caching service (example)
            try:
                # Simulate checking a cache service
                cache_status = "healthy"
                details["cache"] = {
                    "status": cache_status,
                    "message": "Cache service is operational"
                }
            except Exception as e:
                details["cache"] = {
                    "status": "degraded",
                    "message": f"Cache service issues: {str(e)}"
                }
                if overall_status == "healthy":
                    overall_status = "degraded"
            
            # Check external services (example)
            try:
                # Simulate checking an external service
                external_status = "healthy"
                details["external_services"] = {
                    "status": external_status,
                    "message": "External services are operational"
                }
            except Exception as e:
                details["external_services"] = {
                    "status": "degraded",
                    "message": f"External service issues: {str(e)}"
                }
                if overall_status == "healthy":
                    overall_status = "degraded"
            
            # Return health status
            return HealthStatus(
                status=overall_status,
                details=details,
                timestamp=datetime.now()
            )
        
        endpoint.__annotations__["return"] = HealthStatus
        setattr(self.__class__, "endpoint", endpoint)


class AuditLogRouter(UnoRouter):
    """Router for retrieving audit logs for a resource."""
    
    path_suffix: str = "/audit"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Get audit logs for {self.model.display_name_plural}"
    
    @property
    def description(self) -> str:
        return f"""
            Get audit logs tracking changes to {self.model.display_name_plural}.
            This endpoint provides a complete history of create, update, and delete
            operations performed on these resources.
            
            Supports the following query parameters:
            - `resource_id`: Filter logs for a specific resource by ID
            - `action`: Filter by action type (create, update, delete)
            - `start_date`: Filter logs after this date (ISO format)
            - `end_date`: Filter logs before this date (ISO format)
            - `user_id`: Filter logs by the user who performed the action
            - `page`: Page number for pagination
            - `page_size`: Number of logs per page
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any, List, Optional
        from fastapi import Query as QueryParam
        from datetime import datetime
        from pydantic import BaseModel
        
        class AuditLogEntry(BaseModel):
            id: str
            resource_id: str
            resource_type: str
            action: str
            changes: Dict[str, Any]
            user_id: str
            timestamp: datetime
            ip_address: Optional[str] = None
            user_agent: Optional[str] = None
            
        class AuditLogResponse(BaseModel):
            items: List[AuditLogEntry]
            total: int
            page: int
            page_size: int
            total_pages: int
        
        async def endpoint(
            self,
            resource_id: Optional[str] = QueryParam(None, description="Filter logs for a specific resource ID"),
            action: Optional[str] = QueryParam(None, description="Filter by action type (create, update, delete)"),
            start_date: Optional[str] = QueryParam(None, description="Filter logs after this date (ISO format)"),
            end_date: Optional[str] = QueryParam(None, description="Filter logs before this date (ISO format)"),
            user_id: Optional[str] = QueryParam(None, description="Filter logs by the user who performed the action"),
            page: int = QueryParam(1, description="Page number", ge=1),
            page_size: int = QueryParam(20, description="Items per page", ge=1, le=100)
        ) -> AuditLogResponse:
            # In a real implementation, this would query an audit log database
            # For this example, we'll simulate some audit logs
            
            # Generate sample audit logs
            resource_type = self.model.__name__
            sample_logs = []
            
            # Create some sample logs with different actions and timestamps
            actions = ["create", "update", "delete"]
            user_ids = ["user1", "user2", "user3", "admin"]
            
            for i in range(1, 50):
                # Generate a resource ID
                res_id = f"{resource_type.lower()}-{i % 10 + 1}"
                
                # Skip if filtering by resource_id and this doesn't match
                if resource_id and res_id != resource_id:
                    continue
                
                # Generate an action
                log_action = actions[i % len(actions)]
                
                # Skip if filtering by action and this doesn't match
                if action and log_action != action:
                    continue
                
                # Generate user ID
                log_user_id = user_ids[i % len(user_ids)]
                
                # Skip if filtering by user_id and this doesn't match
                if user_id and log_user_id != user_id:
                    continue
                
                # Generate timestamp (last 30 days)
                days_ago = i % 30
                log_timestamp = datetime.now() - timedelta(days=days_ago)
                
                # Skip if filtering by date range
                if start_date:
                    start = datetime.fromisoformat(start_date)
                    if log_timestamp < start:
                        continue
                
                if end_date:
                    end = datetime.fromisoformat(end_date)
                    if log_timestamp > end:
                        continue
                
                # Generate changes based on action
                changes = {}
                if log_action == "create":
                    changes = {
                        "name": f"New {resource_type} {i}",
                        "price": f"{i * 10}.99",
                        "created_at": log_timestamp.isoformat()
                    }
                elif log_action == "update":
                    changes = {
                        "name": {
                            "old": f"Old {resource_type} {i}",
                            "new": f"Updated {resource_type} {i}"
                        },
                        "price": {
                            "old": f"{i * 8}.99",
                            "new": f"{i * 10}.99"
                        },
                        "updated_at": log_timestamp.isoformat()
                    }
                elif log_action == "delete":
                    changes = {
                        "deleted": True,
                        "deleted_at": log_timestamp.isoformat()
                    }
                
                # Create log entry
                log_entry = AuditLogEntry(
                    id=f"log-{i}",
                    resource_id=res_id,
                    resource_type=resource_type,
                    action=log_action,
                    changes=changes,
                    user_id=log_user_id,
                    timestamp=log_timestamp,
                    ip_address=f"192.168.1.{i % 255}",
                    user_agent=f"Mozilla/5.0 (Example/{i})"
                )
                
                sample_logs.append(log_entry)
            
            # Sort logs by timestamp (newest first)
            sample_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            total_logs = len(sample_logs)
            total_pages = (total_logs + page_size - 1) // page_size
            offset = (page - 1) * page_size
            paginated_logs = sample_logs[offset:offset + page_size]
            
            # Return the paginated response
            return AuditLogResponse(
                items=paginated_logs,
                total=total_logs,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        
        endpoint.__annotations__["return"] = AuditLogResponse
        setattr(self.__class__, "endpoint", endpoint)


class ExportRouter(UnoRouter):
    """Router for exporting resources in various formats."""
    
    path_suffix: str = "/export"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Export {self.model.display_name_plural} in various formats"
    
    @property
    def description(self) -> str:
        return f"""
            Export {self.model.display_name_plural} in various formats like JSON, CSV, or Excel.
            
            Supports the following query parameters:
            - `format`: Export format (json, csv, or excel)
            - `filter`: JSON filter criteria to select which resources to export
            - `fields`: Comma-separated list of fields to include in the export
            - `sort_by`: Field to sort by
            - `sort_direction`: Sort direction (asc or desc)
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any, List, Optional
        from fastapi import Query as QueryParam
        from fastapi.responses import StreamingResponse
        import json
        import csv
        import io
        from datetime import datetime
        
        async def endpoint(
            self,
            format: str = QueryParam("json", description="Export format (json, csv, or excel)"),
            filter: Optional[str] = QueryParam(None, description="JSON filter criteria"),
            fields: Optional[str] = QueryParam(None, description="Comma-separated list of fields to include"),
            sort_by: Optional[str] = QueryParam(None, description="Field to sort by"),
            sort_direction: str = QueryParam("asc", description="Sort direction (asc or desc)")
        ):
            # Parse filter if provided
            filters = {}
            if filter:
                try:
                    filters = json.loads(filter)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid filter JSON format"
                    )
            
            # Get all resources with filters
            resources = await self.model.filter(filters=filters)
            
            # Parse fields for inclusion
            included_fields = None
            if fields:
                included_fields = fields.split(",")
            
            # Sort the resources if requested
            if sort_by:
                reverse = sort_direction.lower() == "desc"
                resources.sort(key=lambda x: getattr(x, sort_by, None), reverse=reverse)
            
            # Prepare data with field selection
            data = []
            for resource in resources:
                if hasattr(resource, "dict"):
                    item = resource.dict()
                else:
                    # Fallback to __dict__ if dict() is not available
                    item = resource.__dict__.copy()
                    # Remove SQLAlchemy-specific fields
                    item.pop("_sa_instance_state", None)
                
                # Apply field selection if specified
                if included_fields:
                    item = {k: v for k, v in item.items() if k in included_fields}
                
                data.append(item)
            
            # Export in the requested format
            if format.lower() == "json":
                # For JSON, we can return directly or stream for large datasets
                if len(data) > 1000:  # Threshold for streaming
                    async def stream_json():
                        # Stream as array
                        yield "["
                        for i, item in enumerate(data):
                            item_json = json.dumps(item)
                            if i > 0:
                                yield ","
                            yield item_json
                        yield "]"
                    
                    return StreamingResponse(
                        stream_json(),
                        media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename={self.model.__name__.lower()}_export.json"}
                    )
                else:
                    # Small dataset, return directly
                    return Response(
                        content=json.dumps(data),
                        media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename={self.model.__name__.lower()}_export.json"}
                    )
            
            elif format.lower() == "csv":
                # Create CSV in memory
                output = io.StringIO()
                writer = None
                
                # If we have data, write the header and rows
                if data:
                    # Get column names from the first item
                    columns = list(data[0].keys())
                    
                    # Create writer and write header
                    writer = csv.DictWriter(output, fieldnames=columns)
                    writer.writeheader()
                    
                    # Write rows
                    for item in data:
                        # Convert all values to strings
                        row = {k: str(v) if v is not None else "" for k, v in item.items()}
                        writer.writerow(row)
                
                # Get the CSV content
                csv_content = output.getvalue()
                output.close()
                
                # Return as streaming response if large
                if len(data) > 1000:
                    # For streaming, we need to create a generator
                    async def stream_csv():
                        # Yield in chunks
                        chunk_size = 1024 * 1024  # 1MB chunks
                        for i in range(0, len(csv_content), chunk_size):
                            yield csv_content[i:i + chunk_size]
                    
                    return StreamingResponse(
                        stream_csv(),
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={self.model.__name__.lower()}_export.csv"}
                    )
                else:
                    # Small dataset, return directly
                    return Response(
                        content=csv_content,
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={self.model.__name__.lower()}_export.csv"}
                    )
            
            elif format.lower() == "excel":
                # In a real implementation, you'd use a library like openpyxl or xlsxwriter
                # For this example, we'll just return an error indicating this is not implemented
                raise HTTPException(
                    status_code=501,  # Not Implemented
                    detail="Excel export is not implemented in this example"
                )
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported format: {format}. Supported formats: json, csv, excel"
                )
        
        # No specific return type annotation as it returns different response types
        setattr(self.__class__, "endpoint", endpoint)


class BulkImportRouter(UnoRouter):
    """Router for importing resources in bulk."""
    
    path_suffix: str = "/import"
    method: str = "POST"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Import {self.model.display_name_plural} in bulk"
    
    @property
    def description(self) -> str:
        return f"""
            Import multiple {self.model.display_name_plural} in a single operation.
            
            The request body should contain:
            - `items`: Array of resources to import
            - `options`: Import options (e.g., update_existing, skip_validation)
            
            Returns a response with import results including:
            - `success_count`: Number of successfully imported items
            - `error_count`: Number of items that failed to import
            - `results`: Detailed results for each item
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any, List, Optional, Union
        from pydantic import BaseModel, Field
        
        class ImportOptions(BaseModel):
            update_existing: bool = Field(False, description="Update items if they already exist")
            skip_validation: bool = Field(False, description="Skip validation checks (not recommended)")
            batch_size: int = Field(100, description="Number of items to process in each batch")
        
        class BulkImportRequest(BaseModel):
            items: List[Dict[str, Any]] = Field(..., description="Array of resources to import")
            options: Optional[ImportOptions] = Field(None, description="Import options")
        
        class ImportItemResult(BaseModel):
            success: bool
            index: int
            id: Optional[str] = None
            data: Optional[Dict[str, Any]] = None
            error: Optional[str] = None
        
        class BulkImportResponse(BaseModel):
            success_count: int
            error_count: int
            results: List[ImportItemResult]
            processing_time: float
        
        async def endpoint(self, request: BulkImportRequest) -> BulkImportResponse:
            # Start timing
            start_time = datetime.now()
            
            # Get items and options
            items = request.items
            options = request.options or ImportOptions()
            
            # Initialize results
            results = []
            success_count = 0
            error_count = 0
            
            # Process in batches
            for i in range(0, len(items), options.batch_size):
                batch = items[i:i + options.batch_size]
                
                # Process each item in the batch
                for index, item_data in enumerate(batch):
                    absolute_index = i + index
                    try:
                        # Check if item already exists (if it has an ID)
                        existing_item = None
                        if "id" in item_data and options.update_existing:
                            existing_item = await self.model.get(item_data["id"])
                        
                        if existing_item:
                            # Update existing item
                            for key, value in item_data.items():
                                if key != "id":
                                    setattr(existing_item, key, value)
                            
                            item = existing_item
                        else:
                            # Create new item
                            item = self.model(**item_data)
                        
                        # Validate unless skipped
                        if not options.skip_validation:
                            validation_context = item.validate("edit_schema")
                            if validation_context.has_errors():
                                raise ValueError(f"Validation failed: {validation_context.errors}")
                        
                        # Save the item
                        await item.save()
                        
                        # Record success
                        results.append(ImportItemResult(
                            success=True,
                            index=absolute_index,
                            id=item.id,
                            data=item.dict()
                        ))
                        success_count += 1
                    
                    except Exception as e:
                        # Record error
                        results.append(ImportItemResult(
                            success=False,
                            index=absolute_index,
                            error=str(e)
                        ))
                        error_count += 1
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Return results
            return BulkImportResponse(
                success_count=success_count,
                error_count=error_count,
                results=results,
                processing_time=processing_time
            )
        
        endpoint.__annotations__["return"] = BulkImportResponse
        setattr(self.__class__, "endpoint", endpoint)


class WebhookRegistrationRouter(UnoRouter):
    """Router for managing webhooks for resource events."""
    
    path_suffix: str = "/webhooks"
    method: str = "POST"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Register webhooks for {self.model.display_name_plural} events"
    
    @property
    def description(self) -> str:
        return f"""
            Register webhooks to be notified when {self.model.display_name_plural} change.
            
            You can subscribe to:
            - `created`: When a new resource is created
            - `updated`: When a resource is updated
            - `deleted`: When a resource is deleted
            - `all`: All of the above events
            
            The webhook URL will receive a POST request with details about the event.
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any, List, Optional, Set
        from pydantic import BaseModel, Field, AnyHttpUrl
        from enum import Enum
        
        class WebhookEventType(str, Enum):
            CREATED = "created"
            UPDATED = "updated"
            DELETED = "deleted"
            ALL = "all"
        
        class WebhookRegistrationRequest(BaseModel):
            url: AnyHttpUrl = Field(..., description="The URL to send webhook events to")
            events: List[WebhookEventType] = Field(..., description="Events to subscribe to")
            secret: Optional[str] = Field(None, description="Secret for signing webhook payloads")
            description: Optional[str] = Field(None, description="Description of this webhook")
        
        class WebhookRegistrationResponse(BaseModel):
            id: str
            url: str
            events: List[str]
            created_at: datetime
            resource_type: str
        
        async def endpoint(self, request: WebhookRegistrationRequest) -> WebhookRegistrationResponse:
            # In a real implementation, this would store the webhook in a database
            # For this example, we'll just simulate creating the webhook
            
            # Generate a webhook ID
            import uuid
            webhook_id = str(uuid.uuid4())
            
            # Normalize events (if "all" is included, it supersedes others)
            events = [event.value for event in request.events]
            if WebhookEventType.ALL.value in events:
                events = [WebhookEventType.ALL.value]
            
            # Store the webhook (simulated)
            # In a real implementation, you would store:
            # - webhook ID
            # - URL
            # - Events
            # - Secret (hashed)
            # - Resource type
            # - Created at timestamp
            
            # Return the registration confirmation
            return WebhookRegistrationResponse(
                id=webhook_id,
                url=str(request.url),
                events=events,
                created_at=datetime.now(),
                resource_type=self.model.__name__
            )
        
        endpoint.__annotations__["return"] = WebhookRegistrationResponse
        setattr(self.__class__, "endpoint", endpoint)


class CustomActionRouter(UnoRouter):
    """Router for performing custom actions on resources."""
    
    path_suffix: str = "/{id}/actions/{action}"
    method: str = "POST"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Perform custom actions on {self.model.display_name_plural}"
    
    @property
    def description(self) -> str:
        return f"""
            Perform custom actions on specific {self.model.display_name} resources.
            
            Available actions depend on the resource type, but may include:
            - `publish`: Publish a resource
            - `archive`: Archive a resource
            - `clone`: Create a copy of a resource
            - `process`: Process a resource through a workflow
            
            The request body can include action-specific parameters.
        """
    
    def endpoint_factory(self):
        from typing import Dict, Any, Optional
        from fastapi import Path as PathParam
        
        async def endpoint(
            self,
            id: str = PathParam(..., description="Resource ID"),
            action: str = PathParam(..., description="Action to perform"),
            body: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            # Get the resource
            resource = await self.model.get(id)
            if not resource:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resource not found: {id}"
                )
            
            # Initialize response
            response = {
                "id": id,
                "action": action,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Process based on the action
            if action == "publish":
                # Publish the resource
                if hasattr(resource, "is_published"):
                    resource.is_published = True
                    await resource.save()
                    response["message"] = "Resource published successfully"
                else:
                    response["success"] = False
                    response["message"] = "Resource does not support publishing"
            
            elif action == "archive":
                # Archive the resource
                if hasattr(resource, "is_archived"):
                    resource.is_archived = True
                    await resource.save()
                    response["message"] = "Resource archived successfully"
                else:
                    response["success"] = False
                    response["message"] = "Resource does not support archiving"
            
            elif action == "clone":
                # Clone the resource
                new_resource = self.model()
                
                # Copy fields from the original resource
                for field in resource.__dict__:
                    if not field.startswith("_") and field != "id" and field != "created_at" and field != "updated_at":
                        setattr(new_resource, field, getattr(resource, field))
                
                # Add a suffix to indicate it's a clone
                if hasattr(new_resource, "name"):
                    new_resource.name = f"{new_resource.name} (Clone)"
                
                # Save the new resource
                await new_resource.save()
                
                # Add to response
                response["message"] = "Resource cloned successfully"
                response["clone_id"] = new_resource.id
            
            elif action == "process":
                # Process the resource through a workflow
                # In a real implementation, this would integrate with a workflow engine
                workflow_name = body.get("workflow") if body else None
                
                if not workflow_name:
                    response["success"] = False
                    response["message"] = "Workflow name is required"
                else:
                    # Simulate processing
                    await asyncio.sleep(0.5)  # Simulate some processing time
                    
                    response["message"] = f"Resource processed through {workflow_name} workflow"
                    response["workflow"] = workflow_name
                    response["process_id"] = f"proc-{id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            else:
                # Unknown action
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown action: {action}"
                )
            
            return response
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


# ===== CUSTOM ENDPOINTS =====

class HealthCheckEndpoint(UnoEndpoint):
    """Endpoint for health checks."""
    
    router: UnoRouter = HealthCheckRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class AuditLogEndpoint(UnoEndpoint):
    """Endpoint for retrieving audit logs."""
    
    router: UnoRouter = AuditLogRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class ExportEndpoint(UnoEndpoint):
    """Endpoint for exporting resources."""
    
    router: UnoRouter = ExportRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class BulkImportEndpoint(UnoEndpoint):
    """Endpoint for importing resources in bulk."""
    
    router: UnoRouter = BulkImportRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class WebhookRegistrationEndpoint(UnoEndpoint):
    """Endpoint for registering webhooks."""
    
    router: UnoRouter = WebhookRegistrationRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class CustomActionEndpoint(UnoEndpoint):
    """Endpoint for performing custom actions on resources."""
    
    router: UnoRouter = CustomActionRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


# ===== EXAMPLE USAGE =====

def create_app():
    """Create a FastAPI application with custom endpoints."""
    # Create the app
    app = FastAPI(title="Custom Endpoints Example", description="Example API with custom endpoint behaviors")
    
    # Create the endpoint factory
    factory = UnoEndpointFactory()
    
    # Register custom endpoint types
    factory.register_endpoint_type("HealthCheck", HealthCheckEndpoint)
    factory.register_endpoint_type("AuditLog", AuditLogEndpoint)
    factory.register_endpoint_type("Export", ExportEndpoint)
    factory.register_endpoint_type("BulkImport", BulkImportEndpoint)
    factory.register_endpoint_type("WebhookRegistration", WebhookRegistrationEndpoint)
    factory.register_endpoint_type("CustomAction", CustomActionEndpoint)
    
    # Create standard endpoints plus our custom types
    endpoints = factory.create_endpoints(
        app=app,
        model_obj=ProductModel,
        endpoints=[
            # Standard endpoints
            "Create", "View", "List", "Update", "Delete",
            # Custom endpoints
            "HealthCheck", "AuditLog", "Export", "BulkImport", 
            "WebhookRegistration", "CustomAction"
        ],
        endpoint_tags=["Products"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    return app


# If this script is run directly
if __name__ == "__main__":
    import uvicorn
    
    # Create the app
    app = create_app()
    
    # Run the server
    uvicorn.run(app, host="127.0.0.1", port=8000)