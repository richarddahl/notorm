"""
Codebase analyzer for data modeling.

This module provides tools for analyzing a codebase and extracting data models.
"""

import os
import re
import ast
import enum
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import uuid

from pydantic import BaseModel, Field

# Set up logging
logger = logging.getLogger(__name__)


class ModelType(str, enum.Enum):
    """
    Type of model to analyze.
    """
    
    ENTITY = "entity"
    REPOSITORY = "repository"
    SERVICE = "service"
    ALL = "all"


class EntityField(BaseModel):
    """
    Model for an entity field.
    """
    
    name: str
    type: str
    primaryKey: bool = False


class Entity(BaseModel):
    """
    Model for an entity.
    """
    
    id: str
    name: str
    fields: List[EntityField]
    x: Optional[float] = None
    y: Optional[float] = None


class Relationship(BaseModel):
    """
    Model for a relationship between entities.
    """
    
    source: str
    target: str
    type: str
    name: Optional[str] = None


class AnalyzeCodebase:
    """
    Analyzer for extracting data models from a codebase.
    """
    
    def __init__(self, project_path: str):
        """
        Initialize the analyzer.
        
        Args:
            project_path: Path to the project to analyze
        """
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise ValueError(f"Project path {project_path} does not exist")
    
    def analyze(self, model_type: ModelType = ModelType.ALL) -> Dict[str, Any]:
        """
        Analyze the codebase and extract data models.
        
        Args:
            model_type: Type of model to analyze
            
        Returns:
            Dict with entities and relationships
        """
        entities = []
        relationships = []
        
        if model_type in (ModelType.ENTITY, ModelType.ALL):
            entities, relationships = self._analyze_entities()
        
        return {
            "entities": entities,
            "relationships": relationships
        }
    
    def _analyze_entities(self) -> Tuple[List[Entity], List[Relationship]]:
        """
        Analyze entity models in the codebase.
        
        Returns:
            Tuple of (entities, relationships)
        """
        entities = []
        relationships = []
        entity_map = {}  # name -> id
        
        # Find domain directories
        domain_dirs = self._find_domain_dirs()
        
        for domain_dir in domain_dirs:
            domain_entities, domain_rels = self._analyze_domain_dir(domain_dir)
            
            # Map entity names to IDs for relationship linking
            for entity in domain_entities:
                entity_map[entity.name] = entity.id
            
            entities.extend(domain_entities)
        
        # Process relationships after all entities are known
        for domain_dir in domain_dirs:
            rels = self._extract_relationships(domain_dir, entity_map)
            relationships.extend(rels)
        
        return entities, relationships
    
    def _find_domain_dirs(self) -> List[Path]:
        """
        Find domain directories in the project.
        
        Returns:
            List of domain directories
        """
        domain_dirs = []
        
        # Look for src/*/domain
        src_dir = self.project_path / "src"
        if src_dir.exists():
            for path in src_dir.glob("*/domain"):
                if path.is_dir():
                    domain_dirs.append(path)
        
        # Also look directly for domain
        domain_dir = self.project_path / "domain"
        if domain_dir.exists() and domain_dir.is_dir():
            domain_dirs.append(domain_dir)
        
        return domain_dirs
    
    def _analyze_domain_dir(self, domain_dir: Path) -> Tuple[List[Entity], List[Relationship]]:
        """
        Analyze a domain directory for entities.
        
        Args:
            domain_dir: Domain directory to analyze
            
        Returns:
            Tuple of (entities, relationships)
        """
        entities = []
        relationships = []
        
        # Look for Python files in the domain directory
        for py_file in domain_dir.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Check for entity classes
            entity = self._extract_entity_from_file(py_file)
            if entity:
                entities.append(entity)
        
        return entities, relationships
    
    def _extract_entity_from_file(self, file_path: Path) -> Optional[Entity]:
        """
        Extract entity information from a Python file.
        
        Args:
            file_path: Path to a Python file
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            
            # Parse the file using ast
            tree = ast.parse(file_content)
            
            # Look for class definitions with BaseModel as a base
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class inherits from BaseModel or a Model in name
                    is_entity = False
                    for base in node.bases:
                        if isinstance(base, ast.Name) and (base.id == "BaseModel" or "Model" in base.id):
                            is_entity = True
                            break
                    
                    if not is_entity:
                        continue
                    
                    # Found an entity class
                    fields = []
                    
                    # Extract fields from class body
                    for class_node in node.body:
                        if isinstance(class_node, ast.AnnAssign) and isinstance(class_node.target, ast.Name):
                            field_name = class_node.target.id
                            
                            # Skip private fields and special methods
                            if field_name.startswith("_"):
                                continue
                            
                            # Extract type annotation
                            field_type = "Any"
                            if isinstance(class_node.annotation, ast.Name):
                                field_type = class_node.annotation.id
                            elif isinstance(class_node.annotation, ast.Subscript):
                                field_type = self._extract_subscript_type(class_node.annotation)
                            
                            # Check if field is a primary key
                            is_primary = False
                            if field_name == "id" or field_name.endswith("_id"):
                                is_primary = True
                            
                            fields.append(EntityField(
                                name=field_name,
                                type=field_type,
                                primaryKey=is_primary
                            ))
                    
                    # If we have fields, create an entity
                    if fields:
                        entity_id = f"entity_{str(uuid.uuid4()).replace('-', '')}"
                        return Entity(
                            id=entity_id,
                            name=node.name,
                            fields=fields
                        )
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting entity from {file_path}: {e}")
            return None
    
    def _extract_subscript_type(self, annotation: ast.Subscript) -> str:
        """
        Extract type from a subscript annotation (e.g. List[str]).
        
        Args:
            annotation: AST subscript node
            
        Returns:
            Type as a string
        """
        value_name = ""
        if isinstance(annotation.value, ast.Name):
            value_name = annotation.value.id
        elif isinstance(annotation.value, ast.Attribute):
            value_name = annotation.value.attr
        
        if hasattr(annotation, "slice") and isinstance(annotation.slice, ast.Index):
            if isinstance(annotation.slice.value, ast.Name):
                return f"{value_name}[{annotation.slice.value.id}]"
            elif isinstance(annotation.slice.value, ast.Str):
                return f"{value_name}[{annotation.slice.value.s}]"
        
        # For Python 3.9+
        if hasattr(annotation, "slice") and isinstance(annotation.slice, ast.Name):
            return f"{value_name}[{annotation.slice.id}]"
        
        return value_name
    
    def _extract_relationships(self, domain_dir: Path, entity_map: Dict[str, str]) -> List[Relationship]:
        """
        Extract relationships from a domain directory.
        
        Args:
            domain_dir: Domain directory to analyze
            entity_map: Map of entity names to IDs
            
        Returns:
            List of relationships
        """
        relationships = []
        
        # Look for Python files in the domain directory
        for py_file in domain_dir.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Check for relationships in file
            file_rels = self._extract_relationships_from_file(py_file, entity_map)
            relationships.extend(file_rels)
        
        return relationships
    
    def _extract_relationships_from_file(self, file_path: Path, entity_map: Dict[str, str]) -> List[Relationship]:
        """
        Extract relationships from a Python file.
        
        Args:
            file_path: Path to a Python file
            entity_map: Map of entity names to IDs
            
        Returns:
            List of relationships
        """
        relationships = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            
            # Look for fields that reference other entities
            for entity_name, entity_id in entity_map.items():
                pattern = rf"(?:List|Optional)\[['\"]{entity_name}['\"]"
                for match in re.finditer(pattern, file_content):
                    # Find the class this field is in
                    # This is a simplistic approach - a proper implementation would use AST
                    source_entity = None
                    for src_name, src_id in entity_map.items():
                        if f"class {src_name}" in file_content[:match.start()]:
                            source_entity = src_name
                    
                    if source_entity and source_entity != entity_name:
                        # Determine relationship type based on field type
                        rel_type = "one-to-one"
                        if "List" in match.group(0):
                            rel_type = "one-to-many"
                        
                        # Create relationship
                        relationships.append(Relationship(
                            source=entity_map[source_entity],
                            target=entity_id,
                            type=rel_type,
                            name=f"{source_entity}_{entity_name}"
                        ))
            
            return relationships
        except Exception as e:
            logger.warning(f"Error extracting relationships from {file_path}: {e}")
            return []