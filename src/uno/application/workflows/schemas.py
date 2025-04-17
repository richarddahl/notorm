"""Schema managers for converting between workflow domain entities and DTOs."""

from typing import Dict, List, Optional, Any, Union, Type

from pydantic import BaseModel

from uno.workflows.entities import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
    User,
)

from uno.workflows.dtos import (
    # Workflow Definition DTOs
    WorkflowDefBaseDto,
    WorkflowDefCreateDto,
    WorkflowDefUpdateDto,
    WorkflowDefViewDto,
    WorkflowDefFilterParams,
    
    # Workflow Trigger DTOs
    WorkflowTriggerBaseDto,
    WorkflowTriggerCreateDto,
    WorkflowTriggerUpdateDto,
    WorkflowTriggerViewDto,
    WorkflowTriggerFilterParams,
    
    # Workflow Condition DTOs
    WorkflowConditionBaseDto,
    WorkflowConditionCreateDto,
    WorkflowConditionUpdateDto,
    WorkflowConditionViewDto,
    WorkflowConditionFilterParams,
    
    # Workflow Action DTOs
    WorkflowActionBaseDto,
    WorkflowActionCreateDto,
    WorkflowActionUpdateDto,
    WorkflowActionViewDto,
    WorkflowActionFilterParams,
    
    # Workflow Recipient DTOs
    WorkflowRecipientBaseDto,
    WorkflowRecipientCreateDto,
    WorkflowRecipientUpdateDto,
    WorkflowRecipientViewDto,
    WorkflowRecipientFilterParams,
    
    # Workflow Execution Record DTOs
    WorkflowExecutionRecordBaseDto,
    WorkflowExecutionRecordCreateDto,
    WorkflowExecutionRecordUpdateDto,
    WorkflowExecutionRecordViewDto,
    WorkflowExecutionRecordFilterParams,
    
    # User DTOs
    UserViewDto,
    
    # Event DTOs
    WorkflowEventDto,
)


class WorkflowTriggerSchemaManager:
    """Schema manager for workflow trigger entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": WorkflowTriggerViewDto,
            "create_schema": WorkflowTriggerCreateDto,
            "update_schema": WorkflowTriggerUpdateDto,
            "filter_schema": WorkflowTriggerFilterParams,
        }
    
    def entity_to_dto(
        self, entity: WorkflowTrigger, dto_class: Type[BaseModel] = None
    ) -> Union[WorkflowTriggerViewDto, BaseModel]:
        """Convert a workflow trigger entity to a DTO.
        
        Args:
            entity: The workflow trigger entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "workflow_id": entity.workflow_id,
            "entity_type": entity.entity_type,
            "operation": entity.operation,
            "field_conditions": entity.field_conditions,
            "priority": entity.priority,
            "is_active": entity.is_active,
        }
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[WorkflowTriggerCreateDto, WorkflowTriggerUpdateDto], entity: Optional[WorkflowTrigger] = None
    ) -> WorkflowTrigger:
        """Convert a DTO to a workflow trigger entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "entity_type") and dto.entity_type is not None:
                entity.entity_type = dto.entity_type
            if hasattr(dto, "operation") and dto.operation is not None:
                entity.operation = dto.operation
            if hasattr(dto, "field_conditions") and dto.field_conditions is not None:
                entity.field_conditions = dto.field_conditions
            if hasattr(dto, "priority") and dto.priority is not None:
                entity.priority = dto.priority
            if hasattr(dto, "is_active") and dto.is_active is not None:
                entity.is_active = dto.is_active
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            # Generate a temporary ID that will be replaced when saved to the database
            if "id" not in entity_data:
                entity_data["id"] = ""
            if "workflow_id" not in entity_data:
                entity_data["workflow_id"] = ""
            
            return WorkflowTrigger(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[WorkflowTrigger], dto_class: Type[BaseModel] = None
    ) -> List[Union[WorkflowTriggerViewDto, BaseModel]]:
        """Convert a list of workflow trigger entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]
    
    def dto_list_to_entity_list(
        self, dtos: List[Union[WorkflowTriggerCreateDto, WorkflowTriggerUpdateDto]]
    ) -> List[WorkflowTrigger]:
        """Convert a list of DTOs to a list of workflow trigger entities.
        
        Args:
            dtos: The list of DTOs to convert.
            
        Returns:
            The list of converted entities.
        """
        return [self.dto_to_entity(dto) for dto in dtos]


