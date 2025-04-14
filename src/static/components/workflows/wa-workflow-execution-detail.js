import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element wa-workflow-execution-detail
 * @description A component for viewing detailed workflow execution results
 * @property {Object} execution - The execution record
 * @property {String} workflowId - ID of the workflow
 * @property {String} executionId - ID of the execution
 */
export class WebAwesomeWorkflowExecutionDetail extends LitElement {
  static get properties() {
    return {
      execution: { type: Object },
      workflowId: { type: String },
      executionId: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      activeTab: { type: String },
      showTriggerDataDialog: { type: Boolean },
      showRetryDialog: { type: Boolean },
      actionToRetry: { type: Object }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --detail-bg: var(--wa-background-color, #f5f5f5);
        --detail-padding: 20px;
        --section-gap: 24px;
      }
      .detail-container {
        padding: var(--detail-padding);
        background-color: var(--detail-bg);
        min-height: 600px;
      }
      .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--section-gap);
      }
      .detail-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .detail-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 8px 0 0 0;
      }
      .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin-bottom: var(--section-gap);
      }
      .info-card {
        display: flex;
        flex-direction: column;
      }
      .info-card-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0 0 16px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .info-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .info-item:last-child {
        border-bottom: none;
      }
      .info-label {
        color: var(--wa-text-secondary-color, #757575);
      }
      .info-value {
        font-weight: 500;
        color: var(--wa-text-primary-color, #212121);
      }
      .section-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0 0 16px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .actions-list {
        margin-bottom: var(--section-gap);
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
      .code-block {
        background-color: var(--wa-hover-color, #f5f5f5);
        padding: 12px;
        border-radius: 4px;
        font-family: monospace;
        white-space: pre-wrap;
        overflow-x: auto;
        margin-top: 8px;
      }
      .meta-info {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .error-message {
        color: var(--wa-error-color, #f44336);
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        padding: 8px 12px;
        border-radius: 4px;
        margin-top: 8px;
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
      .timeline {
        position: relative;
        margin-left: 20px;
        padding-left: 20px;
        margin-bottom: var(--section-gap);
      }
      .timeline::before {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 2px;
        background-color: var(--wa-border-color, #e0e0e0);
      }
      .timeline-item {
        position: relative;
        padding-bottom: 20px;
      }
      .timeline-item:last-child {
        padding-bottom: 0;
      }
      .timeline-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: -26px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: var(--wa-primary-color, #3f51b5);
      }
      .timeline-item.success::before {
        background-color: var(--wa-success-color, #4caf50);
      }
      .timeline-item.failure::before {
        background-color: var(--wa-error-color, #f44336);
      }
      .timeline-content {
        position: relative;
        padding: 12px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: 4px;
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      .timeline-time {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
        margin-bottom: 4px;
      }
      .timeline-title {
        font-weight: 500;
        margin-bottom: 8px;
      }
      .condition-details {
        margin-top: 16px;
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
      .json-viewer {
        max-height: 300px;
        overflow: auto;
      }
    `;
  }
  constructor() {
    super();
    this.execution = null;
    this.workflowId = null;
    this.executionId = null;
    this.loading = false;
    this.error = null;
    this.activeTab = 'summary';
    this.showTriggerDataDialog = false;
    this.showRetryDialog = false;
    this.actionToRetry = null;
    
    // Load mock data for demo purposes
    this._loadMockData();
  }
  _loadMockData() {
    // Mock execution data
    this.execution = {
      id: 'exec-12345',
      workflow_id: 'wf-789',
      workflow_name: 'New Order Notification',
      status: 'partial',
      trigger: {
        entity_type: 'order',
        operation: 'create',
        entity_id: 'order-67890',
        data: {
          id: 'order-67890',
          order_number: 'ORD-12345',
          customer_name: 'John Doe',
          customer_email: 'john.doe@example.com',
          total: 129.99,
          status: 'new',
          created_at: '2023-05-01T15:30:45Z'
        }
      },
      conditions: [
        {
          type: 'field',
          field: 'total',
          operator: 'gt',
          value: '100',
          result: true,
          description: 'Order total is greater than $100'
        },
        {
          type: 'field',
          field: 'status',
          operator: 'eq',
          value: 'new',
          result: true,
          description: 'Order status is "new"'
        }
      ],
      actions: [
        {
          id: 'action-1',
          type: 'notification',
          status: 'success',
          started_at: '2023-05-01T15:30:46Z',
          completed_at: '2023-05-01T15:30:47Z',
          duration_ms: 820,
          config: {
            title: 'New Order Created',
            body: 'A new order #ORD-12345 has been created.',
            priority: 'normal'
          },
          recipients: [
            { type: 'role', value: 'sales_manager', status: 'success' },
            { type: 'role', value: 'fulfillment', status: 'success' }
          ],
          result: {
            recipients_count: 5,
            details: 'Notification sent to 5 recipients'
          }
        },
        {
          id: 'action-2',
          type: 'email',
          status: 'failure',
          started_at: '2023-05-01T15:30:47Z',
          completed_at: '2023-05-01T15:30:48Z',
          duration_ms: 1240,
          config: {
            subject: 'New Order Notification',
            body: 'Hello,\n\nA new order #ORD-12345 has been created for John Doe.\n\nTotal: $129.99',
            template: 'default'
          },
          recipients: [
            { type: 'dynamic', value: 'order.customer.email', resolved_value: 'john.doe@example.com', status: 'failure' }
          ],
          result: {
            error: 'SMTP connection failed',
            details: 'Error sending email: Connection refused'
          }
        }
      ],
      timeline: [
        {
          timestamp: '2023-05-01T15:30:45Z',
          event: 'trigger',
          description: 'Workflow triggered by order creation'
        },
        {
          timestamp: '2023-05-01T15:30:45Z',
          event: 'condition_evaluation',
          description: 'Conditions evaluated',
          result: true
        },
        {
          timestamp: '2023-05-01T15:30:46Z',
          event: 'action_start',
          action_id: 'action-1',
          description: 'Started notification action'
        },
        {
          timestamp: '2023-05-01T15:30:47Z',
          event: 'action_complete',
          action_id: 'action-1',
          description: 'Completed notification action',
          result: true
        },
        {
          timestamp: '2023-05-01T15:30:47Z',
          event: 'action_start',
          action_id: 'action-2',
          description: 'Started email action'
        },
        {
          timestamp: '2023-05-01T15:30:48Z',
          event: 'action_error',
          action_id: 'action-2',
          description: 'Error sending email',
          error: 'SMTP connection failed',
          result: false
        },
        {
          timestamp: '2023-05-01T15:30:48Z',
          event: 'execution_complete',
          description: 'Workflow execution completed with partial success'
        }
      ],
      started_at: '2023-05-01T15:30:45Z',
      completed_at: '2023-05-01T15:30:48Z',
      duration_ms: 3240,
      actions_total: 2,
      actions_success: 1,
      actions_failed: 1
    };
  }
  connectedCallback() {
    super.connectedCallback();
    
    if (this.executionId && !this.execution) {
      this.loadExecution();
    }
  }
  async loadExecution() {
    this.loading = true;
    
    try {
      const response = await fetch(`/api/workflows/${this.workflowId}/executions/${this.executionId}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.execution = await response.json();
    } catch (err) {
      console.error('Failed to load execution details:', err);
      this.error = `Error loading execution details: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }
  handleTabChange(e) {
    this.activeTab = e.detail.value;
  }
  showTriggerData() {
    this.showTriggerDataDialog = true;
  }
  closeTriggerDataDialog() {
    this.showTriggerDataDialog = false;
  }
  showRetryActionDialog(action) {
    this.actionToRetry = action;
    this.showRetryDialog = true;
  }
  closeRetryDialog() {
    this.showRetryDialog = false;
    this.actionToRetry = null;
  }
  async retryAction() {
    if (!this.actionToRetry) return;
    
    this.loading = true;
    
    try {
      // In a real implementation, this would call an API
      // const response = await fetch(`/api/workflows/${this.workflowId}/executions/${this.executionId}/actions/${this.actionToRetry.id}/retry`, {
      //   method: 'POST'
      // });
      
      // if (!response.ok) {
      //   throw new Error(`API returned ${response.status}`);
      // }
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update local state to simulate success
      const actionIndex = this.execution.actions.findIndex(a => a.id === this.actionToRetry.id);
      if (actionIndex !== -1) {
        const updatedActions = [...this.execution.actions];
        updatedActions[actionIndex] = {
          ...this.actionToRetry,
          status: 'success',
          result: {
            recipients_count: this.actionToRetry.recipients?.length || 0,
            details: `Action retried successfully at ${new Date().toISOString()}`
          }
        };
        
        this.execution = {
          ...this.execution,
          actions: updatedActions,
          status: 'success',
          actions_failed: this.execution.actions_failed - 1,
          actions_success: this.execution.actions_success + 1
        };
      }
      
      this._showNotification('Action retried successfully', 'success');
      
    } catch (err) {
      console.error('Failed to retry action:', err);
      this._showNotification(`Error retrying action: ${err.message}`, 'error');
    } finally {
      this.loading = false;
      this.closeRetryDialog();
    }
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
  _formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  }
  
  _formatDuration(ms) {
    if (ms < 1000) {
      return `${ms}ms`;
    } else if (ms < 60000) {
      return `${(ms / 1000).toFixed(2)}s`;
    } else {
      const minutes = Math.floor(ms / 60000);
      const seconds = ((ms % 60000) / 1000).toFixed(1);
      return `${minutes}m ${seconds}s`;
    }
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
  _getRecipientTypeIcon(type) {
    switch (type) {
      case 'user': return 'person';
      case 'role': return 'security';
      case 'department': return 'people';
      case 'dynamic': return 'sync';
      default: return 'person';
    }
  }
  _getOperatorLabel(operator) {
    const operators = {
      'eq': 'equal to',
      'neq': 'not equal to',
      'gt': 'greater than',
      'gte': 'greater than or equal to',
      'lt': 'less than',
      'lte': 'less than or equal to',
      'contains': 'contains',
      'starts_with': 'starts with',
      'ends_with': 'ends with',
      'in': 'in',
      'not_in': 'not in'
    };
    
    return operators[operator] || operator;
  }
  renderTriggerDataDialog() {
    if (!this.showTriggerDataDialog || !this.execution?.trigger?.data) return html``;
    
    return html`
      <wa-dialog open @close=${this.closeTriggerDataDialog} style="width: 80vw; max-width: 800px;">
        <div slot="header">Trigger Data</div>
        
        <div>
          <div style="margin-bottom: 16px;">
            <div><strong>Entity Type:</strong> ${this.execution.trigger.entity_type}</div>
            <div><strong>Operation:</strong> ${this.execution.trigger.operation}</div>
            <div><strong>Entity ID:</strong> ${this.execution.trigger.entity_id}</div>
          </div>
          
          <div class="json-viewer">
            <pre class="code-block">${JSON.stringify(this.execution.trigger.data, null, 2)}</pre>
          </div>
        </div>
        
        <div slot="footer">
          <wa-button @click=${this.closeTriggerDataDialog}>Close</wa-button>
        </div>
      </wa-dialog>
    `;
  }
  renderRetryDialog() {
    if (!this.showRetryDialog || !this.actionToRetry) return html``;
    
    return html`
      <wa-dialog open @close=${this.closeRetryDialog}>
        <div slot="header">Retry Action</div>
        
        <div>
          <p>Are you sure you want to retry the following action?</p>
          <div style="margin-top: 16px;">
            <div><strong>Action Type:</strong> ${this._getActionTypeLabel(this.actionToRetry.type)}</div>
            <div><strong>Failed At:</strong> ${this._formatTimestamp(this.actionToRetry.completed_at)}</div>
            <div><strong>Error:</strong> ${this.actionToRetry.result?.error || 'Unknown error'}</div>
          </div>
          
          <div class="error-message">
            <wa-icon name="warning"></wa-icon>
            This will attempt to execute the action again. Recipients may receive duplicate notifications.
          </div>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeRetryDialog}>Cancel</wa-button>
          <wa-button color="warning" @click=${this.retryAction}>Retry Action</wa-button>
        </div>
      </wa-dialog>
    `;
  }
  renderSummaryTab() {
    if (!this.execution) return html``;
    
    return html`
      <div class="info-grid">
        <wa-card class="info-card">
          <div style="padding: 16px;">
            <h3 class="info-card-title">Execution Details</h3>
            
            <div class="info-item">
              <span class="info-label">Status</span>
              <span class="info-value">
                <span class="status-badge ${this.execution.status}">
                  ${this.execution.status}
                </span>
              </span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Trigger</span>
              <span class="info-value">
                ${this.execution.trigger.entity_type} ${this.execution.trigger.operation}
              </span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Entity ID</span>
              <span class="info-value">${this.execution.trigger.entity_id}</span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Started</span>
              <span class="info-value">${this._formatTimestamp(this.execution.started_at)}</span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Completed</span>
              <span class="info-value">${this._formatTimestamp(this.execution.completed_at)}</span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Duration</span>
              <span class="info-value">${this._formatDuration(this.execution.duration_ms)}</span>
            </div>
            
            <div style="margin-top: 16px; text-align: center;">
              <wa-button @click=${this.showTriggerData}>
                <wa-icon slot="prefix" name="data_object"></wa-icon>
                View Trigger Data
              </wa-button>
            </div>
          </div>
        </wa-card>
        
        <wa-card class="info-card">
          <div style="padding: 16px;">
            <h3 class="info-card-title">Execution Results</h3>
            
            <div class="info-item">
              <span class="info-label">Total Actions</span>
              <span class="info-value">${this.execution.actions_total}</span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Successful</span>
              <span class="info-value" style="color: var(--wa-success-color);">
                ${this.execution.actions_success}
              </span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Failed</span>
              <span class="info-value" style="color: var(--wa-error-color);">
                ${this.execution.actions_failed}
              </span>
            </div>
            
            <div class="info-item">
              <span class="info-label">Success Rate</span>
              <span class="info-value">
                ${Math.round((this.execution.actions_success / this.execution.actions_total) * 100)}%
              </span>
            </div>
            
            <div style="margin-top: 16px;">
              <div style="height: 8px; width: 100%; background-color: var(--wa-border-color); border-radius: 4px;">
                <div 
                  style="height: 100%; width: ${Math.round((this.execution.actions_success / this.execution.actions_total) * 100)}%; background-color: var(--wa-success-color); border-radius: 4px;">
                </div>
              </div>
            </div>
          </div>
        </wa-card>
      </div>
      
      <h2 class="section-title">Condition Evaluation</h2>
      
      ${(this.execution.conditions || []).length === 0 ? html`
        <div class="empty-state">
          <wa-icon name="filter_alt" class="empty-state-icon"></wa-icon>
          <h3>No conditions defined</h3>
          <p>This workflow has no trigger conditions and will execute for all matching events.</p>
        </div>
      ` : html`
        <wa-card>
          <div style="padding: 16px;">
            ${this.execution.conditions.map(condition => html`
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
                
                <div style="margin-left: 32px;">
                  <div>${condition.description || `${condition.field} ${this._getOperatorLabel(condition.operator)} ${condition.value}`}</div>
                </div>
              </div>
            `)}
          </div>
        </wa-card>
      `}
      
      <h2 class="section-title">Actions</h2>
      
      <div class="actions-list">
        ${this.execution.actions.map(action => html`
          <wa-card class="action-item ${action.status}">
            <div style="padding: 16px;">
              <div class="action-header">
                <div class="action-title">
                  <wa-icon name="${this._getActionTypeIcon(action.type)}"></wa-icon>
                  ${this._getActionTypeLabel(action.type)}
                  <span class="status-badge ${action.status}">
                    ${action.status}
                  </span>
                </div>
                <div class="meta-info">
                  ${this._formatDuration(action.duration_ms)}
                  ${action.status === 'failure' ? html`
                    <wa-button variant="text" color="warning" @click=${() => this.showRetryActionDialog(action)}>
                      <wa-icon slot="prefix" name="refresh"></wa-icon>
                      Retry
                    </wa-button>
                  ` : ''}
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
                  <div class="action-detail-row"><strong>Template:</strong> ${action.config.template}</div>
                  <div class="action-detail-row"><strong>Body:</strong> ${action.config.body}</div>
                ` : ''}
                
                ${action.type === 'webhook' ? html`
                  <div class="action-detail-row"><strong>URL:</strong> ${action.config.url}</div>
                  <div class="action-detail-row"><strong>Method:</strong> ${action.config.method}</div>
                ` : ''}
                
                <div style="margin-top: 12px;">
                  <strong>Recipients:</strong>
                  ${(action.recipients || []).length === 0 ? html`
                    <div style="font-style: italic; color: var(--wa-text-secondary-color);">No recipients defined</div>
                  ` : html`
                    <div style="margin-top: 8px;">
                      ${action.recipients.map(recipient => html`
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                          <wa-icon name="${this._getRecipientTypeIcon(recipient.type)}"></wa-icon>
                          <div style="flex: 1;">
                            <strong>${recipient.type}:</strong> 
                            ${recipient.value}
                            ${recipient.resolved_value ? html` → ${recipient.resolved_value}` : ''}
                          </div>
                          <span class="status-badge ${recipient.status || 'success'}">
                            ${recipient.status || 'success'}
                          </span>
                        </div>
                      `)}
                    </div>
                  `}
                </div>
                
                <div style="margin-top: 12px;">
                  <strong>Result:</strong>
                  ${action.status === 'success' ? html`
                    <div style="color: var(--wa-success-color);">${action.result.details}</div>
                  ` : html`
                    <div class="error-message">
                      <div><strong>Error:</strong> ${action.result.error}</div>
                      <div>${action.result.details}</div>
                    </div>
                  `}
                </div>
              </div>
            </div>
          </wa-card>
        `)}
      </div>
    `;
  }
  renderTimelineTab() {
    if (!this.execution) return html``;
    
    return html`
      <div class="timeline">
        ${this.execution.timeline.map(event => html`
          <div class="timeline-item ${this._getTimelineItemStatus(event)}">
            <div class="timeline-content">
              <div class="timeline-time">${this._formatTimestamp(event.timestamp)}</div>
              <div class="timeline-title">${this._formatTimelineEvent(event)}</div>
              <div>${event.description}</div>
              
              ${event.error ? html`
                <div class="error-message">
                  ${event.error}
                </div>
              ` : ''}
            </div>
          </div>
        `)}
      </div>
    `;
  }
  _getTimelineItemStatus(event) {
    if (event.event === 'action_error' || (event.result === false && event.event !== 'condition_evaluation')) {
      return 'failure';
    }
    if (event.event === 'action_complete' || event.result === true) {
      return 'success';
    }
    return '';
  }
  _formatTimelineEvent(event) {
    switch (event.event) {
      case 'trigger':
        return 'Workflow Triggered';
      case 'condition_evaluation':
        return 'Conditions Evaluated';
      case 'action_start':
        return 'Action Started';
      case 'action_complete':
        return 'Action Completed';
      case 'action_error':
        return 'Action Failed';
      case 'execution_complete':
        return 'Execution Completed';
      default:
        return event.event.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  }
  renderJsonTab() {
    if (!this.execution) return html``;
    
    return html`
      <wa-card>
        <div style="padding: 16px;">
          <pre class="code-block">${JSON.stringify(this.execution, null, 2)}</pre>
          
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
    if (this.loading) {
      return html`
        <div class="detail-container">
          <div style="display: flex; justify-content: center; align-items: center; height: 400px;">
            <wa-spinner size="large"></wa-spinner>
          </div>
        </div>
      `;
    }
    
    if (this.error) {
      return html`
        <div class="detail-container">
          <wa-alert type="error" style="margin-bottom: 20px;">
            ${this.error}
          </wa-alert>
          
          <div style="display: flex; justify-content: center; margin-top: 24px;">
            <wa-button @click=${() => this.loadExecution()}>
              <wa-icon slot="prefix" name="refresh"></wa-icon>
              Retry
            </wa-button>
          </div>
        </div>
      `;
    }
    
    if (!this.execution) {
      return html`
        <div class="detail-container">
          <div class="empty-state">
            <wa-icon name="search" class="empty-state-icon"></wa-icon>
            <h3>No execution found</h3>
            <p>The requested workflow execution could not be found.</p>
          </div>
        </div>
      `;
    }
    
    return html`
      <div class="detail-container">
        <div class="detail-header">
          <div>
            <h1 class="detail-title">Workflow Execution Details</h1>
            <p class="detail-subtitle">${this.execution.workflow_name}</p>
          </div>
          
          <wa-button variant="outlined" @click=${() => window.history.back()}>
            <wa-icon slot="prefix" name="arrow_back"></wa-icon>
            Back to List
          </wa-button>
        </div>
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="summary">Summary</wa-tab>
          <wa-tab value="timeline">Timeline</wa-tab>
          <wa-tab value="json">JSON</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="summary" ?active=${this.activeTab === 'summary'}>
          ${this.renderSummaryTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="timeline" ?active=${this.activeTab === 'timeline'}>
          ${this.renderTimelineTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="json" ?active=${this.activeTab === 'json'}>
          ${this.renderJsonTab()}
        </wa-tab-panel>
        
        ${this.renderTriggerDataDialog()}
        ${this.renderRetryDialog()}
      </div>
    `;
  }
}
customElements.define('wa-workflow-execution-detail', WebAwesomeWorkflowExecutionDetail);