"""Pattern-based cache invalidation module.

This module provides a pattern-based invalidation strategy.
"""

from typing import Any, Dict, List, Optional, Set, Union
import re
import fnmatch
import hashlib
import threading


class PatternBasedInvalidation:
    """Pattern-based cache invalidation strategy.

    This strategy invalidates cache entries based on patterns associated with
    entity types.
    """

    def __init__(
        self,
        patterns: Optional[dict[str, list[str]]] = None,
        consistent_hashing: bool = False,
    ):
        """Initialize the pattern-based invalidation strategy.

        Args:
            patterns: Optional mapping of entity types to patterns to invalidate.
                     For example: {"user": ["user:{id}", "profile:{id}"]}
            consistent_hashing: Whether to use consistent hashing for shard invalidation.
        """
        self.patterns = patterns or {}
        self.consistent_hashing = consistent_hashing
        self._lock = threading.RLock()

        # Map of entity types to sets of shard keys for consistent hashing
        self._shard_keys: dict[str, Set[str]] = {}

        # Initialize shard keys
        if consistent_hashing:
            for entity_type, entity_patterns in self.patterns.items():
                self._shard_keys[entity_type] = set(entity_patterns)

    def invalidate(self, key: str, value: Any) -> bool:
        """Determine if a value should be invalidated based on patterns.

        This method always returns False because pattern-based invalidation is driven
        by explicit invalidation requests, not by cache lookups.

        Args:
            key: The cache key.
            value: The cached value.

        Returns:
            True if the value should be invalidated, False otherwise.
        """
        # Pattern-based invalidation is driven by explicit invalidation requests, not by cache lookups
        return False

    def invalidate_entity(self, entity_type: str, entity_id: str) -> list[str]:
        """Invalidate cache entries for a specific entity.

        Args:
            entity_type: The type of the entity.
            entity_id: The ID of the entity.

        Returns:
            A list of patterns to invalidate.
        """
        with self._lock:
            # Check if we have patterns for this entity type
            if entity_type not in self.patterns:
                return []

            # Get patterns for this entity type
            entity_patterns = self.patterns[entity_type]

            # Format patterns with the entity ID
            formatted_patterns = []
            for pattern in entity_patterns:
                try:
                    # Try to format the pattern with the entity ID
                    if "{id}" in pattern:
                        formatted_pattern = pattern.replace("{id}", str(entity_id))
                    else:
                        # If no {id} placeholder, try to format using kwargs
                        formatted_pattern = pattern.format(id=entity_id)

                    formatted_patterns.append(formatted_pattern)
                except KeyError:
                    # If formatting fails, still include the original pattern
                    formatted_patterns.append(pattern)

            return formatted_patterns

    def match_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a pattern.

        Args:
            key: The cache key.
            pattern: The pattern to match against.

        Returns:
            True if the key matches the pattern, False otherwise.
        """
        # Handle wildcards using fnmatch
        return fnmatch.fnmatch(key, pattern)

    def register_pattern(self, entity_type: str, pattern: str) -> None:
        """Register a pattern for a specific entity type.

        Args:
            entity_type: The type of the entity.
            pattern: The pattern to invalidate when this entity type is updated.
        """
        with self._lock:
            if entity_type not in self.patterns:
                self.patterns[entity_type] = []

            # Add the pattern if it's not already registered
            if pattern not in self.patterns[entity_type]:
                self.patterns[entity_type].append(pattern)

                # Update shard keys if using consistent hashing
                if self.consistent_hashing and entity_type in self._shard_keys:
                    self._shard_keys[entity_type].add(pattern)

    def unregister_pattern(self, entity_type: str, pattern: str | None = None) -> None:
        """Unregister a pattern.

        Args:
            entity_type: The type of the entity.
            pattern: Optional pattern to unregister. If not provided, all patterns
                    for this entity type will be unregistered.
        """
        with self._lock:
            if entity_type not in self.patterns:
                return

            if pattern is None:
                # Unregister all patterns for this entity type
                del self.patterns[entity_type]

                # Update shard keys if using consistent hashing
                if self.consistent_hashing and entity_type in self._shard_keys:
                    del self._shard_keys[entity_type]
            else:
                # Unregister a specific pattern
                if pattern in self.patterns[entity_type]:
                    self.patterns[entity_type].remove(pattern)

                    # Update shard keys if using consistent hashing
                    if self.consistent_hashing and entity_type in self._shard_keys:
                        self._shard_keys[entity_type].discard(pattern)

                # If no patterns left, remove the entity type
                if not self.patterns[entity_type]:
                    del self.patterns[entity_type]

                    # Update shard keys if using consistent hashing
                    if self.consistent_hashing and entity_type in self._shard_keys:
                        del self._shard_keys[entity_type]

    def get_shard_key(self, entity_type: str, entity_id: str) -> str | None:
        """Get the shard key for a specific entity.

        This method is used for consistent hashing to ensure that the same entity
        is always mapped to the same shard.

        Args:
            entity_type: The type of the entity.
            entity_id: The ID of the entity.

        Returns:
            The shard key or None if consistent hashing is not enabled or if the
            entity type is not registered.
        """
        if not self.consistent_hashing:
            return None

        with self._lock:
            if entity_type not in self._shard_keys or not self._shard_keys[entity_type]:
                return None

            # Use the entity ID to select a shard key consistently
            shard_keys = sorted(
                list(self._shard_keys[entity_type])
            )  # Sort for stability
            hash_val = int(hashlib.md5(str(entity_id).encode()).hexdigest(), 16)
            index = hash_val % len(shard_keys)

            return shard_keys[index]
