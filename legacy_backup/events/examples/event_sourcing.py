"""
Event sourcing example for the Uno event system.

This module demonstrates how to use the event sourcing capabilities
of the Uno event system to build and persist domain entities.
"""

import asyncio
from datetime import datetime, UTC
from typing import List, Optional

from pydantic import Field

from uno.events import Event
from uno.events.core.bus import EventBus
from uno.events.core.publisher import EventPublisher
from uno.events.core.store import InMemoryEventStore
from uno.events.sourcing import AggregateRoot, EventSourcedRepository, apply_event


# 1. Define domain events
class TodoItemCreated(Event):
    """Event emitted when a todo item is created."""
    
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: bool = False


class TodoItemUpdated(Event):
    """Event emitted when a todo item is updated."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class TodoItemCompleted(Event):
    """Event emitted when a todo item is marked as completed."""
    
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TodoItemDeleted(Event):
    """Event emitted when a todo item is deleted."""
    
    reason: Optional[str] = None


# 2. Define an aggregate root
class TodoItem(AggregateRoot):
    """A todo item aggregate root."""
    
    def __init__(self, id: Optional[str] = None):
        """Initialize the todo item."""
        super().__init__(id)
        self.title: Optional[str] = None
        self.description: Optional[str] = None
        self.due_date: Optional[datetime] = None
        self.is_completed: bool = False
        self.completed_at: Optional[datetime] = None
        self.is_deleted: bool = False
        self.deletion_reason: Optional[str] = None
    
    def create(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> None:
        """
        Create a new todo item.
        
        Args:
            title: The title of the todo item
            description: Optional description
            due_date: Optional due date
        """
        event = TodoItemCreated(
            title=title,
            description=description,
            due_date=due_date,
        )
        self.apply(event)
    
    def update(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> None:
        """
        Update the todo item.
        
        Args:
            title: Optional new title
            description: Optional new description
            due_date: Optional new due date
        """
        if self.is_deleted:
            raise ValueError("Cannot update a deleted todo item")
        
        event = TodoItemUpdated(
            title=title,
            description=description,
            due_date=due_date,
        )
        self.apply(event)
    
    def complete(self) -> None:
        """Mark the todo item as completed."""
        if self.is_deleted:
            raise ValueError("Cannot complete a deleted todo item")
        
        if self.is_completed:
            return  # Already completed
        
        event = TodoItemCompleted()
        self.apply(event)
    
    def delete(self, reason: Optional[str] = None) -> None:
        """
        Delete the todo item.
        
        Args:
            reason: Optional reason for deletion
        """
        if self.is_deleted:
            return  # Already deleted
        
        event = TodoItemDeleted(reason=reason)
        self.apply(event)
    
    @apply_event
    def apply_todo_item_created(self, event: TodoItemCreated) -> None:
        """Apply the TodoItemCreated event."""
        self.title = event.title
        self.description = event.description
        self.due_date = event.due_date
        self.is_completed = event.is_completed
    
    @apply_event
    def apply_todo_item_updated(self, event: TodoItemUpdated) -> None:
        """Apply the TodoItemUpdated event."""
        if event.title is not None:
            self.title = event.title
        
        if event.description is not None:
            self.description = event.description
        
        if event.due_date is not None:
            self.due_date = event.due_date
    
    @apply_event
    def apply_todo_item_completed(self, event: TodoItemCompleted) -> None:
        """Apply the TodoItemCompleted event."""
        self.is_completed = True
        self.completed_at = event.completed_at
    
    @apply_event
    def apply_todo_item_deleted(self, event: TodoItemDeleted) -> None:
        """Apply the TodoItemDeleted event."""
        self.is_deleted = True
        self.deletion_reason = event.reason


async def run_example() -> None:
    """Run the event sourcing example."""
    # Create event store and repository
    event_store = InMemoryEventStore()
    repository = EventSourcedRepository(TodoItem, event_store)
    
    # Create a new todo item
    todo = TodoItem()
    todo.create(
        title="Learn event sourcing",
        description="Study event sourcing with Uno",
        due_date=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    
    # Save the todo item
    await repository.save(todo)
    
    print(f"Created Todo: {todo.title}")
    print(f"Description: {todo.description}")
    print(f"Due date: {todo.due_date}")
    print(f"Is completed: {todo.is_completed}")
    
    # Find the todo item by ID
    todo_id = todo.id
    found_todo = await repository.find_by_id(todo_id)
    
    if found_todo:
        print("\nFound Todo by ID:")
        print(f"Title: {found_todo.title}")
        print(f"Description: {found_todo.description}")
        
        # Update the todo item
        found_todo.update(description="Master event sourcing with Uno")
        found_todo.complete()
        
        # Save the changes
        await repository.save(found_todo)
        
        print("\nAfter update:")
        print(f"Description: {found_todo.description}")
        print(f"Is completed: {found_todo.is_completed}")
        print(f"Completed at: {found_todo.completed_at}")
        
        # Get all events for this aggregate
        events = await event_store.get_events_by_aggregate_id(todo_id)
        
        print("\nEvent history:")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event.type} at {event.timestamp}")
        
        # Delete the todo item
        found_todo.delete(reason="No longer needed")
        await repository.save(found_todo)
        
        print("\nAfter deletion:")
        print(f"Is deleted: {found_todo.is_deleted}")
        print(f"Deletion reason: {found_todo.deletion_reason}")
    else:
        print(f"Todo with ID {todo_id} not found")


if __name__ == "__main__":
    asyncio.run(run_example())