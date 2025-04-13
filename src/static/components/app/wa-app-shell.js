import { LitElement, html, css } from 'lit';

/**
 * @element wa-app-shell
 * @description Main application shell that integrates all WebAwesome components
 * @fires wa:route-change - Fired when navigation route changes
 * @fires wa:theme-change - Fired when theme changes
 */
export class WebAwesomeAppShell extends LitElement {
  static properties = {
    currentModule: { type: String, reflect: true },
    currentView: { type: String, reflect: true },
    isAuthenticated: { type: Boolean },
    userProfile: { type: Object },
    theme: { type: String, reflect: true },
    notifications: { type: Array },
    sidebarCollapsed: { type: Boolean },
    globalSearchTerm: { type: String },
  };

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      --sidebar-width: 260px;
      --sidebar-collapsed-width: 70px;
      --header-height: 64px;
      --topbar-height: 48px;
      color: var(--sl-color-neutral-900);
      background-color: var(--sl-color-neutral-50);
    }

    :host([theme="dark"]) {
      color: var(--sl-color-neutral-100);
      background-color: var(--sl-color-neutral-900);
    }

    .app-container {
      display: flex;
      flex: 1;
      height: calc(100vh - var(--header-height));
    }

    .sidebar {
      width: var(--sidebar-width);
      transition: width 0.3s ease;
      background-color: var(--sl-color-neutral-0);
      border-right: 1px solid var(--sl-color-neutral-200);
      overflow-y: auto;
      z-index: 10;
      display: flex;
      flex-direction: column;
    }

    :host([theme="dark"]) .sidebar {
      background-color: var(--sl-color-neutral-950);
      border-right-color: var(--sl-color-neutral-800);
    }

    .sidebar.collapsed {
      width: var(--sidebar-collapsed-width);
    }

    .header {
      height: var(--header-height);
      display: flex;
      align-items: center;
      padding: 0 1rem;
      background-color: var(--sl-color-neutral-0);
      border-bottom: 1px solid var(--sl-color-neutral-200);
      z-index: 20;
    }

    :host([theme="dark"]) .header {
      background-color: var(--sl-color-neutral-950);
      border-bottom-color: var(--sl-color-neutral-800);
    }

    .logo-container {
      display: flex;
      align-items: center;
      margin-right: auto;
    }

    .logo {
      height: 32px;
      margin-right: 1rem;
    }

    .app-title {
      font-size: 1.5rem;
      font-weight: 700;
      line-height: 1;
      margin: 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .sidebar-collapsed .app-title {
      display: none;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .main-content {
      flex: 1;
      overflow-y: auto;
      padding: 1rem;
      display: flex;
      flex-direction: column;
    }

    /* Navigation styles */
    .nav-section {
      margin-bottom: 1rem;
    }

    .nav-section-title {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--sl-color-neutral-500);
      padding: 0.75rem 1rem 0.25rem;
      margin: 0;
    }

    :host([theme="dark"]) .nav-section-title {
      color: var(--sl-color-neutral-400);
    }

    .sidebar.collapsed .nav-section-title {
      display: none;
    }

    .nav-item {
      display: flex;
      align-items: center;
      padding: 0.75rem 1rem;
      color: var(--sl-color-neutral-700);
      text-decoration: none;
      border-left: 3px solid transparent;
      cursor: pointer;
    }

    :host([theme="dark"]) .nav-item {
      color: var(--sl-color-neutral-300);
    }

    .nav-item:hover {
      background-color: var(--sl-color-neutral-100);
      color: var(--sl-color-primary-600);
    }

    :host([theme="dark"]) .nav-item:hover {
      background-color: var(--sl-color-neutral-900);
      color: var(--sl-color-primary-400);
    }

    .nav-item.active {
      background-color: var(--sl-color-primary-50);
      color: var(--sl-color-primary-700);
      border-left-color: var(--sl-color-primary-600);
    }

    :host([theme="dark"]) .nav-item.active {
      background-color: var(--sl-color-primary-900);
      color: var(--sl-color-primary-300);
      border-left-color: var(--sl-color-primary-400);
    }

    .nav-item sl-icon {
      margin-right: 0.75rem;
    }

    .sidebar.collapsed .nav-item {
      justify-content: center;
      padding: 0.75rem 0;
    }

    .sidebar.collapsed .nav-item sl-icon {
      margin-right: 0;
      font-size: 1.5rem;
    }

    .nav-item-text {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .sidebar.collapsed .nav-item-text {
      display: none;
    }

    /* Module content container */
    .module-container {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    /* Top bar styles for module-specific actions */
    .top-bar {
      height: var(--topbar-height);
      display: flex;
      align-items: center;
      padding: 0 1rem;
      background-color: var(--sl-color-neutral-100);
      border-bottom: 1px solid var(--sl-color-neutral-200);
    }

    :host([theme="dark"]) .top-bar {
      background-color: var(--sl-color-neutral-900);
      border-bottom-color: var(--sl-color-neutral-800);
    }

    .breadcrumbs {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex: 1;
    }

    .breadcrumb-item {
      display: flex;
      align-items: center;
    }

    .breadcrumb-separator {
      color: var(--sl-color-neutral-400);
      margin: 0 0.25rem;
    }

    .module-title {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
    }

    .top-bar-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
  `;

  constructor() {
    super();
    this.currentModule = 'dashboard';
    this.currentView = 'overview';
    this.isAuthenticated = true; // For demo purposes
    this.userProfile = {
      name: 'Admin User',
      email: 'admin@example.com',
      avatar: 'https://i.pravatar.cc/150?u=admin@example.com',
      role: 'Administrator'
    };
    this.theme = document.documentElement.classList.contains('sl-theme-dark') ? 'dark' : 'light';
    this.notifications = [];
    this.sidebarCollapsed = false;
    this.globalSearchTerm = '';

    // Load last module from localStorage if available
    const savedModule = localStorage.getItem('wa-current-module');
    if (savedModule) {
      this.currentModule = savedModule;
    }

    // Event listeners for route changes
    window.addEventListener('popstate', this._handleRouteChange.bind(this));
  }

  connectedCallback() {
    super.connectedCallback();
    this._parseRouteFromUrl();
  }

  _parseRouteFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const module = urlParams.get('module');
    const view = urlParams.get('view');
    
    if (module) {
      this.currentModule = module;
    }
    
    if (view) {
      this.currentView = view;
    }
  }

  _handleRouteChange(e) {
    this._parseRouteFromUrl();
  }

  _navigateTo(module, view = 'overview') {
    this.currentModule = module;
    this.currentView = view;
    
    // Save current module to localStorage
    localStorage.setItem('wa-current-module', module);
    
    // Update URL without reloading page
    const url = new URL(window.location);
    url.searchParams.set('module', module);
    url.searchParams.set('view', view);
    window.history.pushState({}, '', url);
    
    // Dispatch custom event
    this.dispatchEvent(new CustomEvent('wa:route-change', {
      detail: { module, view },
      bubbles: true,
      composed: true
    }));
  }

  _toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
  }

  _toggleTheme() {
    this.theme = this.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.classList.toggle('sl-theme-dark');
    document.documentElement.classList.toggle('sl-theme-light');
    
    // Dispatch custom event
    this.dispatchEvent(new CustomEvent('wa:theme-change', {
      detail: { theme: this.theme },
      bubbles: true,
      composed: true
    }));
  }

  _renderModuleContent() {
    switch(this.currentModule) {
      case 'dashboard':
        return html`<wa-admin-dashboard .view=${this.currentView}></wa-admin-dashboard>`;
      case 'authorization':
        return html`<wa-role-manager .view=${this.currentView}></wa-role-manager>`;
      case 'monitoring':
        return html`<wa-system-monitor .view=${this.currentView}></wa-system-monitor>`;
      case 'vector-search':
        return html`<wa-semantic-search .view=${this.currentView}></wa-semantic-search>`;
      case 'reports':
        return html`<webawesome-report-builder .view=${this.currentView}></webawesome-report-builder>`;
      default:
        return html`<div class="placeholder-content">
          <sl-card>
            <h2 slot="header">Module Not Found</h2>
            <p>The requested module "${this.currentModule}" is not available.</p>
            <sl-button slot="footer" variant="primary" @click=${() => this._navigateTo('dashboard')}>
              Return to Dashboard
            </sl-button>
          </sl-card>
        </div>`;
    }
  }

  _renderBreadcrumbs() {
    const moduleTitle = this._getModuleTitle(this.currentModule);
    const viewTitle = this._getViewTitle(this.currentModule, this.currentView);
    
    return html`
      <div class="breadcrumbs">
        <div class="breadcrumb-item">
          <a href="#" @click=${(e) => { e.preventDefault(); this._navigateTo('dashboard'); }}>Home</a>
        </div>
        <div class="breadcrumb-separator">/</div>
        <div class="breadcrumb-item">
          <a href="#" @click=${(e) => { 
            e.preventDefault(); 
            this._navigateTo(this.currentModule); 
          }}>${moduleTitle}</a>
        </div>
        ${this.currentView !== 'overview' ? html`
          <div class="breadcrumb-separator">/</div>
          <div class="breadcrumb-item">${viewTitle}</div>
        ` : ''}
      </div>
    `;
  }

  _getModuleTitle(module) {
    const titles = {
      'dashboard': 'Admin Dashboard',
      'authorization': 'Role Management',
      'monitoring': 'System Monitor',
      'vector-search': 'Vector Search',
      'reports': 'Reports'
    };
    return titles[module] || module.charAt(0).toUpperCase() + module.slice(1);
  }

  _getViewTitle(module, view) {
    if (view === 'overview') return 'Overview';
    
    // Define view titles for each module
    const viewTitles = {
      'dashboard': {
        'statistics': 'System Statistics',
        'activity': 'Recent Activity',
        'settings': 'Dashboard Settings'
      },
      'authorization': {
        'roles': 'Roles',
        'permissions': 'Permissions',
        'assignments': 'User Assignments'
      },
      'monitoring': {
        'metrics': 'Performance Metrics',
        'health': 'Health Checks',
        'logs': 'System Logs',
        'alerts': 'Alerts',
        'tracing': 'Request Tracing'
      },
      'vector-search': {
        'search': 'Search Interface',
        'stats': 'Vector Statistics',
        'settings': 'Search Settings'
      },
      'reports': {
        'create': 'Create Report',
        'list': 'All Reports',
        'templates': 'Report Templates',
        'scheduled': 'Scheduled Reports'
      }
    };
    
    return viewTitles[module]?.[view] || view.charAt(0).toUpperCase() + view.slice(1);
  }

  render() {
    return html`
      <div class="header">
        <div class="logo-container">
          <img src="/static/assets/images/logo-${this.theme}.png" alt="Logo" class="logo">
          <h1 class="app-title">UNO Admin</h1>
        </div>
        
        <div class="header-actions">
          <sl-input 
            placeholder="Global search..." 
            size="small"
            clearable
            .value=${this.globalSearchTerm}
            @sl-input=${(e) => this.globalSearchTerm = e.target.value}
          >
            <sl-icon slot="prefix" name="search"></sl-icon>
          </sl-input>
          
          <sl-button-group>
            <sl-button size="small" pill @click=${this._toggleSidebar}>
              <sl-icon name=${this.sidebarCollapsed ? 'arrow-bar-right' : 'arrow-bar-left'}></sl-icon>
            </sl-button>
            <sl-button size="small" pill @click=${this._toggleTheme}>
              <sl-icon name=${this.theme === 'dark' ? 'sun' : 'moon'}></sl-icon>
            </sl-button>
          </sl-button-group>
          
          <sl-dropdown>
            <sl-button slot="trigger" size="small" pill>
              <sl-icon name="bell"></sl-icon>
              ${this.notifications.length > 0 ? html`
                <sl-badge variant="danger" pill>${this.notifications.length}</sl-badge>
              ` : ''}
            </sl-button>
            <sl-menu>
              ${this.notifications.length > 0 ? 
                this.notifications.map(notification => html`
                  <sl-menu-item>
                    <sl-icon slot="prefix" name=${notification.type === 'error' ? 'exclamation-triangle' : 
                                                notification.type === 'warning' ? 'exclamation-circle' : 
                                                'info-circle'}></sl-icon>
                    <span>${notification.message}</span>
                    <sl-badge slot="suffix" variant=${notification.type === 'error' ? 'danger' : 
                                                    notification.type === 'warning' ? 'warning' : 
                                                    'info'} pill>${notification.time}</sl-badge>
                  </sl-menu-item>
                `) :
                html`<sl-menu-item>No new notifications</sl-menu-item>`
              }
              ${this.notifications.length > 0 ? html`
                <sl-divider></sl-divider>
                <sl-menu-item>View all notifications</sl-menu-item>
              ` : ''}
            </sl-menu>
          </sl-dropdown>
          
          <sl-dropdown>
            <sl-avatar slot="trigger" 
                      image=${this.userProfile.avatar} 
                      label="User menu" 
                      style="cursor: pointer">
            </sl-avatar>
            <sl-menu>
              <sl-menu-item>
                <sl-icon slot="prefix" name="person"></sl-icon>
                Profile
              </sl-menu-item>
              <sl-menu-item>
                <sl-icon slot="prefix" name="gear"></sl-icon>
                Settings
              </sl-menu-item>
              <sl-divider></sl-divider>
              <sl-menu-item>
                <sl-icon slot="prefix" name="box-arrow-right"></sl-icon>
                Sign out
              </sl-menu-item>
            </sl-menu>
          </sl-dropdown>
        </div>
      </div>
      
      <div class="app-container">
        <nav class="sidebar ${this.sidebarCollapsed ? 'collapsed' : ''}">
          <!-- Core navigation -->
          <div class="nav-section">
            <h3 class="nav-section-title">Core</h3>
            <a class="nav-item ${this.currentModule === 'dashboard' ? 'active' : ''}"
               @click=${() => this._navigateTo('dashboard')}>
              <sl-icon name="speedometer"></sl-icon>
              <span class="nav-item-text">Dashboard</span>
            </a>
            <a class="nav-item ${this.currentModule === 'authorization' ? 'active' : ''}"
               @click=${() => this._navigateTo('authorization')}>
              <sl-icon name="shield-lock"></sl-icon>
              <span class="nav-item-text">Authorization</span>
            </a>
          </div>
          
          <!-- Tools navigation -->
          <div class="nav-section">
            <h3 class="nav-section-title">Tools</h3>
            <a class="nav-item ${this.currentModule === 'monitoring' ? 'active' : ''}"
               @click=${() => this._navigateTo('monitoring')}>
              <sl-icon name="graph-up"></sl-icon>
              <span class="nav-item-text">Monitoring</span>
            </a>
            <a class="nav-item ${this.currentModule === 'vector-search' ? 'active' : ''}"
               @click=${() => this._navigateTo('vector-search')}>
              <sl-icon name="search"></sl-icon>
              <span class="nav-item-text">Vector Search</span>
            </a>
            <a class="nav-item ${this.currentModule === 'reports' ? 'active' : ''}"
               @click=${() => this._navigateTo('reports')}>
              <sl-icon name="file-earmark-bar-graph"></sl-icon>
              <span class="nav-item-text">Reports</span>
            </a>
          </div>
        </nav>
        
        <div class="module-container">
          <!-- Top action bar -->
          <div class="top-bar">
            ${this._renderBreadcrumbs()}
            
            <div class="top-bar-actions">
              <!-- Module-specific actions -->
              ${this.currentModule === 'reports' ? html`
                <sl-button size="small" variant="primary">
                  <sl-icon slot="prefix" name="plus"></sl-icon>
                  New Report
                </sl-button>
              ` : ''}
              ${this.currentModule === 'authorization' ? html`
                <sl-button size="small" variant="primary">
                  <sl-icon slot="prefix" name="plus"></sl-icon>
                  New Role
                </sl-button>
              ` : ''}
              ${this.currentModule === 'vector-search' ? html`
                <sl-button size="small" variant="primary">
                  <sl-icon slot="prefix" name="plus"></sl-icon>
                  Create Index
                </sl-button>
              ` : ''}
            </div>
          </div>
          
          <!-- Main content area -->
          <div class="main-content">
            ${this._renderModuleContent()}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('wa-app-shell', WebAwesomeAppShell);