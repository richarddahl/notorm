# Bounded Contexts in the uno Framework

Bounded Contexts are a central pattern in Domain-Driven Design. They provide explicit boundaries around domain models, establishing where specific models, terms, and rules apply.

## What is a Bounded Context?

A Bounded Context is a logical boundary within which a particular domain model is defined and applicable. It encapsulates the domain model, including:

- A consistent ubiquitous language for that context
- A set of domain entities, aggregates, and value objects
- Business rules and invariants specific to that context
- A well-defined interface for interacting with other contexts

## Benefits of Bounded Contexts

- **Clarity**: Each context has a clear responsibility and meaning
- **Independence**: Teams can work on different contexts independently
- **Flexibility**: Different technical approaches can be used in different contexts
- **Evolution**: Contexts can evolve at different rates
- **Integration**: Explicit interfaces between contexts make integration cleaner

## uno Framework Bounded Contexts

The uno framework is organized into several bounded contexts, each with its own responsibility and domain model:

### Core Domain Contexts

1. **Domain Model Context**
   - **Responsibility**: Fundamental domain model patterns and abstractions
   - **Key Components**: Entity, AggregateRoot, ValueObject, DomainEvent
   - **Bounded By**: Core domain interfaces and abstractions

2. **Database Context**
   - **Responsibility**: Database access and persistence
   - **Key Components**: UnoDBRepository, DatabaseSession, UnitOfWork
   - **Bounded By**: Persistence infrastructure concerns

3. **Schema Context**
   - **Responsibility**: Schema definition and validation
   - **Key Components**: UnoSchemaManager, SchemaFactory, ValidationRules
   - **Bounded By**: Data validation and schema evolution

4. **Authorization Context**
   - **Responsibility**: Access control and security
   - **Key Components**: AuthorizationService, PermissionModel, SecurityPolicy
   - **Bounded By**: Security and access control concerns

### Supporting Contexts

5. **API Context**
   - **Responsibility**: API definition and exposure
   - **Key Components**: EndpointFactory, APIDefinition, APISchema
   - **Bounded By**: API structure and HTTP communication

6. **Query Context**
   - **Responsibility**: Query generation and execution
   - **Key Components**: FilterManager, QueryBuilder, SearchService
   - **Bounded By**: Query language and search capabilities

7. **SQL Generation Context**
   - **Responsibility**: SQL statement generation
   - **Key Components**: SQLEmitter, StatementBuilder, SQLRegistry
   - **Bounded By**: SQL dialect and database-specific features

8. **Meta Context**
   - **Responsibility**: Metadata and introspection
   - **Key Components**: MetaType, MetaRecord, MetaObject
   - **Bounded By**: System metadata and type introspection

## Context Map

The Context Map illustrates how different bounded contexts relate to each other:

``````
```

                     +----------------+
                     |                |
               +---->|  API Context   |
               |     |                |
               |     +----------------+
               |              ^
               |              |
```
```
+----------------+     |     +----------------+     +----------------+
|                |     |     |                |     |                |
| Domain Model   +-----------> Authorization  +---->+  Meta Context  |
|   Context      |     |     |   Context      |     |                |
|                |     |     |                |     +----------------+
+----------------+     |     +----------------+```
```

^              |              ^
|              |              |
|              |     +----------------+
|              |     |                |
|              +---->+  Query Context |
|                    |                |
|                    +----------------+
|                              ^
|                              |
```
```
+----------------+           +----------------+
|                |           |                |
| Schema Context +---------->+ SQL Generation |
|                |           |    Context     |
+----------------+           |                |```
```

^                    +----------------+
|                              ^
|                              |
```
```
+----------------+           +----------------+
|                |           |                |
|    Database    +---------->+  Database     |
|     Context    |           |   Context     |
+----------------+           +----------------+
```

## Context Relationships

### Types of Relationships

1. **Upstream-Downstream (Customer-Supplier)**: One context (upstream) provides services that another (downstream) depends on

