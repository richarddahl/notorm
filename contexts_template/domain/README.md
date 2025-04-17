# Domain Layer

Pure business logic: Entities, Value Objects, Aggregates, Domain Events.
No external dependencies allowed in this layer.

Guidelines:
- Define aggregates with clear invariants.
- Keep models behavior-rich (avoid anemic models).
- Emit domain events for state changes.