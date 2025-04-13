import { LitElement, html, css } from 'lit-element';
import { Chart } from 'chart.js/auto';

/**
 * @element report-widget
 * @description A standalone widget for displaying report data as metrics, charts, or tables
 * @property {String} type - Type of widget (metric, chart, table)
 * @property {String} subtype - Subtype for charts (bar, line, pie, etc.)
 * @property {String} title - Widget title
 * @property {Object} data - The data to display
 * @property {Object} config - Widget configuration
 */
export class ReportWidget extends LitElement {
  static get properties() {
    return {
      type: { type: String },
      subtype: { type: String },
      title: { type: String },
      data: { type: Object },
      config: { type: Object },
      loading: { type: Boolean },
      error: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        font-family: var(--system-font, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif);
      }
      .widget {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .widget-header {
        padding: 15px;
        background-color: var(--widget-header-bg, #f8f9fa);
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .widget-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
      }
      .widget-content {
        padding: 15px;
        flex: 1;
        overflow: auto;
        display: flex;
        flex-direction: column;
        position: relative;
      }
      .chart-container {
        flex: 1;
        position: relative;
        min-height: 150px;
      }
      .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
        text-align: center;
      }
      .metric-label {
        text-align: center;
        color: #666;
        font-size: 14px;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      th, td {
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #eee;
      }
      th {
        background-color: var(--table-header-bg, #f1f3f4);
        font-weight: 600;
      }
      .loading-overlay {
        display: flex;
        justify-content: center;
        align-items: center;
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.7);
        z-index: 10;
      }
      .error {
        color: #d32f2f;
        padding: 12px;
        text-align: center;
        background-color: #ffebee;
        border-radius: 4px;
        margin: 10px 0;
        font-size: 14px;
      }
      .widget-actions {
        display: flex;
        gap: 5px;
      }
      .widget-action-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: #666;
        padding: 2px;
        font-size: 14px;
      }
      .widget-action-btn:hover {
        color: var(--primary-color, #4285f4);
      }
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100px;
        color: #666;
      }
      .empty-state-icon {
        font-size: 32px;
        margin-bottom: 10px;
        color: #ccc;
      }
      .trend-indicator {
        display: inline-flex;
        align-items: center;
        font-size: 14px;
        margin-left: 8px;
      }
      .trend-up {
        color: #4caf50;
      }
      .trend-down {
        color: #f44336;
      }
      .trend-neutral {
        color: #9e9e9e;
      }
    `;
  }

  constructor() {
    super();
    this.type = 'metric';
    this.subtype = '';
    this.title = '';
    this.data = null;
    this.config = {};
    this.loading = false;
    this.error = null;
    this.chart = null;
  }

  connectedCallback() {
    super.connectedCallback();
    
    // Handle resize events for charts
    if (this.type === 'chart') {
      this._resizeHandler = this._handleResize.bind(this);
      window.addEventListener('resize', this._resizeHandler);
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    
    if (this._resizeHandler) {
      window.removeEventListener('resize', this._resizeHandler);
    }
    
    this.destroyChart();
  }

  updated(changedProperties) {
    if (changedProperties.has('data') || 
        changedProperties.has('type') || 
        changedProperties.has('config')) {
      this.updateComplete.then(() => {
        this.renderContent();
      });
    }
  }

  _handleResize() {
    // Debounce resize handling
    clearTimeout(this._resizeTimer);
    this._resizeTimer = setTimeout(() => {
      this.destroyChart();
      this.renderContent();
    }, 250);
  }

  destroyChart() {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
  }

  renderContent() {
    if (this.loading || !this.data) return;
    
    const contentEl = this.shadowRoot.querySelector('.widget-content');
    if (!contentEl) return;
    
    switch (this.type) {
      case 'metric':
        this.renderMetric(contentEl);
        break;
      case 'chart':
        this.renderChart(contentEl);
        break;
      case 'table':
        this.renderTable(contentEl);
        break;
    }
  }

  renderMetric(container) {
    if (!this.data) {
      this.renderEmptyState(container);
      return;
    }
    
    let value = this.data;
    let subtitle = this.config.subtitle || '';
    let trendValue = null;
    
    // Extract value from data object if needed
    if (typeof this.data === 'object' && !Array.isArray(this.data)) {
      if (this.config.valueKey) {
        value = this.data[this.config.valueKey];
      } else {
        // Use first numeric property if no valueKey specified
        for (const key in this.data) {
          if (typeof this.data[key] === 'number') {
            value = this.data[key];
            break;
          }
        }
      }
      
      // Get trend value if configured
      if (this.config.trendKey && this.data[this.config.trendKey] !== undefined) {
        trendValue = this.data[this.config.trendKey];
      }
    }
    
    // Format the value
    let formattedValue = value;
    if (this.config.format) {
      const formatter = this.getFormatter(this.config.format);
      formattedValue = formatter(value);
    }
    
    // Render trend indicator if available
    let trendHtml = '';
    if (trendValue !== null) {
      const trendClass = trendValue > 0 ? 'trend-up' : (trendValue < 0 ? 'trend-down' : 'trend-neutral');
      const trendIcon = trendValue > 0 ? '▲' : (trendValue < 0 ? '▼' : '●');
      const formattedTrend = this.config.trendFormat ? 
        this.getFormatter(this.config.trendFormat)(Math.abs(trendValue)) : `${Math.abs(trendValue)}%`;
      
      trendHtml = `
        <div class="trend-indicator ${trendClass}">
          ${trendIcon} ${formattedTrend}
        </div>
      `;
    }
    
    container.innerHTML = `
      <div class="metric-value">
        ${formattedValue}
        ${trendHtml}
      </div>
      <div class="metric-label">${subtitle}</div>
    `;
  }

  renderChart(container) {
    // Clean up existing chart
    this.destroyChart();
    
    if (!this.data || (Array.isArray(this.data) && this.data.length === 0)) {
      this.renderEmptyState(container);
      return;
    }
    
    // Create chart container
    container.innerHTML = '<div class="chart-container"><canvas></canvas></div>';
    const canvas = container.querySelector('canvas');
    if (!canvas) return;
    
    // Determine chart type
    const chartType = this.subtype || 'bar';
    
    // Extract data and configure chart
    const chartData = this.prepareChartData();
    const chartOptions = this.prepareChartOptions();
    
    // Create chart
    this.chart = new Chart(canvas, {
      type: chartType,
      data: chartData,
      options: chartOptions
    });
  }

  prepareChartData() {
    const datasets = [];
    let labels = [];
    
    // Handle different data structures
    if (Array.isArray(this.data)) {
      // Array of objects
      if (typeof this.data[0] === 'object') {
        // Get labels
        if (this.config.labelKey) {
          labels = this.data.map(item => item[this.config.labelKey]);
        } else {
          // Use first string property as label
          const sampleItem = this.data[0];
          const labelKey = Object.keys(sampleItem).find(key => typeof sampleItem[key] === 'string') || Object.keys(sampleItem)[0];
          labels = this.data.map(item => item[labelKey]);
        }
        
        // Get datasets
        if (this.config.series) {
          // Multiple series specified in config
          this.config.series.forEach((series, index) => {
            datasets.push({
              label: series.label || `Series ${index + 1}`,
              data: this.data.map(item => item[series.valueKey]),
              backgroundColor: series.color || this.getChartColor(index),
              borderColor: this.subtype === 'line' ? (series.color || this.getChartColor(index)) : undefined,
              fill: this.subtype === 'line' ? (series.fill !== undefined ? series.fill : false) : undefined
            });
          });
        } else if (this.config.valueKey) {
          // Single series
          datasets.push({
            label: this.config.datasetLabel || 'Value',
            data: this.data.map(item => item[this.config.valueKey]),
            backgroundColor: this.config.color || this.getChartColor(0),
            borderColor: this.subtype === 'line' ? (this.config.color || this.getChartColor(0)) : undefined,
            fill: this.subtype === 'line' ? (this.config.fill !== undefined ? this.config.fill : false) : undefined
          });
        } else {
          // Auto-detect value properties (skip the label key)
          const valueKeys = Object.keys(this.data[0]).filter(key => 
            key !== this.config.labelKey && typeof this.data[0][key] === 'number'
          );
          
          valueKeys.forEach((key, index) => {
            datasets.push({
              label: key,
              data: this.data.map(item => item[key]),
              backgroundColor: this.getChartColor(index),
              borderColor: this.subtype === 'line' ? this.getChartColor(index) : undefined,
              fill: this.subtype === 'line' ? false : undefined
            });
          });
        }
      } else {
        // Simple array of values
        labels = this.data.map((_, index) => `Item ${index + 1}`);
        datasets.push({
          label: this.config.datasetLabel || 'Value',
          data: this.data,
          backgroundColor: this.config.color || this.getChartColor(0),
          borderColor: this.subtype === 'line' ? (this.config.color || this.getChartColor(0)) : undefined,
          fill: this.subtype === 'line' ? (this.config.fill !== undefined ? this.config.fill : false) : undefined
        });
      }
    } else if (typeof this.data === 'object') {
      // Object with key-value pairs
      labels = Object.keys(this.data);
      datasets.push({
        label: this.config.datasetLabel || 'Value',
        data: Object.values(this.data),
        backgroundColor: labels.map((_, index) => this.getChartColor(index)),
        borderColor: this.subtype === 'line' ? this.getChartColor(0) : undefined,
        fill: this.subtype === 'line' ? (this.config.fill !== undefined ? this.config.fill : false) : undefined
      });
    }
    
    return { labels, datasets };
  }

  prepareChartOptions() {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: this.config.showLegend !== false,
          position: this.config.legendPosition || 'top'
        },
        title: {
          display: !!this.config.chartTitle,
          text: this.config.chartTitle
        },
        tooltip: {
          enabled: true
        }
      }
    };
    
    // Additional options based on chart type
    switch (this.subtype) {
      case 'pie':
      case 'doughnut':
        return {
          ...baseOptions,
          cutout: this.subtype === 'doughnut' ? '50%' : undefined
        };
      case 'line':
        return {
          ...baseOptions,
          scales: {
            y: {
              beginAtZero: this.config.beginAtZero !== false,
              title: {
                display: !!this.config.yAxisTitle,
                text: this.config.yAxisTitle
              }
            },
            x: {
              title: {
                display: !!this.config.xAxisTitle,
                text: this.config.xAxisTitle
              }
            }
          },
          elements: {
            line: {
              tension: this.config.lineTension || 0.4
            },
            point: {
              radius: this.config.pointRadius || 3
            }
          }
        };
      case 'bar':
      default:
        return {
          ...baseOptions,
          scales: {
            y: {
              beginAtZero: this.config.beginAtZero !== false,
              title: {
                display: !!this.config.yAxisTitle,
                text: this.config.yAxisTitle
              }
            },
            x: {
              title: {
                display: !!this.config.xAxisTitle,
                text: this.config.xAxisTitle
              }
            }
          }
        };
    }
  }

  getChartColor(index) {
    const colors = [
      'rgba(66, 133, 244, 0.8)',   // Blue
      'rgba(219, 68, 55, 0.8)',    // Red
      'rgba(244, 180, 0, 0.8)',    // Yellow
      'rgba(15, 157, 88, 0.8)',    // Green
      'rgba(171, 71, 188, 0.8)',   // Purple
      'rgba(255, 112, 67, 0.8)',   // Orange
      'rgba(0, 172, 193, 0.8)',    // Cyan
      'rgba(124, 179, 66, 0.8)'    // Light green
    ];
    
    return colors[index % colors.length];
  }

  renderTable(container) {
    if (!this.data || (Array.isArray(this.data) && this.data.length === 0)) {
      this.renderEmptyState(container);
      return;
    }
    
    // Determine columns
    let columns = [];
    if (this.config.columns) {
      columns = this.config.columns;
    } else if (Array.isArray(this.data) && this.data.length > 0) {
      columns = Object.keys(this.data[0]).map(key => {
        return { key, label: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ') };
      });
    } else {
      columns = [
        { key: 'key', label: 'Key' },
        { key: 'value', label: 'Value' }
      ];
    }
    
    // Prepare rows
    let rows = [];
    if (Array.isArray(this.data)) {
      rows = this.data;
    } else {
      rows = Object.entries(this.data).map(([key, value]) => {
        return { key, value };
      });
    }
    
    // Apply limit if specified
    if (this.config.limit && rows.length > this.config.limit) {
      rows = rows.slice(0, this.config.limit);
    }
    
    // Generate table HTML
    let tableHTML = `
      <table>
        <thead>
          <tr>
            ${columns.map(col => `<th>${col.label || col.key}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
    `;
    
    rows.forEach(row => {
      tableHTML += '<tr>';
      columns.forEach(col => {
        const value = row[col.key];
        let displayValue = value;
        
        // Format cell value if format is specified
        if (col.format) {
          const formatter = this.getFormatter(col.format);
          displayValue = formatter(value);
        }
        
        // Handle null/undefined values
        if (displayValue === null || displayValue === undefined) {
          displayValue = '-';
        }
        
        tableHTML += `<td>${displayValue}</td>`;
      });
      tableHTML += '</tr>';
    });
    
    tableHTML += `
        </tbody>
      </table>
    `;
    
    container.innerHTML = tableHTML;
  }

  getFormatter(format) {
    switch (format) {
      case 'number':
        return value => new Intl.NumberFormat().format(value);
      case 'currency':
        return value => new Intl.NumberFormat('en-US', { 
          style: 'currency', 
          currency: this.config.currency || 'USD' 
        }).format(value);
      case 'date':
        return value => new Date(value).toLocaleDateString();
      case 'datetime':
        return value => new Date(value).toLocaleString();
      case 'percentage':
        return value => new Intl.NumberFormat('en-US', { 
          style: 'percent',
          maximumFractionDigits: 2
        }).format(value / 100);
      case 'decimal':
        return value => new Intl.NumberFormat('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        }).format(value);
      default:
        return value => value;
    }
  }

  renderEmptyState(container) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <div>${this.config.emptyMessage || 'No data available'}</div>
      </div>
    `;
  }

  refresh() {
    this.dispatchEvent(new CustomEvent('refresh', {
      detail: { id: this.id }
    }));
  }

  downloadData() {
    if (!this.data) return;
    
    // Convert data to CSV
    let csv;
    const filename = `${this.title.replace(/\s+/g, '_') || 'widget'}_data.csv`;
    
    if (Array.isArray(this.data)) {
      const headers = Object.keys(this.data[0]).join(',');
      const rows = this.data.map(item => Object.values(item).join(','));
      csv = [headers, ...rows].join('\n');
    } else {
      csv = Object.entries(this.data).map(([key, value]) => `${key},${value}`).join('\n');
    }
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  render() {
    return html`
      <div class="widget">
        <div class="widget-header">
          <h3 class="widget-title">${this.title}</h3>
          <div class="widget-actions">
            <button class="widget-action-btn" title="Refresh" @click=${this.refresh}>
              🔄
            </button>
            <button class="widget-action-btn" title="Download data" @click=${this.downloadData}>
              ⬇️
            </button>
          </div>
        </div>
        <div class="widget-content">
          ${this.loading ? html`
            <div class="loading-overlay">
              Loading...
            </div>
          ` : ''}
          
          ${this.error ? html`
            <div class="error">
              ${this.error}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }
}

customElements.define('report-widget', ReportWidget);