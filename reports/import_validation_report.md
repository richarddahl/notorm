# Import Standards Validation Report

Found 8 violations across 4 files.

## Files with violations (sorted by count):
- src/uno/dependencies/interfaces.py: 2 violations
- src/uno/infrastructure/sql/classes.py: 2 violations
- src/uno/domain/__init__.py: 2 violations
- src/uno/domain/exceptions.py: 2 violations

## Detailed Report

### src/uno/dependencies/interfaces.py

#### Backward Compatibility (2)
- Line 131: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 133: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/infrastructure/sql/classes.py

#### Backward Compatibility (2)
- Line 24: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 27: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/domain/__init__.py

#### Backward Compatibility (2)
- Line 327: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 339: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/domain/exceptions.py

#### Backward Compatibility (2)
- Line 13: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 16: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing