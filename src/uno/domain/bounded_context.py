"""
Bounded context management system for the Uno framework.

This module provides tools for defining, mapping and working with bounded contexts
in the domain model. Bounded contexts are a central pattern in Domain-Driven Design
that establish explicit boundaries between different parts of the domain model.
"""

from enum import Enum, auto
from typing import Dict, List, Set, Optional, NamedTuple, Any
from dataclasses import dataclass, field


class ContextRelationType(Enum):
    """Types of relationships between bounded contexts."""

    # Upstream context provides a service that downstream context consumes
    UPSTREAM_DOWNSTREAM = auto()

    # Two contexts share some models with careful translation
    SHARED_KERNEL = auto()

    # One context adapts to protect itself from another context's model
    ANTICORRUPTION_LAYER = auto()

    # Two contexts are separate with minimal integration
    SEPARATE_WAYS = auto()

    # Two contexts are in open communication with conforming models
    CONFORMIST = auto()

    # One context acts as an external service to the other
    OPEN_HOST_SERVICE = auto()

    # Custom-defined relationship
    CUSTOM = auto()


@dataclass
class BoundedContext:
    """
    Represents a bounded context in the domain.

    A bounded context defines a logical boundary around a specific domain model.
    It encapsulates the ubiquitous language, model, and rules for a particular
    subdomain.
    """

    name: str
    package_path: str
    description: str
    responsibility: str
    ubiquitous_language: dict[str, str] = field(default_factory=dict)
    team: str | None = None
    dependencies: Set[str] = field(default_factory=set)
    is_core_domain: bool = False

    def add_term(self, term: str, definition: str) -> None:
        """
        Add a term to the ubiquitous language of this context.

        Args:
            term: The term to define
            definition: The definition of the term in this context
        """
        self.ubiquitous_language[term] = definition

    def add_dependency(self, context_name: str) -> None:
        """
        Add a dependency on another bounded context.

        Args:
            context_name: The name of the context this context depends on
        """
        self.dependencies.add(context_name)


@dataclass
class ContextRelation:
    """Defines a relationship between two bounded contexts."""

    source_context: str
    target_context: str
    relation_type: ContextRelationType
    description: str
    implementation_notes: str | None = None

    @property
    def key(self) -> str:
        """Get a unique key for this relation."""
        return f"{self.source_context}:{self.target_context}"


