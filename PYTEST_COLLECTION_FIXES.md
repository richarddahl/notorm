# Pytest Collection Warning Fixes

## Summary

This document details the fixes applied to address pytest collection warnings. These warnings occurred because classes with names starting with "Test" but not intended as actual test classes were being collected by pytest.

## Issues and Fixes

### 1. TestEntity and TestAggregate Classes

**Issue**: Classes like `TestEntity` and `TestAggregate` in test files were being detected as test classes by pytest, causing collection warnings:

```
tests/unit/test_core/test_application_services.py:43: PytestCollectionWarning: cannot collect test class 'TestEntity' because it has a __init__ constructor
```

**Fix**: Renamed these helper classes to use "Mock" instead of "Test" to avoid pytest attempting to collect them:

```python
# Original:
class TestEntity(Entity[str]):
    """Test entity for application service tests."""
    # ...

# Fixed:
class MockEntity(Entity[str]):
    """Test entity for application service tests."""
    __TEST__ = True  # Marker to avoid pytest collection
    # ...
```

### 2. Updates to References

The class renames required updating all references to these classes throughout the test files:

1. Repository fixtures:
```python
# Original:
return InMemoryRepository(TestEntity)

# Fixed:
return InMemoryRepository(MockEntity)
```

2. Command handlers:
```python
# Original:
create_entity_handler = CreateEntityCommandHandler(
    entity_type=TestEntity, 
    unit_of_work_factory=unit_of_work_factory, 
    repository_type=InMemoryRepository
)

# Fixed:
create_entity_handler = CreateEntityCommandHandler(
    entity_type=MockEntity, 
    unit_of_work_factory=unit_of_work_factory, 
    repository_type=InMemoryRepository
)
```

3. Test entity creation:
```python
# Original:
entity = TestEntity(id="test-1", name="Test Entity", value=10)

# Fixed:
entity = MockEntity(id="test-1", name="Test Entity", value=10)
```

4. Query generics:
```python
# Original:
query = EntityByIdQuery[TestEntity](id="test-1")

# Fixed:
query = EntityByIdQuery[MockEntity](id="test-1")
```

5. Service registration:
```python
# Original:
entity_service = registry.register_entity_service(
    entity_type=TestEntity,
    # ...
)

# Fixed:
entity_service = registry.register_entity_service(
    entity_type=MockEntity,
    # ...
)

# And updating the entity service name in tests:
# Original:
retrieved_entity_service = registry.get("TestEntityService")

# Fixed:
retrieved_entity_service = registry.get("MockEntityService")
```

### 3. `__TEST__` Attribute

In addition to renaming, we added a `__TEST__ = True` marker attribute to these classes. This approach would allow for future filtering if needed, though the class renaming was the primary fix for the collection warnings.

## Files Modified

1. `/tests/unit/test_core/test_application_services.py`
2. `/tests/unit/test_core/test_authorization.py`
3. `/tests/unit/test_core/test_cqrs.py`

## Results

All pytest collection warnings related to test class detection were resolved. The tests now run without these distracting warnings, making it easier to focus on actual test failures.

## Lessons Learned

1. Avoid using "Test" prefix for helper classes in test files, as pytest will attempt to collect them as test classes.
2. If you need a class that represents a test entity or model, prefer naming it with "Mock" prefix.
3. The `__TEST__` attribute pattern can be useful for marking classes that might otherwise be collected by pytest.
4. When renaming classes, ensure you update all references, including type parameters in generic classes.
5. Be careful with default name generation in service registries and similar mechanisms - they often derive names from class names.