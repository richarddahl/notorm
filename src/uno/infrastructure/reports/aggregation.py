# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Report data aggregation and processing service.

This module provides utilities for aggregating, transforming, and caching
report data for visualization and analysis.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from uno.core.errors.result import Result
from uno.caching.manager import get_cache
from uno.reports.services import ReportExecutionService, ReportError
from uno.reports.models import ReportExecutionStatus


class AggregationError(ReportError):
    """Error related to report data aggregation."""

    pass


class ReportDataAggregator:
    """Service for aggregating and processing report data."""

    def __init__(
        self,
        session: AsyncSession,
        execution_service: ReportExecutionService,
        logger: logging.Logger | None = None,
        cache_ttl: int = 300,  # 5 minutes by default
    ):
        """
        Initialize the data aggregator service.

        Args:
            session: SQLAlchemy async session
            execution_service: Service for report execution
            logger: Optional logger
            cache_ttl: Cache time-to-live in seconds
        """
        self.session = session
        self.execution_service = execution_service
        self.logger = logger or logging.getLogger(__name__)
        self.cache_ttl = cache_ttl
        self.cache = get_cache()
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def get_aggregated_data(
        self,
        template_id: str,
        parameters: dict[str, Any],
        aggregations: list[dict[str, Any]],
        cache_key: str | None = None,
        force_refresh: bool = False,
    ) -> Result[dict[str, Any], AggregationError]:
        """
        Get aggregated report data, optimized for visualization.

        Args:
            template_id: The ID of the report template
            parameters: Parameters for the report execution
            aggregations: List of aggregation configs to apply
            cache_key: Optional custom cache key
            force_refresh: Whether to force a refresh of the data

        Returns:
            Result containing aggregated data or an error
        """
        try:
            # Generate cache key if not provided
            if not cache_key:
                cache_key = self._generate_cache_key(
                    template_id, parameters, aggregations
                )

            # Try to get from cache first
            if not force_refresh:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    return Success(json.loads(cached_data))

            # Execute the report to get raw data
            execution_result = await self.execution_service.execute(
                template_id, parameters
            )
            if execution_result.is_failure():
                return Failure(
                    AggregationError(
                        f"Failed to execute report: {execution_result.error}"
                    )
                )

            execution = execution_result.value

            # Wait for completion if needed
            if execution.status not in [ReportExecutionStatus.COMPLETED, "completed"]:
                completion_result = await self.execution_service.wait_for_completion(
                    execution.id, 60
                )
                if completion_result.is_failure():
                    return Failure(
                        AggregationError(
                            f"Failed to wait for report completion: {completion_result.error}"
                        )
                    )
                execution = completion_result.value

            # Get the result data
            result_data = execution.data
            if not result_data:
                return Failure(
                    AggregationError(f"No data in report execution {execution.id}")
                )

            # Apply aggregations
            aggregated_data = await self._apply_aggregations(result_data, aggregations)

            # Store in cache
            await self.cache.set(
                cache_key, json.dumps(aggregated_data), expire=self.cache_ttl
            )

            return Success(aggregated_data)

        except Exception as e:
            self.logger.exception(f"Error aggregating report data: {str(e)}")
            return Failure(AggregationError(f"Error aggregating report data: {str(e)}"))

    async def get_multi_report_data(
        self,
        template_ids: list[str],
        date_range: dict[str, str],
        filters: dict[str, Any],
        cache_key: str | None = None,
        force_refresh: bool = False,
    ) -> Result[dict[str, Any], AggregationError]:
        """
        Get data from multiple reports for dashboard views.

        Args:
            template_ids: List of report template IDs
            date_range: Date range dictionary with start and end dates
            filters: Additional filters to apply
            cache_key: Optional custom cache key
            force_refresh: Whether to force a refresh of the data

        Returns:
            Result containing dictionary of report data keyed by template_id
        """
        try:
            # Generate cache key if not provided
            if not cache_key:
                cache_key = self._generate_cache_key(
                    "multi", template_ids, date_range, filters
                )

            # Try to get from cache first
            if not force_refresh:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    return Success(json.loads(cached_data))

            # Prepare parameters for each report
            common_params = {
                "date_start": date_range.get("start"),
                "date_end": date_range.get("end"),
                **filters,
            }

            # Execute reports concurrently
            execution_tasks = []
            for template_id in template_ids:
                task = self.execution_service.execute(template_id, common_params)
                execution_tasks.append(task)

            execution_results = await asyncio.gather(
                *execution_tasks, return_exceptions=True
            )

            # Process results
            dashboard_data = {}
            completion_tasks = []

            for i, result in enumerate(execution_results):
                template_id = template_ids[i]

                if isinstance(result, Exception):
                    dashboard_data[template_id] = {"error": str(result)}
                    continue

                if result.is_failure():
                    dashboard_data[template_id] = {"error": str(result.error)}
                    continue

                execution = result.value

                # Add task to wait for completion if needed
                if execution.status not in [
                    ReportExecutionStatus.COMPLETED,
                    "completed",
                ]:
                    task = self.execution_service.wait_for_completion(execution.id, 60)
                    completion_tasks.append((template_id, task))
                else:
                    dashboard_data[template_id] = {
                        "execution_id": execution.id,
                        "data": execution.data,
                    }

            # Wait for any pending report completions
            if completion_tasks:
                for template_id, task in completion_tasks:
                    try:
                        completion_result = await task
                        if completion_result.is_success():
                            execution = completion_result.value
                            dashboard_data[template_id] = {
                                "execution_id": execution.id,
                                "data": execution.data,
                            }
                        else:
                            dashboard_data[template_id] = {
                                "error": str(completion_result.error)
                            }
                    except Exception as e:
                        dashboard_data[template_id] = {"error": str(e)}

            # Store in cache
            await self.cache.set(
                cache_key, json.dumps(dashboard_data), expire=self.cache_ttl
            )

            return Success(dashboard_data)

        except Exception as e:
            self.logger.exception(f"Error getting multi-report data: {str(e)}")
            return Failure(
                AggregationError(f"Error getting multi-report data: {str(e)}")
            )

    async def _apply_aggregations(
        self, data: dict[str, Any], aggregations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Apply aggregations to the report data.

        This method uses pandas for efficient data processing. It runs the
        operations in a thread pool to avoid blocking the event loop.

        Args:
            data: Raw report data
            aggregations: List of aggregation configurations

        Returns:
            Dictionary of aggregated data
        """
        # Check if we have rows data
        if "rows" not in data or not data["rows"]:
            return {"aggregated": {}, "original": data}

        # Use pandas for efficient aggregation
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            self._executor, lambda: pd.DataFrame(data["rows"])
        )

        aggregated_data = {}

        for agg_config in aggregations:
            agg_type = agg_config.get("type")
            agg_name = agg_config.get("name")

            if not agg_type or not agg_name:
                continue

            # Handle different aggregation types
            if agg_type == "group_by":
                result = await self._execute_group_by(df, agg_config)
                aggregated_data[agg_name] = result

            elif agg_type == "pivot":
                result = await self._execute_pivot(df, agg_config)
                aggregated_data[agg_name] = result

            elif agg_type == "time_series":
                result = await self._execute_time_series(df, agg_config)
                aggregated_data[agg_name] = result

            elif agg_type == "summary":
                result = await self._execute_summary(df, agg_config)
                aggregated_data[agg_name] = result

        return {"aggregated": aggregated_data, "original": data}

    async def _execute_group_by(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute a group by aggregation on the dataframe."""
        group_by_columns = config.get("group_by", [])
        agg_columns = config.get("aggregate", {})

        if not group_by_columns or not agg_columns:
            return []

        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            self._executor,
            lambda: self._perform_group_by(df, group_by_columns, agg_columns),
        )

        return result

    def _perform_group_by(
        self,
        df: pd.DataFrame,
        group_by_columns: list[str],
        agg_columns: dict[str, Union[str, list[str]]],
    ) -> list[dict[str, Any]]:
        """Perform group by operation in a separate thread."""
        # Check if all columns exist
        all_columns = group_by_columns + list(agg_columns.keys())
        if not all(col in df.columns for col in all_columns):
            available_cols = list(df.columns)
            missing_cols = [col for col in all_columns if col not in available_cols]
            return Failure(
                f"Missing columns in data: {missing_cols}. Available: {available_cols}",
                convert=True,
            )

        # Build aggregation dictionary
        agg_dict = {}
        for col, aggs in agg_columns.items():
            if isinstance(aggs, str):
                agg_dict[col] = [aggs]
            else:
                agg_dict[col] = aggs

        # Perform group by
        grouped = df.groupby(group_by_columns, as_index=False).agg(agg_dict)

        # Convert column names if multi-index
        if isinstance(grouped.columns, pd.MultiIndex):
            grouped.columns = ["_".join(col).strip() for col in grouped.columns.values]

        # Convert to dictionaries and handle NaN
        result = []
        for _, row in grouped.iterrows():
            row_dict = {}
            for col in grouped.columns:
                value = row[col]
                if pd.isna(value):
                    row_dict[col] = None
                elif isinstance(value, np.integer):
                    row_dict[col] = int(value)
                elif isinstance(value, np.floating):
                    row_dict[col] = float(value)
                else:
                    row_dict[col] = value
            result.append(row_dict)

        return result

    async def _execute_pivot(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute a pivot aggregation on the dataframe."""
        index = config.get("index", [])
        columns = config.get("columns")
        values = config.get("values")

        if not index or not columns or not values:
            return []

        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            self._executor,
            lambda: self._perform_pivot(df, index, columns, values, config),
        )

        return result

    def _perform_pivot(
        self,
        df: pd.DataFrame,
        index: list[str],
        columns: str,
        values: str,
        config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Perform pivot operation in a separate thread."""
        # Check if columns exist
        required_cols = index + [columns, values]
        if not all(col in df.columns for col in required_cols):
            available_cols = list(df.columns)
            missing_cols = [col for col in required_cols if col not in available_cols]
            return Failure(
                f"Missing columns in data: {missing_cols}. Available: {available_cols}",
                convert=True,
            )

        # Get aggregation function
        agg_func = config.get("aggfunc", "sum")

        # Create pivot table
        pivot = pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=agg_func,
            fill_value=0,
        )

        # Reset index to convert to flat dataframe
        pivot = pivot.reset_index()

        # Convert to dictionaries
        result = []
        for _, row in pivot.iterrows():
            row_dict = {}
            for col in pivot.columns:
                value = row[col]
                if pd.isna(value):
                    row_dict[str(col)] = None
                elif isinstance(value, np.integer):
                    row_dict[str(col)] = int(value)
                elif isinstance(value, np.floating):
                    row_dict[str(col)] = float(value)
                else:
                    row_dict[str(col)] = value
            result.append(row_dict)

        return result

    async def _execute_time_series(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute a time series aggregation on the dataframe."""
        date_column = config.get("date_column")
        value_column = config.get("value_column")

        if not date_column or not value_column:
            return []

        # Get other config options
        group_by = config.get("group_by", [])
        frequency = config.get("frequency", "D")  # D=daily, W=weekly, M=monthly

        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            self._executor,
            lambda: self._perform_time_series(
                df, date_column, value_column, group_by, frequency
            ),
        )

        return result

    def _perform_time_series(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        group_by: list[str],
        frequency: str,
    ) -> list[dict[str, Any]]:
        """Perform time series operation in a separate thread."""
        # Check if columns exist
        required_cols = [date_column, value_column] + group_by
        if not all(col in df.columns for col in required_cols):
            available_cols = list(df.columns)
            missing_cols = [col for col in required_cols if col not in available_cols]
            return Failure(
                f"Missing columns in data: {missing_cols}. Available: {available_cols}",
                convert=True,
            )

        # Ensure date column is datetime
        try:
            df[date_column] = pd.to_datetime(df[date_column])
        except Exception as e:
            return Failure(
                f"Failed to convert {date_column} to datetime: {str(e)}", convert=True
            )

        # Resample the time series
        if group_by:
            # Group by additional columns first
            grouped = df.groupby(
                group_by + [pd.Grouper(key=date_column, freq=frequency)]
            )
            agg_dict = {value_column: "sum"}
            time_series = grouped.agg(agg_dict).reset_index()
        else:
            # Simple date-based resampling
            df = df.set_index(date_column)
            time_series = df.resample(frequency)[value_column].sum().reset_index()

        # Format dates as ISO strings for JSON
        time_series[date_column] = time_series[date_column].dt.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )

        # Convert to dictionaries
        result = []
        for _, row in time_series.iterrows():
            row_dict = {}
            for col in time_series.columns:
                value = row[col]
                if pd.isna(value):
                    row_dict[col] = None
                elif isinstance(value, np.integer):
                    row_dict[col] = int(value)
                elif isinstance(value, np.floating):
                    row_dict[col] = float(value)
                else:
                    row_dict[col] = value
            result.append(row_dict)

        return result

    async def _execute_summary(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute summary statistics on the dataframe."""
        columns = config.get("columns", [])

        if not columns:
            columns = [col for col in df.columns if is_numeric_dtype(df[col])]

        # Check if the specified columns exist
        if not all(col in df.columns for col in columns):
            available_cols = list(df.columns)
            missing_cols = [col for col in columns if col not in available_cols]
            self.logger.warning(
                f"Missing columns in data: {missing_cols}. Available: {available_cols}"
            )
            # Use only available columns
            columns = [col for col in columns if col in available_cols]

        if not columns:
            return {}

        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            self._executor, lambda: self._perform_summary(df, columns)
        )

        return result

    def _perform_summary(self, df: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
        """Perform summary statistics in a separate thread."""
        summary = {}

        for col in columns:
            if col not in df.columns:
                continue

            if not is_numeric_dtype(df[col]):
                continue

            col_stats = {
                "count": int(df[col].count()),
                "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                "sum": float(df[col].sum()) if not pd.isna(df[col].sum()) else None,
                "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                "median": (
                    float(df[col].median()) if not pd.isna(df[col].median()) else None
                ),
                "std": float(df[col].std()) if not pd.isna(df[col].std()) else None,
            }

            # Add percentiles
            for p in [0.25, 0.5, 0.75, 0.95]:
                try:
                    q_val = float(df[col].quantile(p))
                    if not pd.isna(q_val):
                        col_stats[f"p{int(p*100)}"] = q_val
                except:
                    pass

            summary[col] = col_stats

        # Add record count
        summary["_record_count"] = len(df)

        return summary

    def _generate_cache_key(self, *args) -> str:
        """Generate a unique cache key from the arguments."""
        # Convert all arguments to JSON strings
        json_args = [
            json.dumps(arg, sort_keys=True) if not isinstance(arg, str) else arg
            for arg in args
        ]

        # Join and hash
        combined = ":".join(json_args)
        return f"report_agg:{hashlib.md5(combined.encode()).hexdigest()}"
