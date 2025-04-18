# Import Standards Validation Report

Found 444 violations across 89 files.

## Files with violations (sorted by count):
- src/uno/infrastructure/database/errors.py: 22 violations
- src/uno/core/errors/core_errors.py: 19 violations
- src/uno/core/fastapi_error_handlers.py: 13 violations
- src/uno/core/errors/examples.py: 13 violations
- src/uno/api/domain_repositories.py: 13 violations
- src/uno/infrastructure/reports/models.py: 13 violations
- src/uno/infrastructure/reports/errors.py: 13 violations
- src/uno/application/workflows/models.py: 12 violations
- src/uno/application/workflows/executor.py: 12 violations
- src/uno/values/models.py: 11 violations
- src/uno/dependencies/modern_provider.py: 11 violations
- src/uno/devtools/codegen/model.py: 11 violations
- src/uno/infrastructure/authorization/models.py: 11 violations
- src/uno/attributes/errors.py: 10 violations
- src/uno/infrastructure/sql/errors.py: 10 violations
- src/uno/application/workflows/errors.py: 9 violations
- src/uno/core/errors/base.py: 8 violations
- src/uno/attributes/models.py: 8 violations
- src/uno/api/domain_services.py: 8 violations
- src/uno/application/queries/models.py: 8 violations
- src/uno/infrastructure/database/pg_error_handler.py: 8 violations
- src/uno/values/errors.py: 7 violations
- src/uno/devtools/debugging/error_enhancer.py: 7 violations
- src/uno/application/queries/errors.py: 7 violations
- src/uno/infrastructure/database/enhanced_db.py: 7 violations
- src/uno/examples/ecommerce_app/catalog/repository/models.py: 6 violations
- src/uno/application/workflows/provider.py: 6 violations
- src/uno/infrastructure/database/db.py: 6 violations
- src/uno/core/examples/modern_architecture_example.py: 5 violations
- src/uno/core/di_testing.py: 5 violations
- src/uno/dependencies/service.py: 5 violations
- src/uno/infrastructure/messaging/models.py: 5 violations
- src/uno/domain/exceptions.py: 5 violations
- src/uno/meta/models.py: 4 violations
- src/uno/devtools/debugging/repository_debug.py: 4 violations
- src/uno/devtools/codegen/service.py: 4 violations
- src/uno/devtools/codegen/project.py: 4 violations
- src/uno/examples/ecommerce_app/main.py: 4 violations
- src/uno/application/workflows/integration.py: 4 violations
- src/uno/domain/specification_translators/postgresql.py: 4 violations
- src/uno/migrations/env.py: 3 violations
- src/uno/core/examples/monitoring_example.py: 3 violations
- src/uno/core/examples/error_handling_example.py: 3 violations
- src/uno/core/errors/security.py: 3 violations
- src/uno/core/errors/__init__.py: 3 violations
- src/uno/meta/repositories.py: 3 violations
- src/uno/dependencies/testing.py: 3 violations
- src/uno/attributes/repositories.py: 3 violations
- src/uno/devtools/debugging/middleware.py: 3 violations
- src/uno/api/service_endpoint_adapter.py: 3 violations
- src/uno/infrastructure/authorization/repositories.py: 3 violations
- src/uno/infrastructure/services/factory.py: 3 violations
- src/uno/infrastructure/sql/config.py: 3 violations
- src/uno/infrastructure/sql/registry.py: 3 violations
- src/uno/infrastructure/sql/emitters/database.py: 3 violations
- src/uno/dto/dto_manager.py: 2 violations
- src/uno/enums.py: 2 violations
- src/uno/core/__init__.py: 2 violations
- src/uno/core/errors/logging.py: 2 violations
- src/uno/core/errors/result.py: 2 violations
- src/uno/core/monitoring/dashboard.py: 2 violations
- src/uno/core/base/service.py: 2 violations
- src/uno/model.py: 2 violations
- src/uno/devtools/cli/codegen.py: 2 violations
- src/uno/devtools/codegen/api.py: 2 violations
- src/uno/devtools/codegen/repository.py: 2 violations
- src/uno/api/domain_endpoints.py: 2 violations
- src/uno/application/dto/__init__.py: 2 violations
- src/uno/application/queries/optimized_queries.py: 2 violations
- src/uno/application/queries/batch_operations.py: 2 violations
- src/uno/application/queries/common_patterns.py: 2 violations
- src/uno/application/workflows/recipients.py: 2 violations
- src/uno/application/workflows/conditions.py: 2 violations
- src/uno/application/workflows/engine.py: 2 violations
- src/uno/infrastructure/sql/classes.py: 2 violations
- src/uno/infrastructure/sql/emitter.py: 2 violations
- src/uno/domain/__init__.py: 2 violations
- src/uno/domain/base/model.py: 2 violations
- src/uno/mixins.py: 1 violations
- src/uno/core/examples/resource_example.py: 1 violations
- src/uno/core/examples/batch_operations_example.py: 1 violations
- src/uno/core/examples/async_example.py: 1 violations
- src/uno/core/errors/validation.py: 1 violations
- src/uno/core/fastapi_integration.py: 1 violations
- src/uno/devtools/docs/extractors.py: 1 violations
- src/uno/api/error_handlers.py: 1 violations
- src/uno/infrastructure/repositories/__init__.py: 1 violations
- src/uno/infrastructure/authorization/mixins.py: 1 violations
- src/uno/infrastructure/services/di.py: 1 violations

