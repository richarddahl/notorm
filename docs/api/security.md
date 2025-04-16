# Security API

The Security module provides comprehensive security features for Uno applications, including authentication, authorization, encryption, and audit logging. This document describes the API for interacting with the Security module.

## Overview

The Security module is built on domain-driven design principles and offers the following key capabilities:

- **Audit Logging**: Track security events like login attempts, access control decisions, and administrative actions.
- **Authentication**: Manage JWT tokens, password hashing, and password policy validation.
- **Multi-Factor Authentication**: Set up and verify various MFA methods, primarily TOTP.
- **Encryption**: Protect sensitive data with field-level encryption and key management.

## Endpoints

The Security module exposes RESTful endpoints under the `/api/security` prefix.

### Audit Events

#### Create Security Event

```
POST /api/security/events
```

Create a new security event for audit logging.

**Request Body**:

```json
{
  "event_type": "login",
  "user_id": "user-123",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "success": true,
  "message": "User login successful",
  "severity": "info",
  "details": {
    "session_id": "sess-456",
    "method": "password"
  },
  "context": {
    "app_id": "app-789"
  }
}
```

**Response** (201 Created):

```json
{
  "id": "evt-123",
  "event_type": "login",
  "user_id": "user-123",
  "timestamp": "2025-04-16T10:30:00Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "success": true,
  "message": "User login successful",
  "severity": "info",
  "details": {
    "session_id": "sess-456",
    "method": "password"
  }
}
```

#### Get Security Events

```
GET /api/security/events
```

Get security events with filtering and pagination.

**Query Parameters**:

- `event_type`: Filter by event type
- `user_id`: Filter by user ID
- `start_time`: Filter by start time (ISO 8601 format)
- `end_time`: Filter by end time (ISO 8601 format)
- `severity`: Filter by severity level
- `success`: Filter by success flag
- `page`: Page number (default: 1)
- `page_size`: Page size (default: 20, max: 100)

**Response** (200 OK):

```json
[
  {
    "id": "evt-123",
    "event_type": "login",
    "user_id": "user-123",
    "timestamp": "2025-04-16T10:30:00Z",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "success": true,
    "message": "User login successful",
    "severity": "info",
    "details": {
      "session_id": "sess-456",
      "method": "password"
    }
  },
  // More events...
]
```

### Authentication

#### Generate Token

```
POST /api/security/tokens
```

Generate a new JWT token.

**Request Body**:

```json
{
  "user_id": "user-123",
  "token_type": "access",
  "roles": ["user", "admin"],
  "tenant_id": "tenant-456",
  "custom_claims": {
    "app_id": "app-789"
  }
}
```

**Response** (200 OK):

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_id": "token-123",
  "expires_at": "2025-04-16T11:30:00Z",
  "token_type": "access"
}
```

#### Validate Token

```
POST /api/security/tokens/validate
```

Validate a JWT token.

**Request Body**:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):

```json
{
  "valid": true,
  "claims": {
    "sub": "user-123",
    "exp": 1713193800,
    "iat": 1713190200,
    "jti": "token-123",
    "token_type": "access",
    "roles": ["user", "admin"],
    "tenant_id": "tenant-456"
  }
}
```

Or, if the token is invalid:

```json
{
  "valid": false,
  "error": "Token has expired"
}
```

#### Revoke Token

```
POST /api/security/tokens/revoke/{token_id}
```

Revoke a JWT token.

**Path Parameters**:

- `token_id`: ID of the token to revoke

**Response** (204 No Content)

#### Revoke All User Tokens

```
POST /api/security/tokens/revoke-all/{user_id}
```

Revoke all tokens for a specific user.

**Path Parameters**:

- `user_id`: ID of the user whose tokens should be revoked

**Response** (204 No Content)

### Multi-Factor Authentication

#### Set Up MFA

```
POST /api/security/mfa/setup
```

Set up multi-factor authentication for a user.

**Request Body**:

```json
{
  "user_id": "user-123",
  "mfa_type": "totp"
}
```

**Response** (200 OK):

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "backup_codes": [
    "12345678",
    "23456789",
    // More codes...
  ],
  "provision_uri": "otpauth://totp/Uno%20App:user-123?secret=JBSWY3DPEHPK3PXP&issuer=Uno%20App",
  "type": "totp"
}
```

#### Verify MFA

```
POST /api/security/mfa/verify
```

Verify a multi-factor authentication code.

**Request Body**:

```json
{
  "user_id": "user-123",
  "code": "123456",
  "mfa_type": "totp"
}
```

**Response** (200 OK):

```json
{
  "valid": true
}
```

Or, if the code is invalid:

```json
{
  "valid": false,
  "error": "Invalid code"
}
```

#### Verify Backup Code

```
POST /api/security/mfa/verify-backup
```

Verify a backup code for MFA.

**Request Body**:

```json
{
  "user_id": "user-123",
  "code": "12345678"
}
```

**Response** (200 OK):

```json
{
  "valid": true
}
```

Or, if the code is invalid:

```json
{
  "valid": false,
  "error": "Invalid backup code"
}
```

#### Deactivate MFA

```
POST /api/security/mfa/deactivate/{user_id}
```

