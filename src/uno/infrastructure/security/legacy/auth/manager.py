# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Multi-factor authentication manager for Uno applications.

This module provides MFA management functionality for Uno applications.
"""

import logging
import json
import base64
import secrets
import time
from typing import Dict, List, Optional, Any

from uno.security.config import AuthenticationConfig, MFAType


class MFAManager:
    """
    Multi-factor authentication manager.
    
    This class manages multi-factor authentication for users, including
    setup, verification, and recovery.
    """
    
    def __init__(
        self,
        config: AuthenticationConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the MFA manager.
        
        Args:
            config: Authentication configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.auth.mfa")
        self.provider = self._create_provider()
        self.user_mfa_data: Dict[str, Dict[str, Any]] = {}
    
    def _create_provider(self) -> Any:
        """
        Create an MFA provider based on configuration.
        
        Returns:
            MFA provider
        """
        mfa_type = self.config.mfa_type
        
        if mfa_type == MFAType.TOTP:
            from uno.security.auth.totp import TOTPProvider
            return TOTPProvider()
        elif mfa_type == MFAType.SMS:
            try:
                from uno.security.auth.sms import SMSProvider
                return SMSProvider()
            except ImportError:
                self.logger.warning("SMS provider not available, falling back to TOTP")
                from uno.security.auth.totp import TOTPProvider
                return TOTPProvider()
        elif mfa_type == MFAType.EMAIL:
            try:
                from uno.security.auth.email import EmailProvider
                return EmailProvider()
            except ImportError:
                self.logger.warning("Email provider not available, falling back to TOTP")
                from uno.security.auth.totp import TOTPProvider
                return TOTPProvider()
        elif mfa_type == MFAType.HARDWARE:
            try:
                from uno.security.auth.hardware import HardwareProvider
                return HardwareProvider()
            except ImportError:
                self.logger.warning("Hardware provider not available, falling back to TOTP")
                from uno.security.auth.totp import TOTPProvider
                return TOTPProvider()
        elif mfa_type == MFAType.PUSH:
            try:
                from uno.security.auth.push import PushProvider
                return PushProvider()
            except ImportError:
                self.logger.warning("Push provider not available, falling back to TOTP")
                from uno.security.auth.totp import TOTPProvider
                return TOTPProvider()
        else:
            # Default to TOTP
            from uno.security.auth.totp import TOTPProvider
            return TOTPProvider()
    
    def setup_mfa(self, user_id: str) -> Dict[str, Any]:
        """
        Set up multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            MFA setup information
        """
        if not self.config.enable_mfa:
            return {"enabled": False, "message": "MFA is not enabled"}
        
        try:
            # Set up MFA with the provider
            setup_data = self.provider.setup(user_id)
            
            # Store MFA data
            self.user_mfa_data[user_id] = {
                "provider": self.config.mfa_type.value,
                "data": setup_data,
                "created_at": int(time.time()),
                "enabled": True
            }
            
            # Build response
            result = {
                "user_id": user_id,
                "enabled": True,
                "provider": self.config.mfa_type.value,
                "setup_data": setup_data
            }
            
            # If there's a secret key, also provide recovery codes
            if "secret" in setup_data:
                # Generate recovery codes
                recovery_codes = self._generate_recovery_codes()
                self.user_mfa_data[user_id]["recovery_codes"] = recovery_codes
                result["recovery_codes"] = recovery_codes
            
            return result
        except Exception as e:
            self.logger.error(f"MFA setup error: {str(e)}")
            return {"enabled": False, "error": str(e)}
    
    def verify_mfa(self, user_id: str, code: str) -> bool:
        """
        Verify a multi-factor authentication code.
        
        Args:
            user_id: User ID
            code: MFA code
            
        Returns:
            True if the code is valid, False otherwise
        """
        if not self.config.enable_mfa:
            return True
        
        # Check if this is a recovery code
        if user_id in self.user_mfa_data and "recovery_codes" in self.user_mfa_data[user_id]:
            recovery_codes = self.user_mfa_data[user_id]["recovery_codes"]
            if code in recovery_codes:
                # Valid recovery code - remove it after use
                recovery_codes.remove(code)
                self.user_mfa_data[user_id]["recovery_codes"] = recovery_codes
                return True
        
        try:
            # Check if user has MFA set up
            if user_id not in self.user_mfa_data:
                return False
            
            # Get user's MFA data
            mfa_data = self.user_mfa_data[user_id]
            if not mfa_data.get("enabled", False):
                return True
            
            # Verify with the provider
            return self.provider.verify(user_id, code, mfa_data["data"])
        except Exception as e:
            self.logger.error(f"MFA verification error: {str(e)}")
            return False
    
    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if MFA was disabled, False otherwise
        """
        if user_id in self.user_mfa_data:
            self.user_mfa_data[user_id]["enabled"] = False
            return True
        return False
    
    def reset_mfa(self, user_id: str) -> bool:
        """
        Reset multi-factor authentication for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if MFA was reset, False otherwise
        """
        if user_id in self.user_mfa_data:
            del self.user_mfa_data[user_id]
            return True
        return False
    
    def _generate_recovery_codes(self, count: int = 8, length: int = 10) -> List[str]:
        """
        Generate recovery codes.
        
        Args:
            count: Number of recovery codes to generate
            length: Length of each recovery code
            
        Returns:
            List of recovery codes
        """
        codes = []
        for _ in range(count):
            # Generate a random code
            code = secrets.token_hex(length // 2)
            # Split into groups for readability
            code = "-".join([code[i:i+4] for i in range(0, len(code), 4)])
            codes.append(code)
        
        return codes