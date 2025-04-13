import { LitElement, html, css } from 'lit';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-textarea.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-chip.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-dialog.js';

/**
 * @element wa-workflow-simulator
 * @description A component for simulating workflow execution with custom test data
 * @property {Object} workflow - The workflow definition to simulate
 * @property {String} workflowId - ID of the workflow to simulate
 */
export class WebAwesomeWorkflowSimulator extends LitElement {
  static get properties() {
    return {
      workflow: { type: Object },
      workflowId: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      testMode: { type: String },
      entityData: { type: Object },
      simulationResult: { type: Object },
      activeTab: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --simulator-bg: var(--wa-background-color, #f5f5f5);
        --simulator-padding: 20px;
        --section-gap: 24px;
      }
      .simulator-container {
        padding: var(--simulator-padding);
        background-color: var(--simulator-bg);
        min-height: 600px;
      }
      .simulator-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--section-gap);
      }
      .simulator-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .simulator-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 8px 0 0 0;
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
        margin: 0 0 16px 0;
        color: var(--wa-text-primary-color, #212121);
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
      .code-block {
        background-color: var(--wa-hover-color, #f5f5f5);
        padding: 12px;
        border-radius: 4px;
        font-family: monospace;
        white-space: pre-wrap;
        overflow-x: auto;
        margin-top: 8px;
      }
      .test-options {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 24px;
      }
      .test-option {
        flex: 1;
        min-width: 200px;
        text-align: center;
        padding: 16px;
        border: 2px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .test-option:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .test-option.selected {
        border-color: var(--wa-primary-color, #3f51b5);
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
      }
      .test-icon {
        font-size: 32px;
        margin-bottom: 8px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .test-option.selected .test-icon {
        color: var(--wa-primary-color, #3f51b5);
      }
      .simulation-section {
        margin-top: var(--section-gap);
      }
      .simulation-result {
        margin-top: var(--section-gap);
      }
      .status-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 8px;
        font-size: 12px;
        border-radius: 12px;
        font-weight: 500;
        margin-left: 8px;
      }
      .status-badge.success {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.1));
        color: var(--wa-success-color, #4caf50);
      }
      .status-badge.partial {
        background-color: var(--wa-warning-color-light, rgba(255, 152, 0, 0.1));
        color: var(--wa-warning-color, #ff9800);
      }
      .status-badge.failure {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
      }
      .condition-result {
        padding: 2px 6px;
        font-size: 12px;
        border-radius: 10px;
      }
      .condition-result.true {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.1));
        color: var(--wa-success-color, #4caf50);
      }
      .condition-result.false {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
      }
      .condition-group {
        padding: 12px;
        border: 1px dashed var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        margin-bottom: 12px;
      }
      .action-item {
        padding: 16px;
        border-left: 4px solid var(--wa-primary-color, #3f51b5);
        margin-bottom: 16px;
        border-radius: 0 4px 4px 0;
      }
      .action-item.success {
        border-left-color: var(--wa-success-color, #4caf50);
      }
      .action-item.failure {
        border-left-color: var(--wa-error-color, #f44336);
      }
      .action-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }
      .action-title {
        font-weight: 500;
        font-size: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .action-details {
        margin-left: 32px;
      }
      .action-detail-row {
        margin-bottom: 8px;
      }
      .empty-state {
        text-align: center;
        padding: 40px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        margin-bottom: var(--section-gap);
      }
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin-bottom: var(--section-gap);
      }
      .info-card {
        padding: 16px;
      }
      .template-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
        margin-top: 16px;
      }
      .template-card {
        display: flex;
        flex-direction: column;
        height: 100%;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.2s ease;
      }
      .template-card:hover {
        border-color: var(--wa-border-color, #e0e0e0);
        transform: translateY(-2px);
      }
      .template-card.selected {
        border-color: var(--wa-primary-color, #3f51b5);
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
      }
    `;
  }

  constructor() {
    super();
    this.workflow = null;
    this.workflowId = null;
    this.loading = false;
    this.error = null;
    this.testMode = 'custom';
    this.entityData = {};
    this.simulationResult = null;
    this.activeTab = 'editor';
    
    // Load mock data for demo purposes
    this._loadMockData();
  }

  _loadMockData() {
    // Mock workflow data
    this.workflow = {
      id: 'wf-789',
      name: 'New Order Notification',
      description: 'Sends notification when a new order is created',
      enabled: true,
      version: 1,
      trigger: {
        entity_type: 'order',
        operations: ['create'],
        conditions: [
          {
            type: 'field',
            field: 'total',
            operator: 'gt',
            value: '100'
          },
          {
            type: 'field',
            field: 'status',
            operator: 'eq',
            value: 'new'
          }
        ]
      },
      actions: [
        {
          type: 'notification',
          title: 'New Order Created',
          body: 'A new order #{{order_number}} has been created.',
          priority: 'normal',
          recipients: [
            { type: 'role', value: 'sales_manager' },
            { type: 'role', value: 'fulfillment' }
          ]
        },
        {
          type: 'email',
          subject: 'New Order Notification',
          body: 'Hello,\n\nA new order #{{order_number}} has been created for {{customer_name}}.\n\nTotal: ${{total}}',
          recipients: [
            { type: 'dynamic', value: 'order.customer.email' }
          ]
        }
      ],
      created_at: '2023-04-15T14:32:20Z',
      updated_at: '2023-04-15T14:32:20Z'
    };
    
    // Default test data based on workflow trigger
    this.entityData = {
      id: 'order-12345',
      order_number: 'ORD-12345',
      customer_name: 'John Doe',
      customer_email: 'john.doe@example.com',
      total: 149.99,
      status: 'new',
      created_at: new Date().toISOString()
    };
    
    // Template test data
    this._testTemplates = [
      {
        id: 'template-1',
        name: 'Basic Order',
        description: 'A simple order with default values',
        data: {
          id: 'order-simple',
          order_number: 'ORD-1000',
          customer_name: 'Jane Smith',
          customer_email: 'jane@example.com',
          total: 75.50,
          status: 'new',
          created_at: new Date().toISOString()
        }
      },
      {
        id: 'template-2',
        name: 'Large Order',
        description: 'Order with high value that triggers conditions',
        data: {
          id: 'order-large',
          order_number: 'ORD-2000',
          customer_name: 'Robert Johnson',
          customer_email: 'robert@example.com',
          total: 1299.99,
          status: 'new',
          items: [
            { product_id: 'prod-1', name: 'Laptop', quantity: 1, price: 999.99 },
            { product_id: 'prod-2', name: 'Monitor', quantity: 1, price: 300.00 }
          ],
          created_at: new Date().toISOString()
        }
      },
      {
        id: 'template-3',
        name: 'Pending Order',
        description: 'Order with pending status that fails conditions',
        data: {
          id: 'order-pending',
          order_number: 'ORD-3000',
          customer_name: 'Alice Brown',
          customer_email: 'alice@example.com',
          total: 199.99,
          status: 'pending',
          created_at: new Date().toISOString()
        }
      }
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    
    if (this.workflowId && !this.workflow) {
      this.loadWorkflow();
    }
  }

  async loadWorkflow() {
    this.loading = true;
    
    try {
      const response = await fetch(`/api/workflows/${this.workflowId}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.workflow = await response.json();
      
      // Generate default test data based on workflow trigger
      this._generateDefaultTestData();
      
    } catch (err) {
      console.error('Failed to load workflow:', err);
      this.error = `Error loading workflow: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  _generateDefaultTestData() {
    // In a real implementation, this would be more sophisticated based on the entity type
    // For now, we'll just use a simple template
    
    const entityType = this.workflow?.trigger?.entity_type;
    if (!entityType) return;
    
    const defaultTemplates = {
      'order': {
        id: `order-${Date.now()}`,
        order_number: `ORD-${Math.floor(10000 + Math.random() * 90000)}`,
        customer_name: 'Test Customer',
        customer_email: 'test@example.com',
        total: 199.99,
        status: 'new',
        created_at: new Date().toISOString()
      },
      'customer': {
        id: `customer-${Date.now()}`,
        name: 'Test Customer',
        email: 'test@example.com',
        phone: '555-123-4567',
        status: 'active',
        created_at: new Date().toISOString()
      },
      'product': {
        id: `product-${Date.now()}`,
        name: 'Test Product',
        price: 99.99,
        stock: 5,
        category: 'test',
        updated_at: new Date().toISOString()
      }
    };
    
    this.entityData = defaultTemplates[entityType] || {};
  }

  handleTestModeChange(mode) {
    this.testMode = mode;
    
    if (mode === 'template' && !this.selectedTemplate) {
      // Auto-select first template
      this.selectedTemplate = this._testTemplates[0];
      this.entityData = JSON.parse(JSON.stringify(this.selectedTemplate.data));
    }
  }

  handleTemplateSelect(template) {
    this.selectedTemplate = template;
    this.entityData = JSON.parse(JSON.stringify(template.data));
  }

  handleEntityDataInput(e) {
    try {
      this.entityData = JSON.parse(e.target.value);
    } catch (err) {
      // Ignore JSON parse errors while typing
    }
  }

  async runSimulation() {
    this.loading = true;
    this.simulationResult = null;
    
    try {
      // In a real implementation, this would call an API
      // const response = await fetch(`/api/workflows/${this.workflow.id}/simulate`, {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify({
      //     operation: this.workflow.trigger.operations[0],
      //     entity_data: this.entityData
      //   })
      // });
      
      // if (!response.ok) {
      //   throw new Error(`API returned ${response.status}`);
      // }
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Generate a simulated result
      this.simulationResult = this._generateSimulationResult();
      
      // Switch to results tab
      this.activeTab = 'results';
      
      this._showNotification('Simulation completed successfully', 'success');
      
    } catch (err) {
      console.error('Failed to run simulation:', err);
      this.error = `Error running simulation: ${err.message}`;
      this._showNotification(`Error running simulation: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  _generateSimulationResult() {
    // This is a mock implementation that evaluates conditions and generates a simulated result
    const operation = this.workflow.trigger.operations[0];
    const entityType = this.workflow.trigger.entity_type;
    const entityData = this.entityData;
    
    // Evaluate conditions
    const conditions = this.workflow.trigger.conditions.map(condition => {
      let result = false;
      
      if (condition.type === 'field') {
        const fieldValue = entityData[condition.field];
        
        switch (condition.operator) {
          case 'eq':
            result = String(fieldValue) === condition.value;
            break;
          case 'neq':
            result = String(fieldValue) !== condition.value;
            break;
          case 'gt':
            result = Number(fieldValue) > Number(condition.value);
            break;
          case 'gte':
            result = Number(fieldValue) >= Number(condition.value);
            break;
          case 'lt':
            result = Number(fieldValue) < Number(condition.value);
            break;
          case 'lte':
            result = Number(fieldValue) <= Number(condition.value);
            break;
          case 'contains':
            result = String(fieldValue).includes(condition.value);
            break;
          case 'starts_with':
            result = String(fieldValue).startsWith(condition.value);
            break;
          case 'ends_with':
            result = String(fieldValue).endsWith(condition.value);
            break;
          default:
            result = false;
        }
      }
      
      return {
        ...condition,
        result,
        description: this._getConditionDescription(condition, entityData)
      };
    });
    
    // Check if all conditions pass
    const conditionsPass = conditions.every(c => c.result);
    
    // Determine which actions would execute
    let actions = [];
    
    if (conditionsPass) {
      // All conditions passed, actions would execute
      actions = this.workflow.actions.map(action => {
        // Apply a random success or failure for the email action to demonstrate both cases
        const isEmail = action.type === 'email';
        const success = !isEmail || Math.random() > 0.3;
        
        return {
          type: action.type,
          status: success ? 'success' : 'failure',
          config: { ...action },
          recipients: (action.recipients || []).map(r => ({
            ...r,
            status: success ? 'success' : 'failure'
          })),
          result: success 
            ? { 
                recipients_count: action.recipients?.length || 0,
                details: `Action would be successful with ${action.recipients?.length || 0} recipients`
              }
            : {
                error: 'Simulated failure',
                details: 'This is a simulated error to demonstrate the failure case'
              }
        };
      });
    }
    
    // Determine overall status
    let status = 'success';
    if (!conditionsPass) {
      status = 'failure';
    } else if (actions.some(a => a.status === 'failure')) {
      status = 'partial';
    }
    
    return {
      workflow_id: this.workflow.id,
      workflow_name: this.workflow.name,
      status,
      trigger: {
        entity_type: entityType,
        operation,
        entity_id: entityData.id,
        data: entityData
      },
      conditions,
      actions,
      conditions_result: conditionsPass,
      simulation_time: new Date().toISOString()
    };
  }

  _getConditionDescription(condition, data) {
    if (condition.type !== 'field') return '';
    
    const fieldValue = data[condition.field];
    const operators = {
      'eq': 'equal to',
      'neq': 'not equal to',
      'gt': 'greater than',
      'gte': 'greater than or equal to',
      'lt': 'less than',
      'lte': 'less than or equal to',
      'contains': 'contains',
      'starts_with': 'starts with',
      'ends_with': 'ends with'
    };
    
    return `${condition.field} (${fieldValue}) is ${operators[condition.operator]} ${condition.value}`;
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

  renderEditorTab() {
    if (!this.workflow) return html``;
    
    return html`
      <div class="info-grid">
        <wa-card class="info-card">
          <h3>Workflow Information</h3>
          <div><strong>Name:</strong> ${this.workflow.name}</div>
          <div><strong>Entity Type:</strong> ${this.workflow.trigger.entity_type}</div>
          <div><strong>Operations:</strong> ${this.workflow.trigger.operations.join(', ')}</div>
          <div><strong>Actions:</strong> ${this.workflow.actions.length}</div>
        </wa-card>
        
        <wa-card class="info-card">
          <h3>Test Configuration</h3>
          <div>Select how you want to provide test data for the simulation.</div>
          
          <div class="test-options">
            <div 
              class="test-option ${this.testMode === 'custom' ? 'selected' : ''}"
              @click=${() => this.handleTestModeChange('custom')}>
              <wa-icon name="edit" class="test-icon"></wa-icon>
              <div>Custom Data</div>
              <small>Create your own test data</small>
            </div>
            
            <div 
              class="test-option ${this.testMode === 'template' ? 'selected' : ''}"
              @click=${() => this.handleTestModeChange('template')}>
              <wa-icon name="dashboard_customize" class="test-icon"></wa-icon>
              <div>Templates</div>
              <small>Use predefined templates</small>
            </div>
          </div>
        </wa-card>
      </div>
      
      ${this.testMode === 'template' ? html`
        <h2 class="section-title">Select a Template</h2>
        
        <div class="template-list">
          ${this._testTemplates.map(template => html`
            <wa-card 
              class="template-card ${this.selectedTemplate?.id === template.id ? 'selected' : ''}"
              @click=${() => this.handleTemplateSelect(template)}>
              <div style="padding: 16px;">
                <h3 style="margin-top: 0;">${template.name}</h3>
                <p>${template.description}</p>
                <div style="margin-top: 16px; text-align: right;">
                  <wa-button 
                    variant=${this.selectedTemplate?.id === template.id ? 'filled' : 'outlined'}>
                    ${this.selectedTemplate?.id === template.id ? 'Selected' : 'Select'}
                  </wa-button>
                </div>
              </div>
            </wa-card>
          `)}
        </div>
        
        ${this.selectedTemplate ? html`
          <div style="margin-top: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <h3 style="margin: 0;">Template Preview</h3>
              <wa-button variant="text" color="primary" @click=${() => this.activeTab = 'editor'}>
                <wa-icon slot="prefix" name="edit"></wa-icon>
                Edit Data
              </wa-button>
            </div>
            
            <pre class="code-block">${JSON.stringify(this.entityData, null, 2)}</pre>
          </div>
        ` : ''}
      ` : html`
        <h2 class="section-title">Test Data Editor</h2>
        
        <div>
          <div style="margin-bottom: 16px;">
            <p>Edit the JSON data below to create custom test data for your workflow simulation.</p>
            <p>This data represents a ${this.workflow.trigger.entity_type} entity that will trigger the workflow.</p>
          </div>
          
          <wa-textarea 
            class="json-editor"
            .value=${JSON.stringify(this.entityData, null, 2)}
            @input=${this.handleEntityDataInput}>
          </wa-textarea>
        </div>
      `}
      
      <div style="margin-top: 24px; display: flex; justify-content: flex-end;">
        <wa-button @click=${this.runSimulation}>
          <wa-icon slot="prefix" name="play_arrow"></wa-icon>
          Run Simulation
        </wa-button>
      </div>
    `;
  }

  renderResultsTab() {
    if (!this.simulationResult) {
      return html`
        <div class="empty-state">
          <wa-icon name="science" class="empty-state-icon"></wa-icon>
          <h3>No simulation results</h3>
          <p>Run a simulation to see the results here.</p>
          <wa-button @click=${() => this.activeTab = 'editor'}>Configure Test Data</wa-button>
        </div>
      `;
    }
    
    return html`
      <div class="info-grid">
        <wa-card class="info-card">
          <h3>Simulation Summary</h3>
          <div><strong>Status:</strong> 
            <span class="status-badge ${this.simulationResult.status}">
              ${this.simulationResult.status}
            </span>
          </div>
          <div><strong>Entity Type:</strong> ${this.simulationResult.trigger.entity_type}</div>
          <div><strong>Operation:</strong> ${this.simulationResult.trigger.operation}</div>
          <div><strong>Timestamp:</strong> ${new Date(this.simulationResult.simulation_time).toLocaleString()}</div>
        </wa-card>
        
        <wa-card class="info-card">
          <h3>Results Overview</h3>
          <div><strong>Conditions:</strong> 
            ${this.simulationResult.conditions_result ? 
              html`<span style="color: var(--wa-success-color);">Passed</span>` : 
              html`<span style="color: var(--wa-error-color);">Failed</span>`}
          </div>
          <div><strong>Actions Tested:</strong> ${this.simulationResult.actions.length}</div>
          <div><strong>Successful Actions:</strong> 
            <span style="color: var(--wa-success-color);">
              ${this.simulationResult.actions.filter(a => a.status === 'success').length}
            </span>
          </div>
          <div><strong>Failed Actions:</strong> 
            <span style="color: var(--wa-error-color);">
              ${this.simulationResult.actions.filter(a => a.status === 'failure').length}
            </span>
          </div>
        </wa-card>
      </div>
      
      <h2 class="section-title">Condition Evaluation</h2>
      
      <wa-card>
        <div style="padding: 16px;">
          ${this.simulationResult.conditions.length === 0 ? html`
            <div style="padding: 16px; text-align: center; color: var(--wa-text-secondary-color);">
              No conditions defined. Workflow would trigger for all ${this.simulationResult.trigger.operation} operations on ${this.simulationResult.trigger.entity_type}.
            </div>
          ` : html`
            ${this.simulationResult.conditions.map(condition => html`
              <div class="condition-group">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-icon name="filter_alt"></wa-icon>
                    <strong>Field Condition</strong>
                    <span class="condition-result ${condition.result ? 'true' : 'false'}">
                      ${condition.result ? 'Passed' : 'Failed'}
                    </span>
                  </div>
                </div>
                
                <div style="margin-left: 32px;">${condition.description}</div>
              </div>
            `)}
          `}
        </div>
      </wa-card>
      
      <h2 class="section-title">Action Results</h2>
      
      ${!this.simulationResult.conditions_result ? html`
        <div class="empty-state" style="background-color: var(--wa-error-color-light); color: var(--wa-error-color);">
          <wa-icon name="block" class="empty-state-icon" style="color: var(--wa-error-color);"></wa-icon>
          <h3>Actions Skipped</h3>
          <p>All actions were skipped because one or more conditions failed.</p>
        </div>
      ` : this.simulationResult.actions.length === 0 ? html`
        <div class="empty-state">
          <wa-icon name="check_circle" class="empty-state-icon"></wa-icon>
          <h3>No Actions</h3>
          <p>This workflow doesn't have any actions defined.</p>
        </div>
      ` : html`
        ${this.simulationResult.actions.map(action => html`
          <wa-card class="action-item ${action.status}">
            <div>
              <div class="action-header">
                <div class="action-title">
                  <wa-icon name="${this._getActionTypeIcon(action.type)}"></wa-icon>
                  ${this._getActionTypeLabel(action.type)}
                  <span class="status-badge ${action.status}">
                    ${action.status}
                  </span>
                </div>
              </div>
              
              <div class="action-details">
                ${action.type === 'notification' ? html`
                  <div class="action-detail-row"><strong>Title:</strong> ${action.config.title}</div>
                  <div class="action-detail-row"><strong>Body:</strong> ${action.config.body}</div>
                  <div class="action-detail-row"><strong>Priority:</strong> ${action.config.priority}</div>
                ` : ''}
                
                ${action.type === 'email' ? html`
                  <div class="action-detail-row"><strong>Subject:</strong> ${action.config.subject}</div>
                  <div class="action-detail-row"><strong>Body:</strong> ${action.config.body}</div>
                ` : ''}
                
                <div style="margin-top: 12px;">
                  <strong>Result:</strong>
                  ${action.status === 'success' ? html`
                    <div style="color: var(--wa-success-color);">${action.result.details}</div>
                  ` : html`
                    <div class="error-message" style="color: var(--wa-error-color); background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1)); padding: 8px; border-radius: 4px;">
                      <div><strong>Error:</strong> ${action.result.error}</div>
                      <div>${action.result.details}</div>
                    </div>
                  `}
                </div>
              </div>
            </div>
          </wa-card>
        `)}
      `}
      
      <div style="margin-top: 24px; display: flex; gap: 16px; justify-content: flex-end;">
        <wa-button variant="outlined" @click=${() => this.activeTab = 'editor'}>
          <wa-icon slot="prefix" name="edit"></wa-icon>
          Modify Test Data
        </wa-button>
        
        <wa-button @click=${this.runSimulation}>
          <wa-icon slot="prefix" name="refresh"></wa-icon>
          Run Simulation Again
        </wa-button>
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return html`
        <div class="simulator-container">
          <div style="display: flex; justify-content: center; align-items: center; height: 400px;">
            <wa-spinner size="large"></wa-spinner>
          </div>
        </div>
      `;
    }
    
    if (this.error) {
      return html`
        <div class="simulator-container">
          <wa-alert type="error" style="margin-bottom: 20px;">
            ${this.error}
          </wa-alert>
          
          <div style="display: flex; justify-content: center; margin-top: 24px;">
            <wa-button @click=${() => this.loadWorkflow()}>
              <wa-icon slot="prefix" name="refresh"></wa-icon>
              Retry
            </wa-button>
          </div>
        </div>
      `;
    }
    
    if (!this.workflow) {
      return html`
        <div class="simulator-container">
          <div class="empty-state">
            <wa-icon name="search" class="empty-state-icon"></wa-icon>
            <h3>No workflow found</h3>
            <p>The requested workflow could not be found.</p>
          </div>
        </div>
      `;
    }
    
    return html`
      <div class="simulator-container">
        <div class="simulator-header">
          <div>
            <h1 class="simulator-title">Workflow Simulator</h1>
            <p class="simulator-subtitle">Test workflow behavior with sample data</p>
          </div>
          
          <wa-button variant="outlined" @click=${() => window.history.back()}>
            <wa-icon slot="prefix" name="arrow_back"></wa-icon>
            Back to Workflow
          </wa-button>
        </div>
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="editor">Data Editor</wa-tab>
          <wa-tab value="results">Simulation Results</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="editor" ?active=${this.activeTab === 'editor'}>
          ${this.renderEditorTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="results" ?active=${this.activeTab === 'results'}>
          ${this.renderResultsTab()}
        </wa-tab-panel>
      </div>
    `;
  }
}

customElements.define('wa-workflow-simulator', WebAwesomeWorkflowSimulator);