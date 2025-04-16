"""Schema managers for the Reports module."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Type

from pydantic import BaseModel

from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
)
from uno.reports.dtos import (
    # Field Definition DTOs
    ReportFieldDefinitionBaseDto,
    ReportFieldDefinitionCreateDto,
    ReportFieldDefinitionUpdateDto,
    ReportFieldDefinitionViewDto,
    ReportFieldDefinitionFilterParams,
    
    # Template DTOs
    ReportTemplateBaseDto,
    ReportTemplateCreateDto,
    ReportTemplateUpdateDto,
    ReportTemplateViewDto,
    ReportTemplateFilterParams,
    
    # Trigger DTOs
    ReportTriggerBaseDto,
    ReportTriggerCreateDto,
    ReportTriggerUpdateDto,
    ReportTriggerViewDto,
    ReportTriggerFilterParams,
    
    # Output DTOs
    ReportOutputBaseDto,
    ReportOutputCreateDto,
    ReportOutputUpdateDto,
    ReportOutputViewDto,
    ReportOutputFilterParams,
    
    # Execution DTOs
    ReportExecutionBaseDto,
    ReportExecutionCreateDto,
    ReportExecutionUpdateStatusDto,
    ReportExecutionViewDto,
    ReportExecutionFilterParams,
    
    # Output Execution DTOs
    ReportOutputExecutionBaseDto,
    ReportOutputExecutionCreateDto,
    ReportOutputExecutionUpdateStatusDto,
    ReportOutputExecutionViewDto,
    ReportOutputExecutionFilterParams,
)


class ReportFieldDefinitionSchemaManager:
    """Schema manager for report field definition entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ReportFieldDefinitionViewDto,
            "create_schema": ReportFieldDefinitionCreateDto,
            "update_schema": ReportFieldDefinitionUpdateDto,
            "filter_schema": ReportFieldDefinitionFilterParams,
        }
    
    def entity_to_dto(
        self, entity: ReportFieldDefinition, dto_class: Type[BaseModel] = None
    ) -> Union[ReportFieldDefinitionViewDto, BaseModel]:
        """Convert a field definition entity to a DTO.
        
        Args:
            entity: The field definition entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "name": entity.name,
            "display": entity.display,
            "field_type": entity.field_type,
            "field_config": entity.field_config,
            "description": entity.description,
            "order": entity.order,
            "format_string": entity.format_string,
            "conditional_formats": entity.conditional_formats,
            "is_visible": entity.is_visible,
            "parent_field_id": entity.parent_field_id,
        }
        
        return dto_class(**dto_data)
    
    def dto_to_entity(
        self, dto: Union[ReportFieldDefinitionCreateDto, ReportFieldDefinitionUpdateDto], entity: Optional[ReportFieldDefinition] = None
    ) -> ReportFieldDefinition:
        """Convert a DTO to a field definition entity.
        
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
            if hasattr(dto, "display") and dto.display is not None:
                entity.display = dto.display
            if hasattr(dto, "field_type") and dto.field_type is not None:
                entity.field_type = dto.field_type
            if hasattr(dto, "field_config") and dto.field_config is not None:
                entity.field_config = dto.field_config
            if hasattr(dto, "description") and dto.description is not None:
                entity.description = dto.description
            if hasattr(dto, "order") and dto.order is not None:
                entity.order = dto.order
            if hasattr(dto, "format_string") and dto.format_string is not None:
                entity.format_string = dto.format_string
            if hasattr(dto, "conditional_formats") and dto.conditional_formats is not None:
                entity.conditional_formats = dto.conditional_formats
            if hasattr(dto, "is_visible") and dto.is_visible is not None:
                entity.is_visible = dto.is_visible
            if hasattr(dto, "parent_field_id") and dto.parent_field_id is not None:
                entity.parent_field_id = dto.parent_field_id
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            return ReportFieldDefinition(**entity_data)
    
    def dto_list_to_entity_list(
        self, dtos: List[Union[ReportFieldDefinitionCreateDto, ReportFieldDefinitionUpdateDto]]
    ) -> List[ReportFieldDefinition]:
        """Convert a list of DTOs to a list of field definition entities.
        
        Args:
            dtos: The list of DTOs to convert.
            
        Returns:
            The list of converted entities.
        """
        return [self.dto_to_entity(dto) for dto in dtos]
    
    def entity_list_to_dto_list(
        self, entities: List[ReportFieldDefinition], dto_class: Type[BaseModel] = None
    ) -> List[Union[ReportFieldDefinitionViewDto, BaseModel]]:
        """Convert a list of field definition entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]


class ReportTemplateSchemaManager:
    """Schema manager for report template entities."""
    
    def __init__(self, field_definition_schema_manager: Optional[ReportFieldDefinitionSchemaManager] = None):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ReportTemplateViewDto,
            "create_schema": ReportTemplateCreateDto,
            "update_schema": ReportTemplateUpdateDto,
            "filter_schema": ReportTemplateFilterParams,
        }
        self.field_definition_schema_manager = field_definition_schema_manager or ReportFieldDefinitionSchemaManager()
    
    def entity_to_dto(
        self, entity: ReportTemplate, dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> Union[ReportTemplateViewDto, BaseModel]:
        """Convert a template entity to a DTO.
        
        Args:
            entity: The template entity to convert.
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
            "base_object_type": entity.base_object_type,
            "format_config": entity.format_config,
            "parameter_definitions": entity.parameter_definitions,
            "cache_policy": entity.cache_policy,
            "version": entity.version,
        }
        
        if include_related and hasattr(dto_class, "fields") and entity.fields:
            dto_data["fields"] = self.field_definition_schema_manager.entity_list_to_dto_list(entity.fields)
        
        return dto_class(**dto_data)
    
    def dto_to_entity(
        self, dto: Union[ReportTemplateCreateDto, ReportTemplateUpdateDto], entity: Optional[ReportTemplate] = None
    ) -> ReportTemplate:
        """Convert a DTO to a template entity.
        
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
            if hasattr(dto, "base_object_type") and dto.base_object_type is not None:
                entity.base_object_type = dto.base_object_type
            if hasattr(dto, "format_config") and dto.format_config is not None:
                entity.format_config = dto.format_config
            if hasattr(dto, "parameter_definitions") and dto.parameter_definitions is not None:
                entity.parameter_definitions = dto.parameter_definitions
            if hasattr(dto, "cache_policy") and dto.cache_policy is not None:
                entity.cache_policy = dto.cache_policy
            if hasattr(dto, "version") and dto.version is not None:
                entity.version = dto.version
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude={"field_ids"}, exclude_unset=True)
            return ReportTemplate(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[ReportTemplate], dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> List[Union[ReportTemplateViewDto, BaseModel]]:
        """Convert a list of template entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            include_related: Whether to include related entities.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class, include_related) for entity in entities]


