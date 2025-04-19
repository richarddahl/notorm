# Uno Framework Documentation

Welcome to the Uno Framework documentation! 

## What is Uno?

Uno (Uno is Not an ORM) is a modern Python framework that integrates SQLAlchemy, Pydantic, and FastAPI with PostgreSQL 16. It's designed to leverage the power of PostgreSQL's advanced features while providing a clean, domain-driven design architecture for building robust applications.

Key features:
- **Domain-Driven Design**: Clear separation of domain logic from infrastructure
- **Event-Driven Architecture**: Built-in event system for decoupled communication
- **PostgreSQL Integration**: Offloads work to the database with custom SQL functions and triggers
- **Apache AGE Integration**: Duplicates relational data into a knowledge graph for advanced querying
- **Async-First**: Modern async/await patterns throughout
- **Type-Safe**: Comprehensive type hints and validation with Pydantic v2
- **Protocol-Based**: Flexible contracts using Python's Protocol typing

## Getting Started

- [Installation and Setup](getting_started.md): Get Uno running in your environment
- [Tutorial](tutorial/index.md): Build your first application with Uno
- [Core Concepts](architecture/overview.md): Learn the key architectural concepts

## Why Uno?

Uno addresses common challenges in modern application development:

1. **Complex Domain Logic**: Use DDD principles to manage complexity
2. **Performance**: Leverage PostgreSQL for optimal data processing
3. **Scalability**: Distributed systems support built-in
4. **Maintainability**: Clean architecture with clear boundaries
5. **Advanced Queries**: Knowledge graph integration for complex queries and RAG

## Core Components

- [Domain Layer](domain/guide.md): Business entities and logic
- [Application Layer](application/overview.md): Use cases and orchestration
- [API Layer](api/overview.md): HTTP endpoints and interfaces
- [Infrastructure Layer](database/overview.md): Technical implementations

## Key Patterns

- [Repository Pattern](domain/repository_pattern.md): Data access abstraction
- [Unit of Work](core/uow/index.md): Transaction management
- [CQRS](architecture/cqrs.md): Command Query Responsibility Segregation
- [Event Sourcing](core/events/index.md): Event-based state management
- [Specification Pattern](domain/specification_pattern.md): Query criteria encapsulation

## Community

- [Contributing](contributing.md): Help improve Uno
- [FAQ](faq.md): Frequently asked questions
- [Roadmap](roadmap.md): Future development plans

## License

Uno is open source under the [MIT License](license.md)