class WorkflowConditionSchemaManager:
    """Schema manager for workflow condition entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": WorkflowConditionViewDto,
            "create_schema": WorkflowConditionCreateDto,
            "update_schema": WorkflowConditionUpdateDto,
            "filter_schema": WorkflowConditionFilterParams,
        }
    
    def entity_to_dto(
        self, entity: WorkflowCondition, dto_class: Type[BaseModel] = None
    ) -> Union[WorkflowConditionViewDto, BaseModel]:
        """Convert a workflow condition entity to a DTO.
        
        Args:
            entity: The workflow condition entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "workflow_id": entity.workflow_id,
            "condition_type": entity.condition_type,
            "condition_config": entity.condition_config,
            "query_id": entity.query_id,
            "name": entity.name,
            "description": entity.description,
            "order": entity.order,
        }
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[WorkflowConditionCreateDto, WorkflowConditionUpdateDto], entity: Optional[WorkflowCondition] = None
    ) -> WorkflowCondition:
        """Convert a DTO to a workflow condition entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "condition_type") and dto.condition_type is not None:
                entity.condition_type = dto.condition_type
            if hasattr(dto, "condition_config") and dto.condition_config is not None:
                entity.condition_config = dto.condition_config
            if hasattr(dto, "query_id") and dto.query_id is not None:
                entity.query_id = dto.query_id
            if hasattr(dto, "name") and dto.name is not None:
                entity.name = dto.name
            if hasattr(dto, "description") and dto.description is not None:
                entity.description = dto.description
            if hasattr(dto, "order") and dto.order is not None:
                entity.order = dto.order
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            # Generate a temporary ID that will be replaced when saved to the database
            if "id" not in entity_data:
                entity_data["id"] = ""
            if "workflow_id" not in entity_data:
                entity_data["workflow_id"] = ""
            
            return WorkflowCondition(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[WorkflowCondition], dto_class: Type[BaseModel] = None
    ) -> List[Union[WorkflowConditionViewDto, BaseModel]]:
        """Convert a list of workflow condition entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]
    
    def dto_list_to_entity_list(
        self, dtos: List[Union[WorkflowConditionCreateDto, WorkflowConditionUpdateDto]]
    ) -> List[WorkflowCondition]:
        """Convert a list of DTOs to a list of workflow condition entities.
        
        Args:
            dtos: The list of DTOs to convert.
            
        Returns:
            The list of converted entities.
        """
        return [self.dto_to_entity(dto) for dto in dtos]


class WorkflowRecipientSchemaManager:
    """Schema manager for workflow recipient entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": WorkflowRecipientViewDto,
            "create_schema": WorkflowRecipientCreateDto,
            "update_schema": WorkflowRecipientUpdateDto,
            "filter_schema": WorkflowRecipientFilterParams,
        }
    
    def entity_to_dto(
        self, entity: WorkflowRecipient, dto_class: Type[BaseModel] = None
    ) -> Union[WorkflowRecipientViewDto, BaseModel]:
        """Convert a workflow recipient entity to a DTO.
        
        Args:
            entity: The workflow recipient entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "workflow_id": entity.workflow_id,
            "recipient_type": entity.recipient_type,
            "recipient_id": entity.recipient_id,
            "name": entity.name,
            "action_id": entity.action_id,
            "notification_config": entity.notification_config,
        }
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[WorkflowRecipientCreateDto, WorkflowRecipientUpdateDto], entity: Optional[WorkflowRecipient] = None
    ) -> WorkflowRecipient:
        """Convert a DTO to a workflow recipient entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "recipient_type") and dto.recipient_type is not None:
                entity.recipient_type = dto.recipient_type
            if hasattr(dto, "recipient_id") and dto.recipient_id is not None:
                entity.recipient_id = dto.recipient_id
            if hasattr(dto, "name") and dto.name is not None:
                entity.name = dto.name
            if hasattr(dto, "action_id") and dto.action_id is not None:
                entity.action_id = dto.action_id
            if hasattr(dto, "notification_config") and dto.notification_config is not None:
                entity.notification_config = dto.notification_config
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            # Generate a temporary ID that will be replaced when saved to the database
            if "id" not in entity_data:
                entity_data["id"] = ""
            if "workflow_id" not in entity_data:
                entity_data["workflow_id"] = ""
            
            return WorkflowRecipient(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[WorkflowRecipient], dto_class: Type[BaseModel] = None
    ) -> List[Union[WorkflowRecipientViewDto, BaseModel]]:
        """Convert a list of workflow recipient entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]
    
    def dto_list_to_entity_list(
        self, dtos: List[Union[WorkflowRecipientCreateDto, WorkflowRecipientUpdateDto]]
    ) -> List[WorkflowRecipient]:
        """Convert a list of DTOs to a list of workflow recipient entities.
        
        Args:
            dtos: The list of DTOs to convert.
            
        Returns:
            The list of converted entities.
        """
        return [self.dto_to_entity(dto) for dto in dtos]


