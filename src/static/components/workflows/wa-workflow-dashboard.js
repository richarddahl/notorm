import { LitElement, html, css } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-switch.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-chip.js';
import '@webcomponents/awesome/wa-divider.js';
import '@webcomponents/awesome/wa-tooltip.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';

/**
 * @element wa-workflow-dashboard
 * @description A dashboard component for managing notification workflows
 */
export class WebAwesomeWorkflowDashboard extends LitElement {
  static get properties() {
    return {
      workflows: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      showDeleteDialog: { type: Boolean },
      workflowToDelete: { type: Object },
      searchQuery: { type: String },
      filterEntity: { type: String },
      availableEntities: { type: Array },
      activeTab: { type: String },
      selectedWorkflow: { type: Object },
      executionHistory: { type: Array },
      showHistoryDialog: { type: Boolean },
      historyDetails: { type: Object }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --dashboard-bg: var(--wa-background-color, #f5f5f5);
        --dashboard-padding: 20px;
        --section-gap: 24px;
      }
      .dashboard-container {
        padding: var(--dashboard-padding);
        background-color: var(--dashboard-bg);
        min-height: 600px;
      }
      .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--section-gap);
      }
      .dashboard-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .search-bar {
        display: flex;
        gap: 16px;
        margin-bottom: var(--section-gap);
      }
      .workflow-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        margin-bottom: var(--section-gap);
      }
      .workflow-card {
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .workflow-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
      }
      .workflow-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .workflow-description {
        margin: 8px 0 16px 0;
        color: var(--wa-text-secondary-color, #757575);
        flex-grow: 1;
      }
      .entity-badge {
        display: inline-block;
        padding: 4px 8px;
        font-size: 12px;
        border-radius: 12px;
        margin-right: 8px;
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
      }
      .trigger-badge {
        display: inline-block;
        padding: 4px 8px;
        font-size: 12px;
        border-radius: 12px;
        margin-right: 8px;
      }
      .trigger-badge.create {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.1));
        color: var(--wa-success-color, #4caf50);
      }
      .trigger-badge.update {
        background-color: var(--wa-warning-color-light, rgba(255, 152, 0, 0.1));
        color: var(--wa-warning-color, #ff9800);
      }
      .trigger-badge.delete {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
      }
      .workflow-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 16px;
        border-top: 1px solid var(--wa-border-color, #e0e0e0);
        padding-top: 16px;
      }
      .action-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 6px;
        font-size: 12px;
        color: white;
      }
      .action-notification {
        background-color: var(--wa-secondary-color, #f50057);
      }
      .action-email {
        background-color: var(--wa-success-color, #4caf50);
      }
      .action-webhook {
        background-color: var(--wa-warning-color, #ff9800);
      }
      .action-database {
        background-color: var(--wa-info-color, #2196f3);
      }
      .action-custom {
        background-color: var(--wa-dark-color, #333333);
      }
      .meta-info {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
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
      .workflow-actions {
        display: flex;
        gap: 8px;
      }
      .status-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 8px;
        font-size: 12px;
        border-radius: 12px;
        font-weight: 500;
      }
      .status-badge.active {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.1));
        color: var(--wa-success-color, #4caf50);
      }
      .status-badge.disabled {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
      }
      .history-item {
        padding: 12px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .history-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .history-title {
        font-weight: 500;
      }
      .history-timestamp {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .history-badge {
        display: inline-block;
        padding: 2px 6px;
        font-size: 10px;
        border-radius: 10px;
        margin-left: 8px;
      }
      .history-badge.success {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.1));
        color: var(--wa-success-color, #4caf50);
      }
      .history-badge.partial {
        background-color: var(--wa-warning-color-light, rgba(255, 152, 0, 0.1));
        color: var(--wa-warning-color, #ff9800);
      }
      .history-badge.failure {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
      }
      .history-details-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      .history-details-card {
        padding: 16px;
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-surface-color, #ffffff);
      }
      .history-action-item {
        padding: 12px;
        border-left: 4px solid var(--wa-primary-color, #3f51b5);
        background-color: var(--wa-hover-color, #f5f5f5);
        margin-bottom: 8px;
        border-radius: 0 4px 4px 0;
      }
      .history-action-item.success {
        border-left-color: var(--wa-success-color, #4caf50);
      }
      .history-action-item.failure {
        border-left-color: var(--wa-error-color, #f44336);
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      .stats-card {
        padding: 16px;
        text-align: center;
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-surface-color, #ffffff);
      }
      .stats-value {
        font-size: 32px;
        font-weight: bold;
        color: var(--wa-primary-color, #3f51b5);
        margin: 8px 0;
      }
      .stats-label {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .chart-container {
        height: 300px;
        margin-bottom: 24px;
        padding: 16px;
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-surface-color, #ffffff);
      }
    `;
  }

  constructor() {
    super();
    this.workflows = [];
    this.loading = false;
    this.error = null;
    this.showDeleteDialog = false;
    this.workflowToDelete = null;
    this.searchQuery = '';
    this.filterEntity = '';
    this.availableEntities = [];
    this.activeTab = 'workflows';
    this.selectedWorkflow = null;
    this.executionHistory = [];
    this.showHistoryDialog = false;
    this.historyDetails = null;
    
    // Load mock data for the dashboard
    this._loadMockData();
  }

  _loadMockData() {
    // Mock workflows
    this.workflows = [
      {
        id: '1',
        name: 'New Order Notification',
        description: 'Sends notification when a new order is created',
        enabled: true,
        version: 1,
        trigger: {
          entity_type: 'order',
          operations: ['create'],
          conditions: []
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
      },
      {
        id: '2',
        name: 'Low Inventory Alert',
        description: 'Notifies when product inventory drops below threshold',
        enabled: true,
        version: 2,
        trigger: {
          entity_type: 'product',
          operations: ['update'],
          conditions: [
            {
              type: 'field',
              field: 'stock',
              operator: 'lt',
              value: '10'
            }
          ]
        },
        actions: [
          {
            type: 'notification',
            title: 'Low Inventory Alert',
            body: 'Product {{name}} is running low on stock ({{stock}} remaining).',
            priority: 'high',
            recipients: [
              { type: 'role', value: 'inventory_manager' }
            ]
          },
          {
            type: 'webhook',
            url: 'https://example.com/api/inventory-alerts',
            method: 'POST'
          }
        ],
        created_at: '2023-03-20T09:45:12Z',
        updated_at: '2023-03-22T11:30:05Z'
      },
      {
        id: '3',
        name: 'Customer Status Change',
        description: 'Tracks changes to customer status and sends notifications',
        enabled: false,
        version: 3,
        trigger: {
          entity_type: 'customer',
          operations: ['update'],
          conditions: [
            {
              type: 'field',
              field: 'status',
              operator: 'eq',
              value: 'premium'
            }
          ]
        },
        actions: [
          {
            type: 'notification',
            title: 'Customer Upgraded to Premium',
            body: 'Customer {{name}} has been upgraded to premium status.',
            priority: 'normal',
            recipients: [
              { type: 'role', value: 'account_manager' }
            ]
          },
          {
            type: 'email',
            subject: 'Welcome to Premium Membership',
            body: 'Dear {{name}},\n\nWelcome to our Premium membership program!',
            recipients: [
              { type: 'dynamic', value: 'customer.email' }
            ]
          },
          {
            type: 'database',
            operation: 'update',
            target_entity: 'customer_metadata',
            field_mapping: {
              'premium_since': '{{now}}',
              'welcome_email_sent': true
            }
          }
        ],
        created_at: '2023-02-10T15:20:30Z',
        updated_at: '2023-02-10T15:20:30Z'
      }
    ];
    
    // Mock available entities
    this.availableEntities = [
      { value: 'customer', label: 'Customer' },
      { value: 'order', label: 'Order' },
      { value: 'product', label: 'Product' },
      { value: 'invoice', label: 'Invoice' },
      { value: 'inventory', label: 'Inventory' }
    ];
    
    // Mock execution history
    this.executionHistory = [
      {
        id: 'exec-1',
        workflow_id: '1',
        workflow_name: 'New Order Notification',
        trigger_entity: 'order',
        trigger_operation: 'create',
        entity_id: 'order-12345',
        status: 'success',
        started_at: '2023-05-01T14:32:20Z',
        completed_at: '2023-05-01T14:32:22Z',
        duration_ms: 1840,
        actions_total: 2,
        actions_success: 2,
        actions_failed: 0,
        action_results: [
          {
            type: 'notification',
            status: 'success',
            recipients_count: 5,
            details: 'Notification sent to 5 recipients'
          },
          {
            type: 'email',
            status: 'success',
            recipients_count: 1,
            details: 'Email sent to customer@example.com'
          }
        ]
      },
      {
        id: 'exec-2',
        workflow_id: '2',
        workflow_name: 'Low Inventory Alert',
        trigger_entity: 'product',
        trigger_operation: 'update',
        entity_id: 'product-789',
        status: 'partial',
        started_at: '2023-05-01T10:15:30Z',
        completed_at: '2023-05-01T10:15:31Z',
        duration_ms: 980,
        actions_total: 2,
        actions_success: 1,
        actions_failed: 1,
        action_results: [
          {
            type: 'notification',
            status: 'success',
            recipients_count: 2,
            details: 'Notification sent to 2 recipients'
          },
          {
            type: 'webhook',
            status: 'failed',
            error: 'Webhook endpoint returned status 500',
            details: 'Server error at external endpoint'
          }
        ]
      },
      {
        id: 'exec-3',
        workflow_id: '1',
        workflow_name: 'New Order Notification',
        trigger_entity: 'order',
        trigger_operation: 'create',
        entity_id: 'order-12346',
        status: 'success',
        started_at: '2023-05-01T09:22:15Z',
        completed_at: '2023-05-01T09:22:16Z',
        duration_ms: 910,
        actions_total: 2,
        actions_success: 2,
        actions_failed: 0,
        action_results: [
          {
            type: 'notification',
            status: 'success',
            recipients_count: 5,
            details: 'Notification sent to 5 recipients'
          },
          {
            type: 'email',
            status: 'success',
            recipients_count: 1,
            details: 'Email sent to anothercustomer@example.com'
          }
        ]
      }
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    // In a real implementation, this would load data from an API
    // this.loadWorkflows();
  }

  async loadWorkflows() {
    this.loading = true;
    
    try {
      const response = await fetch('/api/workflows');
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.workflows = await response.json();
    } catch (err) {
      console.error('Failed to load workflows:', err);
      this.error = `Error loading workflows: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  handleSearchInput(e) {
    this.searchQuery = e.target.value;
  }

  handleEntityFilterChange(e) {
    this.filterEntity = e.target.value;
  }

  getFilteredWorkflows() {
    return this.workflows.filter(workflow => {
      // Apply search filter
      const searchMatch = !this.searchQuery || 
        workflow.name.toLowerCase().includes(this.searchQuery.toLowerCase()) || 
        workflow.description.toLowerCase().includes(this.searchQuery.toLowerCase());
      
      // Apply entity filter
      const entityMatch = !this.filterEntity || workflow.trigger.entity_type === this.filterEntity;
      
      return searchMatch && entityMatch;
    });
  }

  createWorkflow() {
    // In a real application, this would navigate to the workflow designer
    window.location.href = '/workflows/new';
  }

  editWorkflow(workflow) {
    // In a real application, this would navigate to the workflow designer with the workflow ID
    window.location.href = `/workflows/edit/${workflow.id}`;
  }

  showDeleteConfirm(workflow) {
    this.workflowToDelete = workflow;
    this.showDeleteDialog = true;
  }

  cancelDelete() {
    this.showDeleteDialog = false;
    this.workflowToDelete = null;
  }

  async confirmDelete() {
    if (!this.workflowToDelete) return;
    
    this.loading = true;
    
    try {
      // In a real implementation, this would call an API
      // const response = await fetch(`/api/workflows/${this.workflowToDelete.id}`, {
      //   method: 'DELETE'
      // });
      
      // if (!response.ok) {
      //   throw new Error(`API returned ${response.status}`);
      // }
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Remove from local list
      this.workflows = this.workflows.filter(w => w.id !== this.workflowToDelete.id);
      
      this._showNotification(`Workflow "${this.workflowToDelete.name}" deleted successfully`, 'success');
      
    } catch (err) {
      console.error('Failed to delete workflow:', err);
      this.error = `Error deleting workflow: ${err.message}`;
      this._showNotification(`Error deleting workflow: ${err.message}`, 'error');
    } finally {
      this.loading = false;
      this.showDeleteDialog = false;
      this.workflowToDelete = null;
    }
  }

  async toggleWorkflowEnabled(workflow, enabled) {
    this.loading = true;
    
    try {
      // In a real implementation, this would call an API
      // const response = await fetch(`/api/workflows/${workflow.id}`, {
      //   method: 'PATCH',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify({ enabled })
      // });
      
      // if (!response.ok) {
      //   throw new Error(`API returned ${response.status}`);
      // }
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Update local state
      this.workflows = this.workflows.map(w => {
        if (w.id === workflow.id) {
          return { ...w, enabled };
        }
        return w;
      });
      
      this._showNotification(
        `Workflow "${workflow.name}" ${enabled ? 'enabled' : 'disabled'} successfully`, 
        'success'
      );
      
    } catch (err) {
      console.error('Failed to update workflow:', err);
      this.error = `Error updating workflow: ${err.message}`;
      this._showNotification(`Error updating workflow: ${err.message}`, 'error');
    } finally {
      this.loading = false;
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

  handleTabChange(e) {
    this.activeTab = e.detail.value;
  }
  
  viewHistoryDetails(historyItem) {
    this.historyDetails = historyItem;
    this.showHistoryDialog = true;
  }
  
  closeHistoryDialog() {
    this.showHistoryDialog = false;
    this.historyDetails = null;
  }
  
  _formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  }
  
  _timeSince(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + ' years ago';
    
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + ' months ago';
    
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + ' days ago';
    
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + ' hours ago';
    
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + ' minutes ago';
    
    return Math.floor(seconds) + ' seconds ago';
  }

  renderDeleteDialog() {
    if (!this.showDeleteDialog) return html``;
    
    return html`
      <wa-dialog open @close=${this.cancelDelete}>
        <div slot="header">Confirm Deletion</div>
        
        <div>
          <p>Are you sure you want to delete the workflow "${this.workflowToDelete?.name}"?</p>
          <p>This action cannot be undone.</p>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.cancelDelete}>Cancel</wa-button>
          <wa-button color="error" @click=${this.confirmDelete}>Delete</wa-button>
        </div>
      </wa-dialog>
    `;
  }

  renderHistoryDialog() {
    if (!this.showHistoryDialog || !this.historyDetails) return html``;
    
    return html`
      <wa-dialog open @close=${this.closeHistoryDialog} style="width: 80vw; max-width: 800px;">
        <div slot="header">Execution Details</div>
        
        <div>
          <div class="history-details-grid">
            <div class="history-details-card">
              <div><strong>Workflow:</strong> ${this.historyDetails.workflow_name}</div>
              <div><strong>Entity:</strong> ${this.historyDetails.trigger_entity}</div>
              <div><strong>Operation:</strong> ${this.historyDetails.trigger_operation}</div>
              <div><strong>Entity ID:</strong> ${this.historyDetails.entity_id}</div>
            </div>
            
            <div class="history-details-card">
              <div><strong>Started:</strong> ${this._formatTimestamp(this.historyDetails.started_at)}</div>
              <div><strong>Completed:</strong> ${this._formatTimestamp(this.historyDetails.completed_at)}</div>
              <div><strong>Duration:</strong> ${this.historyDetails.duration_ms}ms</div>
              <div><strong>Status:</strong> 
                <span class="history-badge ${this.historyDetails.status}">
                  ${this.historyDetails.status}
                </span>
              </div>
            </div>
          </div>
          
          <h3>Action Results</h3>
          
          ${this.historyDetails.action_results.map((action, index) => html`
            <div class="history-action-item ${action.status}">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div>
                  <strong>${this._getActionTypeLabel(action.type)}</strong>
                  <span class="history-badge ${action.status}">
                    ${action.status}
                  </span>
                </div>
                <div class="meta-info">Action ${index + 1} of ${this.historyDetails.action_results.length}</div>
              </div>
              
              <div>${action.details}</div>
              
              ${action.status === 'failed' ? html`
                <div style="color: var(--wa-error-color); margin-top: 8px;">
                  <strong>Error:</strong> ${action.error}
                </div>
              ` : ''}
              
              ${action.recipients_count ? html`
                <div style="margin-top: 8px;">
                  <strong>Recipients:</strong> ${action.recipients_count}
                </div>
              ` : ''}
            </div>
          `)}
        </div>
        
        <div slot="footer">
          <wa-button @click=${this.closeHistoryDialog}>Close</wa-button>
        </div>
      </wa-dialog>
    `;
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
  
  render() {
    const filteredWorkflows = this.getFilteredWorkflows();
    
    return html`
      <div class="dashboard-container">
        <div class="dashboard-header">
          <h1 class="dashboard-title">Workflow Management</h1>
          
          <wa-button @click=${this.createWorkflow}>
            <wa-icon slot="prefix" name="add"></wa-icon>
            Create Workflow
          </wa-button>
        </div>
        
        ${this.error ? html`
          <wa-alert type="error" style="margin-bottom: 20px;">
            ${this.error}
          </wa-alert>
        ` : ''}
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="workflows">Workflows</wa-tab>
          <wa-tab value="history">Execution History</wa-tab>
          <wa-tab value="analytics">Analytics</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="workflows" ?active=${this.activeTab === 'workflows'}>
          <div class="search-bar">
            <wa-input 
              placeholder="Search workflows"
              .value=${this.searchQuery}
              @input=${this.handleSearchInput}
              style="flex: 2;">
              <wa-icon slot="prefix" name="search"></wa-icon>
            </wa-input>
            
            <wa-select 
              placeholder="Filter by entity"
              .value=${this.filterEntity}
              @change=${this.handleEntityFilterChange}
              style="flex: 1;">
              <wa-option value="">All entities</wa-option>
              ${this.availableEntities.map(entity => html`
                <wa-option value="${entity.value}">${entity.label}</wa-option>
              `)}
            </wa-select>
          </div>
          
          ${filteredWorkflows.length === 0 ? html`
            <div class="empty-state">
              <wa-icon name="workflow" class="empty-state-icon"></wa-icon>
              <h2>No workflows found</h2>
              <p>There are no workflows matching your search criteria.</p>
              <wa-button @click=${this.createWorkflow}>Create your first workflow</wa-button>
            </div>
          ` : html`
            <div class="workflow-grid">
              ${repeat(filteredWorkflows, workflow => workflow.id, workflow => html`
                <wa-card class="workflow-card" elevation="1">
                  <div style="padding: 16px;">
                    <div class="workflow-card-header">
                      <h3 class="workflow-title">${workflow.name}</h3>
                      <span class="status-badge ${workflow.enabled ? 'active' : 'disabled'}">
                        ${workflow.enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                    
                    <p class="workflow-description">${workflow.description}</p>
                    
                    <div style="margin-bottom: 12px;">
                      <span class="entity-badge">${workflow.trigger.entity_type}</span>
                      ${workflow.trigger.operations.map(op => html`
                        <span class="trigger-badge ${op}">${op}</span>
                      `)}
                    </div>
                    
                    <div>
                      ${this._getActionCounts(workflow).map(([type, count]) => html`
                        <wa-tooltip text="${count} ${this._getActionTypeLabel(type)} ${count === 1 ? 'action' : 'actions'}">
                          <span class="action-icon action-${type}">
                            ${type.charAt(0).toUpperCase()}
                          </span>
                        </wa-tooltip>
                      `)}
                    </div>
                    
                    <div class="workflow-footer">
                      <div class="meta-info">
                        v${workflow.version} • Updated ${this._timeSince(workflow.updated_at)}
                      </div>
                      
                      <div class="workflow-actions">
                        <wa-button variant="text" @click=${() => this.editWorkflow(workflow)}>Edit</wa-button>
                        <wa-button 
                          variant="text" 
                          color=${workflow.enabled ? 'warning' : 'success'}
                          @click=${() => this.toggleWorkflowEnabled(workflow, !workflow.enabled)}>
                          ${workflow.enabled ? 'Disable' : 'Enable'}
                        </wa-button>
                        <wa-button variant="text" color="error" @click=${() => this.showDeleteConfirm(workflow)}>Delete</wa-button>
                      </div>
                    </div>
                  </div>
                </wa-card>
              `)}
            </div>
          `}
        </wa-tab-panel>
        
        <wa-tab-panel value="history" ?active=${this.activeTab === 'history'}>
          <wa-card>
            <div>
              <div style="padding: 16px; border-bottom: 1px solid var(--wa-border-color, #e0e0e0);">
                <h2 style="margin-top: 0;">Execution History</h2>
                <p>Recent workflow executions and their results.</p>
              </div>
              
              ${this.executionHistory.length === 0 ? html`
                <div style="padding: 32px; text-align: center;">
                  <wa-icon name="history" style="font-size: 48px; margin-bottom: 16px; color: var(--wa-text-secondary-color);"></wa-icon>
                  <h3>No execution history</h3>
                  <p>There are no workflow executions recorded yet.</p>
                </div>
              ` : html`
                ${repeat(this.executionHistory, item => item.id, item => html`
                  <div class="history-item">
                    <div class="history-item-header">
                      <div class="history-title">
                        ${item.workflow_name}
                        <span class="history-badge ${item.status}">
                          ${item.status}
                        </span>
                      </div>
                      <div class="history-timestamp">${this._timeSince(item.started_at)}</div>
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                      <span>Trigger: ${item.trigger_entity} ${item.trigger_operation}</span>
                      <span style="margin-left: 16px;">Entity: ${item.entity_id}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <div>
                        <span style="margin-right: 16px;">
                          <strong>Duration:</strong> ${item.duration_ms}ms
                        </span>
                        <span>
                          <strong>Actions:</strong> 
                          ${item.actions_success}/${item.actions_total} completed
                        </span>
                      </div>
                      
                      <wa-button variant="text" @click=${() => this.viewHistoryDetails(item)}>
                        View Details
                      </wa-button>
                    </div>
                  </div>
                `)}
              `}
            </div>
          </wa-card>
        </wa-tab-panel>
        
        <wa-tab-panel value="analytics" ?active=${this.activeTab === 'analytics'}>
          <div class="stats-grid">
            <div class="stats-card">
              <div class="stats-value">247</div>
              <div class="stats-label">Workflow Executions Today</div>
            </div>
            
            <div class="stats-card">
              <div class="stats-value">93.5%</div>
              <div class="stats-label">Success Rate</div>
            </div>
            
            <div class="stats-card">
              <div class="stats-value">835</div>
              <div class="stats-label">Notifications Sent</div>
            </div>
            
            <div class="stats-card">
              <div class="stats-value">156</div>
              <div class="stats-label">Emails Delivered</div>
            </div>
          </div>
          
          <div class="chart-container">
            <h3 style="margin-top: 0;">Workflow Executions Over Time</h3>
            <div style="display: flex; justify-content: center; align-items: center; height: 80%;">
              <div style="color: var(--wa-text-secondary-color); font-style: italic;">
                Chart visualization would appear here in a real application
              </div>
            </div>
          </div>
          
          <div style="display: flex; gap: 24px;">
            <wa-card style="flex: 1; padding: 16px;">
              <h3 style="margin-top: 0;">Top Workflows by Execution</h3>
              <table style="width: 100%; border-collapse: collapse;">
                <thead>
                  <tr>
                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Workflow</th>
                    <th style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Executions</th>
                    <th style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Success Rate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">New Order Notification</td>
                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">142</td>
                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">98.6%</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Low Inventory Alert</td>
                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">87</td>
                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">89.7%</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Customer Status Change</td>
                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">18</td>
                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">100%</td>
                  </tr>
                </tbody>
              </table>
            </wa-card>
            
            <wa-card style="flex: 1; padding: 16px;">
              <h3 style="margin-top: 0;">Action Types Distribution</h3>
              <div style="display: flex; flex-direction: column; gap: 16px; margin-top: 24px;">
                <div>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Notifications</span>
                    <span>247 (45%)</span>
                  </div>
                  <div style="height: 8px; width: 100%; background-color: var(--wa-border-color); border-radius: 4px;">
                    <div style="height: 100%; width: 45%; background-color: var(--wa-secondary-color); border-radius: 4px;"></div>
                  </div>
                </div>
                
                <div>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Emails</span>
                    <span>156 (28%)</span>
                  </div>
                  <div style="height: 8px; width: 100%; background-color: var(--wa-border-color); border-radius: 4px;">
                    <div style="height: 100%; width: 28%; background-color: var(--wa-success-color); border-radius: 4px;"></div>
                  </div>
                </div>
                
                <div>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Webhooks</span>
                    <span>87 (16%)</span>
                  </div>
                  <div style="height: 8px; width: 100%; background-color: var(--wa-border-color); border-radius: 4px;">
                    <div style="height: 100%; width: 16%; background-color: var(--wa-warning-color); border-radius: 4px;"></div>
                  </div>
                </div>
                
                <div>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Database Operations</span>
                    <span>61 (11%)</span>
                  </div>
                  <div style="height: 8px; width: 100%; background-color: var(--wa-border-color); border-radius: 4px;">
                    <div style="height: 100%; width: 11%; background-color: var(--wa-info-color); border-radius: 4px;"></div>
                  </div>
                </div>
              </div>
            </wa-card>
          </div>
        </wa-tab-panel>
        
        ${this.loading ? html`
          <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                      background: rgba(255, 255, 255, 0.7); display: flex; 
                      align-items: center; justify-content: center; z-index: 9999;">
            <wa-spinner size="large"></wa-spinner>
          </div>
        ` : ''}
        
        ${this.renderDeleteDialog()}
        ${this.renderHistoryDialog()}
      </div>
    `;
  }
  
  _getActionCounts(workflow) {
    const counts = {};
    
    workflow.actions.forEach(action => {
      counts[action.type] = (counts[action.type] || 0) + 1;
    });
    
    return Object.entries(counts);
  }
}

customElements.define('wa-workflow-dashboard', WebAwesomeWorkflowDashboard);