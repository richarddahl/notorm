"""Cache key generation module.

This module provides optimized functions for generating and validating cache keys.
"""

import hashlib
import re
import functools
import pickle
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Optional,
    Union,
    Set,
    Callable,
    TypeVar,
    Generic,
)

# Regular expression for valid cache keys
VALID_KEY_REGEX = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_:.-]*$")

# Maximum key length
MAX_KEY_LENGTH = 250

# Common types that can be directly serialized
SIMPLE_TYPES = (type(None), int, float, bool, str, bytes)

# Type that supports key derivation
T = TypeVar("T")


class KeyDerivationFunction(Generic[T]):
    """A function that can derive a cache key from a specific object type."""

    def __init__(self, target_type: type, deriving_func: Callable[[T], str]):
        """Initialize the key derivation function.

        Args:
            target_type: The type of object this function can handle.
            deriving_func: The function that derives a key from the object.
        """
        self.target_type = target_type
        self.deriving_func = deriving_func

    def can_handle(self, obj: Any) -> bool:
        """Check if this function can handle the given object.

        Args:
            obj: The object to check.

        Returns:
            True if this function can handle the object, False otherwise.
        """
        return isinstance(obj, self.target_type)

    def derive_key(self, obj: T) -> str:
        """Derive a key from the object.

        Args:
            obj: The object to derive a key from.

        Returns:
            The derived key string.
        """
        return self.deriving_func(obj)


# Registry of key derivation functions for specialized types
_key_derivation_registry: list[KeyDerivationFunction] = []


def register_key_derivation(target_type: type) -> Callable:
    """Decorator to register a key derivation function for a specific type.

    Args:
        target_type: The type of object this function can handle.

    Returns:
        A decorator function.
    """

    def decorator(func: Callable) -> Callable:
        _key_derivation_registry.append(KeyDerivationFunction(target_type, func))
        return func

    return decorator


@functools.lru_cache(maxsize=1024)
def validate_key(key: str) -> bool:
    """Validate a cache key.

    Args:
        key: The cache key to validate.

    Returns:
        True if the key is valid, False otherwise.
    """
    if not key or not isinstance(key, str):
        return False

    if len(key) > MAX_KEY_LENGTH:
        return False

    return bool(VALID_KEY_REGEX.match(key))


