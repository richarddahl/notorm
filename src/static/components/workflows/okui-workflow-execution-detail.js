/**
 * Workflow Execution Detail component
 * 
 * A component for viewing detailed information about workflow executions
 * including triggers, conditions, actions taken, and results.
 * 
 * @element okui-workflow-execution-detail
 */
class OkuiWorkflowExecutionDetail extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Initialize state
    this.execution = null;
    this.workflowId = null;
    this.executionId = null;
    this.loading = false;
    this.error = null;
    this.activeTab = 'summary';
    this.showTriggerDataDialog = false;
    this.showRetryDialog = false;
    this.actionToRetry = null;
    
    // Bind methods
    this.handleTabChange = this.handleTabChange.bind(this);
    this.showTriggerData = this.showTriggerData.bind(this);
    this.closeTriggerDataDialog = this.closeTriggerDataDialog.bind(this);
    this.showRetryActionDialog = this.showRetryActionDialog.bind(this);
    this.closeRetryDialog = this.closeRetryDialog.bind(this);
    this.retryAction = this.retryAction.bind(this);
    this.loadExecution = this.loadExecution.bind(this);
    
    // For demonstration purposes, load mock data
    this._loadMockData();
  }
  
  _loadMockData() {
    // Mock execution data for demonstration
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
    if (this.hasAttribute('workflow-id')) {
      this.workflowId = this.getAttribute('workflow-id');
    }
    
    if (this.hasAttribute('execution-id')) {
      this.executionId = this.getAttribute('execution-id');
      this.loadExecution();
    }
    
    this.render();
  }
  
  async loadExecution() {
    this.loading = true;
    this.render();
    
    try {
      // Simulate loading delay
      await new Promise(resolve => setTimeout(resolve, 1200));
      
      // We don't need to fetch since we already loaded mock data in the constructor via _loadMockData()
      
      // In a real implementation, uncomment the following
      /*
      const response = await fetch(`/api/workflows/${this.workflowId}/executions/${this.executionId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load execution: ${response.statusText}`);
      }
      
      this.execution = await response.json();
      */
    } catch (error) {
      console.error('Error loading workflow execution:', error);
      this.error = error.message;
    } finally {
      this.loading = false;
      this.render();
    }
  }
  
  handleTabChange(event) {
    const tabId = event.target.dataset.tab;
    if (tabId) {
      this.activeTab = tabId;
      this.render();
    }
  }
  
  showTriggerData() {
    this.showTriggerDataDialog = true;
    this.render();
  }
  
  closeTriggerDataDialog() {
    this.showTriggerDataDialog = false;
    this.render();
  }
  
  showRetryActionDialog(action) {
    this.actionToRetry = action;
    this.showRetryDialog = true;
    this.render();
  }
  
  closeRetryDialog() {
    this.showRetryDialog = false;
    this.actionToRetry = null;
    this.render();
  }
  
  async retryAction() {
    if (!this.actionToRetry) return;
    
    this.loading = true;
    this.render();
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Update the action status in our mock data
      const actionIndex = this.execution.actions.findIndex(a => a.id === this.actionToRetry.id);
      if (actionIndex !== -1) {
        this.execution.actions[actionIndex].status = 'success';
        this.execution.actions[actionIndex].result = {
          recipients_count: this.execution.actions[actionIndex].recipients.length,
          details: 'Action retry was successful'
        };
        
        // Update recipient statuses
        this.execution.actions[actionIndex].recipients.forEach(r => {
          r.status = 'success';
        });
        
        // Update execution summary data
        this.execution.actions_success += 1;
        this.execution.actions_failed -= 1;
        
        // Update execution status if all actions now successful
        if (this.execution.actions_failed === 0) {
          this.execution.status = 'success';
        }
        
        // Add a timeline entry for the retry
        this.execution.timeline.push({
          timestamp: new Date().toISOString(),
          event: 'action_retry',
          action_id: this.actionToRetry.id,
          description: 'Action was retried manually',
          result: true
        });
      }
      
      this.showNotification('success', 'Action retried successfully');
      
      // In a real implementation, uncomment the following
      /*
      const response = await fetch(`/api/workflows/${this.workflowId}/executions/${this.executionId}/actions/${this.actionToRetry.id}/retry`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to retry action: ${response.statusText}`);
      }
      
      // Update the execution data to reflect the retry
      await this.loadExecution();
      */
    } catch (error) {
      console.error('Error retrying action:', error);
      this.showNotification('error', `Failed to retry action: ${error.message}`);
    } finally {
      this.loading = false;
      this.closeRetryDialog();
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
  
  formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  }
  
  formatDuration(ms) {
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
  
  getTimelineItemStatus(event) {
    if (event.event === 'action_error' || (event.result === false && event.event !== 'condition_evaluation')) {
      return 'failure';
    }
    if (event.event === 'action_complete' || event.result === true) {
      return 'success';
    }
    return '';
  }
  
  formatTimelineEvent(event) {
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
  
  getOperatorLabel(operator) {
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
  
  renderSummaryTab() {
    return `
      <div class="info-grid">
        <div class="info-card">
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
            <span class="info-value">${this.formatTimestamp(this.execution.started_at)}</span>
          </div>
          
          <div class="info-item">
            <span class="info-label">Completed</span>
            <span class="info-value">${this.formatTimestamp(this.execution.completed_at)}</span>
          </div>
          
          <div class="info-item">
            <span class="info-label">Duration</span>
            <span class="info-value">${this.formatDuration(this.execution.duration_ms)}</span>
          </div>
          
          <button type="button" class="btn secondary view-data-btn" id="view-trigger-data-btn">
            View Trigger Data
          </button>
        </div>
        
        <div class="info-card">
          <h3 class="info-card-title">Execution Results</h3>
          
          <div class="info-item">
            <span class="info-label">Total Actions</span>
            <span class="info-value">${this.execution.actions_total}</span>
          </div>
          
          <div class="info-item">
            <span class="info-label">Successful</span>
            <span class="info-value success-text">
              ${this.execution.actions_success}
            </span>
          </div>
          
          <div class="info-item">
            <span class="info-label">Failed</span>
            <span class="info-value error-text">
              ${this.execution.actions_failed}
            </span>
          </div>
          
          <div class="info-item">
            <span class="info-label">Success Rate</span>
            <span class="info-value">
              ${Math.round((this.execution.actions_success / this.execution.actions_total) * 100)}%
            </span>
          </div>
          
          <div class="progress-bar">
            <div 
              class="progress-bar-fill" 
              style="width: ${Math.round((this.execution.actions_success / this.execution.actions_total) * 100)}%;">
            </div>
          </div>
        </div>
      </div>
      
      <h3 class="section-title">Condition Evaluation</h3>
      
      ${this.execution.conditions.length === 0 ? `
        <div class="empty-state">
          <div class="empty-state-icon">⚙️</div>
          <div class="empty-state-title">No conditions defined</div>
          <div class="empty-state-message">This workflow has no trigger conditions and will execute for all matching events.</div>
        </div>
      ` : `
        <div class="condition-list">
          ${this.execution.conditions.map((condition, index) => `
            <div class="condition-card">
              <div class="condition-header">
                <div class="condition-title">Field Condition</div>
                <span class="condition-result ${condition.result ? 'true' : 'false'}">
                  ${condition.result ? 'Passed' : 'Failed'}
                </span>
              </div>
              
              <div class="condition-content">
                ${condition.description || `${condition.field} ${this.getOperatorLabel(condition.operator)} ${condition.value}`}
              </div>
            </div>
          `).join('')}
        </div>
      `}
      
      <h3 class="section-title">Actions</h3>
      
      <div class="actions-list">
        ${this.execution.actions.map((action, index) => `
          <div class="action-card ${action.status}">
            <div class="action-header">
              <div class="action-title">
                ${this.getActionTypeLabel(action.type)}
                <span class="status-badge ${action.status}">
                  ${action.status}
                </span>
              </div>
              <div class="action-meta">
                ${this.formatDuration(action.duration_ms)}
                ${action.status === 'failure' ? `
                  <button type="button" class="btn text warning retry-btn" data-action-index="${index}">
                    Retry
                  </button>
                ` : ''}
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
                <div class="action-detail-row"><strong>Template:</strong> ${action.config.template}</div>
                <div class="action-detail-row"><strong>Body:</strong> ${action.config.body}</div>
              ` : ''}
              
              <div class="action-detail-section">
                <strong>Recipients:</strong>
                ${(action.recipients || []).length === 0 ? `
                  <div class="no-recipients">No recipients defined</div>
                ` : `
                  <div class="recipients-list">
                    ${action.recipients.map(recipient => `
                      <div class="recipient-item">
                        <div class="recipient-info">
                          <strong>${recipient.type}:</strong> 
                          ${recipient.value}
                          ${recipient.resolved_value ? ` → ${recipient.resolved_value}` : ''}
                        </div>
                        <span class="status-badge ${recipient.status || 'success'}">
                          ${recipient.status || 'success'}
                        </span>
                      </div>
                    `).join('')}
                  </div>
                `}
              </div>
              
              <div class="action-detail-section">
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
      </div>
    `;
  }
  
  renderTimelineTab() {
    return `
      <div class="timeline">
        ${this.execution.timeline.map((event, index) => `
          <div class="timeline-item ${this.getTimelineItemStatus(event)}">
            <div class="timeline-content">
              <div class="timeline-time">${this.formatTimestamp(event.timestamp)}</div>
              <div class="timeline-title">${this.formatTimelineEvent(event)}</div>
              <div class="timeline-description">${event.description}</div>
              
              ${event.error ? `
                <div class="error-message">
                  ${event.error}
                </div>
              ` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }
  
  renderJsonTab() {
    return `
      <div class="json-view">
        <pre class="code-block">${JSON.stringify(this.execution, null, 2)}</pre>
      </div>
    `;
  }
  
  renderTriggerDataDialog() {
    if (!this.showTriggerDataDialog) return '';
    
    return `
      <div class="dialog-overlay" id="trigger-data-dialog">
        <div class="dialog">
          <div class="dialog-header">
            <h3 class="dialog-title">Trigger Data</h3>
            <button type="button" class="close-btn" id="close-trigger-data-btn">×</button>
          </div>
          
          <div class="dialog-content">
            <div class="trigger-info">
              <div class="trigger-detail"><strong>Entity Type:</strong> ${this.execution.trigger.entity_type}</div>
              <div class="trigger-detail"><strong>Operation:</strong> ${this.execution.trigger.operation}</div>
              <div class="trigger-detail"><strong>Entity ID:</strong> ${this.execution.trigger.entity_id}</div>
            </div>
            
            <div class="json-view">
              <pre class="code-block">${JSON.stringify(this.execution.trigger.data, null, 2)}</pre>
            </div>
          </div>
          
          <div class="dialog-footer">
            <button type="button" class="btn secondary" id="close-dialog-btn">Close</button>
          </div>
        </div>
      </div>
    `;
  }
  
  renderRetryDialog() {
    if (!this.showRetryDialog || !this.actionToRetry) return '';
    
    return `
      <div class="dialog-overlay" id="retry-dialog">
        <div class="dialog">
          <div class="dialog-header">
            <h3 class="dialog-title">Retry Action</h3>
            <button type="button" class="close-btn" id="close-retry-btn">×</button>
          </div>
          
          <div class="dialog-content">
            <p>Are you sure you want to retry the following action?</p>
            
            <div class="retry-action-info">
              <div><strong>Action Type:</strong> ${this.actionToRetry ? this.getActionTypeLabel(this.actionToRetry.type) : ''}</div>
              <div><strong>Failed At:</strong> ${this.actionToRetry ? this.formatTimestamp(this.actionToRetry.completed_at) : ''}</div>
              <div><strong>Error:</strong> ${this.actionToRetry?.result?.error || 'Unknown error'}</div>
            </div>
            
            <div class="warning-message">
              <strong>Warning:</strong> This will attempt to execute the action again. Recipients may receive duplicate notifications.
            </div>
          </div>
          
          <div class="dialog-footer">
            <button type="button" class="btn secondary" id="cancel-retry-btn">Cancel</button>
            <button type="button" class="btn warning" id="confirm-retry-btn">Retry Action</button>
          </div>
        </div>
      </div>
    `;
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
        
        .execution-detail {
          padding: 20px;
        }
        
        .detail-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .detail-title {
          font-size: 24px;
          font-weight: 500;
          margin: 0;
        }
        
        .detail-subtitle {
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
          margin-bottom: 16px;
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
        
        .progress-bar {
          height: 8px;
          width: 100%;
          background-color: var(--border-color);
          border-radius: 4px;
          overflow: hidden;
          margin-top: 8px;
        }
        
        .progress-bar-fill {
          height: 100%;
          background-color: var(--success-color);
          border-radius: 4px;
        }
        
        .section-title {
          font-size: 18px;
          font-weight: 500;
          margin: 0 0 16px 0;
        }
        
        .condition-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
          margin-bottom: 30px;
        }
        
        .condition-card {
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          padding: 16px;
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
        
        .condition-result {
          padding: 2px 6px;
          font-size: 12px;
          border-radius: 10px;
        }
        
        .condition-result.true {
          background-color: rgba(76, 175, 80, 0.1);
          color: var(--success-color);
        }
        
        .condition-result.false {
          background-color: rgba(244, 67, 54, 0.1);
          color: var(--error-color);
        }
        
        .actions-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
          margin-bottom: 30px;
        }
        
        .action-card {
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          padding: 20px;
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
        
        .action-meta {
          font-size: 14px;
          color: #666;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .action-details {
          margin-left: 0;
        }
        
        .action-detail-row {
          margin-bottom: 8px;
        }
        
        .action-detail-section {
          margin-top: 16px;
        }
        
        .recipients-list {
          margin-top: 8px;
        }
        
        .recipient-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid var(--border-color);
        }
        
        .recipient-item:last-child {
          border-bottom: none;
        }
        
        .no-recipients {
          font-style: italic;
          color: #999;
          margin-top: 8px;
        }
        
        .error-message {
          color: var(--error-color);
          background-color: rgba(244, 67, 54, 0.1);
          padding: 12px;
          border-radius: 4px;
          margin-top: 8px;
        }
        
        .warning-message {
          color: var(--warning-color);
          background-color: rgba(255, 152, 0, 0.1);
          padding: 12px;
          border-radius: 4px;
          margin-top: 16px;
        }
        
        .empty-state {
          text-align: center;
          padding: 40px;
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          margin-bottom: 30px;
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
        }
        
        .timeline {
          position: relative;
          margin-left: 20px;
          padding-left: 20px;
          margin-bottom: 30px;
        }
        
        .timeline::before {
          content: '';
          position: absolute;
          top: 0;
          bottom: 0;
          left: 0;
          width: 2px;
          background-color: var(--border-color);
        }
        
        .timeline-item {
          position: relative;
          padding-bottom:
          20px;
        }
        
        .timeline-item:last-child {
          padding-bottom: 0;
        }
        
        .timeline-item::before {
          content: '';
          position: absolute;
          top: 4px;
          left: -26px;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background-color: var(--primary-color);
        }
        
        .timeline-item.success::before {
          background-color: var(--success-color);
        }
        
        .timeline-item.failure::before {
          background-color: var(--error-color);
        }
        
        .timeline-content {
          background-color: white;
          border-radius: 4px;
          box-shadow: var(--card-shadow);
          padding: 16px;
        }
        
        .timeline-time {
          font-size: 12px;
          color: #666;
          margin-bottom: 8px;
        }
        
        .timeline-title {
          font-weight: 500;
          margin-bottom: 8px;
        }
        
        .timeline-description {
          color: #333;
        }
        
        .code-block {
          background-color: #f5f5f5;
          padding: 16px;
          border-radius: 4px;
          font-family: monospace;
          white-space: pre-wrap;
          overflow-x: auto;
          font-size: 14px;
          line-height: 1.5;
        }
        
        .json-view {
          max-height: 400px;
          overflow: auto;
        }
        
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          display: inline-block;
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
        
        .btn.warning {
          background-color: var(--warning-color);
          color: white;
        }
        
        .btn.text {
          background-color: transparent;
          padding: 4px 8px;
          color: var(--primary-color);
        }
        
        .btn.text.warning {
          color: var(--warning-color);
        }
        
        .loading-state {
          display: flex;
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
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        .error-state {
          padding: 30px;
          text-align: center;
        }
        
        .view-data-btn {
          margin-top: 8px;
          width: 100%;
        }
        
        .retry-action-info {
          margin: 16px 0;
          padding: 12px;
          background-color: #f5f5f5;
          border-radius: 4px;
        }
        
        .retry-action-info > div {
          margin-bottom: 8px;
        }
        
        .retry-action-info > div:last-child {
          margin-bottom: 0;
        }
        
        /* Dialog styles */
        .dialog-overlay {
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
        
        .dialog {
          background-color: white;
          border-radius: 4px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
          width: 90%;
          max-width: 800px;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
        }
        
        .dialog-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
        }
        
        .dialog-title {
          font-size: 18px;
          font-weight: 500;
          margin: 0;
        }
        
        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #666;
        }
        
        .dialog-content {
          padding: 20px;
          overflow-y: auto;
          flex-grow: 1;
        }
        
        .dialog-footer {
          padding: 16px 20px;
          border-top: 1px solid var(--border-color);
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }
        
        .trigger-info {
          margin-bottom: 16px;
        }
        
        .trigger-detail {
          margin-bottom: 8px;
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
      
      <div class="execution-detail">
        ${this.loading ? `
          <div class="loading-state">
            <div class="spinner"></div>
          </div>
        ` : this.error ? `
          <div class="error-state">
            <div class="error-message">
              <strong>Error:</strong> ${this.error}
            </div>
            <button type="button" class="btn primary" style="margin-top: 20px;" id="retry-load-btn">
              Try Again
            </button>
          </div>
        ` : this.execution ? `
          <div class="detail-header">
            <div>
              <h2 class="detail-title">Workflow Execution Details</h2>
              <p class="detail-subtitle">${this.execution.workflow_name}</p>
            </div>
            
            <button type="button" class="back-btn" id="back-btn">
              ← Back to List
            </button>
          </div>
          
          <div class="tabs">
            <button type="button" class="${tabClass('summary')}" data-tab="summary">Summary</button>
            <button type="button" class="${tabClass('timeline')}" data-tab="timeline">Timeline</button>
            <button type="button" class="${tabClass('json')}" data-tab="json">JSON</button>
          </div>
          
          <div class="tab-content ${this.activeTab === 'summary' ? 'active' : ''}" id="summary-tab">
            ${this.renderSummaryTab()}
          </div>
          
          <div class="tab-content ${this.activeTab === 'timeline' ? 'active' : ''}" id="timeline-tab">
            ${this.renderTimelineTab()}
          </div>
          
          <div class="tab-content ${this.activeTab === 'json' ? 'active' : ''}" id="json-tab">
            ${this.renderJsonTab()}
          </div>
          
          ${this.renderTriggerDataDialog()}
          ${this.renderRetryDialog()}
        ` : `
          <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <div class="empty-state-title">No execution found</div>
            <div class="empty-state-message">The requested workflow execution could not be found.</div>
          </div>
        `}
      </div>
    `;
    
    this.setupEventListeners();
  }
  
  setupEventListeners() {
    if (this.loading || this.error || !this.execution) return;
    
    // Tab buttons
    this.shadowRoot.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', this.handleTabChange);
    });
    
    // Back button
    const backBtn = this.shadowRoot.querySelector('#back-btn');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        window.history.back();
      });
    }
    
    // View trigger data button
    const viewTriggerDataBtn = this.shadowRoot.querySelector('#view-trigger-data-btn');
    if (viewTriggerDataBtn) {
      viewTriggerDataBtn.addEventListener('click', this.showTriggerData);
    }
    
    // Close trigger data dialog
    if (this.showTriggerDataDialog) {
      const closeDialogBtns = this.shadowRoot.querySelectorAll('#close-trigger-data-btn, #close-dialog-btn');
      closeDialogBtns.forEach(btn => {
        btn.addEventListener('click', this.closeTriggerDataDialog);
      });
    }
    
    // Retry action buttons
    this.shadowRoot.querySelectorAll('.retry-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const actionIndex = parseInt(btn.dataset.actionIndex);
        if (!isNaN(actionIndex) && actionIndex >= 0 && actionIndex < this.execution.actions.length) {
          this.showRetryActionDialog(this.execution.actions[actionIndex]);
        }
      });
    });
    
    // Close retry dialog
    if (this.showRetryDialog) {
      const closeRetryBtns = this.shadowRoot.querySelectorAll('#close-retry-btn, #cancel-retry-btn');
      closeRetryBtns.forEach(btn => {
        btn.addEventListener('click', this.closeRetryDialog);
      });
      
      const confirmRetryBtn = this.shadowRoot.querySelector('#confirm-retry-btn');
      if (confirmRetryBtn) {
        confirmRetryBtn.addEventListener('click', this.retryAction);
      }
    }
    
    // Try again button (on error)
    const retryLoadBtn = this.shadowRoot.querySelector('#retry-load-btn');
    if (retryLoadBtn) {
      retryLoadBtn.addEventListener('click', this.loadExecution);
    }
  }
}
// Define the new element
customElements.define('okui-workflow-execution-detail', OkuiWorkflowExecutionDetail);