# Audit Logging

The Uno Security Framework includes a comprehensive audit logging system designed to track security-relevant events in your application. This document provides details on how to use the audit logging features to enhance security monitoring, compliance, and incident response capabilities.

## Overview

The audit logging system provides:

- Immutable, tamper-evident logging of security-relevant events
- Structured event data for easy analysis and reporting
- Configurable storage options (database, file, external services)
- Search and analytics capabilities
- Compliance with common regulatory requirements (GDPR, HIPAA, SOX, etc.)

## Core Components

### AuditLogger

The `AuditLogger` is the primary interface for recording security events:

```python
from uno.security.audit import AuditLogger, SecurityEvent

# Get logger instance
audit_logger = AuditLogger.get_instance()

# Log a security event
audit_logger.log(
    event_type=SecurityEvent.LOGIN_SUCCESS,
    user_id="user123",
    metadata={
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
    }
)
```

### SecurityEvent

The `SecurityEvent` enum defines standard security event types:

```python
from uno.security.audit import SecurityEvent

# Authentication events
SecurityEvent.LOGIN_ATTEMPT
SecurityEvent.LOGIN_SUCCESS
SecurityEvent.LOGIN_FAILURE
SecurityEvent.LOGOUT
SecurityEvent.PASSWORD_CHANGE
SecurityEvent.PASSWORD_RESET_REQUEST
SecurityEvent.PASSWORD_RESET_COMPLETE
SecurityEvent.MFA_SETUP
SecurityEvent.MFA_VERIFICATION

# Authorization events
SecurityEvent.PERMISSION_CHANGE
SecurityEvent.ACCESS_DENIED
SecurityEvent.PRIVILEGE_ESCALATION

# Data events
SecurityEvent.DATA_ACCESS
SecurityEvent.DATA_MODIFICATION
SecurityEvent.DATA_DELETION
SecurityEvent.DATA_EXPORT

# System events
SecurityEvent.CONFIGURATION_CHANGE
SecurityEvent.USER_CREATION
SecurityEvent.USER_MODIFICATION
SecurityEvent.USER_DELETION
```

### AuditLogManager

The `AuditLogManager` provides administrative capabilities for managing audit logs:

```python
from uno.security.audit import AuditLogManager

# Create manager instance
log_manager = AuditLogManager()

# Search for specific events
results = log_manager.search(
    event_types=[SecurityEvent.LOGIN_FAILURE],
    user_id="user123",
    time_range=(start_time, end_time)
)

# Export logs for compliance reporting
log_manager.export(
    format="csv",
    time_range=(start_time, end_time),
    destination="/path/to/export.csv"
)

# Verify log integrity
is_valid = log_manager.verify_integrity(time_range=(start_time, end_time))
```

## Configuration

Configure audit logging through the `SecurityConfig`:

```python
from uno.security.config import SecurityConfig

config = SecurityConfig(
    audit={
        "enabled": True,
        "storage": {
            "type": "database",  # Options: "database", "file", "cloud"
            "connection": "postgresql://user:pass@localhost/db",
            "table_name": "audit_logs",
        },
        "retention_period": 365,  # Days to retain logs
        "integrity_check": {
            "enabled": True,
            "algorithm": "sha256",
        },
        "events": {
            "include": ["*"],  # All events
            "exclude": [],  # No exclusions
        }
    }
)
```

## Integrations

### Database Integration

Store audit logs directly in your application database:

```python
# Configure for database storage
config = SecurityConfig(
    audit={
        "storage": {
            "type": "database",
            "connection": "postgresql://user:pass@localhost/db",
            "table_name": "audit_logs",
        }
    }
)
```

### File System Integration

Write audit logs to the file system:

```python
# Configure for file storage
config = SecurityConfig(
    audit={
        "storage": {
            "type": "file",
            "path": "/var/log/myapp/audit.log",
            "rotation": {
                "size": "100MB",
                "backup_count": 10,
            }
        }
    }
)
```

### Cloud Integration

Send audit logs to cloud logging services:

```python
# Configure for cloud storage (AWS CloudWatch example)
config = SecurityConfig(
    audit={
        "storage": {
            "type": "cloud",
            "provider": "aws",
            "log_group": "/myapp/audit",
            "region": "us-west-2",
        }
    }
)
```

## Best Practices

1. **Log all security-critical events**: Authentication attempts, permission changes, sensitive data access, etc.

2. **Include contextual information**: User IDs, IP addresses, request identifiers, and other relevant metadata.

3. **Protect audit logs**: Ensure logs are stored securely and cannot be modified or deleted by unauthorized users.

4. **Implement log rotation**: Establish policies for log retention and rotation to manage storage while meeting compliance requirements.

5. **Set up alerting**: Configure real-time alerts for critical security events like multiple failed login attempts or unusual access patterns.

6. **Regular log reviews**: Establish a process for periodically reviewing audit logs to identify potential security issues.

7. **Compliance alignment**: Configure logging to meet specific regulatory requirements relevant to your application.

## Example Usage

### Basic Usage

```python
from uno.security import SecurityManager
from uno.security.audit import SecurityEvent

# Get security manager instance
security = SecurityManager.get_instance()

# Log authentication event
security.audit.log(
    event_type=SecurityEvent.LOGIN_SUCCESS,
    user_id="user123",
    metadata={
        "ip_address": "192.168.1.1",
        "session_id": "sess_12345",
    }
)
```

### Custom Events

Define and log custom security events:

```python
from uno.security.audit import SecurityEvent, AuditLogger

# Define custom event (as a string or by extending SecurityEvent enum)
CUSTOM_EVENT = "ACCOUNT_LOCKOUT"

# Log custom event
AuditLogger.get_instance().log(
    event_type=CUSTOM_EVENT,
    user_id="user123",
    metadata={
        "reason": "too_many_attempts",
        "lockout_duration": 30,  # minutes
    }
)
```

### Integration with Request Handlers

Automatically log security events in web applications:

```python
from uno.security import SecurityManager

# In FastAPI example
@app.post("/login")
async def login(credentials: LoginCredentials):
    try:
        # Authenticate user
        user = authenticate(credentials.username, credentials.password)
        
        # Log successful login
        SecurityManager.get_instance().audit.log(
            event_type=SecurityEvent.LOGIN_SUCCESS,
            user_id=user.id,
            metadata={
                "ip": request.client.host,
                "user_agent": request.headers.get("User-Agent"),
            }
        )
        
        # Return token
        return {"token": create_token(user)}
        
    except AuthenticationError as e:
        # Log failed login
        SecurityManager.get_instance().audit.log(
            event_type=SecurityEvent.LOGIN_FAILURE,
            user_id=credentials.username,  # Using username since user ID unknown
            metadata={
                "ip": request.client.host,
                "reason": str(e),
            }
        )
        
        # Return error
        raise HTTPException(status_code=401, detail="Authentication failed")
```

## Troubleshooting

### Common Issues

1. **Performance concerns**: If audit logging impacts performance, consider:
   - Asynchronous logging
   - Batching log entries
   - Using a dedicated logging service

2. **Storage growth**: Monitor log storage and implement appropriate retention policies.

3. **Missing events**: Verify that logs are being properly captured by checking log storage.

### Debugging

Enable debug logging for the audit system:

```python
import logging

# Set audit logging to debug level
logging.getLogger("uno.security.audit").setLevel(logging.DEBUG)
```