class ContextMap:
    """
    Manages the map of bounded contexts and their relationships.

    The context map documents how bounded contexts relate to each other
    and provides tools for analyzing and visualizing these relationships.
    """

    def __init__(self):
        self._contexts: dict[str, BoundedContext] = {}
        self._relations: dict[str, ContextRelation] = {}

    def add_context(self, context: BoundedContext) -> None:
        """
        Add a bounded context to the map.

        Args:
            context: The bounded context to add
        """
        self._contexts[context.name] = context

    def add_relation(self, relation: ContextRelation) -> None:
        """
        Add a relationship between contexts.

        Args:
            relation: The relationship to add
        """
        # Ensure both contexts exist
        if relation.source_context not in self._contexts:
            raise ValueError(f"Source context {relation.source_context} not found")
        if relation.target_context not in self._contexts:
            raise ValueError(f"Target context {relation.target_context} not found")

        # Add the relation
        self._relations[relation.key] = relation

        # Update dependencies
        self._contexts[relation.source_context].add_dependency(relation.target_context)

    def get_context(self, name: str) -> Optional[BoundedContext]:
        """
        Get a bounded context by name.

        Args:
            name: The name of the context

        Returns:
            The bounded context, or None if not found
        """
        return self._contexts.get(name)

    def get_relation(self, source: str, target: str) -> Optional[ContextRelation]:
        """
        Get the relationship between two contexts.

        Args:
            source: The source context
            target: The target context

        Returns:
            The relationship, or None if not found
        """
        key = f"{source}:{target}"
        return self._relations.get(key)

    def get_all_contexts(self) -> list[BoundedContext]:
        """
        Get all bounded contexts.

        Returns:
            List of all bounded contexts
        """
        return list(self._contexts.values())

    def get_all_relations(self) -> list[ContextRelation]:
        """
        Get all context relationships.

        Returns:
            List of all relationships
        """
        return list(self._relations.values())

    def get_core_domains(self) -> list[BoundedContext]:
        """
        Get all core domains.

        Returns:
            List of all bounded contexts marked as core domains
        """
        return [ctx for ctx in self._contexts.values() if ctx.is_core_domain]

    def get_dependent_contexts(self, context_name: str) -> list[BoundedContext]:
        """
        Get all contexts that depend on the given context.

        Args:
            context_name: The name of the context

        Returns:
            List of contexts that depend on the given context
        """
        return [
            ctx for ctx in self._contexts.values() if context_name in ctx.dependencies
        ]

    def analyze_dependencies(self) -> dict[str, Any]:
        """
        Analyze the dependencies between contexts.

        Returns:
            Dictionary with analysis results
        """
        result = {
            "circular_dependencies": [],
            "most_depended_on": [],
            "most_dependent": [],
            "isolated_contexts": [],
        }

        # Find circular dependencies
        for context in self._contexts.values():
            for dep in context.dependencies:
                dep_context = self._contexts.get(dep)
                if dep_context and context.name in dep_context.dependencies:
                    result["circular_dependencies"].append((context.name, dep))

        # Find most depended on contexts
        dependency_counts = {name: 0 for name in self._contexts}
        for context in self._contexts.values():
            for dep in context.dependencies:
                if dep in dependency_counts:
                    dependency_counts[dep] += 1

        result["most_depended_on"] = sorted(
            dependency_counts.items(), key=lambda x: x[1], reverse=True
        )

        # Find most dependent contexts
        result["most_dependent"] = sorted(
            [(ctx.name, len(ctx.dependencies)) for ctx in self._contexts.values()],
            key=lambda x: x[1],
            reverse=True,
        )

        # Find isolated contexts (no dependencies and none depend on it)
        result["isolated_contexts"] = [
            name
            for name, count in dependency_counts.items()
            if count == 0 and not self._contexts[name].dependencies
        ]

        return result

    def generate_dot_graph(self) -> str:
        """
        Generate a DOT graph representation of the context map.

        Returns:
            DOT graph string that can be rendered with Graphviz
        """
        lines = ["digraph G {", "  rankdir=LR;", "  node [shape=box];"]

        # Add nodes for contexts
        for name, context in self._contexts.items():
            style = "filled,bold" if context.is_core_domain else "filled"
            fillcolor = "lightblue" if context.is_core_domain else "white"
            lines.append(
                f'  "{name}" [style="{style}",fillcolor="{fillcolor}",label="{name}\\n{context.responsibility}"];'
            )

        # Add edges for relations
        for relation in self._relations.values():
            edge_style = "solid"
            edge_color = "black"

            if relation.relation_type == ContextRelationType.ANTICORRUPTION_LAYER:
                edge_style = "dashed"
                edge_color = "red"
            elif relation.relation_type == ContextRelationType.SHARED_KERNEL:
                edge_style = "bold"
                edge_color = "blue"
            elif relation.relation_type == ContextRelationType.CONFORMIST:
                edge_style = "dotted"

            lines.append(
                f'  "{relation.source_context}" -> "{relation.target_context}" '
                f'[style="{edge_style}",color="{edge_color}",label="{relation.relation_type.name}"];'
            )

        lines.append("}")
        return "\n".join(lines)


# Create a singleton instance
_context_map = ContextMap()


def get_context_map() -> ContextMap:
    """Get the singleton context map instance."""
    return _context_map


def register_bounded_context(context: BoundedContext) -> None:
    """
    Register a bounded context with the context map.

    This is a convenience function for registering contexts
    with the singleton context map.

    Args:
        context: The bounded context to register
    """
    _context_map.add_context(context)


def register_context_relation(relation: ContextRelation) -> None:
    """
    Register a relationship between contexts.

    This is a convenience function for registering relationships
    with the singleton context map.

    Args:
        relation: The relationship to register
    """
    _context_map.add_relation(relation)
