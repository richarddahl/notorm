# Modernization Scripts

This directory contains scripts designed to help modernize the codebase by enforcing current standards and providing validation tools.

## Import Standards Scripts

### `validate_import_standards.py`

Validates the codebase for adherence to the uno framework import standards.

**Usage:**
```
python -m src.scripts.validate_import_standards
```

**Features:**
- Identifies usage of outdated class names and updates them to current standards.
- Detects imports from deprecated modules
- Finds potential backward compatibility layers
- Generates a comprehensive validation report
- Creates a fix guide with concrete suggestions

**Outputs:**
- `reports/import_validation_report.md`: Detailed report of all violations
- `reports/import_fix_guide.md`: Step-by-step guide for fixing the issues

### `modernize_imports.py`

Automatically updates imports and class names to follow the uno framework standards.

**Usage:**
```
python -m src.scripts.modernize_imports [options]
```

**Options:**
- `--path=PATH`: Process only files in the specified path
- `--remove-compat`: Remove backward compatibility layers (use with caution)
- `--dry-run`: Show changes without applying them
- `--auto-fix`: Apply all changes without confirmation

**Features:**
- Replaces outdated class names with their Base-prefixed versions (`UnoModel` → `BaseModel`)
- Updates deprecated import paths to standardized ones
- Adds missing imports for replaced classes
- Optionally removes backward compatibility layers and aliases

**Examples:**
```bash
# Check what changes would be made without applying them
python -m src.scripts.modernize_imports --dry-run

# Modernize imports in a specific directory
python -m src.scripts.modernize_imports --path=src/uno/api

# Automatically fix all imports in the codebase
python -m src.scripts.modernize_imports --auto-fix

# Remove backward compatibility layers and update imports
python -m src.scripts.modernize_imports --remove-compat
```

## Other Modernization Scripts

### `modernize_async.py`

Updates legacy async patterns to modern Python 3.12+ patterns.

**Usage:**
```
python -m src.scripts.modernize_async [path]
```

### `modernize_datetime.py`

Replaces `datetime.utcnow()` with the modern `datetime.now(datetime.UTC)`.

**Usage:**
```
python -m src.scripts.modernize_datetime [path]
```

### `modernize_domain.py`

Modernizes domain model implementations to follow clean architecture principles.

**Usage:**
```
python -m src.scripts.modernize_domain [path]
```

### `modernize_result.py`

Updates code to use the Result pattern for error handling.

**Usage:**
```
python -m src.scripts.modernize_result [path]
```

## Recommended Workflow

For a comprehensive modernization of a module or package:

1. First run validation to identify issues:
   ```
   python -m src.scripts.validate_import_standards
   ```

2. Review the generated reports in the `reports/` directory

3. Apply import modernization with dry run first:
   ```
   python -m src.scripts.modernize_imports --dry-run --path=<target_path>
   ```

4. If changes look good, apply them:
   ```
   python -m src.scripts.modernize_imports --path=<target_path>
   ```

5. Run other modernization scripts as needed:
   ```
   python -m src.scripts.modernize_async <target_path>
   python -m src.scripts.modernize_datetime <target_path>
   python -m src.scripts.modernize_domain <target_path>
   python -m src.scripts.modernize_result <target_path>
   ```

6. Run tests to verify the changes don't break functionality:
   ```
   hatch run test:test tests/path/to/relevant_tests.py
   ```