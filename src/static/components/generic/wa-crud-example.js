import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
import './wa-crud-manager.js';
/**
 * @element wa-crud-example
 * @description Example usage of wa-crud-manager with a sample configuration
 */
export class WebAwesomeCrudExample extends LitElement {
  static get properties() {
    return {
      loading: { type: Boolean },
      apiMode: { type: Boolean }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        padding: 20px;
      }
      
      .header {
        margin-bottom: 24px;
      }
      
      .title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
      }
      
      .subtitle {
        color: #666;
        margin: 0;
      }
      
      .example-tabs {
        margin-bottom: 20px;
        display: flex;
        gap: 16px;
      }
      
      .tab-button {
        padding: 8px 16px;
        border: 1px solid #ccc;
        border-radius: 4px;
        background: white;
        cursor: pointer;
      }
      
      .tab-button.active {
        background: #1976d2;
        color: white;
        border-color: #1976d2;
      }
      
      .code-example {
        background-color: #f5f5f5;
        padding: 16px;
        border-radius: 4px;
        margin-bottom: 24px;
        font-family: monospace;
        white-space: pre-wrap;
      }
    `;
  }
  constructor() {
    super();
    this.loading = false;
    this.apiMode = false;
  }
  // Example schema for users
  getUserSchema() {
    return {
      fields: [
        {
          name: 'id',
          label: 'ID',
          type: 'number',
          readOnly: true
        },
        {
          name: 'name',
          label: 'Name',
          type: 'string',
          isTitle: true,
          inSummary: true,
          sortable: true,
          filterable: true,
          description: 'User\'s full name'
        },
        {
          name: 'email',
          label: 'Email',
          type: 'string',
          inSummary: true,
          sortable: true,
          filterable: true
        },
        {
          name: 'role',
          label: 'Role',
          type: 'select',
          inSummary: true,
          options: [
            { value: 'admin', label: 'Administrator' },
            { value: 'editor', label: 'Editor' },
            { value: 'user', label: 'User' }
          ],
          filterable: true
        },
        {
          name: 'status',
          label: 'Status',
          type: 'boolean',
          inSummary: true,
          sortable: true,
          filterable: true
        },
        {
          name: 'createdAt',
          label: 'Created Date',
          type: 'datetime',
          sortable: true
        },
        {
          name: 'lastLogin',
          label: 'Last Login',
          type: 'datetime',
          sortable: true
        }
      ],
      displayName: "User",
      displayNamePlural: "Users",
      description: "User accounts in the system"
    };
  }
  // Example custom actions
  getCustomActions() {
    return [
      {
        id: 'reset-password',
        label: 'Reset Password',
        icon: 'lock_reset',
        color: 'warning',
        location: 'item',
        bulk: false,
        confirmationRequired: true,
        confirmationMessage: 'Are you sure you want to reset the password for this user?',
        apiEndpoint: '/api/users/{id}/reset-password',
        method: 'POST',
        handler: (entity) => {
          alert(`Password reset requested for ${entity.name}`);
        }
      },
      {
        id: 'send-notification',
        label: 'Send Notification',
        icon: 'notification_important',
        color: 'primary',
        location: 'item',
        bulk: false,
        apiEndpoint: '/api/users/{id}/notify',
        method: 'POST',
        handler: (entity) => {
          alert(`Sending notification to ${entity.name}`);
        }
      },
      {
        id: 'deactivate-users',
        label: 'Deactivate Users',
        icon: 'block',
        color: 'error',
        location: 'bulk',
        bulk: true,
        confirmationRequired: true,
        confirmationMessage: 'Are you sure you want to deactivate the selected users?',
        apiEndpoint: '/api/users/bulk-deactivate',
        method: 'POST',
        bulkHandler: (selectedIds) => {
          alert(`Deactivating users with IDs: ${selectedIds.join(', ')}`);
        }
      }
    ];
  }
  // Mock API data for demo purposes
  generateMockUsers(count = 25) {
    const users = [];
    const roles = ['admin', 'editor', 'user'];
    const now = new Date();
    
    for (let i = 1; i <= count; i++) {
      const firstName = ['John', 'Jane', 'Alex', 'Sarah', 'Michael', 'Emma', 'David', 'Olivia'][Math.floor(Math.random() * 8)];
      const lastName = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson'][Math.floor(Math.random() * 8)];
      const name = `${firstName} ${lastName}`;
      const email = `${firstName.toLowerCase()}.${lastName.toLowerCase()}@example.com`;
      const role = roles[Math.floor(Math.random() * roles.length)];
      const status = Math.random() > 0.3;
      
      // Random date within the last 60 days
      const createdAt = new Date(now.getTime() - Math.random() * 60 * 24 * 60 * 60 * 1000);
      
      // Random date after creation
      const lastLogin = new Date(createdAt.getTime() + Math.random() * (now.getTime() - createdAt.getTime()));
      
      users.push({
        id: i,
        name,
        email,
        role,
        status,
        createdAt: createdAt.toISOString(),
        lastLogin: lastLogin.toISOString()
      });
    }
    
    return users;
  }
  // Mock API endpoint - would replace with real API calls in production
  setupMockApi() {
    const mockUsers = this.generateMockUsers();
    const schema = this.getUserSchema();
    const actions = { actions: this.getCustomActions() };
    
    // Mock fetch to intercept API calls
    const originalFetch = window.fetch;
    window.fetch = (url, options) => {
      // Only intercept calls to our mock API
      if (url.toString().includes('/api/users')) {
        const urlStr = url.toString();
        
        // Handle schema API
        if (urlStr.includes('/api/users/schema')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(schema)
          });
        }
        
        // Handle actions API
        if (urlStr.includes('/api/users/actions')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(actions)
          });
        }
        
        // Handle custom actions
        if (urlStr.includes('/reset-password')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true, message: 'Password reset link sent' })
          });
        }
        
        if (urlStr.includes('/notify')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true, message: 'Notification sent' })
          });
        }
        
        if (urlStr.includes('/bulk-deactivate')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true, message: 'Users deactivated' })
          });
        }
        
        // Handle standard CRUD operations
        return this.handleMockUserApi(url, options, mockUsers);
      }
      
      // Pass through all other requests
      return originalFetch(url, options);
    };
  }
  // Handle mock API requests
  handleMockUserApi(url, options, users) {
    const urlObj = new URL(url, window.location.origin);
    const path = urlObj.pathname;
    const method = options?.method || 'GET';
    
    // Parse query parameters
    const searchParams = urlObj.searchParams;
    const page = parseInt(searchParams.get('page[number]') || '1', 10);
    const pageSize = parseInt(searchParams.get('page[size]') || '20', 10);
    const sortParam = searchParams.get('sort') || '';
    
    // Extract sort field and direction
    let sortField = 'id';
    let sortDirection = 'asc';
    if (sortParam) {
      if (sortParam.startsWith('-')) {
        sortField = sortParam.substring(1);
        sortDirection = 'desc';
      } else {
        sortField = sortParam;
      }
    }
    
    // Extract filters
    const filters = {};
    for (const [key, value] of searchParams.entries()) {
      if (key.startsWith('filter[') && key.endsWith(']')) {
        const field = key.slice(7, -1);
        filters[field] = value;
      }
    }
    
    // Simulate delay for realistic API call
    return new Promise(resolve => {
      setTimeout(() => {
        // Handle different API endpoints
        if (path === '/api/users' && method === 'GET') {
          // Filter users
          let filteredUsers = [...users];
          
          // Apply search filter
          if (filters.search) {
            const searchTerm = filters.search.toLowerCase();
            filteredUsers = filteredUsers.filter(user => 
              user.name.toLowerCase().includes(searchTerm) || 
              user.email.toLowerCase().includes(searchTerm)
            );
          }
          
          // Apply other filters
          Object.entries(filters).forEach(([field, value]) => {
            if (field !== 'search' && value) {
              if (field === 'status') {
                // Convert string 'true'/'false' to boolean
                const boolValue = value === 'true';
                filteredUsers = filteredUsers.filter(user => user[field] === boolValue);
              } else {
                filteredUsers = filteredUsers.filter(user => 
                  String(user[field]).toLowerCase() === String(value).toLowerCase()
                );
              }
            }
          });
          
          // Apply sorting
          filteredUsers.sort((a, b) => {
            const valueA = a[sortField];
            const valueB = b[sortField];
            
            if (valueA < valueB) return sortDirection === 'asc' ? -1 : 1;
            if (valueA > valueB) return sortDirection === 'asc' ? 1 : -1;
            return 0;
          });
          
          // Apply pagination
          const totalCount = filteredUsers.length;
          const start = (page - 1) * pageSize;
          const end = start + pageSize;
          const paginatedUsers = filteredUsers.slice(start, end);
          
          resolve({
            ok: true,
            json: () => Promise.resolve({
              data: paginatedUsers,
              meta: {
                total: totalCount,
                page,
                pageSize
              }
            })
          });
        } 
        else if (path.match(/^\/api\/users\/\d+$/) && method === 'GET') {
          // Get single user
          const id = parseInt(path.split('/').pop(), 10);
          const user = users.find(u => u.id === id);
          
          if (user) {
            resolve({
              ok: true,
              json: () => Promise.resolve({ data: user })
            });
          } else {
            resolve({
              ok: false,
              status: 404,
              json: () => Promise.resolve({ error: 'User not found' })
            });
          }
        }
        else if (path === '/api/users' && method === 'POST') {
          // Create user
          const newUser = JSON.parse(options.body);
          newUser.id = users.length + 1;
          newUser.createdAt = new Date().toISOString();
          newUser.lastLogin = null;
          
          users.push(newUser);
          
          resolve({
            ok: true,
            json: () => Promise.resolve({ data: newUser })
          });
        }
        else if (path.match(/^\/api\/users\/\d+$/) && method === 'PUT') {
          // Update user
          const id = parseInt(path.split('/').pop(), 10);
          const userIndex = users.findIndex(u => u.id === id);
          
          if (userIndex !== -1) {
            const updatedUser = JSON.parse(options.body);
            updatedUser.id = id; // Ensure ID doesn't change
            users[userIndex] = { ...users[userIndex], ...updatedUser };
            
            resolve({
              ok: true,
              json: () => Promise.resolve({ data: users[userIndex] })
            });
          } else {
            resolve({
              ok: false,
              status: 404,
              json: () => Promise.resolve({ error: 'User not found' })
            });
          }
        }
        else if (path.match(/^\/api\/users\/\d+$/) && method === 'DELETE') {
          // Delete user
          const id = parseInt(path.split('/').pop(), 10);
          const userIndex = users.findIndex(u => u.id === id);
          
          if (userIndex !== -1) {
            const deletedUser = users.splice(userIndex, 1)[0];
            
            resolve({
              ok: true,
              json: () => Promise.resolve({ data: deletedUser })
            });
          } else {
            resolve({
              ok: false,
              status: 404,
              json: () => Promise.resolve({ error: 'User not found' })
            });
          }
        }
        else {
          // Unhandled endpoint
          resolve({
            ok: false,
            status: 404,
            json: () => Promise.resolve({ error: 'Endpoint not found' })
          });
        }
      }, 300); // Simulate network delay
    });
  }
  firstUpdated() {
    // Setup mock API
    this.setupMockApi();
    
    // Configure the traditional CRUD component
    const traditionalCrudManager = this.shadowRoot.querySelector('#traditionalCrudManager');
    traditionalCrudManager.schema = this.getUserSchema();
    traditionalCrudManager.customActions = this.getCustomActions();
    
    // Add event listeners to both components
    const addEventListeners = (crudManager) => {
      if (!crudManager) return;
      
      crudManager.addEventListener('entity-created', (e) => {
        console.log('User created:', e.detail.entity);
      });
      
      crudManager.addEventListener('entity-updated', (e) => {
        console.log('User updated:', e.detail.entity);
      });
      
      crudManager.addEventListener('entity-deleted', (e) => {
        console.log('User deleted, ID:', e.detail.entityId);
      });
      
      crudManager.addEventListener('action-executed', (e) => {
        console.log('Custom action executed:', e.detail);
      });
      
      crudManager.addEventListener('bulk-action-executed', (e) => {
        console.log('Bulk action executed:', e.detail);
      });
    };
    
    // Add listeners to traditional mode
    addEventListeners(traditionalCrudManager);
    
    // Add listeners to API mode when it appears
    this.updateComplete.then(() => {
      const apiCrudManager = this.shadowRoot.querySelector('#apiCrudManager');
      addEventListeners(apiCrudManager);
    });
  }
  
  // Toggle between traditional and API modes
  toggleMode() {
    this.apiMode = !this.apiMode;
  }
  render() {
    return html`
      <div class="header">
        <h1 class="title">CRUD Manager Example</h1>
        <p class="subtitle">Demonstration of the wa-crud-manager component with mocked user data</p>
      </div>
      
