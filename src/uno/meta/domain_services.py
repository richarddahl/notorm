"""
Domain services for the Meta module.

This module provides domain services that implement business logic for meta entities,
coordinating entity validation and persistence through repositories.
"""

from typing import List, Dict, Any, Optional, cast
import logging
import uuid

from uno.core.errors.result import Result
from uno.domain.service import UnoEntityService
from uno.meta.entities import MetaType, MetaRecord
from uno.meta.domain_repositories import MetaTypeRepository, MetaRecordRepository


class MetaServiceError(Exception):
    """Base error class for meta service errors."""

    pass


class MetaTypeService(UnoEntityService[MetaType]):
    """Service for meta type entities."""

    def __init__(
        self,
        repository: Optional[MetaTypeRepository] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the meta type service.

        Args:
            repository: The repository for data access
            logger: Optional logger
        """
        if repository is None:
            repository = MetaTypeRepository()

        super().__init__(MetaType, repository, logger)

    async def register_meta_type(
        self, id: str, name: str | None = None, description: str | None = None
    ) -> Result[MetaType]:
        """
        Register a new meta type in the system.

        Args:
            id: The ID of the meta type (typically matches a table name)
            name: Optional display name
            description: Optional description

        Returns:
            Result containing the created meta type
        """
        try:
            repository = cast(MetaTypeRepository, self.repository)

            # Check if meta type already exists
            existing = await repository.get(id)
            if existing:
                return Success(existing)  # Return existing meta type if found

            # Create new meta type
            meta_type = await repository.create_meta_type(id, name, description)
            return Success(meta_type)
        except Exception as e:
            self.logger.error(f"Error registering meta type: {e}")
            return Failure(MetaServiceError(f"Error registering meta type: {str(e)}"))

    async def get_all_types(self) -> Result[list[MetaType]]:
        """
        Get all meta types in the system.

        Returns:
            Result containing all meta types
        """
        try:
            repository = cast(MetaTypeRepository, self.repository)
            meta_types = await repository.get_all_meta_types()
            return Success(meta_types)
        except Exception as e:
            self.logger.error(f"Error getting all meta types: {e}")
            return Failure(MetaServiceError(f"Error getting all meta types: {str(e)}"))

    async def get_with_records(
        self, id: str, record_limit: int = 100
    ) -> Result[MetaType]:
        """
        Get a meta type with its associated records.

        Args:
            id: The ID of the meta type
            record_limit: Maximum number of records to retrieve

        Returns:
            Result containing the meta type with records
        """
        try:
            repository = cast(MetaTypeRepository, self.repository)
            result = await repository.get_with_records(id, record_limit)

            if not result:
                return Failure(MetaServiceError(f"Meta type {id} not found"))

            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting meta type with records: {e}")
            return Failure(
                MetaServiceError(f"Error getting meta type with records: {str(e)}")
            )


class MetaRecordService(UnoEntityService[MetaRecord]):
    """Service for meta record entities."""

    def __init__(
        self,
        repository: Optional[MetaRecordRepository] = None,
        meta_type_service: Optional[MetaTypeService] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the meta record service.

        Args:
            repository: The repository for data access
            meta_type_service: Service for meta types
            logger: Optional logger
        """
        if repository is None:
            repository = MetaRecordRepository()

        super().__init__(MetaRecord, repository, logger)

        # Store the meta type service for loading related data
        self.meta_type_service = meta_type_service

    async def create_record(
        self, meta_type_id: str, record_id: str | None = None
    ) -> Result[MetaRecord]:
        """
        Create a new meta record.

        Args:
            meta_type_id: The ID of the meta type
            record_id: Optional record ID (will be generated if not provided)

        Returns:
            Result containing the created meta record
        """
        try:
            repository = cast(MetaRecordRepository, self.repository)

            # Validate meta type exists if service is available
            if self.meta_type_service:
                meta_type_result = await self.meta_type_service.get_by_id(meta_type_id)
                if meta_type_result.is_failure:
                    return Failure(
                        MetaServiceError(
                            f"Meta type validation failed: {meta_type_result.error}"
                        )
                    )

                if not meta_type_result.value:
                    return Failure(
                        MetaServiceError(f"Meta type {meta_type_id} not found")
                    )

            # Generate record ID if not provided
            if not record_id:
                record_id = str(uuid.uuid4())

            # Create new meta record
            meta_record = await repository.create_meta_record(record_id, meta_type_id)
            return Success(meta_record)
        except Exception as e:
            self.logger.error(f"Error creating meta record: {e}")
            return Failure(MetaServiceError(f"Error creating meta record: {str(e)}"))

    async def find_by_meta_type(
        self, meta_type_id: str, limit: int = 100
    ) -> Result[list[MetaRecord]]:
        """
        Find meta records by meta type.

        Args:
            meta_type_id: The ID of the meta type
            limit: Maximum number of records to return

        Returns:
            Result containing matching meta records
        """
        try:
            repository = cast(MetaRecordRepository, self.repository)
            records = await repository.find_by_meta_type(meta_type_id, limit)
            return Success(records)
        except Exception as e:
            self.logger.error(f"Error finding meta records by type: {e}")
            return Failure(MetaServiceError(f"Error finding meta records: {str(e)}"))

    async def get_with_meta_type(self, id: str) -> Result[MetaRecord]:
        """
        Get a meta record with its associated meta type.

        Args:
            id: The ID of the meta record

        Returns:
            Result containing the meta record with meta type
        """
        try:
            repository = cast(MetaRecordRepository, self.repository)

            # Get the meta type repository if needed
            meta_type_repo = None
            if self.meta_type_service:
                meta_type_repo = cast(
                    MetaTypeRepository, self.meta_type_service.repository
                )

            # Get the meta record with relationships
            result = await repository.get_with_meta_type(id, meta_type_repo)

            if not result:
                return Failure(MetaServiceError(f"Meta record {id} not found"))

            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting meta record with meta type: {e}")
            return Failure(MetaServiceError(f"Error getting meta record: {str(e)}"))

    async def add_attribute(
        self, meta_record_id: str, attribute_id: str
    ) -> Result[MetaRecord]:
        """
        Add an attribute to a meta record.

        Args:
            meta_record_id: The ID of the meta record
            attribute_id: The ID of the attribute to add

        Returns:
            Result containing the updated meta record
        """
        try:
            repository = cast(MetaRecordRepository, self.repository)
            meta_record = await repository.get(meta_record_id)

            if not meta_record:
                return Failure(
                    MetaServiceError(f"Meta record {meta_record_id} not found")
                )

            # Add the attribute
            meta_record.add_attribute(attribute_id)

            # Save the changes
            # In a real implementation, this would update the many-to-many relationship
            await repository.save(meta_record)

            return Success(meta_record)
        except Exception as e:
            self.logger.error(f"Error adding attribute to meta record: {e}")
            return Failure(MetaServiceError(f"Error adding attribute: {str(e)}"))
