/**
 * Data Modeler Application component
 *
 * A web component that serves as the main application shell for the data modeling tool.
 */

import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import "./entity-model-editor.js";
import "./model-code-view.js";

/**
 * Data Modeler Application
 *
 * @element data-modeler-app
 */
@customElement("data-modeler-app")
export class DataModelerApp extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100vh;
      width: 100%;
      box-sizing: border-box;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
        Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
    }

    .app-container {
      display: flex;
      flex-direction: column;
      height: 100%;
    }

    .app-header {
      display: flex;
      align-items: center;
      padding: 10px 20px;
      background-color: #0078d7;
      color: white;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      z-index: 1;
    }

    .app-title {
      font-size: 1.2rem;
      margin: 0;
      flex: 1;
    }

    .app-content {
      flex: 1;
      display: flex;
      overflow: hidden;
    }

    .model-panel {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .tabs {
      display: flex;
      background-color: #f5f5f5;
      border-bottom: 1px solid #ddd;
    }

    .tab {
      padding: 10px 15px;
      cursor: pointer;
      border-right: 1px solid #ddd;
    }

    .tab.active {
      background-color: white;
      border-bottom: 2px solid #0078d7;
    }

    .tab-content {
      flex: 1;
      overflow: hidden;
      background-color: white;
    }

    .project-info {
      display: flex;
      align-items: center;
    }

    .project-name {
      margin-right: 15px;
      color: rgba(255, 255, 255, 0.9);
    }

    button {
      padding: 8px 12px;
      border: none;
      border-radius: 4px;
      background-color: #005a9e;
      color: white;
      cursor: pointer;
      margin-left: 10px;
    }

    button:hover {
      background-color: #004275;
    }

    input {
      padding: 8px;
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 4px;
      background-color: rgba(255, 255, 255, 0.1);
      color: white;
    }

    input::placeholder {
      color: rgba(255, 255, 255, 0.6);
    }
  `;

  @property({ type: String }) projectName = "New Project";
  @property({ type: Array }) entities = [];
  @property({ type: Array }) relationships = [];

  @state() activeTab = "visual";
  @state() generatedCode = null;

  handleModelSaved(event) {
    const { entities, relationships } = event.detail;

    // Generate code using API call
    this.generateCode(entities, relationships).then((code) => {
      this.generatedCode = code;
      this.activeTab = "code";
    });
  }

  async generateCode(entities, relationships) {
    try {
      const response = await fetch("/api/devtools/model/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          projectName: this.projectName,
          entities,
          relationships,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error generating code:", error);
      // Fallback to client-side code generation
      return this.generateCodeLocally(entities, relationships);
    }
  }

  generateCodeLocally(entities, relationships) {
    // Simple client-side code generation as fallback
    const code = {
      entities: {},
      repositories: {},
      services: {},
    };

    // Generate entity models
    entities.forEach((entity) => {
      code.entities[entity.name] = this.generateEntityCode(
        entity,
        relationships
      );
      code.repositories[entity.name] = this.generateRepositoryCode(entity);
      code.services[entity.name] = this.generateServiceCode(entity);
    });

    return code;
  }

  generateEntityCode(entity, relationships) {
    // Template for entity model
    return `"""
${entity.name} entity module.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
${this.generateImportsForRelationships(entity, relationships)}

class ${entity.name}(BaseModel):
    """
    ${entity.name} entity.
    
    This class represents the domain entity for ${entity.name}.
    """
    
    ${entity.fields
      .map((field) => `${field.name}: ${this.getPythonType(field)}`)
      .join("\n    ")}
    ${this.generateRelationshipFields(entity, relationships)}
    
    class Config:
        """Pydantic model configuration."""
        
        validate_assignment = True
        
    def update(self, **kwargs) -> None:
        """
        Update entity fields.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()`;
  }

  generateImportsForRelationships(entity, relationships) {
    // Generate import statements for related entities
    const relatedEntities = relationships
      .filter(
        (rel) =>
          (rel.source.id || rel.source) === entity.id ||
          (rel.target.id || rel.target) === entity.id
      )
      .map((rel) => {
        const relatedEntityId =
          (rel.source.id || rel.source) === entity.id
            ? rel.target.id || rel.target
            : rel.source.id || rel.source;

        return this.entities.find((e) => e.id === relatedEntityId);
      })
      .filter(Boolean);

    if (relatedEntities.length === 0) return "";

    return `from typing import TYPE_CHECKING

if TYPE_CHECKING:
    ${relatedEntities
      .map((e) => `from .${e.name.toLowerCase()} import ${e.name}`)
      .join("\n    ")}`;
  }

  generateRelationshipFields(entity, relationships) {
    const relationshipFields = relationships
      .filter(
        (rel) =>
          (rel.source.id || rel.source) === entity.id ||
          (rel.target.id || rel.target) === entity.id
      )
      .map((rel) => {
        const isSource = (rel.source.id || rel.source) === entity.id;
        const relatedEntityId = isSource
          ? rel.target.id || rel.target
          : rel.source.id || rel.source;
        const relatedEntity = this.entities.find(
          (e) => e.id === relatedEntityId
        );

        if (!relatedEntity) return "";

        const fieldName =
          relatedEntity.name.toLowerCase() + (isSource ? "s" : "");

        // Determine type based on relationship type and direction
        let fieldType;
        if (rel.type === "one-to-many" && isSource) {
          fieldType = `list['${relatedEntity.name}'] = Field(default_factory=list)`;
        } else if (rel.type === "many-to-one" && !isSource) {
          fieldType = `list['${relatedEntity.name}'] = Field(default_factory=list)`;
        } else if (rel.type === "many-to-many") {
          fieldType = `list['${relatedEntity.name}'] = Field(default_factory=list)`;
        } else {
          fieldType = `Optional['${relatedEntity.name}'] = None`;
        }

        return `${fieldName}: ${fieldType}`;
      })
      .filter(Boolean)
      .join("\n    ");

    return relationshipFields;
  }

  getPythonType(field) {
    // Map field types to Python types
    const typeMap = {
      string: "str",
      integer: "int",
      float: "float",
      boolean: "bool",
      datetime: "datetime = Field(default_factory=datetime.utcnow)",
      date: "date",
      uuid: "UUID = Field(default_factory=uuid4)",
      json: "dict",
      array: "List",
      relation: "Any",
    };

    return typeMap[field.type] || "Any";
  }

  generateRepositoryCode(entity) {
    return `"""
${entity.name} repository module.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from uno.dependencies import inject
from uno.database.repository import UnoRepository
from uno.database.session import SessionFactory

from ..domain.${entity.name.toLowerCase()}_entity import ${entity.name}


class ${entity.name}Repository:
    """
    Repository for ${entity.name} entities.
    """
    
    @inject
    def __init__(self, session_factory: SessionFactory):
        """
        Initialize the repository.
        
        Args:
            session_factory: Session factory for creating database sessions
        """
        self.session_factory = session_factory
    
    async def get_by_id(self, id: UUID) -> Optional[${entity.name}]:
        """
        Get a ${entity.name} by ID.
        
        Args:
            id: ${entity.name} ID
            
        Returns:
            ${entity.name} entity if found, None otherwise
        """
        async with self.session_factory.create_async_session() as session:
            # Implementation depends on your ORM approach
            pass
    
    async def list(self, filters: Optional[Dict[str, Any]] = None) -> list[${
      entity.name
    }]:
        """
        List ${entity.name} entities with optional filtering.
        
        Args:
            filters: Optional filters
            
        Returns:
            List of ${entity.name} entities
        """
        async with self.session_factory.create_async_session() as session:
            # Implementation depends on your ORM approach
            pass
    
    async def create(self, entity: ${entity.name}) -> ${entity.name}:
        """
        Create a new ${entity.name}.
        
        Args:
            entity: ${entity.name} entity
            
        Returns:
            Created ${entity.name} entity
        """
        async with self.session_factory.create_async_session() as session:
            # Implementation depends on your ORM approach
            pass
    
    async def update(self, entity: ${entity.name}) -> ${entity.name}:
        """
        Update a ${entity.name}.
        
        Args:
            entity: ${entity.name} entity
            
        Returns:
            Updated ${entity.name} entity
        """
        async with self.session_factory.create_async_session() as session:
            # Implementation depends on your ORM approach
            pass
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete a ${entity.name}.
        
        Args:
            id: ${entity.name} ID
            
        Returns:
            True if deleted, False otherwise
        """
        async with self.session_factory.create_async_session() as session:
            # Implementation depends on your ORM approach
            pass`;
  }

  generateServiceCode(entity) {
    return `"""
${entity.name} service module.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from uno.dependencies import inject
from uno.core.errors import NotFoundError

from ..domain.${entity.name.toLowerCase()}_entity import ${entity.name}
from ..infrastructure.repositories.${entity.name.toLowerCase()}_repository import ${
      entity.name
    }Repository


class ${entity.name}Service:
    """
    Service for ${entity.name} operations.
    """
    
    @inject
    def __init__(self, repository: ${entity.name}Repository):
        """
        Initialize the service.
        
        Args:
            repository: ${entity.name} repository
        """
        self.repository = repository
    
    async def get_by_id(self, id: UUID) -> ${entity.name}:
        """
        Get a ${entity.name} by ID.
        
        Args:
            id: ${entity.name} ID
            
        Returns:
            ${entity.name} entity
            
        Raises:
            NotFoundError: If ${entity.name} not found
        """
        entity = await self.repository.get_by_id(id)
        if not entity:
            raise NotFoundError(f"${entity.name} with ID {id} not found")
        return entity
    
    async def list(self, filters: Optional[Dict[str, Any]] = None) -> list[${
      entity.name
    }]:
        """
        List ${entity.name} entities with optional filtering.
        
        Args:
            filters: Optional filters
            
        Returns:
            List of ${entity.name} entities
        """
        return await self.repository.list(filters)
    
    async def create(self, data: Dict[str, Any]) -> ${entity.name}:
        """
        Create a new ${entity.name}.
        
        Args:
            data: ${entity.name} data
            
        Returns:
            Created ${entity.name} entity
        """
        entity = ${entity.name}(**data)
        return await self.repository.create(entity)
    
    async def update(self, id: UUID, data: Dict[str, Any]) -> ${entity.name}:
        """
        Update a ${entity.name}.
        
        Args:
            id: ${entity.name} ID
            data: ${entity.name} data
            
        Returns:
            Updated ${entity.name} entity
            
        Raises:
            NotFoundError: If ${entity.name} not found
        """
        entity = await self.get_by_id(id)
        entity.update(**data)
        return await self.repository.update(entity)
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete a ${entity.name}.
        
        Args:
            id: ${entity.name} ID
            
        Returns:
            True if deleted, False otherwise
            
        Raises:
            NotFoundError: If ${entity.name} not found
        """
        entity = await self.get_by_id(id)
        return await self.repository.delete(id)`;
  }

  changeTab(tab) {
    this.activeTab = tab;
  }

  updateProjectName(event) {
    this.projectName = event.target.value;
  }

  render() {
    return html`
      <div class="app-container">
        <header class="app-header">
          <h1 class="app-title">Uno Data Modeler</h1>
          <div class="project-info">
            <span class="project-name">Project:</span>
            <input
              type="text"
              .value=${this.projectName}
              @input=${this.updateProjectName}
              placeholder="Project name"
            />
            <button @click=${() => (this.activeTab = "visual")}>
              Edit Model
            </button>
            <button @click=${() => (this.activeTab = "code")}>View Code</button>
          </div>
        </header>
        <main class="app-content">
          <div class="model-panel">
            <div class="tabs">
              <div
                class="tab ${this.activeTab === "visual" ? "active" : ""}"
                @click=${() => this.changeTab("visual")}
              >
                Visual Editor
              </div>
              <div
                class="tab ${this.activeTab === "code" ? "active" : ""}"
                @click=${() => this.changeTab("code")}
              >
                Generated Code
              </div>
            </div>
            <div class="tab-content">
              ${this.activeTab === "visual"
                ? html`
                    <entity-model-editor
                      .entities=${this.entities}
                      .relationships=${this.relationships}
                      .projectName=${this.projectName}
                      @model-saved=${this.handleModelSaved}
                    ></entity-model-editor>
                  `
                : html`
                    <model-code-view
                      .code=${this.generatedCode}
                    ></model-code-view>
                  `}
            </div>
          </div>
        </main>
      </div>
    `;
  }
}