2. **Shared Kernel**: Two contexts share a subset of the domain model

3. **Conformist**: One context conforms to the model of another without translation

4. **Anti-Corruption Layer**: One context protects itself from changes in another by introducing a translation layer

5. **Open Host Service**: One context provides a well-defined API for integration

6. **Separate Ways**: Contexts are separated with minimal integration

### Key Relationships in uno Framework

- **Domain Model ⟶ Database**: Upstream-Downstream
  - Domain Model is upstream, defining the core entities and concepts
  - Database Context is downstream, implementing persistence for these entities

- **Authorization ⟶ Meta Context**: Open Host Service
  - Authorization Context exposes well-defined interfaces for authorization queries
  - Meta Context uses these interfaces to integrate authorization into metadata services

- **Domain Model ⟶ Schema**: Shared Kernel
  - These contexts share core domain concepts, with Schema adding validation capabilities

- **Query ⟶ SQL Generation**: Anti-Corruption Layer
  - Query Context uses an anti-corruption layer to translate domain queries into SQL
  - This protects the Query Context from SQL dialect variations

## Implementation in uno Framework

### Context Organization

Each bounded context in uno is organized into its own package structure:

```
uno/
├── api/              # API Context
├── authorization/    # Authorization Context
├── database/         # Database Context
├── domain/           # Domain Model Context
├── meta/             # Meta Context
├── queries/          # Query Context
├── schema/           # Schema Context
└── sql/              # SQL Generation Context
```

### Context Registration

Bounded contexts are registered using the `BoundedContext` class:

```python
from uno.domain.bounded_context import BoundedContext, register_bounded_context

# Define a bounded context
context = BoundedContext(```

name="domain_model",
package_path="uno.domain",
description="Core domain model components",
responsibility="Define fundamental domain patterns and abstractions",
is_core_domain=True
```
)

# Add ubiquitous language terms
context.add_term("Entity", "An object defined by its identity that has continuity and identity separate from its attributes")
context.add_term("AggregateRoot", "The entry point to an aggregate, ensuring consistency across all entities within the aggregate")
context.add_term("ValueObject", "An immutable object that has no identity and is defined only by its attributes")

# Register the context
register_bounded_context(context)
```

### Context Boundaries

Each context defines clear boundaries through:

1. **Context-Specific Interfaces**: Public interfaces that define how the context is used
2. **Anti-Corruption Layers**: Translation layers between incompatible contexts
3. **Domain Events**: For loose coupling between contexts

### Context Integration

Contexts integrate through:

1. **Domain Events**: For asynchronous communication
2. **Protocol Interfaces**: For synchronous integration
3. **Explicit Dependencies**: Using dependency injection
4. **Context Maps**: Documenting relationships between contexts

## Best Practices

1. **Keep Contexts Focused**: Each context should have a clear responsibility and boundary
2. **Respect Context Boundaries**: Don't bypass context interfaces
3. **Document the Ubiquitous Language**: Each context should have a glossary
4. **Use Integration Patterns**: Choose appropriate patterns for context integration
5. **Evolve Contexts Independently**: Each context should be able to evolve at its own pace
6. **Strategically Size Contexts**: Not too large (unfocused), not too small (complex integration)

## Migrating Toward Bounded Contexts

For existing code, migration to bounded contexts is a gradual process:

1. **Identify Existing Contexts**: Map out implicit contexts in the codebase
2. **Define Context Boundaries**: Draw explicit boundaries around contexts
3. **Establish Context Interfaces**: Define clean interfaces between contexts
4. **Implement Anti-Corruption Layers**: Where needed to translate between contexts
5. **Refactor Incrementally**: Move code to appropriate contexts gradually

## Future Enhancements

1. **Context Visualization**: Generate context map diagrams
2. **Context Metrics**: Measure coupling between contexts
3. **Context Governance**: Tools for managing context evolution
4. **Context Documentation**: Automated documentation generation
5. **Context Testing**: Boundary-focused integration tests