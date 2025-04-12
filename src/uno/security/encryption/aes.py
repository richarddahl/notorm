# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
AES encryption for Uno applications.

This module provides AES encryption for Uno applications,
with support for AES-GCM and AES-CBC modes.
"""

import os
import base64
import json
import secrets
import time
from typing import Dict, List, Optional, Union, Any, Tuple, Literal

# Import cryptography libraries
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    # Mock implementation for when cryptography is not available
    class MockCrypto:
        """Mock cryptography implementation."""
        
        def encrypt(self, data: str, key: bytes) -> bytes:
            """Mock encrypt method."""
            return base64.b64encode(data.encode())
        
        def decrypt(self, data: bytes, key: bytes) -> str:
            """Mock decrypt method."""
            return base64.b64decode(data).decode()
    
    mock_crypto = MockCrypto()


class AESEncryption:
    """
    AES encryption provider.
    
    This class provides AES encryption functionality, with support for
    AES-GCM and AES-CBC modes.
    """
    
    def __init__(
        self, 
        mode: Literal["GCM", "CBC"] = "GCM",
        key_size: int = 256,
    ):
        """
        Initialize the AES encryption provider.
        
        Args:
            mode: AES mode (GCM or CBC)
            key_size: Key size in bits (128, 192, or 256)
        """
        self.mode = mode
        self.key_size = key_size
        self._key = self._get_or_generate_key()
    
    def _get_or_generate_key(self) -> bytes:
        """
        Get or generate an encryption key.
        
        In a production implementation, this would retrieve a key from a
        secure key management system or environment variable.
        
        Returns:
            Encryption key
        """
        # For now, just generate a random key
        # In production, you would use a secure key management system
        return secrets.token_bytes(self.key_size // 8)
    
    def encrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            context: Encryption context
            
        Returns:
            Encrypted data
        """
        try:
            # Use the real cryptography library if available
            if 'cryptography' in globals():
                if self.mode == "GCM":
                    return self._encrypt_gcm(data, context)
                else:
                    return self._encrypt_cbc(data, context)
            else:
                # Use mock implementation otherwise
                return mock_crypto.encrypt(data, self._key).decode()
        except Exception as e:
            # Log error and re-raise
            raise ValueError(f"Encryption error: {str(e)}") from e
    
    def decrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Decrypt data.
        
        Args:
            data: Data to decrypt
            context: Encryption context
            
        Returns:
            Decrypted data
        """
        try:
            # Use the real cryptography library if available
            if 'cryptography' in globals():
                if self.mode == "GCM":
                    return self._decrypt_gcm(data, context)
                else:
                    return self._decrypt_cbc(data, context)
            else:
                # Use mock implementation otherwise
                return mock_crypto.decrypt(data.encode(), self._key)
        except Exception as e:
            # Log error and re-raise
            raise ValueError(f"Decryption error: {str(e)}") from e
    
    def _encrypt_gcm(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Encrypt data using AES-GCM.
        
        Args:
            data: Data to encrypt
            context: Encryption context
            
        Returns:
            Encrypted data
        """
        # Generate a random IV (nonce)
        iv = os.urandom(12)
        
        # Create an encryptor
        encryptor = Cipher(
            algorithms.AES(self._key),
            modes.GCM(iv),
            backend=default_backend()
        ).encryptor()
        
        # Set associated data (if provided in context)
        if context:
            aad = json.dumps(context).encode()
            encryptor.authenticate_additional_data(aad)
        
        # Encrypt the data
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        
        # Get the tag
        tag = encryptor.tag
        
        # Combine IV, ciphertext, and tag
        result = {
            "v": 1,  # Version
            "alg": "AES-GCM",
            "iv": base64.b64encode(iv).decode(),
            "ct": base64.b64encode(ciphertext).decode(),
            "tag": base64.b64encode(tag).decode(),
            "ts": int(time.time())
        }
        
        # Encode as JSON and then as base64
        return base64.b64encode(json.dumps(result).encode()).decode()
    
    def _decrypt_gcm(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Decrypt data using AES-GCM.
        
        Args:
            data: Data to decrypt
            context: Encryption context
            
        Returns:
            Decrypted data
        """
        # Decode from base64 and parse JSON
        try:
            decoded = json.loads(base64.b64decode(data).decode())
        except Exception:
            raise ValueError("Invalid encrypted data format")
        
        # Check version and algorithm
        if decoded.get("v") != 1 or decoded.get("alg") != "AES-GCM":
            raise ValueError("Unsupported encryption version or algorithm")
        
        # Extract IV, ciphertext, and tag
        iv = base64.b64decode(decoded["iv"])
        ciphertext = base64.b64decode(decoded["ct"])
        tag = base64.b64decode(decoded["tag"])
        
        # Create a decryptor
        decryptor = Cipher(
            algorithms.AES(self._key),
            modes.GCM(iv, tag),
            backend=default_backend()
        ).decryptor()
        
        # Set associated data (if provided in context)
        if context:
            aad = json.dumps(context).encode()
            decryptor.authenticate_additional_data(aad)
        
        # Decrypt the data
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode()
    
    def _encrypt_cbc(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Encrypt data using AES-CBC.
        
        Args:
            data: Data to encrypt
            context: Encryption context
            
        Returns:
            Encrypted data
        """
        # Generate a random IV
        iv = os.urandom(16)
        
        # Pad the data
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        
        # Create an encryptor
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt the data
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and ciphertext
        result = {
            "v": 1,  # Version
            "alg": "AES-CBC",
            "iv": base64.b64encode(iv).decode(),
            "ct": base64.b64encode(ciphertext).decode(),
            "ts": int(time.time())
        }
        
        # Encode as JSON and then as base64
        return base64.b64encode(json.dumps(result).encode()).decode()
    
    def _decrypt_cbc(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Decrypt data using AES-CBC.
        
        Args:
            data: Data to decrypt
            context: Encryption context
            
        Returns:
            Decrypted data
        """
        # Decode from base64 and parse JSON
        try:
            decoded = json.loads(base64.b64decode(data).decode())
        except Exception:
            raise ValueError("Invalid encrypted data format")
        
        # Check version and algorithm
        if decoded.get("v") != 1 or decoded.get("alg") != "AES-CBC":
            raise ValueError("Unsupported encryption version or algorithm")
        
        # Extract IV and ciphertext
        iv = base64.b64decode(decoded["iv"])
        ciphertext = base64.b64decode(decoded["ct"])
        
        # Create a decryptor
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt the data
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad the data
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode()