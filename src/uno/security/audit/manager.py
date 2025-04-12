# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Audit log manager for Uno applications.

This module provides management for security audit logs.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any

from uno.security.audit.event import SecurityEvent
from uno.security.audit.logger import AuditLogger
from uno.security.config import AuditingConfig, AuditLogLevel


class AuditLogManager:
    """
    Audit log manager.
    
    This class manages security audit logs, including storage, retention,
    and analysis.
    """
    
    def __init__(
        self,
        config: AuditingConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the audit log manager.
        
        Args:
            config: Auditing configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.audit")
        self.audit_logger = AuditLogger(config, logger)
    
    def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event.
        
        Args:
            event: Security event to log
        """
        self.audit_logger.log_event(event)
    
    def get_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[SecurityEvent]:
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
        return self.audit_logger.get_events(
            start_time, end_time, event_types, user_id, limit, offset
        )
    
    def clean_old_logs(self) -> int:
        """
        Clean old logs based on retention policy.
        
        Returns:
            Number of logs cleaned
        """
        if not self.config.enabled or not self.config.retention_days:
            return 0
        
        # This is a placeholder implementation
        # In a real implementation, this would delete old logs based on the retention policy
        return 0
    
    def export_logs(
        self,
        format: str = "json",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Export logs to a file.
        
        Args:
            format: Export format (json or csv)
            start_time: Optional start time (Unix timestamp)
            end_time: Optional end time (Unix timestamp)
            event_types: Optional list of event types to filter by
            user_id: Optional user ID to filter by
            
        Returns:
            Path to the exported file
        """
        # Get the events
        events = self.get_events(start_time, end_time, event_types, user_id)
        
        # Create a filename
        timestamp = int(time.time())
        filename = f"audit_logs_{timestamp}.{format}"
        
        # Export the events
        if format == "json":
            import json
            with open(filename, "w") as f:
                json.dump([event.to_dict() for event in events], f, indent=2)
        elif format == "csv":
            import csv
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "event_id", "timestamp", "event_type", "user_id",
                    "ip_address", "user_agent", "success", "message",
                    "severity", "details"
                ])
                
                # Write events
                for event in events:
                    writer.writerow([
                        event.event_id,
                        event.timestamp,
                        event.event_type,
                        event.user_id,
                        event.ip_address,
                        event.user_agent,
                        event.success,
                        event.message,
                        event.severity,
                        event.details
                    ])
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return filename
    
    def analyze_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze security events.
        
        Args:
            start_time: Optional start time (Unix timestamp)
            end_time: Optional end time (Unix timestamp)
            
        Returns:
            Analysis results
        """
        # Get the events
        events = self.get_events(start_time, end_time)
        
        # Count events by type
        event_counts = {}
        for event in events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Count events by user
        user_counts = {}
        for event in events:
            if event.user_id:
                user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
        
        # Count failed events
        failed_events = [event for event in events if not event.success]
        failed_count = len(failed_events)
        
        # Count events by severity
        severity_counts = {}
        for event in events:
            severity = event.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_events": len(events),
            "event_counts": event_counts,
            "user_counts": user_counts,
            "failed_count": failed_count,
            "severity_counts": severity_counts
        }