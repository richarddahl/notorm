"""Cache key generation module.

This module provides functions for generating and validating cache keys.
"""

import hashlib
import re
from typing import Any, Dict, List, Tuple, Optional, Union

# Regular expression for valid cache keys
VALID_KEY_REGEX = re.compile(r'^[a-zA-Z0-9_][a-zA-Z0-9_:.-]*$')

# Maximum key length
MAX_KEY_LENGTH = 250


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


def get_cache_key(key: str, prefix: str = "", use_hash: bool = True, 
                  hash_algorithm: str = "md5") -> str:
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
        # Hash the key to ensure it's valid
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


def get_function_cache_key(func: callable, args: Tuple, kwargs: Dict[str, Any], 
                          prefix: str = "", use_hash: bool = True,
                          arg_preprocessors: Optional[Dict[str, callable]] = None) -> str:
    """Generate a cache key for a function call.
    
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
    module_name = func.__module__
    func_name = func.__qualname__
    
    # Start with the function's identity
    key_parts = [f"{module_name}.{func_name}"]
    
    # Add positional arguments
    for i, arg in enumerate(args):
        # Check if we have a preprocessor for this position
        if arg_preprocessors and str(i) in arg_preprocessors:
            arg = arg_preprocessors[str(i)](arg)
        key_parts.append(f"arg{i}:{_serialize_arg(arg)}")
    
    # Add keyword arguments (sorted for consistency)
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        # Check if we have a preprocessor for this parameter
        if arg_preprocessors and k in arg_preprocessors:
            v = arg_preprocessors[k](v)
        key_parts.append(f"{k}:{_serialize_arg(v)}")
    
    # Join the parts with a delimiter
    key = "|".join(key_parts)
    
    # Generate the final key
    return get_cache_key(key, prefix, use_hash)


def _serialize_arg(arg: Any) -> str:
    """Serialize an argument to a string for inclusion in a cache key.
    
    Args:
        arg: The argument to serialize.
        
    Returns:
        The serialized representation of the argument.
    """
    if arg is None:
        return "None"
    
    if isinstance(arg, (int, float, bool, str)):
        return str(arg)
    
    if isinstance(arg, (list, tuple)):
        return f"[{','.join(_serialize_arg(item) for item in arg)}]"
    
    if isinstance(arg, dict):
        sorted_items = sorted(arg.items(), key=lambda x: str(x[0]))
        return f"{{{','.join(f'{_serialize_arg(k)}:{_serialize_arg(v)}' for k, v in sorted_items)}}}"
    
    # For other types, use the type name and hash of repr
    type_name = type(arg).__name__
    arg_hash = hashlib.md5(repr(arg).encode()).hexdigest()[:8]
    return f"{type_name}_{arg_hash}"
