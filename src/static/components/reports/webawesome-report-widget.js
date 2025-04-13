import { LitElement, html, css } from 'lit';
import { styleMap } from 'lit/directives/style-map.js';
import { Chart } from 'chart.js/auto';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-table.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-icon.js';

/**
 * @element wa-report-widget
 * @description A standalone widget for displaying report data as metrics, charts, or tables using WebAwesome
 * @property {String} type - Type of widget (metric, chart, table)
 * @property {String} subtype - Subtype for charts (bar, line, pie, etc.)
 * @property {String} title - Widget title
 * @property {Object} data - The data to display
 * @property {Object} config - Widget configuration
 */
export class WebAwesomeReportWidget extends LitElement {
  static get properties() {
    return {
      type: { type: String },
      subtype: { type: String },
      title: { type: String },
      data: { type: Object },
      config: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      theme: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --widget-bg: var(--wa-card-bg-color, #ffffff);
        --widget-text-color: var(--wa-card-text-color, #333333);
        --widget-padding: var(--wa-card-padding, 16px);
        --widget-border-radius: var(--wa-card-border-radius, 8px);
        --widget-shadow: var(--wa-card-shadow, 0 2px 8px rgba(0,0,0,0.1));
      }
      .chart-container {
        flex: 1;
        position: relative;
        min-height: 150px;
        margin-top: 16px;
      }
      .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
        text-align: center;
        color: var(--wa-primary-color, #3f51b5);
      }
      .metric-label {
        text-align: center;
        color: var(--wa-text-secondary-color, #666);
        font-size: 14px;
      }
      .trend-indicator {
        display: inline-flex;
        align-items: center;
        font-size: 14px;
        margin-left: 8px;
      }
      .trend-up {
        color: var(--wa-success-color, #4caf50);
      }
      .trend-down {
        color: var(--wa-error-color, #f44336);
      }
      .trend-neutral {
        color: var(--wa-text-secondary-color, #9e9e9e);
      }
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100px;
        color: var(--wa-text-secondary-color, #666);
        padding: 20px;
      }
      .empty-state-icon {
        font-size: 32px;
        margin-bottom: 10px;
        color: var(--wa-text-disabled-color, #ccc);
      }
      .widget-actions {
        display: flex;
        gap: 8px;
      }
      .widget-content {
        padding: var(--widget-padding);
        flex: 1;
        display: flex;
        flex-direction: column;
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
    this.theme = 'light';
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
      const trendIcon = trendValue > 0 ? 'trending_up' : (trendValue < 0 ? 'trending_down' : 'remove');
      const formattedTrend = this.config.trendFormat ? 
        this.getFormatter(this.config.trendFormat)(Math.abs(trendValue)) : `${Math.abs(trendValue)}%`;
      
      trendHtml = `
        <span class="trend-indicator ${trendClass}">
          <wa-icon name="${trendIcon}"></wa-icon> ${formattedTrend}
        </span>
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
    
    // Apply WebAwesome theme colors
    this.applyThemeColors(chartData);
    
    // Create chart
    this.chart = new Chart(canvas, {
      type: chartType,
      data: chartData,
      options: chartOptions
    });
  }

  applyThemeColors(chartData) {
    // Apply WebAwesome theme colors to chart datasets
    const primaryColor = getComputedStyle(this).getPropertyValue('--wa-primary-color').trim() || '#3f51b5';
    const secondaryColor = getComputedStyle(this).getPropertyValue('--wa-secondary-color').trim() || '#f50057';
    const successColor = getComputedStyle(this).getPropertyValue('--wa-success-color').trim() || '#4caf50';
    const warningColor = getComputedStyle(this).getPropertyValue('--wa-warning-color').trim() || '#ff9800';
    const errorColor = getComputedStyle(this).getPropertyValue('--wa-error-color').trim() || '#f44336';
    
    // Theme color palette
    const themeColors = [primaryColor, secondaryColor, successColor, warningColor, errorColor];
    
    // Apply to datasets
    chartData.datasets.forEach((dataset, index) => {
      const baseColor = themeColors[index % themeColors.length];
      
      if (this.subtype === 'line') {
        dataset.borderColor = baseColor;
        dataset.backgroundColor = this.hexToRgba(baseColor, 0.2);
      } else if (this.subtype === 'pie' || this.subtype === 'doughnut') {
        if (!dataset.backgroundColor || !Array.isArray(dataset.backgroundColor)) {
          dataset.backgroundColor = Array(dataset.data.length).fill().map((_, i) => 
            this.hexToRgba(themeColors[i % themeColors.length], 0.8)
          );
        }
      } else {
        dataset.backgroundColor = this.hexToRgba(baseColor, 0.8);
      }
    });
  }
  
  hexToRgba(hex, alpha = 1) {
    // Convert hex color to rgba
    let r = 0, g = 0, b = 0;
    
    // 3 digits
    if (hex.length === 4) {
      r = parseInt(hex[1] + hex[1], 16);
      g = parseInt(hex[2] + hex[2], 16);
      b = parseInt(hex[3] + hex[3], 16);
    } 
    // 6 digits
    else if (hex.length === 7) {
      r = parseInt(hex.slice(1, 3), 16);
      g = parseInt(hex.slice(3, 5), 16);
      b = parseInt(hex.slice(5, 7), 16);
    }
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
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
              // Colors will be set in applyThemeColors
            });
          });
        } else if (this.config.valueKey) {
          // Single series
          datasets.push({
            label: this.config.datasetLabel || 'Value',
            data: this.data.map(item => item[this.config.valueKey]),
            // Colors will be set in applyThemeColors
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
              // Colors will be set in applyThemeColors
            });
          });
        }
      } else {
        // Simple array of values
        labels = this.data.map((_, index) => `Item ${index + 1}`);
        datasets.push({
          label: this.config.datasetLabel || 'Value',
          data: this.data,
          // Colors will be set in applyThemeColors
        });
      }
    } else if (typeof this.data === 'object') {
      // Object with key-value pairs
      labels = Object.keys(this.data);
      datasets.push({
        label: this.config.datasetLabel || 'Value',
        data: Object.values(this.data),
        // Colors will be set in applyThemeColors
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

  renderTable(container) {
    if (!this.data || (Array.isArray(this.data) && this.data.length === 0)) {
      this.renderEmptyState(container);
      return;
    }
    
    // Use WebAwesome table instead of custom HTML
    container.innerHTML = '';
    
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
    
    // Create WebAwesome table
    const table = document.createElement('wa-table');
    table.columns = columns.map(col => ({ 
      name: col.key, 
      label: col.label,
      format: col.format
    }));
    table.items = rows;
    table.density = 'compact';
    table.style.width = '100%';
    
    // Optional pagination
    if (this.config.page_size) {
      table.pagination = true;
      table.pageSize = this.config.page_size;
    }
    
    container.appendChild(table);
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
        <wa-icon name="bar_chart" size="large" class="empty-state-icon"></wa-icon>
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
      <wa-card elevation="1">
        <div slot="header" style="display: flex; justify-content: space-between; align-items: center;">
          <div>${this.title}</div>
          <div class="widget-actions">
            <wa-button variant="icon" @click=${this.refresh} title="Refresh">
              <wa-icon name="refresh"></wa-icon>
            </wa-button>
            <wa-button variant="icon" @click=${this.downloadData} title="Download data">
              <wa-icon name="download"></wa-icon>
            </wa-button>
          </div>
        </div>
        
        <div class="widget-content">
          ${this.loading ? html`
            <div style="display: flex; justify-content: center; padding: 20px;">
              <wa-spinner size="medium"></wa-spinner>
            </div>
          ` : ''}
          
          ${this.error ? html`
            <div style="color: var(--wa-error-color); padding: 12px; text-align: center;">
              ${this.error}
            </div>
          ` : ''}
        </div>
      </wa-card>
    `;
  }
}

customElements.define('wa-report-widget', WebAwesomeReportWidget);