/**
 * Entity Model Editor component
 * 
 * A web component for creating and editing entity models visually.
 * Uses lit-element for the component framework and d3.js for visualization.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import * as d3 from 'd3';

/**
 * Entity Model Editor
 * 
 * @element entity-model-editor
 * @fires entity-changed - Fires when an entity is modified
 * @fires relationship-changed - Fires when a relationship is modified
 * @fires model-saved - Fires when the model is saved
 */
@customElement('entity-model-editor')
export class EntityModelEditor extends LitElement {
  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
      box-sizing: border-box;
    }
    
    .editor-container {
      display: flex;
      height: 100%;
    }
    
    .canvas {
      flex: 1;
      border: 1px solid #ccc;
      position: relative;
      overflow: hidden;
    }
    
    .toolbar {
      width: 250px;
      padding: 10px;
      border-left: 1px solid #ccc;
      overflow: auto;
    }
    
    .entity-node {
      fill: #fff;
      stroke: #0078d7;
      stroke-width: 2px;
      cursor: pointer;
    }
    
    .entity-name {
      font-weight: bold;
      font-size: 14px;
      pointer-events: none;
    }
    
    .entity-field {
      font-size: 12px;
      pointer-events: none;
    }
    
    .relationship-line {
      stroke: #555;
      stroke-width: 1.5px;
    }
    
    .relationship-marker {
      fill: #555;
    }
    
    .active {
      stroke: #ff6b6b;
      stroke-width: 3px;
    }
    
    button {
      margin: 5px 0;
      padding: 8px 12px;
      background: #0078d7;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    
    button:hover {
      background: #0063b1;
    }
    
    .property-panel {
      margin-top: 15px;
      border-top: 1px solid #eee;
      padding-top: 10px;
    }
    
    .property-panel label {
      display: block;
      margin: 10px 0 5px;
    }
    
    .property-panel input,
    .property-panel select {
      width: 100%;
      padding: 6px;
      box-sizing: border-box;
    }
    
    .property-list {
      margin-top: 10px;
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid #eee;
    }
    
    .property-item {
      padding: 5px;
      border-bottom: 1px solid #eee;
      display: flex;
      justify-content: space-between;
    }
    
    .property-item:last-child {
      border-bottom: none;
    }
  `;

  @property({ type: Array }) entities = [];
  @property({ type: Array }) relationships = [];
  @property({ type: String }) projectName = '';
  
  @state() selectedEntity = null;
  @state() selectedRelationship = null;
  @state() simulation = null;
  @state() svg = null;
  @state() newFieldName = '';
  @state() newFieldType = 'string';
  
  firstUpdated() {
    this.initializeD3();
  }
  
  updated(changedProperties) {
    if (changedProperties.has('entities') || changedProperties.has('relationships')) {
      this.updateD3();
    }
  }
  
  initializeD3() {
    const container = this.shadowRoot.querySelector('.canvas');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Create SVG container
    this.svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);
    
    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        this.svg.selectAll('g.entities-container')
          .attr('transform', event.transform);
      });
    
    this.svg.call(zoom);
    
    // Create container for entities
    this.svg.append('g')
      .attr('class', 'entities-container');
    
    // Set up force simulation
    this.simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(d => d.id).distance(200))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .on('tick', this.ticked.bind(this));
      
    this.updateD3();
  }
  
  updateD3() {
    if (!this.svg) return;
    
    const container = this.svg.select('g.entities-container');
    
    // Update relationships
    const links = container.selectAll('line.relationship-line')
      .data(this.relationships, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
    
    links.exit().remove();
    
    const newLinks = links.enter()
      .append('line')
      .attr('class', 'relationship-line')
      .on('click', (event, d) => this.selectRelationship(d));
    
    const allLinks = newLinks.merge(links);
    
    // Update entities
    const nodes = container.selectAll('g.entity-node-group')
      .data(this.entities, d => d.id);
    
    nodes.exit().remove();
    
    const newNodes = nodes.enter()
      .append('g')
      .attr('class', 'entity-node-group')
      .call(d3.drag()
        .on('start', this.dragStarted.bind(this))
        .on('drag', this.dragged.bind(this))
        .on('end', this.dragEnded.bind(this)));
    
    newNodes.append('rect')
      .attr('class', 'entity-node')
      .attr('rx', 5)
      .attr('ry', 5)
      .on('click', (event, d) => this.selectEntity(d));
    
    newNodes.append('text')
      .attr('class', 'entity-name')
      .attr('text-anchor', 'middle')
      .attr('dy', 25);
    
    const allNodes = newNodes.merge(nodes);
    
    allNodes.each((d, i, nodes) => {
      const group = d3.select(nodes[i]);
      
      // Update entity name
      group.select('text.entity-name')
        .text(d.name);
      
      // Remove old field texts
      group.selectAll('text.entity-field').remove();
      
      // Add fields
      d.fields.forEach((field, idx) => {
        group
          .append('text')
          .attr('class', 'entity-field')
          .attr('text-anchor', 'middle')
          .attr('dy', 45 + idx * 18)
          .text(`${field.name}: ${field.type}`);
      });
      
      // Update rectangle size based on content
      const textElements = group.selectAll('text');
      let maxWidth = 0;
      let height = 40 + d.fields.length * 18 + 20;
      
      textElements.each(function() {
        const textWidth = this.getComputedTextLength();
        if (textWidth > maxWidth) {
          maxWidth = textWidth;
        }
      });
      
      group.select('rect')
        .attr('width', Math.max(150, maxWidth + 40))
        .attr('height', height);
    });
    
    // Update simulation
    this.simulation.nodes(this.entities);
    this.simulation
      .force('link')
      .links(this.relationships);
    
    this.simulation.alpha(0.3).restart();
  }
  
  ticked() {
    if (!this.svg) return;
    
    const container = this.svg.select('g.entities-container');
    
    container.selectAll('line.relationship-line')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    
    container.selectAll('g.entity-node-group')
      .attr('transform', d => `translate(${d.x - (d.width || 100) / 2}, ${d.y - (d.height || 100) / 2})`);
  }
  
  dragStarted(event, d) {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  
  dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  
  dragEnded(event, d) {
    if (!event.active) this.simulation.alphaTarget(0);
    // Keep position fixed after drag
    // d.fx = null;
    // d.fy = null;
  }
  
  selectEntity(entity) {
    this.selectedEntity = entity;
    this.selectedRelationship = null;
    
    // Update visual selection
    this.svg.selectAll('rect.entity-node')
      .classed('active', d => d.id === entity.id);
    
    this.svg.selectAll('line.relationship-line')
      .classed('active', false);
      
    this.requestUpdate();
  }
  
  selectRelationship(relationship) {
    this.selectedRelationship = relationship;
    this.selectedEntity = null;
    
    // Update visual selection
    this.svg.selectAll('rect.entity-node')
      .classed('active', false);
    
    this.svg.selectAll('line.relationship-line')
      .classed('active', d => 
      (d.source.id || d.source) === (relationship.source.id || relationship.source) && 
      (d.target.id || d.target) === (relationship.target.id || relationship.target));
      
    this.requestUpdate();
  }
  
  addEntity() {
    const newId = `entity_${Date.now()}`;
    const newEntity = {
      id: newId,
      name: `NewEntity${this.entities.length + 1}`,
      fields: [
        { name: 'id', type: 'uuid', primaryKey: true },
        { name: 'created_at', type: 'datetime' },
        { name: 'updated_at', type: 'datetime' }
      ],
      x: Math.random() * 500,
      y: Math.random() * 500
    };
    
    this.entities = [...this.entities, newEntity];
    this.selectEntity(newEntity);
  }
  
  addRelationship() {
    if (this.entities.length < 2) {
      alert('You need at least two entities to create a relationship');
      return;
    }
    
    const source = this.entities[0].id;
    const target = this.entities[1].id;
    
    const newRelationship = {
      source,
      target,
      type: 'one-to-many',
      name: `${this.entities[0].name}_${this.entities[1].name}`
    };
    
    this.relationships = [...this.relationships, newRelationship];
    this.selectRelationship(newRelationship);
  }
  
  updateEntityName(event) {
    if (!this.selectedEntity) return;
    
    const newName = event.target.value;
    this.entities = this.entities.map(entity => 
      entity.id === this.selectedEntity.id 
        ? { ...entity, name: newName } 
        : entity
    );
    
    this.selectedEntity = { ...this.selectedEntity, name: newName };
  }
  
  updateFieldValue(event) {
    this.newFieldName = event.target.value;
  }
  
  updateFieldType(event) {
    this.newFieldType = event.target.value;
  }
  
  addField() {
    if (!this.selectedEntity || !this.newFieldName) return;
    
    const newField = {
      name: this.newFieldName,
      type: this.newFieldType
    };
    
    const updatedEntity = {
      ...this.selectedEntity,
      fields: [...this.selectedEntity.fields, newField]
    };
    
    this.entities = this.entities.map(entity => 
      entity.id === this.selectedEntity.id 
        ? updatedEntity
        : entity
    );
    
    this.selectedEntity = updatedEntity;
    this.newFieldName = '';
    this.newFieldType = 'string';
  }
  
  removeField(fieldName) {
    if (!this.selectedEntity) return;
    
    const updatedEntity = {
      ...this.selectedEntity,
      fields: this.selectedEntity.fields.filter(field => field.name !== fieldName)
    };
    
    this.entities = this.entities.map(entity => 
      entity.id === this.selectedEntity.id 
        ? updatedEntity
        : entity
    );
    
    this.selectedEntity = updatedEntity;
  }
  
  updateRelationshipType(event) {
    if (!this.selectedRelationship) return;
    
    const newType = event.target.value;
    this.relationships = this.relationships.map(rel => {
      if (
        (rel.source.id || rel.source) === (this.selectedRelationship.source.id || this.selectedRelationship.source) && 
        (rel.target.id || rel.target) === (this.selectedRelationship.target.id || this.selectedRelationship.target)
      ) {
        return { ...rel, type: newType };
      }
      return rel;
    });
    
    this.selectedRelationship = { ...this.selectedRelationship, type: newType };
  }
  
  removeEntity() {
    if (!this.selectedEntity) return;
    
    // Remove related relationships
    this.relationships = this.relationships.filter(rel => 
      (rel.source.id || rel.source) !== this.selectedEntity.id && 
      (rel.target.id || rel.target) !== this.selectedEntity.id
    );
    
    // Remove entity
    this.entities = this.entities.filter(entity => entity.id !== this.selectedEntity.id);
    this.selectedEntity = null;
  }
  
  removeRelationship() {
    if (!this.selectedRelationship) return;
    
    this.relationships = this.relationships.filter(rel => 
      !((rel.source.id || rel.source) === (this.selectedRelationship.source.id || this.selectedRelationship.source) && 
      (rel.target.id || rel.target) === (this.selectedRelationship.target.id || this.selectedRelationship.target))
    );
    
    this.selectedRelationship = null;
  }
  
  generateCode() {
    // Trigger model-saved event with the current state
    this.dispatchEvent(new CustomEvent('model-saved', {
      detail: {
        entities: this.entities,
        relationships: this.relationships,
        projectName: this.projectName
      }
    }));
  }
  
  render() {
    return html`
      <div class="editor-container">
        <div class="canvas"></div>
        <div class="toolbar">
          <h3>Entity Modeler</h3>
          <button @click=${this.addEntity}>Add Entity</button>
          <button @click=${this.addRelationship}>Add Relationship</button>
          <button @click=${this.generateCode}>Generate Code</button>
          
          ${this.selectedEntity ? html`
            <div class="property-panel">
              <h4>Entity Properties</h4>
              <label>
                Name:
                <input type="text" .value=${this.selectedEntity.name} @input=${this.updateEntityName}>
              </label>
              
              <h5>Fields</h5>
              <div class="property-list">
                ${this.selectedEntity.fields.map(field => html`
                  <div class="property-item">
                    <span>${field.name}: ${field.type}</span>
                    <button @click=${() => this.removeField(field.name)}>×</button>
                  </div>
                `)}
              </div>
              
              <label>
                New Field:
                <input type="text" .value=${this.newFieldName} @input=${this.updateFieldValue} placeholder="Field name">
              </label>
              
              <label>
                Type:
                <select @change=${this.updateFieldType}>
                  <option value="string">String</option>
                  <option value="integer">Integer</option>
                  <option value="float">Float</option>
                  <option value="boolean">Boolean</option>
                  <option value="datetime">DateTime</option>
                  <option value="date">Date</option>
                  <option value="uuid">UUID</option>
                  <option value="json">JSON</option>
                  <option value="array">Array</option>
                  <option value="relation">Relation</option>
                </select>
              </label>
              
              <button @click=${this.addField}>Add Field</button>
              <button @click=${this.removeEntity}>Remove Entity</button>
            </div>
          ` : ''}
          
          ${this.selectedRelationship ? html`
            <div class="property-panel">
              <h4>Relationship Properties</h4>
              <label>
                Type:
                <select @change=${this.updateRelationshipType} .value=${this.selectedRelationship.type}>
                  <option value="one-to-one">One-to-One</option>
                  <option value="one-to-many">One-to-Many</option>
                  <option value="many-to-one">Many-to-One</option>
                  <option value="many-to-many">Many-to-Many</option>
                </select>
              </label>
              
              <button @click=${this.removeRelationship}>Remove Relationship</button>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }
}