# Dependency Injection System Documentation

## Configuration Interfaces Unification

### Problem

The codebase had two separate interfaces for configuration management:
1. `ConfigProvider` in `uno.core.protocols.__init__`
2. `UnoConfigProtocol` in `uno.dependencies.interfaces`

This duplication created confusion for developers, led to inconsistent implementations, and made it harder to maintain the codebase.

### Solution

We unified the two interfaces into a single comprehensive `ConfigProtocol` interface:

1. Created a new `ConfigProtocol` in `dependencies/interfaces.py` that combines all methods from both interfaces
2. Updated `ConfigProvider` in `core/protocols/__init__.py` to inherit from the new `ConfigProtocol`
3. Deprecated `UnoConfigProtocol` while maintaining backward compatibility
4. Updated all implementations to support the unified interface
5. Created a validation script to ensure consistent usage throughout the codebase

### Interface Design

The unified `ConfigProtocol` includes:

```python
class ConfigProtocol(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def all(self) -> dict[str, Any]: ...
    def set(self, key: str, value: Any) -> None: ...
    def load(self, path: str) -> None: ...
    def reload(self) -> None: ...
    def get_section(self, section: str) -> dict[str, Any]: ...
```

This design:
- Incorporates methods from both previous interfaces
- Uses `get()` as the primary method for retrieving values (replacing `get_value()`)
- Maintains backward compatibility with previous implementations
- Provides a more comprehensive API for configuration management

### Backward Compatibility

To ensure backward compatibility:

1. `UnoConfigProtocol` is preserved but deprecated:
   ```python
   class UnoConfigProtocol(Protocol):
       """Legacy protocol for configuration providers. Deprecated: Use ConfigProtocol instead."""
       def get_value(self, key: str, default: Any = None) -> Any: ...
       def all(self) -> dict[str, Any]: ...
   ```

2. All implementations now support both interfaces:
   - `ConfigurationService` implements all methods from the unified interface
   - `UnoConfig` in `modern_provider.py` maintains both old and new methods
   - New code should use `ConfigProtocol` and its methods

### Migration Path

For existing code:
- Use the new `ConfigProtocol` interface in new code
- Update method calls from `get_value()` to `get()` when modifying existing code
- The validation script `validate_config_protocol.py` can help identify areas that need updating

This unification simplifies the codebase, reduces duplication, and provides a clearer API for configuration management while maintaining compatibility with existing code.