# Import Standards Fix Guide

This guide provides specific fixes for 8 violations across 4 files.

## src/uno/dependencies/interfaces.py

### Evaluate backward compatibility on line 131
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Evaluate backward compatibility on line 133
Code: `DeprecationWarning,`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---

## src/uno/domain/__init__.py

### Evaluate backward compatibility on line 327
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Evaluate backward compatibility on line 339
Code: `DeprecationWarning,`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---

## src/uno/domain/exceptions.py

### Evaluate backward compatibility on line 13
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Evaluate backward compatibility on line 16
Code: `DeprecationWarning,`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---

## src/uno/infrastructure/sql/classes.py

### Evaluate backward compatibility on line 24
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Evaluate backward compatibility on line 27
Code: `DeprecationWarning,`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---
