# Import Standards Validation Report

Found 78 violations across 27 files.

## Files with violations (sorted by count):
- src/uno/dto/dto_manager.py: 12 violations
- src/uno/application/dto/manager.py: 9 violations
- src/uno/core/base/dto.py: 7 violations
- src/uno/devtools/codegen/model.py: 6 violations
- src/uno/devtools/debugging/repository_debug.py: 4 violations
- src/uno/dto/__init__.py: 3 violations
- src/uno/meta/repositories.py: 3 violations
- src/uno/attributes/repositories.py: 3 violations
- src/uno/devtools/codegen/service.py: 3 violations
- src/uno/infrastructure/authorization/repositories.py: 3 violations
- src/uno/domain/__init__.py: 3 violations
- src/uno/core/base/__init__.py: 2 violations
- src/uno/dependencies/service.py: 2 violations
- src/uno/devtools/codegen/project.py: 2 violations
- src/uno/application/dto/__init__.py: 2 violations
- src/uno/infrastructure/sql/classes.py: 2 violations
- src/uno/domain/exceptions.py: 2 violations
- src/uno/dto/entities/__init__.py: 1 violations
- src/uno/core/examples/resource_example.py: 1 violations
- src/uno/core/examples/async_example.py: 1 violations
- src/uno/core/fastapi_integration.py: 1 violations
- src/uno/model.py: 1 violations
- src/uno/devtools/codegen/api.py: 1 violations
- src/uno/devtools/codegen/repository.py: 1 violations
- src/uno/application/dto/dto.py: 1 violations
- src/uno/infrastructure/repositories/__init__.py: 1 violations
- src/uno/domain/base/model.py: 1 violations

## Detailed Report

### src/uno/dto/dto_manager.py

