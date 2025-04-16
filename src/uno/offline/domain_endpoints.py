"""
Domain endpoints for the Offline module.

This module defines FastAPI endpoints for the Offline module.
"""

from typing import Dict, List, Optional, Any, Union, Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request, Body
from pydantic import BaseModel, Field, validator

from uno.core.result import Result
from uno.dependencies.service import inject_dependency
from uno.offline.domain_services import (
    DocumentService,
    CollectionService,
    TransactionService,
    SyncService,
    NetworkService,
    OfflineService
)
from uno.offline.domain_provider import (
    get_document_service,
    get_collection_service,
    get_transaction_service,
    get_sync_service,
    get_network_service,
    get_offline_service
)
from uno.offline.entities import (
    StoreId,
    CollectionId,
    DocumentId,
    TransactionId,
    SyncId,
    ConflictId,
    StorageType,
    RelationshipType,
    ChangeType,
    SyncDirection,
    ConflictResolutionStrategy,
    NetworkStatus
)


# DTOs
class DocumentDTO(BaseModel):
    """DTO for documents."""
    
    id: str = Field(..., description="Document ID")
    collection_id: str = Field(..., description="Collection ID")
    data: Dict[str, Any] = Field(..., description="Document data")
    version: int = Field(..., description="Document version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted: bool = Field(False, description="Whether the document is deleted")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class CreateDocumentDTO(BaseModel):
    """DTO for creating documents."""
    
    data: Dict[str, Any] = Field(..., description="Document data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")


class UpdateDocumentDTO(BaseModel):
    """DTO for updating documents."""
    
    data: Dict[str, Any] = Field(..., description="Updated document data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated document metadata")


class CollectionSchemaDTO(BaseModel):
    """DTO for collection schemas."""
    
    id: str = Field(..., description="Collection ID")
    name: str = Field(..., description="Collection name")
    store_id: str = Field(..., description="Store ID")
    key_path: Union[str, List[str]] = Field(..., description="Path to the primary key")
    auto_increment: bool = Field(False, description="Whether keys auto-increment")
    indexes: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Indexes")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Relationships")
    validators: List[Dict[str, Any]] = Field(default_factory=list, description="Validators")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="Default values")
    max_items: Optional[int] = Field(None, description="Maximum number of items")
    versioned: bool = Field(False, description="Whether documents are versioned")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Collection metadata")


class CreateCollectionDTO(BaseModel):
    """DTO for creating collections."""
    
    name: str = Field(..., description="Collection name")
    key_path: Union[str, List[str]] = Field(..., description="Path to the primary key")
    auto_increment: bool = Field(False, description="Whether keys auto-increment")
    indexes: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Indexes")
    relationships: Optional[List[Dict[str, Any]]] = Field(None, description="Relationships")
    validators: Optional[List[Dict[str, Any]]] = Field(None, description="Validators")
    default_values: Optional[Dict[str, Any]] = Field(None, description="Default values")
    max_items: Optional[int] = Field(None, description="Maximum number of items")
    versioned: bool = Field(False, description="Whether documents are versioned")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Collection metadata")


class TransactionDTO(BaseModel):
    """DTO for transactions."""
    
    id: str = Field(..., description="Transaction ID")
    store_id: str = Field(..., description="Store ID")
    operations: List[Dict[str, Any]] = Field(..., description="Transaction operations")
    start_time: datetime = Field(..., description="Start timestamp")
    commit_time: Optional[datetime] = Field(None, description="Commit timestamp")
    rollback_time: Optional[datetime] = Field(None, description="Rollback timestamp")
    status: str = Field(..., description="Transaction status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Transaction metadata")


class AddOperationDTO(BaseModel):
    """DTO for adding operations to transactions."""
    
    operation_type: str = Field(..., description="Operation type")
    collection_id: str = Field(..., description="Collection ID")
    document_id: Optional[str] = Field(None, description="Document ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Operation data")


class SyncEventDTO(BaseModel):
    """DTO for sync events."""
    
    id: str = Field(..., description="Sync ID")
    store_id: str = Field(..., description="Store ID")
    direction: str = Field(..., description="Sync direction")
    collections: List[str] = Field(..., description="Collections to sync")
    status: str = Field(..., description="Sync status")
    start_time: Optional[datetime] = Field(None, description="Start timestamp")
    end_time: Optional[datetime] = Field(None, description="End timestamp")
    changes_pushed: int = Field(0, description="Number of changes pushed")
    changes_pulled: int = Field(0, description="Number of changes pulled")
    conflicts: List[str] = Field(default_factory=list, description="Conflict IDs")
    error: Optional[str] = Field(None, description="Error message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Sync metadata")


