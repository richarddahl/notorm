# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Password management for Uno applications.

This module provides password management functionality for Uno applications,
including password hashing, verification, and policy enforcement.
"""

import hashlib
import secrets
import string
import re
from typing import Dict, List, Optional, Any, Union

import base64

from uno.security.config import PasswordPolicyLevel


class SecurePasswordPolicy:
    """
    Secure password policy.
    
    This class enforces password policies to ensure that passwords meet
    security requirements.
    """
    
    def __init__(
        self,
        level: Union[str, PasswordPolicyLevel] = PasswordPolicyLevel.STANDARD,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_numbers: bool = True,
        require_special_chars: bool = True,
        password_history: int = 5,
        max_age_days: int = 90,
    ):
        """
        Initialize the password policy.
        
        Args:
            level: Password policy level
            min_length: Minimum password length
            require_uppercase: Require uppercase letters
            require_lowercase: Require lowercase letters
            require_numbers: Require numbers
            require_special_chars: Require special characters
            password_history: Number of previous passwords to remember
            max_age_days: Maximum password age in days
        """
        if isinstance(level, str):
            level = PasswordPolicyLevel(level)
        
        self.level = level
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_special_chars = require_special_chars
        self.password_history = password_history
        self.max_age_days = max_age_days
        
        # Adjust settings based on level
        self._apply_level_settings()
    
    def _apply_level_settings(self) -> None:
        """Apply settings based on the policy level."""
        if self.level == PasswordPolicyLevel.BASIC:
            self.min_length = max(self.min_length, 8)
            self.require_uppercase = True
            self.require_lowercase = True
            self.require_numbers = True
            self.require_special_chars = False
            self.password_history = 3
            self.max_age_days = 180
        elif self.level == PasswordPolicyLevel.STANDARD:
            self.min_length = max(self.min_length, 12)
            self.require_uppercase = True
            self.require_lowercase = True
            self.require_numbers = True
            self.require_special_chars = True
            self.password_history = 5
            self.max_age_days = 90
        elif self.level == PasswordPolicyLevel.STRICT:
            self.min_length = max(self.min_length, 16)
            self.require_uppercase = True
            self.require_lowercase = True
            self.require_numbers = True
            self.require_special_chars = True
            self.password_history = 10
            self.max_age_days = 60
        elif self.level == PasswordPolicyLevel.NIST:
            # NIST SP 800-63B recommendations
            self.min_length = max(self.min_length, 8)
            self.require_uppercase = False
            self.require_lowercase = False
            self.require_numbers = False
            self.require_special_chars = False
            self.password_history = 5
            self.max_age_days = 0  # NIST recommends against mandatory rotation
    
    def validate(self, password: str) -> Dict[str, Any]:
        """
        Validate a password against the policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results and messages
        """
        # Check length
        if len(password) < self.min_length:
            return {
                "valid": False,
                "message": f"Password must be at least {self.min_length} characters long"
            }
        
        # Check complexity requirements
        if self.require_uppercase and not any(c.isupper() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one uppercase letter"
            }
        
        if self.require_lowercase and not any(c.islower() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one lowercase letter"
            }
        
        if self.require_numbers and not any(c.isdigit() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one number"
            }
        
        if self.require_special_chars and not any(not c.isalnum() for c in password):
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
    
    def generate_password(self) -> str:
        """
        Generate a random password that meets the policy requirements.
        
        Returns:
            A secure password
        """
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


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """
    Hash a password using a secure hashing algorithm.
    
    Args:
        password: Password to hash
        salt: Optional salt (will be generated if not provided)
        
    Returns:
        Hashed password
    """
    # Generate salt if not provided
    if salt is None:
        salt = secrets.token_bytes(32)
    
    # Hash the password with the salt using PBKDF2-HMAC-SHA256
    try:
        import hashlib
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            100000,  # 100,000 iterations
            dklen=32
        )
        
        # Combine salt and hash
        storage = salt + hash_bytes
        
        # Convert to base64
        encoded = base64.b64encode(storage).decode()
        
        # Add algorithm identifier
        return f"$pbkdf2-sha256$100000${encoded}"
    except ImportError:
        # Fall back to a simple hash if hashlib's pbkdf2_hmac is not available
        hash_obj = hashlib.sha256()
        hash_obj.update(salt)
        hash_obj.update(password.encode())
        hash_bytes = hash_obj.digest()
        
        # Combine salt and hash
        storage = salt + hash_bytes
        
        # Convert to base64
        encoded = base64.b64encode(storage).decode()
        
        # Add algorithm identifier
        return f"$sha256${encoded}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Password to verify
        hashed_password: Hashed password
        
    Returns:
        True if the password is correct, False otherwise
    """
    # Check the algorithm
    if hashed_password.startswith("$pbkdf2-sha256$"):
        # Parse the hash
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        
        try:
            iterations = int(parts[2])
            storage = base64.b64decode(parts[3])
            
            # Extract salt and hash
            salt = storage[:32]
            stored_hash = storage[32:]
            
            # Compute the hash of the provided password
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt,
                iterations,
                dklen=32
            )
            
            # Compare the hashes
            return computed_hash == stored_hash
        except Exception:
            return False
    elif hashed_password.startswith("$sha256$"):
        # Parse the hash
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        
        try:
            storage = base64.b64decode(parts[2])
            
            # Extract salt and hash
            salt = storage[:32]
            stored_hash = storage[32:]
            
            # Compute the hash of the provided password
            hash_obj = hashlib.sha256()
            hash_obj.update(salt)
            hash_obj.update(password.encode())
            computed_hash = hash_obj.digest()
            
            # Compare the hashes
            return computed_hash == stored_hash
        except Exception:
            return False
    else:
        # Unsupported hash format
        return False