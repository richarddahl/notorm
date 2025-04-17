# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
PostgreSQL error handler.

Maps PostgreSQL error codes to application error types and provides
utilities for handling specific database errors.
"""

from typing import Dict, Type, Optional, Any, Callable, Union, TypeVar, cast, List
import asyncio
import logging
import re
from functools import wraps

# Import error types
from uno.core.errors.base import UnoError, ErrorContext
from uno.database.errors import (
    DatabaseErrorCode,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    DatabaseTransactionError,
    DatabaseTransactionRollbackError,
    DatabaseTransactionConflictError,
    DatabaseIntegrityError,
    DatabaseUniqueViolationError,
    DatabaseForeignKeyViolationError,
    DatabaseQueryError,
    DatabaseQueryTimeoutError,
    DatabaseQuerySyntaxError,
    DatabaseResourceNotFoundError,
    DatabaseTableNotFoundError,
    DatabaseColumnNotFoundError,
    DatabaseSessionError,
    DatabaseOperationalError,
)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Logger
logger = logging.getLogger(__name__)

# Regular expression patterns for extracting error details from PostgreSQL error messages
CONSTRAINT_NAME_PATTERN = re.compile(r'constraint "([^"]+)"')
RELATION_NAME_PATTERN = re.compile(r'relation "([^"]+)"')
COLUMN_NAME_PATTERN = re.compile(r'column "([^"]+)"')
DETAIL_PATTERN = re.compile(r'DETAIL:\s+(.+?)(?:\n|$)')


class PostgresErrorCode:
    """PostgreSQL error codes from the PostgreSQL documentation."""
    
    # Class 00 — Successful Completion
    SUCCESSFUL_COMPLETION = '00000'
    
    # Class 01 — Warning
    WARNING = '01000'
    DYNAMIC_RESULT_SETS_RETURNED = '0100C'
    IMPLICIT_ZERO_BIT_PADDING = '01008'
    NULL_VALUE_ELIMINATED_IN_SET_FUNCTION = '01003'
    PRIVILEGE_NOT_GRANTED = '01007'
    PRIVILEGE_NOT_REVOKED = '01006'
    STRING_DATA_RIGHT_TRUNCATION_WARNING = '01004'
    DEPRECATED_FEATURE = '01P01'
    
    # Class 02 — No Data
    NO_DATA = '02000'
    NO_ADDITIONAL_DYNAMIC_RESULT_SETS_RETURNED = '02001'
    
    # Class 03 — SQL Statement Not Yet Complete
    SQL_STATEMENT_NOT_YET_COMPLETE = '03000'
    
    # Class 08 — Connection Exception
    CONNECTION_EXCEPTION = '08000'
    CONNECTION_DOES_NOT_EXIST = '08003'
    CONNECTION_FAILURE = '08006'
    SQLCLIENT_UNABLE_TO_ESTABLISH_SQLCONNECTION = '08001'
    SQLSERVER_REJECTED_ESTABLISHMENT_OF_SQLCONNECTION = '08004'
    TRANSACTION_RESOLUTION_UNKNOWN = '08007'
    PROTOCOL_VIOLATION = '08P01'
    
    # Class 09 — Triggered Action Exception
    TRIGGERED_ACTION_EXCEPTION = '09000'
    
    # Class 0A — Feature Not Supported
    FEATURE_NOT_SUPPORTED = '0A000'
    
    # Class 0B — Invalid Transaction Initiation
    INVALID_TRANSACTION_INITIATION = '0B000'
    
    # Class 0F — Locator Exception
    LOCATOR_EXCEPTION = '0F000'
    INVALID_LOCATOR_SPECIFICATION = '0F001'
    
    # Class 0L — Invalid Grantor
    INVALID_GRANTOR = '0L000'
    INVALID_GRANT_OPERATION = '0LP01'
    
    # Class 0P — Invalid Role Specification
    INVALID_ROLE_SPECIFICATION = '0P000'
    
    # Class 0Z — Diagnostics Exception
    DIAGNOSTICS_EXCEPTION = '0Z000'
    STACKED_DIAGNOSTICS_ACCESSED_WITHOUT_ACTIVE_HANDLER = '0Z002'
    
    # Class 20 — Case Not Found
    CASE_NOT_FOUND = '20000'
    
    # Class 21 — Cardinality Violation
    CARDINALITY_VIOLATION = '21000'
    
    # Class 22 — Data Exception
    DATA_EXCEPTION = '22000'
    ARRAY_SUBSCRIPT_ERROR = '2202E'
    CHARACTER_NOT_IN_REPERTOIRE = '22021'
    DATETIME_FIELD_OVERFLOW = '22008'
    DIVISION_BY_ZERO = '22012'
    ERROR_IN_ASSIGNMENT = '22005'
    ESCAPE_CHARACTER_CONFLICT = '2200B'
    INDICATOR_OVERFLOW = '22022'
    INTERVAL_FIELD_OVERFLOW = '22015'
    INVALID_ARGUMENT_FOR_LOGARITHM = '2201E'
    INVALID_ARGUMENT_FOR_NTILE_FUNCTION = '22014'
    INVALID_ARGUMENT_FOR_NTH_VALUE_FUNCTION = '22016'
    INVALID_ARGUMENT_FOR_POWER_FUNCTION = '2201F'
    INVALID_ARGUMENT_FOR_WIDTH_BUCKET_FUNCTION = '2201G'
    INVALID_CHARACTER_VALUE_FOR_CAST = '22018'
    INVALID_DATETIME_FORMAT = '22007'
    INVALID_ESCAPE_CHARACTER = '22019'
    INVALID_ESCAPE_OCTET = '2200D'
    INVALID_ESCAPE_SEQUENCE = '22025'
    NONSTANDARD_USE_OF_ESCAPE_CHARACTER = '22P06'
    INVALID_INDICATOR_PARAMETER_VALUE = '22010'
    INVALID_PARAMETER_VALUE = '22023'
    INVALID_REGULAR_EXPRESSION = '2201B'
    INVALID_ROW_COUNT_IN_LIMIT_CLAUSE = '2201W'
    INVALID_ROW_COUNT_IN_RESULT_OFFSET_CLAUSE = '2201X'
    INVALID_TABLESAMPLE_ARGUMENT = '2202H'
    INVALID_TABLESAMPLE_REPEAT = '2202G'
    INVALID_TIME_ZONE_DISPLACEMENT_VALUE = '22009'
    INVALID_USE_OF_ESCAPE_CHARACTER = '2200C'
    MOST_SPECIFIC_TYPE_MISMATCH = '2200G'
    NULL_VALUE_NOT_ALLOWED = '22004'
    NULL_VALUE_NO_INDICATOR_PARAMETER = '22002'
    NUMERIC_VALUE_OUT_OF_RANGE = '22003'
    SEQUENCE_GENERATOR_LIMIT_EXCEEDED = '2200H'
    STRING_DATA_LENGTH_MISMATCH = '22026'
    STRING_DATA_RIGHT_TRUNCATION = '22001'
    SUBSTRING_ERROR = '22011'
    TRIM_ERROR = '22027'
    UNTERMINATED_C_STRING = '22024'
    ZERO_LENGTH_CHARACTER_STRING = '2200F'
    FLOATING_POINT_EXCEPTION = '22P01'
    INVALID_TEXT_REPRESENTATION = '22P02'
    INVALID_BINARY_REPRESENTATION = '22P03'
    BAD_COPY_FILE_FORMAT = '22P04'
    UNTRANSLATABLE_CHARACTER = '22P05'
    NOT_AN_XML_DOCUMENT = '2200L'
    INVALID_XML_DOCUMENT = '2200M'
    INVALID_XML_CONTENT = '2200N'
    INVALID_XML_COMMENT = '2200S'
    INVALID_XML_PROCESSING_INSTRUCTION = '2200T'
    DUPLICATE_JSON_OBJECT_KEY_VALUE = '22030'
    INVALID_JSON_TEXT = '22032'
    INVALID_SQL_JSON_SUBSCRIPT = '22033'
    MORE_THAN_ONE_SQL_JSON_ITEM = '22034'
    NO_SQL_JSON_ITEM = '22035'
    NON_NUMERIC_SQL_JSON_ITEM = '22036'
    NON_UNIQUE_KEYS_IN_A_JSON_OBJECT = '22037'
    SINGLETON_SQL_JSON_ITEM_REQUIRED = '22038'
    SQL_JSON_ARRAY_NOT_FOUND = '22039'
    SQL_JSON_MEMBER_NOT_FOUND = '2203A'
    SQL_JSON_NUMBER_NOT_FOUND = '2203B'
    SQL_JSON_OBJECT_NOT_FOUND = '2203C'
    TOO_MANY_JSON_ARRAY_ELEMENTS = '2203D'
    TOO_MANY_JSON_OBJECT_MEMBERS = '2203E'
    SQL_JSON_SCALAR_REQUIRED = '2203F'
    SQL_JSON_ITEM_CANNOT_BE_CAST_TO_TARGET_TYPE = '2203G'
    
    # Class 23 — Integrity Constraint Violation
    INTEGRITY_CONSTRAINT_VIOLATION = '23000'
    RESTRICT_VIOLATION = '23001'
    NOT_NULL_VIOLATION = '23502'
    FOREIGN_KEY_VIOLATION = '23503'
    UNIQUE_VIOLATION = '23505'
    CHECK_VIOLATION = '23514'
    EXCLUSION_VIOLATION = '23P01'
    
    # Class 24 — Invalid Cursor State
    INVALID_CURSOR_STATE = '24000'
    
    # Class 25 — Invalid Transaction State
    INVALID_TRANSACTION_STATE = '25000'
    ACTIVE_SQL_TRANSACTION = '25001'
    BRANCH_TRANSACTION_ALREADY_ACTIVE = '25002'
    HELD_CURSOR_REQUIRES_SAME_ISOLATION_LEVEL = '25008'
    INAPPROPRIATE_ACCESS_MODE_FOR_BRANCH_TRANSACTION = '25003'
    INAPPROPRIATE_ISOLATION_LEVEL_FOR_BRANCH_TRANSACTION = '25004'
    NO_ACTIVE_SQL_TRANSACTION_FOR_BRANCH_TRANSACTION = '25005'
    READ_ONLY_SQL_TRANSACTION = '25006'
    SCHEMA_AND_DATA_STATEMENT_MIXING_NOT_SUPPORTED = '25007'
    NO_ACTIVE_SQL_TRANSACTION = '25P01'
    IN_FAILED_SQL_TRANSACTION = '25P02'
    IDLE_IN_TRANSACTION_SESSION_TIMEOUT = '25P03'
    
    # Class 26 — Invalid SQL Statement Name
    INVALID_SQL_STATEMENT_NAME = '26000'
    
    # Class 27 — Triggered Data Change Violation
    TRIGGERED_DATA_CHANGE_VIOLATION = '27000'
    
    # Class 28 — Invalid Authorization Specification
    INVALID_AUTHORIZATION_SPECIFICATION = '28000'
    INVALID_PASSWORD = '28P01'
    
    # Class 2B — Dependent Privilege Descriptors Still Exist
    DEPENDENT_PRIVILEGE_DESCRIPTORS_STILL_EXIST = '2B000'
    DEPENDENT_OBJECTS_STILL_EXIST = '2BP01'
    
    # Class 2D — Invalid Transaction Termination
    INVALID_TRANSACTION_TERMINATION = '2D000'
    
    # Class 2F — SQL Routine Exception
    SQL_ROUTINE_EXCEPTION = '2F000'
    FUNCTION_EXECUTED_NO_RETURN_STATEMENT = '2F005'
    MODIFYING_SQL_DATA_NOT_PERMITTED = '2F002'
    PROHIBITED_SQL_STATEMENT_ATTEMPTED = '2F003'
    READING_SQL_DATA_NOT_PERMITTED = '2F004'
    
    # Class 34 — Invalid Cursor Name
    INVALID_CURSOR_NAME = '34000'
    
    # Class 38 — External Routine Exception
    EXTERNAL_ROUTINE_EXCEPTION = '38000'
    CONTAINING_SQL_NOT_PERMITTED = '38001'
    MODIFYING_SQL_DATA_NOT_PERMITTED_EXTERNAL = '38002'
    PROHIBITED_SQL_STATEMENT_ATTEMPTED_EXTERNAL = '38003'
    READING_SQL_DATA_NOT_PERMITTED_EXTERNAL = '38004'
    
    # Class 39 — External Routine Invocation Exception
    EXTERNAL_ROUTINE_INVOCATION_EXCEPTION = '39000'
    INVALID_SQLSTATE_RETURNED = '39001'
    NULL_VALUE_NOT_ALLOWED_EXTERNAL = '39004'
    TRIGGER_PROTOCOL_VIOLATED = '39P01'
    SRF_PROTOCOL_VIOLATED = '39P02'
    EVENT_TRIGGER_PROTOCOL_VIOLATED = '39P03'
    
    # Class 3B — Savepoint Exception
    SAVEPOINT_EXCEPTION = '3B000'
    INVALID_SAVEPOINT_SPECIFICATION = '3B001'
    
    # Class 3D — Invalid Catalog Name
    INVALID_CATALOG_NAME = '3D000'
    
    # Class 3F — Invalid Schema Name
    INVALID_SCHEMA_NAME = '3F000'
    
    # Class 40 — Transaction Rollback
    TRANSACTION_ROLLBACK = '40000'
    TRANSACTION_INTEGRITY_CONSTRAINT_VIOLATION = '40002'
    SERIALIZATION_FAILURE = '40001'
    STATEMENT_COMPLETION_UNKNOWN = '40003'
    DEADLOCK_DETECTED = '40P01'
    
    # Class 42 — Syntax Error or Access Rule Violation
    SYNTAX_ERROR_OR_ACCESS_RULE_VIOLATION = '42000'
    SYNTAX_ERROR = '42601'
    INSUFFICIENT_PRIVILEGE = '42501'
    CANNOT_COERCE = '42846'
    GROUPING_ERROR = '42803'
    WINDOWING_ERROR = '42P20'
    INVALID_RECURSION = '42P19'
    INVALID_FOREIGN_KEY = '42830'
    INVALID_NAME = '42602'
    NAME_TOO_LONG = '42622'
    RESERVED_NAME = '42939'
    DATATYPE_MISMATCH = '42804'
    INDETERMINATE_DATATYPE = '42P18'
    COLLATION_MISMATCH = '42P21'
    INDETERMINATE_COLLATION = '42P22'
    WRONG_OBJECT_TYPE = '42809'
    GENERATED_ALWAYS = '428C9'
    UNDEFINED_COLUMN = '42703'
    UNDEFINED_FUNCTION = '42883'
    UNDEFINED_TABLE = '42P01'
    UNDEFINED_PARAMETER = '42P02'
    UNDEFINED_OBJECT = '42704'
    DUPLICATE_COLUMN = '42701'
    DUPLICATE_CURSOR = '42P03'
    DUPLICATE_DATABASE = '42P04'
    DUPLICATE_FUNCTION = '42723'
    DUPLICATE_PREPARED_STATEMENT = '42P05'
    DUPLICATE_SCHEMA = '42P06'
    DUPLICATE_TABLE = '42P07'
    DUPLICATE_ALIAS = '42712'
    DUPLICATE_OBJECT = '42710'
    AMBIGUOUS_COLUMN = '42702'
    AMBIGUOUS_FUNCTION = '42725'
    AMBIGUOUS_PARAMETER = '42P08'
    AMBIGUOUS_ALIAS = '42P09'
    INVALID_COLUMN_REFERENCE = '42P10'
    INVALID_COLUMN_DEFINITION = '42611'
    INVALID_CURSOR_DEFINITION = '42P11'
    INVALID_DATABASE_DEFINITION = '42P12'
    INVALID_FUNCTION_DEFINITION = '42P13'
    INVALID_PREPARED_STATEMENT_DEFINITION = '42P14'
    INVALID_SCHEMA_DEFINITION = '42P15'
    INVALID_TABLE_DEFINITION = '42P16'
    INVALID_OBJECT_DEFINITION = '42P17'
    
    # Class 44 — WITH CHECK OPTION Violation
    WITH_CHECK_OPTION_VIOLATION = '44000'
    
    # Class 53 — Insufficient Resources
    INSUFFICIENT_RESOURCES = '53000'
    DISK_FULL = '53100'
    OUT_OF_MEMORY = '53200'
    TOO_MANY_CONNECTIONS = '53300'
    CONFIGURATION_LIMIT_EXCEEDED = '53400'
    
    # Class 54 — Program Limit Exceeded
    PROGRAM_LIMIT_EXCEEDED = '54000'
    STATEMENT_TOO_COMPLEX = '54001'
    TOO_MANY_COLUMNS = '54011'
    TOO_MANY_ARGUMENTS = '54023'
    
    # Class 55 — Object Not In Prerequisite State
    OBJECT_NOT_IN_PREREQUISITE_STATE = '55000'
    OBJECT_IN_USE = '55006'
    CANT_CHANGE_RUNTIME_PARAM = '55P02'
    LOCK_NOT_AVAILABLE = '55P03'
    UNSAFE_NEW_ENUM_VALUE_USAGE = '55P04'
    
    # Class 57 — Operator Intervention
    OPERATOR_INTERVENTION = '57000'
    QUERY_CANCELED = '57014'
    ADMIN_SHUTDOWN = '57P01'
    CRASH_SHUTDOWN = '57P02'
    CANNOT_CONNECT_NOW = '57P03'
    DATABASE_DROPPED = '57P04'
    
    # Class 58 — System Error
    SYSTEM_ERROR = '58000'
    IO_ERROR = '58030'
    UNDEFINED_FILE = '58P01'
    DUPLICATE_FILE = '58P02'
    
    # Class 72 — Snapshot Failure
    SNAPSHOT_TOO_OLD = '72000'
    
    # Class F0 — Configuration File Error
    CONFIG_FILE_ERROR = 'F0000'
    LOCK_FILE_EXISTS = 'F0001'
    
    # Class HV — Foreign Data Wrapper Error
    FDW_ERROR = 'HV000'
    FDW_COLUMN_NAME_NOT_FOUND = 'HV005'
    FDW_DYNAMIC_PARAMETER_VALUE_NEEDED = 'HV002'
    FDW_FUNCTION_SEQUENCE_ERROR = 'HV010'
    FDW_INCONSISTENT_DESCRIPTOR_INFORMATION = 'HV021'
    FDW_INVALID_ATTRIBUTE_VALUE = 'HV024'
    FDW_INVALID_COLUMN_NAME = 'HV007'
    FDW_INVALID_COLUMN_NUMBER = 'HV008'
    FDW_INVALID_DATA_TYPE = 'HV004'
    FDW_INVALID_DATA_TYPE_DESCRIPTORS = 'HV006'
    FDW_INVALID_DESCRIPTOR_FIELD_IDENTIFIER = 'HV091'
    FDW_INVALID_HANDLE = 'HV00B'
    FDW_INVALID_OPTION_INDEX = 'HV00C'
    FDW_INVALID_OPTION_NAME = 'HV00D'
    FDW_INVALID_STRING_LENGTH_OR_BUFFER_LENGTH = 'HV090'
    FDW_INVALID_STRING_FORMAT = 'HV00A'
    FDW_INVALID_USE_OF_NULL_POINTER = 'HV009'
    FDW_TOO_MANY_HANDLES = 'HV014'
    FDW_OUT_OF_MEMORY = 'HV001'
    FDW_NO_SCHEMAS = 'HV00P'
    FDW_OPTION_NAME_NOT_FOUND = 'HV00J'
    FDW_REPLY_HANDLE = 'HV00K'
    FDW_SCHEMA_NOT_FOUND = 'HV00Q'
    FDW_TABLE_NOT_FOUND = 'HV00R'
    FDW_UNABLE_TO_CREATE_EXECUTION = 'HV00L'
    FDW_UNABLE_TO_CREATE_REPLY = 'HV00M'
    FDW_UNABLE_TO_ESTABLISH_CONNECTION = 'HV00N'
    
    # Class P0 — PL/pgSQL Error
    PLPGSQL_ERROR = 'P0000'
    RAISE_EXCEPTION = 'P0001'
    NO_DATA_FOUND = 'P0002'
    TOO_MANY_ROWS = 'P0003'
    ASSERT_FAILURE = 'P0004'
    
    # Class XX — Internal Error
    INTERNAL_ERROR = 'XX000'
    DATA_CORRUPTED = 'XX001'
    INDEX_CORRUPTED = 'XX002'


# Map PostgreSQL error codes to UnoError subclasses
PG_ERROR_MAPPING: Dict[str, Type[UnoError]] = {
    # Connection errors
    PostgresErrorCode.CONNECTION_EXCEPTION: DatabaseConnectionError,
    PostgresErrorCode.CONNECTION_DOES_NOT_EXIST: DatabaseConnectionError,
    PostgresErrorCode.CONNECTION_FAILURE: DatabaseConnectionError,
    PostgresErrorCode.SQLCLIENT_UNABLE_TO_ESTABLISH_SQLCONNECTION: DatabaseConnectionError,
    PostgresErrorCode.SQLSERVER_REJECTED_ESTABLISHMENT_OF_SQLCONNECTION: DatabaseConnectionError,
    
    # Transaction errors
    PostgresErrorCode.TRANSACTION_ROLLBACK: DatabaseTransactionRollbackError,
    PostgresErrorCode.TRANSACTION_INTEGRITY_CONSTRAINT_VIOLATION: DatabaseTransactionRollbackError,
    PostgresErrorCode.SERIALIZATION_FAILURE: DatabaseTransactionConflictError,
    PostgresErrorCode.DEADLOCK_DETECTED: DatabaseTransactionConflictError,
    
    # Integrity constraint violations
    PostgresErrorCode.INTEGRITY_CONSTRAINT_VIOLATION: DatabaseIntegrityError,
    PostgresErrorCode.RESTRICT_VIOLATION: DatabaseIntegrityError,
    PostgresErrorCode.NOT_NULL_VIOLATION: DatabaseIntegrityError,
    PostgresErrorCode.FOREIGN_KEY_VIOLATION: DatabaseForeignKeyViolationError,
    PostgresErrorCode.UNIQUE_VIOLATION: DatabaseUniqueViolationError,
    PostgresErrorCode.CHECK_VIOLATION: DatabaseIntegrityError,
    PostgresErrorCode.EXCLUSION_VIOLATION: DatabaseIntegrityError,
    
    # Syntax errors
    PostgresErrorCode.SYNTAX_ERROR: DatabaseQuerySyntaxError,
    
    # Resource errors
    PostgresErrorCode.UNDEFINED_TABLE: DatabaseTableNotFoundError,
    PostgresErrorCode.UNDEFINED_COLUMN: DatabaseColumnNotFoundError,
    PostgresErrorCode.UNDEFINED_OBJECT: DatabaseResourceNotFoundError,
    
    # System errors
    PostgresErrorCode.INSUFFICIENT_RESOURCES: DatabaseOperationalError,
    PostgresErrorCode.DISK_FULL: DatabaseOperationalError,
    PostgresErrorCode.OUT_OF_MEMORY: DatabaseOperationalError,
    PostgresErrorCode.TOO_MANY_CONNECTIONS: DatabaseOperationalError,
    
    # Timeout and cancellation errors
    PostgresErrorCode.QUERY_CANCELED: DatabaseQueryTimeoutError,
    
    # Internal errors
    PostgresErrorCode.INTERNAL_ERROR: DatabaseOperationalError,
    PostgresErrorCode.DATA_CORRUPTED: DatabaseOperationalError,
    PostgresErrorCode.INDEX_CORRUPTED: DatabaseOperationalError,
}


def extract_pg_error_details(error_message: str) -> Dict[str, str]:
    """
    Extract useful details from a PostgreSQL error message.
    
    Args:
        error_message: The PostgreSQL error message
        
    Returns:
        A dictionary of extracted details such as constraint name, table name, etc.
    """
    details = {}
    
    # Try to extract constraint name
    constraint_match = CONSTRAINT_NAME_PATTERN.search(error_message)
    if constraint_match:
        details["constraint_name"] = constraint_match.group(1)
    
    # Try to extract relation/table name
    relation_match = RELATION_NAME_PATTERN.search(error_message)
    if relation_match:
        details["table_name"] = relation_match.group(1)
    
    # Try to extract column name
    column_match = COLUMN_NAME_PATTERN.search(error_message)
    if column_match:
        details["column_name"] = column_match.group(1)
    
    # Try to extract detail message
    detail_match = DETAIL_PATTERN.search(error_message)
    if detail_match:
        details["detail"] = detail_match.group(1)
    
    return details


def extract_pg_error_code(error: Exception) -> Optional[str]:
    """
    Extract the PostgreSQL error code from an exception.
    
    Args:
        error: The exception to extract from
        
    Returns:
        The PostgreSQL error code, or None if not found
    """
    if hasattr(error, 'pgcode'):
        return getattr(error, 'pgcode')
    
    # Some libraries nest the original exception
    if hasattr(error, '__cause__') and error.__cause__ is not None:
        return extract_pg_error_code(error.__cause__)
    
    # Look for error code in exception message (fallback)
    if hasattr(error, 'args') and len(error.args) > 0:
        msg = str(error.args[0])
        code_match = re.search(r'ERROR:\s+\w+:\s+(\w+):', msg)
        if code_match:
            return code_match.group(1)
    
    return None


def map_pg_exception_to_uno_error(
    ex: Exception,
    default_message: Optional[str] = None,
    default_error_class: Type[UnoError] = DatabaseQueryError,
    **context: Any
) -> UnoError:
    """
    Map a PostgreSQL exception to a appropriate UnoError.
    
    Args:
        ex: The PostgreSQL exception
        default_message: Default error message to use if not derived from exception
        default_error_class: Default error class to use if not matched
        **context: Additional context information
        
    Returns:
        An appropriate UnoError subclass instance
    """
    error_code = extract_pg_error_code(ex)
    error_message = str(ex)
    error_details = extract_pg_error_details(error_message)
    error_context = {**context, **error_details}
    
    # If we have a PostgreSQL error code, find the matching error class
    if error_code and error_code in PG_ERROR_MAPPING:
        error_class = PG_ERROR_MAPPING[error_code]
        
        # Special handling for specific error types
        if error_class == DatabaseUniqueViolationError and "constraint_name" in error_details:
            return DatabaseUniqueViolationError(
                constraint_name=error_details["constraint_name"],
                table_name=error_details.get("table_name"),
                message=default_message or error_message,
                **error_context
            )
        
        if error_class == DatabaseForeignKeyViolationError and "constraint_name" in error_details:
            return DatabaseForeignKeyViolationError(
                constraint_name=error_details["constraint_name"],
                table_name=error_details.get("table_name"),
                message=default_message or error_message,
                **error_context
            )
        
        if error_class == DatabaseTableNotFoundError and "table_name" in error_details:
            return DatabaseTableNotFoundError(
                table_name=error_details["table_name"],
                message=default_message or error_message,
                **error_context
            )
        
        if error_class == DatabaseColumnNotFoundError and "column_name" in error_details:
            return DatabaseColumnNotFoundError(
                column_name=error_details["column_name"],
                table_name=error_details.get("table_name"),
                message=default_message or error_message,
                **error_context
            )
        
        # For transaction errors, ensure we include the reason
        if issubclass(error_class, DatabaseTransactionError):
            return error_class(
                reason=default_message or error_message,
                **error_context
            )
        
        # For deadlock detection
        if error_code == PostgresErrorCode.DEADLOCK_DETECTED:
            return DatabaseTransactionConflictError(
                reason="Deadlock detected",
                **error_context
            )
        
        # General case - create the error object with available info
        try:
            return error_class(
                message=default_message or error_message,
                **error_context
            )
        except TypeError:
            # If the constructor doesn't accept these arguments, fall back to default
            logger.warning(
                f"Failed to create error of type {error_class.__name__} "
                f"with the available arguments. Falling back to {default_error_class.__name__}."
            )
    
    # Default case - use the default error class
    return default_error_class(
        reason=default_message or error_message,
        **error_context
    )


async def handle_pg_error(
    coro: Callable[..., Awaitable[T]],
    *args: Any,
    error_message: Optional[str] = None,
    **kwargs: Any
) -> T:
    """
    Execute a coroutine and handle PostgreSQL errors.
    
    Args:
        coro: The coroutine function to execute
        *args: Arguments to pass to the coroutine
        error_message: Optional custom error message
        **kwargs: Keyword arguments to pass to the coroutine
        
    Returns:
        The result of the coroutine
        
    Raises:
        UnoError: An appropriate UnoError if a PostgreSQL error occurs
    """
    try:
        return await coro(*args, **kwargs)
    except Exception as ex:
        # Rethrow UnoErrors as is
        if isinstance(ex, UnoError):
            raise
        
        # Map and raise PostgreSQL errors as UnoErrors
        mapped_error = map_pg_exception_to_uno_error(
            ex, 
            default_message=error_message,
            operation=coro.__name__
        )
        raise mapped_error from ex


def with_pg_error_handling(
    error_message: Optional[str] = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator to handle PostgreSQL errors in async functions.
    
    Args:
        error_message: Optional custom error message
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await handle_pg_error(
                func, 
                *args, 
                error_message=error_message,
                **kwargs
            )
        return wrapper
    return decorator


def is_deadlock_error(error: Exception) -> bool:
    """
    Check if an exception is a PostgreSQL deadlock error.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is a deadlock error
    """
    error_code = extract_pg_error_code(error)
    return error_code == PostgresErrorCode.DEADLOCK_DETECTED


def is_serialization_error(error: Exception) -> bool:
    """
    Check if an exception is a PostgreSQL serialization error.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is a serialization error
    """
    error_code = extract_pg_error_code(error)
    return error_code == PostgresErrorCode.SERIALIZATION_FAILURE


def is_constraint_violation(error: Exception) -> bool:
    """
    Check if an exception is a PostgreSQL constraint violation.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is a constraint violation
    """
    error_code = extract_pg_error_code(error)
    return error_code in [
        PostgresErrorCode.INTEGRITY_CONSTRAINT_VIOLATION,
        PostgresErrorCode.RESTRICT_VIOLATION,
        PostgresErrorCode.NOT_NULL_VIOLATION,
        PostgresErrorCode.FOREIGN_KEY_VIOLATION,
        PostgresErrorCode.UNIQUE_VIOLATION,
        PostgresErrorCode.CHECK_VIOLATION,
        PostgresErrorCode.EXCLUSION_VIOLATION,
    ]


def is_connection_error(error: Exception) -> bool:
    """
    Check if an exception is a PostgreSQL connection error.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is a connection error
    """
    error_code = extract_pg_error_code(error)
    return error_code in [
        PostgresErrorCode.CONNECTION_EXCEPTION,
        PostgresErrorCode.CONNECTION_DOES_NOT_EXIST,
        PostgresErrorCode.CONNECTION_FAILURE,
        PostgresErrorCode.SQLCLIENT_UNABLE_TO_ESTABLISH_SQLCONNECTION,
        PostgresErrorCode.SQLSERVER_REJECTED_ESTABLISHMENT_OF_SQLCONNECTION,
    ]


def is_query_canceled(error: Exception) -> bool:
    """
    Check if an exception is a PostgreSQL query canceled error.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is a query canceled error
    """
    error_code = extract_pg_error_code(error)
    return error_code == PostgresErrorCode.QUERY_CANCELED


def is_transient_error(error: Exception) -> bool:
    """
    Check if an exception is a transient PostgreSQL error that can be retried.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is transient and can be retried
    """
    if is_connection_error(error) or is_deadlock_error(error) or is_serialization_error(error):
        return True
    
    error_code = extract_pg_error_code(error)
    return error_code in [
        PostgresErrorCode.TRANSACTION_ROLLBACK,
        PostgresErrorCode.QUERY_CANCELED,
        PostgresErrorCode.CANNOT_CONNECT_NOW,
        PostgresErrorCode.IDLE_IN_TRANSACTION_SESSION_TIMEOUT,
        PostgresErrorCode.LOCK_NOT_AVAILABLE,
    ]


def get_retry_delay_for_error(error: Exception) -> float:
    """
    Get an appropriate retry delay for a PostgreSQL error.
    
    Args:
        error: The exception
        
    Returns:
        Delay in seconds before retry
    """
    if is_deadlock_error(error):
        # Shorter delay for deadlocks, as they're usually short-lived
        return 0.1
    
    if is_serialization_error(error):
        # Slightly longer delay for serialization failures
        return 0.2
    
    if is_connection_error(error):
        # Longer delay for connection errors
        return 1.0
    
    # Default delay for other errors
    return 0.5