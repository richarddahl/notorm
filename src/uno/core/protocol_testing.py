"""
Protocol testing framework for the UNO framework.

This module provides utilities for testing protocol implementations,
particularly useful for unit tests and validation scripts.
"""

import inspect
import unittest
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    Type,
    TypeVar,
    Union,
)
from unittest.mock import MagicMock

from uno.core.protocol_validator import (
    ProtocolValidationError,
    find_protocol_implementations,
    validate_implementation,
    validate_protocol,
    _get_protocol_attributes,
)

T = TypeVar("T")
P = TypeVar("P", bound=Protocol)


class ProtocolMock(Generic[P]):
    """
    A utility class for creating mock implementations of protocols for testing.

    This class creates a mock implementation of a protocol that passes static
    type checking and can be configured with specific behaviors for testing.

    Example:
        repo_mock = ProtocolMock[Repository[User, UUID]]()
        repo_mock.configure_method("get", return_value=User(id=uuid4(), name="Test"))
        service = UserService(repo_mock.create())
    """

    def __init__(self, protocol_type: Optional[Type[P]] = None):
        """
        Initialize a protocol mock.

        Args:
            protocol_type: The protocol type to mock. If not provided, it will be inferred
                          from the type annotation.
        """
        self.protocol_type = protocol_type or self._infer_protocol_type()
        if (
            not hasattr(self.protocol_type, "_is_protocol")
            or not self.protocol_type._is_protocol
        ):
            raise TypeError(
                f"The provided type '{self.protocol_type.__name__}' is not a Protocol."
            )

        self.mock = MagicMock()
        self._configure_protocol_methods()

    def _infer_protocol_type(self) -> Type[P]:
        """
        Infer the protocol type from the type annotation.

        Returns:
            The inferred protocol type.

        Raises:
            TypeError: If the protocol type cannot be inferred.
        """
        # Try to extract the protocol type from the generic type
        if not hasattr(self, "__orig_class__"):
            raise TypeError(
                "Protocol type not provided and couldn't be inferred. "
                "Either provide protocol_type parameter or use ProtocolMock[YourProtocol]."
            )

        # Extract the first type argument from __orig_class__
        # e.g., for ProtocolMock[Repository[User, UUID]], return Repository[User, UUID]
        orig_class = getattr(self, "__orig_class__")
        if not hasattr(orig_class, "__args__") or not orig_class.__args__:
            raise TypeError(
                "Invalid generic type parameters. Usage: ProtocolMock[YourProtocol]"
            )

        protocol_type = orig_class.__args__[0]
        return protocol_type

    def _configure_protocol_methods(self) -> None:
        """Configure the mock with methods defined in the protocol."""
        protocol_attrs = _get_protocol_attributes(self.protocol_type)

        for attr_name in protocol_attrs:
            # Skip dunder methods except for specific ones
            if attr_name.startswith("__") and attr_name.endswith("__"):
                if attr_name not in (
                    "__aenter__",
                    "__aexit__",
                    "__enter__",
                    "__exit__",
                ):
                    continue

            # Get the attribute from the protocol
            if hasattr(self.protocol_type, attr_name):
                attr = getattr(self.protocol_type, attr_name)

                # Configure methods
                if inspect.isfunction(attr) or inspect.ismethod(attr):
                    # For methods, create a mock method that returns MagicMock
                    setattr(self.mock, attr_name, MagicMock())
                # Configure properties
                elif isinstance(attr, property):
                    # For properties, set up both getter and setter
                    prop_mock = MagicMock()
                    setattr(self.mock, attr_name, prop_mock)
            else:
                # For attributes, just create a mock attribute
                setattr(self.mock, attr_name, MagicMock())

    def configure_method(self, method_name: str, **kwargs) -> "ProtocolMock[P]":
        """
        Configure a method on the mock.

        Args:
            method_name: The name of the method to configure.
            **kwargs: Arguments to pass to MagicMock.configure_mock().

        Returns:
            Self for method chaining.

        Raises:
            AttributeError: If the method doesn't exist in the protocol.
        """
        if not hasattr(self.mock, method_name):
            raise AttributeError(
                f"Protocol '{self.protocol_type.__name__}' doesn't have method '{method_name}'"
            )

        method_mock = getattr(self.mock, method_name)
        method_mock.configure_mock(**kwargs)
        return self

    def configure_property(self, property_name: str, value: Any) -> "ProtocolMock[P]":
        """
        Configure a property on the mock.

        Args:
            property_name: The name of the property to configure.
            value: The value to set for the property.

        Returns:
            Self for method chaining.

        Raises:
            AttributeError: If the property doesn't exist in the protocol.
        """
        if not hasattr(self.mock, property_name):
            raise AttributeError(
                f"Protocol '{self.protocol_type.__name__}' doesn't have property '{property_name}'"
            )

        setattr(self.mock, property_name, value)
        return self

    def create(self) -> P:
        """
        Create the mock implementation of the protocol.

        Returns:
            A mock object that implements the protocol.
        """
        return self.mock


