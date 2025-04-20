# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Field-level encryption for Uno applications.

This module provides field-level encryption for sensitive data in Uno models.
"""

import json
import base64
from typing import Dict, List, Optional, Union, Any, Type, TypeVar, Generic, cast
from dataclasses import dataclass, asdict

from uno.security.encryption.manager import EncryptionManager


T = TypeVar("T")


@dataclass
class EncryptedField(Generic[T]):
    """
    Encrypted field wrapper.

    This class wraps a field value to provide automatic encryption and decryption.
    """

    value: T
    field_name: str
    entity_type: str | None = None
    is_encrypted: bool = False
    _encryption_manager: Optional[EncryptionManager] = None

    def __post_init__(self) -> None:
        """Validate after initialization."""
        # Check if value is already an EncryptedField (avoid nesting)
        if isinstance(self.value, EncryptedField):
            self.value = self.value.get_value()

    def set_encryption_manager(self, manager: EncryptionManager) -> None:
        """
        Set the encryption manager.

        Args:
            manager: Encryption manager
        """
        self._encryption_manager = manager

    def encrypt(self) -> "EncryptedField[T]":
        """
        Encrypt the field value.

        Returns:
            Self with encrypted value
        """
        if self.is_encrypted or self._encryption_manager is None:
            return self

        # Convert value to string for encryption
        if isinstance(self.value, (dict, list, tuple)):
            # Serialize complex objects
            serialized = json.dumps(self.value)
            encrypted = self._encryption_manager.encrypt_field(
                self.field_name, serialized, self.entity_type
            )
            # Store a flag indicating this is a JSON value
            self.value = cast(T, f"json:{encrypted}")
        elif self.value is not None:
            # Convert to string and encrypt
            encrypted = self._encryption_manager.encrypt_field(
                self.field_name, str(self.value), self.entity_type
            )
            self.value = cast(T, encrypted)

        self.is_encrypted = True
        return self

    def decrypt(self) -> "EncryptedField[T]":
        """
        Decrypt the field value.

        Returns:
            Self with decrypted value
        """
        if not self.is_encrypted or self._encryption_manager is None:
            return self

        # Decrypt the value
        if self.value is not None:
            if isinstance(self.value, str) and self.value.startswith("json:"):
                # Decrypt and deserialize JSON
                json_str = self.value[5:]  # Remove "json:" prefix
                decrypted = self._encryption_manager.decrypt_field(
                    self.field_name, json_str, self.entity_type
                )
                self.value = cast(T, json.loads(decrypted))
            else:
                # Decrypt and convert back to original type
                decrypted = self._encryption_manager.decrypt_field(
                    self.field_name, str(self.value), self.entity_type
                )
                # Try to convert back to original type (if possible)
                if isinstance(self.value, int) or type(self.value).__name__ == "int":
                    self.value = cast(T, int(decrypted))
                elif (
                    isinstance(self.value, float)
                    or type(self.value).__name__ == "float"
                ):
                    self.value = cast(T, float(decrypted))
                elif (
                    isinstance(self.value, bool) or type(self.value).__name__ == "bool"
                ):
                    self.value = cast(T, decrypted.lower() == "true")
                else:
                    self.value = cast(T, decrypted)

        self.is_encrypted = False
        return self

    def get_value(self) -> T:
        """
        Get the field value.

        Returns:
            Field value (decrypted if necessary)
        """
        if self.is_encrypted:
            return self.decrypt().value
        return self.value

    def __str__(self) -> str:
        """String representation."""
        if self.is_encrypted:
            return "[Encrypted]"
        return str(self.value)

    def __repr__(self) -> str:
        """Representation."""
        if self.is_encrypted:
            return f"EncryptedField(field_name={self.field_name}, is_encrypted=True)"
        return f"EncryptedField(field_name={self.field_name}, value={self.value}, is_encrypted=False)"


class FieldEncryption:
    """
    Field encryption utility.

    This class provides utilities for field-level encryption in Uno models.
    """

    def __init__(self, encryption_manager: EncryptionManager):
        """
        Initialize field encryption.

        Args:
            encryption_manager: Encryption manager
        """
        self.encryption_manager = encryption_manager

    def encrypt_field(
        self, field_name: str, value: Any, entity_type: str | None = None
    ) -> Any:
        """
        Encrypt a field.

        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type

        Returns:
            Encrypted field value
        """
        if value is None:
            return None

        # Check if the field should be encrypted
        if field_name not in self.encryption_manager.config.encrypted_fields:
            return value

        # Wrap in EncryptedField
        field = EncryptedField(
            value=value, field_name=field_name, entity_type=entity_type
        )
        field.set_encryption_manager(self.encryption_manager)

        # Encrypt and return the value
        return field.encrypt().value

    def decrypt_field(
        self, field_name: str, value: Any, entity_type: str | None = None
    ) -> Any:
        """
        Decrypt a field.

        Args:
            field_name: Field name
            value: Field value
            entity_type: Entity type

        Returns:
            Decrypted field value
        """
        if value is None:
            return None

        # Check if the field should be decrypted
        if field_name not in self.encryption_manager.config.encrypted_fields:
            return value

        # Wrap in EncryptedField (with is_encrypted=True)
        field = EncryptedField(
            value=value,
            field_name=field_name,
            entity_type=entity_type,
            is_encrypted=True,
        )
        field.set_encryption_manager(self.encryption_manager)

        # Decrypt and return the value
        return field.decrypt().value

    def encrypt_dict(
        self, data: dict[str, Any], entity_type: str | None = None
    ) -> dict[str, Any]:
        """
        Encrypt a dictionary of field values.

        Args:
            data: Dictionary of field values
            entity_type: Entity type

        Returns:
            Dictionary with encrypted field values
        """
        if not data:
            return data

        result = {}
        for field_name, value in data.items():
            result[field_name] = self.encrypt_field(field_name, value, entity_type)

        return result

    def decrypt_dict(
        self, data: dict[str, Any], entity_type: str | None = None
    ) -> dict[str, Any]:
        """
        Decrypt a dictionary of field values.

        Args:
            data: Dictionary of field values
            entity_type: Entity type

        Returns:
            Dictionary with decrypted field values
        """
        if not data:
            return data

        result = {}
        for field_name, value in data.items():
            result[field_name] = self.decrypt_field(field_name, value, entity_type)

        return result

    def encrypt_model(self, model: Any) -> Any:
        """
        Encrypt sensitive fields in a model.

        Args:
            model: Model instance

        Returns:
            Model with encrypted fields
        """
        if hasattr(model, "to_dict"):
            # Convert to dictionary
            data = model.to_dict()

            # Encrypt the dictionary
            encrypted_data = self.encrypt_dict(data, type(model).__name__)

            # Set the encrypted values back to the model
            for field_name, value in encrypted_data.items():
                if hasattr(model, field_name):
                    setattr(model, field_name, value)

        return model

    def decrypt_model(self, model: Any) -> Any:
        """
        Decrypt sensitive fields in a model.

        Args:
            model: Model instance

        Returns:
            Model with decrypted fields
        """
        if hasattr(model, "to_dict"):
            # Convert to dictionary
            data = model.to_dict()

            # Decrypt the dictionary
            decrypted_data = self.decrypt_dict(data, type(model).__name__)

            # Set the decrypted values back to the model
            for field_name, value in decrypted_data.items():
                if hasattr(model, field_name):
                    setattr(model, field_name, value)

        return model