class WorkflowActionSchemaManager:
    """Schema manager for workflow action entities."""
    
    def __init__(self, recipient_schema_manager: Optional[WorkflowRecipientSchemaManager] = None):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": WorkflowActionViewDto,
            "create_schema": WorkflowActionCreateDto,
            "update_schema": WorkflowActionUpdateDto,
            "filter_schema": WorkflowActionFilterParams,
        }
        self.recipient_schema_manager = recipient_schema_manager or WorkflowRecipientSchemaManager()
    
    def entity_to_dto(
        self, entity: WorkflowAction, dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> Union[WorkflowActionViewDto, BaseModel]:
        """Convert a workflow action entity to a DTO.
        
        Args:
            entity: The workflow action entity to convert.
            dto_class: Optional DTO class to use for conversion.
            include_related: Whether to include related entities.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "workflow_id": entity.workflow_id,
            "action_type": entity.action_type,
            "action_config": entity.action_config,
            "name": entity.name,
            "description": entity.description,
            "order": entity.order,
            "is_active": entity.is_active,
            "retry_policy": entity.retry_policy,
        }
        
        if include_related and hasattr(entity, "recipients") and entity.recipients:
            dto_data["recipients"] = self.recipient_schema_manager.entity_list_to_dto_list(entity.recipients)
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[WorkflowActionCreateDto, WorkflowActionUpdateDto], entity: Optional[WorkflowAction] = None
    ) -> WorkflowAction:
        """Convert a DTO to a workflow action entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "action_type") and dto.action_type is not None:
                entity.action_type = dto.action_type
            if hasattr(dto, "action_config") and dto.action_config is not None:
                entity.action_config = dto.action_config
            if hasattr(dto, "name") and dto.name is not None:
                entity.name = dto.name
            if hasattr(dto, "description") and dto.description is not None:
                entity.description = dto.description
            if hasattr(dto, "order") and dto.order is not None:
                entity.order = dto.order
            if hasattr(dto, "is_active") and dto.is_active is not None:
                entity.is_active = dto.is_active
            if hasattr(dto, "retry_policy") and dto.retry_policy is not None:
                entity.retry_policy = dto.retry_policy
            
            # Handle recipients (if included in the DTO)
            if hasattr(dto, "recipients") and dto.recipients:
                entity.recipients = self.recipient_schema_manager.dto_list_to_entity_list(dto.recipients)
                for recipient in entity.recipients:
                    recipient.action_id = entity.id
                    recipient.workflow_id = entity.workflow_id
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude={"recipients"}, exclude_unset=True)
            # Generate a temporary ID that will be replaced when saved to the database
            if "id" not in entity_data:
                entity_data["id"] = ""
            if "workflow_id" not in entity_data:
                entity_data["workflow_id"] = ""
            
            entity = WorkflowAction(**entity_data)
            
            # Handle recipients (if included in the DTO)
            if hasattr(dto, "recipients") and dto.recipients:
                entity.recipients = self.recipient_schema_manager.dto_list_to_entity_list(dto.recipients)
                for recipient in entity.recipients:
                    recipient.action_id = entity.id
            
            return entity
    
    def entity_list_to_dto_list(
        self, entities: List[WorkflowAction], dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> List[Union[WorkflowActionViewDto, BaseModel]]:
        """Convert a list of workflow action entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            include_related: Whether to include related entities.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class, include_related) for entity in entities]
    
    def dto_list_to_entity_list(
        self, dtos: List[Union[WorkflowActionCreateDto, WorkflowActionUpdateDto]]
    ) -> List[WorkflowAction]:
        """Convert a list of DTOs to a list of workflow action entities.
        
        Args:
            dtos: The list of DTOs to convert.
            
        Returns:
            The list of converted entities.
        """
        return [self.dto_to_entity(dto) for dto in dtos]


class WorkflowExecutionRecordSchemaManager:
    """Schema manager for workflow execution record entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": WorkflowExecutionRecordViewDto,
            "create_schema": WorkflowExecutionRecordCreateDto,
            "update_schema": WorkflowExecutionRecordUpdateDto,
            "filter_schema": WorkflowExecutionRecordFilterParams,
        }
    
    def entity_to_dto(
        self, entity: WorkflowExecutionRecord, dto_class: Type[BaseModel] = None
    ) -> Union[WorkflowExecutionRecordViewDto, BaseModel]:
        """Convert a workflow execution record entity to a DTO.
        
        Args:
            entity: The workflow execution record entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "workflow_id": entity.workflow_id,
            "trigger_event_id": entity.trigger_event_id,
            "status": entity.status,
            "executed_at": entity.executed_at,
            "completed_at": entity.completed_at,
            "result": entity.result,
            "error": entity.error,
            "context": entity.context,
            "execution_time": entity.execution_time,
        }
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[WorkflowExecutionRecordCreateDto, WorkflowExecutionRecordUpdateDto], entity: Optional[WorkflowExecutionRecord] = None
    ) -> WorkflowExecutionRecord:
        """Convert a DTO to a workflow execution record entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "status") and dto.status is not None:
                entity.status = dto.status
            if hasattr(dto, "completed_at") and dto.completed_at is not None:
                entity.completed_at = dto.completed_at
            if hasattr(dto, "result") and dto.result is not None:
                entity.result = dto.result
            if hasattr(dto, "error") and dto.error is not None:
                entity.error = dto.error
            if hasattr(dto, "context") and dto.context is not None:
                entity.context = dto.context
            if hasattr(dto, "execution_time") and dto.execution_time is not None:
                entity.execution_time = dto.execution_time
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            # Generate a temporary ID that will be replaced when saved to the database
            if "id" not in entity_data:
                entity_data["id"] = ""
            
            return WorkflowExecutionRecord(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[WorkflowExecutionRecord], dto_class: Type[BaseModel] = None
    ) -> List[Union[WorkflowExecutionRecordViewDto, BaseModel]]:
        """Convert a list of workflow execution record entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]
    
    def dto_list_to_entity_list(
        self, dtos: List[Union[WorkflowExecutionRecordCreateDto, WorkflowExecutionRecordUpdateDto]]
    ) -> List[WorkflowExecutionRecord]:
        """Convert a list of DTOs to a list of workflow execution record entities.
        
        Args:
            dtos: The list of DTOs to convert.
            
        Returns:
            The list of converted entities.
        """
        return [self.dto_to_entity(dto) for dto in dtos]


class UserSchemaManager:
    """Schema manager for user entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": UserViewDto,
        }
    
    def entity_to_dto(
        self, entity: User, dto_class: Type[BaseModel] = None
    ) -> Union[UserViewDto, BaseModel]:
        """Convert a user entity to a DTO.
        
        Args:
            entity: The user entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "username": entity.username,
            "email": entity.email,
            "is_active": entity.is_active,
            "display_name": entity.display_name,
            "roles": entity.roles,
        }
        
        return dto_class(**dto_data)
    
    def entity_list_to_dto_list(
        self, entities: List[User], dto_class: Type[BaseModel] = None
    ) -> List[Union[UserViewDto, BaseModel]]:
        """Convert a list of user entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]


