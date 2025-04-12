# Authentication

The Uno Security Framework provides comprehensive authentication functionality for securing user access to your applications.

## Overview

The authentication component includes:

- **Password management**: Secure password hashing, validation, and policy enforcement
- **Multi-factor authentication**: Time-based one-time passwords (TOTP) and other MFA methods
- **Single sign-on**: Integration with OAuth 2.0, OpenID Connect, and SAML

## Configuration

Authentication is configured through the `AuthenticationConfig` class:

```python
from uno.security.config import (
    AuthenticationConfig, MFAType, SSOProvider, PasswordPolicyConfig, PasswordPolicyLevel
)

auth_config = AuthenticationConfig(
    enable_mfa=True,
    mfa_type=MFAType.TOTP,
    enable_sso=True,
    sso_provider=SSOProvider.OIDC,
    sso_config={
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "redirect_uri": "https://example.com/callback",
        "provider_url": "https://auth.example.com"
    },
    session_timeout_minutes=60,
    idle_timeout_minutes=15,
    remember_me_duration_days=30,
    jwt_expiration_minutes=60,
    refresh_token_expiration_days=7,
    password_policy=PasswordPolicyConfig(
        level=PasswordPolicyLevel.STRICT,
        min_length=16,
        require_uppercase=True,
        require_lowercase=True,
        require_numbers=True,
        require_special_chars=True,
        password_history=5,
        max_age_days=90,
        lockout_threshold=5,
        lockout_duration_minutes=30
    )
)
```

MFA types:

- `NONE`: No multi-factor authentication
- `TOTP`: Time-based one-time passwords (Google Authenticator, Authy, etc.)
- `SMS`: SMS-based verification codes
- `EMAIL`: Email-based verification codes
- `HARDWARE`: Hardware security keys
- `PUSH`: Push notifications to mobile devices

SSO providers:

- `NONE`: No single sign-on
- `OAUTH2`: OAuth 2.0
- `SAML`: Security Assertion Markup Language
- `OIDC`: OpenID Connect
- `LDAP`: Lightweight Directory Access Protocol
- `ACTIVE_DIRECTORY`: Microsoft Active Directory

Password policy levels:

- `BASIC`: Basic requirements (8+ characters, uppercase, lowercase, numbers)
- `STANDARD`: Standard requirements (12+ characters, uppercase, lowercase, numbers, special characters)
- `STRICT`: Strict requirements (16+ characters, uppercase, lowercase, numbers, special characters)
- `NIST`: NIST SP 800-63B recommendations (8+ characters, no composition rules, no mandatory rotation)
- `CUSTOM`: Custom requirements

## Using Authentication

### Password Management

```python
from uno.security import SecurityManager
from uno.security.config import SecurityConfig

# Create a security manager
security_manager = SecurityManager(SecurityConfig())

# Hash a password
hashed_password = security_manager.hash_password("MySecurePassword123!")

# Verify a password
is_valid = security_manager.verify_password("MySecurePassword123!", hashed_password)

# Validate a password against the policy
result = security_manager.validate_password_policy("MySecurePassword123!")
if result["valid"]:
    # Password is valid
    pass
else:
    # Password is invalid
    print(result["message"])

# Generate a secure password
password = security_manager.generate_secure_password()
```

#### Direct Password Hashing

You can also use the password hashing functions directly:

```python
from uno.security.auth.password import hash_password, verify_password

# Hash a password
hashed_password = hash_password("MySecurePassword123!")

# Verify a password
is_valid = verify_password("MySecurePassword123!", hashed_password)
```

### Password Policy

The framework includes a configurable password policy:

```python
from uno.security.auth.password import SecurePasswordPolicy, PasswordPolicyLevel

# Create a password policy
policy = SecurePasswordPolicy(
    level=PasswordPolicyLevel.STRICT,
    min_length=16,
    require_uppercase=True,
    require_lowercase=True,
    require_numbers=True,
    require_special_chars=True
)

# Validate a password
result = policy.validate("MySecurePassword123!")
if result["valid"]:
    # Password is valid
    pass
else:
    # Password is invalid
    print(result["message"])

# Generate a secure password
password = policy.generate_password()
```