class SyncRequestDTO(BaseModel):
    """DTO for sync requests."""
    
    collections: List[str] = Field(..., description="Collections to sync")
    direction: str = Field("bidirectional", description="Sync direction")


class ConflictDTO(BaseModel):
    """DTO for conflicts."""
    
    id: str = Field(..., description="Conflict ID")
    document_id: str = Field(..., description="Document ID")
    collection_id: str = Field(..., description="Collection ID")
    client_data: Dict[str, Any] = Field(..., description="Client data")
    server_data: Dict[str, Any] = Field(..., description="Server data")
    client_version: int = Field(..., description="Client version")
    server_version: int = Field(..., description="Server version")
    resolved: bool = Field(False, description="Whether the conflict is resolved")
    resolution_strategy: Optional[str] = Field(None, description="Resolution strategy")
    resolved_data: Optional[Dict[str, Any]] = Field(None, description="Resolved data")
    sync_id: str = Field(..., description="Sync ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Conflict metadata")


class ResolveConflictDTO(BaseModel):
    """DTO for resolving conflicts."""
    
    strategy: str = Field(..., description="Resolution strategy")
    resolved_data: Optional[Dict[str, Any]] = Field(None, description="Resolved data")


class NetworkStateDTO(BaseModel):
    """DTO for network state."""
    
    status: str = Field(..., description="Network status")
    last_online: Optional[datetime] = Field(None, description="Last online timestamp")
    last_offline: Optional[datetime] = Field(None, description="Last offline timestamp")
    check_interval: int = Field(..., description="Check interval")
    last_check: datetime = Field(..., description="Last check timestamp")


class UpdateNetworkStatusDTO(BaseModel):
    """DTO for updating network status."""
    
    status: str = Field(..., description="Network status")


