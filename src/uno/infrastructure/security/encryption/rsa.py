# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
RSA encryption for Uno applications.

This module provides RSA encryption for Uno applications,
with support for asymmetric encryption.
"""

import os
import base64
import json
import time
from typing import Dict, List, Optional, Union, Any, Tuple

# Import cryptography libraries
try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
except ImportError:
    # Mock implementation for when cryptography is not available
    class MockCrypto:
        """Mock cryptography implementation."""
        
        def encrypt(self, data: str, key: Any) -> bytes:
            """Mock encrypt method."""
            return base64.b64encode(data.encode())
        
        def decrypt(self, data: bytes, key: Any) -> str:
            """Mock decrypt method."""
            return base64.b64decode(data).decode()
    
    mock_crypto = MockCrypto()


class RSAEncryption:
    """
    RSA encryption provider.
    
    This class provides RSA encryption functionality for Uno applications.
    """
    
    def __init__(
        self, 
        key_size: int = 2048,
    ):
        """
        Initialize the RSA encryption provider.
        
        Args:
            key_size: Key size in bits (2048, 3072, or 4096)
        """
        self.key_size = key_size
        self._private_key, self._public_key = self._get_or_generate_keys()
    
    def _get_or_generate_keys(self) -> Tuple[Any, Any]:
        """
        Get or generate RSA key pair.
        
        In a production implementation, this would retrieve keys from a
        secure key management system or environment variable.
        
        Returns:
            Tuple of (private_key, public_key)
        """
        # For now, just generate a random key pair
        # In production, you would use a secure key management system
        try:
            if 'cryptography' in globals():
                # Generate a private key
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=self.key_size,
                    backend=default_backend()
                )
                
                # Get the public key
                public_key = private_key.public_key()
                
                return private_key, public_key
            else:
                # Return mock keys
                return "mock_private_key", "mock_public_key"
        except Exception as e:
            # Log error and re-raise
            raise ValueError(f"Failed to generate RSA key pair: {str(e)}") from e
    
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
                # Encrypt with public key
                ciphertext = self._public_key.encrypt(
                    data.encode(),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                # Create result with metadata
                result = {
                    "v": 1,  # Version
                    "alg": "RSA-OAEP-SHA256",
                    "ct": base64.b64encode(ciphertext).decode(),
                    "ts": int(time.time())
                }
                
                # Encode as JSON and then as base64
                return base64.b64encode(json.dumps(result).encode()).decode()
            else:
                # Use mock implementation otherwise
                return mock_crypto.encrypt(data, self._public_key).decode()
        except Exception as e:
            # Log error and re-raise
            raise ValueError(f"RSA encryption error: {str(e)}") from e
    
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
                # Decode from base64 and parse JSON
                try:
                    decoded = json.loads(base64.b64decode(data).decode())
                except Exception:
                    raise ValueError("Invalid encrypted data format")
                
                # Check version and algorithm
                if decoded.get("v") != 1 or decoded.get("alg") != "RSA-OAEP-SHA256":
                    raise ValueError("Unsupported encryption version or algorithm")
                
                # Extract ciphertext
                ciphertext = base64.b64decode(decoded["ct"])
                
                # Decrypt with private key
                plaintext = self._private_key.decrypt(
                    ciphertext,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                return plaintext.decode()
            else:
                # Use mock implementation otherwise
                return mock_crypto.decrypt(data.encode(), self._private_key)
        except Exception as e:
            # Log error and re-raise
            raise ValueError(f"RSA decryption error: {str(e)}") from e
    
    def get_public_key_pem(self) -> str:
        """
        Get the public key in PEM format.
        
        Returns:
            Public key in PEM format
        """
        try:
            if 'cryptography' in globals():
                # Serialize the public key to PEM format
                pem = self._public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                return pem.decode()
            else:
                # Return a mock public key
                return "-----BEGIN PUBLIC KEY-----\nMock Public Key\n-----END PUBLIC KEY-----"
        except Exception as e:
            # Log error and re-raise
            raise ValueError(f"Failed to get public key PEM: {str(e)}") from e