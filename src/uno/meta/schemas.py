"""
Schema managers for the Meta module.

This module contains schema managers that handle conversion between domain entities and DTOs,
following the domain-driven design approach. Each schema manager provides methods to convert
domain entities to DTOs and vice versa.
"""

from typing import List, Optional, Union, Dict, Any, Type

from uno.meta.entities import MetaType, MetaRecord
from uno.meta.dtos import (
    # Meta Type DTOs
    MetaTypeBaseDto,
    MetaTypeCreateDto,
    MetaTypeUpdateDto,
    MetaTypeViewDto,
    MetaTypeFilterParams,
    MetaTypeListDto,
    # Meta Record DTOs
    MetaRecordBaseDto,
    MetaRecordCreateDto,
    MetaRecordUpdateDto,
    MetaRecordViewDto,
    MetaRecordFilterParams,
    MetaRecordListDto,
)


class MetaTypeSchemaManager:
    """Schema manager for meta type entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": MetaTypeViewDto,
            "create_schema": MetaTypeCreateDto,
            "update_schema": MetaTypeUpdateDto,
            "filter_schema": MetaTypeFilterParams,
            "list_schema": MetaTypeListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: MetaType, record_count: int = 0) -> MetaTypeViewDto:
        """
        Convert a meta type entity to a DTO.

        Args:
            entity: The entity to convert
            record_count: Optional count of records for this type

        Returns:
            MetaTypeViewDto
        """
        return MetaTypeViewDto(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            display_name=entity.display_name,
            record_count=record_count,
        )

    def dto_to_entity(
        self,
        dto: Union[MetaTypeCreateDto, MetaTypeUpdateDto],
        existing_entity: Optional[MetaType] = None,
    ) -> MetaType:
        """
        Convert a DTO to a meta type entity.

        Args:
            dto: The DTO to convert
            existing_entity: Optional existing entity to update

        Returns:
            MetaType entity
        """
        if existing_entity:
            # Update existing entity
            if isinstance(dto, MetaTypeUpdateDto):
                if dto.name is not None:
                    existing_entity.name = dto.name
                if dto.description is not None:
                    existing_entity.description = dto.description
            return existing_entity
        else:
            # Create new entity
            if isinstance(dto, MetaTypeCreateDto):
                return MetaType(
                    id=dto.id,
                    name=dto.name,
                    description=dto.description,
                )
            raise ValueError(f"Cannot create entity from {type(dto).__name__}")

    def entities_to_list_dto(
        self,
        entities: list[MetaType],
        record_counts: dict[str, int],
        total: int,
        limit: int,
        offset: int,
    ) -> MetaTypeListDto:
        """
        Convert a list of meta type entities to a list DTO with pagination data.

        Args:
            entities: List of entities to convert
            record_counts: Dictionary mapping type IDs to record counts
            total: Total number of entities matching the query
            limit: Maximum number of results to return
            offset: Number of results skipped

        Returns:
            MetaTypeListDto
        """
        return MetaTypeListDto(
            items=[
                self.entity_to_dto(entity, record_counts.get(entity.id, 0))
                for entity in entities
            ],
            total=total,
            limit=limit,
            offset=offset,
        )


class MetaRecordSchemaManager:
    """Schema manager for meta record entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": MetaRecordViewDto,
            "create_schema": MetaRecordCreateDto,
            "update_schema": MetaRecordUpdateDto,
            "filter_schema": MetaRecordFilterParams,
            "list_schema": MetaRecordListDto,
        }

    def get_schema(self, schema_name: str) -> Type:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: MetaRecord) -> MetaRecordViewDto:
        """Convert a meta record entity to a DTO."""
        return MetaRecordViewDto(
            id=entity.id,
            meta_type_id=entity.meta_type_id,
            type_name=entity.type_name,
            attributes=entity.attributes.copy() if entity.attributes else [],
        )

    def dto_to_entity(
        self,
        dto: Union[MetaRecordCreateDto, MetaRecordUpdateDto],
        existing_entity: Optional[MetaRecord] = None,
    ) -> MetaRecord:
        """
        Convert a DTO to a meta record entity.

        Args:
            dto: The DTO to convert
            existing_entity: Optional existing entity to update

        Returns:
            MetaRecord entity
        """
        if existing_entity:
            # Update existing entity
            if isinstance(dto, MetaRecordUpdateDto):
                if dto.attributes is not None:
                    existing_entity.attributes = dto.attributes.copy()
            return existing_entity
        else:
            # Create new entity
            if isinstance(dto, MetaRecordCreateDto):
                entity = MetaRecord(
                    id=dto.id,
                    meta_type_id=dto.meta_type_id,
                )
                if dto.attributes:
                    entity.attributes = dto.attributes.copy()
                return entity
            raise ValueError(f"Cannot create entity from {type(dto).__name__}")

    def entities_to_list_dto(
        self, entities: list[MetaRecord], total: int, limit: int, offset: int
    ) -> MetaRecordListDto:
        """Convert a list of meta record entities to a list DTO with pagination data."""
        return MetaRecordListDto(
            items=[self.entity_to_dto(entity) for entity in entities],
            total=total,
            limit=limit,
            offset=offset,
        )
