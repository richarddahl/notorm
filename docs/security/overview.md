# Security Framework

The Uno Security Framework provides comprehensive security features for Uno applications, including encryption, authentication, audit logging, and security testing.

## Key Components

The security framework consists of several key components:

1. **Encryption**: Field-level encryption, data-at-rest encryption, and key management
2. **Authentication**: Multi-factor authentication, secure password policies, and single sign-on
3. **Audit Logging**: Comprehensive audit logging of security events
4. **Security Testing**: Dependency scanning, static analysis, and penetration testing

## Getting Started

To use the Uno Security Framework, you first need to create a `SecurityManager` instance:

```python
from uno.security import SecurityManager
from uno.security.config import SecurityConfig

# Create a security configuration
config = SecurityConfig()

# Create a security manager
security_manager = SecurityManager(config)
```

You can then use the security manager to access various security features:

```python
# Encrypt sensitive data
encrypted_data = security_manager.encrypt("sensitive data")

# Decrypt data
decrypted_data = security_manager.decrypt(encrypted_data)

# Hash a password
hashed_password = security_manager.hash_password("MySecurePassword123!")

# Verify a password
is_valid = security_manager.verify_password("MySecurePassword123!", hashed_password)

# Log a security event
from uno.security.audit import SecurityEvent
event = SecurityEvent.login(user_id="user123", ip_address="192.168.1.1")
security_manager.trigger_event(event)
```

## Configuration

The security framework is highly configurable through the `SecurityConfig` class. Here's an example configuration:

```python
from uno.security.config import (```

SecurityConfig, EncryptionAlgorithm, KeyManagementType, 
PasswordPolicyLevel, MFAType, AuditLogLevel
```
)

# Create a configuration
config = SecurityConfig(```

encryption=EncryptionConfig(```

algorithm=EncryptionAlgorithm.AES_GCM,
key_management=KeyManagementType.VAULT,
field_level_encryption=True,
encrypted_fields=["password", "credit_card", "ssn"]
```
),
authentication=AuthenticationConfig(```

enable_mfa=True,
mfa_type=MFAType.TOTP,
session_timeout_minutes=60,
password_policy=PasswordPolicyConfig(
    level=PasswordPolicyLevel.STRICT,
    min_length=16
)
```
),
auditing=AuditingConfig(```

enabled=True,
level=AuditLogLevel.DETAILED,
storage=AuditLogStorage.DATABASE,
retention_days=365
```
),
web_security=WebSecurityConfig(```

enable_csrf_protection=True,
enable_xss_protection=True,
content_security_policy_level="strict",
allowed_hosts=["example.com"]
```
),
testing=SecurityTestingConfig(```

enable_dependency_scanning=True,
enable_static_analysis=True,
fail_build_on_critical=True
```
)
```
)
```

The framework also provides predefined configurations for production and development environments:

```python
# Production configuration
prod_config = SecurityConfig.production_defaults()

# Development configuration
dev_config = SecurityConfig.development_defaults()
```

## Encryption

The encryption component provides field-level encryption, data-at-rest encryption, and key management.

### Field-Level Encryption

Field-level encryption allows you to encrypt sensitive fields in your models:

```python
# Encrypt a field
encrypted_ssn = security_manager.encrypt_field("ssn", "123-45-6789")

# Decrypt a field
decrypted_ssn = security_manager.decrypt_field("ssn", encrypted_ssn)

# Encrypt a model
from uno.security.encryption import FieldEncryption
field_encryption = FieldEncryption(security_manager.encryption_manager)
encrypted_model = field_encryption.encrypt_model(user)

# Decrypt a model
decrypted_model = field_encryption.decrypt_model(encrypted_model)
```

### Key Management

The framework supports various key management systems:

- Local key management (for development)
- HashiCorp Vault
- AWS KMS
- Azure Key Vault
- Google Cloud KMS

```python
# Rotate encryption keys
security_manager.encryption_manager.rotate_keys()
```

## Authentication

The authentication component provides multi-factor authentication, secure password policies, JWT token validation, and single sign-on. For a comprehensive guide to authentication, see [Authentication](authentication.md).

