/**
 * Data modeler app component
 * 
 * This is a web component for the Uno Data Modeler application
 */

// Constants for the SVG grid
const GRID_SIZE = 20;
const ENTITY_WIDTH = 220;
const ENTITY_HEADER_HEIGHT = 40;
const FIELD_HEIGHT = 30;
const ENTITY_PADDING = 10;

class DataModelerApp extends HTMLElement {
    constructor() {
        super();
        this._entities = [];
        this._relationships = [];
        this._projectName = 'UnoProject';
        this._selectedEntity = null;
        this._draggedEntity = null;
        this._dragOffsetX = 0;
        this._dragOffsetY = 0;
        this._isCreatingRelationship = false;
        this._relationshipStartEntity = null;
        this._relationshipStartPoint = { x: 0, y: 0 };
        
        // Create shadow DOM
        this.attachShadow({ mode: 'open' });
        
        // Initialize the component
        this._render();
        this._addEventListeners();
    }
    
    // Getters and setters
    get entities() {
        return this._entities;
    }
    
    set entities(value) {
        this._entities = value;
        this._renderEntities();
    }
    
    get relationships() {
        return this._relationships;
    }
    
    set relationships(value) {
        this._relationships = value;
        this._renderRelationships();
    }
    
    get projectName() {
        return this._projectName;
    }
    
    set projectName(value) {
        this._projectName = value;
        this.shadowRoot.querySelector('.project-name').textContent = value;
    }
    
    // Lifecycle callbacks
    connectedCallback() {
        // Component connected to the DOM
        this._renderEntities();
        this._renderRelationships();
    }
    
