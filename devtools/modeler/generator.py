"""
Code generator for data models.

This module provides tools for generating code from data models.
"""

import os
import logging
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import jinja2

from uno.devtools.modeler.analyzer import Entity, Relationship

# Set up logging
logger = logging.getLogger(__name__)

# Templates directory - relative to this file
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class CodeGenerator:
    """
    Generator for code from data models.
    """

    def __init__(self, project_name: str, template_dir: Optional[Path] = None):
        """
        Initialize the code generator.

        Args:
            project_name: Name of the project
            template_dir: Directory containing templates
        """
        self.project_name = project_name
        self.template_dir = template_dir or TEMPLATE_DIR

        # Set up Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["snake_case"] = self._to_snake_case
        self.env.filters["camel_case"] = self._to_camel_case
        self.env.filters["pascal_case"] = self._to_pascal_case

    def generate(
        self, entities: list[Entity], relationships: list[Relationship]
    ) -> dict[str, dict[str, str]]:
        """
        Generate code from a data model.

        Args:
            entities: List of entities
            relationships: List of relationships

        Returns:
            Dict with generated code for entities, repositories, and services
        """
        result = {"entities": {}, "repositories": {}, "services": {}}

        # Create entity_map for relationship lookup
        entity_map = {entity.id: entity for entity in entities}

        # Generate code for each entity
        for entity in entities:
            # Generate entity model
            result["entities"][entity.name] = self._generate_entity(
                entity, relationships, entity_map
            )

            # Generate repository
            result["repositories"][entity.name] = self._generate_repository(
                entity, relationships, entity_map
            )

            # Generate service
            result["services"][entity.name] = self._generate_service(
                entity, relationships, entity_map
            )

        return result

    def _generate_entity(
        self,
        entity: Entity,
        relationships: list[Relationship],
        entity_map: dict[str, Entity],
    ) -> str:
        """
        Generate code for an entity model.

        Args:
            entity: Entity to generate code for
            relationships: All relationships
            entity_map: Map of entity IDs to entities

        Returns:
            Generated code
        """
        try:
            template = self.env.get_template("feature/entity.py.j2")

            # Find relationships for this entity
            entity_relationships = self._find_entity_relationships(
                entity, relationships, entity_map
            )

            # Render the template
            return template.render(
                feature_name=entity.name,
                entity=entity,
                relationships=entity_relationships,
                project_name=self.project_name,
            )
        except Exception as e:
            logger.exception(f"Error generating entity code for {entity.name}")
            return f"# Error generating entity code: {str(e)}"

    def _generate_repository(
        self,
        entity: Entity,
        relationships: list[Relationship],
        entity_map: dict[str, Entity],
    ) -> str:
        """
        Generate code for a repository.

        Args:
            entity: Entity to generate repository for
            relationships: All relationships
            entity_map: Map of entity IDs to entities

        Returns:
            Generated code
        """
        try:
            template = self.env.get_template("feature/repository.py.j2")

            # Find relationships for this entity
            entity_relationships = self._find_entity_relationships(
                entity, relationships, entity_map
            )

            # Render the template
            return template.render(
                feature_name=entity.name,
                entity=entity,
                relationships=entity_relationships,
                project_name=self.project_name,
            )
        except Exception as e:
            logger.exception(f"Error generating repository code for {entity.name}")
            return f"# Error generating repository code: {str(e)}"

    def _generate_service(
        self,
        entity: Entity,
        relationships: list[Relationship],
        entity_map: dict[str, Entity],
    ) -> str:
        """
        Generate code for a service.

        Args:
            entity: Entity to generate service for
            relationships: All relationships
            entity_map: Map of entity IDs to entities

        Returns:
            Generated code
        """
        try:
            template = self.env.get_template("feature/service.py.j2")

            # Find relationships for this entity
            entity_relationships = self._find_entity_relationships(
                entity, relationships, entity_map
            )

            # Render the template
            return template.render(
                feature_name=entity.name,
                entity=entity,
                relationships=entity_relationships,
                project_name=self.project_name,
            )
        except Exception as e:
            logger.exception(f"Error generating service code for {entity.name}")
            return f"# Error generating service code: {str(e)}"

    def _find_entity_relationships(
        self,
        entity: Entity,
        relationships: list[Relationship],
        entity_map: dict[str, Entity],
    ) -> list[dict[str, Any]]:
        """
        Find relationships for an entity.

        Args:
            entity: Entity to find relationships for
            relationships: All relationships
            entity_map: Map of entity IDs to entities

        Returns:
            List of relationship details
        """
        entity_relationships = []

        for relationship in relationships:
            is_source = relationship.source == entity.id
            is_target = relationship.target == entity.id

            if not (is_source or is_target):
                continue

            related_id = relationship.target if is_source else relationship.source
            if related_id not in entity_map:
                continue

            related_entity = entity_map[related_id]

            entity_relationships.append(
                {
                    "entity_id": entity.id,
                    "related_id": related_id,
                    "related_name": related_entity.name,
                    "type": relationship.type,
                    "is_source": is_source,
                    "is_target": is_target,
                    "is_many": relationship.type in ("one-to-many", "many-to-many")
                    or (relationship.type == "many-to-one" and is_source),
                }
            )

        return entity_relationships

    def _to_snake_case(self, text: str) -> str:
        """
        Convert text to snake_case.

        Args:
            text: Text to convert

        Returns:
            Text in snake_case
        """
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _to_camel_case(self, text: str) -> str:
        """
        Convert text to camelCase.

        Args:
            text: Text to convert

        Returns:
            Text in camelCase
        """
        parts = text.split("_")
        return parts[0] + "".join(x.title() for x in parts[1:])

    def _to_pascal_case(self, text: str) -> str:
        """
        Convert text to PascalCase.

        Args:
            text: Text to convert

        Returns:
            Text in PascalCase
        """
        return "".join(x.title() for x in text.split("_"))
