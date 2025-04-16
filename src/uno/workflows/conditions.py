#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Advanced conditional logic for workflow execution.

This module provides enhanced condition types and evaluation functions
for workflow conditions, supporting complex logic combinations, time-based
conditions, and other advanced features.
"""

import logging
import json
import asyncio
import re
from datetime import datetime, time, timedelta, timezone
from typing import (
    Dict,
    Any,
    List,
    Set,
    Optional,
    Callable,
    Union,
    Type,
    Protocol,
    runtime_checkable,
)
from enum import Enum, auto
import math

import inject

from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.base import UnoError
from uno.workflows.errors import (
    WorkflowErrorCode,
    WorkflowConditionError,
    WorkflowInvalidDefinitionError,
)
from uno.settings import uno_settings
from uno.database.db_manager import DBManager

from uno.workflows.models import WorkflowConditionType
from uno.workflows.engine import WorkflowEventModel
from uno.queries.entities import Query
from uno.workflows.entities import WorkflowCondition


class ConditionError(UnoError):
    """Error raised when there's an issue evaluating a condition."""

    pass


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""

    AND = "and"
    OR = "or"
    NOT = "not"


class ComparisonOperator(str, Enum):
    """Comparison operators for field value conditions."""

    EQUAL = "eq"
    NOT_EQUAL = "neq"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "nin"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    MATCHES = "matches"  # Regex match
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"


class TimeUnit(str, Enum):
    """Time units for time-based conditions."""

    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


class TimeOperator(str, Enum):
    """Operators for time-based conditions."""

    BEFORE = "before"
    AFTER = "after"
    BETWEEN = "between"
    ON_WEEKDAY = "on_weekday"
    IN_BUSINESS_HOURS = "in_business_hours"
    RECURRING = "recurring"