### Multi-Factor Authentication

```python
# Set up MFA for a user
mfa_setup = security_manager.setup_mfa("user123")
# QR code and setup instructions are in mfa_setup

# Verify an MFA code
is_valid = security_manager.verify_mfa("user123", "123456")
```

### Password Management

```python
# Validate a password against the policy
result = security_manager.validate_password_policy("MySecurePassword123!")
if result["valid"]:```

# Password is valid
pass
```
else:```

# Password is invalid
print(result["message"])
```

# Generate a secure password
password = security_manager.generate_secure_password()
```

### Single Sign-On

```python
from uno.security.auth import OIDCProvider

# Create an OIDC provider
oidc_provider = OIDCProvider(```

client_id="client-id",
client_secret="client-secret",
redirect_uri="https://example.com/callback",
issuer_url="https://auth.example.com"
```
)

# Get the authorization URL
auth_url = oidc_provider.get_authorization_url()

# Handle the callback
user = oidc_provider.handle_callback(code="authorization-code")
```

## Audit Logging

The audit logging component provides comprehensive logging of security events.

```python
# Log a login event
event = SecurityEvent.login(user_id="user123", ip_address="192.168.1.1")
security_manager.trigger_event(event)

# Log a failed login
event = SecurityEvent.login(user_id="user123", success=False, ip_address="192.168.1.1")
security_manager.trigger_event(event)

# Log an admin action
event = SecurityEvent.admin_action(```

user_id="admin",
action="delete_user",
target_id="user123",
target_type="user"
```
)
security_manager.trigger_event(event)

# Get audit logs
events = security_manager.audit_log_manager.get_events(```

start_time=time.time() - 86400,  # Last 24 hours
event_types=["login", "failed_login"],
user_id="user123"
```
)

# Analyze audit logs
analysis = security_manager.audit_log_manager.analyze_events()
print(f"Total events: {analysis['total_events']}")
print(f"Failed events: {analysis['failed_count']}")
```

## Security Testing

The security testing component provides dependency scanning, static analysis, and penetration testing.

```python
from uno.security.testing import SecurityScanner

# Create a security scanner
scanner = SecurityScanner(security_manager.config.testing)

# Scan a target
results = scanner.scan("/path/to/app")

# Check for vulnerabilities
for vuln in results["vulnerabilities"]:```

print(f"{vuln['severity']} vulnerability: {vuln['title']}")
print(f"  {vuln['description']}")
if vuln["recommendation"]:```

print(f"  Recommendation: {vuln['recommendation']}")
```
```

# Save a report
scanner.save_report(results, "security_report.json")
```

## Web Security

The web security component provides CSRF protection, XSS protection, and content security policies.

```python
# Get security headers
headers = security_manager.get_security_headers()
# Add these headers to your HTTP responses

# Validate a CORS request
result = security_manager.validate_cors_request(```

origin="https://example.com",
method="GET",
headers=["Content-Type", "Authorization"]
```
)
if result["allowed"]:```

# CORS request is allowed
cors_headers = result["headers"]
# Add these headers to your HTTP response
```
else:```

# CORS request is not allowed
pass
```

# Validate a host
is_allowed = security_manager.validate_host("example.com")
```

## Best Practices

Here are some best practices for using the Uno Security Framework:

1. **Use strong encryption**: Always use strong encryption algorithms like AES-GCM for sensitive data.
2. **Rotate keys regularly**: Rotate encryption keys regularly to limit the impact of a key compromise.
3. **Enable MFA**: Enable multi-factor authentication for all users, especially administrators.
4. **Use strict password policies**: Use strict password policies to prevent weak passwords.
5. **Log security events**: Log all security events and regularly review audit logs.
6. **Run security tests**: Run security tests regularly to detect vulnerabilities.
7. **Keep dependencies up to date**: Keep all dependencies up to date to avoid known vulnerabilities.
8. **Use secure defaults**: Use the predefined security configurations for production environments.
9. **Follow the principle of least privilege**: Give users only the permissions they need.
10. **Validate all inputs**: Validate all inputs to prevent injection attacks.