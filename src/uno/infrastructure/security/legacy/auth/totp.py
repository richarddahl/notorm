# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
TOTP authentication provider for Uno applications.

This module provides TOTP (Time-based One-Time Password) authentication
for Uno applications.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Dict, List, Optional, Any, Tuple

import base64
import qrcode  # type: ignore
from io import BytesIO


class TOTPProvider:
    """
    TOTP authentication provider.
    
    This class provides TOTP (Time-based One-Time Password) authentication
    functionality, compatible with authenticator apps like Google Authenticator,
    Authy, and Microsoft Authenticator.
    """
    
    def __init__(
        self,
        digits: int = 6,
        interval: int = 30,
        algorithm: str = "SHA1",
        issuer: str = "Uno App",
    ):
        """
        Initialize the TOTP provider.
        
        Args:
            digits: Number of digits in the TOTP code
            interval: TOTP interval in seconds
            algorithm: HMAC algorithm (SHA1, SHA256, or SHA512)
            issuer: Issuer name for the TOTP URI
        """
        self.digits = digits
        self.interval = interval
        self.algorithm = algorithm
        self.issuer = issuer
    
    def setup(self, user_id: str) -> Dict[str, Any]:
        """
        Set up TOTP for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            TOTP setup data
        """
        # Generate a random secret
        secret = base64.b32encode(os.urandom(20)).decode('utf-8').strip('=')
        
        # Create TOTP URI
        uri = self._create_totp_uri(user_id, secret)
        
        # Generate QR code
        qr_code = self._generate_qr_code(uri)
        
        return {
            "secret": secret,
            "uri": uri,
            "qr_code": qr_code,
            "digits": self.digits,
            "interval": self.interval,
            "algorithm": self.algorithm,
        }
    
    def verify(self, user_id: str, code: str, setup_data: Dict[str, Any]) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            user_id: User ID
            code: TOTP code
            setup_data: TOTP setup data
            
        Returns:
            True if the code is valid, False otherwise
        """
        if "secret" not in setup_data:
            return False
        
        secret = setup_data["secret"]
        digits = setup_data.get("digits", self.digits)
        interval = setup_data.get("interval", self.interval)
        algorithm = setup_data.get("algorithm", self.algorithm)
        
        # Get the current time
        current_time = int(time.time())
        
        # Check the current time window and adjacent windows
        for offset in [-1, 0, 1]:
            if self._generate_totp(secret, current_time + offset * interval, digits, interval, algorithm) == code:
                return True
        
        return False
    
    def _create_totp_uri(self, user_id: str, secret: str) -> str:
        """
        Create a TOTP URI.
        
        Args:
            user_id: User ID
            secret: TOTP secret
            
        Returns:
            TOTP URI
        """
        return f"otpauth://totp/{self.issuer}:{user_id}?secret={secret}&issuer={self.issuer}&algorithm={self.algorithm}&digits={self.digits}&period={self.interval}"
    
    def _generate_qr_code(self, uri: str) -> str:
        """
        Generate a QR code for a TOTP URI.
        
        Args:
            uri: TOTP URI
            
        Returns:
            Base64-encoded QR code image
        """
        try:
            # Create a QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)
            
            # Create an image from the QR code
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save the image to a BytesIO object
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            
            # Convert to base64
            return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        except Exception as e:
            # This might fail if qrcode is not installed
            return ""
    
    def _generate_totp(
        self, 
        secret: str, 
        timestamp: int,
        digits: int,
        interval: int,
        algorithm: str,
    ) -> str:
        """
        Generate a TOTP code.
        
        Args:
            secret: TOTP secret
            timestamp: Unix timestamp
            digits: Number of digits in the TOTP code
            interval: TOTP interval in seconds
            algorithm: HMAC algorithm
            
        Returns:
            TOTP code
        """
        # Calculate the TOTP counter value
        counter = int(timestamp // interval)
        
        # Convert counter to bytes (8 bytes, big-endian)
        counter_bytes = counter.to_bytes(8, byteorder='big')
        
        # Decode the base32-encoded secret
        secret_bytes = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8))
        
        # Select the HMAC algorithm
        hash_algorithm = None
        if algorithm == "SHA1":
            hash_algorithm = hashlib.sha1
        elif algorithm == "SHA256":
            hash_algorithm = hashlib.sha256
        elif algorithm == "SHA512":
            hash_algorithm = hashlib.sha512
        else:
            hash_algorithm = hashlib.sha1
        
        # Calculate the HMAC-SHA1 of the counter using the secret as the key
        h = hmac.new(secret_bytes, counter_bytes, hash_algorithm).digest()
        
        # Get the offset (low 4 bits of the last byte)
        offset = h[-1] & 0x0F
        
        # Get a 4-byte slice of the HMAC starting at the offset
        truncated_hash = h[offset:offset+4]
        
        # Convert to an integer and mask the most significant bit
        code_int = int.from_bytes(truncated_hash, byteorder='big') & 0x7FFFFFFF
        
        # Get the specified number of digits
        code_int = code_int % (10 ** digits)
        
        # Format as a zero-padded string
        return f"{code_int:0{digits}d}"