## Detailed Report

### src/uno/infrastructure/database/errors.py

#### Legacy Class Name (22)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 68: `class DatabaseConnectionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 91: `class DatabaseConnectionTimeoutError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 114: `class DatabaseConnectionPoolExhaustedError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 138: `class DatabaseQueryError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 162: `class DatabaseQueryTimeoutError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 186: `class DatabaseQuerySyntaxError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 211: `class DatabaseTransactionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 229: `class DatabaseTransactionRollbackError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 247: `class DatabaseTransactionConflictError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 266: `class DatabaseIntegrityError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 289: `class DatabaseUniqueViolationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 315: `class DatabaseForeignKeyViolationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 342: `class DatabaseResourceNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 362: `class DatabaseResourceAlreadyExistsError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 382: `class DatabaseTableNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 400: `class DatabaseColumnNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 424: `class DatabaseSessionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 442: `class DatabaseSessionExpiredError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 464: `class DatabaseConfigError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 488: `class DatabaseOperationalError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 506: `class DatabaseNotSupportedError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/errors/core_errors.py

#### Legacy Class Name (19)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 55: `class ConfigNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 73: `class ConfigInvalidError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 93: `class ConfigTypeMismatchError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 119: `class InitializationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 142: `class ComponentInitializationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 163: `class DependencyNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 186: `class DependencyResolutionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 206: `class DependencyCycleError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 226: `class ObjectNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 252: `class ObjectInvalidError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 277: `class ObjectPropertyError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 300: `class SerializationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 320: `class DeserializationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 341: `class ProtocolValidationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 361: `class InterfaceMethodError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 382: `class OperationFailedError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 402: `class NotImplementedError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 420: `class InternalError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/fastapi_error_handlers.py

