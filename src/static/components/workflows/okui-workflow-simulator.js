/**
 * Workflow Simulator component
 * 
 * A component for simulating workflow execution with custom test data
 * to verify behavior without actually triggering real actions.
 * 
 * @element okui-workflow-simulator
 */
class OkuiWorkflowSimulator extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Initialize state
    this.workflow = null;
    this.workflowId = null;
    this.loading = false;
    this.error = null;
    this.testMode = 'custom';
    this.entityData = {};
    this.simulationResult = null;
    this.activeTab = 'editor';
    this.selectedTemplate = null;
    
    // Bind methods
    this.handleTabChange = this.handleTabChange.bind(this);
    this.handleTestModeChange = this.handleTestModeChange.bind(this);
    this.handleTemplateSelect = this.handleTemplateSelect.bind(this);
    this.handleEntityDataInput = this.handleEntityDataInput.bind(this);
    this.runSimulation = this.runSimulation.bind(this);
    this.loadWorkflow = this.loadWorkflow.bind(this);
    
    // Load mock data for demonstration purposes
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
    if (this.hasAttribute('workflow-id')) {
      this.workflowId = this.getAttribute('workflow-id');
      this.loadWorkflow();
    }
    
    this.render();
  }
  
  async loadWorkflow() {
    this.loading = true;
    this.render();
    
    try {
      // Simulate loading delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // We already have mock data from the constructor
      // Just update it with the workflowId
      if (this.workflowId) {
        this.workflow.id = this.workflowId;
      }
      
      // Generate default test data based on workflow trigger
      this._generateDefaultTestData();
      
      // In a real implementation, uncomment the following
      /*
      const response = await fetch(`/api/workflows/${this.workflowId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load workflow: ${response.statusText}`);
      }
      
      this.workflow = await response.json();
      
      // Generate default test data based on workflow trigger
      this._generateDefaultTestData();
      */
    } catch (error) {
      console.error('Error loading workflow:', error);
      this.error = error.message;
    } finally {
      this.loading = false;
      this.render();
    }
  }
  
  _generateDefaultTestData() {
    // Generate default test data based on entity type
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
  
  handleTabChange(event) {
    const tabId = event.target.dataset.tab;
    if (tabId) {
      this.activeTab = tabId;
      this.render();
    }
  }
  
  handleTestModeChange(mode) {
    this.testMode = mode;
    
    if (mode === 'template' && !this.selectedTemplate) {
      // Auto-select first template
      this.selectedTemplate = this._testTemplates[0];
      this.entityData = JSON.parse(JSON.stringify(this.selectedTemplate.data));
    }
    
    this.render();
  }
  
  handleTemplateSelect(template) {
    this.selectedTemplate = template;
    this.entityData = JSON.parse(JSON.stringify(template.data));
    this.render();
  }
  
  handleEntityDataInput(event) {
    const textarea = event.target;
    try {
      this.entityData = JSON.parse(textarea.value);
    } catch (err) {
      // Ignore parse errors while typing
    }
  }
  
  async runSimulation() {
    this.loading = true;
    this.simulationResult = null;
    this.render();
    
    try {
      // In a real implementation, this would call an API
      // const response = await fetch(`/api/admin/workflows/${this.workflow.id}/simulate`, {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify({
      //     operation: this.workflow.trigger.operations[0],
      //     entity_data: this.entityData
      //   })
      // });
      
      // Simulate API call and processing time
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Generate a simulated result
      this.simulationResult = this._generateSimulationResult();
      
      // Switch to results tab
      this.activeTab = 'results';
      
      this.showNotification('success', 'Simulation completed successfully');
    } catch (error) {
      console.error('Error running simulation:', error);
      this.error = error.message;
      this.showNotification('error', `Failed to run simulation: ${error.message}`);
    } finally {
      this.loading = false;
      this.render();
    }
  }
  
  _generateSimulationResult() {
    // Mock implementation that evaluates conditions and generates a simulated result
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
        // For demo purposes, randomly simulate success or failure for email action
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
  
  getActionTypeLabel(type) {
    switch (type) {
      case 'notification': return 'In-App Notification';
      case 'email': return 'Email';
      case 'sms': return 'SMS';
      case 'webhook': return 'Webhook';
      case 'database_update': return 'Database Update';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  }
  
  showNotification(type, message) {
    // Simple notification display
    const notification = document.createElement('div');
    notification.className = `okui-notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }
  
  renderEditorTab() {
    const templateClass = (template) => 
      `template-card ${this.selectedTemplate?.id === template.id ? 'selected' : ''}`;
    
    const testOptionClass = (mode) => 
      `test-option ${this.testMode === mode ? 'selected' : ''}`;
    
    return `
      <div class="info-grid">
        <div class="info-card">
          <h3 class="info-card-title">Workflow Information</h3>
          <div class="info-item"><span class="info-label">Name:</span> <span class="info-value">${this.workflow.name}</span></div>
          <div class="info-item"><span class="info-label">Entity Type:</span> <span class="info-value">${this.workflow.trigger.entity_type}</span></div>
          <div class="info-item"><span class="info-label">Operations:</span> <span class="info-value">${this.workflow.trigger.operations.join(', ')}</span></div>
          <div class="info-item"><span class="info-label">Actions:</span> <span class="info-value">${this.workflow.actions.length}</span></div>
        </div>
        
        <div class="info-card">
          <h3 class="info-card-title">Test Configuration</h3>
          <p>Select how you want to provide test data for the simulation.</p>
          
          <div class="test-options">
            <div 
              class="${testOptionClass('custom')}"
              id="custom-option">
              <div class="test-icon">✏️</div>
              <div class="test-name">Custom Data</div>
              <div class="test-description">Create your own test data</div>
            </div>
            
            <div 
              class="${testOptionClass('template')}"
              id="template-option">
              <div class="test-icon">📋</div>
              <div class="test-name">Templates</div>
              <div class="test-description">Use predefined templates</div>
            </div>
          </div>
        </div>
      </div>
      
      ${this.testMode === 'template' ? `
        <h3 class="section-title">Select a Template</h3>
        
        <div class="template-list">
          ${this._testTemplates.map(template => `
            <div class="${templateClass(template)}" data-template-id="${template.id}">
              <h4 class="template-title">${template.name}</h4>
              <p class="template-description">${template.description}</p>
              <button type="button" class="btn ${this.selectedTemplate?.id === template.id ? 'primary' : 'secondary'} select-template-btn" data-template-id="${template.id}">
                ${this.selectedTemplate?.id === template.id ? 'Selected' : 'Select'}
              </button>
            </div>
          `).join('')}
        </div>
        
        ${this.selectedTemplate ? `
          <div class="preview-section">
            <div class="preview-header">
              <h3 class="section-title">Template Preview</h3>
              <button type="button" class="btn text" id="edit-json-btn">
                Edit Data
              </button>
            </div>
            
            <pre class="code-block">${JSON.stringify(this.entityData, null, 2)}</pre>
          </div>
        ` : ''}
      ` : `
        <h3 class="section-title">Test Data Editor</h3>
        
        <div class="editor-container">
          <p>Edit the JSON data below to create custom test data for your workflow simulation.</p>
          <p>This data represents a ${this.workflow.trigger.entity_type} entity that will trigger the workflow.</p>
          
          <textarea 
            class="json-editor" 
            id="json-editor"
          >${JSON.stringify(this.entityData, null, 2)}</textarea>
        </div>
      `}
      
      <div class="action-bar">
        <button type="button" class="btn primary" id="run-simulation-btn">
          Run Simulation
        </button>
      </div>
    `;
  }
  
  renderResultsTab() {
    if (!this.simulationResult) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon">🧪</div>
          <div class="empty-state-title">No simulation results</div>
          <div class="empty-state-message">Run a simulation to see the results here.</div>
          <button type="button" class="btn primary" id="go-to-editor-btn">Configure Test Data</button>
        </div>
      `;
    }
    
    return `
      <div class="info-grid">
        <div class="info-card">
          <h3 class="info-card-title">Simulation Summary</h3>
          <div class="info-item">
            <span class="info-label">Status:</span> 
            <span class="info-value">
              <span class="status-badge ${this.simulationResult.status}">
                ${this.simulationResult.status}
              </span>
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Entity Type:</span>
            <span class="info-value">${this.simulationResult.trigger.entity_type}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Operation:</span>
            <span class="info-value">${this.simulationResult.trigger.operation}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Timestamp:</span>
            <span class="info-value">${new Date(this.simulationResult.simulation_time).toLocaleString()}</span>
          </div>
        </div>
        
        <div class="info-card">
          <h3 class="info-card-title">Results Overview</h3>
          <div class="info-item">
            <span class="info-label">Conditions:</span>
            <span class="info-value ${this.simulationResult.conditions_result ? 'success-text' : 'error-text'}">
              ${this.simulationResult.conditions_result ? 'Passed' : 'Failed'}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Actions Tested:</span>
            <span class="info-value">${this.simulationResult.actions.length}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Successful:</span>
            <span class="info-value success-text">
              ${this.simulationResult.actions.filter(a => a.status === 'success').length}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Failed:</span>
            <span class="info-value error-text">
              ${this.simulationResult.actions.filter(a => a.status === 'failure').length}
            </span>
          </div>
        </div>
      </div>
      
      <h3 class="section-title">Condition Evaluation</h3>
      
      <div class="condition-section">
        ${this.simulationResult.conditions.length === 0 ? `
          <div class="empty-state">
            <div class="empty-state-message">No conditions defined. Workflow will trigger for all ${this.simulationResult.trigger.operation} operations on ${this.simulationResult.trigger.entity_type}.</div>
          </div>
        ` : `
          ${this.simulationResult.conditions.map(condition => `
            <div class="condition-card">
              <div class="condition-header">
                <div class="condition-title">Field Condition</div>
                <span class="condition-result ${condition.result ? 'true' : 'false'}">
                  ${condition.result ? 'Passed' : 'Failed'}
                </span>
              </div>
              <div class="condition-content">${condition.description}</div>
            </div>
          `).join('')}
        `}
      </div>
      
      <h3 class="section-title">Action Results</h3>
      
      <div class="action-section">
        ${!this.simulationResult.conditions_result ? `
          <div class="empty-state error">
            <div class="empty-state-icon">❌</div>
            <div class="empty-state-title">Actions Skipped</div>
            <div class="empty-state-message">All actions were skipped because one or more conditions failed.</div>
          </div>
        ` : this.simulationResult.actions.length === 0 ? `
          <div class="empty-state">
            <div class="empty-state-icon">ℹ️</div>
            <div class="empty-state-title">No Actions</div>
            <div class="empty-state-message">This workflow doesn't have any actions defined.</div>
          </div>
        ` : `
          ${this.simulationResult.actions.map(action => `
            <div class="action-card ${action.status}">
              <div class="action-header">
                <div class="action-title">
                  ${this.getActionTypeLabel(action.type)}
                  <span class="status-badge ${action.status}">${action.status}</span>
                </div>
              </div>
              
              <div class="action-details">
                ${action.type === 'notification' ? `
                  <div class="action-detail-row"><strong>Title:</strong> ${action.config.title}</div>
                  <div class="action-detail-row"><strong>Body:</strong> ${action.config.body}</div>
                  <div class="action-detail-row"><strong>Priority:</strong> ${action.config.priority}</div>
                ` : ''}
                
                ${action.type === 'email' ? `
                  <div class="action-detail-row"><strong>Subject:</strong> ${action.config.subject}</div>
                  <div class="action-detail-row"><strong>Body:</strong> ${action.config.body}</div>
                ` : ''}
                
                <div class="action-result">
                  <strong>Result:</strong>
                  ${action.status === 'success' ? `
                    <div class="success-text">${action.result.details}</div>
                  ` : `
                    <div class="error-message">
                      <div><strong>Error:</strong> ${action.result.error}</div>
                      <div>${action.result.details}</div>
                    </div>
                  `}
                </div>
              </div>
            </div>
          `).join('')}
        `}
      </div>
      
      <div class="action-bar">
        <button type="button" class="btn secondary" id="modify-data-btn">
          Modify Test Data
        </button>
        
        <button type="button" class="btn primary" id="run-again-btn">
          Run Simulation Again
        </button>
      </div>
    `;
  }
  
  setupEventListeners() {
    // Tab navigation
    this.shadowRoot.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', this.handleTabChange);
    });
    
    if (this.activeTab === 'editor') {
      // Test mode options
      const customOption = this.shadowRoot.querySelector('#custom-option');
      const templateOption = this.shadowRoot.querySelector('#template-option');
      
      if (customOption) {
        customOption.addEventListener('click', () => this.handleTestModeChange('custom'));
      }
      
      if (templateOption) {
        templateOption.addEventListener('click', () => this.handleTestModeChange('template'));
      }
      
      // Template selection
      this.shadowRoot.querySelectorAll('.select-template-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const templateId = e.target.dataset.templateId;
          const template = this._testTemplates.find(t => t.id === templateId);
          if (template) {
            this.handleTemplateSelect(template);
          }
        });
      });
      
      this.shadowRoot.querySelectorAll('.template-card').forEach(card => {
        card.addEventListener('click', (e) => {
          const templateId = card.dataset.templateId;
          const template = this._testTemplates.find(t => t.id === templateId);
          if (template) {
            this.handleTemplateSelect(template);
          }
        });
      });
      
      // Edit JSON button (in template mode)
      const editJsonBtn = this.shadowRoot.querySelector('#edit-json-btn');
      if (editJsonBtn) {
        editJsonBtn.addEventListener('click', () => {
          this.testMode = 'custom';
          this.render();
        });
      }
      
      // JSON editor
      const jsonEditor = this.shadowRoot.querySelector('#json-editor');
      if (jsonEditor) {
        jsonEditor.addEventListener('input', this.handleEntityDataInput);
      }
      
      // Run simulation button
      const runSimulationBtn = this.shadowRoot.querySelector('#run-simulation-btn');
      if (runSimulationBtn) {
        runSimulationBtn.addEventListener('click', this.runSimulation);
      }
    } else if (this.activeTab === 'results') {
      // Modify data button
      const modifyDataBtn = this.shadowRoot.querySelector('#modify-data-btn');
      if (modifyDataBtn) {
        modifyDataBtn.addEventListener('click', () => {
          this.activeTab = 'editor';
          this.render();
        });
      }
      
      // Go to editor button (when no results)
      const goToEditorBtn = this.shadowRoot.querySelector('#go-to-editor-btn');
      if (goToEditorBtn) {
        goToEditorBtn.addEventListener('click', () => {
          this.activeTab = 'editor';
          this.render();
        });
      }
      
      // Run again button
      const runAgainBtn = this.shadowRoot.querySelector('#run-again-btn');
      if (runAgainBtn) {
        runAgainBtn.addEventListener('click', this.runSimulation);
      }
    }
    
    // Back button
    const backBtn = this.shadowRoot.querySelector('#back-btn');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        window.history.back();
      });
    }
    
    // Retry button (on error)
    const retryBtn = this.shadowRoot.querySelector('#retry-btn');
    if (retryBtn) {
      retryBtn.addEventListener('click', this.loadWorkflow);
    }
  }
  
  render() {
    const tabClass = (tab) => `tab-btn ${this.activeTab === tab ? 'active' : ''}`;
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--wa-font-family, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif);
          color: var(--wa-text-color, #333);
          background-color: var(--wa-background-color, #f9f9f9);
          --primary-color: var(--wa-primary-color, #3f51b5);
          --success-color: var(--wa-success-color, #4caf50);
          --warning-color: var(--wa-warning-color, #ff9800);
          --error-color: var(--wa-error-color, #f44336);
          --border-color: var(--wa-border-color, #e0e0e0);
          --card-shadow: var(--wa-card-shadow, 0 2px 4px rgba(0, 0, 0, 0.1));
        }
        
        .simulator-container {
          padding: 20px;
        }
        
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .title-section {
          flex: 1;
        }
        
        .title {
          font-size: 24px;
          font-weight: 500;
          margin: 0;
        }
        
        .subtitle {
          color: #666;
          margin: 5px 0 0;
        }
        
        .back-btn {
          padding: 8px 16px;
          background-color: transparent;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .tabs {
          display: flex;
          border-bottom: 1px solid var(--border-color);
          margin-bottom: 24px;
        }
        
        .tab-btn {
          padding: 12px 20px;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 16px;
          color: #666;
          position: relative;
        }
        
        .tab-btn.active {
          color: var(--primary-color);
          font-weight: 500;
        }
        
        .tab-btn.active::after {
          content: '';
          position: absolute;
          bottom: -1px;
          left: 0;
          width: 100%;
          height: 3px;
          background-color: var(--primary-color);
        }
        
        .tab-content {
          display: none;
        }
        
        .tab-content.active {
          display: block;
        }
        
        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }
        
        .info-card {
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          padding: 20px;
        }
        
        .info-card-title {
          font-size: 18px;
          font-weight: 500;
          margin: 0 0 16px 0;
        }
        
        .info-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 12px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--border-color);
        }
        
        .info-item:last-of-type {
          border-bottom: none;
        }
        
        .info-label {
          color: #666;
        }
        
        .info-value {
          font-weight: 500;
        }
        
        .success-text {
          color: var(--success-color);
        }
        
        .error-text {
          color: var(--error-color);
        }
        
        .section-title {
          font-size: 18px;
          font-weight: 500;
          margin: 30px 0 16px 0;
        }
        
        .test-options {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          margin-top: 16px;
        }
        
        .test-option {
          flex: 1;
          min-width: 200px;
          padding: 16px;
          border: 2px solid var(--border-color);
          border-radius: 4px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .test-option:hover {
          background-color: #f5f5f5;
        }
        
        .test-option.selected {
          border-color: var(--primary-color);
          background-color: rgba(63, 81, 181, 0.05);
        }
        
        .test-icon {
          font-size: 24px;
          margin-bottom: 8px;
        }
        
        .test-name {
          font-weight: 500;
          margin-bottom: 4px;
        }
        
        .test-description {
          font-size: 14px;
          color: #666;
        }
        
        .template-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
          margin-bottom: 30px;
        }
        
        .template-card {
          padding: 16px;
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          cursor: pointer;
          border: 2px solid transparent;
          transition: all 0.2s ease;
        }
        
        .template-card:hover {
          border-color: var(--border-color);
          transform: translateY(-2px);
        }
        
        .template-card.selected {
          border-color: var(--primary-color);
          background-color: rgba(63, 81, 181, 0.05);
        }
        
        .template-title {
          font-size: 16px;
          font-weight: 500;
          margin: 0 0 8px 0;
        }
        
        .template-description {
          font-size: 14px;
          color: #666;
          margin: 0 0 16px 0;
        }
        
        .preview-section {
          margin-top: 30px;
        }
        
        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .editor-container {
          margin-bottom: 30px;
        }
        
        .json-editor {
          width: 100%;
          min-height: 300px;
          font-family: monospace;
          font-size: 14px;
          padding: 16px;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          resize: vertical;
        }
        
        .code-block {
          background-color: #f5f5f5;
          padding: 16px;
          border-radius: 4px;
          font-family: monospace;
          font-size: 14px;
          white-space: pre-wrap;
          overflow-x: auto;
        }
        
        .action-bar {
          display: flex;
          justify-content: flex-end;
          gap: 16px;
          margin-top: 30px;
        }
        
        .btn {
          padding: 10px 16px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
        }
        
        .btn.primary {
          background-color: var(--primary-color);
          color: white;
        }
        
        .btn.secondary {
          background-color: #f5f5f5;
          color: #333;
          border: 1px solid var(--border-color);
        }
        
        .btn.text {
          background-color: transparent;
          color: var(--primary-color);
          padding: 6px 12px;
        }
        
        .status-badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
        }
        
        .status-badge.success {
          background-color: rgba(76, 175, 80, 0.1);
          color: var(--success-color);
        }
        
        .status-badge.partial {
          background-color: rgba(255, 152, 0, 0.1);
          color: var(--warning-color);
        }
        
        .status-badge.failure {
          background-color: rgba(244, 67, 54, 0.1);
          color: var(--error-color);
        }
        
        .condition-section {
          margin-bottom: 30px;
        }
        
        .condition-card {
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          padding: 16px;
          margin-bottom: 16px;
        }
        
        .condition-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        
        .condition-title {
          font-weight: 500;
        }
        
        .condition-content {
          color: #666;
        }
        
        .condition-result {
          display: inline-block;
          padding: 2px 6px;
          border-radius: 10px;
          font-size: 12px;
        }
        
        .condition-result.true {
          background-color: rgba(76, 175, 80, 0.1);
          color: var(--success-color);
        }
        
        .condition-result.false {
          background-color: rgba(244, 67, 54, 0.1);
          color: var(--error-color);
        }
        
        .action-section {
          margin-bottom: 30px;
        }
        
        .action-card {
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          padding: 16px;
          margin-bottom: 16px;
          border-left: 4px solid var(--primary-color);
        }
        
        .action-card.success {
          border-left-color: var(--success-color);
        }
        
        .action-card.failure {
          border-left-color: var(--error-color);
        }
        
        .action-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .action-title {
          font-weight: 500;
          font-size: 16px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .action-details {
          margin-left: 0;
        }
        
        .action-detail-row {
          margin-bottom: 8px;
        }
        
        .action-result {
          margin-top: 16px;
        }
        
        .error-message {
          color: var(--error-color);
          background-color: rgba(244, 67, 54, 0.1);
          padding: 12px;
          border-radius: 4px;
          margin-top: 8px;
        }
        
        .empty-state {
          text-align: center;
          padding: 40px;
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          margin-bottom: 30px;
        }
        
        .empty-state.error {
          background-color: rgba(244, 67, 54, 0.05);
        }
        
        .empty-state-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }
        
        .empty-state-title {
          font-size: 18px;
          font-weight: 500;
          margin-bottom: 8px;
        }
        
        .empty-state-message {
          color: #666;
          margin-bottom: 16px;
        }
        
        .loading-state {
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 400px;
        }
        
        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(0, 0, 0, 0.1);
          border-radius: 50%;
          border-top-color: var(--primary-color);
          animation: spin 1s ease-in-out infinite;
          margin-bottom: 16px;
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        .error-state {
          text-align: center;
          padding: 40px;
        }
        
        /* Notification styling */
        .okui-notification {
          position: fixed;
          top: 20px;
          right: 20px;
          padding: 15px 25px;
          border-radius: 4px;
          background-color: #333;
          color: white;
          z-index: 1000;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .okui-notification.success {
          background-color: var(--success-color);
        }
        
        .okui-notification.error {
          background-color: var(--error-color);
        }
      </style>
      
      <div class="simulator-container">
        ${this.loading ? `
          <div class="loading-state">
            <div class="spinner"></div>
            <div>Loading...</div>
          </div>
        ` : this.error ? `
          <div class="error-state">
            <div class="error-message">
              <strong>Error:</strong> ${this.error}
            </div>
            <button type="button" class="btn primary" id="retry-btn" style="margin-top: 20px;">
              Try Again
            </button>
          </div>
        ` : this.workflow ? `
          <div class="header">
            <div class="title-section">
              <h2 class="title">Workflow Simulator</h2>
              <p class="subtitle">Test workflow behavior with sample data</p>
            </div>
            
            <button type="button" class="back-btn" id="back-btn">
              ← Back to Workflow
            </button>
          </div>
          
          <div class="tabs">
            <button type="button" class="${tabClass('editor')}" data-tab="editor">Data Editor</button>
            <button type="button" class="${tabClass('results')}" data-tab="results">Simulation Results</button>
          </div>
          
          <div class="tab-content ${this.activeTab === 'editor' ? 'active' : ''}" id="editor-tab">
            ${this.renderEditorTab()}
          </div>
          
          <div class="tab-content ${this.activeTab === 'results' ? 'active' : ''}" id="results-tab">
            ${this.renderResultsTab()}
          </div>
        ` : `
          <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <div class="empty-state-title">No workflow found</div>
            <div class="empty-state-message">The requested workflow could not be found.</div>
          </div>
        `}
      </div>
    `;
    
    this.setupEventListeners();
  }
}

// Define the new element
customElements.define('okui-workflow-simulator', OkuiWorkflowSimulator);