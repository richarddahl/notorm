# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Local key manager for Uno applications.

This module provides a local key manager for Uno applications.
"""

import os
import json
import base64
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from uno.security.config import EncryptionConfig


class LocalKeyManager:
    """
    Local key manager.

    This class manages encryption keys locally, typically for development
    or testing environments.
    """

    def __init__(self, config: EncryptionConfig):
        """
        Initialize the local key manager.

        Args:
            config: Encryption configuration
        """
        self.config = config
        self.keys: dict[str, dict[str, Any]] = {}
        self.current_key_id: str | None = None

        # Key storage path (default to user's home directory)
        self.key_path = Path.home() / ".uno" / "keys"

        # Create the directory if it doesn't exist
        os.makedirs(self.key_path, exist_ok=True)

        # Load keys
        self._load_keys()

    def _load_keys(self) -> None:
        """Load keys from storage."""
        key_file = self.key_path / "keys.json"

        if key_file.exists():
            try:
                with open(key_file, "r") as f:
                    key_data = json.load(f)
                    self.keys = key_data.get("keys", {})
                    self.current_key_id = key_data.get("current_key_id")
            except Exception as e:
                # Failed to load keys
                pass

        # If no keys were loaded, generate a new one
        if not self.keys or self.current_key_id is None:
            self._generate_key()
            self._save_keys()

    def _save_keys(self) -> None:
        """Save keys to storage."""
        key_file = self.key_path / "keys.json"

        # Create a data structure to save
        key_data = {"keys": self.keys, "current_key_id": self.current_key_id}

        try:
            with open(key_file, "w") as f:
                json.dump(key_data, f)
        except Exception as e:
            # Failed to save keys
            pass

    def _generate_key(self) -> str:
        """
        Generate a new encryption key.

        Returns:
            Key ID
        """
        # Generate a random key ID
        key_id = f"key-{int(time.time())}"

        # Generate a random key
        key_bytes = os.urandom(32)  # 256 bits
        key_b64 = base64.b64encode(key_bytes).decode()

        # Store the key
        self.keys[key_id] = {
            "key": key_b64,
            "created_at": int(time.time()),
            "algorithm": self.config.algorithm.value,
        }

        # Set as current key
        self.current_key_id = key_id

        return key_id

    def get_current_key(self) -> dict[str, Any]:
        """
        Get the current encryption key.

        Returns:
            Current encryption key
        """
        if self.current_key_id is None or self.current_key_id not in self.keys:
            self._generate_key()
            self._save_keys()

        return self.keys[self.current_key_id]

    def get_key(self, key_id: str) -> dict[str, Any] | None:
        """
        Get a specific encryption key.

        Args:
            key_id: Key ID

        Returns:
            Encryption key or None if not found
        """
        return self.keys.get(key_id)

    def rotate_keys(self) -> bool:
        """
        Rotate encryption keys.

        Returns:
            True if key rotation was successful, False otherwise
        """
        try:
            # Generate a new key
            self._generate_key()

            # Save keys
            self._save_keys()

            return True
        except Exception as e:
            # Failed to rotate keys
            return False
