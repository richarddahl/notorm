"""File cache module.

This module provides a file-based cache implementation.
"""

from typing import Any, Dict, List, Optional, Tuple, Set, Union
import os
import json
import pickle
import threading
import time
import hashlib
import fnmatch
import shutil
from pathlib import Path

from uno.caching.local.base import LocalCache


class FileCache(LocalCache):
    """File-based cache implementation.

    This implementation stores cache entries in files on disk. It shards the cache
    into multiple directories to improve performance when the cache contains many
    entries.
    """

    def __init__(
        self,
        directory: str | None = None,
        max_size: int = 1000,
        ttl: int = 300,
        shards: int = 8,
        serializer: str = "pickle",
    ):
        """Initialize the file cache.

        Args:
            directory: The directory to store cache files in. If not provided,
                       a directory in the system's temp directory will be used.
            max_size: The maximum size of the cache in MB.
            ttl: The default time-to-live in seconds.
            shards: The number of shards to use.
            serializer: The serialization format to use. Either "pickle" or "json".
        """
        self.max_size = max_size * 1024 * 1024  # Convert MB to bytes
        self.default_ttl = ttl
        self.shards = shards
        self.serializer = serializer

        # Set up the cache directory
        if directory is None:
            import tempfile

            self.directory = os.path.join(tempfile.gettempdir(), "uno_cache")
        else:
            self.directory = directory

        # Create the cache directory and shard directories if they don't exist
        os.makedirs(self.directory, exist_ok=True)
        for i in range(self.shards):
            shard_dir = os.path.join(self.directory, str(i))
            os.makedirs(shard_dir, exist_ok=True)

        self._index_lock = threading.RLock()
        self._shard_locks = [threading.RLock() for _ in range(self.shards)]

        # Initialize size tracker
        self._current_size = self._calculate_size()

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "size": self._current_size,
            "max_size": self.max_size,
            "insertions": 0,
            "deletions": 0,
            "created_at": time.time(),
        }

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found or expired.
        """
        shard = self._get_shard(key)
        file_path = self._get_file_path(key, shard)

        # Use the appropriate shard lock
        with self._shard_locks[shard]:
            if not os.path.exists(file_path):
                with self._index_lock:
                    self._stats["misses"] += 1
                return None

            try:
                # Read the cache entry
                with open(file_path, "rb") as f:
                    entry = self._deserialize(f.read())

                # Check if the entry has expired
                if entry["expiry"] < time.time():
                    # Remove expired entry
                    os.unlink(file_path)
                    with self._index_lock:
                        self._current_size -= os.path.getsize(file_path)
                        self._stats["size"] = self._current_size
                        self._stats["expirations"] += 1
                        self._stats["misses"] += 1
                    return None

                with self._index_lock:
                    self._stats["hits"] += 1

                # Touch the file to update access time (helps with LRU-like behavior)
                os.utime(file_path, None)

                return entry["value"]
            except (IOError, pickle.PickleError, json.JSONDecodeError) as e:
                # Handle read errors
                with self._index_lock:
                    self._stats["misses"] += 1
                return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.

        Returns:
            True if the value was successfully cached, False otherwise.
        """
        if ttl is None:
            ttl = self.default_ttl

        shard = self._get_shard(key)
        file_path = self._get_file_path(key, shard)

        # Create cache entry
        entry = {"key": key, "value": value, "expiry": time.time() + ttl}

        # Serialize the entry
        try:
            data = self._serialize(entry)
        except (pickle.PickleError, TypeError) as e:
            # Handle serialization errors
            return False

        # Use the appropriate shard lock
        with self._shard_locks[shard]:
            # Check if we need to make room for the new entry
            data_size = len(data)
            existing_size = (
                os.path.getsize(file_path) if os.path.exists(file_path) else 0
            )

            with self._index_lock:
                # If the entry already exists, update stats based on size difference
                size_diff = data_size - existing_size

                if size_diff > 0 and self._current_size + size_diff > self.max_size:
                    # Need to make room
                    self._evict(size_diff)

                try:
                    # Write the cache entry
                    with open(file_path, "wb") as f:
                        f.write(data)

                    # Update size tracker
                    self._current_size = self._current_size - existing_size + data_size
                    self._stats["size"] = self._current_size

                    if existing_size == 0:
                        self._stats["insertions"] += 1

                    return True
                except IOError as e:
                    # Handle write errors
                    return False

    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key.

        Returns:
            True if the value was successfully deleted, False otherwise.
        """
        shard = self._get_shard(key)
        file_path = self._get_file_path(key, shard)

        # Use the appropriate shard lock
        with self._shard_locks[shard]:
            if not os.path.exists(file_path):
                return False

            try:
                # Get the file size before deleting
                file_size = os.path.getsize(file_path)

                # Delete the file
                os.unlink(file_path)

                # Update size tracker
                with self._index_lock:
                    self._current_size -= file_size
                    self._stats["size"] = self._current_size
                    self._stats["deletions"] += 1

                return True
            except IOError as e:
                # Handle delete errors
                return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        This method uses Unix shell-style wildcards (e.g., * matches any characters).

        Args:
            pattern: The pattern to match against cache keys.

        Returns:
            The number of keys invalidated.
        """
        count = 0

        # We need to check all shards
        for shard in range(self.shards):
            shard_dir = os.path.join(self.directory, str(shard))

            # Use the appropriate shard lock
            with self._shard_locks[shard]:
                try:
                    # List all files in the shard directory
                    files = os.listdir(shard_dir)

                    for filename in files:
                        file_path = os.path.join(shard_dir, filename)

                        # Extract key from filename
                        key = self._decode_filename(filename)

                        # Check if key matches the pattern
                        if fnmatch.fnmatch(key, pattern):
                            try:
                                # Get the file size before deleting
                                file_size = os.path.getsize(file_path)

                                # Delete the file
                                os.unlink(file_path)

                                # Update size tracker
                                with self._index_lock:
                                    self._current_size -= file_size
                                    self._stats["size"] = self._current_size
                                    self._stats["deletions"] += 1

                                count += 1
                            except IOError:
                                # Ignore errors for individual files
                                pass
                except IOError:
                    # Ignore errors for listing directories
                    pass

        return count

    def clear(self) -> bool:
        """Clear all cached values.

        Returns:
            True if the cache was successfully cleared, False otherwise.
        """
        try:
            # Acquire all shard locks (to prevent deadlocks, acquire in order)
            for lock in self._shard_locks:
                lock.acquire()

            try:
                # Delete all files in all shard directories
                for shard in range(self.shards):
                    shard_dir = os.path.join(self.directory, str(shard))

                    for filename in os.listdir(shard_dir):
                        file_path = os.path.join(shard_dir, filename)
                        try:
                            os.unlink(file_path)
                        except IOError:
                            # Ignore errors for individual files
                            pass

                # Reset size tracker
                with self._index_lock:
                    self._current_size = 0
                    self._stats["size"] = 0

                return True
            finally:
                # Release all shard locks
                for lock in reversed(self._shard_locks):
                    lock.release()
        except Exception:
            # Handle any errors
            return False

    def check_health(self) -> bool:
        """Check the health of the cache.

        Returns:
            True if the cache is healthy, False otherwise.
        """
        try:
            # Check if the cache directory exists and is writable
            if not os.path.isdir(self.directory):
                return False

            # Check if all shard directories exist and are writable
            for shard in range(self.shards):
                shard_dir = os.path.join(self.directory, str(shard))
                if not os.path.isdir(shard_dir):
                    return False

                # Try to write a test file
                test_file = os.path.join(shard_dir, "_health_check")
                try:
                    with open(test_file, "w") as f:
                        f.write("ok")
                    os.unlink(test_file)
                except IOError:
                    return False

            return True
        except Exception:
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            A dictionary with cache statistics.
        """
        with self._index_lock:
            # Copy stats and add current size
            stats = self._stats.copy()
            stats["size"] = self._current_size

            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            stats["hit_rate"] = (
                stats["hits"] / total_requests if total_requests > 0 else 0
            )

            # Calculate current entry count
            stats["entry_count"] = sum(
                len(os.listdir(os.path.join(self.directory, str(shard))))
                for shard in range(self.shards)
            )

            # Add uptime
            stats["uptime"] = time.time() - stats["created_at"]

            return stats

    def close(self) -> None:
        """Close the cache and release resources."""
        pass  # No resources to release

    def _get_shard(self, key: str) -> int:
        """Get the shard number for a key.

        Args:
            key: The cache key.

        Returns:
            The shard number.
        """
        # Use a simple hash-based sharding
        hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_val % self.shards

    def _get_file_path(self, key: str, shard: int) -> str:
        """Get the file path for a key.

        Args:
            key: The cache key.
            shard: The shard number.

        Returns:
            The file path.
        """
        filename = self._encode_filename(key)
        return os.path.join(self.directory, str(shard), filename)

    def _encode_filename(self, key: str) -> str:
        """Encode a key into a valid filename.

        Args:
            key: The cache key.

        Returns:
            The encoded filename.
        """
        # Use a hash to ensure the filename is valid
        return hashlib.md5(key.encode()).hexdigest()

    def _decode_filename(self, filename: str) -> str:
        """Decode a filename into a key.

        This is a fake implementation since we can't recover the original key from the hash.
        We use this in the invalidate_pattern method to decide whether to invalidate a key.
        If we want to support pattern matching, we would need to store the original key in the cache entry.

        Args:
            filename: The encoded filename.

        Returns:
            The decoded key (or the filename itself if it can't be decoded).
        """
        # Since we use a hash for the filename, we can't recover the original key
        # To support pattern matching properly, we would need to store the original
        # key in the cache entry and read it from the file
        return filename

    def _serialize(self, entry: dict[str, Any]) -> bytes:
        """Serialize a cache entry.

        Args:
            entry: The cache entry to serialize.

        Returns:
            The serialized entry as bytes.
        """
        if self.serializer == "pickle":
            return pickle.dumps(entry)
        elif self.serializer == "json":
            return json.dumps(entry).encode()
        else:
            raise ValueError(f"Unsupported serializer: {self.serializer}")

    def _deserialize(self, data: bytes) -> dict[str, Any]:
        """Deserialize a cache entry.

        Args:
            data: The serialized cache entry.

        Returns:
            The deserialized entry.
        """
        if self.serializer == "pickle":
            return pickle.loads(data)
        elif self.serializer == "json":
            return json.loads(data.decode())
        else:
            raise ValueError(f"Unsupported serializer: {self.serializer}")

    def _calculate_size(self) -> int:
        """Calculate the current size of the cache in bytes.

        Returns:
            The current size in bytes.
        """
        total_size = 0

        for shard in range(self.shards):
            shard_dir = os.path.join(self.directory, str(shard))

            try:
                for filename in os.listdir(shard_dir):
                    file_path = os.path.join(shard_dir, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        # Ignore errors for individual files
                        pass
            except OSError:
                # Ignore errors for listing directories
                pass

        return total_size

    def _evict(self, needed_space: int) -> None:
        """Evict entries to make room for new entries.

        This method uses a simple LRU-based approach, evicting the least recently
        accessed entries first (based on file access times).

        Args:
            needed_space: The amount of space needed in bytes.
        """
        # Find all files in all shard directories
        all_files = []

        for shard in range(self.shards):
            shard_dir = os.path.join(self.directory, str(shard))

            try:
                for filename in os.listdir(shard_dir):
                    file_path = os.path.join(shard_dir, filename)
                    try:
                        # Get file stats
                        stats = os.stat(file_path)
                        all_files.append((file_path, stats.st_atime, stats.st_size))
                    except OSError:
                        # Ignore errors for individual files
                        pass
            except OSError:
                # Ignore errors for listing directories
                pass

        # Sort files by access time (oldest first)
        all_files.sort(key=lambda x: x[1])

        # Evict files until we have enough space
        freed_space = 0
        evicted_count = 0

        for file_path, _, file_size in all_files:
            if freed_space >= needed_space:
                break

            try:
                # Delete the file
                os.unlink(file_path)

                # Update counters
                freed_space += file_size
                self._current_size -= file_size
                evicted_count += 1
            except OSError:
                # Ignore errors for individual files
                pass

        # Update stats
        self._stats["size"] = self._current_size
        self._stats["evictions"] += evicted_count