class ReportTriggerSchemaManager:
    """Schema manager for report trigger entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ReportTriggerViewDto,
            "create_schema": ReportTriggerCreateDto,
            "update_schema": ReportTriggerUpdateDto,
            "filter_schema": ReportTriggerFilterParams,
        }
    
    def entity_to_dto(
        self, entity: ReportTrigger, dto_class: Type[BaseModel] = None
    ) -> Union[ReportTriggerViewDto, BaseModel]:
        """Convert a trigger entity to a DTO.
        
        Args:
            entity: The trigger entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "report_template_id": entity.report_template_id,
            "trigger_type": entity.trigger_type,
            "trigger_config": entity.trigger_config,
            "schedule": entity.schedule,
            "event_type": entity.event_type,
            "entity_type": entity.entity_type,
            "query_id": entity.query_id,
            "is_active": entity.is_active,
            "last_triggered": entity.last_triggered,
        }
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[ReportTriggerCreateDto, ReportTriggerUpdateDto], entity: Optional[ReportTrigger] = None
    ) -> ReportTrigger:
        """Convert a DTO to a trigger entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "trigger_type") and dto.trigger_type is not None:
                entity.trigger_type = dto.trigger_type
            if hasattr(dto, "trigger_config") and dto.trigger_config is not None:
                entity.trigger_config = dto.trigger_config
            if hasattr(dto, "schedule") and dto.schedule is not None:
                entity.schedule = dto.schedule
            if hasattr(dto, "event_type") and dto.event_type is not None:
                entity.event_type = dto.event_type
            if hasattr(dto, "entity_type") and dto.entity_type is not None:
                entity.entity_type = dto.entity_type
            if hasattr(dto, "query_id") and dto.query_id is not None:
                entity.query_id = dto.query_id
            if hasattr(dto, "is_active") and dto.is_active is not None:
                entity.is_active = dto.is_active
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            return ReportTrigger(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[ReportTrigger], dto_class: Type[BaseModel] = None
    ) -> List[Union[ReportTriggerViewDto, BaseModel]]:
        """Convert a list of trigger entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]


class ReportOutputSchemaManager:
    """Schema manager for report output entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ReportOutputViewDto,
            "create_schema": ReportOutputCreateDto,
            "update_schema": ReportOutputUpdateDto,
            "filter_schema": ReportOutputFilterParams,
        }
    
    def entity_to_dto(
        self, entity: ReportOutput, dto_class: Type[BaseModel] = None
    ) -> Union[ReportOutputViewDto, BaseModel]:
        """Convert an output entity to a DTO.
        
        Args:
            entity: The output entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "report_template_id": entity.report_template_id,
            "output_type": entity.output_type,
            "format": entity.format,
            "output_config": entity.output_config,
            "format_config": entity.format_config,
            "is_active": entity.is_active,
        }
        
        return dto_class(**dto_data)
    
    def dto_to_entity(
        self, dto: Union[ReportOutputCreateDto, ReportOutputUpdateDto], entity: Optional[ReportOutput] = None
    ) -> ReportOutput:
        """Convert a DTO to an output entity.
        
        Args:
            dto: The DTO to convert.
            entity: Optional existing entity to update.
            
        Returns:
            The converted entity.
        """
        if entity:
            # Update existing entity
            if hasattr(dto, "output_type") and dto.output_type is not None:
                entity.output_type = dto.output_type
            if hasattr(dto, "format") and dto.format is not None:
                entity.format = dto.format
            if hasattr(dto, "output_config") and dto.output_config is not None:
                entity.output_config = dto.output_config
            if hasattr(dto, "format_config") and dto.format_config is not None:
                entity.format_config = dto.format_config
            if hasattr(dto, "is_active") and dto.is_active is not None:
                entity.is_active = dto.is_active
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            return ReportOutput(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[ReportOutput], dto_class: Type[BaseModel] = None
    ) -> List[Union[ReportOutputViewDto, BaseModel]]:
        """Convert a list of output entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]


class ReportOutputExecutionSchemaManager:
    """Schema manager for report output execution entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ReportOutputExecutionViewDto,
            "create_schema": ReportOutputExecutionCreateDto,
            "update_schema": ReportOutputExecutionUpdateStatusDto,
            "filter_schema": ReportOutputExecutionFilterParams,
        }
    
    def entity_to_dto(
        self, entity: ReportOutputExecution, dto_class: Type[BaseModel] = None
    ) -> Union[ReportOutputExecutionViewDto, BaseModel]:
        """Convert an output execution entity to a DTO.
        
        Args:
            entity: The output execution entity to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "report_execution_id": entity.report_execution_id,
            "report_output_id": entity.report_output_id,
            "status": entity.status,
            "completed_at": entity.completed_at,
            "error_details": entity.error_details,
            "output_location": entity.output_location,
            "output_size_bytes": entity.output_size_bytes,
        }
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[ReportOutputExecutionCreateDto, ReportOutputExecutionUpdateStatusDto], entity: Optional[ReportOutputExecution] = None
    ) -> ReportOutputExecution:
        """Convert a DTO to an output execution entity.
        
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
            if hasattr(dto, "error_details") and dto.error_details is not None:
                entity.error_details = dto.error_details
            if hasattr(dto, "output_location") and dto.output_location is not None:
                entity.output_location = dto.output_location
            if hasattr(dto, "output_size_bytes") and dto.output_size_bytes is not None:
                entity.output_size_bytes = dto.output_size_bytes
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            return ReportOutputExecution(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[ReportOutputExecution], dto_class: Type[BaseModel] = None
    ) -> List[Union[ReportOutputExecutionViewDto, BaseModel]]:
        """Convert a list of output execution entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class) for entity in entities]


class ReportExecutionSchemaManager:
    """Schema manager for report execution entities."""
    
    def __init__(self, output_execution_schema_manager: Optional[ReportOutputExecutionSchemaManager] = None):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ReportExecutionViewDto,
            "create_schema": ReportExecutionCreateDto,
            "update_schema": ReportExecutionUpdateStatusDto,
            "filter_schema": ReportExecutionFilterParams,
        }
        self.output_execution_schema_manager = output_execution_schema_manager or ReportOutputExecutionSchemaManager()
    
    def entity_to_dto(
        self, entity: ReportExecution, dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> Union[ReportExecutionViewDto, BaseModel]:
        """Convert an execution entity to a DTO.
        
        Args:
            entity: The execution entity to convert.
            dto_class: Optional DTO class to use for conversion.
            include_related: Whether to include related entities.
            
        Returns:
            The converted DTO.
        """
        dto_class = dto_class or self.schemas["view_schema"]
        
        dto_data = {
            "id": entity.id,
            "report_template_id": entity.report_template_id,
            "triggered_by": entity.triggered_by,
            "trigger_type": entity.trigger_type,
            "parameters": entity.parameters,
            "status": entity.status,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
            "error_details": entity.error_details,
            "row_count": entity.row_count,
            "execution_time_ms": entity.execution_time_ms,
            "result_hash": entity.result_hash,
        }
        
        if include_related and hasattr(dto_class, "output_executions") and entity.output_executions:
            dto_data["output_executions"] = self.output_execution_schema_manager.entity_list_to_dto_list(entity.output_executions)
        
        return dto_class(**{k: v for k, v in dto_data.items() if hasattr(dto_class, k)})
    
    def dto_to_entity(
        self, dto: Union[ReportExecutionCreateDto, ReportExecutionUpdateStatusDto], entity: Optional[ReportExecution] = None
    ) -> ReportExecution:
        """Convert a DTO to an execution entity.
        
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
            if hasattr(dto, "error_details") and dto.error_details is not None:
                entity.error_details = dto.error_details
            
            return entity
        else:
            # Create new entity
            entity_data = dto.dict(exclude_unset=True)
            return ReportExecution(**entity_data)
    
    def entity_list_to_dto_list(
        self, entities: List[ReportExecution], dto_class: Type[BaseModel] = None, include_related: bool = True
    ) -> List[Union[ReportExecutionViewDto, BaseModel]]:
        """Convert a list of execution entities to a list of DTOs.
        
        Args:
            entities: The list of entities to convert.
            dto_class: Optional DTO class to use for conversion.
            include_related: Whether to include related entities.
            
        Returns:
            The list of converted DTOs.
        """
        return [self.entity_to_dto(entity, dto_class, include_related) for entity in entities]