class Weekday(int, Enum):
    """Weekdays for time-based conditions."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@runtime_checkable
class ConditionEvaluator(Protocol):
    """Interface for condition evaluators."""

    async def evaluate(
        self,
        condition: "WorkflowCondition",
        event: WorkflowEventModel,
        context: Dict[str, Any],
    ) -> Result[bool]:
        """Evaluate a condition against an event."""
        ...


class FieldValueEvaluator:
    """Evaluator for field value conditions."""

    @inject.params(logger=logging.Logger)
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    async def evaluate(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any],
    ) -> Result[bool]:
        """Evaluate a field value condition."""
        try:
            config = condition.condition_config
            if not config or not config.get("field"):
                return Failure(
                    ConditionError("Field value condition missing field configuration")
                )

            field = config["field"]
            operator = config.get("operator", ComparisonOperator.EQUAL)
            expected_value = config.get("value")

            # Support for nested field paths using dot notation
            payload = event.payload
            if event.operation in ["update", "UPDATE"]:
                # For updates, check against the new values
                payload = payload.get("new", payload)

            # Get the actual value using field path
            actual_value = self._get_value_from_path(payload, field)

            # Special operators that check for null/empty
            if operator == ComparisonOperator.IS_NULL:
                return Success(actual_value is None)

            if operator == ComparisonOperator.IS_NOT_NULL:
                return Success(actual_value is not None)

            if operator == ComparisonOperator.IS_EMPTY:
                return Success(
                    actual_value == "" or actual_value == [] or actual_value == {}
                )

            if operator == ComparisonOperator.IS_NOT_EMPTY:
                return Success(
                    not (actual_value == "" or actual_value == [] or actual_value == {})
                )

            # If the field doesn't exist or is null, return False for all other operators
            if actual_value is None:
                return Success(False)

            # Perform the comparison based on the operator
            if operator == ComparisonOperator.EQUAL:
                result = actual_value == expected_value
            elif operator == ComparisonOperator.NOT_EQUAL:
                result = actual_value != expected_value
            elif operator == ComparisonOperator.GREATER_THAN:
                result = actual_value > expected_value
            elif operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
                result = actual_value >= expected_value
            elif operator == ComparisonOperator.LESS_THAN:
                result = actual_value < expected_value
            elif operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
                result = actual_value <= expected_value
            elif operator == ComparisonOperator.IN:
                result = actual_value in expected_value
            elif operator == ComparisonOperator.NOT_IN:
                result = actual_value not in expected_value
            elif operator == ComparisonOperator.CONTAINS:
                result = expected_value in actual_value
            elif operator == ComparisonOperator.NOT_CONTAINS:
                result = expected_value not in actual_value
            elif operator == ComparisonOperator.STARTS_WITH:
                result = str(actual_value).startswith(str(expected_value))
            elif operator == ComparisonOperator.ENDS_WITH:
                result = str(actual_value).endswith(str(expected_value))
            elif operator == ComparisonOperator.MATCHES:
                result = bool(re.match(expected_value, str(actual_value)))
            elif operator == ComparisonOperator.BETWEEN:
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    min_val, max_val = expected_value
                    result = min_val <= actual_value <= max_val
                else:
                    return Failure(
                        ConditionError(
                            f"Between operator requires a list of two values, got: {expected_value}"
                        )
                    )
            else:
                return Failure(ConditionError(f"Unsupported operator: {operator}"))

            return Success(result)

        except Exception as e:
            self.logger.exception(f"Error evaluating field value condition: {e}")
            return Failure(
                ConditionError(f"Error evaluating field value condition: {str(e)}")
            )

    def _get_value_from_path(self, data: Dict[str, Any], path: str) -> Any:
        """Get a value from a nested object using dot notation."""
        if "." not in path:
            return data.get(path)

        # Handle dot notation for nested fields
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None

        return current


class TimeBasedEvaluator:
    """Evaluator for time-based conditions."""

    @inject.params(logger=logging.Logger)
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        # Default business hours
        self.business_hours = {
            "start": time(9, 0),  # 9:00 AM
            "end": time(17, 0),  # 5:00 PM
            "weekdays": [
                Weekday.MONDAY,
                Weekday.TUESDAY,
                Weekday.WEDNESDAY,
                Weekday.THURSDAY,
                Weekday.FRIDAY,
            ],
        }

    async def evaluate(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any],
    ) -> Result[bool]:
        """Evaluate a time-based condition."""
        try:
            config = condition.condition_config
            if not config or not config.get("operator"):
                return Failure(
                    ConditionError(
                        "Time-based condition missing operator configuration"
                    )
                )

            operator = config.get("operator")

            # Get current time in UTC
            now = datetime.now(timezone.utc)

            # Override business hours if provided
            if config.get("business_hours"):
                self.business_hours = config.get("business_hours")

            # Handle different time operations
            if operator == TimeOperator.BEFORE:
                # Time before a specific datetime
                target_time = self._parse_datetime(config.get("datetime"))
                if not target_time:
                    return Failure(
                        ConditionError("Before operator requires a datetime value")
                    )

                return Success(now < target_time)

            elif operator == TimeOperator.AFTER:
                # Time after a specific datetime
                target_time = self._parse_datetime(config.get("datetime"))
                if not target_time:
                    return Failure(
                        ConditionError("After operator requires a datetime value")
                    )

                return Success(now > target_time)

            elif operator == TimeOperator.BETWEEN:
                # Time between two datetimes
                start_time = self._parse_datetime(config.get("start_datetime"))
                end_time = self._parse_datetime(config.get("end_datetime"))

                if not start_time or not end_time:
                    return Failure(
                        ConditionError(
                            "Between operator requires start_datetime and end_datetime values"
                        )
                    )

                return Success(start_time <= now <= end_time)

            elif operator == TimeOperator.ON_WEEKDAY:
                # Check if current day is one of the specified weekdays
                weekdays = config.get("weekdays", [])
                if not weekdays:
                    return Failure(
                        ConditionError("On-weekday operator requires weekdays value")
                    )

                current_weekday = now.weekday()
                return Success(current_weekday in weekdays)

            elif operator == TimeOperator.IN_BUSINESS_HOURS:
                # Check if current time is within business hours
                return Success(self._is_business_hours(now))

            elif operator == TimeOperator.RECURRING:
                # Check if current time matches a recurring schedule
                interval = config.get("interval", 1)
                unit = config.get("unit", TimeUnit.DAYS)
                reference_time = self._parse_datetime(config.get("reference_datetime"))

                if not reference_time:
                    return Failure(
                        ConditionError(
                            "Recurring operator requires reference_datetime value"
                        )
                    )

                # Calculate the time elapsed since the reference time
                elapsed = now - reference_time

                # Convert the interval to timedelta based on the unit
                if unit == TimeUnit.SECONDS:
                    interval_delta = timedelta(seconds=interval)
                elif unit == TimeUnit.MINUTES:
                    interval_delta = timedelta(minutes=interval)
                elif unit == TimeUnit.HOURS:
                    interval_delta = timedelta(hours=interval)
                elif unit == TimeUnit.DAYS:
                    interval_delta = timedelta(days=interval)
                elif unit == TimeUnit.WEEKS:
                    interval_delta = timedelta(weeks=interval)
                elif unit == TimeUnit.MONTHS:
                    # Approximate months as 30.44 days
                    interval_delta = timedelta(days=30.44 * interval)
                elif unit == TimeUnit.YEARS:
                    # Approximate years as 365.25 days
                    interval_delta = timedelta(days=365.25 * interval)
                else:
                    return Failure(ConditionError(f"Unsupported time unit: {unit}"))

                # Check if the elapsed time is a multiple of the interval
                # Allow for a small tolerance to account for processing delays
                tolerance = timedelta(seconds=60)  # 1 minute tolerance

                # Calculate how many intervals have passed
                intervals_passed = (
                    elapsed.total_seconds() / interval_delta.total_seconds()
                )
                # Check if it's close to a whole number of intervals
                is_on_interval = (
                    abs(intervals_passed - round(intervals_passed))
                    * interval_delta.total_seconds()
                    <= tolerance.total_seconds()
                )

                return Success(is_on_interval)

            else:
                return Failure(ConditionError(f"Unsupported time operator: {operator}"))

        except Exception as e:
            self.logger.exception(f"Error evaluating time-based condition: {e}")
            return Failure(
                ConditionError(f"Error evaluating time-based condition: {str(e)}")
            )

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse a datetime string to a datetime object with UTC timezone."""
        if not dt_str:
            return None

        try:
            # Try ISO format first
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            # Ensure it has timezone info
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            try:
                # Try common datetime formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%d/%m/%Y %H:%M:%S",
                    "%d/%m/%Y",
                    "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y",
                ]

                for fmt in formats:
                    try:
                        dt = datetime.strptime(dt_str, fmt)
                        # Add UTC timezone
                        dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                    except ValueError:
                        continue

                return None
            except Exception:
                return None

    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if the given datetime is within business hours."""
        # Check if it's a business day
        if dt.weekday() not in self.business_hours.get(
            "weekdays", [0, 1, 2, 3, 4]
        ):  # Default M-F
            return False

        # Check if it's within business hours
        current_time = dt.time()
        start_time = self.business_hours.get("start", time(9, 0))
        end_time = self.business_hours.get("end", time(17, 0))

        return start_time <= current_time <= end_time


class RoleBasedEvaluator:
    """Evaluator for role-based conditions."""

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def evaluate(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any],
    ) -> Result[bool]:
        """Evaluate a role-based condition."""
        try:
            config = condition.condition_config
            if not config:
                return Failure(
                    ConditionError("Role-based condition missing configuration")
                )

            # Get user ID from event or context
            user_id = None

            # Check event payload for user ID
            payload = event.payload
            if event.operation in ["update", "UPDATE"]:
                # For updates, check against the new values
                payload = payload.get("new", payload)

            # Try common field names for user ID
            user_id_fields = [
                "user_id",
                "userId",
                "created_by",
                "modified_by",
                "owner_id",
                "ownerId",
            ]
            for field in user_id_fields:
                if field in payload:
                    user_id = payload[field]
                    break

            # If not found in payload, try context
            if not user_id and "user_id" in context:
                user_id = context["user_id"]

            # If still no user ID, check for a specified user ID in the config
            if not user_id and "user_id" in config:
                user_id = config["user_id"]

            if not user_id:
                self.logger.warning(
                    "No user ID found for role-based condition evaluation"
                )
                return Success(False)

            # Check if roles are directly specified in the condition
            if "roles" in config:
                required_roles = config["roles"]
                user_roles = await self._get_user_roles(user_id)

                # Determine the role match type (any or all)
                match_type = config.get("match_type", "any")

                if match_type == "any":
                    # User must have at least one of the specified roles
                    return Success(any(role in user_roles for role in required_roles))
                else:
                    # User must have all specified roles
                    return Success(all(role in user_roles for role in required_roles))

            # Check for permission check
            if "permission" in config:
                required_permission = config["permission"]
                has_permission = await self._check_user_permission(
                    user_id, required_permission
                )
                return Success(has_permission)

            return Failure(
                ConditionError(
                    "Role-based condition missing roles or permission configuration"
                )
            )

        except Exception as e:
            self.logger.exception(f"Error evaluating role-based condition: {e}")
            return Failure(
                ConditionError(f"Error evaluating role-based condition: {str(e)}")
            )

    async def _get_user_roles(self, user_id: str) -> List[str]:
        """Get the roles assigned to a user."""
        try:
            if not self.db_manager:
                return []

            async with self.db_manager.get_enhanced_session() as session:
                # Query for user roles
                query = """
                SELECT r.name
                FROM user_role ur
                JOIN role r ON ur.role_id = r.id
                WHERE ur.user_id = :user_id
                """

                result = await session.execute(query, {"user_id": user_id})
                roles = [row["name"] for row in result]

                return roles

        except Exception as e:
            self.logger.error(f"Error fetching user roles: {e}")
            return []

    async def _check_user_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission."""
        try:
            if not self.db_manager:
                return False

            async with self.db_manager.get_enhanced_session() as session:
                # Query for user permissions
                query = """
                SELECT COUNT(*) as has_permission
                FROM user_permission up
                WHERE up.user_id = :user_id AND up.permission = :permission
                
                UNION
                
                SELECT COUNT(*) as has_permission
                FROM user_role ur
                JOIN role_permission rp ON ur.role_id = rp.role_id
                WHERE ur.user_id = :user_id AND rp.permission = :permission
                """

                result = await session.execute(
                    query, {"user_id": user_id, "permission": permission}
                )

                # If any of the queries return a count > 0, the user has the permission
                for row in result:
                    if row["has_permission"] > 0:
                        return True

                return False

        except Exception as e:
            self.logger.error(f"Error checking user permission: {e}")
            return False


