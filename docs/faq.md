# Frequently Asked Questions

## General Questions

### What is uno?

uno is a comprehensive application framework for building data-driven applications with PostgreSQL and FastAPI. Despite its name, it's not just an ORM – it's a complete framework that provides a unified approach to database operations, API definition, and business logic.

### Why is it called "Uno"?

The name "uno" (Spanish for "one") represents the unified nature of the framework, bringing together database, API, and business logic in a cohesive but loosely coupled system.

### Is it production-ready?

Yes, uno is designed for production use. It includes features like comprehensive error handling, connection pooling, retry mechanisms, and security features that make it suitable for production environments.

### What Python versions are supported?

uno requires Python 3.12 or higher due to its use of modern type annotations and language features.

### What PostgreSQL versions are supported?

uno is designed to work with PostgreSQL 16 or higher to leverage the latest PostgreSQL features, including improved JSON support, row-level security, and performance enhancements.

## Technical Questions

### How does uno differ from SQLAlchemy?

SQLAlchemy is an excellent ORM and SQL toolkit, but uno goes beyond by providing:

1. A complete business logic layer with Pydantic integration
2. Automatic API endpoint generation with FastAPI
3. PostgreSQL-specific features like row-level security and JSON operations
4. SQL generation for complex database objects
5. Integrated authorization and filtering

uno actually uses SQLAlchemy internally for its data models, but adds significant functionality on top.

### Can I use uno with existing databases?

Yes, uno can work with existing databases. You can define models that map to your existing tables, create business objects based on those models, and gradually add uno features to your application.

### Does uno support database migrations?

Yes, uno includes full support for database migrations using Alembic. The framework provides commands for generating, applying, and managing migrations.

### How does the authorization system work?

uno includes a comprehensive authorization system with:

1. User and role management
2. Permission-based access control
3. Row-level security integration with PostgreSQL
4. API-level authorization checks

### Can I use uno with other databases?

While uno is optimized for PostgreSQL and leverages many PostgreSQL-specific features, the core architecture could work with other databases. However, you would lose many of the advanced features that rely on PostgreSQL capabilities.

### How do I handle transactions?

uno provides both explicit and implicit transaction support:

1. For explicit transactions, use the SQLAlchemy session transaction context:
   ```python
   async with AsyncSession() as session:
       async with session.begin():
           # Operations inside this block are in a transaction
           # ...
   ```

2. Many uno operations use transactions automatically (like `save()` and `delete()`).

### How does caching work in uno?

uno doesn't provide an integrated caching system, but it's designed to work well with caching solutions like Redis or memcached. The clean separation of concerns makes it easy to add caching at the business logic or API layer.

## Best Practices

### How should I structure my uno application?

A typical uno application is structured as follows:

1. **Models**: Define your database models using `UnoModel`
2. **Business Objects**: Define your business logic using `UnoObj`
3. **API**: Configure endpoints using `EndpointFactory`
4. **Configuration**: Set up database connections and settings

### How do I test a uno application?

uno is designed for testability:

1. Use dependency injection to mock components
2. Use the testing utilities in `uno.testing` for common test scenarios
3. Use the asynchronous testing support in pytest for async tests
4. Create a separate test database for integration tests

### How do I deploy a uno application?

uno applications can be deployed like any FastAPI application:

1. Use gunicorn with uvicorn workers for production
2. Set up database connection pooling
3. Configure environment variables for different environments
4. Use Docker for containerization (a Dockerfile is provided in the project)

### How do I optimize performance with uno?

1. Use appropriate indices on frequently queried columns
2. Enable connection pooling with appropriate pool size
3. Use pagination for large result sets
4. Leverage PostgreSQL-specific features like JSONB indexing
5. Use the async API for I/O-bound operations

### How do I handle security with uno?

1. Use the built-in authorization system
2. Enable row-level security for data isolation
3. Use HTTPS for all API communication
4. Follow password security best practices
5. Validate and sanitize all inputs

## Troubleshooting

### Connection issues with uno

If you're experiencing connection issues:

1. Verify that PostgreSQL is running and accessible
2. Check your connection settings (host, port, user, password)
3. Ensure the database and schemas exist
4. Check for firewall or network issues
5. Look at PostgreSQL logs for connection errors

### Database migration errors

If you encounter migration errors:

1. Check that your models are correctly defined
2. Verify that the current database state matches what Alembic expects
3. Consider creating a manual migration for complex changes
4. Look at the Alembic documentation for specific error messages

### Type checking errors with mypy

uno makes extensive use of type annotations. If you're seeing mypy errors:

1. Ensure you're using Python 3.12+
2. Install the required type stubs with `mypy --install-types`
3. Follow the type annotation patterns in the framework
4. Use proper generic types with `UnoObj[YourModel]`

### API endpoint errors

If you're having issues with API endpoints:

1. Verify that your business objects are correctly registered
2. Check the FastAPI documentation for your endpoints
3. Use the API debugger to inspect requests and responses
4. Ensure your authorization setup is correct

## Getting Help

### Where can I get help with uno?

If you need help with uno, you can:

1. Check the [documentation](index.md) for guides and reference material
2. Look at the example code in the repository
3. File an issue on the GitHub repository
4. Join the community discussion forum

### How can I contribute to uno?

Contributions are welcome! You can:

1. File bug reports on the GitHub repository
2. Submit pull requests for bug fixes or features
3. Improve the documentation
4. Share your experiences and examples