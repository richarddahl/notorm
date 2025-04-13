import { LitElement, html, css } from 'lit-element';

/**
 * @element report-builder
 * @description An interactive report builder for creating custom report templates
 * @property {Object} template - The report template being edited
 * @property {Array} availableEntities - List of available entity types
 * @property {Array} availableFields - List of available fields for the selected entity
 * @property {Boolean} loading - Loading state
 * @property {String} error - Error message if loading failed
 */
export class ReportBuilder extends LitElement {
  static get properties() {
    return {
      template: { type: Object },
      availableEntities: { type: Array },
      availableFields: { type: Array },
      selectedFields: { type: Array },
      entityFields: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      mode: { type: String },
      showFieldConfig: { type: Boolean },
      currentField: { type: Object },
      previewData: { type: Object },
      activeTab: { type: String },
      triggerConfig: { type: Object },
      outputConfig: { type: Object },
      availableTriggerTypes: { type: Array },
      availableOutputTypes: { type: Array }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        font-family: var(--system-font, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif);
        --primary-color: #4285f4;
        --primary-color-dark: #3367d6;
      }
      .builder-container {
        padding: 20px;
        max-width: 1200px;
        margin: 0 auto;
      }
      .tabs {
        display: flex;
        border-bottom: 1px solid #ddd;
        margin-bottom: 20px;
      }
      .tab {
        padding: 10px 20px;
        cursor: pointer;
        border: 1px solid transparent;
        border-bottom: none;
        border-radius: 4px 4px 0 0;
        margin-right: 5px;
      }
      .tab.active {
        border-color: #ddd;
        background-color: white;
        border-bottom: 1px solid white;
        margin-bottom: -1px;
      }
      .tab:hover:not(.active) {
        background-color: #f5f5f5;
      }
      .tab-content {
        display: none;
      }
      .tab-content.active {
        display: block;
      }
      .form-group {
        margin-bottom: 16px;
      }
      .form-row {
        display: flex;
        gap: 20px;
        margin-bottom: 16px;
      }
      .form-row > div {
        flex: 1;
      }
      label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
      }
      input, select, textarea {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
      }
      textarea {
        min-height: 100px;
        font-family: inherit;
      }
      .actions {
        display: flex;
        justify-content: space-between;
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #eee;
      }
      button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 14px;
      }
      button:hover {
        background-color: var(--primary-color-dark);
      }
      button.secondary {
        background-color: #f1f3f4;
        color: #444;
      }
      button.secondary:hover {
        background-color: #e8eaed;
      }
      button.danger {
        background-color: #ea4335;
      }
      button.danger:hover {
        background-color: #d93025;
      }
      .field-list {
        border: 1px solid #ddd;
        border-radius: 4px;
        max-height: 400px;
        overflow-y: auto;
      }
      .field-item {
        padding: 12px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .field-item:last-child {
        border-bottom: none;
      }
      .field-item:hover {
        background-color: #f8f9fa;
      }
      .field-actions {
        display: flex;
        gap: 8px;
      }
      .field-actions button {
        padding: 4px 8px;
        font-size: 12px;
      }
      .field-dialog {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
      }
      .field-dialog-content {
        background-color: white;
        border-radius: 4px;
        width: 600px;
        max-width: 90%;
        padding: 20px;
        max-height: 90vh;
        overflow-y: auto;
      }
      .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
      }
      .dialog-header h3 {
        margin: 0;
      }
      .close-button {
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        color: #666;
      }
      .dialog-footer {
        margin-top: 20px;
        text-align: right;
      }
      .field-type-selector {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
      }
      .field-type-option {
        flex: 1;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 12px;
        cursor: pointer;
        text-align: center;
      }
      .field-type-option:hover {
        background-color: #f8f9fa;
      }
      .field-type-option.selected {
        border-color: var(--primary-color);
        background-color: rgba(66, 133, 244, 0.1);
      }
      .field-type-icon {
        font-size: 24px;
        margin-bottom: 8px;
      }
      .section-title {
        font-size: 18px;
        font-weight: 600;
        margin: 24px 0 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #eee;
      }
      .preview-container {
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 20px;
        margin-top: 20px;
      }
      .error {
        color: #d32f2f;
        padding: 12px;
        background-color: #ffebee;
        border-radius: 4px;
        margin-bottom: 16px;
      }
      .info-message {
        background-color: #e3f2fd;
        border-left: 4px solid var(--primary-color);
        padding: 12px;
        margin-bottom: 16px;
        border-radius: 0 4px 4px 0;
      }
      .trigger-item, .output-item {
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-bottom: 12px;
        background-color: #f8f9fa;
      }
      .trigger-header, .output-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
      }
      .trigger-title, .output-title {
        font-weight: 600;
      }
      .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        background-color: #e0e0e0;
        margin-left: 8px;
      }
      .badge.schedule {
        background-color: #c8e6c9;
        color: #2e7d32;
      }
      .badge.event {
        background-color: #ffecb3;
        color: #ff8f00;
      }
      .badge.api {
        background-color: #bbdefb;
        color: #1976d2;
      }
      .badge.query {
        background-color: #e1bee7;
        color: #7b1fa2;
      }
      .badge.pdf {
        background-color: #ffcdd2;
        color: #c62828;
      }
      .badge.email {
        background-color: #dcedc8;
        color: #33691e;
      }
      .badge.excel {
        background-color: #c8e6c9;
        color: #1b5e20;
      }
      .badge.webhook {
        background-color: #d1c4e9;
        color: #4527a0;
      }
      .drag-handle {
        cursor: move;
        color: #999;
        margin-right: 8px;
      }
      .placeholder-text {
        text-align: center;
        padding: 30px;
        color: #999;
      }
      .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
      }
      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 3px solid rgba(66, 133, 244, 0.3);
        border-radius: 50%;
        border-top-color: var(--primary-color);
        animation: spin 1s ease-in-out infinite;
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      .field-search {
        margin-bottom: 12px;
      }
      .parameter-list {
        margin-top: 12px;
      }
      .parameter-item {
        display: flex;
        gap: 10px;
        align-items: center;
        margin-bottom: 8px;
      }
      .parameter-item button {
        padding: 4px 8px;
        font-size: 12px;
      }
      .json-editor {
        font-family: monospace;
        height: 200px;
        width: 100%;
        background-color: #f8f9fa;
      }
    `;
  }

  constructor() {
    super();
    this.template = this._createEmptyTemplate();
    this.availableEntities = [];
    this.availableFields = [];
    this.selectedFields = [];
    this.entityFields = {};
    this.loading = false;
    this.error = null;
    this.mode = 'create';
    this.showFieldConfig = false;
    this.currentField = null;
    this.previewData = null;
    this.activeTab = 'design';
    this.triggerConfig = { type: 'schedule' };
    this.outputConfig = { type: 'pdf' };
    
    this.availableTriggerTypes = [
      { value: 'schedule', label: 'Schedule', description: 'Run report on a scheduled basis' },
      { value: 'event', label: 'Event', description: 'Run report when a specific event occurs' },
      { value: 'api', label: 'API', description: 'Run report on-demand via API' },
      { value: 'query', label: 'Query', description: 'Run report when a query returns results' }
    ];
    
    this.availableOutputTypes = [
      { value: 'pdf', label: 'PDF', description: 'Generate PDF document' },
      { value: 'excel', label: 'Excel', description: 'Generate Excel spreadsheet' },
      { value: 'email', label: 'Email', description: 'Send report via email' },
      { value: 'webhook', label: 'Webhook', description: 'Send report data to a webhook URL' },
      { value: 'dashboard', label: 'Dashboard', description: 'Display report on a dashboard' }
    ];
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
  
  connectedCallback() {
    super.connectedCallback();
    this.loadEntities();
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
    
    if (this.entityFields[entityType]) {
      this.availableFields = this.entityFields[entityType];
      return;
    }
    
    this.loading = true;
    
    try {
      const response = await fetch(`/api/reports/entities/${entityType}/fields`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const fields = await response.json();
      this.entityFields[entityType] = fields;
      this.availableFields = fields;
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
    this.selectedFields = [];
    
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

  showAddFieldDialog() {
    this.currentField = {
      name: '',
      source: '',
      display_name: '',
      type: 'source',
      format: '',
      display: true
    };
    this.showFieldConfig = true;
  }

  showEditFieldDialog(field, index) {
    this.currentField = { ...field, index };
    this.showFieldConfig = true;
  }

  closeFieldDialog() {
    this.showFieldConfig = false;
    this.currentField = null;
  }

  addField(field) {
    // Generate a unique name if not provided
    if (!field.name) {
      field.name = this._generateFieldName(field);
    }
    
    // Generate display name if not provided
    if (!field.display_name) {
      field.display_name = this._formatDisplayName(field.name);
    }
    
    this.template = {
      ...this.template,
      fields: [...this.template.fields, field]
    };
    
    this.closeFieldDialog();
  }

  updateField(field, index) {
    const fields = [...this.template.fields];
    fields[index] = field;
    
    this.template = {
      ...this.template,
      fields
    };
    
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

  handleFieldTypeChange(type) {
    this.currentField = {
      ...this.currentField,
      type
    };
  }

  handleFieldSourceChange(e) {
    this.currentField = {
      ...this.currentField,
      source: e.target.value
    };
  }

  handleFieldNameChange(e) {
    this.currentField = {
      ...this.currentField,
      name: e.target.value
    };
  }

  handleFieldDisplayNameChange(e) {
    this.currentField = {
      ...this.currentField,
      display_name: e.target.value
    };
  }

  handleFieldFormatChange(e) {
    this.currentField = {
      ...this.currentField,
      format: e.target.value
    };
  }

  handleFieldDisplayChange(e) {
    this.currentField = {
      ...this.currentField,
      display: e.target.checked
    };
  }

  saveField() {
    if (this.currentField.index !== undefined) {
      this.updateField(this.currentField, this.currentField.index);
    } else {
      this.addField(this.currentField);
    }
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
      
      // Reset form if creating new template
      if (this.mode === 'create') {
        this.template = this._createEmptyTemplate();
        this.selectedFields = [];
      } else {
        this.template = savedTemplate;
      }
      
    } catch (err) {
      console.error('Failed to save template:', err);
      this.error = `Error saving template: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  validateTemplate() {
    // Basic validation
    if (!this.template.name) {
      this.error = 'Template name is required';
      return false;
    }
    
    if (!this.template.entity_type) {
      this.error = 'Entity type is required';
      return false;
    }
    
    if (!this.template.fields.length) {
      this.error = 'At least one field is required';
      return false;
    }
    
    return true;
  }

  handleTabChange(tab) {
    this.activeTab = tab;
  }

  addTrigger() {
    // Initialize trigger based on type
    let trigger = {
      type: this.triggerConfig.type,
      name: this.triggerConfig.name || `${this.triggerConfig.type} Trigger`,
      enabled: true
    };
    
    switch (this.triggerConfig.type) {
      case 'schedule':
        trigger.schedule = {
          type: this.triggerConfig.scheduleType || 'cron',
          expression: this.triggerConfig.cronExpression || '0 0 * * *'
        };
        break;
      case 'event':
        trigger.event_type = this.triggerConfig.eventType || '';
        if (this.triggerConfig.eventFilter) {
          trigger.event_filter = JSON.parse(this.triggerConfig.eventFilter);
        }
        break;
      case 'query':
        if (this.triggerConfig.queryDefinition) {
          trigger.query_definition = JSON.parse(this.triggerConfig.queryDefinition);
        }
        trigger.check_interval = this.triggerConfig.checkInterval || 3600;
        break;
      case 'api':
        trigger.required_parameters = this.triggerConfig.requiredParameters || [];
        break;
    }
    
    this.template = {
      ...this.template,
      triggers: [...this.template.triggers, trigger]
    };
    
    // Reset trigger config
    this.triggerConfig = { type: 'schedule' };
  }

  removeTrigger(index) {
    const triggers = [...this.template.triggers];
    triggers.splice(index, 1);
    
    this.template = {
      ...this.template,
      triggers
    };
  }

  addOutput() {
    // Initialize output based on type
    let output = {
      type: this.outputConfig.type,
      name: this.outputConfig.name || `${this.outputConfig.type} Output`,
      config: {}
    };
    
    switch (this.outputConfig.type) {
      case 'pdf':
        output.config = {
          template_path: this.outputConfig.templatePath || '',
          paper_size: this.outputConfig.paperSize || 'A4',
          orientation: this.outputConfig.orientation || 'portrait'
        };
        break;
      case 'excel':
        output.config = {
          sheet_name: this.outputConfig.sheetName || 'Report',
          include_headers: this.outputConfig.includeHeaders !== false
        };
        break;
      case 'email':
        output.config = {
          recipients: this.outputConfig.recipients ? this.outputConfig.recipients.split(',').map(r => r.trim()) : [],
          subject: this.outputConfig.subject || '{{template.name}} Report',
          template_path: this.outputConfig.emailTemplatePath || '',
          include_attachments: this.outputConfig.includeAttachments || false,
          attachment_formats: this.outputConfig.attachmentFormats || []
        };
        break;
      case 'webhook':
        output.config = {
          url: this.outputConfig.webhookUrl || '',
          method: this.outputConfig.webhookMethod || 'POST',
          headers: this.outputConfig.webhookHeaders ? JSON.parse(this.outputConfig.webhookHeaders) : {}
        };
        break;
      case 'dashboard':
        output.config = {
          layout: this.outputConfig.dashboardLayout ? JSON.parse(this.outputConfig.dashboardLayout) : []
        };
        break;
    }
    
    this.template = {
      ...this.template,
      outputs: [...this.template.outputs, output]
    };
    
    // Reset output config
    this.outputConfig = { type: 'pdf' };
  }

  removeOutput(index) {
    const outputs = [...this.template.outputs];
    outputs.splice(index, 1);
    
    this.template = {
      ...this.template,
      outputs
    };
  }

  handleTriggerTypeChange(e) {
    this.triggerConfig = {
      ...this.triggerConfig,
      type: e.target.value
    };
  }

  handleOutputTypeChange(e) {
    this.outputConfig = {
      ...this.outputConfig,
      type: e.target.value
    };
  }

  handleTriggerConfigChange(e) {
    const { name, value } = e.target;
    this.triggerConfig = {
      ...this.triggerConfig,
      [name]: value
    };
  }

  handleOutputConfigChange(e) {
    const { name, value } = e.target;
    this.outputConfig = {
      ...this.outputConfig,
      [name]: value
    };
  }

  addRequiredParameter() {
    if (!this.triggerConfig.newParameter) return;
    
    const requiredParameters = this.triggerConfig.requiredParameters || [];
    
    if (!requiredParameters.includes(this.triggerConfig.newParameter)) {
      this.triggerConfig = {
        ...this.triggerConfig,
        requiredParameters: [...requiredParameters, this.triggerConfig.newParameter],
        newParameter: ''
      };
    }
  }

  removeRequiredParameter(param) {
    const requiredParameters = this.triggerConfig.requiredParameters || [];
    
    this.triggerConfig = {
      ...this.triggerConfig,
      requiredParameters: requiredParameters.filter(p => p !== param)
    };
  }

  addAttachmentFormat() {
    if (!this.outputConfig.newFormat) return;
    
    const attachmentFormats = this.outputConfig.attachmentFormats || [];
    
    if (!attachmentFormats.includes(this.outputConfig.newFormat)) {
      this.outputConfig = {
        ...this.outputConfig,
        attachmentFormats: [...attachmentFormats, this.outputConfig.newFormat],
        newFormat: ''
      };
    }
  }

  removeAttachmentFormat(format) {
    const attachmentFormats = this.outputConfig.attachmentFormats || [];
    
    this.outputConfig = {
      ...this.outputConfig,
      attachmentFormats: attachmentFormats.filter(f => f !== format)
    };
  }

  async generatePreview() {
    if (!this.validateTemplate()) {
      return;
    }
    
    this.loading = true;
    
    try {
      const response = await fetch('/api/reports/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.template)
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.previewData = await response.json();
      this.activeTab = 'preview';
    } catch (err) {
      console.error('Failed to generate preview:', err);
      this.error = `Error generating preview: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  cancel() {
    this.dispatchEvent(new CustomEvent('cancel'));
  }

  renderFieldDialog() {
    if (!this.showFieldConfig) return html``;
    
    return html`
      <div class="field-dialog">
        <div class="field-dialog-content">
          <div class="dialog-header">
            <h3>${this.currentField.index !== undefined ? 'Edit Field' : 'Add Field'}</h3>
            <button class="close-button" @click=${this.closeFieldDialog}>&times;</button>
          </div>
          
          <div class="field-type-selector">
            <div class="field-type-option ${this.currentField.type === 'source' ? 'selected' : ''}"
                 @click=${() => this.handleFieldTypeChange('source')}>
              <div class="field-type-icon">📊</div>
              <div>Source Field</div>
              <small>Data from entity property</small>
            </div>
            
            <div class="field-type-option ${this.currentField.type === 'calculated' ? 'selected' : ''}"
                 @click=${() => this.handleFieldTypeChange('calculated')}>
              <div class="field-type-icon">🧮</div>
              <div>Calculated Field</div>
              <small>Formula-based calculation</small>
            </div>
            
            <div class="field-type-option ${this.currentField.type === 'parameter' ? 'selected' : ''}"
                 @click=${() => this.handleFieldTypeChange('parameter')}>
              <div class="field-type-icon">🎛️</div>
              <div>Parameter</div>
              <small>User-provided value</small>
            </div>
            
            <div class="field-type-option ${this.currentField.type === 'sql' ? 'selected' : ''}"
                 @click=${() => this.handleFieldTypeChange('sql')}>
              <div class="field-type-icon">📝</div>
              <div>SQL Query</div>
              <small>Custom SQL definition</small>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="field-name">Field Name</label>
              <input type="text" id="field-name" .value=${this.currentField.name || ''}
                    @input=${this.handleFieldNameChange} placeholder="e.g., total_sales">
              <small>Used as identifier in the system</small>
            </div>
            
            <div class="form-group">
              <label for="field-display-name">Display Name</label>
              <input type="text" id="field-display-name" .value=${this.currentField.display_name || ''}
                    @input=${this.handleFieldDisplayNameChange} placeholder="e.g., Total Sales">
              <small>Human-readable name shown in reports</small>
            </div>
          </div>
          
          ${this.currentField.type === 'source' ? html`
            <div class="form-group">
              <label for="field-source">Source</label>
              <select id="field-source" .value=${this.currentField.source || ''}
                      @change=${this.handleFieldSourceChange}>
                <option value="">Select a source field</option>
                ${this.availableFields.map(field => html`
                  <option value="${field.path}">${field.name} (${field.path})</option>
                `)}
              </select>
              <small>Entity property path to source data from</small>
            </div>
          ` : ''}
          
          ${this.currentField.type === 'calculated' ? html`
            <div class="form-group">
              <label for="calculation-type">Calculation Type</label>
              <select id="calculation-type" .value=${this.currentField.calculation?.type || 'formula'}
                      @change=${e => this.currentField = {...this.currentField, calculation: {...(this.currentField.calculation || {}), type: e.target.value}}}>
                <option value="formula">Formula</option>
                <option value="aggregation">Aggregation</option>
                <option value="conditional">Conditional</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="calculation-expression">Expression</label>
              <textarea id="calculation-expression" 
                       .value=${this.currentField.calculation?.expression || ''}
                       @input=${e => this.currentField = {...this.currentField, calculation: {...(this.currentField.calculation || {}), expression: e.target.value}}}
                       placeholder="Enter formula expression, e.g.: total_revenue - total_cost"></textarea>
              <small>Reference other fields by name, e.g., total_revenue + tax</small>
            </div>
            
            <div class="form-group">
              <label>Dependencies</label>
              <div class="field-search">
                <select @change=${e => {
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
                  <option value="">Add dependency field...</option>
                  ${this.template.fields.map(field => html`
                    <option value="${field.name}">${field.display_name || field.name}</option>
                  `)}
                </select>
              </div>
              
              <div class="parameter-list">
                ${(this.currentField.calculation?.dependencies || []).map(dep => html`
                  <div class="parameter-item">
                    <span>${dep}</span>
                    <button class="secondary" @click=${() => {
                      const dependencies = (this.currentField.calculation?.dependencies || []).filter(d => d !== dep);
                      this.currentField = {
                        ...this.currentField, 
                        calculation: {...(this.currentField.calculation || {}), dependencies}
                      };
                    }}>Remove</button>
                  </div>
                `)}
              </div>
            </div>
          ` : ''}
          
          ${this.currentField.type === 'parameter' ? html`
            <div class="form-group">
              <label for="parameter-type">Parameter Type</label>
              <select id="parameter-type" .value=${this.currentField.parameter_type || 'string'}
                      @change=${e => this.currentField = {...this.currentField, parameter_type: e.target.value}}>
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
                <option value="date">Date</option>
                <option value="daterange">Date Range</option>
                <option value="enum">Enumeration</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="parameter-default">Default Value</label>
              <input type="text" id="parameter-default" .value=${this.currentField.default || ''}
                     @input=${e => this.currentField = {...this.currentField, default: e.target.value}}
                     placeholder="Default value">
            </div>
            
            <div class="form-group">
              <label for="parameter-required">Required</label>
              <input type="checkbox" id="parameter-required" 
                     ?checked=${this.currentField.required}
                     @change=${e => this.currentField = {...this.currentField, required: e.target.checked}}>
              <span>This parameter is required</span>
            </div>
            
            ${this.currentField.parameter_type === 'enum' ? html`
              <div class="form-group">
                <label>Enum Values</label>
                <div class="field-search">
                  <div class="form-row">
                    <input type="text" id="enum-value" placeholder="Value"
                           .value=${this.currentField.newEnumValue || ''}
                           @input=${e => this.currentField = {...this.currentField, newEnumValue: e.target.value}}>
                    <input type="text" id="enum-label" placeholder="Label"
                           .value=${this.currentField.newEnumLabel || ''}
                           @input=${e => this.currentField = {...this.currentField, newEnumLabel: e.target.value}}>
                    <button @click=${() => {
                      if (!this.currentField.newEnumValue) return;
                      const values = this.currentField.enum_values || [];
                      this.currentField = {
                        ...this.currentField,
                        enum_values: [...values, {
                          value: this.currentField.newEnumValue,
                          label: this.currentField.newEnumLabel || this.currentField.newEnumValue
                        }],
                        newEnumValue: '',
                        newEnumLabel: ''
                      };
                    }}>Add</button>
                  </div>
                </div>
                
                <div class="parameter-list">
                  ${(this.currentField.enum_values || []).map((item, idx) => html`
                    <div class="parameter-item">
                      <span>${item.label} (${item.value})</span>
                      <button class="secondary" @click=${() => {
                        const values = [...(this.currentField.enum_values || [])];
                        values.splice(idx, 1);
                        this.currentField = {...this.currentField, enum_values: values};
                      }}>Remove</button>
                    </div>
                  `)}
                </div>
              </div>
            ` : ''}
          ` : ''}
          
          ${this.currentField.type === 'sql' ? html`
            <div class="form-group">
              <label for="sql-query">SQL Query</label>
              <textarea id="sql-query" class="json-editor"
                       .value=${this.currentField.sql_definition?.query || ''}
                       @input=${e => this.currentField = {
                         ...this.currentField, 
                         sql_definition: {
                           ...(this.currentField.sql_definition || {}), 
                           query: e.target.value
                         }
                       }}
                       placeholder="SELECT column FROM table WHERE condition = :parameter"></textarea>
              <small>Use named parameters with colon prefix, e.g., :customer_id</small>
            </div>
            
            <div class="form-group">
              <label>Query Parameters</label>
              <div class="field-search">
                <input type="text" id="new-parameter" placeholder="Add parameter"
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
                <button @click=${() => {
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
                }}>Add</button>
              </div>
              
              <div class="parameter-list">
                ${(this.currentField.sql_definition?.parameters || []).map(param => html`
                  <div class="parameter-item">
                    <span>${param}</span>
                    <button class="secondary" @click=${() => {
                      const parameters = (this.currentField.sql_definition?.parameters || []).filter(p => p !== param);
                      this.currentField = {
                        ...this.currentField, 
                        sql_definition: {...(this.currentField.sql_definition || {}), parameters}
                      };
                    }}>Remove</button>
                  </div>
                `)}
              </div>
            </div>
          ` : ''}
          
          <div class="form-row">
            <div class="form-group">
              <label for="field-format">Format</label>
              <select id="field-format" .value=${this.currentField.format || ''}
                      @change=${this.handleFieldFormatChange}>
                <option value="">No formatting</option>
                <option value="number">Number</option>
                <option value="currency">Currency</option>
                <option value="percentage">Percentage</option>
                <option value="date">Date</option>
                <option value="datetime">Date & Time</option>
                <option value="boolean">Boolean</option>
                <option value="json">JSON</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Display Options</label>
              <div>
                <input type="checkbox" id="field-display" 
                       ?checked=${this.currentField.display !== false}
                       @change=${this.handleFieldDisplayChange}>
                <label for="field-display" style="display: inline;">Show in report output</label>
              </div>
            </div>
          </div>
          
          <div class="dialog-footer">
            <button class="secondary" @click=${this.closeFieldDialog}>Cancel</button>
            <button @click=${this.saveField}>
              ${this.currentField.index !== undefined ? 'Update' : 'Add'} Field
            </button>
          </div>
        </div>
      </div>
    `;
  }

  renderDesignTab() {
    return html`
      <div class="form-row">
        <div class="form-group">
          <label for="template-name">Report Name</label>
          <input type="text" id="template-name" .value=${this.template.name || ''}
                 @input=${this.handleNameChange} placeholder="e.g., Monthly Sales Report">
        </div>
        
        <div class="form-group">
          <label for="entity-type">Entity Type</label>
          <select id="entity-type" .value=${this.template.entity_type || ''}
                  @change=${this.handleEntityChange}>
            <option value="">Select an entity type</option>
            ${this.availableEntities.map(entity => html`
              <option value="${entity.value}">${entity.label}</option>
            `)}
          </select>
        </div>
      </div>
      
      <div class="form-group">
        <label for="template-description">Description</label>
        <textarea id="template-description" .value=${this.template.description || ''}
                 @input=${this.handleDescriptionChange} 
                 placeholder="Describe the purpose and content of this report"></textarea>
      </div>
      
      <div class="section-title">Fields</div>
      
      <div class="field-list">
        ${this.template.fields.length === 0 ? html`
          <div class="placeholder-text">
            No fields added yet. Click "Add Field" to start building your report.
          </div>
        ` : ''}
        
        ${this.template.fields.map((field, index) => html`
          <div class="field-item">
            <div>
              <strong>${field.display_name || field.name}</strong>
              <div>
                <small>
                  ${field.type === 'source' ? `Source: ${field.source}` : ''}
                  ${field.type === 'calculated' ? 'Calculated field' : ''}
                  ${field.type === 'parameter' ? `Parameter (${field.parameter_type})` : ''}
                  ${field.type === 'sql' ? 'SQL Query' : ''}
                  ${field.format ? ` • Format: ${field.format}` : ''}
                  ${field.display === false ? ' • Hidden' : ''}
                </small>
              </div>
            </div>
            <div class="field-actions">
              <button class="secondary" @click=${() => this.showEditFieldDialog(field, index)}>Edit</button>
              <button class="danger" @click=${() => this.removeField(index)}>Remove</button>
            </div>
          </div>
        `)}
      </div>
      
      <div style="margin-top: 16px;">
        <button @click=${this.showAddFieldDialog}>Add Field</button>
      </div>
    `;
  }

  renderTriggersTab() {
    return html`
      <div class="section-title">Existing Triggers</div>
      
      <div class="field-list">
        ${this.template.triggers.length === 0 ? html`
          <div class="placeholder-text">
            No triggers configured yet. Add a trigger to control when this report runs.
          </div>
        ` : ''}
        
        ${this.template.triggers.map((trigger, index) => html`
          <div class="trigger-item">
            <div class="trigger-header">
              <div>
                <span class="trigger-title">${trigger.name}</span>
                <span class="badge ${trigger.type}">${trigger.type}</span>
                ${trigger.enabled ? html`
                  <span class="badge">enabled</span>
                ` : html`
                  <span class="badge" style="background-color: #ffcdd2; color: #b71c1c;">disabled</span>
                `}
              </div>
              <div class="field-actions">
                <button class="danger" @click=${() => this.removeTrigger(index)}>Remove</button>
              </div>
            </div>
            <div>
              ${trigger.type === 'schedule' ? html`
                <div>Schedule: ${trigger.schedule.expression}</div>
              ` : ''}
              ${trigger.type === 'event' ? html`
                <div>Event Type: ${trigger.event_type}</div>
                ${trigger.event_filter ? html`
                  <div>Filter: ${JSON.stringify(trigger.event_filter)}</div>
                ` : ''}
              ` : ''}
              ${trigger.type === 'query' ? html`
                <div>Check Interval: ${trigger.check_interval} seconds</div>
              ` : ''}
              ${trigger.type === 'api' ? html`
                <div>Required Parameters: ${trigger.required_parameters.join(', ') || 'None'}</div>
              ` : ''}
            </div>
          </div>
        `)}
      </div>
      
      <div class="section-title">Add Trigger</div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="trigger-type">Trigger Type</label>
          <select id="trigger-type" .value=${this.triggerConfig.type || 'schedule'}
                  @change=${this.handleTriggerTypeChange}>
            ${this.availableTriggerTypes.map(type => html`
              <option value="${type.value}">${type.label}</option>
            `)}
          </select>
          <small>${this.availableTriggerTypes.find(t => t.value === this.triggerConfig.type)?.description}</small>
        </div>
        
        <div class="form-group">
          <label for="trigger-name">Trigger Name</label>
          <input type="text" id="trigger-name" name="name"
                 .value=${this.triggerConfig.name || ''}
                 @input=${this.handleTriggerConfigChange}
                 placeholder="e.g., Daily Execution">
        </div>
      </div>
      
      ${this.triggerConfig.type === 'schedule' ? html`
        <div class="form-row">
          <div class="form-group">
            <label for="schedule-type">Schedule Type</label>
            <select id="schedule-type" name="scheduleType"
                    .value=${this.triggerConfig.scheduleType || 'cron'}
                    @change=${this.handleTriggerConfigChange}>
              <option value="cron">Cron Expression</option>
              <option value="interval">Interval</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="cron-expression">Cron Expression</label>
            <input type="text" id="cron-expression" name="cronExpression"
                   .value=${this.triggerConfig.cronExpression || '0 0 * * *'}
                   @input=${this.handleTriggerConfigChange}
                   placeholder="e.g., 0 0 * * * (daily at midnight)">
            <small>Standard cron format: minute hour day month day-of-week</small>
          </div>
        </div>
      ` : ''}
      
      ${this.triggerConfig.type === 'event' ? html`
        <div class="form-row">
          <div class="form-group">
            <label for="event-type">Event Type</label>
            <input type="text" id="event-type" name="eventType"
                   .value=${this.triggerConfig.eventType || ''}
                   @input=${this.handleTriggerConfigChange}
                   placeholder="e.g., order.created">
          </div>
        </div>
        
        <div class="form-group">
          <label for="event-filter">Event Filter (JSON)</label>
          <textarea id="event-filter" class="json-editor" name="eventFilter"
                  .value=${this.triggerConfig.eventFilter || ''}
                  @input=${this.handleTriggerConfigChange}
                  placeholder='{"condition": "event.data.status === \"completed\""}'>
          </textarea>
          <small>JSON filter conditions to determine if the event should trigger the report</small>
        </div>
      ` : ''}
      
      ${this.triggerConfig.type === 'query' ? html`
        <div class="form-group">
          <label for="query-definition">Query Definition (JSON)</label>
          <textarea id="query-definition" class="json-editor" name="queryDefinition"
                  .value=${this.triggerConfig.queryDefinition || ''}
                  @input=${this.handleTriggerConfigChange}
                  placeholder='{"conditions": [{"field": "quantity", "operator": "lt", "value": 10}]}'>
          </textarea>
          <small>Query conditions that will trigger the report when matching records are found</small>
        </div>
        
        <div class="form-group">
          <label for="check-interval">Check Interval (seconds)</label>
          <input type="number" id="check-interval" name="checkInterval"
                 .value=${this.triggerConfig.checkInterval || 3600}
                 @input=${this.handleTriggerConfigChange}>
          <small>How often to check if the query conditions are met</small>
        </div>
      ` : ''}
      
      ${this.triggerConfig.type === 'api' ? html`
        <div class="form-group">
          <label>Required Parameters</label>
          <div class="field-search">
            <input type="text" id="new-parameter" name="newParameter"
                   .value=${this.triggerConfig.newParameter || ''}
                   @input=${this.handleTriggerConfigChange}
                   placeholder="Parameter name">
            <button @click=${this.addRequiredParameter}>Add</button>
          </div>
          
          <div class="parameter-list">
            ${(this.triggerConfig.requiredParameters || []).map(param => html`
              <div class="parameter-item">
                <span>${param}</span>
                <button class="secondary" @click=${() => this.removeRequiredParameter(param)}>Remove</button>
              </div>
            `)}
          </div>
        </div>
      ` : ''}
      
      <div style="margin-top: 16px;">
        <button @click=${this.addTrigger}>Add Trigger</button>
      </div>
    `;
  }

  renderOutputsTab() {
    return html`
      <div class="section-title">Existing Outputs</div>
      
      <div class="field-list">
        ${this.template.outputs.length === 0 ? html`
          <div class="placeholder-text">
            No outputs configured yet. Add an output to define how report results are delivered.
          </div>
        ` : ''}
        
        ${this.template.outputs.map((output, index) => html`
          <div class="output-item">
            <div class="output-header">
              <div>
                <span class="output-title">${output.name}</span>
                <span class="badge ${output.type}">${output.type}</span>
              </div>
              <div class="field-actions">
                <button class="danger" @click=${() => this.removeOutput(index)}>Remove</button>
              </div>
            </div>
            <div>
              ${output.type === 'pdf' ? html`
                <div>Template: ${output.config.template_path || 'Default template'}</div>
                <div>Paper: ${output.config.paper_size} (${output.config.orientation})</div>
              ` : ''}
              ${output.type === 'excel' ? html`
                <div>Sheet Name: ${output.config.sheet_name}</div>
                <div>Include Headers: ${output.config.include_headers ? 'Yes' : 'No'}</div>
              ` : ''}
              ${output.type === 'email' ? html`
                <div>Recipients: ${output.config.recipients.join(', ')}</div>
                <div>Subject: ${output.config.subject}</div>
                <div>Attachments: ${output.config.include_attachments ? 
                  output.config.attachment_formats.join(', ') : 'None'}</div>
              ` : ''}
              ${output.type === 'webhook' ? html`
                <div>URL: ${output.config.url}</div>
                <div>Method: ${output.config.method}</div>
              ` : ''}
              ${output.type === 'dashboard' ? html`
                <div>Widgets: ${output.config.layout.length}</div>
              ` : ''}
            </div>
          </div>
        `)}
      </div>
      
      <div class="section-title">Add Output</div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="output-type">Output Type</label>
          <select id="output-type" .value=${this.outputConfig.type || 'pdf'}
                  @change=${this.handleOutputTypeChange}>
            ${this.availableOutputTypes.map(type => html`
              <option value="${type.value}">${type.label}</option>
            `)}
          </select>
          <small>${this.availableOutputTypes.find(t => t.value === this.outputConfig.type)?.description}</small>
        </div>
        
        <div class="form-group">
          <label for="output-name">Output Name</label>
          <input type="text" id="output-name" name="name"
                 .value=${this.outputConfig.name || ''}
                 @input=${this.handleOutputConfigChange}
                 placeholder="e.g., PDF Report">
        </div>
      </div>
      
      ${this.outputConfig.type === 'pdf' ? html`
        <div class="form-row">
          <div class="form-group">
            <label for="template-path">Template Path</label>
            <input type="text" id="template-path" name="templatePath"
                   .value=${this.outputConfig.templatePath || ''}
                   @input=${this.handleOutputConfigChange}
                   placeholder="templates/report.html">
            <small>Path to HTML template for PDF rendering</small>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="paper-size">Paper Size</label>
            <select id="paper-size" name="paperSize"
                    .value=${this.outputConfig.paperSize || 'A4'}
                    @change=${this.handleOutputConfigChange}>
              <option value="A4">A4</option>
              <option value="Letter">Letter</option>
              <option value="Legal">Legal</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="orientation">Orientation</label>
            <select id="orientation" name="orientation"
                    .value=${this.outputConfig.orientation || 'portrait'}
                    @change=${this.handleOutputConfigChange}>
              <option value="portrait">Portrait</option>
              <option value="landscape">Landscape</option>
            </select>
          </div>
        </div>
      ` : ''}
      
      ${this.outputConfig.type === 'excel' ? html`
        <div class="form-row">
          <div class="form-group">
            <label for="sheet-name">Sheet Name</label>
            <input type="text" id="sheet-name" name="sheetName"
                   .value=${this.outputConfig.sheetName || 'Report'}
                   @input=${this.handleOutputConfigChange}>
          </div>
          
          <div class="form-group">
            <label>Options</label>
            <div>
              <input type="checkbox" id="include-headers" name="includeHeaders"
                     ?checked=${this.outputConfig.includeHeaders !== false}
                     @change=${e => this.outputConfig = {...this.outputConfig, includeHeaders: e.target.checked}}>
              <label for="include-headers" style="display: inline;">Include column headers</label>
            </div>
          </div>
        </div>
      ` : ''}
      
      ${this.outputConfig.type === 'email' ? html`
        <div class="form-group">
          <label for="recipients">Recipients (comma-separated)</label>
          <input type="text" id="recipients" name="recipients"
                 .value=${this.outputConfig.recipients || ''}
                 @input=${this.handleOutputConfigChange}
                 placeholder="user@example.com, {{customer.email}}">
          <small>Can include static emails or field references like {{user.email}}</small>
        </div>
        
        <div class="form-group">
          <label for="subject">Email Subject</label>
          <input type="text" id="subject" name="subject"
                 .value=${this.outputConfig.subject || ''}
                 @input=${this.handleOutputConfigChange}
                 placeholder="Your report is ready">
          <small>Can include template variables like {{report_name}}</small>
        </div>
        
        <div class="form-group">
          <label for="email-template-path">Email Template Path</label>
          <input type="text" id="email-template-path" name="emailTemplatePath"
                 .value=${this.outputConfig.emailTemplatePath || ''}
                 @input=${this.handleOutputConfigChange}
                 placeholder="templates/email.html">
        </div>
        
        <div class="form-group">
          <label>Include Attachments</label>
          <div>
            <input type="checkbox" id="include-attachments" name="includeAttachments"
                   ?checked=${this.outputConfig.includeAttachments}
                   @change=${e => this.outputConfig = {...this.outputConfig, includeAttachments: e.target.checked}}>
            <label for="include-attachments" style="display: inline;">Attach report files</label>
          </div>
          
          ${this.outputConfig.includeAttachments ? html`
            <div class="parameter-list">
              <div class="field-search" style="margin-top: 10px;">
                <select name="newFormat"
                       .value=${this.outputConfig.newFormat || ''}
                       @change=${this.handleOutputConfigChange}>
                  <option value="">Add attachment format...</option>
                  <option value="pdf">PDF</option>
                  <option value="xlsx">Excel</option>
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
                <button @click=${this.addAttachmentFormat}>Add</button>
              </div>
              
              ${(this.outputConfig.attachmentFormats || []).map(format => html`
                <div class="parameter-item">
                  <span>${format.toUpperCase()}</span>
                  <button class="secondary" @click=${() => this.removeAttachmentFormat(format)}>Remove</button>
                </div>
              `)}
            </div>
          ` : ''}
        </div>
      ` : ''}
      
      ${this.outputConfig.type === 'webhook' ? html`
        <div class="form-group">
          <label for="webhook-url">Webhook URL</label>
          <input type="text" id="webhook-url" name="webhookUrl"
                 .value=${this.outputConfig.webhookUrl || ''}
                 @input=${this.handleOutputConfigChange}
                 placeholder="https://example.com/webhook">
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="webhook-method">HTTP Method</label>
            <select id="webhook-method" name="webhookMethod"
                    .value=${this.outputConfig.webhookMethod || 'POST'}
                    @change=${this.handleOutputConfigChange}>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label for="webhook-headers">HTTP Headers (JSON)</label>
          <textarea id="webhook-headers" class="json-editor" name="webhookHeaders"
                   .value=${this.outputConfig.webhookHeaders || ''}
                   @input=${this.handleOutputConfigChange}
                   placeholder='{"Content-Type": "application/json", "Authorization": "Bearer {{api_key}}"}'>
          </textarea>
        </div>
      ` : ''}
      
      ${this.outputConfig.type === 'dashboard' ? html`
        <div class="form-group">
          <label for="dashboard-layout">Dashboard Layout (JSON)</label>
          <textarea id="dashboard-layout" class="json-editor" name="dashboardLayout"
                   .value=${this.outputConfig.dashboardLayout || ''}
                   @input=${this.handleOutputConfigChange}
                   placeholder='[{"widget": "chart", "type": "bar", "field": "sales_by_region", "width": 6, "height": 4}]'>
          </textarea>
          <small>Array of widget configurations for dashboard layout</small>
        </div>
      ` : ''}
      
      <div style="margin-top: 16px;">
        <button @click=${this.addOutput}>Add Output</button>
      </div>
    `;
  }

  renderPreviewTab() {
    if (!this.previewData) {
      return html`
        <div class="placeholder-text">
          <p>No preview data available. Click "Generate Preview" to preview this report.</p>
          <button @click=${this.generatePreview}>Generate Preview</button>
        </div>
      `;
    }
    
    return html`
      <div class="preview-container">
        <h3>Report Preview: ${this.template.name}</h3>
        
        <div class="section-title">Preview Data</div>
        <pre style="background-color: #f8f9fa; padding: 16px; border-radius: 4px; overflow: auto; max-height: 400px;">
          ${JSON.stringify(this.previewData, null, 2)}
        </pre>
        
        <div class="section-title">Sample Rendering</div>
        <div style="margin-top: 20px;">
          <table>
            <thead>
              <tr>
                ${this.template.fields
                  .filter(field => field.display !== false)
                  .map(field => html`<th>${field.display_name}</th>`)}
              </tr>
            </thead>
            <tbody>
              ${this.previewData && this.previewData.rows ? 
                this.previewData.rows.map(row => html`
                  <tr>
                    ${this.template.fields
                      .filter(field => field.display !== false)
                      .map(field => html`<td>${row[field.name] || ''}</td>`)}
                  </tr>
                `) : html`
                  <tr>
                    <td colspan="${this.template.fields.filter(field => field.display !== false).length}">
                      No preview data available
                    </td>
                  </tr>
                `}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  render() {
    return html`
      <div class="builder-container">
        <h2>${this.mode === 'create' ? 'Create New Report' : 'Edit Report'}</h2>
        
        ${this.error ? html`<div class="error">${this.error}</div>` : ''}
        
        <div class="tabs">
          <div class="tab ${this.activeTab === 'design' ? 'active' : ''}"
               @click=${() => this.handleTabChange('design')}>
            Design
          </div>
          <div class="tab ${this.activeTab === 'triggers' ? 'active' : ''}"
               @click=${() => this.handleTabChange('triggers')}>
            Triggers
          </div>
          <div class="tab ${this.activeTab === 'outputs' ? 'active' : ''}"
               @click=${() => this.handleTabChange('outputs')}>
            Outputs
          </div>
          <div class="tab ${this.activeTab === 'preview' ? 'active' : ''}"
               @click=${() => this.handleTabChange('preview')}>
            Preview
          </div>
        </div>
        
        <div class="tab-content ${this.activeTab === 'design' ? 'active' : ''}">
          ${this.renderDesignTab()}
        </div>
        
        <div class="tab-content ${this.activeTab === 'triggers' ? 'active' : ''}">
          ${this.renderTriggersTab()}
        </div>
        
        <div class="tab-content ${this.activeTab === 'outputs' ? 'active' : ''}">
          ${this.renderOutputsTab()}
        </div>
        
        <div class="tab-content ${this.activeTab === 'preview' ? 'active' : ''}">
          ${this.renderPreviewTab()}
        </div>
        
        <div class="actions">
          <div>
            <button class="secondary" @click=${this.cancel}>Cancel</button>
          </div>
          <div>
            <button class="secondary" @click=${this.generatePreview}>Generate Preview</button>
            <button @click=${this.saveTemplate}>
              ${this.mode === 'create' ? 'Create' : 'Save'} Report
            </button>
          </div>
        </div>
        
        ${this.showFieldConfig ? this.renderFieldDialog() : ''}
        
        ${this.loading ? html`
          <div class="loading-overlay">
            <div class="loading-spinner"></div>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('report-builder', ReportBuilder);