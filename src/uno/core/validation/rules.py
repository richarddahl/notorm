"""
Business rule validation utilities.

This module provides utilities for implementing complex business rules
that can be composed, reused, and applied to domain objects.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Set, TypeVar

from uno.core.errors.result import ValidationResult, ValidationError, ErrorSeverity
from uno.core.validation.validator import Validator, ValidationContext

T = TypeVar("T")  # Type of object being validated


class Rule(Generic[T], ABC):
    """
    Abstract base class for business rules.

    This class represents a business rule that can be applied to an object
    and returns a validation result.
    """

    @abstractmethod
    def evaluate(self, obj: T, context: ValidationContext) -> bool:
        """
        Evaluate the rule against an object.

        Args:
            obj: The object to validate
            context: The validation context to update

        Returns:
            True if the rule is satisfied, False otherwise
        """
        pass

    def __and__(self, other: "Rule[T]") -> "CompositeRule[T]":
        """
        Combine this rule with another rule using AND.

        Args:
            other: Another rule to combine with this one

        Returns:
            A composite rule that is satisfied if both rules are satisfied
        """
        return AndRule(self, other)

    def __or__(self, other: "Rule[T]") -> "CompositeRule[T]":
        """
        Combine this rule with another rule using OR.

        Args:
            other: Another rule to combine with this one

        Returns:
            A composite rule that is satisfied if either rule is satisfied
        """
        return OrRule(self, other)

    def __invert__(self) -> "Rule[T]":
        """
        Negate this rule.

        Returns:
            A rule that is satisfied if this rule is not satisfied
        """
        return NotRule(self)


class CompositeRule(Rule[T], ABC):
    """
    Base class for composite rules.

    This class represents a rule that is composed of other rules.
    """

    def __init__(self, *rules: Rule[T]):
        """
        Initialize a composite rule.

        Args:
            *rules: The rules to compose
        """
        self.rules = rules


class AndRule(CompositeRule[T]):
    """
    A rule that is satisfied if all of its component rules are satisfied.
    """

    def evaluate(self, obj: T, context: ValidationContext) -> bool:
        """
        Evaluate the rule against an object.

        The rule is satisfied if all component rules are satisfied.

        Args:
            obj: The object to validate
            context: The validation context to update

        Returns:
            True if all component rules are satisfied, False otherwise
        """
        result = True
        for rule in self.rules:
            if not rule.evaluate(obj, context):
                result = False
        return result


class OrRule(CompositeRule[T]):
    """
    A rule that is satisfied if any of its component rules are satisfied.
    """

    def evaluate(self, obj: T, context: ValidationContext) -> bool:
        """
        Evaluate the rule against an object.

        The rule is satisfied if any component rule is satisfied.

        Args:
            obj: The object to validate
            context: The validation context to update

        Returns:
            True if any component rule is satisfied, False otherwise
        """
        if not self.rules:
            return True

        for rule in self.rules:
            if rule.evaluate(obj, context):
                return True
        return False


class NotRule(Rule[T]):
    """
    A rule that negates another rule.
    """

    def __init__(self, rule: Rule[T]):
        """
        Initialize a NOT rule.

        Args:
            rule: The rule to negate
        """
        self.rule = rule

    def evaluate(self, obj: T, context: ValidationContext) -> bool:
        """
        Evaluate the rule against an object.

        The rule is satisfied if the component rule is not satisfied.

        Args:
            obj: The object to validate
            context: The validation context to update

        Returns:
            True if the component rule is not satisfied, False otherwise
        """
        # Create a temporary context to avoid adding errors twice
        temp_context = ValidationContext()
        result = not self.rule.evaluate(obj, temp_context)
        return result


class RuleSet(Rule[T]):
    """
    A set of rules to be applied to an object.

    This class allows for organizing rules into named sets that can be
    applied together.
    """

    def __init__(
        self, name: str, description: str = "", rules: Optional[list[Rule[T]]] = None
    ):
        """
        Initialize a rule set.

        Args:
            name: The name of the rule set
            description: A description of the rule set
            rules: The rules in the set
        """
        self.name = name
        self.description = description
        self.rules = rules or []

    def add_rule(self, rule: Rule[T]) -> "RuleSet[T]":
        """
        Add a rule to the set.

        Args:
            rule: The rule to add

        Returns:
            Self for chaining
        """
        self.rules.append(rule)
        return self

    def evaluate(self, obj: T, context: ValidationContext) -> bool:
        """
        Evaluate the rule set against an object.

        The rule set is satisfied if all rules in the set are satisfied.

        Args:
            obj: The object to validate
            context: The validation context to update

        Returns:
            True if all rules in the set are satisfied, False otherwise
        """
        result = True
        for rule in self.rules:
            if not rule.evaluate(obj, context):
                result = False
        return result


class RuleValidator(Validator[T]):
    """
    Validator that applies business rules to objects.

    This validator applies a set of business rules to objects and collects
    validation errors.
    """

    def __init__(self, rules: Optional[list[Rule[T]]] = None):
        """
        Initialize a rule validator.

        Args:
            rules: The rules to apply
        """
        self.rules = rules or []

    def add_rule(self, rule: Rule[T]) -> "RuleValidator[T]":
        """
        Add a rule to the validator.

        Args:
            rule: The rule to add

        Returns:
            Self for chaining
        """
        self.rules.append(rule)
        return self

    def _validate(self, obj: T, context: ValidationContext) -> None:
        """
        Validate an object against business rules.

        Args:
            obj: The object to validate
            context: The validation context to update
        """
        for rule in self.rules:
            rule.evaluate(obj, context)