Deactivate multi-factor authentication for a user.

**Path Parameters**:

- `user_id`: ID of the user whose MFA should be deactivated

**Response** (204 No Content)

#### Regenerate Backup Codes

```
POST /api/security/mfa/regenerate-backup-codes
```

Regenerate backup codes for MFA.

**Request Body**:

```json
{
  "user_id": "user-123"
}
```

**Response** (200 OK):

```json
{
  "backup_codes": [
    "12345678",
    "23456789",
    // More codes...
  ]
}
```

### Password Validation

```
POST /api/security/password/validate
```

Validate a password against the password policy.

**Request Body**:

```json
{
  "password": "MySecurePassword123!"
}
```

**Response** (200 OK):

```json
{
  "valid": true,
  "message": "Password meets all requirements"
}
```

Or, if the password is invalid:

```json
{
  "valid": false,
  "message": "Password must contain at least one special character"
}
```

## Integration with Domain-Driven Design

The Security module is built using domain-driven design principles:

1. **Entities**: Core domain objects like `SecurityEvent`, `EncryptionKey`, `JWTToken`, and `MFACredential`.
2. **Value Objects**: Immutable objects like `EncryptionKeyId` and `TokenId`.
3. **Repositories**: Data access interfaces with implementations for each entity.
4. **Domain Services**: Business logic in services like `AuditService`, `EncryptionService`, `AuthenticationService`, and `MFAService`.
5. **Application Services**: Coordinating services like `SecurityService` that orchestrate domain services.

## Using the Security Module Programmatically

### Configuring Dependencies

```python
from uno.dependencies.container import configure_container
from uno.security import configure_security_dependencies

# Configure security dependencies
configure_container(configure_security_dependencies)
```

### Using Security Services

```python
import inject
from uno.security import (
    SecurityService,
    AuditServiceProtocol,
    SecurityEvent
)

# Get security service
security_service = inject.instance(SecurityService)

# Get audit service
audit_service = inject.instance(AuditServiceProtocol)

# Create and log a security event
event = SecurityEvent.create_login_event(
    user_id="user-123",
    success=True,
    ip_address="192.168.1.1"
)
result = await audit_service.log_event(event)
```

### Authentication Example

```python
from uno.security import (
    AuthenticationServiceProtocol,
    TokenType
)

# Get authentication service
auth_service = inject.instance(AuthenticationServiceProtocol)

# Generate a token
result = await auth_service.generate_token(
    user_id="user-123",
    token_type=TokenType.ACCESS,
    roles=["user", "admin"]
)

if result.is_success():
    token_string, token_entity = result.value
    print(f"Token: {token_string}")
else:
    print(f"Error: {result.error}")

# Validate a token
validate_result = await auth_service.validate_token(token_string)

if validate_result.is_success():
    claims = validate_result.value
    print(f"Valid token for user: {claims['sub']}")
else:
    print(f"Error: {validate_result.error}")
```

### MFA Example

```python
from uno.security import (
    MFAServiceProtocol,
    MFAType
)

# Get MFA service
mfa_service = inject.instance(MFAServiceProtocol)

# Set up MFA
setup_result = await mfa_service.setup_mfa(
    user_id="user-123",
    mfa_type=MFAType.TOTP
)

if setup_result.is_success():
    setup_info = setup_result.value
    print(f"Secret: {setup_info['secret']}")
    print(f"Provision URI: {setup_info['provision_uri']}")
else:
    print(f"Error: {setup_result.error}")

# Verify MFA code
verify_result = await mfa_service.verify_mfa(
    user_id="user-123",
    code="123456"
)

if verify_result.is_success() and verify_result.value:
    print("MFA code verified")
else:
    print("Invalid MFA code")
```

## Security Best Practices

When using the Security module, follow these best practices:

1. **Store Secrets Securely**: Never hardcode secrets or store them in version control.
2. **Use Environment Variables**: Load sensitive information from environment variables or a secure vault.
3. **Enable MFA**: Multi-factor authentication significantly improves security.
4. **Rotate Keys Regularly**: Set up a key rotation schedule for encryption keys.
5. **Monitor Audit Logs**: Regularly review security events to detect suspicious activity.
6. **Use HTTPS**: Always use HTTPS in production to protect tokens and sensitive data.
7. **Set Appropriate Timeouts**: Configure short-lived access tokens and longer-lived refresh tokens.
8. **Implement Rate Limiting**: Protect authentication endpoints from brute force attacks.

## Error Handling

All services in the Security module use the Result pattern for error handling. This means that instead of throwing exceptions, they return a `Result` object that can be either successful or contain an error message.

```python
from uno.core.result import Result

# Example of checking a result
result = await auth_service.validate_token(token)

if result.is_success():
    # Success case
    claims = result.value
    user_id = claims["sub"]
else:
    # Error case
    error_message = result.error
    logger.error(f"Token validation failed: {error_message}")
```

This pattern allows for more robust error handling and better separation of concerns.

## Further Reading

- [Security Configuration Guide](../security/overview.md)
- [Authentication Deep Dive](../security/authentication.md)
- [Encryption Guide](../security/encryption.md)
- [Audit Logging Best Practices](../security/audit.md)