class QueryMatchEvaluator:
    """Evaluator for query match conditions."""

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def evaluate(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any],
    ) -> Result[bool]:
        """
        Evaluate a query match condition.

        This leverages the graph database for complex queries that involve
        many joins, returning the IDs of matching records.
        """
        try:
            # If no query is associated, return an error
            if not condition.query_id:
                return Failure(
                    ConditionError(
                        "Query match condition requires a query_id but none was provided"
                    )
                )

            # Get payload data
            payload = event.payload
            if event.operation in ["update", "UPDATE"]:
                # For updates, check against the new values
                payload = payload.get("new", payload)

            # Get record ID from payload
            record_id = payload.get("id")
            if not record_id:
                self.logger.warning("No record ID found in event payload")
                return Success(False)

            # Get the query
            query = await Query.get(condition.query_id)
            if not query:
                return Failure(
                    ConditionError(f"Query with ID {condition.query_id} not found")
                )

            # Use the QueryExecutor to check if the record matches the query
            # This leverages the graph database for complex queries
            match_result = await query.check_record_match(record_id)

            if match_result.is_failure:
                return Failure(
                    ConditionError(f"Error executing query match: {match_result.error}")
                )

            # Return the match result (True if the record matches, False otherwise)
            matched = match_result.value
            self.logger.debug(
                f"Query match condition: record {record_id} {'matches' if matched else 'does not match'} query {condition.query_id}"
            )
            return Success(matched)

        except Exception as e:
            self.logger.exception(f"Error evaluating query match condition: {e}")
            return Failure(
                ConditionError(f"Error evaluating query match condition: {str(e)}")
            )

        # Fallback - assume no match
        return Success(False)


