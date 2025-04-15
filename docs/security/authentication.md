# Authentication

The Uno Security Framework provides comprehensive authentication functionality for securing user access to your applications.

## Overview

The authentication component includes:

- **Password management**: Secure password hashing, validation, and policy enforcement
- **Multi-factor authentication**: Time-based one-time passwords (TOTP) and other MFA methods
- **Single sign-on**: Integration with OAuth 2.0, OpenID Connect, and SAML
- **JWT-based authentication**: Complete JSON Web Token (JWT) authentication system for FastAPI applications
- **Role-based access control**: Flexible role-based authorization system

## Configuration

Authentication is configured through the `AuthenticationConfig` class:

```python
from uno.security.config import (```

AuthenticationConfig, MFAType, SSOProvider, PasswordPolicyConfig, PasswordPolicyLevel
```
)

auth_config = AuthenticationConfig(```

# Multi-factor authentication
enable_mfa=True,
mfa_type=MFAType.TOTP,
```
    ```

# Single sign-on
enable_sso=True,
sso_provider=SSOProvider.OIDC,
sso_config={
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "redirect_uri": "https://example.com/callback",
    "provider_url": "https://auth.example.com"
},
```
    ```

# Session management
session_timeout_minutes=60,
idle_timeout_minutes=15,
remember_me_duration_days=30,
```
    ```

# JWT configuration
jwt_expiration_minutes=60,
refresh_token_expiration_days=7,
jwt_secret_key="your-secure-secret-key",
jwt_algorithm="HS256",
jwt_issuer="uno_application",
jwt_audience="uno_api",
enable_jwt_middleware=True,
jwt_exclude_paths=[
    "/auth/login", 
    "/auth/register", 
    "/auth/refresh", 
    "/docs", 
    "/openapi.json"
],
```
    ```

# Password policy
password_policy=PasswordPolicyConfig(```

level=PasswordPolicyLevel.STRICT,
min_length=16,
require_uppercase=True,
require_lowercase=True,
require_numbers=True,
require_special_chars=True
```,
    password_history=5,
    max_age_days=90,
    lockout_threshold=5,
    lockout_duration_minutes=30
)
```
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

### JWT Authentication

The Uno framework provides comprehensive JSON Web Token (JWT) authentication for FastAPI applications.

#### Basic JWT Setup

```python
from fastapi import FastAPI, Depends
from uno.security.auth import JWTAuth, JWTConfig, get_current_user_id, require_role
from uno.security.auth.fastapi_integration import configure_jwt_auth

# Create FastAPI app
app = FastAPI()

# Configure JWT auth
jwt_config = JWTConfig(```

secret_key="your-secure-secret-key",
algorithm="HS256",
access_token_expire_minutes=30
```
)

# Set up JWT authentication
jwt_auth = configure_jwt_auth(```

app=app,
config=jwt_config,
exclude_paths=["/auth/login", "/docs", "/openapi.json"]
```
)

# Protected route
@app.get("/protected")
async def protected_route(user_id: str = Depends(get_current_user_id)):```

return {"message": "This is a protected route", "user_id": user_id}
```

# Admin route with role check
@app.get("/admin")
async def admin_route(```

user_id: str = Depends(get_current_user_id),
has_role: bool = Depends(require_role("admin"))
```
):```

return {"message": "Admin access granted", "user_id": user_id}
```
```

#### Complete Authentication System

For a more complete authentication system, including login and registration endpoints:

```python
from fastapi import FastAPI, Depends, HTTPException
from uno.security.auth import JWTAuth, JWTConfig
from uno.security.auth.fastapi_integration import (```

configure_jwt_auth,
create_auth_router,
create_test_authenticator
```
)

# Create FastAPI app
app = FastAPI()

# Configure JWT authentication
jwt_config = JWTConfig(```

secret_key="your-secure-secret-key",
algorithm="HS256",
access_token_expire_minutes=30
```,
    refresh_token_expire_days=7
)

# Sample user database (replace with your own user storage)
users_db = {```

"user1": {
    "id": "user1",
    "username": "john",
    "password": "hashed_password_here",
    "email": "john@example.com",
    "roles": ["user"]
}
```
}

# Set up JWT authentication
jwt_auth = configure_jwt_auth(```

app=app,
config=jwt_config
```
)

# Create authenticator function
authenticate_user = create_test_authenticator(users_db)

# Create auth router with login and refresh endpoints
auth_router = create_auth_router(```

jwt_auth=jwt_auth,
user_model=dict,  # Replace with your User model
authenticate_user=authenticate_user
```
)

# Register the auth router
app.include_router(auth_router)
```

#### Token Creation and Validation

The `JWTAuth` class provides methods for creating and validating tokens:

```python
from uno.security.auth import JWTAuth, JWTConfig

# Create JWT auth
jwt_auth = JWTAuth(JWTConfig("your-secure-secret-key"))

# Create access token
access_token = jwt_auth.create_access_token(```

subject="user123",
additional_claims={
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["user", "admin"]
}
```
)

# Create refresh token
refresh_token = jwt_auth.create_refresh_token(```

subject="user123",
additional_claims={
    "email": "user@example.com"
}
```
)

# Decode and validate token
token_data = jwt_auth.decode_token(access_token)
print(f"User ID: {token_data.sub}")
print(f"Roles: {token_data.roles}")
print(f"Email: {token_data.email}")

