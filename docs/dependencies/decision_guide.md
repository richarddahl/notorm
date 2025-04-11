# Decision Guide: UnoObj vs Dependency Injection

This guide helps you decide which architectural pattern to use for different parts of your application.

With Uno's new unified database architecture, both patterns can share the same database layer components, making the decision less about technical constraints and more about application design considerations.

## Quick Decision Table

| Factor | UnoObj Pattern | Dependency Injection |
|--------|---------------|----------------------|
| Complexity | Simple CRUD | Complex business logic |
| Development speed | Faster | More setup required |
| Testability | Limited | Excellent |
| Control over queries | Standard queries | Custom queries |
| Team size | Small teams | Larger teams |
| Maintenance needs | Lower | Higher |

## Detailed Decision Factors

### Complexity of Domain

**Use UnoObj when:**
- The domain is simple with straightforward rules
- Standard CRUD operations are sufficient
- Minimal custom business logic is required

**Use Dependency Injection when:**
- Complex business rules exist
- Multiple validation steps are needed
- Orchestration across different domains is required
- Custom workflows go beyond CRUD

### Query Requirements

**Use UnoObj when:**
- Standard filters and sorting are sufficient
- Basic relationships need to be loaded
- Performance is not critical

**Use Dependency Injection when:**
- Complex queries with specific optimizations are needed
- Custom SQL or database-specific features are required
- Performance-critical operations need fine-tuning
- Aggregations and analytics require specialized queries

### Testing Needs

**Use UnoObj when:**
- Basic integration tests are sufficient
- Business logic is simple enough to test as a whole
- Mocking is not a primary concern

**Use Dependency Injection when:**
- Unit tests with mock dependencies are important
- Complex business logic needs isolated testing
- Test coverage of specific edge cases is required
- Test-driven development is practiced

### Team Factors

**Use UnoObj when:**
- Small teams with shared understanding
- Rapid prototyping is prioritized
- Less experienced developers need guardrails

**Use Dependency Injection when:**
- Larger teams with specialized roles
- Multiple developers work on the same domain
- Clear contract boundaries between components are needed
- Experienced developers who value explicit patterns

### Future Maintenance

**Use UnoObj when:**
- Future changes are likely to be minor
- Feature set is relatively stable
- Domain is well-understood and unlikely to evolve dramatically

**Use Dependency Injection when:**
- Significant future changes are anticipated
- Long-term maintenance is a priority
- Domain is still evolving and may require restructuring
- Need to adapt to changing requirements over time

## Real-World Examples

### User Authentication (DI Pattern)

Authentication typically involves:
- Complex password validation
- Integration with external services
- Security considerations
- Token management
- Session tracking

These requirements make it a good candidate for the dependency injection pattern.

### Simple Content Management (UnoObj Pattern)

Basic content management with:
- Standard CRUD for articles/pages
- Basic metadata handling
- Simple permissions

This could be effectively implemented with the UnoObj pattern.

### Order Processing (Hybrid Approach)

Order processing might use:
- UnoObj for simple order entities
- DI for complex pricing engines
- DI for payment processing
- UnoObj for order status tracking

This mixed approach leverages the strengths of both patterns.

## Unified Database Architecture

Uno's new database architecture provides a foundation that works with both patterns:

| Component | UnoObj Integration | Dependency Injection Integration |
|-----------|-------------------|--------------------------------|
| DatabaseProvider | Access through helper methods | Access through DI container |
| UnoBaseRepository | Use as foundation for UnoObj data access | Use directly with DI |
| SchemaManager | Use for schema generation | Use for DDL operations |

### When to Use DatabaseProvider Directly

**Use with UnoObj when:**
- Custom connection handling is needed
- Transaction management across multiple operations
- Advanced session configuration

**Use with Dependency Injection when:**
- Custom repositories need direct database access
- Services need to control transaction boundaries
- Performance-critical operations need connection pooling

### When to Use UnoBaseRepository

**Use with UnoObj when:**
- Extending UnoObj with repository features
- Adding custom queries to UnoObj
- Bridging between UnoObj and repository pattern

**Use with Dependency Injection when:**
- Implementing the repository pattern
- Creating testable data access layers
- Defining clear domain boundaries

### When to Use SchemaManager

**Use with UnoObj when:**
- Generating schema from UnoObj models
- Schema verification before operations
- Custom DDL operations

**Use with Dependency Injection when:**
- Scripted schema management
- Database migrations
- Schema validation in services

## Transitioning Between Patterns

With the unified database architecture, transitioning between patterns is smoother:

1. Start by integrating the new DatabaseProvider
2. Begin with UnoObj for initial CRUD leveraging the provider
3. Identify components that grow complex
4. Create UnoBaseRepository implementations for those components
5. Add services that use these repositories
6. Gradually transition endpoints to use the new components
7. Maintain UnoObj for parts that remain simple

This evolutionary approach allows you to balance development speed with architectural needs while maintaining a consistent database layer.

## Conclusion

Both patterns have their place in a well-designed application. The key is choosing the right pattern for each specific component based on its requirements, complexity, and future maintenance needs.

With Uno's unified database architecture, you can make these decisions based on application design considerations rather than technical limitations. The shared database layer makes it possible to combine both patterns effectively and evolve your application over time.

When in doubt:
- Default to UnoObj for simpler domains to gain development speed
- Adopt dependency injection where complexity, testing, or maintenance justify the additional structure
- Use the unified database architecture components regardless of your pattern choice
- Consider a hybrid approach for complex applications

The most successful Uno applications often use UnoObj for rapid development of CRUD features and dependency injection for complex business logic, all built on the foundation of the unified database architecture.