class ProtocolTestCase(unittest.TestCase, Generic[P]):
    """
    Base test case for testing protocol implementations.

    This class provides utilities for testing that classes correctly implement
    protocols, with additional functionality for testing protocol behavior.

    Example:
        class TestUserRepository(ProtocolTestCase[Repository[User, UUID]]):
            protocol_type = Repository[User, UUID]
            implementation_type = PostgresUserRepository

            def test_get_returns_user(self):
                # Test the implementation
                repo = self.create_implementation()
                # ...
    """

    protocol_type: Type[P] = NotImplemented
    implementation_type: Type = NotImplemented

    def setUp(self) -> None:
        """Set up the test case."""
        super().setUp()
        if self.protocol_type is NotImplemented:
            raise TypeError(
                "protocol_type must be defined in the test case. "
                "Usage: protocol_type = YourProtocol"
            )

        if (
            not hasattr(self.protocol_type, "_is_protocol")
            or not self.protocol_type._is_protocol
        ):
            raise TypeError(
                f"The provided type '{self.protocol_type.__name__}' is not a Protocol."
            )

    def validate_implementation_static(
        self, implementation_type: Optional[Type] = None
    ) -> None:
        """
        Validate that the implementation correctly implements the protocol statically.

        Args:
            implementation_type: The implementation type to validate. Defaults to self.implementation_type.

        Raises:
            ProtocolValidationError: If the implementation doesn't properly implement the protocol.
        """
        implementation_type = implementation_type or self.implementation_type
        if implementation_type is NotImplemented:
            raise TypeError(
                "implementation_type must be defined in the test case. "
                "Usage: implementation_type = YourImplementation"
            )

        validate_protocol(implementation_type, self.protocol_type)

    def validate_implementation_runtime(self, instance: Any) -> None:
        """
        Validate that an instance correctly implements the protocol at runtime.

        Args:
            instance: The instance to validate.

        Raises:
            ProtocolValidationError: If the instance doesn't properly implement the protocol.
        """
        validate_implementation(instance, self.protocol_type)

    def create_implementation(self, *args, **kwargs) -> P:
        """
        Create an instance of the implementation.

        Args:
            *args: Arguments to pass to the implementation constructor.
            **kwargs: Keyword arguments to pass to the implementation constructor.

        Returns:
            An instance of the implementation.
        """
        if self.implementation_type is NotImplemented:
            raise TypeError(
                "implementation_type must be defined in the test case. "
                "Usage: implementation_type = YourImplementation"
            )

        instance = self.implementation_type(*args, **kwargs)
        self.validate_implementation_runtime(instance)
        return instance

    def create_mock(self) -> ProtocolMock[P]:
        """
        Create a mock implementation of the protocol.

        Returns:
            A ProtocolMock for the protocol.
        """
        return ProtocolMock(self.protocol_type)


def all_protocol_implementations(module_name: str) -> Dict[Type[Protocol], List[Type]]:
    """
    Find all implementations of all protocols in a module.

    Args:
        module_name: The module to search in.

    Returns:
        A dictionary mapping protocols to lists of implementations.
    """
    import importlib

    module = importlib.import_module(module_name)

    # Find all protocols in the module
    protocols = []
    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and hasattr(obj, "_is_protocol")
            and obj._is_protocol
            and obj.__module__ == module.__name__
        ):
            protocols.append(obj)

    # Find implementations for each protocol
    implementations = {}
    for protocol in protocols:
        impls = find_protocol_implementations(module, protocol)
        if impls:
            implementations[protocol] = impls

    return implementations


def create_protocol_test_suite(
    module_name: str, base_test_case: Type[unittest.TestCase] = unittest.TestCase
) -> unittest.TestSuite:
    """
    Create a test suite that tests all protocol implementations in a module.

    Args:
        module_name: The module to search in.
        base_test_case: The base test case to use for tests.

    Returns:
        A test suite containing tests for all protocol implementations.
    """
    suite = unittest.TestSuite()

    # Find all implementations
    implementations = all_protocol_implementations(module_name)

    # Create test cases
    for protocol, impls in implementations.items():
        for impl in impls:
            test_name = f"test_{impl.__name__}_implements_{protocol.__name__}"

            # Create a test function
            def test_func(self, impl=impl, protocol=protocol):
                try:
                    validate_protocol(impl, protocol)
                except ProtocolValidationError as e:
                    self.fail(str(e))

            # Create a test case class
            test_class = type(
                f"Test{impl.__name__}Protocol",
                (base_test_case,),
                {test_name: test_func},
            )

            # Add the test case to the suite
            suite.addTest(test_class(test_name))

    return suite
