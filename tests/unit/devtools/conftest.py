# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Pytest fixtures and helpers for Developer Tools tests.
"""

import pytest
import re
import inspect


# Helper for matching dictionaries with partial information
class PartialDictMatcher:
    """Matcher for dictionaries that contain at least the expected keys/values."""
    
    def __init__(self, expected):
        self.expected = expected
    
    def __eq__(self, actual):
        if not isinstance(actual, dict):
            return False
        
        for key, value in self.expected.items():
            if key not in actual:
                return False
            
            if isinstance(value, PartialDictMatcher):
                if not value == actual[key]:
                    return False
            elif callable(value):
                if not value(actual[key]):
                    return False
            elif actual[key] != value:
                return False
        
        return True
    
    def __repr__(self):
        return f"PartialDictMatcher({self.expected})"


# Helper for matching any string
class AnyStringMatcher:
    """Matcher for any string."""
    
    def __eq__(self, actual):
        return isinstance(actual, str)
    
    def __repr__(self):
        return "AnyString()"


# Helper for matching any number
class AnyNumberMatcher:
    """Matcher for any number."""
    
    def __eq__(self, actual):
        return isinstance(actual, (int, float))
    
    def __repr__(self):
        return "AnyNumber()"


# Helper for matching any float
class AnyFloatMatcher:
    """Matcher for any float."""
    
    def __eq__(self, actual):
        return isinstance(actual, float)
    
    def __repr__(self):
        return "AnyFloat()"


# Helper for matching any integer
class AnyIntMatcher:
    """Matcher for any integer."""
    
    def __eq__(self, actual):
        return isinstance(actual, int)
    
    def __repr__(self):
        return "AnyInt()"


# Helper for matching instance of a class
class InstanceOfMatcher:
    """Matcher for instances of a class."""
    
    def __init__(self, cls):
        self.cls = cls
    
    def __eq__(self, actual):
        return isinstance(actual, self.cls)
    
    def __repr__(self):
        return f"InstanceOf({self.cls.__name__})"


# Register helpers with pytest
@pytest.fixture
def helpers():
    """Fixture providing test helpers."""
    return type(
        "Helpers",
        (),
        {
            "match_partial_dict": lambda expected: PartialDictMatcher(expected),
            "any_string": AnyStringMatcher(),
            "any_number": AnyNumberMatcher(),
            "any_float": AnyFloatMatcher(),
            "any_int": AnyIntMatcher(),
            "instance_of": lambda cls: InstanceOfMatcher(cls),
            "any_instance_of_object": InstanceOfMatcher(object),
        },
    )


# Add the helpers to the pytest namespace
pytest.helpers = type(
    "Helpers",
    (),
    {
        "match_partial_dict": lambda expected: PartialDictMatcher(expected),
        "any_string": AnyStringMatcher(),
        "any_number": AnyNumberMatcher(),
        "any_float": AnyFloatMatcher(),
        "any_int": AnyIntMatcher(),
        "instance_of": lambda cls: InstanceOfMatcher(cls),
        "any_instance_of_object": InstanceOfMatcher(object),
    },
)