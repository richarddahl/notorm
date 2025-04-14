"""
Specialized command handlers for the CQRS pattern in the Uno framework.

This module provides optimized command handlers for common command patterns,
supporting the command side of the CQRS pattern.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast, Protocol, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from uno.domain.cqrs import Command, CommandHandler, CommandResult, CommandStatus
from uno.domain.model import Entity, AggregateRoot
from uno.domain.repositories import Repository, AggregateRepository
from uno.domain.unit_of_work import UnitOfWork
from uno.domain.events import DomainEvent
from uno.domain.exceptions import UnoError, EntityNotFoundError, ValidationError


# Type variables
T = TypeVar('T')
EntityT = TypeVar('EntityT', bound=Entity)
AggregateT = TypeVar('AggregateT', bound=AggregateRoot)


class CreateEntityCommand(Command):
    """Command to create a new entity."""
    
    entity_data: Dict[str, Any]


class CreateEntityCommandHandler(CommandHandler[CreateEntityCommand, EntityT], Generic[EntityT]):
    """Handler for the CreateEntityCommand."""
    
    def __init__(
        self,
        entity_type: Type[EntityT],
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        repository_type: Type[Repository],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the create entity command handler.
        
        Args:
            entity_type: The type of entity to create
            unit_of_work_factory: Factory function that creates units of work
            repository_type: The type of repository to use
            logger: Optional logger instance
        """
        super().__init__(CreateEntityCommand, unit_of_work_factory, logger=logger)
        self.entity_type = entity_type
        self.repository_type = repository_type
    
    def validate(self, command: CreateEntityCommand) -> None:
        """
        Validate the create entity command.
        
        Args:
            command: The command to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Ensure entity_data contains all required fields
        required_fields = getattr(self.entity_type, "__dataclass_fields__", {})
        for field_name, field in required_fields.items():
            if field.default is None and field_name not in command.entity_data:
                raise ValidationError(f"Required field '{field_name}' is missing")
    
    async def _handle(self, command: CreateEntityCommand, uow: UnitOfWork) -> EntityT:
        """
        Handle the create entity command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            The created entity
        """
        # Get the repository
        repository = uow.get_repository(self.repository_type)
        
        # Create the entity
        entity = self.entity_type(**command.entity_data)
        
        # Store the entity
        created_entity = await repository.add(entity)
        
        return created_entity


class UpdateEntityCommand(Command):
    """Command to update an existing entity."""
    
    id: str
    entity_data: Dict[str, Any]


class UpdateEntityCommandHandler(CommandHandler[UpdateEntityCommand, EntityT], Generic[EntityT]):
    """Handler for the UpdateEntityCommand."""
    
    def __init__(
        self,
        entity_type: Type[EntityT],
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        repository_type: Type[Repository],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the update entity command handler.
        
        Args:
            entity_type: The type of entity to update
            unit_of_work_factory: Factory function that creates units of work
            repository_type: The type of repository to use
            logger: Optional logger instance
        """
        super().__init__(UpdateEntityCommand, unit_of_work_factory, logger=logger)
        self.entity_type = entity_type
        self.repository_type = repository_type
    
    async def _handle(self, command: UpdateEntityCommand, uow: UnitOfWork) -> EntityT:
        """
        Handle the update entity command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            The updated entity
        """
        # Get the repository
        repository = uow.get_repository(self.repository_type)
        
        # Get the existing entity
        entity = await repository.get_by_id(command.id)
        
        # Update the entity
        for key, value in command.entity_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        # Update the entity's timestamp
        if hasattr(entity, 'update') and callable(getattr(entity, 'update')):
            entity.update()
        
        # Save the updated entity
        updated_entity = await repository.update(entity)
        
        return updated_entity


class DeleteEntityCommand(Command):
    """Command to delete an entity."""
    
    id: str


