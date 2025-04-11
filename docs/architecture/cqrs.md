# Command Query Responsibility Segregation (CQRS)

The Uno framework implements the Command Query Responsibility Segregation (CQRS) pattern to separate the read and write operations, allowing each to be optimized independently.

## Overview

CQRS stands for Command Query Responsibility Segregation. It's a pattern that separates read and write operations for a data store. In this pattern:

- **Commands** change the state of the system but don't return data
- **Queries** return data but don't change the state of the system

This separation allows each side to be optimized independently, which is particularly valuable in complex domains.

## Implementation

The Uno framework implements CQRS with the following components:

### Command Side

The command side handles state changes in the system through commands.

#### Command

A command represents an intent to change the system state. It is immutable and named with an imperative verb.

```python
class CreateUserCommand(Command):
    username: str
    email: str
    password: str
```

#### Command Handler

Command handlers process commands and execute the business logic that changes the system state.

```python
class CreateUserCommandHandler(CommandHandler[CreateUserCommand, User]):
    async def _handle(self, command: CreateUserCommand, uow: UnitOfWork) -> User:
        # Business logic to create a user
        repository = uow.get_repository(UserRepository)
        user = User(
            username=command.username,
            email=command.email,
            password=hash_password(command.password)
        )
        return await repository.add(user)
```

#### Command Result

Commands return standardized results that indicate success or failure and contain any relevant output data.

```python
# Example of a command execution
result = await dispatcher.dispatch_command(CreateUserCommand(
    username="johndoe",
    email="john@example.com",
    password="secure_password"
))

if result.is_success:
    print(f"User created with ID: {result.output.id}")
else:
    print(f"Error: {result.error}")
```

### Query Side

The query side handles read operations that don't change the system state.

#### Query

A query represents a request for information. It is immutable and typically named with a noun.

```python
class GetUserByIdQuery(Query[User]):
    id: str
```

#### Query Handler

Query handlers process queries and retrieve information without changing the system state.

```python
class GetUserByIdQueryHandler(QueryHandler[GetUserByIdQuery, Optional[User]]):
    async def _handle(self, query: GetUserByIdQuery) -> Optional[User]:
        # Business logic to get a user
        repository = self.repository
        return await repository.get(query.id)
```

#### Query Result

Queries return standardized results that contain the requested information or error details.

```python
# Example of a query execution
result = await dispatcher.dispatch_query(GetUserByIdQuery(id="user123"))

if result.is_success:
    if result.output:
        print(f"Found user: {result.output.username}")
    else:
        print("User not found")
else:
    print(f"Error: {result.error}")
```

### Specialized Implementations

#### SQL-Based Query Handlers

For performance-critical read operations, the Uno framework provides SQL-based query handlers that bypass the domain model and execute optimized SQL queries directly.

```python
class GetUserStatsQueryHandler(SqlQueryHandler[GetUserStatsQuery, UserStats, UserModel]):
    def build_query(self, query: GetUserStatsQuery) -> Select:
        return select(
            self.model_class.id,
            func.count(self.model_class.posts).label("post_count"),
            func.avg(self.model_class.posts.likes).label("avg_likes")
        ).where(self.model_class.id == query.user_id)
    
    def map_result(self, result: Any) -> UserStats:
        row = result.first()
        return UserStats(
            user_id=row.id,
            post_count=row.post_count,
            average_likes=row.avg_likes
        )
```

#### Pagination Support

The Uno framework includes built-in support for pagination, making it easy to work with large result sets.

```python
class GetUsersQuery(PaginatedQuery[User]):
    search_term: Optional[str] = None

class GetUsersQueryHandler(PaginatedEntityQueryHandler[User]):
    async def _handle(self, query: GetUsersQuery) -> PaginatedResult[User]:
        # Additional filtering based on search term
        filters = {}
        if query.search_term:
            filters["username"] = {"$like": f"%{query.search_term}%"}
        
        # The base class handles pagination automatically
        return await super()._handle(
            PaginatedEntityQuery(
                page=query.page,
                page_size=query.page_size,
                filters=filters,
                order_by=["username"]
            )
        )
```

#### Specialized Command Handlers

The command side also includes specialized handlers for common operations such as:

- Creating entities and aggregates
- Updating entities and aggregates with optimistic concurrency control
- Deleting entities and aggregates
- Batch operations
- Transactional operations with validation

## Benefits

The CQRS pattern in the Uno framework provides several benefits:

1. **Separation of concerns**: Read and write logic can be developed, optimized, and scaled independently.
2. **Performance optimization**: Queries can be optimized for read performance without compromising the domain model's integrity.
3. **Scalability**: Read and write sides can be scaled independently based on their different usage patterns.
4. **Security**: Command and query models can have different security requirements and implementations.
5. **Complexity management**: Complex domain logic can be isolated in command handlers while keeping query handlers simple and focused.

## Integration with Other Patterns

CQRS in the Uno framework integrates seamlessly with other architectural patterns:

- **Domain-Driven Design (DDD)**: Commands typically interact with the domain model, preserving business rules and invariants.
- **Event-Driven Architecture**: Commands can publish domain events that trigger further actions in the system.
- **Unit of Work**: Commands execute within a unit of work to ensure transaction integrity.
- **Repository Pattern**: Both commands and queries use repositories to access data, but in different ways.

## Example Usage

### Registering Handlers

```python
# Register command handlers
dispatcher = get_dispatcher()
dispatcher.register_command_handler(CreateUserCommandHandler(
    command_type=CreateUserCommand,
    unit_of_work_factory=lambda: SqlAlchemyUnitOfWork(session_factory)
))

# Register query handlers
dispatcher.register_query_handler(GetUserByIdQueryHandler(
    query_type=GetUserByIdQuery,
    repository=user_repository
))
```

### Using Commands and Queries

```python
# Execute a command
create_result = await dispatcher.dispatch_command(CreateUserCommand(
    username="johndoe",
    email="john@example.com", 
    password="secure_password"
))

if create_result.is_success:
    # Execute a query
    get_result = await dispatcher.dispatch_query(GetUserByIdQuery(
        id=create_result.output.id
    ))
    
    if get_result.is_success:
        print(f"Created and retrieved user: {get_result.output.username}")
```

## Best Practices

1. **Command validation**: Validate commands before executing them to catch errors early.
2. **Optimistic concurrency**: Use versioning for aggregate updates to prevent concurrency conflicts.
3. **Idempotent commands**: Design commands to be idempotent when possible to support retries.
4. **Read models**: Consider creating specialized read models optimized for specific query use cases.
5. **Security**: Implement appropriate authorization checks in both command and query handlers.
6. **Error handling**: Use standardized error codes and messages for consistency.

## Conclusion

The CQRS pattern in the Uno framework provides a powerful way to separate read and write operations, allowing each to be optimized independently while maintaining a clean, maintainable architecture. By combining CQRS with other patterns like DDD and event-driven architecture, the Uno framework offers a comprehensive solution for building complex, high-performance applications.