/**
 * Simple admin dashboard component
 * @element okui-admin-dashboard
 */
class OkuiAdminDashboard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.siteName = 'UNO Admin';
  }

  connectedCallback() {
    // Get attribute value if provided
    if (this.hasAttribute('site-name')) {
      this.siteName = this.getAttribute('site-name');
    }
    
    this.render();
  }
  
  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--wa-font-family, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif);
          color: var(--wa-text-color, #333);
          background-color: var(--wa-background-color, #f5f5f5);
          padding: 20px;
        }

        .header {
          background-color: var(--wa-primary-color, #3f51b5);
          color: white;
          padding: 20px;
          border-radius: 4px;
          margin-bottom: 20px;
        }

        .header h1 {
          margin: 0 0 10px 0;
        }

        .header p {
          margin: 0;
          opacity: 0.8;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
          margin-bottom: 20px;
        }

        .card {
          background-color: white;
          border-radius: 4px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          padding: 20px;
          height: 100%;
        }

        .card h2 {
          margin-top: 0;
          color: var(--wa-primary-color, #3f51b5);
          font-size: 1.25rem;
        }

        ul {
          padding-left: 20px;
          margin-bottom: 10px;
        }

        li {
          margin-bottom: 8px;
        }

        .system-status {
          display: flex;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 10px;
          margin-bottom: 10px;
        }

        .status-item {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .status-healthy {
          background-color: #4caf50;
        }

        .status-warning {
          background-color: #ff9800;
        }

        .status-error {
          background-color: #f44336;
        }

        .module-list {
          margin-top: 30px;
        }

        .module-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-bottom: 10px;
        }

        .module-item {
          background-color: #f5f5f5;
          padding: 15px;
          border-radius: 4px;
          text-align: center;
          transition: transform 0.2s ease;
          cursor: pointer;
        }

        .module-item:hover {
          transform: translateY(-5px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        h3 {
          margin-top: 0;
        }

        .section-title {
          margin-top: 30px;
          margin-bottom: 15px;
          border-bottom: 1px solid #eee;
          padding-bottom: 10px;
        }
      </style>
      
      <div class="admin-dashboard">
        <div class="header">
          <h1>${this.siteName}</h1>
          <p>Welcome to the UNO administration interface</p>
        </div>

        <div class="dashboard-grid">
          <div class="card">
            <h2>System Status</h2>
            <div class="system-status">
              <div class="status-item">
                <div class="status-indicator status-healthy"></div>
                <span>Database: Connected</span>
              </div>
              <div class="status-item">
                <div class="status-indicator status-healthy"></div>
                <span>Cache: Operational</span>
              </div>
              <div class="status-item">
                <div class="status-indicator status-warning"></div>
                <span>Jobs: 2 failures</span>
              </div>
            </div>
            <p>All systems are operational. View detailed metrics in the Monitoring panel.</p>
          </div>

          <div class="card">
            <h2>Quick Stats</h2>
            <ul>
              <li><strong>Active Users:</strong> 42</li>
              <li><strong>Requests/min:</strong> 257</li>
              <li><strong>Database Size:</strong> 4.2 GB</li>
              <li><strong>Uptime:</strong> 7 days</li>
              <li><strong>Version:</strong> 1.2.0</li>
            </ul>
          </div>

          <div class="card">
            <h2>Recent Activity</h2>
            <ul>
              <li>User login: admin@example.com (2 min ago)</li>
              <li>Report generated: Sales Q2 (15 min ago)</li>
              <li>Workflow completed: Invoice Processing (1 hour ago)</li>
              <li>Attribute updated: Product Category (3 hours ago)</li>
            </ul>
          </div>
        </div>

        <h2 class="section-title">Administration Modules</h2>

        <div class="module-list">
          <h3>Core</h3>
          <div class="module-row">
            <div class="module-item" id="attributes-module">
              <h4>Attributes</h4>
              <p>Manage entity attributes</p>
            </div>
            <div class="module-item" id="values-module">
              <h4>Values</h4>
              <p>Manage entity values</p>
            </div>
            <div class="module-item" id="authorization-module">
              <h4>Authorization</h4>
              <p>User roles and permissions</p>
            </div>
          </div>

          <h3>Tools</h3>
          <div class="module-row">
            <div class="module-item" id="workflows-module">
              <h4>Workflows</h4>
              <p>Workflow management</p>
            </div>
            <div class="module-item" id="reports-module">
              <h4>Reports</h4>
              <p>Report generation and management</p>
            </div>
            <div class="module-item" id="vector-search-module">
              <h4>Vector Search</h4>
              <p>Semantic search interface</p>
            </div>
          </div>

          <h3>System</h3>
          <div class="module-row">
            <div class="module-item" id="jobs-module">
              <h4>Jobs</h4>
              <p>Background job management</p>
            </div>
            <div class="module-item" id="monitoring-module">
              <h4>Monitoring</h4>
              <p>System health and performance</p>
            </div>
            <div class="module-item" id="security-module">
              <h4>Security</h4>
              <p>Security settings and audit logs</p>
            </div>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    this.shadowRoot.getElementById('attributes-module').addEventListener('click', () => {
      window.location.href = '/admin/attributes';
    });
    this.shadowRoot.getElementById('values-module').addEventListener('click', () => {
      window.location.href = '/admin/values';
    });
    this.shadowRoot.getElementById('authorization-module').addEventListener('click', () => {
      window.location.href = '/admin/authorization';
    });
    this.shadowRoot.getElementById('workflows-module').addEventListener('click', () => {
      window.location.href = '/admin/workflows';
    });
    this.shadowRoot.getElementById('reports-module').addEventListener('click', () => {
      window.location.href = '/admin/reports';
    });
    this.shadowRoot.getElementById('vector-search-module').addEventListener('click', () => {
      window.location.href = '/admin/vector-search';
    });
    this.shadowRoot.getElementById('jobs-module').addEventListener('click', () => {
      window.location.href = '/admin/jobs';
    });
    this.shadowRoot.getElementById('monitoring-module').addEventListener('click', () => {
      window.location.href = '/admin/monitoring';
    });
    this.shadowRoot.getElementById('security-module').addEventListener('click', () => {
      window.location.href = '/admin/security';
    });
  }
}

// Define the new element
customElements.define('okui-admin-dashboard', OkuiAdminDashboard);