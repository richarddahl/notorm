/**
 * App shell component for UNO Admin interface
 * @element okui-app-shell
 */
import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';

export class OkuiAppShell extends LitElement {
  static get properties() {
    return {
      siteName: { type: String },
      theme: { type: String, reflect: true }
    };
  }

  constructor() {
    super();
    this.siteName = 'UNO Admin';
    this.theme = localStorage.getItem('wa-theme') || 'light';
  }

  connectedCallback() {
    super.connectedCallback();
    // Get attribute value if provided
    if (this.hasAttribute('site-name')) {
      this.siteName = this.getAttribute('site-name');
    }
  }

  static get styles() {
    return css`
      :host {
        display: block;
        font-family: var(--wa-font-family, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif);
        --header-height: 64px;
      }
      .app-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
      }
      .header {
        height: var(--header-height);
        display: flex;
        align-items: center;
        padding: 0 20px;
        background-color: var(--wa-header-bg, #2c3e50);
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
      .logo {
        font-weight: bold;
        font-size: 1.5rem;
        margin-right: 20px;
      }
      .header-actions {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-left: auto;
      }
      .nav-button, .theme-button, .user-menu {
        background: none;
        border: none;
        color: white;
        font-size: 16px;
        cursor: pointer;
        padding: 8px;
        border-radius: 4px;
      }
      .nav-button:hover, .theme-button:hover, .user-menu:hover {
        background-color: rgba(255, 255, 255, 0.1);
      }
      .main-content {
        display: flex;
        flex: 1;
        height: calc(100vh - var(--header-height));
      }
      .sidebar {
        width: 240px;
        background-color: var(--wa-sidebar-bg, #f5f5f5);
        border-right: 1px solid #e0e0e0;
        padding: 20px 0;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
      }
      .sidebar-nav {
        display: flex;
        flex-direction: column;
      }
      .nav-section {
        margin-bottom: 20px;
      }
      .nav-section-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: #757575;
        padding: 0 20px;
        margin: 15px 0 5px;
      }
      .nav-item {
        display: flex;
        align-items: center;
        padding: 10px 20px;
        color: var(--wa-text-color, #424242);
        text-decoration: none;
        cursor: pointer;
      }
      .nav-item:hover {
        background-color: var(--wa-hover-bg, #e0e0e0);
      }
      .nav-item.active {
        background-color: var(--wa-active-bg, #e8eaf6);
        border-left: 3px solid var(--wa-primary-color, #3f51b5);
        color: var(--wa-primary-color, #3f51b5);
        font-weight: 500;
      }
      .content-area {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        background-color: var(--wa-content-bg, white);
      }
      
      /* Theme-specific styles */
      :host([theme="dark"]) .sidebar {
        background-color: #333;
        border-right-color: #444;
      }
      
      :host([theme="dark"]) .nav-item {
        color: #ccc;
      }
      
      :host([theme="dark"]) .nav-item:hover {
        background-color: #444;
      }
      
      :host([theme="dark"]) .nav-item.active {
        background-color: #3f51b5;
        color: white;
      }
      
      :host([theme="dark"]) .nav-section-title {
        color: #999;
      }
      
      :host([theme="dark"]) .content-area {
        background-color: #222;
        color: #eee;
      }
    `;
  }
  
  render() {
    return html`
      <div class="app-container">
        <header class="header">
          <div class="logo">${this.siteName}</div>
          <div class="header-actions">
            <button class="theme-button" @click=${this.toggleTheme}>
              ${this.theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button class="user-menu">👤 Admin</button>
          </div>
        </header>
        
        <div class="main-content">
          <aside class="sidebar">
            <nav class="sidebar-nav">
              <div class="nav-section">
                <div class="nav-section-title">Core</div>
                <a class="nav-item ${window.location.pathname === '/admin' ? 'active' : ''}" href="/admin">Dashboard</a>
                <a class="nav-item ${window.location.pathname === '/admin/attributes' ? 'active' : ''}" href="/admin/attributes">Attributes</a>
                <a class="nav-item ${window.location.pathname === '/admin/values' ? 'active' : ''}" href="/admin/values">Values</a>
                <a class="nav-item ${window.location.pathname === '/admin/authorization' ? 'active' : ''}" href="/admin/authorization">Authorization</a>
              </div>
              
              <div class="nav-section">
                <div class="nav-section-title">Tools</div>
                <a class="nav-item ${window.location.pathname === '/admin/workflows' ? 'active' : ''}" href="/admin/workflows">Workflows</a>
                <a class="nav-item ${window.location.pathname === '/admin/reports' ? 'active' : ''}" href="/admin/reports">Reports</a>
                <a class="nav-item ${window.location.pathname === '/admin/vector-search' ? 'active' : ''}" href="/admin/vector-search">Vector Search</a>
                <a class="nav-item ${window.location.pathname === '/admin/crud' ? 'active' : ''}" href="/admin/crud">CRUD Manager</a>
              </div>
              
              <div class="nav-section">
                <div class="nav-section-title">System</div>
                <a class="nav-item ${window.location.pathname === '/admin/jobs' ? 'active' : ''}" href="/admin/jobs">Jobs</a>
                <a class="nav-item ${window.location.pathname === '/admin/monitoring' ? 'active' : ''}" href="/admin/monitoring">Monitoring</a>
                <a class="nav-item ${window.location.pathname === '/admin/security' ? 'active' : ''}" href="/admin/security">Security</a>
              </div>
            </nav>
          </aside>
          
          <div class="content-area">
            <slot></slot>
          </div>
        </div>
      </div>
    `;
  }
  
  toggleTheme() {
    this.theme = this.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('wa-theme', this.theme);
    
    // Dispatch event for document-level theme change
    const event = new CustomEvent('wa:theme-change', {
      bubbles: true,
      composed: true, // Allows the event to cross the shadow DOM boundary
      detail: { theme: this.theme }
    });
    this.dispatchEvent(event);
  }
}

// Define the new element
customElements.define('okui-app-shell', OkuiAppShell);