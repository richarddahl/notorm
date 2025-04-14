import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element wa-workflow-designer
 * @description An interactive workflow designer component for defining notification workflows
 * @property {Object} workflow - The workflow definition being edited
 * @property {String} mode - Edit or create mode
 * @property {Array} availableEntities - List of available entity types
 * @property {Array} availableActions - List of available action types
 */
export class WebAwesomeWorkflowDesigner extends LitElement {
  static get properties() {
    return {
      workflow: { type: Object },
      mode: { type: String },
      availableEntities: { type: Array },
      availableActionTypes: { type: Array },
      availableConditionTypes: { type: Array },
      availableRecipientTypes: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      activeTab: { type: String },
      showTriggerDialog: { type: Boolean },
      currentTrigger: { type: Object },
      showConditionDialog: { type: Boolean },
      currentCondition: { type: Object },
      showActionDialog: { type: Boolean },
      currentAction: { type: Object },
      showRecipientDialog: { type: Boolean },
      currentRecipient: { type: Object }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --designer-bg: var(--wa-background-color, #f5f5f5);
        --designer-padding: 20px;
        --section-gap: 24px;
      }
      .designer-container {
        padding: var(--designer-padding);
        background-color: var(--designer-bg);
        min-height: 600px;
      }
      .designer-header {
        margin-bottom: var(--section-gap);
      }
      .designer-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .designer-subtitle {
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
      .element-list {
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
      .type-options {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
      }
      .type-option {
        flex: 1;
        text-align: center;
        padding: 16px;
        border: 2px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .type-option:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .type-option.selected {
        border-color: var(--wa-primary-color, #3f51b5);
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
      }
      .type-icon {
        font-size: 32px;
        margin-bottom: 8px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .type-option.selected .type-icon {
        color: var(--wa-primary-color, #3f51b5);
      }
      .element-config-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .workflow-canvas {
        min-height: 400px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        padding: 24px;
      }
      .workflow-step {
        padding: 16px;
        margin-bottom: 24px;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-surface-color, #ffffff);
        position: relative;
      }
      .workflow-step-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .workflow-step-title {
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .workflow-step-body {
        padding-left: 24px;
      }
      .workflow-connector {
        width: 2px;
        height: 24px;
        background-color: var(--wa-primary-color, #3f51b5);
        margin-left: 12px;
      }
      .badge-container {
        position: absolute;
        left: -12px;
        top: 16px;
        width: 24px;
        height: 24px;
        background-color: var(--wa-primary-color, #3f51b5);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        z-index: 1;
      }
      .operation-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-left: 8px;
      }
      .entity-badge {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
      }
      .operation-badge.create {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.1));
        color: var(--wa-success-color, #4caf50);
      }
      .operation-badge.update {
        background-color: var(--wa-warning-color-light, rgba(255, 152, 0, 0.1));
        color: var(--wa-warning-color, #ff9800);
      }
      .operation-badge.delete {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
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
      .condition-group {
        padding: 12px;
        border: 1px dashed var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        margin-bottom: 12px;
      }
      .condition-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .operator-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
        font-weight: 500;
      }
      .action-card {
        border-left: 4px solid var(--wa-primary-color, #3f51b5);
        margin-bottom: 12px;
      }
      .action-card.notification {
        border-left-color: var(--wa-secondary-color, #f50057);
      }
      .action-card.email {
        border-left-color: var(--wa-success-color, #4caf50);
      }
      .action-card.webhook {
        border-left-color: var(--wa-warning-color, #ff9800);
      }
      .action-card.database {
        border-left-color: var(--wa-info-color, #2196f3);
      }
      .recipient-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px;
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-hover-color, #f5f5f5);
        margin-bottom: 8px;
      }
      .recipient-type {
        font-weight: 500;
      }
      .condition-builder {
        padding: 16px;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        margin-top: 8px;
      }
      .condition-row {
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
        align-items: center;
      }
      .test-trigger {
        margin-top: 16px;
        padding: 16px;
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-info-color-light, rgba(33, 150, 243, 0.1));
      }
    `;
  }
  constructor() {
    super();
    this.workflow = this._createEmptyWorkflow();
    this.mode = 'create';
    this.availableEntities = [];
    this.availableActionTypes = [];
    this.availableConditionTypes = [];
    this.availableRecipientTypes = [];
    this.loading = false;
    this.error = null;
    this.activeTab = 'design';
    this.showTriggerDialog = false;
    this.currentTrigger = null;
    this.showConditionDialog = false;
    this.currentCondition = null;
    this.showActionDialog = false;
    this.currentAction = null;
    this.showRecipientDialog = false;
    this.currentRecipient = null;
    
    // Load mock data for demo purposes
    this._loadMockData();
  }
  _createEmptyWorkflow() {
    return {
      name: '',
      description: '',
      enabled: true,
      version: 1,
      trigger: {
        entity_type: '',
        operations: [],
        conditions: []
      },
      actions: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
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
    
    // Mock available action types
    this.availableActionTypes = [
      { value: 'notification', label: 'In-App Notification', icon: 'notifications' },
      { value: 'email', label: 'Email', icon: 'email' },
      { value: 'webhook', label: 'Webhook', icon: 'http' },
      { value: 'database', label: 'Database Operation', icon: 'storage' },
      { value: 'custom', label: 'Custom', icon: 'code' }
    ];
    
    // Mock available condition types
    this.availableConditionTypes = [
      { value: 'field', label: 'Field Condition', description: 'Check a field value' },
      { value: 'time', label: 'Time Condition', description: 'Based on time pattern' },
      { value: 'role', label: 'Role Condition', description: 'Based on user role' },
      { value: 'composite', label: 'Composite Condition', description: 'Combine multiple conditions' }
    ];
    
    // Mock available recipient types
    this.availableRecipientTypes = [
      { value: 'user', label: 'User', description: 'Specific user' },
      { value: 'role', label: 'Role', description: 'All users with role' },
      { value: 'department', label: 'Department', description: 'All users in department' },
      { value: 'dynamic', label: 'Dynamic', description: 'Based on entity attribute' }
    ];
    
    // Available operations
    this._availableOperations = [
      { value: 'create', label: 'Create' },
      { value: 'update', label: 'Update' },
      { value: 'delete', label: 'Delete' }
    ];
    
    // Available fields by entity
    this._entityFields = {
      'customer': [
        { name: 'name', type: 'string' },
        { name: 'email', type: 'string' },
        { name: 'status', type: 'string' },
        { name: 'created_at', type: 'datetime' }
      ],
      'order': [
        { name: 'order_number', type: 'string' },
        { name: 'total', type: 'number' },
        { name: 'status', type: 'string' },
        { name: 'payment_status', type: 'string' },
        { name: 'customer_id', type: 'string' }
      ],
      'product': [
        { name: 'name', type: 'string' },
        { name: 'price', type: 'number' },
        { name: 'stock', type: 'number' },
        { name: 'category', type: 'string' }
      ]
    };
    
    // Available operators
    this._operators = [
      { value: 'eq', label: 'Equal to', types: ['string', 'number', 'boolean', 'datetime'] },
      { value: 'neq', label: 'Not equal to', types: ['string', 'number', 'boolean', 'datetime'] },
      { value: 'gt', label: 'Greater than', types: ['number', 'datetime'] },
      { value: 'gte', label: 'Greater than or equal', types: ['number', 'datetime'] },
      { value: 'lt', label: 'Less than', types: ['number', 'datetime'] },
      { value: 'lte', label: 'Less than or equal', types: ['number', 'datetime'] },
      { value: 'contains', label: 'Contains', types: ['string'] },
      { value: 'starts_with', label: 'Starts with', types: ['string'] },
      { value: 'ends_with', label: 'Ends with', types: ['string'] },
      { value: 'in', label: 'In list', types: ['string', 'number'] },
      { value: 'not_in', label: 'Not in list', types: ['string', 'number'] }
    ];
  }
  connectedCallback() {
    super.connectedCallback();
    
    // In a real implementation, we would load entities from the server
    // this.loadEntities();
  }
  async loadEntities() {
    this.loading = true;
    
    try {
      const response = await fetch('/api/workflow/entities');
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
  handleNameChange(e) {
    this.workflow = {
      ...this.workflow,
      name: e.target.value
    };
  }
  handleDescriptionChange(e) {
    this.workflow = {
      ...this.workflow,
      description: e.target.value
    };
  }
  handleEntityTypeChange(e) {
    const entityType = e.target.value;
    this.workflow = {
      ...this.workflow,
      trigger: {
        ...this.workflow.trigger,
        entity_type: entityType,
        conditions: []
      }
    };
  }
  handleOperationsChange(operation, checked) {
    const operations = [...(this.workflow.trigger.operations || [])];
    
    if (checked && !operations.includes(operation)) {
      operations.push(operation);
    } else if (!checked && operations.includes(operation)) {
      const index = operations.indexOf(operation);
      operations.splice(index, 1);
    }
    
    this.workflow = {
      ...this.workflow,
      trigger: {
        ...this.workflow.trigger,
        operations
      }
    };
  }
  addTriggerCondition() {
    this.currentCondition = {
      type: 'field',
      field: '',
      operator: 'eq',
      value: ''
    };
    this.showConditionDialog = true;
  }
  cancelConditionDialog() {
    this.showConditionDialog = false;
    this.currentCondition = null;
  }
  handleConditionTypeChange(type) {
    this.currentCondition = {
      ...this.currentCondition,
      type
    };
  }
  saveCondition() {
    const conditions = [...(this.workflow.trigger.conditions || [])];
    
    if (this.currentCondition.index !== undefined) {
      // Update existing condition
      conditions[this.currentCondition.index] = this.currentCondition;
    } else {
      // Add new condition
      conditions.push(this.currentCondition);
    }
    
    this.workflow = {
      ...this.workflow,
      trigger: {
        ...this.workflow.trigger,
        conditions
      }
    };
    
    this.showConditionDialog = false;
    this.currentCondition = null;
  }
  removeCondition(index) {
    const conditions = [...(this.workflow.trigger.conditions || [])];
    conditions.splice(index, 1);
    
    this.workflow = {
      ...this.workflow,
      trigger: {
        ...this.workflow.trigger,
        conditions
      }
    };
  }
  addAction() {
    this.currentAction = {
      type: 'notification',
      title: '',
      body: '',
      recipients: []
    };
    this.showActionDialog = true;
  }
  cancelActionDialog() {
    this.showActionDialog = false;
    this.currentAction = null;
  }
  handleActionTypeChange(type) {
    this.currentAction = {
      ...this.currentAction,
      type
    };
  }
  saveAction() {
    const actions = [...(this.workflow.actions || [])];
    
    if (this.currentAction.index !== undefined) {
      // Update existing action
      actions[this.currentAction.index] = this.currentAction;
    } else {
      // Add new action
      actions.push(this.currentAction);
    }
    
    this.workflow = {
      ...this.workflow,
      actions
    };
    
    this.showActionDialog = false;
    this.currentAction = null;
  }
  removeAction(index) {
    const actions = [...(this.workflow.actions || [])];
    actions.splice(index, 1);
    
    this.workflow = {
      ...this.workflow,
      actions
    };
  }
  addRecipient(actionIndex) {
    this.currentRecipient = {
      type: 'user',
      value: '',
      actionIndex
    };
    this.showRecipientDialog = true;
  }
  cancelRecipientDialog() {
    this.showRecipientDialog = false;
    this.currentRecipient = null;
  }
  handleRecipientTypeChange(type) {
    this.currentRecipient = {
      ...this.currentRecipient,
      type
    };
  }
  saveRecipient() {
    const actions = [...(this.workflow.actions || [])];
    const actionIndex = this.currentRecipient.actionIndex;
    
    if (!actions[actionIndex].recipients) {
      actions[actionIndex].recipients = [];
    }
    
    const recipient = {
      type: this.currentRecipient.type,
      value: this.currentRecipient.value
    };
    
    if (this.currentRecipient.index !== undefined) {
      // Update existing recipient
      actions[actionIndex].recipients[this.currentRecipient.index] = recipient;
    } else {
      // Add new recipient
      actions[actionIndex].recipients.push(recipient);
    }
    
    this.workflow = {
      ...this.workflow,
      actions
    };
    
    this.showRecipientDialog = false;
    this.currentRecipient = null;
  }
  removeRecipient(actionIndex, recipientIndex) {
    const actions = [...(this.workflow.actions || [])];
    actions[actionIndex].recipients.splice(recipientIndex, 1);
    
    this.workflow = {
      ...this.workflow,
      actions
    };
  }
  async saveWorkflow() {
    if (!this.validateWorkflow()) {
      return;
    }
    
    this.loading = true;
    
    try {
      const endpoint = this.mode === 'create' ? '/api/workflows' : `/api/workflows/${this.workflow.id}`;
      const method = this.mode === 'create' ? 'POST' : 'PUT';
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.workflow)
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const savedWorkflow = await response.json();
      
      // Dispatch event
      this.dispatchEvent(new CustomEvent('workflow-saved', {
        detail: { workflow: savedWorkflow }
      }));
      
      // Show success notification
      this._showNotification('Workflow saved successfully', 'success');
      
      // Reset form if creating new workflow
      if (this.mode === 'create') {
        this.workflow = this._createEmptyWorkflow();
      } else {
        this.workflow = savedWorkflow;
      }
      
    } catch (err) {
      console.error('Failed to save workflow:', err);
      this.error = `Error saving workflow: ${err.message}`;
      this._showNotification(`Error saving workflow: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  validateWorkflow() {
    // Basic validation
    if (!this.workflow.name) {
      this.error = 'Workflow name is required';
      this._showNotification('Workflow name is required', 'error');
      return false;
    }
    
    if (!this.workflow.trigger.entity_type) {
      this.error = 'Entity type is required';
      this._showNotification('Entity type is required', 'error');
      return false;
    }
    
    if (!this.workflow.trigger.operations || this.workflow.trigger.operations.length === 0) {
      this.error = 'At least one operation must be selected';
      this._showNotification('At least one operation must be selected', 'error');
      return false;
    }
    
    if (!this.workflow.actions || this.workflow.actions.length === 0) {
      this.error = 'At least one action is required';
      this._showNotification('At least one action is required', 'error');
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
  testWorkflow() {
    // In a real implementation, this would send a request to test the workflow
    this._showNotification('Workflow test initiated', 'info');
  }
  cancel() {
    this.dispatchEvent(new CustomEvent('cancel'));
  }
  renderConditionDialog() {
    if (!this.showConditionDialog) return html``;
    
    const entityType = this.workflow.trigger.entity_type;
    const fields = entityType && this._entityFields[entityType] ? this._entityFields[entityType] : [];
    
    return html`
      <wa-dialog open @close=${this.cancelConditionDialog}>
        <div slot="header">
          ${this.currentCondition.index !== undefined ? 'Edit Condition' : 'Add Condition'}
        </div>
        
        <div>
          <div class="type-options">
            ${this.availableConditionTypes.map(type => html`
              <div 
                class="type-option ${this.currentCondition.type === type.value ? 'selected' : ''}"
                @click=${() => this.handleConditionTypeChange(type.value)}>
                <wa-icon name="${this._getConditionTypeIcon(type.value)}" class="type-icon"></wa-icon>
                <div>${type.label}</div>
                <small>${type.description}</small>
              </div>
            `)}
          </div>
          
          ${this.currentCondition.type === 'field' ? html`
            <div class="element-config-section">
              <wa-select 
                label="Field"
                required
                .value=${this.currentCondition.field || ''}
                @change=${e => this.currentCondition = {...this.currentCondition, field: e.target.value}}>
                <wa-option value="">Select a field</wa-option>
                ${fields.map(field => html`
                  <wa-option value="${field.name}">${field.name}</wa-option>
                `)}
              </wa-select>
              
              <wa-select 
                label="Operator"
                required
                .value=${this.currentCondition.operator || 'eq'}
                @change=${e => this.currentCondition = {...this.currentCondition, operator: e.target.value}}>
                ${this._getOperatorsForField(this.currentCondition.field, fields).map(op => html`
                  <wa-option value="${op.value}">${op.label}</wa-option>
                `)}
              </wa-select>
              
              <wa-input 
                label="Value"
                required
                .value=${this.currentCondition.value || ''}
                @input=${e => this.currentCondition = {...this.currentCondition, value: e.target.value}}
                helptext="The value to compare against">
              </wa-input>
            </div>
          ` : ''}
          
          ${this.currentCondition.type === 'time' ? html`
            <div class="element-config-section">
              <wa-select 
                label="Time Pattern"
                required
                .value=${this.currentCondition.pattern || 'time_of_day'}
                @change=${e => this.currentCondition = {...this.currentCondition, pattern: e.target.value}}>
                <wa-option value="time_of_day">Time of Day</wa-option>
                <wa-option value="day_of_week">Day of Week</wa-option>
                <wa-option value="day_of_month">Day of Month</wa-option>
                <wa-option value="business_hours">Business Hours</wa-option>
                <wa-option value="after_hours">After Hours</wa-option>
              </wa-select>
              
              ${this.currentCondition.pattern === 'time_of_day' ? html`
                <div class="form-row">
                  <wa-input 
                    label="Start Time"
                    type="time"
                    .value=${this.currentCondition.start_time || '09:00'}
                    @input=${e => this.currentCondition = {...this.currentCondition, start_time: e.target.value}}>
                  </wa-input>
                  
                  <wa-input 
                    label="End Time"
                    type="time"
                    .value=${this.currentCondition.end_time || '17:00'}
                    @input=${e => this.currentCondition = {...this.currentCondition, end_time: e.target.value}}>
                  </wa-input>
                </div>
              ` : ''}
              
              ${this.currentCondition.pattern === 'day_of_week' ? html`
                <div style="margin-top: 16px;">
                  <label>Days of Week</label>
                  <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px;">
                    ${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(day => html`
                      <wa-checkbox 
                        label="${day}"
                        ?checked=${(this.currentCondition.days || []).includes(day.toLowerCase())}
                        @change=${e => {
                          const days = this.currentCondition.days || [];
                          const dayValue = day.toLowerCase();
                          if (e.target.checked && !days.includes(dayValue)) {
                            this.currentCondition = {...this.currentCondition, days: [...days, dayValue]};
                          } else if (!e.target.checked && days.includes(dayValue)) {
                            this.currentCondition = {
                              ...this.currentCondition, 
                              days: days.filter(d => d !== dayValue)
                            };
                          }
                        }}>
                      </wa-checkbox>
                    `)}
                  </div>
                </div>
              ` : ''}
            </div>
          ` : ''}
          
          ${this.currentCondition.type === 'role' ? html`
            <div class="element-config-section">
              <wa-select 
                label="Role Requirement"
                required
                .value=${this.currentCondition.role_check || 'has_role'}
                @change=${e => this.currentCondition = {...this.currentCondition, role_check: e.target.value}}>
                <wa-option value="has_role">User Has Role</wa-option>
                <wa-option value="has_any_role">User Has Any Role</wa-option>
                <wa-option value="has_all_roles">User Has All Roles</wa-option>
              </wa-select>
              
              <div style="margin-top: 16px;">
                <label>Roles</label>
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                  <wa-input
                    placeholder="Role name"
                    .value=${this.currentCondition.newRole || ''}
                    @input=${e => this.currentCondition = {...this.currentCondition, newRole: e.target.value}}
                    @keydown=${e => {
                      if (e.key === 'Enter' && this.currentCondition.newRole) {
                        const roles = this.currentCondition.roles || [];
                        if (!roles.includes(this.currentCondition.newRole)) {
                          this.currentCondition = {
                            ...this.currentCondition, 
                            roles: [...roles, this.currentCondition.newRole],
                            newRole: ''
                          };
                        }
                      }
                    }}>
                  </wa-input>
                  <wa-button
                    @click=${() => {
                      if (!this.currentCondition.newRole) return;
                      const roles = this.currentCondition.roles || [];
                      if (!roles.includes(this.currentCondition.newRole)) {
                        this.currentCondition = {
                          ...this.currentCondition, 
                          roles: [...roles, this.currentCondition.newRole],
                          newRole: ''
                        };
                      }
                    }}>
                    Add
                  </wa-button>
                </div>
                
                <div style="margin-top: 12px;">
                  ${(this.currentCondition.roles || []).map(role => html`
                    <wa-chip
                      @remove=${() => {
                        const roles = (this.currentCondition.roles || [])
                          .filter(r => r !== role);
                        this.currentCondition = {
                          ...this.currentCondition, 
                          roles
                        };
                      }}>
                      ${role}
                    </wa-chip>
                  `)}
                </div>
              </div>
            </div>
          ` : ''}
          
          ${this.currentCondition.type === 'composite' ? html`
            <div class="element-config-section">
              <wa-select 
                label="Logical Operator"
                required
                .value=${this.currentCondition.operator || 'and'}
                @change=${e => this.currentCondition = {...this.currentCondition, operator: e.target.value}}>
                <wa-option value="and">AND</wa-option>
                <wa-option value="or">OR</wa-option>
                <wa-option value="not">NOT</wa-option>
              </wa-select>
              
              <div class="condition-builder">
                <div style="margin-bottom: 16px;">
                  <strong>Sub-conditions</strong>
                  <small style="display: block; color: var(--wa-text-secondary-color);">
                    All conditions will be combined with the ${this.currentCondition.operator || 'AND'} operator
                  </small>
                </div>
                
                ${(this.currentCondition.conditions || []).length === 0 ? html`
                  <div style="padding: 16px; text-align: center; color: var(--wa-text-secondary-color);">
                    No sub-conditions added yet. Click "Add Sub-condition" to add one.
                  </div>
                ` : html`
                  ${(this.currentCondition.conditions || []).map((condition, index) => html`
                    <div class="condition-item">
                      <wa-icon name="${this._getConditionTypeIcon(condition.type)}"></wa-icon>
                      <div style="flex: 1;">
                        ${this._formatConditionSummary(condition)}
                      </div>
                      <wa-button 
                        variant="icon" 
                        color="error"
                        @click=${() => {
                          const conditions = [...(this.currentCondition.conditions || [])];
                          conditions.splice(index, 1);
                          this.currentCondition = {...this.currentCondition, conditions};
                        }}>
                        <wa-icon name="delete"></wa-icon>
                      </wa-button>
                    </div>
                  `)}
                `}
                
                <div style="margin-top: 16px;">
                  <wa-button 
                    variant="outlined"
                    @click=${() => {
                      // In a real implementation, we would show a dialog to add a sub-condition
                      // For this demo, we'll add a simple field condition
                      const conditions = [...(this.currentCondition.conditions || [])];
                      conditions.push({
                        type: 'field',
                        field: 'status',
                        operator: 'eq',
                        value: 'active'
                      });
                      this.currentCondition = {...this.currentCondition, conditions};
                    }}>
                    Add Sub-condition
                  </wa-button>
                </div>
              </div>
            </div>
          ` : ''}
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.cancelConditionDialog}>Cancel</wa-button>
          <wa-button @click=${this.saveCondition}>
            ${this.currentCondition.index !== undefined ? 'Update' : 'Add'} Condition
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  renderActionDialog() {
    if (!this.showActionDialog) return html``;
    
    return html`
      <wa-dialog open @close=${this.cancelActionDialog}>
        <div slot="header">
          ${this.currentAction.index !== undefined ? 'Edit Action' : 'Add Action'}
        </div>
        
        <div>
          <div class="type-options">
            ${this.availableActionTypes.map(type => html`
              <div 
                class="type-option ${this.currentAction.type === type.value ? 'selected' : ''}"
                @click=${() => this.handleActionTypeChange(type.value)}>
                <wa-icon name="${type.icon}" class="type-icon"></wa-icon>
                <div>${type.label}</div>
              </div>
            `)}
          </div>
          
          ${this.currentAction.type === 'notification' ? html`
            <div class="element-config-section">
              <wa-input 
                label="Notification Title"
                required
                .value=${this.currentAction.title || ''}
                @input=${e => this.currentAction = {...this.currentAction, title: e.target.value}}
                helptext="Title shown in the notification">
              </wa-input>
              
              <wa-textarea 
                label="Notification Body"
                required
                .value=${this.currentAction.body || ''}
                @input=${e => this.currentAction = {...this.currentAction, body: e.target.value}}
                helptext="Main content of the notification">
              </wa-textarea>
              
              <wa-select 
                label="Priority"
                .value=${this.currentAction.priority || 'normal'}
                @change=${e => this.currentAction = {...this.currentAction, priority: e.target.value}}>
                <wa-option value="low">Low</wa-option>
                <wa-option value="normal">Normal</wa-option>
                <wa-option value="high">High</wa-option>
                <wa-option value="urgent">Urgent</wa-option>
              </wa-select>
              
              <wa-checkbox
                label="Require acknowledgment"
                ?checked=${this.currentAction.require_ack}
                @change=${e => this.currentAction = {...this.currentAction, require_ack: e.target.checked}}>
                Recipients must acknowledge this notification
              </wa-checkbox>
            </div>
          ` : ''}
          
          ${this.currentAction.type === 'email' ? html`
            <div class="element-config-section">
              <wa-input 
                label="Email Subject"
                required
                .value=${this.currentAction.subject || ''}
                @input=${e => this.currentAction = {...this.currentAction, subject: e.target.value}}
                helptext="Subject line of the email">
              </wa-input>
              
              <wa-select 
                label="Email Template"
                .value=${this.currentAction.template || 'default'}
                @change=${e => this.currentAction = {...this.currentAction, template: e.target.value}}>
                <wa-option value="default">Default Template</wa-option>
                <wa-option value="minimal">Minimal</wa-option>
                <wa-option value="branded">Branded</wa-option>
                <wa-option value="alert">Alert</wa-option>
              </wa-select>
              
              <wa-textarea 
                label="Email Body"
                required
                .value=${this.currentAction.body || ''}
                @input=${e => this.currentAction = {...this.currentAction, body: e.target.value}}
                helptext="Main content of the email. Supports template variables like {{field_name}}.">
              </wa-textarea>
            </div>
          ` : ''}
          
          ${this.currentAction.type === 'webhook' ? html`
            <div class="element-config-section">
              <wa-input 
                label="Webhook URL"
                required
                .value=${this.currentAction.url || ''}
                @input=${e => this.currentAction = {...this.currentAction, url: e.target.value}}
                helptext="The URL to call">
              </wa-input>
              
              <wa-select 
                label="HTTP Method"
                .value=${this.currentAction.method || 'POST'}
                @change=${e => this.currentAction = {...this.currentAction, method: e.target.value}}>
                <wa-option value="GET">GET</wa-option>
                <wa-option value="POST">POST</wa-option>
                <wa-option value="PUT">PUT</wa-option>
                <wa-option value="PATCH">PATCH</wa-option>
                <wa-option value="DELETE">DELETE</wa-option>
              </wa-select>
              
              <wa-textarea 
                label="Request Body Template"
                .value=${this.currentAction.body_template || ''}
                @input=${e => this.currentAction = {...this.currentAction, body_template: e.target.value}}
                helptext="JSON template for the request body. Use {{field_name}} for variables.">
              </wa-textarea>
              
              <div style="margin-top: 16px;">
                <label>Headers</label>
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                  <wa-input
                    placeholder="Header name"
                    .value=${this.currentAction.newHeaderName || ''}
                    @input=${e => this.currentAction = {...this.currentAction, newHeaderName: e.target.value}}>
                  </wa-input>
                  <wa-input
                    placeholder="Header value"
                    .value=${this.currentAction.newHeaderValue || ''}
                    @input=${e => this.currentAction = {...this.currentAction, newHeaderValue: e.target.value}}>
                  </wa-input>
                  <wa-button
                    @click=${() => {
                      if (!this.currentAction.newHeaderName || !this.currentAction.newHeaderValue) return;
                      const headers = this.currentAction.headers || {};
                      this.currentAction = {
                        ...this.currentAction, 
                        headers: {
                          ...headers,
                          [this.currentAction.newHeaderName]: this.currentAction.newHeaderValue
                        },
                        newHeaderName: '',
                        newHeaderValue: ''
                      };
                    }}>
                    Add
                  </wa-button>
                </div>
                
                <div style="margin-top: 12px;">
                  ${Object.entries(this.currentAction.headers || {}).map(([name, value]) => html`
                    <wa-chip
                      @remove=${() => {
                        const headers = {...(this.currentAction.headers || {})};
                        delete headers[name];
                        this.currentAction = {
                          ...this.currentAction, 
                          headers
                        };
                      }}>
                      ${name}: ${value}
                    </wa-chip>
                  `)}
                </div>
              </div>
            </div>
          ` : ''}
          
          ${this.currentAction.type === 'database' ? html`
            <div class="element-config-section">
              <wa-select 
                label="Operation Type"
                required
                .value=${this.currentAction.operation || 'update'}
                @change=${e => this.currentAction = {...this.currentAction, operation: e.target.value}}>
                <wa-option value="update">Update Record</wa-option>
                <wa-option value="insert">Insert Record</wa-option>
                <wa-option value="delete">Delete Record</wa-option>
              </wa-select>
              
              <wa-input 
                label="Target Entity"
                required
                .value=${this.currentAction.target_entity || ''}
                @input=${e => this.currentAction = {...this.currentAction, target_entity: e.target.value}}
                helptext="The entity to perform the operation on">
              </wa-input>
              
              ${this.currentAction.operation !== 'delete' ? html`
                <wa-textarea 
                  label="Field Mapping"
                  class="json-editor"
                  .value=${this.currentAction.field_mapping ? JSON.stringify(this.currentAction.field_mapping, null, 2) : '{}'}
                  @input=${e => {
                    try {
                      const mapping = JSON.parse(e.target.value);
                      this.currentAction = {...this.currentAction, field_mapping: mapping};
                    } catch (err) {
                      // Ignore JSON parse errors while typing
                    }
                  }}
                  helptext="JSON mapping of target fields to values or source fields. Use {{field_name}} for variables.">
                </wa-textarea>
              ` : ''}
              
              <wa-textarea 
                label="Condition"
                .value=${this.currentAction.condition || ''}
                @input=${e => this.currentAction = {...this.currentAction, condition: e.target.value}}
                helptext="SQL-like condition to identify records (e.g., id = {{entity.id}})">
              </wa-textarea>
            </div>
          ` : ''}
          
          ${this.currentAction.type === 'custom' ? html`
            <div class="element-config-section">
              <wa-input 
                label="Custom Action Name"
                required
                .value=${this.currentAction.name || ''}
                @input=${e => this.currentAction = {...this.currentAction, name: e.target.value}}
                helptext="Identifier for this custom action">
              </wa-input>
              
              <wa-input 
                label="Handler"
                required
                .value=${this.currentAction.handler || ''}
                @input=${e => this.currentAction = {...this.currentAction, handler: e.target.value}}
                helptext="Custom handler function name">
              </wa-input>
              
              <wa-textarea 
                label="Configuration"
                class="json-editor"
                .value=${this.currentAction.config ? JSON.stringify(this.currentAction.config, null, 2) : '{}'}
                @input=${e => {
                  try {
                    const config = JSON.parse(e.target.value);
                    this.currentAction = {...this.currentAction, config};
                  } catch (err) {
                    // Ignore JSON parse errors while typing
                  }
                }}
                helptext="JSON configuration for the custom action">
              </wa-textarea>
            </div>
          ` : ''}
          
          ${['notification', 'email'].includes(this.currentAction.type) ? html`
            <div class="element-config-section">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <label>Recipients</label>
                <wa-button 
                  variant="text" 
                  @click=${() => {
                    // In a real implementation, we would use a more sophisticated approach
                    // For this demo, we'll add a simple recipient
                    const recipients = [...(this.currentAction.recipients || [])];
                    recipients.push({
                      type: 'user',
                      value: 'admin@example.com'
                    });
                    this.currentAction = {...this.currentAction, recipients};
                  }}>
                  <wa-icon slot="prefix" name="add"></wa-icon>
                  Add Recipient
                </wa-button>
              </div>
              
              ${(this.currentAction.recipients || []).length === 0 ? html`
                <div style="padding: 16px; text-align: center; color: var(--wa-text-secondary-color);">
                  No recipients added yet. Click "Add Recipient" to add one.
                </div>
              ` : html`
                ${(this.currentAction.recipients || []).map((recipient, index) => html`
                  <div class="recipient-item">
                    <wa-icon name="${this._getRecipientTypeIcon(recipient.type)}"></wa-icon>
                    <div style="flex: 1;">
                      <span class="recipient-type">${this._getRecipientTypeLabel(recipient.type)}:</span>
                      ${recipient.value}
                    </div>
                    <wa-button 
                      variant="icon" 
                      color="error"
                      @click=${() => {
                        const recipients = [...(this.currentAction.recipients || [])];
                        recipients.splice(index, 1);
                        this.currentAction = {...this.currentAction, recipients};
                      }}>
                      <wa-icon name="delete"></wa-icon>
                    </wa-button>
                  </div>
                `)}
              `}
            </div>
          ` : ''}
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.cancelActionDialog}>Cancel</wa-button>
          <wa-button @click=${this.saveAction}>
            ${this.currentAction.index !== undefined ? 'Update' : 'Add'} Action
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  _getConditionTypeIcon(type) {
    switch (type) {
      case 'field': return 'data_object';
      case 'time': return 'schedule';
      case 'role': return 'security';
      case 'composite': return 'account_tree';
      default: return 'filter_alt';
    }
  }
  _getRecipientTypeIcon(type) {
    switch (type) {
      case 'user': return 'person';
      case 'role': return 'security';
      case 'department': return 'people';
      case 'dynamic': return 'sync';
      default: return 'person';
    }
  }
  _getRecipientTypeLabel(type) {
    switch (type) {
      case 'user': return 'User';
      case 'role': return 'Role';
      case 'department': return 'Department';
      case 'dynamic': return 'Dynamic';
      default: return 'User';
    }
  }
  _getOperatorsForField(fieldName, fields) {
    if (!fieldName || !fields) return this._operators;
    
    const field = fields.find(f => f.name === fieldName);
    if (!field) return this._operators;
    
    return this._operators.filter(op => op.types.includes(field.type));
  }
  _formatConditionSummary(condition) {
    switch (condition.type) {
      case 'field':
        const operator = this._operators.find(op => op.value === condition.operator);
        return `${condition.field} ${operator ? operator.label : condition.operator} ${condition.value}`;
      case 'time':
        return `Time: ${condition.pattern}`;
      case 'role':
        return `Role: ${condition.role_check} ${(condition.roles || []).join(', ')}`;
      case 'composite':
        return `Composite: ${condition.operator.toUpperCase()} (${(condition.conditions || []).length} conditions)`;
      default:
        return `Condition: ${condition.type}`;
    }
  }
  renderDesignTab() {
    return html`
      <div class="form-row">
        <wa-input 
          label="Workflow Name" 
          required
          .value=${this.workflow.name || ''}
          @input=${this.handleNameChange}
          placeholder="e.g., New Order Notification">
        </wa-input>
        
        <wa-switch
          label="Enabled"
          ?checked=${this.workflow.enabled !== false}
          @change=${e => this.workflow = {...this.workflow, enabled: e.target.checked}}>
          Workflow is active
        </wa-switch>
      </div>
      
      <wa-textarea 
        label="Description"
        .value=${this.workflow.description || ''}
        @input=${this.handleDescriptionChange}
        placeholder="Describe the purpose and behavior of this workflow">
      </wa-textarea>
      
      <div class="section-title">Trigger Definition</div>
      
      <div class="form-row">
        <wa-select 
          label="Entity Type" 
          required
          .value=${this.workflow.trigger.entity_type || ''}
          @change=${this.handleEntityTypeChange}>
          <wa-option value="">Select an entity type</wa-option>
          ${this.availableEntities.map(entity => html`
            <wa-option value="${entity.value}">${entity.label}</wa-option>
          `)}
        </wa-select>
      </div>
      
      <div style="margin-top: 16px;">
        <label>Trigger Operations</label>
        <div style="display: flex; gap: 16px; margin-top: 8px;">
          ${this._availableOperations.map(op => html`
            <wa-checkbox 
              label="${op.label}"
              ?checked=${(this.workflow.trigger.operations || []).includes(op.value)}
              @change=${e => this.handleOperationsChange(op.value, e.target.checked)}>
            </wa-checkbox>
          `)}
        </div>
      </div>
      
      <div style="margin-top: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <label>Trigger Conditions</label>
          <wa-button 
            variant="text" 
            @click=${this.addTriggerCondition}>
            <wa-icon slot="prefix" name="add"></wa-icon>
            Add Condition
          </wa-button>
        </div>
        
        ${(this.workflow.trigger.conditions || []).length === 0 ? html`
          <div class="empty-list" style="margin-top: 8px;">
            <wa-icon name="filter_alt" size="large" style="margin-bottom: 12px;"></wa-icon>
            <div>No conditions defined. Workflow will trigger for all ${this.workflow.trigger.operations.join(', ')} operations on ${this.workflow.trigger.entity_type}.</div>
          </div>
        ` : html`
          <wa-card elevation="1" style="margin-top: 8px;">
            <div style="padding: 16px;">
              ${(this.workflow.trigger.conditions || []).map((condition, index) => html`
                <div class="condition-group">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <wa-icon name="${this._getConditionTypeIcon(condition.type)}"></wa-icon>
                      <strong>${condition.type.charAt(0).toUpperCase() + condition.type.slice(1)} Condition</strong>
                    </div>
                    <div>
                      <wa-button variant="text" @click=${() => {
                        this.currentCondition = {...condition, index};
                        this.showConditionDialog = true;
                      }}>Edit</wa-button>
                      <wa-button variant="text" color="error" @click=${() => this.removeCondition(index)}>Remove</wa-button>
                    </div>
                  </div>
                  
                  <div style="margin-left: 32px;">
                    ${this._formatConditionSummary(condition)}
                  </div>
                </div>
              `)}
            </div>
          </wa-card>
        `}
      </div>
      
      <div class="section-title">Actions</div>
      
      ${(this.workflow.actions || []).length === 0 ? html`
        <div class="empty-list">
          <wa-icon name="play_arrow" size="large" style="margin-bottom: 12px;"></wa-icon>
          <div>No actions defined yet. Click "Add Action" to define what happens when this workflow triggers.</div>
        </div>
      ` : html`
        ${(this.workflow.actions || []).map((action, index) => html`
          <wa-card class="action-card ${action.type}" elevation="1" style="margin-bottom: 16px;">
            <div style="padding: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <wa-icon name="${this._getActionTypeIcon(action.type)}"></wa-icon>
                  <strong>${this._getActionTypeLabel(action.type)}</strong>
                </div>
                <div>
                  <wa-button variant="text" @click=${() => {
                    this.currentAction = {...action, index};
                    this.showActionDialog = true;
                  }}>Edit</wa-button>
                  <wa-button variant="text" color="error" @click=${() => this.removeAction(index)}>Remove</wa-button>
                </div>
              </div>
              
              <div style="margin-left: 32px;">
                ${action.type === 'notification' ? html`
                  <div><strong>Title:</strong> ${action.title}</div>
                  <div><strong>Body:</strong> ${action.body}</div>
                  <div><strong>Priority:</strong> ${action.priority || 'Normal'}</div>
                  <div><strong>Require Acknowledgment:</strong> ${action.require_ack ? 'Yes' : 'No'}</div>
                ` : ''}
                
                ${action.type === 'email' ? html`
                  <div><strong>Subject:</strong> ${action.subject}</div>
                  <div><strong>Template:</strong> ${action.template || 'Default'}</div>
                  <div><strong>Body:</strong> ${action.body?.substring(0, 100)}${action.body?.length > 100 ? '...' : ''}</div>
                ` : ''}
                
                ${action.type === 'webhook' ? html`
                  <div><strong>URL:</strong> ${action.url}</div>
                  <div><strong>Method:</strong> ${action.method || 'POST'}</div>
                  ${action.headers ? html`<div><strong>Headers:</strong> ${Object.keys(action.headers).length} defined</div>` : ''}
                ` : ''}
                
                ${action.type === 'database' ? html`
                  <div><strong>Operation:</strong> ${action.operation}</div>
                  <div><strong>Target Entity:</strong> ${action.target_entity}</div>
                  <div><strong>Condition:</strong> ${action.condition || 'None'}</div>
                ` : ''}
                
                ${action.type === 'custom' ? html`
                  <div><strong>Name:</strong> ${action.name}</div>
                  <div><strong>Handler:</strong> ${action.handler}</div>
                ` : ''}
                
                ${['notification', 'email'].includes(action.type) && (action.recipients || []).length > 0 ? html`
                  <div style="margin-top: 8px;">
                    <strong>Recipients (${(action.recipients || []).length}):</strong>
                    <div style="margin-top: 8px;">
                      ${(action.recipients || []).slice(0, 3).map(recipient => html`
                        <div class="recipient-item">
                          <wa-icon name="${this._getRecipientTypeIcon(recipient.type)}"></wa-icon>
                          <div>
                            <span class="recipient-type">${this._getRecipientTypeLabel(recipient.type)}:</span>
                            ${recipient.value}
                          </div>
                        </div>
                      `)}
                      ${(action.recipients || []).length > 3 ? html`
                        <div style="text-align: center; padding: 8px; color: var(--wa-text-secondary-color);">
                          +${(action.recipients || []).length - 3} more recipients
                        </div>
                      ` : ''}
                    </div>
                  </div>
                ` : ''}
              </div>
            </div>
          </wa-card>
        `)}
      `}
      
      <div style="margin-top: 16px;">
        <wa-button @click=${this.addAction}>
          <wa-icon slot="prefix" name="add"></wa-icon>
          Add Action
        </wa-button>
      </div>
    `;
  }
  _getActionTypeIcon(type) {
    switch (type) {
      case 'notification': return 'notifications';
      case 'email': return 'email';
      case 'webhook': return 'http';
      case 'database': return 'storage';
      case 'custom': return 'code';
      default: return 'play_arrow';
    }
  }
  _getActionTypeLabel(type) {
    switch (type) {
      case 'notification': return 'In-App Notification';
      case 'email': return 'Email';
      case 'webhook': return 'Webhook';
      case 'database': return 'Database Operation';
      case 'custom': return 'Custom Action';
      default: return 'Action';
    }
  }
  renderTestTab() {
    return html`
      <div class="section-title">Test Workflow</div>
      
      <wa-card>
        <div style="padding: 16px;">
          <p>Use this tool to simulate a trigger event and test your workflow configuration.</p>
          
          <div class="form-row">
            <wa-select 
              label="Operation"
              .value=${this.workflow.trigger.operations?.[0] || 'create'}>
              ${this._availableOperations.map(op => html`
                <wa-option value="${op.value}" ?disabled=${!(this.workflow.trigger.operations || []).includes(op.value)}>
                  ${op.label}
                </wa-option>
              `)}
            </wa-select>
            
            <wa-input 
              label="Entity ID"
              value="sample-123"
              helptext="Optional: Specific entity ID to use for testing">
            </wa-input>
          </div>
          
          <wa-textarea 
            label="Test Data"
            class="json-editor"
            .value=${'{\n  "name": "Test Entity",\n  "status": "active",\n  "created_at": "2023-05-01T12:00:00Z"\n}'}
            helptext="Sample entity data to use for testing condition evaluation">
          </wa-textarea>
          
          <div class="test-trigger">
            <strong>Test Results Preview</strong>
            <div style="margin-top: 8px;">
              <div>✅ <strong>Trigger conditions:</strong> All conditions would pass</div>
              <div>✅ <strong>Actions:</strong> ${this.workflow.actions.length} actions would execute</div>
              <div>📧 <strong>Recipients:</strong> 4 recipients would receive notifications</div>
            </div>
          </div>
          
          <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
            <wa-button @click=${this.testWorkflow}>
              <wa-icon slot="prefix" name="play_arrow"></wa-icon>
              Run Test
            </wa-button>
          </div>
        </div>
      </wa-card>
    `;
  }
  renderJsonTab() {
    return html`
      <div class="section-title">JSON Configuration</div>
      
      <wa-card>
        <div style="padding: 16px;">
          <wa-textarea 
            class="json-editor"
            style="height: 500px;"
            readonly
            .value=${JSON.stringify(this.workflow, null, 2)}>
          </wa-textarea>
          
          <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
            <wa-button variant="outlined">
              <wa-icon slot="prefix" name="content_copy"></wa-icon>
              Copy JSON
            </wa-button>
          </div>
        </div>
      </wa-card>
    `;
  }
  render() {
    return html`
      <div class="designer-container">
        <div class="designer-header">
          <h1 class="designer-title">${this.mode === 'create' ? 'Create New Workflow' : 'Edit Workflow'}</h1>
          <p class="designer-subtitle">Define triggers, conditions, and actions for automated workflows</p>
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
          <wa-tab value="test">Test</wa-tab>
          <wa-tab value="json">JSON</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="design" ?active=${this.activeTab === 'design'}>
          ${this.renderDesignTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="test" ?active=${this.activeTab === 'test'}>
          ${this.renderTestTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="json" ?active=${this.activeTab === 'json'}>
          ${this.renderJsonTab()}
        </wa-tab-panel>
        
        <div class="actions">
          <wa-button variant="outlined" @click=${this.cancel}>Cancel</wa-button>
          <wa-button @click=${this.saveWorkflow}>
            ${this.mode === 'create' ? 'Create' : 'Save'} Workflow
          </wa-button>
        </div>
        
        ${this.renderConditionDialog()}
        ${this.renderActionDialog()}
        
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
customElements.define('wa-workflow-designer', WebAwesomeWorkflowDesigner);