class DeleteEntityCommandHandler(CommandHandler[DeleteEntityCommand, bool], Generic[EntityT]):
    """Handler for the DeleteEntityCommand."""
    
    def __init__(
        self,
        entity_type: Type[EntityT],
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        repository_type: Type[Repository],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the delete entity command handler.
        
        Args:
            entity_type: The type of entity to delete
            unit_of_work_factory: Factory function that creates units of work
            repository_type: The type of repository to use
            logger: Optional logger instance
        """
        super().__init__(DeleteEntityCommand, unit_of_work_factory, logger=logger)
        self.entity_type = entity_type
        self.repository_type = repository_type
    
    async def _handle(self, command: DeleteEntityCommand, uow: UnitOfWork) -> bool:
        """
        Handle the delete entity command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        # Get the repository
        repository = uow.get_repository(self.repository_type)
        
        # Delete the entity
        return await repository.remove_by_id(command.id)


class CreateAggregateCommand(Command):
    """Command to create a new aggregate."""
    
    aggregate_data: Dict[str, Any]


class CreateAggregateCommandHandler(CommandHandler[CreateAggregateCommand, AggregateT], Generic[AggregateT]):
    """Handler for the CreateAggregateCommand."""
    
    def __init__(
        self,
        aggregate_type: Type[AggregateT],
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        repository_type: Type[AggregateRepository],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the create aggregate command handler.
        
        Args:
            aggregate_type: The type of aggregate to create
            unit_of_work_factory: Factory function that creates units of work
            repository_type: The type of repository to use
            logger: Optional logger instance
        """
        super().__init__(CreateAggregateCommand, unit_of_work_factory, logger=logger)
        self.aggregate_type = aggregate_type
        self.repository_type = repository_type
    
    def validate(self, command: CreateAggregateCommand) -> None:
        """
        Validate the create aggregate command.
        
        Args:
            command: The command to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Ensure aggregate_data contains all required fields
        required_fields = getattr(self.aggregate_type, "__dataclass_fields__", {})
        for field_name, field in required_fields.items():
            if field.default is None and field_name not in command.aggregate_data:
                raise ValidationError(f"Required field '{field_name}' is missing")
    
    async def _handle(self, command: CreateAggregateCommand, uow: UnitOfWork) -> AggregateT:
        """
        Handle the create aggregate command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            The created aggregate
        """
        # Get the repository
        repository = uow.get_repository(self.repository_type)
        
        # Create the aggregate
        aggregate = self.aggregate_type(**command.aggregate_data)
        
        # Apply invariant checks and prepare for saving
        aggregate.apply_changes()
        
        # Save the aggregate
        created_aggregate = await repository.save(aggregate)
        
        return created_aggregate


class UpdateAggregateCommand(Command):
    """Command to update an existing aggregate."""
    
    id: str
    version: int
    aggregate_data: Dict[str, Any]


class UpdateAggregateCommandHandler(CommandHandler[UpdateAggregateCommand, AggregateT], Generic[AggregateT]):
    """Handler for the UpdateAggregateCommand."""
    
    def __init__(
        self,
        aggregate_type: Type[AggregateT],
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        repository_type: Type[AggregateRepository],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the update aggregate command handler.
        
        Args:
            aggregate_type: The type of aggregate to update
            unit_of_work_factory: Factory function that creates units of work
            repository_type: The type of repository to use
            logger: Optional logger instance
        """
        super().__init__(UpdateAggregateCommand, unit_of_work_factory, logger=logger)
        self.aggregate_type = aggregate_type
        self.repository_type = repository_type
    
    async def _handle(self, command: UpdateAggregateCommand, uow: UnitOfWork) -> AggregateT:
        """
        Handle the update aggregate command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            The updated aggregate
        """
        # Get the repository
        repository = uow.get_repository(self.repository_type)
        
        # Get the existing aggregate
        aggregate = await repository.get_by_id(command.id)
        
        # Check versioning for optimistic concurrency control
        if aggregate.version != command.version:
            raise UnoError(
                message=f"Aggregate version mismatch: expected {command.version}, but got {aggregate.version}",
                error_code="CONCURRENCY_ERROR"
            )
        
        # Update the aggregate
        for key, value in command.aggregate_data.items():
            if hasattr(aggregate, key):
                setattr(aggregate, key, value)
        
        # Apply invariant checks and prepare for saving
        aggregate.apply_changes()
        
        # Save the updated aggregate
        updated_aggregate = await repository.save(aggregate)
        
        return updated_aggregate


class DeleteAggregateCommand(Command):
    """Command to delete an aggregate."""
    
    id: str
    version: Optional[int] = None


class DeleteAggregateCommandHandler(CommandHandler[DeleteAggregateCommand, bool], Generic[AggregateT]):
    """Handler for the DeleteAggregateCommand."""
    
    def __init__(
        self,
        aggregate_type: Type[AggregateT],
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        repository_type: Type[AggregateRepository],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the delete aggregate command handler.
        
        Args:
            aggregate_type: The type of aggregate to delete
            unit_of_work_factory: Factory function that creates units of work
            repository_type: The type of repository to use
            logger: Optional logger instance
        """
        super().__init__(DeleteAggregateCommand, unit_of_work_factory, logger=logger)
        self.aggregate_type = aggregate_type
        self.repository_type = repository_type
    
    async def _handle(self, command: DeleteAggregateCommand, uow: UnitOfWork) -> bool:
        """
        Handle the delete aggregate command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            True if the aggregate was deleted, False otherwise
        """
        # Get the repository
        repository = uow.get_repository(self.repository_type)
        
        # If version is specified, check optimistic concurrency
        if command.version is not None:
            aggregate = await repository.get(command.id)
            if aggregate is None:
                return False
            
            if aggregate.version != command.version:
                raise UnoError(
                    message=f"Aggregate version mismatch: expected {command.version}, but got {aggregate.version}",
                    error_code="CONCURRENCY_ERROR"
                )
        
        # Delete the aggregate
        return await repository.remove_by_id(command.id)


class BatchCommandResult:
    """
    Result of a batch command execution.
    
    This class encapsulates the results of multiple command executions.
    """
    
    def __init__(self):
        """Initialize the batch command result."""
        self.results: List[CommandResult] = []
        self.success_count: int = 0
        self.failure_count: int = 0
    
    def add_result(self, result: CommandResult) -> None:
        """
        Add a command result to the batch.
        
        Args:
            result: The command result to add
        """
        self.results.append(result)
        if result.is_success:
            self.success_count += 1
        else:
            self.failure_count += 1
    
    @property
    def is_success(self) -> bool:
        """Check if all commands in the batch were successful."""
        return self.failure_count == 0
    
    @property
    def is_partial_success(self) -> bool:
        """Check if some commands in the batch were successful."""
        return self.success_count > 0 and self.failure_count > 0
    
    @property
    def is_failure(self) -> bool:
        """Check if all commands in the batch failed."""
        return self.success_count == 0 and self.failure_count > 0


class BatchCommand(Command):
    """
    Command to execute multiple commands in a batch.
    
    This command allows executing multiple commands within a single transaction.
    """
    
    commands: List[Command]
    all_or_nothing: bool = True


class BatchCommandHandler(CommandHandler[BatchCommand, BatchCommandResult]):
    """Handler for the BatchCommand."""
    
    def __init__(
        self,
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        dispatcher: Any,  # Dispatcher
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the batch command handler.
        
        Args:
            unit_of_work_factory: Factory function that creates units of work
            dispatcher: The dispatcher to use for individual commands
            logger: Optional logger instance
        """
        super().__init__(BatchCommand, unit_of_work_factory, logger=logger)
        self.dispatcher = dispatcher
    
    async def _handle(self, command: BatchCommand, uow: UnitOfWork) -> BatchCommandResult:
        """
        Handle the batch command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            The batch command result
        """
        result = BatchCommandResult()
        
        for cmd in command.commands:
            cmd_result = await self.dispatcher.dispatch_command(cmd)
            result.add_result(cmd_result)
            
            # If one command fails and all_or_nothing is True, abort the batch
            if command.all_or_nothing and cmd_result.is_failure:
                return result
        
        return result


class TransactionCommand(Command):
    """
    Command to execute a transaction with validation.
    
    This command validates all steps of a transaction before executing,
    ensuring atomicity and validating the entire transaction as a unit.
    """
    
    commands: List[Command]
    validation_commands: Optional[List[Command]] = None


class TransactionCommandHandler(CommandHandler[TransactionCommand, List[CommandResult]]):
    """Handler for the TransactionCommand."""
    
    def __init__(
        self,
        unit_of_work_factory: Any,  # Callable[[], UnitOfWork]
        dispatcher: Any,  # Dispatcher
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the transaction command handler.
        
        Args:
            unit_of_work_factory: Factory function that creates units of work
            dispatcher: The dispatcher to use for commands
            logger: Optional logger instance
        """
        super().__init__(TransactionCommand, unit_of_work_factory, logger=logger)
        self.dispatcher = dispatcher
    
    async def _handle(self, command: TransactionCommand, uow: UnitOfWork) -> List[CommandResult]:
        """
        Handle the transaction command.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            List of command results
        """
        # First validate the entire transaction
        if command.validation_commands:
            for validation_cmd in command.validation_commands:
                result = await self.dispatcher.dispatch_command(validation_cmd)
                if result.is_failure:
                    return [result]
        
        # Execute all commands in the transaction
        results = []
        for cmd in command.commands:
            result = await self.dispatcher.dispatch_command(cmd)
            results.append(result)
            
            # If one command fails, abort the transaction
            if result.is_failure:
                return results
        
        return results


# Register a command handler function decorator
def command_handler(command_type: Type[Command], unit_of_work_factory: Any, logger: Optional[logging.Logger] = None):
    """
    Decorator to create a command handler from a function.
    
    This decorator creates a command handler from a function, making it
    easier to create simple command handlers without defining a class.
    
    Args:
        command_type: The type of command this handler can process
        unit_of_work_factory: Factory function that creates units of work
        logger: Optional logger instance
        
    Returns:
        A command handler
    """
    
    def decorator(func):
        class FunctionCommandHandler(CommandHandler[Command, Any]):
            def __init__(self):
                super().__init__(command_type, unit_of_work_factory, logger=logger)
            
            async def _handle(self, command: Command, uow: UnitOfWork) -> Any:
                return await func(command, uow)
        
        return FunctionCommandHandler()
    
    return decorator


# Custom validation tools for commands
class Validator:
    """Utilities for command validation."""
    
    @staticmethod
    def required(data: Dict[str, Any], *fields: str) -> None:
        """
        Check that all required fields are present.
        
        Args:
            data: The data to validate
            *fields: The required fields
            
        Raises:
            ValidationError: If any required field is missing
        """
        for field in fields:
            if field not in data or data[field] is None:
                raise ValidationError(f"Required field '{field}' is missing")
    
    @staticmethod
    def min_length(value: str, min_length: int, field_name: str) -> None:
        """
        Check that a string field has at least the minimum length.
        
        Args:
            value: The string to validate
            min_length: The minimum allowed length
            field_name: The name of the field
            
        Raises:
            ValidationError: If the string is too short
        """
        if value is None:
            return
        
        if len(value) < min_length:
            raise ValidationError(
                f"Field '{field_name}' must be at least {min_length} characters long"
            )
    
    @staticmethod
    def max_length(value: str, max_length: int, field_name: str) -> None:
        """
        Check that a string field doesn't exceed the maximum length.
        
        Args:
            value: The string to validate
            max_length: The maximum allowed length
            field_name: The name of the field
            
        Raises:
            ValidationError: If the string is too long
        """
        if value is None:
            return
        
        if len(value) > max_length:
            raise ValidationError(
                f"Field '{field_name}' must be at most {max_length} characters long"
            )
    
    @staticmethod
    def range(value: Union[int, float], min_value: Union[int, float], max_value: Union[int, float], field_name: str) -> None:
        """
        Check that a numeric field is within the specified range.
        
        Args:
            value: The number to validate
            min_value: The minimum allowed value
            max_value: The maximum allowed value
            field_name: The name of the field
            
        Raises:
            ValidationError: If the number is out of range
        """
        if value is None:
            return
        
        if value < min_value or value > max_value:
            raise ValidationError(
                f"Field '{field_name}' must be between {min_value} and {max_value}"
            )