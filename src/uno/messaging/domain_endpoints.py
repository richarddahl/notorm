# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from uno.messaging.dtos import (
    MessageCreateDto, MessageUpdateDto, MessageViewDto, 
    MessageListDto, MessageFilterParams
)
from uno.messaging.domain_services import MessageDomainServiceProtocol
from uno.messaging.schemas import MessageSchemaManager
from uno.dependencies.service import inject_dependency
from uno.dependencies.database import get_db_session, get_repository
from uno.messaging.domain_repositories import MessageRepositoryProtocol
from uno.core.errors import EntityNotFoundError


def register_message_endpoints(
    router: APIRouter,
    prefix: str = "/messages",
    tags: List[str] = None,
    dependencies: List[Any] = None
) -> Dict[str, Any]:
    """Register message API endpoints."""
    if tags is None:
        tags = ["messages"]
    
    if dependencies is None:
        dependencies = []
    
    # Schema manager for entity-DTO conversions
    schema_manager = MessageSchemaManager()
    
    # Dependency for message service
    def get_message_service() -> MessageDomainServiceProtocol:
        """Get message domain service."""
        session = get_db_session()
        repository = get_repository(MessageRepositoryProtocol, session)
        return inject_dependency(MessageDomainServiceProtocol, repository=repository)
    
    # GET /messages
    @router.get(
        f"{prefix}",
        response_model=MessageListDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get messages",
        description="Get messages for the current user"
    )
    async def get_messages(
        user_id: str = Query(..., description="User ID to get messages for"),
        only_unread: bool = Query(False, description="Only show unread messages"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageListDto:
        """Get messages for a user."""
        try:
            filter_params = MessageFilterParams(
                only_unread=only_unread,
                page=page,
                page_size=page_size
            )
            
            messages = await service.get_messages_for_user(
                user_id=user_id,
                only_unread=filter_params.only_unread,
                page=filter_params.page,
                page_size=filter_params.page_size
            )
            
            # TODO: Get actual count
            total = len(messages)
            if len(messages) == page_size:
                total = page * page_size + 1  # At least one more page
            
            return schema_manager.entities_to_list_dto(
                entities=messages,
                total=total,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get messages: {str(e)}"
            )
    
    # GET /messages/drafts
    @router.get(
        f"{prefix}/drafts",
        response_model=MessageListDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get draft messages",
        description="Get draft messages for the current user"
    )
    async def get_draft_messages(
        user_id: str = Query(..., description="User ID to get draft messages for"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageListDto:
        """Get draft messages for a user."""
        try:
            messages = await service.get_draft_messages(
                user_id=user_id,
                page=page,
                page_size=page_size
            )
            
            # TODO: Get actual count
            total = len(messages)
            if len(messages) == page_size:
                total = page * page_size + 1  # At least one more page
            
            return schema_manager.entities_to_list_dto(
                entities=messages,
                total=total,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get draft messages: {str(e)}"
            )
    
    # GET /messages/sent
    @router.get(
        f"{prefix}/sent",
        response_model=MessageListDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get sent messages",
        description="Get sent messages for the current user"
    )
    async def get_sent_messages(
        user_id: str = Query(..., description="User ID to get sent messages for"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageListDto:
        """Get sent messages for a user."""
        try:
            messages = await service.get_sent_messages(
                user_id=user_id,
                page=page,
                page_size=page_size
            )
            
            # TODO: Get actual count
            total = len(messages)
            if len(messages) == page_size:
                total = page * page_size + 1  # At least one more page
            
            return schema_manager.entities_to_list_dto(
                entities=messages,
                total=total,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get sent messages: {str(e)}"
            )
    
    # GET /messages/thread/{message_id}
    @router.get(
        f"{prefix}/thread/{{message_id}}",
        response_model=MessageListDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get message thread",
        description="Get all messages in a thread"
    )
    async def get_message_thread(
        message_id: str = Path(..., description="Parent message ID"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageListDto:
        """Get all messages in a thread."""
        try:
            messages = await service.get_message_thread(
                parent_message_id=message_id,
                page=page,
                page_size=page_size
            )
            
            # TODO: Get actual count
            total = len(messages)
            if len(messages) == page_size:
                total = page * page_size + 1  # At least one more page
            
            return schema_manager.entities_to_list_dto(
                entities=messages,
                total=total,
                page=page,
                page_size=page_size
            )
        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get message thread: {str(e)}"
            )
    
    # GET /messages/{message_id}
    @router.get(
        f"{prefix}/{{message_id}}",
        response_model=MessageViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Get message",
        description="Get a message by ID"
    )
    async def get_message(
        message_id: str = Path(..., description="Message ID"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageViewDto:
        """Get a message by ID."""
        try:
            message = await service.get_message(message_id)
            return schema_manager.entity_to_dto(message)
        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get message: {str(e)}"
            )
    
    # POST /messages
    @router.post(
        f"{prefix}",
        response_model=MessageViewDto,
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        dependencies=dependencies,
        summary="Create message",
        description="Create a new message"
    )
    async def create_message(
        message_data: MessageCreateDto,
        sender_id: str = Query(..., description="ID of the sender"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageViewDto:
        """Create a new message."""
        try:
            params = schema_manager.create_dto_to_params(message_data, sender_id)
            message = await service.create_message(**params)
            return schema_manager.entity_to_dto(message)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create message: {str(e)}"
            )
    
    # PUT /messages/{message_id}
    @router.put(
        f"{prefix}/{{message_id}}",
        response_model=MessageViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Update message",
        description="Update an existing message"
    )
    async def update_message(
        message_id: str = Path(..., description="Message ID"),
        message_data: MessageUpdateDto = None,
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageViewDto:
        """Update an existing message."""
        try:
            if message_data is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message data is required"
                )
            
            params = schema_manager.update_dto_to_params(message_data)
            message = await service.update_message(message_id=message_id, **params)
            return schema_manager.entity_to_dto(message)
        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update message: {str(e)}"
            )
    
    # POST /messages/{message_id}/send
    @router.post(
        f"{prefix}/{{message_id}}/send",
        response_model=MessageViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Send message",
        description="Send a draft message"
    )
    async def send_message(
        message_id: str = Path(..., description="Message ID"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageViewDto:
        """Send a draft message."""
        try:
            message = await service.send_message(message_id)
            return schema_manager.entity_to_dto(message)
        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send message: {str(e)}"
            )
    
    # POST /messages/{message_id}/read
    @router.post(
        f"{prefix}/{{message_id}}/read",
        response_model=MessageViewDto,
        tags=tags,
        dependencies=dependencies,
        summary="Mark as read",
        description="Mark a message as read by a user"
    )
    async def mark_as_read(
        message_id: str = Path(..., description="Message ID"),
        user_id: str = Query(..., description="User ID"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> MessageViewDto:
        """Mark a message as read by a user."""
        try:
            message = await service.mark_as_read(message_id, user_id)
            return schema_manager.entity_to_dto(message)
        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to mark message as read: {str(e)}"
            )
    
    # DELETE /messages/{message_id}
    @router.delete(
        f"{prefix}/{{message_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        dependencies=dependencies,
        summary="Delete message",
        description="Delete a message"
    )
    async def delete_message(
        message_id: str = Path(..., description="Message ID"),
        service: MessageDomainServiceProtocol = Depends(get_message_service)
    ) -> None:
        """Delete a message."""
        try:
            await service.delete_message(message_id)
        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete message: {str(e)}"
            )
    
    endpoints = {
        "get_messages": get_messages,
        "get_draft_messages": get_draft_messages,
        "get_sent_messages": get_sent_messages,
        "get_message_thread": get_message_thread,
        "get_message": get_message,
        "create_message": create_message,
        "update_message": update_message,
        "send_message": send_message,
        "mark_as_read": mark_as_read,
        "delete_message": delete_message
    }
    
    return endpoints