#### Legacy Class Name (12)
- Line 39: `from uno.core.base.dto import BaseDTO, DTOConfig, PaginatedListDTO`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 67: `self.schemas: Dict[str, Type[BaseDTO]] = {}`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 79: `def create_schema(self, schema_name: str, model: Type[BaseModel]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 109: `def create_all_schemas(self, model: Type[BaseModel]) -> Dict[str, Type[BaseDTO]]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 123: `def get_schema(self, schema_name: str) -> Optional[Type[BaseDTO]]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 135: `def get_list_schema(self, model: Type[Any]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 190: `__base__=BaseDTO,`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 199: `typed_list_schema = cast(Type[BaseDTO], list_schema)`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 205: `def _create_schema_from_sqlalchemy_model(self, model: Type[Any]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 230: `f"{model.__name__}DTO", __base__=BaseDTO, **fields`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 233: `return cast(Type[BaseDTO], schema)`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 267: `def _get_or_create_detail_schema(self, model: Type[BaseModel]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/application/dto/manager.py

#### Legacy Class Name (9)
- Line 30: `from uno.core.base.dto import BaseDTO, DTOConfig, PaginatedListDTO`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 57: `self.dtos: Dict[str, Type[BaseDTO]] = {}`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 69: `def create_dto(self, dto_name: str, model: Type[BaseModel]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 99: `def create_all_dtos(self, model: Type[BaseModel]) -> Dict[str, Type[BaseDTO]]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 113: `def get_dto(self, dto_name: str) -> Optional[Type[BaseDTO]]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 185: `def _create_dto_from_sqlalchemy_model(self, model: Type[Any]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 209: `f"{model.__name__}DTO", __base__=BaseDTO, **fields`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 212: `return cast(Type[BaseDTO], dto)`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 246: `def _get_or_create_detail_dto(self, model: Type[BaseModel]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/core/base/dto.py

#### Legacy Class Name (7)
- Line 29: `DTOT = TypeVar("DTOT", bound="BaseDTO")`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 33: `class BaseDTO(BaseModel):`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 85: `dto_base: Type[BaseDTO] = BaseDTO`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 89: `def create_dto(self, dto_name: str, model: Type[BaseModel]) -> Type[BaseDTO]:`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 169: `return cast(Type[BaseDTO], dto_cls)`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 172: `class PaginatedListDTO(BaseDTO, Generic[T]):`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 190: `class WithMetadataDTO(BaseDTO):`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/devtools/codegen/model.py

#### Legacy Class Name (6)
- Line 4: `This module provides tools for generating BaseModel and BaseDTO classes.`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 29: `base_dto_class: str = "BaseDTO",`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 36: `"""Generate a BaseModel class with an optional BaseDTO.`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 43: `include_schema: Whether to generate a BaseDTO class`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 137: `include_schema: Whether to generate a BaseDTO class`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 275: `"""Generate a BaseDTO class definition.`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/devtools/debugging/repository_debug.py

#### Legacy Class Name (4)
- Line 15: `from uno.dependencies.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 171: `def patch_repository_class(self, repo_class: Type[UnoRepository]) -> None:`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 247: `base_repo = uno.database.repository.UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 361: `def debug_repository(repository: UnoRepository) -> None:`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/dto/__init__.py

#### Legacy Class Name (3)
- Line 9: `- Base DTO classes: uno.core.base.dto (BaseDTO, PaginatedListDTO, etc.)`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 21: `BaseDTO,`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 91: `"BaseDTO",`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/meta/repositories.py

#### Legacy Class Name (3)
- Line 14: `from uno.dependencies.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 18: `class MetaTypeRepository(UnoRepository[MetaTypeModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 60: `class MetaRecordRepository(UnoRepository[MetaRecordModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/attributes/repositories.py

#### Legacy Class Name (3)
- Line 19: `from uno.database.repository import UnoBaseRepository as UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 34: `class AttributeRepository(UnoRepository, AttributeRepositoryProtocol):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 369: `class AttributeTypeRepository(UnoRepository, AttributeTypeRepositoryProtocol):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/devtools/codegen/service.py

#### Legacy Class Name (3)
- Line 20: `base_class: str = "UnoService",`
  - Suggestion: Replace with BaseService and import from uno.core.base.service
- Line 66: `if base_class == "UnoService":`
  - Suggestion: Replace with BaseService and import from uno.core.base.service
- Line 67: `import_statements.append("from uno.domain.service import UnoService")`
  - Suggestion: Replace with BaseService and import from uno.core.base.service

### src/uno/infrastructure/authorization/repositories.py

#### Legacy Class Name (3)
- Line 15: `from uno.dependencies.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 26: `class UserRepository(UnoRepository[UserModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 195: `class GroupRepository(UnoRepository[GroupModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/domain/__init__.py

#### Backward Compatibility (2)
- Line 327: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 339: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

#### Legacy Class Name (1)
- Line 338: `"- For DTOs, use uno.core.base.dto: BaseDTO, PaginatedListDTO, etc.",`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/core/base/__init__.py

#### Legacy Class Name (2)
- Line 11: `from uno.core.base.dto import BaseDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 36: `"BaseDTO",`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/dependencies/service.py

#### Legacy Class Name (2)
- Line 14: `from uno.dependencies.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 21: `class UnoService(UnoServiceProtocol[T], Generic[ModelT, T]):`
  - Suggestion: Replace with BaseService and import from uno.core.base.service

### src/uno/devtools/codegen/project.py

#### Legacy Class Name (2)
- Line 566: `from uno.database.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 572: `class {name.capitalize()}Repository(UnoRepository):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/application/dto/__init__.py

#### Legacy Class Name (2)
- Line 13: `from uno.core.base.dto import BaseDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 17: `"BaseDTO",`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/infrastructure/sql/classes.py

#### Backward Compatibility (2)
- Line 24: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 27: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/domain/exceptions.py

#### Backward Compatibility (2)
- Line 13: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 16: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/dto/entities/__init__.py

#### Legacy Class Name (1)
- Line 20: `from uno.core.base.dto import BaseDTO`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/core/examples/resource_example.py

#### Deprecated Import (1)
- Line 19: `from uno.core.async_manager import get_async_manager, run_application`
  - Suggestion: Use from uno.core.async.task_manager import

### src/uno/core/examples/async_example.py

#### Deprecated Import (1)
- Line 12: `from uno.core.async_manager import (`
  - Suggestion: Use from uno.core.async.task_manager import

### src/uno/core/fastapi_integration.py

#### Deprecated Import (1)
- Line 15: `from uno.core.async_manager import get_async_manager`
  - Suggestion: Use from uno.core.async.task_manager import

### src/uno/model.py

#### Backward Compatibility (1)
- Line 177: `# For backward compatibility only - use BaseModel directly in new code`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/devtools/codegen/api.py

#### Deprecated Import (1)
- Line 177: `imports.append(f"from uno.repository import {repository_name}")`
  - Suggestion: Use from uno.core.base.repository import

### src/uno/devtools/codegen/repository.py

#### Legacy Class Name (1)
- Line 29: `base_repository_class: str = "UnoRepository",`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/application/dto/dto.py

#### Legacy Class Name (1)
- Line 14: `BaseDTO,`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/infrastructure/repositories/__init__.py

#### Backward Compatibility (1)
- Line 42: `# For backward compatibility`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/domain/base/model.py

#### Backward Compatibility (1)
- Line 177: `# For backward compatibility only - use BaseModel directly in new code`
  - Suggestion: Potential backward compatibility layer - consider removing