    // Render the component
    _render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    height: 100%;
                }
                
                .app-container {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                }
                
                .toolbar {
                    background-color: #3f51b5;
                    color: white;
                    padding: 10px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .project-name {
                    font-size: 1.5em;
                    font-weight: bold;
                }
                
                .toolbar-actions {
                    display: flex;
                    gap: 10px;
                }
                
                .btn {
                    background-color: #ffffff;
                    border: none;
                    color: #3f51b5;
                    padding: 8px 12px;
                    font-size: 0.9em;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: background-color 0.2s;
                }
                
                .btn:hover {
                    background-color: #e8eaf6;
                }
                
                .content {
                    flex: 1;
                    display: flex;
                    overflow: hidden;
                }
                
                .sidebar {
                    width: 300px;
                    border-right: 1px solid #e0e0e0;
                    background-color: #f9f9f9;
                    overflow-y: auto;
                    padding: 15px;
                }
                
                .sidebar h3 {
                    margin-top: 0;
                    color: #3f51b5;
                }
                
                .sidebar-section {
                    margin-bottom: 20px;
                }
                
                .canvas-container {
                    flex: 1;
                    overflow: auto;
                    position: relative;
                    background-color: #f0f0f0;
                }
                
                .canvas {
                    min-width: 2000px;
                    min-height: 2000px;
                    position: relative;
                }
                
                .grid {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-size: ${GRID_SIZE}px ${GRID_SIZE}px;
                    background-image: radial-gradient(circle, #c1c1c1 1px, transparent 1px);
                    pointer-events: none;
                }
                
                .entity {
                    position: absolute;
                    width: ${ENTITY_WIDTH}px;
                    background-color: white;
                    border-radius: 4px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
                    cursor: move;
                    overflow: hidden;
                }
                
                .entity.selected {
                    box-shadow: 0 0 0 2px #3f51b5;
                }
                
                .entity-header {
                    background-color: #3f51b5;
                    color: white;
                    padding: 10px;
                    font-weight: bold;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .entity-fields {
                    padding: 0;
                }
                
                .field {
                    padding: 8px 10px;
                    border-bottom: 1px solid #e0e0e0;
                    display: flex;
                    justify-content: space-between;
                }
                
                .field:last-child {
                    border-bottom: none;
                }
                
                .field-name {
                    font-weight: bold;
                }
                
                .field-type {
                    color: #666;
                    font-size: 0.9em;
                }
                
                /* Form styles */
                .form-group {
                    margin-bottom: 15px;
                }
                
                label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }
                
                input, select {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                
                /* Relationship styles */
                .relationship-line {
                    stroke: #666;
                    stroke-width: 2;
                }
                
                .relationship-marker {
                    fill: #666;
                }
                
                .connector {
                    position: absolute;
                    width: 12px;
                    height: 12px;
                    background-color: #3f51b5;
                    border-radius: 50%;
                    cursor: pointer;
                    z-index: 10;
                }
                
                .temp-connector-line {
                    position: absolute;
                    border-top: 2px dashed #3f51b5;
                    transform-origin: 0 0;
                    pointer-events: none;
                    z-index: 9;
                }
            </style>
            
            <div class="app-container">
                <div class="toolbar">
                    <div class="project-name">${this._projectName}</div>
                    <div class="toolbar-actions">
                        <button class="btn add-entity-btn">Add Entity</button>
                        <button class="btn save-model-btn">Save Model</button>
                        <button class="btn generate-code-btn">Generate Code</button>
                    </div>
                </div>
                
                <div class="content">
                    <div class="sidebar">
                        <div class="sidebar-section entity-details" style="display: none;">
                            <h3>Entity Details</h3>
                            <div class="form-group">
                                <label for="entity-name">Name</label>
                                <input type="text" id="entity-name">
                            </div>
                            
                            <h4>Fields</h4>
                            <div class="fields-list"></div>
                            
                            <button class="btn add-field-btn">Add Field</button>
                        </div>
                        
                        <div class="sidebar-section" id="entity-form" style="display: none;">
                            <h3>New Entity</h3>
                            <div class="form-group">
                                <label for="new-entity-name">Name</label>
                                <input type="text" id="new-entity-name">
                            </div>
                            
                            <button class="btn create-entity-btn">Create</button>
                            <button class="btn cancel-entity-btn">Cancel</button>
                        </div>
                        
                        <div class="sidebar-section" id="field-form" style="display: none;">
                            <h3>New Field</h3>
                            <div class="form-group">
                                <label for="field-name">Name</label>
                                <input type="text" id="field-name">
                            </div>
                            
                            <div class="form-group">
                                <label for="field-type">Type</label>
                                <select id="field-type">
                                    <option value="string">String</option>
                                    <option value="integer">Integer</option>
                                    <option value="float">Float</option>
                                    <option value="boolean">Boolean</option>
                                    <option value="datetime">DateTime</option>
                                    <option value="uuid">UUID</option>
                                    <option value="text">Text</option>
                                    <option value="json">JSON</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="field-primary-key">
                                    Primary Key
                                </label>
                            </div>
                            
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="field-nullable">
                                    Nullable
                                </label>
                            </div>
                            
                            <button class="btn add-field-confirm-btn">Add</button>
                            <button class="btn cancel-field-btn">Cancel</button>
                        </div>
                        
                        <div class="sidebar-section" id="welcome-message">
                            <h3>Uno Data Modeler</h3>
                            <p>Welcome to the Uno Data Modeler! Use this tool to visually design your data models.</p>
                            <p>Start by adding an entity using the "Add Entity" button, or select an existing entity to edit its details.</p>
                        </div>
                    </div>
                    
                    <div class="canvas-container">
                        <div class="canvas">
                            <div class="grid"></div>
                            <svg class="relationships-svg" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5;"></svg>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add event listeners
    _addEventListeners() {
        // Toolbar actions
        const addEntityBtn = this.shadowRoot.querySelector('.add-entity-btn');
        const saveModelBtn = this.shadowRoot.querySelector('.save-model-btn');
        const generateCodeBtn = this.shadowRoot.querySelector('.generate-code-btn');
        
        addEntityBtn.addEventListener('click', () => this._showEntityForm());
        saveModelBtn.addEventListener('click', () => this._saveModel());
        generateCodeBtn.addEventListener('click', () => this._generateCode());
        
        // Form actions
        const createEntityBtn = this.shadowRoot.querySelector('.create-entity-btn');
        const cancelEntityBtn = this.shadowRoot.querySelector('.cancel-entity-btn');
        const addFieldBtn = this.shadowRoot.querySelector('.add-field-btn');
        const addFieldConfirmBtn = this.shadowRoot.querySelector('.add-field-confirm-btn');
        const cancelFieldBtn = this.shadowRoot.querySelector('.cancel-field-btn');
        
        createEntityBtn.addEventListener('click', () => this._createEntity());
        cancelEntityBtn.addEventListener('click', () => this._hideEntityForm());
        addFieldBtn.addEventListener('click', () => this._showFieldForm());
        addFieldConfirmBtn.addEventListener('click', () => this._addField());
        cancelFieldBtn.addEventListener('click', () => this._hideFieldForm());
        
        // Canvas events for drag and drop
        const canvas = this.shadowRoot.querySelector('.canvas');
        canvas.addEventListener('mousemove', (e) => this._handleCanvasMouseMove(e));
        canvas.addEventListener('mouseup', () => this._handleCanvasMouseUp());
    }
    
    // Render entities
    _renderEntities() {
        const canvas = this.shadowRoot.querySelector('.canvas');
        
        // Remove existing entities
        const existingEntities = this.shadowRoot.querySelectorAll('.entity');
        existingEntities.forEach(el => el.remove());
        
        // Create entity elements
        this._entities.forEach(entity => {
            const entityElement = document.createElement('div');
            entityElement.className = 'entity';
            entityElement.dataset.id = entity.id;
            entityElement.style.left = `${entity.x}px`;
            entityElement.style.top = `${entity.y}px`;
            
            // Calculate entity height based on number of fields
            const entityHeight = ENTITY_HEADER_HEIGHT + (entity.fields.length * FIELD_HEIGHT);
            entityElement.style.height = `${entityHeight}px`;
            
            // Create header
            const header = document.createElement('div');
            header.className = 'entity-header';
            header.textContent = entity.name;
            
            // Create fields container
            const fieldsContainer = document.createElement('div');
            fieldsContainer.className = 'entity-fields';
            
            // Add fields
            entity.fields.forEach(field => {
                const fieldElement = document.createElement('div');
                fieldElement.className = 'field';
                
                const fieldName = document.createElement('div');
                fieldName.className = 'field-name';
                fieldName.textContent = field.name;
                if (field.primaryKey) {
                    fieldName.textContent += ' 🔑';
                }
                
                const fieldType = document.createElement('div');
                fieldType.className = 'field-type';
                fieldType.textContent = field.type;
                
                fieldElement.appendChild(fieldName);
                fieldElement.appendChild(fieldType);
                fieldsContainer.appendChild(fieldElement);
            });
            
            // Add elements to entity
            entityElement.appendChild(header);
            entityElement.appendChild(fieldsContainer);
            
            // Add event listeners for entity
            entityElement.addEventListener('mousedown', (e) => this._handleEntityMouseDown(e, entity));
            entityElement.addEventListener('click', () => this._selectEntity(entity));
            
            // Add entity to canvas
            canvas.appendChild(entityElement);
        });
    }
    
    // Render relationships
    _renderRelationships() {
        const svg = this.shadowRoot.querySelector('.relationships-svg');
        svg.innerHTML = '';
        
        this._relationships.forEach(relationship => {
            const sourceEntity = this._entities.find(e => e.id === relationship.source);
            const targetEntity = this._entities.find(e => e.id === relationship.target);
            
            if (!sourceEntity || !targetEntity) return;
            
            // Calculate connection points
            const sourcePoint = this._getEntityConnectionPoint(sourceEntity, targetEntity);
            const targetPoint = this._getEntityConnectionPoint(targetEntity, sourceEntity);
            
            // Create line
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', sourcePoint.x);
            line.setAttribute('y1', sourcePoint.y);
            line.setAttribute('x2', targetPoint.x);
            line.setAttribute('y2', targetPoint.y);
            line.setAttribute('class', 'relationship-line');
            
            // Create marker for relationship type
            if (relationship.type === 'one-to-many') {
                // Add arrow marker to target side
                this._addMarkerDefinition(svg, 'arrow');
                line.setAttribute('marker-end', 'url(#arrow)');
            }
            
            svg.appendChild(line);
            
            // Add relationship label
            const labelX = (sourcePoint.x + targetPoint.x) / 2;
            const labelY = (sourcePoint.y + targetPoint.y) / 2 - 10;
            
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', labelX);
            label.setAttribute('y', labelY);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('font-size', '12');
            label.textContent = relationship.name || relationship.type;
            
            svg.appendChild(label);
        });
    }
    
    // Add SVG marker definition
    _addMarkerDefinition(svg, id) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', id);
        marker.setAttribute('viewBox', '0 0 10 10');
        marker.setAttribute('refX', '8');
        marker.setAttribute('refY', '5');
        marker.setAttribute('markerWidth', '6');
        marker.setAttribute('markerHeight', '6');
        marker.setAttribute('orient', 'auto');
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
        path.setAttribute('class', 'relationship-marker');
        
        marker.appendChild(path);
        defs.appendChild(marker);
        svg.appendChild(defs);
    }
    
    // Calculate entity connection point
    _getEntityConnectionPoint(entity1, entity2) {
        const entity1Rect = {
            left: entity1.x,
            top: entity1.y,
            right: entity1.x + ENTITY_WIDTH,
            bottom: entity1.y + ENTITY_HEADER_HEIGHT + (entity1.fields.length * FIELD_HEIGHT)
        };
        
        const entity2Rect = {
            left: entity2.x,
            top: entity2.y,
            right: entity2.x + ENTITY_WIDTH,
            bottom: entity2.y + ENTITY_HEADER_HEIGHT + (entity2.fields.length * FIELD_HEIGHT)
        };
        
        const entity1Center = {
            x: (entity1Rect.left + entity1Rect.right) / 2,
            y: (entity1Rect.top + entity1Rect.bottom) / 2
        };
        
        const entity2Center = {
            x: (entity2Rect.left + entity2Rect.right) / 2,
            y: (entity2Rect.top + entity2Rect.bottom) / 2
        };
        
        // Determine which side to connect from
        const dx = entity2Center.x - entity1Center.x;
        const dy = entity2Center.y - entity1Center.y;
        
        // Check which side has the greatest projection
        if (Math.abs(dx) > Math.abs(dy)) {
            // Connect on left or right side
            if (dx > 0) {
                // Connect from right side of entity1
                return {
                    x: entity1Rect.right,
                    y: entity1Center.y
                };
            } else {
                // Connect from left side of entity1
                return {
                    x: entity1Rect.left,
                    y: entity1Center.y
                };
            }
        } else {
            // Connect on top or bottom side
            if (dy > 0) {
                // Connect from bottom side of entity1
                return {
                    x: entity1Center.x,
                    y: entity1Rect.bottom
                };
            } else {
                // Connect from top side of entity1
                return {
                    x: entity1Center.x,
                    y: entity1Rect.top
                };
            }
        }
    }
    
    // Show entity form
    _showEntityForm() {
        this.shadowRoot.querySelector('#welcome-message').style.display = 'none';
        this.shadowRoot.querySelector('.entity-details').style.display = 'none';
        this.shadowRoot.querySelector('#field-form').style.display = 'none';
        this.shadowRoot.querySelector('#entity-form').style.display = 'block';
        
        // Clear form fields
        this.shadowRoot.querySelector('#new-entity-name').value = '';
    }
    
    // Hide entity form
    _hideEntityForm() {
        this.shadowRoot.querySelector('#entity-form').style.display = 'none';
        this.shadowRoot.querySelector('#welcome-message').style.display = 'block';
    }
    
    // Create a new entity
    _createEntity() {
        const nameInput = this.shadowRoot.querySelector('#new-entity-name');
        const name = nameInput.value.trim();
        
        if (!name) {
            alert('Entity name is required');
            return;
        }
        
        // Generate a unique ID
        const id = 'entity_' + Math.random().toString(36).substr(2, 9);
        
        // Create default fields
        const fields = [
            { name: 'id', type: 'uuid', primaryKey: true },
            { name: 'created_at', type: 'datetime' },
            { name: 'updated_at', type: 'datetime' }
        ];
        
        // Find an empty spot for the new entity
        let x = 100;
        let y = 100;
        
        // Try to avoid overlap with existing entities
        if (this._entities.length > 0) {
            x = Math.max(...this._entities.map(e => e.x)) + 50;
            y = Math.min(...this._entities.map(e => e.y));
        }
        
        // Create the entity
        const newEntity = {
            id,
            name,
            fields,
            x,
            y
        };
        
        // Add to entities array
        this._entities = [...this._entities, newEntity];
        
        // Render entities
        this._renderEntities();
        
        // Hide form
        this._hideEntityForm();
        
        // Select the new entity
        this._selectEntity(newEntity);
    }
    
    // Select an entity
    _selectEntity(entity) {
        // Deselect previous entity
        if (this._selectedEntity) {
            const prevElement = this.shadowRoot.querySelector(`.entity[data-id="${this._selectedEntity.id}"]`);
            if (prevElement) {
                prevElement.classList.remove('selected');
            }
        }
        
        // Select new entity
        this._selectedEntity = entity;
        const element = this.shadowRoot.querySelector(`.entity[data-id="${entity.id}"]`);
        if (element) {
            element.classList.add('selected');
        }
        
        // Show entity details in sidebar
        this._showEntityDetails(entity);
    }
    
    // Show entity details in sidebar
    _showEntityDetails(entity) {
        this.shadowRoot.querySelector('#welcome-message').style.display = 'none';
        this.shadowRoot.querySelector('#entity-form').style.display = 'none';
        this.shadowRoot.querySelector('#field-form').style.display = 'none';
        this.shadowRoot.querySelector('.entity-details').style.display = 'block';
        
        // Set entity name
        const nameInput = this.shadowRoot.querySelector('#entity-name');
        nameInput.value = entity.name;
        
        // Set up event listener for entity name change
        nameInput.onchange = () => {
            entity.name = nameInput.value;
            this._renderEntities();
        };
        
        // Render fields
        const fieldsList = this.shadowRoot.querySelector('.fields-list');
        fieldsList.innerHTML = '';
        
        entity.fields.forEach((field, index) => {
            const fieldItem = document.createElement('div');
            fieldItem.className = 'field-item';
            fieldItem.style.padding = '5px';
            fieldItem.style.marginBottom = '5px';
            fieldItem.style.border = '1px solid #e0e0e0';
            fieldItem.style.borderRadius = '4px';
            
            const fieldNameType = document.createElement('div');
            fieldNameType.textContent = `${field.name}: ${field.type}`;
            if (field.primaryKey) {
                fieldNameType.textContent += ' 🔑';
            }
            
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.className = 'btn';
            deleteButton.style.marginTop = '5px';
            deleteButton.style.backgroundColor = '#f44336';
            deleteButton.style.color = 'white';
            
            deleteButton.onclick = () => {
                if (field.primaryKey) {
                    alert('Cannot delete primary key field');
                    return;
                }
                
                // Remove field
                entity.fields.splice(index, 1);
                this._renderEntities();
                this._showEntityDetails(entity);
            };
            
            fieldItem.appendChild(fieldNameType);
            fieldItem.appendChild(deleteButton);
            fieldsList.appendChild(fieldItem);
        });
    }
    
    // Show field form
    _showFieldForm() {
        this.shadowRoot.querySelector('#welcome-message').style.display = 'none';
        this.shadowRoot.querySelector('#entity-form').style.display = 'none';
        this.shadowRoot.querySelector('.entity-details').style.display = 'none';
        this.shadowRoot.querySelector('#field-form').style.display = 'block';
        
        // Clear form fields
        this.shadowRoot.querySelector('#field-name').value = '';
        this.shadowRoot.querySelector('#field-type').value = 'string';
        this.shadowRoot.querySelector('#field-primary-key').checked = false;
        this.shadowRoot.querySelector('#field-nullable').checked = false;
    }
    
    // Hide field form
    _hideFieldForm() {
        this.shadowRoot.querySelector('#field-form').style.display = 'none';
        
        if (this._selectedEntity) {
            this.shadowRoot.querySelector('.entity-details').style.display = 'block';
        } else {
            this.shadowRoot.querySelector('#welcome-message').style.display = 'block';
        }
    }
    
    // Add a field to the selected entity
    _addField() {
        if (!this._selectedEntity) return;
        
        const nameInput = this.shadowRoot.querySelector('#field-name');
        const typeSelect = this.shadowRoot.querySelector('#field-type');
        const primaryKeyCheckbox = this.shadowRoot.querySelector('#field-primary-key');
        const nullableCheckbox = this.shadowRoot.querySelector('#field-nullable');
        
        const name = nameInput.value.trim();
        const type = typeSelect.value;
        const primaryKey = primaryKeyCheckbox.checked;
        const nullable = nullableCheckbox.checked;
        
        if (!name) {
            alert('Field name is required');
            return;
        }
        
        // Check if field name is unique
        if (this._selectedEntity.fields.some(f => f.name === name)) {
            alert('Field name must be unique');
            return;
        }
        
        // Check if there's already a primary key when adding another
        if (primaryKey && this._selectedEntity.fields.some(f => f.primaryKey)) {
            alert('Entity already has a primary key');
            return;
        }
        
        // Create the field
        const newField = {
            name,
            type,
            primaryKey,
            nullable
        };
        
        // Add field to entity
        this._selectedEntity.fields.push(newField);
        
        // Render entities
        this._renderEntities();
        
        // Hide form and show entity details
        this._hideFieldForm();
        this._showEntityDetails(this._selectedEntity);
    }
    
    // Handle mouse down on entity for dragging
    _handleEntityMouseDown(event, entity) {
        event.stopPropagation();
        
        // Select entity
        this._selectEntity(entity);
        
        // Start dragging
        this._draggedEntity = entity;
        const rect = event.currentTarget.getBoundingClientRect();
        const canvasRect = this.shadowRoot.querySelector('.canvas').getBoundingClientRect();
        
        this._dragOffsetX = event.clientX - rect.left - canvasRect.left + this.shadowRoot.querySelector('.canvas-container').scrollLeft;
        this._dragOffsetY = event.clientY - rect.top - canvasRect.top + this.shadowRoot.querySelector('.canvas-container').scrollTop;
    }
    
    // Handle mouse move on canvas for dragging
    _handleCanvasMouseMove(event) {
        if (!this._draggedEntity) return;
        
        event.preventDefault();
        
        const canvasRect = this.shadowRoot.querySelector('.canvas').getBoundingClientRect();
        const canvasScrollLeft = this.shadowRoot.querySelector('.canvas-container').scrollLeft;
        const canvasScrollTop = this.shadowRoot.querySelector('.canvas-container').scrollTop;
        
        // Calculate new position with grid snapping
        let newX = event.clientX - canvasRect.left - this._dragOffsetX + canvasScrollLeft;
        let newY = event.clientY - canvasRect.top - this._dragOffsetY + canvasScrollTop;
        
        // Snap to grid
        newX = Math.round(newX / GRID_SIZE) * GRID_SIZE;
        newY = Math.round(newY / GRID_SIZE) * GRID_SIZE;
        
        // Update entity position
        this._draggedEntity.x = newX;
        this._draggedEntity.y = newY;
        
        // Update entity element position
        const entityElement = this.shadowRoot.querySelector(`.entity[data-id="${this._draggedEntity.id}"]`);
        if (entityElement) {
            entityElement.style.left = `${newX}px`;
            entityElement.style.top = `${newY}px`;
        }
        
        // Update relationships
        this._renderRelationships();
    }
    
    // Handle mouse up on canvas for dragging
    _handleCanvasMouseUp() {
        this._draggedEntity = null;
    }
    
    // Save the current model
    _saveModel() {
        // Create the model object
        const model = {
            projectName: this._projectName,
            entities: this._entities,
            relationships: this._relationships
        };
        
        // Convert to JSON
        const json = JSON.stringify(model, null, 2);
        
        // Create a download link
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this._projectName.replace(/\s+/g, '_')}_model.json`;
        a.click();
        
        // Clean up
        URL.revokeObjectURL(url);
    }
    
    // Generate code from the model
    _generateCode() {
        // Format entities for API request
        const apiEntities = this._entities.map(entity => ({
            id: entity.id,
            name: entity.name,
            fields: entity.fields.map(field => ({
                name: field.name,
                type: field.type,
                primaryKey: field.primaryKey,
                nullable: field.nullable || false
            }))
        }));
        
        // Send to API
        fetch('/api/devtools/model/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                projectName: this._projectName,
                entities: apiEntities,
                relationships: this._relationships
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error generating code');
            }
            return response.json();
        })
        .then(data => {
            alert('Code generated successfully!');
            console.log('Generated code:', data);
            
            // TODO: Add a UI for viewing/downloading generated code
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error generating code: ' + error.message);
        });
    }
}

// Define the custom element if not already defined
if (!customElements.get('data-modeler-app')) {
    customElements.define('data-modeler-app', DataModelerApp);
    console.log('data-modeler-app component registered');
} else {
    console.log('data-modeler-app component already registered');
}