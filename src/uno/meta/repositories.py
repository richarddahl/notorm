"""
Repository implementations for meta models.

This module implements repositories for the meta domain models,
which handle metadata about entities in the system.
"""

from typing import List, Optional, Dict, Any
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.repository import BaseRepository
from uno.meta.models import MetaTypeModel, MetaRecordModel


class MetaTypeRepository(BaseRepository[MetaTypeModel]):
    """
    Repository for MetaType entities.

    Provides data access methods for type metadata.
    """

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a database session."""
        super().__init__(session, MetaTypeModel, logger)

    async def get_all_types(self) -> list[MetaTypeModel]:
        """
        Get all meta types.

        Returns:
            List of all meta types
        """
        stmt = select(self.model_class)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_type_by_id(self, type_id: str) -> Optional[MetaTypeModel]:
        """
        Get a meta type by ID.

        This is an alias for the standard get method, provided
        for consistency with the repository pattern.

        Args:
            type_id: The type ID to look up

        Returns:
            The meta type if found, None otherwise
        """
        return await self.get(type_id)


class MetaRecordRepository(BaseRepository[MetaRecordModel]):
    """
    Repository for MetaRecord entities.

    Provides data access methods for entity metadata records.
    """

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a database session."""
        super().__init__(session, MetaRecordModel, logger)

    async def find_by_type(
        self, type_id: str, limit: int | None = None, offset: int | None = None
    ) -> list[MetaRecordModel]:
        """
        Find all records of a specific meta type.

        Args:
            type_id: The meta type ID to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of meta records of the specified type
        """
        stmt = select(self.model_class).where(self.model_class.meta_type_id == type_id)

        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_ids(self, record_ids: list[str]) -> list[MetaRecordModel]:
        """
        Find meta records by a list of IDs.

        Args:
            record_ids: List of record IDs to find

        Returns:
            List of found meta records
        """
        if not record_ids:
            return []

        stmt = select(self.model_class).where(self.model_class.id.in_(record_ids))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_with_type(self, record_id: str, type_id: str) -> MetaRecordModel:
        """
        Create a new meta record with the specified type.

        Args:
            record_id: The record ID
            type_id: The meta type ID

        Returns:
            The created meta record
        """
        return await self.create({"id": record_id, "meta_type_id": type_id})
