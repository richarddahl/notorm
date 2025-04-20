# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Security audit logger for Uno applications.

This module provides a logger for security events.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Protocol

from uno.security.audit.event import SecurityEvent
from uno.security.config import AuditingConfig, AuditLogLevel, AuditLogStorage


class AuditLogStorage(Protocol):
    """Protocol for audit log storage backends."""

    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        ...

    def get_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: list[str] | None = None,
        user_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SecurityEvent]:
        """
        Get security events.

        Args:
            start_time: Optional start time (Unix timestamp)
            end_time: Optional end time (Unix timestamp)
            event_types: Optional list of event types to filter by
            user_id: Optional user ID to filter by
            limit: Optional limit on the number of events to return
            offset: Optional offset for pagination

        Returns:
            List of security events
        """
        ...


class FileLogStorage:
    """
    File-based audit log storage.

    This class stores audit logs in a file, with one JSON object per line.
    """

    def __init__(self, log_file: str, max_file_size: int = 10_000_000):
        """
        Initialize file-based log storage.

        Args:
            log_file: Path to the log file
            max_file_size: Maximum file size in bytes (default: 10 MB)
        """
        self.log_file = log_file
        self.max_file_size = max_file_size

        # Create the log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Rotate the log file if it's too large
        self._rotate_log_file_if_needed()

    def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event.

        Args:
            event: Security event to log
        """
        # Rotate the log file if it's too large
        self._rotate_log_file_if_needed()

        # Write the event to the log file
        with open(self.log_file, "a") as f:
            f.write(event.to_json() + "\n")

    def get_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: list[str] | None = None,
        user_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SecurityEvent]:
        """
        Get security events.

        Args:
            start_time: Optional start time (Unix timestamp)
            end_time: Optional end time (Unix timestamp)
            event_types: Optional list of event types to filter by
            user_id: Optional user ID to filter by
            limit: Optional limit on the number of events to return
            offset: Optional offset for pagination

        Returns:
            List of security events
        """
        events = []
        offset = offset or 0
        count = 0

        # Read all log files (including rotated ones)
        log_files = self._get_log_files()
        for log_file in log_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            # Parse the event
                            event = SecurityEvent.from_json(line.strip())

                            # Apply filters
                            if start_time is not None and event.timestamp < start_time:
                                continue
                            if end_time is not None and event.timestamp > end_time:
                                continue
                            if (
                                event_types is not None
                                and event.event_type not in event_types
                            ):
                                continue
                            if user_id is not None and event.user_id != user_id:
                                continue

                            # Apply offset
                            if count < offset:
                                count += 1
                                continue

                            # Add the event
                            events.append(event)
                            count += 1

                            # Check limit
                            if limit is not None and len(events) >= limit:
                                break
                        except Exception:
                            # Skip invalid lines
                            continue

                    # Check limit
                    if limit is not None and len(events) >= limit:
                        break
            except Exception:
                # Skip invalid files
                continue

        return events

    def _rotate_log_file_if_needed(self) -> None:
        """Rotate the log file if it's too large."""
        if not os.path.exists(self.log_file):
            return

        if os.path.getsize(self.log_file) >= self.max_file_size:
            # Rotate the log file
            timestamp = int(time.time())
            rotated_file = f"{self.log_file}.{timestamp}"
            os.rename(self.log_file, rotated_file)

    def _get_log_files(self) -> list[str]:
        """
        Get all log files, including rotated ones.

        Returns:
            List of log file paths
        """
        log_dir = os.path.dirname(self.log_file)
        log_base = os.path.basename(self.log_file)

        log_files = []

        # Check if the current log file exists
        if os.path.exists(self.log_file):
            log_files.append(self.log_file)

        # Find rotated log files
        if log_dir:
            for filename in os.listdir(log_dir):
                if filename.startswith(log_base + "."):
                    log_files.append(os.path.join(log_dir, filename))

        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return log_files


class DatabaseLogStorage:
    """
    Database-based audit log storage.

    This class is a placeholder for a database-based audit log storage implementation.
    In a real implementation, this would store audit logs in a database table.
    """

    def __init__(self, connection_string: str):
        """
        Initialize database-based log storage.

        Args:
            connection_string: Database connection string
        """
        self.connection_string = connection_string

    def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event.

        Args:
            event: Security event to log
        """
        # Placeholder implementation
        pass

    def get_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: list[str] | None = None,
        user_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SecurityEvent]:
        """
        Get security events.

        Args:
            start_time: Optional start time (Unix timestamp)
            end_time: Optional end time (Unix timestamp)
            event_types: Optional list of event types to filter by
            user_id: Optional user ID to filter by
            limit: Optional limit on the number of events to return
            offset: Optional offset for pagination

        Returns:
            List of security events
        """
        # Placeholder implementation
        return []


class AuditLogger:
    """
    Security audit logger.

    This class provides logging for security events, with configurable
    log level, storage, and filtering.
    """

    def __init__(
        self,
        config: AuditingConfig,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the audit logger.

        Args:
            config: Auditing configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.audit")
        self.storage = self._create_storage()

    def _create_storage(self) -> Any:
        """
        Create a storage backend based on configuration.

        Returns:
            Storage backend
        """
        storage_type = self.config.storage

        if storage_type == AuditLogStorage.FILE:
            storage_path = self.config.storage_path or "audit.log"
            return FileLogStorage(storage_path)
        elif storage_type == AuditLogStorage.DATABASE:
            # Placeholder for database storage
            return DatabaseLogStorage("placeholder")
        elif storage_type == AuditLogStorage.REMOTE:
            # Placeholder for remote storage
            return None
        elif storage_type == AuditLogStorage.SYSLOG:
            # Placeholder for syslog storage
            return None
        else:
            # Default to file storage
            return FileLogStorage("audit.log")

    def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event.

        Args:
            event: Security event to log
        """
        if not self.config.enabled:
            return

        # Check if the event type should be logged
        if (
            self.config.include_events
            and event.event_type not in self.config.include_events
        ):
            return

        # Store the event
        if self.storage:
            self.storage.log_event(event)

        # Log to the regular logger as well
        if event.severity == "info":
            self.logger.info(event.message or event.event_type)
        elif event.severity == "warning":
            self.logger.warning(event.message or event.event_type)
        elif event.severity == "error":
            self.logger.error(event.message or event.event_type)
        elif event.severity == "critical":
            self.logger.critical(event.message or event.event_type)
        else:
            self.logger.info(event.message or event.event_type)

    def get_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: list[str] | None = None,
        user_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SecurityEvent]:
        """
        Get security events.

        Args:
            start_time: Optional start time (Unix timestamp)
            end_time: Optional end time (Unix timestamp)
            event_types: Optional list of event types to filter by
            user_id: Optional user ID to filter by
            limit: Optional limit on the number of events to return
            offset: Optional offset for pagination

        Returns:
            List of security events
        """
        if not self.config.enabled or not self.storage:
            return []

        return self.storage.get_events(
            start_time, end_time, event_types, user_id, limit, offset
        )
