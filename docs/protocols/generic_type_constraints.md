# Generic Type Constraints in Protocols

This document describes the enhanced generic type constraints that have been added to protocols in the Uno framework.

## Introduction

Generic type constraints provide several key benefits:

1. **Type Safety**: Ensure that implementations correctly match the expected types
2. **Clarity**: Make interfaces more self-documenting and easier to understand
3. **Flexibility**: Allow for specialized implementations that maintain type safety
4. **Static Analysis**: Enable better static analysis tools to catch type errors early

By applying proper generic type constraints to our protocols, we've made the Uno framework more robust and developer-friendly.

## Key Concepts

### Type Variables and Variance

Our enhanced protocols use several kinds of type variables:

- **Invariant Type Variables**: Standard type variables that must match exactly
- **Covariant Type Variables (`T_co`)**: Allow subtypes in return values
- **Contravariant Type Variables (`T_contra`)**: Allow supertypes in arguments
- **Bounded Type Variables**: Restrict types to a specific base type

Example:
```python
KeyT = TypeVar('KeyT')                           # Invariant
ValueT_co = TypeVar('ValueT_co', covariant=True) # Covariant
KeyT_contra = TypeVar('KeyT_contra', contravariant=True) # Contravariant
StrKeyT = TypeVar('StrKeyT', bound=str)          # Bounded
```

### Protocol Generics

Protocols can be parameterized with type variables to create generic interfaces:

```python
@runtime_checkable
class Repository(Protocol[EntityT, KeyT]):
    """
    Protocol for repositories.
    
    Type Parameters:
        EntityT: Type of entity managed by this repository
        KeyT: Type of entity key/identifier
    """
    
    async def get(self, id: KeyT) -> Optional[EntityT]:
        """Get an entity by its ID."""
        ...
```

## Enhanced Protocols

### Database Session Protocols

The database session protocols now use generic type parameters to specify the types of statements, results, and models:

```python
@runtime_checkable
class DatabaseSessionProtocol(Protocol[StatementT, ResultT_co, ModelT]):
    """Protocol for database sessions."""
    
    async def execute(self, statement: StatementT, *args: Any, **kwargs: Any) -> ResultT_co:
        """Execute a statement."""
        ...
    
    def add(self, instance: ModelT) -> None:
        """Add an instance to the session."""
        ...
```

### Repository Pattern

The repository pattern has been extended with additional type parameters:

```python
@runtime_checkable
class DatabaseRepository(Protocol[EntityT, KeyT, FilterT, DataT, MergeResultT]):
    """Protocol for database repositories."""
    
    @classmethod
    async def get(cls, **kwargs: Any) -> Optional[EntityT]:
        """Get an entity by keyword arguments."""
        ...
    
    @classmethod
    async def filter(cls, filters: Optional[FilterT] = None) -> List[EntityT]:
        """Filter entities by criteria."""
        ...
```

### Configuration Management

The configuration provider protocol uses contravariant key types and covariant value types:

```python
@runtime_checkable
class ConfigProvider(Protocol[KeyT_contra, ValueT_co, SectionT, DefaultT]):
    """Protocol for configuration providers."""
    
    def get(self, key: KeyT_contra, default: Optional[DefaultT] = None) -> Union[ValueT_co, DefaultT]:
        """Get a configuration value."""
        ...
```

### Cache Implementations

Cache protocols now have proper type constraints for keys, values, and TTL:

```python
@runtime_checkable
class Cache(Protocol[KeyT, ValueT, TTLT, PrefixT]):
    """Protocol for cache implementations."""
    
    async def get(self, key: KeyT) -> Optional[ValueT]:
        """Get a value from the cache."""
        ...
    
    async def set(self, key: KeyT, value: ValueT, ttl: Optional[TTLT] = None) -> None:
        """Set a value in the cache."""
        ...
```

### Plugin Architecture

Plugin protocols now have rich type parameters for context, configuration, and events:

```python
@runtime_checkable
class Plugin(Protocol[PluginContextT, PluginConfigT, PluginEventT, PluginNameT, PluginVersionT]):
    """Protocol for plugins."""
    
    async def initialize(self, context: PluginContextT) -> None:
        """Initialize the plugin."""
        ...
    
    async def configure(self, config: PluginConfigT) -> None:
        """Configure the plugin."""
        ...
```

### Health Checks

Health check protocols now use type parameters for status, details, and component names:

```python
@runtime_checkable
class HealthCheck(Protocol[HealthStatusT, HealthDetailsT, HealthComponentT]):
    """Protocol for health checks."""
    
    async def check(self) -> Tuple[HealthStatusT, Optional[HealthDetailsT]]:
        """Perform the health check."""
        ...
```

## Best Practices

When working with generically-constrained protocols, follow these best practices:

### 1. Use Appropriate Variance

- Use **covariant** (`T_co`) for return types
- Use **contravariant** (`T_contra`) for parameter types
- Use **invariant** for types used both as parameters and return values

### 2. Be Specific About Bounds

When a type must be a subclass of a specific type, use bounded type variables:

```python
PrefixT = TypeVar('PrefixT', bound=str)
```

### 3. Document Type Parameters

Always document what each type parameter represents:

```python
"""
Type Parameters:
    EntityT: Type of entity managed by this repository
    KeyT: Type of entity key/identifier
"""
```

### 4. Use Type Aliases for Complex Types

For complex types, create type aliases to improve readability:

```python
# Instead of Dict[str, Union[str, int, bool, List[Any], Dict[str, Any]]]
ConfigValueT = Union[str, int, bool, List[Any], Dict[str, Any]]
ConfigDictT = Dict[str, ConfigValueT]
```

### 5. Leverage Protocol Composition

Combine multiple protocols using union types or inheritance:

```python
class AdvancedRepository(Repository[EntityT, KeyT], Cacheable[EntityT, KeyT], Protocol[EntityT, KeyT]):
    """A repository with caching capabilities."""
    ...
```

## Examples

### Example 1: Using Database Repository

```python
class UserModel(BaseModel):
    id: UUID
    name: str
    email: str

# Type-safe repository for users
UserRepo = DatabaseRepository[UserModel, UUID, UserFilter, Dict[str, Any], Dict[str, Any]]

# Implementation
@implements(UserRepo)
class PostgresUserRepository:
    @classmethod
    async def get(cls, **kwargs: Any) -> Optional[UserModel]:
        # Implementation details...
        return user if user else None
```

### Example 2: Using Configuration Provider

```python
# Type-safe configuration provider
AppConfig = ConfigProvider[str, Union[str, int, bool, List[str]], str, Any]

# Implementation
@implements(AppConfig)
class EnvironmentConfigProvider:
    def get(self, key: str, default: Optional[Any] = None) -> Union[str, int, bool, List[str], Any]:
        # Implementation details...
        return value or default
```

## Conclusion

The enhanced generic type constraints in the Uno framework protocols provide stronger type safety, clearer interfaces, and better development experiences. These improvements allow for greater flexibility in implementations while maintaining strict type checking, resulting in more robust and maintainable code.