#### Legacy Class Name (13)
- Line 9: `with the Uno error system. These handlers convert UnoError objects to`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 21: `from uno.core.errors.base import UnoError, ErrorCode, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 40: `@app.exception_handler(UnoError)`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 41: `async def uno_error_handler(request: Request, exc: UnoError) -> JSONResponse:`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 43: `Handle UnoError exceptions.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 45: `This handler converts UnoError objects to JSONResponse with appropriate status code`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 50: `exc: The UnoError exception`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 55: `logger.error(f"UnoError: {exc}", exc_info=True)`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 222: `def _build_error_response(exc: UnoError, include_traceback: bool = False) -> Dict[str, Any]:`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 224: `Build a standardized error response from an UnoError.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 227: `exc: The UnoError exception`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 304: `if not isinstance(exc, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 305: `exc = UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/errors/examples.py

#### Legacy Class Name (13)
- Line 9: `It demonstrates how to use UnoError, context, and the Result pattern.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 17: `UnoError, ErrorCode, with_error_context, with_async_error_context,`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 33: `Demonstrate basic error handling with UnoError.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 63: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 68: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 85: `Demonstrate error context with UnoError.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 95: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 131: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 140: `except UnoError as e:`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 196: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 205: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 248: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 256: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/api/domain_repositories.py

#### Legacy Class Name (13)
- Line 17: `from uno.core.errors.catalog import ErrorCodes, UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 241: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 251: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 273: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 283: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 449: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 459: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 489: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 499: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 806: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 816: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 842: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 852: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/reports/models.py

#### Legacy Class Name (12)
- Line 18: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 27: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 106: `class ReportFieldConfigModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 134: `class ReportFieldModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 160: `class ReportTypeModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 183: `class ReportModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 207: `class ReportTemplateModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 261: `class ReportFieldDefinitionModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 321: `class ReportTriggerModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 380: `class ReportOutputModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 428: `class ReportExecutionModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 496: `class ReportOutputExecutionModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 18: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/infrastructure/reports/errors.py

#### Legacy Class Name (13)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 55: `class ReportError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 80: `class ReportTemplateNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 98: `class ReportTemplateAlreadyExistsError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 116: `class ReportTemplateInvalidError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 140: `class ReportFieldNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 158: `class ReportFieldInvalidError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 185: `class ReportExecutionFailedError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 211: `class ReportExecutionNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 230: `class ReportOutputFormatInvalidError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 253: `class ReportOutputDeliveryFailedError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 280: `class ReportTriggerNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 298: `class ReportTriggerInvalidError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/workflows/models.py

#### Legacy Class Name (11)
- Line 28: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 89: `class WorkflowDefinition(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 146: `class WorkflowTriggerModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 194: `class WorkflowConditionModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 249: `class WorkflowActionModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 306: `class WorkflowRecipientModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 355: `class WorkflowExecutionLog(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 418: `class Workflow(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 429: `class TaskType(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 536: `class Task(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 565: `class TaskRecord(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 28: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/application/workflows/executor.py

#### Legacy Class Name (12)
- Line 173: `return Failure(UnoError(f"Error executing notification action: {str(e)}"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 307: `return Failure(UnoError(f"Error executing email action: {str(e)}"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 389: `return Failure(UnoError("No URL provided for webhook action"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 478: `return Failure(UnoError(f"Error executing webhook action: {str(e)}"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 509: `return Failure(UnoError("No target table provided for database action"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 515: `UnoError("No field mappings provided for database action")`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 569: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 625: `UnoError(f"Unsupported database operation: {operation}")`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 630: `return Failure(UnoError(f"Error executing database action: {str(e)}"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 666: `return Failure(UnoError("No executor type provided for custom action"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 672: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 695: `return Failure(UnoError(f"Error executing custom action: {str(e)}"))`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/values/models.py

#### Legacy Class Name (10)
- Line 15: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 27: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 52: `class AttachmentModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 73: `class BooleanValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 92: `class DateTimeValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 111: `class DateValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 128: `class DecimalValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 145: `class IntegerValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 162: `class TextValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 179: `class TimeValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 15: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/dependencies/modern_provider.py

#### Legacy Class Name (11)
- Line 48: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 104: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 119: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 258: `UnoError: If the service provider is not initialized`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 262: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 293: `UnoError: If the service provider is not initialized`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 297: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 323: `UnoError: If the service provider is not initialized`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 327: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 350: `UnoError: If the service provider is not initialized`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 354: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/devtools/codegen/model.py

#### Legacy Class Name (10)
- Line 4: `This module provides tools for generating UnoModel and UnoDTO classes.`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 4: `This module provides tools for generating UnoModel and UnoDTO classes.`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 28: `base_model_class: str = "UnoModel",`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 29: `base_dto_class: str = "UnoDTO",`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 36: `"""Generate a UnoModel class with an optional UnoDTO.`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 36: `"""Generate a UnoModel class with an optional UnoDTO.`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 43: `include_schema: Whether to generate a UnoDTO class`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 137: `include_schema: Whether to generate a UnoDTO class`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 198: `"""Generate a UnoModel class definition.`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 274: `"""Generate a UnoDTO class definition.`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

#### Deprecated Import (1)
- Line 158: `imports.append(f"from uno.model import {base_model_class}")`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/infrastructure/authorization/models.py

#### Legacy Class Name (10)
- Line 25: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 33: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 61: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 89: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 115: `class UserModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 196: `class GroupModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 237: `class ResponsibilityRoleModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 266: `class RoleModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 325: `class TenantModel(ModelMixin, UnoModel, RecordAuditModelMixin):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 364: `class PermissionModel(UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 25: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/attributes/errors.py

#### Legacy Class Name (10)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 50: `class AttributeNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 68: `class AttributeTypeNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 86: `class AttributeInvalidDataError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 104: `class AttributeTypeInvalidDataError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 122: `class AttributeValueError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 148: `class AttributeServiceError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 171: `class AttributeTypeServiceError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 194: `class AttributeValidationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 220: `class AttributeGraphError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/sql/errors.py

#### Legacy Class Name (10)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 51: `class SQLStatementError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 74: `class SQLExecutionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 97: `class SQLSyntaxError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 121: `class SQLEmitterError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 144: `class SQLEmitterInvalidConfigError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 171: `class SQLRegistryClassNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 189: `class SQLRegistryClassAlreadyExistsError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 208: `class SQLConfigError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 231: `class SQLConfigInvalidError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/workflows/errors.py

#### Legacy Class Name (9)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 47: `class WorkflowNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 65: `class WorkflowInvalidDefinitionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 88: `class WorkflowExecutionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 112: `class WorkflowActionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 138: `class WorkflowConditionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 166: `class WorkflowEventError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 185: `class WorkflowQueryError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 207: `class WorkflowRecipientError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/errors/base.py

#### Legacy Class Name (8)
- Line 295: `class UnoError(Exception):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 305: `Initialize a UnoError.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 406: `class ValidationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 451: `class EntityNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 473: `class AuthorizationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 507: `class DatabaseError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 537: `class ConfigurationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 563: `class DependencyError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/attributes/models.py

#### Legacy Class Name (7)
- Line 14: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 22: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 45: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 69: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 93: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 115: `class AttributeTypeModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 238: `class AttributeModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 14: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/api/domain_services.py

#### Legacy Class Name (8)
- Line 17: `from uno.core.errors.catalog import ErrorCodes, UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 337: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 349: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 460: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 524: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 535: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 586: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 599: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/queries/models.py

#### Legacy Class Name (7)
- Line 18: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 26: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 47: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 68: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 88: `class QueryPathModel(ModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 148: `class QueryValueModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 208: `class QueryModel(DefaultModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 18: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/infrastructure/database/pg_error_handler.py

#### Legacy Class Name (8)
- Line 19: `from uno.core.errors.base import UnoError, ErrorContext`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 402: `PG_ERROR_MAPPING: Dict[str, Type[UnoError]] = {`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 514: `default_error_class: Type[UnoError] = DatabaseQueryError,`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 516: `) -> UnoError:`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 518: `Map a PostgreSQL exception to a appropriate UnoError.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 527: `An appropriate UnoError subclass instance`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 623: `UnoError: An appropriate UnoError if a PostgreSQL error occurs`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 629: `if isinstance(ex, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/values/errors.py

#### Legacy Class Name (7)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 43: `class ValueNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 66: `class ValueInvalidDataError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 89: `class ValueTypeMismatchError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 109: `class ValueValidationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 132: `class ValueServiceError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 155: `class ValueRepositoryError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/devtools/debugging/error_enhancer.py

#### Legacy Class Name (7)
- Line 16: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 75: `class EnhancedUnoError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 76: `"""Enhanced version of UnoError with additional debugging information."""`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 264: `"""Hook to enhance UnoError instances.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 272: `if isinstance(error, UnoError) and not isinstance(error, EnhancedUnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 313: `if isinstance(error, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 363: `if not isinstance(error, UnoError) and not isinstance(error, EnhancedUnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/queries/errors.py

#### Legacy Class Name (7)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 46: `class QueryNotFoundError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 64: `class QueryInvalidDataError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 82: `class QueryExecutionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 105: `class QueryPathError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 128: `class QueryValueError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 151: `class FilterError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/database/enhanced_db.py

#### Legacy Class Name (5)
- Line 44: `from uno.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 46: `T = TypeVar('T', bound=UnoModel)`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 514: `def _get_model_class_by_name(self, name: str) -> Type[UnoModel]:`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 530: `from uno.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 536: `issubclass(obj, UnoModel) and`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (2)
- Line 44: `from uno.model import UnoModel`
  - Suggestion: Use from uno.domain.base.model import
- Line 530: `from uno.model import UnoModel`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/examples/ecommerce_app/catalog/repository/models.py

#### Legacy Class Name (5)
- Line 17: `from uno.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 31: `class ProductModel(UnoModel, Base):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 82: `class ProductVariantModel(UnoModel, Base):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 112: `class ProductImageModel(UnoModel, Base):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 132: `class CategoryModel(UnoModel, Base):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 17: `from uno.model import UnoModel`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/application/workflows/provider.py

#### Legacy Class Name (6)
- Line 13: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 364: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 379: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 438: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 458: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 475: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/database/db.py

#### Legacy Class Name (6)
- Line 170: `raise UnoError(f"Unknown error occurred: {e}", "UNKNOWN_ERROR") from e`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 195: `raise UnoError(f"Unknown error occurred: {e}") from e`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 215: `UnoError: For other errors`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 269: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 296: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 376: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/examples/modern_architecture_example.py

#### Legacy Class Name (5)
- Line 5: `1. Modern error handling with UnoError, Result pattern, and error catalog`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 19: `from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 109: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 115: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 121: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/di_testing.py

#### Legacy Class Name (5)
- Line 13: `from .errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 70: `UnoError: If the test container is not set up`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 73: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 88: `UnoError: If the test container is not set up`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 91: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/dependencies/service.py

#### Legacy Class Name (4)
- Line 12: `from uno.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 14: `from uno.dependencies.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 17: `ModelT = TypeVar('ModelT', bound=UnoModel)`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 21: `class UnoService(UnoServiceProtocol[T], Generic[ModelT, T]):`
  - Suggestion: Replace with BaseService and import from uno.core.base.service

#### Deprecated Import (1)
- Line 12: `from uno.model import UnoModel`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/infrastructure/messaging/models.py

#### Legacy Class Name (4)
- Line 15: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 29: `UnoModel.metadata,`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 49: `class MessageModel(GroupModelMixin, ModelMixin, UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 118: `class MessageUserModel(UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 15: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/domain/exceptions.py

#### Backward Compatibility (2)
- Line 13: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 16: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

#### Legacy Class Name (3)
- Line 21: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 24: `class DomainError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 31: `DEPRECATED: Use UnoError from uno.core.errors.base instead.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/meta/models.py

#### Legacy Class Name (3)
- Line 8: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 11: `class MetaTypeModel(UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 22: `class MetaRecordModel(UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 8: `from uno.model import UnoModel, PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

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

### src/uno/devtools/codegen/service.py

#### Legacy Class Name (4)
- Line 20: `base_class: str = "UnoService",`
  - Suggestion: Replace with BaseService and import from uno.core.base.service
- Line 62: `"from uno.core.errors import UnoError"`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 66: `if base_class == "UnoService":`
  - Suggestion: Replace with BaseService and import from uno.core.base.service
- Line 67: `import_statements.append("from uno.domain.service import UnoService")`
  - Suggestion: Replace with BaseService and import from uno.core.base.service

### src/uno/devtools/codegen/project.py

#### Legacy Class Name (4)
- Line 538: `from uno.database.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 541: `class {name.capitalize()}(UnoModel):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 566: `from uno.database.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 572: `class {name.capitalize()}Repository(UnoRepository):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/examples/ecommerce_app/main.py

#### Legacy Class Name (4)
- Line 14: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 48: `@app.exception_handler(UnoError)`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 49: `async def uno_error_handler(request: Request, exc: UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 50: `"""Handle UnoError exceptions and convert to appropriate HTTP responses."""`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/workflows/integration.py

#### Legacy Class Name (4)
- Line 19: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 136: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 150: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 172: `UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/domain/specification_translators/postgresql.py

#### Legacy Class Name (3)
- Line 33: `from uno.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 37: `M = TypeVar('M', bound=UnoModel)`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 49: `def __init__(self, model_class: Type[UnoModel]):`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 33: `from uno.model import UnoModel`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/migrations/env.py

#### Legacy Class Name (2)
- Line 14: `from uno.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 46: `target_metadata = UnoModel.metadata`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 14: `from uno.model import UnoModel`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/core/examples/monitoring_example.py

#### Legacy Class Name (3)
- Line 40: `UnoError, ErrorCode, Result, Success, Failure, of, failure, from_exception,`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 153: `return failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 297: `if isinstance(error, UnoError) and error.error_code == ErrorCode.RESOURCE_NOT_FOUND:`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/examples/error_handling_example.py

#### Legacy Class Name (3)
- Line 5: `UnoError, Result pattern, and contextual error information.`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 12: `UnoError, ErrorCode, add_error_context, with_error_context, with_async_error_context`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 91: `return Failure(UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/errors/security.py

#### Legacy Class Name (3)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCode`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 16: `class AuthenticationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 41: `class AuthorizationError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/errors/__init__.py

#### Legacy Class Name (3)
- Line 9: `1. Structured exceptions with error codes (UnoError)`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 18: `UnoError,`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 61: `"UnoError",`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/meta/repositories.py

#### Legacy Class Name (3)
- Line 14: `from uno.dependencies.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 18: `class MetaTypeRepository(UnoRepository[MetaTypeModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 60: `class MetaRecordRepository(UnoRepository[MetaRecordModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/dependencies/testing.py

#### Legacy Class Name (2)
- Line 20: `from uno.model import UnoModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 23: `ModelT = TypeVar('ModelT', bound=UnoModel)`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 20: `from uno.model import UnoModel`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/attributes/repositories.py

#### Legacy Class Name (3)
- Line 19: `from uno.database.repository import UnoBaseRepository as UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 34: `class AttributeRepository(UnoRepository, AttributeRepositoryProtocol):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 369: `class AttributeTypeRepository(UnoRepository, AttributeTypeRepositoryProtocol):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/devtools/debugging/middleware.py

#### Legacy Class Name (3)
- Line 22: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 243: `if isinstance(exc, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 308: `if isinstance(exc, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/api/service_endpoint_adapter.py

#### Legacy Class Name (3)
- Line 19: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 217: `if isinstance(error, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 434: `if isinstance(error, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/authorization/repositories.py

#### Legacy Class Name (3)
- Line 15: `from uno.dependencies.repository import UnoRepository`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 26: `class UserRepository(UnoRepository[UserModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository
- Line 195: `class GroupRepository(UnoRepository[GroupModel]):`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

### src/uno/infrastructure/services/factory.py

#### Legacy Class Name (3)
- Line 15: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 85: `UnoError: If service creation fails`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 116: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/sql/config.py

#### Legacy Class Name (3)
- Line 66: `UnoError: If a subclass with the same name already exists in the registry`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 99: `UnoError: If SQL emission fails`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 116: `raise UnoError(f"Failed to emit SQL: {e}", "SQL_EMISSION_ERROR")`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/sql/registry.py

#### Legacy Class Name (3)
- Line 44: `UnoError: If a class with the same name already exists in the registry`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 52: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 96: `UnoError: If SQL emission fails`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/sql/emitters/database.py

#### Legacy Class Name (3)
- Line 19: `from uno.core.errors import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 287: `UnoError: If the PGULID SQL file cannot be read`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 311: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/dto/dto_manager.py

#### Legacy Class Name (2)
- Line 141: `and SQLAlchemy models like UnoModel.`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 144: `model: The model to create a list schema for (can be BaseModel or UnoModel)`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

### src/uno/enums.py

#### Legacy Class Name (2)
- Line 67: `Enumeration class for UnoModel match types.`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 88: `Tenants are a key concept in the UnoModel library.`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

### src/uno/core/__init__.py

#### Legacy Class Name (2)
- Line 56: `from uno.core.errors.base import ErrorCategory, UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 136: `"UnoError",`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/errors/logging.py

#### Legacy Class Name (2)
- Line 23: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 149: `if isinstance(exc_value, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/errors/result.py

#### Legacy Class Name (2)
- Line 15: `from uno.core.errors.base import UnoError, ErrorCode, get_error_context`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 306: `if isinstance(self.error, UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/monitoring/dashboard.py

#### Legacy Class Name (2)
- Line 38: `from uno.core.errors import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 148: `raise UnoError(`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/base/service.py

#### Legacy Class Name (2)
- Line 13: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 192: `except UnoError as e:`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/model.py

#### Backward Compatibility (1)
- Line 177: `# For backward compatibility only - use BaseModel directly in new code`
  - Suggestion: Potential backward compatibility layer - consider removing

#### Legacy Class Name (1)
- Line 178: `UnoModel = BaseModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

### src/uno/devtools/cli/codegen.py

#### Legacy Class Name (2)
- Line 51: `"""Generate a UnoModel class."""`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model
- Line 224: `model_parser = generate_subparsers.add_parser("model", help="Generate a UnoModel class")`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

### src/uno/devtools/codegen/api.py

#### Deprecated Import (2)
- Line 175: `imports.append(f"from uno.model import {model_name}")`
  - Suggestion: Use from uno.domain.base.model import
- Line 177: `imports.append(f"from uno.repository import {repository_name}")`
  - Suggestion: Use from uno.core.base.repository import

### src/uno/devtools/codegen/repository.py

#### Legacy Class Name (1)
- Line 29: `base_repository_class: str = "UnoRepository",`
  - Suggestion: Replace with BaseRepository and import from uno.core.base.repository

#### Deprecated Import (1)
- Line 135: `imports.append(f"from uno.model import {model_name}")`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/api/domain_endpoints.py

#### Legacy Class Name (2)
- Line 16: `from uno.core.errors import UnoError, ErrorCodes`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 155: `error: UnoError = result.error`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/dto/__init__.py

#### Legacy Class Name (2)
- Line 13: `from .dto import UnoDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto
- Line 17: `"UnoDTO",`
  - Suggestion: Replace with BaseDTO and import from uno.core.base.dto

### src/uno/application/queries/optimized_queries.py

#### Legacy Class Name (1)
- Line 33: `from uno.model import UnoModel as Model`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 33: `from uno.model import UnoModel as Model`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/application/queries/batch_operations.py

#### Legacy Class Name (1)
- Line 36: `from uno.model import UnoModel as Model`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 36: `from uno.model import UnoModel as Model`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/application/queries/common_patterns.py

#### Legacy Class Name (1)
- Line 34: `from uno.model import UnoModel as Model`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

#### Deprecated Import (1)
- Line 34: `from uno.model import UnoModel as Model`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/application/workflows/recipients.py

#### Legacy Class Name (2)
- Line 35: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 48: `class RecipientError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/workflows/conditions.py

#### Legacy Class Name (2)
- Line 37: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 52: `class ConditionError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/application/workflows/engine.py

#### Legacy Class Name (2)
- Line 15: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 51: `class WorkflowEngineError(UnoError):`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/sql/classes.py

#### Backward Compatibility (2)
- Line 24: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 27: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/infrastructure/sql/emitter.py

#### Legacy Class Name (2)
- Line 209: `UnoError: If SQL execution fails`
  - Suggestion: Replace with BaseError and import from uno.core.base.error
- Line 262: `UnoError: If SQL execution fails`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/domain/__init__.py

#### Backward Compatibility (2)
- Line 327: `warnings.warn(`
  - Suggestion: Potential backward compatibility layer - consider removing
- Line 339: `DeprecationWarning,`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/domain/base/model.py

#### Backward Compatibility (1)
- Line 177: `# For backward compatibility only - use BaseModel directly in new code`
  - Suggestion: Potential backward compatibility layer - consider removing

#### Legacy Class Name (1)
- Line 178: `UnoModel = BaseModel`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

### src/uno/mixins.py

#### Deprecated Import (1)
- Line 15: `from uno.model import PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/core/examples/resource_example.py

#### Deprecated Import (1)
- Line 19: `from uno.core.async_manager import get_async_manager, run_application`
  - Suggestion: Use from uno.core.async.task_manager import

### src/uno/core/examples/batch_operations_example.py

#### Deprecated Import (1)
- Line 20: `from uno.model import Model`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/core/examples/async_example.py

#### Deprecated Import (1)
- Line 12: `from uno.core.async_manager import (`
  - Suggestion: Use from uno.core.async.task_manager import

### src/uno/core/errors/validation.py

#### Legacy Class Name (1)
- Line 13: `from uno.core.errors.base import UnoError, ErrorCode, ValidationError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/core/fastapi_integration.py

#### Deprecated Import (1)
- Line 15: `from uno.core.async_manager import get_async_manager`
  - Suggestion: Use from uno.core.async.task_manager import

### src/uno/devtools/docs/extractors.py

#### Legacy Class Name (1)
- Line 1004: `any(base.__name__ in ("UnoModel", "BaseModel", "Model") for base in obj.__mro__) or`
  - Suggestion: Replace with BaseModel and import from uno.domain.base.model

### src/uno/api/error_handlers.py

#### Legacy Class Name (1)
- Line 21: `from uno.core.errors.base import UnoError, ValidationError, NotFoundError, AuthorizationError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error

### src/uno/infrastructure/repositories/__init__.py

#### Backward Compatibility (1)
- Line 42: `# For backward compatibility`
  - Suggestion: Potential backward compatibility layer - consider removing

### src/uno/infrastructure/authorization/mixins.py

#### Deprecated Import (1)
- Line 16: `from uno.model import PostgresTypes`
  - Suggestion: Use from uno.domain.base.model import

### src/uno/infrastructure/services/di.py

#### Legacy Class Name (1)
- Line 12: `from uno.core.errors.base import UnoError`
  - Suggestion: Replace with BaseError and import from uno.core.base.error