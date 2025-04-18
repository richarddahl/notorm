"""
Repository implementations for the Meta module.

This module provides repository implementations for persisting and retrieving
meta entities from the database.
"""

from typing import List, Dict, Any, Optional, Type, TypeVar, cast
import logging

from uno.core.base.respository import UnoDBRepository
from uno.core.errors.result import Result, Success, Failure
from uno.meta.entities import MetaType, MetaRecord


# Type variables
T = TypeVar("T")


class MetaRepositoryError(Exception):
    """Base error class for meta repository errors."""

    pass


class MetaTypeRepository(UnoDBRepository[MetaType]):
    """Repository for meta type entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=MetaType, db_factory=db_factory)

    async def create_meta_type(
        self, id: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> MetaType:
        """
        Create a new meta type.

        Args:
            id: The ID of the meta type
            name: Optional display name
            description: Optional description

        Returns:
            The created meta type
        """
        meta_type = MetaType(id=id, name=name, description=description)

        # Validate the meta type
        meta_type.validate()

        # Save to database
        return await self.add(meta_type)

    async def get_all_meta_types(self) -> List[MetaType]:
        """
        Get all meta types in the system.

        Returns:
            List of all meta types
        """
        return await self.list()

    async def get_with_records(
        self, id: str, record_limit: int = 100
    ) -> Optional[MetaType]:
        """
        Get a meta type with its associated records.

        Args:
            id: The ID of the meta type
            record_limit: Maximum number of records to retrieve

        Returns:
            The meta type with loaded records if found, None otherwise
        """
        # First get the basic meta type
        meta_type = await self.get(id)
        if not meta_type:
            return None

        # In a real implementation, load related records
        # For now, we'll just initialize the list
        meta_type.meta_records = []

        return meta_type


class MetaRecordRepository(UnoDBRepository[MetaRecord]):
    """Repository for meta record entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=MetaRecord, db_factory=db_factory)

    async def create_meta_record(self, id: str, meta_type_id: str) -> MetaRecord:
        """
        Create a new meta record.

        Args:
            id: The ID of the meta record
            meta_type_id: The ID of the associated meta type

        Returns:
            The created meta record
        """
        meta_record = MetaRecord(id=id, meta_type_id=meta_type_id)

        # Validate the meta record
        meta_record.validate()

        # Save to database
        return await self.add(meta_record)

    async def find_by_meta_type(
        self, meta_type_id: str, limit: int = 100
    ) -> List[MetaRecord]:
        """
        Find meta records by meta type ID.

        Args:
            meta_type_id: The meta type ID to search for
            limit: Maximum number of records to return

        Returns:
            List of meta records with the given meta type
        """
        filters = {"meta_type_id": {"lookup": "eq", "val": meta_type_id}}
        return await self.list(filters=filters, limit=limit)

    async def get_with_meta_type(
        self, id: str, meta_type_repo=None
    ) -> Optional[MetaRecord]:
        """
        Get a meta record with its associated meta type.

        Args:
            id: The ID of the meta record
            meta_type_repo: Optional repository for loading meta types

        Returns:
            The meta record with loaded meta type if found, None otherwise
        """
        # First get the basic meta record
        meta_record = await self.get(id)
        if not meta_record:
            return None

        # Load meta type if repository is provided
        if meta_type_repo and meta_record.meta_type_id:
            meta_record.meta_type = await meta_type_repo.get(meta_record.meta_type_id)

        return meta_record

    async def _convert_to_entity(self, data: Dict[str, Any]) -> MetaRecord:
        """Override to handle the specific meta record properties."""
        entity = await super()._convert_to_entity(data)

        # Set up empty collections
        entity.attributes = []

        return entity