class WorkflowDefSchemaManager:
    """Schema manager for workflow definition entities."""
    
    def __init__(
        self,
        trigger_schema_manager: Optional[WorkflowTriggerSchemaManager] = None,
        condition_schema_manager: Optional[WorkflowConditionSchemaManager] = None,
        action_schema_manager: Optional[WorkflowActionSchemaManager] = None,
        recipient_schema_manager: Optional[WorkflowRecipientSchemaManager] = None,
    ):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": WorkflowDefViewDto,
            "create_schema": WorkflowDefCreateDto,
            "update_schema": WorkflowDefUpdateDto,
            "filter_schema": WorkflowDefFilterParams,
        }
        self.trigger_schema_manager = trigger_schema_manager or WorkflowTriggerSchemaManager()
        self.condition_schema_manager = condition_schema_manager or WorkflowConditionSchemaManager()
        self.action_schema_manager = action_schema_manager or WorkflowActionSchemaManager(
            recipient_schema_manager=recipient_schema_manager or WorkflowRecipientSchemaManager()
        )
        self.recipient_schema_manager = recipient_schema_manager or WorkflowRecipientSchemaManager()
    
    def entity_to_dto(
        self, entity: WorkflowDef, dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> Union[WorkflowDefViewDto, BaseModel]:
        """Convert a workflow definition entity to a DTO.
        
        Args:
            entity: The workflow definition entity to convert.
            dto_class: Optional DTO class to use for conversion.
            include_related: Whether to include related entities.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "status": entity.status,
            "version": entity.version,
        }
        
        if include_related:
            if hasattr(entity, "triggers") and entity.triggers:
                dto_data["triggers"] = self.trigger_schema_manager.entity_list_to_dto_list(entity.triggers)
            
            if hasattr(entity, "conditions") and entity.conditions:
                dto_data["conditions"] = self.condition_schema_manager.entity_list_to_dto_list(entity.conditions)
            
            if hasattr(entity, "actions") and entity.actions:
                dto_data["actions"] = self.action_schema_manager.entity_list_to_dto_list(entity.actions)
            
            if hasattr(entity, "recipients") and entity.recipients:
                dto_data["recipients"] = self.recipient_schema_manager.entity_list_to_dto_list(entity.recipients)
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[WorkflowDefCreateDto, WorkflowDefUpdateDto], entity: Optional[WorkflowDef] = None
    ) -> WorkflowDef:
        """Convert a DTO to a workflow definition entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "name") and dto.name is not None:
                entity.name = dto.name
            if hasattr(dto, "description") and dto.description is not None:
                entity.description = dto.description
            if hasattr(dto, "status") and dto.status is not None:
                entity.status = dto.status
            if hasattr(dto, "version") and dto.version is not None:
                entity.version = dto.version
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(
                exclude={"triggers", "conditions", "actions", "recipients"}, 
                exclude_unset=True
            )
            # Generate a temporary ID that will be replaced when saved to the database
            if "id" not in entity_data:
                entity_data["id"] = ""
            
            entity = WorkflowDef(**entity_data)
            
            # Handle related entities
            if hasattr(dto, "triggers") and dto.triggers:
                entity.triggers = self.trigger_schema_manager.dto_list_to_entity_list(dto.triggers)
                for trigger in entity.triggers:
                    trigger.workflow_id = entity.id
            
            if hasattr(dto, "conditions") and dto.conditions:
                entity.conditions = self.condition_schema_manager.dto_list_to_entity_list(dto.conditions)
                for condition in entity.conditions:
                    condition.workflow_id = entity.id
            
            if hasattr(dto, "actions") and dto.actions:
                entity.actions = self.action_schema_manager.dto_list_to_entity_list(dto.actions)
                for action in entity.actions:
                    action.workflow_id = entity.id
                    for recipient in action.recipients:
                        recipient.workflow_id = entity.id
                        recipient.action_id = action.id
            
            if hasattr(dto, "recipients") and dto.recipients:
                entity.recipients = self.recipient_schema_manager.dto_list_to_entity_list(dto.recipients)
                for recipient in entity.recipients:
                    recipient.workflow_id = entity.id
            
            return entity
    
    def entity_list_to_dto_list(
        self, entities: List[WorkflowDef], dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> List[Union[WorkflowDefViewDto, BaseModel]]:
        """Convert a list of workflow definition entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            include_related: Whether to include related entities.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class, include_related) for entity in entities]
    
    def dto_list_to_entity_list(
        self, dtos: List[Union[WorkflowDefCreateDto, WorkflowDefUpdateDto]]
    ) -> List[WorkflowDef]:
        """Convert a list of DTOs to a list of workflow definition entities.
        
        Args:
            dtos: The list of DTOs to convert.
            
        Returns:
            The list of converted entities.
        """
        return [self.dto_to_entity(dto) for dto in dtos]


def register_workflow_schemas():
    """Register all workflow schemas with the schema registry."""
    # This function is needed for backward compatibility
    # with the code that expects schemas to be registered
    pass