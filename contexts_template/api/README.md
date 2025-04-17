# API Layer

Controllers, REST/gRPC endpoints, or CLI entry points.
Depends on the application layer only.

Guidelines:
- Expose use cases via HTTP, gRPC, or CLI.
- Validate request data and map to commands.
- Handle responses and map errors appropriately.