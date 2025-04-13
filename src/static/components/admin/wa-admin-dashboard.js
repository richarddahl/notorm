import { LitElement, html, css } from 'lit';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-drawer.js';
import '@webcomponents/awesome/wa-app-bar.js';
import '@webcomponents/awesome/wa-list.js';
import '@webcomponents/awesome/wa-list-item.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-avatar.js';
import '@webcomponents/awesome/wa-divider.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-tooltip.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-menu.js';
import '@webcomponents/awesome/wa-menu-item.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-switch.js';

/**
 * @element wa-admin-dashboard
 * @description Main administration dashboard for UNO framework with WebAwesome components
 */
export class WebAwesomeAdminDashboard extends LitElement {
  static get properties() {
    return {
      drawerOpen: { type: Boolean },
      currentModule: { type: String },
      user: { type: Object },
      notifications: { type: Array },
      systemStatus: { type: Object },
      theme: { type: String },
      loading: { type: Boolean },
      error: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --sidebar-width: 280px;
        height: 100vh;
        overflow: hidden;
      }
      .dashboard-container {
        display: flex;
        height: 100%;
        background-color: var(--wa-background-color, #f5f5f5);
      }
      .header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 10;
      }
      .content-area {
        flex: 1;
        overflow-y: auto;
        margin-top: 64px;
        padding: 24px;
        height: calc(100vh - 64px);
        box-sizing: border-box;
      }
      .content-area.with-drawer {
        margin-left: var(--sidebar-width);
        width: calc(100% - var(--sidebar-width));
      }
      .sidebar-content {
        padding: 16px 0;
        height: 100%;
        overflow-y: auto;
      }
      .module-group {
        margin-bottom: 16px;
      }
      .module-group-title {
        padding: 0 16px;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        color: var(--wa-text-secondary-color, #757575);
        margin: 16px 0 8px 0;
      }
      .menu-footer {
        padding: 16px;
        margin-top: auto;
      }
      .system-status {
        margin-top: 24px;
        padding: 16px;
        border-radius: var(--wa-border-radius, 4px);
        background-color: var(--wa-surface-color, #ffffff);
      }
      .status-item {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
      }
      .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
      }
      .status-healthy {
        background-color: var(--wa-success-color, #4caf50);
      }
      .status-warning {
        background-color: var(--wa-warning-color, #ff9800);
      }
      .status-error {
        background-color: var(--wa-error-color, #f44336);
      }
      .status-text {
        font-size: 14px;
      }
      .status-detail {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .welcome-card {
        margin-bottom: 24px;
        background: linear-gradient(to right, var(--wa-primary-color, #3f51b5), var(--wa-secondary-color, #f50057));
        color: white;
      }
      .welcome-content {
        padding: 24px;
      }
      .welcome-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
      }
      .welcome-message {
        font-size: 16px;
        margin: 0;
        opacity: 0.9;
      }
      .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px;
      }
      .module-card {
        height: 100%;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      .module-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--wa-shadow-4, 0 6px 10px rgba(0,0,0,0.14), 0 1px 18px rgba(0,0,0,0.12));
      }
      .module-icon {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
        padding: 12px;
        border-radius: 50%;
        margin-bottom: 8px;
      }
      .module-content {
        padding: 24px;
        text-align: center;
      }
      .module-title {
        font-size: 18px;
        font-weight: 500;
        margin: 8px 0;
      }
      .module-description {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .notification-badge {
        font-size: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        background-color: var(--wa-error-color, #f44336);
        color: white;
        border-radius: 50%;
      }
    `;
  }

  constructor() {
    super();
    this.drawerOpen = true;
    this.currentModule = 'overview';
    this.user = {
      name: 'Admin User',
      email: 'admin@example.com',
      avatar: ''
    };
    this.notifications = [
      { 
        id: 1, 
        title: 'System Update Available', 
        message: 'A new version of UNO is available', 
        type: 'info', 
        time: '2h ago' 
      },
      { 
        id: 2, 
        title: 'Cache Invalidation', 
        message: 'Global cache invalidation completed', 
        type: 'success', 
        time: '3h ago' 
      },
      { 
        id: 3, 
        title: 'Failed Jobs', 
        message: '2 background jobs failed execution', 
        type: 'error', 
        time: '4h ago' 
      }
    ];
    this.systemStatus = {
      database: { status: 'healthy', message: 'Connected', time: '100ms' },
      cache: { status: 'healthy', message: 'Operational', time: '5ms' },
      jobs: { status: 'warning', message: '2 failed jobs', time: '' },
      api: { status: 'healthy', message: 'All endpoints available', time: '250ms' }
    };
    this.theme = localStorage.getItem('uno-theme') || 'light';
    this.loading = false;
    this.error = null;
    
    this.moduleGroups = [
      {
        title: 'Core',
        modules: [
          { id: 'overview', name: 'Overview', icon: 'dashboard' },
          { id: 'users', name: 'Users', icon: 'people' },
          { id: 'security', name: 'Security', icon: 'security' }
        ]
      },
      {
        title: 'Data',
        modules: [
          { id: 'entities', name: 'Entities', icon: 'storage' },
          { id: 'reports', name: 'Reports', icon: 'assessment' },
          { id: 'vector-search', name: 'Vector Search', icon: 'scatter_plot' }
        ]
      },
      {
        title: 'System',
        modules: [
          { id: 'monitoring', name: 'Monitoring', icon: 'monitoring' },
          { id: 'caching', name: 'Caching', icon: 'cached' },
          { id: 'jobs', name: 'Jobs', icon: 'work' }
        ]
      },
      {
        title: 'Integration',
        modules: [
          { id: 'realtime', name: 'Realtime', icon: 'bolt' },
          { id: 'offline', name: 'Offline', icon: 'cloud_off' },
          { id: 'tenants', name: 'Tenants', icon: 'apartment' }
        ]
      }
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadSystemStatus();
    
    // Apply theme
    document.body.setAttribute('theme', this.theme);
  }

  async loadSystemStatus() {
    this.loading = true;
    
    try {
      // In a real implementation, this would be an API call
      // For now, we'll simulate a delay and use the mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update system status (mock data for demo)
      this.systemStatus = {
        database: { status: 'healthy', message: 'Connected', time: '100ms' },
        cache: { status: 'healthy', message: 'Operational', time: '5ms' },
        jobs: { status: 'warning', message: '2 failed jobs', time: '' },
        api: { status: 'healthy', message: 'All endpoints available', time: '250ms' }
      };
    } catch (err) {
      console.error('Failed to load system status:', err);
      this.error = `Error loading system status: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  toggleDrawer() {
    this.drawerOpen = !this.drawerOpen;
  }

  navigateTo(moduleId) {
    this.currentModule = moduleId;
    
    // In a real app, this might update the URL or load specific content
    // For this demo, we'll just update the currentModule property
    
    // On mobile, close the drawer after navigation
    if (window.innerWidth < 768) {
      this.drawerOpen = false;
    }
  }

  toggleTheme() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('uno-theme', this.theme);
    document.body.setAttribute('theme', this.theme);
  }

  renderModuleContent() {
    switch (this.currentModule) {
      case 'overview':
        return this.renderOverview();
      case 'monitoring':
        return this.renderMonitoring();
      case 'reports':
        return this.renderReports();
      case 'security':
        return this.renderSecurity();
      case 'caching':
        return this.renderCaching();
      case 'jobs':
        return this.renderJobs();
      case 'vector-search':
        return this.renderVectorSearch();
      case 'realtime':
        return this.renderRealtime();
      case 'offline':
        return this.renderOffline();
      case 'tenants':
        return this.renderTenants();
      case 'users':
        return this.renderUsers();
      default:
        return html`
          <p>Module content not implemented yet.</p>
          <wa-button @click=${() => this.navigateTo('overview')}>
            Return to Overview
          </wa-button>
        `;
    }
  }

  renderOverview() {
    return html`
      <wa-card class="welcome-card" elevation="3">
        <div class="welcome-content">
          <h1 class="welcome-title">Welcome to UNO Administration</h1>
          <p class="welcome-message">
            Manage your application, monitor performance, and configure settings.
          </p>
        </div>
      </wa-card>
      
      <div class="dashboard-grid">
        ${this.moduleGroups.flatMap(group => group.modules).map(module => html`
          <wa-card class="module-card" elevation="1" @click=${() => this.navigateTo(module.id)}>
            <div class="module-content">
              <div class="module-icon">
                <wa-icon name="${module.icon}" size="large"></wa-icon>
              </div>
              <h2 class="module-title">${module.name}</h2>
              <p class="module-description">
                ${this.getModuleDescription(module.id)}
              </p>
            </div>
          </wa-card>
        `)}
      </div>
    `;
  }

  getModuleDescription(moduleId) {
    const descriptions = {
      'overview': 'Dashboard overview and system status',
      'users': 'User management and access control',
      'security': 'Security settings and audit logs',
      'entities': 'Entity configuration and data management',
      'reports': 'Report templates and execution',
      'vector-search': 'Vector search and semantic querying',
      'monitoring': 'System health and performance metrics',
      'caching': 'Cache configuration and management',
      'jobs': 'Background job scheduling and monitoring',
      'realtime': 'Realtime communication and notifications',
      'offline': 'Offline mode and data synchronization',
      'tenants': 'Multi-tenant management and configuration'
    };
    
    return descriptions[moduleId] || 'Module description not available';
  }

  renderMonitoring() {
    return html`
      <h1>System Monitoring</h1>
      
      <wa-tabs>
        <wa-tab value="metrics">Metrics</wa-tab>
        <wa-tab value="health">Health</wa-tab>
        <wa-tab value="tracing">Tracing</wa-tab>
        <wa-tab value="logs">Logs</wa-tab>
      </wa-tabs>
      
      <wa-tab-panel value="metrics" active>
        <div style="height: 400px; margin-top: 24px; background-color: var(--wa-surface-color); border-radius: 4px; padding: 16px;">
          <h2>System Metrics</h2>
          <p>Performance metrics would be displayed here using charts and graphs.</p>
          
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 24px;">
            <wa-card>
              <div style="padding: 16px; text-align: center;">
                <h3 style="margin-top: 0;">CPU Usage</h3>
                <div style="font-size: 32px; font-weight: bold; color: var(--wa-primary-color);">24%</div>
              </div>
            </wa-card>
            
            <wa-card>
              <div style="padding: 16px; text-align: center;">
                <h3 style="margin-top: 0;">Memory</h3>
                <div style="font-size: 32px; font-weight: bold; color: var(--wa-primary-color);">3.2 GB</div>
              </div>
            </wa-card>
            
            <wa-card>
              <div style="padding: 16px; text-align: center;">
                <h3 style="margin-top: 0;">DB Connections</h3>
                <div style="font-size: 32px; font-weight: bold; color: var(--wa-primary-color);">48</div>
              </div>
            </wa-card>
            
            <wa-card>
              <div style="padding: 16px; text-align: center;">
                <h3 style="margin-top: 0;">Response Time</h3>
                <div style="font-size: 32px; font-weight: bold; color: var(--wa-primary-color);">125 ms</div>
              </div>
            </wa-card>
          </div>
        </div>
      </wa-tab-panel>
    `;
  }

  renderReports() {
    return html`
      <h1>Reports Management</h1>
      
      <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
        <wa-button @click=${() => window.location.href = '/reports/templates/new'}>
          <wa-icon slot="prefix" name="add"></wa-icon>
          New Report
        </wa-button>
      </div>
      
      <wa-card>
        <div style="padding: 0;">
          <wa-tabs>
            <wa-tab value="templates">Templates</wa-tab>
            <wa-tab value="executions">Executions</wa-tab>
            <wa-tab value="schedules">Schedules</wa-tab>
            <wa-tab value="dashboards">Dashboards</wa-tab>
          </wa-tabs>
          
          <wa-tab-panel value="templates" active>
            <div style="padding: 16px;">
              <p>The report template list would be loaded here.</p>
              <wa-button @click=${() => window.location.href = '/reports/templates'}>
                View All Templates
              </wa-button>
            </div>
          </wa-tab-panel>
        </div>
      </wa-card>
    `;
  }

  renderSecurity() {
    return html`
      <h1>Security Management</h1>
      
      <wa-tabs>
        <wa-tab value="audit">Audit Log</wa-tab>
        <wa-tab value="auth">Authentication</wa-tab>
        <wa-tab value="encryption">Encryption</wa-tab>
      </wa-tabs>
      
      <wa-tab-panel value="audit" active>
        <div style="margin-top: 24px;">
          <wa-card>
            <div style="padding: 16px;">
              <h2 style="margin-top: 0;">Audit Log</h2>
              
              <table style="width: 100%; border-collapse: collapse;">
                <thead>
                  <tr>
                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Timestamp</th>
                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">User</th>
                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Action</th>
                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Resource</th>
                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">2023-05-01 14:32:45</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">admin@example.com</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">LOGIN</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">User</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">192.168.1.1</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">2023-05-01 14:35:12</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">admin@example.com</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">UPDATE</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Role</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">192.168.1.1</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">2023-05-01 14:40:33</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">admin@example.com</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">CREATE</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">User</td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">192.168.1.1</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </wa-card>
        </div>
      </wa-tab-panel>
    `;
  }

  renderCaching() {
    return html`
      <h1>Cache Management</h1>
      
      <div style="display: flex; gap: 16px; margin-bottom: 24px;">
        <wa-button color="primary">
          <wa-icon slot="prefix" name="refresh"></wa-icon>
          Refresh Status
        </wa-button>
        
        <wa-button color="error">
          <wa-icon slot="prefix" name="delete"></wa-icon>
          Invalidate All Caches
        </wa-button>
      </div>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0;">Memory Cache</h2>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Status:</span>
              <span style="color: var(--wa-success-color);">Active</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Size:</span>
              <span>256 MB</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Items:</span>
              <span>12,548</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>Hit Rate:</span>
              <span>94.2%</span>
            </div>
            
            <div style="margin-top: 24px;">
              <wa-button variant="outlined" fullwidth>Invalidate</wa-button>
            </div>
          </div>
        </wa-card>
        
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0;">Redis Cache</h2>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Status:</span>
              <span style="color: var(--wa-success-color);">Active</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Size:</span>
              <span>1.2 GB</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Items:</span>
              <span>45,789</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>Hit Rate:</span>
              <span>88.7%</span>
            </div>
            
            <div style="margin-top: 24px;">
              <wa-button variant="outlined" fullwidth>Invalidate</wa-button>
            </div>
          </div>
        </wa-card>
        
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0;">File Cache</h2>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Status:</span>
              <span style="color: var(--wa-success-color);">Active</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Size:</span>
              <span>512 MB</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <span>Items:</span>
              <span>5,284</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>Hit Rate:</span>
              <span>97.3%</span>
            </div>
            
            <div style="margin-top: 24px;">
              <wa-button variant="outlined" fullwidth>Invalidate</wa-button>
            </div>
          </div>
        </wa-card>
      </div>
    `;
  }

  renderJobs() {
    return html`
      <h1>Background Jobs</h1>
      
      <wa-tabs>
        <wa-tab value="active">Active Jobs</wa-tab>
        <wa-tab value="queued">Queued</wa-tab>
        <wa-tab value="completed">Completed</wa-tab>
        <wa-tab value="failed">Failed</wa-tab>
      </wa-tabs>
      
      <wa-tab-panel value="active" active>
        <wa-card style="margin-top: 24px;">
          <div style="padding: 16px;">
            <table style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">ID</th>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Type</th>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Status</th>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Progress</th>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Started</th>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">job-123456</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Data Export</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-primary-color-light); color: var(--wa-primary-color);">
                      Running
                    </span>
                  </td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <div style="width: 100%; height: 8px; background-color: var(--wa-border-color); border-radius: 4px;">
                      <div style="width: 75%; height: 100%; background-color: var(--wa-primary-color); border-radius: 4px;"></div>
                    </div>
                    <div style="font-size: 12px; text-align: right;">75%</div>
                  </td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">2 min ago</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-button variant="text" color="error">Cancel</wa-button>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">job-123457</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Report Generation</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-primary-color-light); color: var(--wa-primary-color);">
                      Running
                    </span>
                  </td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <div style="width: 100%; height: 8px; background-color: var(--wa-border-color); border-radius: 4px;">
                      <div style="width: 30%; height: 100%; background-color: var(--wa-primary-color); border-radius: 4px;"></div>
                    </div>
                    <div style="font-size: 12px; text-align: right;">30%</div>
                  </td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">5 min ago</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-button variant="text" color="error">Cancel</wa-button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </wa-card>
      </wa-tab-panel>
    `;
  }

  renderVectorSearch() {
    return html`
      <h1>Vector Search</h1>
      
      <div style="display: flex; flex-direction: column; gap: 24px;">
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0;">Semantic Search</h2>
            
            <div style="display: flex; gap: 16px; margin-bottom: 16px;">
              <wa-input
                placeholder="Enter your search query"
                style="flex: 1;">
              </wa-input>
              
              <wa-button>
                <wa-icon slot="prefix" name="search"></wa-icon>
                Search
              </wa-button>
            </div>
            
            <div style="display: flex; gap: 16px; margin-bottom: 16px;">
              <wa-select
                label="Entity Type"
                style="flex: 1;">
                <wa-option value="product">Product</wa-option>
                <wa-option value="customer">Customer</wa-option>
                <wa-option value="order">Order</wa-option>
              </wa-select>
              
              <wa-select
                label="Similarity Threshold"
                style="flex: 1;">
                <wa-option value="0.7">High (0.7+)</wa-option>
                <wa-option value="0.5">Medium (0.5+)</wa-option>
                <wa-option value="0.3">Low (0.3+)</wa-option>
              </wa-select>
              
              <wa-select
                label="Max Results"
                style="flex: 1;">
                <wa-option value="10">10</wa-option>
                <wa-option value="25">25</wa-option>
                <wa-option value="50">50</wa-option>
                <wa-option value="100">100</wa-option>
              </wa-select>
            </div>
            
            <p>Enter a natural language query to search using semantic similarity.</p>
          </div>
        </wa-card>
        
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0;">Vector Index Management</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px;">
              <div style="padding: 16px; border: 1px solid var(--wa-border-color); border-radius: 4px;">
                <h3 style="margin-top: 0;">Product Vectors</h3>
                <div style="margin-bottom: 8px;">
                  <strong>Dimensions:</strong> 384
                </div>
                <div style="margin-bottom: 8px;">
                  <strong>Records:</strong> 15,482
                </div>
                <div style="margin-bottom: 8px;">
                  <strong>Last Updated:</strong> 1 hour ago
                </div>
                <div style="margin-top: 16px;">
                  <wa-button variant="outlined" fullwidth>Rebuild Index</wa-button>
                </div>
              </div>
              
              <div style="padding: 16px; border: 1px solid var(--wa-border-color); border-radius: 4px;">
                <h3 style="margin-top: 0;">Customer Vectors</h3>
                <div style="margin-bottom: 8px;">
                  <strong>Dimensions:</strong> 384
                </div>
                <div style="margin-bottom: 8px;">
                  <strong>Records:</strong> 8,745
                </div>
                <div style="margin-bottom: 8px;">
                  <strong>Last Updated:</strong> 3 hours ago
                </div>
                <div style="margin-top: 16px;">
                  <wa-button variant="outlined" fullwidth>Rebuild Index</wa-button>
                </div>
              </div>
              
              <div style="padding: 16px; border: 1px solid var(--wa-border-color); border-radius: 4px;">
                <h3 style="margin-top: 0;">Document Vectors</h3>
                <div style="margin-bottom: 8px;">
                  <strong>Dimensions:</strong> 768
                </div>
                <div style="margin-bottom: 8px;">
                  <strong>Records:</strong> 42,567
                </div>
                <div style="margin-bottom: 8px;">
                  <strong>Last Updated:</strong> 12 minutes ago
                </div>
                <div style="margin-top: 16px;">
                  <wa-button variant="outlined" fullwidth>Rebuild Index</wa-button>
                </div>
              </div>
            </div>
          </div>
        </wa-card>
      </div>
    `;
  }

  renderRealtime() {
    return html`
      <h1>Realtime Communications</h1>
      
      <wa-card style="margin-bottom: 24px;">
        <div style="padding: 16px;">
          <h2 style="margin-top: 0;">Connection Status</h2>
          
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; margin-top: 16px;">
            <div style="padding: 16px; border: 1px solid var(--wa-border-color); border-radius: 4px;">
              <h3 style="margin-top: 0;">WebSocket</h3>
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: var(--wa-success-color);"></span>
                <span>Connected</span>
              </div>
              <div style="margin-bottom: 8px;">
                <strong>Active Connections:</strong> 254
              </div>
              <div style="margin-bottom: 8px;">
                <strong>Messages/sec:</strong> 42.3
              </div>
            </div>
            
            <div style="padding: 16px; border: 1px solid var(--wa-border-color); border-radius: 4px;">
              <h3 style="margin-top: 0;">Server-Sent Events</h3>
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: var(--wa-success-color);"></span>
                <span>Connected</span>
              </div>
              <div style="margin-bottom: 8px;">
                <strong>Active Connections:</strong> 187
              </div>
              <div style="margin-bottom: 8px;">
                <strong>Events/sec:</strong> 28.5
              </div>
            </div>
            
            <div style="padding: 16px; border: 1px solid var(--wa-border-color); border-radius: 4px;">
              <h3 style="margin-top: 0;">Notification Hub</h3>
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: var(--wa-success-color);"></span>
                <span>Active</span>
              </div>
              <div style="margin-bottom: 8px;">
                <strong>Subscribers:</strong> 842
              </div>
              <div style="margin-bottom: 8px;">
                <strong>Notifications/sec:</strong> 15.8
              </div>
            </div>
          </div>
        </div>
      </wa-card>
      
      <wa-card>
        <div style="padding: 16px;">
          <h2 style="margin-top: 0;">Active Subscriptions</h2>
          
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Channel</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Subscribers</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Messages (24h)</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Peak Traffic</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">orders/new</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">124</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">1,547</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">45/min</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">View</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">notifications/user</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">542</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">8,921</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">356/min</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">View</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">chat/rooms</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">89</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">12,458</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">267/min</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">View</wa-button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </wa-card>
    `;
  }

  renderOffline() {
    return html`
      <h1>Offline Mode Management</h1>
      
      <div style="display: flex; gap: 24px; margin-bottom: 24px;">
        <wa-card style="flex: 1;">
          <div style="padding: 16px;">
            <h2 style="margin-top: 0;">Offline Status</h2>
            
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
              <span style="font-weight: 500;">Global Offline Mode:</span>
              <wa-switch></wa-switch>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin-top: 24px;">
              <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: var(--wa-primary-color);">24</div>
                <div>Clients in Offline Mode</div>
              </div>
              
              <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: var(--wa-primary-color);">1,284</div>
                <div>Pending Sync Operations</div>
              </div>
              
              <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: var(--wa-primary-color);">15</div>
                <div>Sync Conflicts</div>
              </div>
            </div>
          </div>
        </wa-card>
        
        <wa-card style="flex: 1;">
          <div style="padding: 16px;">
            <h2 style="margin-top: 0;">Data Synchronization</h2>
            
            <div style="margin-bottom: 16px;">
              <wa-button color="primary">
                <wa-icon slot="prefix" name="sync"></wa-icon>
                Trigger Global Sync
              </wa-button>
            </div>
            
            <div style="margin-top: 24px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span>Last Global Sync:</span>
                <span>15 minutes ago</span>
              </div>
              
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span>Sync Frequency:</span>
                <span>30 minutes</span>
              </div>
              
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span>Auto-resolve Conflicts:</span>
                <span>Enabled</span>
              </div>
            </div>
          </div>
        </wa-card>
      </div>
      
      <wa-card>
        <div style="padding: 16px;">
          <h2 style="margin-top: 0;">Offline-Enabled Entities</h2>
          
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Entity</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Status</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Cache Strategy</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Records</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Product</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-success-color-light); color: var(--wa-success-color);">
                    Enabled
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Read-only</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">15,482</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Configure</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Order</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-success-color-light); color: var(--wa-success-color);">
                    Enabled
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Read-write</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">8,745</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Configure</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Customer</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-error-color-light); color: var(--wa-error-color);">
                    Disabled
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">N/A</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">42,567</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Configure</wa-button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </wa-card>
    `;
  }

  renderTenants() {
    return html`
      <h1>Multi-Tenant Management</h1>
      
      <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
        <wa-button>
          <wa-icon slot="prefix" name="add"></wa-icon>
          New Tenant
        </wa-button>
      </div>
      
      <wa-card>
        <div style="padding: 16px;">
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Tenant</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Status</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Users</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Database</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Storage</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-avatar size="small" style="background-color: var(--wa-primary-color);">A</wa-avatar>
                    <div>
                      <div>Acme Corporation</div>
                      <div style="font-size: 12px; color: var(--wa-text-secondary-color);">acme.example.com</div>
                    </div>
                  </div>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-success-color-light); color: var(--wa-success-color);">
                    Active
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">124</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Schema</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">2.3 GB</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Manage</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-avatar size="small" style="background-color: var(--wa-secondary-color);">G</wa-avatar>
                    <div>
                      <div>Globex Inc</div>
                      <div style="font-size: 12px; color: var(--wa-text-secondary-color);">globex.example.com</div>
                    </div>
                  </div>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-success-color-light); color: var(--wa-success-color);">
                    Active
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">87</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Schema</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">1.8 GB</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Manage</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-avatar size="small" style="background-color: var(--wa-info-color);">S</wa-avatar>
                    <div>
                      <div>Soylent Corp</div>
                      <div style="font-size: 12px; color: var(--wa-text-secondary-color);">soylent.example.com</div>
                    </div>
                  </div>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-warning-color-light); color: var(--wa-warning-color);">
                    Suspended
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">45</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Schema</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">0.9 GB</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Manage</wa-button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </wa-card>
    `;
  }

  renderUsers() {
    return html`
      <h1>User Management</h1>
      
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <wa-input 
          placeholder="Search users..."
          style="width: 300px;">
          <wa-icon slot="prefix" name="search"></wa-icon>
        </wa-input>
        
        <wa-button>
          <wa-icon slot="prefix" name="add"></wa-icon>
          New User
        </wa-button>
      </div>
      
      <wa-card>
        <div style="padding: 16px;">
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">User</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Email</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Role</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Status</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Last Activity</th>
                <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-avatar size="small" style="background-color: var(--wa-primary-color);">JD</wa-avatar>
                    <div>John Doe</div>
                  </div>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">john.doe@example.com</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-chip>Administrator</wa-chip>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-success-color-light); color: var(--wa-success-color);">
                    Active
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">2 minutes ago</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Edit</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-avatar size="small" style="background-color: var(--wa-secondary-color);">JS</wa-avatar>
                    <div>Jane Smith</div>
                  </div>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">jane.smith@example.com</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-chip>Editor</wa-chip>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-success-color-light); color: var(--wa-success-color);">
                    Active
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">1 hour ago</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Edit</wa-button>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-avatar size="small" style="background-color: var(--wa-info-color);">RJ</wa-avatar>
                    <div>Robert Johnson</div>
                  </div>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">robert.johnson@example.com</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-chip>Viewer</wa-chip>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <span style="display: inline-block; padding: 4px 8px; border-radius: 12px; background-color: var(--wa-warning-color-light); color: var(--wa-warning-color);">
                    Inactive
                  </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">5 days ago</td>
                <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                  <wa-button variant="text">Edit</wa-button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </wa-card>
    `;
  }

  render() {
    return html`
      <div class="dashboard-container">
        <wa-app-bar class="header" elevation="2" position="fixed">
          <wa-button
            slot="navigation"
            variant="icon"
            @click=${this.toggleDrawer}>
            <wa-icon name="menu"></wa-icon>
          </wa-button>
          
          <span slot="title">UNO Admin</span>
          
          <div slot="actions">
            <wa-button variant="icon" @click=${this.toggleTheme}>
              <wa-icon name=${this.theme === 'light' ? 'dark_mode' : 'light_mode'}></wa-icon>
            </wa-button>
            
            <wa-button variant="icon">
              <wa-icon name="notifications"></wa-icon>
              ${this.notifications.length > 0 ? html`
                <wa-badge slot="badge">${this.notifications.length}</wa-badge>
              ` : ''}
            </wa-button>
            
            <wa-button variant="icon">
              <wa-avatar size="small">${this.user.name.charAt(0)}</wa-avatar>
            </wa-button>
          </div>
        </wa-app-bar>
        
        <wa-drawer
          open=${this.drawerOpen}
          variant="persistent"
          style="margin-top: 64px; height: calc(100% - 64px);">
          <div class="sidebar-content">
            ${this.moduleGroups.map(group => html`
              <div class="module-group">
                <div class="module-group-title">${group.title}</div>
                <wa-list>
                  ${group.modules.map(module => html`
                    <wa-list-item
                      ?selected=${this.currentModule === module.id}
                      @click=${() => this.navigateTo(module.id)}>
                      <wa-icon slot="start" name=${module.icon}></wa-icon>
                      ${module.name}
                    </wa-list-item>
                  `)}
                </wa-list>
              </div>
            `)}
            
            <div class="system-status">
              <h3 style="margin-top: 0; margin-bottom: 16px;">System Status</h3>
              ${Object.entries(this.systemStatus).map(([key, status]) => html`
                <div class="status-item">
                  <div class="status-indicator ${status.status === 'healthy' ? 'status-healthy' : 
                                               status.status === 'warning' ? 'status-warning' : 
                                               'status-error'}"></div>
                  <div>
                    <div class="status-text">${key.charAt(0).toUpperCase() + key.slice(1)}</div>
                    <div class="status-detail">${status.message}</div>
                  </div>
                </div>
              `)}
            </div>
          </div>
        </wa-drawer>
        
        <main class="content-area ${this.drawerOpen ? 'with-drawer' : ''}">
          ${this.renderModuleContent()}
        </main>
      </div>
    `;
  }
}

customElements.define('wa-admin-dashboard', WebAwesomeAdminDashboard);