@functools.lru_cache(maxsize=1024)
def get_cache_key(
    key: str, prefix: str = "", use_hash: bool = True, hash_algorithm: str = "md5"
) -> str:
    """Generate a cache key.

    Args:
        key: The base key.
        prefix: Optional prefix for the key.
        use_hash: Whether to hash the key for safety.
        hash_algorithm: The hash algorithm to use if hashing is enabled.

    Returns:
        The generated cache key.
    """
    if not key:
        raise ValueError("Key cannot be empty")

    prefixed_key = f"{prefix}{key}" if prefix else key

    if use_hash:
        # Hash the key to ensure it's valid - use optimized approach
        if hash_algorithm == "md5":
            hashed = hashlib.md5(prefixed_key.encode()).hexdigest()
        elif hash_algorithm == "sha1":
            hashed = hashlib.sha1(prefixed_key.encode()).hexdigest()
        elif hash_algorithm == "sha256":
            hashed = hashlib.sha256(prefixed_key.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")

        # Use the first 32 characters of the hash
        result = hashed[:32]
    else:
        # Ensure the key is valid
        if not validate_key(prefixed_key):
            raise ValueError(f"Invalid cache key: {prefixed_key}")

        result = prefixed_key

    return result


class CompositeKey:
    """A specialized key generator for composite objects with multiple fields.

    This class efficiently creates cache keys from structured data without
    needing to serialize the entire object.
    """

    def __init__(self, prefix: str = "", use_hash: bool = True):
        """Initialize the composite key generator.

        Args:
            prefix: Optional prefix for generated keys.
            use_hash: Whether to hash the generated keys.
        """
        self.prefix = prefix
        self.use_hash = use_hash
        self.parts: list[str] = []

    def add_field(self, name: str, value: Any) -> "CompositeKey":
        """Add a field to the composite key.

        Args:
            name: The field name.
            value: The field value.

        Returns:
            Self (for method chaining).
        """
        serialized = _serialize_arg(value)
        self.parts.append(f"{name}:{serialized}")
        return self

    def add_fields(self, **kwargs) -> "CompositeKey":
        """Add multiple fields from keyword arguments.

        Args:
            **kwargs: Name-value pairs to add to the key.

        Returns:
            Self (for method chaining).
        """
        for name, value in kwargs.items():
            self.add_field(name, value)
        return self

    def build(self) -> str:
        """Build the final cache key.

        Returns:
            The generated cache key.
        """
        key = "|".join(self.parts)
        return get_cache_key(key, self.prefix, self.use_hash)


# Dictionary of common function signatures to avoid recalculation
_function_signature_cache = {}


def get_function_cache_key(
    func: callable,
    args: Tuple,
    kwargs: Dict[str, Any],
    prefix: str = "",
    use_hash: bool = True,
    arg_preprocessors: Optional[Dict[str, callable]] = None,
) -> str:
    """Generate a cache key for a function call.

    This optimized version uses a signature cache and specialized key
    derivation for common types.

    Args:
        func: The function being called.
        args: The positional arguments to the function.
        kwargs: The keyword arguments to the function.
        prefix: Optional prefix for the key.
        use_hash: Whether to hash the key for safety.
        arg_preprocessors: Optional mapping of argument names to preprocessor functions.

    Returns:
        The generated cache key.
    """
    # Fast path for no-argument functions
    if not args and not kwargs:
        func_id = id(
            func
        )  # Use function id as it's faster than computing qualified name
        if func_id in _function_signature_cache:
            func_sig = _function_signature_cache[func_id]
        else:
            module_name = func.__module__
            func_name = func.__qualname__
            func_sig = f"{module_name}.{func_name}"
            _function_signature_cache[func_id] = func_sig

        key = func_sig
        return get_cache_key(key, prefix, use_hash)

    # For functions with arguments, use the composite key builder
    composite = CompositeKey(prefix, use_hash)

    # Add function signature
    func_id = id(func)
    if func_id in _function_signature_cache:
        func_sig = _function_signature_cache[func_id]
    else:
        module_name = func.__module__
        func_name = func.__qualname__
        func_sig = f"{module_name}.{func_name}"
        _function_signature_cache[func_id] = func_sig

    composite.add_field("func", func_sig)

    # Add positional arguments
    for i, arg in enumerate(args):
        # Check if we have a preprocessor for this position
        if arg_preprocessors and str(i) in arg_preprocessors:
            arg = arg_preprocessors[str(i)](arg)
        composite.add_field(f"arg{i}", arg)

    # Add keyword arguments (sorted for consistency)
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        # Check if we have a preprocessor for this parameter
        if arg_preprocessors and k in arg_preprocessors:
            v = arg_preprocessors[k](v)
        composite.add_field(k, v)

    return composite.build()


# Fast serialization lookup table for common primitive types
def _serialize_primitive(value: Any) -> str:
    """Efficiently serialize primitive types.

    Args:
        value: The value to serialize (must be a primitive type).

    Returns:
        The serialized string representation.
    """
    if value is None:
        return "None"
    elif isinstance(value, bool):
        return "True" if value else "False"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        # Use a consistent format for floats to avoid precision issues
        return f"{value:.12g}"
    elif isinstance(value, str):
        # For strings, we can return directly if they're not too long
        if len(value) <= 64:
            return value
        # Otherwise, use a hash to prevent overly long keys
        return f"str:{hashlib.md5(value.encode()).hexdigest()[:16]}"
    elif isinstance(value, bytes):
        # For bytes, always use a hash
        return f"bytes:{hashlib.md5(value).hexdigest()[:16]}"
    # Should never reach here if called correctly
    return str(value)


def _serialize_arg(arg: Any) -> str:
    """Serialize an argument to a string for inclusion in a cache key.

    This optimized version first checks for key derivation functions,
    then special-cases common types for faster serialization.

    Args:
        arg: The argument to serialize.

    Returns:
        The serialized representation of the argument.
    """
    # Check if we have a specialized key derivation function
    for derivation in _key_derivation_registry:
        if derivation.can_handle(arg):
            return derivation.derive_key(arg)

    # Fast path for common primitive types
    if isinstance(arg, SIMPLE_TYPES):
        return _serialize_primitive(arg)

    # Handle collection types
    if isinstance(arg, (list, tuple)):
        # For empty collections, return a simple identifier
        if not arg:
            return "[]" if isinstance(arg, list) else "()"

        # For small collections, serialize all items
        if len(arg) <= 10:
            return f"[{','.join(_serialize_arg(item) for item in arg)}]"

        # For larger collections, use a hash of pickle representation
        # This is faster than recursively serializing large collections
        return f"{type(arg).__name__}_{hashlib.md5(pickle.dumps(arg)).hexdigest()[:16]}"

    if isinstance(arg, dict):
        # For empty dict, return a simple identifier
        if not arg:
            return "{}"

        # For small dictionaries, serialize key-value pairs
        if len(arg) <= 10:
            sorted_items = sorted(arg.items(), key=lambda x: str(x[0]))
            return f"{{{','.join(f'{_serialize_arg(k)}:{_serialize_arg(v)}' for k, v in sorted_items)}}}"

        # For larger dictionaries, use a hash of pickle representation
        return f"dict_{hashlib.md5(pickle.dumps(arg)).hexdigest()[:16]}"

    # For other types, use the type name and hash of repr
    type_name = type(arg).__name__

    # Use pickle-based hashing for consistent results
    try:
        arg_hash = hashlib.md5(pickle.dumps(arg)).hexdigest()[:16]
    except (pickle.PickleError, TypeError):
        # Fallback to repr for unpicklable objects
        arg_hash = hashlib.md5(repr(arg).encode()).hexdigest()[:16]

    return f"{type_name}_{arg_hash}"


# Example key derivation functions
@register_key_derivation(set)
def _derive_key_for_set(s: Set[Any]) -> str:
    """Derive a key for a set by converting to sorted list."""
    if not s:
        return "set_{}"
    sorted_items = sorted(s, key=lambda x: _serialize_arg(x))
    return f"set_[{','.join(_serialize_arg(item) for item in sorted_items)}]"


# Specialized key generation for common objects can be added here
# For example, UUID objects could have a custom serializer
try:
    import uuid

    @register_key_derivation(uuid.UUID)
    def _derive_key_for_uuid(uuid_obj: uuid.UUID) -> str:
        """Derive a key for UUID objects."""
        return f"uuid_{str(uuid_obj)}"

except ImportError:
    pass


# Add more specialized serializers for common types in your domain
# For example, if you frequently use datetime objects:
try:
    from datetime import datetime, date, time

    @register_key_derivation(datetime)
    def _derive_key_for_datetime(dt: datetime) -> str:
        """Derive a key for datetime objects."""
        return f"dt_{dt.isoformat()}"

    @register_key_derivation(date)
    def _derive_key_for_date(d: date) -> str:
        """Derive a key for date objects."""
        return f"date_{d.isoformat()}"

    @register_key_derivation(time)
    def _derive_key_for_time(t: time) -> str:
        """Derive a key for time objects."""
        return f"time_{t.isoformat()}"

except ImportError:
    pass
