# Files and Modules to Remove

This document identifies files and modules that are no longer needed due to the comprehensive modernization efforts in the UNO framework. All files listed below have been verified to exist in the repository and contain explicit deprecation warnings or have been clearly superseded by modern implementations.

## Core Module Files

- `/src/uno/protocols.py` - Legacy protocol definitions that have been migrated to the core protocol system
- `/src/uno/core/events/basic.py` - Legacy event implementations replaced by the unified event system

## Legacy Infrastructure Components

- `/src/uno/infrastructure/repositories/__init__.py` - Contains explicit deprecation warnings, replaced by uno.domain.entity
- `/src/uno/infrastructure/repositories/base.py` - Legacy base repository implementation
- `/src/uno/infrastructure/services/__init__.py` - Contains "CRITICAL DEPRECATION NOTICE", replaced by uno.domain.entity.service
- `/src/uno/infrastructure/services/di.py` - Part of the deprecated services package

## One-Time Modernization Scripts

These scripts have performed their one-time migration function and are no longer needed:

- `/src/scripts/modernize_imports.py` - One-time script to update legacy class names and imports
- `/src/scripts/modernize_async.py` - One-time script to modernize async patterns
- `/src/scripts/modernize_datetime.py` - One-time script to update datetime.utcnow() to datetime.now(UTC)
- `/src/scripts/modernize_domain.py` - One-time script to modernize domain model implementations
- `/src/scripts/modernize_result.py` - One-time script to modernize Result pattern usage
- `/src/scripts/modernize_error_classes.py` - One-time script to update error class implementations

## API and Integration Files

- `/src/uno/values/api_integration.py` - Legacy API integration replaced by domain endpoint pattern
- `/src/uno/values/domain_api_integration.py` - Legacy domain API integration

## Implementation Plan

To safely remove these files:

1. **Verification Phase**
   - For each file, run `grep -r "import filename"` to find any remaining dependencies
   - Check test coverage to ensure all functionality has been migrated
   - Review the FINAL_ARCHITECTURE_PLAN.md to confirm these components are marked for removal

2. **Removal Phase**
   - First remove the one-time modernization scripts, as they've already completed their task
   - Then remove explicitly deprecated infrastructure components
   - Finally remove the legacy API integration files

3. **Post-Removal Validation**
   - Run the test suite to ensure no functionality is broken
   - Verify imports are resolved correctly
   - Check that documentation references to these files are updated

All of these files have been explicitly deprecated in code comments or are one-time utility scripts that have already served their purpose. Removing them will complete the modernization of the UNO framework, resulting in a cleaner, more maintainable codebase with a unified architecture.