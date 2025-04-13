import { LitElement, html, css } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-textarea.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-checkbox.js';
import '@webcomponents/awesome/wa-radio.js';
import '@webcomponents/awesome/wa-switch.js';
import '@webcomponents/awesome/wa-list.js';
import '@webcomponents/awesome/wa-list-item.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-divider.js';
import '@webcomponents/awesome/wa-chip.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-tooltip.js';
import '@webcomponents/awesome/wa-spinner.js';

/**
 * @element wa-report-builder
 * @description An interactive report builder component using WebAwesome
 * @property {Object} template - The report template being edited
 * @property {String} mode - Edit or create mode
 * @property {Array} availableEntities - List of available entity types
 */
export class WebAwesomeReportBuilder extends LitElement {
  static get properties() {
    return {
      template: { type: Object },
      mode: { type: String },
      availableEntities: { type: Array },
      availableFields: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      activeTab: { type: String },
      showFieldDialog: { type: Boolean },
      currentField: { type: Object },
      showTriggerDialog: { type: Boolean },
      currentTrigger: { type: Object },
      showOutputDialog: { type: Boolean },
      currentOutput: { type: Object }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --builder-bg: var(--wa-background-color, #f5f5f5);
        --builder-padding: 20px;
        --section-gap: 24px;
      }
      .builder-container {
        padding: var(--builder-padding);
        background-color: var(--builder-bg);
        min-height: 600px;
      }
      .builder-header {
        margin-bottom: var(--section-gap);
      }
      .builder-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .builder-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .form-row {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
      }
      .form-row > * {
        flex: 1;
      }
      .section-title {
        font-size: 18px;
        font-weight: 500;
        margin: 24px 0 16px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .field-list {
        margin-bottom: 20px;
      }
      .empty-list {
        padding: 32px;
        text-align: center;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        color: var(--wa-text-secondary-color, #757575);
      }
      .actions {
        display: flex;
        justify-content: space-between;
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .field-type-options {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
      }
      .field-type-option {
        flex: 1;
        text-align: center;
        padding: 16px;
        border: 2px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .field-type-option:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .field-type-option.selected {
        border-color: var(--wa-primary-color, #3f51b5);
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
      }
      .field-type-icon {
        font-size: 32px;
        margin-bottom: 8px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .field-type-option.selected .field-type-icon {
        color: var(--wa-primary-color, #3f51b5);
      }
      .field-config-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .parameter-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .json-editor {
        width: 100%;
        min-height: 200px;
        font-family: monospace;
        padding: 12px;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-surface-color, #ffffff);
      }
      .preview-section {
        margin-top: 24px;
        padding: 16px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
    `;
  }

  constructor() {
    super();
    this.template = this._createEmptyTemplate();
    this.mode = 'create';
    this.availableEntities = [];
    this.availableFields = [];
    this.loading = false;
    this.error = null;
    this.activeTab = 'design';
    this.showFieldDialog = false;
    this.currentField = null;
    this.showTriggerDialog = false;
    this.currentTrigger = null;
    this.showOutputDialog = false;
    this.currentOutput = null;
    
    // Mock data for demo purposes
    this._loadMockData();
  }

  _createEmptyTemplate() {
    return {
      name: '',
      description: '',
      entity_type: '',
      fields: [],
      triggers: [],
      outputs: [],
      metadata: {}
    };
  }
  
  _loadMockData() {
    // Mock available entities
    this.availableEntities = [
      { value: 'customer', label: 'Customer' },
      { value: 'order', label: 'Order' },
      { value: 'product', label: 'Product' },
      { value: 'invoice', label: 'Invoice' },
      { value: 'inventory', label: 'Inventory' }
    ];
    
    // Mock available fields for customer entity
    const customerFields = [
      { path: 'id', name: 'ID', type: 'string' },
      { path: 'name', name: 'Name', type: 'string' },
      { path: 'email', name: 'Email', type: 'string' },
      { path: 'phone', name: 'Phone', type: 'string' },
      { path: 'created_at', name: 'Created At', type: 'datetime' },
      { path: 'updated_at', name: 'Updated At', type: 'datetime' },
      { path: 'orders.count()', name: 'Order Count', type: 'number' },
      { path: 'orders.sum(total)', name: 'Total Spent', type: 'number' },
      { path: 'address.city', name: 'City', type: 'string' },
      { path: 'address.country', name: 'Country', type: 'string' }
    ];
    
    // Mock available fields for order entity
    const orderFields = [
      { path: 'id', name: 'ID', type: 'string' },
      { path: 'number', name: 'Order Number', type: 'string' },
      { path: 'customer.name', name: 'Customer Name', type: 'string' },
      { path: 'created_at', name: 'Order Date', type: 'datetime' },
      { path: 'status', name: 'Status', type: 'string' },
      { path: 'total', name: 'Total Amount', type: 'number' },
      { path: 'items.count()', name: 'Item Count', type: 'number' },
      { path: 'shipping_address', name: 'Shipping Address', type: 'string' },
      { path: 'payment_method', name: 'Payment Method', type: 'string' }
    ];
    
    this._entityFields = {
      'customer': customerFields,
      'order': orderFields
    };
  }

  connectedCallback() {
    super.connectedCallback();
    
    // In a real implementation, we would load entities from the server
    // this.loadEntities();
  }

  async loadEntities() {
    this.loading = true;
    
    try {
      const response = await fetch('/api/reports/entities');
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.availableEntities = await response.json();
    } catch (err) {
      console.error('Failed to load entities:', err);
      this.error = `Error loading entities: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  async loadEntityFields(entityType) {
    if (!entityType) return;
    
    // For demo purposes, use mock data
    if (this._entityFields && this._entityFields[entityType]) {
      this.availableFields = this._entityFields[entityType];
      return;
    }
    
    this.loading = true;
    
    try {
      const response = await fetch(`/api/reports/entities/${entityType}/fields`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.availableFields = await response.json();
    } catch (err) {
      console.error(`Failed to load fields for ${entityType}:`, err);
      this.error = `Error loading fields: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  handleEntityChange(e) {
    const entityType = e.target.value;
    this.template = {
      ...this.template,
      entity_type: entityType,
      fields: []
    };
    
    if (entityType) {
      this.loadEntityFields(entityType);
    } else {
      this.availableFields = [];
    }
  }

  handleNameChange(e) {
    this.template = {
      ...this.template,
      name: e.target.value
    };
  }

  handleDescriptionChange(e) {
    this.template = {
      ...this.template,
      description: e.target.value
    };
  }

  showAddField() {
    this.currentField = {
      name: '',
      display_name: '',
      type: 'source',
      format: '',
      display: true
    };
    this.showFieldDialog = true;
  }

  showEditField(field, index) {
    this.currentField = { ...field, index };
    this.showFieldDialog = true;
  }

  closeFieldDialog() {
    this.showFieldDialog = false;
    this.currentField = null;
  }

  handleFieldTypeChange(type) {
    this.currentField = {
      ...this.currentField,
      type
    };
  }

  saveField() {
    // Generate a name if not provided
    if (!this.currentField.name) {
      this.currentField.name = this._generateFieldName(this.currentField);
    }
    
    // Generate display name if not provided
    if (!this.currentField.display_name) {
      this.currentField.display_name = this._formatDisplayName(this.currentField.name);
    }
    
    if (this.currentField.index !== undefined) {
      // Update existing field
      const fields = [...this.template.fields];
      fields[this.currentField.index] = this.currentField;
      this.template = {
        ...this.template,
        fields
      };
    } else {
      // Add new field
      this.template = {
        ...this.template,
        fields: [...this.template.fields, this.currentField]
      };
    }
    
    this.closeFieldDialog();
  }

  removeField(index) {
    const fields = [...this.template.fields];
    fields.splice(index, 1);
    
    this.template = {
      ...this.template,
      fields
    };
  }

  _generateFieldName(field) {
    let baseName = '';
    
    if (field.type === 'source' && field.source) {
      baseName = field.source.split('.').pop() || 'field';
    } else if (field.type === 'calculated') {
      baseName = 'calculated_field';
    } else if (field.type === 'parameter') {
      baseName = 'parameter';
    } else if (field.type === 'sql') {
      baseName = 'sql_field';
    } else {
      baseName = 'field';
    }
    
    // Check for uniqueness
    let name = baseName;
    let counter = 1;
    
    while (this.template.fields.some(f => f.name === name)) {
      name = `${baseName}_${counter}`;
      counter++;
    }
    
    return name;
  }

  _formatDisplayName(name) {
    return name
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  showAddTrigger() {
    this.currentTrigger = {
      type: 'schedule',
      name: 'New Schedule',
      schedule: {
        type: 'cron',
        expression: '0 0 * * *'  // Daily at midnight
      },
      enabled: true
    };
    this.showTriggerDialog = true;
  }

  closeTriggerDialog() {
    this.showTriggerDialog = false;
    this.currentTrigger = null;
  }

  saveTrigger() {
    if (this.currentTrigger.index !== undefined) {
      // Update existing trigger
      const triggers = [...this.template.triggers];
      triggers[this.currentTrigger.index] = this.currentTrigger;
      this.template = {
        ...this.template,
        triggers
      };
    } else {
      // Add new trigger
      this.template = {
        ...this.template,
        triggers: [...this.template.triggers, this.currentTrigger]
      };
    }
    
    this.closeTriggerDialog();
  }

  showAddOutput() {
    this.currentOutput = {
      type: 'pdf',
      name: 'PDF Output',
      config: {
        template_path: 'templates/default.html',
        paper_size: 'A4',
        orientation: 'portrait'
      }
    };
    this.showOutputDialog = true;
  }

  closeOutputDialog() {
    this.showOutputDialog = false;
    this.currentOutput = null;
  }

  saveOutput() {
    if (this.currentOutput.index !== undefined) {
      // Update existing output
      const outputs = [...this.template.outputs];
      outputs[this.currentOutput.index] = this.currentOutput;
      this.template = {
        ...this.template,
        outputs
      };
    } else {
      // Add new output
      this.template = {
        ...this.template,
        outputs: [...this.template.outputs, this.currentOutput]
      };
    }
    
    this.closeOutputDialog();
  }

  async saveTemplate() {
    if (!this.validateTemplate()) {
      return;
    }
    
    this.loading = true;
    
    try {
      const endpoint = this.mode === 'create' ? '/api/reports/templates' : `/api/reports/templates/${this.template.id}`;
      const method = this.mode === 'create' ? 'POST' : 'PUT';
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.template)
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const savedTemplate = await response.json();
      
      // Dispatch event
      this.dispatchEvent(new CustomEvent('template-saved', {
        detail: { template: savedTemplate }
      }));
      
      // Show success notification
      this._showNotification('Report template saved successfully', 'success');
      
      // Reset form if creating new template
      if (this.mode === 'create') {
        this.template = this._createEmptyTemplate();
      } else {
        this.template = savedTemplate;
      }
      
    } catch (err) {
      console.error('Failed to save template:', err);
      this.error = `Error saving template: ${err.message}`;
      this._showNotification(`Error saving template: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  validateTemplate() {
    // Basic validation
    if (!this.template.name) {
      this.error = 'Template name is required';
      this._showNotification('Template name is required', 'error');
      return false;
    }
    
    if (!this.template.entity_type) {
      this.error = 'Entity type is required';
      this._showNotification('Entity type is required', 'error');
      return false;
    }
    
    if (!this.template.fields.length) {
      this.error = 'At least one field is required';
      this._showNotification('At least one field is required', 'error');
      return false;
    }
    
    return true;
  }

  _showNotification(message, type = 'info') {
    // Create and show a notification
    const alertEl = document.createElement('wa-alert');
    alertEl.type = type;
    alertEl.message = message;
    alertEl.duration = 5000;
    alertEl.position = 'top-right';
    
    document.body.appendChild(alertEl);
    alertEl.show();
    
    alertEl.addEventListener('close', () => {
      document.body.removeChild(alertEl);
    });
  }

  handleTabChange(e) {
    this.activeTab = e.detail.value;
  }

  cancel() {
    this.dispatchEvent(new CustomEvent('cancel'));
  }

  renderFieldDialog() {
    if (!this.showFieldDialog) return html``;
    
    return html`
      <wa-dialog open @close=${this.closeFieldDialog}>
        <div slot="header">
          ${this.currentField.index !== undefined ? 'Edit Field' : 'Add Field'}
        </div>
        
        <div>
          <div class="field-type-options">
            <div 
              class="field-type-option ${this.currentField.type === 'source' ? 'selected' : ''}"
              @click=${() => this.handleFieldTypeChange('source')}>
              <wa-icon name="data_object" class="field-type-icon"></wa-icon>
              <div>Source Field</div>
              <small>Data from entity property</small>
            </div>
            
            <div 
              class="field-type-option ${this.currentField.type === 'calculated' ? 'selected' : ''}"
              @click=${() => this.handleFieldTypeChange('calculated')}>
              <wa-icon name="calculate" class="field-type-icon"></wa-icon>
              <div>Calculated Field</div>
              <small>Formula-based calculation</small>
            </div>
            
            <div 
              class="field-type-option ${this.currentField.type === 'parameter' ? 'selected' : ''}"
              @click=${() => this.handleFieldTypeChange('parameter')}>
              <wa-icon name="tune" class="field-type-icon"></wa-icon>
              <div>Parameter</div>
              <small>User-provided value</small>
            </div>
            
            <div 
              class="field-type-option ${this.currentField.type === 'sql' ? 'selected' : ''}"
              @click=${() => this.handleFieldTypeChange('sql')}>
              <wa-icon name="code" class="field-type-icon"></wa-icon>
              <div>SQL Query</div>
              <small>Custom SQL definition</small>
            </div>
          </div>
          
          <div class="form-row">
            <wa-input 
              label="Field Name" 
              .value=${this.currentField.name || ''}
              @input=${e => this.currentField = {...this.currentField, name: e.target.value}}
              helptext="Used as identifier in the system">
            </wa-input>
            
            <wa-input 
              label="Display Name" 
              .value=${this.currentField.display_name || ''}
              @input=${e => this.currentField = {...this.currentField, display_name: e.target.value}}
              helptext="Human-readable name shown in reports">
            </wa-input>
          </div>
          
          ${this.currentField.type === 'source' ? html`
            <wa-select 
              label="Source Field"
              .value=${this.currentField.source || ''}
              @change=${e => this.currentField = {...this.currentField, source: e.target.value}}
              helptext="Entity property path to source data from">
              <wa-option value="">Select a source field</wa-option>
              ${this.availableFields.map(field => html`
                <wa-option value="${field.path}">${field.name} (${field.path})</wa-option>
              `)}
            </wa-select>
          ` : ''}
          
          ${this.currentField.type === 'calculated' ? html`
            <div class="field-config-section">
              <wa-select 
                label="Calculation Type"
                .value=${this.currentField.calculation?.type || 'formula'}
                @change=${e => this.currentField = {
                  ...this.currentField, 
                  calculation: {...(this.currentField.calculation || {}), type: e.target.value}
                }}>
                <wa-option value="formula">Formula</wa-option>
                <wa-option value="aggregation">Aggregation</wa-option>
                <wa-option value="conditional">Conditional</wa-option>
              </wa-select>
              
              <wa-textarea 
                label="Expression"
                .value=${this.currentField.calculation?.expression || ''}
                @input=${e => this.currentField = {
                  ...this.currentField, 
                  calculation: {...(this.currentField.calculation || {}), expression: e.target.value}
                }}
                helptext="Reference other fields by name, e.g., total_revenue + tax">
              </wa-textarea>
              
              <div style="margin-top: 16px;">
                <label>Dependencies</label>
                <wa-select 
                  placeholder="Add dependency field"
                  @change=${e => {
                    if (!e.target.value) return;
                    const dependencies = this.currentField.calculation?.dependencies || [];
                    if (!dependencies.includes(e.target.value)) {
                      this.currentField = {
                        ...this.currentField, 
                        calculation: {
                          ...(this.currentField.calculation || {}), 
                          dependencies: [...dependencies, e.target.value]
                        }
                      };
                    }
                    e.target.value = '';
                  }}>
                  <wa-option value="">Select field...</wa-option>
                  ${this.template.fields.map(field => html`
                    <wa-option value="${field.name}">${field.display_name || field.name}</wa-option>
                  `)}
                </wa-select>
                
                <div style="margin-top: 12px;">
                  ${(this.currentField.calculation?.dependencies || []).map(dep => html`
                    <wa-chip
                      @remove=${() => {
                        const dependencies = (this.currentField.calculation?.dependencies || [])
                          .filter(d => d !== dep);
                        this.currentField = {
                          ...this.currentField, 
                          calculation: {...(this.currentField.calculation || {}), dependencies}
                        };
                      }}>
                      ${dep}
                    </wa-chip>
                  `)}
                </div>
              </div>
            </div>
          ` : ''}
          
          ${this.currentField.type === 'parameter' ? html`
            <div class="field-config-section">
              <wa-select 
                label="Parameter Type"
                .value=${this.currentField.parameter_type || 'string'}
                @change=${e => this.currentField = {...this.currentField, parameter_type: e.target.value}}>
                <wa-option value="string">String</wa-option>
                <wa-option value="number">Number</wa-option>
                <wa-option value="boolean">Boolean</wa-option>
                <wa-option value="date">Date</wa-option>
                <wa-option value="daterange">Date Range</wa-option>
                <wa-option value="enum">Enumeration</wa-option>
              </wa-select>
              
              <wa-input 
                label="Default Value"
                .value=${this.currentField.default || ''}
                @input=${e => this.currentField = {...this.currentField, default: e.target.value}}>
              </wa-input>
              
              <wa-checkbox
                label="Required"
                ?checked=${this.currentField.required}
                @change=${e => this.currentField = {...this.currentField, required: e.target.checked}}>
                This parameter is required
              </wa-checkbox>
            </div>
          ` : ''}
          
          ${this.currentField.type === 'sql' ? html`
            <div class="field-config-section">
              <wa-textarea 
                label="SQL Query"
                class="json-editor"
                .value=${this.currentField.sql_definition?.query || ''}
                @input=${e => this.currentField = {
                  ...this.currentField, 
                  sql_definition: {
                    ...(this.currentField.sql_definition || {}), 
                    query: e.target.value
                  }
                }}
                helptext="Use named parameters with colon prefix, e.g., :customer_id">
              </wa-textarea>
              
              <div style="margin-top: 16px;">
                <label>Query Parameters</label>
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                  <wa-input
                    placeholder="Parameter name"
                    .value=${this.currentField.newParameter || ''}
                    @input=${e => this.currentField = {...this.currentField, newParameter: e.target.value}}
                    @keydown=${e => {
                      if (e.key === 'Enter' && this.currentField.newParameter) {
                        const parameters = this.currentField.sql_definition?.parameters || [];
                        if (!parameters.includes(this.currentField.newParameter)) {
                          this.currentField = {
                            ...this.currentField, 
                            sql_definition: {
                              ...(this.currentField.sql_definition || {}), 
                              parameters: [...parameters, this.currentField.newParameter]
                            },
                            newParameter: ''
                          };
                        }
                      }
                    }}>
                  </wa-input>
                  <wa-button
                    @click=${() => {
                      if (!this.currentField.newParameter) return;
                      const parameters = this.currentField.sql_definition?.parameters || [];
                      if (!parameters.includes(this.currentField.newParameter)) {
                        this.currentField = {
                          ...this.currentField, 
                          sql_definition: {
                            ...(this.currentField.sql_definition || {}), 
                            parameters: [...parameters, this.currentField.newParameter]
                          },
                          newParameter: ''
                        };
                      }
                    }}>
                    Add
                  </wa-button>
                </div>
                
                <div style="margin-top: 12px;">
                  ${(this.currentField.sql_definition?.parameters || []).map(param => html`
                    <wa-chip
                      @remove=${() => {
                        const parameters = (this.currentField.sql_definition?.parameters || [])
                          .filter(p => p !== param);
                        this.currentField = {
                          ...this.currentField, 
                          sql_definition: {...(this.currentField.sql_definition || {}), parameters}
                        };
                      }}>
                      ${param}
                    </wa-chip>
                  `)}
                </div>
              </div>
            </div>
          ` : ''}
          
          <div class="form-row">
            <wa-select 
              label="Format"
              .value=${this.currentField.format || ''}
              @change=${e => this.currentField = {...this.currentField, format: e.target.value}}>
              <wa-option value="">No formatting</wa-option>
              <wa-option value="number">Number</wa-option>
              <wa-option value="currency">Currency</wa-option>
              <wa-option value="percentage">Percentage</wa-option>
              <wa-option value="date">Date</wa-option>
              <wa-option value="datetime">Date & Time</wa-option>
              <wa-option value="boolean">Boolean</wa-option>
              <wa-option value="json">JSON</wa-option>
            </wa-select>
            
            <div>
              <label>Display Options</label>
              <wa-checkbox
                label="Show in report output"
                ?checked=${this.currentField.display !== false}
                @change=${e => this.currentField = {...this.currentField, display: e.target.checked}}>
              </wa-checkbox>
            </div>
          </div>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeFieldDialog}>Cancel</wa-button>
          <wa-button @click=${this.saveField}>
            ${this.currentField.index !== undefined ? 'Update' : 'Add'} Field
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }

  renderDesignTab() {
    return html`
      <div class="form-row">
        <wa-input 
          label="Report Name" 
          required
          .value=${this.template.name || ''}
          @input=${this.handleNameChange}
          placeholder="e.g., Monthly Sales Report">
        </wa-input>
        
        <wa-select 
          label="Entity Type" 
          required
          .value=${this.template.entity_type || ''}
          @change=${this.handleEntityChange}>
          <wa-option value="">Select an entity type</wa-option>
          ${this.availableEntities.map(entity => html`
            <wa-option value="${entity.value}">${entity.label}</wa-option>
          `)}
        </wa-select>
      </div>
      
      <wa-textarea 
        label="Description"
        .value=${this.template.description || ''}
        @input=${this.handleDescriptionChange}
        placeholder="Describe the purpose and content of this report">
      </wa-textarea>
      
      <div class="section-title">Fields</div>
      
      ${this.template.fields.length === 0 ? html`
        <div class="empty-list">
          <wa-icon name="list_alt" size="large" style="margin-bottom: 12px;"></wa-icon>
          <div>No fields added yet. Click "Add Field" to start building your report.</div>
        </div>
      ` : html`
        <wa-card elevation="0" class="field-list">
          <wa-list>
            ${repeat(this.template.fields, (_, index) => index, (field, index) => html`
              <wa-list-item>
                <div slot="title">${field.display_name || field.name}</div>
                <div slot="description">
                  ${field.type === 'source' ? `Source: ${field.source}` : ''}
                  ${field.type === 'calculated' ? 'Calculated field' : ''}
                  ${field.type === 'parameter' ? `Parameter (${field.parameter_type})` : ''}
                  ${field.type === 'sql' ? 'SQL Query' : ''}
                  ${field.format ? ` • Format: ${field.format}` : ''}
                  ${field.display === false ? ' • Hidden' : ''}
                </div>
                <div slot="trailing">
                  <wa-button variant="text" @click=${() => this.showEditField(field, index)}>Edit</wa-button>
                  <wa-button variant="text" color="error" @click=${() => this.removeField(index)}>Remove</wa-button>
                </div>
              </wa-list-item>
              ${index < this.template.fields.length - 1 ? html`<wa-divider></wa-divider>` : ''}
            `)}
          </wa-list>
        </wa-card>
      `}
      
      <div style="margin-top: 16px;">
        <wa-button @click=${this.showAddField}>Add Field</wa-button>
      </div>
    `;
  }

  renderTriggersTab() {
    return html`
      <div class="section-title">Triggers</div>
      
      ${this.template.triggers.length === 0 ? html`
        <div class="empty-list">
          <wa-icon name="schedule" size="large" style="margin-bottom: 12px;"></wa-icon>
          <div>No triggers configured yet. Add a trigger to control when this report runs.</div>
        </div>
      ` : html`
        <wa-card elevation="0" class="field-list">
          <wa-list>
            ${repeat(this.template.triggers, (_, index) => index, (trigger, index) => html`
              <wa-list-item>
                <div slot="title">
                  ${trigger.name}
                  <wa-chip size="small" color=${trigger.enabled ? 'success' : 'default'}>
                    ${trigger.enabled ? 'Enabled' : 'Disabled'}
                  </wa-chip>
                </div>
                <div slot="description">
                  <wa-chip 
                    size="small" 
                    color=${
                      trigger.type === 'schedule' ? 'primary' : 
                      trigger.type === 'event' ? 'warning' : 
                      trigger.type === 'api' ? 'info' : 
                      'default'
                    }>
                    ${trigger.type}
                  </wa-chip>
                  ${trigger.type === 'schedule' && trigger.schedule ? 
                    `Schedule: ${trigger.schedule.expression}` : ''}
                  ${trigger.type === 'event' && trigger.event_type ? 
                    `Event: ${trigger.event_type}` : ''}
                </div>
                <div slot="trailing">
                  <wa-button variant="text" color="error" @click=${() => {
                    const triggers = [...this.template.triggers];
                    triggers.splice(index, 1);
                    this.template = { ...this.template, triggers };
                  }}>Remove</wa-button>
                </div>
              </wa-list-item>
              ${index < this.template.triggers.length - 1 ? html`<wa-divider></wa-divider>` : ''}
            `)}
          </wa-list>
        </wa-card>
      `}
      
      <div style="margin-top: 16px;">
        <wa-button @click=${this.showAddTrigger}>Add Trigger</wa-button>
      </div>
    `;
  }

  renderOutputsTab() {
    return html`
      <div class="section-title">Outputs</div>
      
      ${this.template.outputs.length === 0 ? html`
        <div class="empty-list">
          <wa-icon name="description" size="large" style="margin-bottom: 12px;"></wa-icon>
          <div>No outputs configured yet. Add an output to define how report results are delivered.</div>
        </div>
      ` : html`
        <wa-card elevation="0" class="field-list">
          <wa-list>
            ${repeat(this.template.outputs, (_, index) => index, (output, index) => html`
              <wa-list-item>
                <div slot="title">${output.name}</div>
                <div slot="description">
                  <wa-chip 
                    size="small" 
                    color=${
                      output.type === 'pdf' ? 'error' : 
                      output.type === 'email' ? 'success' : 
                      output.type === 'webhook' ? 'warning' : 
                      output.type === 'excel' ? 'primary' : 
                      'default'
                    }>
                    ${output.type}
                  </wa-chip>
                  ${output.type === 'pdf' && output.config ? 
                    `Template: ${output.config.template_path || 'Default'}` : ''}
                  ${output.type === 'email' && output.config && output.config.recipients ? 
                    `Recipients: ${output.config.recipients.join(', ')}` : ''}
                </div>
                <div slot="trailing">
                  <wa-button variant="text" color="error" @click=${() => {
                    const outputs = [...this.template.outputs];
                    outputs.splice(index, 1);
                    this.template = { ...this.template, outputs };
                  }}>Remove</wa-button>
                </div>
              </wa-list-item>
              ${index < this.template.outputs.length - 1 ? html`<wa-divider></wa-divider>` : ''}
            `)}
          </wa-list>
        </wa-card>
      `}
      
      <div style="margin-top: 16px;">
        <wa-button @click=${this.showAddOutput}>Add Output</wa-button>
      </div>
    `;
  }

  render() {
    return html`
      <div class="builder-container">
        <div class="builder-header">
          <h1 class="builder-title">${this.mode === 'create' ? 'Create New Report' : 'Edit Report'}</h1>
          <p class="builder-subtitle">Define the structure and behavior of your report</p>
        </div>
        
        ${this.error ? html`
          <wa-alert type="error" style="margin-bottom: 20px;">
            ${this.error}
          </wa-alert>
        ` : ''}
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="design">Design</wa-tab>
          <wa-tab value="triggers">Triggers</wa-tab>
          <wa-tab value="outputs">Outputs</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="design" ?active=${this.activeTab === 'design'}>
          ${this.renderDesignTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="triggers" ?active=${this.activeTab === 'triggers'}>
          ${this.renderTriggersTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="outputs" ?active=${this.activeTab === 'outputs'}>
          ${this.renderOutputsTab()}
        </wa-tab-panel>
        
        <div class="actions">
          <wa-button variant="outlined" @click=${this.cancel}>Cancel</wa-button>
          <wa-button @click=${this.saveTemplate}>
            ${this.mode === 'create' ? 'Create' : 'Save'} Report
          </wa-button>
        </div>
        
        ${this.renderFieldDialog()}
        
        ${this.loading ? html`
          <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                      background: rgba(255, 255, 255, 0.7); display: flex; 
                      align-items: center; justify-content: center; z-index: 9999;">
            <wa-spinner size="large"></wa-spinner>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('wa-report-builder', WebAwesomeReportBuilder);