# Uno Offline Module

The Offline module provides capabilities for offline operation, data synchronization, conflict resolution, and progressive enhancement in Uno applications.

## Components

### Store

The Store component provides a local storage mechanism for offline data:

- `store.py`: Core storage interface
- `transaction.py`: Manages offline transactions
- `schema.py`: Defines the schema for offline data
- `query.py`: Query capabilities for offline data
- `options.py`: Configuration options for the store

### Sync

The Sync component handles synchronization between offline and online data:

- `engine.py`: Core synchronization engine
- `adapter.py`: Interface for sync adapters
- `conflict.py`: Conflict detection and resolution
- `tracker.py`: Tracks changes for sync
- `errors.py`: Sync-specific error definitions

### Progressive Enhancement

The Progressive component provides capabilities for progressive web applications:

- `detector.py`: Detects network connectivity
- `enhancer.py`: Enhances app functionality based on connectivity
- `strategies.py`: Strategies for progressive enhancement
- `config.py`: Configuration for progressive enhancement

## Usage

See the documentation at `/docs/offline/overview.md` for detailed usage instructions.