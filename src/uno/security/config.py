# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Security configuration for Uno applications.

This module provides a configuration system for security settings in Uno applications.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union, Any
import os
import yaml
from pathlib import Path
import secrets
import string

from pydantic import BaseModel, Field, root_validator, validator


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms."""
    
    AES_GCM = "aes-gcm"
    AES_CBC = "aes-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    RSA = "rsa"
    NONE = "none"


class KeyManagementType(str, Enum):
    """Key management types for encryption."""
    
    LOCAL = "local"
    VAULT = "vault"
    AWS_KMS = "aws-kms"
    AZURE_KEY_VAULT = "azure-key-vault"
    GCP_KMS = "gcp-kms"


class PasswordPolicyLevel(str, Enum):
    """Password policy levels."""
    
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CUSTOM = "custom"
    NIST = "nist"


class MFAType(str, Enum):
    """Multi-factor authentication types."""
    
    NONE = "none"
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    HARDWARE = "hardware"
    PUSH = "push"


class SSOProvider(str, Enum):
    """Single sign-on providers."""
    
    NONE = "none"
    OAUTH2 = "oauth2"
    SAML = "saml"
    OIDC = "oidc"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active-directory"


class AuditLogLevel(str, Enum):
    """Audit log levels."""
    
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    DETAILED = "detailed"
    VERBOSE = "verbose"


class AuditLogStorage(str, Enum):
    """Audit log storage options."""
    
    DATABASE = "database"
    FILE = "file"
    REMOTE = "remote"
    SYSLOG = "syslog"


class ContentSecurityPolicyLevel(str, Enum):
    """Content Security Policy (CSP) levels."""
    
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    CUSTOM = "custom"


class EncryptionConfig(BaseModel):
    """Configuration for encryption."""
    
    algorithm: EncryptionAlgorithm = Field(
        EncryptionAlgorithm.AES_GCM,
        description="Encryption algorithm to use"
    )
    key_management: KeyManagementType = Field(
        KeyManagementType.LOCAL,
        description="Key management system"
    )
    key_rotation_days: int = Field(
        90,
        description="Number of days between key rotations"
    )
    data_at_rest_encryption: bool = Field(
        True,
        description="Enable encryption for data at rest"
    )
    data_in_transit_encryption: bool = Field(
        True,
        description="Enable encryption for data in transit (HTTPS)"
    )
    field_level_encryption: bool = Field(
        True,
        description="Enable field-level encryption for sensitive data"
    )
    encrypted_fields: List[str] = Field(
        default_factory=lambda: ["password", "ssn", "credit_card", "api_key"],
        description="Fields to encrypt"
    )
    key_vault_url: Optional[str] = Field(
        None,
        description="URL for key vault (if using external key management)"
    )
    key_identifier: Optional[str] = Field(
        None,
        description="Key identifier for key vault"
    )


class PasswordPolicyConfig(BaseModel):
    """Configuration for password policy."""
    
    level: PasswordPolicyLevel = Field(
        PasswordPolicyLevel.STANDARD,
        description="Password policy level"
    )
    min_length: int = Field(
        12,
        description="Minimum password length"
    )
    require_uppercase: bool = Field(
        True,
        description="Require uppercase letters"
    )
    require_lowercase: bool = Field(
        True,
        description="Require lowercase letters"
    )
    require_numbers: bool = Field(
        True,
        description="Require numbers"
    )
    require_special_chars: bool = Field(
        True,
        description="Require special characters"
    )
    password_history: int = Field(
        5,
        description="Number of previous passwords to remember"
    )
    max_age_days: int = Field(
        90,
        description="Maximum password age in days"
    )
    lockout_threshold: int = Field(
        5,
        description="Number of failed attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        30,
        description="Lockout duration in minutes"
    )
    
    @validator("min_length")
    def validate_min_length(cls, v, values, **kwargs):
        """Validate minimum password length based on level."""
        level = values.get("level")
        if level == PasswordPolicyLevel.BASIC and v < 8:
            return 8
        elif level == PasswordPolicyLevel.STANDARD and v < 12:
            return 12
        elif level == PasswordPolicyLevel.STRICT and v < 16:
            return 16
        elif level == PasswordPolicyLevel.NIST and v < 8:
            return 8
        return v
    
    @root_validator
    def validate_nist_policy(cls, values):
        """Apply NIST policy if selected."""
        if values.get("level") == PasswordPolicyLevel.NIST:
            # NIST SP 800-63B recommendations
            values["min_length"] = max(values.get("min_length", 8), 8)
            values["require_uppercase"] = False  # NIST doesn't require character types
            values["require_lowercase"] = False
            values["require_numbers"] = False
            values["require_special_chars"] = False
            values["max_age_days"] = 0  # NIST recommends against mandatory rotation
        return values
    
    def generate_password(self) -> str:
        """Generate a random password that meets the policy requirements."""
        length = max(16, self.min_length)  # Use at least 16 characters for generated passwords
        
        # Define character sets
        uppercase_chars = string.ascii_uppercase
        lowercase_chars = string.ascii_lowercase
        digit_chars = string.digits
        special_chars = string.punctuation
        
        # Start with an empty character set
        chars = ""
        
        # Add required character sets
        if self.require_uppercase:
            chars += uppercase_chars
        if self.require_lowercase:
            chars += lowercase_chars
        if self.require_numbers:
            chars += digit_chars
        if self.require_special_chars:
            chars += special_chars
        
        # If no character sets are required, use all
        if not chars:
            chars = string.ascii_letters + string.digits + string.punctuation
        
        # Generate password
        password = "".join(secrets.choice(chars) for _ in range(length))
        
        # Ensure all required character types are included
        if self.require_uppercase and not any(c in uppercase_chars for c in password):
            password = password[:-1] + secrets.choice(uppercase_chars)
        if self.require_lowercase and not any(c in lowercase_chars for c in password):
            password = password[:-1] + secrets.choice(lowercase_chars)
        if self.require_numbers and not any(c in digit_chars for c in password):
            password = password[:-1] + secrets.choice(digit_chars)
        if self.require_special_chars and not any(c in special_chars for c in password):
            password = password[:-1] + secrets.choice(special_chars)
        
        return password


class AuthenticationConfig(BaseModel):
    """Configuration for authentication."""
    
    enable_mfa: bool = Field(
        True,
        description="Enable multi-factor authentication"
    )
    mfa_type: MFAType = Field(
        MFAType.TOTP,
        description="Multi-factor authentication type"
    )
    enable_sso: bool = Field(
        False,
        description="Enable single sign-on"
    )
    sso_provider: SSOProvider = Field(
        SSOProvider.NONE,
        description="Single sign-on provider"
    )
    sso_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Single sign-on configuration"
    )
    session_timeout_minutes: int = Field(
        60,
        description="Session timeout in minutes"
    )
    idle_timeout_minutes: int = Field(
        15,
        description="Idle timeout in minutes"
    )
    remember_me_duration_days: int = Field(
        30,
        description="Remember me duration in days"
    )
    jwt_expiration_minutes: int = Field(
        60,
        description="JWT expiration in minutes"
    )
    refresh_token_expiration_days: int = Field(
        7,
        description="Refresh token expiration in days"
    )
    password_policy: PasswordPolicyConfig = Field(
        default_factory=PasswordPolicyConfig,
        description="Password policy"
    )
    

class AuditingConfig(BaseModel):
    """Configuration for security auditing."""
    
    enabled: bool = Field(
        True,
        description="Enable security auditing"
    )
    level: AuditLogLevel = Field(
        AuditLogLevel.STANDARD,
        description="Audit log level"
    )
    storage: AuditLogStorage = Field(
        AuditLogStorage.DATABASE,
        description="Audit log storage"
    )
    storage_path: Optional[str] = Field(
        None,
        description="Path for audit log storage (if file or remote)"
    )
    retention_days: int = Field(
        365,
        description="Audit log retention in days"
    )
    include_events: List[str] = Field(
        default_factory=lambda: [
            "login", 
            "logout", 
            "failed_login", 
            "password_change",
            "mfa_change",
            "permission_change",
            "admin_action",
            "security_setting_change",
            "data_export",
            "api_key_usage"
        ],
        description="Events to include in audit logs"
    )
    include_user_agent: bool = Field(
        True,
        description="Include user agent in audit logs"
    )
    include_ip_address: bool = Field(
        True,
        description="Include IP address in audit logs"
    )
    include_request_id: bool = Field(
        True,
        description="Include request ID in audit logs"
    )
    

class WebSecurityConfig(BaseModel):
    """Configuration for web security."""
    
    enable_csrf_protection: bool = Field(
        True,
        description="Enable CSRF protection"
    )
    enable_xss_protection: bool = Field(
        True,
        description="Enable XSS protection"
    )
    enable_clickjacking_protection: bool = Field(
        True,
        description="Enable clickjacking protection"
    )
    enable_content_type_options: bool = Field(
        True,
        description="Enable content type options"
    )
    enable_referrer_policy: bool = Field(
        True,
        description="Enable referrer policy"
    )
    referrer_policy: str = Field(
        "strict-origin-when-cross-origin",
        description="Referrer policy"
    )
    enable_hsts: bool = Field(
        True,
        description="Enable HTTP Strict Transport Security"
    )
    hsts_max_age: int = Field(
        31536000,  # 1 year
        description="HSTS max age in seconds"
    )
    hsts_include_subdomains: bool = Field(
        True,
        description="Include subdomains in HSTS"
    )
    hsts_preload: bool = Field(
        False,
        description="Enable HSTS preload"
    )
    content_security_policy_level: ContentSecurityPolicyLevel = Field(
        ContentSecurityPolicyLevel.STRICT,
        description="Content Security Policy level"
    )
    custom_csp_directives: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom Content Security Policy directives"
    )
    allowed_hosts: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed hosts"
    )
    cors_allowed_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins"
    )
    cors_allowed_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="CORS allowed methods"
    )
    cors_allowed_headers: List[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed headers"
    )
    cors_expose_headers: List[str] = Field(
        default_factory=list,
        description="CORS expose headers"
    )
    cors_allow_credentials: bool = Field(
        False,
        description="CORS allow credentials"
    )
    cors_max_age: int = Field(
        86400,  # 1 day
        description="CORS max age in seconds"
    )
    

class SecurityTestingConfig(BaseModel):
    """Configuration for security testing."""
    
    enable_dependency_scanning: bool = Field(
        True,
        description="Enable dependency scanning"
    )
    enable_static_analysis: bool = Field(
        True,
        description="Enable static analysis"
    )
    enable_dynamic_analysis: bool = Field(
        False,
        description="Enable dynamic analysis (DAST)"
    )
    enable_penetration_testing: bool = Field(
        False,
        description="Enable penetration testing"
    )
    scan_frequency: str = Field(
        "weekly",
        description="Scan frequency"
    )
    fail_build_on_critical: bool = Field(
        True,
        description="Fail build on critical vulnerabilities"
    )
    fail_build_on_high: bool = Field(
        True,
        description="Fail build on high vulnerabilities"
    )
    fail_build_on_medium: bool = Field(
        False,
        description="Fail build on medium vulnerabilities"
    )
    allowed_vulnerabilities: List[str] = Field(
        default_factory=list,
        description="Allowed vulnerability IDs (exceptions)"
    )
    security_scan_timeout: int = Field(
        1800,  # 30 minutes
        description="Security scan timeout in seconds"
    )


class SecurityConfig(BaseModel):
    """Main security configuration for Uno applications."""
    
    encryption: EncryptionConfig = Field(
        default_factory=EncryptionConfig,
        description="Encryption configuration"
    )
    authentication: AuthenticationConfig = Field(
        default_factory=AuthenticationConfig,
        description="Authentication configuration"
    )
    auditing: AuditingConfig = Field(
        default_factory=AuditingConfig,
        description="Auditing configuration"
    )
    web_security: WebSecurityConfig = Field(
        default_factory=WebSecurityConfig,
        description="Web security configuration"
    )
    testing: SecurityTestingConfig = Field(
        default_factory=SecurityTestingConfig,
        description="Security testing configuration"
    )
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "SecurityConfig":
        """
        Create a security configuration from a YAML file.
        
        Args:
            path: Path to the YAML file
            
        Returns:
            A SecurityConfig instance
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def to_yaml(self, path: Union[str, Path]) -> None:
        """
        Save the security configuration to a YAML file.
        
        Args:
            path: Path to save the YAML file
        """
        with open(path, "w") as f:
            yaml.dump(self.dict(), f, sort_keys=False, indent=2)
    
    @classmethod
    def production_defaults(cls) -> "SecurityConfig":
        """
        Create a security configuration with production defaults.
        
        Returns:
            A SecurityConfig instance with production defaults
        """
        config = cls()
        
        # Encryption defaults
        config.encryption.algorithm = EncryptionAlgorithm.AES_GCM
        config.encryption.key_management = KeyManagementType.VAULT
        config.encryption.key_rotation_days = 30
        
        # Authentication defaults
        config.authentication.enable_mfa = True
        config.authentication.mfa_type = MFAType.TOTP
        config.authentication.session_timeout_minutes = 30
        config.authentication.idle_timeout_minutes = 10
        config.authentication.password_policy.level = PasswordPolicyLevel.STRICT
        
        # Auditing defaults
        config.auditing.level = AuditLogLevel.DETAILED
        config.auditing.storage = AuditLogStorage.DATABASE
        config.auditing.retention_days = 730  # 2 years
        
        # Web security defaults
        config.web_security.content_security_policy_level = ContentSecurityPolicyLevel.STRICT
        config.web_security.hsts_max_age = 63072000  # 2 years
        config.web_security.hsts_preload = True
        config.web_security.cors_allow_credentials = False
        config.web_security.allowed_hosts = []  # Must be explicitly set
        
        # Testing defaults
        config.testing.enable_dependency_scanning = True
        config.testing.enable_static_analysis = True
        config.testing.enable_dynamic_analysis = True
        config.testing.fail_build_on_critical = True
        config.testing.fail_build_on_high = True
        
        return config
    
    @classmethod
    def development_defaults(cls) -> "SecurityConfig":
        """
        Create a security configuration with development defaults.
        
        Returns:
            A SecurityConfig instance with development defaults
        """
        config = cls()
        
        # Encryption defaults
        config.encryption.algorithm = EncryptionAlgorithm.AES_GCM
        config.encryption.key_management = KeyManagementType.LOCAL
        
        # Authentication defaults
        config.authentication.enable_mfa = False
        config.authentication.session_timeout_minutes = 240  # 4 hours
        config.authentication.idle_timeout_minutes = 60  # 1 hour
        config.authentication.password_policy.level = PasswordPolicyLevel.BASIC
        
        # Auditing defaults
        config.auditing.level = AuditLogLevel.BASIC
        
        # Web security defaults
        config.web_security.content_security_policy_level = ContentSecurityPolicyLevel.BASIC
        config.web_security.cors_allowed_origins = ["http://localhost:*"]
        config.web_security.allowed_hosts = ["localhost", "127.0.0.1"]
        
        # Testing defaults
        config.testing.enable_dependency_scanning = True
        config.testing.enable_static_analysis = True
        config.testing.enable_dynamic_analysis = False
        config.testing.fail_build_on_medium = False
        
        return config