class CustomEvaluator:
    """Evaluator for custom conditions."""

    @inject.params(logger=logging.Logger)
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        custom_evaluators: Dict[str, Callable] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.custom_evaluators = custom_evaluators or {}

    def register_custom_evaluator(
        self, evaluator_type: str, evaluator_func: Callable
    ) -> None:
        """Register a custom evaluator function for a specific type."""
        self.custom_evaluators[evaluator_type] = evaluator_func

    async def evaluate(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any],
    ) -> Result[bool]:
        """Evaluate a custom condition."""
        try:
            config = condition.condition_config

            # Get custom evaluator type
            evaluator_type = config.get("evaluator_type")
            if not evaluator_type:
                return Failure(
                    ConditionError("No evaluator type provided for custom condition")
                )

            # Find the corresponding evaluator function
            evaluator_func = self.custom_evaluators.get(evaluator_type)
            if not evaluator_func:
                return Failure(
                    ConditionError(
                        f"No evaluator found for custom condition type: {evaluator_type}"
                    )
                )

            # Execute the custom function
            result = evaluator_func(condition, event, context)

            # Handle both synchronous and asynchronous functions
            if asyncio.iscoroutine(result):
                result = await result

            # If the result is already a Result object, return it
            if isinstance(result, Result):
                return result

            # Otherwise, wrap it in a Success
            return Success(bool(result))

        except Exception as e:
            self.logger.exception(f"Error evaluating custom condition: {e}")
            return Failure(
                ConditionError(f"Error evaluating custom condition: {str(e)}")
            )