# Refresh access token
new_access_token = jwt_auth.refresh_access_token(refresh_token)
```

#### FastAPI Dependencies

The Uno JWT system provides several FastAPI dependencies for authenticated routes:

```python
from fastapi import FastAPI, Depends
from uno.security.auth import (```

get_current_user_id,
get_current_user_roles,
get_current_tenant_id,
require_role,
require_any_role,
require_all_roles
```
)

app = FastAPI()

# Route requiring authentication
@app.get("/profile")
async def get_profile(user_id: str = Depends(get_current_user_id)):```

return {"user_id": user_id}
```

# Route requiring a specific role
@app.get("/admin")
async def admin_panel(```

user_id: str = Depends(get_current_user_id),
has_role: bool = Depends(require_role("admin"))
```
):```

return {"message": "Welcome to the admin panel"}
```

# Route requiring any of multiple roles
@app.get("/reports")
async def reports(```

user_id: str = Depends(get_current_user_id),
has_role: bool = Depends(require_any_role(["admin", "reports"]))
```
):```

return {"message": "Access to reports granted"}
```

# Route requiring all roles
@app.get("/super-admin")
async def super_admin(```

user_id: str = Depends(get_current_user_id),
has_roles: bool = Depends(require_all_roles(["admin", "superuser"]))
```
):```

return {"message": "Super admin access granted"}
```

# Route with tenant context
@app.get("/tenant-data")
async def tenant_data(```

user_id: str = Depends(get_current_user_id),
tenant_id: str = Depends(get_current_tenant_id)
```
):```

return {"message": f"Data for tenant {tenant_id}"}
```
```

#### JWT Security Considerations

1. **Secret Key**: Use a strong, unique secret key for JWT signing
2. **HTTPS**: Always use HTTPS to protect tokens in transit
3. **Token Expiration**: Use short-lived access tokens and longer-lived refresh tokens
4. **Claims Validation**: Validate issuer, audience, and other claims
5. **Token Storage**: Store tokens securely on the client side
6. **Refresh Token Security**: Treat refresh tokens with extra security
7. **Revocation**: Implement token revocation for logout and security incidents

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
policy = SecurePasswordPolicy(```

level=PasswordPolicyLevel.STRICT,
min_length=16,
require_uppercase=True,
require_lowercase=True,
require_numbers=True,
require_special_chars=True
```
)

# Validate a password
result = policy.validate("MySecurePassword123!")
if result["valid"]:```

# Password is valid
pass
```
else:```

# Password is invalid
print(result["message"])
```

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
totp_provider = TOTPProvider(```

digits=6,
interval=30,
algorithm="SHA1",
issuer="My App"
```
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
oauth2_provider = OAuth2Provider(```

client_id="your-client-id",
client_secret="your-client-secret",
redirect_uri="https://example.com/callback",
authorization_url="https://auth.example.com/oauth/authorize",
token_url="https://auth.example.com/oauth/token",
userinfo_url="https://auth.example.com/userinfo"
```
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
oidc_provider = OIDCProvider(```

client_id="your-client-id",
client_secret="your-client-secret",
redirect_uri="https://example.com/callback",
issuer_url="https://auth.example.com"
```
)

# The rest is the same as OAuth2Provider
```

## Advanced JWT Usage

### Custom Token Claims

You can add custom claims to your tokens:

```python
# Add custom claims
access_token = jwt_auth.create_access_token(```

subject="user123",
additional_claims={
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["user", "admin"],
    "permissions": ["read", "write"],
    "subscription_level": "premium"
}
```
)

# Access custom claims
token_data = jwt_auth.decode_token(access_token)
subscription = token_data.custom_claims.get("subscription_level")
```

### Multi-tenancy Support

The JWT authentication system supports multi-tenancy:

```python
# Add tenant information to token
access_token = jwt_auth.create_access_token(```

subject="user123",
additional_claims={
    "tenant_id": "tenant456"
}
```
)

# Tenant context is automatically extracted
@app.get("/tenant-profile")
async def tenant_profile(```

user_id: str = Depends(get_current_user_id),
tenant_id: str = Depends(get_current_tenant_id)
```
):```

# Data is automatically scoped to the tenant
return {"user_id": user_id, "tenant_id": tenant_id}
```
```

### Custom Authentication Logic

You can implement custom authentication logic:

```python
from fastapi import FastAPI, Depends, HTTPException, status
from uno.security.auth import JWTBearer, TokenData

# Create FastAPI app
app = FastAPI()

# Create JWT bearer security scheme
oauth2_scheme = JWTBearer(jwt_auth)

# Custom validation
async def get_premium_user(token_data: TokenData = Depends(oauth2_scheme)):```

# Check if user has premium subscription
if token_data.custom_claims.get("subscription_level") != "premium":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Premium subscription required"
    )
```
    ```

# Return user ID
return token_data.sub
```

# Protected premium route
@app.get("/premium-content")
async def premium_content(user_id: str = Depends(get_premium_user)):```

return {"message": "This is premium content", "user_id": user_id}
```
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

### JWT Token Security

1. **Token Storage**: Never store tokens in localStorage or sessionStorage; use HttpOnly cookies instead.
2. **Token Scope**: Limit tokens to the minimum required scope and permissions.
3. **Token Leakage**: Implement mechanisms to detect and respond to token leakage.
4. **Token Refresh**: Implement a secure token refresh mechanism for longer sessions.
5. **Token Revocation**: Provide a way to revoke tokens when users log out or in security incidents.