# Endpoints
def create_offline_router() -> APIRouter:
    """
    Create FastAPI router for offline endpoints.
    
    Returns:
        FastAPI router
    """
    router = APIRouter(
        prefix="/api/offline",
        tags=["offline"],
        responses={401: {"description": "Unauthorized"}},
    )
    
    # Document endpoints
    @router.post(
        "/collections/{collection_id}/documents",
        response_model=DocumentDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create document",
        description="Create a new document in a collection"
    )
    async def create_document(
        collection_id: str,
        request: CreateDocumentDTO,
        document_service: DocumentService = Depends(get_document_service)
    ) -> DocumentDTO:
        """Create a new document in a collection."""
        try:
            # Create document
            result = await document_service.create_document(
                CollectionId(collection_id),
                request.data
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            document = result.value
            
            # Convert to DTO
            return DocumentDTO(
                id=document.id.value,
                collection_id=document.collection_id.value,
                data=document.data,
                version=document.version,
                created_at=document.created_at,
                updated_at=document.updated_at,
                deleted=document.deleted,
                deleted_at=document.deleted_at,
                metadata=document.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/collections/{collection_id}/documents/{document_id}",
        response_model=DocumentDTO,
        summary="Get document",
        description="Get a document by ID"
    )
    async def get_document(
        collection_id: str,
        document_id: str,
        document_service: DocumentService = Depends(get_document_service)
    ) -> DocumentDTO:
        """Get a document by ID."""
        try:
            # Get document
            result = await document_service.get_document(
                CollectionId(collection_id),
                DocumentId(document_id)
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            document = result.value
            
            # Convert to DTO
            return DocumentDTO(
                id=document.id.value,
                collection_id=document.collection_id.value,
                data=document.data,
                version=document.version,
                created_at=document.created_at,
                updated_at=document.updated_at,
                deleted=document.deleted,
                deleted_at=document.deleted_at,
                metadata=document.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.put(
        "/collections/{collection_id}/documents/{document_id}",
        response_model=DocumentDTO,
        summary="Update document",
        description="Update a document"
    )
    async def update_document(
        collection_id: str,
        document_id: str,
        request: UpdateDocumentDTO,
        document_service: DocumentService = Depends(get_document_service)
    ) -> DocumentDTO:
        """Update a document."""
        try:
            # Update document
            result = await document_service.update_document(
                CollectionId(collection_id),
                DocumentId(document_id),
                request.data
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            document = result.value
            
            # Convert to DTO
            return DocumentDTO(
                id=document.id.value,
                collection_id=document.collection_id.value,
                data=document.data,
                version=document.version,
                created_at=document.created_at,
                updated_at=document.updated_at,
                deleted=document.deleted,
                deleted_at=document.deleted_at,
                metadata=document.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.delete(
        "/collections/{collection_id}/documents/{document_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete document",
        description="Delete a document"
    )
    async def delete_document(
        collection_id: str,
        document_id: str,
        document_service: DocumentService = Depends(get_document_service)
    ) -> None:
        """Delete a document."""
        try:
            # Delete document
            result = await document_service.delete_document(
                CollectionId(collection_id),
                DocumentId(document_id)
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/collections/{collection_id}/documents",
        response_model=List[DocumentDTO],
        summary="List documents",
        description="List documents in a collection"
    )
    async def list_documents(
        collection_id: str,
        limit: int = 100,
        offset: int = 0,
        document_service: DocumentService = Depends(get_document_service)
    ) -> List[DocumentDTO]:
        """List documents in a collection."""
        try:
            # List documents
            result = await document_service.list_documents(
                CollectionId(collection_id),
                limit,
                offset
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            documents = result.value
            
            # Convert to DTOs
            return [
                DocumentDTO(
                    id=document.id.value,
                    collection_id=document.collection_id.value,
                    data=document.data,
                    version=document.version,
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                    deleted=document.deleted,
                    deleted_at=document.deleted_at,
                    metadata=document.metadata
                )
                for document in documents
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Collection endpoints
    @router.post(
        "/stores/{store_id}/collections",
        response_model=CollectionSchemaDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create collection",
        description="Create a new collection in a store"
    )
    async def create_collection(
        store_id: str,
        request: CreateCollectionDTO,
        collection_service: CollectionService = Depends(get_collection_service)
    ) -> CollectionSchemaDTO:
        """Create a new collection in a store."""
        try:
            # Create collection
            result = await collection_service.create_collection(
                StoreId(store_id),
                request.name,
                request.key_path,
                auto_increment=request.auto_increment,
                indexes=request.indexes or {},
                relationships=request.relationships or [],
                validators=request.validators or [],
                default_values=request.default_values or {},
                max_items=request.max_items,
                versioned=request.versioned,
                metadata=request.metadata or {}
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            schema = result.value
            
            # Convert to DTO
            return CollectionSchemaDTO(
                id=schema.id.value,
                name=schema.name,
                store_id=schema.store_id.value,
                key_path=schema.key_path,
                auto_increment=schema.auto_increment,
                indexes=schema.indexes,
                relationships=schema.relationships,
                validators=schema.validators,
                default_values=schema.default_values,
                max_items=schema.max_items,
                versioned=schema.versioned,
                metadata=schema.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/collections/{collection_id}",
        response_model=CollectionSchemaDTO,
        summary="Get collection",
        description="Get a collection by ID"
    )
    async def get_collection(
        collection_id: str,
        collection_service: CollectionService = Depends(get_collection_service)
    ) -> CollectionSchemaDTO:
        """Get a collection by ID."""
        try:
            # Get collection
            result = await collection_service.get_collection(CollectionId(collection_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            schema = result.value
            
            # Convert to DTO
            return CollectionSchemaDTO(
                id=schema.id.value,
                name=schema.name,
                store_id=schema.store_id.value,
                key_path=schema.key_path,
                auto_increment=schema.auto_increment,
                indexes=schema.indexes,
                relationships=schema.relationships,
                validators=schema.validators,
                default_values=schema.default_values,
                max_items=schema.max_items,
                versioned=schema.versioned,
                metadata=schema.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/stores/{store_id}/collections",
        response_model=List[CollectionSchemaDTO],
        summary="List collections",
        description="List collections in a store"
    )
    async def list_collections(
        store_id: str,
        collection_service: CollectionService = Depends(get_collection_service)
    ) -> List[CollectionSchemaDTO]:
        """List collections in a store."""
        try:
            # List collections
            result = await collection_service.list_collections(StoreId(store_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            schemas = result.value
            
            # Convert to DTOs
            return [
                CollectionSchemaDTO(
                    id=schema.id.value,
                    name=schema.name,
                    store_id=schema.store_id.value,
                    key_path=schema.key_path,
                    auto_increment=schema.auto_increment,
                    indexes=schema.indexes,
                    relationships=schema.relationships,
                    validators=schema.validators,
                    default_values=schema.default_values,
                    max_items=schema.max_items,
                    versioned=schema.versioned,
                    metadata=schema.metadata
                )
                for schema in schemas
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Transaction endpoints
    @router.post(
        "/stores/{store_id}/transactions",
        response_model=TransactionDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Begin transaction",
        description="Begin a new transaction"
    )
    async def begin_transaction(
        store_id: str,
        transaction_service: TransactionService = Depends(get_transaction_service)
    ) -> TransactionDTO:
        """Begin a new transaction."""
        try:
            # Begin transaction
            result = await transaction_service.begin_transaction(StoreId(store_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            transaction = result.value
            
            # Convert to DTO
            return TransactionDTO(
                id=transaction.id.value,
                store_id=transaction.store_id.value,
                operations=transaction.operations,
                start_time=transaction.start_time,
                commit_time=transaction.commit_time,
                rollback_time=transaction.rollback_time,
                status=transaction.status,
                metadata=transaction.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post(
        "/transactions/{transaction_id}/commit",
        response_model=TransactionDTO,
        summary="Commit transaction",
        description="Commit a transaction"
    )
    async def commit_transaction(
        transaction_id: str,
        transaction_service: TransactionService = Depends(get_transaction_service)
    ) -> TransactionDTO:
        """Commit a transaction."""
        try:
            # Commit transaction
            result = await transaction_service.commit_transaction(TransactionId(transaction_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            transaction = result.value
            
            # Convert to DTO
            return TransactionDTO(
                id=transaction.id.value,
                store_id=transaction.store_id.value,
                operations=transaction.operations,
                start_time=transaction.start_time,
                commit_time=transaction.commit_time,
                rollback_time=transaction.rollback_time,
                status=transaction.status,
                metadata=transaction.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post(
        "/transactions/{transaction_id}/rollback",
        response_model=TransactionDTO,
        summary="Rollback transaction",
        description="Rollback a transaction"
    )
    async def rollback_transaction(
        transaction_id: str,
        transaction_service: TransactionService = Depends(get_transaction_service)
    ) -> TransactionDTO:
        """Rollback a transaction."""
        try:
            # Rollback transaction
            result = await transaction_service.rollback_transaction(TransactionId(transaction_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            transaction = result.value
            
            # Convert to DTO
            return TransactionDTO(
                id=transaction.id.value,
                store_id=transaction.store_id.value,
                operations=transaction.operations,
                start_time=transaction.start_time,
                commit_time=transaction.commit_time,
                rollback_time=transaction.rollback_time,
                status=transaction.status,
                metadata=transaction.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post(
        "/transactions/{transaction_id}/operations",
        response_model=TransactionDTO,
        summary="Add operation",
        description="Add an operation to a transaction"
    )
    async def add_operation(
        transaction_id: str,
        request: AddOperationDTO,
        transaction_service: TransactionService = Depends(get_transaction_service)
    ) -> TransactionDTO:
        """Add an operation to a transaction."""
        try:
            # Add operation
            result = await transaction_service.add_operation(
                TransactionId(transaction_id),
                request.operation_type,
                CollectionId(request.collection_id),
                DocumentId(request.document_id) if request.document_id else None,
                request.data
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            transaction = result.value
            
            # Convert to DTO
            return TransactionDTO(
                id=transaction.id.value,
                store_id=transaction.store_id.value,
                operations=transaction.operations,
                start_time=transaction.start_time,
                commit_time=transaction.commit_time,
                rollback_time=transaction.rollback_time,
                status=transaction.status,
                metadata=transaction.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Sync endpoints
    @router.post(
        "/stores/{store_id}/sync",
        response_model=SyncEventDTO,
        summary="Synchronize",
        description="Synchronize data with the server"
    )
    async def synchronize(
        store_id: str,
        request: SyncRequestDTO,
        sync_service: SyncService = Depends(get_sync_service)
    ) -> SyncEventDTO:
        """Synchronize data with the server."""
        try:
            # Convert collections to CollectionId objects
            collections = [CollectionId(cid) for cid in request.collections]
            
            # Convert direction
            direction = SyncDirection(request.direction)
            
            # Synchronize
            result = await sync_service.synchronize(
                StoreId(store_id),
                collections,
                direction
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            sync_event = result.value
            
            # Convert to DTO
            return SyncEventDTO(
                id=sync_event.id.value,
                store_id=sync_event.store_id.value,
                direction=sync_event.direction.value,
                collections=[c.value for c in sync_event.collections],
                status=sync_event.status.value,
                start_time=sync_event.start_time,
                end_time=sync_event.end_time,
                changes_pushed=sync_event.changes_pushed,
                changes_pulled=sync_event.changes_pulled,
                conflicts=[c.value for c in sync_event.conflicts],
                error=sync_event.error,
                metadata=sync_event.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/conflicts",
        response_model=List[ConflictDTO],
        summary="List unresolved conflicts",
        description="List unresolved conflicts"
    )
    async def list_unresolved_conflicts(
        sync_id: Optional[str] = None,
        sync_service: SyncService = Depends(get_sync_service)
    ) -> List[ConflictDTO]:
        """List unresolved conflicts."""
        try:
            # List conflicts
            result = await sync_service.list_unresolved_conflicts(
                SyncId(sync_id) if sync_id else None
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            conflicts = result.value
            
            # Convert to DTOs
            return [
                ConflictDTO(
                    id=conflict.id.value,
                    document_id=conflict.document_id.value,
                    collection_id=conflict.collection_id.value,
                    client_data=conflict.client_data,
                    server_data=conflict.server_data,
                    client_version=conflict.client_version,
                    server_version=conflict.server_version,
                    resolved=conflict.resolved,
                    resolution_strategy=conflict.resolution_strategy.value if conflict.resolution_strategy else None,
                    resolved_data=conflict.resolved_data,
                    sync_id=conflict.sync_id.value,
                    created_at=conflict.created_at,
                    resolved_at=conflict.resolved_at,
                    metadata=conflict.metadata
                )
                for conflict in conflicts
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post(
        "/conflicts/{conflict_id}/resolve",
        response_model=ConflictDTO,
        summary="Resolve conflict",
        description="Resolve a conflict"
    )
    async def resolve_conflict(
        conflict_id: str,
        request: ResolveConflictDTO,
        sync_service: SyncService = Depends(get_sync_service)
    ) -> ConflictDTO:
        """Resolve a conflict."""
        try:
            # Convert strategy
            strategy = ConflictResolutionStrategy(request.strategy)
            
            # Resolve conflict
            result = await sync_service.resolve_conflict(
                ConflictId(conflict_id),
                strategy,
                request.resolved_data
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            conflict = result.value
            
            # Convert to DTO
            return ConflictDTO(
                id=conflict.id.value,
                document_id=conflict.document_id.value,
                collection_id=conflict.collection_id.value,
                client_data=conflict.client_data,
                server_data=conflict.server_data,
                client_version=conflict.client_version,
                server_version=conflict.server_version,
                resolved=conflict.resolved,
                resolution_strategy=conflict.resolution_strategy.value if conflict.resolution_strategy else None,
                resolved_data=conflict.resolved_data,
                sync_id=conflict.sync_id.value,
                created_at=conflict.created_at,
                resolved_at=conflict.resolved_at,
                metadata=conflict.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Network endpoints
    @router.get(
        "/network",
        response_model=NetworkStateDTO,
        summary="Get network state",
        description="Get the current network state"
    )
    async def get_network_state(
        network_service: NetworkService = Depends(get_network_service)
    ) -> NetworkStateDTO:
        """Get the current network state."""
        try:
            # Get network state
            result = await network_service.get_network_state()
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            state = result.value
            
            # Convert to DTO
            return NetworkStateDTO(
                status=state.status.value,
                last_online=state.last_online,
                last_offline=state.last_offline,
                check_interval=state.check_interval,
                last_check=state.last_check
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post(
        "/network",
        response_model=NetworkStateDTO,
        summary="Update network status",
        description="Update the network status"
    )
    async def update_network_status(
        request: UpdateNetworkStatusDTO,
        network_service: NetworkService = Depends(get_network_service)
    ) -> NetworkStateDTO:
        """Update the network status."""
        try:
            # Convert status
            status = NetworkStatus(request.status)
            
            # Update status
            result = await network_service.update_network_status(status)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            state = result.value
            
            # Convert to DTO
            return NetworkStateDTO(
                status=state.status.value,
                last_online=state.last_online,
                last_offline=state.last_offline,
                check_interval=state.check_interval,
                last_check=state.last_check
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    return router