# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Security manager for Uno applications.

This module provides a security manager for coordinating all security-related
functionality in Uno applications.
"""

import logging
from typing import Dict, List, Optional, Union, Any, Type, TypeVar, Protocol
import time
import json
import re
import ipaddress
from pathlib import Path

from uno.security.config import SecurityConfig
from uno.security.encryption import EncryptionManager
from uno.security.auth import MFAManager, SSOProvider
from uno.security.audit import AuditLogManager, SecurityEvent


class SecurityHook(Protocol):
    """Protocol for security hooks."""
    
    def __call__(self, event: SecurityEvent) -> None:
        """Process a security event."""
        ...


T = TypeVar('T')


class SecurityManager:
    """
    Security manager for Uno applications.
    
    This class is the main entry point for security functionality in Uno applications.
    It coordinates all security-related operations, including encryption, authentication,
    authorization, audit logging, and security testing.
    """
    
    def __init__(
        self,
        config: Optional[SecurityConfig] = None,
        encryption_manager: Optional[EncryptionManager] = None,
        mfa_manager: Optional[MFAManager] = None,
        audit_log_manager: Optional[AuditLogManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the security manager.
        
        Args:
            config: Security configuration
            encryption_manager: Encryption manager
            mfa_manager: Multi-factor authentication manager
            audit_log_manager: Audit log manager
            logger: Logger
        """
        self.config = config or SecurityConfig()
        self.logger = logger or logging.getLogger("uno.security")
        
        # Initialize managers
        from uno.security.encryption import EncryptionManager
        from uno.security.auth import MFAManager
        from uno.security.audit import AuditLogManager
        
        self.encryption_manager = encryption_manager or EncryptionManager(
            self.config.encryption, self.logger
        )
        self.mfa_manager = mfa_manager or MFAManager(
            self.config.authentication, self.logger
        )
        self.audit_log_manager = audit_log_manager or AuditLogManager(
            self.config.auditing, self.logger
        )
        
        # Security hooks
        self.security_hooks: Dict[str, List[SecurityHook]] = {}
        
        # Initialize security hooks
        self._initialize_hooks()
    
    def _initialize_hooks(self) -> None:
        """Initialize security hooks."""
        # Register default hooks
        self.register_hook("login", self._log_login_event)
        self.register_hook("logout", self._log_logout_event)
        self.register_hook("failed_login", self._log_failed_login)
        self.register_hook("password_change", self._log_password_change)
        self.register_hook("security_setting_change", self._log_security_setting_change)
    
    def register_hook(self, event_type: str, hook: SecurityHook) -> None:
        """
        Register a security hook.
        
        Args:
            event_type: Type of event to hook
            hook: Hook function
        """
        if event_type not in self.security_hooks:
            self.security_hooks[event_type] = []
        
        self.security_hooks[event_type].append(hook)
    
    def trigger_event(self, event: SecurityEvent) -> None:
        """
        Trigger a security event.
        
        Args:
            event: Security event
        """
        # Log the event
        self.audit_log_manager.log_event(event)
        
        # Execute hooks
        if event.event_type in self.security_hooks:
            for hook in self.security_hooks[event.event_type]:
                try:
                    hook(event)
                except Exception as e:
                    self.logger.error(f"Error executing security hook: {str(e)}")
    
    def encrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            context: Encryption context
            
        Returns:
            Encrypted data
        """
        return self.encryption_manager.encrypt(data, context)
    
    def decrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Decrypt data.
        
        Args:
            data: Data to decrypt
            context: Encryption context
            
        Returns:
            Decrypted data
        """
        return self.encryption_manager.decrypt(data, context)
    
    def encrypt_field(
        self, 
        field_name: str, 
        value: str, 
        entity_type: Optional[str] = None
    ) -> str:
        """
        Encrypt a field value.
        
        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type
            
        Returns:
            Encrypted field value
        """
        # Check if field should be encrypted
        if field_name in self.config.encryption.encrypted_fields:
            context = {"field_name": field_name}
            if entity_type:
                context["entity_type"] = entity_type
            
            return self.encryption_manager.encrypt(value, context)
        
        return value
    
    def decrypt_field(
        self, 
        field_name: str, 
        value: str, 
        entity_type: Optional[str] = None
    ) -> str:
        """
        Decrypt a field value.
        
        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type
            
        Returns:
            Decrypted field value
        """
        # Check if field should be decrypted
        if field_name in self.config.encryption.encrypted_fields:
            context = {"field_name": field_name}
            if entity_type:
                context["entity_type"] = entity_type
            
            return self.encryption_manager.decrypt(value, context)
        
        return value
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        from uno.security.auth import hash_password
        return hash_password(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password
            
        Returns:
            True if the password is valid, False otherwise
        """
        from uno.security.auth import verify_password
        return verify_password(password, hashed_password)
    
    def validate_password_policy(self, password: str) -> Dict[str, Any]:
        """
        Validate a password against the password policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results and messages
        """
        policy = self.config.authentication.password_policy
        
        # Check length
        if len(password) < policy.min_length:
            return {
                "valid": False,
                "message": f"Password must be at least {policy.min_length} characters long"
            }
        
        # Check complexity requirements
        if policy.require_uppercase and not any(c.isupper() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one uppercase letter"
            }
        
        if policy.require_lowercase and not any(c.islower() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one lowercase letter"
            }
        
        if policy.require_numbers and not any(c.isdigit() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one number"
            }
        
        if policy.require_special_chars and not any(not c.isalnum() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one special character"
            }
        
        # Check common passwords and patterns
        if self._is_common_password(password):
            return {
                "valid": False,
                "message": "Password is too common or easily guessable"
            }
        
        return {"valid": True, "message": "Password meets all requirements"}
    
    def _is_common_password(self, password: str) -> bool:
        """
        Check if a password is common or easily guessable.
        
        Args:
            password: Password to check
            
        Returns:
            True if the password is common, False otherwise
        """
        # List of common passwords
        common_passwords = [
            "password", "123456", "12345678", "qwerty", "admin",
            "welcome", "password123", "abc123", "letmein", "monkey"
        ]
        
        # Check against common passwords
        if password.lower() in common_passwords:
            return True
        
        # Check for sequential patterns
        if re.search(r"(?:012|123|234|345|456|567|678|789|987|876|765|654|543|432|321|210)", password):
            return True
        
        # Check for repeated patterns
        if re.search(r"(.)\1{2,}", password):  # Same character repeated 3+ times
            return True
        
        # Check for keyboard patterns
        keyboard_patterns = [
            "qwerty", "asdfgh", "zxcvbn", "qazwsx", "qwaszx", "zxcasd"
        ]
        for pattern in keyboard_patterns:
            if pattern in password.lower():
                return True
        
        return False
    
    def generate_secure_password(self) -> str:
        """
        Generate a secure password.
        
        Returns:
            A secure password
        """
        return self.config.authentication.password_policy.generate_password()
    
    def setup_mfa(self, user_id: str) -> Dict[str, Any]:
        """
        Set up multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            MFA setup information
        """
        return self.mfa_manager.setup_mfa(user_id)
    
    def verify_mfa(self, user_id: str, code: str) -> bool:
        """
        Verify a multi-factor authentication code.
        
        Args:
            user_id: User ID
            code: MFA code
            
        Returns:
            True if the code is valid, False otherwise
        """
        return self.mfa_manager.verify_mfa(user_id, code)
    
    def get_security_headers(self) -> Dict[str, str]:
        """
        Get security headers for HTTP responses.
        
        Returns:
            Dictionary of security headers
        """
        web_config = self.config.web_security
        headers = {}
        
        # Content-Security-Policy
        if web_config.content_security_policy_level != "none":
            csp = self._get_content_security_policy()
            headers["Content-Security-Policy"] = csp
        
        # X-Frame-Options
        if web_config.enable_clickjacking_protection:
            headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        if web_config.enable_content_type_options:
            headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer-Policy
        if web_config.enable_referrer_policy:
            headers["Referrer-Policy"] = web_config.referrer_policy
        
        # Strict-Transport-Security (HSTS)
        if web_config.enable_hsts:
            hsts_value = f"max-age={web_config.hsts_max_age}"
            if web_config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if web_config.hsts_preload:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value
        
        # X-XSS-Protection
        if web_config.enable_xss_protection:
            headers["X-XSS-Protection"] = "1; mode=block"
        
        return headers
    
    def _get_content_security_policy(self) -> str:
        """
        Get the Content Security Policy (CSP) value.
        
        Returns:
            CSP value
        """
        web_config = self.config.web_security
        csp_level = web_config.content_security_policy_level
        
        if csp_level == "basic":
            # Basic CSP (prevents XSS but allows some modern features)
            csp = {
                "default-src": "'self'",
                "script-src": "'self' 'unsafe-inline'",
                "style-src": "'self' 'unsafe-inline'",
                "img-src": "'self' data:",
                "font-src": "'self'",
                "connect-src": "'self'",
                "frame-src": "'self'",
                "object-src": "'none'",
                "base-uri": "'self'",
                "form-action": "'self'"
            }
        elif csp_level == "strict":
            # Strict CSP (more secure but may break some features)
            csp = {
                "default-src": "'self'",
                "script-src": "'self'",
                "style-src": "'self'",
                "img-src": "'self'",
                "font-src": "'self'",
                "connect-src": "'self'",
                "frame-src": "'none'",
                "object-src": "'none'",
                "base-uri": "'self'",
                "form-action": "'self'",
                "frame-ancestors": "'none'"
            }
        elif csp_level == "custom":
            # Custom CSP from configuration
            csp = dict(web_config.custom_csp_directives)
        else:
            # No CSP
            return ""
        
        # Convert dictionary to CSP string
        return "; ".join(f"{key} {value}" for key, value in csp.items())
    
    def validate_cors_request(
        self, 
        origin: str, 
        method: str, 
        headers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a CORS request.
        
        Args:
            origin: Origin header
            method: Request method
            headers: Request headers
            
        Returns:
            Dictionary with validation results and CORS headers
        """
        web_config = self.config.web_security
        cors_headers = {}
        
        # Check if origin is allowed
        allowed_origins = web_config.cors_allowed_origins
        is_allowed_origin = False
        
        if "*" in allowed_origins:
            is_allowed_origin = True
            cors_headers["Access-Control-Allow-Origin"] = "*"
        else:
            for allowed_origin in allowed_origins:
                if allowed_origin.endswith("*"):
                    # Handle wildcard origins (e.g., "https://*.example.com")
                    pattern = f"^{allowed_origin.replace('*', '.*')}$"
                    if re.match(pattern, origin):
                        is_allowed_origin = True
                        cors_headers["Access-Control-Allow-Origin"] = origin
                        break
                elif allowed_origin == origin:
                    is_allowed_origin = True
                    cors_headers["Access-Control-Allow-Origin"] = origin
                    break
        
        # Check if method is allowed
        allowed_methods = web_config.cors_allowed_methods
        is_allowed_method = method in allowed_methods or "*" in allowed_methods
        
        # Add CORS headers
        if is_allowed_origin:
            if allowed_methods != ["*"]:
                cors_headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
            else:
                cors_headers["Access-Control-Allow-Methods"] = "*"
            
            if web_config.cors_allowed_headers != ["*"]:
                cors_headers["Access-Control-Allow-Headers"] = ", ".join(web_config.cors_allowed_headers)
            else:
                cors_headers["Access-Control-Allow-Headers"] = "*"
            
            if web_config.cors_expose_headers:
                cors_headers["Access-Control-Expose-Headers"] = ", ".join(web_config.cors_expose_headers)
            
            if web_config.cors_allow_credentials:
                cors_headers["Access-Control-Allow-Credentials"] = "true"
            
            cors_headers["Access-Control-Max-Age"] = str(web_config.cors_max_age)
        
        return {
            "allowed": is_allowed_origin and is_allowed_method,
            "headers": cors_headers
        }
    
    def validate_host(self, host: str) -> bool:
        """
        Validate a host against the allowed hosts list.
        
        Args:
            host: Host to validate
            
        Returns:
            True if the host is allowed, False otherwise
        """
        allowed_hosts = self.config.web_security.allowed_hosts
        
        # Any host allowed
        if "*" in allowed_hosts:
            return True
        
        # Exact match
        if host in allowed_hosts:
            return True
        
        # Wildcard match
        for allowed_host in allowed_hosts:
            if allowed_host.startswith("*.") and host.endswith(allowed_host[1:]):
                return True
        
        return False
    
    def validate_ip_address(self, ip_address: str) -> bool:
        """
        Validate an IP address against allowed/blocked networks.
        
        This is just a placeholder implementation. In a real implementation, you
        would check against allowed/blocked IP ranges from configuration.
        
        Args:
            ip_address: IP address to validate
            
        Returns:
            True if the IP address is allowed, False otherwise
        """
        # For now, allow all IP addresses
        try:
            # Check if it's a valid IP address
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False
    
    def _log_login_event(self, event: SecurityEvent) -> None:
        """Log a login event."""
        # This is a placeholder for additional processing of login events
        pass
    
    def _log_logout_event(self, event: SecurityEvent) -> None:
        """Log a logout event."""
        # This is a placeholder for additional processing of logout events
        pass
    
    def _log_failed_login(self, event: SecurityEvent) -> None:
        """
        Log a failed login attempt.
        
        This method could implement additional logic like rate limiting or
        account lockout after multiple failed attempts.
        """
        # This is a placeholder for additional processing of failed login events
        pass
    
    def _log_password_change(self, event: SecurityEvent) -> None:
        """Log a password change event."""
        # This is a placeholder for additional processing of password change events
        pass
    
    def _log_security_setting_change(self, event: SecurityEvent) -> None:
        """Log a security setting change event."""
        # This is a placeholder for additional processing of security setting change events
        pass