      <div class="example-tabs">
        <button 
          @click=${() => this.toggleMode()} 
          class="tab-button ${!this.apiMode ? 'active' : ''}">
          Traditional Mode
        </button>
        <button 
          @click=${() => this.toggleMode()} 
          class="tab-button ${this.apiMode ? 'active' : ''}">
          API Mode
        </button>
      </div>
      
      ${!this.apiMode ? html`
        <!-- Traditional mode with schema and actions passed as properties -->
        <wa-crud-manager
          id="traditionalCrudManager"
          base-url="/api"
          entity-type="users"
          title="User Management (Traditional)"
          description="Schema and actions passed directly as properties"
          layout-type="table">
        </wa-crud-manager>
        
        <div class="code-example">
          // Traditional usage with schema and actions passed directly
          &lt;wa-crud-manager
            base-url="/api"
            entity-type="users"
            title="User Management"
            description="Schema and actions passed directly as properties"
            .schema=\${mySchema}
            .customActions=\${myCustomActions}&gt;
          &lt;/wa-crud-manager&gt;
        </div>
      ` : html`
        <!-- API mode with schema and actions loaded from API -->
        <wa-crud-manager
          id="apiCrudManager"
          base-url="/api"
          entity-type="users"
          title="User Management (API Mode)"
          description="Schema and actions loaded from API"
          layout-type="table"
          schema-api-enabled
          schema-api-endpoint="/api/{entityType}/schema"
          actions-api-enabled
          actions-api-endpoint="/api/{entityType}/actions">
        </wa-crud-manager>
        
        <div class="code-example">
          // API mode with schema and actions loaded dynamically
          &lt;wa-crud-manager
            base-url="/api"
            entity-type="users"
            title="User Management"
            description="Schema and actions loaded from API"
            schema-api-enabled
            schema-api-endpoint="/api/{entityType}/schema"
            actions-api-enabled
            actions-api-endpoint="/api/{entityType}/actions"&gt;
          &lt;/wa-crud-manager&gt;
        </div>
      `}
      
      <p>Open the browser console to see event output when interacting with the component.</p>
    `;
  }
}
customElements.define('wa-crud-example', WebAwesomeCrudExample);