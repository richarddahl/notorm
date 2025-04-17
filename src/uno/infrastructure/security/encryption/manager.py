# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Encryption manager for Uno applications.

This module provides encryption management for Uno applications,
including encryption, decryption, and key management.
"""

import logging
import os
import base64
import json
import time
from typing import Dict, List, Optional, Union, Any, Protocol
from abc import ABC, abstractmethod
from pathlib import Path

from uno.security.config import EncryptionConfig, EncryptionAlgorithm, KeyManagementType


class EncryptionProvider(Protocol):
    """Protocol for encryption providers."""
    
    def encrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Encrypt data."""
        ...
    
    def decrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Decrypt data."""
        ...


class EncryptionManager:
    """
    Encryption manager for Uno applications.
    
    This class coordinates encryption operations, including encryption, decryption,
    and key management.
    """
    
    def __init__(
        self,
        config: EncryptionConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the encryption manager.
        
        Args:
            config: Encryption configuration
            logger: Logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.encryption")
        self.provider = self._create_provider()
        self.key_manager = self._create_key_manager()
        
        # Initialize encryption provider
        self._initialize()
    
    def _create_provider(self) -> EncryptionProvider:
        """
        Create an encryption provider based on configuration.
        
        Returns:
            Encryption provider
        """
        algorithm = self.config.algorithm
        
        if algorithm == EncryptionAlgorithm.AES_GCM:
            from uno.security.encryption.aes import AESEncryption
            return AESEncryption(mode="GCM")
        elif algorithm == EncryptionAlgorithm.AES_CBC:
            from uno.security.encryption.aes import AESEncryption
            return AESEncryption(mode="CBC")
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            try:
                from uno.security.encryption.chacha20 import ChaCha20Poly1305Encryption
                return ChaCha20Poly1305Encryption()
            except ImportError:
                self.logger.warning("ChaCha20-Poly1305 not available, falling back to AES-GCM")
                from uno.security.encryption.aes import AESEncryption
                return AESEncryption(mode="GCM")
        elif algorithm == EncryptionAlgorithm.RSA:
            from uno.security.encryption.rsa import RSAEncryption
            return RSAEncryption()
        else:
            # Default to AES-GCM
            from uno.security.encryption.aes import AESEncryption
            return AESEncryption(mode="GCM")
    
    def _create_key_manager(self) -> Any:
        """
        Create a key manager based on configuration.
        
        Returns:
            Key manager
        """
        key_management = self.config.key_management
        
        if key_management == KeyManagementType.VAULT:
            try:
                from uno.security.encryption.vault_key_manager import VaultKeyManager
                return VaultKeyManager(self.config)
            except ImportError:
                self.logger.warning("Vault key manager not available, falling back to local")
                from uno.security.encryption.local_key_manager import LocalKeyManager
                return LocalKeyManager(self.config)
        elif key_management == KeyManagementType.AWS_KMS:
            try:
                from uno.security.encryption.aws_key_manager import AWSKeyManager
                return AWSKeyManager(self.config)
            except ImportError:
                self.logger.warning("AWS KMS key manager not available, falling back to local")
                from uno.security.encryption.local_key_manager import LocalKeyManager
                return LocalKeyManager(self.config)
        elif key_management == KeyManagementType.AZURE_KEY_VAULT:
            try:
                from uno.security.encryption.azure_key_manager import AzureKeyManager
                return AzureKeyManager(self.config)
            except ImportError:
                self.logger.warning("Azure Key Vault manager not available, falling back to local")
                from uno.security.encryption.local_key_manager import LocalKeyManager
                return LocalKeyManager(self.config)
        elif key_management == KeyManagementType.GCP_KMS:
            try:
                from uno.security.encryption.gcp_key_manager import GCPKeyManager
                return GCPKeyManager(self.config)
            except ImportError:
                self.logger.warning("GCP KMS key manager not available, falling back to local")
                from uno.security.encryption.local_key_manager import LocalKeyManager
                return LocalKeyManager(self.config)
        else:
            # Default to local key management
            from uno.security.encryption.local_key_manager import LocalKeyManager
            return LocalKeyManager(self.config)
    
    def _initialize(self) -> None:
        """Initialize the encryption manager."""
        pass
    
    def encrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            context: Encryption context
            
        Returns:
            Encrypted data
        """
        if not data:
            return data
        
        try:
            return self.provider.encrypt(data, context)
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            # In production, you might want to re-raise the exception or return a specific error value
            raise
    
    def decrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Decrypt data.
        
        Args:
            data: Data to decrypt
            context: Encryption context
            
        Returns:
            Decrypted data
        """
        if not data:
            return data
        
        try:
            return self.provider.decrypt(data, context)
        except Exception as e:
            self.logger.error(f"Decryption error: {str(e)}")
            # In production, you might want to re-raise the exception or return a specific error value
            raise
    
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
        if not value:
            return value
        
        # Check if field should be encrypted
        if field_name in self.config.encrypted_fields:
            context = {"field_name": field_name}
            if entity_type:
                context["entity_type"] = entity_type
            
            return self.encrypt(value, context)
        
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
        if not value:
            return value
        
        # Check if field should be decrypted
        if field_name in self.config.encrypted_fields:
            context = {"field_name": field_name}
            if entity_type:
                context["entity_type"] = entity_type
            
            return self.decrypt(value, context)
        
        return value
    
    def rotate_keys(self) -> bool:
        """
        Rotate encryption keys.
        
        Returns:
            True if key rotation was successful, False otherwise
        """
        try:
            # Check if key rotation is supported
            if hasattr(self.key_manager, 'rotate_keys'):
                return self.key_manager.rotate_keys()
            
            return False
        except Exception as e:
            self.logger.error(f"Key rotation error: {str(e)}")
            return False