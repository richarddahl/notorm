# Event System Cleanup

This document details the cleanup of legacy event system code as part of the architectural modernization plan for the UNO framework.

## Overview

As part of Phase 1 of the implementation plan, we've removed all legacy, inconsistent, and partially implemented event bus code throughout the codebase. The legacy event system was scattered across multiple locations with inconsistent interfaces and implementations.

## Actions Taken

1. **Removed Legacy Code:**
   - Removed the entire `/src/uno/events/` directory including:
     - `core/bus.py`, `core/event.py`, `core/handler.py`, `core/store.py`, `core/publisher.py`
     - `adapters/postgres.py`, `adapters/redis.py`
     - `sourcing/aggregate.py`, `sourcing/repository.py`
     - `examples/` and `testing/` directories
   - Removed domain-specific implementations:
     - `src/uno/domain/vector_events.py`
     - `src/uno/domain/vector_events_example.py`
     - `src/uno/domain/vector_update_service.py`

2. **Created Backward Compatibility Layer:**
   - Implemented a compatibility module in `src/uno/domain/event_import_fix.py`
   - Provided transitional implementations for:
     - `EventDispatcher` → forwards to `AsyncEventBus`
     - `domain_event_handler` → deprecation warning + passthrough
     - `EventHandler` and `EventSubscriber` base classes → deprecation warnings

3. **Updated Import References:**
   - Updated `/src/uno/domain/index.py` to import from the new system
   - Added deprecation warnings for legacy imports
   - Maintained API compatibility while encouraging migration

4. **Fixed Example Code:**
   - Updated workflow examples to use the new event system
   - Changed `UnoEvent` references to `Event` from the core system
   - Added compatibility with the transitional layer

## New Event System Structure

The new event system is implemented under `/src/uno/core/events/` and follows a clean, modular architecture:

1. **Core Components:**
   - `Event`: Base class for all domain events (immutable, with metadata)
   - `AsyncEventBus`: Implementation of `EventBusProtocol`
   - `EventStore`: Interface for event persistence
   - `InMemoryEventStore`: In-memory implementation of `EventStore`
   - `EventPublisher`: High-level interface for publishing events

2. **Protocol Definitions:**
   - All interfaces defined in `/src/uno/core/protocols/event.py`
   - Clear separation between interfaces and implementations
   - Type-safe with proper generics and type hints

## Migration Path

For existing code that uses the legacy event system, we provide a smooth migration path:

1. **Immediate Changes:**
   - Continue using existing imports (via compatibility layer)
   - Observe deprecation warnings that indicate needed changes

2. **Recommended Updates:**
   - Migrate from `UnoEvent` to `Event` from `uno.core.events`
   - Replace `EventDispatcher` with `AsyncEventBus`
   - Use function-based event handlers instead of class-based ones
   - Update event registration to use the new async API

3. **Long-term Plan:**
   - Phase 5 will completely remove the compatibility layer
   - All code should directly use the new API by then

## Benefits

This cleanup provides numerous benefits:

1. **Simplified Mental Model:** Single, canonical implementation of the event system
2. **Improved Type Safety:** Comprehensive type hints and protocol validation
3. **Better Async Support:** Proper async/await patterns throughout
4. **Reduced Code Duplication:** Eliminated multiple implementations of similar functionality
5. **Clear Migration Path:** Deprecation warnings and compatibility layer for smooth transition

## Next Steps

With the event system cleanup complete, work will continue on:

1. Finishing the Protocol Testing framework 
2. Implementing the Unit of Work pattern
3. Adding a PostgreSQL implementation of the EventStore
4. Improving documentation and examples using the new event system