class CompositeEvaluator:
    """Evaluator for composite conditions with logical operators."""

    @inject.params(logger=logging.Logger)
    def __init__(
        self,
        condition_evaluators: Dict[WorkflowConditionType, ConditionEvaluator] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.condition_evaluators = condition_evaluators or {}

    async def evaluate(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any],
    ) -> Result[bool]:
        """Evaluate a composite condition."""
        try:
            config = condition.condition_config

            # Get the logical operator
            operator = config.get("operator", LogicalOperator.AND)

            # Get subconditions
            subconditions = config.get("conditions", [])
            if not subconditions:
                return Failure(
                    ConditionError("Composite condition has no subconditions")
                )

            # For NOT operator, there should be only one subcondition
            if operator == LogicalOperator.NOT and len(subconditions) != 1:
                return Failure(
                    ConditionError("NOT operator should have exactly one subcondition")
                )

            # Evaluate each subcondition
            results = []

            for subcond in subconditions:
                # Create a temporary WorkflowCondition object for the subcondition
                subcond_obj = WorkflowCondition(
                    id=condition.id + "_sub",  # Use the parent ID with a suffix
                    workflow_id=condition.workflow_id,
                    condition_type=subcond.get(
                        "type", WorkflowConditionType.FIELD_VALUE
                    ),
                    condition_config=subcond.get("config", {}),
                    query_id=subcond.get("query_id"),
                    name=subcond.get("name", ""),
                    description=subcond.get("description"),
                    order=0,
                )

                # Find the appropriate evaluator
                evaluator = self.condition_evaluators.get(subcond_obj.condition_type)
                if not evaluator:
                    self.logger.warning(
                        f"No evaluator found for condition type: {subcond_obj.condition_type}"
                    )
                    results.append(False)
                    continue

                # Evaluate the subcondition
                result = await evaluator.evaluate(subcond_obj, event, context)

                if result.is_failure:
                    self.logger.warning(
                        f"Failed to evaluate subcondition: {result.error}"
                    )
                    results.append(False)
                else:
                    results.append(result.value)

            # Apply the logical operator
            if operator == LogicalOperator.AND:
                return Success(all(results))
            elif operator == LogicalOperator.OR:
                return Success(any(results))
            elif operator == LogicalOperator.NOT:
                return Success(not results[0])
            else:
                return Failure(
                    ConditionError(f"Unsupported logical operator: {operator}")
                )

        except Exception as e:
            self.logger.exception(f"Error evaluating composite condition: {e}")
            return Failure(
                ConditionError(f"Error evaluating composite condition: {str(e)}")
            )


