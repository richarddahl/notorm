/**
 * Profiler Dashboard component
 * 
 * A web component for displaying performance profiling metrics for Uno applications.
 */

// Import the LitElement base class and HTML helper function
const LitElement = window.litElement?.LitElement || Object.getPrototypeOf(document.createElement('span')).constructor;
const html = window.litElement?.html || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));
const css = window.litElement?.css || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));

/**
 * Profiler Dashboard
 * 
 * @element profiler-dashboard
 * @attr {String} api-base-url - Base URL for API endpoints
 */
class ProfilerDashboard extends LitElement {
  static get properties() {
    return {
      apiBaseUrl: { type: String, attribute: 'api-base-url' },
      summary: { type: Object },
      queries: { type: Object },
      endpoints: { type: Object },
      resources: { type: Object },
      functions: { type: Object },
      activeTab: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      refreshInterval: { type: Number },
      autoRefresh: { type: Boolean },
      resourceTimeWindow: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
      }
      
      .dashboard {
        display: flex;
        flex-direction: column;
        height: 100%;
        padding: 0;
        overflow: hidden;
      }
      
      .dashboard-header {
        background-color: var(--primary-color, #0078d7);
        color: white;
        padding: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
      
      .dashboard-title {
        font-size: 24px;
        font-weight: 600;
        margin: 0;
      }
      
      .dashboard-controls {
        display: flex;
        align-items: center;
        gap: 16px;
      }
      
      .dashboard-content {
        flex: 1;
        overflow: auto;
        padding: 16px;
      }
      
      .metrics-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      
      .metric-card {
        background-color: white;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 16px;
      }
      
      .metric-title {
        font-size: 14px;
        color: #666;
        margin-bottom: 8px;
      }
      
      .metric-value {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 4px;
      }
      
      .metric-subtitle {
        font-size: 12px;
        color: #666;
      }
      
      .tabs {
        display: flex;
        margin-bottom: 16px;
        border-bottom: 1px solid #ddd;
      }
      
      .tab {
        padding: 8px 16px;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        transition: border-color 0.2s;
      }
      
      .tab.active {
        border-bottom-color: var(--primary-color, #0078d7);
        color: var(--primary-color, #0078d7);
        font-weight: 500;
      }
      
      .tab-content {
        display: none;
      }
      
      .tab-content.active {
        display: block;
      }
      
      .card {
        background-color: white;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 16px;
        margin-bottom: 16px;
      }
      
      .card-title {
        font-size: 18px;
        font-weight: 600;
        margin-top: 0;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #ddd;
      }
      
      table {
        width: 100%;
        border-collapse: collapse;
      }
      
      th, td {
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
      }
      
      th {
        font-weight: 600;
        background-color: #f5f5f5;
      }
      
      tr:hover {
        background-color: #f9f9f9;
      }
      
      .chart-container {
        position: relative;
        height: 300px;
        margin-bottom: 16px;
      }
      
      .loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999;
      }
      
      .loading-spinner {
        display: inline-block;
        width: 40px;
        height: 40px;
        border: 4px solid rgba(0, 120, 212, 0.2);
        border-radius: 50%;
        border-top-color: var(--primary-color, #0078d7);
        animation: spin 1s ease-in-out infinite;
      }
      
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      
      .error-message {
        background-color: #ffebee;
        color: #c62828;
        padding: 16px;
        border-radius: 4px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
      }
      
      .error-message::before {
        content: '⚠️';
        font-size: 20px;
        margin-right: 8px;
      }
      
      .status-success { color: #107c10; }
      .status-warning { color: #ff8c00; }
      .status-error { color: #e81123; }
      
      .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 6px;
      }
      
      .status-indicator-success { background-color: #107c10; }
      .status-indicator-warning { background-color: #ff8c00; }
      .status-indicator-error { background-color: #e81123; }
      
      .progress-bar {
        width: 100%;
        height: 6px;
        background-color: #e0e0e0;
        border-radius: 3px;
        overflow: hidden;
        margin-top: 4px;
      }
      
      .progress-bar-fill {
        height: 100%;
        background-color: var(--primary-color, #0078d7);
      }
      
      .monospace {
        font-family: monospace;
        white-space: pre-wrap;
        word-break: break-all;
        background-color: #f5f5f5;
        padding: 8px;
        border-radius: 4px;
      }
      
      button {
        cursor: pointer;
        padding: 8px 16px;
        background-color: var(--primary-color, #0078d7);
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 500;
        transition: background-color 0.2s;
      }
      
      button:hover {
        background-color: var(--primary-dark, #005a9e);
      }
      
      button.secondary {
        background-color: #f0f0f0;
        color: #333;
        border: 1px solid #ddd;
      }
      
      button.secondary:hover {
        background-color: #e0e0e0;
      }
      
      button.danger {
        background-color: #e81123;
      }
      
      button.danger:hover {
        background-color: #c00e1e;
      }
      
      button[disabled] {
        opacity: 0.5;
        cursor: not-allowed;
      }
      
      .flex {
        display: flex;
      }
      
      .flex-col {
        flex-direction: column;
      }
      
      .justify-between {
        justify-content: space-between;
      }
      
      .items-center {
        align-items: center;
      }
      
      .gap-2 {
        gap: 8px;
      }
      
      .gap-4 {
        gap: 16px;
      }
      
      select {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
      }
    `;
  }

  constructor() {
    super();
    this.apiBaseUrl = '/api';
    this.summary = null;
    this.queries = null;
    this.endpoints = null;
    this.resources = null;
    this.functions = null;
    this.activeTab = 'overview';
    this.loading = false;
    this.error = null;
    this.refreshInterval = 10000; // 10 seconds
    this.autoRefresh = true;
    this.resourceTimeWindow = '1h';
    this._refreshIntervalId = null;
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadData();
    this._startAutoRefresh();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopAutoRefresh();
  }

  _startAutoRefresh() {
    if (this.autoRefresh && !this._refreshIntervalId) {
      this._refreshIntervalId = setInterval(() => {
        this.loadData();
      }, this.refreshInterval);
    }
  }

  _stopAutoRefresh() {
    if (this._refreshIntervalId) {
      clearInterval(this._refreshIntervalId);
      this._refreshIntervalId = null;
    }
  }

  async loadData() {
    this.loading = true;
    this.error = null;

    try {
      // Load summary data
      const summaryResponse = await fetch(`${this.apiBaseUrl}/metrics/summary`);
      if (!summaryResponse.ok) {
        throw new Error(`Failed to load summary data: ${summaryResponse.statusText}`);
      }
      this.summary = await summaryResponse.json();

      // Load tab-specific data based on active tab
      if (this.activeTab === 'queries') {
        await this._loadQueriesData();
      } else if (this.activeTab === 'endpoints') {
        await this._loadEndpointsData();
      } else if (this.activeTab === 'resources') {
        await this._loadResourcesData();
      } else if (this.activeTab === 'functions') {
        await this._loadFunctionsData();
      }
    } catch (error) {
      console.error('Error loading data:', error);
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  async _loadQueriesData() {
    const response = await fetch(`${this.apiBaseUrl}/metrics/queries?include_patterns=true&include_slow=true&include_n_plus_1=true&limit=20`);
    if (!response.ok) {
      throw new Error(`Failed to load query data: ${response.statusText}`);
    }
    this.queries = await response.json();
  }

  async _loadEndpointsData() {
    const response = await fetch(`${this.apiBaseUrl}/metrics/endpoints?include_stats=true&include_slow=true&include_error_prone=true&limit=20`);
    if (!response.ok) {
      throw new Error(`Failed to load endpoint data: ${response.statusText}`);
    }
    this.endpoints = await response.json();
  }

  async _loadResourcesData() {
    const response = await fetch(`${this.apiBaseUrl}/metrics/resources?window=${this.resourceTimeWindow}`);
    if (!response.ok) {
      throw new Error(`Failed to load resource data: ${response.statusText}`);
    }
    this.resources = await response.json();
    
    // Draw charts if we have data
    if (this.resources && this.isTabActive('resources')) {
      this._drawResourceCharts();
    }
  }

  async _loadFunctionsData() {
    const response = await fetch(`${this.apiBaseUrl}/metrics/functions?include_stats=true&include_slow=true&include_hotspots=true&limit=20`);
    if (!response.ok) {
      throw new Error(`Failed to load function data: ${response.statusText}`);
    }
    this.functions = await response.json();
  }

  async resetMetrics() {
    if (!confirm('Are you sure you want to reset all metrics?')) {
      return;
    }

    this.loading = true;
    try {
      const response = await fetch(`${this.apiBaseUrl}/metrics/reset`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to reset metrics: ${response.statusText}`);
      }
      
      // Reload data
      await this.loadData();
    } catch (error) {
      console.error('Error resetting metrics:', error);
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  changeTab(tab) {
    this.activeTab = tab;
    
    // Load data for the new tab
    if (tab === 'queries' && !this.queries) {
      this._loadQueriesData();
    } else if (tab === 'endpoints' && !this.endpoints) {
      this._loadEndpointsData();
    } else if (tab === 'resources' && !this.resources) {
      this._loadResourcesData();
    } else if (tab === 'functions' && !this.functions) {
      this._loadFunctionsData();
    }
    
    // Draw charts if needed
    if (tab === 'resources' && this.resources) {
      // We need to wait for the DOM to update before drawing charts
      setTimeout(() => this._drawResourceCharts(), 0);
    }
  }

  isTabActive(tab) {
    return this.activeTab === tab;
  }

  toggleAutoRefresh() {
    this.autoRefresh = !this.autoRefresh;
    if (this.autoRefresh) {
      this._startAutoRefresh();
      this.loadData(); // Load data immediately when enabling
    } else {
      this._stopAutoRefresh();
    }
  }

  changeResourceTimeWindow(event) {
    this.resourceTimeWindow = event.target.value;
    this._loadResourcesData();
  }

  _drawResourceCharts() {
    if (!this.resources || !this.resources.memory || !this.resources.cpu) {
      return;
    }
    
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.warn('Chart.js is not available. Loading it dynamically...');
      
      // Load Chart.js dynamically
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
      script.onload = () => this._drawResourceCharts();
      document.head.appendChild(script);
      return;
    }
    
    // Memory chart
    this._drawMemoryChart();
    
    // CPU chart
    this._drawCpuChart();
  }

  _drawMemoryChart() {
    const memoryCanvas = this.shadowRoot.getElementById('memoryChart');
    if (!memoryCanvas) {
      console.warn('Memory chart canvas not found');
      return;
    }
    
    // Get data
    const memorySeries = this.resources.memory.series || [];
    
    // Prepare data
    const labels = memorySeries.map(d => new Date(d.timestamp));
    const systemData = memorySeries.map(d => d.percent);
    const processData = memorySeries.map(d => d.process_percent);
    
    // Create chart
    if (memoryCanvas._chart) {
      memoryCanvas._chart.destroy();
    }
    
    memoryCanvas._chart = new Chart(memoryCanvas, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'System Memory',
            data: systemData,
            borderColor: '#0078d7',
            backgroundColor: 'rgba(0, 120, 215, 0.1)',
            fill: true,
            tension: 0.1,
          },
          {
            label: 'Process Memory',
            data: processData,
            borderColor: '#107c10',
            backgroundColor: 'rgba(16, 124, 16, 0.1)',
            fill: true,
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'minute',
              tooltipFormat: 'HH:mm:ss',
            },
            title: {
              display: true,
              text: 'Time',
            },
          },
          y: {
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'Memory Usage (%)',
            },
          },
        },
        plugins: {
          title: {
            display: true,
            text: 'Memory Usage',
          },
          tooltip: {
            mode: 'index',
            intersect: false,
          },
        },
      },
    });
  }

  _drawCpuChart() {
    const cpuCanvas = this.shadowRoot.getElementById('cpuChart');
    if (!cpuCanvas) {
      console.warn('CPU chart canvas not found');
      return;
    }
    
    // Get data
    const cpuSeries = this.resources.cpu.series || [];
    
    // Prepare data
    const labels = cpuSeries.map(d => new Date(d.timestamp));
    const systemData = cpuSeries.map(d => d.percent);
    const processData = cpuSeries.map(d => d.process_percent);
    
    // Create chart
    if (cpuCanvas._chart) {
      cpuCanvas._chart.destroy();
    }
    
    cpuCanvas._chart = new Chart(cpuCanvas, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'System CPU',
            data: systemData,
            borderColor: '#e81123',
            backgroundColor: 'rgba(232, 17, 35, 0.1)',
            fill: true,
            tension: 0.1,
          },
          {
            label: 'Process CPU',
            data: processData,
            borderColor: '#ff8c00',
            backgroundColor: 'rgba(255, 140, 0, 0.1)',
            fill: true,
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'minute',
              tooltipFormat: 'HH:mm:ss',
            },
            title: {
              display: true,
              text: 'Time',
            },
          },
          y: {
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'CPU Usage (%)',
            },
          },
        },
        plugins: {
          title: {
            display: true,
            text: 'CPU Usage',
          },
          tooltip: {
            mode: 'index',
            intersect: false,
          },
        },
      },
    });
  }

  formatDuration(seconds) {
    if (seconds < 0.001) {
      return `${(seconds * 1000000).toFixed(0)}μs`;
    } else if (seconds < 1) {
      return `${(seconds * 1000).toFixed(1)}ms`;
    } else {
      return `${seconds.toFixed(2)}s`;
    }
  }

  formatDateTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString();
  }

  formatNumber(num) {
    return new Intl.NumberFormat().format(num);
  }

  getDurationClass(duration) {
    if (duration < 0.1) {
      return 'status-success';
    } else if (duration < 1.0) {
      return 'status-warning';
    } else {
      return 'status-error';
    }
  }

  render() {
    return html`
      <div class="dashboard">
        ${this.loading ? html`
          <div class="loading-overlay">
            <div class="loading-spinner"></div>
          </div>
        ` : ''}
        
        <header class="dashboard-header">
          <h1 class="dashboard-title">Uno Profiler Dashboard</h1>
          <div class="dashboard-controls">
            <label>
              <input type="checkbox" ?checked=${this.autoRefresh} @change=${this.toggleAutoRefresh}>
              Auto-refresh
            </label>
            <button @click=${this.loadData}>Refresh</button>
            <button class="danger" @click=${this.resetMetrics}>Reset Metrics</button>
          </div>
        </header>
        
        <main class="dashboard-content">
          ${this.error ? html`
            <div class="error-message">${this.error}</div>
          ` : ''}
          
          ${this.summary ? this.renderSummary() : ''}
          
          <div class="tabs">
            <div class="tab ${this.isTabActive('overview') ? 'active' : ''}" @click=${() => this.changeTab('overview')}>Overview</div>
            <div class="tab ${this.isTabActive('queries') ? 'active' : ''}" @click=${() => this.changeTab('queries')}>SQL Queries</div>
            <div class="tab ${this.isTabActive('endpoints') ? 'active' : ''}" @click=${() => this.changeTab('endpoints')}>Endpoints</div>
            <div class="tab ${this.isTabActive('resources') ? 'active' : ''}" @click=${() => this.changeTab('resources')}>Resources</div>
            <div class="tab ${this.isTabActive('functions') ? 'active' : ''}" @click=${() => this.changeTab('functions')}>Functions</div>
          </div>
          
          <div class="tab-content ${this.isTabActive('overview') ? 'active' : ''}">
            ${this.renderOverviewTab()}
          </div>
          
          <div class="tab-content ${this.isTabActive('queries') ? 'active' : ''}">
            <query-analyzer api-base-url="${this.apiBaseUrl}"></query-analyzer>
          </div>
          
          <div class="tab-content ${this.isTabActive('endpoints') ? 'active' : ''}">
            <endpoint-analyzer api-base-url="${this.apiBaseUrl}"></endpoint-analyzer>
          </div>
          
          <div class="tab-content ${this.isTabActive('resources') ? 'active' : ''}">
            <resource-monitor api-base-url="${this.apiBaseUrl}"></resource-monitor>
          </div>
          
          <div class="tab-content ${this.isTabActive('functions') ? 'active' : ''}">
            <function-analyzer api-base-url="${this.apiBaseUrl}"></function-analyzer>
          </div>
        </main>
      </div>
    `;
  }

  renderSummary() {
    return html`
      <div class="metrics-summary">
        <div class="metric-card">
          <div class="metric-title">Queries</div>
          <div class="metric-value">${this.formatNumber(this.summary.queries.total)}</div>
          <div class="metric-subtitle">${this.summary.queries.slow_count} slow queries</div>
        </div>
        
        <div class="metric-card">
          <div class="metric-title">Endpoints</div>
          <div class="metric-value">${this.formatNumber(this.summary.endpoints.total_requests)}</div>
          <div class="metric-subtitle">${this.summary.endpoints.total} unique endpoints</div>
        </div>
        
        <div class="metric-card">
          <div class="metric-title">Memory Usage</div>
          <div class="metric-value">${this.summary.resources.memory.latest_percent.toFixed(1)}%</div>
          <div class="metric-subtitle">Process: ${this.summary.resources.memory.latest_process_percent?.toFixed(1) || 0}%</div>
        </div>
        
        <div class="metric-card">
          <div class="metric-title">CPU Usage</div>
          <div class="metric-value">${this.summary.resources.cpu.latest_percent.toFixed(1)}%</div>
          <div class="metric-subtitle">Process: ${this.summary.resources.cpu.latest_process_percent?.toFixed(1) || 0}%</div>
        </div>
        
        <div class="metric-card">
          <div class="metric-title">Functions</div>
          <div class="metric-value">${this.formatNumber(this.summary.functions.total_calls)}</div>
          <div class="metric-subtitle">${this.summary.functions.total} unique functions</div>
        </div>
      </div>
    `;
  }

  renderOverviewTab() {
    return html`
      <div class="card">
        <h2 class="card-title">Performance Overview</h2>
        <p>This dashboard provides insights into the performance of your Uno application. Use the tabs above to explore specific aspects of your application's performance.</p>
        
        <div class="flex justify-between gap-4">
          <div style="flex: 1;">
            <h3>Top Issues</h3>
            <ul>
              ${this.summary.queries.slow_count > 0 ? html`
                <li>
                  <span class="status-indicator status-indicator-${this.summary.queries.slow_count > 5 ? 'error' : 'warning'}"></span>
                  <a href="#" @click=${() => this.changeTab('queries')}>${this.summary.queries.slow_count} slow queries detected</a>
                </li>
              ` : ''}
              
              ${this.summary.endpoints.slow_count > 0 ? html`
                <li>
                  <span class="status-indicator status-indicator-${this.summary.endpoints.slow_count > 5 ? 'error' : 'warning'}"></span>
                  <a href="#" @click=${() => this.changeTab('endpoints')}>${this.summary.endpoints.slow_count} slow endpoints detected</a>
                </li>
              ` : ''}
              
              ${this.summary.endpoints.error_prone_count > 0 ? html`
                <li>
                  <span class="status-indicator status-indicator-error"></span>
                  <a href="#" @click=${() => this.changeTab('endpoints')}>${this.summary.endpoints.error_prone_count} error-prone endpoints detected</a>
                </li>
              ` : ''}
              
              ${this.summary.functions.slow_count > 0 ? html`
                <li>
                  <span class="status-indicator status-indicator-${this.summary.functions.slow_count > 5 ? 'error' : 'warning'}"></span>
                  <a href="#" @click=${() => this.changeTab('functions')}>${this.summary.functions.slow_count} slow functions detected</a>
                </li>
              ` : ''}
              
              ${this.summary.functions.hotspot_count > 0 ? html`
                <li>
                  <span class="status-indicator status-indicator-warning"></span>
                  <a href="#" @click=${() => this.changeTab('functions')}>${this.summary.functions.hotspot_count} function hotspots detected</a>
                </li>
              ` : ''}
              
              ${this.summary.resources.memory.latest_percent > 80 ? html`
                <li>
                  <span class="status-indicator status-indicator-error"></span>
                  <a href="#" @click=${() => this.changeTab('resources')}>High memory usage (${this.summary.resources.memory.latest_percent.toFixed(1)}%)</a>
                </li>
              ` : this.summary.resources.memory.latest_percent > 60 ? html`
                <li>
                  <span class="status-indicator status-indicator-warning"></span>
                  <a href="#" @click=${() => this.changeTab('resources')}>Elevated memory usage (${this.summary.resources.memory.latest_percent.toFixed(1)}%)</a>
                </li>
              ` : ''}
              
              ${this.summary.resources.cpu.latest_percent > 80 ? html`
                <li>
                  <span class="status-indicator status-indicator-error"></span>
                  <a href="#" @click=${() => this.changeTab('resources')}>High CPU usage (${this.summary.resources.cpu.latest_percent.toFixed(1)}%)</a>
                </li>
              ` : this.summary.resources.cpu.latest_percent > 60 ? html`
                <li>
                  <span class="status-indicator status-indicator-warning"></span>
                  <a href="#" @click=${() => this.changeTab('resources')}>Elevated CPU usage (${this.summary.resources.cpu.latest_percent.toFixed(1)}%)</a>
                </li>
              ` : ''}
              
              ${this.summary.queries.slow_count === 0 && this.summary.endpoints.slow_count === 0 && this.summary.functions.slow_count === 0 ? html`
                <li>
                  <span class="status-indicator status-indicator-success"></span>
                  No major performance issues detected
                </li>
              ` : ''}
            </ul>
          </div>
          
          <div style="flex: 1;">
            <h3>Quick Actions</h3>
            <div class="flex flex-col gap-2">
              <button @click=${() => this.changeTab('queries')}>Analyze SQL Queries</button>
              <button @click=${() => this.changeTab('endpoints')}>Analyze Endpoints</button>
              <button @click=${() => this.changeTab('functions')}>Find Hotspots</button>
              <button @click=${() => this.changeTab('resources')}>Monitor Resources</button>
              <button class="danger" @click=${this.resetMetrics}>Reset All Metrics</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderQueriesTab() {
    if (!this.queries) {
      return html`
        <div class="card">
          <h2 class="card-title">SQL Queries</h2>
          <p>Loading query data...</p>
        </div>
      `;
    }

    return html`
      <div class="card">
        <h2 class="card-title">SQL Queries</h2>
        
        <div class="flex justify-between items-center gap-4 mb-4">
          <div>
            <strong>Total Queries:</strong> ${this.formatNumber(this.queries.total_queries)} | 
            <strong>Unique Patterns:</strong> ${this.formatNumber(this.queries.unique_patterns)}
          </div>
        </div>
        
        ${this.queries.slow_queries && this.queries.slow_queries.length > 0 ? html`
          <h3>Slow Queries</h3>
          <table>
            <thead>
              <tr>
                <th>Query</th>
                <th>Duration</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              ${this.queries.slow_queries.map(query => html`
                <tr>
                  <td>
                    <div class="monospace" style="max-height: 100px; overflow-y: auto;">
                      ${query.query}
                    </div>
                  </td>
                  <td class="${this.getDurationClass(query.duration)}">${this.formatDuration(query.duration)}</td>
                  <td>${this.formatDateTime(query.timestamp)}</td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
          <p><span class="status-indicator status-indicator-success"></span> No slow queries detected</p>
        `}
        
        ${this.queries.n_plus_1_candidates && Object.keys(this.queries.n_plus_1_candidates).length > 0 ? html`
          <h3 class="mt-4">Potential N+1 Query Issues</h3>
          <div class="monospace" style="max-height: 300px; overflow-y: auto;">
            <strong>Found ${Object.keys(this.queries.n_plus_1_candidates).length} potential N+1 query patterns:</strong>
            <ul>
              ${Object.values(this.queries.n_plus_1_candidates).map(candidate => html`
                <li>
                  Pattern executed ${candidate.count} times: <code>${candidate.pattern.length > 100 ? candidate.pattern.slice(0, 100) + '...' : candidate.pattern}</code>
                  <br>
                  Similar patterns:
                  <ul>
                    ${candidate.similar_patterns.map(similar => html`
                      <li>Pattern executed ${similar.count} times</li>
                    `)}
                  </ul>
                </li>
              `)}
            </ul>
          </div>
        ` : html`
          <p class="mt-4"><span class="status-indicator status-indicator-success"></span> No potential N+1 query issues detected</p>
        `}
      </div>
    `;
  }

  renderEndpointsTab() {
    if (!this.endpoints) {
      return html`
        <div class="card">
          <h2 class="card-title">Endpoints</h2>
          <p>Loading endpoint data...</p>
        </div>
      `;
    }

    return html`
      <div class="card">
        <h2 class="card-title">Endpoints</h2>
        
        <div class="flex justify-between items-center gap-4 mb-4">
          <div>
            <strong>Total Requests:</strong> ${this.formatNumber(this.endpoints.total_requests)} | 
            <strong>Unique Endpoints:</strong> ${this.formatNumber(this.endpoints.total_endpoints)}
          </div>
        </div>
        
        ${this.endpoints.slow_endpoints && this.endpoints.slow_endpoints.length > 0 ? html`
          <h3>Slow Endpoints</h3>
          <table>
            <thead>
              <tr>
                <th>Method</th>
                <th>Path</th>
                <th>Average Duration</th>
                <th>Max Duration</th>
                <th>Request Count</th>
              </tr>
            </thead>
            <tbody>
              ${this.endpoints.slow_endpoints.map(endpoint => html`
                <tr>
                  <td>${endpoint.method}</td>
                  <td>${endpoint.path}</td>
                  <td class="${this.getDurationClass(endpoint.avg)}">${this.formatDuration(endpoint.avg)}</td>
                  <td class="${this.getDurationClass(endpoint.max)}">${this.formatDuration(endpoint.max)}</td>
                  <td>${endpoint.count}</td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
          <p><span class="status-indicator status-indicator-success"></span> No slow endpoints detected</p>
        `}
        
        ${this.endpoints.error_prone_endpoints && this.endpoints.error_prone_endpoints.length > 0 ? html`
          <h3 class="mt-4">Error-Prone Endpoints</h3>
          <table>
            <thead>
              <tr>
                <th>Method</th>
                <th>Path</th>
                <th>Error Rate</th>
                <th>Error Count</th>
                <th>Total Requests</th>
              </tr>
            </thead>
            <tbody>
              ${this.endpoints.error_prone_endpoints.map(endpoint => html`
                <tr>
                  <td>${endpoint.method}</td>
                  <td>${endpoint.path}</td>
                  <td class="status-error">${(endpoint.error_rate * 100).toFixed(1)}%</td>
                  <td>${endpoint.error_count}</td>
                  <td>${endpoint.total_requests}</td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
          <p class="mt-4"><span class="status-indicator status-indicator-success"></span> No error-prone endpoints detected</p>
        `}
      </div>
    `;
  }

  renderResourcesTab() {
    return html`
      <div class="card">
        <h2 class="card-title">Resource Utilization</h2>
        
        <div class="flex justify-between items-center gap-4 mb-4">
          <div>
            <strong>Time Window:</strong>
            <select @change=${this.changeResourceTimeWindow} .value=${this.resourceTimeWindow}>
              <option value="5m">Last 5 minutes</option>
              <option value="15m">Last 15 minutes</option>
              <option value="30m">Last 30 minutes</option>
              <option value="1h">Last hour</option>
              <option value="3h">Last 3 hours</option>
              <option value="6h">Last 6 hours</option>
              <option value="12h">Last 12 hours</option>
              <option value="1d">Last 24 hours</option>
            </select>
          </div>
        </div>
        
        <div class="chart-container">
          <canvas id="memoryChart"></canvas>
        </div>
        
        <div class="chart-container">
          <canvas id="cpuChart"></canvas>
        </div>
        
        ${this.resources ? html`
          <div class="metrics-summary">
            <div class="metric-card">
              <div class="metric-title">Current Memory Usage</div>
              <div class="metric-value">${this.resources.memory.latest?.percent.toFixed(1)}%</div>
              <div class="metric-subtitle">System Memory</div>
              <div class="progress-bar">
                <div class="progress-bar-fill" style="width: ${this.resources.memory.latest?.percent}%"></div>
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-title">Current Process Memory</div>
              <div class="metric-value">${this.resources.memory.latest?.process_percent?.toFixed(1) || 0}%</div>
              <div class="metric-subtitle">Application Memory</div>
              <div class="progress-bar">
                <div class="progress-bar-fill" style="width: ${this.resources.memory.latest?.process_percent || 0}%"></div>
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-title">Current CPU Usage</div>
              <div class="metric-value">${this.resources.cpu.latest?.percent.toFixed(1)}%</div>
              <div class="metric-subtitle">System CPU</div>
              <div class="progress-bar">
                <div class="progress-bar-fill" style="width: ${this.resources.cpu.latest?.percent}%"></div>
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-title">Current Process CPU</div>
              <div class="metric-value">${this.resources.cpu.latest?.process_percent?.toFixed(1) || 0}%</div>
              <div class="metric-subtitle">Application CPU</div>
              <div class="progress-bar">
                <div class="progress-bar-fill" style="width: ${this.resources.cpu.latest?.process_percent || 0}%"></div>
              </div>
            </div>
          </div>
        ` : html`
          <p>Loading resource data...</p>
        `}
      </div>
    `;
  }

  renderFunctionsTab() {
    if (!this.functions) {
      return html`
        <div class="card">
          <h2 class="card-title">Functions</h2>
          <p>Loading function data...</p>
        </div>
      `;
    }

    return html`
      <div class="card">
        <h2 class="card-title">Functions</h2>
        
        <div class="flex justify-between items-center gap-4 mb-4">
          <div>
            <strong>Total Function Calls:</strong> ${this.formatNumber(this.functions.total_calls)} | 
            <strong>Unique Functions:</strong> ${this.formatNumber(this.functions.total_functions)}
          </div>
        </div>
        
        ${this.functions.hotspots && this.functions.hotspots.length > 0 ? html`
          <h3>Function Hotspots</h3>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Module</th>
                <th>Call Count</th>
                <th>Average Duration</th>
                <th>Total Time</th>
              </tr>
            </thead>
            <tbody>
              ${this.functions.hotspots.map(func => html`
                <tr>
                  <td>${func.name}</td>
                  <td>${func.module || '(unknown)'}</td>
                  <td>${func.count}</td>
                  <td class="${this.getDurationClass(func.avg)}">${this.formatDuration(func.avg)}</td>
                  <td class="${this.getDurationClass(func.total_time / 10)}">${this.formatDuration(func.total_time)}</td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
          <p><span class="status-indicator status-indicator-success"></span> No function hotspots detected</p>
        `}
        
        ${this.functions.slow_functions && this.functions.slow_functions.length > 0 ? html`
          <h3 class="mt-4">Slow Functions</h3>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Module</th>
                <th>Maximum Duration</th>
                <th>Average Duration</th>
                <th>Call Count</th>
              </tr>
            </thead>
            <tbody>
              ${this.functions.slow_functions.map(func => html`
                <tr>
                  <td>${func.name}</td>
                  <td>${func.module || '(unknown)'}</td>
                  <td class="${this.getDurationClass(func.max)}">${this.formatDuration(func.max)}</td>
                  <td class="${this.getDurationClass(func.avg)}">${this.formatDuration(func.avg)}</td>
                  <td>${func.count}</td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
          <p class="mt-4"><span class="status-indicator status-indicator-success"></span> No slow functions detected</p>
        `}
      </div>
    `;
  }
}

// Define the custom element
if (!customElements.get('profiler-dashboard')) {
  customElements.define('profiler-dashboard', ProfilerDashboard);
}