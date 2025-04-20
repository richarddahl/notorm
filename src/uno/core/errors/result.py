from typing import Generic, TypeVar, Callable, cast
from uno.core.errors.framework import FrameworkError
from uno.core.errors.framework import ErrorDetail

T = TypeVar("T")
E = TypeVar("E", bound=FrameworkError)


class Success(Generic[T]):
    """Represents a successful operation."""

    def __init__(self, value: T):
        """
        Initialize a success result.

        Args:
            value: The successful value
        """
        self._value = value

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False

    def value(self) -> T:
        return self._value


class Failure(Generic[E]):
    """Represents a failed operation."""

    def __init__(self, error: E):
        """
        Initialize a failure result.

        Args:
            error: The error that occurred
        """
        if not isinstance(error, FrameworkError):
            raise TypeError("Error must be a FrameworkError subclass")

        self._error = error

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True

    def error(self) -> E:
        return self._error


class Result(Generic[T, E]):
    """Represents the result of an operation that may succeed or fail."""

    def __init__(self, value: Success[T] | Failure[E]):
        """
        Initialize a Result instance.

        Args:
            value: The success or failure value
        """
        if isinstance(value, Failure) and not isinstance(value.error(), FrameworkError):
            raise TypeError("Error must be a FrameworkError subclass")

        self._value = value

    def is_success(self) -> bool:
        """Check if this is a success result."""
        return isinstance(self._value, Success)

    def is_failure(self) -> bool:
        """Check if this is a failure result."""
        return isinstance(self._value, Failure)

    def value(self) -> T:
        """Get the success value if this is a success result."""
        if self.is_success():
            return self._value.value()
        raise ValueError("Cannot get value from a failure Result")

    def error(self) -> E:
        """Get the error if this is a failure result."""
        if self.is_failure():
            return self._value.error()
        raise ValueError("Cannot get error from a success Result")

    @classmethod
    def success(cls, value: T) -> "Result[T, E]":
        """Create a success result."""
        return cls(Success(value))

    @classmethod
    def failure(cls, error: E) -> "Result[T, E]":
        """Create a failure result with an error."""
        if not isinstance(error, FrameworkError):
            raise TypeError("Error must be a FrameworkError subclass")

        return cls(Failure(error))

    def map(self, func: Callable[[T], T]) -> "Result[T, E]":
        """
        Apply a function to the success value if this is a success result.

        Args:
            func: The function to apply

        Returns:
            A new Result with the transformed value
        """
        if self.is_success():
            return Result.success(func(self.value()))
        return self

    def flat_map(self, func: Callable[[T], "Result[T, E]"]) -> "Result[T, E]":
        """
        Apply a function that returns a Result to the success value.

        Args:
            func: The function to apply

        Returns:
            The result of applying the function
        """
        if self.is_success():
            return func(self.value())
        return self

    def recover(self, func: Callable[[E], T]) -> "Result[T, E]":
        """
        Apply a recovery function to the error if this is a failure result.

        Args:
            func: The recovery function

        Returns:
            A new Result with the recovered value
        """
        if self.is_failure():
            return Result.success(func(self.error()))
        return self

    def or_else(self, default: T) -> T:
        """
        Get the success value or a default value if this is a failure result.

        Args:
            default: The default value to return

        Returns:
            The success value if successful, or the default value if failed
        """
        return self.value() if self.is_success() else default

    def to_error_detail(self) -> "ErrorDetail":
        """
        Convert the error to an ErrorDetail if this is a failure result.

        Returns:
            The error as an ErrorDetail

        Raises:
            ValueError: If this is a success result
        """
        from uno.core.errors.framework import ErrorDetail

        if self.is_failure():
            error = self.error()
            return ErrorDetail(
                code=error.code,
                message=error.message,
                category=error.category,
                severity=error.severity,
                details=error.details,
                timestamp=error.timestamp,
                trace_id=error.context.trace_id if error.context else None,
            )
        raise ValueError("Cannot convert success result to error detail")

    @classmethod
    def from_error_detail(cls, detail: ErrorDetail) -> "Result[T, E]":
        """
        Create a failure result from an ErrorDetail.

        Args:
            detail: The error detail

        Returns:
            A failure result with the error
        """
        error = cast(
            E,
            FrameworkError(
                message=detail.message,
                code=detail.code,
                details=detail.details,
                category=detail.category,
                severity=detail.severity,
            ),
        )
        return cls.failure(error)
