import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element wa-role-manager
 * @description Component for managing roles and permissions in the UNO authorization system
 * @property {Array} roles - List of roles
 * @property {Array} permissions - List of available permissions
 * @property {Object} currentRole - Role being created or edited
 * @property {Boolean} loading - Loading state
 * @property {String} error - Error message if loading failed
 */
export class WebAwesomeRoleManager extends LitElement {
  static get properties() {
    return {
      roles: { type: Array },
      permissions: { type: Array },
      currentRole: { type: Object },
      showRoleDialog: { type: Boolean },
      showDeleteDialog: { type: Boolean },
      roleToDelete: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      searchTerm: { type: String },
      permissionCategories: { type: Array },
      selectedCategory: { type: String },
      permissionView: { type: String },
      selectedRoleId: { type: String }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --manager-bg: var(--wa-background-color, #f5f5f5);
        --manager-padding: 20px;
      }
      .manager-container {
        padding: var(--manager-padding);
        background-color: var(--manager-bg);
        min-height: 600px;
      }
      .manager-header {
        margin-bottom: 24px;
      }
      .manager-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .manager-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .search-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
      }
      .search-input {
        width: 300px;
      }
      .role-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px;
        margin-bottom: 24px;
      }
      .role-card {
        height: 100%;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      .role-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--wa-shadow-3, 0 3px 5px rgba(0,0,0,0.2));
      }
      .role-card.selected {
        border: 2px solid var(--wa-primary-color, #3f51b5);
      }
      .role-content {
        padding: 16px;
      }
      .role-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }
      .role-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .role-description {
        color: var(--wa-text-secondary-color, #757575);
        margin: 0 0 16px 0;
        font-size: 14px;
      }
      .role-meta {
        color: var(--wa-text-secondary-color, #757575);
        font-size: 14px;
        margin-top: 12px;
      }
      .role-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 16px;
      }
      .permission-list {
        margin-top: 16px;
      }
      .permission-category {
        margin-bottom: 24px;
      }
      .category-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0 0 12px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .permission-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 12px;
      }
      .permission-item {
        padding: 12px;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-surface-color, #ffffff);
      }
      .permission-name {
        font-weight: 500;
        margin-bottom: 4px;
      }
      .permission-description {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .permission-filters {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
        flex-wrap: wrap;
      }
      .permission-chip {
        border-radius: 16px;
        font-size: 12px;
        padding: 4px 8px;
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
        display: inline-flex;
        align-items: center;
        margin-right: 8px;
        margin-bottom: 8px;
      }
      .chip-badge {
        background-color: var(--wa-primary-color, #3f51b5);
        color: white;
        border-radius: 50%;
        width: 16px;
        height: 16px;
        font-size: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-left: 4px;
      }
      .detail-panel {
        margin-top: 24px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      .detail-header {
        padding: 16px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .detail-content {
        padding: 16px;
      }
      .detail-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0;
      }
      .user-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
      }
      .user-name {
        font-weight: 500;
      }
      .user-email {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .role-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      .stat-card {
        padding: 16px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        text-align: center;
      }
      .stat-value {
        font-size: 24px;
        font-weight: 500;
        color: var(--wa-primary-color, #3f51b5);
        margin-bottom: 4px;
      }
      .stat-label {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .permission-view-toggle {
        display: flex;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        overflow: hidden;
      }
      .view-option {
        padding: 8px 16px;
        cursor: pointer;
        background-color: var(--wa-surface-color, #ffffff);
      }
      .view-option.active {
        background-color: var(--wa-primary-color, #3f51b5);
        color: white;
      }
    `;
  }
  constructor() {
    super();
    this.roles = [];
    this.permissions = [];
    this.currentRole = null;
    this.showRoleDialog = false;
    this.showDeleteDialog = false;
    this.roleToDelete = null;
    this.loading = false;
    this.error = null;
    this.searchTerm = '';
    this.permissionCategories = ['All', 'Entity', 'Report', 'Administration', 'Security', 'API'];
    this.selectedCategory = 'All';
    this.permissionView = 'grid';
    this.selectedRoleId = null;
    
    // Mock data for demo
    this._loadMockData();
  }
  _loadMockData() {
    this.roles = [
      {
        id: '1',
        name: 'Administrator',
        description: 'Full system access with all permissions',
        system: true,
        userCount: 3,
        permissions: ['*'],
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z'
      },
      {
        id: '2',
        name: 'Report Viewer',
        description: 'Can view and export reports but not create or modify them',
        system: false,
        userCount: 12,
        permissions: ['report:view', 'report:export'],
        createdAt: '2023-01-15T00:00:00Z',
        updatedAt: '2023-02-01T00:00:00Z'
      },
      {
        id: '3',
        name: 'Report Administrator',
        description: 'Can create, view, and manage all reports',
        system: false,
        userCount: 5,
        permissions: ['report:view', 'report:create', 'report:edit', 'report:delete', 'report:export', 'report:schedule'],
        createdAt: '2023-01-20T00:00:00Z',
        updatedAt: '2023-02-15T00:00:00Z'
      },
      {
        id: '4',
        name: 'Data Editor',
        description: 'Can view and edit data but cannot manage system settings',
        system: false,
        userCount: 24,
        permissions: ['entity:view', 'entity:create', 'entity:edit', 'entity:delete'],
        createdAt: '2023-02-10T00:00:00Z',
        updatedAt: '2023-03-05T00:00:00Z'
      },
      {
        id: '5',
        name: 'Guest',
        description: 'Limited read-only access to the system',
        system: true,
        userCount: 8,
        permissions: ['entity:view', 'report:view'],
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z'
      }
    ];
    
    this.permissions = [
      {
        id: 'entity:view',
        name: 'View Entities',
        description: 'Can view entity data',
        category: 'Entity'
      },
      {
        id: 'entity:create',
        name: 'Create Entities',
        description: 'Can create new entity records',
        category: 'Entity'
      },
      {
        id: 'entity:edit',
        name: 'Edit Entities',
        description: 'Can modify existing entity records',
        category: 'Entity'
      },
      {
        id: 'entity:delete',
        name: 'Delete Entities',
        description: 'Can delete entity records',
        category: 'Entity'
      },
      {
        id: 'report:view',
        name: 'View Reports',
        description: 'Can view reports and dashboards',
        category: 'Report'
      },
      {
        id: 'report:create',
        name: 'Create Reports',
        description: 'Can create new report templates',
        category: 'Report'
      },
      {
        id: 'report:edit',
        name: 'Edit Reports',
        description: 'Can modify existing report templates',
        category: 'Report'
      },
      {
        id: 'report:delete',
        name: 'Delete Reports',
        description: 'Can delete report templates',
        category: 'Report'
      },
      {
        id: 'report:export',
        name: 'Export Reports',
        description: 'Can export reports in various formats',
        category: 'Report'
      },
      {
        id: 'report:schedule',
        name: 'Schedule Reports',
        description: 'Can schedule automated report generation',
        category: 'Report'
      },
      {
        id: 'admin:users',
        name: 'Manage Users',
        description: 'Can create, modify, and delete user accounts',
        category: 'Administration'
      },
      {
        id: 'admin:roles',
        name: 'Manage Roles',
        description: 'Can create, modify, and delete roles',
        category: 'Administration'
      },
      {
        id: 'admin:settings',
        name: 'Manage Settings',
        description: 'Can modify system settings',
        category: 'Administration'
      },
      {
        id: 'security:audit',
        name: 'View Audit Logs',
        description: 'Can view security audit logs',
        category: 'Security'
      },
      {
        id: 'api:access',
        name: 'API Access',
        description: 'Can use the API to access the system',
        category: 'API'
      }
    ];
  }
  connectedCallback() {
    super.connectedCallback();
    // In a real app, you would fetch roles and permissions from the server
    // this.loadRoles();
    // this.loadPermissions();
  }
  handleSearch(e) {
    this.searchTerm = e.target.value.toLowerCase();
  }
  selectRole(roleId) {
    this.selectedRoleId = this.selectedRoleId === roleId ? null : roleId;
  }
  showAddRole() {
    this.currentRole = {
      name: '',
      description: '',
      permissions: []
    };
    this.showRoleDialog = true;
  }
  showEditRole(role) {
    this.currentRole = {...role};
    this.showRoleDialog = true;
  }
  confirmDeleteRole(role) {
    this.roleToDelete = role;
    this.showDeleteDialog = true;
  }
  cancelDelete() {
    this.showDeleteDialog = false;
    this.roleToDelete = null;
  }
  closeRoleDialog() {
    this.showRoleDialog = false;
    this.currentRole = null;
  }
  handleRoleNameChange(e) {
    this.currentRole = {
      ...this.currentRole,
      name: e.target.value
    };
  }
  handleRoleDescriptionChange(e) {
    this.currentRole = {
      ...this.currentRole,
      description: e.target.value
    };
  }
  togglePermission(permissionId) {
    const permissions = [...(this.currentRole.permissions || [])];
    
    if (permissions.includes(permissionId)) {
      // Remove permission
      const index = permissions.indexOf(permissionId);
      permissions.splice(index, 1);
    } else {
      // Add permission
      permissions.push(permissionId);
    }
    
    this.currentRole = {
      ...this.currentRole,
      permissions
    };
  }
  selectCategory(category) {
    this.selectedCategory = category;
  }
  selectPermissionView(view) {
    this.permissionView = view;
  }
  async saveRole() {
    if (!this.currentRole.name) {
      this._showNotification('Role name is required', 'error');
      return;
    }
    
    this.loading = true;
    
    try {
      // In a real app, you would save the role to the server
      // const response = await fetch('/api/authorization/roles', {
      //   method: this.currentRole.id ? 'PUT' : 'POST',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify(this.currentRole)
      // });
      
      // Mock saving
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (this.currentRole.id) {
        // Update existing role
        this.roles = this.roles.map(role => 
          role.id === this.currentRole.id ? this.currentRole : role
        );
      } else {
        // Add new role
        const newRole = {
          ...this.currentRole,
          id: `${this.roles.length + 1}`,
          userCount: 0,
          system: false,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        this.roles = [...this.roles, newRole];
      }
      
      this._showNotification(
        `Role ${this.currentRole.id ? 'updated' : 'created'} successfully`, 
        'success'
      );
      
      this.closeRoleDialog();
      
    } catch (err) {
      console.error('Failed to save role:', err);
      this._showNotification(`Error saving role: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  async deleteRole() {
    if (!this.roleToDelete) return;
    
    this.loading = true;
    
    try {
      // In a real app, you would delete the role from the server
      // const response = await fetch(`/api/authorization/roles/${this.roleToDelete.id}`, {
      //   method: 'DELETE'
      // });
      
      // Mock deletion
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Remove role from list
      this.roles = this.roles.filter(role => role.id !== this.roleToDelete.id);
      
      this._showNotification('Role deleted successfully', 'success');
      
      this.cancelDelete();
      
    } catch (err) {
      console.error('Failed to delete role:', err);
      this._showNotification(`Error deleting role: ${err.message}`, 'error');
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
  get filteredRoles() {
    if (!this.roles || this.roles.length === 0) {
      return [];
    }
    
    let filtered = [...this.roles];
    
    if (this.searchTerm) {
      filtered = filtered.filter(role =>
        role.name.toLowerCase().includes(this.searchTerm) ||
        role.description.toLowerCase().includes(this.searchTerm)
      );
    }
    
    return filtered;
  }
  get filteredPermissions() {
    if (!this.permissions || this.permissions.length === 0) {
      return [];
    }
    
    if (this.selectedCategory === 'All') {
      return this.permissions;
    }
    
    return this.permissions.filter(permission => 
      permission.category === this.selectedCategory
    );
  }
  get permissionsByCategory() {
    const grouped = {};
    
    this.permissions.forEach(permission => {
      if (!grouped[permission.category]) {
        grouped[permission.category] = [];
      }
      grouped[permission.category].push(permission);
    });
    
    return grouped;
  }
  get selectedRole() {
    if (!this.selectedRoleId) return null;
    return this.roles.find(role => role.id === this.selectedRoleId);
  }
  renderRoleDialog() {
    if (!this.showRoleDialog || !this.currentRole) return html``;
    
    return html`
      <wa-dialog open @close=${this.closeRoleDialog}>
        <div slot="header">
          ${this.currentRole.id ? 'Edit Role' : 'Add Role'}
        </div>
        
        <div>
          <wa-input 
            label="Role Name"
            required
            .value=${this.currentRole.name || ''}
            @input=${this.handleRoleNameChange}
            placeholder="e.g., Report Administrator">
          </wa-input>
          
          <wa-input 
            label="Description"
            .value=${this.currentRole.description || ''}
            @input=${this.handleRoleDescriptionChange}
            placeholder="Brief description of the role and its purpose"
            style="margin-top: 16px;">
          </wa-input>
          
          <div style="margin-top: 24px;">
            <div style="font-weight: 500; margin-bottom: 16px;">Permissions</div>
            
            <div class="permission-filters">
              <div style="font-weight: 500; margin-right: 8px;">Categories:</div>
              ${this.permissionCategories.map(category => html`
                <wa-button 
                  variant=${this.selectedCategory === category ? 'filled' : 'outlined'}
                  size="small"
                  @click=${() => this.selectCategory(category)}>
                  ${category}
                </wa-button>
              `)}
            </div>
            
            <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
              <div class="permission-view-toggle">
                <div 
                  class="view-option ${this.permissionView === 'grid' ? 'active' : ''}"
                  @click=${() => this.selectPermissionView('grid')}>
                  <wa-icon name="grid_view"></wa-icon>
                </div>
                <div 
                  class="view-option ${this.permissionView === 'list' ? 'active' : ''}"
                  @click=${() => this.selectPermissionView('list')}>
                  <wa-icon name="list"></wa-icon>
                </div>
              </div>
              
              <wa-button variant="text" @click=${() => {
                this.currentRole = {
                  ...this.currentRole,
                  permissions: this.permissions.map(p => p.id)
                };
              }}>Select All</wa-button>
            </div>
            
            ${this.permissionView === 'grid' ? html`
              <div class="permission-grid">
                ${this.filteredPermissions.map(permission => html`
                  <div class="permission-item">
                    <wa-checkbox
                      ?checked=${this.currentRole.permissions?.includes(permission.id)}
                      @change=${() => this.togglePermission(permission.id)}>
                      <div class="permission-name">${permission.name}</div>
                      <div class="permission-description">${permission.description}</div>
                    </wa-checkbox>
                  </div>
                `)}
              </div>
            ` : html`
              <wa-card elevation="0" style="margin-bottom: 16px;">
                ${this.filteredPermissions.map(permission => html`
                  <div style="padding: 8px 16px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <div style="font-weight: 500;">${permission.name}</div>
                      <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${permission.description}</div>
                    </div>
                    <wa-checkbox
                      ?checked=${this.currentRole.permissions?.includes(permission.id)}
                      @change=${() => this.togglePermission(permission.id)}>
                    </wa-checkbox>
                  </div>
                  <wa-divider></wa-divider>
                `)}
              </wa-card>
            `}
          </div>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeRoleDialog}>Cancel</wa-button>
          <wa-button @click=${this.saveRole}>
            ${this.currentRole.id ? 'Update' : 'Create'} Role
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  renderDeleteDialog() {
    if (!this.showDeleteDialog || !this.roleToDelete) return html``;
    
    return html`
      <wa-dialog open @close=${this.cancelDelete}>
        <div slot="header">Delete Role</div>
        
        <div>
          <p>Are you sure you want to delete the role "${this.roleToDelete.name}"?</p>
          
          ${this.roleToDelete.userCount > 0 ? html`
            <wa-alert type="warning" style="margin-top: 16px;">
              This role is assigned to ${this.roleToDelete.userCount} user${this.roleToDelete.userCount !== 1 ? 's' : ''}.
              These users will lose the permissions granted by this role.
            </wa-alert>
          ` : ''}
          
          ${this.roleToDelete.system ? html`
            <wa-alert type="error" style="margin-top: 16px;">
              This is a system role and cannot be deleted. System roles are essential
              for the proper functioning of the application.
            </wa-alert>
          ` : ''}
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.cancelDelete}>Cancel</wa-button>
          <wa-button 
            color="error" 
            @click=${this.deleteRole}
            ?disabled=${this.roleToDelete.system}>
            Delete Role
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  renderRoleDetail() {
    if (!this.selectedRole) return html``;
    
    const role = this.selectedRole;
    const rolePermissions = this.permissions.filter(p => 
      role.permissions.includes('*') || role.permissions.includes(p.id)
    );
    
    // Group permissions by category
    const permissionsByCategory = {};
    rolePermissions.forEach(permission => {
      if (!permissionsByCategory[permission.category]) {
        permissionsByCategory[permission.category] = [];
      }
      permissionsByCategory[permission.category].push(permission);
    });
    
    // Mock user data
    const mockUsers = [
      { id: 1, name: 'John Doe', email: 'john.doe@example.com', avatar: 'JD' },
      { id: 2, name: 'Jane Smith', email: 'jane.smith@example.com', avatar: 'JS' },
      { id: 3, name: 'Bob Johnson', email: 'bob.johnson@example.com', avatar: 'BJ' }
    ];
    
    return html`
      <div class="detail-panel">
        <div class="detail-header">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 class="detail-title">${role.name}</h2>
            
            <div>
              <wa-button variant="outlined" @click=${() => this.showEditRole(role)}>
                <wa-icon slot="prefix" name="edit"></wa-icon>
                Edit
              </wa-button>
              
              <wa-button 
                variant="outlined" 
                color="error" 
                @click=${() => this.confirmDeleteRole(role)}>
                <wa-icon slot="prefix" name="delete"></wa-icon>
                Delete
              </wa-button>
            </div>
          </div>
          
          <p style="margin: 8px 0 0 0;">${role.description}</p>
        </div>
        
        <div class="detail-content">
          <wa-tabs>
            <wa-tab value="permissions">Permissions</wa-tab>
            <wa-tab value="users">Users (${role.userCount})</wa-tab>
            <wa-tab value="details">Details</wa-tab>
          </wa-tabs>
          
          <wa-tab-panel value="permissions" active>
            <div style="margin-top: 16px;">
              <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;">
                ${role.permissions.includes('*') ? html`
                  <wa-chip color="primary">All Permissions</wa-chip>
                ` : rolePermissions.map(permission => html`
                  <wa-chip>${permission.name}</wa-chip>
                `)}
              </div>
              
              ${!role.permissions.includes('*') ? html`
                ${Object.entries(permissionsByCategory).map(([category, permissions]) => html`
                  <div class="permission-category">
                    <h3 class="category-title">${category}</h3>
                    <div class="permission-grid">
                      ${permissions.map(permission => html`
                        <div class="permission-item">
                          <div class="permission-name">${permission.name}</div>
                          <div class="permission-description">${permission.description}</div>
                        </div>
                      `)}
                    </div>
                  </div>
                `)}
              ` : html`
                <wa-alert type="info">
                  This role has the "*" permission, which grants access to all system functions.
                  This is typically reserved for system administrators.
                </wa-alert>
              `}
            </div>
          </wa-tab-panel>
          
          <wa-tab-panel value="users">
            <div style="margin-top: 16px;">
              ${role.userCount > 0 ? html`
                <div style="margin-bottom: 16px;">
                  <wa-input 
                    placeholder="Search users..."
                    style="width: 300px;">
                    <wa-icon slot="prefix" name="search"></wa-icon>
                  </wa-input>
                </div>
                
                <wa-card elevation="0">
                  ${mockUsers.map(user => html`
                    <div class="user-row">
                      <wa-avatar size="small" style="background-color: var(--wa-primary-color);">${user.avatar}</wa-avatar>
                      <div style="flex: 1;">
                        <div class="user-name">${user.name}</div>
                        <div class="user-email">${user.email}</div>
                      </div>
                      <wa-button variant="text">Remove</wa-button>
                    </div>
                    <wa-divider></wa-divider>
                  `)}
                </wa-card>
                
                <div style="margin-top: 16px; text-align: center;">
                  <wa-button variant="outlined">
                    <wa-icon slot="prefix" name="add"></wa-icon>
                    Add Users to Role
                  </wa-button>
                </div>
              ` : html`
                <div class="empty-list" style="text-align: center; padding: 32px;">
                  <wa-icon name="people" size="large" style="margin-bottom: 12px;"></wa-icon>
                  <div>No users assigned to this role yet.</div>
                  <wa-button style="margin-top: 16px;">
                    <wa-icon slot="prefix" name="add"></wa-icon>
                    Add Users to Role
                  </wa-button>
                </div>
              `}
            </div>
          </wa-tab-panel>
          
          <wa-tab-panel value="details">
            <div style="margin-top: 16px;">
              <div style="margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <div style="font-weight: 500;">Role ID</div>
                  <div>${role.id}</div>
                </div>
                
                <wa-divider></wa-divider>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 8px 0;">
                  <div style="font-weight: 500;">System Role</div>
                  <div>${role.system ? 'Yes' : 'No'}</div>
                </div>
                
                <wa-divider></wa-divider>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 8px 0;">
                  <div style="font-weight: 500;">Created</div>
                  <div>${new Date(role.createdAt).toLocaleString()}</div>
                </div>
                
                <wa-divider></wa-divider>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 8px 0;">
                  <div style="font-weight: 500;">Last Updated</div>
                  <div>${new Date(role.updatedAt).toLocaleString()}</div>
                </div>
              </div>
              
              <wa-alert type="info">
                Role IDs are used in the API and for programmatic access. The system will automatically
                handle role assignments and permission checks based on this ID.
              </wa-alert>
            </div>
          </wa-tab-panel>
        </div>
      </div>
    `;
  }
  render() {
    return html`
      <div class="manager-container">
        <div class="manager-header">
          <h1 class="manager-title">Role Management</h1>
          <p class="manager-subtitle">Create and manage roles to control access to system features</p>
        </div>
        
        <div class="search-bar">
          <wa-input 
            placeholder="Search roles..."
            .value=${this.searchTerm}
            @input=${this.handleSearch}
            class="search-input">
            <wa-icon slot="prefix" name="search"></wa-icon>
          </wa-input>
          
          <wa-button @click=${this.showAddRole}>
            <wa-icon slot="prefix" name="add"></wa-icon>
            Add Role
          </wa-button>
        </div>
        
        ${this.error ? html`
          <wa-alert type="error" style="margin-bottom: 24px;">
            ${this.error}
            <wa-button slot="action" variant="text">Retry</wa-button>
          </wa-alert>
        ` : ''}
        
        <div class="role-stats">
          <div class="stat-card">
            <div class="stat-value">${this.roles.length}</div>
            <div class="stat-label">Total Roles</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-value">${this.roles.reduce((total, role) => total + (role.userCount || 0), 0)}</div>
            <div class="stat-label">Total Assignments</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-value">${this.permissions.length}</div>
            <div class="stat-label">Permission Types</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-value">${this.roles.filter(r => r.system).length}</div>
            <div class="stat-label">System Roles</div>
          </div>
        </div>
        
        <div class="role-grid">
          ${this.filteredRoles.map(role => html`
            <wa-card 
              class="role-card ${this.selectedRoleId === role.id ? 'selected' : ''}"
              elevation="1"
              @click=${() => this.selectRole(role.id)}>
              <div class="role-content">
                <div class="role-header">
                  <h2 class="role-title">${role.name}</h2>
                  ${role.system ? html`
                    <wa-chip size="small">System</wa-chip>
                  ` : ''}
                </div>
                
                <p class="role-description">${role.description}</p>
                
                <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                  ${role.permissions.includes('*') ? html`
                    <span class="permission-chip">
                      All Permissions
                    </span>
                  ` : role.permissions.slice(0, 3).map(permId => html`
                    <span class="permission-chip">
                      ${this.permissions.find(p => p.id === permId)?.name || permId}
                    </span>
                  `)}
                  
                  ${role.permissions.length > 3 && !role.permissions.includes('*') ? html`
                    <span class="permission-chip">
                      +${role.permissions.length - 3} more
                      <span class="chip-badge">${role.permissions.length - 3}</span>
                    </span>
                  ` : ''}
                </div>
                
                <div class="role-meta">
                  <div>Users: ${role.userCount}</div>
                  <div>Last updated: ${new Date(role.updatedAt).toLocaleString()}</div>
                </div>
                
                <div class="role-actions">
                  <wa-button variant="text" @click=${(e) => {
                    e.stopPropagation();
                    this.showEditRole(role);
                  }}>
                    Edit
                  </wa-button>
                  
                  <wa-button 
                    variant="text" 
                    color="error" 
                    ?disabled=${role.system}
                    @click=${(e) => {
                      e.stopPropagation();
                      this.confirmDeleteRole(role);
                    }}>
                    Delete
                  </wa-button>
                </div>
              </div>
            </wa-card>
          `)}
        </div>
        
        ${this.renderRoleDetail()}
        ${this.renderRoleDialog()}
        ${this.renderDeleteDialog()}
        
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
// Define the custom element if not already registered
if (!customElements.get('wa-role-manager')) {
  customElements.define('wa-role-manager', WebAwesomeRoleManager);
  console.log('wa-role-manager component registered');
} else {
  console.log('wa-role-manager component already registered');
}