class ConditionEvaluatorRegistry:
    """Registry for condition evaluators."""

    def __init__(self):
        self.evaluators: Dict[WorkflowConditionType, ConditionEvaluator] = {}

    def register(
        self, condition_type: WorkflowConditionType, evaluator: ConditionEvaluator
    ) -> None:
        """Register a condition evaluator."""
        self.evaluators[condition_type] = evaluator

    def get(
        self, condition_type: WorkflowConditionType
    ) -> Optional[ConditionEvaluator]:
        """Get a condition evaluator by condition type."""
        return self.evaluators.get(condition_type)

    def has(self, condition_type: WorkflowConditionType) -> bool:
        """Check if an evaluator exists for the condition type."""
        return condition_type in self.evaluators


# Singleton registry instance
_registry = ConditionEvaluatorRegistry()


def get_evaluator_registry() -> ConditionEvaluatorRegistry:
    """Get the global condition evaluator registry."""
    return _registry


def register_evaluator(
    condition_type: WorkflowConditionType, evaluator: ConditionEvaluator
) -> None:
    """Register a condition evaluator in the global registry."""
    _registry.register(condition_type, evaluator)


def get_evaluator(
    condition_type: WorkflowConditionType,
) -> Optional[ConditionEvaluator]:
    """Get a condition evaluator from the global registry."""
    return _registry.get(condition_type)


# Add a new condition type for composite conditions
class ExtendedWorkflowConditionType(str, Enum):
    """Extended condition types including composite conditions."""

    FIELD_VALUE = WorkflowConditionType.FIELD_VALUE
    TIME_BASED = WorkflowConditionType.TIME_BASED
    ROLE_BASED = WorkflowConditionType.ROLE_BASED
    QUERY_MATCH = WorkflowConditionType.QUERY_MATCH
    CUSTOM = WorkflowConditionType.CUSTOM
    COMPOSITE = "composite"  # New type for logical combinations of conditions


# Initialize standard evaluators
def init_evaluators() -> None:
    """Initialize and register the standard evaluators."""
    # Create evaluators
    field_evaluator = FieldValueEvaluator()
    time_evaluator = TimeBasedEvaluator()
    role_evaluator = RoleBasedEvaluator()
    query_evaluator = QueryMatchEvaluator()
    custom_evaluator = CustomEvaluator()

    # Register evaluators
    register_evaluator(WorkflowConditionType.FIELD_VALUE, field_evaluator)
    register_evaluator(WorkflowConditionType.TIME_BASED, time_evaluator)
    register_evaluator(WorkflowConditionType.ROLE_BASED, role_evaluator)
    register_evaluator(WorkflowConditionType.QUERY_MATCH, query_evaluator)
    register_evaluator(WorkflowConditionType.CUSTOM, custom_evaluator)

    # Create and register composite evaluator
    composite_evaluator = CompositeEvaluator(_registry.evaluators)
    register_evaluator(ExtendedWorkflowConditionType.COMPOSITE, composite_evaluator)
