/**
 * Resource Monitor Component
 * 
 * A web component for monitoring system and application resource usage
 */

import { loadChartJS, createTimeSeriesChart, parseDate } from './chart-loader.js';

// Import or use the LitElement base class
const LitElement = window.litElement?.LitElement || Object.getPrototypeOf(document.createElement('span')).constructor;
const html = window.litElement?.html || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));
const css = window.litElement?.css || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));

/**
 * Resource Monitor
 * 
 * @element resource-monitor
 * @attr {String} api-base-url - Base URL for API endpoints
 */
class ResourceMonitor extends LitElement {
  static get properties() {
    return {
      apiBaseUrl: { type: String, attribute: 'api-base-url' },
      data: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      timeWindow: { type: String },
      chartReady: { type: Boolean },
      autoRefresh: { type: Boolean },
      refreshInterval: { type: Number },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        width: 100%;
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
      
      .chart-container {
        position: relative;
        height: 300px;
        margin-bottom: 16px;
      }
      
      .chart-legend {
        padding: 8px;
        font-size: 12px;
        display: flex;
        justify-content: center;
        gap: 16px;
        flex-wrap: wrap;
      }
      
      .legend-item {
        display: flex;
        align-items: center;
        margin-right: 16px;
      }
      
      .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 4px;
      }
      
      .controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
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
      
      .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid rgba(0, 120, 212, 0.2);
        border-radius: 50%;
        border-top-color: var(--primary-color, #0078d7);
        animation: spin 1s ease-in-out infinite;
        margin-right: 8px;
      }
      
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      
      select {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
      }
      
      .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
      
      .progress-bar-fill.warning {
        background-color: #ff8c00;
      }
      
      .progress-bar-fill.danger {
        background-color: #e81123;
      }
      
      .checkbox-wrapper {
        display: flex;
        align-items: center;
        margin-right: 16px;
      }
      
      .checkbox-wrapper input {
        margin-right: 4px;
      }
      
      .flex {
        display: flex;
      }
      
      .gap-2 {
        gap: 8px;
      }
      
      .justify-between {
        justify-content: space-between;
      }
      
      .items-center {
        align-items: center;
      }
    `;
  }

  constructor() {
    super();
    this.apiBaseUrl = '/api';
    this.data = null;
    this.loading = false;
    this.error = null;
    this.timeWindow = '1h';
    this.chartReady = false;
    this.autoRefresh = true;
    this.refreshInterval = 10000; // 10 seconds
    this._refreshIntervalId = null;
  }

  connectedCallback() {
    super.connectedCallback();
    this._loadChartJS();
    this.loadData();
    this._startAutoRefresh();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopAutoRefresh();
  }

  async _loadChartJS() {
    try {
      await loadChartJS();
      this.chartReady = true;
      if (this.data) {
        this._renderCharts();
      }
    } catch (error) {
      console.error('Failed to load Chart.js:', error);
      this.error = 'Failed to load chart library';
    }
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

  toggleAutoRefresh() {
    this.autoRefresh = !this.autoRefresh;
    if (this.autoRefresh) {
      this._startAutoRefresh();
      this.loadData(); // Load data immediately when enabling
    } else {
      this._stopAutoRefresh();
    }
  }

  async loadData() {
    this.loading = true;
    this.error = null;

    try {
      const response = await fetch(`${this.apiBaseUrl}/metrics/resources?window=${this.timeWindow}`);
      if (!response.ok) {
        throw new Error(`Failed to load resource data: ${response.statusText}`);
      }
      this.data = await response.json();
      
      // Render charts if Chart.js is ready
      if (this.chartReady) {
        this._renderCharts();
      }
    } catch (error) {
      console.error('Error loading data:', error);
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  changeTimeWindow(event) {
    this.timeWindow = event.target.value;
    this.loadData();
  }

  _renderCharts() {
    if (!this.data || !this.chartReady) {
      return;
    }
    
    requestAnimationFrame(() => {
      this._renderMemoryChart();
      this._renderCpuChart();
    });
  }

  _renderMemoryChart() {
    const memoryCanvas = this.shadowRoot.getElementById('memoryChart');
    if (!memoryCanvas) {
      console.warn('Memory chart canvas not found');
      return;
    }
    
    // Get data
    const memorySeries = this.data.memory.series || [];
    
    // Prepare data
    const datasets = [
      {
        label: 'System Memory',
        data: memorySeries.map(d => ({
          x: parseDate(d.timestamp),
          y: d.percent
        })),
        borderColor: '#0078d7',
        backgroundColor: 'rgba(0, 120, 215, 0.1)',
        fill: true,
        tension: 0.1,
      },
      {
        label: 'Process Memory',
        data: memorySeries.map(d => ({
          x: parseDate(d.timestamp),
          y: d.process_percent || 0
        })),
        borderColor: '#107c10',
        backgroundColor: 'rgba(16, 124, 16, 0.1)',
        fill: true,
        tension: 0.1,
      },
    ];
    
    // Create chart
    createTimeSeriesChart(memoryCanvas, {
      datasets,
      title: 'Memory Usage',
      yAxisTitle: 'Memory Usage (%)',
      yMin: 0,
      yMax: 100,
    });
  }

  _renderCpuChart() {
    const cpuCanvas = this.shadowRoot.getElementById('cpuChart');
    if (!cpuCanvas) {
      console.warn('CPU chart canvas not found');
      return;
    }
    
    // Get data
    const cpuSeries = this.data.cpu.series || [];
    
    // Prepare data
    const datasets = [
      {
        label: 'System CPU',
        data: cpuSeries.map(d => ({
          x: parseDate(d.timestamp),
          y: d.percent
        })),
        borderColor: '#e81123',
        backgroundColor: 'rgba(232, 17, 35, 0.1)',
        fill: true,
        tension: 0.1,
      },
      {
        label: 'Process CPU',
        data: cpuSeries.map(d => ({
          x: parseDate(d.timestamp),
          y: d.process_percent || 0
        })),
        borderColor: '#ff8c00',
        backgroundColor: 'rgba(255, 140, 0, 0.1)',
        fill: true,
        tension: 0.1,
      },
    ];
    
    // Create chart
    createTimeSeriesChart(cpuCanvas, {
      datasets,
      title: 'CPU Usage',
      yAxisTitle: 'CPU Usage (%)',
      yMin: 0,
      yMax: 100,
    });
  }

  getFillClass(value) {
    if (value > 80) {
      return 'danger';
    } else if (value > 60) {
      return 'warning';
    }
    return '';
  }

  render() {
    return html`
      <div class="card">
        <h2 class="card-title">Resource Utilization</h2>
        
        <div class="controls">
          <div class="flex items-center gap-2">
            <label for="timeWindow">Time Window:</label>
            <select id="timeWindow" @change=${this.changeTimeWindow} .value=${this.timeWindow}>
              <option value="5m">Last 5 minutes</option>
              <option value="15m">Last 15 minutes</option>
              <option value="30m">Last 30 minutes</option>
              <option value="1h">Last hour</option>
              <option value="3h">Last 3 hours</option>
              <option value="6h">Last 6 hours</option>
              <option value="12h">Last 12 hours</option>
              <option value="1d">Last 24 hours</option>
            </select>
            
            <div class="checkbox-wrapper">
              <input type="checkbox" id="autoRefresh" ?checked=${this.autoRefresh} @change=${this.toggleAutoRefresh}>
              <label for="autoRefresh">Auto-refresh</label>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            ${this.loading ? html`<div class="loading-spinner"></div> Loading...` : 
              html`<button @click=${this.loadData}>Refresh</button>`}
          </div>
        </div>
        
        ${this.error ? html`<div class="error">${this.error}</div>` : ''}
        
        ${this.data ? html`
          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-title">Current Memory Usage</div>
              <div class="metric-value">${this.data.memory.latest?.percent.toFixed(1)}%</div>
              <div class="metric-subtitle">System Memory</div>
              <div class="progress-bar">
                <div class="progress-bar-fill ${this.getFillClass(this.data.memory.latest?.percent)}" 
                     style="width: ${this.data.memory.latest?.percent}%"></div>
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-title">Current Process Memory</div>
              <div class="metric-value">${this.data.memory.latest?.process_percent?.toFixed(1) || 0}%</div>
              <div class="metric-subtitle">Application Memory</div>
              <div class="progress-bar">
                <div class="progress-bar-fill ${this.getFillClass(this.data.memory.latest?.process_percent || 0)}"
                     style="width: ${this.data.memory.latest?.process_percent || 0}%"></div>
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-title">Current CPU Usage</div>
              <div class="metric-value">${this.data.cpu.latest?.percent.toFixed(1)}%</div>
              <div class="metric-subtitle">System CPU</div>
              <div class="progress-bar">
                <div class="progress-bar-fill ${this.getFillClass(this.data.cpu.latest?.percent)}"
                     style="width: ${this.data.cpu.latest?.percent}%"></div>
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-title">Current Process CPU</div>
              <div class="metric-value">${this.data.cpu.latest?.process_percent?.toFixed(1) || 0}%</div>
              <div class="metric-subtitle">Application CPU</div>
              <div class="progress-bar">
                <div class="progress-bar-fill ${this.getFillClass(this.data.cpu.latest?.process_percent || 0)}"
                     style="width: ${this.data.cpu.latest?.process_percent || 0}%"></div>
              </div>
            </div>
          </div>
          
          <div class="chart-container">
            <canvas id="memoryChart"></canvas>
          </div>
          
          <div class="chart-container">
            <canvas id="cpuChart"></canvas>
          </div>
          
          <div class="card">
            <h3>Additional Statistics</h3>
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-title">Memory - Average Usage</div>
                <div class="metric-value">${this.data.memory.avg_percent?.toFixed(1) || 0}%</div>
                <div class="metric-subtitle">System Average</div>
              </div>
              
              <div class="metric-card">
                <div class="metric-title">Memory - Peak Usage</div>
                <div class="metric-value">${this.data.memory.max_percent?.toFixed(1) || 0}%</div>
                <div class="metric-subtitle">System Maximum</div>
              </div>
              
              <div class="metric-card">
                <div class="metric-title">CPU - Average Usage</div>
                <div class="metric-value">${this.data.cpu.avg_percent?.toFixed(1) || 0}%</div>
                <div class="metric-subtitle">System Average</div>
              </div>
              
              <div class="metric-card">
                <div class="metric-title">CPU - Peak Usage</div>
                <div class="metric-value">${this.data.cpu.max_percent?.toFixed(1) || 0}%</div>
                <div class="metric-subtitle">System Maximum</div>
              </div>
            </div>
          </div>
        ` : html`
          <p>Loading resource data...</p>
        `}
      </div>
    `;
  }
}

// Define the custom element
if (!customElements.get('resource-monitor')) {
  customElements.define('resource-monitor', ResourceMonitor);
}