### Multi-Factor Authentication

```python
# Set up MFA for a user
mfa_setup = security_manager.setup_mfa("user123")
# QR code and setup instructions are in mfa_setup

# Verify an MFA code
is_valid = security_manager.verify_mfa("user123", "123456")

# Disable MFA for a user
security_manager.mfa_manager.disable_mfa("user123")

# Reset MFA for a user
security_manager.mfa_manager.reset_mfa("user123")
```

#### TOTP Provider

You can also use the TOTP provider directly:

```python
from uno.security.auth.totp import TOTPProvider

# Create a TOTP provider
totp_provider = TOTPProvider(
    digits=6,
    interval=30,
    algorithm="SHA1",
    issuer="My App"
)

# Set up TOTP for a user
setup_data = totp_provider.setup("user123")
# QR code and secret are in setup_data

# Verify a TOTP code
is_valid = totp_provider.verify("user123", "123456", setup_data)
```

### Single Sign-On

#### OAuth 2.0

```python
from uno.security.auth.sso import OAuth2Provider

# Create an OAuth2 provider
oauth2_provider = OAuth2Provider(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="https://example.com/callback",
    authorization_url="https://auth.example.com/oauth/authorize",
    token_url="https://auth.example.com/oauth/token",
    userinfo_url="https://auth.example.com/userinfo"
)

# Get the authorization URL
auth_url = oauth2_provider.get_authorization_url()
# Redirect the user to this URL

# Handle the callback
code = "authorization-code-from-callback"
user = oauth2_provider.handle_callback(code)
# User information is in the user object

# Validate a token
is_valid = oauth2_provider.validate_token("access-token")

# Refresh a token
new_tokens = oauth2_provider.refresh_token("refresh-token")

# Get user information
user_info = oauth2_provider.get_user_info("access-token")
```

#### OpenID Connect

```python
from uno.security.auth.sso import OIDCProvider

# Create an OIDC provider
oidc_provider = OIDCProvider(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="https://example.com/callback",
    issuer_url="https://auth.example.com"
)

# The rest is the same as OAuth2Provider
```

## Best Practices

1. **Use strong password policies**: Enforce strong password policies to prevent weak passwords.
2. **Enable MFA**: Enable multi-factor authentication for all users, especially administrators.
3. **Use HTTPS**: Always use HTTPS to protect authentication data in transit.
4. **Implement account lockout**: Implement account lockout after multiple failed login attempts.
5. **Use secure password storage**: Store passwords securely using modern hashing algorithms.
6. **Limit session duration**: Implement session timeouts to limit the impact of session hijacking.
7. **Implement CSRF protection**: Protect against cross-site request forgery attacks.
8. **Use secure cookies**: Set secure and HTTP-only flags on authentication cookies.
9. **Implement proper logging**: Log authentication events for security monitoring.
10. **Follow security standards**: Follow security standards like OWASP and NIST guidelines.

## Security Considerations

### Password Storage

The framework uses PBKDF2-HMAC-SHA256 with a randomly generated salt and 100,000 iterations for password hashing. This is a secure method that is resistant to brute-force attacks.

### MFA Security

TOTP-based MFA uses a shared secret that is encoded as a base32 string and displayed as a QR code. The secret should be stored securely on the server, and the QR code should be shown only once during setup.

### SSO Security

When implementing SSO, make sure to:

1. **Validate tokens**: Always validate tokens received from the identity provider.
2. **Use HTTPS**: Always use HTTPS for all SSO-related URLs.
3. **Validate state**: Use the state parameter to prevent CSRF attacks.
4. **Secure client secrets**: Keep client secrets secure and never expose them to clients.
5. **Validate redirect URIs**: Only allow pre-registered redirect URIs.