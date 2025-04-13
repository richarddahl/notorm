import { LitElement, html, css } from 'lit';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-divider.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-chip.js';
import '@webcomponents/awesome/wa-tooltip.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-switch.js';
import '@webcomponents/awesome/wa-progress.js';
import { Chart } from 'chart.js/auto';

/**
 * @element wa-system-monitor
 * @description System monitoring dashboard for UNO framework using WebAwesome components
 */
export class WebAwesomeSystemMonitor extends LitElement {
  static get properties() {
    return {
      metrics: { type: Object },
      activeTab: { type: String },
      timeRange: { type: String },
      refreshInterval: { type: Number },
      loading: { type: Boolean },
      error: { type: String },
      alerts: { type: Array },
      resourceStats: { type: Object },
      healthStatus: { type: Object },
      traces: { type: Array },
      logs: { type: Array },
      autoRefresh: { type: Boolean }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --monitor-bg: var(--wa-background-color, #f5f5f5);
        --monitor-padding: 20px;
      }
      .monitor-container {
        padding: var(--monitor-padding);
        background-color: var(--monitor-bg);
        min-height: 600px;
      }
      .monitor-header {
        margin-bottom: 24px;
      }
      .monitor-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .monitor-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
      }
      .control-group {
        display: flex;
        gap: 12px;
        align-items: center;
      }
      .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      .chart-container {
        height: 300px;
        position: relative;
        margin-bottom: 24px;
      }
      .health-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px;
        margin-bottom: 24px;
      }
      .health-item {
        padding: 16px;
      }
      .health-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }
      .health-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0;
      }
      .health-status {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        padding: 8px 0;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
      }
      .status-healthy {
        background-color: var(--wa-success-color, #4caf50);
      }
      .status-warning {
        background-color: var(--wa-warning-color, #ff9800);
      }
      .status-critical {
        background-color: var(--wa-error-color, #f44336);
      }
      .metric-card {
        padding: 16px;
        text-align: center;
      }
      .metric-value {
        font-size: 24px;
        font-weight: 500;
        color: var(--wa-primary-color, #3f51b5);
        margin-bottom: 8px;
      }
      .metric-label {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .alert-item {
        margin-bottom: 16px;
      }
      .alert-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .alert-title {
        font-weight: 500;
      }
      .alert-time {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .trace-table {
        width: 100%;
        border-collapse: collapse;
      }
      .trace-table th, .trace-table td {
        padding: 8px;
        text-align: left;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .trace-table th {
        font-weight: 500;
        color: var(--wa-text-primary-color, #212121);
      }
      .log-item {
        padding: 8px 16px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .log-time {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
        margin-right: 8px;
      }
      .log-level {
        font-size: 12px;
        font-weight: 500;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 8px;
      }
      .log-info {
        background-color: var(--wa-info-color-light, rgba(25, 118, 210, 0.1));
        color: var(--wa-info-color, #1976d2);
      }
      .log-warning {
        background-color: var(--wa-warning-color-light, rgba(255, 152, 0, 0.1));
        color: var(--wa-warning-color, #ff9800);
      }
      .log-error {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
      }
      .log-debug {
        background-color: var(--wa-default-color-light, rgba(117, 117, 117, 0.1));
        color: var(--wa-default-color, #757575);
      }
      .resource-bar {
        margin-bottom: 16px;
      }
      .resource-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
      }
      .resource-name {
        font-weight: 500;
      }
      .resource-value {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
    `;
  }

  constructor() {
    super();
    this.activeTab = 'overview';
    this.timeRange = '1h';
    this.refreshInterval = 30;
    this.loading = false;
    this.error = null;
    this.metrics = {};
    this.alerts = [];
    this.resourceStats = {};
    this.healthStatus = {};
    this.traces = [];
    this.logs = [];
    this.autoRefresh = true;
    this._charts = {};
    this._refreshTimer = null;
    
    // Mock data for demo
    this._loadMockData();
  }

  _loadMockData() {
    // CPU usage history (last 24 hours, every hour)
    const cpuData = Array.from({ length: 24 }, (_, i) => {
      return {
        timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
        value: 10 + Math.random() * 50
      };
    });
    
    // Memory usage history
    const memoryData = Array.from({ length: 24 }, (_, i) => {
      return {
        timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
        value: 2 + Math.random() * 6
      };
    });
    
    // Request rate history
    const requestData = Array.from({ length: 24 }, (_, i) => {
      return {
        timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
        value: 50 + Math.random() * 150
      };
    });
    
    // Response time history
    const responseTimeData = Array.from({ length: 24 }, (_, i) => {
      return {
        timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
        value: 50 + Math.random() * 200
      };
    });
    
    // Set metrics
    this.metrics = {
      cpu: {
        current: 24.5,
        history: cpuData
      },
      memory: {
        current: 3.2,
        total: 8,
        history: memoryData
      },
      requests: {
        rate: 78,
        total: 1256789,
        history: requestData
      },
      responseTime: {
        average: 125,
        p95: 287,
        history: responseTimeData
      }
    };
    
    // Resource stats
    this.resourceStats = {
      cpu: 24.5,
      memory: 40.0,
      disk: 62.3,
      network: 18.7,
      database: 35.2,
      cache: 64.8
    };
    
    // Health status
    this.healthStatus = {
      api: { status: 'healthy', message: 'All endpoints available', latency: '125ms' },
      database: { status: 'healthy', message: 'Connected', latency: '5ms' },
      cache: { status: 'healthy', message: 'Connected', hitRate: '94.2%' },
      message_queue: { status: 'warning', message: '1 failed message delivery', queue: 25 },
      storage: { status: 'healthy', message: 'Available', usage: '62.3%' },
      worker: { status: 'healthy', message: 'Running', jobs: '48 active' }
    };
    
    // Alerts
    this.alerts = [
      {
        id: 1,
        title: 'High CPU Usage',
        message: 'CPU usage exceeded 80% for more than 5 minutes',
        severity: 'warning',
        timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
        resolved: true
      },
      {
        id: 2,
        title: 'Database Connection Error',
        message: 'Temporary connection loss to the database, recovered automatically',
        severity: 'error',
        timestamp: new Date(Date.now() - 3 * 3600000).toISOString(),
        resolved: true
      },
      {
        id: 3,
        title: 'Failed Job Execution',
        message: 'Background job "data-cleanup" failed to execute',
        severity: 'error',
        timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
        resolved: false
      },
      {
        id: 4,
        title: 'High Memory Usage',
        message: 'Memory usage reached 85% of available RAM',
        severity: 'warning',
        timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
        resolved: true
      }
    ];
    
    // Traces (for tracing tab)
    this.traces = [
      {
        id: 'trace-1',
        name: 'GET /api/users',
        duration: 125,
        status: 'success',
        timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
        user: 'admin@example.com'
      },
      {
        id: 'trace-2',
        name: 'POST /api/reports/execute',
        duration: 3250,
        status: 'success',
        timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
        user: 'john.doe@example.com'
      },
      {
        id: 'trace-3',
        name: 'GET /api/data/orders',
        duration: 87,
        status: 'success',
        timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
        user: 'jane.smith@example.com'
      },
      {
        id: 'trace-4',
        name: 'PUT /api/users/5',
        duration: 178,
        status: 'error',
        timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
        user: 'admin@example.com'
      }
    ];
    
    // Logs (for logs tab)
    this.logs = [
      {
        id: 'log-1',
        timestamp: new Date(Date.now() - 2 * 60000).toISOString(),
        level: 'info',
        message: 'Application started successfully',
        source: 'app.startup'
      },
      {
        id: 'log-2',
        timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
        level: 'info',
        message: 'User logged in: admin@example.com',
        source: 'auth.login'
      },
      {
        id: 'log-3',
        timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
        level: 'warning',
        message: 'High memory usage detected: 85%',
        source: 'system.resources'
      },
      {
        id: 'log-4',
        timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
        level: 'error',
        message: 'Failed to connect to database: Connection timeout',
        source: 'database.connection'
      },
      {
        id: 'log-5',
        timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
        level: 'info',
        message: 'Cache invalidated for: users',
        source: 'cache.invalidation'
      },
      {
        id: 'log-6',
        timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
        level: 'debug',
        message: 'Processing request: GET /api/users',
        source: 'http.request'
      },
      {
        id: 'log-7',
        timestamp: new Date(Date.now() - 35 * 60000).toISOString(),
        level: 'error',
        message: 'Background job failed: data-cleanup',
        source: 'jobs.execution'
      }
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    
    if (this.autoRefresh) {
      this._setupRefreshTimer();
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    
    this._clearRefreshTimer();
    this._destroyCharts();
  }

  _setupRefreshTimer() {
    this._clearRefreshTimer();
    
    if (this.refreshInterval > 0) {
      this._refreshTimer = setInterval(() => {
        this.refresh();
      }, this.refreshInterval * 1000);
    }
  }

  _clearRefreshTimer() {
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }
  }

  refresh() {
    // In a real app, this would fetch new data from the API
    // For demo, we'll just simulate some changes in the data
    
    this.loading = true;
    
    // Simulate API delay
    setTimeout(() => {
      // Update current metrics with slight changes
      this.metrics = {
        ...this.metrics,
        cpu: {
          ...this.metrics.cpu,
          current: Math.max(5, Math.min(95, this.metrics.cpu.current + (Math.random() * 10 - 5)))
        },
        memory: {
          ...this.metrics.memory,
          current: Math.max(1, Math.min(this.metrics.memory.total, this.metrics.memory.current + (Math.random() * 0.5 - 0.25)))
        },
        requests: {
          ...this.metrics.requests,
          rate: Math.max(10, Math.min(200, this.metrics.requests.rate + (Math.random() * 30 - 15))),
          total: this.metrics.requests.total + Math.floor(Math.random() * 100)
        },
        responseTime: {
          ...this.metrics.responseTime,
          average: Math.max(50, Math.min(300, this.metrics.responseTime.average + (Math.random() * 40 - 20))),
          p95: Math.max(100, Math.min(500, this.metrics.responseTime.p95 + (Math.random() * 60 - 30)))
        }
      };
      
      // Update resource stats
      this.resourceStats = {
        cpu: Math.max(5, Math.min(95, this.resourceStats.cpu + (Math.random() * 10 - 5))),
        memory: Math.max(5, Math.min(95, this.resourceStats.memory + (Math.random() * 8 - 4))),
        disk: Math.max(5, Math.min(95, this.resourceStats.disk + (Math.random() * 2 - 1))),
        network: Math.max(5, Math.min(95, this.resourceStats.network + (Math.random() * 15 - 7.5))),
        database: Math.max(5, Math.min(95, this.resourceStats.database + (Math.random() * 10 - 5))),
        cache: Math.max(5, Math.min(95, this.resourceStats.cache + (Math.random() * 10 - 5)))
      };
      
      // Occasionally add a new log entry
      if (Math.random() > 0.7) {
        const levels = ['info', 'warning', 'error', 'debug'];
        const level = levels[Math.floor(Math.random() * levels.length)];
        const sources = ['app.startup', 'auth.login', 'system.resources', 'database.connection', 'cache.invalidation', 'http.request', 'jobs.execution'];
        const source = sources[Math.floor(Math.random() * sources.length)];
        
        const newLog = {
          id: `log-${Date.now()}`,
          timestamp: new Date().toISOString(),
          level,
          message: `New log entry: ${level} from ${source}`,
          source
        };
        
        this.logs = [newLog, ...this.logs].slice(0, 100); // Keep only the last 100 logs
      }
      
      this.loading = false;
      this._updateCharts();
    }, 500);
  }

  updated(changedProperties) {
    if (changedProperties.has('activeTab')) {
      // When tab changes, render charts if needed
      this._renderCharts();
    }
    
    if (changedProperties.has('autoRefresh')) {
      if (this.autoRefresh) {
        this._setupRefreshTimer();
      } else {
        this._clearRefreshTimer();
      }
    }
    
    if (changedProperties.has('refreshInterval') && this.autoRefresh) {
      this._setupRefreshTimer();
    }
    
    if (changedProperties.has('timeRange')) {
      // Time range changed, update charts
      this._updateCharts();
    }
  }

  _renderCharts() {
    if (this.activeTab === 'overview' || this.activeTab === 'metrics') {
      // Allow DOM to update, then initialize charts
      setTimeout(() => {
        this._initializeCharts();
      }, 100);
    }
  }

  _initializeCharts() {
    // Destroy existing charts first
    this._destroyCharts();
    
    // Initialize charts based on active tab
    if (this.activeTab === 'overview' || this.activeTab === 'metrics') {
      this._initCpuChart();
      this._initMemoryChart();
      this._initRequestChart();
      this._initResponseTimeChart();
    }
  }

  _destroyCharts() {
    Object.values(this._charts).forEach(chart => {
      if (chart) chart.destroy();
    });
    this._charts = {};
  }

  _updateCharts() {
    // Update existing charts with new data
    Object.keys(this._charts).forEach(chartId => {
      const chart = this._charts[chartId];
      if (!chart) return;
      
      if (chartId === 'cpuChart') {
        this._updateCpuChart(chart);
      } else if (chartId === 'memoryChart') {
        this._updateMemoryChart(chart);
      } else if (chartId === 'requestChart') {
        this._updateRequestChart(chart);
      } else if (chartId === 'responseTimeChart') {
        this._updateResponseTimeChart(chart);
      }
    });
  }

  _getFilteredTimeData(data, hoursBack) {
    if (!data || !Array.isArray(data)) return { labels: [], values: [] };
    
    const cutoffTime = new Date(Date.now() - hoursBack * 3600000);
    const filteredData = data.filter(item => new Date(item.timestamp) >= cutoffTime);
    
    return {
      labels: filteredData.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      }),
      values: filteredData.map(item => item.value)
    };
  }

  _getTimeRangeHours() {
    switch (this.timeRange) {
      case '1h': return 1;
      case '6h': return 6;
      case '24h': return 24;
      case '7d': return 168; // 7 * 24
      case '30d': return 720; // 30 * 24
      default: return 24;
    }
  }

  _initCpuChart() {
    const chartContainer = this.shadowRoot.querySelector('#cpuChartContainer');
    if (!chartContainer) return;
    
    const canvas = document.createElement('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.cpu?.history, hoursBack);
    
    this._charts.cpuChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'CPU Usage (%)',
          data: values,
          fill: true,
          backgroundColor: 'rgba(63, 81, 181, 0.1)',
          borderColor: 'rgba(63, 81, 181, 1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'CPU Usage'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'Usage (%)'
            }
          }
        }
      }
    });
  }

  _updateCpuChart(chart) {
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.cpu?.history, hoursBack);
    
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
  }

  _initMemoryChart() {
    const chartContainer = this.shadowRoot.querySelector('#memoryChartContainer');
    if (!chartContainer) return;
    
    const canvas = document.createElement('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.memory?.history, hoursBack);
    
    this._charts.memoryChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Memory Usage (GB)',
          data: values,
          fill: true,
          backgroundColor: 'rgba(211, 47, 47, 0.1)',
          borderColor: 'rgba(211, 47, 47, 1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Memory Usage'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: this.metrics.memory?.total || 8,
            title: {
              display: true,
              text: 'Usage (GB)'
            }
          }
        }
      }
    });
  }

  _updateMemoryChart(chart) {
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.memory?.history, hoursBack);
    
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
  }

  _initRequestChart() {
    const chartContainer = this.shadowRoot.querySelector('#requestChartContainer');
    if (!chartContainer) return;
    
    const canvas = document.createElement('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.requests?.history, hoursBack);
    
    this._charts.requestChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Requests per Minute',
          data: values,
          backgroundColor: 'rgba(16, 150, 24, 0.6)',
          borderColor: 'rgba(16, 150, 24, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Request Rate'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Requests/Min'
            }
          }
        }
      }
    });
  }

  _updateRequestChart(chart) {
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.requests?.history, hoursBack);
    
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
  }

  _initResponseTimeChart() {
    const chartContainer = this.shadowRoot.querySelector('#responseTimeChartContainer');
    if (!chartContainer) return;
    
    const canvas = document.createElement('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.responseTime?.history, hoursBack);
    
    this._charts.responseTimeChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Response Time (ms)',
          data: values,
          fill: false,
          borderColor: 'rgba(245, 0, 87, 1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Response Time'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Time (ms)'
            }
          }
        }
      }
    });
  }

  _updateResponseTimeChart(chart) {
    const hoursBack = this._getTimeRangeHours();
    const { labels, values } = this._getFilteredTimeData(this.metrics.responseTime?.history, hoursBack);
    
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
  }

  handleTimeRangeChange(e) {
    this.timeRange = e.target.value;
  }

  handleRefreshIntervalChange(e) {
    this.refreshInterval = parseInt(e.target.value, 10);
  }

  handleAutoRefreshChange(e) {
    this.autoRefresh = e.target.checked;
  }

  handleTabChange(e) {
    this.activeTab = e.detail.value;
  }

  render() {
    return html`
      <div class="monitor-container">
        <div class="monitor-header">
          <h1 class="monitor-title">System Monitoring</h1>
          <p class="monitor-subtitle">Real-time monitoring and performance metrics for your application</p>
        </div>
        
        <div class="controls">
          <div class="control-group">
            <wa-select 
              label="Time Range"
              .value=${this.timeRange}
              @change=${this.handleTimeRangeChange}>
              <wa-option value="1h">Last Hour</wa-option>
              <wa-option value="6h">Last 6 Hours</wa-option>
              <wa-option value="24h">Last 24 Hours</wa-option>
              <wa-option value="7d">Last 7 Days</wa-option>
              <wa-option value="30d">Last 30 Days</wa-option>
            </wa-select>
            
            <wa-select 
              label="Refresh Interval"
              .value=${this.refreshInterval.toString()}
              @change=${this.handleRefreshIntervalChange}>
              <wa-option value="10">10 seconds</wa-option>
              <wa-option value="30">30 seconds</wa-option>
              <wa-option value="60">1 minute</wa-option>
              <wa-option value="300">5 minutes</wa-option>
            </wa-select>
            
            <div style="display: flex; align-items: center; gap: 8px;">
              <wa-switch 
                .checked=${this.autoRefresh}
                @change=${this.handleAutoRefreshChange}>
              </wa-switch>
              <span>Auto-refresh</span>
            </div>
          </div>
          
          <wa-button @click=${this.refresh}>
            <wa-icon slot="prefix" name="refresh"></wa-icon>
            Refresh Now
          </wa-button>
        </div>
        
        ${this.error ? html`
          <wa-alert type="error" style="margin-bottom: 24px;">
            ${this.error}
            <wa-button slot="action" variant="text" @click=${this.refresh}>
              Retry
            </wa-button>
          </wa-alert>
        ` : ''}
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="overview">Overview</wa-tab>
          <wa-tab value="metrics">Metrics</wa-tab>
          <wa-tab value="health">Health</wa-tab>
          <wa-tab value="alerts">Alerts</wa-tab>
          <wa-tab value="tracing">Tracing</wa-tab>
          <wa-tab value="logs">Logs</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="overview" ?active=${this.activeTab === 'overview'}>
          ${this._renderOverviewPanel()}
        </wa-tab-panel>
        
        <wa-tab-panel value="metrics" ?active=${this.activeTab === 'metrics'}>
          ${this._renderMetricsPanel()}
        </wa-tab-panel>
        
        <wa-tab-panel value="health" ?active=${this.activeTab === 'health'}>
          ${this._renderHealthPanel()}
        </wa-tab-panel>
        
        <wa-tab-panel value="alerts" ?active=${this.activeTab === 'alerts'}>
          ${this._renderAlertsPanel()}
        </wa-tab-panel>
        
        <wa-tab-panel value="tracing" ?active=${this.activeTab === 'tracing'}>
          ${this._renderTracingPanel()}
        </wa-tab-panel>
        
        <wa-tab-panel value="logs" ?active=${this.activeTab === 'logs'}>
          ${this._renderLogsPanel()}
        </wa-tab-panel>
        
        ${this.loading ? html`
          <div style="position: fixed; top: 16px; right: 16px; z-index: 1000;">
            <wa-spinner size="small"></wa-spinner>
            <span style="margin-left: 8px;">Loading...</span>
          </div>
        ` : ''}
      </div>
    `;
  }

  _renderOverviewPanel() {
    return html`
      <div style="margin-top: 24px;">
        <!-- Key Metrics Summary -->
        <div class="metrics-grid">
          <wa-card>
            <div class="metric-card">
              <div class="metric-value">${this.metrics.cpu?.current.toFixed(1)}%</div>
              <div class="metric-label">CPU Usage</div>
            </div>
          </wa-card>
          
          <wa-card>
            <div class="metric-card">
              <div class="metric-value">${this.metrics.memory?.current.toFixed(1)} GB</div>
              <div class="metric-label">Memory Usage</div>
            </div>
          </wa-card>
          
          <wa-card>
            <div class="metric-card">
              <div class="metric-value">${this.metrics.requests?.rate.toFixed(0)}</div>
              <div class="metric-label">Requests/Min</div>
            </div>
          </wa-card>
          
          <wa-card>
            <div class="metric-card">
              <div class="metric-value">${this.metrics.responseTime?.average.toFixed(0)} ms</div>
              <div class="metric-label">Avg Response Time</div>
            </div>
          </wa-card>
        </div>
        
        <!-- Resource Usage -->
        <wa-card style="margin-bottom: 24px;">
          <div style="padding: 16px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">Resource Usage</h2>
            
            ${Object.entries(this.resourceStats).map(([resource, value]) => html`
              <div class="resource-bar">
                <div class="resource-label">
                  <div class="resource-name">${resource.charAt(0).toUpperCase() + resource.slice(1)}</div>
                  <div class="resource-value">${value.toFixed(1)}%</div>
                </div>
                <wa-progress 
                  value=${value} 
                  max="100"
                  color=${value > 80 ? 'error' : value > 60 ? 'warning' : 'primary'}>
                </wa-progress>
              </div>
            `)}
          </div>
        </wa-card>
        
        <!-- Status Summary -->
        <wa-card style="margin-bottom: 24px;">
          <div style="padding: 16px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">System Status</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;">
              ${Object.entries(this.healthStatus).map(([service, status]) => html`
                <div class="health-status">
                  <div class="status-indicator status-${status.status}"></div>
                  <div style="flex: 1;">
                    <div style="font-weight: 500;">${service.charAt(0).toUpperCase() + service.slice(1).replace('_', ' ')}</div>
                    <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${status.message}</div>
                  </div>
                </div>
              `)}
            </div>
          </div>
        </wa-card>
        
        <!-- Recent Alerts -->
        <wa-card style="margin-bottom: 24px;">
          <div style="padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <h2 style="margin: 0;">Recent Alerts</h2>
              <wa-button variant="text">
                View All
              </wa-button>
            </div>
            
            ${this.alerts.slice(0, 3).map(alert => html`
              <div class="alert-item">
                <div class="alert-header">
                  <div class="alert-title">
                    <wa-icon 
                      name=${alert.severity === 'error' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'} 
                      style="color: ${alert.severity === 'error' ? 'var(--wa-error-color)' : alert.severity === 'warning' ? 'var(--wa-warning-color)' : 'var(--wa-info-color)'}">
                    </wa-icon>
                    ${alert.title}
                    ${alert.resolved ? html`
                      <wa-chip size="small" color="success">Resolved</wa-chip>
                    ` : html`
                      <wa-chip size="small" color="error">Active</wa-chip>
                    `}
                  </div>
                  <div class="alert-time">${this._formatRelativeTime(alert.timestamp)}</div>
                </div>
                <div>${alert.message}</div>
              </div>
              <wa-divider></wa-divider>
            `)}
          </div>
        </wa-card>
        
        <!-- Charts -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 24px;">
          <wa-card>
            <div style="padding: 16px;">
              <div id="cpuChartContainer" class="chart-container"></div>
            </div>
          </wa-card>
          
          <wa-card>
            <div style="padding: 16px;">
              <div id="memoryChartContainer" class="chart-container"></div>
            </div>
          </wa-card>
        </div>
      </div>
    `;
  }

  _renderMetricsPanel() {
    return html`
      <div style="margin-top: 24px;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 24px; margin-bottom: 24px;">
          <wa-card>
            <div style="padding: 16px;">
              <div id="cpuChartContainer" class="chart-container"></div>
            </div>
          </wa-card>
          
          <wa-card>
            <div style="padding: 16px;">
              <div id="memoryChartContainer" class="chart-container"></div>
            </div>
          </wa-card>
          
          <wa-card>
            <div style="padding: 16px;">
              <div id="requestChartContainer" class="chart-container"></div>
            </div>
          </wa-card>
          
          <wa-card>
            <div style="padding: 16px;">
              <div id="responseTimeChartContainer" class="chart-container"></div>
            </div>
          </wa-card>
        </div>
        
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">System Resources</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-bottom: 24px;">
              ${Object.entries(this.resourceStats).map(([resource, value]) => html`
                <div>
                  <div style="font-weight: 500; margin-bottom: 8px;">${resource.charAt(0).toUpperCase() + resource.slice(1)}</div>
                  <wa-progress 
                    value=${value} 
                    max="100"
                    color=${value > 80 ? 'error' : value > 60 ? 'warning' : 'primary'}>
                    ${value.toFixed(1)}%
                  </wa-progress>
                </div>
              `)}
            </div>
            
            <h3 style="margin-top: 24px; margin-bottom: 16px;">Detailed Metrics</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Metric</th>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Value</th>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">CPU Usage</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">${this.metrics.cpu?.current.toFixed(1)}%</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-chip 
                      color=${this.metrics.cpu?.current > 80 ? 'error' : this.metrics.cpu?.current > 60 ? 'warning' : 'success'}>
                      ${this.metrics.cpu?.current > 80 ? 'Critical' : this.metrics.cpu?.current > 60 ? 'Warning' : 'Normal'}
                    </wa-chip>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Memory Usage</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">${this.metrics.memory?.current.toFixed(1)} GB / ${this.metrics.memory?.total} GB</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-chip 
                      color=${(this.metrics.memory?.current / this.metrics.memory?.total) > 0.8 ? 'error' : 
                             (this.metrics.memory?.current / this.metrics.memory?.total) > 0.6 ? 'warning' : 'success'}>
                      ${(this.metrics.memory?.current / this.metrics.memory?.total) > 0.8 ? 'Critical' : 
                        (this.metrics.memory?.current / this.metrics.memory?.total) > 0.6 ? 'Warning' : 'Normal'}
                    </wa-chip>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Request Rate</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">${this.metrics.requests?.rate.toFixed(0)} requests/min</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-chip color="success">Normal</wa-chip>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Avg. Response Time</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">${this.metrics.responseTime?.average.toFixed(0)} ms</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-chip 
                      color=${this.metrics.responseTime?.average > 200 ? 'error' : 
                             this.metrics.responseTime?.average > 100 ? 'warning' : 'success'}>
                      ${this.metrics.responseTime?.average > 200 ? 'Critical' : 
                        this.metrics.responseTime?.average > 100 ? 'Warning' : 'Normal'}
                    </wa-chip>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">P95 Response Time</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">${this.metrics.responseTime?.p95.toFixed(0)} ms</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-chip 
                      color=${this.metrics.responseTime?.p95 > 400 ? 'error' : 
                             this.metrics.responseTime?.p95 > 200 ? 'warning' : 'success'}>
                      ${this.metrics.responseTime?.p95 > 400 ? 'Critical' : 
                        this.metrics.responseTime?.p95 > 200 ? 'Warning' : 'Normal'}
                    </wa-chip>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Total Requests</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">${this.metrics.requests?.total.toLocaleString()}</td>
                  <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                    <wa-chip color="success">N/A</wa-chip>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </wa-card>
      </div>
    `;
  }

  _renderHealthPanel() {
    return html`
      <div style="margin-top: 24px;">
        <wa-card style="margin-bottom: 24px;">
          <div style="padding: 16px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">Health Summary</h2>
            
            <div style="display: flex; gap: 16px; margin-bottom: 24px;">
              <div style="flex: 1; text-align: center; padding: 24px; background-color: var(--wa-success-color-light); border-radius: var(--wa-border-radius);">
                <wa-icon name="check_circle" style="font-size: 48px; color: var(--wa-success-color);"></wa-icon>
                <div style="font-size: 24px; font-weight: 500; margin-top: 8px;">${Object.values(this.healthStatus).filter(s => s.status === 'healthy').length}</div>
                <div style="color: var(--wa-text-secondary-color);">Healthy Services</div>
              </div>
              
              <div style="flex: 1; text-align: center; padding: 24px; background-color: var(--wa-warning-color-light); border-radius: var(--wa-border-radius);">
                <wa-icon name="warning" style="font-size: 48px; color: var(--wa-warning-color);"></wa-icon>
                <div style="font-size: 24px; font-weight: 500; margin-top: 8px;">${Object.values(this.healthStatus).filter(s => s.status === 'warning').length}</div>
                <div style="color: var(--wa-text-secondary-color);">Warning Services</div>
              </div>
              
              <div style="flex: 1; text-align: center; padding: 24px; background-color: var(--wa-error-color-light); border-radius: var(--wa-border-radius);">
                <wa-icon name="error" style="font-size: 48px; color: var(--wa-error-color);"></wa-icon>
                <div style="font-size: 24px; font-weight: 500; margin-top: 8px;">${Object.values(this.healthStatus).filter(s => s.status === 'critical').length}</div>
                <div style="color: var(--wa-text-secondary-color);">Critical Services</div>
              </div>
            </div>
          </div>
        </wa-card>
        
        <div class="health-grid">
          ${Object.entries(this.healthStatus).map(([service, status]) => html`
            <wa-card>
              <div class="health-item">
                <div class="health-header">
                  <h3 class="health-title">${service.charAt(0).toUpperCase() + service.slice(1).replace('_', ' ')}</h3>
                  <wa-chip 
                    color=${status.status === 'healthy' ? 'success' : 
                           status.status === 'warning' ? 'warning' : 'error'}>
                    ${status.status.charAt(0).toUpperCase() + status.status.slice(1)}
                  </wa-chip>
                </div>
                
                <div style="display: flex; flex-direction: column; gap: 8px;">
                  <div>
                    <strong>Status:</strong> ${status.message}
                  </div>
                  
                  ${status.latency ? html`
                    <div>
                      <strong>Latency:</strong> ${status.latency}
                    </div>
                  ` : ''}
                  
                  ${status.hitRate ? html`
                    <div>
                      <strong>Hit Rate:</strong> ${status.hitRate}
                    </div>
                  ` : ''}
                  
                  ${status.queue ? html`
                    <div>
                      <strong>Queue Size:</strong> ${status.queue}
                    </div>
                  ` : ''}
                  
                  ${status.usage ? html`
                    <div>
                      <strong>Usage:</strong> ${status.usage}
                    </div>
                  ` : ''}
                  
                  ${status.jobs ? html`
                    <div>
                      <strong>Jobs:</strong> ${status.jobs}
                    </div>
                  ` : ''}
                </div>
                
                <div style="margin-top: 16px;">
                  <wa-button variant="outlined" fullwidth>
                    View Details
                  </wa-button>
                </div>
              </div>
            </wa-card>
          `)}
        </div>
      </div>
    `;
  }

  _renderAlertsPanel() {
    return html`
      <div style="margin-top: 24px;">
        <wa-card>
          <div style="padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
              <h2 style="margin: 0;">Alerts</h2>
              
              <div style="display: flex; gap: 8px;">
                <wa-button variant="outlined">
                  <wa-icon slot="prefix" name="filter_list"></wa-icon>
                  Filter
                </wa-button>
                
                <wa-button variant="outlined" color="error">
                  <wa-icon slot="prefix" name="notifications_off"></wa-icon>
                  Clear All
                </wa-button>
              </div>
            </div>
            
            <div style="margin-bottom: 24px;">
              <div style="display: flex; gap: 16px; margin-bottom: 16px;">
                <wa-button 
                  variant="filled" 
                  size="small">
                  All
                </wa-button>
                
                <wa-button 
                  variant="outlined" 
                  size="small">
                  Active
                </wa-button>
                
                <wa-button 
                  variant="outlined" 
                  size="small">
                  Resolved
                </wa-button>
              </div>
            </div>
            
            ${this.alerts.map(alert => html`
              <div class="alert-item" style="padding: 16px; border-radius: var(--wa-border-radius); background-color: var(--wa-surface-color);">
                <div class="alert-header">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <wa-icon 
                      name=${alert.severity === 'error' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'} 
                      style="color: ${alert.severity === 'error' ? 'var(--wa-error-color)' : alert.severity === 'warning' ? 'var(--wa-warning-color)' : 'var(--wa-info-color)'}">
                    </wa-icon>
                    <span class="alert-title">${alert.title}</span>
                    ${alert.resolved ? html`
                      <wa-chip size="small" color="success">Resolved</wa-chip>
                    ` : html`
                      <wa-chip size="small" color="error">Active</wa-chip>
                    `}
                  </div>
                  <div class="alert-time">${this._formatDate(alert.timestamp)}</div>
                </div>
                
                <div style="margin: 12px 0;">${alert.message}</div>
                
                <div style="display: flex; justify-content: flex-end; gap: 8px;">
                  <wa-button variant="text">
                    View Details
                  </wa-button>
                  
                  ${!alert.resolved ? html`
                    <wa-button variant="text" color="success">
                      Mark Resolved
                    </wa-button>
                  ` : ''}
                </div>
              </div>
              <wa-divider style="margin: 16px 0;"></wa-divider>
            `)}
            
            <div style="text-align: center; margin-top: 24px;">
              <wa-button variant="outlined">
                Load More
              </wa-button>
            </div>
          </div>
        </wa-card>
      </div>
    `;
  }

  _renderTracingPanel() {
    return html`
      <div style="margin-top: 24px;">
        <wa-card>
          <div style="padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
              <h2 style="margin: 0;">Distributed Tracing</h2>
              
              <div>
                <wa-button variant="outlined">
                  <wa-icon slot="prefix" name="filter_list"></wa-icon>
                  Filter
                </wa-button>
              </div>
            </div>
            
            <table class="trace-table">
              <thead>
                <tr>
                  <th>Operation</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Timestamp</th>
                  <th>User</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${this.traces.map(trace => html`
                  <tr>
                    <td>${trace.name}</td>
                    <td>
                      <wa-chip 
                        color=${trace.status === 'success' ? 'success' : 'error'}>
                        ${trace.status}
                      </wa-chip>
                    </td>
                    <td>${trace.duration} ms</td>
                    <td>${this._formatDate(trace.timestamp)}</td>
                    <td>${trace.user}</td>
                    <td>
                      <wa-button variant="text">
                        View
                      </wa-button>
                    </td>
                  </tr>
                `)}
              </tbody>
            </table>
            
            <div style="text-align: center; margin-top: 24px;">
              <wa-button variant="outlined">
                Load More
              </wa-button>
            </div>
          </div>
        </wa-card>
      </div>
    `;
  }

  _renderLogsPanel() {
    return html`
      <div style="margin-top: 24px;">
        <wa-card>
          <div style="padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
              <h2 style="margin: 0;">Logs</h2>
              
              <div style="display: flex; gap: 8px;">
                <wa-button variant="outlined">
                  <wa-icon slot="prefix" name="filter_list"></wa-icon>
                  Filter
                </wa-button>
                
                <wa-button variant="outlined">
                  <wa-icon slot="prefix" name="file_download"></wa-icon>
                  Export
                </wa-button>
              </div>
            </div>
            
            <div style="margin-bottom: 24px;">
              <div style="display: flex; gap: 16px; margin-bottom: 16px;">
                <wa-button 
                  variant="filled" 
                  size="small">
                  All
                </wa-button>
                
                <wa-button 
                  variant="outlined" 
                  size="small">
                  Info
                </wa-button>
                
                <wa-button 
                  variant="outlined" 
                  size="small">
                  Warning
                </wa-button>
                
                <wa-button 
                  variant="outlined" 
                  size="small">
                  Error
                </wa-button>
                
                <wa-button 
                  variant="outlined" 
                  size="small">
                  Debug
                </wa-button>
              </div>
            </div>
            
            <div style="border: 1px solid var(--wa-border-color); border-radius: var(--wa-border-radius); max-height: 600px; overflow-y: auto;">
              ${this.logs.map(log => html`
                <div class="log-item">
                  <span class="log-time">${this._formatDate(log.timestamp)}</span>
                  <span class="log-level log-${log.level}">${log.level.toUpperCase()}</span>
                  <span class="log-source">[${log.source}]</span>
                  <span>${log.message}</span>
                </div>
              `)}
            </div>
            
            <div style="text-align: center; margin-top: 24px;">
              <wa-button variant="outlined">
                Load More
              </wa-button>
            </div>
          </div>
        </wa-card>
      </div>
    `;
  }

  _formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString();
  }

  _formatRelativeTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
      return `${diffSec} second${diffSec !== 1 ? 's' : ''} ago`;
    } else if (diffMin < 60) {
      return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    } else if (diffHour < 24) {
      return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    } else if (diffDay < 30) {
      return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
    } else {
      return this._formatDate(dateString);
    }
  }
}

customElements.define('wa-system-monitor', WebAwesomeSystemMonitor);