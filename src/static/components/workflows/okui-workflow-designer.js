/**
 * Workflow Designer component
 * 
 * A visual designer for creating and configuring workflows in the UNO framework.
 * Allows administrators to define triggers, conditions, actions, and recipients
 * for notification workflows.
 * 
 * @element okui-workflow-designer
 */
class OkuiWorkflowDesigner extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Initialize empty workflow definition
    this.workflow = {
      id: null,
      name: '',
      description: '',
      status: 'draft',
      triggers: [],
      conditions: [],
      actions: [],
      recipients: []
    };
    
    // Track UI state
    this.currentStep = 'info';  // info, triggers, conditions, actions, recipients, review
    this.isSaving = false;
    this.errors = {};
    
    // Bind methods
    this.handleStepChange = this.handleStepChange.bind(this);
    this.handleSave = this.handleSave.bind(this);
    this.handleInfoChange = this.handleInfoChange.bind(this);
    this.handleAddTrigger = this.handleAddTrigger.bind(this);
    this.handleAddCondition = this.handleAddCondition.bind(this);
    this.handleAddAction = this.handleAddAction.bind(this);
    this.handleAddRecipient = this.handleAddRecipient.bind(this);
    this.handleRemoveItem = this.handleRemoveItem.bind(this);
  }
  
  connectedCallback() {
    // Load workflow if ID is provided
    if (this.hasAttribute('workflow-id')) {
      const workflowId = this.getAttribute('workflow-id');
      this.loadWorkflow(workflowId);
    }
    
    this.render();
    this.setupEventListeners();
  }
  
  async loadWorkflow(workflowId) {
    try {
      // For demonstration, we'll load mock data instead of fetching from API
      setTimeout(() => {
        // Mock workflow data
        this.workflow = {
          id: workflowId,
          name: 'Sample Notification Workflow',
          description: 'This is an example workflow for notification purposes',
          status: 'draft',
          triggers: [
            {
              entity_type: 'order',
              operation: 'create',
              field_conditions: {
                'status': 'new',
                'total': '100'
              }
            }
          ],
          conditions: [
            {
              condition_type: 'time_based',
              condition_config: {
                value: 'business_hours'
              }
            }
          ],
          actions: [
            {
              type: 'notification',
              action_type: 'notification',
              title: 'New Order Created',
              body: 'A new order has been created and requires attention',
              priority: 'normal',
              order: 0,
              action_config: {
                title: 'New Order Created',
                body: 'A new order has been created and requires attention',
                priority: 'normal'
              }
            }
          ],
          recipients: [
            {
              recipient_type: 'role',
              recipient_id: 'sales_manager'
            }
          ]
        };
        this.render();
      }, 1000);
      
      // In a real implementation, uncomment the following
      /*
      const response = await fetch(`/api/workflows/${workflowId}`);
      if (!response.ok) {
        throw new Error(`Failed to load workflow: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.workflow = data;
      this.render();
      */
    } catch (error) {
      console.error('Error loading workflow:', error);
      this.showNotification('error', `Failed to load workflow: ${error.message}`);
    }
  }
  
  setupEventListeners() {
    // Navigation buttons
    this.shadowRoot.querySelectorAll('.step-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.handleStepChange(btn.dataset.step);
      });
    });
    
    // Save button
    const saveBtn = this.shadowRoot.querySelector('#save-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', this.handleSave);
    }
    
    // Info form inputs
    const infoForm = this.shadowRoot.querySelector('#info-form');
    if (infoForm) {
      infoForm.addEventListener('input', this.handleInfoChange);
    }
    
    // Add buttons
    const addTriggerBtn = this.shadowRoot.querySelector('#add-trigger-btn');
    if (addTriggerBtn) {
      addTriggerBtn.addEventListener('click', this.handleAddTrigger);
    }
    
    const addConditionBtn = this.shadowRoot.querySelector('#add-condition-btn');
    if (addConditionBtn) {
      addConditionBtn.addEventListener('click', this.handleAddCondition);
    }
    
    const addActionBtn = this.shadowRoot.querySelector('#add-action-btn');
    if (addActionBtn) {
      addActionBtn.addEventListener('click', this.handleAddAction);
    }
    
    const addRecipientBtn = this.shadowRoot.querySelector('#add-recipient-btn');
    if (addRecipientBtn) {
      addRecipientBtn.addEventListener('click', this.handleAddRecipient);
    }
    
    // Remove buttons
    this.shadowRoot.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const type = btn.dataset.type;
        const index = parseInt(btn.dataset.index);
        this.handleRemoveItem(type, index);
      });
    });
  }
  
  handleStepChange(step) {
    // Validate current step before proceeding
    if (this.validateStep(this.currentStep)) {
      this.currentStep = step;
      this.render();
      this.setupEventListeners();
    }
  }
  
  validateStep(step) {
    this.errors = {};
    
    switch (step) {
      case 'info':
        if (!this.workflow.name || this.workflow.name.trim() === '') {
          this.errors.name = 'Workflow name is required';
        }
        break;
        
      case 'triggers':
        if (this.workflow.triggers.length === 0) {
          this.errors.triggers = 'At least one trigger is required';
        }
        break;
        
      case 'actions':
        if (this.workflow.actions.length === 0) {
          this.errors.actions = 'At least one action is required';
        }
        break;
        
      case 'recipients':
        if (this.workflow.recipients.length === 0) {
          this.errors.recipients = 'At least one recipient is required';
        }
        break;
    }
    
    const hasErrors = Object.keys(this.errors).length > 0;
    
    if (hasErrors) {
      this.render(); // Re-render to show errors
      this.setupEventListeners();
    }
    
    return !hasErrors;
  }
  
  handleInfoChange(event) {
    const field = event.target.name;
    if (field && field in this.workflow) {
      this.workflow[field] = event.target.value;
    }
  }
  
  handleAddTrigger() {
    const entityTypeSelect = this.shadowRoot.querySelector('#trigger-entity-type');
    const operationSelect = this.shadowRoot.querySelector('#trigger-operation');
    
    if (entityTypeSelect && operationSelect) {
      const newTrigger = {
        entity_type: entityTypeSelect.value,
        operation: operationSelect.value,
        field_conditions: {}
      };
      
      // Get field conditions from form
      const fieldNameInput = this.shadowRoot.querySelector('#trigger-field-name');
      const fieldValueInput = this.shadowRoot.querySelector('#trigger-field-value');
      
      if (fieldNameInput && fieldValueInput && fieldNameInput.value) {
        newTrigger.field_conditions[fieldNameInput.value] = fieldValueInput.value;
      }
      
      this.workflow.triggers.push(newTrigger);
      this.render();
      this.setupEventListeners();
    }
  }
  
  handleAddCondition() {
    const typeSelect = this.shadowRoot.querySelector('#condition-type');
    const valueInput = this.shadowRoot.querySelector('#condition-value');
    
    if (typeSelect && valueInput) {
      const newCondition = {
        condition_type: typeSelect.value,
        condition_config: {
          value: valueInput.value
        }
      };
      
      this.workflow.conditions.push(newCondition);
      this.render();
      this.setupEventListeners();
    }
  }
  
  handleAddAction() {
    const typeSelect = this.shadowRoot.querySelector('#action-type');
    const messageInput = this.shadowRoot.querySelector('#action-message');
    
    if (typeSelect && messageInput) {
      const newAction = {
        action_type: typeSelect.value,
        action_config: {
          message: messageInput.value
        },
        order: this.workflow.actions.length
      };
      
      this.workflow.actions.push(newAction);
      this.render();
      this.setupEventListeners();
    }
  }
  
  handleAddRecipient() {
    const typeSelect = this.shadowRoot.querySelector('#recipient-type');
    const idInput = this.shadowRoot.querySelector('#recipient-id');
    
    if (typeSelect && idInput) {
      const newRecipient = {
        recipient_type: typeSelect.value,
        recipient_id: idInput.value
      };
      
      this.workflow.recipients.push(newRecipient);
      this.render();
      this.setupEventListeners();
    }
  }
  
  handleRemoveItem(type, index) {
    if (type === 'trigger' && index < this.workflow.triggers.length) {
      this.workflow.triggers.splice(index, 1);
    } else if (type === 'condition' && index < this.workflow.conditions.length) {
      this.workflow.conditions.splice(index, 1);
    } else if (type === 'action' && index < this.workflow.actions.length) {
      this.workflow.actions.splice(index, 1);
    } else if (type === 'recipient' && index < this.workflow.recipients.length) {
      this.workflow.recipients.splice(index, 1);
    }
    
    this.render();
    this.setupEventListeners();
  }
  
  async handleSave() {
    // Validate all steps
    const infoValid = this.validateStep('info');
    const triggersValid = this.validateStep('triggers');
    const actionsValid = this.validateStep('actions');
    const recipientsValid = this.validateStep('recipients');
    
    if (!(infoValid && triggersValid && actionsValid && recipientsValid)) {
      this.showNotification('error', 'Please fix the validation errors before saving.');
      return;
    }
    
    this.isSaving = true;
    this.render();
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Generate an ID if this is a new workflow
      if (!this.workflow.id) {
        this.workflow.id = 'wf-' + Math.floor(Math.random() * 10000);
      }
      
      // Add timestamps
      this.workflow.updated_at = new Date().toISOString();
      if (!this.workflow.created_at) {
        this.workflow.created_at = new Date().toISOString();
      }
      
      this.showNotification('success', 'Workflow saved successfully!');
      
      // In a real implementation, we would redirect after successful save
      // Simulate by showing an alert
      setTimeout(() => {
        alert('In a real implementation, you would be redirected to the workflow dashboard after saving.');
      }, 1000);
      
      // Uncomment in a real implementation
      /*
      const url = this.workflow.id 
        ? `/api/workflows/${this.workflow.id}` 
        : '/api/workflows';
      
      const method = this.workflow.id ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.workflow)
      });
      
      if (!response.ok) {
        throw new Error(`Save failed: ${response.statusText}`);
      }
      
      const savedWorkflow = await response.json();
      this.workflow = savedWorkflow;
      
      this.showNotification('success', 'Workflow saved successfully!');
      
      // Redirect to dashboard if this was a new workflow
      if (method === 'POST') {
        window.location.href = '/admin/workflows';
      }
      */
    } catch (error) {
      console.error('Error saving workflow:', error);
      this.showNotification('error', `Failed to save workflow: ${error.message}`);
    } finally {
      this.isSaving = false;
      this.render();
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
  
  renderInfoStep() {
    return `
      <div class="step-content">
        <form id="info-form">
          <div class="form-group ${this.errors.name ? 'has-error' : ''}">
            <label for="name">Workflow Name</label>
            <input 
              type="text" 
              id="name" 
              name="name" 
              value="${this.workflow.name}" 
              placeholder="Enter workflow name"
            >
            ${this.errors.name ? `<div class="error-message">${this.errors.name}</div>` : ''}
          </div>
          
          <div class="form-group">
            <label for="description">Description</label>
            <textarea 
              id="description" 
              name="description" 
              placeholder="Enter workflow description"
            >${this.workflow.description}</textarea>
          </div>
          
          <div class="form-group">
            <label for="status">Status</label>
            <select id="status" name="status">
              <option value="draft" ${this.workflow.status === 'draft' ? 'selected' : ''}>Draft</option>
              <option value="active" ${this.workflow.status === 'active' ? 'selected' : ''}>Active</option>
              <option value="inactive" ${this.workflow.status === 'inactive' ? 'selected' : ''}>Inactive</option>
            </select>
          </div>
        </form>
      </div>
    `;
  }
  
  renderTriggersStep() {
    return `
      <div class="step-content">
        <h3>Configure Triggers</h3>
        <p>Define what events will trigger this workflow.</p>
        
        ${this.errors.triggers ? `<div class="error-message">${this.errors.triggers}</div>` : ''}
        
        <div class="card">
          <h4>Add Trigger</h4>
          <div class="form-row">
            <div class="form-group">
              <label for="trigger-entity-type">Entity Type</label>
              <select id="trigger-entity-type">
                <option value="user">User</option>
                <option value="order">Order</option>
                <option value="product">Product</option>
                <option value="document">Document</option>
                <option value="task">Task</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="trigger-operation">Operation</label>
              <select id="trigger-operation">
                <option value="create">Create</option>
                <option value="update">Update</option>
                <option value="delete">Delete</option>
              </select>
            </div>
          </div>
          
          <h4>Field Conditions (Optional)</h4>
          <div class="form-row">
            <div class="form-group">
              <label for="trigger-field-name">Field Name</label>
              <input type="text" id="trigger-field-name" placeholder="e.g., status">
            </div>
            
            <div class="form-group">
              <label for="trigger-field-value">Field Value</label>
              <input type="text" id="trigger-field-value" placeholder="e.g., approved">
            </div>
          </div>
          
          <button type="button" id="add-trigger-btn" class="btn primary">Add Trigger</button>
        </div>
        
        <div class="triggers-list">
          ${this.workflow.triggers.length === 0 ? 
            '<p class="empty-state">No triggers defined yet.</p>' : 
            this.workflow.triggers.map((trigger, index) => `
              <div class="list-item">
                <div class="list-item-content">
                  <div class="list-item-title">
                    ${trigger.entity_type.charAt(0).toUpperCase() + trigger.entity_type.slice(1)} ${trigger.operation}
                  </div>
                  <div class="list-item-subtitle">
                    ${Object.keys(trigger.field_conditions).length > 0 ? 
                      `When ${Object.entries(trigger.field_conditions).map(([key, value]) => `${key} = ${value}`).join(' AND ')}` : 
                      'No field conditions'
                    }
                  </div>
                </div>
                <button type="button" class="remove-btn" data-type="trigger" data-index="${index}">
                  Remove
                </button>
              </div>
            `).join('')
          }
        </div>
      </div>
    `;
  }
  
  renderConditionsStep() {
    return `
      <div class="step-content">
        <h3>Configure Conditions</h3>
        <p>Add additional conditions that must be met for the workflow to execute.</p>
        
        <div class="card">
          <h4>Add Condition</h4>
          <div class="form-row">
            <div class="form-group">
              <label for="condition-type">Condition Type</label>
              <select id="condition-type">
                <option value="field_value">Field Value</option>
                <option value="time_based">Time Based</option>
                <option value="role_based">Role Based</option>
                <option value="custom">Custom Logic</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="condition-value">Value</label>
              <input type="text" id="condition-value" placeholder="Condition value">
            </div>
          </div>
          
          <button type="button" id="add-condition-btn" class="btn primary">Add Condition</button>
        </div>
        
        <div class="conditions-list">
          ${this.workflow.conditions.length === 0 ? 
            '<p class="empty-state">No additional conditions defined. Default trigger conditions will be used.</p>' : 
            this.workflow.conditions.map((condition, index) => `
              <div class="list-item">
                <div class="list-item-content">
                  <div class="list-item-title">
                    ${condition.condition_type.charAt(0).toUpperCase() + condition.condition_type.slice(1).replace('_', ' ')}
                  </div>
                  <div class="list-item-subtitle">
                    ${condition.condition_config.value || 'No value provided'}
                  </div>
                </div>
                <button type="button" class="remove-btn" data-type="condition" data-index="${index}">
                  Remove
                </button>
              </div>
            `).join('')
          }
        </div>
      </div>
    `;
  }
  
  renderActionsStep() {
    return `
      <div class="step-content">
        <h3>Configure Actions</h3>
        <p>Define what actions should be taken when the workflow is triggered.</p>
        
        ${this.errors.actions ? `<div class="error-message">${this.errors.actions}</div>` : ''}
        
        <div class="card">
          <h4>Add Action</h4>
          <div class="form-row">
            <div class="form-group">
              <label for="action-type">Action Type</label>
              <select id="action-type">
                <option value="notification">In-App Notification</option>
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="webhook">Webhook</option>
                <option value="database_update">Database Update</option>
              </select>
            </div>
          </div>
          
          <div class="form-group">
            <label for="action-message">Message</label>
            <textarea id="action-message" placeholder="Enter message or payload"></textarea>
          </div>
          
          <button type="button" id="add-action-btn" class="btn primary">Add Action</button>
        </div>
        
        <div class="actions-list">
          ${this.workflow.actions.length === 0 ? 
            '<p class="empty-state">No actions defined yet.</p>' : 
            this.workflow.actions.map((action, index) => `
              <div class="list-item">
                <div class="list-item-content">
                  <div class="list-item-title">
                    ${action.action_type.charAt(0).toUpperCase() + action.action_type.slice(1).replace('_', ' ')}
                  </div>
                  <div class="list-item-subtitle">
                    ${action.action_config.message || 'No message provided'}
                  </div>
                </div>
                <div class="list-item-order">
                  Order: ${action.order + 1}
                </div>
                <button type="button" class="remove-btn" data-type="action" data-index="${index}">
                  Remove
                </button>
              </div>
            `).join('')
          }
        </div>
      </div>
    `;
  }
  
  renderRecipientsStep() {
    return `
      <div class="step-content">
        <h3>Configure Recipients</h3>
        <p>Define who should receive notifications or actions from this workflow.</p>
        
        ${this.errors.recipients ? `<div class="error-message">${this.errors.recipients}</div>` : ''}
        
        <div class="card">
          <h4>Add Recipient</h4>
          <div class="form-row">
            <div class="form-group">
              <label for="recipient-type">Recipient Type</label>
              <select id="recipient-type">
                <option value="user">User</option>
                <option value="role">Role</option>
                <option value="group">Group</option>
                <option value="attribute">By Attribute</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="recipient-id">ID or Value</label>
              <input type="text" id="recipient-id" placeholder="User ID, role name, etc.">
            </div>
          </div>
          
          <button type="button" id="add-recipient-btn" class="btn primary">Add Recipient</button>
        </div>
        
        <div class="recipients-list">
          ${this.workflow.recipients.length === 0 ? 
            '<p class="empty-state">No recipients defined yet.</p>' : 
            this.workflow.recipients.map((recipient, index) => `
              <div class="list-item">
                <div class="list-item-content">
                  <div class="list-item-title">
                    ${recipient.recipient_type.charAt(0).toUpperCase() + recipient.recipient_type.slice(1)}
                  </div>
                  <div class="list-item-subtitle">
                    ${recipient.recipient_id}
                  </div>
                </div>
                <button type="button" class="remove-btn" data-type="recipient" data-index="${index}">
                  Remove
                </button>
              </div>
            `).join('')
          }
        </div>
      </div>
    `;
  }
  
  renderReviewStep() {
    return `
      <div class="step-content">
        <h3>Review and Save</h3>
        <p>Review your workflow configuration before saving.</p>
        
        <div class="review-section">
          <h4>Basic Information</h4>
          <div class="review-item">
            <div class="review-label">Name:</div>
            <div class="review-value">${this.workflow.name}</div>
          </div>
          <div class="review-item">
            <div class="review-label">Description:</div>
            <div class="review-value">${this.workflow.description || 'None'}</div>
          </div>
          <div class="review-item">
            <div class="review-label">Status:</div>
            <div class="review-value">${this.workflow.status}</div>
          </div>
        </div>
        
        <div class="review-section">
          <h4>Triggers (${this.workflow.triggers.length})</h4>
          ${this.workflow.triggers.length === 0 ? 
            '<p class="empty-state">No triggers defined.</p>' : 
            this.workflow.triggers.map(trigger => `
              <div class="review-item">
                <div class="review-value">
                  ${trigger.entity_type.charAt(0).toUpperCase() + trigger.entity_type.slice(1)} ${trigger.operation}
                  ${Object.keys(trigger.field_conditions).length > 0 ? 
                    ` when ${Object.entries(trigger.field_conditions).map(([key, value]) => `${key} = ${value}`).join(' AND ')}` : 
                    ''
                  }
                </div>
              </div>
            `).join('')
          }
        </div>
        
        <div class="review-section">
          <h4>Conditions (${this.workflow.conditions.length})</h4>
          ${this.workflow.conditions.length === 0 ? 
            '<p class="empty-state">No additional conditions defined.</p>' : 
            this.workflow.conditions.map(condition => `
              <div class="review-item">
                <div class="review-value">
                  ${condition.condition_type.charAt(0).toUpperCase() + condition.condition_type.slice(1).replace('_', ' ')}: 
                  ${condition.condition_config.value || 'No value provided'}
                </div>
              </div>
            `).join('')
          }
        </div>
        
        <div class="review-section">
          <h4>Actions (${this.workflow.actions.length})</h4>
          ${this.workflow.actions.length === 0 ? 
            '<p class="empty-state">No actions defined.</p>' : 
            this.workflow.actions.map(action => `
              <div class="review-item">
                <div class="review-value">
                  ${action.order + 1}. ${action.action_type.charAt(0).toUpperCase() + action.action_type.slice(1).replace('_', ' ')}: 
                  ${action.action_config.message || 'No message provided'}
                </div>
              </div>
            `).join('')
          }
        </div>
        
        <div class="review-section">
          <h4>Recipients (${this.workflow.recipients.length})</h4>
          ${this.workflow.recipients.length === 0 ? 
            '<p class="empty-state">No recipients defined.</p>' : 
            this.workflow.recipients.map(recipient => `
              <div class="review-item">
                <div class="review-value">
                  ${recipient.recipient_type.charAt(0).toUpperCase() + recipient.recipient_type.slice(1)}: 
                  ${recipient.recipient_id}
                </div>
              </div>
            `).join('')
          }
        </div>
        
        <div class="form-actions">
          <button type="button" id="save-btn" class="btn primary" ${this.isSaving ? 'disabled' : ''}>
            ${this.isSaving ? 'Saving...' : 'Save Workflow'}
          </button>
        </div>
      </div>
    `;
  }
  
  render() {
    const stepButtonClass = (step) => {
      return `step-btn ${this.currentStep === step ? 'active' : ''}`;
    };
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--wa-font-family, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif);
          color: var(--wa-text-color, #333);
          background-color: var(--wa-background-color, #fff);
          --primary-color: var(--wa-primary-color, #3f51b5);
          --error-color: var(--wa-error-color, #f44336);
          --success-color: var(--wa-success-color, #4caf50);
          --border-color: var(--wa-border-color, #e0e0e0);
          --card-shadow: var(--wa-card-shadow, 0 2px 4px rgba(0, 0, 0, 0.1));
        }
        
        .workflow-designer {
          padding: 20px;
        }
        
        .designer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        
        .designer-title {
          font-size: 24px;
          font-weight: 500;
          margin: 0;
        }
        
        .designer-subtitle {
          color: #666;
          margin: 5px 0 0;
        }
        
        .workflow-steps {
          display: flex;
          border-bottom: 1px solid var(--border-color);
          margin-bottom: 20px;
        }
        
        .step-btn {
          padding: 12px 20px;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 16px;
          color: #666;
          position: relative;
        }
        
        .step-btn.active {
          color: var(--primary-color);
          font-weight: 500;
        }
        
        .step-btn.active::after {
          content: '';
          position: absolute;
          bottom: -1px;
          left: 0;
          width: 100%;
          height: 3px;
          background-color: var(--primary-color);
        }
        
        .step-content {
          margin-bottom: 30px;
        }
        
        h3 {
          font-size: 18px;
          margin: 0 0 10px;
        }
        
        h4 {
          font-size: 16px;
          margin: 15px 0 10px;
        }
        
        p {
          margin: 0 0 15px;
          color: #666;
        }
        
        .card {
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          padding: 20px;
          margin-bottom: 20px;
        }
        
        .form-group {
          margin-bottom: 15px;
        }
        
        .form-row {
          display: flex;
          gap: 15px;
          margin-bottom: 15px;
        }
        
        .form-row .form-group {
          flex: 1;
        }
        
        label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
        }
        
        input, select, textarea {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          font-size: 16px;
        }
        
        textarea {
          min-height: 100px;
          resize: vertical;
        }
        
        .btn {
          padding: 10px 16px;
          border: none;
          border-radius: 4px;
          font-size: 16px;
          cursor: pointer;
          background-color: #f5f5f5;
          color: #333;
        }
        
        .btn.primary {
          background-color: var(--primary-color);
          color: white;
        }
        
        .btn[disabled] {
          opacity: 0.7;
          cursor: not-allowed;
        }
        
        .form-group.has-error input,
        .form-group.has-error select,
        .form-group.has-error textarea {
          border-color: var(--error-color);
        }
        
        .error-message {
          color: var(--error-color);
          font-size: 14px;
          margin-top: 5px;
        }
        
        .list-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          margin-bottom: 8px;
        }
        
        .list-item-title {
          font-weight: 500;
        }
        
        .list-item-subtitle {
          font-size: 14px;
          color: #666;
        }
        
        .remove-btn {
          padding: 6px 12px;
          background-color: transparent;
          border: 1px solid #d32f2f;
          color: #d32f2f;
          border-radius: 4px;
          cursor: pointer;
        }
        
        .empty-state {
          font-style: italic;
          color: #999;
          padding: 10px 0;
        }
        
        .review-section {
          margin-bottom: 20px;
        }
        
        .review-item {
          display: flex;
          margin-bottom: 8px;
        }
        
        .review-label {
          font-weight: 500;
          width: 120px;
        }
        
        .review-value {
          flex: 1;
        }
        
        .form-actions {
          margin-top: 30px;
          display: flex;
          justify-content: flex-end;
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
      
      <div class="workflow-designer">
        <div class="designer-header">
          <div>
            <h2 class="designer-title">${this.workflow.id ? 'Edit Workflow' : 'Create New Workflow'}</h2>
            <p class="designer-subtitle">Configure your notification workflow</p>
          </div>
        </div>
        
        <div class="workflow-steps">
          <button type="button" class="${stepButtonClass('info')}" data-step="info">Basic Info</button>
          <button type="button" class="${stepButtonClass('triggers')}" data-step="triggers">Triggers</button>
          <button type="button" class="${stepButtonClass('conditions')}" data-step="conditions">Conditions</button>
          <button type="button" class="${stepButtonClass('actions')}" data-step="actions">Actions</button>
          <button type="button" class="${stepButtonClass('recipients')}" data-step="recipients">Recipients</button>
          <button type="button" class="${stepButtonClass('review')}" data-step="review">Review</button>
        </div>
        
        ${
          this.currentStep === 'info' ? this.renderInfoStep() :
          this.currentStep === 'triggers' ? this.renderTriggersStep() :
          this.currentStep === 'conditions' ? this.renderConditionsStep() :
          this.currentStep === 'actions' ? this.renderActionsStep() :
          this.currentStep === 'recipients' ? this.renderRecipientsStep() :
          this.renderReviewStep()
        }
      </div>
    `;
  }
}

// Define the new element
customElements.define('okui-workflow-designer', OkuiWorkflowDesigner);