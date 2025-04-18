#!/usr/bin/env python3
"""
Script to refactor the BaseService in dependencies/service.py to use the standardized service pattern.

This script:
1. Updates the BaseService to inherit from the core BaseService
2. Updates the CrudService to use the modern error handling
3. Updates imports and related protocols
4. Ensures backward compatibility via adapters

Usage:
    python -m src.scripts.refactor_dependency_service

"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class DependencyServiceRefactorer:
    """Tool to refactor the BaseService in dependencies/service.py."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.service_path = base_dir / "src" / "uno" / "dependencies" / "service.py"
        self.interfaces_path = base_dir / "src" / "uno" / "dependencies" / "interfaces.py"
        self.modern_service_path = base_dir / "src" / "uno" / "core" / "base" / "service.py"
        self.repository_path = base_dir / "src" / "uno" / "dependencies" / "repository.py"
        
        # Check if files exist
        if not self.service_path.exists():
            raise FileNotFoundError(f"Service file not found at {self.service_path}")
        if not self.interfaces_path.exists():
            raise FileNotFoundError(f"Interfaces file not found at {self.interfaces_path}")
        if not self.modern_service_path.exists():
            raise FileNotFoundError(f"Modern service file not found at {self.modern_service_path}")
    
    def update_service_file(self) -> str:
        """
        Update the dependencies/service.py file to use the standardized BaseService.
        
        Returns:
            Updated content for the service.py file
        """
        with open(self.service_path, 'r') as f:
            content = f.read()
        
        # Create the refactored content
        new_content = '''"""
Base service implementation for dependency injection in the Uno framework.

This module provides service implementations that integrate with the 
dependency injection system, while following the standardized service pattern.
"""

from typing import Dict, List, Optional, TypeVar, Generic, Any, Type, cast
import logging

from uno.domain.base.model import BaseModel
from uno.core.base.service import BaseService as CoreBaseService, ServiceProtocol
from uno.core.base.error import BaseError
from uno.core.errors.result import Result, Success, Failure
from uno.dependencies.interfaces import UnoRepositoryProtocol

# Type variables
ModelT = TypeVar("ModelT", bound=BaseModel)
T = TypeVar("T")
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseService(CoreBaseService[Dict[str, Any], T], Generic[ModelT, T]):
    """
    DI-compatible service implementation that extends the core BaseService.
    
    This service follows the standardized service pattern while providing
    compatibility with the dependency injection system.
    """

    def __init__(
        self,
        repository: UnoRepositoryProtocol[ModelT],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the service.

        Args:
            repository: Repository for data access
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.repository = repository
    
    # Note: The execute method is inherited from CoreBaseService
    # and automatically provides error handling
    
    async def _execute_internal(self, input_data: Dict[str, Any]) -> Result[T]:
        """
        Internal implementation of the service operation.
        
        This method must be overridden by subclasses to provide specific
        service operation logic.
        
        Args:
            input_data: Dictionary of parameters for the operation
            
        Returns:
            Result containing the operation output
        """
        raise NotImplementedError("Subclasses must implement _execute_internal()")


class CrudService(Generic[ModelT]):
    """
    Generic CRUD service implementation that uses the Result pattern.

    Provides standardized CRUD operations using a repository.
    """

    def __init__(
        self,
        repository: UnoRepositoryProtocol[ModelT],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the CRUD service.

        Args:
            repository: Repository for data access
            logger: Optional logger instance
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

    async def get(self, id: str) -> Result[Optional[ModelT]]:
        """
        Get a model by ID.

        Args:
            id: The unique identifier of the model

        Returns:
            Result containing the model instance if found, None otherwise
        """
        try:
            result = await self.repository.get(id)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error getting entity: {str(e)}")
            return Failure(str(e))

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Result[List[ModelT]]:
        """
        List models with optional filtering and pagination.

        Args:
            filters: Dictionary of field name to value pairs for filtering
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing list of model instances
        """
        try:
            result = await self.repository.list(filters, limit, offset)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error listing entities: {str(e)}")
            return Failure(str(e))

    async def create(self, data: Dict[str, Any]) -> Result[ModelT]:
        """
        Create a new model instance.

        Args:
            data: Dictionary of field name to value pairs

        Returns:
            Result containing the created model instance
        """
        try:
            result = await self.repository.create(data)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            return Failure(str(e))

    async def update(self, id: str, data: Dict[str, Any]) -> Result[Optional[ModelT]]:
        """
        Update an existing model by ID.

        Args:
            id: The unique identifier of the model
            data: Dictionary of field name to value pairs to update

        Returns:
            Result containing the updated model instance if found, None otherwise
        """
        try:
            result = await self.repository.update(id, data)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            return Failure(str(e))

    async def delete(self, id: str) -> Result[bool]:
        """
        Delete a model by ID.

        Args:
            id: The unique identifier of the model

        Returns:
            Result containing True if the model was deleted, False otherwise
        """
        try:
            result = await self.repository.delete(id)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error deleting entity: {str(e)}")
            return Failure(str(e))


# Legacy adapter for backward compatibility
class LegacyServiceAdapter(ServiceProtocol[InputT, OutputT]):
    """
    Adapter to provide backward compatibility for legacy code.
    
    This adapter allows services using the new Result pattern to be used
    with code expecting the older service interface.
    """
    
    def __init__(self, service: ServiceProtocol[InputT, OutputT]):
        """
        Initialize the adapter.
        
        Args:
            service: Modern service to adapt
        """
        self.service = service
    
    async def execute(self, *args, **kwargs) -> OutputT:
        """
        Execute the service operation, unwrapping Result.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            The operation result
            
        Raises:
            Exception: If the operation fails
        """
        # Convert args/kwargs to the expected input format for the service
        input_data = kwargs if kwargs else args[0] if args else {}
        
        # Execute the service and handle the Result
        result = await self.service.execute(input_data)
        
        if result.is_success():
            return result.value
        else:
            # Recreate an exception from the failure
            error_code = getattr(result, "error_code", None)
            if error_code:
                raise BaseError(result.error, error_code)
            else:
                raise Exception(result.error)
'''
        
        return new_content
    
    def update_interfaces_file(self) -> str:
        """
        Update the dependencies/interfaces.py file to modify the UnoServiceProtocol.
        
        Returns:
            Updated content for the interfaces.py file
        """
        with open(self.interfaces_path, 'r') as f:
            content = f.read()
        
        # Add deprecation warning to UnoServiceProtocol
        import_section_end = content.find("T = TypeVar('T')")
        if import_section_end == -1:
            import_section_end = content.find("import psycopg")
            if import_section_end != -1:
                import_section_end = content.find("\n", import_section_end) + 1
        
        if import_section_end != -1:
            # Add import for warnings
            content = content[:import_section_end] + "import warnings\n" + content[import_section_end:]
        
        # Find the UnoServiceProtocol definition
        protocol_start = content.find("class UnoServiceProtocol(Protocol, Generic[T]):")
        if protocol_start != -1:
            # Find the end of the class docstring
            docstring_start = content.find('"""', protocol_start)
            if docstring_start != -1:
                docstring_end = content.find('"""', docstring_start + 3)
                if docstring_end != -1:
                    # Add deprecation note to docstring
                    insert_pos = docstring_end + 3
                    deprecation_note = """
    
    .. deprecated:: 1.0.0
        Use ServiceProtocol from uno.core.base.service instead.
        This protocol is maintained for backward compatibility only.
    """
                    content = content[:insert_pos] + deprecation_note + content[insert_pos:]
                    
                    # Add deprecation warning to class definition
                    warning_code = """
    def __new__(cls, *args, **kwargs):
        warnings.warn(
            "UnoServiceProtocol is deprecated. Use ServiceProtocol from uno.core.base.service instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls)
"""
                    # Find position to insert the warning (after the class definition and docstring)
                    method_start = content.find("    async def execute", insert_pos)
                    if method_start != -1:
                        content = content[:method_start] + warning_code + content[method_start:]
        
        return content
    
    def create_migration_guide(self) -> str:
        """
        Create a migration guide for transitioning from the old service pattern to the new one.
        
        Returns:
            Content for the migration guide
        """
        guide = """# Service Refactoring Migration Guide

## Overview

The `BaseService` class in `src/uno/dependencies/service.py` has been refactored to align with the standardized service pattern defined in `src/uno/core/base/service.py`. This guide explains how to migrate your existing services to the new pattern.

## Key Changes

1. `BaseService` now extends `CoreBaseService` from `uno.core.base.service`
2. Services now use the `Result` pattern for error handling
3. `CrudService` has been updated to use the Result pattern
4. A `LegacyServiceAdapter` provides backward compatibility

## How to Migrate Your Services

### For Simple Services

1. Update your imports:

```python
# Before
from uno.dependencies.service import BaseService

# After
from uno.core.base.service import BaseService
```

2. Update your service implementation:

```python
# Before
class MyService(BaseService[ModelT, ResultT]):
    async def execute(self, *args, **kwargs) -> ResultT:
        # Implementation

# After
class MyService(BaseService[Dict[str, Any], ResultT]):
    async def _execute_internal(self, input_data: Dict[str, Any]) -> Result[ResultT]:
        # Implementation
        return Success(result)
```

### For CRUD Services

1. Update your imports:

```python
# Before
from uno.dependencies.service import CrudService

# After
from uno.dependencies.service import CrudService  # New Result-based implementation
from uno.core.errors.result import Result, Success, Failure
```

2. Update your service usage:

```python
# Before
result = await crud_service.get(id)

# After
result = await crud_service.get(id)
if result.is_success():
    data = result.value
    # Use the data
else:
    # Handle the error
    error_message = result.error
```

### For Code That Can't Be Updated Immediately

Use the `LegacyServiceAdapter` to wrap new-style services:

```python
from uno.dependencies.service import LegacyServiceAdapter

# Create a modern service
modern_service = MyModernService(repository, logger)

# Wrap it with the adapter for legacy code
legacy_compatible_service = LegacyServiceAdapter(modern_service)

# Legacy code can use it with the old interface
result = await legacy_compatible_service.execute(*args, **kwargs)
```

## Benefits of the New Pattern

1. **Consistent Error Handling**: The `Result` pattern provides a standardized way to handle both success and failure cases
2. **Separation of Concerns**: The pattern separates error handling from business logic
3. **Type Safety**: Better type hints through generics
4. **Validation Support**: Built-in mechanism for input validation

## Examples

### Example: Simple Service

```python
from typing import Dict, Any
from uno.core.base.service import BaseService
from uno.core.errors.result import Result, Success, Failure

class UserCreationService(BaseService[Dict[str, Any], User]):
    def __init__(self, user_repository, logger=None):
        super().__init__(logger)
        self.user_repository = user_repository
    
    async def validate(self, input_data: Dict[str, Any]) -> Optional[Result[User]]:
        # Validate input
        if "email" not in input_data:
            return Failure("Email is required")
        return None
    
    async def _execute_internal(self, input_data: Dict[str, Any]) -> Result[User]:
        try:
            user = await self.user_repository.create(input_data)
            return Success(user)
        except Exception as e:
            return Failure(str(e))
```

### Example: CRUD Service Usage

```python
# Create a CRUD service
user_service = CrudService(user_repository)

# Get a user
result = await user_service.get("user-123")
if result.is_success():
    user = result.value
    # Use user data
else:
    # Handle error
    error_message = result.error
```

## Questions?

If you have questions about migrating your services, please contact the development team.
"""
        return guide
    
    def run(self, auto_apply=False, dry_run=False):
        """
        Execute the refactoring process.
        
        Args:
            auto_apply: If True, apply changes without prompting
            dry_run: If True, don't apply changes, just show what would change
        """
        print("Starting refactoring of dependency service...")
        
        # Update service.py
        new_service_content = self.update_service_file()
        print(f"Updated content for {self.service_path}")
        
        # Update interfaces.py
        new_interfaces_content = self.update_interfaces_file()
        print(f"Updated content for {self.interfaces_path}")
        
        # Create migration guide
        guide_content = self.create_migration_guide()
        guide_path = self.base_dir / "docs" / "dependencies" / "service_migration_guide.md"
        os.makedirs(guide_path.parent, exist_ok=True)
        print(f"Created migration guide at {guide_path}")
        
        # Write updated files
        print("\nFiles to update:")
        print(f"1. {self.service_path}")
        print(f"2. {self.interfaces_path}")
        print(f"3. {guide_path}")
        
        apply_changes = auto_apply
        
        if dry_run:
            print("\nDry run mode - no changes will be applied.")
            apply_changes = False
        elif not auto_apply:
            try:
                choice = input("\nDo you want to apply these changes? (y/n): ")
                apply_changes = choice.lower() == 'y'
            except (EOFError, KeyboardInterrupt):
                print("\nInteractive input failed. Use --apply or --dry-run for non-interactive mode.")
                apply_changes = False
        
        if apply_changes:
            # Write service.py
            with open(self.service_path, 'w') as f:
                f.write(new_service_content)
            
            # Write interfaces.py
            with open(self.interfaces_path, 'w') as f:
                f.write(new_interfaces_content)
            
            # Write migration guide
            with open(guide_path, 'w') as f:
                f.write(guide_content)
            
            print("\nRefactoring completed successfully!")
            print(f"Migration guide written to {guide_path}")
            print("\nNext steps:")
            print("1. Test the changes to ensure backward compatibility")
            print("2. Identify and update service implementations to use the new pattern")
            print("3. Plan for removing the legacy adapter in the future")
        else:
            print("\nRefactoring canceled. No files were modified.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Refactor the BaseService in dependencies/service.py")
    parser.add_argument("--apply", action="store_true", help="Apply the changes without prompting")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without applying")
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent.parent
    refactorer = DependencyServiceRefactorer(base_dir)
    
    if args.apply:
        refactorer.run(auto_apply=True)
    elif args.dry_run:
        refactorer.run(dry_run=True)
    else:
        refactorer.run()


if __name__ == "__main__":
    main()