/**
 * Workflow Dashboard component
 * 
 * A dashboard for managing notification workflows in the UNO framework.
 * Shows a list of existing workflows with their status and allows for
 * creating, editing, and activating/deactivating workflows.
 * 
 * @element okui-workflow-dashboard
 */
class OkuiWorkflowDashboard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Initialize state
    this.workflows = [];
    this.isLoading = true;
    this.error = null;
    this.filter = 'all'; // all, active, draft, inactive
    this.searchTerm = '';
    
    // Bind methods
    this.handleFilterChange = this.handleFilterChange.bind(this);
    this.handleSearch = this.handleSearch.bind(this);
    this.handleCreateWorkflow = this.handleCreateWorkflow.bind(this);
    this.handleEditWorkflow = this.handleEditWorkflow.bind(this);
    this.handleToggleStatus = this.handleToggleStatus.bind(this);
    this.handleDeleteWorkflow = this.handleDeleteWorkflow.bind(this);
    this.loadWorkflows = this.loadWorkflows.bind(this);
  }
  
  connectedCallback() {
    this.loadWorkflows();
    this.render();
  }
  
  async loadWorkflows() {
    this.isLoading = true;
    this.error = null;
    this.render();
    
    try {
      // Load mocked data for demonstration
      setTimeout(() => {
        // Mock data for demonstration
        this.workflows = [
          {
            id: 'wf-123',
            name: 'New Order Notification',
            description: 'Sends notification when new orders are created',
            status: 'active',
            created_at: '2023-04-01T10:30:00Z',
            updated_at: '2023-04-01T10:30:00Z'
          },
          {
            id: 'wf-456',
            name: 'Low Stock Alert',
            description: 'Notifies inventory manager when stock is low',
            status: 'active',
            created_at: '2023-04-02T14:15:00Z',
            updated_at: '2023-04-02T14:15:00Z'
          },
          {
            id: 'wf-789',
            name: 'Customer Follow-up',
            description: 'Sends follow-up email 7 days after purchase',
            status: 'draft',
            created_at: '2023-04-03T09:45:00Z',
            updated_at: '2023-04-03T09:45:00Z'
          },
          {
            id: 'wf-101',
            name: 'Approval Reminder',
            description: 'Reminds managers about pending approvals',
            status: 'inactive',
            created_at: '2023-04-04T11:20:00Z',
            updated_at: '2023-04-04T11:20:00Z'
          }
        ];
        
        this.isLoading = false;
        this.render();
        this.setupEventListeners();
      }, 1000);
      
      // When API is ready, uncomment this code and remove the mock data above
      /*
      const response = await fetch('/api/workflows');
      if (!response.ok) {
        throw new Error(`Failed to load workflows: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.workflows = Array.isArray(data) ? data : (data.items || []);
      this.isLoading = false;
      this.render();
      this.setupEventListeners();
      */
    } catch (error) {
      console.error('Error loading workflows:', error);
      this.error = error.message;
      this.isLoading = false;
      this.render();
    }
  }
  
  setupEventListeners() {
    // Filter buttons
    this.shadowRoot.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.handleFilterChange(btn.dataset.filter);
      });
    });
    
    // Search input
    const searchInput = this.shadowRoot.querySelector('#search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.handleSearch(e.target.value);
      });
    }
    
    // Create button
    const createBtn = this.shadowRoot.querySelector('#create-workflow-btn');
    if (createBtn) {
      createBtn.addEventListener('click', this.handleCreateWorkflow);
    }
    
    // Edit buttons
    this.shadowRoot.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.handleEditWorkflow(btn.dataset.id);
      });
    });
    
    // Status toggle buttons
    this.shadowRoot.querySelectorAll('.status-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.handleToggleStatus(btn.dataset.id, btn.dataset.action);
      });
    });
    
    // Delete buttons
    this.shadowRoot.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.handleDeleteWorkflow(btn.dataset.id);
      });
    });
  }
  
  handleFilterChange(filter) {
    this.filter = filter;
    this.render();
    this.setupEventListeners();
  }
  
  handleSearch(term) {
    this.searchTerm = term;
    this.render();
    this.setupEventListeners();
  }
  
  handleCreateWorkflow() {
    // For demonstration purposes, we'll stay on the same page
    alert('This would navigate to the workflow designer in a real implementation');
    
    // In production, uncomment this:
    // window.location.href = '/admin/workflows/designer';
  }
  
  handleEditWorkflow(workflowId) {
    // For demonstration purposes, we'll stay on the same page
    alert(`This would navigate to edit workflow ${workflowId} in a real implementation`);
    
    // In production, uncomment this:
    // window.location.href = `/admin/workflows/designer?workflow_id=${workflowId}`;
  }
  
  async handleToggleStatus(workflowId, action) {
    try {
      const workflow = this.workflows.find(w => w.id === workflowId);
      if (!workflow) {
        throw new Error('Workflow not found');
      }
      
      let newStatus;
      if (action === 'activate') {
        newStatus = 'active';
      } else if (action === 'deactivate') {
        newStatus = 'inactive';
      } else if (action === 'draft') {
        newStatus = 'draft';
      } else {
        throw new Error('Invalid action');
      }
      
      // In a real implementation, this would call an API endpoint
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Update local state
      workflow.status = newStatus;
      this.render();
      this.setupEventListeners();
      
      this.showNotification('success', `Workflow status updated to ${newStatus}`);
    } catch (error) {
      console.error('Error updating workflow status:', error);
      this.showNotification('error', error.message);
    }
  }
  
  async handleDeleteWorkflow(workflowId) {
    // Confirm deletion
    if (!confirm('Are you sure you want to delete this workflow? This action cannot be undone.')) {
      return;
    }
    
    try {
      // In a real implementation, this would call an API endpoint
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Remove from local state
      this.workflows = this.workflows.filter(w => w.id !== workflowId);
      this.render();
      this.setupEventListeners();
      
      this.showNotification('success', 'Workflow deleted successfully');
    } catch (error) {
      console.error('Error deleting workflow:', error);
      this.showNotification('error', error.message);
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
  
  getFilteredWorkflows() {
    let filtered = [...this.workflows];
    
    // Apply status filter
    if (this.filter !== 'all') {
      filtered = filtered.filter(w => w.status === this.filter);
    }
    
    // Apply search filter
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(w => 
        w.name.toLowerCase().includes(term) || 
        (w.description && w.description.toLowerCase().includes(term))
      );
    }
    
    return filtered;
  }
  
  renderStatusBadge(status) {
    let badgeClass = '';
    let label = status;
    
    switch (status) {
      case 'active':
        badgeClass = 'status-badge active';
        label = 'Active';
        break;
      case 'inactive':
        badgeClass = 'status-badge inactive';
        label = 'Inactive';
        break;
      case 'draft':
        badgeClass = 'status-badge draft';
        label = 'Draft';
        break;
    }
    
    return `<span class="${badgeClass}">${label}</span>`;
  }
  
  renderStatusActions(workflow) {
    const { id, status } = workflow;
    
    // Different actions based on current status
    if (status === 'active') {
      return `
        <button type="button" class="status-toggle-btn" data-id="${id}" data-action="deactivate">
          Deactivate
        </button>
      `;
    } else if (status === 'inactive') {
      return `
        <button type="button" class="status-toggle-btn" data-id="${id}" data-action="activate">
          Activate
        </button>
      `;
    } else if (status === 'draft') {
      return `
        <button type="button" class="status-toggle-btn" data-id="${id}" data-action="activate">
          Publish
        </button>
      `;
    }
    
    return '';
  }
  
  render() {
    const filteredWorkflows = this.getFilteredWorkflows();
    const filterBtnClass = (filter) => `filter-btn ${this.filter === filter ? 'active' : ''}`;
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--wa-font-family, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif);
          color: var(--wa-text-color, #333);
          background-color: var(--wa-background-color, #fff);
          --primary-color: var(--wa-primary-color, #3f51b5);
          --success-color: var(--wa-success-color, #4caf50);
          --warning-color: var(--wa-warning-color, #ff9800);
          --error-color: var(--wa-error-color, #f44336);
          --border-color: var(--wa-border-color, #e0e0e0);
        }
        
        .dashboard {
          padding: 20px;
        }
        
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        
        .dashboard-title {
          margin: 0;
          font-size: 24px;
          font-weight: 500;
        }
        
        .dashboard-actions {
          display: flex;
          gap: 10px;
        }
        
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          background-color: #f5f5f5;
          color: #333;
        }
        
        .btn.primary {
          background-color: var(--primary-color);
          color: white;
        }
        
        .actions-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        
        .filters {
          display: flex;
          gap: 10px;
        }
        
        .filter-btn {
          padding: 6px 12px;
          border: 1px solid var(--border-color);
          border-radius: 20px;
          background: none;
          cursor: pointer;
          font-size: 14px;
        }
        
        .filter-btn.active {
          background-color: var(--primary-color);
          color: white;
          border-color: var(--primary-color);
        }
        
        .search-box {
          position: relative;
          width: 250px;
        }
        
        .search-box input {
          width: 100%;
          padding: 8px 12px;
          padding-left: 32px;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          font-size: 14px;
        }
        
        .search-icon {
          position: absolute;
          left: 10px;
          top: 50%;
          transform: translateY(-50%);
          color: #999;
        }
        
        .workflow-table {
          width: 100%;
          border-collapse: collapse;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .workflow-table th,
        .workflow-table td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid var(--border-color);
        }
        
        .workflow-table th {
          background-color: #f5f5f5;
          font-weight: 500;
        }
        
        .workflow-table tr:last-child td {
          border-bottom: none;
        }
        
        .workflow-table tr:nth-child(even) {
          background-color: #f9f9f9;
        }
        
        .status-badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
        }
        
        .status-badge.active {
          background-color: rgba(76, 175, 80, 0.1);
          color: var(--success-color);
        }
        
        .status-badge.inactive {
          background-color: rgba(244, 67, 54, 0.1);
          color: var(--error-color);
        }
        
        .status-badge.draft {
          background-color: rgba(255, 152, 0, 0.1);
          color: var(--warning-color);
        }
        
        .workflow-actions {
          display: flex;
          gap: 8px;
        }
        
        .workflow-actions button {
          padding: 4px 8px;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          background: none;
          cursor: pointer;
          font-size: 12px;
        }
        
        .edit-btn {
          color: var(--primary-color);
          border-color: var(--primary-color);
        }
        
        .delete-btn {
          color: var(--error-color);
          border-color: var(--error-color);
        }
        
        .status-toggle-btn {
          color: var(--success-color);
          border-color: var(--success-color);
        }
        
        .empty-state {
          padding: 40px;
          text-align: center;
          background-color: #f9f9f9;
          border: 1px dashed var(--border-color);
          border-radius: 4px;
          color: #666;
        }
        
        .empty-state-icon {
          font-size: 48px;
          margin-bottom: 16px;
          color: #999;
        }
        
        .empty-state-title {
          font-size: 18px;
          font-weight: 500;
          margin-bottom: 8px;
        }
        
        .empty-state-message {
          margin-bottom: 16px;
        }
        
        .loading-state {
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 40px;
          color: #666;
        }
        
        .error-state {
          padding: 20px;
          background-color: rgba(244, 67, 54, 0.1);
          border: 1px solid var(--error-color);
          border-radius: 4px;
          color: var(--error-color);
          margin-bottom: 20px;
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
      
      <div class="dashboard">
        <div class="dashboard-header">
          <h2 class="dashboard-title">Workflow Management</h2>
          <div class="dashboard-actions">
            <button type="button" id="create-workflow-btn" class="btn primary">
              Create New Workflow
            </button>
          </div>
        </div>
        
        ${this.error ? 
          `<div class="error-state">
            <strong>Error:</strong> ${this.error}
          </div>` : 
          ''
        }
        
        <div class="actions-bar">
          <div class="filters">
            <button type="button" class="${filterBtnClass('all')}" data-filter="all">
              All Workflows
            </button>
            <button type="button" class="${filterBtnClass('active')}" data-filter="active">
              Active
            </button>
            <button type="button" class="${filterBtnClass('draft')}" data-filter="draft">
              Drafts
            </button>
            <button type="button" class="${filterBtnClass('inactive')}" data-filter="inactive">
              Inactive
            </button>
          </div>
          
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input 
              type="text" 
              id="search-input" 
              placeholder="Search workflows..." 
              value="${this.searchTerm}"
            >
          </div>
        </div>
        
        ${this.isLoading ? 
          `<div class="loading-state">Loading workflows...</div>` : 
          filteredWorkflows.length === 0 ? 
            `<div class="empty-state">
              <div class="empty-state-icon">📋</div>
              <div class="empty-state-title">No workflows found</div>
              <div class="empty-state-message">
                ${this.searchTerm || this.filter !== 'all' ? 
                  'Try adjusting your filters or search term.' : 
                  'Get started by creating your first workflow.'}
              </div>
              <button type="button" id="create-workflow-btn" class="btn primary">
                Create New Workflow
              </button>
            </div>` : 
            `<table class="workflow-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${filteredWorkflows.map(workflow => `
                  <tr>
                    <td>${workflow.name}</td>
                    <td>${workflow.description || 'No description'}</td>
                    <td>${this.renderStatusBadge(workflow.status)}</td>
                    <td>${new Date(workflow.created_at).toLocaleDateString()}</td>
                    <td>
                      <div class="workflow-actions">
                        <button type="button" class="edit-btn" data-id="${workflow.id}">
                          Edit
                        </button>
                        ${this.renderStatusActions(workflow)}
                        <button type="button" class="delete-btn" data-id="${workflow.id}">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>`
        }
      </div>
    `;
    
    this.setupEventListeners();
  }
}
// Define the new element
customElements.define('okui-workflow-dashboard', OkuiWorkflowDashboard);