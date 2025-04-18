# Import Standards Modernization

## Overview

As part of our ongoing efforts to modernize the Uno framework codebase, we've implemented tools to validate and automatically update code to follow our standardized import patterns and naming conventions.

## New Tools

### 1. Import Standards Validator

The `validate_import_standards.py` script analyzes the codebase for:

- Usage of legacy class names (`UnoModel`, `UnoRepository`, `UnoError`, etc.)
- Imports from deprecated modules
- Backward compatibility layers 

It generates detailed reports with:
- A list of all violations organized by file
- Specific suggestions for fixes
- Line-by-line guidance for updating the code

**Usage:**
```bash
python -m src.scripts.validate_import_standards
```

### 2. Automatic Import Modernizer

The `modernize_imports.py` script automatically updates:

- Legacy class names to their `Base`-prefixed versions 
- Deprecated import paths to the standardized ones
- Adds missing imports as needed

It includes safety features to:
- Preserve backward compatibility alias definitions
- Skip updates in comments
- Avoid modifying intentional compatibility layers

**Usage:**
```bash
# Dry run to see changes without applying them
python -m src.scripts.modernize_imports --dry-run --path=src/uno/path/to/file.py

# Apply changes with confirmation for each file
python -m src.scripts.modernize_imports --path=src/uno/path/to/file.py

# Apply changes automatically without confirmation
python -m src.scripts.modernize_imports --auto-fix --path=src/uno/path/to/file.py

# Remove backward compatibility layers (use with caution)
python -m src.scripts.modernize_imports --remove-compat --path=src/uno/path/to/file.py
```

### 3. Error Classes Modernizer

The `modernize_error_classes.py` script focuses specifically on modernizing our error handling code:

- Renames `UnoError` to `BaseError` throughout the codebase
- Updates error class imports to use the standardized paths
- Preserves backward compatibility aliases

**Usage:**
```bash
python -m src.scripts.modernize_error_classes --dry-run
python -m src.scripts.modernize_error_classes --auto-fix
```

## Initial Analysis Results

Our initial analysis identified 444 import standard violations across 89 files, with the most common issues being:

1. Use of legacy class names like `UnoError` instead of `BaseError`
2. Imports from deprecated modules
3. Backward compatibility layers that could be removed

## Next Steps

1. **Incremental Modernization**: Apply the modernization scripts incrementally to different parts of the codebase, focusing on core modules first.

2. **Test Extensively**: After each modernization step, run comprehensive tests to ensure no regressions.

3. **Documentation Updates**: Update documentation to reflect the standardized class names and import paths.

4. **Remove Compatibility Layers**: Once all code has been updated to use the standardized imports, we can remove the backward compatibility layers.

5. **CI Integration**: Add an import standards validation check to our CI pipeline to ensure new code follows the standards.

## Documentation

For more details, see:
- `src/scripts/README_MODERNIZATION.md`: Complete documentation of modernization scripts
- `DEVELOPER_GUIDE.md`: Updated with standardized import paths and modernization tools
- `CLAUDE.md`: Updated with new script documentation

## Impact

These modernization tools will help us:
- Establish a consistent coding style across the codebase
- Simplify the mental model for developers
- Reduce confusion about which classes and modules to use
- Make the codebase more maintainable in the long term